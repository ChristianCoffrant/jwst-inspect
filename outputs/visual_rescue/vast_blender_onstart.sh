#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
WORK=/workspace/jwst_visual_rescue
OUT="$WORK/output"
mkdir -p "$OUT"

{
  echo "visual rescue start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi || true

  apt-get update
  apt-get install -y --no-install-recommends blender ca-certificates curl python3

  cd "$WORK"
  curl -L -o jwst_nasa.glb "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/James%20Webb%20Space%20Telescope%20%28B%29/James%20Webb%20Space%20Telescope%20%28B%29.glb"
  curl -L -o jwst_nasa_preview.png "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/James%20Webb%20Space%20Telescope%20%28B%29/James%20Webb%20Space%20Telescope%20%28B%29.png"

  cat > render_jwst.py <<'PY'
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

work = Path("/workspace/jwst_visual_rescue")
out = work / "output"
out.mkdir(parents=True, exist_ok=True)
glb = work / "jwst_nasa.glb"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=str(glb))

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
for obj in meshes:
    obj.select_set(True)
bpy.ops.object.shade_smooth()

def bounds(objects):
    points = []
    for obj in objects:
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    min_v = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    max_v = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return min_v, max_v

min_v, max_v = bounds(meshes)
center = (min_v + max_v) * 0.5
extent = max(max_v.x - min_v.x, max_v.y - min_v.y, max_v.z - min_v.z)
for obj in meshes:
    obj.location -= center
    obj.scale *= 8.0 / extent
bpy.context.view_layer.update()
min_v, max_v = bounds(meshes)
center = (min_v + max_v) * 0.5

for material in bpy.data.materials:
    name = material.name.lower()
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        continue
    if "gold" in name or "mirror" in name or "reflector" in name:
        bsdf.inputs["Metallic"].default_value = 0.85
        bsdf.inputs["Roughness"].default_value = 0.18
        bsdf.inputs["Base Color"].default_value = (1.0, 0.66, 0.18, 1.0)
    elif "foil" in name or "silver" in name:
        bsdf.inputs["Metallic"].default_value = 0.35
        bsdf.inputs["Roughness"].default_value = 0.32
    elif "black" in name:
        bsdf.inputs["Base Color"].default_value = (0.015, 0.017, 0.018, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.color = (0.0, 0.0, 0.0)

def add_light(name, loc, power, size):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.size = size
    return light

add_light("large_sun_key", (8, -12, 10), 850, 5.5)
add_light("cool_fill", (-10, 7, 4), 70, 9.0)
add_light("mirror_rim", (0, 14, 8), 260, 3.0)

bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera
camera.data.lens = 42
camera.data.dof.use_dof = True
camera.data.dof.aperture_fstop = 7.5

def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def render(path, engine, camera_loc, target=(0, 0, 0), samples=96):
    camera.location = Vector(camera_loc)
    look_at(camera, target)
    camera.data.dof.focus_distance = (camera.location - Vector(target)).length
    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    if engine == "cycles":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 8
        prefs = bpy.context.preferences
        prefs.addons["cycles"].preferences.compute_device_type = "CUDA"
        for device in prefs.addons["cycles"].preferences.devices:
            device.use = True
        scene.cycles.device = "GPU"
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
        scene.eevee.taa_render_samples = 64 if hasattr(scene, "eevee") else 16
    scene.render.filepath = str(out / path)
    bpy.ops.render.render(write_still=True)

renders = [
    ("nasa_jwst_cycles_mirror_beauty.png", "cycles", (8.8, -11.5, 6.6), (0.0, 0.0, 1.2), 128),
    ("nasa_jwst_cycles_sunshield_beauty.png", "cycles", (-7.8, -10.0, 4.0), (-0.5, 0.0, -0.8), 128),
    ("nasa_jwst_eevee_raster_overview.png", "eevee", (9.5, -13.5, 7.2), (0.0, 0.0, 0.2), 48),
]

status = "success"
errors = []
for path, engine, loc, target, samples in renders:
    try:
        render(path, engine, loc, target, samples)
    except Exception as exc:
        status = "partial" if Path(out / path).exists() else "failed"
        errors.append({"path": path, "error": repr(exc)})

manifest = {
    "status": status,
    "source_asset": "NASA 3D Resources James Webb Space Telescope (B) GLB",
    "source_url": "https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/",
    "renderer": "Blender Cycles GPU plus Blender EEVEE raster preview",
    "outputs": [row[0] for row in renders if Path(out / row[0]).exists()],
    "errors": errors,
}
(out / "visual_rescue_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

  blender -b --python render_jwst.py
  cp jwst_nasa_preview.png "$OUT/nasa_official_3d_preview.png"
  echo "visual rescue done: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/onstart.log" 2>&1 || {
  echo "visual rescue failed: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/onstart.log"
  exit 0
}

tail -f /dev/null
