"""Build a new local review bundle from explicitly selected, matching evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def repo_path(root, name):
    """Use one unambiguous relative spelling for both disk and ZIP entries."""
    if (not isinstance(name, str) or not name or '\\' in name
            or any(ord(char) < 32 for char in name)
            or name.startswith('/') or ':' in name
            or any(part in {'', '.', '..'} for part in name.split('/'))):
        raise ValueError(f'expected a safe repository-relative path: {name!r}')
    if any(part in {'.git', '.aws', '.codex', '.agents'} for part in PurePosixPath(name).parts):
        raise ValueError(f'private metadata is not a review input: {name}')
    path = root / name
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'path resolves outside repository: {name}')
    return path


def git(root, *args):
    try:
        return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
    except subprocess.CalledProcessError as error:
        raise ValueError('Git provenance could not be verified') from error


def commit_id(root, value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
        raise ValueError('source commit must be a full Git commit SHA')
    return git(root, 'rev-parse', '--verify', f'{value}^{{commit}}')


def check_app_source(root, native_commit, capture_commit, head):
    current_tree = git(root, 'rev-parse', f'{head}:app')
    for label, commit in [('native receipt', native_commit), ('demo capture', capture_commit)]:
        if git(root, 'rev-parse', f'{commit}:app') != current_tree:
            raise ValueError(f'{label} app tree differs from current HEAD; rebuild and recapture')
    if git(root, 'status', '--porcelain=v1', '--untracked-files=all', '--', 'app'):
        raise ValueError('uncommitted app inputs are not represented by the native receipt')
    return current_tree


def expected_digest(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError(f'missing or invalid SHA-256: {label}')
    return value


def recorded_digest(item, key):
    return expected_digest(item.get(key), key)


def check_source_inventory(root, recorded):
    # Match release.sh: tracked inputs plus ignored generated runtime inputs.
    names = set(filter(None, git(root, 'ls-files', '--cached', '--others',
                                '--exclude-standard', '-z', '--', 'app').split('\0')))
    for folder in ('src', 'assets', 'types', 'vendor', 'tools'):
        for path in (root / 'app' / folder).rglob('*'):
            if path.is_symlink():
                raise ValueError(f'symlinked app source: {path}')
            if path.is_file() and '__pycache__' not in path.parts and path.name != '.DS_Store':
                names.add(path.relative_to(root).as_posix())
    measured = []
    for name in sorted(names):
        path = repo_path(root, name)
        if path.resolve() != path.absolute() or not path.is_file():
            raise ValueError(f'missing or symlinked app source: {name}')
        measured.append({'path': name, 'sha256': digest(path)})
    if (not measured or not isinstance(recorded, list)
            or not all(isinstance(item, dict) for item in recorded)
            or sorted(recorded, key=lambda item: item.get('path', '')) != measured):
        raise ValueError('receipt requires a matching complete app source inventory; rebuild')
    return measured


def check_fresh_outputs(paths, root):
    for path in paths:
        if path.exists() or path.is_symlink():
            raise ValueError(f'output already exists: {path.relative_to(root)}')


def verify_zip(path, entries):
    """Check every selected payload and generated metadata entry after writing."""
    with zipfile.ZipFile(path) as archive:
        if (archive.testzip() is not None or len(archive.namelist()) != len(entries)
                or set(archive.namelist()) != set(entries)):
            raise ValueError('ZIP member verification failed')
        for name, expected in entries.items():
            with archive.open(name) as stream:
                checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
            if checksum != expected:
                raise ValueError(f'ZIP payload SHA-256 mismatch: {name}')


def package_review(*, root, native_receipt, demo_manifest, output, receipt, include=()):
    root = Path(root).resolve()
    output_path = repo_path(root, output)
    receipt_path = repo_path(root, receipt)
    if output_path.suffix != '.zip':
        raise ValueError('output must be a ZIP path')
    source_name = str(PurePosixPath(output).with_name(output_path.stem + '-source.zip'))
    source_path = repo_path(root, source_name)
    outputs = [output_path, receipt_path, source_path]
    if len(set(outputs)) != 3:
        raise ValueError('output paths must be distinct')
    check_fresh_outputs(outputs, root)

    selected = {}

    def select(name, expected=None):
        path = repo_path(root, name)
        if path in outputs:
            raise ValueError(f'input and output paths overlap: {name}')
        if not path.is_file():
            raise ValueError(f'missing input: {name}')
        measured = digest(path)
        if expected is not None and measured != expected_digest(expected, name):
            raise ValueError(f'input SHA-256 mismatch: {name}')
        if name in selected and selected[name]['sha256'] != measured:
            raise ValueError(f'input changed while checking: {name}')
        selected[name] = {'path': name, 'bytes': path.stat().st_size, 'sha256': measured}
        return path

    native = json.loads(select(native_receipt).read_text())
    demo = json.loads(select(demo_manifest).read_text())
    head = commit_id(root, git(root, 'rev-parse', 'HEAD'))
    native_commit = commit_id(root, native['source_commit'])
    capture_commit = commit_id(root, demo['capture_source_commit'])
    app_tree = check_app_source(root, native_commit, capture_commit, head)
    for name in git(root, 'ls-tree', '-r', '--name-only', '-z', head).split('\0'):
        if name:
            repo_path(root, name)
    package_hash = expected_digest(native['package']['sha256'], 'native package')
    if expected_digest(demo['capture_package_sha256'], 'demo capture package') != package_hash:
        raise ValueError('demo capture package does not match the native receipt package')
    select(native['package']['path'], package_hash)
    select(demo['video'], expected_digest(demo['sha256'], 'demo video'))
    select(demo['capture_manifest'], recorded_digest(demo, 'capture_manifest_sha256'))
    source_inventory = check_source_inventory(root, native.get('app_source_files'))

    # Only named evidence enters the bundle. There is no directory or log crawl.
    for shot in demo['shots']:
        select(shot['source'], recorded_digest(shot, 'source_sha256'))
    for key in ['capture_files', 'evidence_logs']:
        for item in native.get(key, []):
            select(item['path'], recorded_digest(item, 'sha256'))
    screen_review = native.get('screen_review', {})
    for item in screen_review.get('sources', []):
        select(item['path'], recorded_digest(item, 'sha256'))
    if screen_review.get('contact_sheet'):
        select(screen_review['contact_sheet'], recorded_digest(screen_review, 'sha256'))
    for item in native.get('app_source_files', []):
        if not item['path'].startswith('app/'):
            raise ValueError('recorded app source must be inside app/')
        select(item['path'], expected_digest(item['sha256'], item['path']))
    for name in include:
        select(name)
    reserved = {'REVIEW_README.txt', 'bundle-manifest.json', 'SHA256SUMS'}
    if reserved & set(selected):
        raise ValueError('selected input collides with generated ZIP metadata')

    # All input/path/provenance checks precede creation of any output artifact.
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        with tempfile.TemporaryDirectory(prefix='.review-', dir=output_path.parent) as temporary:
            temp = Path(temporary)
            source = temp / 'source.zip'
            subprocess.run(['git', 'archive', '--format=zip', '--prefix=calm-frames/',
                            '-o', str(source), head], cwd=root, check=True)
            with zipfile.ZipFile(source) as archive:
                if archive.testzip() is not None:
                    raise ValueError('source ZIP CRC verification failed')
            selected[source_name] = {'path': source_name, 'bytes': source.stat().st_size,
                                     'sha256': digest(source)}
            entries = [selected[name] for name in sorted(selected)]
            scope = ('Local review only. Unpublished. Hash and Git checks establish input '
                     'integrity; they do not establish native execution or acceptance.')
            manifest = {'source_archive_commit': head, 'app_tree': app_tree,
                        'native_receipt_source_commit': native_commit,
                        'recorded_app_commit': capture_commit, 'files': entries, 'scope': scope}
            readme = (
                'Calm Frames local review bundle\n\n'
                f'Source archive commit: {head}\n'
                f'Native receipt: {native_receipt}\n'
                f'Demo manifest: {demo_manifest}\n'
                f'Package: {native["package"]["path"]}\n'
                f'Demo: {demo["video"]}\n\n'
                'Native execution was not performed by this packaging tool. Read the supplied '
                'receipts for observations, scope and unresolved limitations. The package and '
                'demo hashes match their supplied receipts, and the recorded app trees match '
                'the archived app tree. Documentation commits may differ.\n\n'
                'SHA256SUMS and bundle-manifest.json identify the selected payload files. '
                'Only explicitly selected evidence is included. This is neither a published '
                'release nor a submitted entry.\n'
            )
            metadata = {
                'REVIEW_README.txt': readme.encode(),
                'bundle-manifest.json': (json.dumps(manifest, indent=2) + '\n').encode(),
                'SHA256SUMS': ''.join(f'{item["sha256"]}  {item["path"]}\n' for item in entries).encode(),
            }
            bundle = temp / 'review.zip'
            with zipfile.ZipFile(bundle, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for item in entries:
                    archive.write(source if item['path'] == source_name else root / item['path'], item['path'])
                for name, data in metadata.items():
                    archive.writestr(name, data)
            checks = {item['path']: item['sha256'] for item in entries}
            checks.update({name: hashlib.sha256(data).hexdigest() for name, data in metadata.items()})
            verify_zip(bundle, checks)
            if git(root, 'rev-parse', 'HEAD') != head:
                raise ValueError('HEAD changed during packaging; retry with a stable source commit')
            check_app_source(root, native_commit, capture_commit, head)
            check_source_inventory(root, source_inventory)
            result = {'bundle': output, 'sha256': digest(bundle), 'bytes': bundle.stat().st_size,
                      'payload_files': len(entries), 'source_archive': source_name,
                      'source_archive_sha256': digest(source), 'source_archive_commit': head,
                      'app_tree': app_tree, 'native_receipt_source_commit': native_commit,
                      'recorded_app_commit': capture_commit, 'package_sha256': package_hash,
                      'video_sha256': demo['sha256'], 'native_receipt': native_receipt,
                      'demo_manifest': demo_manifest,
                      'verification': 'ZIP CRC and every payload and metadata SHA-256 verified after writing',
                      'scope': scope, 'published': False}
            receipt_file = temp / 'receipt.json'
            receipt_file.write_text(json.dumps(result, indent=2) + '\n')
            # Hard links create fresh names atomically and never replace an old artifact.
            for staged, target in [(source, source_path), (bundle, output_path), (receipt_file, receipt_path)]:
                os.link(staged, target)
                created.append(target)
            return result
    except Exception:
        for path in created:
            path.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-receipt', required=True)
    parser.add_argument('--demo-manifest', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--include', action='append', default=[], help='Explicit repository-relative review file; repeatable')
    args = parser.parse_args()
    try:
        result = package_review(root=ROOT, **vars(args))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, f'Review bundle refused: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
