"""Extend the fitted Codex V2 throttle neck and check the cable-bracket landing."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

HERE = Path(__file__).resolve().parent
CODEX = HERE.parent
sys.dont_write_bytecode = True
sys.path[:0] = [str(CODEX), str(CODEX / "airflow_regression")]

import numpy as np
from scipy.optimize import brentq
from shapely.geometry import Polygon, box
import trimesh

import generate_intake_manifold_v2_codex as gen
from local_job import one_job
from verify_geometry import (
    FULL, LEFT, RIGHT, area_profile, cable_clearance, mesh_solid, rear_socket_checks, throat_frame,
    volume_difference,
)
import verify_airflow_v2 as flow


def read_params():
    return json.loads((CODEX / "intake_manifold_v2_codex_parameters.json").read_text(encoding="utf-8"))


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def lateral_frame(config, station):
    *controls, _, _, _ = gen.tb_neck_bezier_points(config)
    center, tangent = gen.bezier_point_and_tangent(*controls, station)
    lateral = np.array([tangent[1], -tangent[0]])
    return center[:2], lateral / np.linalg.norm(lateral)


def preserve_bracket_frame(original, extension_mm, setback_mm):
    params = deepcopy(original)
    old = original["throttle_body"]["cable_bracket_boss"]
    axis = gen.tb_neck_bezier_points(original)[-1]
    center, lateral = lateral_frame(original, old["neck_t_center"])
    old_pair_center = center + lateral * old["lateral_front_offset_mm"] + old["offset_xy_mm"]
    tb = params["throttle_body"]
    tb["flange_back_offset_mm"] = (np.asarray(tb["flange_back_offset_mm"]) + extension_mm * axis).tolist()
    tb["neck_length_mm"] += extension_mm
    bracket = tb["cable_bracket_boss"]

    def angle_difference(station):
        tangent = lateral_frame(params, station)[1]
        return float(lateral[0] * tangent[1] - lateral[1] * tangent[0])

    samples = np.linspace(0.15, 0.80, 61)
    roots = [brentq(angle_difference, float(a), float(b)) for a, b in zip(samples, samples[1:])
             if angle_difference(a) * angle_difference(b) <= 0]
    station = min(roots, key=lambda t: abs(t - old["neck_t_center"]))
    center, direction = lateral_frame(params, station)
    move = (extension_mm - setback_mm) * axis
    bracket["offset_xy_mm"] = (old_pair_center + move[:2] - center -
                               direction * bracket["lateral_front_offset_mm"]).tolist()
    bracket["neck_t_center"] = station
    bracket["top_z_mm"] += float(move[2])
    return params


def measure(config, plenum, iacv):
    tb = gen.build_throttle_body_components(config)
    cable = gen.build_cable_bracket_boss_components(config, tb["outer"])
    clearances, _ = cable_clearance(gen, {"_cable_parts": cable}, config, iacv)
    air = gen.m_union([plenum, tb["tb_bore"]])
    supply_z = config["throttle_body"]["iacv_mount"]["supply_pocket_bottom_z_mm"]
    pocket, = [piece for piece in iacv["cutters"].decompose() if abs(piece.bounding_box()[2] - supply_z) < 1e-4]
    return {
        **clearances,
        "cable_pilot_min_gap_to_air_mm": cable["cutters"].min_gap(air, 20),
        "iacv_supply_min_gap_to_air_mm": pocket.min_gap(air, 20),
        "socket_pocket_min_gap_to_air_mm": tb["rear_access"].min_gap(air, 20),
        "throttle_face_world_xyz_mm": tb["flange_face_center"].tolist(),
    }


def survey():
    original = read_params()
    plenum = gen.build_plenum_loft(original, is_inner=True)
    iacv = gen.build_iacv_components(original)
    baseline = measure(original, plenum, iacv)
    rows = []
    for extension in (6, 8, 9):
        for setback in (0, 1.5, 3):
            try:
                config = preserve_bracket_frame(original, extension, setback)
                results = measure(config, plenum, iacv)
            except (ValueError, AssertionError) as error:
                results = {"error": str(error) or "Existing cable bracket clearance check failed"}
            rows.append({"neck_extension_mm": extension, "bracket_setback_relative_to_throttle_mm": setback,
                         **results})
    write_json(HERE / "neck_bracket_survey.json", {"baseline": baseline, "candidates": rows})
    for row in rows:
        print(row, flush=True)


def validate_export(output, original, config):
    base_manifest = json.loads((CODEX / "stl/manifest.json").read_text(encoding="utf-8"))
    new_manifest = json.loads((output / "stl/manifest.json").read_text(encoding="utf-8"))

    def read_part(root, manifest, part):
        entry = manifest["parts"][part]
        path = root / entry["file"]
        assert sha256(path.read_bytes()).hexdigest() == entry["sha256"], path
        mesh = trimesh.load_mesh(path)
        assert mesh.is_volume and mesh.body_count == 1 and mesh.is_winding_consistent, path
        return mesh_solid(mesh)

    base = read_part(CODEX, base_manifest, FULL)
    revised = read_part(output, new_manifest, FULL)
    old_left = read_part(CODEX, base_manifest, LEFT)
    new_left = read_part(output, new_manifest, LEFT)
    right = read_part(output, new_manifest, RIGHT)
    *_, face0, axis0 = gen.tb_neck_bezier_points(original)
    *_, face, axis = gen.tb_neck_bezier_points(config)
    move = face - face0
    assert np.allclose(axis, axis0) and np.allclose(move, 8 * axis)
    comparisons = {
        "left_half_mm3": volume_difference(old_left, new_left),
        "runner_boot_lands_mm3": volume_difference(base.trim_by_plane([0, -1, 0], 119),
                                                  revised.trim_by_plane([0, -1, 0], 119)),
    }
    assert max(comparisons.values()) < 0.05, comparisons
    frame, _ = throat_frame(face, axis)
    old_face = base.transform(np.column_stack((frame, -frame @ face0)))
    new_face = revised.transform(np.column_stack((frame, -frame @ face)))
    tb = config["throttle_body"]
    u, v = tb["bore_from_bolt_grid_uv_mm"]
    w, h = tb["flange_width_mm"] / 2 + 1, tb["flange_height_mm"] / 2 + 1
    face_window = box(-u - w, -v - h, -u + w, -v + h)

    def flange_section(body, depth):
        section = Polygon()
        for loop in body.slice(-depth).to_polygons():
            # The tilted slice also crosses the cylinder 4 runner far from the flange.
            section = section.symmetric_difference(Polygon(loop).intersection(face_window))
        return section

    face_differences = {}
    for depth in (0.1, 0.5, 1.1, 2.05, 2.4, 3.0):
        a, b = (flange_section(body, depth) for body in (old_face, new_face))
        face_differences[str(depth)] = a.symmetric_difference(b).area
    assert max(face_differences.values()) < 0.05, face_differences

    plenum = gen.build_plenum_loft(config, is_inner=True)
    iacv = gen.build_iacv_components(config)
    before, after = (measure(p, plenum, iacv) for p in (original, config))
    shift = np.asarray(after["bolt_centers_world_xyz_mm"]) - np.asarray(before["bolt_centers_world_xyz_mm"])
    assert np.allclose(shift, 5 * axis)
    for key in ("closest_to_iacv_pad_mm", "closest_to_throttle_flange_mm",
                "cable_pilot_min_gap_to_air_mm", "iacv_supply_min_gap_to_air_mm", "socket_pocket_min_gap_to_air_mm"):
        assert after[key] > before[key], (key, before[key], after[key])
    probes = rear_socket_checks(gen, right, config)
    assert all(row["interference_mm3"] < 0.05 and row["rear_washer_annulus_support_fraction"] >= 0.995
               for row in probes), probes

    profiles = {}
    for label, params in (("fitted_v2", original), ("extended_v2", config)):
        tb = gen.build_throttle_body_components(params)
        datum = tb["flange_face_center"]
        region = gen.m_union([plenum, tb["tb_bore"]]).trim_by_plane(-axis, float((-axis) @ datum))
        frame, _ = throat_frame(datum, axis)
        profile = area_profile(region, datum, frame)
        assert profile["min_area_mm2"] >= 3317, profile["min_area_mm2"]
        profiles[label] = profile
    flow.gen = gen
    air = flow.extract_fluid_cavity(config)["fluid_solid"]
    intrusion = abs((revised ^ air).volume())
    assert intrusion < 0.1, intrusion

    front_edge = gen.build_throttle_body_components(config)["outer"].bounding_box()[1] - 2
    coupon = revised.trim_by_plane([1, 0, 0], 125).trim_by_plane([0, 1, 0], front_edge).rotate([0, -90, 0])
    x0, y0, z0, x1, y1, _ = coupon.bounding_box()
    coupon = coupon.translate([-(x0 + x1) / 2, -(y0 + y1) / 2, -z0])
    coupon_path = output / "stl" / "svt_v2_neck_bracket_fit_coupon.stl"
    coupon_mesh, _ = gen.export_checked_stl(coupon, coupon_path)
    report = {
        "neck_extension_along_throttle_axis_mm": float(np.linalg.norm(move)),
        "throttle_flange_move_xyz_mm": move.tolist(),
        "bracket_move_xyz_mm": shift[0].tolist(),
        "bracket_setback_relative_to_throttle_mm": 3,
        "interface_symmetric_differences": comparisons,
        "throttle_flange_section_differences_mm2_by_depth_mm": face_differences,
        "fitted_v2": before, "extended_v2": after, "throttle_neck_section_profiles": profiles,
        "rear_socket_probes": probes,
        "capped_main_air_path_solid_overlap_mm3": intrusion,
        "fit_coupon": {"file": coupon_path.name, "extents_mm": coupon_mesh.extents.tolist(),
                       "sha256": sha256(coupon_path.read_bytes()).hexdigest()},
        "right_print_extents_mm": new_manifest["parts"]["svt_intake_manifold_v2_split_right_print_oriented"]["extents_mm"],
    }
    write_json(output / "geometry_validation.json", report)


def publish(destination):
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"{destination} already exists. Choose a fresh output directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    original = read_params()
    config = preserve_bracket_frame(original, extension_mm=8, setback_mm=3)
    config["metadata"]["revision"] = "Stage-2 V2 Codex extended throttle neck and cable-bracket fit candidate"
    with TemporaryDirectory(prefix=".neck-", dir=destination.parent) as work:
        stage = Path(work).resolve()
        if stage.parent != destination.parent:
            raise ValueError(f"Temporary directory escaped {destination.parent}")
        path = stage / "parameters.json"
        write_json(path, config)
        saved = gen.PARAMS_PATH, gen.STL_DIR, gen.FITMENT_DIR
        try:
            gen.PARAMS_PATH, gen.STL_DIR, gen.FITMENT_DIR = path, stage / "stl", stage / "fitment"
            gen.main()
        finally:
            gen.PARAMS_PATH, gen.STL_DIR, gen.FITMENT_DIR = saved
        validate_export(stage, original, config)
        destination.mkdir()
        for artifact in stage.iterdir():
            artifact.rename(destination / artifact.name)
    print(f"Verified model and fit coupon saved in {destination}", flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--export", type=Path, help="Write the checked revision into a fresh directory")
    args = cli.parse_args()
    with one_job():
        if args.export:
            publish(args.export)
        else:
            survey()
