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
LOG = OUT/'native-finish-trace.log'
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
    with (OUT/'native-finish-actions.jsonl').open('a') as f:
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
    (OUT/'native-finish-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', name, flush=True)

def collect():
    with LOG.open('w', buffering=1) as f:
        for line in stream.stdout:
            if 'CALM_' in line or 'io.github.alejandropublius.calmframes' in line:
                f.write(line)

try:
    stream=subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
    thread=threading.Thread(target=collect,daemon=True);thread.start();time.sleep(.6)
    press('KEY_BACK','kid-mode-home-learn')
    note('How it works Back restores focus to How it works')
    down=press('KEY_DOWN');wait('CALM_TRACE focus kid-mode-home-poster-',down)
    focus=re.findall(r'CALM_TRACE focus (\S+)',logs())[-1].strip("',")
    acadia='kid-mode-home-poster-prepared-2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28'
    if focus!=acadia: press('KEY_LEFT',acadia)
    press('KEY_ENTER','kid-mode-details-play')
    play=press('KEY_ENTER');in_player=True
    wait(r'CALM_TRACE prepared-playback .*d1abd36aa0cf3ba51d6e66c186c9a1c1deb9cf04b027919dd67a465722015e46',play)
    wait('CALM_TRACE playback picture-shown',play)
    back=press('KEY_BACK');wait('CALM_TRACE focus kid-mode-details-play',back);in_player=False
    press('KEY_BACK',acadia)
    note('Acadia map destination > Details > Watch > Back > Back restores the same destination')
    press('KEY_DOWN','kid-mode-home-more-info')
    press('KEY_LEFT','kid-mode-home-watch')
    note('App remains open on Home with Acadia selected and Watch focused')
    result.update(result='completed',selected_home_title='Acadia')
except Exception as error:
    result.update(result='stopped',reason=str(error));print('STOP',error,flush=True)
finally:
    if stream is not None:
        os.killpg(stream.pid,signal.SIGTERM)
        try:stream.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(stream.pid,signal.SIGKILL);stream.wait()
        thread.join(timeout=3);result['collector_stopped']=True
    focuses=re.findall(r'CALM_TRACE focus (\S+)',logs())
    result['last_reported_focus']=focuses[-1].strip("',") if focuses else None
    (OUT/'native-finish-results.json').write_text(json.dumps(result,indent=2)+'\n')
