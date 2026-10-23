# Harbor: practice holds demo

The 20 second Harbor film opens on water and cuts to the bright sailboat and
lighthouse scene. Blender animates ripples and reflections in our generated
Harbor artwork, with a slow camera move. It is a 2.5D animated illustration.
The artwork, animation, captions and synthesized water ambience are supplied
under Apache-2.0. No external recording or music is used. Asset origins and
hashes are recorded in `media/LICENSES.csv` and `docs/brand/README.md`.

The source is measured under WCAG, broadcast and extra-cautious profiles at
the strictest selectable room before practice intervals are added. The
`measured-source.*.json` files record those original measurements. The two
intervals in `harbor.*.json` are scheduled practice holds, not detections.
Title details explain this before playback, and the player displays
"Practice holds" throughout this version. There is no burned-in test banner.

The app plays `harbor.precovered.mp4`, the extra-cautious master with the widest
practice guard, and runs the normal live cover over it. The source is included
for reproducibility. The source map identifies the analyzed original;
`verification.json` separately binds the rendition and packaged artifacts.

English captions describe the scene. Continuous synthesized water ambience
makes audible continuity available during holds. Both MP4s carry subtitles,
and `harbor.vtt` uses the native external text-track path.

Rebuild with `.venv/bin/python -m eval.benign_story` with Blender 4.3 or later
and ffmpeg on PATH. To reuse an existing silent render, supply `--rendered`
with its path. Reuse never skips source analysis or production checks.
A temporary signing key is deleted after export; only its public half ships.

The October 13 files have new media identities and new software evidence.
Earlier device observations describe the older geometric film. This revision
still needs its own Vega playback and recording; no device result is implied.
