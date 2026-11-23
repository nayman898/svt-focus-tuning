"""Run the frozen V2 WOT solver one case at a time on the flat-face CAD."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from generate_iacv_revision import deck_seal_land, gen, one_job, read_json, volume_difference, write_json
import verify_airflow_v2 as solver


def extract(params):
    original = gen.build_throttle_body_components
    try:
        if "iacv_flange_feed" in params["throttle_body"]:
            gen.build_throttle_body_components = lambda config: deck_seal_land(config, original(config))[0]
        solver.gen = gen
        return solver.extract_fluid_cavity(params)
    finally:
        gen.build_throttle_body_components = original


def compare_domains(root, other):
    sources = [directory / "parameters.json" for directory in (root, other)]
    a, b = (extract(read_json(source))["fluid_solid"] for source in sources)
    difference = volume_difference(a, b)
    assert difference < 0.01, difference
    write_json(HERE / f"wot_domain_equivalence_{root.name}_{other.name}.json", {
        "parameter_sha256": {p.parent.name: sha256(p.read_bytes()).hexdigest() for p in sources},
        "symmetric_capped_wot_cavity_difference_mm3": difference,
    })
    print("Capped WOT cavity difference in mm³", difference, flush=True)


def wot_cases(root, jobs, preconditioned, name, boundary_cases):
    source = root / "parameters.json"
    params = read_json(source)
    fluid = extract(params)
    ids = {"parameters": sha256(source.read_bytes()).hexdigest(),
           "frozen_solver": sha256(Path(solver.__file__).read_bytes()).hexdigest()}
    audit = solver.audit_cad_flow_geometry(fluid, params)
    lumped = []
    for rpm in (3000, 4000, 5000, 6000, 6500, 7000, 7500):
        row = solver.solve_1d_compressible_and_pulsating(params, audit, rpm=rpm)
        lumped.append({key: value for key, value in row.items() if not key.startswith("_")})
    write_json(HERE / f"{name}wot_lumped_rpm_sweep.json", {"source_sha256": ids, "cases": lumped})
    for pitch, offset, rpm in jobs:
        label = f"{name}wot_dx{pitch:g}_offset{offset:g}_rpm{rpm:g}"
        start = perf_counter()
        grid = solver.voxelize_fluid_solid(fluid["fluid_solid"], dx=pitch, grid_offset_mm=(offset,) * 3)
        print(label, int(grid["inside"].sum()), flush=True)
        native_cg = solver._jacobi_cg
        try:
            if preconditioned:
                from pressure_preconditioner import attach
                attach(solver)
            mass = 0.2777 * rpm / 7000
            result = solver.solve_3d_navier_stokes_fvm(grid, params, fluid, total_mass_flow_kgs=mass)
        finally:
            solver._jacobi_cg = native_cg
        write_json(HERE / f"{label}.json", {
            "geometry": str(root.name), "inputs": {"dx_mm": pitch, "offset_each_axis_mm": offset, "rpm": rpm,
            "flow_kg_s": mass, "pressure_amg_preconditioned": preconditioned},
            "source_sha256": ids, "elapsed_s": perf_counter() - start,
            "result": {k: v for k, v in result.items() if not k.startswith("slice_")},
        })
        print(label, result["status"], result["tb_to_plenum_dp_kpa"], result["cyl_maldistribution_spread_pct"],
              flush=True)
    boundary = []
    for pitch, offset in boundary_cases:
        grid = solver.voxelize_fluid_solid(fluid["fluid_solid"], dx=pitch, grid_offset_mm=(offset,) * 3)
        info = solver.solve_3d_navier_stokes_fvm(grid, params, fluid, total_mass_flow_kgs=0.2777, n_picard=0)
        data = info["boundary_diagnostics"]
        assert data["inlet_to_outlet_connected"] and data["disjoint_outlets"] and not data["empty_active_outlets"], data
        boundary.append(data)
    if boundary:
        write_json(HERE / f"{name}wot_boundary_only.json", {"source_sha256": ids, "cases": boundary})


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--case", nargs=3, action="append", type=float, metavar=("DX", "OFFSET", "RPM"), default=[])
    cli.add_argument("--boundary-case", nargs=2, action="append", type=float, metavar=("DX", "OFFSET"), default=[])
    cli.add_argument("--root", type=Path, default=HERE.parent / "verified")
    cli.add_argument("--compare-domains", type=Path, help="Compare the capped WOT cavity with another model folder")
    cli.add_argument("--label", default="")
    cli.add_argument("--amg", action="store_true")
    args = cli.parse_args()
    with one_job():
        if args.compare_domains:
            compare_domains(args.root, args.compare_domains)
        else:
            wot_cases(args.root, args.case, args.amg, args.label + "_" if args.label else "", args.boundary_case)
