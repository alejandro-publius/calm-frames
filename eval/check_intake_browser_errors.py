"""Exercise actual caregiver HTTP/browser errors with a private benign fixture.

No signer, household data, native device, external service or video playback.
Only the unreadable-response and disconnected-network cases inject transport
failures; analysis, report, cancellation and damaged-record checks use the server.
Run with system Playwright and a separately specified normal pipeline Python.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_browser(output: Path, pipeline_python: Path) -> dict:
    from playwright.sync_api import expect, sync_playwright

    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    jobs = output / 'private-imports'
    sample = output / 'steady-fixture.mp4'
    subprocess.run([
        'ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=0x6faea8:s=160x90:r=12:d=1',
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=mono:sample_rate=48000',
        '-shortest', '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-movflags', '+faststart', str(sample),
    ], check=True, timeout=20, capture_output=True)
    original_hash = hashlib.sha256(sample.read_bytes()).hexdigest()
    with socket.socket() as reserved:
        reserved.bind(('127.0.0.1', 0))
        port = reserved.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT / 'flashmap/src')]))
    server = subprocess.Popen([
        str(pipeline_python), '-m', 'pipeline.local_intake', 'serve', '--root', str(jobs), '--port', str(port),
    ], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    checks: dict = {}
    errors: list[str] = []
    external: list[str] = []

    def record(name, operation):
        try:
            operation()
            checks[name] = {'passed': True}
        except AssertionError as error:
            # Assertion details may contain private temporary paths; retain only the check name.
            checks[name] = {'passed': False, 'error': type(error).__name__}
        (output / 'progress-checks.json').write_text(json.dumps(checks, indent=2) + '\n')

    try:
        for _ in range(100):
            assert server.poll() is None, 'Local server stopped'
            try:
                with urllib.request.urlopen(origin + '/jobs', timeout=1) as response:
                    assert response.status == 200
                break
            except OSError:
                time.sleep(.05)
        else:
            raise AssertionError('Local server did not start')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1100, 'height': 900}, reduced_motion='reduce', accept_downloads=True)
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: external.append(r.url) if r.url.startswith('http') and not r.url.startswith(origin + '/') else None)
            page.on('dialog', lambda dialog: dialog.accept())
            page.goto(origin)
            notice = page.locator('#notice')
            analyze = page.get_by_role('button', name='Analyze the full video')
            page.get_by_label('Video title').fill('Fictional caregiver example')
            page.get_by_label('Choose your video').set_input_files(sample)
            assert not page.locator('#upload').evaluate('(form) => form.checkValidity()')
            assert page.request.get(origin + '/jobs').json()['jobs'] == []
            checks['permission_required_without_sending_file'] = {'passed': True}
            page.get_by_role('checkbox').check()
            page.get_by_label('Choose your video').set_input_files({'name': 'unsupported.mov', 'mimeType': 'video/quicktime', 'buffer': b'not media'})
            analyze.click()
            expect(notice).to_contain_text('MP4')
            assert page.request.get(origin + '/jobs').json()['jobs'] == []
            checks['unsupported_extension_refused_without_job'] = {'passed': True}
            page.get_by_label('Choose your video').set_input_files({'name': 'broken.mp4', 'mimeType': 'video/mp4', 'buffer': b'not an MP4'})
            analyze.click()
            page.get_by_role('button', name='Analyze again').wait_for(timeout=15000)
            record('analysis_failure_announced', lambda: expect(notice).to_contain_text('Import stopped', timeout=1500))
            page.screenshot(path=output / 'analysis-error.png', full_page=True)
            page.get_by_role('button', name='Remove local import').click()
            expect(page.locator('article')).to_have_count(0)
            assert hashlib.sha256(sample.read_bytes()).hexdigest() == original_hash
            checks['explicit_removal_preserves_original'] = {'passed': True}

            page.get_by_label('Choose your video').set_input_files(sample)
            page.get_by_role('checkbox').check()
            analyze.click()
            save = page.get_by_role('button', name='Save caregiver review (JSON)')
            save.wait_for(timeout=45000)
            expect(notice).to_contain_text('Analysis complete')
            page.get_by_role('button', name='Approve review and prepare').click()
            page.get_by_role('button', name='Retry preparation with configured signer').wait_for()
            record('missing_signer_announced', lambda: expect(notice).to_contain_text('No authorized signer', timeout=1500))
            page.screenshot(path=output / 'signer-blocked.png', full_page=True)
            with page.expect_download() as download:
                save.click()
            download.value.save_as(output / 'caregiver-review.json')
            report = json.loads((output / 'caregiver-review.json').read_text())
            assert not report['tv_playback_authorized']
            assert report['source']['sha256'] == original_hash
            assert report['analysis']['frame_count'] == 12
            checks['blocked_preparation_retains_downloadable_analysis'] = {'passed': True}

            job = page.request.get(origin + '/jobs').json()['jobs'][0]
            map_file = jobs / job['id'] / 'runs' / job['review']['analysis_run'] / 'wcag.json'
            saved_map = map_file.read_bytes()
            map_file.write_bytes(b'changed fixture')
            save.click()
            record('changed_report_has_reachable_recovery_guidance', lambda: expect(notice).to_contain_text('Remove this local import', timeout=1500))
            assert page.request.get(origin + '/jobs/' + job['id'] + '/review').status == 400
            map_file.write_bytes(saved_map)
            assert page.request.get(origin + '/jobs/' + job['id'] + '/review').json() == report
            checks['changed_map_refused_original_report_restored'] = {'passed': True}

            report_url = origin + '/jobs/' + job['id'] + '/review'
            page.route(report_url, lambda route: route.fulfill(status=503, content_type='text/html', body='<h1>Unavailable</h1>'))
            save.click()
            record('unreadable_response_has_actionable_guidance', lambda: expect(notice).to_contain_text('unreadable response', timeout=1500))
            page.unroute(report_url)
            page.route(origin + '/jobs', lambda route: route.abort('connectionfailed'))
            expect(notice).to_contain_text('Local connection lost', timeout=5000)
            expect(analyze).to_be_disabled()
            expect(save).to_be_visible()
            page.unroute(origin + '/jobs')
            expect(notice).to_contain_text('Local connection restored', timeout=5000)
            expect(analyze).to_be_enabled()
            checks['disconnect_preserves_review_and_recovers'] = {'passed': True}

            # Copy only our fictional fixture, then damage its saved package snapshot.
            bad_id = 'f' * 32
            bad_path = jobs / bad_id
            shutil.copytree(jobs / job['id'], bad_path)
            damaged = dict(job, id=bad_id, title='Damaged fixture', status='package_review', package=None)
            (bad_path / 'job.json').write_text(json.dumps(damaged))
            page.get_by_role('heading', name='Unreadable import').wait_for(timeout=5000)
            expect(save).to_have_count(1)
            assert page.request.get(report_url).json() == report
            checks['damaged_package_isolated_from_intact_report'] = {'passed': True}
            for width, height in ((1100, 900), (390, 844)):
                page.set_viewport_size({'width': width, 'height': height})
                save.focus()
                page.keyboard.press('Tab')
                page.keyboard.press('Shift+Tab')
                assert save.evaluate('(button) => button === document.activeElement')
                assert save.evaluate('(button) => getComputedStyle(button).outlineStyle') != 'none'
                assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=output / f'errors-{width}.png', full_page=True)
            assert page.locator('video,audio,iframe').count() == 0
            assert page.evaluate('() => document.getAnimations().length') == 0
            assert not errors and not external
            checks['responsive_focus_reduced_motion_no_external_requests'] = {'passed': True}
            browser.close()
    finally:
        server.send_signal(signal.SIGINT)
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=3)
    result = {
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'tested_files': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                         for name in ('pipeline/local_intake.py', 'pipeline/local_intake.html', 'eval/check_intake_browser_errors.py')},
        'checks': checks, 'page_errors': errors, 'external_requests': external,
        'fixture': {'kind': 'generated steady color and silent audio, never played', 'sha256': original_hash},
        'native_or_signer_acceptance': False,
    }
    (output / 'browser-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({name: value['passed'] for name, value in checks.items()}))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pipeline-python', type=Path, required=True)
    args = parser.parse_args()
    # Keep the virtual-environment entry point; resolving its symlink loses dependencies.
    receipt = check_browser(args.output.resolve(), args.pipeline_python.absolute())
    raise SystemExit(0 if all(check['passed'] for check in receipt['checks'].values()) else 1)
