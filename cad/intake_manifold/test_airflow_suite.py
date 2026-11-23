#!/usr/bin/env python3
"""
Automated Verification & Regression Test Suite for 3D FVM + CAD Boundary Tagging.

Tests required by GEMINI_REVIEW.md:
  1. Straight circular duct benchmark (Ø42.8 x 200 mm): convergence, mass balance, physical dP.
  2. Symmetric 4-way T-manifold (nominal & half-cell shifted grids): grid-phase invariance & symmetry.
  3. Stage-2 CAD outlet-masking matrix: all 4 open, each single runner open ([1]..[4]), empty ([]).
  4. Stage-2 CAD fine-grid (dx = 2.0 mm) boundary & phase-shift validation (aligned vs. half-shifted).
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys

import manifold3d as md
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_intake_manifold as gen
import verify_airflow as va

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_parameters.json"


def _make_straight_duct_case(dx: float = 3.0):
    params = {
        "runners": {
            "center_x_mm": [0.0],
            "spigot": {
                "outer_width_mm": 50.8,
                "outer_height_mm": 50.8,
                "wall_thickness_mm": 4.0,
                "tip_y_mm": -146.0,
                "center_z_mm": -35.0,
            },
        },
        "throttle_body": {"bore_diameter_mm": 42.8},
    }
    # Circular cylinder D=42.8 mm along Y in [-146, +54] centered at (0, Y, -35)
    cyl = md.Manifold.cylinder(200.0, 21.4, 21.4, circular_segments=96, center=True)
    cyl = cyl.rotate([90.0, 0.0, 0.0]).translate([0.0, -46.0, -35.0])
    fluid_meta = {
        "fluid_solid": cyl,
        "p_flange_face": np.array([0.0, 54.0, -35.0]),
        "tb_axis": np.array([0.0, 1.0, 0.0]),
        "tip_y": -146.0,
    }
    grid = va.voxelize_fluid_solid(cyl, dx=dx)
    mdot_pipe = 0.10
    res = va.solve_3d_navier_stokes_fvm(
        grid, params, fluid_meta, total_mass_flow_kgs=mdot_pipe, active_cyls=[1], n_picard=200, k_port_valve=0.0, wall_drag_mult=1.0
    )
    assert res["status"] == "CONVERGED" and res["converged"], f"Pipe failed to converge: {res}"
    assert res["mass_conservation_error_pct"] < 1e-3, f"Pipe mass err: {res['mass_conservation_error_pct']}"
    assert res["convergence"]["cg_max_info"] == 0
    assert res["convergence"]["bicgstab_max_info"] == 0
    assert res["cyl_maldistribution_spread_pct"] is None

    # Analytical turbulent Darcy-Weisbach comparison across 156 mm gauge section
    d_m = 0.0428
    area_m2 = math.pi * 0.25 * d_m**2
    u_m = mdot_pipe / (va.RHO0 * area_m2)
    re = va.RHO0 * u_m * d_m / va.MU_AIR
    f_d = 1.0 / (-1.8 * math.log10((va.EPSILON_WALL_M / (3.7 * d_m)) ** 1.11 + 6.9 / re)) ** 2
    dp_analytical_pa = f_d * (0.156 / d_m) * 0.5 * va.RHO0 * (u_m**2)
    dp_fvm_pa = res["tb_to_plenum_dp_kpa"] * 1000.0
    # Staircased grid + eddy viscosity adds finite laminar/roughness head over 1D Darcy; verify strictly positive and same OOM
    assert 0.5 * dp_analytical_pa <= dp_fvm_pa <= 6.0 * dp_analytical_pa, (
        f"Pipe dP={dp_fvm_pa:.1f} Pa out of physical range vs analytical Darcy {dp_analytical_pa:.1f} Pa"
    )
    print(f"[PASS] Test 1: Straight Pipe Benchmark (iters={res['outer_iterations']}, dP={dp_fvm_pa:.1f} Pa vs Darcy={dp_analytical_pa:.1f} Pa)")


def _make_symmetric_4way_case():
    params = {
        "runners": {
            "center_x_mm": [-138.0, -46.0, 46.0, 138.0],
            "spigot": {
                "outer_width_mm": 50.8,
                "outer_height_mm": 50.8,
                "wall_thickness_mm": 4.0,
                "tip_y_mm": -146.0,
                "center_z_mm": 0.0,
            },
        },
        "throttle_body": {"bore_diameter_mm": 65.0},
    }
    # Symmetric header box X in [-180, +180], Y in [-40, +40], Z in [-32, +32]
    box = md.Manifold.cube([360.0, 80.0, 64.0], center=True).translate([0.0, 0.0, 0.0])
    # Central top +Y inlet pipe D=65 mm entering strictly at X=0 (Y in [0, 90], Z=0)
    tb = md.Manifold.cylinder(90.0, 32.5, 32.5, circular_segments=72, center=True).rotate([-90.0, 0.0, 0.0]).translate([0.0, 45.0, 0.0])
    runners = []
    for xc in params["runners"]["center_x_mm"]:
        r = md.Manifold.cylinder(146.0, 21.4, 21.4, circular_segments=64, center=True).rotate([90.0, 0.0, 0.0]).translate([xc, -73.0, 0.0])
        runners.append(r)
    solid = gen.m_union([box, tb, *runners])
    fluid_meta = {
        "fluid_solid": solid,
        "p_flange_face": np.array([0.0, 90.0, 0.0]),
        "tb_axis": np.array([0.0, 1.0, 0.0]),
        "tip_y": -146.0,
    }
    sym_results = {}
    for label, off in [("aligned", (0.0, 0.0, 0.0)), ("half_shifted", (2.0, 2.0, 2.0))]:
        g = va.voxelize_fluid_solid(solid, dx=4.0, grid_offset_mm=off)
        res = va.solve_3d_navier_stokes_fvm(g, params, fluid_meta, total_mass_flow_kgs=0.14, active_cyls=[1, 2, 3, 4], n_picard=320)
        assert res["status"] == "CONVERGED" and res["converged"], f"Sym 4-way ({label}) failed: {res}"
        assert res["mass_conservation_error_pct"] < 1e-3
        assert res["convergence"]["cg_max_info"] == 0 and res["convergence"]["bicgstab_max_info"] == 0
        sh = res["cyl_flow_share_pct"]
        assert abs(sh[0] - sh[3]) < 0.05 and abs(sh[1] - sh[2]) < 0.05, (
            f"Sym 4-way ({label}) broke mirror symmetry: {sh}"
        )
        sym_results[label] = res
        print(
            f"[PASS] Test 2 ({label}): Symmetric 4-Way Manifold "
            f"(iters={res['outer_iterations']}, shares={sh}, dp={res['tb_to_plenum_dp_kpa']} kPa)"
        )
    sh_a = np.array(sym_results["aligned"]["cyl_flow_share_pct"], dtype=np.float64)
    sh_s = np.array(sym_results["half_shifted"]["cyl_flow_share_pct"], dtype=np.float64)
    dp_a = sym_results["aligned"]["tb_to_plenum_dp_kpa"]
    dp_s = sym_results["half_shifted"]["tb_to_plenum_dp_kpa"]
    assert float(np.max(np.abs(sh_a - sh_s))) < 0.25, f"Grid-phase shift changed shares: {sh_a} vs {sh_s}"
    assert abs(dp_a - dp_s) / max(abs(dp_a), 1e-6) < 0.03, f"Grid-phase shift changed dP: {dp_a} vs {dp_s}"
    print(f"[PASS] Test 2 (phase-invariance): max |dShare|={float(np.max(np.abs(sh_a - sh_s))):.4f}%, rel dP diff={abs(dp_a - dp_s)/max(abs(dp_a), 1e-6)*100:.2f}%")


def _make_stage2_matrix_and_fine_grid_tests():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    fluid = va.extract_fluid_cavity(params)
    mdot = 0.2777

    # 3) Fine-grid 2.0 mm boundary & phase-shift check
    for label, off in [("dx2_aligned", (0.0, 0.0, 0.0)), ("dx2_shifted", (1.0, 1.0, 1.0))]:
        g2 = va.voxelize_fluid_solid(fluid["fluid_solid"], dx=2.0, grid_offset_mm=off)
        r2 = va.solve_3d_navier_stokes_fvm(g2, params, fluid, total_mass_flow_kgs=mdot, active_cyls=[1, 2, 3, 4], n_picard=0)
        bd = r2["boundary_diagnostics"]
        assert bd["n_inlet_cells"] > 200, f"{label} low inlet cells: {bd}"
        assert bd["disjoint_outlets"] and bd["inlet_to_outlet_connected"]
        assert len(bd["empty_active_outlets"]) == 0
        assert all(cnt >= 320 for cnt in bd["outlet_face_counts_all"]), f"{label} expected ~360 faces/runner, got {bd['outlet_face_counts_all']}"
        print(f"[PASS] Test 4 ({label}): 2mm Boundary Counts={bd['outlet_face_counts_all']}, InletCells={bd['n_inlet_cells']}, Connected=True")

    # 4) Stage-2 4 mm outlet-masking matrix
    g4 = va.voxelize_fluid_solid(fluid["fluid_solid"], dx=4.0)

    # All open
    r_all = va.solve_3d_navier_stokes_fvm(g4, params, fluid, total_mass_flow_kgs=mdot, active_cyls=[1, 2, 3, 4], n_picard=320)
    assert r_all["status"] == "CONVERGED" and r_all["mass_conservation_error_pct"] < 1e-3
    assert r_all["convergence"]["cg_max_info"] == 0 and r_all["convergence"]["bicgstab_max_info"] == 0
    print(f"[PASS] Test 3a (All 4 Open): spread={r_all['cyl_maldistribution_spread_pct']}%, dP={r_all['tb_to_plenum_dp_kpa']} kPa")

    # Each individual cylinder open ([1], [2], [3], [4])
    for cyl in (1, 2, 3, 4):
        r_one = va.solve_3d_navier_stokes_fvm(g4, params, fluid, total_mass_flow_kgs=mdot * 0.35, active_cyls=[cyl], n_picard=320)
        assert r_one["status"] == "CONVERGED" and r_one["mass_conservation_error_pct"] < 1e-3
        assert r_one["cyl_maldistribution_spread_pct"] is None
        for idx in range(4):
            if idx + 1 == cyl:
                assert abs(r_one["cyl_mass_flow_raw_kgs"][idx] - mdot * 0.35) < 1e-4
                assert abs(r_one["cyl_flow_share_pct"][idx] - 100.0) < 1e-2
            else:
                assert r_one["cyl_mass_flow_raw_kgs"][idx] == 0.0, f"Inactive cyl {idx+1} leaked flow: {r_one['cyl_mass_flow_raw_kgs']}"
                assert r_one["cyl_flow_share_pct"][idx] == 0.0
        print(f"[PASS] Test 3b (Only Cyl {cyl} Open): flows={r_one['cyl_mass_flow_raw_kgs']}, dP={r_one['tb_to_plenum_dp_kpa']} kPa")

    # Empty active outlets -> structured FAILED_BOUNDARY
    r_empty = va.solve_3d_navier_stokes_fvm(g4, params, fluid, total_mass_flow_kgs=mdot, active_cyls=[], n_picard=240)
    assert r_empty["status"] == "FAILED_BOUNDARY" and not r_empty["converged"]
    print("[PASS] Test 3c (Empty Outlets): Cleanly rejected with FAILED_BOUNDARY")


def main():
    _make_straight_duct_case()
    _make_symmetric_4way_case()
    _make_stage2_matrix_and_fine_grid_tests()
    print("\nALL AIRFLOW VERIFICATION & BOUNDARY REGRESSION TESTS PASSED.")


if __name__ == "__main__":
    main()
