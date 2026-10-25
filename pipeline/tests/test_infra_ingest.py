"""The ingest container: what it publishes, what it refuses, and what it holds.

Two halves, neither of which calls AWS:

  * the entrypoint driven end to end against moto, which is a real S3, DynamoDB
    and SSM in this process. The pipeline itself is handed in as a function that
    writes a known title, because what is under test here is the publishing
    rule, not ffmpeg;
  * the Dockerfile and the build context read as text, so the promises made in
    docs/SECURITY.md about the image (ARM64, base pinned by digest, hashes for
    every package, not root) fail here if someone changes the file.

The publishing/container mutations are listed in docs/SECURITY.md. The offline
session fixture preserves the host environment and refuses identity-file and
network fallback. Its negative controls are recorded in
docs/overnight-2026-10-25/OFFLINE_AWS_TESTS.md.
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

boto3 = pytest.importorskip("boto3", reason="boto3 is needed for the ingest container tests")
moto = pytest.importorskip("moto", reason="moto is needed for the ingest container tests")

from botocore import configloader  # noqa: E402
from botocore import session as botocore_session  # noqa: E402
from botocore.config import Config  # noqa: E402
from botocore.configprovider import EnvironmentProvider  # noqa: E402
from botocore.credentials import CredentialResolver  # noqa: E402
from botocore.httpsession import URLLib3Session  # noqa: E402
from botocore.session import Session as BotocoreSession  # noqa: E402
from botocore.tokens import TokenProviderChain  # noqa: E402
from moto import mock_aws  # noqa: E402
from moto.core.base_backend import AccountSpecificBackend  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
INGEST_DIR = REPO / "pipeline" / "infra" / "ingest"
if str(INGEST_DIR) not in sys.path:
    sys.path.insert(0, str(INGEST_DIR))

import entrypoint  # noqa: E402

REGION = "us-east-1"
SOURCE_BUCKET = "calm-frames-source-test"
DELIVERY_BUCKET = "calm-frames-delivery-test"
TABLE = "calm-frames-catalog-test"
KEY_PARAM = "/calm-frames/signing-key"
UPLOAD_KEY = "uploads/HAZARD_example.mp4"
SOURCE_BYTES = b"not really a video, but it hashes like one"


def throwaway_private_key_pem() -> str:
    """A new Ed25519 key, made here and thrown away with the test process.

    Generated rather than written down. A PEM block in a repository is a thing
    someone copies, a thing gitleaks has to be told to ignore, and a thing that
    looks like a key in a diff. None of those are worth it for a fixture.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    return (
        ed25519.Ed25519PrivateKey.generate()
        .private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        .decode("ascii")
    )


def make_settings(tmp_path: Path, **overrides) -> entrypoint.Settings:
    values = {
        "source_bucket": SOURCE_BUCKET,
        "source_key": UPLOAD_KEY,
        "delivery_bucket": DELIVERY_BUCKET,
        "catalog_table": TABLE,
        "presets": ["wcag"],
        "signing_key_param": "",
        "workdir": tmp_path / "work",
    }
    values.update(overrides)
    return entrypoint.Settings(**values)


class InMemoryAwsSession(BotocoreSession):
    """A test-only profile that cannot open a developer's AWS identity files."""

    @property
    def full_config(self):
        return {"profiles": {"offline-ingest-tests": {"region": REGION}}}


@contextmanager
def isolated_aws_clients():
    """Use Moto backends with no environment, profile-file or network fallback.

    Moto's default credential/session patching is disabled. Dummy credentials
    belong only to this private session, never to os.environ or boto3's global
    session. The host's AWS_PROFILE guard remains in force throughout.
    """
    def environment_snapshot():
        # Pytest itself changes this marker between fixture setup and teardown.
        return {key: value for key, value in os.environ.items() if key != "PYTEST_CURRENT_TEST"}

    environment = environment_snapshot()
    default_session = boto3.DEFAULT_SESSION

    def refuse_identity_files(*args, **kwargs):
        raise AssertionError("AWS identity/config files are forbidden in offline tests")

    def refuse_credentials(*args, **kwargs):
        raise AssertionError("Ambient AWS credentials are forbidden in offline tests")

    def refuse_transport(*args, **kwargs):
        raise AssertionError("AWS HTTP transport is forbidden outside Moto")

    def refuse_socket(*args, **kwargs):
        raise AssertionError("Network sockets are forbidden in offline tests")

    def in_memory_core():
        core = InMemoryAwsSession(profile="offline-ingest-tests")
        core.set_credentials("FOOBARKEY", "FOOBARSECRET")
        core.register_component("credential_provider", CredentialResolver([]))
        core.register_component("token_provider", TokenProviderChain([]))
        return core

    with pytest.MonkeyPatch.context() as isolated:
        # Moto's lazy SSM/EC2 region tables also construct fresh SDK sessions.
        # Their constructors must use the same in-memory identity boundary.
        isolated.setattr(botocore_session, "get_session", in_memory_core)
        isolated.setattr(configloader, "load_config", refuse_identity_files)
        isolated.setattr(configloader, "raw_config_parse", refuse_identity_files)
        isolated.setattr(CredentialResolver, "load_credentials", refuse_credentials)
        isolated.setattr(URLLib3Session, "send", refuse_transport)
        isolated.setattr(socket, "getaddrinfo", refuse_socket)
        isolated.setattr(socket, "create_connection", refuse_socket)
        isolated.setattr(socket.socket, "connect", refuse_socket)
        isolated.setattr(socket.socket, "connect_ex", refuse_socket)
        try:
            with mock_aws(config={"core": {
                "mock_credentials": False,
                "reset_boto3_session": False,
                "service_whitelist": ["s3", "ssm", "dynamodb"],
                "passthrough": {"urls": [], "services": []},
            }}):
                session = boto3.Session(
                    botocore_session=in_memory_core(),
                    aws_access_key_id="FOOBARKEY",
                    aws_secret_access_key="FOOBARSECRET",
                    region_name=REGION,
                )
                # Moto queries SDK region metadata through its own Session().
                # Give that offline lookup the same in-memory session as clients.
                isolated.setattr(AccountSpecificBackend, "get_session", staticmethod(lambda: session))
                config = Config(
                    ignore_configured_endpoint_urls=True,
                    proxies={},
                    retries={"max_attempts": 0},
                    defaults_mode="legacy",
                )
                clients = {
                    service: session.client(service, config=config)
                    for service in ("s3", "ssm", "dynamodb")
                }
                try:
                    yield clients
                finally:
                    for client in clients.values():
                        client.close()
        finally:
            # Do not let pytest print environment contents if a guard fails.
            if environment_snapshot() != environment:
                pytest.fail("Offline AWS fixture changed the process environment")
            if boto3.DEFAULT_SESSION is not default_session:
                pytest.fail("Offline AWS fixture replaced the global boto3 session")


@pytest.fixture
def aws_clients():
    with isolated_aws_clients() as clients:
        yield clients


def set_up_aws(clients) -> None:
    clients["s3"].create_bucket(Bucket=SOURCE_BUCKET)
    clients["s3"].create_bucket(Bucket=DELIVERY_BUCKET)
    clients["s3"].put_object(Bucket=SOURCE_BUCKET, Key=UPLOAD_KEY, Body=SOURCE_BYTES)
    clients["dynamodb"].create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "sha256", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "sha256", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def fake_pipeline(workdir: Path, *, verified: bool, seen: dict):
    """A stand in for pipeline.ingest that writes the title tree it would write.

    It records the arguments it was called with, so a test can check that the
    key really was passed, and writes both the files that may be published and
    the ones that must never leave the task.
    """
    from pipeline.hashing import sha256_file
    from pipeline.layout import TitleLayout

    def run(argv: list[str]) -> int:
        seen["argv"] = list(argv)
        source = Path(argv[0])
        seen["key_exists_during_run"] = (
            Path(argv[argv.index("--key") + 1]).exists() if "--key" in argv else None
        )
        if "--key" in argv:
            key_path = Path(argv[argv.index("--key") + 1])
            seen["key_mode"] = key_path.stat().st_mode & 0o777
            seen["key_dir_mode"] = key_path.parent.stat().st_mode & 0o777
        sha = sha256_file(source)
        layout = TitleLayout(workdir, sha)
        layout.root.mkdir(parents=True, exist_ok=True)

        publishable = {
            "maps/wcag.json": '{"version": 1}',
            "plans/wcag.json": "{}",
            "bif/wcag.bif": "bif",
            "bif/wcag.json": "{}",
            "posters/wcag.json": "{}",
            "posters/wcag/poster_01.jpg": "jpeg",
            "safe/wcag/safe.mp4": "the kid safe rendition",
            "safe/wcag/hls/master.m3u8": "#EXTM3U",
            "safe/wcag/hls/segment_000.ts": "ts",
            "verify/report.json": '{"passed": true}',
        }
        # These are the files the task must keep to itself. The cover model is
        # the original video with covers drawn on it, so it is exactly as
        # hazardous as the original.
        private = {
            "verify/cover_model_wcag.mp4": "the original with covers on it",
            "probe.json": "{}",
            "luma.json": "{}",
            "state.json": "{}",
            "still.png": "png",
            "work/luma_metadata.txt": "scratch",
        }
        for relative, text in {**publishable, **private}.items():
            path = layout.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

        entry = {
            "sha256": sha,
            "title": "Example",
            "source_name": source.name,
            "duration_s": 12.5,
            "width": 1920,
            "height": 1080,
            "status": "verified" if verified else "failed",
            "verified": verified,
            "renditions": {"wcag": {"preset": "wcag"}},
        }
        layout.entry_path.write_text(json.dumps(entry))
        return 0

    return run


def delivery_keys(clients) -> list[str]:
    listing = clients["s3"].list_objects_v2(Bucket=DELIVERY_BUCKET)
    return sorted(item["Key"] for item in listing.get("Contents", []))


class TestOfflineAwsIsolation:
    def test_a_missing_ambient_profile_cannot_affect_mocked_services(self, monkeypatch):
        original = EnvironmentProvider.provide
        profile_reads = []

        def nonexistent_profile(provider):
            if provider._name in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE"):
                profile_reads.append(provider._name)
                return "nonexistent-offline-profile"
            return original(provider)

        # Model an invalid ambient profile without changing the actual guard.
        monkeypatch.setattr(EnvironmentProvider, "provide", nonexistent_profile)
        assert EnvironmentProvider("AWS_PROFILE", {}).provide() == "nonexistent-offline-profile"
        profile_reads.clear()
        with isolated_aws_clients() as clients:
            set_up_aws(clients)
            clients["ssm"].put_parameter(Name=KEY_PARAM, Value="fictional", Type="String")
            assert clients["s3"].get_object(Bucket=SOURCE_BUCKET, Key=UPLOAD_KEY)["Body"].read() == SOURCE_BYTES
            assert clients["dynamodb"].scan(TableName=TABLE)["Items"] == []
            assert clients["ssm"].get_parameter(Name=KEY_PARAM)["Parameter"]["Value"] == "fictional"
        assert profile_reads == []

    def test_requests_that_escape_moto_are_refused_before_transport(self, monkeypatch):
        from moto.core.models import botocore_stubber

        with isolated_aws_clients() as clients:
            assert clients["s3"].list_buckets()["Buckets"] == []
            with monkeypatch.context() as escaped:
                escaped.setattr(botocore_stubber, "enabled", False)
                with pytest.raises(AssertionError, match="AWS HTTP transport is forbidden outside Moto"):
                    clients["s3"].list_buckets()
            with pytest.raises(AssertionError, match="Network sockets are forbidden"):
                socket.create_connection(("offline.example.invalid", 443))

    def test_identity_file_and_provider_fallbacks_fail_closed(self, tmp_path):
        class UnexpectedProvider:
            METHOD = "offline-unexpected"

            def load(self):
                pytest.fail("An ambient credential provider was consulted")

        with isolated_aws_clients():
            for loader in (configloader.load_config, configloader.raw_config_parse):
                with pytest.raises(AssertionError, match="AWS identity/config files are forbidden"):
                    loader(str(tmp_path / "nonexistent-config"))
            with pytest.raises(AssertionError, match="Ambient AWS credentials are forbidden"):
                CredentialResolver([UnexpectedProvider()]).load_credentials()


class TestOnlyACheckedTitleIsPublished:
    def test_a_verified_title_is_published_and_written_to_the_catalog(self, tmp_path, aws_clients):
        clients = aws_clients
        set_up_aws(clients)
        settings = make_settings(tmp_path)
        seen: dict = {}

        code = entrypoint.run(
            settings, clients, fake_pipeline(settings.workdir, verified=True, seen=seen)
        )

        assert code == 0
        keys = delivery_keys(clients)
        assert any(key.endswith("safe/wcag/hls/master.m3u8") for key in keys)
        assert any(key.endswith("maps/wcag.json") for key in keys)
        assert any(key.endswith("entry.json") for key in keys)

        rows = clients["dynamodb"].scan(TableName=TABLE)["Items"]
        assert len(rows) == 1
        assert rows[0]["verified"]["BOOL"] is True
        assert rows[0]["status"]["S"] == "verified"

    def test_nothing_is_published_when_verify_did_not_pass(self, tmp_path, aws_clients):
        """The guard: a title verify refused publishes no bytes at all.

        Seen to fail by making is_publishable return True whatever the entry
        says. The failure reads:
          assert [] == []  ->  AssertionError on delivery_keys(clients) == []
        """
        clients = aws_clients
        set_up_aws(clients)
        settings = make_settings(tmp_path)
        seen: dict = {}

        code = entrypoint.run(
            settings, clients, fake_pipeline(settings.workdir, verified=False, seen=seen)
        )

        assert code != 0
        assert delivery_keys(clients) == []
        assert clients["dynamodb"].scan(TableName=TABLE)["Items"] == []

    def test_a_half_written_entry_is_not_publishable(self):
        assert entrypoint.is_publishable({"verified": True, "status": "verified"})
        assert not entrypoint.is_publishable({"verified": True, "status": "pending"})
        assert not entrypoint.is_publishable({"verified": False, "status": "verified"})
        assert not entrypoint.is_publishable({})


class TestTheHazardousFilesStayInTheTask:
    def test_the_cover_model_and_the_source_never_reach_the_delivery_bucket(self, tmp_path, aws_clients):
        """The guard: the upload list is an allowlist, not a directory walk.

        Seen to fail by replacing publishable_paths with a walk of the title
        directory. The failure names the file:
          AssertionError: verify/cover_model_wcag.mp4 was published
        """
        clients = aws_clients
        set_up_aws(clients)
        settings = make_settings(tmp_path)
        seen: dict = {}

        entrypoint.run(
            settings, clients, fake_pipeline(settings.workdir, verified=True, seen=seen)
        )

        keys = delivery_keys(clients)
        for forbidden in (
            "cover_model",
            "probe.json",
            "luma.json",
            "state.json",
            "still.png",
            "work/",
            "HAZARD_example.mp4",
        ):
            offending = [key for key in keys if forbidden in key]
            assert offending == [], f"{forbidden} was published as {offending}"

    def test_the_allowlist_only_returns_files_that_exist(self, tmp_path):
        root = tmp_path / "titles" / "abc"
        (root / "maps").mkdir(parents=True)
        (root / "maps" / "wcag.json").write_text("{}")
        paths = entrypoint.publishable_paths(root, ["wcag"])
        assert [path.name for path in paths] == ["wcag.json"]


class TestAHostileObjectKey:
    @pytest.mark.parametrize(
        "key",
        [
            "uploads/../../../etc/passwd",
            "uploads/a/../../b",
            "somewhere/else.mp4",
            "uploads/",
            "uploads/.",
            "uploads/..",
            "uploads/.hidden",
            "uploads/name\nwith-newline.mp4",
        ],
    )
    def test_a_key_that_is_not_a_plain_name_under_uploads_is_refused(self, key):
        """The guard: an S3 key is attacker controlled text, not a file path.

        Seen to fail by having local_name_for return the last component with no
        check. The failure reads:
          Failed: DID NOT RAISE <class 'entrypoint.TaskRefused'>
        """
        with pytest.raises(entrypoint.TaskRefused):
            entrypoint.local_name_for(key)

    def test_an_ordinary_key_still_works(self):
        assert entrypoint.local_name_for("uploads/HAZARD_a b.mp4") == "HAZARD_a b.mp4"
        assert entrypoint.local_name_for("uploads/nested/title.webm") == "title.webm"


class TestTheSigningKey:
    def test_the_key_is_readable_only_by_this_user_and_is_gone_at_the_end(self, tmp_path, aws_clients):
        """The guard: a private key fetched into the task does not outlive it.

        Seen to fail by removing the cleanup in the finally block. The failure
        reads:
          AssertionError: assert not True  ->  the keys directory still exists
        """
        clients = aws_clients
        set_up_aws(clients)
        clients["ssm"].put_parameter(
            Name=KEY_PARAM, Value=throwaway_private_key_pem(), Type="SecureString"
        )
        settings = make_settings(tmp_path, signing_key_param=KEY_PARAM)
        seen: dict = {}

        entrypoint.run(
            settings, clients, fake_pipeline(settings.workdir, verified=True, seen=seen)
        )

        assert seen["key_exists_during_run"] is True
        assert seen["key_mode"] == 0o600
        assert seen["key_dir_mode"] == 0o700
        assert not (settings.workdir / "keys").exists()
        # And it was never published.
        assert [key for key in delivery_keys(clients) if "key" in key.lower()] == []

    def test_the_key_is_deleted_even_when_the_pipeline_raises(self, tmp_path, aws_clients):
        clients = aws_clients
        set_up_aws(clients)
        clients["ssm"].put_parameter(
            Name=KEY_PARAM, Value=throwaway_private_key_pem(), Type="SecureString"
        )
        settings = make_settings(tmp_path, signing_key_param=KEY_PARAM)

        def explode(argv):
            raise RuntimeError("ffmpeg fell over")

        with pytest.raises(RuntimeError):
            entrypoint.run(settings, clients, explode)
        assert not (settings.workdir / "keys").exists()

    def test_a_parameter_that_is_not_a_private_key_is_refused(self, tmp_path, aws_clients):
        clients = aws_clients
        clients["ssm"].put_parameter(Name=KEY_PARAM, Value="hello", Type="SecureString")
        with pytest.raises(entrypoint.TaskRefused):
            entrypoint.fetch_signing_key(clients["ssm"], KEY_PARAM, tmp_path / "keys")

    def test_without_a_parameter_the_pipeline_is_run_with_no_key_at_all(self, tmp_path, aws_clients):
        clients = aws_clients
        set_up_aws(clients)
        settings = make_settings(tmp_path)
        seen: dict = {}

        entrypoint.run(
            settings, clients, fake_pipeline(settings.workdir, verified=True, seen=seen)
        )

        assert "--key" not in seen["argv"]
        assert "--pub" not in seen["argv"]


class TestSettings:
    def test_a_missing_bucket_name_stops_the_task_before_it_starts(self):
        with pytest.raises(entrypoint.TaskRefused):
            entrypoint.Settings.from_env({"CALM_FRAMES_SOURCE_KEY": UPLOAD_KEY})

    def test_the_defaults_are_one_preset_and_no_signing_key(self):
        settings = entrypoint.Settings.from_env(
            {
                "CALM_FRAMES_SOURCE_BUCKET": SOURCE_BUCKET,
                "CALM_FRAMES_SOURCE_KEY": UPLOAD_KEY,
                "CALM_FRAMES_DELIVERY_BUCKET": DELIVERY_BUCKET,
                "CALM_FRAMES_CATALOG_TABLE": TABLE,
            }
        )
        assert settings.presets == ["wcag"]
        assert settings.signing_key_param == ""
        assert settings.workdir == Path("/work")


@pytest.fixture(scope="module")
def dockerfile() -> str:
    return (INGEST_DIR / "Dockerfile").read_text()


@pytest.fixture(scope="module")
def stack_module():
    aws_cdk = pytest.importorskip("aws_cdk", reason="aws-cdk-lib is needed")
    infra = REPO / "pipeline" / "infra"
    if str(infra) not in sys.path:
        sys.path.insert(0, str(infra))
    import calm_frames_stack

    return aws_cdk, calm_frames_stack


class TestTheImageItself:
    """Read the Dockerfile rather than build it, so this runs on any CI box."""

    def test_the_base_image_is_pinned_by_digest(self, dockerfile):
        """The guard: a tag moves, a digest does not.

        Seen to fail by dropping the @sha256: part of the FROM line. The failure
        reads:
          AssertionError: the FROM line must pin a digest
        """
        from_lines = [line for line in dockerfile.splitlines() if line.startswith("FROM ")]
        assert from_lines, "there is no FROM line"
        for line in from_lines:
            assert "@sha256:" in line, "the FROM line must pin a digest"

    def test_ffmpeg_is_pinned_to_one_apt_version(self, dockerfile):
        """The guard: a bare package name lets the decoder change under a rebuild.

        This image's ffmpeg is not the one on the machine that wrote it, and
        neither is the one on a CI runner. docs/ENVIRONMENT.md lists all three.
        The pin is what makes the container's decoder a fact of the commit
        rather than a fact of the day the build ran.

        Seen to fail by putting the bare name back. The failure reads:
          AssertionError: apt installs ffmpeg without an exact version
        """
        installs = [
            line for line in dockerfile.splitlines() if "apt-get install" in line and "ffmpeg" in line
        ]
        assert installs, "the image never installs ffmpeg"
        for line in installs:
            assert re.search(r"ffmpeg=\$\{?FFMPEG_APT_VERSION\}?|ffmpeg=[0-9]", line), (
                "apt installs ffmpeg without an exact version"
            )

        arg_lines = [line for line in dockerfile.splitlines() if line.startswith("ARG FFMPEG_APT_VERSION=")]
        assert len(arg_lines) == 1, "there is no single ARG holding the pinned ffmpeg version"
        pinned = arg_lines[0].split("=", 1)[1].strip()
        assert re.fullmatch(r"\d+:\d+\.\d+\.\d+-[0-9a-z+.~]+", pinned), (
            f"the pinned ffmpeg version does not look like a Debian version: {pinned!r}"
        )

    def test_every_python_package_is_installed_from_a_hash(self, dockerfile):
        assert "--require-hashes" in dockerfile
        requirements = (INGEST_DIR / "requirements.txt").read_text()
        assert "--hash=sha256:" in requirements
        for line in requirements.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "--hash", "#")):
                continue
            if stripped.endswith("\\"):
                stripped = stripped[:-1].strip()
            if stripped.startswith("#"):
                continue
            assert "==" in stripped, f"unpinned requirement: {line!r}"

    def test_the_task_does_not_run_as_root(self, dockerfile):
        users = [line.split()[1] for line in dockerfile.splitlines() if line.startswith("USER ")]
        assert users, "the image never leaves root"
        assert users[-1] not in ("root", "0")

    def test_the_build_context_cannot_pick_up_media_or_keys(self):
        """The guard: .dockerignore is an allowlist, so nothing new leaks in.

        Seen to fail by removing the leading `*` line. The failure reads:
          AssertionError: .dockerignore must start by ignoring everything
        """
        ignore = (REPO / ".dockerignore").read_text().splitlines()
        meaningful = [line.strip() for line in ignore if line.strip() and not line.startswith("#")]
        assert meaningful[0] == "*", ".dockerignore must start by ignoring everything"
        allowed = {line[1:].rstrip("/") for line in meaningful if line.startswith("!")}
        # media/, the keys and .git are not in the allowlist, so they cannot be
        # sent to the daemon whatever else changes.
        for forbidden in ("media", ".git", "results", "app", "eval", "docs"):
            assert forbidden not in allowed
        assert "**/*.pem" in meaningful

    def test_the_build_context_leaves_out_what_a_deploy_or_an_install_writes(self):
        """The guard: generated files inside the allowed directories stay out.

        The image pushed on Oct 9, 2026 carried pipeline/infra/cdk.context.json,
        the CDK lookup cache the deploy had written into the checkout minutes
        before the build, and that file holds an availability zone lookup keyed
        by the account id. The editable install of flashmap in the venv writes
        flashmap/src/flashmap.egg-info/, which `flashmap/*.egg-info/` does not
        reach, and pytest leaves flashmap/.pytest_cache/ behind.

        Read through scripts/build_context.py, the matcher `make image-context`
        uses. It reimplements docker's rules rather than calling docker, so the
        second half checks that the code the image needs still goes in, which
        stops this from passing by excluding everything.

        Seen to fail, Oct 9 2026: removing each of the three new .dockerignore
        lines in turn turned this red with that path named, and restoring the
        line turned it green.
        """
        import importlib.util  # noqa: PLC0415

        spec = importlib.util.spec_from_file_location(
            "build_context", REPO / "scripts" / "build_context.py"
        )
        build_context = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_context)
        rules = build_context.read_rules(REPO / ".dockerignore")

        for generated in (
            "pipeline/infra/cdk.context.json",
            "flashmap/src/flashmap.egg-info",
            "flashmap/src/flashmap.egg-info/PKG-INFO",
            "flashmap/.pytest_cache",
            "flashmap/.pytest_cache/v/cache/nodeids",
        ):
            assert not build_context.included(generated, rules), (
                f"{generated} would be sent to the docker daemon"
            )
        for needed in (
            "flashmap/pyproject.toml",
            "flashmap/src/flashmap/analyze.py",
            "pipeline/ingest.py",
            "pipeline/infra/ingest/entrypoint.py",
            "pipeline/infra/ingest/requirements.txt",
        ):
            assert build_context.included(needed, rules), f"{needed} is needed and left out"


class TestTheStackKnowsAboutTheContainer:
    """The parts of the template that only exist because of this container."""

    def template(self, stack_module, **overrides):
        aws_cdk, module = stack_module
        from aws_cdk.assertions import Template  # noqa: PLC0415

        app = aws_cdk.App()
        stack = module.CalmFramesStack(
            app,
            "TestStack",
            config=module.StackConfig(**overrides),
            env=aws_cdk.Environment(account="123456789012", region="us-east-1"),
        )
        return Template.from_stack(stack)

    def test_the_task_is_told_which_presets_to_build(self, stack_module):
        template = self.template(stack_module)
        definitions = template.find_resources("AWS::ECS::TaskDefinition")
        environments = [
            {pair["Name"]: pair["Value"] for pair in container["Environment"]}
            for definition in definitions.values()
            for container in definition["Properties"]["ContainerDefinitions"]
        ]
        assert environments
        for environment in environments:
            assert environment["CALM_FRAMES_PRESETS"] == "wcag"
            assert "CALM_FRAMES_SIGNING_KEY_PARAM" not in environment

    def test_no_parameter_means_no_permission_to_read_one(self, stack_module):
        """The guard: the default stack cannot read any SSM parameter.

        Seen to fail by granting ssm:GetParameter whether or not a parameter
        name was configured. The failure reads:
          AssertionError: assert [] == [] where the left side is the GetParameter
          statements found in the template.
        """
        template = self.template(stack_module)
        statements = [
            statement
            for policy in template.find_resources("AWS::IAM::Policy").values()
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]
            if "ssm:" in str(statement.get("Action"))
        ]
        assert statements == []

    def test_a_configured_parameter_is_readable_and_nothing_else_is(self, stack_module):
        """The guard: the grant names one parameter, never a wildcard.

        Seen to fail by widening the resource to "*". The failure reads:
          AssertionError: assert '*'.endswith('parameter/calm-frames/signing-key')
        """
        template = self.template(stack_module, signing_key_parameter="/calm-frames/signing-key")
        statements = [
            statement
            for policy in template.find_resources("AWS::IAM::Policy").values()
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]
            if "ssm:GetParameter" in str(statement.get("Action"))
        ]
        assert len(statements) == 1
        resource = statements[0]["Resource"]
        assert isinstance(resource, str)
        assert resource.endswith("parameter/calm-frames/signing-key")

        decrypt = [
            statement
            for policy in template.find_resources("AWS::IAM::Policy").values()
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]
            if "kms:Decrypt" in str(statement.get("Action"))
        ]
        assert len(decrypt) == 1
        assert decrypt[0]["Condition"]["StringEquals"]["kms:ViaService"] == (
            "ssm.us-east-1.amazonaws.com"
        )
        assert decrypt[0]["Resource"] != "*"


def test_the_entrypoint_is_the_file_the_dockerfile_runs():
    """A rename that forgets the Dockerfile would leave a task that cannot start."""
    dockerfile = (INGEST_DIR / "Dockerfile").read_text()
    assert "COPY pipeline/infra/ingest/entrypoint.py" in dockerfile
    assert 'ENTRYPOINT ["python", "/opt/calmframes/ingest_entrypoint.py"]' in dockerfile
    assert (INGEST_DIR / "entrypoint.py").is_file()


def test_no_key_file_is_committed_anywhere_under_the_pipeline():
    """The fixture key is generated, so no PEM should exist in the tree at all."""
    assert list((REPO / "pipeline").rglob("*.pem")) == []
