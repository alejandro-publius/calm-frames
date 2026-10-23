"""Read existing debug text only. No device or capture action."""
import datetime as dt
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
source = root / 'results/forest-activation-2026-10-18/native.log'
text = source.read_text()
rows = []
active = None
for line in text.splitlines():
    stamp = dt.datetime.strptime(line[:22], '%b %d %H:%M:%S.%f').replace(year=2026)
    if "CALM_TRACE screen player'" in line and active is None:
        active = {'entry': stamp}
    if active is None:
        continue
    if 'CALM_TRACE prepared-playback ' in line and 'identity' not in active:
        raw = line.split('CALM_TRACE prepared-playback ', 1)[1].split("}',", 1)[0] + '}'
        active['identity'] = json.loads(raw)
    if 'CALM_TRACE playback picture-shown ' in line and 'ready' not in active:
        active['ready'] = stamp
    if 'CALM_TRACE playback ended' in line and 'ended' not in active:
        active['ended'] = stamp
    if 'CALM_TRACE screen player-left' in line:
        if all(key in active for key in ('identity', 'ready', 'ended')):
            rows.append({'bundle_id': active['identity']['bundleId'],
                'entry_to_readiness_log_ms': round((active['ready'] - active['entry']).total_seconds()*1000, 3),
                'ended_to_player_left_log_ms': round((stamp - active['ended']).total_seconds()*1000, 3)})
        active = None
assert len(rows) == 3
output = {'source': str(source.relative_to(root)), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'installed_source': '805f855e60870eb018b3a6a2ab36e1f7d3e887dc',
    'method': 'First occurrence per player session; duplicate collector lines ignored. Wall time of existing debug log entries.',
    'limits': 'Three individual samples. Not displayed-frame TTFF, cold launch, CPU/memory, percentile, audio, physical timing, or kit performance.',
    'new_device_operations': 0, 'samples': rows}
Path(__file__).with_name('existing-log-latency.json').write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps(output, indent=2))
