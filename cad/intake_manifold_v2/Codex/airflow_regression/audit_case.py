"""Check the WOT CAD, run the existing lumped model, or benchmark the frozen FVM."""

import argparse
from importlib.metadata import version
import math
from pathlib import Path

from run_case import CODEX, HERE, V1, VARIANTS, design_params, digest, save_json, solver, v2
from local_job import one_job

import manifold3d as md
import numpy as np
import trimesh


def audit_design(design):
    generator, params = design_params(design)
    solver.gen = generator
    fluid = solver.extract_fluid_cavity(params)
    audit = solver.audit_cad_flow_geometry(fluid, params)
    output = {
        "design": design, "solver_sha256": digest(Path(solver.__file__)),
        "generator_sha256": digest(Path(generator.__file__)), "parameters_sha256": digest(generator.PARAMS_PATH),
        "cad": {key: value for key, value in audit.items() if not isinstance(value, list) or len(value) < 10},
    }
    if design in ("v1", "v2"):
        prefix = V1 if design == "v1" else CODEX
        filename = "svt_intake_manifold_1piece_full.stl" if design == "v1" else "svt_intake_manifold_v2_1piece_full_codex.stl"
        path = prefix / "stl" / filename
        mesh = trimesh.load_mesh(path)
        casting = generator.trimesh_to_manifold(mesh)
        overlap = fluid["fluid_solid"] ^ casting
        output["stl"] = {
            "sha256": digest(path), "watertight": bool(mesh.is_watertight), "body_count": int(mesh.body_count),
            "manifold_status": str(casting.status()), "capped_wot_cavity_overlap_mm3": abs(overlap.volume()),
        }
    save_json(HERE / "audits" / f"{design}.json", output)
    runs = []
    for rpm in (3000, 4000, 5000, 6000, 6500, 7000, 7500):
        result = solver.solve_1d_compressible_and_pulsating(params, audit, rpm=rpm)
        runs.append({key: value for key, value in result.items() if not key.startswith("_")})
        output["lumped_model"] = runs
        save_json(HERE / "audits" / f"{design}.json", output)
    print(design, output.get("stl"), [(r["rpm"], r["ve_maldistribution_spread_pct"],
                                       r["ve_maldistribution_720ca_pct"]) for r in runs], flush=True)


def audit_runner_geometry(design):
    generator, params = design_params(design)
    solid = generator.assemble_all(params)["svt_intake_manifold_v2_1piece_full"]
    roots = generator.audit_runner_root_walls_72ray(generator.manifold_to_trimesh(solid), params)
    passed = all(root["min_pressure_wall_mm"] >= 4.5 and root["min_all_ray_span_mm"] >= 2.5 for root in roots)
    output = {"design": design, "passes_existing_root_wall_audits": passed, "runner_roots": roots}
    save_json(HERE / "audits" / f"{design}_runner_walls.json", output)
    print(design, output, flush=True)


def benchmark(dx, offset):
    solver.gen = v2
    params = {
        "runners": {"center_x_mm": [0], "spigot": {"outer_width_mm": 50.8, "outer_height_mm": 50.8,
                    "wall_thickness_mm": 4.0, "tip_y_mm": -146.0, "center_z_mm": 68.0}},
        "throttle_body": {"bore_diameter_mm": 42.8},
    }
    solid = md.Manifold.cylinder(200, 21.4, 21.4, circular_segments=192, center=True)
    solid = solid.rotate([90, 0, 0]).translate([0, -46, 68])
    fluid = {"fluid_solid": solid, "p_flange_face": np.array([0, 54, 68]), "tb_axis": np.array([0, 1, 0]), "tip_y": -146.0}
    mass = 0.10
    diameter_m = 0.0428
    speed = mass / (solver.RHO0 * math.pi * diameter_m**2 / 4)
    reynolds = solver.RHO0 * speed * diameter_m / solver.MU_AIR
    darcy_f = (-1.8 * math.log10((solver.EPSILON_WALL_M / (3.7 * diameter_m))**1.11 + 6.9 / reynolds))**-2
    # The two plane windows are centered 18 mm from the inlet and 26 mm from the outlet.
    darcy_pa = darcy_f * 0.156 / diameter_m * 0.5 * solver.RHO0 * speed**2
    grid = solver.voxelize_fluid_solid(solid, dx=dx, grid_offset_mm=(offset,) * 3)
    result = solver.solve_3d_navier_stokes_fvm(
        grid, params, fluid, mass, active_cyls=[1], n_picard=320, k_port_valve=0.0, wall_drag_mult=1.0,
    )
    result = {key: value for key, value in result.items() if not key.startswith("slice_")}
    fvm_pa = result["tb_to_plenum_dp_kpa"] * 1000
    output = {
        "dx_mm": dx, "offset_mm": offset, "fvm_total_pressure_loss_pa": fvm_pa, "haaland_darcy_loss_pa": darcy_pa,
        "fvm_to_darcy_ratio": fvm_pa / darcy_pa, "reynolds": reynolds, "solver_sha256": digest(Path(solver.__file__)),
        "packages": {name: version(name) for name in ("numpy", "scipy", "manifold3d", "trimesh", "matplotlib", "shapely")},
        "result": result,
    }
    save_json(HERE / "audits" / f"duct_dx{dx:g}_shift{offset:g}.json", output)
    print(result["status"], fvm_pa, darcy_pa, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", choices=("duct", "v1", "v2", *VARIANTS))
    parser.add_argument("--dx", type=float, default=3)
    parser.add_argument("--offset", type=float, default=0)
    parser.add_argument("--runner-walls", action="store_true", help="Audit runner walls on assembled V2 CAD")
    args = parser.parse_args()
    if args.runner_walls:
        if args.design in ("duct", "v1"):
            parser.error("--runner-walls expects a V2 design")
        audit_runner_geometry(args.design)
    elif args.design == "duct":
        benchmark(args.dx, args.offset)
    else:
        audit_design(args.design)


if __name__ == "__main__":
    with one_job():
        main()
