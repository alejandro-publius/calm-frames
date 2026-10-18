import datetime,json,os,re,signal,subprocess,threading,time,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent;root=out.parents[1];log=out/'native.log';events=[];stream=None
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
result={'capture':False,'pin_operations':False,'rebuild':True,'reinstall':True,'audio_system_changes':False,'owner_watched': 'not asserted'}
try:
 build=json.loads((out/'build-receipt.json').read_text());inputs=json.loads((out/'app-inputs.json').read_text())
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert build['build_exit']==0 and not build['changed_inputs']
 assert all(digest(root/f)==h for f,h in inputs.items())
 package=Path(build['package_path']);assert digest(package)==build['package_sha256']
 receipt=out/'install-receipt.json';assert not receipt.exists(),'Installation slot already used'
 install={'source_commit':build['source_commit'],'package_sha256':build['package_sha256'],'install_count':1,'started_utc':now(),'app_inputs_matched':len(inputs)}
 receipt.write_text(json.dumps(install,indent=2)+'\n')
 def command(args):
  p=subprocess.run(['vega',*args],capture_output=True,text=True,timeout=60)
  events.append({'at':now(),'command':args,'exit':p.returncode,'output':p.stdout})
  assert p.returncode==0 and 'FAILED' not in p.stdout,p.stdout+p.stderr
  return p.stdout
 command(['device','run-cmd','--device','VirtualDevice','--command','vlcm terminate-app --force --pkg-id io.github.alejandropublius.calmframes'])
 command(['device','install-app','--device','VirtualDevice','--packagePath',str(package),'--buildType','Debug'])
 transferred=command(['device','run-cmd','--device','VirtualDevice','--command','sha256sum /tmp/'+package.name]);assert build['package_sha256'] in transferred
 install.update(device_copy_sha256_matches=True,completed_utc=now());receipt.write_text(json.dumps(install,indent=2)+'\n')
 command(['device','run-cmd','--device','VirtualDevice','--command','vmsgr send pkg://io.github.alejandropublius.calmframes.main'])
 time.sleep(4)
 stream=subprocess.Popen(['vega','device','start-log-stream','--device','VirtualDevice'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
 thread=threading.Thread(target=collect,daemon=True);thread.start();time.sleep(2)
 key('KEY_RIGHT','kid-mode-home-more-info');key('KEY_LEFT','kid-mode-home-watch')
 mark('One install and launch; transferred hash matched. Home Watch focus confirmed by direction keys.')
 acadia='kid-mode-home-poster-prepared-2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28'
 otters='kid-mode-home-poster-prepared-02c2b0c0674262862ad9d02a7107e421c398aac0b06bfc4fff04098d32ebe4d6'
 forest='kid-mode-home-poster-prepared-63432b83ef15c0614d1fd80b4a899d4227a6703a0b847cb194f7ba6725b8454c'
 key('KEY_UP',acadia);key('KEY_RIGHT',forest)
 mark('Forest selected; entering Details and attribution route.')
 key('KEY_ENTER','kid-mode-details-play');key('KEY_RIGHT','kid-mode-details-show-info');key('KEY_ENTER','kid-mode-details-info-back')
 time.sleep(3);key('KEY_BACK','kid-mode-details-show-info');key('KEY_LEFT','kid-mode-details-play')
 start=key('KEY_ENTER');wait(r'CALM_TRACE prepared-playback .*77d43b664cb49d6caf82887c70d13df9d98eb32add815abd5d41320ca316503f',start);wait('CALM_TRACE playback picture-shown',start)
 mark('Exact Forest rendition started; allowing the full 12-second clip to finish. Audio output is not observed.')
 wait('CALM_TRACE playback ended',start,35);wait('CALM_TRACE focus kid-mode-details-play',start);mark('Forest naturally ended and returned to Details.')
 key('KEY_BACK',forest);key('KEY_RIGHT',otters)
 key('KEY_ENTER','kid-mode-details-play');mark('Sea Otters Details focus confirmed. Holding for 10 seconds.');time.sleep(10)
 start=key('KEY_ENTER');wait(r'CALM_TRACE prepared-playback .*b8dea9a7534215b2b360b284be2d0b23976f7caea215c691e576dff72ba6cbef',start);wait('CALM_TRACE playback picture-shown',start)
 mark('Sea Otters playback started; allowing the entire approximately 20-second silent clip to finish.')
 wait('CALM_TRACE playback ended',start,50);wait('CALM_TRACE focus kid-mode-details-play',start);mark('Sea Otters naturally ended and returned to Details.');time.sleep(5)
 key('KEY_BACK',otters);mark('Returned to coastal map. Holding for 6 seconds.');time.sleep(6)
 key('KEY_LEFT',forest);key('KEY_LEFT',acadia);time.sleep(3);key('KEY_ENTER','kid-mode-details-play');mark('Acadia Details focus confirmed. Holding for 10 seconds.');time.sleep(10)
 start=key('KEY_ENTER');wait(r'CALM_TRACE prepared-playback .*d1abd36aa0cf3ba51d6e66c186c9a1c1deb9cf04b027919dd67a465722015e46',start);wait('CALM_TRACE playback picture-shown',start)
 mark('Acadia playback started. Letting both ocean-replacement intervals play without skipping.')
 wait(r'CALM_TRACE playback cover on media=[7-9]\d{3}',start,25);wait('CALM_TRACE playback cover-surface baked-ambient',start);mark('First Acadia ocean-replacement interval requested.')
 wait(r'CALM_TRACE playback cover off media=1[2-4]\d{3}',start,15);second=len(read())
 wait(r'CALM_TRACE playback cover on media=2[8-9]\d{3}',second,35);wait('CALM_TRACE playback cover-surface baked-ambient',second);mark('Second Acadia ocean-replacement interval requested.')
 wait(r'CALM_TRACE playback cover off media=3[1-4]\d{3}',second,15);wait('CALM_TRACE playback ended',second,25);wait('CALM_TRACE focus kid-mode-details-play',second);mark('Acadia naturally ended and returned to Details.');time.sleep(5)
 key('KEY_BACK',acadia);time.sleep(3);key('KEY_DOWN','kid-mode-home-more-info');key('KEY_LEFT','kid-mode-home-watch')
 key('KEY_UP',acadia);key('KEY_RIGHT',forest);key('KEY_RIGHT',otters)
 key('KEY_UP','kid-mode-home-learn');key('KEY_ENTER','picture-hold-dismiss')
 mark('How it works opened; compiled copy verified separately. No diagnostic shortcut is exposed.')
 time.sleep(5);key('KEY_BACK','kid-mode-home-learn')
 mark('How it works Back restored its opener; selected Sea Otters remains. App left open on Home.')
 result.update(status='completed',final_focus='kid-mode-home-learn',final_selection='Sea Otters')
except Exception as e:
 result.update(status='stopped',reason=str(e));mark('Stopped: '+str(e))
finally:
 if stream:
  os.killpg(stream.pid,signal.SIGTERM)
  try:stream.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(stream.pid,signal.SIGKILL);stream.wait()
  thread.join(timeout=3)
 result.update(collector_stopped=True,events=events);(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
