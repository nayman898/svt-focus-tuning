"""Export a tested runner revision in a separate folder and verify the fit interfaces."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from run_case import HERE, VARIANTS, design_params, digest, save_json, solver, v2
from local_job import one_job
from verify_geometry import FULL, LEFT, RIGHT, cable_clearance, mesh_solid, rear_socket_checks, volume_difference

import trimesh


def exported_solid(folder, entry):
    path = folder / Path(entry["file"]).name
    if digest(path) != entry["sha256"]:
        raise ValueError(f"STL hash does not match manifest: {path}")
    mesh = trimesh.load_mesh(path)
    assert mesh.is_volume and mesh.body_count == 1 and mesh.is_winding_consistent, path
    return mesh_solid(mesh)


def export_candidate(design, out):
    _, params = design_params(design)
    params["metadata"]["revision"] = f"Stage-2 V2 Codex airflow candidate ({design})"
    candidate_params = out / "parameters.json"
    save_json(candidate_params, params)
    params_path, stl_dir, fitment_dir = v2.PARAMS_PATH, v2.STL_DIR, v2.FITMENT_DIR
    native_export = v2.export_checked_stl
    simplified_stls = {}

    def export_float32(solid, path):
        try:
            return native_export(solid, path)
        except ValueError as error:
            for tolerance_mm in (0.0001, 0.0003, 0.001):
                try:
                    exported = native_export(solid.simplify(tolerance_mm), path)
                except ValueError:
                    continue
                simplified_stls[path.name] = tolerance_mm
                return exported
            raise error

    try:
        v2.PARAMS_PATH, v2.STL_DIR, v2.FITMENT_DIR = candidate_params, out / "stl", out / "fitment"
        v2.export_checked_stl = export_float32
        v2.main()
    finally:
        v2.PARAMS_PATH, v2.STL_DIR, v2.FITMENT_DIR = params_path, stl_dir, fitment_dir
        v2.export_checked_stl = native_export

    baseline = json.loads((stl_dir / "manifest.json").read_text(encoding="utf-8"))
    revised = json.loads((out / "stl" / "manifest.json").read_text(encoding="utf-8"))
    old = {label: exported_solid(stl_dir, baseline["parts"][label]) for label in (FULL, LEFT, RIGHT)}
    new = {label: exported_solid(out / "stl", revised["parts"][label]) for label in (FULL, LEFT, RIGHT)}
    *_, back, face, axis = v2.tb_neck_bezier_points(params)
    split_x = params["center_split"]["split_x_mm"]
    half_thick = params["center_split"]["flange_thickness_per_side_mm"]
    lower, upper = split_x - half_thick, split_x + half_thick
    interfaces = {
        "four_boot_lands": volume_difference(old[FULL].trim_by_plane([0, -1, 0], 119),
                                             new[FULL].trim_by_plane([0, -1, 0], 119)),
        "throttle_flange_bore_bolts_and_face_seal": volume_difference(
            old[FULL].trim_by_plane(axis, float(back @ axis)), new[FULL].trim_by_plane(axis, float(back @ axis))),
    }
    for label in (LEFT, RIGHT):
        interfaces[label + "_center_joint"] = volume_difference(
            old[label].trim_by_plane([1, 0, 0], lower).trim_by_plane([-1, 0, 0], -upper),
            new[label].trim_by_plane([1, 0, 0], lower).trim_by_plane([-1, 0, 0], -upper),
        )
    assert max(interfaces.values()) < 0.05, interfaces
    matching_gauges = {}
    for label in revised["parts"]:
        if "gauge" in label or "dowel" in label:
            matching_gauges[label] = baseline["parts"][label]["sha256"] == revised["parts"][label]["sha256"]
    assert all(matching_gauges.values()), matching_gauges
    solver.gen = v2
    air = solver.extract_fluid_cavity(params)["fluid_solid"]
    intrusion = abs((new[FULL] ^ air).volume())
    assert intrusion < 0.1, intrusion
    sleeves = rear_socket_checks(v2, new[RIGHT], params)
    assert all(check["interference_mm3"] < 0.05 and check["rear_washer_annulus_support_fraction"] >= 0.995
               for check in sleeves), sleeves
    tb_parts = v2.build_throttle_body_components(params)
    cable = v2.build_cable_bracket_boss_components(params, tb_parts["outer"])
    iacv = v2.build_iacv_components(params)
    clearances, _ = cable_clearance(v2, {"_cable_parts": cable}, params, iacv)
    supply_z = params["throttle_body"]["iacv_mount"]["supply_pocket_bottom_z_mm"]
    pocket, = [piece for piece in iacv["cutters"].decompose() if abs(piece.bounding_box()[2] - supply_z) < 1e-4]
    air_gaps = {"cable_pilot": cable["cutters"].min_gap(air, 25), "iacv_supply": pocket.min_gap(air, 25)}
    assert min(air_gaps.values()) >= 4.5, air_gaps
    geometry = {
        "throttle_face_center_mm": face.tolist(), "throttle_axis": axis.tolist(),
        "stl_simplification_tolerances_mm": simplified_stls,
        "interface_symmetric_difference_mm3_vs_codex_v2": interfaces,
        "matching_gauge_hashes": matching_gauges,
        "main_cavity_stl_overlap_mm3": intrusion, "access_clearance": sleeves, "air_gaps_mm": air_gaps,
        "cable_clearances": clearances, "runner_root_wall_audit": revised["runner_root_wall_audit"],
    }
    save_json(out / "geometry_validation.json", geometry)
    print(design, json.dumps(geometry), flush=True)


def publish(design, destination):
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"{destination} already exists. Choose a fresh --output directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{design}-", dir=destination.parent) as work:
        staged = Path(work).resolve()
        if staged.parent != destination.parent:
            raise ValueError(f"Temporary directory escaped {destination.parent}")
        try:
            export_candidate(design, staged)
        except (AssertionError, ValueError) as error:
            save_json(destination / "geometry_rejection.json", {
                "design": design, "status": "REJECTED", "failed_check": str(error),
            })
            raise
        destination.mkdir()
        for artifact in staged.iterdir():
            artifact.rename(destination / artifact.name)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("design", choices=tuple(VARIANTS))
    cli.add_argument("--output", type=Path, help="Write a verified model into this fresh directory")
    args = cli.parse_args()
    with one_job():
        publish(args.design, args.output or HERE / args.design)
