import urllib.request,urllib.error,json,time
from pathlib import Path
root=Path('/Users/alexvintera/Documents/Codex/2026-10-15/task/intake-development');base='http://127.0.0.1:8766';records=[]
def request(path,body=None,headers=None):
 req=urllib.request.Request(base+path,data=body,headers=headers or {})
 try:
  with urllib.request.urlopen(req,timeout=45) as r:return r.status,r.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
def record(name,passed,detail):
 records.append(dict(check=name,passed=passed,detail=detail));(root/'http-results.json').write_text(json.dumps(records,indent=2)+'\n');print(name,passed,detail,flush=True);assert passed
status,raw=request('/');record('Local page available',status==200 and b'<video' not in raw,'No video element or media endpoint')
status,raw=request('/jobs',b'',{'Content-Type':'application/json'});record('Cross-origin/missing origin rejected',status==403,status)
status,raw=request('/original.mp4');record('Original media cannot be fetched',status==404,status)
source=Path('/Users/alexvintera/calm-frames-claude-video-2026-10-15/media/HAZARD_nps_acadia_coastal_broll_720p.mp4')
b='CalmLocalTestBoundary104';data=(f'--{b}\r\nContent-Disposition: form-data; name="title"\r\n\r\nExisting Acadia source analysis check\r\n--{b}\r\nContent-Disposition: form-data; name="video"; filename="acadia-test.mp4"\r\nContent-Type: video/mp4\r\n\r\n'.encode()+source.read_bytes()+f'\r\n--{b}--\r\n'.encode())
status,raw=request('/jobs',data,{'Origin':base,'Content-Type':'multipart/form-data; boundary='+b});record('Upload existing fixture for real analysis',status==200,status)
job=json.loads(raw);(root/'real-job-id.txt').write_text(job['id'])
start=time.time();old=None
while time.time()-start<600:
 status,raw=request('/jobs');jobs=json.loads(raw)['jobs'];job=next(j for j in jobs if j['id']==job['id'])
 if job['stage']!=old:print(job['status'],job['stage'],flush=True);old=job['stage']
 if job['status'] not in ['queued','checking','analyzing']:break
 time.sleep(1)
(root/'real-job.json').write_text(json.dumps(job,indent=2)+'\n')
record('Full-file review produced',job['status']=='review',job.get('error') or job['status'])
record('Real Acadia identity and all frames',job['review']['source_sha256']=='2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28' and job['review']['frame_count']==1804,job['review']['frame_count'])
status,raw=request('/jobs/'+job['id']+'/approve',b'',{'Origin':base});approved=json.loads(raw)
record('Explicit review approval remains signing blocked',status==200 and approved['status']=='signing_blocked' and approved['playable'] is False,approved.get('status'))
(root/'real-approved-job.json').write_text(json.dumps(approved,indent=2)+'\n')
