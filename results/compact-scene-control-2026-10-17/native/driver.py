import json,time
from importlib.machinery import SourceFileLoader
h=SourceFileLoader('ctl','/Users/alexvintera/Documents/Codex/2026-10-15/task/compact-native/helper.py').load_module()
result={'checks':[]}
def note(name,evidence):
 result['checks'].append({'check':name,'evidence':evidence});print('PASS',name,evidence,flush=True)
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
 result['pause_window_log']=h.log()[pausedStart:]
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
 backStart=len(h.log());h.press('KEY_BACK');h.wait(r'CALM_TRACE playback back',backStart,5);h.wait(r'CALM_TRACE focus kid-mode-home-watch',backStart,5)
 assert h.focus()=='kid-mode-home-watch',h.focus()
 note('Manual Back during playback','Back key followed by leavePlayer and Home Watch focus, before video ended')
 reviewStart=len(h.log());h.press('KEY_ENTER')
 h.wait(r'CALM_TRACE playback cover on media=[7-9]\d{3}',reviewStart,16)
 pauseStart=len(h.log());h.press('KEY_PLAYPAUSE');h.wait(r'"kind"\s*:\s*"pause"',pauseStart,5)
 assert h.focus()=='calm-card-skip',h.focus()
 note('Owner review state','App remains open, paused in first covered scene with Skip focused')
 result['result']='completed'
except Exception as e:
 result['result']='stopped';result['reason']=str(e);print('STOP',str(e),flush=True)
finally:
 (h.P/'playback-results.json').write_text(json.dumps(result,indent=2)+'\n')
