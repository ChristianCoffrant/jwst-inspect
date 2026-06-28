import json
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
    obj.scale *= 8.0 / extent
bpy.context.view_layer.update()

for material in bpy.data.materials:
    name = material.name.lower()
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        continue
    if "gold" in name or "mirror" in name or "reflector" in name:
        bsdf.inputs["Metallic"].default_value = 0.88
        bsdf.inputs["Roughness"].default_value = 0.16
        bsdf.inputs["Base Color"].default_value = (1.0, 0.64, 0.16, 1.0)
    elif "foil" in name or "silver" in name:
        bsdf.inputs["Metallic"].default_value = 0.42
        bsdf.inputs["Roughness"].default_value = 0.28
    elif "black" in name:
        bsdf.inputs["Base Color"].default_value = (0.012, 0.014, 0.016, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.58

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.color = (0.0, 0.0, 0.0)


def add_light(name, loc, power, size):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.size = size


add_light("sun_key", (8, -12, 9), 900, 5.5)
add_light("cool_fill", (-10, 7, 4), 85, 9.0)
add_light("mirror_rim", (0, 14, 7), 320, 3.0)

bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera
camera.data.lens = 44
camera.data.dof.use_dof = True
camera.data.dof.aperture_fstop = 8.0


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def configure_cycles(scene, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
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


def configure_eevee(scene):
    available = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available else "BLENDER_EEVEE"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 64


def render(path, engine, camera_loc, target, samples=96):
    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    camera.location = Vector(camera_loc)
    look_at(camera, target)
    camera.data.dof.focus_distance = (camera.location - Vector(target)).length
    device_note = "raster"
    if engine == "cycles":
        device_note = configure_cycles(scene, samples)
    else:
        configure_eevee(scene)
    scene.render.filepath = str(out / path)
    bpy.ops.render.render(write_still=True)
    return device_note


renders = [
    ("nasa_jwst_cycles_mirror_beauty.png", "cycles", (8.8, -11.5, 6.6), (0.0, 0.0, 1.2), 96),
    ("nasa_jwst_cycles_sunshield_beauty.png", "cycles", (-7.8, -10.0, 4.0), (-0.5, 0.0, -0.8), 96),
    ("nasa_jwst_eevee_raster_overview.png", "eevee", (9.5, -13.5, 7.2), (0.0, 0.0, 0.2), 32),
]

status = "success"
errors = []
device_notes = {}
for path, engine, loc, target, samples in renders:
    try:
        device_notes[path] = render(path, engine, loc, target, samples)
    except Exception as exc:
        status = "partial" if any(Path(out / row[0]).exists() for row in renders) else "failed"
        errors.append({"path": path, "error": repr(exc)})

manifest = {
    "status": status,
    "source_asset": "NASA 3D Resources James Webb Space Telescope (B) GLB",
    "source_url": "https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/",
    "renderer": "Blender 4.2 Cycles plus EEVEE raster preview on Vast.ai RTX 5090",
    "device_notes": device_notes,
    "outputs": [row[0] for row in renders if Path(out / row[0]).exists()],
    "errors": errors,
}
(out / "visual_rescue_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
