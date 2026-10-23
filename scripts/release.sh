#!/usr/bin/env bash
# Prepare selected Vega packages locally. Nothing is published.
# Defaults: aarch64 Debug for the Apple Silicon Vega Virtual Device.
#   make release RELEASE_ARGS="--tag review-polish"
#   make release RELEASE_ARGS="--skip-build --receipt results/redesign_validation_2026-10-10.json"
#   make release RELEASE_ARGS="--all-architectures --build-type Release"
# An existing output directory is preserved; choose a new --tag for another run.
set -eu
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${RELEASE_PYTHON:-$REPO/.venv/bin/python}"
[ -x "$PYTHON" ] || PYTHON=python3
exec "$PYTHON" - "$REPO" "$@" <<'PY'
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib

REPO = Path(sys.argv[1]).resolve()
ARCHES = ('armv7', 'aarch64', 'x86_64')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def command(args, **kwargs):
    return subprocess.run(args, cwd=REPO / 'app', check=True, **kwargs)


def digest(path):
    require(path.is_file() and not path.is_symlink(), f'missing or nonregular file: {path}')
    require(path.resolve() == path.absolute(), f'symlinked input path: {path}')
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def source_inventory():
    # Include all recorded app inputs, plus ignored generated runtime inputs.
    # This covers artwork, fonts, vendor code, build configuration and the
    # prepared library, rather than treating app/src timestamps as provenance.
    tracked = subprocess.check_output(['git', 'ls-files', '--cached', '--others',
        '--exclude-standard', '-z', '--', 'app'], cwd=REPO).decode().split('\0')
    names = set(filter(None, tracked))
    for folder in ('src', 'assets', 'types', 'vendor', 'tools'):
        root = REPO / 'app' / folder
        for path in root.rglob('*'):
            if path.is_symlink():
                raise ValueError(f'symlinked build input: {path}')
            if path.is_file() and '__pycache__' not in path.parts and path.name != '.DS_Store':
                names.add(path.relative_to(REPO).as_posix())
    require(names, 'no app source inventory was found')
    return [{'path': name, 'sha256': digest(REPO / name)} for name in sorted(names)]


def package_path(arch, kind):
    return REPO / f'app/build/{arch}-{kind.lower()}/calm-frames-app_{arch}.vpkg'


def check_receipt(path, package, arch, kind, sources):
    data = json.loads(path.read_text())
    entry = data.get('package', {})
    require(entry.get('path') == package.relative_to(REPO).as_posix(),
            f'receipt package path does not match {arch} {kind}: {path}')
    require(entry.get('target') == f'{arch} {kind}', f'receipt target does not match: {path}')
    require(entry.get('sha256') == digest(package), f'package hash differs from receipt: {path}')
    recorded = data.get('app_source_files')
    require(isinstance(recorded, list) and all(isinstance(item, dict) for item in recorded),
            f'receipt has no complete app source inventory: {path}')
    require(sorted(recorded, key=lambda item: item.get('path', '')) == sources,
            f'build inputs differ from receipt (including added, deleted or generated files): {path}; rebuild')
    return data


def source_state():
    head = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD^{commit}'],
                          cwd=REPO, text=True, capture_output=True)
    changed = subprocess.check_output(['git', 'status', '--porcelain=v1',
        '--untracked-files=all', '--', 'app'], cwd=REPO, text=True)
    return {'source_commit': head.stdout.strip() if head.returncode == 0 else None,
            'app_inputs_committed': head.returncode == 0 and not changed.strip()}


def inspect_package(package, arch, manifest):
    require(package.stat().st_size > 0, f'empty package: {package}')
    raw = subprocess.check_output(['tar', '-xOf', str(package), 'manifest.toml'], timeout=30)
    require(len(raw) <= 1024 * 1024, 'packaged manifest is too large')
    packed = tomllib.loads(raw.decode())
    for key in ('id', 'version'):
        require(packed.get('package', {}).get(key) == manifest['package'][key],
                f'packaged {key} differs from app/manifest.toml: {package}')
    require(packed.get('os', {}).get('version') == manifest['os']['version'],
            f'packaged OS requirements differ from app/manifest.toml: {package}')
    native = subprocess.check_output(['tar', '-xOf', str(package),
        f'lib/{arch}/com.amazon.keplerscript.carousel.so'], timeout=30)
    require(native, f'package is missing its {arch} native runtime')


def main():
    parser = argparse.ArgumentParser(description='Prepare checked packages locally; never publish or claim native validation.')
    parser.add_argument('--skip-build', action='store_true', help='require matching --receipt files instead of rebuilding')
    parser.add_argument('--arch', action='append', choices=ARCHES, help='repeat to select packages; default aarch64')
    parser.add_argument('--all-architectures', action='store_true')
    parser.add_argument('--build-type', choices=('Debug', 'Release'), default='Debug')
    parser.add_argument('--receipt', action='append', type=Path, default=[], help='package and complete app_source_files hash receipt; repeat for multiple targets')
    parser.add_argument('--tag')
    parser.add_argument('--pin', default='', help='deprecated compatibility option; ignored and never written to reviewer documents; do not supply a household PIN')
    args = parser.parse_args(sys.argv[2:])
    require(not (args.arch and args.all_architectures), 'choose --arch or --all-architectures')
    arches = list(ARCHES) if args.all_architectures else list(dict.fromkeys(args.arch or ['aarch64']))
    require(not args.pin or re.fullmatch(r'[0-9]{4}', args.pin), '--pin must contain exactly four digits')
    manifest = tomllib.loads((REPO / 'app/manifest.toml').read_text())
    version = manifest['package']['version']
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', version), 'package version is not a safe filename')
    tag = args.tag or f'v{version}'
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', tag) and '..' not in tag,
            '--tag must be a simple name containing letters, digits, dots, underscores or hyphens')
    parent = REPO / 'build/release'
    out = parent / tag
    require(parent.resolve() == parent, 'release output parent must not be symlinked')
    require(not out.exists() and not out.is_symlink(), f'output already exists; choose a new --tag: {out}')
    require(not args.skip_build or args.receipt, '--skip-build requires --receipt with matching package and source hashes')
    require(args.skip_build or not args.receipt, '--receipt is only used with --skip-build')
    sources = source_inventory()
    packages = [package_path(arch, args.build_type) for arch in arches]
    receipt_paths = []
    # Direct npm exec below bypasses npm's prebuild hook. Reused packages also
    # need the compiled registry to match the exact approved ambient reports.
    command(['node', 'tools/approved_baked_ambient.mjs', '--check'])
    command(['node', 'tools/playback_proof.mjs', '--check'])
    if args.skip_build:
        require(len(args.receipt) == len(arches), 'supply one --receipt per selected --arch, in the same order')
        for arch, package, proof in zip(arches, packages, args.receipt):
            check_receipt(proof, package, arch, args.build_type, sources)
            receipt_paths.append(str(proof.resolve()))
    else:
        print(f'Building {", ".join(arches)} {args.build_type}. Native validation remains a separate step.', flush=True)
        # Use the documented target option directly. The existing npm
        # postbuild hook intentionally checks all three architectures.
        before_packages = {str(path): path.stat() if path.exists() else None for path in packages}
        command(['node', 'tools/check_native_inputs.mjs'])
        command(['node', 'tools/check_prepared_library.mjs', '--require-reports'])
        for arch in arches:
            command(['npm', 'exec', '--', 'react-native', 'build-kepler',
                     '--build-type', args.build_type, '--target', arch])
        after = source_inventory()
        # The SDK regenerates manifest module declarations during a build.
        require([x for x in sources if x['path'] != 'app/manifest.toml'] ==
                [x for x in after if x['path'] != 'app/manifest.toml'],
                'app inputs changed while building; review the change and rebuild')
        sources = after
        manifest = tomllib.loads((REPO / 'app/manifest.toml').read_text())
        require(manifest['package']['version'] == version, 'app version changed while building')
        for package in packages:
            before = before_packages[str(package)]
            require(package.is_file(), f'build did not produce a package: {package}')
            current = package.stat()
            identity = lambda stat: (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            require(before is None or identity(current) != identity(before),
                    f'build did not produce a fresh package: {package}')
    # Existing and newly built packages both pass delivery and identity gates.
    checked = []
    for arch, package in zip(arches, packages):
        package_hash = digest(package)
        inspect_package(package, arch, manifest)
        command(['node', 'tools/check_prepared_library.mjs', '--packages', args.build_type, '--arch', arch, '--require-reports'])
        require(digest(package) == package_hash, 'package changed during validation')
        checked.append({'path': package.relative_to(REPO).as_posix(), 'sha256': package_hash,
                        'target': f'{arch} {args.build_type}'})
    require(source_inventory() == sources, 'app inputs changed during package validation')
    source = source_state()
    if not args.skip_build:
        for package, item in zip(packages, checked):
            proof = package.parent / 'release-build-receipt.json'
            require(not proof.is_symlink(), 'build receipt must not be symlinked')
            proof.write_text(json.dumps({**source, 'package': item, 'app_source_files': sources,
                'native_validation_performed': False,
                'scope': 'Build and package preparation only. No simulator execution or recording.'}, indent=2) + '\n')
            receipt_paths.append(str(proof))
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.prepare-', dir=parent))
    try:
        names = []
        for arch, package, item in zip(arches, packages, checked):
            suffix = '-debug' if args.build_type == 'Debug' else ''
            name = f'calm-frames-{version}-{arch}{suffix}.vpkg'
            shutil.copyfile(package, stage / name)
            require(digest(stage / name) == item['sha256'], 'package changed during copying')
            names.append(name)
        require(source_inventory() == sources, 'app inputs changed during assembly')
        (stage / 'SHA256SUMS').write_text(''.join(f'{digest(stage / name)}  {name}\n' for name in names))
        preparation = {**source, 'generated_utc': datetime.now(timezone.utc).isoformat(),
            'packages': checked, 'source_receipts': receipt_paths, 'app_source_files': sources,
            'native_validation_performed': False, 'published': False}
        (stage / 'PREPARATION.json').write_text(json.dumps(preparation, indent=2) + '\n')
        table = '\n'.join(f'| {name} | {arch} {args.build_type} |' for arch, name in zip(arches, names))
        instructions = '\n'.join(f'    vega device install-app --device VirtualDevice --packagePath {name} --buildType {args.build_type}' for name in names)
        (stage / 'NOTES.md').write_text(f'''# Calm Frames {tag}

A calmer way to watch.

An accessibility prototype with analyzed, signed maps and prepared covered
renditions. Harbor's benign practice holds use clearly labelled synthetic
intervals. Not a medical device. It reduces exposure to flashing above published
limits in the videos it plays.

## Packages

| File | Target |
|---|---|
{table}

These are {args.build_type} builds for Vega OS {manifest['os']['version']['target']}.
Native validation is not performed by this script. Observe the exact package
on its matching Vega Virtual Device before describing it as demonstrated.
PREPARATION.json records build-input and package hashes; it is not playback evidence.
Every referenced original preparation report passed the strict delivery gate.
Debug builds retain logs. Release builds strip console.log.

## Install on the matching simulator

Use aarch64 for Apple Silicon and x86_64 for an Intel simulator. No physical
Fire TV is required. Install only the package matching the connected simulator.

    source ~/vega/env
    # Start only if the virtual device is stopped; keep it alive after this shell.
    nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
    vega device is-connected --device VirtualDevice
{instructions}
    vega device run-cmd --device VirtualDevice --command 'vmsgr send pkg://{manifest['package']['id']}.main'

## Parent PIN

On a fresh installation, choose and confirm your own four digit PIN during
onboarding. Only a salted hash is stored. On a configured simulator, use its
owner's PIN and preserve existing household data.

## Verify and review

    shasum -a 256 -c SHA256SUMS

Read LICENSE, NOTICE and docs/AMAZON_SAMPLE_LICENSE_REVIEW.md in the repository.
Dependency review and Amazon sample redistribution terms remain separate
publication checks. This preparation step does not waive them.
''')
        # Never delete an existing release, including on a failed validation.
        # Reserve a new directory exclusively before moving staged files into it.
        out.mkdir()
        for item in stage.iterdir():
            item.rename(out / item.name)
        stage.rmdir()
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f'Ready for local review in {out}')
    print('Native playback, recording and submission are not performed here.')
    if not source['app_inputs_committed']:
        print('Commit the app inputs and recheck this package with --skip-build and a new --tag before publication.')
        print('Nothing was published. No GitHub API call was made.')
        return
    require(source_state() == source, 'source commit changed during preparation; recheck before publication')
    print('The following publication command is printed only; review first:')
    print(shlex.join(['gh', 'release', 'create', tag, '--target', source['source_commit'], *[str(out / name) for name in names],
        str(out / 'SHA256SUMS'), str(out / 'PREPARATION.json'), '--repo',
        'alejandro-publius/calm-frames', '--title', f'Calm Frames {tag}', '--notes-file', str(out / 'NOTES.md')]))
    print('Nothing was published. No GitHub API call was made.')


try:
    main()
except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
    print(f'release: {error}', file=sys.stderr)
    sys.exit(1)
PY
