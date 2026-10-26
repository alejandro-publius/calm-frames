"""Route-only verification of the existing installed app using text logs; no install or launch."""
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
    stream=subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
    thread=threading.Thread(target=collect,daemon=True);thread.start();time.sleep(.6)
    acadia='kid-mode-home-poster-prepared-2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28'
    otters='kid-mode-home-poster-prepared-02c2b0c0674262862ad9d02a7107e421c398aac0b06bfc4fff04098d32ebe4d6'
    press('KEY_UP',acadia)
    press('KEY_RIGHT',otters)
    press('KEY_ENTER','kid-mode-details-play')
    note('From Home Acadia Watch: Up, Right, Select opens Sea Otters Details with Watch focused')
    play=press('KEY_ENTER');in_player=True
    wait(r'CALM_TRACE prepared-playback .*b8dea9a7534215b2b360b284be2d0b23976f7caea215c691e576dff72ba6cbef',play)
    wait('CALM_TRACE playback picture-shown',play)
    note('A fourth Select starts the exact approved NOAA sea-otter clip')
    back=press('KEY_BACK');wait('CALM_TRACE focus kid-mode-details-play',back);in_player=False
    press('KEY_BACK',otters)
    press('KEY_LEFT',acadia)
    press('KEY_DOWN','kid-mode-home-more-info')
    press('KEY_LEFT','kid-mode-home-watch')
    note('Return: Back, Back, Left, Down, Left restores Home Acadia Watch')
    result.update(result='completed',installed_build_changed=False,selected_home_title='Acadia')
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
    (OUT/'native-results.json').write_text(json.dumps(result,indent=2)+'\n')
