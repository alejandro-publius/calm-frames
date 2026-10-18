"""Exact delivery binding for the separately verified baked-ambient recipe."""
import hashlib
import json
import math

from . import PipelineError
from .flashmap_adapter import PRESETS, parse_map
from .hideplan import build_app_playback_plan


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PipelineError('Duplicate ambient report field.')
            result[key] = value
        return result
    def constant(_):
        raise PipelineError('Nonfinite ambient report measurement.')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def require(ok, message='Ambient verification binding is invalid.'):
    if not ok:
        raise PipelineError(message)


def _hash(value, length=64):
    return isinstance(value, str) and len(value) == length and all(c in '0123456789abcdef' for c in value)


def check_ambient_report(report: dict, titles: list[dict]) -> None:
    require(isinstance(titles, list) and len(titles) > 0)
    require(set(report) == {'version', 'recipe', 'passed', 'outcome', 'sourceSha256',
                            'publicKeyFingerprint', 'inputBindingRaw', 'presets'})
    require(type(report['version']) is int and report['version'] == 1 and report['recipe'] == 'baked-ambient-v1' and report['passed'] is True
            and report['outcome'] == 'cover proven drawn' and _hash(report['publicKeyFingerprint']))
    binding = strict_json(report['inputBindingRaw'])
    require(set(binding) == {'sourceSha256', 'ambientSha256', 'mapSha256', 'renditionSha256', 'metadataSha512'})
    require(_hash(binding['ambientSha256']) and binding['sourceSha256'] == report['sourceSha256'])
    require(set(report['presets']) == set(PRESETS))
    for field in ('mapSha256', 'renditionSha256', 'metadataSha512'):
        require(set(binding[field]) == set(PRESETS))
        require(all(_hash(x, 128 if field == 'metadataSha512' else 64) for x in binding[field].values()))
    for title in titles:
        require(title['sourceSha256'] == report['sourceSha256'] and title['verification']['outcome'] == report['outcome'])
        require(title['verification']['checkedInputsSha256'] == hashlib.sha256(report['inputBindingRaw'].encode()).hexdigest())
        maps = {p: parse_map(strict_json(title['maps'][p]['text'])) for p in PRESETS}
        require(all(binding['mapSha256'][p] == title['maps'][p]['sha256'] for p in PRESETS))
        require(all(m.raw['signature']['key_id'] == 'sha256:' + report['publicKeyFingerprint'] for m in maps.values()))
        for preset in PRESETS:
            proof = report['presets'][preset]
            require(set(proof) == {'metadataRaw', 'ambientAnalysis', 'outputAnalysis', 'timingAudio', 'reproductionSha256'})
            raw = proof['metadataRaw']
            require(hashlib.sha512(raw.encode()).hexdigest() == binding['metadataSha512'][preset])
            meta = strict_json(raw)
            require(set(meta) == {'version', 'recipe', 'sourceSha256', 'renditionSha256', 'ambientSha256', 'durationMs',
                                 'renditionStartOffsetMs', 'preset', 'mapSha256', 'intervals', 'audioPreserved',
                                 'frameTimingPreserved', 'analysis'})
            rendition = title['renditions'][preset]
            require(type(meta['version']) is int and meta['version'] == 1 and meta['recipe'] == report['recipe'] and meta['preset'] == preset
                    and meta['sourceSha256'] == title['sourceSha256'] and meta['ambientSha256'] == binding['ambientSha256']
                    and meta['renditionSha256'] == rendition['sha256'] == binding['renditionSha256'][preset] == proof['reproductionSha256']
                    and meta['durationMs'] == title['durationMs'] == rendition['durationMs']
                    and meta['renditionStartOffsetMs'] == rendition['startOffsetMs'] == 0
                    and meta['audioPreserved'] is True and meta['frameTimingPreserved'] is True)
            require(type(meta['renditionStartOffsetMs']) in (int, float) and set(meta['analysis']) == {'wcag', 'broadcast'})
            require(all(type(span.get(k)) in (int, float) for span in meta['intervals'] for k in ('startMs', 'endMs')))
            require(meta['mapSha256'] == {p: binding['mapSha256'][p] for p in ('wcag', 'broadcast')})
            plan = build_app_playback_plan(maps, source_sha256=title['sourceSha256'], duration_ms=title['durationMs'], preset=preset)
            require(meta['intervals'] == [{'startMs': i.start_ms, 'endMs': i.end_ms} for i in plan.intervals]
                    and bool(plan.intervals), 'Ambient intervals differ from the authenticated app plan.')
            timing = proof['timingAudio']
            require(set(timing) == {'frameCount', 'audioPacketCount', 'videoDurationRational', 'frameTimesSha256',
                                   'audioPacketsSha256', 'sourceEqualsOutput'})
            require(timing['sourceEqualsOutput'] is True and type(timing['frameCount']) is int and timing['frameCount'] > 0
                    and type(timing['audioPacketCount']) is int and timing['audioPacketCount'] >= 0
                    and _hash(timing['frameTimesSha256']) and _hash(timing['audioPacketsSha256']))
            from fractions import Fraction
            duration = float(Fraction(timing['videoDurationRational'])) * 1000
            require(math.isfinite(duration) and abs(duration - title['durationMs']) < 0.001)
            for group, expected in [('ambientAnalysis', meta['ambientSha256']), ('outputAnalysis', rendition['sha256'])]:
                require(set(proof[group]) == {'wcag', 'broadcast'})
                for profile in ('wcag', 'broadcast'):
                    entry = proof[group][profile]
                    require(set(entry) == {'raw', 'sha256'} and _hash(entry['sha256']))
                    require(hashlib.sha256(entry['raw'].encode()).hexdigest() == entry['sha256'])
                    analysis = strict_json(entry['raw'])
                    require(analysis['source']['sha256'] == expected and analysis['segments'] == []
                            and analysis['summary']['pass'] is True and analysis['profile'] == maps[profile].raw['profile'])
                    require(analysis['profile']['room']['tv_diagonal_in'] == 85 and analysis['profile']['room']['seat_distance_in'] == 48)
                    if group == 'outputAnalysis':
                        require(meta['analysis'][profile] == entry['sha256'])
