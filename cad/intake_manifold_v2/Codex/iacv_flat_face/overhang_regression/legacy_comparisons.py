"""Recheck V2's legacy protruding-bellmouth reference and eight-point taper study."""

from copy import deepcopy
from pathlib import Path

from full_regression import CODEX, HERE, MAIN_FLOW, digest, one_job, read_json, solve, solver, voxelize, write_json
from solver_controls import load


def main():
    reference = CODEX / "reference"
    source = reference / "intake_manifold_v2_parameters.json"
    generator = reference / "generate_intake_manifold_v2.py"
    solver.gen = load(generator, "legacy_v2_generator")
    stage2 = read_json(source)
    protruding = solver.make_baseline_params(stage2)
    ids = {"solver": digest(Path(solver.__file__)), "parameters": digest(source), "generator": digest(generator)}
    report = {"source_sha256": ids, "taper_study": []}
    for ratio in (0.54, 0.58, 0.60, 0.64, 0.68, 0.72, 0.78, 0.84):
        row = {"taper_cyl1_area_ratio": ratio}
        for name, config in (("stage2_flush", stage2), ("legacy_protruding", protruding)):
            params = deepcopy(config)
            params["plenum"]["taper_cyl1_area_ratio"] = ratio
            fluid = solver.extract_fluid_cavity(params)
            audit = solver.audit_cad_flow_geometry(fluid, params)
            values = solver.solve_1d_compressible_and_pulsating(params, audit, rpm=7000)
            row[name] = {key: values[key] for key in ("dp_total_kpa", "ve_maldistribution_spread_pct",
                                                       "ve_maldistribution_720ca_pct")}
        report["taper_study"].append(row)
        print(ratio, row["stage2_flush"], row["legacy_protruding"], flush=True)
    write_json(HERE / "legacy_comparisons.json", report)
    fluid = solver.extract_fluid_cavity(protruding)
    result = solve(voxelize(fluid, 4, 0), protruding, fluid, MAIN_FLOW, n_picard=400)
    report["protruding_bellmouth_4mm_3d"] = {k: v for k, v in result.items() if not k.startswith("slice_")}
    write_json(HERE / "legacy_comparisons.json", report)
    print("Legacy reference", result["status"], result["tb_to_plenum_dp_kpa"],
          result["cyl_maldistribution_spread_pct"], flush=True)


if __name__ == "__main__":
    with one_job():
        main()
