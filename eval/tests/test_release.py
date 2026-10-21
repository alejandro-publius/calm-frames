"""Exercise release preparation with fake packages, never native validation."""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def project(tmp_path):
    repo = tmp_path / 'project'
    (repo / 'scripts').mkdir(parents=True)
    shutil.copy2(ROOT / 'scripts/release.sh', repo / 'scripts/release.sh')
    files = {
        'app/manifest.toml': '[package]\nid = "io.example.calm"\nversion = "0.1.0"\n[os.version]\nmin = "1.2"\ntarget = "1.2"\n',
        'app/src/App.tsx': 'source', 'app/assets/image/harbor.png': 'art',
        'app/assets/fonts/Inter.ttf': 'font', 'app/package-lock.json': '{}',
        'app/vendor/parser.js': 'vendor', 'app/tools/check_prepared_library.mjs': '// fixture',
        'app/assets/raw/prepared-library/catalog.json': 'prepared',
        '.gitignore': 'app/build/\nbuild/\n',
    }
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    for arch in ('aarch64', 'armv7', 'x86_64'):
        for kind in ('debug', 'release'):
            package = repo / f'app/build/{arch}-{kind}/calm-frames-app_{arch}.vpkg'
            package.parent.mkdir(parents=True)
            with tarfile.open(package, 'w') as archive:
                for name, data in [('manifest.toml', (repo / 'app/manifest.toml').read_bytes()),
                                   (f'lib/{arch}/com.amazon.keplerscript.carousel.so', b'fixture')]:
                    member = tarfile.TarInfo(name)
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
    shims = repo / 'shims'
    shims.mkdir()
    (shims / 'node').write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$RELEASE_TEST_LOG"\nexit "${RELEASE_TEST_GATE_STATUS:-0}"\n')
    (shims / 'npm').write_text('''#!/bin/sh
printf '%s\n' "$*" >> "$RELEASE_TEST_LOG"
if [ "${RELEASE_TEST_BUILD_STATUS:-0}" -ne 0 ]; then exit "$RELEASE_TEST_BUILD_STATUS"; fi
if [ "${RELEASE_TEST_NO_OUTPUT:-0}" = 1 ]; then exit 0; fi
kind=; arch=
while [ "$#" -gt 0 ]; do
 case "$1" in --build-type) shift; kind="$1" ;; --target) shift; arch="$1" ;; esac
 shift
done
kind=$(printf '%s' "$kind" | tr '[:upper:]' '[:lower:]')
touch "build/$arch-$kind/calm-frames-app_$arch.vpkg"
''')
    for file in shims.iterdir():
        file.chmod(0o755)
    return repo


def receipt(repo, arch='aarch64', kind='debug'):
    package = repo / f'app/build/{arch}-{kind}/calm-frames-app_{arch}.vpkg'
    paths = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--', 'app']).decode().split('\0')
    result = {'source_commit': 'fixture-only', 'package': {
        'path': str(package.relative_to(repo)), 'sha256': sha(package), 'target': f'{arch} {kind.title()}'},
        'app_source_files': [{'path': p, 'sha256': sha(repo / p)} for p in paths if p]}
    path = repo / f'{arch}-{kind}-receipt.json'
    path.write_text(json.dumps(result))
    return path


def run_release(repo, *args, env=None):
    settings = dict(os.environ, PATH=str(repo / 'shims') + os.pathsep + os.environ['PATH'],
                    RELEASE_TEST_LOG=str(repo / 'commands.log'), RELEASE_PYTHON=sys.executable,
                    DEMO_PIN='')
    settings.update(env or {})
    return subprocess.run(['bash', str(repo / 'scripts/release.sh'), *args], cwd=repo,
                          text=True, capture_output=True, env=settings, timeout=20)


def test_unsafe_tag_cannot_remove_neighbor(project):
    neighbor = project / 'build/precious'
    neighbor.mkdir(parents=True)
    (neighbor / 'keep').write_text('user work')
    result = run_release(project, '--skip-build', '--tag', '../precious')
    assert result.returncode != 0
    assert (neighbor / 'keep').read_text() == 'user work'


def test_missing_package_preserves_existing_output(project):
    out = project / 'build/release/v0.1.0'
    out.mkdir(parents=True)
    (out / 'keep').write_text('user work')
    for path in (project / 'app/build').rglob('*.vpkg'):
        path.unlink()
    result = run_release(project, '--skip-build')
    assert result.returncode != 0
    assert (out / 'keep').read_text() == 'user work'


def test_skip_build_without_provenance_is_refused(project):
    result = run_release(project, '--skip-build')
    assert result.returncode != 0
    assert not (project / 'build/release/v0.1.0').exists()


@pytest.mark.parametrize('changed', ['app/src/App.tsx', 'app/assets/image/harbor.png',
    'app/assets/fonts/Inter.ttf', 'app/manifest.toml', 'app/package-lock.json',
    'app/vendor/parser.js', 'app/assets/raw/prepared-library/catalog.json'])
def test_changed_inputs_fail_even_with_older_timestamp(project, changed):
    proof = receipt(project)
    path = project / changed
    path.write_bytes(path.read_bytes() + (b'\n# changed\n' if changed == 'app/manifest.toml' else b'changed'))
    os.utime(path, (1, 1))
    result = run_release(project, '--skip-build', '--receipt', str(proof))
    assert result.returncode != 0
    assert not (project / 'build/release/v0.1.0').exists()


@pytest.mark.parametrize('change', ['new', 'deleted', 'omitted', 'duplicate', 'package', 'symlink'])
def test_incomplete_receipts_and_substitutions_fail(project, change):
    proof = receipt(project)
    data = json.loads(proof.read_text())
    if change == 'new':
        (project / 'app/src/new.ts').write_text('new build input')
    elif change == 'deleted':
        (project / 'app/assets/fonts/Inter.ttf').unlink()
    elif change == 'omitted':
        data['app_source_files'] = data['app_source_files'][1:]
    elif change == 'duplicate':
        data['app_source_files'].append(data['app_source_files'][0])
    elif change == 'package':
        (project / data['package']['path']).write_text('substituted')
    else:
        font = project / 'app/assets/fonts/Inter.ttf'
        font.unlink()
        font.symlink_to(project / 'app/src/App.tsx')
    proof.write_text(json.dumps(data))
    result = run_release(project, '--skip-build', '--receipt', str(proof))
    assert result.returncode != 0
    assert not (project / 'build/release/v0.1.0').exists()


def test_default_assembles_only_aarch64_debug_and_preserves_evidence_scope(project):
    proof = receipt(project)
    result = run_release(project, '--skip-build', '--receipt', str(proof))
    assert result.returncode == 0, result.stderr
    out = project / 'build/release/v0.1.0'
    assert [p.name for p in out.glob('*.vpkg')] == ['calm-frames-0.1.0-aarch64-debug.vpkg']
    notes = (out / 'NOTES.md').read_text()
    assert 'aarch64 Debug' in notes
    assert 'Native validation is not performed by this script' in notes
    assert 'Fire TV Stick' not in notes
    assert "vega device run-cmd --device VirtualDevice --command 'vmsgr send pkg://io.example.calm.main'" in notes
    assert '--packagePath calm-frames-0.1.0-aarch64-debug.vpkg --buildType Debug' in notes
    assert '--device Simulator' not in notes
    assert '--componentId' not in notes
    assert json.loads((out / 'PREPARATION.json').read_text())['native_validation_performed'] is False
    assert 'Nothing was published' in result.stdout
    assert (project / 'commands.log').read_text().strip().endswith('--packages Debug --arch aarch64 --require-reports')


def test_selected_release_architecture_uses_matching_package_and_notes(project):
    proof = receipt(project, 'x86_64', 'release')
    result = run_release(project, '--skip-build', '--arch', 'x86_64', '--build-type', 'Release', '--receipt', str(proof))
    assert result.returncode == 0, result.stderr
    notes = (project / 'build/release/v0.1.0/NOTES.md').read_text()
    assert 'calm-frames-0.1.0-x86_64.vpkg' in notes
    assert 'aarch64.vpkg' not in notes


@pytest.mark.parametrize('source', ['argument', 'environment'])
def test_reviewer_documents_never_include_supplied_pin(project, source):
    # Deliberately fake sentinel; never inspect a real household or credential.
    sentinel = '8642'
    args = ['--pin', sentinel] if source == 'argument' else []
    settings = {'DEMO_PIN': sentinel} if source == 'environment' else {}
    result = run_release(project, '--skip-build', '--receipt', str(receipt(project)),
                         *args, env=settings)
    assert result.returncode == 0, result.stderr
    out = project / 'build/release/v0.1.0'
    for name in ('NOTES.md', 'PREPARATION.json', 'SHA256SUMS'):
        assert sentinel not in (out / name).read_text()
    assert sentinel not in result.stdout + result.stderr
    notes = (out / 'NOTES.md').read_text()
    assert 'choose and confirm your own four digit PIN' in notes
    assert "owner's PIN and preserve existing household data" in notes


@pytest.mark.parametrize('args', [('--arch', 'mips'), ('--build-type', 'Other'), ('--tag',), ('--pin', '123x'), ('--tag', '$(id)'), ('--tag', '-option')])
def test_invalid_options_stop_before_build(project, args):
    result = run_release(project, *args)
    assert result.returncode != 0
    assert not (project / 'commands.log').exists()


def test_build_uses_selected_target_and_creates_reusable_receipt(project):
    result = run_release(project, '--tag', 'fresh')
    assert result.returncode == 0, result.stderr
    commands = (project / 'commands.log').read_text()
    assert 'exec -- react-native build-kepler --build-type Debug --target aarch64' in commands
    proof = project / 'app/build/aarch64-debug/release-build-receipt.json'
    assert proof.exists()
    reused = run_release(project, '--skip-build', '--tag', 'reuse', '--receipt', str(proof))
    assert reused.returncode == 0, reused.stderr


@pytest.mark.parametrize('settings', [{'RELEASE_TEST_BUILD_STATUS': '4'}, {'RELEASE_TEST_NO_OUTPUT': '1'}, {'RELEASE_TEST_GATE_STATUS': '1'}])
def test_failed_build_or_package_gate_never_assembles(project, settings):
    result = run_release(project, env=settings)
    assert result.returncode != 0
    assert not (project / 'build/release/v0.1.0').exists()


def test_existing_output_is_never_replaced(project):
    proof = receipt(project)
    assert run_release(project, '--skip-build', '--receipt', str(proof)).returncode == 0
    out = project / 'build/release/v0.1.0'
    (out / 'user-notes').write_text('keep')
    result = run_release(project, '--skip-build', '--receipt', str(proof))
    assert result.returncode != 0
    assert (out / 'user-notes').read_text() == 'keep'


def test_ignored_generated_runtime_source_must_also_match_receipt(project):
    proof = receipt(project)
    with (project / '.gitignore').open('a') as stream:
        stream.write('app/src/generated/\n')
    generated = project / 'app/src/generated/polyfill.js'
    generated.parent.mkdir()
    generated.write_text('unrecorded runtime input')
    result = run_release(project, '--skip-build', '--receipt', str(proof))
    assert result.returncode != 0
    assert 'build inputs differ' in result.stderr


@pytest.mark.parametrize('wrong', ['identity', 'architecture'])
def test_package_contents_cannot_be_relabelled_by_receipt(project, wrong):
    package = project / 'app/build/aarch64-debug/calm-frames-app_aarch64.vpkg'
    raw = (project / 'app/manifest.toml').read_bytes()
    if wrong == 'identity':
        raw = raw.replace(b'io.example.calm', b'io.example.other')
    arch = 'x86_64' if wrong == 'architecture' else 'aarch64'
    with tarfile.open(package, 'w') as archive:
        for name, data in [('manifest.toml', raw), (f'lib/{arch}/com.amazon.keplerscript.carousel.so', b'fixture')]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    proof = receipt(project)
    result = run_release(project, '--skip-build', '--receipt', str(proof))
    assert result.returncode != 0
    assert not (project / 'build/release/v0.1.0').exists()


def test_multiple_targets_only_include_explicit_receipts(project):
    first = receipt(project, 'aarch64', 'release')
    second = receipt(project, 'x86_64', 'release')
    result = run_release(project, '--skip-build', '--arch', 'aarch64', '--arch', 'x86_64',
                         '--build-type', 'Release', '--receipt', str(first), '--receipt', str(second))
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in (project / 'build/release/v0.1.0').glob('*.vpkg')) == [
        'calm-frames-0.1.0-aarch64.vpkg', 'calm-frames-0.1.0-x86_64.vpkg']


def test_publication_command_pins_the_prepared_source_commit(project):
    subprocess.run(['git', '-C', str(project), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture'], check=True)
    head = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    result = run_release(project, '--skip-build', '--receipt', str(receipt(project)))
    assert result.returncode == 0, result.stderr
    assert f'--target {head}' in result.stdout
    proof = json.loads((project / 'build/release/v0.1.0/PREPARATION.json').read_text())
    assert proof['source_commit'] == head and proof['app_inputs_committed'] is True


def test_uncommitted_app_preparation_does_not_print_a_publish_command(project):
    result = run_release(project, '--skip-build', '--receipt', str(receipt(project)))
    assert result.returncode == 0, result.stderr
    assert 'gh release create' not in result.stdout
    assert 'Commit the app inputs' in result.stdout


@pytest.mark.parametrize('skip_build', [False, True])
def test_missing_original_reports_block_release_preparation(project, skip_build):
    # Model the real Node gate's legacy-compatible versus strict report result.
    (project / 'shims/node').write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$RELEASE_TEST_LOG"
case " $* " in *" --require-reports "*) echo 'Missing original verification reports' >&2; exit 1 ;; esac
exit 0
''')
    args = ['--skip-build', '--receipt', str(receipt(project))] if skip_build else []
    result = run_release(project, *args)
    assert result.returncode != 0
    assert not (project / 'build/release/v0.1.0').exists()
    calls = (project / 'commands.log').read_text()
    assert '--require-reports' in calls
    assert 'build-kepler' not in calls


@pytest.mark.parametrize('skip_build', [False, True])
def test_ambient_approval_failure_blocks_build_and_package_reuse(project, skip_build):
    (project / 'shims/node').write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$RELEASE_TEST_LOG"
case "$1" in tools/approved_baked_ambient.mjs) echo 'Compiled ambient metadata differs from exact approval' >&2; exit 1 ;; esac
exit 0
''')
    args = ['--skip-build', '--receipt', str(receipt(project))] if skip_build else []
    result = run_release(project, *args)
    assert result.returncode != 0
    assert 'Compiled ambient metadata differs' in result.stderr
    assert (project / 'commands.log').read_text().splitlines() == [
        'tools/approved_baked_ambient.mjs --check']
    assert not (project / 'build/release/v0.1.0').exists()


@pytest.mark.parametrize('skip_build', [False, True])
def test_stale_playback_proof_blocks_build_and_package_reuse(project, skip_build):
    (project / 'shims/node').write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$RELEASE_TEST_LOG"
case "$1" in tools/playback_proof.mjs) echo 'Playback proof differs from approved reports' >&2; exit 1 ;; esac
exit 0
''')
    args = ['--skip-build', '--receipt', str(receipt(project))] if skip_build else []
    result = run_release(project, *args)
    assert result.returncode != 0
    assert 'Playback proof differs' in result.stderr
    calls = (project / 'commands.log').read_text().splitlines()
    assert calls == ['tools/approved_baked_ambient.mjs --check', 'tools/playback_proof.mjs --check']
    assert not (project / 'build/release/v0.1.0').exists()
