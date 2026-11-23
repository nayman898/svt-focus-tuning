"""Run the frozen V2 steady-flow model on the stock and Codex CAD at the same conditions."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / "reference"))

import generate_intake_manifold_v2 as baseline
import generate_intake_manifold_v2_codex as codex
import verify_airflow_v2 as verifier


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--offset", type=float, default=0.0, help="Translate the 4 mm lattice by this many mm on each axis")
    args = cli.parse_args()
    result = {
        "operating_point": {"boost_psig": verifier.BOOST_PSI, "inlet_c": verifier.T0_IN_K - 273.15,
                            "inlet_flow_kg_s": 0.2777, "dx_mm": 4.0, "grid_offset_each_axis_mm": args.offset},
        "source_sha256": {Path(module.__file__).name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                          for module in (verifier, baseline, codex)},
        "cases": {},
    }
    for label, generator in (("gemini_v2_current_cad", baseline), ("codex_v2", codex)):
        print(f"{label}, offset {args.offset:g} mm", flush=True)
        verifier.gen = generator
        params = json.loads(generator.PARAMS_PATH.read_text(encoding="utf-8"))
        fluid = verifier.extract_fluid_cavity(params)
        grid = verifier.voxelize_fluid_solid(fluid["fluid_solid"], dx=4.0, grid_offset_mm=(args.offset,) * 3)
        res = verifier.solve_3d_navier_stokes_fvm(grid, params, fluid, total_mass_flow_kgs=0.2777)
        case = {key: value for key, value in res.items() if not key.startswith("slice_")}
        case["params_sha256"] = hashlib.sha256(generator.PARAMS_PATH.read_bytes()).hexdigest()
        result["cases"][label] = case
        name = "airflow_screen.json" if args.offset == 0 else f"airflow_screen_offset_{args.offset:g}mm.json"
        (HERE / name).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print({key: case.get(key) for key in ("status", "outer_iterations", "tb_to_plenum_dp_kpa",
                                               "cyl_maldistribution_spread_pct", "convergence")}, flush=True)


if __name__ == "__main__":
    main()
