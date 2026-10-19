"""Reproduce, verify and stage a baked-ocean catalog without granting approval."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from .ambient import media_identity, prepare_ambient_candidate
from .ambient_report import check_ambient_report, require, strict_json
from .flashmap_adapter import PRESETS
from .hashing import fingerprint, sha256_file
from .packaged_library import (
    _bounded_file,
    _check_bundle,
    _copy_checked,
    _json_text,
    _root,
    catalog_module,
    check_packaged_library,
)


def export_ambient_catalog(*, source: Path, ambient: Path, source_manifest: Path,
                           candidates: dict[str, Path], output: Path, verification_dir: Path,
                           attribution: str) -> dict:
    source, ambient, source_manifest = map(_root, (source, ambient, source_manifest))
    output, verification_dir = map(_root, (output, verification_dir))
    require(not output.exists() and not verification_dir.exists(), 'Use new export and verification directories.')
    require(set(candidates) == set(PRESETS), 'All three candidate presets are required.')
    manifest = strict_json(_bounded_file(source_manifest, source_manifest.parent, 16*1024*1024).read_bytes())
    _check_bundle(manifest, source_manifest.parent)  # Includes every map signature and exact artifact hash.
    require(len(manifest['titles']) == 1, 'This bounded export replaces one exact Acadia-style title.')
    title = manifest['titles'][0]
    require(sha256_file(source) == title['sourceSha256'], 'The actual source differs from its authenticated maps.')
    source_inputs = {source: sha256_file(source), ambient: sha256_file(ambient), source_manifest: sha256_file(source_manifest)}
    map_paths = {p: source_manifest.parent/title['maps'][p]['path'] for p in PRESETS}
    source_inputs.update({path: sha256_file(path) for path in map_paths.values()})
    candidate_hashes = {}
    old_metadata = {}
    for p, directory in candidates.items():
        directory = _root(directory)
        candidate = _bounded_file(directory/'candidate.mp4', directory, 64*1024*1024)
        raw = _bounded_file(directory/'metadata.draft.json', directory, 16384).read_bytes()
        receipt = strict_json(_bounded_file(directory/'receipt.json', directory, 65536).read_bytes())
        meta = strict_json(raw)
        require(receipt['metadataSha256'] == hashlib.sha256(raw).hexdigest()
                and meta['renditionSha256'] == sha256_file(candidate), 'Candidate metadata or media changed.')
        candidate_hashes[p] = sha256_file(candidate)
        old_metadata[p] = meta
        source_inputs[candidate] = candidate_hashes[p]
    verification_dir.mkdir(parents=True)
    proofs, metadata_hashes = {}, {}
    identity = media_identity(source)
    for p in PRESETS:
        directory = verification_dir/p
        prepare_ambient_candidate(source, ambient, maps={q: map_paths[q] for q in ('wcag', 'broadcast')},
                                  preset=p, out_dir=directory, attribution=attribution)
        require(sha256_file(directory/'candidate.mp4') == candidate_hashes[p],
                'Independent recipe reproduction differs from the proposed media.')
        draft = (directory/'metadata.draft.json').read_text()
        meta = strict_json(draft)
        require({k:v for k,v in meta.items() if k != 'analysis'} ==
                {k:v for k,v in old_metadata[p].items() if k != 'analysis'}, 'Candidate recipe metadata changed.')
        proof = {'metadataRaw': draft, 'reproductionSha256': candidate_hashes[p],
                 'timingAudio': {'sourceEqualsOutput': True, 'frameCount': len(identity['frame_times']),
                                 'audioPacketCount': len(identity['audio_packets']),
                                 'videoDurationRational': identity['video_duration'],
                                 'frameTimesSha256': fingerprint(identity['frame_times']),
                                 'audioPacketsSha256': fingerprint(identity['audio_packets'])}}
        for group, directory_name in [('ambientAnalysis', 'ambient-analysis'), ('outputAnalysis', 'output-analysis')]:
            proof[group] = {q: {'raw': (directory/directory_name/f'{q}.json').read_text(),
                                'sha256': sha256_file(directory/directory_name/f'{q}.json')}
                            for q in ('wcag', 'broadcast')}
        proofs[p] = proof
        metadata_hashes[p] = hashlib.sha512(draft.encode()).hexdigest()
    require(all(sha256_file(path) == digest for path, digest in source_inputs.items()), 'Export input changed during verification.')
    signer = hashlib.sha256(base64.b64decode(manifest['publicKeyBase64'], validate=True)).hexdigest()
    binding = {'sourceSha256': title['sourceSha256'], 'ambientSha256': sha256_file(ambient),
               'mapSha256': {p: title['maps'][p]['sha256'] for p in PRESETS},
               'renditionSha256': candidate_hashes, 'metadataSha512': metadata_hashes}
    binding_raw = _json_text(binding)
    report = {'version': 1, 'recipe': 'baked-ambient-v1', 'passed': True, 'outcome': 'cover proven drawn',
              'sourceSha256': title['sourceSha256'], 'publicKeyFingerprint': signer,
              'inputBindingRaw': binding_raw, 'presets': proofs}
    report_raw = _json_text(report)
    report_sha = hashlib.sha256(report_raw.encode()).hexdigest()
    title['verification'] = {'reportSha256': report_sha, 'checkedInputsSha256': hashlib.sha256(binding_raw.encode()).hexdigest(),
                             'outcome': report['outcome']}
    for p in PRESETS:
        require(not title['renditions'][p].get('captions'), 'Caption-bearing catalogs need a separate cue-preservation proof.')
        title['renditions'][p].update(sha256=candidate_hashes[p], durationMs=title['durationMs'], startOffsetMs=0)
        manifest['files'][title['renditions'][p]['path']] = candidate_hashes[p]
    check_ambient_report(report, [title])
    manifest.pop('bundleId')
    manifest['bundleId'] = fingerprint(manifest)
    output.mkdir(parents=True)
    bundle = output/manifest['bundleId']
    bundle.mkdir()
    for p in PRESETS:
        _copy_checked(map_paths[p], bundle/title['maps'][p]['path'], title['maps'][p]['sha256'], source_manifest.parent)
        _copy_checked(verification_dir/p/'candidate.mp4', bundle/title['renditions'][p]['path'], candidate_hashes[p], verification_dir)
    text = _json_text(manifest)
    (bundle/'manifest.json').write_text(text)
    (output/'reports').mkdir()
    (output/'reports'/f'{report_sha}.json').write_text(report_raw)
    (output/'catalog.json').write_text(text)
    (output/'catalog.ts').write_text(catalog_module(text))
    check_packaged_library(output, require_reports=True)
    return {'bundleId': manifest['bundleId'], 'catalogSha256': sha256_file(output/'catalog.json'),
            'publicKeyFingerprint': signer, 'reportSha256': report_sha, 'metadataSha512': metadata_hashes,
            'approved': False, 'output': str(output), 'existingSigner': True}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'ambient', 'source-manifest', 'wcag', 'broadcast', 'extra-cautious', 'output', 'verification-dir'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--attribution', required=True)
    args = parser.parse_args()
    print(json.dumps(export_ambient_catalog(source=args.source, ambient=args.ambient, source_manifest=args.source_manifest,
          candidates={p: getattr(args, p.replace('-', '_')) for p in PRESETS}, output=args.output,
          verification_dir=args.verification_dir, attribution=args.attribution), indent=2))


if __name__ == '__main__':
    main()
