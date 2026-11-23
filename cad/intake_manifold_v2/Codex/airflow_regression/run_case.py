"""Compare Stage-2 V1 and Codex V2 on the same frozen steady-flow solver."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from time import perf_counter

for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

HERE = Path(__file__).resolve().parent
CODEX = HERE.parent
V1 = CODEX.parent.parent / "intake_manifold"
sys.dont_write_bytecode = True
sys.path[:0] = [str(CODEX / "reference"), str(CODEX), str(V1)]

import generate_intake_manifold as v1
import generate_intake_manifold_v2_codex as v2
import verify_airflow_v2 as solver
from local_job import one_job


VARIANTS = {
    "neutral": {"bellmouth": {"axial_entry_angles_deg": [0, 0, 0, 0]}},
    "reach": {"bellmouth": {"axial_entry_angles_deg": [0, 10, 14, 0]}},
    "reach2": {"bellmouth": {"axial_entry_angles_deg": [0, 20, 24, -8]}},
    "scoop": {"bellmouth": {"axial_entry_angles_deg": [0, 2.5, 4, 24]}},
    "low_entry": {"sweep": {"entry_elevation_deg": 24}},
    "high_entry": {"sweep": {"entry_elevation_deg": 40}},
    "high_scoop": {"sweep": {"entry_elevation_deg": 40}, "bellmouth": {"axial_entry_angles_deg": [0, 2.5, 4, 24]}},
    "wide_entry": {"sweep": {"plenum_entry_diameter_mm": 50}},
    "entry_48": {"sweep": {"plenum_entry_diameter_mm": 48}},
    "wide_low": {"sweep": {"plenum_entry_diameter_mm": 50, "plenum_entry_z_mm": 2}},
    "raised_entry": {"sweep": {"plenum_entry_z_mm": 18}},
    "lowered_entry": {"sweep": {"plenum_entry_z_mm": 2}},
    "taper_45": {"plenum": {"taper_cyl1_area_ratio": 0.45}},
    "taper_75": {"plenum": {"taper_cyl1_area_ratio": 0.75}},
    "guide_12": {"plenum": {"rear_wall_flow_guide": {"blend_x_mm": [84, 164], "depth_mm": 12}}},
    "guide_24": {"plenum": {"rear_wall_flow_guide": {"blend_x_mm": [84, 164], "depth_mm": 24}}},
    "guide_short": {"plenum": {"rear_wall_flow_guide": {"blend_x_mm": [110, 165], "depth_mm": 16}}},
    "c4_wide": {"runners": {"entry_sweep_overrides": {"4": {"plenum_entry_diameter_mm": 54}}}},
    "c4_wide_high": {"runners": {"entry_sweep_overrides": {"4": {
        "plenum_entry_diameter_mm": 57, "entry_elevation_deg": 40, "plenum_entry_z_mm": 17,
    }}}},
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def design_params(design):
    generator = v1 if design == "v1" else v2
    params = json.loads(generator.PARAMS_PATH.read_text(encoding="utf-8"))
    for section, overrides in VARIANTS.get(design, {}).items():
        target = params[section] if section in ("plenum", "runners") else params["runners"][section]
        target.update(overrides)
    if "rear_wall_flow_guide" in params["plenum"]:
        import shape_plenum

        shape_plenum.attach(generator)
    if "entry_sweep_overrides" in params["runners"]:
        import shape_runners

        shape_runners.attach(generator)
    return generator, params


def baseline_stl(design):
    directory = V1 if design == "v1" else CODEX
    name = "svt_intake_manifold_1piece_full" if design == "v1" else "svt_intake_manifold_v2_1piece_full"
    manifest = json.loads((directory / "stl" / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["parts"][name]
    path = directory / entry["file"]
    if digest(path) != entry["sha256"]:
        raise ValueError(f"STL hash differs from manifest for {design}")
    return path


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", choices=("v1", "v2", *VARIANTS))
    parser.add_argument("--dx", type=float, default=4)
    parser.add_argument("--offset", type=float, default=0)
    parser.add_argument("--rpm", type=float, default=7000)
    parser.add_argument("--cylinder", type=int, choices=range(1, 5))
    parser.add_argument("--max-iterations", type=int, default=320)
    parser.add_argument("--drag", type=float, default=1.4)
    parser.add_argument("--valve-k", type=float, default=14)
    parser.add_argument("--amg", action="store_true", help="Use a multigrid preconditioner for the same pressure equations")
    args = parser.parse_args()
    label = f"{args.design}_dx{args.dx:g}_shift{args.offset:g}_rpm{args.rpm:g}"
    if args.cylinder is not None:
        label += f"_c{args.cylinder}"
    if args.valve_k != 14:
        label += f"_k{args.valve_k:g}"
    if args.drag != 1.4:
        label += f"_drag{args.drag:g}"
    if args.max_iterations != 320:
        label += f"_it{args.max_iterations}"
    if args.amg:
        label += "_amg"
    start = perf_counter()
    print(label, flush=True)
    generator, params = design_params(args.design)
    source = {
        "generator": digest(Path(generator.__file__)),
        "parameters": digest(generator.PARAMS_PATH),
        "solver": digest(Path(solver.__file__)),
    }
    if args.design in ("v1", "v2"):
        source["full_stl"] = digest(baseline_stl(args.design))
    if "rear_wall_flow_guide" in params["plenum"]:
        source["plenum_flow_guide"] = digest(HERE / "shape_plenum.py")
    if "entry_sweep_overrides" in params["runners"]:
        source["per_runner_entry"] = digest(HERE / "shape_runners.py")
    if args.amg:
        import pressure_preconditioner

        source["pressure_preconditioner"] = digest(Path(pressure_preconditioner.__file__))
        pressure_preconditioner.attach(solver)
    solver.gen = generator
    fluid = solver.extract_fluid_cavity(params)
    grid = solver.voxelize_fluid_solid(fluid["fluid_solid"], dx=args.dx, grid_offset_mm=(args.offset,) * 3)
    print(f"{label}: {int(grid['inside'].sum()):,} fluid cells after {perf_counter() - start:.1f} s", flush=True)
    mass = 0.2777 * args.rpm / 7000 * (0.35 if args.cylinder else 1)
    result = solver.solve_3d_navier_stokes_fvm(
        grid, params, fluid, total_mass_flow_kgs=mass, active_cyls=[args.cylinder] if args.cylinder else None,
        n_picard=args.max_iterations, k_port_valve=args.valve_k, wall_drag_mult=args.drag,
    )
    data = {
        "inputs": vars(args), "flow_kg_s": mass, "boost_psig": solver.BOOST_PSI,
        "temperature_c": solver.T0_IN_K - 273.15, "density_kg_m3": solver.RHO0,
        "fluid_volume_cm3": fluid["fluid_solid"].volume() / 1000,
        "source_sha256": source,
        "parameter_overrides": VARIANTS.get(args.design, {}),
        "elapsed_seconds": round(perf_counter() - start, 1),
        "result": {key: value for key, value in result.items() if not key.startswith("slice_")},
    }
    save_json(HERE / "cases" / (label + ".json"), data)
    print(label, data["elapsed_seconds"], result["status"], result.get("tb_to_plenum_dp_kpa"),
          result.get("cyl_maldistribution_spread_pct"), result.get("cyl_flow_share_pct"), flush=True)


if __name__ == "__main__":
    with one_job():
        main()
