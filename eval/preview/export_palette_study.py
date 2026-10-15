"""Export only Home, Settings and palette state fixtures; preserve committed evidence."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
created=[]
try:
    for name in ('home','parent','palette'):
        target=ROOT/f'app/test/calmframes/duskPaletteExport-{name}.test.tsx'
        if target.exists(): raise RuntimeError(f'Refusing to overwrite {target}')
        target.write_text((ROOT/f'eval/preview/{name}.fixture.tsx').read_text()); created.append(target)
    subprocess.run(['npm','--prefix','app','test','--','--runInBand','--coverage=false','--watchman=false','--testPathPattern=duskPaletteExport|controlSurface.test'],cwd=ROOT,check=True)
finally:
    for target in created: target.unlink()
