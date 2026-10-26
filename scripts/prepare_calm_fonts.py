"""Create static, uniquely named Vega faces from the pinned OFL inputs in .logs/font-inputs."""
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'.logs/font-inputs'; OUTPUT=ROOT/'app/assets/fonts'
items=[('Fraunces.ttf','CalmDisplaySemibold',{'wght':600,'opsz':32,'SOFT':20,'WONK':0}),('SourceSans3-Regular.ttf','CalmSansRegular',None),('SourceSans3-Semibold.ttf','CalmSansSemibold',None)]
records=[]
for filename,family,axes in items:
 source=INPUT/filename; font=TTFont(source)
 if axes: font=instantiateVariableFont(font,axes,inplace=False)
 # Unique families avoid synthetic weights and match Vega's filename convention.
 for name_id,value in [(1,family),(2,'Regular'),(3,family+'-CalmFrames'),(4,family),(6,family),(16,family),(17,'Regular')]:
  font['name'].removeNames(nameID=name_id)
  font['name'].setName(value,name_id,3,1,0x409)
  font['name'].setName(value,name_id,1,0,0)
 font.recalcTimestamp=False
 target=OUTPUT/(family+'.ttf');font.save(target)
 checked=TTFont(target)
 assert 'fvar' not in checked and checked['name'].getDebugName(1)==family
 cmap=checked.getBestCmap();digits=[checked['hmtx'][cmap[ord(c)]][0] for c in '0123456789']
 if family.startswith('CalmSans'): assert len(set(digits))==1, digits
 records.append({'file':target.name,'family':family,'axes':axes,'inputSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'digitAdvanceWidths':digits,'unitsPerEm':checked['head'].unitsPerEm,'variable':False})
(OUTPUT/'FONT_PROVENANCE.json').write_text(json.dumps({'sources':{'Fraunces':'https://github.com/undercasetype/Fraunces/tree/7ccdec31c6028118dce3e47fe864e3744460371d','SourceSans3':'https://github.com/adobe-fonts/source-sans/tree/87b37a2daaed80fcb8e8ccb0085c4d72ddade12e'},'license':'SIL Open Font License 1.1; included alongside the fonts','faces':records},indent=2)+'\n')
print(json.dumps(records,indent=2))
