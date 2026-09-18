# Test fixtures

Only files that do not flash live here.

- `calm_sweep_theora.ogv` is 24 frames of 64 by 48, a slow grey sweep, Theora in Ogg at 10
  frames per second. Frames 8 to 12 repeat frame 7 and frames 20 to 23 repeat frame 19, and Ogg
  writes a repeated frame as a zero length packet. The run at the end leaves the file's last
  decodable frame at 1.9 s of a 2.4 s duration, which is the shape that made the still and
  poster steps come back with no frame at all. It is the same 4.2 KB clip as
  `flashmap/tests/fixtures/calm_sweep_theora.ogv`, kept here as well so neither package needs
  the other's tests to run. How it is built is in that package's fixtures README.

Anything that flashes is generated into a temporary directory, measured and deleted in the same
test. Nothing that flashes is written into this folder or committed.
