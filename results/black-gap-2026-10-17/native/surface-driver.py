import json
from importlib.machinery import SourceFileLoader
h=SourceFileLoader('ctl','/Users/alexvintera/Documents/Codex/2026-10-15/task/black-gap-review/native/helper.py').load_module()
r={'checks':[]}
def key(k,focus):
 start=len(h.log());h.press(k);h.wait('CALM_TRACE focus '+focus,start,8)
def note(name):
 r['checks'].append(name);(h.P/'surface-results.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',name,flush=True)
try:
 key('KEY_RIGHT','kid-mode-home-more-info')
 key('KEY_ENTER','kid-mode-details-play')
 key('KEY_RIGHT','kid-mode-details-show-info')
 key('KEY_ENTER','kid-mode-details-info-back')
 key('KEY_BACK','kid-mode-details-show-info')
 key('KEY_BACK','kid-mode-home-more-info')
 note('Home Details More info Back Back returns Home Details focus')
 key('KEY_UP','kid-mode-home-choose-profile')
 key('KEY_RIGHT','kid-mode-home-learn')
 key('KEY_ENTER','picture-hold-dismiss')
 key('KEY_BACK','kid-mode-home-learn')
 note('How it works Back returns its opener')
 key('KEY_RIGHT','kid-mode-home-parent-area')
 key('KEY_ENTER','kid-mode-parent-key-1')
 key('KEY_BACK','kid-mode-home-parent-area')
 note('Parents hardware Back cancelled without PIN entry; Parents focus restored')
 key('KEY_ENTER','kid-mode-parent-key-1')
 key('KEY_UP','kid-mode-parent-back')
 key('KEY_ENTER','kid-mode-home-parent-area')
 note('Parents on-screen Back cancelled without PIN entry; Parents focus restored')
 start=len(h.log());h.press('KEY_DOWN')
 h.wait(r'CALM_TRACE focus kid-mode-home-(?:watch|more-info)',start,8)
 if h.focus()=='kid-mode-home-more-info':key('KEY_LEFT','kid-mode-home-watch')
 assert h.focus()=='kid-mode-home-watch',h.focus()
 r['result']='completed'
except Exception as e:r.update(result='stopped',reason=str(e));print('STOP',str(e),flush=True)
finally:(h.P/'surface-results.json').write_text(json.dumps(r,indent=2)+'\n')
