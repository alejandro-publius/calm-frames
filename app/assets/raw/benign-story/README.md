# Harbor story: benign scene-hold demonstration

Original geometric artwork, captions and generated tone by the Calm Frames
project, dedicated to the public domain under CC0-1.0. No external artwork,
video or music is used. Text uses Pillow's built-in Aileron font renderer;
no font file is redistributed. Generator: `eval/benign_story.py`.

The original `harbor.mp4` contains no detected violations in the measured
WCAG, broadcast and extra-cautious checks at the strictest selectable room.
`measured-source.*.json` preserves those signed results. The two intervals in
`harbor.*.json` are explicitly synthetic practice holds, not detector findings.
They demonstrate scene continuity without showing flashing. Burned-in labels,
title details, playback labels and spoken cards disclose this distinction.

The app plays `harbor.precovered.mp4`, the verified extra-cautious master with
the widest demonstration guard, and runs the normal live cover over it. The
original is included to make the source checks reproducible. The source map
hash identifies the analyzed original; `verification.json` separately binds
the played rendition and every packaged artifact to their actual bytes.

Enable **English practice captions** in the player. `harbor.vtt` goes through
the existing native text-track path. A quiet continuous tone demonstrates
audible continuity. It is not narration. Both MP4s also carry a subtitle track.

Rebuild from the repository with `.venv/bin/python -m eval.benign_story`.
The generator uses the real analyzer, then the production pipeline's image,
pre-covered master, HLS, caption and signature checks. It refuses a source
that measures a violation. The temporary signing key is deleted after export;
only `demo.pub.pem` ships. Rebuilding rotates this demonstration key and its
compiled public key together, leaving the existing gradient key unchanged.

`verification.json` contains the actual pipeline checks and exact asset
hashes. It is software evidence. Native caption/image composition, audible
continuity on a device, screen timing and physical-TV validation remain
unmeasured. No clinical claim is made by this demonstration.
