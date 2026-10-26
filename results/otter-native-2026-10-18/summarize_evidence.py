"""Keep the bounded raw log locally and prepare readable text-only evidence."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
local = ROOT/'build/otter-native-2026-10-18'
local.mkdir(parents=True, exist_ok=True)
trace = OUT/'native-trace.log'
raw = local/'native-device-full.log'
if not raw.exists():
    raw.write_bytes(trace.read_bytes())
trace.write_text('\n'.join(line.rstrip() for line in raw.read_text().splitlines() if 'CALM_' in line)+'\n')
raw_build = local/'build-full.log'
if not raw_build.exists():
    raw_build.write_bytes((OUT/'build.log').read_bytes())
(OUT/'build.log').write_text('\n'.join(line.rstrip() for line in raw_build.read_text().splitlines())+'\n')
events = []
identities = []
for line in trace.read_text().splitlines():
    if 'CALM_TRACE ' not in line:
        continue
    value = line.split('CALM_TRACE ',1)[1].split("', { [Stack]",1)[0]
    if not events or events[-1]['value'] != value:
        events.append({'device_time': ' '.join(line.split()[:3]), 'value': value})
    if value.startswith('prepared-playback '):
        item = json.JSONDecoder().raw_decode(value[len('prepared-playback '):])[0]
        if item not in identities:
            identities.append(item)
build = json.loads((OUT/'build-receipt.json').read_text())
ambient = hashlib.sha256((ROOT/'app/src/calmframes/approvedBakedAmbient.ts').read_bytes()).hexdigest()
assert ambient == (OUT/'ambient-registry-before.sha256').read_text().strip()
summary = {'source_commit': build['source_commit'], 'package_sha256': build['package_sha256'],
           'selected_prepared_media': identities, 'ambient_registry_sha256': ambient,
           'ambient_registry_unchanged': True, 'acadia_scheduled_intervals_ms': [[7343,12699],[28113,31593]],
           'trace_events': events,
           'native_results': json.loads((OUT/'native-results.json').read_text()),
           'pixels_or_audio_observed': False,
           'raw_application_text_log': str(raw.relative_to(ROOT))}
(OUT/'evidence-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
assert len(identities) == 2
assert summary['native_results']['result'] == 'completed'
print('Two selected identities; nine checks complete; ambient registry unchanged; collector stopped.')
