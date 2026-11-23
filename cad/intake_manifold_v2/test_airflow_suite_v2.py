#!/usr/bin/env python3
"""
Automated Verification & Regression Test Suite for V2 3D FVM + CAD Boundary Tagging.

Tests required by GEMINI_REVIEW.md:
  1. Straight circular duct benchmark (Ø42.8 x 200 mm): convergence, mass balance, physical dP.
  2. Symmetric 4-way T-manifold (nominal & half-cell shifted grids): grid-phase invariance & symmetry.
  3. Stage-2 V2 CAD outlet-masking matrix: all 4 open, each single runner open ([1]..[4]), empty ([]).
  4. Stage-2 V2 CAD fine-grid (dx = 2.0 mm) boundary & phase-shift validation (aligned vs. half-shifted).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import manifold3d as md
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_intake_manifold_v2 as gen
import verify_airflow_v2 as va

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_v2_parameters.json"


def _make_straight_duct_case(dx: float = 3.0):
    params = {
        "runners": {"center_x_mm": [0.0], "spigot": {"outer_width_mm": 50.8, "outer_height_mm": 50.8, "wall_thickness_mm": 4.0, "tip_y_mm": -146.0, "center_z_mm": 68.0}},
        "throttle_body": {"bore_diameter_mm": 42.8},
    }
    cyl = md.Manifold.cylinder(200.0, 21.4, 21.4, circular_segments=96, center=True).rotate([90.0, 0.0, 0.0]).translate([0.0, -46.0, 68.0])
    fluid_meta = {"fluid_solid": cyl, "p_flange_face": np.array([0.0, 54.0, 68.0]), "tb_axis": np.array([0.0, 1.0, 0.0]), "tip_y": -146.0}
    res = va.solve_3d_navier_stokes_fvm(va.voxelize_fluid_solid(cyl, dx=dx), params, fluid_meta, total_mass_flow_kgs=0.10, active_cyls=[1], n_picard=240, k_port_valve=0.0, wall_drag_mult=1.0)
    assert res["status"] == "CONVERGED" and res["converged"] and res["mass_conservation_error_pct"] < 1e-3
    assert res["convergence"]["cg_max_info"] == 0 and res["convergence"]["bicgstab_max_info"] == 0 and res["cyl_maldistribution_spread_pct"] is None
    d_m = 0.0428
    u_m = 0.10 / (va.RHO0 * math.pi * 0.25 * d_m**2)
    f_d = 1.0 / (-1.8 * math.log10((va.EPSILON_WALL_M / (3.7 * d_m)) ** 1.11 + 6.9 / (va.RHO0 * u_m * d_m / va.MU_AIR))) ** 2
    dp_analytical_pa = f_d * (0.156 / d_m) * 0.5 * va.RHO0 * (u_m**2)
    dp_fvm_pa = res["tb_to_plenum_dp_kpa"] * 1000.0
    assert 0.5 * dp_analytical_pa <= dp_fvm_pa <= 6.0 * dp_analytical_pa
    print(f"[PASS] Test 1: Straight Pipe Benchmark (iters={res['outer_iterations']}, dP={dp_fvm_pa:.1f} Pa vs Darcy={dp_analytical_pa:.1f} Pa)")


def _make_symmetric_4way_case():
    params = {
        "runners": {"center_x_mm": [-138.0, -46.0, 46.0, 138.0], "spigot": {"outer_width_mm": 50.8, "outer_height_mm": 50.8, "wall_thickness_mm": 4.0, "tip_y_mm": -146.0, "center_z_mm": 0.0}},
        "throttle_body": {"bore_diameter_mm": 65.0},
    }
    box = md.Manifold.cube([360.0, 80.0, 64.0], center=True)
    tb = md.Manifold.cylinder(90.0, 32.5, 32.5, circular_segments=72, center=True).rotate([-90.0, 0.0, 0.0]).translate([0.0, 45.0, 0.0])
    runners = [md.Manifold.cylinder(146.0, 21.4, 21.4, circular_segments=64, center=True).rotate([90.0, 0.0, 0.0]).translate([xc, -73.0, 0.0]) for xc in params["runners"]["center_x_mm"]]
    solid = gen.m_union([box, tb, *runners])
    fluid_meta = {"fluid_solid": solid, "p_flange_face": np.array([0.0, 90.0, 0.0]), "tb_axis": np.array([0.0, 1.0, 0.0]), "tip_y": -146.0}
    sym_results = {}
    for label, off in [("aligned", (0.0, 0.0, 0.0)), ("half_shifted", (2.0, 2.0, 2.0))]:
        res = va.solve_3d_navier_stokes_fvm(va.voxelize_fluid_solid(solid, dx=4.0, grid_offset_mm=off), params, fluid_meta, total_mass_flow_kgs=0.14, active_cyls=[1, 2, 3, 4], n_picard=320)
        assert res["status"] == "CONVERGED" and res["converged"] and res["mass_conservation_error_pct"] < 1e-3
        assert res["convergence"]["cg_max_info"] == 0 and res["convergence"]["bicgstab_max_info"] == 0
        sh = res["cyl_flow_share_pct"]
        assert abs(sh[0] - sh[3]) < 0.05 and abs(sh[1] - sh[2]) < 0.05
        sym_results[label] = res
        print(f"[PASS] Test 2 ({label}): Symmetric 4-Way Manifold (iters={res['outer_iterations']}, shares={sh}, dp={res['tb_to_plenum_dp_kpa']} kPa)")
    sh_a, sh_s = np.array(sym_results["aligned"]["cyl_flow_share_pct"]), np.array(sym_results["half_shifted"]["cyl_flow_share_pct"])
    dp_a, dp_s = sym_results["aligned"]["tb_to_plenum_dp_kpa"], sym_results["half_shifted"]["tb_to_plenum_dp_kpa"]
    assert float(np.max(np.abs(sh_a - sh_s))) < 0.25 and abs(dp_a - dp_s) / max(abs(dp_a), 1e-6) < 0.03
    print(f"[PASS] Test 2 (phase-invariance): max |dShare|={float(np.max(np.abs(sh_a - sh_s))):.4f}%, rel dP diff={abs(dp_a - dp_s)/dp_a*100:.2f}%")


def _make_stage2_v2_matrix_and_fine_grid_tests():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    fluid = va.extract_fluid_cavity(params)
    mdot = 0.2777

    # 2.0 mm fine-grid aligned & shifted boundary validation
    inlet_counts = []
    for label, off in [("dx2_aligned", (0.0, 0.0, 0.0)), ("dx2_shifted", (1.0, 1.0, 1.0))]:
        r2 = va.solve_3d_navier_stokes_fvm(va.voxelize_fluid_solid(fluid["fluid_solid"], dx=2.0, grid_offset_mm=off), params, fluid, total_mass_flow_kgs=mdot, active_cyls=[1, 2, 3, 4], n_picard=0)
        bd = r2["boundary_diagnostics"]
        assert bd["n_inlet_cells"] > 400 and bd["disjoint_outlets"] and bd["inlet_to_outlet_connected"] and len(bd["empty_active_outlets"]) == 0
        assert all(cnt >= 320 for cnt in bd["outlet_face_counts_all"]), f"{label}: {bd['outlet_face_counts_all']}"
        inlet_counts.append(bd["n_inlet_cells"])
        print(f"[PASS] Test 4 ({label}): 2mm Boundary Counts={bd['outlet_face_counts_all']}, Oblique InletCells={bd['n_inlet_cells']}, Connected=True")
    assert abs(inlet_counts[0] - inlet_counts[1]) / max(inlet_counts) < 0.08, f"Oblique TB inlet phase drift too large: {inlet_counts}"

    # Stage-2 V2 4 mm outlet-masking matrix
    g4 = va.voxelize_fluid_solid(fluid["fluid_solid"], dx=4.0)
    r_all = va.solve_3d_navier_stokes_fvm(g4, params, fluid, total_mass_flow_kgs=mdot, active_cyls=[1, 2, 3, 4], n_picard=320)
    assert r_all["status"] == "CONVERGED" and r_all["mass_conservation_error_pct"] < 1e-3 and r_all["convergence"]["cg_max_info"] == 0 and r_all["convergence"]["bicgstab_max_info"] == 0
    print(f"[PASS] Test 3a (V2 All 4 Open): spread={r_all['cyl_maldistribution_spread_pct']}%, dP={r_all['tb_to_plenum_dp_kpa']} kPa, shares={r_all['cyl_flow_share_pct']}")

    for cyl in (1, 2, 3, 4):
        r_one = va.solve_3d_navier_stokes_fvm(g4, params, fluid, total_mass_flow_kgs=mdot * 0.35, active_cyls=[cyl], n_picard=320)
        assert r_one["status"] == "CONVERGED" and r_one["mass_conservation_error_pct"] < 1e-3 and r_one["cyl_maldistribution_spread_pct"] is None
        for idx in range(4):
            if idx + 1 == cyl:
                assert abs(r_one["cyl_mass_flow_raw_kgs"][idx] - mdot * 0.35) < 1e-4 and abs(r_one["cyl_flow_share_pct"][idx] - 100.0) < 1e-2
            else:
                assert r_one["cyl_mass_flow_raw_kgs"][idx] == 0.0 and r_one["cyl_flow_share_pct"][idx] == 0.0
        print(f"[PASS] Test 3b (V2 Only Cyl {cyl} Open): flows={r_one['cyl_mass_flow_raw_kgs']}, dP={r_one['tb_to_plenum_dp_kpa']} kPa")

    r_empty = va.solve_3d_navier_stokes_fvm(g4, params, fluid, total_mass_flow_kgs=mdot, active_cyls=[], n_picard=320)
    assert r_empty["status"] == "FAILED_BOUNDARY" and not r_empty["converged"]
    print("[PASS] Test 3c (V2 Empty Outlets): Cleanly rejected with FAILED_BOUNDARY")


def main():
    _make_straight_duct_case()
    _make_symmetric_4way_case()
    _make_stage2_v2_matrix_and_fine_grid_tests()
    print("\nALL V2 AIRFLOW VERIFICATION & BOUNDARY REGRESSION TESTS PASSED.")


if __name__ == "__main__":
    main()
