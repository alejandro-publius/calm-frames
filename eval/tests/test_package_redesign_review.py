"""A review bundle must not combine current source with stale native evidence."""
import hashlib
import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'package_redesign_review.py'
spec = importlib.util.spec_from_file_location('package_review', SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    return path


def save_receipts(root, native, demo):
    put(root, 'results/native.json', json.dumps(native))
    put(root, 'results/demo.json', json.dumps(demo))


@pytest.fixture
def inputs(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'user.name', 'Fixture')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    put(root, '.gitignore', 'build/\n.logs/\napp/build/\napp/src/generated/\n')
    put(root, 'app/src/main.ts', 'export const title = "Calm";\n')
    put(root, 'app/assets/art.png', 'benign fixture artwork')
    put(root, 'app/package-lock.json', '{}')
    put(root, 'README.md', 'Fixture source, not native validation.')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Initial app')
    commit = git(root, 'rev-parse', 'HEAD')
    package = put(root, 'app/build/demo.vpkg', 'benign package bytes')
    video = put(root, 'build/demo.mp4', 'benign video bytes')
    capture = put(root, '.logs/capture.png', 'benign captured image')
    plan = put(root, '.logs/capture-plan.json', '{}')
    inventory = [{'path': name, 'sha256': sha(root / name)}
                 for name in sorted(git(root, 'ls-files', '--', 'app').splitlines())]
    native = {'source_commit': commit,
              'package': {'path': 'app/build/demo.vpkg', 'sha256': sha(package)},
              'app_source_files': inventory,
              'capture_files': [{'path': '.logs/capture.png', 'sha256': sha(capture)}]}
    demo = {'video': 'build/demo.mp4', 'sha256': sha(video),
            'capture_manifest': '.logs/capture-plan.json', 'capture_manifest_sha256': sha(plan),
            'capture_source_commit': commit, 'capture_package_sha256': sha(package),
            'shots': [{'source': '.logs/capture.png', 'source_sha256': sha(capture)}]}
    save_receipts(root, native, demo)
    return root, native, demo


def package(root, **kwargs):
    return review.package_review(root=root, native_receipt='results/native.json',
                                 demo_manifest='results/demo.json',
                                 output='build/review.zip', receipt='results/bundle.json',
                                 **kwargs)


def assert_no_outputs(root):
    assert not (root / 'build/review.zip').exists()
    assert not (root / 'build/review-source.zip').exists()
    assert not (root / 'results/bundle.json').exists()


def test_packages_doc_only_head_and_verifies_every_payload(inputs):
    root, native, _ = inputs
    put(root, 'README.md', 'Updated documentation')
    git(root, 'add', 'README.md')
    git(root, 'commit', '-qm', 'Documentation only')
    put(root, '.logs/authentication.log', 'must not be discovered')
    receipt = package(root, include=['README.md'])
    assert receipt['source_archive_commit'] == git(root, 'rev-parse', 'HEAD')
    assert receipt['native_receipt_source_commit'] == native['source_commit']
    assert receipt['published'] is False
    with zipfile.ZipFile(root / 'build/review.zip') as archive:
        manifest = json.loads(archive.read('bundle-manifest.json'))
        for item in manifest['files']:
            assert hashlib.sha256(archive.read(item['path'])).hexdigest() == item['sha256']
        assert '.logs/capture.png' in archive.namelist()
        assert '.logs/authentication.log' not in archive.namelist()
        assert 'Native execution was not performed by this packaging tool' in archive.read('REVIEW_README.txt').decode()


@pytest.mark.parametrize('name', ['app/src/main.ts', 'app/assets/art.png', 'app/package-lock.json'])
def test_rejects_new_app_commit_before_writing(inputs, name):
    root, _, _ = inputs
    put(root, name, 'changed app input')
    git(root, 'add', name)
    git(root, 'commit', '-qm', 'Changed app')
    with pytest.raises(ValueError, match='app tree'):
        package(root)
    assert_no_outputs(root)


@pytest.mark.parametrize('name', ['app/src/main.ts', 'app/src/untracked.ts'])
def test_rejects_uncommitted_app_inputs(inputs, name):
    root, _, _ = inputs
    put(root, name, 'not represented in commit')
    with pytest.raises(ValueError, match='uncommitted app'):
        package(root)
    assert_no_outputs(root)


@pytest.mark.parametrize('name', ['app/build/demo.vpkg', 'build/demo.mp4', '.logs/capture.png'])
def test_rejects_changed_recorded_payload_hash(inputs, name):
    root, _, _ = inputs
    put(root, name, 'different bytes')
    with pytest.raises(ValueError, match='SHA-256'):
        package(root)
    assert_no_outputs(root)


def test_rejects_demo_from_different_package(inputs):
    root, native, demo = inputs
    demo['capture_package_sha256'] = '0' * 64
    save_receipts(root, native, demo)
    with pytest.raises(ValueError, match='capture package'):
        package(root)
    assert_no_outputs(root)


def test_rejects_changed_shot_hash_even_if_capture_receipt_matches(inputs):
    root, native, demo = inputs
    demo['shots'][0]['source_sha256'] = '0' * 64
    save_receipts(root, native, demo)
    with pytest.raises(ValueError, match='SHA-256'):
        package(root)
    assert_no_outputs(root)


def test_rejects_old_capture_commit_even_with_current_package_hash(inputs):
    root, native, demo = inputs
    put(root, 'app/assets/art.png', 'updated art')
    git(root, 'add', 'app/assets/art.png')
    git(root, 'commit', '-qm', 'Updated art')
    native['source_commit'] = git(root, 'rev-parse', 'HEAD')
    save_receipts(root, native, demo)
    with pytest.raises(ValueError, match='demo capture app tree'):
        package(root)
    assert_no_outputs(root)


def test_rejects_invalid_recorded_capture_hash(inputs):
    root, native, demo = inputs
    native['capture_files'][0]['sha256'] = None
    save_receipts(root, native, demo)
    with pytest.raises(ValueError, match='invalid SHA-256'):
        package(root)
    assert_no_outputs(root)


def test_zip_payload_verification_rejects_different_bytes(tmp_path):
    archive = tmp_path / 'payload.zip'
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('file.txt', b'unexpected content')
    with pytest.raises(ValueError, match='ZIP payload SHA-256'):
        review.verify_zip(archive, {'file.txt': hashlib.sha256(b'expected content').hexdigest()})


@pytest.mark.parametrize('name', ['build/review.zip', 'build/review-source.zip', 'results/bundle.json'])
def test_never_overwrites_existing_outputs(inputs, name):
    root, _, _ = inputs
    existing = put(root, name, 'preserved previous artifact')
    with pytest.raises(ValueError, match='already exists'):
        package(root)
    assert existing.read_text() == 'preserved previous artifact'
    assert sum((root / path).exists() for path in ['build/review.zip', 'build/review-source.zip', 'results/bundle.json']) == 1


@pytest.mark.parametrize('name', ['../outside.txt', '/tmp/outside.txt', 'docs/../README.md', 'bad\nname.txt', r'docs\file.txt'])
def test_rejects_unsafe_zip_paths(inputs, name):
    root, _, _ = inputs
    with pytest.raises(ValueError, match='safe repository-relative'):
        package(root, include=[name])
    assert_no_outputs(root)


def test_rejects_symlink_outside_repository(inputs):
    root, _, _ = inputs
    outside = put(root.parent, 'outside.txt', 'outside')
    (root / 'linked.txt').symlink_to(outside)
    with pytest.raises(ValueError, match='outside repository'):
        package(root, include=['linked.txt'])
    assert_no_outputs(root)


def test_missing_input_does_not_leave_partial_archives(inputs):
    root, _, _ = inputs
    with pytest.raises(ValueError, match='missing input'):
        package(root, include=['docs/missing.md'])
    assert_no_outputs(root)


def test_rejects_unsafe_committed_source_archive_name(inputs):
    root, _, _ = inputs
    put(root, 'unsafe\nname.txt', 'fixture')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Unusual source path')
    with pytest.raises(ValueError, match='safe repository-relative'):
        package(root)
    assert_no_outputs(root)


@pytest.mark.parametrize('mode', ['missing', 'empty', 'partial'])
def test_requires_complete_app_inventory(inputs, mode):
    root, native, demo = inputs
    if mode == 'missing':
        del native['app_source_files']
    else:
        native['app_source_files'] = [] if mode == 'empty' else native['app_source_files'][:1]
    save_receipts(root, native, demo)
    with pytest.raises(ValueError, match='complete app source inventory'):
        package(root)
    assert_no_outputs(root)


def test_rejects_added_ignored_runtime_source(inputs):
    root, _, _ = inputs
    put(root, 'app/src/generated/polyfill.ts', 'unrecorded generated source')
    with pytest.raises(ValueError, match='complete app source inventory'):
        package(root)
    assert_no_outputs(root)


@pytest.mark.parametrize('location', ['shot', 'capture'])
def test_requires_recorded_evidence_hash(inputs, location):
    root, native, demo = inputs
    if location == 'shot':
        del demo['shots'][0]['source_sha256']
    else:
        del native['capture_files'][0]['sha256']
    save_receipts(root, native, demo)
    with pytest.raises(ValueError, match='SHA-256'):
        package(root)
    assert_no_outputs(root)


def test_includes_original_capture_plan(inputs):
    root, _, _ = inputs
    package(root)
    with zipfile.ZipFile(root / 'build/review.zip') as archive:
        assert archive.read('.logs/capture-plan.json') == b'{}'


def test_rejects_changed_capture_plan(inputs):
    root, _, _ = inputs
    put(root, '.logs/capture-plan.json', 'changed plan')
    with pytest.raises(ValueError, match='SHA-256'):
        package(root)
    assert_no_outputs(root)
