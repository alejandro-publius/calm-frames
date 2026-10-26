import json,time
from importlib.machinery import SourceFileLoader
h=SourceFileLoader('ctl','/Users/alexvintera/Documents/Codex/2026-10-15/task/finish-native/helper.py').load_module()
result={'checks':[]}
def note(name,evidence):
 result['checks'].append({'check':name,'evidence':evidence});(h.P/'playback-results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',name,evidence,flush=True)
try:
 if h.focus() is None:
  initial=len(h.log());h.press('KEY_RIGHT');h.wait(r'CALM_TRACE focus kid-mode-home-more-info',initial,8)
 if h.focus()=='kid-mode-home-more-info':
  initial=len(h.log());h.press('KEY_LEFT');h.wait(r'CALM_TRACE focus kid-mode-home-watch',initial,5)
 assert h.focus()=='kid-mode-home-watch',h.focus()
 start=len(h.log());h.press('KEY_ENTER')
 h.wait(r'CALM_TRACE prepared-playback .*2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28',start,15)
 h.wait(r'CALM_TRACE playback cover on media=[7-9]\d{3}',start,16)
 pausedStart=len(h.log());h.press('KEY_PLAYPAUSE')
 h.wait(r'"kind"\s*:\s*"pause"',pausedStart,5)
 time.sleep(1.5)
 result['pause_observed']=True
 resumeStart=len(h.log());h.press('KEY_PLAYPAUSE');h.wait(r'"kind"\s*:\s*"playing"',resumeStart,5)
 h.wait(r'CALM_TRACE playback cover off media=1[2-4]\d{3}',resumeStart,10)
 note('Pause/resume during first cover','pause then playing and first cover-off events; inspect timing samples for exact pause duration')
 h.wait(r'CALM_TRACE playback cover on media=2[8-9]\d{3}',resumeStart,22)
 assert h.focus()=='calm-card-skip',h.focus()
 skipStart=len(h.log());h.press('KEY_ENTER')
 h.wait(r'CALM_TRACE seek .*playhead-write',skipStart,5)
 h.wait(r'"kind"\s*:\s*"seeked"',skipStart,5)
 h.wait(r'CALM_TRACE playback cover off media=3[1-4]\d{3}',skipStart,5)
 note('Activate Skip during second cover','Skip focused; Enter caused guarded playhead-write, seeked and cover-off')
 h.wait(r'CALM_TRACE playback ended',skipStart,18)
 h.wait(r'CALM_TRACE focus kid-mode-home-watch',skipStart,8)
 note('End-of-video return','Native ended -> existing teardown -> Home Watch without presentation delay')
 reviewStart=len(h.log());h.press('KEY_ENTER')
 h.wait(r'CALM_TRACE playback picture-shown',reviewStart,15)
 backStart=len(h.log());h.press('KEY_BACK')
 h.wait(r'CALM_TRACE playback back',backStart,8);h.wait(r'CALM_TRACE focus kid-mode-home-watch',backStart,8)
 note('Manual Back during playback','Returned Home Watch before video ended')
 result['result']='completed'
except Exception as e:
 result['result']='stopped';result['reason']=str(e);print('STOP',str(e),flush=True)
finally:
 (h.P/'playback-results.json').write_text(json.dumps(result,indent=2)+'\n')
