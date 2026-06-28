from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the official NASA detailed JWST STL package.")
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


def set_principled(mat, color, metallic: float, roughness: float, emission: float = 0.0) -> None:
    nodes, _links, bsdf = material_nodes(mat)
    if not bsdf:
        return
    set_input(bsdf, "Base Color", color)
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", roughness)
    if emission > 0:
        set_input(bsdf, "Emission Color", color)
        set_input(bsdf, "Emission Strength", emission)
    mat.diffuse_color = color


def make_mat(name: str, color, metallic: float, roughness: float, emission: float = 0.0):
    mat = bpy.data.materials.new(name)
    set_principled(mat, color, metallic, roughness, emission)
    return mat


def add_bump(mat, scale: float, strength: float, distance: float) -> None:
    nodes, links, bsdf = material_nodes(mat)
    if not bsdf:
        return
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.54
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
    noise.inputs["Roughness"].default_value = 0.44
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = low_color
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = high_color
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


def add_gold_cell_shader(mat) -> None:
    nodes, links, bsdf = material_nodes(mat)
    if not bsdf:
        return
    try:
        voronoi = nodes.new(type="ShaderNodeTexVoronoi")
        voronoi.inputs["Scale"].default_value = 3.4
        voronoi.inputs["Randomness"].default_value = 0.18
        try:
            voronoi.feature = "DISTANCE_TO_EDGE"
        except Exception:
            pass
        ramp = nodes.new(type="ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.018
        ramp.color_ramp.elements[0].color = (0.48, 0.26, 0.035, 1)
        ramp.color_ramp.elements[1].position = 0.10
        ramp.color_ramp.elements[1].color = (1.0, 0.72, 0.13, 1)
        output = voronoi.outputs.get("Distance") or voronoi.outputs[0]
        links.new(output, ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    except Exception:
        return


def import_stl(filepath: Path) -> list[bpy.types.Object]:
    before = set(bpy.context.scene.objects)
    try:
        bpy.ops.wm.stl_import(filepath=str(filepath))
    except Exception:
        bpy.ops.import_mesh.stl(filepath=str(filepath))
    return [obj for obj in bpy.context.scene.objects if obj not in before and obj.type == "MESH"]


def classify_material(path: Path, mats: dict[str, bpy.types.Material]) -> str:
    name = path.name.lower()
    if "primary mirror" in name:
        return "gold_mirror"
    if "sunshield" in name:
        return "sunshield_foil"
    if "solar array" in name:
        return "solar_panel"
    if "lower bus" in name or "aft cover" in name or "forward cover" in name:
        return "black_blanket"
    if "secondary mirror" in name:
        return "dark_truss"
    if "boom" in name or "arm" in name or "mount" in name or "pin connection" in name or "flap" in name:
        return "dark_truss"
    return "brushed_structure"


def build_materials() -> dict[str, bpy.types.Material]:
    mats = {
        "gold_mirror": make_mat("v4_gold_coated_mirror", (1.0, 0.65, 0.08, 1), 0.30, 0.26, 0.012),
        "sunshield_foil": make_mat("v4_silver_kapton", (0.68, 0.67, 0.64, 1), 0.84, 0.15),
        "solar_panel": make_mat("v4_blue_black_solar", (0.015, 0.035, 0.13, 1), 0.18, 0.24),
        "black_blanket": make_mat("v4_black_thermal_blanket", (0.018, 0.017, 0.016, 1), 0.18, 0.64),
        "dark_truss": make_mat("v4_dark_anodized_truss", (0.07, 0.067, 0.062, 1), 0.45, 0.34),
        "brushed_structure": make_mat("v4_brushed_structure", (0.58, 0.57, 0.54, 1), 0.54, 0.30),
    }
    add_color_noise(mats["gold_mirror"], 9.0, (0.88, 0.52, 0.06, 1), (1.0, 0.80, 0.20, 1))
    add_bump(mats["gold_mirror"], 42.0, 0.002, 0.001)
    add_color_noise(mats["sunshield_foil"], 18.0, (0.42, 0.41, 0.40, 1), (0.96, 0.92, 0.86, 1))
    add_bump(mats["sunshield_foil"], 74.0, 0.018, 0.008)
    add_bump(mats["black_blanket"], 58.0, 0.03, 0.014)
    add_bump(mats["dark_truss"], 40.0, 0.01, 0.004)
    return mats


def load_detailed_stl_scene(repo_root: Path) -> tuple[dict[str, str], list[bpy.types.Object]]:
    stl_root = repo_root / "assets" / "official_nasa" / "jwst_detailed_stl"
    mats = build_materials()
    part_map: dict[str, str] = {}
    mesh_objects: list[bpy.types.Object] = []
    for path in sorted(stl_root.glob("*.stl")):
        if path.name.endswith(".stl") and ".1" not in path.name and ".2" not in path.name and ".3" not in path.name and ".4" not in path.name and ".5" not in path.name and ".6" not in path.name and ".7" not in path.name and ".8" not in path.name and ".9" not in path.name:
            continue
        imported = import_stl(path)
        mat_key = classify_material(path, mats)
        for obj in imported:
            obj.name = path.stem[:58]
            obj.data.materials.append(mats[mat_key])
            mesh_objects.append(obj)
        part_map[path.name] = mat_key

    corners: list[Vector] = []
    for obj in mesh_objects:
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    min_v = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    max_v = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    center = (min_v + max_v) * 0.5
    scale = 16.0 / max((max_v - min_v).length, 1e-6)
    for obj in mesh_objects:
        mesh = obj.data
        world = obj.matrix_world.copy()
        for vertex in mesh.vertices:
            vertex.co = (world @ vertex.co - center) * scale
        obj.matrix_world = Matrix.Identity(4)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
        normal = obj.modifiers.new("v4_weighted_normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
        obj.select_set(False)
    return part_map, mesh_objects


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


def add_primary_mirror_hex_lines(mesh_objects: list[bpy.types.Object]) -> None:
    primary_objects = [obj for obj in mesh_objects if ".11 Primary mirror" in obj.name]
    if not primary_objects:
        return
    vertices: list[Vector] = []
    for obj in primary_objects:
        vertices.extend(obj.matrix_world @ vertex.co for vertex in obj.data.vertices)
    if not vertices:
        return
    min_y, max_y = min(v.y for v in vertices), max(v.y for v in vertices)
    span_y = max_y - min_y
    front = [v for v in vertices if v.y > max_y - span_y * 0.34]
    if len(front) < 30:
        front = vertices
    # Use the full primary mirror footprint for placement. The extreme front
    # vertices mostly describe the central instrument protrusion, not the mirror.
    min_x, max_x = min(v.x for v in vertices), max(v.x for v in vertices)
    min_z, max_z = min(v.z for v in vertices), max(v.z for v in vertices)
    center_x = (min_x + max_x) * 0.5
    center_z = (min_z + max_z) * 0.5
    span_x = max_x - min_x
    span_z = max_z - min_z
    mirror_span = min(span_x, span_z)
    hex_radius = mirror_span / 5.9
    line_y = max_y + span_y * 0.035
    line_mat = make_mat("v4_attached_gold_mirror_hex_seams", (0.32, 0.16, 0.025, 1), 0.24, 0.42, 0.004)
    axial_centers: list[tuple[int, int]] = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= 2 and not (q == 0 and r == 0):
                axial_centers.append((q, r))
    for idx, (q, r) in enumerate(axial_centers):
        x = hex_radius * math.sqrt(3) * (q + r / 2)
        z = hex_radius * 1.5 * r
        if abs(x) > span_x * 0.47 or abs(z) > span_z * 0.47:
            continue
        tile_center = Vector((center_x + x, line_y, center_z + z))
        points: list[Vector] = []
        for corner in range(7):
            angle = math.radians(30 + corner * 60)
            points.append(
                Vector(
                    (
                        tile_center.x + math.cos(angle) * hex_radius * 0.54,
                        tile_center.y,
                        tile_center.z + math.sin(angle) * hex_radius * 0.54,
                    )
                )
            )
        add_curve_polyline(f"v4_attached_mirror_hex_{idx:02d}", points, line_mat, mirror_span * 0.0018)


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


def add_starfield(seed: int, count: int = 90) -> None:
    random.seed(seed)
    star_mat = make_emission_mat("v4_star_emission", (1, 1, 1, 1), 1.4)
    for idx in range(count):
        radius = random.uniform(90, 190)
        theta = random.uniform(0, math.tau)
        z = random.uniform(-0.72, 0.72)
        planar = math.sqrt(max(0.0, 1.0 - z * z))
        loc = Vector((radius * planar * math.cos(theta), radius * planar * math.sin(theta), radius * z))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=3, radius=random.uniform(0.006, 0.030), location=loc)
        star = bpy.context.object
        star.name = f"v4_star_{idx:04d}"
        star.data.materials.append(star_mat)


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(name: str, loc: tuple[float, float, float], target: tuple[float, float, float], lens: float, ortho_scale: float | None = None):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = name
    if ortho_scale is None:
        cam.data.lens = lens
    else:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (Vector(target) - cam.location).length
    cam.data.dof.aperture_fstop = 10.0
    look_at(cam, Vector(target))
    return cam


def add_lighting() -> None:
    world = bpy.data.worlds.new("v4_deep_space_black")
    world.color = (0.001, 0.001, 0.004)
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="SUN", location=(-35, -55, 42))
    sun = bpy.context.object
    sun.name = "v4_hard_solar_key"
    sun.data.energy = 4.6
    look_at(sun, Vector((0, 0, 0)))
    for name, loc, target, energy, size in [
        ("v4_negative_y_gold_fill", (6.5, -21, 7.0), (0, 0, 1.1), 320, 10),
        ("v4_positive_y_gold_fill", (6.5, 21, 7.0), (0, 0, 1.1), 880, 11),
        ("v4_positive_y_soft_mirror_box", (-5.5, 19, 4.5), (0, 0, 1.0), 460, 13),
        ("v4_sunshield_sheen_fill", (-6.5, 18, 2.0), (0, 0, -0.2), 240, 14),
    ]:
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        look_at(light, Vector(target))


def render_still(path: Path, cam, samples: int) -> None:
    bpy.context.scene.camera = cam
    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_pass(repo_root: Path, output_dir: Path, width: int, height: int, samples: int) -> None:
    clear_scene()
    setup_render(width, height, samples)
    part_map, mesh_objects = load_detailed_stl_scene(repo_root)
    # Loop19-24 proved geometric mirror seam overlays are less trustworthy than
    # the official STL surface: they can drift visibly off the curved mirror edge.
    # The final branch keeps detail in the official mesh and material response.
    add_starfield(9912, 70)
    add_lighting()
    loops = [
        ("loop25", "final clean STL full body", add_camera("v4_final_clean_full_body", (8.8, 29, 5.8), (0, 0, 0.2), 44, 12.8), samples),
        ("loop26", "final clean mirror close", add_camera("v4_final_clean_mirror_close", (4.7, 22.5, 4.7), (0, 0, 1.1), 58), samples),
        ("loop27", "final wide SVS-style composition", add_camera("v4_final_clean_wide_svs", (-10.5, 31, 6.0), (0, 0, 0.0), 44, 14.4), samples),
        ("loop28", "final low cinematic sunshield", add_camera("v4_final_low_cinematic", (-7.8, 27.0, 2.6), (0, 0, 0.35), 42, 12.8), samples),
        ("loop29", "final positive-y inspection POV", add_camera("v4_final_inspector_pov", (7.4, 23.5, 2.2), (0, 0, 0.8), 35), samples),
        ("loop30", "final high-sample detailed STL hero", add_camera("v4_final_high_sample_candidate", (-9.2, 30, 5.6), (0, 0, 0.0), 44, 12.8), max(samples, 512)),
    ]
    manifest = {
        "render_package_id": "jwst_v4_official_detailed_stl",
        "status": "inspection_required",
        "source_asset": "NASA official detailed STL package: webb telescope model for 3D printing, detailed version",
        "source_url": "https://science.nasa.gov/asset/webb/webb-telescope-model-for-3d-printing-detailed-version/",
        "part_material_map": part_map,
        "loops": [],
    }
    for loop_id, focus, cam, loop_samples in loops:
        loop_dir = output_dir / "render_loops" / loop_id
        loop_dir.mkdir(parents=True, exist_ok=True)
        image_path = loop_dir / "rtx_cycles.png"
        render_still(image_path, cam, loop_samples)
        record = {
            "loop_id": loop_id,
            "focus": focus,
            "artifacts": {"rtx": image_path.as_posix()},
            "human_inspection_status": "pending",
            "postprocessed": False,
            "uses_official_detailed_stl": True,
        }
        (loop_dir / "visual_inspection_note.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        manifest["loops"].append(record)
    (output_dir / "v4_detailed_stl_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    render_pass(Path(args.repo_root), Path(args.output_dir), args.width, args.height, args.samples)


if __name__ == "__main__":
    main()
