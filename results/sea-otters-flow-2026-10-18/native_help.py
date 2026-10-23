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
LOG = OUT/'native-help-trace.log'
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
    with (OUT/'native-help-actions.jsonl').open('a') as f:
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
    (OUT/'native-help-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', name, flush=True)

def collect():
    with LOG.open('w', buffering=1) as f:
        for line in stream.stdout:
            if 'CALM_' in line or 'io.github.alejandropublius.calmframes' in line:
                f.write(line)

try:
    stream = subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)
    thread = threading.Thread(target=collect, daemon=True); thread.start(); time.sleep(.6)
    press('KEY_LEFT', 'kid-mode-home-watch')
    note('Final route corrected: Down from Acadia reaches Details, then Left reaches Watch')
    press('KEY_UP', 'kid-mode-home-poster-prepared-2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28')
    up=press('KEY_UP'); wait('CALM_TRACE focus kid-mode-home-',up)
    for _ in range(3):
        focus=re.findall(r'CALM_TRACE focus (\S+)',logs())[-1].strip("',")
        if focus=='kid-mode-home-learn': break
        press('KEY_LEFT' if focus=='kid-mode-home-parent-area' else 'KEY_RIGHT')
    assert re.findall(r'CALM_TRACE focus (\S+)',logs())[-1].strip("',")=='kid-mode-home-learn'
    press('KEY_ENTER','picture-hold-dismiss')
    down=press('KEY_DOWN'); wait('CALM_TRACE focus picture-hold-',down)
    focus=re.findall(r'CALM_TRACE focus (\S+)',logs())[-1].strip("',")
    if focus=='picture-hold-bridge-test': press('KEY_RIGHT','picture-hold-playback-check')
    else: assert focus=='picture-hold-playback-check',focus
    press('KEY_ENTER','kid-mode-details-play')
    play=press('KEY_ENTER'); in_player=True
    wait('CALM_TRACE playback picture-shown',play)
    back=press('KEY_BACK'); wait('CALM_TRACE focus kid-mode-details-play',back); in_player=False
    press('KEY_BACK','kid-mode-home-learn')
    note('How it works > Check playback > Watch > Back > Back returns focus to How it works')
    down=press('KEY_DOWN'); wait('CALM_TRACE focus kid-mode-home-poster-',down)
    focus=re.findall(r'CALM_TRACE focus (\S+)',logs())[-1].strip("',")
    if '02c2b0' in focus: press('KEY_LEFT','kid-mode-home-poster-prepared-2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28')
    down=press('KEY_DOWN'); wait('CALM_TRACE focus kid-mode-home-',down)
    focus=re.findall(r'CALM_TRACE focus (\S+)',logs())[-1].strip("',")
    if focus=='kid-mode-home-more-info': press('KEY_LEFT','kid-mode-home-watch')
    else: assert focus=='kid-mode-home-watch',focus
    note('App remains open at Home, Acadia selected, Watch focused')
    result['result']='completed'
except Exception as error:
    result.update(result='stopped',reason=str(error)); print('STOP',error,flush=True)
finally:
    if stream is not None:
        os.killpg(stream.pid,signal.SIGTERM)
        try: stream.wait(timeout=5)
        except subprocess.TimeoutExpired: os.killpg(stream.pid,signal.SIGKILL); stream.wait()
        thread.join(timeout=3); result['collector_stopped']=True
    focuses=re.findall(r'CALM_TRACE focus (\S+)',logs())
    result['last_reported_focus']=focuses[-1].strip("',") if focuses else None
    (OUT/'native-help-results.json').write_text(json.dumps(result,indent=2)+'\n')
