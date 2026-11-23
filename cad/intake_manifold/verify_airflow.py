#!/usr/bin/env python3
"""
Airflow Verification & Boost Aerodynamic Optimization Suite for the
2004 Ford Focus SVT (2.0L Zetec-E Turbo @ 18 psi) Upper Intake Manifold.

Combines:
  1. Exact 3D CAD internal cavity extraction & axial/projected blockage audit (manifold3d).
  2. Fast, strictly mass-conserving 3D Finite-Volume Navier-Stokes Solver
     (Rhie-Chow stabilized Oseen-SIMPLE projection with Colebrook wall shear and eddy
     viscosity, solved via Jacobi-preconditioned CG / BiCGSTAB) on the 3D fluid cavity
     at 18.0 psi boost / 7,000 RPM.
  3. 1D/Quasi-3D Compressible Fanno + Idelchik Dividing-Flow + 720-deg Crank-Angle
     Pulsating Engine Simulation (1-3-4-2 firing order) + Helmholtz wave tuning.
  4. Parametric comparison & taper sweep: Baseline (14 mm protruding stacks, 0.78 taper,
     10 deg cant) vs. Boost-Optimized (wall-flush 6.5 mm bellmouths, taper, cant).

Outputs:
  stl/airflow_verification.json
  fitment/03_airflow_verification.png
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import time
from pathlib import Path

import manifold3d as md
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
import numpy as np
import scipy.sparse as sp
import scipy.sparse.csgraph as csgraph
import scipy.sparse.linalg as spla
from shapely.geometry import Polygon as ShapelyPolygon
import trimesh

import generate_intake_manifold as gen

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_parameters.json"
STL_DIR = ROOT / "stl"
FITMENT_DIR = ROOT / "fitment"

# Gas & Engine Operating Envelope (2004 Focus SVT 2.02L Zetec-E + Pulsar G25-550 @ 18 psi)
GAMMA = 1.4
R_AIR = 287.058  # J/(kg*K)
P_AMB_PA = 101325.0
BOOST_PSI = 18.0
PSI_TO_PA = 6894.757
P0_IN_PA = P_AMB_PA + BOOST_PSI * PSI_TO_PA  # 225,431 Pa abs
T0_IN_K = 325.15  # 52 C / 125 F intercooled charge air at 18 psi
RHO0 = P0_IN_PA / (R_AIR * T0_IN_K)  # 2.415 kg/m^3
MU_AIR = 1.96e-5  # Pa*s at 325 K
A0_SOUND = math.sqrt(GAMMA * R_AIR * T0_IN_K)  # 361.5 m/s

BORE_M = 0.0853
STROKE_M = 0.0880
ROD_M = 0.1363
N_CYL = 4
ENGINE_DISP_L = (math.pi * 0.25 * BORE_M**2 * STROKE_M * N_CYL) * 1000.0  # 2.012 L
DESIGN_RPM = 7000.0
VE_REF = 0.98
EPSILON_WALL_M = 0.000035  # 0.035 mm internal printed PAHT-CF/PPA-CF surface roughness


# ---------------------------------------------------------------------------
# 1. Exact 3D CAD Fluid Cavity Extraction & Geometric Audit
# ---------------------------------------------------------------------------

def _oriented_halfspace(origin: np.ndarray, normal_keep: np.ndarray, size: float = 1200.0) -> md.Manifold:
    """Create a large cube keeping the half-space (x - origin) . normal_keep >= 0."""
    n = normal_keep / np.linalg.norm(normal_keep)
    box = md.Manifold.cube([size, size, size], center=True).translate([0.0, 0.0, size * 0.5])
    mesh = gen.manifold_to_trimesh(box)
    z = np.array([0.0, 0.0, 1.0])
    if np.allclose(n, -z):
        mat = np.diag([1.0, -1.0, -1.0, 1.0])
    elif np.allclose(n, z):
        mat = np.eye(4)
    else:
        import trimesh
        mat = trimesh.geometry.align_vectors(z, n)
    mesh.apply_transform(mat)
    mesh.apply_translation(origin)
    return gen.trimesh_to_manifold(mesh)


def extract_fluid_cavity(params: dict) -> dict:
    """
    Build the exact 3D internal air volume bounded at the 65 mm TB flange face
    and the 4 runner spigot exit planes (Y = tip_y_mm), directly from CAD primitives.
    """
    pl_inner = gen.build_plenum_loft(params, is_inner=True)
    bm_cfg = params["runners"]["bellmouth"]
    wall_flush = bool(bm_cfg.get("wall_flush_bellmouth", False))

    runner_bores: list[md.Manifold] = []
    bellmouth_outers: list[md.Manifold] = []
    for xc in params["runners"]["center_x_mm"]:
        rc = gen.build_single_runner_components(xc, params)
        runner_bores.append(rc["inner_bore"])
        bellmouth_outers.append(rc["bellmouth_outer"])

    tip_y = params["runners"]["spigot"]["tip_y_mm"]
    runner_clip = md.Manifold.cube([1200.0, 1200.0, 1200.0], center=True).translate([0.0, tip_y + 600.0, 0.0])
    runner_bores_clipped = [rb ^ runner_clip for rb in runner_bores]

    tb_parts_geom = gen.build_throttle_body_components(params)
    p_flange_face = tb_parts_geom["flange_face_center"]
    tb_axis = tb_parts_geom["tb_axis"]
    tb_bore_full = tb_parts_geom["tb_bore"]
    tb_clip = _oriented_halfspace(p_flange_face, -tb_axis)
    tb_bore_clipped = tb_bore_full ^ tb_clip

    fluid_raw = gen.m_union([pl_inner, tb_bore_clipped, *runner_bores_clipped])
    bm_intrusion = None
    if not wall_flush:
        # Solid sleeves protruding inside plenum displace air and obstruct cross-flow
        bm_walls = gen.m_union(bellmouth_outers) - gen.m_union(runner_bores_clipped)
        bm_intrusion = bm_walls ^ pl_inner
        fluid_solid = fluid_raw - bm_walls
    else:
        fluid_solid = fluid_raw

    return {
        "fluid_solid": fluid_solid,
        "pl_inner": pl_inner,
        "bm_intrusion": bm_intrusion,
        "tb_bore": tb_bore_clipped,
        "runner_bores": runner_bores_clipped,
        "p_flange_face": p_flange_face,
        "tb_axis": tb_axis,
        "tip_y": tip_y,
    }


def _polygon_area_perimeter(polys: list[np.ndarray]) -> tuple[float, float]:
    """Compute signed-nesting net area and perimeter of 2D cross-section polygons."""
    if not polys:
        return 0.0, 0.0
    sh = [ShapelyPolygon(p) for p in polys if len(p) >= 3]
    if not sh:
        return 0.0, 0.0
    area = 0.0
    perim = 0.0
    for i, pi in enumerate(sh):
        depth = sum(
            1
            for j, pj in enumerate(sh)
            if i != j and pj.area > pi.area and pj.contains(pi.representative_point())
        )
        perim += float(pi.length)
        if depth % 2 == 0:
            area += float(pi.area)
        else:
            area -= float(pi.area)
    return max(area, 0.0), perim


def _slice_normal_metrics(solid: md.Manifold, origin: np.ndarray, normal: np.ndarray) -> tuple[float, float, list[np.ndarray]]:
    """Slice `solid` on the plane through `origin` with unit `normal` and return (area_mm2, perim_mm, polys)."""
    n = np.asarray(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    mesh = gen.manifold_to_trimesh(solid)
    z_axis = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    # Transform solid so `origin` is at 0 and `n` aligns with +Z, then slice at Z=0
    if np.allclose(n, z_axis):
        rot = np.eye(4)
    elif np.allclose(n, -z_axis):
        rot = np.diag([1.0, -1.0, -1.0, 1.0])
    else:
        rot = trimesh.geometry.align_vectors(n, z_axis)
    mesh_t = mesh.copy()
    mesh_t.apply_translation(-np.asarray(origin, dtype=np.float64))
    mesh_t.apply_transform(rot)
    s_loc = gen.trimesh_to_manifold(mesh_t)
    polys = [np.asarray(p) for p in s_loc.slice(0.0).to_polygons() if len(p) >= 3]
    area, perim = _polygon_area_perimeter(polys)
    return float(area), float(perim), polys


def audit_cad_flow_geometry(fluid_meta: dict, params: dict, cross_check_stl_path: Path | None = None) -> dict:
    """
    Slice the true 3D internal air cavity along X (from Cyl 1 to TB flange) and normal to each
    runner centerline to measure exact effective flow area, bare plenum area, solid bluff shadow
    (tracked separately from empirical wake assumptions), true CAD throat/exit dimensions, and Dh(X).
    """
    fluid_solid = fluid_meta["fluid_solid"]
    pl_inner = fluid_meta["pl_inner"]
    bm_intrusion = fluid_meta["bm_intrusion"]

    rot_fluid = fluid_solid.rotate([0.0, -90.0, 0.0])
    rot_bare = pl_inner.rotate([0.0, -90.0, 0.0])
    rot_pl_fluid = (fluid_solid ^ pl_inner).rotate([0.0, -90.0, 0.0])

    xs = np.linspace(-172.0, 212.0, 97)
    area_fluid = []
    area_bare = []
    area_pl_fluid = []
    dh_fluid = []

    proj_grid_y = np.linspace(-55.0, 55.0, 45)
    proj_grid_z = np.linspace(-50.0, 50.0, 41)
    gy, gz = np.meshgrid(proj_grid_y, proj_grid_z, indexing="ij")
    pts_yz = np.column_stack([gy.ravel(), gz.ravel()])

    for x in xs:
        af, pf = _polygon_area_perimeter([np.asarray(p) for p in rot_fluid.slice(float(x)).to_polygons()])
        ab, _ = _polygon_area_perimeter([np.asarray(p) for p in rot_bare.slice(float(x)).to_polygons()])
        apf, _ = _polygon_area_perimeter([np.asarray(p) for p in rot_pl_fluid.slice(float(x)).to_polygons()])
        area_fluid.append(af)
        area_bare.append(ab)
        area_pl_fluid.append(apf)
        dh_fluid.append(4.0 * af / pf if pf > 1e-6 else 0.0)

    area_bare_arr = np.asarray(area_bare)
    area_pl_arr = np.asarray(area_pl_fluid)

    # Projected solid shadow fraction of protruding internal sleeves (0.0% when wall_flush=True)
    cyl_solid_shadow = []
    effective_core_arr = area_pl_arr.copy()
    if bm_intrusion is not None:
        rot_bm = bm_intrusion.rotate([0.0, -90.0, 0.0])
        for xc in params["runners"]["center_x_mm"]:
            blocked_mask = np.zeros(pts_yz.shape[0], dtype=bool)
            bare_mask = np.zeros(pts_yz.shape[0], dtype=bool)
            for p in rot_bare.slice(float(xc)).to_polygons():
                if len(p) >= 3:
                    bare_mask ^= MplPath(np.asarray(p)).contains_points(pts_yz)
            for dx_s in np.linspace(-30.0, 30.0, 15):
                polys_bm = [np.asarray(p) for p in rot_bm.slice(float(xc + dx_s)).to_polygons()]
                layer = np.zeros(pts_yz.shape[0], dtype=bool)
                for p in polys_bm:
                    if len(p) >= 3:
                        layer ^= MplPath(p).contains_points(pts_yz)
                blocked_mask |= layer
            n_bare = max(int(np.sum(bare_mask)), 1)
            blk_pct = float(np.sum(blocked_mask & bare_mask)) / n_bare * 100.0
            cyl_solid_shadow.append(round(blk_pct, 2))
            for i, x in enumerate(xs):
                w_g = math.exp(-0.5 * ((x - xc) / 14.0) ** 2)
                effective_core_arr[i] = min(effective_core_arr[i], area_bare_arr[i] * (1.0 - (blk_pct / 100.0) * w_g))
    else:
        cyl_solid_shadow = [0.0, 0.0, 0.0, 0.0]

    # Measure true normal-plane throat, sweep minimum, and spigot exit sections from CAD runner bores
    sp = params["runners"]["spigot"]
    tip_y = float(sp["tip_y_mm"])
    sp_z = float(sp["center_z_mm"])
    runner_sections = []
    throat_areas, throat_perims, exit_areas, exit_perims, min_areas = [], [], [], [], []
    for cyl_idx, (xc, rb_solid) in enumerate(zip(params["runners"]["center_x_mm"], fluid_meta["runner_bores"]), start=1):
        _p_bm, inlet_dir, p0, p1, p2, p3 = gen.runner_bezier_points(xc, params)
        a_th, p_th, _ = _slice_normal_metrics(rb_solid, p0, inlet_dir)
        a_ex, p_ex, _ = _slice_normal_metrics(rb_solid, np.array([xc, tip_y + 5.0, sp_z]), np.array([0.0, -1.0, 0.0]))
        sweep_areas = [a_th, a_ex]
        for tt in (0.05, 0.15, 0.30, 0.50, 0.70, 0.85, 0.95):
            pt_t, tan_t = gen.bezier_point_and_tangent(p0, p1, p2, p3, tt)
            a_t, _, _ = _slice_normal_metrics(rb_solid, pt_t, tan_t)
            if a_t > 100.0:
                sweep_areas.append(a_t)
        a_min = min(sweep_areas)
        dh_th = 4.0 * a_th / p_th if p_th > 1e-6 else 0.0
        runner_sections.append({
            "cylinder": cyl_idx,
            "x_center_mm": xc,
            "throat_area_mm2": round(a_th, 2),
            "throat_perimeter_mm": round(p_th, 2),
            "throat_dh_mm": round(dh_th, 2),
            "min_sweep_area_mm2": round(a_min, 2),
            "exit_area_mm2": round(a_ex, 2),
            "exit_perimeter_mm": round(p_ex, 2),
        })
        throat_areas.append(a_th)
        throat_perims.append(p_th)
        exit_areas.append(a_ex)
        exit_perims.append(p_ex)
        min_areas.append(a_min)

    fluid_mesh = gen.manifold_to_trimesh(fluid_solid)
    total_fluid_vol_l = float(fluid_mesh.volume) / 1_000_000.0
    bare_plenum_vol_l = float(gen.manifold_to_trimesh(pl_inner).volume) / 1_000_000.0

    stl_overlap_cm3 = None
    if cross_check_stl_path is not None and cross_check_stl_path.exists():
        stl_m = trimesh.load(cross_check_stl_path)
        stl_solid = gen.trimesh_to_manifold(stl_m)
        stl_overlap_cm3 = round(float((fluid_solid ^ stl_solid).volume()) / 1000.0, 4)

    area_throat = float(np.mean(throat_areas))
    perim_throat = float(np.mean(throat_perims))
    area_spigot_exit = float(np.mean(exit_areas))
    perim_exit = float(np.mean(exit_perims))
    tb_area = math.pi * 0.25 * (params["throttle_body"]["bore_diameter_mm"] ** 2)

    return {
        "xs_mm": xs.tolist(),
        "area_fluid_mm2": [round(v, 1) for v in area_fluid],
        "area_plenum_core_mm2": [round(float(v), 1) for v in effective_core_arr],
        "area_bare_mm2": [round(float(v), 1) for v in area_bare_arr],
        "dh_mm": [round(v, 2) for v in dh_fluid],
        "cyl_solid_shadow_pct": cyl_solid_shadow,
        "cyl_peak_blockage_pct": cyl_solid_shadow,
        "mean_stack_blockage_pct": round(float(np.mean(cyl_solid_shadow)), 2),
        "total_fluid_volume_liters": round(total_fluid_vol_l, 3),
        "bare_plenum_volume_liters": round(bare_plenum_vol_l, 3),
        "tb_inlet_area_mm2": round(tb_area, 1),
        "runner_throat_area_mm2": round(area_throat, 2),
        "runner_throat_perimeter_mm": round(perim_throat, 2),
        "runner_min_sweep_area_mm2": round(float(min(min_areas)), 2),
        "runner_exit_area_mm2": round(area_spigot_exit, 2),
        "runner_exit_perimeter_mm": round(perim_exit, 2),
        "runner_contraction_ratio": round(area_throat / area_spigot_exit, 3),
        "plenum_to_runner_area_ratio_cyl4": round(float(area_bare_arr[np.argmin(np.abs(xs - 138.0))]) / area_spigot_exit, 2),
        "plenum_to_runner_area_ratio_cyl1": round(float(area_bare_arr[np.argmin(np.abs(xs + 138.0))]) / area_spigot_exit, 2),
        "runner_normal_sections": runner_sections,
        "stl_cavity_wall_overlap_cm3": stl_overlap_cm3,
        "wot_cavity_scope": "Main TB-to-spigot WOT cavity (5 NPT vacuum ports and IACV passages modeled as closed/sealed)",
    }


# ---------------------------------------------------------------------------
# 2. Conservative 3D Finite-Volume Navier-Stokes Solver (Flux-Carrying SIMPLE)
# ---------------------------------------------------------------------------

def voxelize_fluid_solid(
    fluid_solid: md.Manifold,
    dx: float = 4.0,
    grid_offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> dict:
    """Classify a 3D uniform Cartesian grid against exact Z-slices of `fluid_solid`.
    Supports arbitrary sub-cell `grid_offset_mm = (ox, oy, oz)` for phase invariance testing.
    Aligns X grid nodes to exact cylinder periodicity at dx=4.0 mm when offset == 0.
    """
    solid_mesh = gen.manifold_to_trimesh(fluid_solid)
    bmin, bmax = solid_mesh.bounds[0], solid_mesh.bounds[1]
    ox, oy, oz = (float(v) for v in grid_offset_mm)

    x_phase = 2.0 if (abs(dx - 4.0) < 1e-6 and abs(ox) < 1e-9) else 0.0
    x_start = math.floor((bmin[0] - x_phase) / dx) * dx + x_phase + ox
    while x_start > bmin[0] + 1e-6:
        x_start -= dx
    y_start = math.floor(bmin[1] / dx) * dx + oy
    while y_start > bmin[1] + 1e-6:
        y_start -= dx
    z_phase = dx * 0.35 if abs(oz) < 1e-9 else oz
    z_start = math.floor(bmin[2] / dx) * dx + z_phase
    while z_start < bmin[2] + 1e-6:
        z_start += dx
    if z_start - dx > bmin[2] + 1e-6:
        z_start -= dx

    xs = np.arange(x_start, bmax[0] + dx * 0.75, dx)
    ys = np.arange(y_start, bmax[1] + dx * 0.75, dx)
    zs = np.arange(z_start, bmax[2] - dx * 0.10, dx)
    nx, ny, nz = len(xs), len(ys), len(zs)

    gx, gy = np.meshgrid(xs, ys, indexing="ij")
    pts_xy = np.column_stack([gx.ravel(), gy.ravel()])
    inside = np.zeros((nx, ny, nz), dtype=bool)

    for k, z_val in enumerate(zs):
        polys = [np.asarray(p) for p in fluid_solid.slice(float(z_val)).to_polygons()]
        if not polys:
            continue
        layer = np.zeros(pts_xy.shape[0], dtype=bool)
        for p in polys:
            if len(p) >= 3:
                layer ^= MplPath(p).contains_points(pts_xy)
        inside[:, :, k] = layer.reshape(nx, ny)

    return {
        "dx_m": dx * 1e-3,
        "dx_mm": dx,
        "grid_offset_mm": [ox, oy, oz],
        "xs_mm": xs,
        "ys_mm": ys,
        "zs_mm": zs,
        "inside": inside,
    }


def _jacobi_cg(
    A: sp.csr_matrix,
    b: np.ndarray,
    tol: float = 1e-7,
    maxiter: int = 3000,
    x0: np.ndarray | None = None,
) -> tuple[np.ndarray, int, float]:
    b_norm = float(np.linalg.norm(b))
    if b_norm < 1e-30:
        return np.zeros_like(b), 0, 0.0
    diag = np.maximum(A.diagonal(), 1e-12)
    M = sp.diags(1.0 / diag)
    x, info = spla.cg(A, b, x0=x0, rtol=tol, atol=0.0, maxiter=maxiter, M=M)
    rel_res = float(np.linalg.norm(A @ x - b)) / b_norm
    return x, int(info), rel_res


def _jacobi_bicgstab(
    A: sp.csr_matrix,
    b: np.ndarray,
    tol: float = 1e-6,
    maxiter: int = 400,
    x0: np.ndarray | None = None,
) -> tuple[np.ndarray, int, float]:
    b_norm = float(np.linalg.norm(b))
    if b_norm < 1e-30:
        return np.zeros_like(b), 0, 0.0
    diag = A.diagonal()
    inv_diag = np.where(np.abs(diag) > 1e-12, 1.0 / diag, 1.0)
    M = sp.diags(inv_diag)
    x, info = spla.bicgstab(A, b, x0=x0, rtol=tol, atol=0.0, maxiter=maxiter, M=M)
    rel_res = float(np.linalg.norm(A @ x - b)) / b_norm
    return x, int(info), rel_res


def solve_3d_navier_stokes_fvm(
    grid: dict,
    params: dict,
    fluid_meta: dict,
    total_mass_flow_kgs: float,
    active_cyls: list[int] | None = None,
    n_picard: int = 320,
    k_port_valve: float = 14.0,
    wall_drag_mult: float = 1.4,
    tol_mom: float = 2.0e-4,
) -> dict:
    """
    Strictly conservative 3D steady incompressible turbulent Navier-Stokes SIMPLE solver
    carrying strictly divergence-free signed face fluxes across outer iterations, with
    Patankar implicit under-relaxation, Rhie-Chow stabilization, Colebrook/Darcy wall
    shear, flux-weighted total-pressure reference planes, and pre-solve boundary validation.
    """
    cyl_xs = [float(x) for x in params["runners"]["center_x_mm"]]
    n_outlets_total = len(cyl_xs)
    if active_cyls is None:
        active_cyls = list(range(1, n_outlets_total + 1))

    dx_m = grid["dx_m"]
    dx_mm = grid["dx_mm"]
    xs_mm, ys_mm, zs_mm = grid["xs_mm"], grid["ys_mm"], grid["zs_mm"]
    inside = grid["inside"]
    nx, ny, nz = inside.shape
    N_grid = nx * ny * nz

    act_idx = np.flatnonzero(inside)
    n_cells = len(act_idx)
    if n_cells == 0:
        return {
            "status": "FAILED_BOUNDARY",
            "converged": False,
            "n_fluid_cells": 0,
            "boundary_diagnostics": {"reason": "Zero fluid cells inside voxelized domain"},
            "mass_conservation_error_pct": None,
            "cyl_mass_flow_raw_kgs": [0.0] * n_outlets_total,
            "cyl_flow_share_pct": [None] * n_outlets_total,
            "cyl_maldistribution_spread_pct": None,
            "tb_to_plenum_dp_kpa": None,
            "tb_to_plenum_dp_psi": None,
        }

    remap = np.full(N_grid, -1, dtype=np.int32)
    remap[act_idx] = np.arange(n_cells, dtype=np.int32)

    ii, jj, kk = np.unravel_index(act_idx, (nx, ny, nz))
    px = xs_mm[ii]
    py = ys_mm[jj]
    pz = zs_mm[kk]
    pts_mm = np.column_stack([px, py, pz])

    p_face = np.asarray(fluid_meta["p_flange_face"], dtype=np.float64)
    tb_axis = np.asarray(fluid_meta["tb_axis"], dtype=np.float64)
    tb_axis = tb_axis / np.linalg.norm(tb_axis)
    tip_y = float(fluid_meta["tip_y"])

    # Build neighbor table for all 6 faces
    dirs = [
        (1, 0, 0, "px", 0, 1.0),
        (-1, 0, 0, "mx", 0, -1.0),
        (0, 1, 0, "py", 1, 1.0),
        (0, -1, 0, "my", 1, -1.0),
        (0, 0, 1, "pz", 2, 1.0),
        (0, 0, -1, "mz", 2, -1.0),
    ]
    nbrs = {}
    wall_face_count = np.zeros(n_cells, dtype=np.float64)
    adj_rows, adj_cols = [], []
    for ox, oy, oz, key, _ax, _sgn in dirs:
        ni = np.clip(ii + ox, 0, nx - 1)
        nj = np.clip(jj + oy, 0, ny - 1)
        nk = np.clip(kk + oz, 0, nz - 1)
        in_bounds = (
            (ii + ox >= 0) & (ii + ox < nx) &
            (jj + oy >= 0) & (jj + oy < ny) &
            (kk + oz >= 0) & (kk + oz < nz)
        )
        raw_nbr = remap[np.ravel_multi_index((ni, nj, nk), (nx, ny, nz))]
        valid = in_bounds & (raw_nbr >= 0)
        nbrs[key] = (valid, np.where(valid, raw_nbr, 0))
        wall_face_count += (~valid).astype(np.float64)
        r_v = np.flatnonzero(valid)
        adj_rows.append(r_v)
        adj_cols.append(raw_nbr[valid])

    adj_mat = sp.csr_matrix(
        (np.ones(sum(len(r) for r in adj_rows)), (np.concatenate(adj_rows), np.concatenate(adj_cols))),
        shape=(n_cells, n_cells),
    )
    n_components, comp_labels = csgraph.connected_components(adj_mat, directed=False)

    # Geometric TB inlet-cap face tagging (1 open boundary layer matching +tb_axis cap)
    cardinal_axes = [(1, 0, 0, "px"), (-1, 0, 0, "mx"), (0, 1, 0, "py"), (0, -1, 0, "my"), (0, 0, 1, "pz"), (0, 0, -1, "mz")]
    in_open_key = max(cardinal_axes, key=lambda a: a[0] * tb_axis[0] + a[1] * tb_axis[1] + a[2] * tb_axis[2])[3]
    r_tb = 0.5 * float(params["throttle_body"]["bore_diameter_mm"])
    signed_dist_tb = (pts_mm - p_face[None, :]) @ tb_axis
    r_perp_tb = np.linalg.norm((pts_mm - p_face[None, :]) - signed_dist_tb[:, None] * tb_axis[None, :], axis=1)
    inlet_cell = (
        (~nbrs[in_open_key][0])
        & (signed_dist_tb >= -dx_mm * 1.25)
        & (signed_dist_tb <= dx_mm * 0.5)
        & (r_perp_tb <= r_tb + 0.75 * dx_mm)
    )

    # Geometric CAD spigot outlet patch tagging (1 face per unique (i, k) column on -Y cap)
    sp_cfg = params["runners"]["spigot"]
    r_sp_in = 0.5 * max(float(sp_cfg["outer_width_mm"]), float(sp_cfg["outer_height_mm"])) - float(sp_cfg["wall_thickness_mm"])
    sp_z = float(sp_cfg["center_z_mm"])
    outlet_masks: list[np.ndarray] = []
    for xc in cyl_xs:
        cand = np.flatnonzero(
            (~nbrs["my"][0]) & (py <= tip_y + 1.5 * dx_mm) & (np.hypot(px - xc, pz - sp_z) <= r_sp_in + 0.75 * dx_mm)
        )
        m = np.zeros(n_cells, dtype=bool)
        if len(cand) > 0:
            order_j = cand[np.argsort(jj[cand])]
            seen_ik: set[tuple[int, int]] = set()
            for ci in order_j:
                ik = (int(ii[ci]), int(kk[ci]))
                if ik not in seen_ik:
                    seen_ik.add(ik)
                    m[ci] = True
        outlet_masks.append(m)

    # Pre-solve boundary & connectivity verification
    valid_active_ids = all(isinstance(c, int) and 1 <= c <= n_outlets_total for c in active_cyls)
    overlap_counts = sum(m.astype(np.int32) for m in outlet_masks) if outlet_masks else np.zeros(n_cells, dtype=np.int32)
    disjoint_outlets = bool(np.all(overlap_counts <= 1))
    all_outlet_mask = np.zeros(n_cells, dtype=bool)
    empty_active = []
    if valid_active_ids:
        for c_idx in active_cyls:
            if not np.any(outlet_masks[c_idx - 1]):
                empty_active.append(c_idx)
            all_outlet_mask |= outlet_masks[c_idx - 1]

    inlet_comps = set(comp_labels[inlet_cell].tolist()) if np.any(inlet_cell) else set()
    active_out_comps = set(comp_labels[all_outlet_mask].tolist()) if np.any(all_outlet_mask) else set()
    connected_ok = bool(inlet_comps) and bool(active_out_comps) and (inlet_comps <= active_out_comps)
    # Also ensure every active outlet touches an inlet component
    all_active_outlets_sourced = True
    if valid_active_ids:
        for c_idx in active_cyls:
            om_c = outlet_masks[c_idx - 1]
            if not np.any(om_c) or not (set(comp_labels[om_c].tolist()) & inlet_comps):
                all_active_outlets_sourced = False

    n_in = int(np.sum(inlet_cell))
    boundary_diag = {
        "dx_mm": round(dx_mm, 3),
        "grid_offset_mm": grid.get("grid_offset_mm", [0.0, 0.0, 0.0]),
        "n_connected_components": int(n_components),
        "n_inlet_cells": n_in,
        "active_cyls": list(active_cyls),
        "outlet_face_counts_all": [int(np.sum(m)) for m in outlet_masks],
        "outlet_areas_mm2_all": [round(int(np.sum(m)) * (dx_mm**2), 2) for m in outlet_masks],
        "empty_active_outlets": empty_active,
        "disjoint_outlets": disjoint_outlets,
        "inlet_to_outlet_connected": connected_ok and all_active_outlets_sourced,
    }
    if (
        n_in == 0
        or len(active_cyls) == 0
        or not valid_active_ids
        or bool(empty_active)
        or not disjoint_outlets
        or not (connected_ok and all_active_outlets_sourced)
    ):
        return {
            "status": "FAILED_BOUNDARY",
            "converged": False,
            "n_fluid_cells": int(n_cells),
            "boundary_diagnostics": boundary_diag,
            "mass_conservation_error_pct": None,
            "cyl_mass_flow_raw_kgs": [0.0] * n_outlets_total,
            "cyl_forward_flow_kgs": [0.0] * n_outlets_total,
            "cyl_reverse_flow_kgs": [0.0] * n_outlets_total,
            "cyl_flow_share_pct": [None] * n_outlets_total,
            "cyl_maldistribution_spread_pct": None,
            "tb_to_plenum_dp_kpa": None,
            "tb_to_plenum_dp_psi": None,
        }

    tb_area_m2 = math.pi * 0.25 * (float(params["throttle_body"]["bore_diameter_mm"]) * 1e-3) ** 2
    u_in_mag = total_mass_flow_kgs / (RHO0 * tb_area_m2)
    u_in_vec = -tb_axis * u_in_mag
    face_area = dx_m * dx_m
    q_target = total_mass_flow_kgs / RHO0
    q_in_per_cell = np.where(inlet_cell, q_target / n_in, 0.0)

    # Subtract open inlet & active outlet cap faces from closed-wall shear count
    wall_face_count[inlet_cell & (~nbrs[in_open_key][0])] = np.maximum(
        wall_face_count[inlet_cell & (~nbrs[in_open_key][0])] - 1.0, 0.0
    )
    wall_face_count[all_outlet_mask] = np.maximum(wall_face_count[all_outlet_mask] - 1.0, 0.0)

    # Porous lower-runner + intake valve impedance cleanly downstream of reference section (py <= tip_y + 20 mm)
    spigot_zone = np.zeros(n_cells, dtype=bool)
    if k_port_valve > 0.0:
        for c_idx in active_cyls:
            xc_a = cyl_xs[c_idx - 1]
            spigot_zone |= (py <= tip_y + 20.0) & (np.hypot(px - xc_a, pz - sp_z) <= r_sp_in + 0.75 * dx_mm)

    inv_dx2 = 1.0 / (dx_m * dx_m)

    def calc_cell_grad(field: np.ndarray, outlet_dirichlet_zero: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        grads = []
        for k_p, k_m in [("px", "mx"), ("py", "my"), ("pz", "mz")]:
            vp, np_idx = nbrs[k_p]
            vm, nm_idx = nbrs[k_m]
            f_p = np.where(vp, field[np_idx], field)
            if outlet_dirichlet_zero and (k_m == "my"):
                has_out = (~vm) & all_outlet_mask
                f_m = np.where(vm, field[nm_idx], np.where(has_out, 0.0, field))
                denom = np.where(vp & (vm | has_out), 2.0 * dx_m, dx_m)
                has_diff = vp | vm | has_out
            else:
                f_m = np.where(vm, field[nm_idx], field)
                denom = np.where(vp & vm, 2.0 * dx_m, dx_m)
                has_diff = vp | vm
            grads.append(np.where(has_diff, (f_p - f_m) / denom, 0.0))
        return grads[0], grads[1], grads[2]

    # Step 1: Divergence-free potential flow initialization
    lp_rows0, lp_cols0, lp_vals0 = [], [], []
    lp_diag0 = np.zeros(n_cells, dtype=np.float64)
    for _ox, _oy, _oz, key, _ax, _sgn in dirs:
        valid, nb = nbrs[key]
        r = np.flatnonzero(valid)
        c = nb[valid]
        lp_rows0.append(r)
        lp_cols0.append(c)
        lp_vals0.append(np.full(len(r), -inv_dx2))
        np.add.at(lp_diag0, r, inv_dx2)
    lp_diag0[all_outlet_mask] += inv_dx2
    lp_rows0.append(np.arange(n_cells))
    lp_cols0.append(np.arange(n_cells))
    lp_vals0.append(lp_diag0)
    L_p0 = sp.csr_matrix(
        (np.concatenate(lp_vals0), (np.concatenate(lp_rows0), np.concatenate(lp_cols0))),
        shape=(n_cells, n_cells),
    )

    q_vol_src = q_in_per_cell / (dx_m**3)
    phi0, cg0_info, cg0_res = _jacobi_cg(L_p0, q_vol_src, tol=1e-8, maxiter=3000)
    gx0, gy0, gz0 = calc_cell_grad(phi0, outlet_dirichlet_zero=True)
    u = -gx0.copy()
    v = -gy0.copy()
    w = -gz0.copy()
    p = np.zeros(n_cells, dtype=np.float64)

    # Persistent strictly divergence-free signed face fluxes (initialized from phi0)
    face_flux: dict[str, np.ndarray] = {}
    for _ox, _oy, _oz, key, _ax, _sgn in dirs:
        valid, nb = nbrs[key]
        r = np.flatnonzero(valid)
        c = nb[valid]
        face_flux[key] = -(phi0[c] - phi0[r]) / dx_m
    om_idx = np.flatnonzero(all_outlet_mask)
    v_out_divfree = phi0[om_idx] / dx_m

    # Reference sampling masks (cleanly outside TB source plug & porous exit zone)
    inlet_ref = (signed_dist_tb >= -22.0) & (signed_dist_tb <= -14.0) & (r_perp_tb <= r_tb + 0.75 * dx_mm)
    if not np.any(inlet_ref):
        inlet_ref = (signed_dist_tb >= -dx_mm * 3.5) & (signed_dist_tb < -dx_mm * 1.45) & (r_perp_tb <= r_tb + 0.75 * dx_mm)
    pre_spigot_masks = []
    for xc in cyl_xs:
        pm = (py >= tip_y + 22.0) & (py <= tip_y + 30.0) & (np.hypot(px - xc, pz - sp_z) <= r_sp_in + 0.75 * dx_mm)
        if not np.any(pm):
            pm = (py >= tip_y + dx_mm * 5.0) & (py <= tip_y + dx_mm * 7.5) & (np.hypot(px - xc, pz - sp_z) <= r_sp_in + 0.75 * dx_mm)
        pre_spigot_masks.append(pm)

    dh_ref = 0.052
    re_ref = RHO0 * max(u_in_mag, 15.0) * dh_ref / MU_AIR
    inv_sqrt_f = -1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_ref)) ** 1.11 + 6.9 / max(re_ref, 5000.0))
    f_darcy = 1.0 / (inv_sqrt_f**2)
    nu_eff = 0.0045
    alpha_u = 0.65
    alpha_p = 0.30

    r_all = np.arange(n_cells)
    q_in_div = q_vol_src
    max_cg_info = cg0_info
    max_cg_res = cg0_res
    max_bicg_info = 0
    max_bicg_res = 0.0
    mom_res_hist: list[float] = []
    face_cont_hist: list[float] = []
    dp_hist: list[float] = []
    spread_hist: list[float | None] = []
    converged = False
    n_outer_done = 0

    om_lookup = np.full(n_cells, -1, dtype=np.int32)
    om_lookup[om_idx] = np.arange(len(om_idx), dtype=np.int32)

    def _compute_flux_weighted_metrics(u_fld, v_fld, w_fld, p_fld, v_out_fld):
        spd_fld = np.sqrt(u_fld * u_fld + v_fld * v_fld + w_fld * w_fld)
        p0_fld = p_fld + 0.5 * RHO0 * (spd_fld**2)
        if np.any(inlet_ref):
            w_in = np.maximum(-(u_fld[inlet_ref] * tb_axis[0] + v_fld[inlet_ref] * tb_axis[1] + w_fld[inlet_ref] * tb_axis[2]), 0.0)
            w_sum = float(np.sum(w_in))
            p0_in_fw = float(np.sum(w_in * p0_fld[inlet_ref]) / w_sum) if w_sum > 1e-12 else float(np.mean(p0_fld[inlet_ref]))
        else:
            p0_in_fw = float(np.mean(p0_fld[inlet_cell]))

        c_flows, c_fwd, c_rev, c_dp = [], [], [], []
        for idx in range(n_outlets_total):
            c_id = idx + 1
            active_om = outlet_masks[idx] & all_outlet_mask
            if (c_id not in active_cyls) or (not np.any(active_om)):
                c_flows.append(0.0)
                c_fwd.append(0.0)
                c_rev.append(0.0)
                c_dp.append(0.0)
                continue
            loc = om_lookup[np.flatnonzero(active_om)]
            v_f = v_out_fld[loc]
            m_net = float(np.sum(RHO0 * v_f * face_area))
            m_fwd = float(np.sum(RHO0 * np.maximum(v_f, 0.0) * face_area))
            m_rev = float(np.sum(RHO0 * np.maximum(-v_f, 0.0) * face_area))
            c_flows.append(m_net)
            c_fwd.append(m_fwd)
            c_rev.append(m_rev)

            pm = pre_spigot_masks[idx]
            if np.any(pm):
                w_out = np.maximum(-v_fld[pm], 0.0)
                wo_sum = float(np.sum(w_out))
                p0_out_fw = float(np.sum(w_out * p0_fld[pm]) / wo_sum) if wo_sum > 1e-12 else float(np.mean(p0_fld[pm]))
            else:
                p0_out_fw = float(np.mean(p0_fld[np.flatnonzero(active_om)]))
            c_dp.append(p0_in_fw - p0_out_fw)

        active_dps = [c_dp[c_id - 1] for c_id in active_cyls]
        dp_mean_kpa = float(np.mean(active_dps)) * 1e-3 if active_dps else 0.0
        net_sum = sum(c_flows)
        if len(active_cyls) >= 2 and abs(net_sum) > 1e-9:
            shares = [100.0 * f / net_sum if (idx + 1) in active_cyls else None for idx, f in enumerate(c_flows)]
            act_sh = [s for s in shares if s is not None]
            spread = (max(act_sh) - min(act_sh)) / (100.0 / len(active_cyls)) * 100.0
        elif len(active_cyls) == 1 and abs(net_sum) > 1e-9:
            shares = [100.0 if (idx + 1) in active_cyls else 0.0 for idx in range(n_outlets_total)]
            spread = None
        else:
            shares = [None] * n_outlets_total
            spread = None
        return c_flows, c_fwd, c_rev, c_dp, dp_mean_kpa, shares, spread, p0_in_fw

    for it in range(n_picard):
        n_outer_done = it + 1
        speed = np.sqrt(u * u + v * v + w * w)
        wall_drag = (f_darcy / 8.0) * (wall_face_count / dx_m) * speed * wall_drag_mult
        outlet_drag = np.where(spigot_zone, 0.5 * (k_port_valve / 0.020) * speed, 0.0)

        m_rows, m_cols, m_vals = [], [], []
        # Conservative advection + outlet conv outflow balance: sum_f(conv_out - conv_in) + v_out/dx == q_in_div
        m_diag_steady = wall_drag + outlet_drag + 1e-8
        m_diag_steady[om_idx] += np.maximum(v_out_divfree, 0.0) / dx_m

        for (_ox, _oy, _oz, key, _ax, _sgn) in dirs:
            valid, nb = nbrs[key]
            r = np.flatnonzero(valid)
            c = nb[valid]
            flux = face_flux[key]
            conv_out = np.maximum(flux, 0.0) / dx_m
            conv_in = np.maximum(-flux, 0.0) / dx_m
            diff = nu_eff / (dx_m * dx_m)
            m_rows.append(r)
            m_cols.append(c)
            m_vals.append(-(conv_in + diff))
            np.add.at(m_diag_steady, r, conv_out + diff)

        M_steady = sp.csr_matrix(
            (np.concatenate([*m_vals, m_diag_steady]), (np.concatenate([*m_rows, r_all]), np.concatenate([*m_cols, r_all]))),
            shape=(n_cells, n_cells),
        )

        gpx, gpy, gpz = calc_cell_grad(p, outlet_dirichlet_zero=True)
        rhs_steady_u = q_in_div * u_in_vec[0] - (gpx / RHO0)
        rhs_steady_v = q_in_div * u_in_vec[1] - (gpy / RHO0)
        rhs_steady_w = q_in_div * u_in_vec[2] - (gpz / RHO0)

        mom_scale = max(float(np.linalg.norm(m_diag_steady * np.maximum(speed, u_in_mag * 0.25))), 1e-12)
        mom_res = max(
            float(np.linalg.norm(M_steady @ u - rhs_steady_u)),
            float(np.linalg.norm(M_steady @ v - rhs_steady_v)),
            float(np.linalg.norm(M_steady @ w - rhs_steady_w)),
        ) / mom_scale
        mom_res_hist.append(mom_res)

        # Patankar implicit under-relaxation
        a_p_rel = m_diag_steady / alpha_u
        extra_diag = ((1.0 - alpha_u) / alpha_u) * m_diag_steady
        M_vel = sp.csr_matrix(
            (np.concatenate([*m_vals, a_p_rel]), (np.concatenate([*m_rows, r_all]), np.concatenate([*m_cols, r_all]))),
            shape=(n_cells, n_cells),
        )
        d_p = 1.0 / a_p_rel

        u_star, b_info_u, b_res_u = _jacobi_bicgstab(M_vel, rhs_steady_u + extra_diag * u, tol=1e-6, maxiter=400, x0=u)
        v_star, b_info_v, b_res_v = _jacobi_bicgstab(M_vel, rhs_steady_v + extra_diag * v, tol=1e-6, maxiter=400, x0=v)
        w_star, b_info_w, b_res_w = _jacobi_bicgstab(M_vel, rhs_steady_w + extra_diag * w, tol=1e-6, maxiter=400, x0=w)
        max_bicg_info = max(max_bicg_info, abs(b_info_u), abs(b_info_v), abs(b_info_w))
        max_bicg_res = max(max_bicg_res, b_res_u, b_res_v, b_res_w)

        # Assemble SPD pressure-correction matrix L_p and Rhie-Chow face velocities
        lp_rows, lp_cols, lp_vals = [], [], []
        lp_diag = np.zeros(n_cells, dtype=np.float64)
        div_u = -q_in_div.copy()
        u_f_dict: dict[str, np.ndarray] = {}

        for (_ox, _oy, _oz, key, _ax, sgn), comp, gp_comp in zip(
            dirs, [u_star, u_star, v_star, v_star, w_star, w_star], [gpx, gpx, gpy, gpy, gpz, gpz]
        ):
            valid, nb = nbrs[key]
            r = np.flatnonzero(valid)
            c = nb[valid]
            d_f = 0.5 * (d_p[r] + d_p[c])
            cond = d_f * inv_dx2
            lp_rows.append(r)
            lp_cols.append(c)
            lp_vals.append(-cond)
            np.add.at(lp_diag, r, cond)

            rc_corr = -(d_f / RHO0) * ((p[c] - p[r]) / (sgn * dx_m) - 0.5 * (gp_comp[r] + gp_comp[c]))
            u_f = (0.5 * (comp[r] + comp[c]) + rc_corr) * sgn
            u_f_dict[key] = u_f
            np.add.at(div_u, r, u_f / dx_m)

        lp_diag[om_idx] += d_p[om_idx] * inv_dx2
        lp_rows.append(r_all)
        lp_cols.append(r_all)
        lp_vals.append(lp_diag)
        L_p = sp.csr_matrix(
            (np.concatenate(lp_vals), (np.concatenate(lp_rows), np.concatenate(lp_cols))),
            shape=(n_cells, n_cells),
        )

        rc_out = -(d_p[om_idx] / RHO0) * ((0.0 - p[om_idx]) / (-dx_m) - gpy[om_idx])
        v_out_face = -(v_star[om_idx] + rc_out)
        div_u[om_idx] += v_out_face / dx_m

        rhs_p = -RHO0 * div_u
        p_corr, cg_info, cg_res = _jacobi_cg(L_p, rhs_p, tol=1e-8, maxiter=3000)
        max_cg_info = max(max_cg_info, abs(cg_info))
        max_cg_res = max(max_cg_res, cg_res)

        # Update persistent strictly divergence-free signed face fluxes
        for (_ox, _oy, _oz, key, _ax, _sgn) in dirs:
            valid, nb = nbrs[key]
            r = np.flatnonzero(valid)
            c = nb[valid]
            d_f = 0.5 * (d_p[r] + d_p[c])
            face_flux[key] = u_f_dict[key] + (d_f / RHO0) * (p_corr[r] - p_corr[c]) / dx_m

        v_out_divfree = v_out_face + (d_p[om_idx] / RHO0) * (p_corr[om_idx] / dx_m)

        gpc_x, gpc_y, gpc_z = calc_cell_grad(p_corr, outlet_dirichlet_zero=True)
        u = u_star - (d_p / RHO0) * gpc_x
        v = v_star - (d_p / RHO0) * gpc_y
        w = w_star - (d_p / RHO0) * gpc_z
        p = p + alpha_p * p_corr

        # Track face continuity residual after correction
        div_check = -q_in_div.copy()
        for (_ox, _oy, _oz, key, _ax, _sgn) in dirs:
            valid, _ = nbrs[key]
            r = np.flatnonzero(valid)
            np.add.at(div_check, r, face_flux[key] / dx_m)
        div_check[om_idx] += v_out_divfree / dx_m
        face_cont_res = float(np.sum(np.abs(div_check)) * (dx_m**3) / q_target)
        face_cont_hist.append(face_cont_res)

        _, _, _, _, dp_kpa_it, _, spread_it, _ = _compute_flux_weighted_metrics(u, v, w, p, v_out_divfree)
        dp_hist.append(dp_kpa_it)
        spread_hist.append(spread_it)

        if it >= 24 and mom_res < tol_mom and cg_info == 0 and b_info_u == 0 and b_info_v == 0 and b_info_w == 0:
            rel_dp_chg = abs(dp_hist[-1] - dp_hist[-5]) / max(abs(dp_hist[-1]), 1e-6)
            if spread_it is None or spread_hist[-5] is None:
                spread_ok = True
            else:
                spread_ok = abs(spread_it - spread_hist[-5]) < 0.01
            if rel_dp_chg < 2e-4 and spread_ok:
                converged = True
                break

    speed = np.sqrt(u * u + v * v + w * w)
    mach = speed / A0_SOUND
    cyl_flows, cyl_fwd, cyl_rev, cyl_dp_pa, dp_manifold_mean_kpa, flow_shares_pct, maldist_pct, p0_in_fw = (
        _compute_flux_weighted_metrics(u, v, w, p, v_out_divfree)
    )
    raw_sum = sum(cyl_flows)
    mass_err_pct = abs(raw_sum - total_mass_flow_kgs) / total_mass_flow_kgs * 100.0

    # Check relaxed cell-velocity continuity metric too for transparent reporting
    div_vel_cell = -q_in_div.copy()
    for (_ox, _oy, _oz, key, _ax, sgn), comp in zip(dirs, [u, u, v, v, w, w]):
        valid, nb = nbrs[key]
        r = np.flatnonzero(valid)
        c = nb[valid]
        np.add.at(div_vel_cell, r, 0.5 * (comp[r] + comp[c]) * sgn / dx_m)
    div_vel_cell[om_idx] += v_out_divfree / dx_m
    cell_vel_cont_ratio = float(np.sum(np.abs(div_vel_cell)) * (dx_m**3) / q_target)

    # Mid-plane XY slice (near Z = -4 mm or domain mid-Z if duct)
    z_target = -4.0 if (zs_mm[0] < -10.0 and zs_mm[-1] > 10.0) else float(np.mean(zs_mm))
    z_slice_idx = int(np.argmin(np.abs(zs_mm - z_target)))
    grid_vx = np.full((nx, ny), np.nan)
    grid_vy = np.full((nx, ny), np.nan)
    grid_speed = np.full((nx, ny), np.nan)
    grid_p = np.full((nx, ny), np.nan)
    sl_mask = (kk == z_slice_idx)
    grid_vx[ii[sl_mask], jj[sl_mask]] = u[sl_mask]
    grid_vy[ii[sl_mask], jj[sl_mask]] = v[sl_mask]
    grid_speed[ii[sl_mask], jj[sl_mask]] = speed[sl_mask]
    grid_p[ii[sl_mask], jj[sl_mask]] = p[sl_mask] * 1e-3

    return {
        "status": "CONVERGED" if converged else "NOT_CONVERGED",
        "converged": bool(converged),
        "outer_iterations": int(n_outer_done),
        "n_fluid_cells": int(n_cells),
        "boundary_diagnostics": boundary_diag,
        "convergence": {
            "final_momentum_rel_res": round(mom_res_hist[-1], 7) if mom_res_hist else None,
            "final_face_continuity_rel": round(face_cont_hist[-1], 10) if face_cont_hist else None,
            "cell_vel_imbalance_ratio": round(cell_vel_cont_ratio, 5),
            "cg_max_info": int(max_cg_info),
            "cg_max_rel_res": round(max_cg_res, 9),
            "bicgstab_max_info": int(max_bicg_info),
            "bicgstab_max_rel_res": round(max_bicg_res, 9),
            "dp_history_tail_kpa": [round(float(x), 4) for x in dp_hist[-5:]],
            "spread_history_tail_pct": [round(float(x), 3) if x is not None else None for x in spread_hist[-5:]],
        },
        "reference_planes": {
            "inlet_section_dist_from_tb_face_mm": [-22.0, -14.0],
            "outlet_section_y_mm": [round(tip_y + 22.0, 2), round(tip_y + 30.0, 2)],
            "porous_zone_y_max_mm": round(tip_y + 20.0, 2) if k_port_valve > 0.0 else None,
            "inlet_flux_weighted_p0_rel_pa": round(p0_in_fw, 2),
        },
        "mass_conservation_error_pct": round(mass_err_pct, 6),
        "cyl_mass_flow_raw_kgs": [round(f, 6) for f in cyl_flows],
        "cyl_forward_flow_kgs": [round(f, 6) for f in cyl_fwd],
        "cyl_reverse_flow_kgs": [round(f, 6) for f in cyl_rev],
        "cyl_flow_share_pct": [round(s, 3) if s is not None else None for s in flow_shares_pct],
        "cyl_maldistribution_spread_pct": round(maldist_pct, 3) if maldist_pct is not None else None,
        "cyl_dp_total_kpa": [round(dp * 1e-3, 4) for dp in cyl_dp_pa],
        "tb_to_plenum_dp_kpa": round(dp_manifold_mean_kpa, 4),
        "tb_to_plenum_dp_psi": round(dp_manifold_mean_kpa * 0.145038, 4),
        "max_mach_3d": round(float(np.max(mach)), 3),
        "max_vel_3d_ms": round(float(np.max(speed)), 1),
        "mean_tb_vel_ms": round(float(u_in_mag), 2),
        "model_assumptions": (
            f"Steady incompressible screening FVM (rho={RHO0:.3f} kg/m^3, uniform nu_eff={nu_eff} m^2/s, "
            f"Colebrook wall drag mult={wall_drag_mult}, outlet porous valve K={k_port_valve}); "
            "flux-weighted total pressure planes outside source & porous zones."
        ),
        "slice_z_mm": round(float(zs_mm[z_slice_idx]), 1),
        "slice_vx": grid_vx,
        "slice_vy": grid_vy,
        "slice_speed": grid_speed,
        "slice_p_kpa": grid_p,
    }


# ---------------------------------------------------------------------------
# 3. 1D Compressible Dividing-Manifold + 720-deg Crank-Angle Pulsating Solver
# ---------------------------------------------------------------------------

def solve_1d_compressible_and_pulsating(
    params: dict,
    cad_audit: dict,
    rpm: float = DESIGN_RPM,
) -> dict:
    """
    Solve:
      (A) Coupled 1D Compressible Dividing-Flow Network (Idelchik T-junction + Fanno wall
          friction + taper ram recovery + CAD-measured solid shadow blockage + runner S-bend
          + series OEM lower manifold/intake valve curtain pumping impedance) at prescribed load.
      (B) 720-degree crank-angle unsteady pulsating cycle (1-3-4-2 firing order, 0.5-deg step x
          6 cycles) with independent runner port pressure/inertance ODE where resistance strictly
          opposes flow, plus documented physical & effective acoustic tuning frequencies.
    """
    pl = params["plenum"]
    tb = params["throttle_body"]
    rn = params["runners"]
    bm = rn["bellmouth"]

    wall_flush = bool(bm.get("wall_flush_bellmouth", False))
    cant_deg = float(tb["forward_cant_deg"])
    flare_mm = float(bm["flare_radial_mm"])
    scoop_angles = bm.get("axial_entry_angles_deg", [0.0, 0.0, 0.0, 0.0])

    a_tb = math.pi * 0.25 * (float(tb["bore_diameter_mm"]) * 1e-3) ** 2
    a_exit = float(cad_audit["runner_exit_area_mm2"]) * 1e-6
    a_throat = float(cad_audit["runner_throat_area_mm2"]) * 1e-6
    perim_exit_m = float(cad_audit["runner_exit_perimeter_mm"]) * 1e-3
    perim_throat_m = float(cad_audit["runner_throat_perimeter_mm"]) * 1e-3
    dh_exit = 4.0 * a_exit / perim_exit_m
    dh_throat = 4.0 * a_throat / perim_throat_m

    xs_cyl = np.array(rn["center_x_mm"], dtype=float)
    w0 = pl["inner_width_y_mm"] * 1e-3
    h0 = pl["inner_height_z_mm"] * 1e-3
    r0 = pl["inner_corner_radius_mm"] * 1e-3
    a_pl_full = w0 * h0 - (4.0 - math.pi) * (r0**2)
    perim_pl_full = 2.0 * (w0 - 2 * r0) + 2.0 * (h0 - 2 * r0) + 2.0 * math.pi * r0

    def plenum_area_at_x(x_mm: float) -> float:
        return a_pl_full * gen.plenum_area_scale(x_mm, params)

    def plenum_dh_at_x(x_mm: float) -> float:
        s = math.sqrt(gen.plenum_area_scale(x_mm, params))
        return 4.0 * plenum_area_at_x(x_mm) / (perim_pl_full * s)

    disp_m3 = ENGINE_DISP_L * 1e-3
    mdot_total_ref = RHO0 * disp_m3 * (rpm / 120.0) * VE_REF
    mdot_cyl_ref = mdot_total_ref / 4.0

    # Projected solid shadow blockage fraction beta[0..3] measured from 3D CAD
    beta_cyl = np.asarray(cad_audit["cyl_solid_shadow_pct"], dtype=float) / 100.0

    r_over_dh = (flare_mm * 1e-3) / dh_throat
    k_bell_base = max(0.025, 0.038 + 0.18 * math.exp(-r_over_dh / 0.07))
    if not wall_flush:
        k_bell_base += 0.065  # protruding sharp lip grazing separation overhead

    re_runner = RHO0 * (mdot_cyl_ref * 2.4 / (RHO0 * a_exit)) * dh_exit / MU_AIR
    f_run = 1.0 / (-1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_exit)) ** 1.11 + 6.9 / max(re_runner, 5000.0))) ** 2
    l_upper_m = 0.108
    l_lower_oem_m = 0.135
    l_physical_total_m = l_upper_m + l_lower_oem_m  # 0.243 m
    k_fric_run = f_run * (l_upper_m / dh_exit) * ((a_exit / (0.5 * (a_throat + a_exit))) ** 2)
    k_sbend = 0.065
    k_runner_base = k_bell_base * ((a_exit / a_throat) ** 2) + k_fric_run + k_sbend

    a_pl4 = plenum_area_at_x(pl["cyl4_end_x_mm"])
    ar_diff = a_tb / a_pl4
    k_diff_tb = 0.52 * ((1.0 - ar_diff) ** 2) + 0.015 * ((cant_deg / 10.0) ** 1.6)
    dp_tb_pa = 0.5 * RHO0 * ((mdot_total_ref / (RHO0 * a_tb)) ** 2) * k_diff_tb

    k_head_valve = 3.2 * ((a_exit / 884.1e-6) ** 2)

    mdot_c = np.full(4, mdot_cyl_ref, dtype=float)
    p_pl_nodes = np.full(4, P0_IN_PA - dp_tb_pa, dtype=float)
    p_pl_eff = np.full(4, P0_IN_PA - dp_tb_pa, dtype=float)
    dp_scoop = np.zeros(4, dtype=float)
    k_runner_tot = np.zeros(4, dtype=float)
    net_res_rel = 1.0

    for _ in range(45):
        m_seg = np.array([
            mdot_c[0],
            mdot_c[0] + mdot_c[1],
            mdot_c[0] + mdot_c[1] + mdot_c[2],
            np.sum(mdot_c),
        ])
        v_ax = np.array([
            1.45 * m_seg[i] / (RHO0 * plenum_area_at_x(xs_cyl[i]) * (1.0 - 0.8 * beta_cyl[i]))
            for i in range(4)
        ])
        v_pulse_seg = np.array([
            (2.4 * mdot_c[i]) / (RHO0 * plenum_area_at_x(xs_cyl[i]) * (1.0 - 0.8 * beta_cyl[i]))
            for i in range(4)
        ])

        v_tb = m_seg[3] / (RHO0 * a_tb)
        dp_tb = 0.5 * RHO0 * (v_tb**2) * k_diff_tb
        p_04 = P0_IN_PA - dp_tb
        q_pl4 = 0.5 * RHO0 * (v_ax[3] ** 2)
        p_pl_nodes[3] = p_04 - q_pl4

        pitch_m = rn["pitch_mm"] * 1e-3
        for j in (2, 1, 0):
            dh_mid = plenum_dh_at_x(0.5 * (xs_cyl[j + 1] + xs_cyl[j]))
            v_up = v_ax[j + 1]
            v_dn = v_ax[j]
            v_p_mid = 0.5 * (v_pulse_seg[j + 1] + v_pulse_seg[j])

            dp_ram = 0.5 * RHO0 * (v_up**2 - v_dn**2) * 0.72
            re_p = RHO0 * max(v_p_mid, 1.0) * dh_mid / MU_AIR
            f_p = 1.0 / (-1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_mid)) ** 1.11 + 6.9 / max(re_p, 5000.0))) ** 2
            dp_fric_pulse = f_p * (pitch_m / dh_mid) * 0.5 * RHO0 * (v_p_mid**2) * 1.45
            dp_taper_accel = 0.22 * 0.5 * RHO0 * max(v_pulse_seg[j] ** 2 - v_pulse_seg[j + 1] ** 2, 0.0)
            b_k = beta_cyl[j + 1]
            k_wake = 1.35 * ((b_k / max(1.0 - b_k, 0.25)) ** 2) if not wall_flush else 0.0
            dp_wake = k_wake * 0.5 * RHO0 * max(v_up**2, (0.65 * v_p_mid) ** 2)

            p_raw = p_pl_nodes[j + 1] + dp_ram - dp_fric_pulse - dp_taper_accel - dp_wake
            p_pl_nodes[j] = min(p_raw, p_04 - 0.12 * q_pl4)

        for i in range(4):
            v_exit_i = (mdot_c[i] * 2.4) / (RHO0 * a_exit)
            v_throat_i = v_exit_i * (a_exit / a_throat)
            vr = v_ax[i] / max(v_throat_i, 1.0)
            c_turn = 0.14 if wall_flush else 0.42
            ax_rad = math.radians(float(scoop_angles[i])) if (wall_flush and i < len(scoop_angles)) else 0.0
            k_turn_i = c_turn * (vr**2) * ((1.0 - math.sin(ax_rad)) ** 2)
            dp_scoop[i] = 0.55 * math.sin(ax_rad) * 0.5 * RHO0 * (v_ax[i] ** 2)
            p_pl_eff[i] = p_pl_nodes[i] + dp_scoop[i]

            k_jet_4 = 0.0
            if i == 3:
                k_jet_4 = 0.055 * max(0.0, (cant_deg - 4.0) / 6.0) ** 1.5

            k_runner_tot[i] = k_runner_base + (k_turn_i + k_jet_4) * ((a_exit / a_throat) ** 2)

        def branch_sum(p_cyl_back: float) -> np.ndarray:
            arr = np.zeros(4)
            for i in range(4):
                dp_i = max(p_pl_eff[i] - p_cyl_back, 10.0)
                k_series = k_runner_tot[i] + k_head_valve
                y_comp = max(1.0 - dp_i / (3.0 * GAMMA * p_pl_eff[i]), 0.85)
                cd_series = 1.0 / math.sqrt(k_series)
                arr[i] = cd_series * y_comp * (a_exit * 0.28) * math.sqrt(2.0 * RHO0 * dp_i)
            return arr

        hi = float(np.min(p_pl_eff)) - 15.0
        lo = P0_IN_PA - 75000.0
        while float(np.sum(branch_sum(lo))) < mdot_total_ref and lo > P0_IN_PA * 0.15:
            lo = max(P0_IN_PA * 0.15, lo - 40000.0)
        assert float(np.sum(branch_sum(lo))) >= mdot_total_ref >= float(np.sum(branch_sum(hi))), (
            f"1D network bisection failed to bracket {mdot_total_ref:.5f} kg/s at {rpm} RPM "
            f"(lo_sum={float(np.sum(branch_sum(lo))):.5f}, hi_sum={float(np.sum(branch_sum(hi))):.5f})"
        )
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if float(np.sum(branch_sum(mid))) > mdot_total_ref:
                lo = mid
            else:
                hi = mid
        mdot_new = branch_sum(0.5 * (lo + hi))
        net_res_rel = abs(float(np.sum(mdot_new)) - mdot_total_ref) / mdot_total_ref
        mdot_c = 0.5 * mdot_new + 0.5 * mdot_c

    assert net_res_rel < 1e-4, f"1D network failed to converge at {rpm} RPM (rel_res={net_res_rel:.6f})"

    mean_spigot_dp_pa = float(np.mean([
        k_runner_tot[i] * 0.5 * RHO0 * ((mdot_c[i] / (RHO0 * a_exit * 0.28)) ** 2) for i in range(4)
    ]))
    dp_upper_manifold_pa = dp_tb_pa + mean_spigot_dp_pa + max(0.0, float(np.mean(P0_IN_PA - dp_tb_pa - p_pl_nodes)))
    dp_upper_kpa = dp_upper_manifold_pa * 1e-3

    mean_m = float(np.mean(mdot_c))
    ve_cyl = [VE_REF * (m / mean_m) for m in mdot_c]
    ve_spread_pct = (max(ve_cyl) - min(ve_cyl)) / VE_REF * 100.0
    cd_runner_mean = float(np.mean(1.0 / np.sqrt(1.0 + k_runner_tot)))

    # (B) 720-deg Crank-Angle Unsteady Pulsating Simulation (0.5-deg steps x 6 cycles, 1-3-4-2)
    n_ca = 1440
    n_cycles = 6
    ca_deg = np.linspace(0.0, 720.0, n_ca, endpoint=False)
    omega = rpm * 2.0 * math.pi / 60.0
    d_theta = math.radians(720.0 / n_ca)
    dt = d_theta / omega

    r_crank = STROKE_M * 0.5
    lam = r_crank / ROD_M
    a_piston = math.pi * 0.25 * (BORE_M**2)

    intake_offsets = [0.0, 540.0, 180.0, 360.0]
    v_plenum = float(cad_audit["bare_plenum_volume_liters"]) * 1e-3
    a_valve_max = 0.00102

    a_eff_inertia = 0.5 * (a_throat + a_exit)
    l_eff_inertia = l_upper_m + l_lower_oem_m
    inertance = l_eff_inertia / a_eff_inertia
    v_port = a_eff_inertia * l_upper_m

    p_pl_inst = P0_IN_PA - 600.0
    m_run_inst = np.zeros(4, dtype=float)
    p_port_arr = np.full(4, P0_IN_PA - 600.0, dtype=float)
    p_cyl_arr = np.full(4, P0_IN_PA, dtype=float)

    p_pl_hist = np.zeros(n_ca)
    m_run_hist = np.zeros((n_ca, 4))
    prev_net_mass = None
    last_net_mass = None
    periodic_res_pct = 0.0

    def valve_area(theta_local: float) -> float:
        if theta_local <= 232.0:
            u = (theta_local + 12.0) / 244.0
        elif theta_local >= 708.0:
            u = (theta_local - 708.0) / 244.0
        else:
            return 0.0
        return a_valve_max * (math.sin(math.pi * max(0.0, min(1.0, u))) ** 1.35)

    def cyl_vol_dvol(theta_local: float) -> tuple[float, float]:
        th = math.radians(theta_local)
        cr = 10.2
        v_clear = (disp_m3 / 4.0) / (cr - 1.0)
        disp_x = r_crank * ((1.0 - math.cos(th)) + (1.0 / lam) * (1.0 - math.sqrt(1.0 - (lam * math.sin(th)) ** 2)))
        vol = v_clear + a_piston * disp_x
        d_x_dth = r_crank * (math.sin(th) + (lam * math.sin(th) * math.cos(th)) / math.sqrt(1.0 - (lam * math.sin(th)) ** 2))
        return vol, a_piston * d_x_dth * omega

    p_pl_bias_ref = p_pl_eff - float(np.mean(p_pl_eff))
    for cyc in range(n_cycles):
        cyc_valve_mass = np.zeros(4, dtype=float)
        for s_idx, th_g in enumerate(ca_deg):
            dp_tb_inst = P0_IN_PA - p_pl_inst
            sgn_tb = 1.0 if dp_tb_inst >= 0 else -1.0
            mdot_tb = sgn_tb * (0.94 * a_tb) * math.sqrt(2.0 * RHO0 * abs(dp_tb_inst))

            mdot_valves = np.zeros(4)
            mdot_runners = np.zeros(4)
            for c in range(4):
                th_loc = (th_g - intake_offsets[c]) % 720.0
                vol_c, dvol_c = cyl_vol_dvol(th_loc)
                av = valve_area(th_loc)

                p_pl_local = p_pl_inst + p_pl_bias_ref[c]
                c_drag_lin = 0.5 * k_runner_tot[c] * abs(m_run_inst[c]) / (RHO0 * a_exit**2)
                # Consistent runner momentum ODE: friction c_drag_lin*m_run strictly opposes flow
                m_run_inst[c] = (m_run_inst[c] + dt * (p_pl_local - p_port_arr[c]) / inertance) / (
                    1.0 + dt * c_drag_lin / inertance
                )
                mdot_runners[c] = m_run_inst[c]

                dp_v = p_port_arr[c] - p_cyl_arr[c]
                if av > 1e-7:
                    cd_v = 0.72
                    sgn_v = 1.0 if dp_v >= 0 else -1.0
                    mdot_valves[c] = sgn_v * cd_v * av * math.sqrt(2.0 * RHO0 * abs(dp_v))

                # Runner port capacitive update
                dp_port = (GAMMA * R_AIR * T0_IN_K / v_port) * (m_run_inst[c] - mdot_valves[c]) * dt
                p_port_arr[c] = max(0.35 * P_AMB_PA, min(1.5 * P0_IN_PA, p_port_arr[c] + dp_port))

                if (th_loc <= 250.0) or (th_loc >= 700.0):
                    dm_in = mdot_valves[c] * dt
                    dp_cyl = (GAMMA * R_AIR * T0_IN_K / vol_c) * dm_in - (GAMMA * p_cyl_arr[c] / vol_c) * dvol_c * dt
                    p_cyl_arr[c] = max(0.35 * P_AMB_PA, min(1.5 * P0_IN_PA, p_cyl_arr[c] + dp_cyl))
                else:
                    p_cyl_arr[c] = P0_IN_PA - 1200.0

                cyc_valve_mass[c] += mdot_valves[c] * dt

            dm_pl = mdot_tb - float(np.sum(mdot_runners))
            p_pl_inst += (GAMMA * R_AIR * T0_IN_K / v_plenum) * dm_pl * dt

            if cyc == n_cycles - 1:
                p_pl_hist[s_idx] = p_pl_inst
                m_run_hist[s_idx, :] = mdot_valves

        prev_net_mass = last_net_mass
        last_net_mass = cyc_valve_mass
        if prev_net_mass is not None:
            denom = max(float(np.mean(np.abs(last_net_mass))), 1e-9)
            periodic_res_pct = float(np.max(np.abs(last_net_mass - prev_net_mass))) / denom * 100.0

    mdot_peak_runner = float(np.max(m_run_hist))
    net_admitted_mass_cyl = np.sum(m_run_hist, axis=0) * dt
    rev_backflow_mass_cyl = np.sum(np.maximum(-m_run_hist, 0.0), axis=0) * dt
    ve_pulsating_raw = net_admitted_mass_cyl / (RHO0 * (disp_m3 / 4.0))
    ve_pulse_scaled = [VE_REF * float(v / np.mean(ve_pulsating_raw)) for v in ve_pulsating_raw]
    ve_pulse_spread_pct = (max(ve_pulse_scaled) - min(ve_pulse_scaled)) / VE_REF * 100.0
    v_peak_throat = mdot_peak_runner / (RHO0 * a_throat)
    v_peak_exit = mdot_peak_runner / (RHO0 * a_exit)
    mach_peak_throat = v_peak_throat / A0_SOUND
    mach_peak_exit = v_peak_exit / A0_SOUND
    plenum_ripple_kpa = float(np.max(p_pl_hist) - np.min(p_pl_hist)) * 1e-3

    # Unified physical + end-corrected effective acoustic runner length
    l_acoustic_eff_m = l_physical_total_m + 0.6 * dh_exit
    a_run_mean = 0.5 * (a_throat + a_exit)
    v_cyl_eff = v_plenum * 0.5 + 0.5 * (disp_m3 / 4.0)
    f_helmholtz_hz = (A0_SOUND / (2.0 * math.pi)) * math.sqrt(a_run_mean / (l_acoustic_eff_m * v_cyl_eff))
    rpm_helmholtz_3rd = f_helmholtz_hz * 120.0 / 3.0
    f_quarter_hz = A0_SOUND / (4.0 * l_acoustic_eff_m)
    rpm_pulse_optimal = f_quarter_hz * 120.0 / 4.0

    return {
        "rpm": rpm,
        "boost_psi": BOOST_PSI,
        "p0_in_kpa": round(P0_IN_PA * 1e-3, 2),
        "t0_in_c": round(T0_IN_K - 273.15, 1),
        "rho0_kgm3": round(RHO0, 3),
        "flow_mode": "prescribed_load_relative_distribution",
        "network_mass_residual_pct": round(net_res_rel * 100.0, 6),
        "total_mass_flow_kgs": round(mdot_total_ref, 4),
        "total_mass_flow_lbmin": round(mdot_total_ref * 132.277, 2),
        "cyl_mass_flow_kgs": [round(float(v), 5) for v in mdot_c],
        "cyl_ve": [round(float(v), 4) for v in ve_cyl],
        "ve_maldistribution_spread_pct": round(ve_spread_pct, 2),
        "cyl_net_admitted_mass_g": [round(float(m * 1000.0), 4) for m in net_admitted_mass_cyl],
        "cyl_reverse_backflow_mass_g": [round(float(m * 1000.0), 4) for m in rev_backflow_mass_cyl],
        "unscaled_net_admitted_mass_ratio": [round(float(v), 4) for v in ve_pulsating_raw],
        "cyl_ve_720ca_pulsating": [round(v, 4) for v in ve_pulse_scaled],
        "ve_maldistribution_720ca_pct": round(ve_pulse_spread_pct, 2),
        "periodic_state_residual_pct": round(periodic_res_pct, 4),
        "runner_discharge_coeff_cd": round(cd_runner_mean, 4),
        "k_runner_total": [round(float(k), 4) for k in k_runner_tot],
        "dp_total_kpa": round(dp_upper_kpa, 3),
        "dp_total_psi": round(dp_upper_kpa * 0.145038, 3),
        "dp_tb_diffuser_kpa": round(dp_tb_pa * 1e-3, 3),
        "plenum_static_pressure_kpa": [round(float(p * 1e-3), 3) for p in p_pl_nodes],
        "peak_runner_vel_throat_ms": round(v_peak_throat, 1),
        "peak_runner_vel_exit_ms": round(v_peak_exit, 1),
        "peak_mach_throat": round(mach_peak_throat, 3),
        "peak_mach_exit": round(mach_peak_exit, 3),
        "plenum_ripple_kpa": round(plenum_ripple_kpa, 2),
        "physical_runner_length_mm": round(l_physical_total_m * 1000.0, 1),
        "effective_acoustic_length_mm": round(l_acoustic_eff_m * 1000.0, 1),
        "helmholtz_freq_hz": round(f_helmholtz_hz, 1),
        "helmholtz_3rd_harmonic_rpm": round(rpm_helmholtz_3rd, 0),
        "quarter_wave_4th_harmonic_rpm": round(rpm_pulse_optimal, 0),
        "_ca_deg": ca_deg,
        "_p_pl_kpa": p_pl_hist * 1e-3,
        "_m_run_hist": m_run_hist,
    }


def evaluate_design(
    params: dict,
    label: str,
    dx_vox: float = 4.0,
    run_3d: bool = True,
    cross_check_stl_path: Path | None = None,
    grid_offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> dict:
    """Run complete CAD audit + 3D FVM Navier-Stokes + 1D Compressible/Pulsating verification."""
    t0 = time.perf_counter()
    fluid = extract_fluid_cavity(params)
    audit = audit_cad_flow_geometry(fluid, params, cross_check_stl_path=cross_check_stl_path)
    sim1d = solve_1d_compressible_and_pulsating(params, audit, rpm=DESIGN_RPM)

    res = {
        "label": label,
        "params_key": {
            "wall_flush_bellmouth": bool(params["runners"]["bellmouth"].get("wall_flush_bellmouth", False)),
            "spigot_wall_mm": params["runners"]["spigot"]["wall_thickness_mm"],
            "runner_entry_mm": params["runners"]["sweep"]["plenum_entry_diameter_mm"],
            "flare_radial_mm": params["runners"]["bellmouth"]["flare_radial_mm"],
            "axial_entry_angles_deg": params["runners"]["bellmouth"].get("axial_entry_angles_deg", [0.0, 0.0, 0.0, 0.0]),
            "plenum_size_mm": [params["plenum"]["inner_width_y_mm"], params["plenum"]["inner_height_z_mm"]],
            "taper_cyl1_area_ratio": params["plenum"]["taper_cyl1_area_ratio"],
            "forward_cant_deg": params["throttle_body"]["forward_cant_deg"],
        },
        "cad_audit": audit,
        "sim_1d_7000rpm": {k: v for k, v in sim1d.items() if not k.startswith("_")},
        "_sim1d_traces": sim1d,
        "_fluid": fluid,
    }

    if run_3d:
        grid = voxelize_fluid_solid(fluid["fluid_solid"], dx=dx_vox, grid_offset_mm=grid_offset_mm)
        ns3d = solve_3d_navier_stokes_fvm(
            grid, params, fluid, total_mass_flow_kgs=sim1d["total_mass_flow_kgs"], active_cyls=[1, 2, 3, 4], n_picard=320
        )
        res["cfd_3d"] = {k: v for k, v in ns3d.items() if not k.startswith("slice_")}
        res["_cfd_3d_slices"] = ns3d
        res["_grid"] = grid

    res["elapsed_s"] = round(time.perf_counter() - t0, 2)
    return res


def compute_3grid_gci(params: dict, fluid_meta: dict, total_mass_flow_kgs: float) -> dict:
    """
    Run a 3-grid refinement study (dx = 4.0, 3.0, 2.5 mm) plus a dx = 2.0 mm boundary/connectivity check,
    and compute Roache Grid Convergence Index (GCI) uncertainty on pressure drop and cylinder spread.
    """
    spacings = [4.0, 3.0, 2.5]
    runs = []
    for dx in spacings:
        t0 = time.perf_counter()
        g = voxelize_fluid_solid(fluid_meta["fluid_solid"], dx=dx)
        r = solve_3d_navier_stokes_fvm(g, params, fluid_meta, total_mass_flow_kgs=total_mass_flow_kgs, active_cyls=[1, 2, 3, 4], n_picard=320)
        assert r["converged"], f"3-grid GCI solve did not converge at dx={dx} mm"
        runs.append({
            "dx_mm": dx,
            "n_cells": r["n_fluid_cells"],
            "outer_iterations": r["outer_iterations"],
            "dp_kpa": r["tb_to_plenum_dp_kpa"],
            "dp_psi": r["tb_to_plenum_dp_psi"],
            "spread_pct": r["cyl_maldistribution_spread_pct"],
            "cyl_shares_pct": r["cyl_flow_share_pct"],
            "outlet_face_counts": r["boundary_diagnostics"]["outlet_face_counts_all"],
            "elapsed_s": round(time.perf_counter() - t0, 2),
        })

    def _roache_gci(f3: float, f2: float, f1: float) -> dict:
        # f3 = coarse (4.0), f2 = mid (3.0), f1 = fine (2.5)
        r21 = 3.0 / 2.5  # 1.20
        r32 = 4.0 / 3.0  # 1.3333
        eps21 = f2 - f1
        eps32 = f3 - f2
        if abs(eps21) < 1e-12:
            return {"observed_order": None, "richardson_extrap": round(f1, 4), "gci_fine_abs": 0.0, "monotonic": True}
        s = 1.0 if (eps32 / eps21) > 0 else -1.0
        p = 1.0
        if s > 0:
            for _ in range(30):
                rhs_arg = max(abs(eps32 / eps21), 1e-6)
                q_p = math.log(max((r21**p - s) / max(r32**p - s, 1e-6), 1e-6))
                p_new = abs(math.log(rhs_arg) + q_p) / math.log(r21)
                p = float(np.clip(0.5 * p + 0.5 * p_new, 0.5, 2.5))
            extrap = f1 + (f1 - f2) / (r21**p - 1.0)
            gci_fine = 1.25 * abs(f1 - f2) / (r21**p - 1.0)
            return {"observed_order": round(p, 2), "richardson_extrap": round(extrap, 4), "gci_fine_abs": round(gci_fine, 4), "monotonic": True}
        else:
            # Oscillatory convergence across grids: bound with half-spread * 3.0 safety
            amp = max(abs(f3 - f2), abs(f2 - f1), abs(f3 - f1))
            return {"observed_order": None, "richardson_extrap": round(f1, 4), "gci_fine_abs": round(1.5 * amp, 4), "monotonic": False}

    dp_gci = _roache_gci(runs[0]["dp_kpa"], runs[1]["dp_kpa"], runs[2]["dp_kpa"])
    sp_gci = _roache_gci(runs[0]["spread_pct"], runs[1]["spread_pct"], runs[2]["spread_pct"])

    # Fine-grid 2.0 mm boundary/phase check (verify 360+ outlet faces per runner and graph connectivity)
    fine_bnd = {}
    for label_k, off in [("aligned", (0.0, 0.0, 0.0)), ("half_shifted", (1.0, 1.0, 1.0))]:
        g2 = voxelize_fluid_solid(fluid_meta["fluid_solid"], dx=2.0, grid_offset_mm=off)
        # Run 0 outer iterations? We can inspect boundary_diagnostics via n_picard=0
        r2 = solve_3d_navier_stokes_fvm(g2, params, fluid_meta, total_mass_flow_kgs=total_mass_flow_kgs, active_cyls=[1, 2, 3, 4], n_picard=0)
        bd = r2["boundary_diagnostics"]
        assert len(bd["empty_active_outlets"]) == 0 and bd["disjoint_outlets"] and bd["inlet_to_outlet_connected"]
        fine_bnd[label_k] = {
            "n_cells": r2["n_fluid_cells"],
            "n_inlet_cells": bd["n_inlet_cells"],
            "outlet_face_counts": bd["outlet_face_counts_all"],
            "outlet_areas_mm2": bd["outlet_areas_mm2_all"],
        }

    return {
        "grids": runs,
        "dp_kpa_gci": dp_gci,
        "spread_pct_gci": sp_gci,
        "fine_2mm_boundary_validation": fine_bnd,
    }


def make_baseline_params(opt_params: dict) -> dict:
    base = copy.deepcopy(opt_params)
    base["runners"]["spigot"]["outer_width_mm"] = 48.0
    base["runners"]["spigot"]["outer_height_mm"] = 36.0
    base["runners"]["spigot"]["corner_radius_mm"] = 16.0
    base["runners"]["spigot"]["wall_thickness_mm"] = 5.0
    base["runners"]["spigot"]["land_length_mm"] = 28.0
    base["runners"]["spigot"]["retention_bead_height_mm"] = 1.5
    base["runners"]["spigot"]["retention_bead_width_mm"] = 5.5
    base["runners"]["spigot"]["retention_bead_offset_from_tip_mm"] = 4.0
    base["runners"]["sweep"]["plenum_entry_diameter_mm"] = 44.0
    base["runners"]["bellmouth"]["wall_flush_bellmouth"] = False
    base["runners"]["bellmouth"]["flare_radial_mm"] = 6.0
    base["runners"]["bellmouth"]["wall_thickness_mm"] = 4.5
    base["runners"]["bellmouth"]["axial_entry_angles_deg"] = [0.0, 0.0, 0.0, 0.0]
    base["plenum"]["inner_width_y_mm"] = 96.0
    base["plenum"]["inner_height_z_mm"] = 84.0
    base["plenum"]["inner_corner_radius_mm"] = 38.0
    base["plenum"]["taper_cyl1_area_ratio"] = 0.78
    base["plenum"].pop("split_x_area_ratio", None)
    base["throttle_body"]["forward_cant_deg"] = 10.0
    return base


def plot_verification_report(
    base_res: dict,
    opt_res: dict,
    sweep_taper: list[dict],
    rpm_sweep_opt: list[dict],
    out_path: Path,
    case_id: str = "",
):
    fig = plt.figure(figsize=(18, 12), facecolor="#f6f5f0")
    fig.suptitle(
        "2004 Focus SVT 2.0L Turbo (18 PSI Boost / 7,000 RPM) — Converged Flux-Carrying 3D FVM + 1D Airflow Verification",
        fontsize=14.5,
        fontweight="bold",
        y=0.975,
        color="#182028",
    )

    vmax_spd = max(
        48.0,
        float(np.nanpercentile(base_res["_cfd_3d_slices"]["slice_speed"], 98)),
        float(np.nanpercentile(opt_res["_cfd_3d_slices"]["slice_speed"], 98)),
    )

    tp_b = base_res["params_key"]["taper_cyl1_area_ratio"]
    cant_b = base_res["params_key"]["forward_cant_deg"]
    tp_o = opt_res["params_key"]["taper_cyl1_area_ratio"]
    fl_o = opt_res["params_key"]["flare_radial_mm"]
    cant_o = opt_res["params_key"]["forward_cant_deg"]

    for ax_idx, (res, title_tag) in enumerate(
        [
            (base_res, f"Baseline CAD (14mm Sleeves, 38x26mm, {tp_b:.2f} Taper, {cant_b:g}° TB)"),
            (opt_res, f'Stage-2 Max-Boost Compatible (Flush +{fl_o:g}mm, Ø42.8 (2" Round), {tp_o:.2f}->0.889 Taper, Scoop, {cant_o:g}° TB)'),
        ],
        start=1,
    ):
        ax = fig.add_subplot(3, 2, ax_idx)
        ax.set_facecolor("#e9e6de")
        g = res["_grid"]
        sl = res["_cfd_3d_slices"]
        spd = sl["slice_speed"].T
        vx = sl["slice_vx"].T
        vy = sl["slice_vy"].T
        xs, ys = g["xs_mm"], g["ys_mm"]
        half_dx = g["dx_mm"] * 0.5
        extent = [xs[0] - half_dx, xs[-1] + half_dx, ys[0] - half_dx, ys[-1] + half_dx]
        im = ax.imshow(spd, origin="lower", extent=extent, aspect="equal", cmap="inferno", vmin=0.0, vmax=vmax_spd)
        step = 3
        qx, qy = np.meshgrid(xs[::step], ys[::step])
        uvx = np.nan_to_num(vx[::step, ::step], nan=0.0)
        uvy = np.nan_to_num(vy[::step, ::step], nan=0.0)
        mag = np.hypot(uvx, uvy)
        ok = mag > 1.5
        ax.quiver(qx[ok], qy[ok], uvx[ok], uvy[ok], color="white", alpha=0.88, scale=420, width=0.0032, headwidth=3.5)
        cb = fig.colorbar(im, ax=ax, fraction=0.032, pad=0.02)
        cb.set_label("Velocity [m/s]", fontsize=8)
        ax.set_title(
            f"{title_tag}\n3D FVM Z={sl['slice_z_mm']} mm | ΔP={res['cfd_3d']['tb_to_plenum_dp_kpa']:.3f} kPa | Spread={res['cfd_3d']['cyl_maldistribution_spread_pct']:.2f}% ({res['cfd_3d']['outer_iterations']} iters)",
            fontsize=9.8,
            fontweight="bold",
        )
        ax.set_xlabel("X [mm] (Cyl 1..4 -> TB)", fontsize=8)
        ax.set_ylabel("Y [mm]", fontsize=8)
        ax.tick_params(labelsize=8)

    ax3 = fig.add_subplot(3, 2, 3)
    ax3.set_facecolor("#ffffff")
    xb = np.asarray(base_res["cad_audit"]["xs_mm"])
    ab_bare = np.asarray(base_res["cad_audit"]["area_bare_mm2"])
    ab_core = np.asarray(base_res["cad_audit"]["area_plenum_core_mm2"])
    ao_bare = np.asarray(opt_res["cad_audit"]["area_bare_mm2"])
    ao_core = np.asarray(opt_res["cad_audit"]["area_plenum_core_mm2"])
    m_in = (xb >= -162) & (xb <= 162)
    ax3.plot(xb[m_in], ab_bare[m_in], color="#b0b0b0", ls="--", lw=1.2, label=f"Baseline Bare Plenum Area ({tp_b:.2f})")
    ax3.plot(xb[m_in], ab_core[m_in], color="#c0392b", lw=2.2, label=f"Baseline Solid-Shadow Area (Peak {max(base_res['cad_audit']['cyl_solid_shadow_pct']):.1f}%)")
    ax3.plot(xb[m_in], ao_bare[m_in], color="#85c1e9", ls="--", lw=1.2, label=f"Stage-2 Bare Plenum Area ({tp_o:.2f}->0.889)")
    ax3.plot(xb[m_in], ao_core[m_in], color="#1a5276", lw=2.3, label=f"Stage-2 Unobstructed Area (Shadow {max(opt_res['cad_audit']['cyl_solid_shadow_pct']):.1f}%)")
    for idx, xc in enumerate([-138, -46, 46, 138], start=1):
        ax3.axvline(xc, color="#888888", lw=0.7, ls=":")
        ax3.text(xc, 7100, f"Cyl {idx}", ha="center", va="bottom", fontsize=8)
    ax3.set_ylim(3800, 7600)
    ax3.set_xlim(-168, 168)
    ax3.grid(True, ls=":", alpha=0.5)
    ax3.legend(fontsize=7.6, loc="lower right")
    ax3.set_title("Exact CAD Cross-Section Audit: Eliminating Protruding Sleeve Solid Shadow", fontsize=10, fontweight="bold")
    ax3.set_xlabel("Plenum X Position [mm]", fontsize=8)
    ax3.set_ylabel("Effective Axial Flow Area [mm²]", fontsize=8)

    ax4 = fig.add_subplot(3, 2, 4)
    ax4.set_facecolor("#ffffff")
    tapers = [s["taper"] for s in sweep_taper]
    spread_flush = [s["spread_flush_pct"] for s in sweep_taper]
    spread_prot = [s["spread_protruding_pct"] for s in sweep_taper]
    ax4.plot(tapers, spread_prot, "o--", color="#c0392b", lw=1.8, ms=5, label="Baseline (Protruding, Regenerated CAD)")
    ax4.plot(tapers, spread_flush, "s-", color="#117864", lw=2.3, ms=5.5, label="Stage-2 Flush (Regenerated CAD per Taper)")
    ax4.scatter([tp_b], [base_res["sim_1d_7000rpm"]["ve_maldistribution_spread_pct"]], color="#922b21", s=110, zorder=5, label=f"Baseline ({tp_b:.2f})")
    ax4.scatter([tp_o], [opt_res["sim_1d_7000rpm"]["ve_maldistribution_spread_pct"]], color="#0e6251", marker="*", s=180, zorder=6, label=f"Stage-2 Design ({tp_o:.2f})")
    ax4.axhspan(0, 1.5, color="#d4efdf", alpha=0.45, label="Target Boost Maldistribution (< 1.5%)")
    ax4.set_ylim(0.0, 2.25)
    ax4.grid(True, ls=":", alpha=0.5)
    ax4.legend(fontsize=7.5, loc="upper left", ncol=2)
    ax4.set_title("1D Prescribed-Load Flow Spread vs. Regenerated Plenum Taper (7,000 RPM @ 18 psi)", fontsize=9.8, fontweight="bold")
    ax4.set_xlabel("Plenum Cyl-1 / Cyl-4 Area Ratio (`taper_cyl1_area_ratio` < 0.889)", fontsize=8)
    ax4.set_ylabel("Max-to-Min Flow Spread [%]", fontsize=8)

    ax5 = fig.add_subplot(3, 2, 5)
    ax5.set_facecolor("#ffffff")
    cyls = np.arange(1, 5)
    w_bar = 0.19
    b_3d = base_res["cfd_3d"]["cyl_flow_share_pct"]
    b_1d = [25.0 * (v / VE_REF) for v in base_res["sim_1d_7000rpm"]["cyl_ve"]]
    o_3d = opt_res["cfd_3d"]["cyl_flow_share_pct"]
    o_1d = [25.0 * (v / VE_REF) for v in opt_res["sim_1d_7000rpm"]["cyl_ve"]]
    ax5.bar(cyls - 1.5 * w_bar, b_3d, width=w_bar, color="#e67e22", alpha=0.88, label=f"Baseline 3D FVM Share ({base_res['cfd_3d']['cyl_maldistribution_spread_pct']:.2f}%)")
    ax5.bar(cyls - 0.5 * w_bar, b_1d, width=w_bar, color="#c0392b", alpha=0.90, label=f"Baseline 1D Rel. Dist. ({base_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']:.2f}%)")
    ax5.bar(cyls + 0.5 * w_bar, o_3d, width=w_bar, color="#2980b9", alpha=0.90, label=f"Stage-2 3D FVM Share ({opt_res['cfd_3d']['cyl_maldistribution_spread_pct']:.2f}%)")
    ax5.bar(cyls + 1.5 * w_bar, o_1d, width=w_bar, color="#117864", alpha=0.92, label=f"Stage-2 1D Rel. Dist. ({opt_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']:.2f}%)")
    ax5.axhline(25.0, color="#333333", ls="--", lw=1.0)
    ax5.set_xticks(cyls)
    ax5.set_xticklabels([f"Cyl {i}" for i in cyls])
    ax5.set_ylim(23.8, 26.2)
    ax5.grid(True, axis="y", ls=":", alpha=0.5)
    ax5.legend(fontsize=7.5, loc="lower right")
    ax5.set_title("Per-Cylinder Flow Share: 3D FVM vs. 1D Prescribed-Load Distribution (Equal Share = 25%)", fontsize=9.8, fontweight="bold")
    ax5.set_ylabel("Cylinder Share of Total Airflow [%]", fontsize=8)

    ax6 = fig.add_subplot(3, 2, 6)
    ax6.set_facecolor("#ffffff")
    tr = opt_res["_sim1d_traces"]
    ca = tr["_ca_deg"]
    mr = tr["_m_run_hist"] * 1000.0
    colors = ["#1f618d", "#117864", "#d68910", "#b03a2e"]
    for i in range(4):
        ax6.plot(ca, mr[:, i], color=colors[i], lw=1.6, label=f"Cyl {i+1} Valve Flow [g/s]")
    ax6_r = ax6.twinx()
    ax6_r.plot(ca, tr["_p_pl_kpa"], color="#2c3e50", ls="--", lw=1.4, label="Plenum Pressure [kPa abs]")
    ax6.set_xlim(0, 720)
    ax6.set_xticks([0, 180, 360, 540, 720])
    ax6.grid(True, ls=":", alpha=0.5)
    lines1, labels1 = ax6.get_legend_handles_labels()
    lines2, labels2 = ax6_r.get_legend_handles_labels()
    ax6.legend(lines1 + lines2, labels1 + labels2, fontsize=7.5, loc="upper right")
    ax6.set_title(
        f"720° Lumped Cycle (1-3-4-2 @ 7,000 RPM, L_phys={opt_res['sim_1d_7000rpm']['physical_runner_length_mm']:.0f}mm): Peak M={opt_res['sim_1d_7000rpm']['peak_mach_throat']:.3f}, f_H={opt_res['sim_1d_7000rpm']['helmholtz_freq_hz']:.1f} Hz",
        fontsize=9.6,
        fontweight="bold",
    )
    ax6.set_xlabel("Crank Angle [deg]", fontsize=8)
    ax6.set_ylabel("Instantaneous Valve Mass Flow [g/s]", fontsize=8)
    ax6_r.set_ylabel("Plenum Pressure [kPa abs]", fontsize=8)

    if case_id:
        fig.text(
            0.5,
            0.006,
            f"Provenance case_id: {case_id} | Steady incompressible screening FVM + 1D/720-deg lumped audit",
            ha="center",
            fontsize=7.8,
            color="#444444",
        )
    plt.tight_layout(rect=[0, 0.02, 1, 0.945])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def _file_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    t_start = time.perf_counter()
    opt_params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    base_params = make_baseline_params(opt_params)
    stl_1pc = STL_DIR / "svt_intake_manifold_1piece_full.stl"

    print("1/5 Running converged 3D FVM + 1D Audit on BASELINE geometry...")
    base_res = evaluate_design(base_params, "baseline_protruding_14mm_078taper_10cant", dx_vox=4.0, run_3d=True)
    assert base_res["cfd_3d"]["converged"], f"Baseline 3D FVM failed: {base_res['cfd_3d']['status']}"
    print(
        f"    Done in {base_res['elapsed_s']}s ({base_res['cfd_3d']['outer_iterations']} iters) | "
        f"mass_err={base_res['cfd_3d']['mass_conservation_error_pct']}% | "
        f"3D dP={base_res['cfd_3d']['tb_to_plenum_dp_kpa']} kPa | 3D spread={base_res['cfd_3d']['cyl_maldistribution_spread_pct']}% | "
        f"1D spread={base_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']}%"
    )

    print("2/5 Running converged 3D FVM + 1D Audit on STAGE-2 MAX-BOOST geometry...")
    opt_res = evaluate_design(
        opt_params,
        "stage2_compat_flush_7flare_42p8round_060taper_0889split_scoop_7cant",
        dx_vox=4.0,
        run_3d=True,
        cross_check_stl_path=stl_1pc,
    )
    assert opt_res["cfd_3d"]["converged"], f"Stage-2 3D FVM failed: {opt_res['cfd_3d']['status']}"
    print(
        f"    Done in {opt_res['elapsed_s']}s ({opt_res['cfd_3d']['outer_iterations']} iters) | "
        f"mass_err={opt_res['cfd_3d']['mass_conservation_error_pct']}% | "
        f"3D dP={opt_res['cfd_3d']['tb_to_plenum_dp_kpa']} kPa | 3D spread={opt_res['cfd_3d']['cyl_maldistribution_spread_pct']}% | "
        f"1D spread={opt_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']}% | "
        f"STL overlap={opt_res['cad_audit']['stl_cavity_wall_overlap_cm3']} cm3"
    )

    print("3/5 Running 3-grid refinement study (4.0, 3.0, 2.5 mm GCI) + 2.0 mm boundary check...")
    gci_study = compute_3grid_gci(opt_params, opt_res["_fluid"], opt_res["sim_1d_7000rpm"]["total_mass_flow_kgs"])
    print(
        f"    GCI dP={gci_study['dp_kpa_gci']['richardson_extrap']} +/- {gci_study['dp_kpa_gci']['gci_fine_abs']} kPa | "
        f"Spread={gci_study['spread_pct_gci']['richardson_extrap']} +/- {gci_study['spread_pct_gci']['gci_fine_abs']}%"
    )

    print("4/5 Running regenerated-CAD monotonic taper & RPM curves...")
    sweep_taper = []
    for taper in [0.54, 0.58, 0.60, 0.64, 0.68, 0.72, 0.78, 0.84]:
        p_flush = copy.deepcopy(opt_params)
        p_flush["plenum"]["taper_cyl1_area_ratio"] = taper
        fl_f = extract_fluid_cavity(p_flush)
        aud_f = audit_cad_flow_geometry(fl_f, p_flush)
        s_f = solve_1d_compressible_and_pulsating(p_flush, aud_f, rpm=DESIGN_RPM)

        p_prot = copy.deepcopy(base_params)
        p_prot["plenum"]["taper_cyl1_area_ratio"] = taper
        fl_p = extract_fluid_cavity(p_prot)
        aud_p = audit_cad_flow_geometry(fl_p, p_prot)
        s_p = solve_1d_compressible_and_pulsating(p_prot, aud_p, rpm=DESIGN_RPM)

        sweep_taper.append({
            "taper": taper,
            "bare_plenum_l_flush": aud_f["bare_plenum_volume_liters"],
            "bare_plenum_l_prot": aud_p["bare_plenum_volume_liters"],
            "spread_flush_pct": s_f["ve_maldistribution_spread_pct"],
            "spread_protruding_pct": s_p["ve_maldistribution_spread_pct"],
            "dp_flush_kpa": s_f["dp_total_kpa"],
            "dp_protruding_kpa": s_p["dp_total_kpa"],
        })

    rpm_sweep = []
    for rpm in [3000, 4000, 5000, 6000, 6500, 7000, 7500]:
        s_r = solve_1d_compressible_and_pulsating(opt_params, opt_res["cad_audit"], rpm=float(rpm))
        rpm_sweep.append({k: v for k, v in s_r.items() if not k.startswith("_")})

    provenance = {
        "case_id": f"stage2_{(_file_sha256(PARAMS_PATH) or '')[:8]}_{(_file_sha256(stl_1pc) or '')[:8]}",
        "intake_manifold_parameters_sha256": _file_sha256(PARAMS_PATH),
        "generate_intake_manifold_sha256": _file_sha256(ROOT / "generate_intake_manifold.py"),
        "verify_airflow_sha256": _file_sha256(Path(__file__)),
        "manifest_sha256": _file_sha256(STL_DIR / "manifest.json"),
        "stl_1piece_full_sha256": _file_sha256(stl_1pc),
    }

    print("5/5 Saving verification JSON (with SHA-256 provenance) and multi-panel plot...")
    plot_verification_report(
        base_res, opt_res, sweep_taper, rpm_sweep, FITMENT_DIR / "03_airflow_verification.png",
        case_id=provenance["case_id"],
    )

    keep_audit = {
        "cyl_solid_shadow_pct",
        "cyl_peak_blockage_pct",
        "mean_stack_blockage_pct",
        "total_fluid_volume_liters",
        "bare_plenum_volume_liters",
        "tb_inlet_area_mm2",
        "runner_throat_area_mm2",
        "runner_throat_perimeter_mm",
        "runner_min_sweep_area_mm2",
        "runner_exit_area_mm2",
        "runner_exit_perimeter_mm",
        "runner_contraction_ratio",
        "plenum_to_runner_area_ratio_cyl4",
        "plenum_to_runner_area_ratio_cyl1",
        "runner_normal_sections",
        "stl_cavity_wall_overlap_cm3",
        "wot_cavity_scope",
    }
    summary = {
        "provenance": provenance,
        "operating_point": {
            "engine": "2004 Ford Focus SVT 2.02L Zetec-E Turbo (Pulsar G25-550)",
            "displacement_liters": round(ENGINE_DISP_L, 3),
            "boost_psig": BOOST_PSI,
            "p0_abs_kpa": round(P0_IN_PA * 1e-3, 2),
            "iat_c": round(T0_IN_K - 273.15, 1),
            "design_rpm": DESIGN_RPM,
        },
        "baseline": {
            "params": base_res["params_key"],
            "cad_audit": {k: v for k, v in base_res["cad_audit"].items() if k in keep_audit},
            "cfd_3d": base_res["cfd_3d"],
            "sim_1d_7000rpm": base_res["sim_1d_7000rpm"],
        },
        "boost_optimized": {
            "params": opt_res["params_key"],
            "cad_audit": {k: v for k, v in opt_res["cad_audit"].items() if k in keep_audit},
            "cfd_3d": opt_res["cfd_3d"],
            "sim_1d_7000rpm": opt_res["sim_1d_7000rpm"],
        },
        "grid_refinement_gci": gci_study,
        "taper_sweep": sweep_taper,
        "rpm_sweep_optimized": rpm_sweep,
        "total_runtime_s": round(time.perf_counter() - t_start, 2),
    }
    STL_DIR.mkdir(parents=True, exist_ok=True)
    (STL_DIR / "airflow_verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Completed airflow verification in {summary['total_runtime_s']}s.")


if __name__ == "__main__":
    main()
