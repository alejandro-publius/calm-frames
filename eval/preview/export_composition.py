import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
created=[]
try:
 for height in (1080,720):
  source=(ROOT/'eval/preview/composition.fixture.tsx').read_text()
  if height==720:
   source=source.replace('composition-preview/1080','composition-preview/720')
   source+="\njest.mock('../../src/utils/pixelUtils', () => ({ ...jest.requireActual('../../src/utils/pixelUtils'), scaleUxToDp: (value: number) => Math.round(value * 720 / 1080) }));\n"
  target=ROOT/f'app/test/calmframes/compositionExport{height}.test.tsx'
  if target.exists():raise RuntimeError('Refusing to overwrite '+str(target))
  target.write_text(source);created.append(target)
 subprocess.run(['npm','--prefix','app','test','--','--runInBand','--coverage=false','--watchman=false','--testPathPattern=compositionExport'],cwd=ROOT,check=True)
finally:
 for target in created:target.unlink()
