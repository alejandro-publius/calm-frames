"""Export 1080p and 720p host trees using in-memory fixtures; no native app access."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FIXTURES=[('home','Home'),('harbor','Details'),('parent','Parent'),('playback','Playback'),('unavailable','Unavailable'),('utility','Utility')]
created=[]
try:
 for height in (1080,720):
  for name,dest in FIXTURES:
   source=(ROOT/f'eval/preview/{name}.fixture.tsx').read_text()
   if height==720:
    if name in ('home','harbor','utility'):
     source+="\njest.mock('../../src/utils/pixelUtils', () => ({ ...jest.requireActual('../../src/utils/pixelUtils'), scaleUxToDp: (value: number) => Math.round(value * 720 / 1080) }));\n"
     source=source.replace("'../../build/home-preview'","'../../build/home-preview/720'").replace("'../../build/design-preview', stage","'../../build/design-preview', stage, '720'").replace("'../../build/utility-preview'","'../../build/utility-preview/720'")
    else:
     source=source.replace('const height = 1080','const height = 720').replace('Math.round(v * 1080 / 1080)','Math.round(v * 720 / 1080)').replace('width: 1920, height: 1080','width: 1280, height: 720')
   target=ROOT/f'app/test/calmframes/wholeFlowExport{height}{dest}.test.tsx'
   if target.exists():raise RuntimeError(f'Refusing to overwrite {target}')
   target.write_text(source);created.append(target)
 subprocess.run(['npm','--prefix','app','test','--','--runInBand','--coverage=false','--watchman=false','--testPathPattern=wholeFlowExport'],cwd=ROOT,check=True)
finally:
 for target in created:target.unlink()
