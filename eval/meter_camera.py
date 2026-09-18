#!/usr/bin/env python3
"""Rendering for the meter's validation: a known display clip, and a simulated camera.

SAFETY, NOT NEGOTIABLE
----------------------
Everything this module writes is a strobe on purpose, and a recording of a strobe is still a
strobe. So:

- clips are written only under a scratch directory outside the repository, owner only, with a
  `HAZARD_` name;
- the job that writes one analyses it and deletes it in the same `finally` block;
- the run asserts at exit that no `HAZARD_` file survived;
- nothing here or downstream opens, plays, previews or thumbnails one. The only thing that ever
  sees these pixels is a decoder and the meter.

If you want to look at one: do not. Run `eval/meter.py run --plot` and read the graph.

What the camera model is
------------------------
A model, and labelled as one everywhere its numbers appear. It is not a measurement of any
phone. It exists so the meter can be checked against footage whose true answer is known, which
no real recording can offer. It does the things that break a naive reading of a filmed screen:

- the TV is a rectangle inside a darker room, with a bezel, so the screen has to be found;
- optical blur, so edges are soft and a small flashing patch bleeds;
- exposure gain and lens flare, so the camera's black is not the display's black;
- a plain power law encoding rather than the sRGB curve the meter assumes, so the calibration
  has something real to absorb;
- shot and read noise, so a still screen is never quite still;
- an exposure window, so a camera at 60 fps averages a fast strobe instead of sampling it.

What it does not do: rolling shutter, a display refresh beat against the shutter, autoexposure
hunting, motion, or the camera's colour matrix. `results/meter_validation.json` lists these as
what the validation does not cover.
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.spec import load_spec  # noqa: E402

__all__ = [
    "HAZARD_PREFIX",
    "scratch_dir",
    "sweep_leftovers",
    "DisplayClip",
    "CameraModel",
    "render_display_clip",
    "decode_display_frames",
    "simulate_camera_frames",
    "write_recording",
    "simulate_static_frames",
]

HAZARD_PREFIX = "HAZARD_meter_"


def scratch_dir() -> Path:
    """Where hazard clips live for the seconds they exist. Never inside the repository."""
    base = os.environ.get("CALM_METER_SCRATCH")
    if not base:
        tmp = os.environ.get("TMPDIR", "/tmp")
        base = str(Path(tmp) / "calm-frames-meter")
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def sweep_leftovers(fail: bool = True) -> int:
    """Delete anything with the hazard name that a crash left behind. Returns how many."""
    directory = scratch_dir()
    left = sorted(directory.glob(f"{HAZARD_PREFIX}*"))
    for path in left:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    if left and fail:
        raise AssertionError(
            f"{len(left)} hazard clips outlived their job: {[p.name for p in left]}"
        )
    return len(left)


# ----------------------------------------------------------------- the display clip


@dataclass(frozen=True)
class DisplayClip:
    """What the TV shows. The ground truth for a validation trial.

    `flash_hz` is the full cycle rate, so the designed number of flashes in a second is
    `flash_hz` under non overlapping pairing, which is the reading in
    flashmap/docs/SPEC_SOURCES.md. `patch_fraction` is the side of the flashing square as a share
    of the picture width, so the area of any 10 degree window it can fill is known in advance.
    """

    name: str
    flash_hz: float
    duration_ms: float = 3000.0
    display_fps: int = 120
    width: int = 320
    height: int = 180
    low_rgb: tuple[int, int, int] = (40, 40, 40)
    high_rgb: tuple[int, int, int] = (230, 230, 230)
    background_rgb: tuple[int, int, int] = (40, 40, 40)
    patch_fraction: float = 1.0
    ramp_to_rgb: tuple[int, int, int] | None = None
    crf: int = 20

    @property
    def frame_count(self) -> int:
        return int(round(self.duration_ms * self.display_fps / 1000.0))

    def half_period_frames(self) -> float | None:
        if self.flash_hz <= 0:
            return None
        return self.display_fps / (2.0 * self.flash_hz)

    def designed_flashes_per_second(self) -> float:
        """The rate a correct meter should read back, at the peak of the run."""
        return float(self.flash_hz)

    def patch_box(self) -> tuple[int, int, int, int]:
        """(y0, y1, x0, x1) of the flashing square, centred."""
        side_w = max(1, int(round(self.width * self.patch_fraction)))
        side_h = max(1, int(round(self.height * self.patch_fraction)))
        y0 = (self.height - side_h) // 2
        x0 = (self.width - side_w) // 2
        return y0, y0 + side_h, x0, x0 + side_w

    def window_coverage(self, spec=None) -> float:
        """What share of the busiest 10 degree window the flashing square can fill.

        Worked out from the geometry rather than measured, so the area rule has a truth of its
        own. A square of side s inside a window of side w covers min(1, (s/w)^2) of it when it is
        smaller than the window, and all of it when it is not.
        """
        spec = spec or load_spec()
        win_w = self.width * spec.field_width_fraction
        win_h = self.height * spec.field_height_fraction
        _, y1, _, x1 = self.patch_box()
        y0, _, x0, _ = self.patch_box()
        side_w, side_h = x1 - x0, y1 - y0
        return float(min(1.0, side_w / win_w) * min(1.0, side_h / win_h))

    def frames(self) -> list[NDArray[np.uint8]]:
        """Every frame the TV shows, drawn in 8 bit sRGB."""
        y0, y1, x0, x1 = self.patch_box()
        out: list[NDArray[np.uint8]] = []
        for index in range(self.frame_count):
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            if self.ramp_to_rgb is not None:
                position = index / max(1, self.frame_count - 1)
                colour = [
                    int(round(a + (b - a) * position))
                    for a, b in zip(self.background_rgb, self.ramp_to_rgb)
                ]
                frame[:, :] = colour
            else:
                frame[:, :] = self.background_rgb
            if self.flash_hz > 0:
                seconds = index / self.display_fps
                high = int(seconds * self.flash_hz * 2.0) % 2 == 1
                frame[y0:y1, x0:x1] = self.high_rgb if high else self.low_rgb
            out.append(frame)
        return out

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["frame_count"] = self.frame_count
        data["designed_flashes_per_second"] = self.designed_flashes_per_second()
        data["designed_window_coverage"] = self.window_coverage()
        return data


def render_display_clip(clip: DisplayClip, destination: Path) -> dict[str, object]:
    """Encode the display clip. The caller owns the file and must delete it."""
    import av

    frames = clip.frames()
    container = av.open(str(destination), "w")
    try:
        stream = container.add_stream("libx264", rate=Fraction(clip.display_fps, 1))
        stream.width = clip.width
        stream.height = clip.height
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = Fraction(1, 1000)
        stream.codec_context.color_primaries = 1
        stream.codec_context.color_trc = 1
        stream.codec_context.colorspace = 1
        stream.options = {
            "preset": "veryfast",
            "crf": str(int(clip.crf)),
            "x264-params": "scenecut=0:keyint=60",
        }
        for index, frame_array in enumerate(frames):
            frame = av.VideoFrame.from_ndarray(frame_array, format="rgb24")
            frame.pts = int(round(index * 1000.0 / clip.display_fps))
            frame.time_base = Fraction(1, 1000)
            container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
    finally:
        container.close()
    os.chmod(destination, 0o600)
    return {"frames_written": len(frames), "bytes": destination.stat().st_size}


def decode_display_frames(path: Path) -> tuple[list[NDArray[np.uint8]], list[float]]:
    """Read the clip back, so the camera sees what the encoder produced and not what we drew."""
    import av

    frames: list[NDArray[np.uint8]] = []
    times: list[float] = []
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        for frame in container.decode(stream):
            if frame.pts is None:
                continue
            frames.append(frame.to_ndarray(format="rgb24"))
            times.append(float(frame.pts * frame.time_base * 1000))
    return frames, times


# ----------------------------------------------------------------- the camera model


@dataclass(frozen=True)
class CameraModel:
    """A simulated phone pointed at a TV. Every number here is a model parameter."""

    fps: float = 240.0
    exposure_ms: float = 1000.0 / 240.0
    width: int = 384
    height: int = 216
    tv_box: tuple[float, float, float, float] = (0.13, 0.15, 0.87, 0.85)
    bezel_fraction: float = 0.02
    room_level: float = 0.015
    bezel_level: float = 0.004
    gain: float = 0.85
    flare: float = 0.012
    encoding_gamma: float = 2.2
    blur_sigma: float = 1.1
    read_noise: float = 0.0035
    shot_noise: float = 0.006
    seed: int = 20260917
    phase_fraction: float = 0.31
    crf: int = 18

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["note"] = (
            "A model of a camera, not a measurement of one. Blur, noise, gain, flare and the "
            "exposure window are chosen to be plausible, not fitted to any phone."
        )
        return data


def _gaussian_blur(image: NDArray[np.floating], sigma: float) -> NDArray[np.floating]:
    """Separable Gaussian blur, edges held. Small kernels only, which is all a lens needs here.

    Everything in the camera model runs in float32. The signal is an 8 bit picture with noise on
    it, so float32 is far more precision than the numbers carry, and it halves the memory the
    simulation moves. The meter itself works in float64.
    """
    if sigma <= 0:
        return image
    radius = max(1, int(round(3 * sigma)))
    offsets = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-(offsets**2) / (2 * sigma * sigma))
    kernel /= kernel.sum()
    padded = np.pad(image, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    out = np.zeros_like(image)
    for index, weight in enumerate(kernel):
        out += weight * padded[radius : radius + image.shape[0], index : index + image.shape[1]]
    padded = np.pad(out, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    out = np.zeros_like(image)
    for index, weight in enumerate(kernel):
        out += weight * padded[index : index + image.shape[0], radius : radius + image.shape[1]]
    return out


def _place_on_scene(
    display_linear: NDArray[np.floating], model: CameraModel
) -> NDArray[np.float32]:
    """Put the TV picture into the room, in display linear light."""
    scene = np.full((model.height, model.width, 3), model.room_level, dtype=np.float32)
    x0 = int(round(model.tv_box[0] * model.width))
    y0 = int(round(model.tv_box[1] * model.height))
    x1 = int(round(model.tv_box[2] * model.width))
    y1 = int(round(model.tv_box[3] * model.height))
    scene[y0:y1, x0:x1] = model.bezel_level
    bezel_x = max(1, int(round((x1 - x0) * model.bezel_fraction)))
    bezel_y = max(1, int(round((y1 - y0) * model.bezel_fraction)))
    px0, py0 = x0 + bezel_x, y0 + bezel_y
    px1, py1 = x1 - bezel_x, y1 - bezel_y
    target_h, target_w = py1 - py0, px1 - px0
    source_h, source_w = display_linear.shape[:2]
    rows = (np.arange(target_h) * source_h // target_h).clip(0, source_h - 1)
    cols = (np.arange(target_w) * source_w // target_w).clip(0, source_w - 1)
    scene[py0:py1, px0:px1] = display_linear[np.ix_(rows, cols)]
    return scene


def simulate_camera_frames(
    display_frames: list[NDArray[np.uint8]],
    display_times_ms: list[float],
    model: CameraModel,
) -> tuple[list[NDArray[np.uint8]], list[float]]:
    """Film the display clip with the simulated camera.

    Each camera frame is the average of the display frames shown during its exposure window,
    which is why a camera at 60 fps reads a fast strobe as something shallower than it is.
    """
    spec = load_spec()
    rng = np.random.default_rng(model.seed)
    display_linear = [
        spec.srgb_to_linear(np.asarray(f, dtype=np.float64) / 255.0).astype(np.float32)
        for f in display_frames
    ]
    times = np.asarray(display_times_ms, dtype=np.float64)
    if len(times) < 2:
        raise ValueError("need at least two display frames to film")
    frame_ms = float(np.median(np.diff(times)))
    total_ms = times[-1] + frame_ms

    camera_step = 1000.0 / model.fps
    start = model.phase_fraction * camera_step
    frames: list[NDArray[np.uint8]] = []
    stamps: list[float] = []
    time_ms = start
    while time_ms + model.exposure_ms <= total_ms:
        window_start, window_end = time_ms, time_ms + model.exposure_ms
        first = int(np.searchsorted(times, window_start, side="right") - 1)
        last = int(np.searchsorted(times, window_end, side="right") - 1)
        first = max(0, min(first, len(display_linear) - 1))
        last = max(first, min(last, len(display_linear) - 1))
        if last == first:
            integrated = display_linear[first]
        else:
            weights = []
            for index in range(first, last + 1):
                frame_start = times[index]
                frame_end = times[index + 1] if index + 1 < len(times) else total_ms
                overlap = min(window_end, frame_end) - max(window_start, frame_start)
                weights.append(max(0.0, overlap))
            total_weight = sum(weights)
            integrated = np.zeros_like(display_linear[first])
            for index, weight in zip(range(first, last + 1), weights):
                if weight > 0:
                    integrated = integrated + display_linear[index] * (weight / total_weight)

        scene = _place_on_scene(integrated, model)
        scene = _gaussian_blur(scene, model.blur_sigma)
        sensor = scene * np.float32(model.gain) + np.float32(model.flare)
        noise = rng.standard_normal(size=sensor.shape, dtype=np.float32)
        sensor = sensor + noise * (
            np.float32(model.read_noise)
            + np.float32(model.shot_noise) * np.sqrt(np.maximum(sensor, np.float32(0.0)))
        )
        sensor = np.clip(sensor, 0.0, 1.0)
        encoded = np.clip(
            np.round(255.0 * sensor ** np.float32(1.0 / model.encoding_gamma)), 0, 255
        )
        frames.append(encoded.astype(np.uint8))
        stamps.append(time_ms)
        time_ms += camera_step
    return frames, stamps


def simulate_static_frames(
    display_image: NDArray[np.uint8], model: CameraModel, count: int = 8
) -> list[NDArray[np.uint8]]:
    """Film a still picture, for the step chart and the gray field.

    A still chart is not hazardous, so it never becomes a file. It stays in memory.
    """
    step_ms = 1000.0 / model.fps
    held = count + 3
    display = [display_image] * held
    times = [index * step_ms for index in range(held)]
    frames, _ = simulate_camera_frames(display, times, model)
    if len(frames) < count:
        raise RuntimeError(
            f"the camera model produced {len(frames)} frames of a still picture, needed {count}"
        )
    return frames[:count]


def write_recording(
    frames: list[NDArray[np.uint8]],
    times_ms: list[float],
    destination: Path,
    model: CameraModel,
) -> dict[str, object]:
    """Encode the simulated recording, so the meter reads a file the way it will on the night."""
    import av

    container = av.open(str(destination), "w")
    try:
        rate = Fraction(int(round(model.fps)), 1)
        stream = container.add_stream("libx264", rate=rate)
        stream.width = frames[0].shape[1]
        stream.height = frames[0].shape[0]
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 100000)
        stream.codec_context.time_base = Fraction(1, 100000)
        stream.codec_context.color_primaries = 1
        stream.codec_context.color_trc = 1
        stream.codec_context.colorspace = 1
        stream.options = {
            "preset": "veryfast",
            "crf": str(int(model.crf)),
            "x264-params": "scenecut=0:keyint=120",
        }
        for array, time_ms in zip(frames, times_ms):
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            frame.pts = int(round(time_ms * 100.0))
            frame.time_base = Fraction(1, 100000)
            container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
    finally:
        container.close()
    os.chmod(destination, 0o600)
    return {"frames_written": len(frames), "bytes": destination.stat().st_size}
