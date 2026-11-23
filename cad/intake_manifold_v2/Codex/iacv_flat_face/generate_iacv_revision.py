"""Add a sealed throttle-face feed to the extended-neck Codex V2."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

HERE = Path(__file__).resolve().parent
CODEX = HERE.parent
PHOTO = CODEX / "fitment/factory_photo_plate"
EXTENDED = CODEX / "neck_bracket_revision/verified"
sys.dont_write_bytecode = True
sys.path[:0] = [str(CODEX), str(PHOTO), str(CODEX / "airflow_regression")]

import manifold3d as md
import numpy as np
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
import trimesh

import generate_intake_manifold_v2_codex as gen
from build_fit_plate import project, smooth_curve
from local_job import one_job
from verify_geometry import FULL, LEFT, RIGHT, area_profile, mesh_solid, rear_socket_checks, throat_frame, volume_difference

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_params():
    params = read_json(EXTENDED / "parameters.json")
    tb = params["throttle_body"]
    tb["oring_groove"]["enabled"] = False
    tb["iacv_mount"]["side_supply_tap_enabled"] = False
    coords = read_json(PHOTO / "photo_points.json")
    measurement = read_json(PHOTO / "photo_measurements.json")
    transform = np.asarray(measurement["photo_to_mm_matrix"])
    lip = smooth_curve(project(coords["iacv_opening_lip_px"], transform), closed=True)
    seal = [smooth_curve(project(coords[key], transform), closed=closed)
            for key, closed in (("outer_gasket_centerline_px", True), ("iacv_gasket_divider_centerline_px", False))]
    feed = orient(Polygon(lip).buffer(-1.8), sign=1.0)
    tb["iacv_flange_feed"] = {
        "face_opening_uv_mm": np.asarray(feed.exterior.coords[:-1]).tolist(),
        "visible_throttle_seal_centerlines_uv_mm": [line.tolist() for line in seal],
        "photo_trace_to_cut_inset_mm": 1.8,
        "duct_diameter_mm": 11.1,
        "duct_wall_mm": 5.0,
    }
    params["metadata"]["revision"] = "Stage-2 V2 Codex extended neck, flat factory throttle face and IACV feed"
    return params


def closed_profile(poly, count):
    outline = LineString(poly.exterior.coords)
    return np.asarray([outline.interpolate(i / count, normalized=True).coords[0] for i in range(count)])


def circular_match(profile, center, radius):
    start = profile[0] - np.mean(profile, axis=0)
    angle = np.arctan2(start[1], start[0])
    return center + radius * gen.ellipse_points(2, 2, len(profile)) @ np.array(
        [[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])


def flange_fasteners(params):
    cfg = params["throttle_body"]
    *_, back, _, axis = gen.tb_neck_bezier_points(params)
    u, v, offset = gen.throttle_mounting_frame(axis, cfg)
    centers = [back + offset + sx * cfg["bolt_spacing_x_mm"] / 2 * u + sy * cfg["bolt_spacing_y_mm"] / 2 * v
               for sx in (-1, 1) for sy in (-1, 1)]
    sockets = gen.m_union([gen.make_cylinder_along(p - 14 * axis, p - 0.30 * axis, 6.27, 64) for p in centers])
    holes = gen.m_union([gen.make_cylinder_along(p - 2 * axis, p + 15 * axis, cfg["bolt_hole_diameter_mm"] / 2, 64)
                         for p in centers])
    return sockets, holes


def make_route(params, tb, cup_uv, route_path):
    cfg = params["throttle_body"]["iacv_flange_feed"]
    port = Polygon(cfg["face_opening_uv_mm"])
    radius = cfg["duct_diameter_mm"] / 2
    wall = cfg["duct_wall_mm"]
    face, axis = tb["flange_face_center"], tb["tb_axis"]
    u, v, offset = gen.throttle_mounting_frame(axis, params["throttle_body"])
    origin = face + offset
    axes = np.stack((u, v))
    cup = np.asarray(cup_uv)
    depths = np.r_[-1.5, np.linspace(0.3, 11, 32), 11.65]

    def adapter(poly, end_radius):
        profile = closed_profile(orient(poly, sign=1), 96)
        circle = circular_match(profile, cup, end_radius)
        rings = []
        for d in depths:
            weight = gen.eased_progress((d - 0.32) / 10.68, 0.26, 0.31)
            rings.append(origin - d * axis + ((1 - weight) * profile + weight * circle) @ axes)
        return gen.trimesh_to_manifold(gen.loft_closed_solid(rings))

    inlet = adapter(port, radius)
    # Existing flange thickness supports the face opening. This sleeve blends into the new duct behind it.
    inlet_outer = adapter(port.buffer(wall), radius + wall)
    inlet_outer = inlet_outer.trim_by_plane(-axis, float((-axis) @ face) + 1.25)

    deltas = cfg.get("round_transition_approach_uv_mm", [[-1.6, -1.9], [-4.3, -5.0]])
    approach = [origin + (cup + np.array(delta)) @ axes - depth * axis
                for depth, delta in zip((11, 17, 24), ([0, 0], *deltas), strict=True)]
    p = params["throttle_body"]["iacv_mount"]
    x = p["x_center_mm"] + p["port_spacing_x_mm"] / 2
    y = p["y_center_mm"]
    points = np.array([*approach, *route_path, [x, y, 54.6]])
    stations = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    curve = CubicSpline(stations, points, bc_type=((1, -axis), (1, [0, 1, 0])))
    ts = np.r_[-0.75, np.linspace(0, stations[-1], 100)]
    positions, tangents = curve(ts), curve(ts, 1)

    def tube(rad, add_fairing=False):
        profile = gen.ellipse_points(2 * rad, 2 * rad, 96)
        rings = []
        for index, (position, tangent) in enumerate(zip(positions, tangents, strict=True)):
            ring = gen.ring_frame_points(position, tangent, np.array([0.0, 0, 1]), profile)
            if add_fairing:
                # Build-direction down is -X in the existing right-half print orientation.
                tangent = tangent / np.linalg.norm(tangent)
                down = np.array([-1.0, 0, 0]) + tangent * tangent[0]
                magnitude = np.linalg.norm(down)
                if magnitude > 1e-6:
                    radial = (ring - position) / rad
                    cosine = np.clip(radial @ (down / magnitude), -1, 1)
                    sine = np.sqrt(np.maximum(1e-8, 1 - cosine**2) + 0.0049)
                    shoulder = np.where(cosine > 0.707, np.maximum(1, np.sqrt(2) / (np.maximum(cosine, 0) + sine)), 1)
                    fade_in = gen.eased_progress((ts[index] - 16) / 20, 0.35, 0.35)
                    fade_out = 1 - gen.eased_progress((ts[index] - 61) / 23, 0.35, 0.35)
                    ring = position + rad * radial * (1 + (shoulder - 1) * magnitude * fade_in * fade_out)[:, None]
            rings.append(ring)
        return gen.trimesh_to_manifold(gen.loft_closed_solid(rings))

    sockets, holes = flange_fasteners(params)
    deck_guard = gen.make_rounded_prism(p["pad_length_x_mm"] + 4, p["pad_width_y_mm"] + 4,
                                       p["pad_corner_radius_mm"], 35, segments=96,
                                       center=(p["x_center_mm"], y, p["top_z_mm"] + 17.5), axis="z")
    fairing = cfg.get("printer_fairing", False)
    return {"inner": inlet + tube(radius), "outer": (inlet_outer + tube(radius+wall, fairing)) - sockets - deck_guard,
            "stations": points, "centerline": curve, "centerline_length_mm": stations[-1],
            "sockets": sockets, "bolt_holes": holes, "iacv_deck_guard": deck_guard}


def iacv_with_closed_side_tap(params, original):
    cfg = params["throttle_body"]["iacv_mount"]
    floor = cfg["supply_pocket_bottom_z_mm"]
    x = cfg["x_center_mm"] + cfg["port_spacing_x_mm"] / 2
    y = cfg["y_center_mm"]
    keep = [part for part in original["cutters"].decompose() if abs(part.bounding_box()[2] - floor) > 1e-4]
    supply = gen.make_cylinder_along(np.array([x, y, floor]), np.array([x, y, cfg["top_z_mm"] + 4]),
                                     cfg["port_diameter_mm"] / 2, segments=64)
    assert len(keep) == 3
    return {**original, "cutters": gen.m_union([*keep, supply]), "supply": supply, "tap_face": None}


def deck_seal_land(params, tb):
    body = params["throttle_body"]
    cfg = body["iacv_flange_feed"]
    face, axis = tb["flange_face_center"], tb["tb_axis"]
    u, v, offset = gen.throttle_mounting_frame(axis, body)
    radius = body["bore_diameter_mm"] / 2
    center = np.asarray(body["bore_from_bolt_grid_uv_mm"])
    first, divider = cfg["visible_throttle_seal_centerlines_uv_mm"]
    seal = LineString([*first, first[0]]).union(LineString(divider))
    band = seal.buffer(1.60)
    directions = gen.ellipse_points(2, 2, 480)
    origin = Point(center)
    cut_radii = []
    for direction in directions:
        ray = LineString([center, center + radius * direction])
        crossing = ray.intersection(band)
        cut_radii.append(radius if crossing.is_empty else origin.distance(crossing))
    cut_radii = np.asarray(cut_radii)
    axes = np.stack((u, v))
    depths = np.r_[-2.25, np.linspace(0, 5.5, 45), 5.7]
    rings = []
    for depth in depths:
        fade = gen.eased_progress((depth - 1.0) / 4.5, 0.24, 0.24)
        radii = cut_radii + fade * (radius + 0.03 - cut_radii)
        rings.append(face + offset - depth * axis + (center + radii[:, None] * directions) @ axes)
    opening = gen.trimesh_to_manifold(gen.loft_closed_solid(rings))
    stock = gen.make_cylinder_along(face + 2.2*axis, face - 5.58*axis, radius+1, 160)
    support = stock - opening
    trimmed = {**tb, "tb_bore": tb["tb_bore"] - support, "cutters": tb["cutters"] - support}
    area_loss = Polygon(radius * directions).area - Polygon(cut_radii[:, None] * directions).area
    measure = {"max_local_radial_inset_mm": float(radius - cut_radii.min()),
               "face_opening_area_reduction_mm2": area_loss, "requested_photo_seal_land_mm": 1.60}
    return trimmed, measure


def flush_flange_blend(params, tb):
    cfg = params["throttle_body"]
    face, axis = tb["flange_face_center"], tb["tb_axis"]
    u, v, offset = gen.throttle_mounting_frame(axis, cfg)
    frame = np.stack((u, v, axis))
    origin = face + offset
    w, h, r = (cfg[k] for k in ("flange_width_mm", "flange_height_mm", "flange_corner_radius_mm"))
    thickness = cfg["flange_thickness_mm"]
    start, stop, fade_end = thickness - 2.5, thickness + 10, thickness + 17

    def ring(depth):
        extra = 48 * max(gen.eased_progress((start - depth) / 4, 0.35, 0.35),
                         gen.eased_progress((depth - stop) / (fade_end - stop), 0.35, 0.35))
        section = gen.rounded_rect_points(w + 0.012 + 2*extra, h + 0.012 + 2*extra, r + extra, 192)
        return origin - depth*axis + section @ frame[:2]

    envelope = gen.trimesh_to_manifold(gen.loft_closed_solid([
        ring(d) for d in (-150, *np.linspace(start - 4, start, 21), stop,
                          *np.linspace(stop + 0.2, fade_end, 38), 200)
    ]))
    original = tb["outer"]
    # Keep the original face and the deep diffuser. Clip only the material around the flange-back blend.
    revised = original ^ envelope
    removed = original - envelope
    keep_wall = removed.min_gap(tb["tb_bore"], 25)
    assert keep_wall >= 4.5 and removed.volume() > 1, (keep_wall, removed.volume())
    profile = Polygon(gen.rounded_rect_points(w, h, r, 192)).buffer(0.02)
    transform = np.column_stack((frame, -frame @ origin))
    before, after = (m.transform(transform) for m in (original, revised))
    results = {}
    for d in (10, 10.8, 11.9, 12.1, 13, 14, 16, 18, 20, 22):
        sections = []
        for part in (before, after):
            section = Polygon()
            for loop in part.slice(-d).to_polygons():
                section = section.symmetric_difference(Polygon(loop))
            sections.append(section.difference(profile).area)
        results[str(d)] = sections
    assert max(row[1] for row in results.values()) < 0.05, results
    return {**tb, "outer": revised}, {"removed_exterior_mm3": removed.volume(),
        "minimum_bore_wall_at_trim_mm": keep_wall, "measured_depth_behind_face_mm": [start, stop],
        "profile_overhang_area_before_after_mm2": results}


def measure_route(params, tb, plenum_air, iacv, cable, route):
    cfg = params["throttle_body"]["iacv_mount"]
    air = gen.m_union([plenum_air, tb["tb_bore"]])
    duct, rib = route["inner"], route["outer"]
    outer_trim = gen.m_union([tb["outer"], rib, iacv["outer"]])
    cable_upper = cable["outer"].trim_by_plane([0, 0, 1], cable["top_z"] - 3)
    # The radius at the outlet stays above the existing pocket floor.
    return {
        "connected_duct_components": len(duct.decompose()),
        "supply_pocket_intersection_mm3": (duct ^ iacv["supply"]).volume(),
        "main_air_to_feed_mm": duct.min_gap(air, 30),
        "bracket_pilots_to_feed_mm": cable["cutters"].min_gap(duct, 30),
        "iacv_bolts_and_outlet_to_feed_mm": (iacv["cutters"] - iacv["supply"]).min_gap(duct, 30),
        "added_rib_to_cable_post_tops_mm": rib.min_gap(cable_upper, 30),
        "flange_holes_to_feed_mm": route["bolt_holes"].min_gap(duct, 30),
        "socket_clearance_to_feed_mm": route["sockets"].min_gap(duct, 30),
        "iacv_mounting_face_to_duct_mm": route["iacv_deck_guard"].min_gap(duct, 30),
        "rib_overlap_with_neck_mm3": (rib ^ tb["outer"]).volume(),
        "rib_overlap_with_iacv_mm3": (rib ^ iacv["outer"]).volume(),
        "outside_covered_duct_mm3": (duct.trim_by_plane(-tb["tb_axis"],
            float((-tb["tb_axis"]) @ tb["flange_face_center"]) + 0.05) - outer_trim).volume(),
        "rib_top_z_mm": rib.bounding_box()[5],
        "supply_port_floor_z_mm": cfg["supply_pocket_bottom_z_mm"],
    }


PATHS = {
    "direct": [[163, -46, 57.5], [157, -38, 57.5], [161, -30, 55.5], [173, -21, 54.6],
               [174, -12, 54.6], [171, -3, 54.6], [167.5, 4, 54.6]],
    "wider": [[161, -47, 58], [153, -39, 58], [154, -31, 55.5], [165, -24, 54.6],
              [175, -17, 54.6], [174, -8, 54.6], [169, 2, 54.6]],
    "smoothed": [[159.10, -48.90, 58], [153.97, -40.17, 58], [155.90, -30.91, 55.5],
                 [165.66, -22.95, 54.6], [173.10, -15.10, 54.6], [173.72, -6.10, 54.6], [168.41, 3.85, 54.6]],
}


def survey():
    params = load_params()
    tb = gen.build_throttle_body_components(params)
    plenum_air = gen.build_plenum_loft(params, is_inner=True)
    iacv = iacv_with_closed_side_tap(params, gen.build_iacv_components(params))
    cable = gen.build_cable_bracket_boss_components(params, tb["outer"])
    result = []
    for cup in ((-27, 26), (-30, 25)):
        for name, points in PATHS.items():
            cfg = params["throttle_body"]["iacv_flange_feed"]
            if name == "smoothed":
                cfg["round_transition_approach_uv_mm"] = [[-0.57, -1.16], [-4.36, -3.1]]
            else:
                cfg.pop("round_transition_approach_uv_mm", None)
            route = make_route(params, tb, cup, points)
            checks = measure_route(params, tb, plenum_air, iacv, cable, route)
            trial_shell = gen.m_union([tb["outer"], route["outer"], iacv["outer"]])
            body = gen.m_diff(trial_shell, [tb["cutters"], route["inner"], iacv["cutters"]])
            access = rear_socket_checks(gen, body, params)
            row = {"cup_uv_mm": cup, "path": name, **checks, "socket_interference_mm3": [x["interference_mm3"] for x in access]}
            result.append(row)
            print(row, flush=True)
    write_json(HERE / "route_survey.json", result)


def flat_face_checks(body, tb, config):
    face, axis = tb["flange_face_center"], tb["tb_axis"]
    u, v, shift = gen.throttle_mounting_frame(axis, config["throttle_body"])
    frame = np.stack((u, v, axis))
    flange = body.transform(np.column_stack((frame, -frame @ (face + shift))))
    flange_size = config["throttle_body"]
    w, h = flange_size["flange_width_mm"] / 2 + 1, flange_size["flange_height_mm"] / 2 + 1
    window = box(-w, -h, w, h)
    cfg = flange_size["iacv_flange_feed"]
    first = cfg["visible_throttle_seal_centerlines_uv_mm"][0]
    seal = LineString([*first, first[0]]).union(LineString(cfg["visible_throttle_seal_centerlines_uv_mm"][1]))
    profile_stats = {}
    reference_loops = []
    for depth in (0.1, 0.25, 1.1, 2.2):
        section = Polygon()
        for loop in flange.slice(-depth).to_polygons():
            section = section.symmetric_difference(Polygon(loop).intersection(window))
        assert isinstance(section, Polygon) and section.is_valid and len(section.interiors) == 6, (depth, section)
        assert section.covers(seal), depth
        profile_stats[str(depth)] = {"seal_centerline_to_edge_mm": section.boundary.distance(seal),
                                     "openings": len(section.interiors)}
        if depth == 0.1:
            reference_loops = [np.asarray(section.exterior.coords[:-1]),
                               *[np.asarray(hole.coords[:-1]) for hole in section.interiors]]
    assert profile_stats["0.1"]["seal_centerline_to_edge_mm"] >= 1.5, profile_stats
    return profile_stats, md.CrossSection(reference_loops, md.FillRule.EvenOdd).extrude(4)


def install_fit_template(root, manifest, params, left, coupon_path):
    gauge_key = "svt_v2_tb_flange_fit_gauge"
    mesh = trimesh.load_mesh(coupon_path)
    assert mesh.is_volume and mesh.body_count == 1
    sections = {LEFT: left, gauge_key: mesh_solid(mesh)}
    for name in ("svt_v2_runner_boot_fit_gauge", "svt_v2_iacv_flange_fit_gauge"):
        sections[name] = mesh_solid(trimesh.load_mesh(root / manifest["parts"][name]["file"]))
    gen.render_1to1_svg(sections, params, root / "fitment/02_interfaces_1to1_template_v2.svg")
    manifest["parts"][gauge_key].update({
        "file": f"stl/{coupon_path.name}", "sha256": sha256(coupon_path.read_bytes()).hexdigest(),
        "triangle_count": int(len(mesh.faces)), "collapsed_faces_omitted": 0,
        "extents_mm": np.round(mesh.extents, 2).tolist(), "bounds_min_mm": np.round(mesh.bounds[0], 2).tolist(),
        "bounds_max_mm": np.round(mesh.bounds[1], 2).tolist(), "solid_volume_cm3": round(float(mesh.volume) / 1000, 2),
    })
    write_json(root / "stl/manifest.json", manifest)
    (root / "stl/svt_v2_tb_flange_fit_gauge_codex.stl").unlink(missing_ok=True)


def save_candidate(destination, row):
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"{destination} already exists. Choose a fresh destination.")
    params = load_params()
    mechanical_reference = gen.build_throttle_body_components(params)
    cable = gen.build_cable_bracket_boss_components(params, mechanical_reference["outer"])
    cfg = params["throttle_body"]["iacv_flange_feed"]
    route_path = PATHS[row["path"]]
    cfg["round_transition_center_uv_mm"] = row["cup_uv_mm"]
    cfg["route_path_xyz_mm"] = route_path
    if row["path"] == "smoothed":
        cfg["round_transition_approach_uv_mm"] = [[-0.57, -1.16], [-4.36, -3.1]]
        params["metadata"]["revision"] += " with eased supply-duct bends"
    if row.get("polish"):
        cfg["printer_fairing"] = True
        params["metadata"]["revision"] += " with printer-oriented duct fairing"
    if row.get("clear_split"):
        params["center_split"]["keep_plenum_cavity_clear"] = True
    original_tb = gen.build_throttle_body_components(params)
    tb, seal_land = deck_seal_land(params, original_tb)
    flange_blend = None
    if row.get("flush_flange"):
        tb, flange_blend = flush_flange_blend(params, tb)
        params["throttle_body"]["flush_back_blend_to_flange_profile"] = True
        params["metadata"]["revision"] += " and flush flange-back blend"
    plenum = gen.build_plenum_loft(params, is_inner=True)
    iacv = iacv_with_closed_side_tap(params, gen.build_iacv_components(params))
    route = make_route(params, tb, row["cup_uv_mm"], route_path)
    checks = measure_route(params, tb, plenum, iacv, cable, route)
    assert checks["connected_duct_components"] == 1 and checks["supply_pocket_intersection_mm3"] > 100, checks
    assert checks["outside_covered_duct_mm3"] < 0.005, checks
    gaps = [checks[k] for k in ("main_air_to_feed_mm", "bracket_pilots_to_feed_mm", "iacv_bolts_and_outlet_to_feed_mm",
                               "flange_holes_to_feed_mm", "socket_clearance_to_feed_mm", "iacv_mounting_face_to_duct_mm")]
    assert min(gaps) >= 4.5 and checks["added_rib_to_cable_post_tops_mm"] > 0, checks
    checks["bracket_foot_overlap_with_neck_mm3"] = [(p ^ tb["outer"]).volume() for p in cable["posts"]]
    assert min(checks["bracket_foot_overlap_with_neck_mm3"]) > 0, checks
    sealed = {**tb, "outer": tb["outer"] + route["outer"], "cutters": tb["cutters"] + route["inner"]}
    saved = gen.PARAMS_PATH, gen.STL_DIR, gen.FITMENT_DIR
    native_tb, native_iacv = gen.build_throttle_body_components, gen.build_iacv_components
    native_cable, native_export = gen.build_cable_bracket_boss_components, gen.export_checked_stl
    native_split = gen.build_center_split_flange_and_cutters

    def cut_split(config):
        components = native_split(config)
        return {**components, "flange_ring": components["flange_ring"] - plenum}
    simplifications = {}

    def export_stl(solid, path):
        try:
            return native_export(solid, path)
        except ValueError as error:
            for tolerance in (0.0001, 0.0003, 0.001):
                try:
                    mesh = native_export(solid.simplify(tolerance), path)
                except ValueError:
                    continue
                simplifications[path.name] = tolerance
                return mesh
            raise error

    print("Route geometry passed. Exporting the manifold and checking the assembled interfaces.", flush=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".iacv-", dir=destination.parent) as work:
        stage = Path(work).resolve()
        if stage.parent != destination.parent:
            raise ValueError(f"Temporary directory escaped {destination.parent}")
        config_file = stage / "parameters.json"
        write_json(config_file, params)
        try:
            gen.PARAMS_PATH, gen.STL_DIR, gen.FITMENT_DIR = config_file, stage / "stl", stage / "fitment"
            gen.build_throttle_body_components = lambda config: sealed
            gen.build_iacv_components = lambda config: iacv
            gen.build_cable_bracket_boss_components = lambda config, neck: cable
            if row.get("clear_split"):
                gen.build_center_split_flange_and_cutters = cut_split
            gen.export_checked_stl = export_stl
            gen.main()
        finally:
            gen.PARAMS_PATH, gen.STL_DIR, gen.FITMENT_DIR = saved
            gen.build_throttle_body_components, gen.build_iacv_components = native_tb, native_iacv
            gen.build_cable_bracket_boss_components, gen.export_checked_stl = native_cable, native_export
            gen.build_center_split_flange_and_cutters = native_split
        manifest = read_json(stage / "stl/manifest.json")
        originals = read_json(EXTENDED / "stl/manifest.json")

        def imported(root, data, key):
            record = data["parts"][key]
            filename = root / record["file"]
            assert sha256(filename.read_bytes()).hexdigest() == record["sha256"]
            mesh = trimesh.load_mesh(filename)
            assert mesh.is_volume and mesh.body_count == 1 and mesh.is_winding_consistent
            return mesh_solid(mesh)

        full, right, left = (imported(stage, manifest, key) for key in (FULL, RIGHT, LEFT))
        previous_left = imported(EXTENDED, originals, LEFT)
        left_difference = volume_difference(previous_left, left)
        assert left_difference < 0.05, left_difference
        slices, coupon = flat_face_checks(full, tb, params)
        coupon_path = stage / "stl/svt_v2_flat_face_iacv_fit_coupon.stl"
        export_stl(coupon, coupon_path)
        sockets = rear_socket_checks(gen, right, params)
        assert all(p["interference_mm3"] < 0.05 and p["rear_washer_annulus_support_fraction"] >= 0.995
                   for p in sockets), sockets
        face, axis = tb["flange_face_center"], tb["tb_axis"]
        inside_plane = float((-axis) @ face)
        main = (plenum + tb["tb_bore"]).trim_by_plane(-axis, inside_plane)
        nominal_main = (plenum + original_tb["tb_bore"]).trim_by_plane(-axis, inside_plane)
        frame, _ = throat_frame(face, axis)
        area = area_profile(main, face, frame)["min_area_mm2"]
        nominal = area_profile(nominal_main, face, frame)["min_area_mm2"]
        assert area >= nominal - seal_land["face_opening_area_reduction_mm2"] - 0.10, (area, nominal, seal_land)
        capped_feed = route["inner"].trim_by_plane(-axis, inside_plane + 0.02)
        feed_obstruction = abs((full ^ capped_feed).volume())
        assert feed_obstruction < 0.02, feed_obstruction
        report = {"route": checks, "flat_face_sections": slices, "rear_sockets": sockets, "flange_back_blend": flange_blend,
                  "left_half_difference_mm3": left_difference, "minimum_sampled_bore_area_mm2": area,
                  "unmodified_minimum_sampled_bore_area_mm2": nominal, "seal_land_support": seal_land,
                  "solid_in_capped_iacv_feed_mm3": feed_obstruction, "stl_simplification_mm": simplifications,
                  "right_print_extents_mm": manifest["parts"]["svt_intake_manifold_v2_split_right_print_oriented"]["extents_mm"],
                  "fit_coupon_sha256": sha256(coupon_path.read_bytes()).hexdigest()}
        install_fit_template(stage, manifest, params, left, coupon_path)
        write_json(stage / "geometry_validation.json", report)
        destination.mkdir()
        for artifact in stage.iterdir():
            artifact.rename(destination / artifact.name)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--export", type=Path)
    cli.add_argument("--path", choices=tuple(PATHS))
    cli.add_argument("--cup", nargs=2, type=float)
    cli.add_argument("--polish", action="store_true", help="Blend the outside of the duct for the right-half print orientation")
    cli.add_argument("--clear-split", action="store_true", help="Keep the tapered plenum clear through the split joint")
    cli.add_argument("--flush-flange", action="store_true", help="Confine the round back blend inside the square flange")
    args = cli.parse_args()
    with one_job():
        if args.export:
            if args.path is None or args.cup is None:
                cli.error("--export requires both --path and --cup")
            save_candidate(args.export, {"path": args.path, "cup_uv_mm": args.cup, "polish": args.polish,
                                         "flush_flange": args.flush_flange, "clear_split": args.clear_split})
        else:
            survey()
