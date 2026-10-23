import json,time
from importlib.machinery import SourceFileLoader
h=SourceFileLoader('ctl','/tmp/calm-controls-helper.py').load_module()
r={'checks':[]}
try:
 h.wait(r'CALM_TRACE playback cover on media=2[8-9]\d{3}',0,60)
 assert h.focus()=='calm-card-skip',h.focus()
 start=len(h.log());h.press('KEY_ENTER');h.wait(r'CALM_TRACE seek .*playhead-write',start,8);h.wait(r'"kind"\s*:\s*"seeked"',start,8)
 r['checks'].append('Skip activated; guarded playhead-write and seeked observed');print('PASS Skip',flush=True)
 start=len(h.log());h.press('KEY_BACK');h.wait(r'CALM_TRACE playback back',start,8);h.wait(r'CALM_TRACE focus kid-mode-home-watch',start,8)
 r['checks'].append('Manual Back during playback returned Home Watch');r['result']='completed';print('PASS manual playback Back',flush=True)
except Exception as e:r['result']='stopped';r['reason']=str(e);print('STOP',str(e),flush=True)
finally:(h.P/'finish-results.json').write_text(json.dumps(r,indent=2)+'\n')
