import datetime,json,os,re,signal,subprocess,threading,time
from pathlib import Path
out=Path(__file__).resolve().parent;log=out/'native-route.log';events=[];stream=None
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
result={'capture':False,'pin_operations':False,'rebuild':False,'reinstall':False,'audio_system_changes':False,'owner_watched': 'not asserted'}
try:
 stream=subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
 thread=threading.Thread(target=collect,daemon=True);thread.start();time.sleep(1)
 key('KEY_LEFT','kid-mode-home-watch')
 mark('Coastal map visible: Acadia selected, Watch focused. Holding for 8 seconds.');time.sleep(8)
 acadia='kid-mode-home-poster-prepared-2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28'
 otters='kid-mode-home-poster-prepared-02c2b0c0674262862ad9d02a7107e421c398aac0b06bfc4fff04098d32ebe4d6'
 key('KEY_UP',acadia);time.sleep(2);key('KEY_RIGHT',otters)
 mark('Sea Otters selected on coastal map. Holding for 6 seconds.');time.sleep(6)
 key('KEY_ENTER','kid-mode-details-play');mark('Sea Otters Details visible. Holding for 10 seconds.');time.sleep(10)
 start=key('KEY_ENTER');wait(r'CALM_TRACE prepared-playback .*b8dea9a7534215b2b360b284be2d0b23976f7caea215c691e576dff72ba6cbef',start);wait('CALM_TRACE playback picture-shown',start)
 mark('Sea Otters playback started; allowing the entire approximately 20-second silent clip to finish.')
 wait('CALM_TRACE playback ended',start,50);wait('CALM_TRACE focus kid-mode-details-play',start);mark('Sea Otters naturally ended and returned to Details.');time.sleep(5)
 key('KEY_BACK',otters);mark('Returned to coastal map. Holding for 6 seconds.');time.sleep(6)
 key('KEY_LEFT',acadia);time.sleep(3);key('KEY_ENTER','kid-mode-details-play');mark('Acadia Details visible. Holding for 10 seconds.');time.sleep(10)
 start=key('KEY_ENTER');wait(r'CALM_TRACE prepared-playback .*d1abd36aa0cf3ba51d6e66c186c9a1c1deb9cf04b027919dd67a465722015e46',start);wait('CALM_TRACE playback picture-shown',start)
 mark('Acadia playback started. Letting both ocean-replacement intervals play without skipping.')
 wait(r'CALM_TRACE playback cover on media=[7-9]\d{3}',start,25);wait('CALM_TRACE playback cover-surface baked-ambient',start);mark('First Acadia ocean-replacement interval requested.')
 wait(r'CALM_TRACE playback cover off media=1[2-4]\d{3}',start,15);second=len(read())
 wait(r'CALM_TRACE playback cover on media=2[8-9]\d{3}',second,35);wait('CALM_TRACE playback cover-surface baked-ambient',second);mark('Second Acadia ocean-replacement interval requested.')
 wait(r'CALM_TRACE playback cover off media=3[1-4]\d{3}',second,15);wait('CALM_TRACE playback ended',second,25);wait('CALM_TRACE focus kid-mode-details-play',second);mark('Acadia naturally ended and returned to Details.');time.sleep(5)
 key('KEY_BACK',acadia);time.sleep(3);key('KEY_DOWN','kid-mode-home-more-info');key('KEY_LEFT','kid-mode-home-watch')
 mark('Walkthrough completed. Home with Acadia selected and Watch focused; app left open.')
 result.update(status='completed',final_focus='kid-mode-home-watch',final_selection='Acadia')
except Exception as e:
 result.update(status='stopped',reason=str(e));mark('Stopped: '+str(e))
finally:
 if stream:
  os.killpg(stream.pid,signal.SIGTERM)
  try:stream.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(stream.pid,signal.SIGKILL);stream.wait()
  thread.join(timeout=3)
 result.update(collector_stopped=True,events=events);(out/'native-route-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
