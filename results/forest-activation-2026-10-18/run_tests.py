import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent
names=set('forestActivation homeIntroduction pickerFocusReturn duskLantern copy coastalIslands playbackUi captionPlumbing returnFocus tenFoot VideoPlayerUI detailDiscovery coverHarness playerWiring homeComposition bufferingOpening cinematicComposition cinemaSelection sceneBridgeFixture otterPreview playerOpening openingAlignment playbackCardSequence playerRouteFallback titleCoverPresentation controlSurface bakedAmbient sceneBridges coveredSections coveredSectionsStrip playerSceneTimeline packagedLibrary ambientPersonalCovers openingFrame VideoHandler KidModeScreen screens profilePicker parentGate'.split())
files=sorted(str(p.relative_to(root)) for p in (root/'app/test').rglob('*') if p.name.split('.')[0] in names and p.suffix in ('.ts','.tsx') and '.test.' in p.name)
with (out/'bounded-tests.log').open('w') as log:
 result=subprocess.run(['app/node_modules/.bin/jest','--config','app/jest.config.json','--ci','--watchman=false','--coverage=false','--runInBand',*files],cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
print('Bounded test exit',result.returncode,'files',len(files))
raise SystemExit(result.returncode)
