import json,os,signal,subprocess,time,urllib.request,urllib.error
from pathlib import Path
root=Path('/Users/alexvintera/Documents/Codex/2026-10-15/task/intake-development'); work=root/'lifecycle-jobs';base='http://127.0.0.1:8767';records=[]
python='/Users/alexvintera/calm-frames/.venv/bin/python';repo='/Users/alexvintera/calm-frames-claude-tv-2026-10-16'
def record(name,passed,detail):
 records.append(dict(check=name,passed=passed,detail=detail));(root/'lifecycle-results.json').write_text(json.dumps(records,indent=2)+'\n');print(name,passed,detail,flush=True);assert passed

def req(path,data=None,content='application/json'):
 with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers={'Origin':base,'Content-Type':content}),timeout=10) as r:return json.load(r)
def start():
 log=(root/'lifecycle-server.log').open('a');p=subprocess.Popen([python,'-m','pipeline.local_intake','serve','--root',str(work),'--port','8767'],cwd=repo,stdout=log,stderr=log,start_new_session=True)
 for _ in range(100):
  try:req('/jobs');return p
  except OSError:time.sleep(.05)
 raise RuntimeError('server did not start')
def upload(data):
 b='BoundedLifecycle104';body=(f'--{b}\r\nContent-Disposition: form-data; name="title"\r\n\r\nLifecycle test fixture\r\n--{b}\r\nContent-Disposition: form-data; name="video"; filename="test.mp4"\r\nContent-Type: video/mp4\r\n\r\n'.encode()+data+f'\r\n--{b}--\r\n'.encode());return req('/jobs',body,'multipart/form-data; boundary='+b)
def job(identity):return next(j for j in req('/jobs')['jobs'] if j['id']==identity)
def worker_pid(identity):
 lines=subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines();matching=[int(line.strip().split(' ',1)[0]) for line in lines if '-m pipeline.local_intake worker --job '+str(work/identity)+' --mode' in line];assert len(matching)==1;return matching[0]
def alive(pid):
 try:os.kill(pid,0);return True
 except ProcessLookupError:return False
p=start()
try:
 malformed=upload(b'not a video')['id']
 for _ in range(100):
  result=job(malformed)
  if result['status']=='failed':break
  time.sleep(.05)
 record('Malformed file fails closed',result['status']=='failed' and result['playable'] is False,result.get('error'))
 req('/jobs/'+malformed+'/delete',b'')
 source=Path('/Users/alexvintera/calm-frames-claude-video-2026-10-15/media/HAZARD_nps_acadia_coastal_broll_720p.mp4').read_bytes()
 identity=upload(source)['id'];child=worker_pid(identity); old_run=job(identity)['run_id']
 # Kill only the Popen child created by this test. Worker must detect parent loss itself.
 p.kill();p.wait()
 for _ in range(100):
  if not alive(child):break
  time.sleep(.05)
 record('Worker exits after server death',not alive(child),{'owned_worker_pid':child})
 p=start();result=job(identity)
 record('Restart invalidates incomplete run',result['status']=='interrupted' and result['run_id'] is None,result['status'])
 result=req('/jobs/'+identity+'/retry',b'');child=worker_pid(identity)
 record('Retry has a new run identity',result['run_id']!=old_run,result['run_id'])
 result=req('/jobs/'+identity+'/cancel',b'')
 record('Cancellation stops owned worker and revokes review',result['status']=='canceled' and result['run_id'] is None and result['review'] is None and not alive(child),result['status'])
 time.sleep(.4);record('No stale completion after cancel',job(identity)['status']=='canceled',job(identity)['status'])
 req('/jobs/'+identity+'/delete',b'')
 record('Remove only deletes owned copied job',not(work/identity).exists(),identity)
finally:
 if p.poll() is None:p.send_signal(signal.SIGINT);p.wait(timeout=10)
