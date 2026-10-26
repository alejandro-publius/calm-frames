import time,json
from importlib.machinery import SourceFileLoader
h=SourceFileLoader('ctl','/tmp/calm-reset-helper.py').load_module()
def events(offset):
 out=[];seen=set()
 for line in h.log()[offset:].splitlines():
  if 'CALM_TIMING' not in line:continue
  try:e,_=json.JSONDecoder().raw_decode(line.split('CALM_TIMING',1)[1].strip())
  except ValueError:continue
  k=json.dumps(e,sort_keys=True)
  if k not in seen:seen.add(k);out.append(e)
 return out
r={'checks':[]};start=0
try:
 h.press('KEY_RIGHT');assert h.focus()=='kid-mode-home-more-info',h.focus()
 h.press('KEY_LEFT');assert h.focus()=='kid-mode-home-watch',h.focus()
 start=len(h.log());h.press('KEY_ENTER');h.wait(r'"kind"\s*:\s*"playing"',start,15)
 time.sleep(5)
 ts=[e for e in events(start) if e['kind']=='timeupdate'];assert len(ts)>3,'No regular timeupdates'
 wall=ts[-1]['wallClockMs']-ts[0]['wallClockMs'];media=ts[-1]['mediaTimeMs']-ts[0]['mediaTimeMs'];r['initial_progress']={'wall_ms':wall,'media_ms':media};print('initial progress',r['initial_progress'],flush=True)
 assert media/wall>.8,'Initial playback still slow'
 h.wait(r'CALM_TRACE playback cover on media=[7-9]\d{3}',start,8)
 p=len(h.log());h.press('KEY_PLAYPAUSE');h.wait(r'"kind"\s*:\s*"pause"',p,5);time.sleep(1.5)
 u=len(h.log());h.press('KEY_PLAYPAUSE');h.wait(r'"kind"\s*:\s*"playing"',u,5)
 h.wait(r'CALM_TRACE playback cover off media=1[2-4]\d{3}',u,12)
 r['checks'].append('Pause/resume during first cover, cover clears');print('PASS Pause/resume',flush=True)
 h.wait(r'CALM_TRACE playback cover on media=2[8-9]\d{3}',u,24)
 assert h.focus()=='calm-card-skip',h.focus()
 k=len(h.log());h.press('KEY_ENTER');h.wait(r'CALM_TRACE seek .*playhead-write',k,5);h.wait(r'"kind"\s*:\s*"seeked"',k,10);h.wait(r'CALM_TRACE playback cover off media=3[1-4]\d{3}',k,5)
 r['checks'].append('Skip during second cover; guarded seek and release');print('PASS Skip',flush=True)
 time.sleep(1.5)
 b=len(h.log());h.press('KEY_BACK');h.wait(r'CALM_TRACE focus kid-mode-home-watch',b,10)
 r['checks'].append('Manual Back -> Home Watch');r['status']='completed';print('PASS manual Back',flush=True)
except Exception as e:
 r['status']='failed';r['reason']=str(e);print('FAIL',str(e),flush=True)
 if start and not h.focus().startswith('kid-mode-home-'):
  try:h.press('KEY_BACK')
  except Exception:pass
finally:
 r['events']=events(start);(h.P/'verification.json').write_text(json.dumps(r,indent=2)+'\n')
