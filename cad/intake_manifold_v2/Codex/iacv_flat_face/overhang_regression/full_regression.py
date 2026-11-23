"""Run matched WOT flow cases on the actual exported, assembled V2 split halves."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent
REVISION = HERE.parent
CODEX = REVISION.parent
VALIDATION = REVISION / "validation"
sys.path[:0] = [str(VALIDATION), str(REVISION)]

from wot_check import extract, solver
from generate_iacv_revision import LEFT, RIGHT, gen, mesh_solid, one_job, read_json, write_json
from pressure_preconditioner import attach
import numpy as np
import trimesh


ROOTS = {"fitted": CODEX, "corrected": REVISION / "flange_corrected"}
MAIN_FLOW = 0.2777
NOMINAL = (4, 0, 7000, None, 14)
GRID_CASES = (NOMINAL, (4, 2, 7000, None, 14), (3, 0, 7000, None, 14),
              (2.5, 0, 7000, None, 14))
RPM_CASES = tuple((4, 0, rpm, None, 14) for rpm in (3000, 5000, 7500))
MASK_CASES = tuple((4, 0, 7000, cyl, 14) for cyl in (1, 2, 3, 4))
SENSITIVITY_CASES = ((4, 0, 7000, None, 7),)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def from_exports(design):
    root = ROOTS[design]
    source = root / ("parameters.json" if design == "corrected" else "intake_manifold_v2_codex_parameters.json")
    params = read_json(source)
    analytic = extract(params)
    air = analytic["fluid_solid"]
    parts = read_json(root / "stl/manifest.json")["parts"]
    ids = {"parameters": digest(source), "frozen_solver": digest(Path(solver.__file__)),
           "generator": digest(Path(gen.__file__)), "regression": digest(Path(__file__))}
    intrusions = []
    for side in (LEFT, RIGHT):
        key = side if side in parts else side.removesuffix("_codex")
        record = parts[key]
        path = root / record["file"]
        ids[side] = digest(path)
        assert ids[side] == record["sha256"], path
        mesh = trimesh.load_mesh(path)
        assert mesh.is_volume and mesh.is_winding_consistent and mesh.body_count == 1, path
        intrusions.append(mesh_solid(mesh) ^ air)
    obstruction = gen.m_union(intrusions)
    physical = {**analytic, "fluid_solid": air - obstruction}
    audit = solver.audit_cad_flow_geometry(physical, params)
    lumped = []
    for rpm in (3000, 4000, 5000, 6000, 6500, 7000, 7500):
        result = solver.solve_1d_compressible_and_pulsating(params, audit, rpm=rpm)
        lumped.append({k: v for k, v in result.items() if not k.startswith("_")})
    write_json(HERE / f"{design}_domain.json", {
        "source_sha256": ids, "solid_in_capped_wot_mm3": obstruction.volume(),
        "each_half_solid_in_capped_wot_mm3": [part.volume() for part in intrusions],
        "capped_wot_cm3": physical["fluid_solid"].volume() / 1000,
        "throttle_face_center_mm": analytic["p_flange_face"].tolist(),
        "throttle_axis": analytic["tb_axis"].tolist(), "section_audit": audit, "lumped_rpm_sweep": lumped,
    })
    return params, physical, ids


def voxelize(fluid, pitch, offset):
    return solver.voxelize_fluid_solid(fluid["fluid_solid"], dx=pitch, grid_offset_mm=(offset,) * 3)


def solve(grid, params, fluid, mass, **options):
    native = solver._jacobi_cg
    try:
        attach(solver)
        return solver.solve_3d_navier_stokes_fvm(grid, params, fluid, mass, **options)
    finally:
        solver._jacobi_cg = native


def archive_result(params, physical, grid, pitch, offset, ids):
    prefix = "" if pitch == 4 else "polished_"
    archived = VALIDATION / f"{prefix}wot_dx{pitch:g}_offset{offset:g}_rpm7000.json"
    old = read_json(archived)
    old_params_path = REVISION / old["geometry"] / "parameters.json"
    assert old["source_sha256"]["frozen_solver"] == ids["frozen_solver"]
    assert digest(old_params_path) == old["source_sha256"]["parameters"]
    old_params = read_json(old_params_path)
    assert params["runners"] == old_params["runners"]
    old_fluid = extract(old_params)
    if not all(np.array_equal(physical[key], old_fluid[key]) for key in ("p_flange_face", "tb_axis", "tip_y")):
        return None, None
    old_grid = voxelize(old_fluid, pitch, offset)
    keys = ("xs_mm", "ys_mm", "zs_mm", "inside")
    if not all(np.array_equal(grid[key], old_grid[key]) for key in keys):
        print("Archived grid differs; solving export-derived grid", pitch, offset, flush=True)
        return None, None
    assert old["inputs"]["flow_kg_s"] == MAIN_FLOW and old["inputs"]["pressure_amg_preconditioned"]
    if not old["result"]["converged"]:
        return None, None
    return old["result"], {"path": str(archived.relative_to(REVISION)), "sha256": digest(archived),
                           "verified_equal": [*keys, "throttle_face", "throttle_axis", "tip_y", "runners"]}


def boundary_cases(design, params, fluid, ids):
    results = []
    for pitch, offset, outlets in ((2, 0, None), (2, 1, None), (4, 0, [])):
        grid = voxelize(fluid, pitch, offset)
        result = solve(grid, params, fluid, MAIN_FLOW, active_cyls=outlets, n_picard=0)
        diag = result["boundary_diagnostics"]
        if outlets == []:
            assert result["status"] == "FAILED_BOUNDARY", result
        else:
            assert diag["inlet_to_outlet_connected"] and diag["disjoint_outlets"] and not diag["empty_active_outlets"], diag
            assert diag["n_inlet_cells"] > 400 and min(diag["outlet_face_counts_all"]) >= 320, diag
        results.append({"dx_mm": pitch, "offset_mm": offset, "status": result["status"], "boundary": diag})
    inlet = [r["boundary"]["n_inlet_cells"] for r in results[:2]]
    assert abs(inlet[0] - inlet[1]) / max(inlet) < 0.08, inlet
    write_json(HERE / f"{design}_boundary.json", {"source_sha256": ids, "cases": results})


def run(designs, groups, max_iterations):
    cases = {"grid": GRID_CASES, "rpm": RPM_CASES, "mask": MASK_CASES, "valve": SENSITIVITY_CASES}
    requested = [case for group in groups if group != "boundary" for case in cases[group]]
    folder = HERE / "cases"
    folder.mkdir(exist_ok=True)
    for design in designs:
        print("Loading verified split STLs", design, flush=True)
        params, fluid, ids = from_exports(design)
        grids = {}
        if "boundary" in groups:
            boundary_cases(design, params, fluid, ids)
        for pitch, offset, rpm, cylinder, valve_k in requested:
            label = f"{design}_dx{pitch:g}_shift{offset:g}_rpm{rpm}"
            label += f"_c{cylinder}" if cylinder else ""
            label += f"_k{valve_k}" if valve_k != 14 else ""
            path = folder / f"{label}.json"
            if path.exists():
                old = read_json(path)
                if old["source_sha256"] == ids and old["result"]["converged"]:
                    print(label, "already converged", flush=True)
                    continue
            start = perf_counter()
            if (pitch, offset) not in grids:
                grids[pitch, offset] = voxelize(fluid, pitch, offset)
            grid = grids[pitch, offset]
            print(label, int(grid["inside"].sum()), "cells", flush=True)
            mass = MAIN_FLOW * rpm / 7000 * (0.35 if cylinder else 1)
            result, evidence = None, None
            if design == "corrected" and (pitch, offset, rpm, cylinder, valve_k) in GRID_CASES:
                result, evidence = archive_result(params, fluid, grid, pitch, offset, ids)
            if result is None:
                result = solve(grid, params, fluid, mass, active_cyls=[cylinder] if cylinder else None,
                               n_picard=max_iterations, k_port_valve=valve_k)
            if cylinder and result["converged"]:
                flows = result["cyl_mass_flow_raw_kgs"]
                assert abs(flows[cylinder - 1] - mass) < 1e-4 and all(
                    f == 0 for i, f in enumerate(flows, 1) if i != cylinder), flows
            write_json(path, {"design": design, "source_sha256": ids, "archived_exact_grid": evidence,
                "elapsed_s": perf_counter() - start, "inputs": {"dx_mm": pitch, "offset_mm": offset,
                "rpm": rpm, "flow_kg_s": mass, "active_cyls": [cylinder] if cylinder else [1, 2, 3, 4],
                "valve_k": valve_k, "wall_drag_multiplier": 1.4, "boost_psig": solver.BOOST_PSI,
                "inlet_temperature_c": solver.T0_IN_K - 273.15, "picard_limit": max_iterations},
                "result": {k: v for k, v in result.items() if not k.startswith("slice_")}})
            print(label, result["status"], result.get("tb_to_plenum_dp_kpa"),
                  result.get("cyl_maldistribution_spread_pct"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", nargs="+", choices=tuple(ROOTS), default=tuple(ROOTS))
    parser.add_argument("--group", nargs="+", choices=("grid", "boundary", "rpm", "mask", "valve"),
                        default=("boundary", "grid", "rpm", "mask", "valve"))
    parser.add_argument("--max-iterations", type=int, default=400)
    args = parser.parse_args()
    with one_job():
        run(args.design, args.group, args.max_iterations)
