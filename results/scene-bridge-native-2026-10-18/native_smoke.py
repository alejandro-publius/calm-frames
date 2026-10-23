"""One install and bounded remote-key smoke; text logs only, no image/audio capture."""
import json
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path

P = Path(__file__).resolve().parent
LOG = P / 'native-device.log'
result = {'checks': [], 'capture_used': False, 'media_played': False}
stream = None


def log():
    return LOG.read_text(errors='replace') if LOG.exists() else ''


def wait(pattern, start=0, seconds=15):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        found = re.search(pattern, log()[start:])
        if found:
            return found
        time.sleep(.08)
    raise RuntimeError('No log match: ' + pattern)


def press(key, expected=None):
    start = len(log())
    began = time.time()
    output = subprocess.run(['vega', 'device', 'run-cmd', '--device', 'VirtualDevice',
                             '--command', 'inputd-cli button_press ' + key],
                            capture_output=True, text=True, timeout=30)
    with (P / 'native-actions.jsonl').open('a') as f:
        f.write(json.dumps({'key': key, 'start': began, 'end': time.time(),
                            'exit': output.returncode, 'output': output.stdout + output.stderr}) + '\n')
    if output.returncode or 'FAILED' in output.stdout:
        raise RuntimeError(output.stdout + output.stderr)
    if expected:
        wait('CALM_TRACE focus ' + expected, start, 12)
    time.sleep(.3)
    return start


def note(name):
    result['checks'].append(name)
    (P / 'native-results.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', name, flush=True)


def collect():
    with LOG.open('w', buffering=1) as f:
        for line in stream.stdout:
            if any(token in line for token in ['CALM_', 'io.github.alejandropublius.calmframes', 'inputd']):
                f.write(line)


try:
    stream = subprocess.Popen(['vega', 'device', 'start-log-stream', '--device', 'VirtualDevice'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, bufsize=1, start_new_session=True)
    result['collector_pid'] = stream.pid
    thread = threading.Thread(target=collect, daemon=True)
    thread.start()
    time.sleep(.5)
    initial = len(log())
    install = subprocess.run(['/Users/alexvintera/calm-frames/.venv/bin/python', str(P/'install.py')],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
    (P / 'install.log').write_text(install.stdout)
    print(install.stdout, flush=True)
    if install.returncode:
        raise RuntimeError('The single installation did not complete; see install receipt.')
    try:
        wait('CALM_TRACE focus kid-mode-home-watch', initial, 15)
        note('Launch reports Home Watch focus')
    except RuntimeError:
        result['initial_focus_trace_missing'] = True
    press('KEY_RIGHT', 'kid-mode-home-more-info')
    press('KEY_UP', 'kid-mode-home-choose-profile')
    press('KEY_RIGHT', 'kid-mode-home-learn')
    press('KEY_ENTER', 'picture-hold-dismiss')
    note('How it works opens at Back')
    press('KEY_DOWN', 'picture-hold-bridge-test')
    start = press('KEY_ENTER', 'scene-bridge-fixture-back')
    wait('CALM_TRACE playback scene-bridge-fixture state=test-text opaque_requested=true media=none', start)
    note('Explicit development entry mounts verified static test text with return focused')
    press('KEY_RIGHT', 'scene-bridge-fixture-fallback')
    start = press('KEY_ENTER')
    wait('CALM_TRACE playback scene-bridge-fixture state=fallback opaque_requested=true media=none', start)
    note('Stale identity requests ordinary opaque fallback')
    press('KEY_RIGHT', 'scene-bridge-fixture-valid')
    start = press('KEY_ENTER')
    wait('CALM_TRACE playback scene-bridge-fixture state=test-text opaque_requested=true media=none', start)
    note('Valid identity restores the static test text')
    start = press('KEY_BACK', 'picture-hold-bridge-test')
    wait('CALM_TRACE playback scene-bridge-fixture dismissed', start)
    note('Hardware Back dismisses the fixture and restores entry focus')
    start = press('KEY_ENTER', 'scene-bridge-fixture-back')
    wait('CALM_TRACE playback scene-bridge-fixture state=test-text opaque_requested=true media=none', start)
    start = press('KEY_ENTER', 'picture-hold-bridge-test')
    wait('CALM_TRACE playback scene-bridge-fixture dismissed', start)
    note('Skip test and return dismisses the fixture and restores entry focus')
    press('KEY_BACK', 'kid-mode-home-learn')
    note('How it works Back restores Home opener')
    press('KEY_RIGHT', 'kid-mode-home-parent-area')
    press('KEY_ENTER', 'kid-mode-parent-key-1')
    press('KEY_BACK', 'kid-mode-home-parent-area')
    note('Parents cancel restores Parents without PIN entry')
    start = press('KEY_DOWN')
    wait(r'CALM_TRACE focus kid-mode-home-(?:watch|more-info)', start, 12)
    focuses = re.findall(r'CALM_TRACE focus (\S+)', log())
    if focuses[-1] == 'kid-mode-home-more-info':
        press('KEY_LEFT', 'kid-mode-home-watch')
    note('App returned to Home Watch')
    result['personal_editor_native_tested'] = False
    result['registered_real_scene_bridge_native_tested'] = False
    result['static_fixture_native_state_tested'] = True
    result['result'] = 'completed'
except Exception as error:
    result.update(result='stopped', reason=str(error))
    print('STOP', error, flush=True)
finally:
    if stream is not None:
        os.killpg(stream.pid, signal.SIGTERM)
        try:
            stream.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(stream.pid, signal.SIGKILL)
            stream.wait()
        thread.join(timeout=3)
        result['collector_stopped'] = True
    focuses = re.findall(r'CALM_TRACE focus (\S+)', log())
    result['last_reported_focus'] = focuses[-1] if focuses else None
    result['native_visual_audio_acceptance'] = False
    (P / 'native-results.json').write_text(json.dumps(result, indent=2) + '\n')
