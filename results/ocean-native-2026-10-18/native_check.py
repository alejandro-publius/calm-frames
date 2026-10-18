"""Single update/install and bounded public playback checks using text logs only."""
import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
LOG = OUT/'native-trace.log'
result = {'checks': [], 'capture_used': False, 'visual_audio_acceptance': False,
          'native_error_injected': False, 'household_records_inspected': False}
stream = None
in_player = False
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def logs():
    return LOG.read_text(errors='replace') if LOG.exists() else ''

def wait(pattern, start=0, seconds=15):
    end = time.monotonic()+seconds
    while time.monotonic()<end:
        match = re.search(pattern, logs()[start:])
        if match:
            return match
        time.sleep(.08)
    raise RuntimeError('No log match: '+pattern)

def run(args):
    began = now()
    p = subprocess.run(['vega', *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=60)
    with (OUT/'native-actions.jsonl').open('a') as f:
        f.write(json.dumps({'args': args, 'start_utc': began, 'end_utc': now(),
                            'exit': p.returncode, 'output': p.stdout})+'\n')
    if p.returncode or 'FAILED' in p.stdout:
        raise RuntimeError(p.stdout)
    return p.stdout

def press(key, expected=None):
    start = len(logs())
    run(['device', 'run-cmd', '--device', 'VirtualDevice', '--command', 'inputd-cli button_press '+key])
    if expected:
        wait('CALM_TRACE focus '+expected, start)
    time.sleep(.2)
    return start

def note(name):
    result['checks'].append(name)
    (OUT/'native-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', name, flush=True)

def collect():
    with LOG.open('w', buffering=1) as f:
        for line in stream.stdout:
            if 'CALM_' in line or 'io.github.alejandropublius.calmframes' in line:
                f.write(line)

try:
    build = json.loads((OUT/'build-receipt.json').read_text())
    inputs = json.loads((OUT/'app-inputs.json').read_text())
    assert build['build_exit']==0 and not build['changed_inputs']
    assert all(sha(ROOT/f)==h for f,h in inputs.items())
    package = Path(build['package_path'])
    assert sha(package)==build['package_sha256']
    assert not (OUT/'install-receipt.json').exists(), 'Installation slot already used.'
    install = {'source_commit': build['source_commit'], 'package_sha256': build['package_sha256'],
               'package_path': str(package), 'install_count': 1, 'inputs_matched': len(inputs), 'started_utc': now()}
    (OUT/'install-receipt.json').write_text(json.dumps(install, indent=2)+'\n')
    stream = subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                              bufsize=1, start_new_session=True)
    thread = threading.Thread(target=collect, daemon=True)
    thread.start()
    time.sleep(.6)
    run(['device','run-cmd','--device','VirtualDevice','--command',
         'vlcm terminate-app --force --pkg-id io.github.alejandropublius.calmframes'])
    output = run(['device','install-app','--device','VirtualDevice','--packagePath',str(package),'--buildType','Debug'])
    install['install_output'] = output
    transferred = run(['device','run-cmd','--device','VirtualDevice','--command','sha256sum /tmp/'+package.name])
    assert build['package_sha256'] in transferred
    install['device_copy_sha256_matches'] = True
    run(['device','run-cmd','--device','VirtualDevice','--command','vmsgr send pkg://io.github.alejandropublius.calmframes.main'])
    running = run(['device','running-apps','--device','VirtualDevice'])
    assert 'io.github.alejandropublius.calmframes.main' in running
    install.update(running_confirmed=True, completed_utc=now())
    (OUT/'install-receipt.json').write_text(json.dumps(install, indent=2)+'\n')
    note('Single update installed; transferred package SHA-256 and all app inputs match')
    time.sleep(2)
    press('KEY_RIGHT', 'kid-mode-home-more-info')
    press('KEY_LEFT', 'kid-mode-home-watch')
    start = press('KEY_ENTER')
    in_player = True
    wait(r'CALM_TRACE prepared-playback .*d1abd36aa0cf3ba51d6e66c186c9a1c1deb9cf04b027919dd67a465722015e46', start)
    wait('CALM_TRACE playback picture-shown', start)
    note('Home Watch selects the approved replacement and clears its opening cover')
    first = wait(r'CALM_TRACE playback cover on media=([7-9]\d{3})', start, 20)
    wait('CALM_TRACE playback cover-surface baked-ambient', start, 5)
    note('First scheduled interval requests the baked ocean surface while guard cover stays on')
    wait(r'CALM_TRACE playback cover off media=1[2-4]\d{3}', start, 12)
    second_start = len(logs())
    second = wait(r'CALM_TRACE playback cover on media=(2[8-9]\d{3})', second_start, 24)
    wait('CALM_TRACE playback cover-surface baked-ambient', second_start, 5)
    note('Second scheduled interval requests the baked ocean surface while guard cover stays on')
    wait(r'CALM_TRACE playback cover off media=3[1-4]\d{3}', second_start, 10)
    wait('CALM_TRACE playback ended', second_start, 15)
    wait('CALM_TRACE focus kid-mode-home-watch', second_start)
    in_player = False
    result['scheduled_cover_on_media_ms'] = [int(first.group(1)),int(second.group(1))]
    note('Uninterrupted playback reports natural end, teardown and Home Watch return')
    second_run = press('KEY_ENTER')
    in_player = True
    wait('CALM_TRACE playback picture-shown', second_run)
    wait(r'CALM_TRACE playback cover on media=[7-9]\d{3}', second_run, 20)
    paused = press('KEY_PLAYPAUSE')
    wait('CALM_TRACE playback cover-surface (?:message|plain|signed-still)', paused, 6)
    note('Pause during scheduled ocean interval restores the opaque fallback')
    resumed = press('KEY_PLAYPAUSE')
    wait('CALM_TRACE playback cover-surface baked-ambient', resumed, 6)
    note('Resume restores eligible baked ocean presentation')
    focuses = re.findall(r'CALM_TRACE focus (\S+)', logs())
    assert focuses and focuses[-1].strip("',")=='calm-card-skip', focuses[-1:]
    skipped = press('KEY_ENTER')
    wait(r'CALM_TRACE seek .*cover-request.*true', skipped, 6)
    wait(r'CALM_TRACE seek .*playhead-write', skipped, 6)
    wait(r'CALM_TRACE playback cover off media=1[2-5]\d{3}', skipped, 10)
    segment = logs()[skipped:]
    assert segment.index('cover-request')<segment.index('playhead-write')
    note('Skip requests cover before playhead write, then releases after guarded seek')
    back = press('KEY_BACK')
    wait('CALM_TRACE focus kid-mode-home-watch', back)
    in_player = False
    note('Manual playback Back returns Home Watch')
    result['result'] = 'completed'
except Exception as error:
    result.update(result='stopped', reason=str(error))
    print('STOP', str(error), flush=True)
    if in_player:
        try:
            back = press('KEY_BACK')
            wait('CALM_TRACE focus kid-mode-home-watch', back, 10)
            in_player = False
            result['failure_cleanup_home'] = True
        except Exception as cleanup:
            result['cleanup_error'] = str(cleanup)
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
    focuses = re.findall(r'CALM_TRACE focus (\S+)', logs())
    result['last_reported_focus'] = focuses[-1].strip("',") if focuses else None
    (OUT/'native-results.json').write_text(json.dumps(result, indent=2)+'\n')
