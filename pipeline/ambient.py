"""Unsigned, local-only baked ambient candidates. Never signs or exports a catalog.

A solid backing removes source pixels before any replacement is composited.
Only source audio is mapped. Every source PTS and audio packet is checked after
encoding; both the replacement and complete result go through the unchanged
room-aware analyzers. Failed candidates remain unapproved diagnostic artifacts.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from . import PipelineError, ffmpegtool
from .flashmap_adapter import FlashmapAdapter, load_map
from .hashing import sha256_file
from .hideplan import build_app_playback_plan
from .probe import probe_video
from .render import _colour_tag_args, _subtitle_plan


def media_identity(path: Path) -> dict:
    video = ffmpegtool.ffprobe_json(['-select_streams', 'v:0', '-show_streams',
                                     '-show_frames', '-show_entries',
                                     'stream=time_base,duration_ts,start_pts:frame=pts', str(path)])
    audio = ffmpegtool.ffprobe_json(['-select_streams', 'a', '-show_packets',
                                     '-show_data_hash', 'sha256', '-show_entries',
                                     'packet=stream_index,pts,dts,duration,data_hash', str(path)])
    stream = video['streams'][0]
    time_base = Fraction(stream['time_base'])
    return {'frame_times': [str(int(f['pts']) * time_base) for f in video['frames']],
            'video_duration': str(int(stream['duration_ts']) * time_base),
            'video_start': str(int(stream.get('start_pts', 0)) * time_base),
            'time_base': stream['time_base'], 'audio_packets': audio.get('packets', [])}


def _clean_analysis(client: FlashmapAdapter, media: Path, root: Path) -> dict:
    reports = {}
    for profile in ('wcag', 'broadcast'):
        path = root / f'{profile}.json'
        doc = client.analyze(media, profile=profile, out_path=path, diag_in=85, distance_ft=4)
        if doc.source_sha256 != sha256_file(media) or doc.profile != profile or not doc.is_clean:
            raise PipelineError(f'{media.name}: {profile} replacement analysis rejected; see {path}')
        reports[profile] = sha256_file(path)
    return reports


def prepare_ambient_candidate(source: Path, ambient: Path, *, maps: dict[str, Path],
                              preset: str, out_dir: Path, attribution: str,
                              client: FlashmapAdapter | None = None) -> dict:
    """Create a new isolated draft directory; no trust or signing material is read."""
    source, ambient, out_dir = Path(source), Path(ambient), Path(out_dir)
    if not attribution.strip():
        raise PipelineError('Replacement provenance/attribution is required.')
    if out_dir.exists():
        raise PipelineError('Use a new candidate directory; existing evidence is never overwritten.')
    client = client or FlashmapAdapter()
    if set(maps) != {'wcag', 'broadcast'}:
        raise PipelineError('Both exact source profiles are required for the review binding.')
    inputs = {path: sha256_file(path) for path in [source, ambient, *maps.values()]}
    source_hash = inputs[source]
    source_probe, ambient_probe = probe_video(source), probe_video(ambient)
    plan = build_app_playback_plan({name: load_map(path) for name, path in maps.items()},
                                  source_sha256=source_hash, duration_ms=source_probe.duration_ms,
                                  preset=preset)
    if not plan.intervals:
        raise PipelineError('No covered intervals need replacement.')
    if ambient_probe.has_audio or ambient_probe.has_subtitles:
        raise PipelineError('Use an audio-free, subtitle-free replacement asset.')
    if ambient_probe.duration_ms < max(i.duration_ms for i in plan.intervals) + 100:
        raise PipelineError('Replacement must outlast every covered interval; no looping or short EOF.')
    identity = media_identity(source)
    if identity['video_start'] != '0' or not identity['frame_times']:
        raise PipelineError('This bounded recipe requires a zero-start source timeline.')
    out_dir.mkdir(parents=True)
    receipt = {'status': 'rejected', 'approved': False, 'signed': False, 'preset': preset,
               'sourceSha256': source_hash, 'ambientSha256': sha256_file(ambient),
               'attribution': attribution, 'intervals': [dict(startMs=i.start_ms, endMs=i.end_ms)
                                                        for i in plan.intervals]}
    try:
        receipt['ambientAnalysis'] = _clean_analysis(client, ambient, out_dir / 'ambient-analysis')
        terms = [f'gte(t,{i.start_ms / 1000:.9f})*lt(t,{i.end_ms / 1000:.9f})' for i in plan.intervals]
        # Backing does not depend on ambient frames/EOF and never exposes raw covered pixels.
        graph = [f"[0:v]drawbox=color=black:t=fill:enable='{'+'.join(terms)}'[base0]"]
        args = ['-i', str(source)]
        for index, (interval, term) in enumerate(zip(plan.intervals, terms), 1):
            args += ['-i', str(ambient)]
            graph += [f'[{index}:v]scale={source_probe.width}:{source_probe.height},setsar=1,'
                      f'format=yuv420p,setpts=PTS-STARTPTS+{interval.start_ms / 1000:.9f}/TB[a{index}]',
                      f"[base{index-1}][a{index}]overlay=eof_action=pass:repeatlast=0:"
                      f"enable='{term}'[base{index}]"]
        args += ['-filter_complex_threads', '1', '-filter_complex', ';'.join(graph),
                 '-map', f'[base{len(plan.intervals)}]', '-map', '0:a?', '-c:a', 'copy']
        keep_subs, skipped = _subtitle_plan(source_probe)
        if skipped:
            raise PipelineError('This recipe refuses caption formats it cannot preserve.')
        if keep_subs:
            args += ['-map', '0:s', '-c:s', 'copy']
        output = out_dir / 'candidate.mp4'
        args += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                 '-fps_mode', 'passthrough', '-enc_time_base', identity['time_base'],
                 '-video_track_timescale', str(Fraction(identity['time_base']).denominator)]
        args += _colour_tag_args(source_probe) + ['-movflags', '+faststart', str(output)]
        ffmpegtool.run_ffmpeg(args)
        actual = media_identity(output)
        for field in ('frame_times', 'video_duration', 'video_start', 'audio_packets'):
            if actual[field] != identity[field]:
                raise PipelineError(f'Prepared candidate changed source {field}.')
        receipt['timingAudioExact'] = True
        output_hash = sha256_file(output)
        receipt['outputAnalysis'] = _clean_analysis(client, output, out_dir / 'output-analysis')
        if any(sha256_file(path) != digest for path, digest in inputs.items()) or sha256_file(output) != output_hash:
            raise PipelineError('Input or output bytes changed during preparation.')
        # This draft is the exact review input for future compiled approval. It is NOT an approval.
        metadata = {'version': 1, 'recipe': 'baked-ambient-v1', 'sourceSha256': source_hash,
                    'renditionSha256': sha256_file(output), 'ambientSha256': sha256_file(ambient),
                    'durationMs': source_probe.duration_ms, 'renditionStartOffsetMs': 0,
                    'preset': preset, 'mapSha256': {k: sha256_file(v) for k, v in sorted(maps.items())},
                    'intervals': receipt['intervals'], 'audioPreserved': True,
                    'frameTimingPreserved': True, 'analysis': receipt['outputAnalysis']}
        (out_dir / 'metadata.draft.json').write_text(json.dumps(metadata, indent=2) + '\n')
        receipt.update(status='prepared-unapproved', renditionSha256=metadata['renditionSha256'],
                       metadataSha256=sha256_file(out_dir / 'metadata.draft.json'),
                       frameCount=len(actual['frame_times']), audioPacketCount=len(actual['audio_packets']))
        return receipt
    except Exception as error:
        receipt['error'] = str(error)
        raise
    finally:
        (out_dir / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--ambient', type=Path, required=True)
    parser.add_argument('--wcag-map', type=Path, required=True)
    parser.add_argument('--broadcast-map', type=Path, required=True)
    parser.add_argument('--preset', choices=['wcag', 'broadcast', 'extra-cautious'], required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--attribution', required=True)
    args = parser.parse_args()
    result = prepare_ambient_candidate(args.source, args.ambient,
                                       maps={'wcag': args.wcag_map, 'broadcast': args.broadcast_map},
                                       preset=args.preset, out_dir=args.out_dir, attribution=args.attribution)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
