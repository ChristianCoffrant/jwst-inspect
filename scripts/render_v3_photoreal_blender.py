from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a photoreal-oriented JWST pass from the official NASA GLB.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--samples", type=int, default=192)
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    return parser.parse_args(argv)


def set_input(node, name: str, value) -> None:
    if node and name in node.inputs:
        node.inputs[name].default_value = value


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def setup_render(width: int, height: int, samples: int) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.film_transparent = False
    for view_transform in ("AgX", "Standard", "Filmic"):
        try:
            scene.view_settings.view_transform = view_transform
            break
        except TypeError:
            continue
    for look in ("Medium High Contrast", "None"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 5
    try:
        scene.cycles.device = "GPU"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = True
    except Exception:
        pass


def material_nodes(mat):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    return nodes, mat.node_tree.links, bsdf


def set_principled(mat, color, metallic: float, roughness: float, alpha: float = 1.0, emission: float = 0.0) -> None:
    nodes, _links, bsdf = material_nodes(mat)
    if not bsdf:
        return
    set_input(bsdf, "Base Color", color)
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Alpha", alpha)
    if emission > 0:
        set_input(bsdf, "Emission Color", color)
        set_input(bsdf, "Emission Strength", emission)
    mat.diffuse_color = color


def add_bump(mat, scale: float, strength: float, distance: float) -> None:
    nodes, links, bsdf = material_nodes(mat)
    if not bsdf:
        return
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 12.0
    noise.inputs["Roughness"].default_value = 0.58
    bump = nodes.new(type="ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def add_color_noise(mat, scale: float, low_color, high_color) -> None:
    nodes, links, bsdf = material_nodes(mat)
    if not bsdf:
        return
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.46
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = low_color
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = high_color
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


def improve_official_materials() -> dict[str, str]:
    decisions: dict[str, str] = {}
    for mat in bpy.data.materials:
        name = (mat.name or "").lower()
        if "gold" in name or "topreflector" in name or "mirror" in name:
            set_principled(mat, (1.0, 0.63, 0.08, 1), 0.52, 0.24, emission=0.006)
            add_color_noise(mat, 10.0, (0.86, 0.48, 0.06, 1), (1.0, 0.76, 0.18, 1))
            add_bump(mat, 58.0, 0.0025, 0.0010)
            decisions[mat.name] = "beryllium_gold_mirror"
        elif "foillayer" in name and "purpley" not in name:
            set_principled(mat, (0.66, 0.65, 0.64, 1), 0.88, 0.12)
            add_color_noise(mat, 16.0, (0.47, 0.46, 0.45, 1), (0.94, 0.91, 0.84, 1))
            add_bump(mat, 58.0, 0.013, 0.006)
            decisions[mat.name] = "silver_kapton_sunshield"
        elif "purpley" in name:
            set_principled(mat, (0.84, 0.47, 0.78, 1), 0.68, 0.17)
            add_color_noise(mat, 13.0, (0.42, 0.20, 0.52, 1), (0.95, 0.48, 0.88, 1))
            add_bump(mat, 42.0, 0.012, 0.006)
            decisions[mat.name] = "purple_kapton_underside"
        elif "solar" in name:
            set_principled(mat, (0.015, 0.035, 0.13, 1), 0.15, 0.22)
            add_bump(mat, 90.0, 0.025, 0.010)
            decisions[mat.name] = "blue_black_solar_panel"
        elif "silver" in name or "bracket" in name or "default" in name or "white" in name:
            set_principled(mat, (0.62, 0.62, 0.60, 1), 0.58, 0.26)
            add_bump(mat, 75.0, 0.006, 0.003)
            decisions[mat.name] = "brushed_silver_structure"
        elif "black" in name or "instrument" in name or "paint" in name or "sc_" in name:
            set_principled(mat, (0.018, 0.017, 0.016, 1), 0.20, 0.62)
            add_bump(mat, 60.0, 0.035, 0.018)
            decisions[mat.name] = "black_thermal_blanket"
        else:
            set_principled(mat, (0.45, 0.43, 0.39, 1), 0.35, 0.45)
            decisions[mat.name] = "neutral_spacecraft_material"
    return decisions


def import_official_jwst(repo_root: Path) -> list[bpy.types.Object]:
    glb = repo_root / "assets" / "official_nasa" / "James Webb Space Telescope (B).glb"
    bpy.ops.import_scene.gltf(filepath=str(glb))
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in mesh_objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
        bevel = obj.modifiers.new("small_real_edge_bevel", "BEVEL")
        bevel.width = 0.006
        bevel.segments = 1
        bevel.affect = "EDGES"
        normal = obj.modifiers.new("weighted_spacecraft_normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
        obj.select_set(False)

    # Normalize to a stable frame while preserving official geometry proportions.
    corners: list[Vector] = []
    for obj in mesh_objects:
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    min_v = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    max_v = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    center = (min_v + max_v) * 0.5
    scale = 16.0 / max((max_v - min_v).length, 1e-6)
    for obj in mesh_objects:
        obj.location = (obj.location - center) * scale
        obj.scale = tuple(component * scale for component in obj.scale)
    return mesh_objects


def mirror_material_name(name: str) -> bool:
    lower = name.lower()
    return "gold" in lower or "topreflector" in lower or "mirror" in lower


def estimate_mirror_frame(mesh_objects: list[bpy.types.Object]) -> tuple[Vector, Vector, Vector, float] | None:
    points: list[Vector] = []
    normals: list[Vector] = []
    for obj in mesh_objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        for poly in mesh.polygons:
            mat_name = ""
            if poly.material_index < len(obj.material_slots):
                mat = obj.material_slots[poly.material_index].material
                mat_name = mat.name if mat else ""
            if not mirror_material_name(mat_name):
                continue
            world_normal = obj.matrix_world.to_3x3() @ poly.normal
            if world_normal.length > 0:
                normals.append(world_normal.normalized())
            for vertex_index in poly.vertices:
                points.append(obj.matrix_world @ mesh.vertices[vertex_index].co)
    if len(points) < 20:
        return None
    center = sum(points, Vector((0, 0, 0))) / len(points)
    normal = sum(normals, Vector((0, 0, 0)))
    if normal.length == 0:
        normal = Vector((0, -1, 0))
    normal.normalize()
    if normal.y > 0:
        normal *= -1
    basis_u = Vector((1, 0, 0)) - normal * Vector((1, 0, 0)).dot(normal)
    if basis_u.length < 0.01:
        basis_u = Vector((0, 0, 1)) - normal * Vector((0, 0, 1)).dot(normal)
    basis_u.normalize()
    basis_v = normal.cross(basis_u)
    if basis_v.z < 0:
        basis_v *= -1
    basis_v.normalize()
    projected_u = [(point - center).dot(basis_u) for point in points]
    projected_v = [(point - center).dot(basis_v) for point in points]
    span = max(max(projected_u) - min(projected_u), max(projected_v) - min(projected_v))
    return center, basis_u, basis_v, span


def add_curve_polyline(name: str, points: list[Vector], mat, bevel_depth: float) -> None:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    polyline = curve.splines.new("POLY")
    polyline.points.add(len(points) - 1)
    for point, curve_point in zip(points, polyline.points):
        curve_point.co = (point.x, point.y, point.z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)


def add_mirror_cell_accents(mesh_objects: list[bpy.types.Object]) -> None:
    frame = estimate_mirror_frame(mesh_objects)
    if frame is None:
        return
    center, basis_u, basis_v, span = frame
    line_mat = make_principled_material("v3_subtle_mirror_cell_seams", (0.34, 0.20, 0.045, 1), 0.28, 0.38)
    hex_radius = span / 8.2
    normal = basis_u.cross(basis_v)
    if normal.y > 0:
        normal *= -1
    normal.normalize()
    offset_center = center + normal * -0.035 + basis_v * 0.02
    axial_centers: list[tuple[int, int]] = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= 2 and not (q == 0 and r == 0):
                axial_centers.append((q, r))
    for idx, (q, r) in enumerate(axial_centers):
        x = hex_radius * math.sqrt(3) * (q + r / 2)
        z = hex_radius * 1.5 * r
        if abs(x) > span * 0.48 or abs(z) > span * 0.47:
            continue
        tile_center = offset_center + basis_u * x + basis_v * z
        pts: list[Vector] = []
        for corner in range(7):
            angle = math.radians(30 + corner * 60)
            pts.append(tile_center + basis_u * (math.cos(angle) * hex_radius * 0.56) + basis_v * (math.sin(angle) * hex_radius * 0.56))
        add_curve_polyline(f"v3_mirror_hex_cell_seam_{idx:02d}", pts, line_mat, span * 0.0016)


def make_emission_mat(name: str, color, strength: float):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    output = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def add_starfield(seed: int, count: int = 1200) -> None:
    random.seed(seed)
    star_mat = make_emission_mat("v3_star_emission", (1, 1, 1, 1), 1.6)
    warm_mat = make_emission_mat("v3_warm_star_emission", (1.0, 0.86, 0.62, 1), 1.2)
    blue_mat = make_emission_mat("v3_blue_star_emission", (0.62, 0.78, 1.0, 1), 1.0)
    for idx in range(count):
        radius = random.uniform(90, 190)
        theta = random.uniform(0, math.tau)
        z = random.uniform(-0.72, 0.72)
        planar = math.sqrt(max(0.0, 1.0 - z * z))
        loc = Vector((radius * planar * math.cos(theta), radius * planar * math.sin(theta), radius * z))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=3, radius=random.uniform(0.006, 0.030), location=loc)
        star = bpy.context.object
        star.name = f"v3_star_{idx:04d}"
        star.data.materials.append(random.choices([star_mat, warm_mat, blue_mat], [0.84, 0.09, 0.07])[0])


def make_principled_material(name: str, color, metallic: float, roughness: float):
    mat = bpy.data.materials.new(name)
    set_principled(mat, color, metallic, roughness)
    return mat


def add_distant_earth(mode: str) -> None:
    if mode == "none":
        return
    earth_mat = make_principled_material("v3_distant_earth_blue_limb", (0.02, 0.17, 0.42, 1), 0.0, 0.48)
    cloud_mat = make_principled_material("v3_distant_earth_clouds", (0.9, 0.94, 1.0, 1), 0.0, 0.38)
    atmosphere_mat = make_emission_mat("v3_thin_blue_atmosphere", (0.18, 0.45, 1.0, 1), 0.18)
    center = Vector((-28, 52, 18)) if mode == "limb" else Vector((-42, 70, 24))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=20, location=center)
    earth = bpy.context.object
    earth.name = "v3_distant_earth_limb"
    earth.data.materials.append(earth_mat)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=20.12, location=center)
    atmosphere = bpy.context.object
    atmosphere.name = "v3_distant_earth_atmosphere"
    atmosphere.data.materials.append(atmosphere_mat)
    for idx in range(28):
        angle = idx * 0.58
        x = center.x + math.cos(angle) * random.uniform(6, 18)
        y = center.y + math.sin(angle) * random.uniform(6, 18)
        z = center.z + random.uniform(-10, 10)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=random.uniform(0.9, 2.2), location=(x, y, z))
        cloud = bpy.context.object
        cloud.name = f"v3_distant_cloud_{idx:02d}"
        cloud.scale = (1.8, 0.38, 0.12)
        cloud.data.materials.append(cloud_mat)


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(
    name: str,
    loc: tuple[float, float, float],
    target: tuple[float, float, float],
    lens: float,
    ortho_scale: float | None = None,
):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = name
    if ortho_scale is None:
        cam.data.lens = lens
    else:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = None
    cam.data.dof.focus_distance = (Vector(target) - cam.location).length
    cam.data.dof.aperture_fstop = 9.5
    look_at(cam, Vector(target))
    return cam


def add_lighting(key_variant: str) -> None:
    world = bpy.data.worlds.new("v3_deep_space_black")
    world.color = (0.001, 0.001, 0.004)
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="SUN", location=(-30, -60, 45))
    sun = bpy.context.object
    sun.name = "v3_hard_solar_key"
    sun.data.energy = 4.2 if key_variant == "balanced" else 5.4
    look_at(sun, Vector((0, 0, 0)))
    bpy.ops.object.light_add(type="AREA", location=(7, -20, 7.2))
    fill = bpy.context.object
    fill.name = "v3_mirror_side_softbox"
    fill.data.energy = 520 if key_variant == "balanced" else 160
    fill.data.size = 10
    look_at(fill, Vector((0, -0.1, 1.15)))
    bpy.ops.object.light_add(type="SPOT", location=(3.8, -16.5, 5.4))
    mirror_spot = bpy.context.object
    mirror_spot.name = "v3_gold_mirror_spot_fill"
    mirror_spot.data.energy = 620
    mirror_spot.data.spot_size = 0.95
    mirror_spot.data.spot_blend = 0.68
    look_at(mirror_spot, Vector((0, -0.1, 1.15)))
    bpy.ops.object.light_add(type="POINT", location=(-10, 15, 8))
    rim = bpy.context.object
    rim.name = "v3_tiny_rim_glint"
    rim.data.energy = 22


def add_hidden_reflection_cards() -> None:
    cards = [
        ("v3_gold_mirror_reflection_card", (1.6, -12.8, 4.2), (5.8, 3.0, 1.0), (1.0, 0.72, 0.20, 1), 2.4),
        ("v3_sunshield_white_reflection_card", (-4.8, -12.0, 1.1), (4.6, 1.4, 1.0), (0.92, 0.88, 0.80, 1), 0.34),
        ("v3_purple_edge_reflection_card", (-7.2, -12.0, -0.7), (2.8, 1.0, 1.0), (0.9, 0.38, 0.86, 1), 0.28),
    ]
    for name, loc, scale, color, strength in cards:
        mat = make_emission_mat(f"{name}_mat", color, strength)
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        card = bpy.context.object
        card.name = name
        card.scale = scale
        card.data.materials.append(mat)
        look_at(card, Vector((0, -0.1, 0.8)))
        card.visible_camera = False


def add_inspector_craft() -> None:
    body_mat = make_principled_material("v3_inspector_dark_body", (0.035, 0.045, 0.058, 1), 0.45, 0.34)
    panel_mat = make_principled_material("v3_inspector_blue_panels", (0.02, 0.05, 0.17, 1), 0.25, 0.20)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-7.8, -24.0, 2.0))
    body = bpy.context.object
    body.name = "v3_inspector_craft_body"
    body.scale = (0.12, 0.16, 0.09)
    body.data.materials.append(body_mat)
    for x in (-0.42, 0.42):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-7.8 + x, -24.0, 2.0))
        panel = bpy.context.object
        panel.name = "v3_inspector_craft_panel"
        panel.scale = (0.24, 0.012, 0.08)
        panel.data.materials.append(panel_mat)


def render_still(path: Path, cam, samples: int) -> None:
    bpy.context.scene.camera = cam
    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_pass(repo_root: Path, output_dir: Path, width: int, height: int, samples: int) -> None:
    clear_scene()
    setup_render(width, height, samples)
    mesh_objects = import_official_jwst(repo_root)
    material_map = improve_official_materials()
    # Loop51-56 showed that free geometric mirror accents can float off the official mesh.
    # Keep visual detail material-bound unless the scene provides verified attachment points.
    add_starfield(4128, 70)
    add_inspector_craft()
    add_lighting("balanced")
    add_hidden_reflection_cards()

    loops = [
        {
            "loop_id": "loop57",
            "focus": "rollback clean full-body hero",
            "camera": add_camera("v3_loop57_clean_full_body", (8.6, -29.0, 5.6), (0.0, 0.0, 0.05), 44, ortho_scale=12.8),
            "earth": "none",
            "samples": samples,
            "inspection_notes": "Rejects the floating hex overlay and keeps only material-bound gold variation on the official model.",
        },
        {
            "loop_id": "loop58",
            "focus": "clean mirror close validation",
            "camera": add_camera("v3_loop58_clean_mirror_close", (5.1, -17.6, 4.8), (0.0, -0.1, 1.15), 60),
            "earth": "none",
            "samples": samples,
            "inspection_notes": "Checks whether material-only gold variation adds detail without fake unattached geometry.",
        },
        {
            "loop_id": "loop59",
            "focus": "clean textured Kapton shield",
            "camera": add_camera("v3_loop59_textured_kapton", (-9.0, -25.8, 3.9), (-0.35, 0.0, -0.05), 42, ortho_scale=13.2),
            "earth": "none",
            "samples": samples,
            "inspection_notes": "Checks that procedural foil variation gives the sunshield a less plastic, less flat material response.",
        },
        {
            "loop_id": "loop60",
            "focus": "NASA/SVS angle match",
            "camera": add_camera("v3_loop60_svs_angle_match", (13.0, -28.0, 5.2), (0.0, -0.1, 0.0), 42, ortho_scale=13.0),
            "earth": "none",
            "samples": samples,
            "inspection_notes": "Moves off the dead-on angle toward the official deployment composition while keeping the entire spacecraft in frame.",
        },
        {
            "loop_id": "loop61",
            "focus": "inspection-craft POV composition",
            "camera": add_camera("v3_loop61_inspector_pov", (-7.8, -24.0, 2.0), (0.0, -0.1, 0.75), 35),
            "earth": "none",
            "samples": samples,
            "inspection_notes": "Tests whether the craft POV is readable after the hero asset and lighting changes.",
        },
        {
            "loop_id": "loop62",
            "focus": "seventh-pass high-sample hero",
            "camera": add_camera("v3_loop62_high_sample_hero", (9.0, -29.5, 5.4), (0.0, 0.0, 0.02), 44, ortho_scale=12.5),
            "earth": "none",
            "samples": max(samples, 384),
            "inspection_notes": "High-sample candidate after rejecting unattached geometry and retaining only material-bound visual improvements.",
        },
    ]

    manifest = {
        "render_package_id": "jwst_v3_photoreal_recovery",
        "status": "inspection_required",
        "source_asset": "assets/official_nasa/James Webb Space Telescope (B).glb",
        "failed_branch": "v2 loops 9-20 used crude procedural replacement; v3 keeps the official GLB as the hero asset.",
        "pass_notes": "Seventh v3 pass explicitly rejects loop51-56 floating geometry and keeps only material-bound visual detail.",
        "material_decisions": material_map,
        "loops": [],
    }

    # Earth limb is scene state; create it only before the first loop that needs it.
    earth_added = False
    for item in loops:
        if item["earth"] != "none" and not earth_added:
            add_distant_earth(item["earth"])
            earth_added = True
        loop_dir = output_dir / "render_loops" / item["loop_id"]
        loop_dir.mkdir(parents=True, exist_ok=True)
        image_path = loop_dir / "rtx_cycles.png"
        render_still(image_path, item["camera"], item["samples"])
        record = {
            "loop_id": item["loop_id"],
            "focus": item["focus"],
            "artifacts": {"rtx": image_path.as_posix()},
            "human_inspection_status": "pending",
            "inspection_notes": item["inspection_notes"],
            "postprocessed": False,
            "uses_official_glb_as_visible_hero": True,
        }
        (loop_dir / "visual_inspection_note.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        manifest["loops"].append(record)
    (output_dir / "v3_photoreal_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    render_pass(Path(args.repo_root), Path(args.output_dir), args.width, args.height, args.samples)


if __name__ == "__main__":
    main()
