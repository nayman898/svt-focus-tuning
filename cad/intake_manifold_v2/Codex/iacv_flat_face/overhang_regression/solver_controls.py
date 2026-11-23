"""Run Gemini's duct and symmetric-manifold controls and retain their raw diagnostics."""

from contextlib import redirect_stdout
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path

from full_regression import HERE, CODEX, one_job, solver, solve, write_json


def load(path, name):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    path = CODEX.parent / "test_airflow_suite_v2.py"
    suite = load(path, "gemini_airflow_controls")
    suite.va = solver
    solver.gen = suite.gen
    native = solver.solve_3d_navier_stokes_fvm
    tests = []
    for case in (suite._make_straight_duct_case, suite._make_symmetric_4way_case):
        rows = []

        def record(grid, params, fluid, total_mass_flow_kgs, **options):
            solver.solve_3d_navier_stokes_fvm = native
            try:
                result = solve(grid, params, fluid, total_mass_flow_kgs, **options)
            finally:
                solver.solve_3d_navier_stokes_fvm = record
            rows.append({k: v for k, v in result.items() if not k.startswith("slice_")})
            return result

        output = StringIO()
        status = "PASS"
        solver.solve_3d_navier_stokes_fvm = record
        try:
            with redirect_stdout(output):
                case()
        except AssertionError as error:
            status = f"FAIL {error}".strip()
        finally:
            solver.solve_3d_navier_stokes_fvm = native
        tests.append({"test": case.__name__, "status": status, "messages": output.getvalue(), "results": rows})
        write_json(HERE / "solver_controls.json", {
            "suite_sha256": sha256(path.read_bytes()).hexdigest(),
            "solver_sha256": sha256(Path(solver.__file__).read_bytes()).hexdigest(), "tests": tests,
        })
        print(case.__name__, status, output.getvalue(), flush=True)


if __name__ == "__main__":
    with one_job():
        main()
