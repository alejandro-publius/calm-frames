"""Render the Harbor film from the approved artwork in Blender.

This is a 2.5D animated illustration, not a fully modeled 3D harbor. Emission
materials preserve the painted colors. Three traveling wave fields deform the
water's texture coordinates; a mesh attribute protects the boat and shoreline.
The first 2.5 seconds show the wave plate, followed by a cut to the harbor and a
slow camera move. The source images are read without modification.

    .venv/bin/python -m eval.render_harbor --output build/harbor-cinematic/harbor.mp4
    .venv/bin/python -m eval.render_harbor --output build/harbor-cinematic/preview.mp4 --preview

Blender 4.3 or later and ffmpeg must be on PATH. No Python packages beyond
Blender's own modules are needed. The output contains picture only; captions,
audio, analysis, packaging and signing belong to the normal preparation tools.
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
ARTWORK = REPO / "app/assets/image/tv"
FPS = 24
DURATION_SECONDS = 20
CUT_FRAME = 61
IMAGE_WIDTH = 1944
IMAGE_HEIGHT = 809

# Coordinates refer to the unchanged artwork, from its top left. A conservative
# waterline and a padded boat silhouette stop waves pulling solid edges around.
WATERLINE = (
    (0, 418), (1180, 418), (1290, 432), (1377, 444), (1379, 490),
    (1417, 522), (1477, 544), (1570, 565), (1694, 584),
    (1820, 596), (1944, 613),
)
BOAT = (
    (1329, 394), (1340, 394), (1340, 421), (1355, 430), (1429, 584),
    (1430, 598), (1439, 603), (1437, 626), (1426, 643), (1350, 650),
    (1285, 646), (1250, 641), (1227, 626), (1205, 594), (1221, 589),
    (1323, 408),
)


def smoothstep(low: float, high: float, value: float) -> float:
    value = min(1.0, max(0.0, (value - low) / (high - low)))
    return value * value * (3.0 - 2.0 * value)


def boat_distance(x: float, y: float) -> float:
    """Signed distance to the protected silhouette, negative inside it."""
    inside = False
    distance = math.inf
    for index, (ax, ay) in enumerate(BOAT):
        bx, by = BOAT[(index + 1) % len(BOAT)]
        fraction = min(1.0, max(0.0, (
            (x - ax) * (bx - ax) + (y - ay) * (by - ay)
        ) / ((bx - ax) ** 2 + (by - ay) ** 2)))
        distance = min(distance, math.hypot(
            x - ax - fraction * (bx - ax), y - ay - fraction * (by - ay)))
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return -distance if inside else distance


def water_strength(x: float, y: float) -> float:
    shore = float(WATERLINE[-1][1])
    for (ax, ay), (bx, by) in zip(WATERLINE, WATERLINE[1:]):
        if ax <= x <= bx:
            shore = ay + (by - ay) * (x - ax) / (bx - ax)
            break
    # Motion grows towards the camera, with a broad still margin around solids.
    depth = 0.28 + 0.72 * smoothstep(410.0, 809.0, y)
    return (smoothstep(0.0, 32.0, y - shore)
            * smoothstep(12.0, 34.0, boat_distance(x, y)) * depth)


def math_node(nodes: Any, links: Any, operation: str, left: Any, right: Any = 0.0) -> Any:
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    for index, value in enumerate((left, right)):
        if isinstance(value, (float, int)):
            node.inputs[index].default_value = value
        else:
            links.new(value, node.inputs[index])
    return node.outputs[0]


def material(bpy: Any, name: str, image_path: Path, *, closeup: bool) -> Any:
    surface = bpy.data.materials.new(name)
    surface.use_nodes = True
    nodes = surface.node_tree.nodes
    links = surface.node_tree.links
    nodes.clear()
    coordinates = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coordinates.outputs["UV"], separate.inputs[0])
    u, v = separate.outputs[0], separate.outputs[1]
    clock = nodes.new("ShaderNodeValue")
    clock.name = "Seconds"
    clock.outputs[0].default_value = 0.0
    clock.outputs[0].keyframe_insert("default_value", frame=1)
    clock.outputs[0].default_value = DURATION_SECONDS
    clock.outputs[0].keyframe_insert("default_value", frame=FPS * DURATION_SECONDS + 1)
    if closeup:
        strength: Any = 1.0
    else:
        mask = nodes.new("ShaderNodeAttribute")
        mask.attribute_name = "water_strength"
        strength = mask.outputs["Fac"]

    def wave(uf: float, vf: float, speed: float) -> Any:
        phase = math_node(nodes, links, "ADD",
                          math_node(nodes, links, "MULTIPLY", u, uf),
                          math_node(nodes, links, "MULTIPLY", v, vf))
        phase = math_node(nodes, links, "SUBTRACT", phase,
                          math_node(nodes, links, "MULTIPLY", clock.outputs[0], speed))
        return math_node(nodes, links, "SINE", phase)

    long_wave = wave(8.0, 62.0, 0.68)
    short_wave = wave(-17.0, 137.0, 0.93)
    ripple = wave(27.0, 291.0, 1.24)
    dx = math_node(nodes, links, "ADD",
                   math_node(nodes, links, "MULTIPLY", long_wave, 0.0028),
                   math_node(nodes, links, "MULTIPLY", short_wave, 0.0011))
    dy = math_node(nodes, links, "ADD",
                   math_node(nodes, links, "MULTIPLY", long_wave,
                             0.0065 if closeup else 0.0032),
                   math_node(nodes, links, "MULTIPLY", short_wave,
                             0.0028 if closeup else 0.0014))
    dy = math_node(nodes, links, "ADD", dy,
                   math_node(nodes, links, "MULTIPLY", ripple, 0.00065))
    warped = nodes.new("ShaderNodeCombineXYZ")
    links.new(math_node(nodes, links, "ADD", u,
                        math_node(nodes, links, "MULTIPLY", dx, strength)), warped.inputs[0])
    links.new(math_node(nodes, links, "ADD", v,
                        math_node(nodes, links, "MULTIPLY", dy, strength)), warped.inputs[1])
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(image_path), check_existing=True)
    if not closeup and tuple(texture.image.size) != (IMAGE_WIDTH, IMAGE_HEIGHT):
        raise ValueError(f"Unexpected artwork dimensions: {image_path}")
    texture.interpolation = "Linear"
    texture.extension = "EXTEND"
    links.new(warped.outputs[0], texture.inputs["Vector"])
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    links.new(texture.outputs["Color"], emission.inputs["Color"])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(emission.outputs[0], output.inputs["Surface"])
    for curve in surface.node_tree.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "LINEAR"
    return surface


def plate(bpy: Any, name: str, surface: Any, *, closeup: bool) -> Any:
    columns, rows = 244, 102
    vertices = []
    strengths = []
    for row in range(rows + 1):
        for column in range(columns + 1):
            u, v = column / columns, row / rows
            vertices.append(((u - 0.5) * 19.44, (v - 0.5) * 8.09, 0.0))
            strengths.append(1.0 if closeup else water_strength(
                u * IMAGE_WIDTH, (1.0 - v) * IMAGE_HEIGHT))
    faces = []
    for row in range(rows):
        for column in range(columns):
            start = row * (columns + 1) + column
            faces.append((start, start + 1, start + columns + 2, start + columns + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        vertex = vertices[loop.vertex_index]
        uv_layer.data[loop.index].uv = (vertex[0] / 19.44 + 0.5, vertex[1] / 8.09 + 0.5)
    attribute = mesh.attributes.new(name="water_strength", type="FLOAT", domain="POINT")
    attribute.data.foreach_set("value", strengths)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(surface)
    for frame, hidden in ((1, not closeup), (CUT_FRAME - 1, not closeup),
                          (CUT_FRAME, closeup), (FPS * DURATION_SECONDS, closeup)):
        obj.hide_render = hidden
        obj.keyframe_insert(data_path="hide_render", frame=frame)
    return obj


def setup_scene(bpy: Any, *, preview: bool, frame_limit: int | None) -> Any:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1 if preview else 4
    scene.cycles.use_denoising = False
    scene.cycles.use_animated_seed = False
    scene.cycles.max_bounces = 0
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.use_persistent_data = True
    scene.render.resolution_x = 640 if preview else 1280
    scene.render.resolution_y = 360 if preview else 720
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.display_settings.display_device = "sRGB"
    scene.frame_start = 1
    limit = 144 if preview else FPS * DURATION_SECONDS
    scene.frame_end = min(limit, frame_limit) if frame_limit is not None else limit
    for name, filename, closeup in (
        ("Opening waves", "harbor-water.png", True),
        ("Harbor", "harbor-cinematic.png", False),
    ):
        surface = material(bpy, name, ARTWORK / filename, closeup=closeup)
        plate(bpy, name, surface, closeup=closeup)
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    scene.camera = camera
    # The right-biased crop leaves the whole lighthouse visible throughout.
    for frame, x, y, scale in (
        (1, 2.55, -0.02, 13.80), (CUT_FRAME - 1, 2.63, -0.035, 13.65),
        (CUT_FRAME, 2.52, 0.0, 14.10), (FPS * DURATION_SECONDS, 2.62, 0.015, 13.88),
    ):
        camera.location = (x, y, 10.0)
        camera.keyframe_insert(data_path="location", frame=frame)
        camera_data.ortho_scale = scale
        camera_data.keyframe_insert(data_path="ortho_scale", frame=frame)
    for animated in (camera, camera_data):
        for curve in animated.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
    scene.frame_set(1)
    return scene


def render_inside_blender(arguments: argparse.Namespace) -> dict[str, object]:
    bpy = importlib.import_module("bpy")
    started = time.monotonic()
    output = arguments.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = setup_scene(bpy, preview=arguments.preview, frame_limit=arguments.frame_limit)
    if arguments.still_frame is not None:
        scene.frame_set(arguments.still_frame)
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
    else:
        frames = output.parent / (output.stem + "-frames")
        frames.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(frames / "frame-")
        bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix(".blend")))
        bpy.ops.render.render(animation=True)
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-framerate", str(FPS), "-start_number", "1", "-i", str(frames / "frame-%04d.png"),
            "-frames:v", str(scene.frame_end), "-an", "-c:v", "libx264", "-preset", "medium",
            "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ], check=True)
    report: dict[str, object] = {
        "output": str(output), "renderer": f"Blender {bpy.app.version_string} Cycles CPU",
        "method": "2.5D artwork with masked traveling-wave UV deformation and camera motion",
        "width": scene.render.resolution_x, "height": scene.render.resolution_y,
        "fps": FPS, "frame_count": 1 if arguments.still_frame is not None else scene.frame_end,
        "render_seconds": round(time.monotonic() - started, 2),
        "audio": False, "captions": False,
    }
    output.with_suffix(".render.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def render_harbor(output: Path, *, preview: bool = False, frame_limit: int | None = None) -> Path:
    """Render a silent intermediate for the existing media preparation pipeline."""
    executable = shutil.which("blender")
    if executable is None:
        raise RuntimeError("Blender 4.3 or later must be installed to render Harbor.")
    command = [executable, "--background", "--factory-startup", "--threads", "4",
               "--python-exit-code", "1", "--python",
               str(Path(__file__).resolve()), "--", "--inside-blender", "--output", str(output)]
    if preview:
        command.append("--preview")
    if frame_limit is not None:
        command.extend(("--frame-limit", str(frame_limit)))
    subprocess.run(command, check=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", action="store_true", help="Render six seconds at 640x360.")
    parser.add_argument("--frame-limit", type=int)
    parser.add_argument("--still-frame", type=int, help="Render one numbered frame to a PNG.")
    parser.add_argument("--inside-blender", action="store_true", help=argparse.SUPPRESS)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    arguments = parser.parse_args(argv)
    if arguments.frame_limit is not None and not 1 <= arguments.frame_limit <= FPS * DURATION_SECONDS:
        parser.error("--frame-limit must be between 1 and 480")
    if arguments.still_frame is not None and not 1 <= arguments.still_frame <= FPS * DURATION_SECONDS:
        parser.error("--still-frame must be between 1 and 480")
    if arguments.inside_blender:
        print(json.dumps(render_inside_blender(arguments), indent=2))
    elif arguments.still_frame is not None:
        executable = shutil.which("blender")
        if executable is None:
            parser.error("Blender 4.3 or later is required")
        subprocess.run([executable, "--background", "--factory-startup", "--threads", "4",
                        "--python-exit-code", "1",
                        "--python", str(Path(__file__).resolve()), "--", "--inside-blender",
                        *argv], check=True)
    else:
        render_harbor(arguments.output, preview=arguments.preview,
                      frame_limit=arguments.frame_limit)


if __name__ == "__main__":
    main()
