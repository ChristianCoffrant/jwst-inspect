import json
import random
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
    for poly in obj.data.polygons:
        poly.use_smooth = True


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
    obj.scale *= 8.6 / extent
bpy.context.view_layer.update()

for material in bpy.data.materials:
    name = material.name.lower()
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        continue
    if "gold" in name or "mirror" in name or "reflector" in name:
        bsdf.inputs["Metallic"].default_value = 0.92
        bsdf.inputs["Roughness"].default_value = 0.13
        bsdf.inputs["Base Color"].default_value = (1.0, 0.67, 0.14, 1.0)
    elif "foil" in name or "silver" in name:
        bsdf.inputs["Metallic"].default_value = 0.55
        bsdf.inputs["Roughness"].default_value = 0.22
    elif "black" in name:
        bsdf.inputs["Base Color"].default_value = (0.006, 0.007, 0.008, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.50

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.color = (0.0, 0.0, 0.0)

scene = bpy.context.scene
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0.4
scene.view_settings.gamma = 1.0


def add_light(name, loc, power, size):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.size = size


add_light("hard_sun_key", (8.5, -9.5, 10.0), 1650, 3.2)
add_light("gold_mirror_kicker", (-5.5, 4.0, 7.0), 520, 2.0)
add_light("cold_space_fill", (-9.0, -4.0, 3.5), 150, 7.5)
add_light("sunshield_edge_rim", (4.0, 10.0, 4.0), 460, 2.4)

star_mat = bpy.data.materials.new("star_emission")
star_mat.use_nodes = True
nodes = star_mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Emission Color"].default_value = (1.0, 0.95, 0.82, 1.0)
bsdf.inputs["Emission Strength"].default_value = 2.5
random.seed(17)
for index in range(360):
    x = random.uniform(-38, 38)
    y = random.uniform(12, 42)
    z = random.uniform(-14, 24)
    radius = random.uniform(0.012, 0.038)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=radius, location=(x, y, z))
    star = bpy.context.object
    star.name = f"star_{index:03d}"
    star.data.materials.append(star_mat)

bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera
camera.data.lens = 54
camera.data.dof.use_dof = True
camera.data.dof.aperture_fstop = 10.0


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def configure_cycles(samples):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 9
    device_note = "cpu"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for device_type in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()
                for device in prefs.devices:
                    device.use = True
                scene.cycles.device = "GPU"
                device_note = device_type.lower()
                break
            except Exception:
                scene.cycles.device = "CPU"
    except Exception:
        scene.cycles.device = "CPU"
    return device_note


def configure_eevee():
    available = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available else "BLENDER_EEVEE"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 96
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 4
        scene.eevee.gtao_factor = 1.5
    return "eevee"


def render(path, engine, camera_loc, target, lens, samples):
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    camera.data.lens = lens
    camera.location = Vector(camera_loc)
    look_at(camera, target)
    camera.data.dof.focus_distance = (camera.location - Vector(target)).length
    if engine == "cycles":
        device_note = configure_cycles(samples)
    else:
        device_note = configure_eevee()
    scene.render.filepath = str(out / path)
    bpy.ops.render.render(write_still=True)
    return device_note


renders = [
    ("nasa_jwst_cycles_v2_mirror_close.png", "cycles", (5.2, -7.4, 3.8), (0.1, -0.1, 0.9), 72, 128),
    ("nasa_jwst_cycles_v2_sunshield_sweep.png", "cycles", (-6.4, -8.2, 3.2), (-0.9, 0.2, -1.2), 48, 128),
    ("nasa_jwst_eevee_v2_raster_overview.png", "eevee", (7.2, -9.0, 4.8), (-0.2, 0.0, 0.0), 50, 96),
]

status = "success"
errors = []
device_notes = {}
for path, engine, loc, target, lens, samples in renders:
    try:
        device_notes[path] = render(path, engine, loc, target, lens, samples)
    except Exception as exc:
        status = "partial" if any(Path(out / row[0]).exists() for row in renders) else "failed"
        errors.append({"path": path, "error": repr(exc)})

manifest = {
    "status": status,
    "source_asset": "NASA 3D Resources James Webb Space Telescope (B) GLB",
    "source_url": "https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/",
    "renderer": "Blender 4.2 Cycles and EEVEE on Vast.ai RTX 5090",
    "device_notes": device_notes,
    "outputs": [row[0] for row in renders if Path(out / row[0]).exists()],
    "errors": errors,
}
(out / "visual_rescue_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
