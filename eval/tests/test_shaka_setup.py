"""Exercise dependency patches with real temporary Git repositories, no network or SDK."""
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def git(root, *args, env=None):
    return subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@invalid.example", *args],
                          cwd=root, env=env, capture_output=True, check=True).stdout


def test_patch_setup_needs_no_global_identity_and_stops_on_bad_patch(tmp_path):
    setup = tmp_path / "setup"
    player = setup / "shaka-player"
    player.mkdir(parents=True)
    helper = setup / "applyPatches.sh"
    shutil.copyfile(REPO / "app/shaka-setup/applyPatches.sh", helper)
    git(player, "init")
    (player / "fixture.txt").write_text("base\n")
    git(player, "add", "fixture.txt")
    git(player, "commit", "-m", "base fixture")
    base = git(player, "rev-parse", "HEAD").decode().strip()
    (player / "fixture.txt").write_text("patched\n")
    git(player, "commit", "-am", "test dependency patch")
    patch = git(player, "format-patch", "-1", "--stdout")
    git(player, "checkout", "--detach", base)
    patches = player / "shaka-rel/shaka-patch"
    patches.mkdir(parents=True)
    file = patches / "001.patch"
    file.write_bytes(patch)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("GIT_", "EMAIL"))}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    result = subprocess.run(["bash", str(helper)], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert (player / "fixture.txt").read_text() == "patched\n"
    assert git(player, "log", "-1", "--format=%ce").decode().strip() == "dependency-build@invalid.example"
    file.write_text("malformed patch must not be skipped\n")
    result = subprocess.run(["bash", str(helper)], env=env, capture_output=True, check=False)
    assert result.returncode != 0
    assert (player / "fixture.txt").read_text() == "patched\n"
