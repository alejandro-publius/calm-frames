import subprocess,time,json,re,sys,os
from pathlib import Path
P=Path('/tmp/calm-controls-2026-10-17');LOG=P/'device.log'
def call(*args):
 r=subprocess.run(['vega',*args],capture_output=True,text=True,timeout=35)
 if r.returncode or 'FAILED' in r.stdout:raise RuntimeError(r.stdout+r.stderr)
 return r.stdout+r.stderr
def log():return LOG.read_text(errors='replace') if LOG.exists() else ''
def focus():
 h=re.findall(r'CALM_TRACE focus (\S+)',log());return h[-1] if h else None
def press(k):
 start=time.time();r=call('device','run-cmd','--device','Simulator','--command','inputd-cli button_press '+k)
 with (P/'actions.jsonl').open('a') as f:f.write(json.dumps({'key':k,'host_start':start,'host_end':time.time(),'result':r})+'\n')
 time.sleep(.5);print(k,'focus',focus(),flush=True)
def wait(pattern,start=0,seconds=12):
 end=time.time()+seconds
 while time.time()<end:
  m=re.search(pattern,log()[start:])
  if m:return m
  time.sleep(.08)
 raise RuntimeError('No log match: '+pattern)
if __name__=='__main__':
 if sys.argv[1]=='stream':
  with LOG.open('w',buffering=1) as f:
   p=subprocess.Popen(['vega','device','start-log-stream','--device','Simulator'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
   (P/'stream.pid').write_text(str(os.getpid()))
   for line in p.stdout:
    if any(t in line for t in ['CALM_','io.github.alejandropublius.calmframes','inputd']):f.write(line)
 elif sys.argv[1]=='press':press(sys.argv[2])
