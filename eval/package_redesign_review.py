"""Package the October 10 reviewed artifacts without publishing anything."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build'
ZIP = OUT / 'calm-frames-redesign-review-2026-10-10.zip'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    source = OUT / 'calm-frames-redesign-source.zip'
    subprocess.run(['git', 'archive', '--format=zip', '--prefix=calm-frames/', '-o', str(source), source_commit], cwd=ROOT, check=True)
    native = json.loads((ROOT / 'results/redesign_validation_2026-10-10.json').read_text())
    demo = json.loads((ROOT / 'results/redesign_demo_manifest_2026-10-10.json').read_text())
    files = {
        str(source.relative_to(ROOT)), native['package']['path'], demo['video'],
        'build/submission-redesign/Calm-Frames-demo-English.srt',
        'build/submission-redesign/demo-contact.png',
        'build/submission-redesign/native-screen-review.png',
        'README.md', 'LICENSE', 'CLAUDE.md',
    }
    docs = ['COMPLETION_CHECKLIST', 'SUBMISSION', 'VIDEO_SCRIPT', 'SHOT_MANIFEST',
            'ENVIRONMENT', 'FEEDBACK', 'FRICTION_LOG', 'SECURITY', 'OPEN_SOURCE_PR', 'STATUS']
    files.update('docs/' + name + '.md' for name in docs)
    for directory in ['docs/brand', 'docs/design', 'docs/upstream-pr']:
        files.update(str(p.relative_to(ROOT)) for p in (ROOT / directory).rglob('*') if p.is_file())
    receipts = ['redesign_validation_2026-10-10', 'approved_design_2026-10-10',
                'redesign_demo_manifest_2026-10-10', 'redesign_video_check',
                'redesign_video_check.map', 'redesign_video_check_broadcast',
                'redesign_video_check_broadcast.map', 'redesign_brand_broadcast',
                'claude_redesign_2026-10-10', 'claude_final_reviews_2026-10-10',
                'recovery_review_2026-10-10', 'native_validation_2026-10-10',
                'aws_deploy_2026-10-09', 'upstream_review_2026-10-10', 'audit']
    files.update('results/' + name + '.json' for name in receipts)
    files.update(item['source'] for item in demo['shots'])
    files.update(item['path'] for item in native['capture_files'])
    files.update(item['path'] for item in native['screen_review']['sources'])
    files.update(item['path'] for item in native['evidence_logs'])
    entries = []
    for name in sorted(files):
        path = ROOT / name
        assert path.is_file(), name
        entries.append({'path': name, 'bytes': path.stat().st_size, 'sha256': digest(path)})
    assert digest(ROOT / native['package']['path']) == native['package']['sha256']
    assert digest(ROOT / demo['video']) == demo['sha256']
    manifest = {'source_archive_commit': source_commit, 'tested_app_commit': native['source_commit'],
                'recorded_app_commit': demo['capture_source_commit'], 'files': entries,
                'scope': 'Local review only. Unpublished. Security and redistribution review remain open.'}
    readme = '''Calm Frames approved design review, October 10, 2026

Start with docs/COMPLETION_CHECKLIST.md and docs/SUBMISSION.md.
The aarch64 Debug package is for the Apple Silicon Vega Virtual Device.
The 156-second English demo and SRT are in build/submission-redesign/.
Source archive, current docs, branding and exact evidence are included.
SHA256SUMS and bundle-manifest.json identify every payload file.

Demo captures use cba1a29. Final app 73fbbed changes only one unavailable-title
sentence, separately reinstalled and observed. See the native receipt.
The .logs directory contains selected evidence, not all development logs.
Raw Claude authentication logs and unrelated/account-screen captures are excluded.

This is a local review artifact. It is not a published release or submitted entry.
Read the unresolved security and Amazon polyfill redistribution items before
publishing source. Personal entrant fields and public submission URLs are pending.
'''
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for item in entries:
            z.write(ROOT / item['path'], item['path'])
        z.writestr('REVIEW_README.txt', readme)
        z.writestr('bundle-manifest.json', json.dumps(manifest, indent=2) + '\n')
        z.writestr('SHA256SUMS', ''.join(f"{item['sha256']}  {item['path']}\n" for item in entries))
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        for item in entries:
            assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256'], item['path']
    receipt = {'bundle': str(ZIP.relative_to(ROOT)), 'sha256': digest(ZIP),
               'bytes': ZIP.stat().st_size, 'payload_files': len(entries),
               'source_archive_commit': source_commit, 'tested_app_commit': native['source_commit'],
               'package_sha256': native['package']['sha256'], 'video_sha256': demo['sha256'],
               'verification': 'ZIP CRC and every payload SHA-256 verified after writing',
               'published': False}
    (ROOT / 'results/redesign_review_bundle_2026-10-10.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
