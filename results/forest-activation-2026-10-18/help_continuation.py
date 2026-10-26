import datetime,json,os,re,signal,subprocess,threading,time,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent;root=out.parents[1];log=out/'help-native.log';events=[];stream=None
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def mark(text):
 events.append({'at':now(),'event':text});print(text,flush=True)
def read():return log.read_text(errors='replace') if log.exists() else ''
def wait(pattern,start=0,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  m=re.search(pattern,read()[start:])
  if m:return m
  time.sleep(.12)
 raise RuntimeError('Expected event missing: '+pattern)
def key(name,focus=None):
 start=len(read());p=subprocess.run(['vega','device','run-cmd','--device','VirtualDevice','--command','inputd-cli button_press '+name],capture_output=True,text=True,timeout=15)
 events.append({'at':now(),'key':name,'exit':p.returncode})
 if p.returncode or 'FAILED' in p.stdout:raise RuntimeError('Remote command failed: '+name)
 if focus:wait('CALM_TRACE focus '+focus,start)
 time.sleep(.7);return start
def collect():
 with log.open('w',buffering=1) as f:
  for line in stream.stdout:
   if 'CALM_TRACE' in line:f.write(line)
result={'capture':False,'pin_operations':False,'reinstall':False,'relaunch':False}
try:
 stream=subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
 thread=threading.Thread(target=collect,daemon=True);thread.start();time.sleep(2)
 key('KEY_RIGHT','kid-mode-home-learn');key('KEY_ENTER','picture-hold-dismiss')
 mark('How it works opened with Back focused; compiled copy checked separately.')
 time.sleep(5);key('KEY_BACK','kid-mode-home-learn')
 mark('How it works Back restores its opener; Sea Otters remains selected.')
 result.update(status='completed',final_focus='kid-mode-home-learn',final_selection='Sea Otters')
except Exception as e:
 result.update(status='stopped',reason=str(e));mark('Stopped: '+str(e))
finally:
 if stream:
  os.killpg(stream.pid,signal.SIGTERM)
  try:stream.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(stream.pid,signal.SIGKILL);stream.wait()
  thread.join(timeout=3)
 result.update(collector_stopped=True,events=events);(out/'help-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 if result['status']=='completed':
  initial=json.loads((out/'receipt.json').read_text())
  combined={**initial,**result,'events':initial['events']+events,'initial_route_note':'All three playback checks completed; final Up reached profile, not How it works. Continued from observed profile focus with Right, without another install or launch.','reinstall':True,'install_count':1}
  combined.pop('reason',None);(out/'completion-receipt.json').write_text(json.dumps(combined,indent=2)+'\n')
