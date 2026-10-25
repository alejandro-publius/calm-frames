"""Record the real local caregiver workflow using the existing licensed Forest rendition.

Requires installed Playwright, Chromium and ffmpeg. The pipeline Python must have
its normal dependencies. No signer, playback, native capture, network source,
art generation or speech service is used. All output stays in a new private folder.
"""
from __future__ import annotations

import argparse
import base64
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
FOREST = Path('app/assets/raw/prepared-library/77d43b664cb49d6caf82887c70d13df9d98eb32add815abd5d41320ca316503f/titles/63432b83ef15c0614d1fd80b4a899d4227a6703a0b847cb194f7ba6725b8454c/wcag.mp4')
EXPECTED = '38dc13a36048c229ebc1b5558dd3b52b7f99b9de1ae71d2d03dddf8259629c98'
CREDIT = 'NPS: G Litten. Recorded public-domain source; no NPS endorsement implied.'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n')


def capture(output: Path, pipeline_python: Path) -> None:
    from playwright.sync_api import sync_playwright

    output = output.resolve()
    assert not output.exists(), 'Use a new output directory; preserve earlier captures.'
    assert sha(ROOT / FOREST) == EXPECTED, 'The reviewed example input changed.'
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip(), 'Commit source before capture.'
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    output.mkdir(parents=True, mode=0o700)
    private = output / 'private'
    private.mkdir(mode=0o700)
    inputs = private / 'forest-prepared-review.mp4'
    shutil.copyfile(ROOT / FOREST, inputs)
    jobs = private / 'imports'
    frames = private / 'frames'
    frames.mkdir()
    with socket.socket() as reserved:
        reserved.bind(('127.0.0.1', 0))
        port = reserved.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT / 'flashmap/src')]))
    server = subprocess.Popen(
        [str(pipeline_python), '-m', 'pipeline.local_intake', 'serve', '--root', str(jobs), '--port', str(port)],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    pictures: list[dict] = []
    events: list[dict] = []
    checks: dict = {}
    t0 = time.monotonic()

    def mark(name: str) -> None:
        events.append({'event': name, 'elapsed_s': round(time.monotonic() - t0, 3)})

    try:
        for _ in range(100):
            assert server.poll() is None, 'Local server stopped.'
            try:
                with urllib.request.urlopen(origin + '/jobs', timeout=1) as response:
                    assert response.status == 200
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError('Local server did not become ready.')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1100, 'height': 850}, reduced_motion='reduce', accept_downloads=True)
            page = context.new_page()
            errors: list[str] = []
            external: list[str] = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: external.append(r.url) if r.url.startswith('http') and not r.url.startswith(origin + '/') else None)
            page.goto(origin)
            page.get_by_role('heading', name='Add a video').wait_for()
            cdp = context.new_cdp_session(page)
            t0 = time.monotonic()

            def frame(event: dict) -> None:
                name = f'{len(pictures):05d}.jpg'
                data = base64.b64decode(event['data'])
                (frames / name).write_bytes(data)
                pictures.append({'file': name, 'elapsed_s': time.monotonic() - t0, 'sha256': hashlib.sha256(data).hexdigest()})
                cdp.send('Page.screencastFrameAck', {'sessionId': event['sessionId']})

            cdp.on('Page.screencastFrame', frame)
            cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 90, 'maxWidth': 1100, 'maxHeight': 850, 'everyNthFrame': 1})
            page.wait_for_timeout(700)
            mark('select_existing_licensed_rendition')
            page.get_by_label('Video title').fill('Forest creek (licensed review example)')
            page.get_by_label('Choose your video').set_input_files(inputs)
            assert not page.locator('#upload').evaluate('(form) => form.checkValidity()')
            page.get_by_role('checkbox').check()
            page.get_by_role('button', name='Analyze the full video').focus()
            page.wait_for_timeout(700)
            mark('submit_real_analysis')
            page.keyboard.press('Enter')
            save = page.get_by_role('button', name='Save caregiver review (JSON)')
            save.wait_for(timeout=120000)
            mark('complete_review_visible')
            data = page.request.get(origin + '/jobs').json()
            job = data['jobs'][0]
            assert job['status'] == 'review' and job['review']['analysis_complete'] is True
            assert job['review']['source_sha256'] == EXPECTED
            assert job['review']['frame_count'] == 360 and job['review']['duration_ms'] == 12000
            assert data['signer_configured'] is False
            selector = page.get_by_label('Viewing preset')
            selector.focus()
            for preset in ('wcag', 'broadcast', 'extra-cautious'):
                selector.select_option(preset)
                mark('review_preset_' + preset)
                page.wait_for_timeout(1100)
            page.get_by_text('Analysis identity and limits', exact=True).click()
            page.wait_for_timeout(1000)
            # Exercise actual keyboard travel to the report download.
            page.get_by_label('Video title').focus()
            for _ in range(20):
                if save.evaluate('(b) => b === document.activeElement'):
                    break
                page.keyboard.press('Tab')
            assert save.evaluate('(b) => b === document.activeElement')
            assert save.evaluate('(b) => getComputedStyle(b).outlineStyle') != 'none'
            with page.expect_download() as downloading:
                page.keyboard.press('Enter')
            downloading.value.save_as(output / 'caregiver-review.json')
            report = json.loads((output / 'caregiver-review.json').read_text())
            assert report['source']['sha256'] == EXPECTED and report['tv_playback_authorized'] is False
            assert report['processing_permission_confirmed'] is True and report['permission_verified_by_application'] is False
            mark('saved_exact_review_json')
            page.wait_for_timeout(1400)
            page.screenshot(path=output / 'desktop-review.png', full_page=True)
            assert page.locator('video,audio,iframe').count() == 0
            assert page.evaluate('document.getAnimations().length') == 0
            cdp.send('Page.stopScreencast')
            cdp.remove_listener('Page.screencastFrame', frame)
            stop = time.monotonic() - t0
            write(private / 'raw-recording.json', {
                'source_commit': source, 'capture_tool_sha256': sha(Path(__file__)),
                'events': events, 'stop_elapsed_s': stop, 'frames': pictures,
                'scope': 'Actual local caregiver browser; no media playback or native capture',
            })
            # Exercise the newly fixed nested-record failure outside the demonstration take.
            damaged = jobs / ('d' * 32)
            shutil.copytree(jobs / job['id'], damaged)
            bad = json.loads((damaged / 'job.json').read_text())
            bad['id'] = damaged.name
            bad['review']['presets'].pop('extra-cautious')
            write(damaged / 'job.json', bad)
            page.get_by_role('heading', name='Unreadable import').wait_for(timeout=6000)
            assert page.get_by_role('button', name='Save caregiver review (JSON)').count() == 1
            assert page.request.get(origin + f'/jobs/{damaged.name}/review').status == 400
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=output / 'narrow-isolated-review.png', full_page=True)
            remove = page.get_by_role('article').filter(has=page.get_by_role('heading', name='Unreadable import')).get_by_role('button', name='Remove local import')
            remove.focus()
            page.on('dialog', lambda dialog: dialog.accept())
            remove.press('Enter')
            page.get_by_role('heading', name='Unreadable import').wait_for(state='detached')
            assert not damaged.exists() and sha(jobs / job['id'] / 'original.mp4') == EXPECTED
            assert not errors and not external
            checks = {'permission_required': True, 'real_file_analysis_frames': 360, 'duration_ms': 12000, 'three_presets_reviewed': True, 'keyboard_report_download': True, 'visible_focus': True, 'nested_corruption_isolated': True, 'invalid_report_http_status': 400, 'keyboard_remove_only_corrupt_copy': True, 'source_preserved': True, 'narrow_horizontal_overflow': False, 'reduced_motion_emulated': True, 'active_animations': 0, 'media_elements': 0, 'page_errors': errors, 'external_requests': external, 'native_fire_tv': False}
            checks['browser_version'] = browser.version
            write(output / 'browser-checks.json', {'source_commit': source, **checks})
            browser.close()
        assert pictures and stop > pictures[-1]['elapsed_s']
        # Preserve real waits between browser frames. This is browser IPC timing,
        # never a decoder/compositor timing measurement or moving-nature footage.
        listing = private / 'frames.ffconcat'
        lines = ['ffconcat version 1.0']
        for i, picture in enumerate(pictures):
            end = pictures[i + 1]['elapsed_s'] if i + 1 < len(pictures) else stop
            lines += [f"file 'frames/{picture['file']}'", f"duration {max(0.001, end - picture['elapsed_s']):.6f}"]
        lines.append(f"file 'frames/{pictures[-1]['file']}'")
        listing.write_text('\n'.join(lines) + '\n')
        (private / 'heading.txt').write_text(f'CAREGIVER BROWSER | Source {source[:7]} | Silent review recording')
        (private / 'credit.txt').write_text('NPS: G Litten | 12 s prepared Forest input | Analysis only, not TV delivery')
        filters = ('pad=1100:946:0:44:color=0x0c131a,'
                   f'drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile={private}/heading.txt:fontcolor=white:fontsize=21:x=18:y=12,'
                   f'drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile={private}/credit.txt:fontcolor=white:fontsize=19:x=18:y=917')
        video = output / 'caregiver-browser-walkthrough.mp4'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(listing), '-vf', filters, '-r', '25', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', str(video)], check=True, timeout=120)
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_name,width,height,pix_fmt', '-of', 'json', str(video)]))
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-f', 'null', '-'], check=True, timeout=60)
        observed = stop - pictures[0]['elapsed_s']
        assert abs(float(probe['format']['duration']) - observed) < 0.25
        write(output / 'capture-receipt.json', {'source_commit': source, 'capture_tool_sha256': sha(Path(__file__)), 'kind': 'actual_caregiver_browser_walkthrough', 'input': {'path': str(FOREST), 'sha256': EXPECTED, 'bytes': inputs.stat().st_size, 'kind': 'existing_approved_prepared_rendition', 'credit': CREDIT, 'license_record': 'media/LICENSES.csv', 'license_record_sha256': sha(ROOT / 'media/LICENSES.csv'), 'original_source': 'https://www.nps.gov/media/video/view.htm?id=F2E1744E-F295-B2E5-52AF33C2205A8C9E', 'recorded_rights_review': '2026-10-18', 'fresh_license_fetch': False}, 'checks': checks, 'events': events, 'recorded_elapsed_s': observed, 'frame_count': len(pictures), 'raw_frames': pictures, 'video': {'file': video.name, 'bytes': video.stat().st_size, 'sha256': sha(video), 'probe': probe, 'decode_exit_code': 0}, 'limits': ['Silent caregiver browser, not native Fire TV footage', 'No media played, signer configured, edition approved or TV package produced', 'Not the final eight-cue replacement demo', 'No human comfort or medical acceptance', 'No qualifying long Forest or Sea Otters edition acquired']})
        print(json.dumps({'source_commit': source, 'output': str(output), 'video': video.name, 'duration_s': probe['format']['duration'], 'frames_analyzed': 360, 'checks': checks}), flush=True)
    finally:
        if server.poll() is None:
            server.send_signal(signal.SIGINT)
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--pipeline-python', required=True, type=Path)
    args = parser.parse_args()
    capture(args.output, args.pipeline_python)
