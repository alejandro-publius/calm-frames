// Guard band simulation, driven through the app's own cover scheduler.
//
// EVAL_PLAN section 7 says the guard band ablation is measured in simulation over the flash
// maps, and that the simulation reuses app/src/calmframes/coverSchedule.ts so an ablation
// cannot drift from the shipped scheduler. So this harness imports that file rather than
// restating what it does. Node 22 strips the types.
//
// Input on stdin: {"guardBands": [...], "clips": [{"id", "durationMs", "segments": [...]}]}
// Output on stdout: the cover intervals the app would build, per clip per guard band.
// It decides nothing and compares nothing: the Python side does the arithmetic against the
// ground truth onsets.

import { buildCoverIntervals, DEFAULT_MIN_COVER_MS } from '../../app/src/calmframes/coverSchedule.ts';

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  input += chunk;
});
process.stdin.on('end', () => {
  const request = JSON.parse(input);
  const out = { minCoverMs: DEFAULT_MIN_COVER_MS, clips: {} };
  for (const clip of request.clips) {
    out.clips[clip.id] = {};
    for (const guardBandMs of request.guardBands) {
      const intervals = buildCoverIntervals(clip.segments, {
        guardBandMs,
        durationMs: clip.durationMs,
      });
      out.clips[clip.id][String(guardBandMs)] = intervals.map((interval) => ({
        startMs: interval.startMs,
        endMs: interval.endMs,
        reason: interval.reason,
      }));
    }
  }
  process.stdout.write(JSON.stringify(out));
});
