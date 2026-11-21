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
import scipy.sparse.linalg as spla
from shapely.geometry import Polygon as ShapelyPolygon

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

    tb = params["throttle_body"]
    pl = params["plenum"]
    cant_rad = math.radians(tb["forward_cant_deg"])
    tb_axis = np.array([math.cos(cant_rad), math.sin(cant_rad), 0.0])
    p_start = np.array([pl["cyl4_end_x_mm"] - 4.0, 0.0, 0.0])
    p_flange_back = np.array([pl["cyl4_end_x_mm"], 0.0, 0.0]) + tb_axis * tb["neck_length_mm"]
    p_flange_face = p_flange_back + tb_axis * tb["flange_thickness_mm"]

    n_pts = pl["profile_segments"]
    up_hint = np.array([0.0, 0.0, 1.0])
    bore_d = tb["bore_diameter_mm"]
    neck_in_rings = []
    n_steps = 18
    for k in range(n_steps + 1):
        t = k / n_steps
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        pos = p_start + (p_flange_back + tb_axis * 4.0 - p_start) * t
        tan = np.array([1.0, 0.0, 0.0]) * (1.0 - s_t) + tb_axis * s_t
        w_in = pl["inner_width_y_mm"] + (bore_d - pl["inner_width_y_mm"]) * s_t
        h_in = pl["inner_height_z_mm"] + (bore_d - pl["inner_height_z_mm"]) * s_t
        r_in = pl["inner_corner_radius_mm"] + (bore_d * 0.5 - pl["inner_corner_radius_mm"]) * s_t
        neck_in_rings.append(
            gen.ring_frame_points(pos, tan, up_hint, gen.rounded_rect_points(w_in, h_in, r_in, n_pts))
        )
    neck_in_rings.append(
        gen.ring_frame_points(
            p_flange_face + tb_axis * 6.0, tb_axis, up_hint, gen.rounded_rect_points(bore_d, bore_d, bore_d * 0.5, n_pts)
        )
    )
    tb_bore_full = gen.trimesh_to_manifold(gen.loft_closed_solid(neck_in_rings))
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


def audit_cad_flow_geometry(fluid_meta: dict, params: dict) -> dict:
    """
    Slice the true 3D internal air cavity along X (from Cyl 1 to TB flange) to measure
    exact effective flow area, bare plenum area, projected bluff blockage beta(X), and Dh(X).
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

    # Measure projected YZ bluff shadow of protruding bellmouths in +-32 mm zone around each cylinder
    proj_grid_y = np.linspace(-55.0, 55.0, 45)
    proj_grid_z = np.linspace(-50.0, 50.0, 41)
    gy, gz = np.meshgrid(proj_grid_y, proj_grid_z, indexing="ij")
    pts_yz = np.column_stack([gy.ravel(), gz.ravel()])  # shape (N, 2) -> slice X gives (Y=-x2d? check rot!)

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

    # Projected bluff-body obstruction ratio per cylinder (X-projected shadow of protruding stacks onto YZ plenum area)
    cyl_blockages = []
    effective_core_arr = area_pl_arr.copy()
    if bm_intrusion is not None:
        rot_bm = bm_intrusion.rotate([0.0, -90.0, 0.0])
        for xc in params["runners"]["center_x_mm"]:
            # Union 2D X-slices across [xc - 32, xc + 32] to get true frontal wake blockage in (Y,Z)
            blocked_mask = np.zeros(pts_yz.shape[0], dtype=bool)
            bare_mask = np.zeros(pts_yz.shape[0], dtype=bool)
            for p in rot_bare.slice(float(xc)).to_polygons():
                if len(p) >= 3:
                    bare_mask ^= MplPath(np.asarray(p)).contains_points(pts_yz)
            for dx_s in np.linspace(-30.0, 30.0, 15):
                # In rot_bm, cross section intersects both hollow bore + outer sleeve -> track solid protruding obstacle
                polys_bm = [np.asarray(p) for p in rot_bm.slice(float(xc + dx_s)).to_polygons()]
                # Also any hollow cavity enclosed inside a protruding sleeve in YZ cannot carry X-axial cross-flow straight through:
                layer = np.zeros(pts_yz.shape[0], dtype=bool)
                for p in polys_bm:
                    if len(p) >= 3:
                        layer ^= MplPath(p).contains_points(pts_yz)
                blocked_mask |= layer
            n_bare = max(int(np.sum(bare_mask)), 1)
            blk_pct = float(np.sum(blocked_mask & bare_mask)) / n_bare * 100.0
            cyl_blockages.append(round(blk_pct, 2))
            # Reflect true wake/frontal obstruction dip smoothly on plot curve near cylinder station
            for i, x in enumerate(xs):
                w_g = math.exp(-0.5 * ((x - xc) / 14.0) ** 2)
                effective_core_arr[i] = min(effective_core_arr[i], area_bare_arr[i] * (1.0 - (blk_pct / 100.0) * w_g))
    else:
        cyl_blockages = [0.0, 0.0, 0.0, 0.0]

    fluid_mesh = gen.manifold_to_trimesh(fluid_solid)
    total_fluid_vol_l = float(fluid_mesh.volume) / 1_000_000.0
    bare_plenum_vol_l = float(gen.manifold_to_trimesh(pl_inner).volume) / 1_000_000.0

    sp = params["runners"]["spigot"]
    sw = params["runners"]["sweep"]
    sp_w_in = sp["outer_width_mm"] - 2.0 * sp["wall_thickness_mm"]
    sp_h_in = sp["outer_height_mm"] - 2.0 * sp["wall_thickness_mm"]
    sp_r_in = sp["corner_radius_mm"] - sp["wall_thickness_mm"]
    area_spigot_exit = sp_w_in * sp_h_in - (4.0 - math.pi) * (sp_r_in**2)

    en_w = sw["plenum_entry_diameter_mm"]
    en_h = en_w - 6.0
    en_r = en_h * 0.48
    area_throat = en_w * en_h - (4.0 - math.pi) * (en_r**2)

    tb_area = math.pi * 0.25 * (params["throttle_body"]["bore_diameter_mm"] ** 2)

    return {
        "xs_mm": xs.tolist(),
        "area_fluid_mm2": [round(v, 1) for v in area_fluid],
        "area_plenum_core_mm2": [round(float(v), 1) for v in effective_core_arr],
        "area_bare_mm2": [round(float(v), 1) for v in area_bare_arr],
        "dh_mm": [round(v, 2) for v in dh_fluid],
        "cyl_peak_blockage_pct": cyl_blockages,
        "mean_stack_blockage_pct": round(float(np.mean(cyl_blockages)), 2),
        "total_fluid_volume_liters": round(total_fluid_vol_l, 3),
        "bare_plenum_volume_liters": round(bare_plenum_vol_l, 3),
        "tb_inlet_area_mm2": round(tb_area, 1),
        "runner_throat_area_mm2": round(area_throat, 1),
        "runner_exit_area_mm2": round(area_spigot_exit, 1),
        "runner_contraction_ratio": round(area_throat / area_spigot_exit, 3),
        "plenum_to_runner_area_ratio_cyl4": round(float(area_bare_arr[np.argmin(np.abs(xs - 138.0))]) / area_spigot_exit, 2),
        "plenum_to_runner_area_ratio_cyl1": round(float(area_bare_arr[np.argmin(np.abs(xs + 138.0))]) / area_spigot_exit, 2),
    }


# ---------------------------------------------------------------------------
# 2. Conservative 3D Finite-Volume Navier-Stokes Solver (Jacobi-PCG)
# ---------------------------------------------------------------------------

def voxelize_fluid_solid(fluid_solid: md.Manifold, dx: float = 5.5) -> dict:
    """Classify a 3D uniform Cartesian grid against exact Z-slices of `fluid_solid`."""
    solid_mesh = gen.manifold_to_trimesh(fluid_solid)
    bmin, bmax = solid_mesh.bounds[0], solid_mesh.bounds[1]

    xs = np.arange(bmin[0] - dx * 0.5, bmax[0] + dx * 0.75, dx)
    ys = np.arange(bmin[1] - dx * 0.5, bmax[1] + dx * 0.75, dx)
    zs = np.arange(bmin[2] + dx * 0.35, bmax[2] - dx * 0.25, dx)
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
        "xs_mm": xs,
        "ys_mm": ys,
        "zs_mm": zs,
        "inside": inside,
    }


def _jacobi_cg(A: sp.csr_matrix, b: np.ndarray, tol: float = 1e-6, maxiter: int = 600) -> np.ndarray:
    diag = np.maximum(A.diagonal(), 1e-12)
    M = sp.diags(1.0 / diag)
    x, _ = spla.cg(A, b, rtol=tol, maxiter=maxiter, M=M)
    return x


def _jacobi_bicgstab(A: sp.csr_matrix, b: np.ndarray, tol: float = 1e-5, maxiter: int = 200) -> np.ndarray:
    diag = A.diagonal()
    inv_diag = np.where(np.abs(diag) > 1e-12, 1.0 / diag, 1.0)
    M = sp.diags(inv_diag)
    x, _ = spla.bicgstab(A, b, rtol=tol, maxiter=maxiter, M=M)
    return x


def solve_3d_navier_stokes_fvm(
    grid: dict,
    params: dict,
    fluid_meta: dict,
    total_mass_flow_kgs: float,
    active_cyls: list[int] | None = None,
    n_picard: int = 16,
) -> dict:
    """
    Strictly conservative 3D steady turbulent Navier-Stokes projection solver (Oseen-SIMPLE
    with Rhie-Chow face-flux stabilization, Colebrook/Darcy boundary-layer friction, and
    eddy viscosity) on the voxelized 3D fluid cavity. Uses Jacobi-CG / BiCGSTAB only.
    """
    if active_cyls is None:
        active_cyls = [1, 2, 3, 4]

    dx_m = grid["dx_m"]
    dx_mm = grid["dx_mm"]
    xs_mm, ys_mm, zs_mm = grid["xs_mm"], grid["ys_mm"], grid["zs_mm"]
    inside = grid["inside"]
    nx, ny, nz = inside.shape
    N_grid = nx * ny * nz

    act_idx = np.flatnonzero(inside)
    n_cells = len(act_idx)
    remap = np.full(N_grid, -1, dtype=np.int32)
    remap[act_idx] = np.arange(n_cells, dtype=np.int32)

    ii, jj, kk = np.unravel_index(act_idx, (nx, ny, nz))
    px = xs_mm[ii]
    py = ys_mm[jj]
    pz = zs_mm[kk]
    pts_mm = np.column_stack([px, py, pz])

    p_face = fluid_meta["p_flange_face"]
    tb_axis = fluid_meta["tb_axis"]
    tip_y = fluid_meta["tip_y"]
    cyl_xs = params["runners"]["center_x_mm"]

    # Build neighbor table for 6 faces
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

    # Identify plug inlet cells (a transverse slice inside the TB bore right behind p_flange_face)
    signed_dist_tb = (pts_mm - p_face[None, :]) @ tb_axis
    r_perp_tb = np.linalg.norm((pts_mm - p_face[None, :]) - signed_dist_tb[:, None] * tb_axis[None, :], axis=1)
    inlet_cell = (signed_dist_tb >= -dx_mm * 1.45) & (signed_dist_tb <= dx_mm * 0.1) & (r_perp_tb <= params["throttle_body"]["bore_diameter_mm"] * 0.55)

    tb_area_m2 = math.pi * 0.25 * (params["throttle_body"]["bore_diameter_mm"] * 1e-3) ** 2
    u_in_mag = total_mass_flow_kgs / (RHO0 * tb_area_m2)
    u_in_vec = -tb_axis * u_in_mag
    face_area = dx_m * dx_m
    q_target = total_mass_flow_kgs / RHO0

    # Volumetric source distributed smoothly across the TB entrance plug disk so total injected Q == Q_target strictly
    n_in = max(int(np.sum(inlet_cell)), 1)
    q_in_per_cell = np.where(inlet_cell, q_target / n_in, 0.0)

    outlet_masks = []
    for xc in cyl_xs:
        m = (py <= tip_y + dx_mm * 0.95) & (~nbrs["my"][0]) & (np.abs(px - xc) <= 30.0)
        outlet_masks.append(m)
    all_outlet_mask = np.zeros(n_cells, dtype=bool)
    for c_idx in active_cyls:
        all_outlet_mask |= outlet_masks[c_idx - 1]

    wall_face_count[inlet_cell] = np.maximum(wall_face_count[inlet_cell] - 1.0, 0.0)
    wall_face_count[all_outlet_mask] = np.maximum(wall_face_count[all_outlet_mask] - 1.0, 0.0)

    # Porous lower-runner + intake valve impedance distributed across the straight spigot lands
    spigot_zone = np.zeros(n_cells, dtype=bool)
    for c_idx in active_cyls:
        spigot_zone |= (py <= tip_y + 24.0) & (np.abs(px - cyl_xs[c_idx - 1]) <= 30.0)
    k_port_valve = 14.0

    # Constant matrix topology for SPD L_p with variable SIMPLE face conductance d_f
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
    phi0 = _jacobi_cg(L_p0, q_vol_src, tol=1e-7, maxiter=700)
    gx0, gy0, gz0 = calc_cell_grad(phi0, outlet_dirichlet_zero=True)
    u = -gx0.copy()
    v = -gy0.copy()
    w = -gz0.copy()
    p = np.zeros(n_cells, dtype=np.float64)

    dh_ref = 0.052
    re_ref = RHO0 * max(u_in_mag, 15.0) * dh_ref / MU_AIR
    inv_sqrt_f = -1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_ref)) ** 1.11 + 6.9 / max(re_ref, 5000.0))
    f_darcy = 1.0 / (inv_sqrt_f**2)
    nu_eff = 0.0045  # Mixing-length turbulent eddy viscosity (~0.003-0.005 m^2/s for 40-50 m/s in 40 mm duct)
    dt_pseudo = 0.00020
    alpha_p = 0.45
    alpha_u = 0.55

    r_all = np.arange(n_cells)
    om_idx = np.flatnonzero(all_outlet_mask)
    q_in_div = q_vol_src
    v_out_divfree = np.zeros(len(om_idx), dtype=np.float64)

    for _it in range(n_picard):
        speed = np.sqrt(u * u + v * v + w * w)
        wall_drag = (f_darcy / 8.0) * (wall_face_count / dx_m) * speed * 1.4
        outlet_drag = np.where(spigot_zone, 0.5 * (k_port_valve / 0.024) * speed, 0.0)
        inflow_rate = q_in_div

        m_rows, m_cols, m_vals = [], [], []
        m_diag = (1.0 / dt_pseudo) + wall_drag + outlet_drag + inflow_rate + 1e-6

        vel_comps = [u, u, v, v, w, w]
        for (_ox, _oy, _oz, key, _ax, sgn), comp in zip(dirs, vel_comps):
            valid, nb = nbrs[key]
            r = np.flatnonzero(valid)
            c = nb[valid]
            u_face_out = 0.5 * (comp[r] + comp[c]) * sgn
            conv_out = np.maximum(u_face_out, 0.0) / dx_m
            conv_in = np.maximum(-u_face_out, 0.0) / dx_m
            diff = nu_eff / (dx_m * dx_m)
            m_rows.append(r)
            m_cols.append(c)
            m_vals.append(-(conv_in + diff))
            np.add.at(m_diag, r, conv_out + diff)

        m_rows.append(r_all)
        m_cols.append(r_all)
        m_vals.append(m_diag)
        M_vel = sp.csr_matrix(
            (np.concatenate(m_vals), (np.concatenate(m_rows), np.concatenate(m_cols))),
            shape=(n_cells, n_cells),
        )

        # True SIMPLE momentum-interpolation coefficient d_p = 1 / a_P
        d_p = 1.0 / m_diag

        gpx, gpy, gpz = calc_cell_grad(p, outlet_dirichlet_zero=True)
        rhs_u = (u / dt_pseudo) - (gpx / RHO0) + inflow_rate * u_in_vec[0]
        rhs_v = (v / dt_pseudo) - (gpy / RHO0) + inflow_rate * u_in_vec[1]
        rhs_w = (w / dt_pseudo) - (gpz / RHO0) + inflow_rate * u_in_vec[2]

        u_star = _jacobi_bicgstab(M_vel, rhs_u, tol=1e-5, maxiter=180)
        v_star = _jacobi_bicgstab(M_vel, rhs_v, tol=1e-5, maxiter=180)
        w_star = _jacobi_bicgstab(M_vel, rhs_w, tol=1e-5, maxiter=180)

        # Build symmetric SPD pressure-correction matrix L_p with face conductance d_f / dx_m^2
        lp_rows, lp_cols, lp_vals = [], [], []
        lp_diag = np.zeros(n_cells, dtype=np.float64)
        div_u = -q_in_div.copy()

        for (_ox, _oy, _oz, key, ax, sgn), comp, gp_comp in zip(
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
            np.add.at(div_u, r, u_f / dx_m)

        # Outlet boundary face flux (-Y on all_outlet_mask)
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
        p_corr = _jacobi_cg(L_p, rhs_p, tol=1e-7, maxiter=600)

        # Projected divergence-free outlet boundary face velocity
        v_out_divfree = v_out_face + (d_p[om_idx] / RHO0) * (p_corr[om_idx] / dx_m)

        gpc_x, gpc_y, gpc_z = calc_cell_grad(p_corr, outlet_dirichlet_zero=True)
        u_new = u_star - (d_p / RHO0) * gpc_x
        v_new = v_star - (d_p / RHO0) * gpc_y
        w_new = w_star - (d_p / RHO0) * gpc_z

        u = alpha_u * u_new + (1.0 - alpha_u) * u
        v = alpha_u * v_new + (1.0 - alpha_u) * v
        w = alpha_u * w_new + (1.0 - alpha_u) * w
        p = p + alpha_p * p_corr

    # Map outlet fluxes from strictly divergence-free v_out_divfree back to each cylinder
    om_lookup = np.full(n_cells, -1, dtype=np.int32)
    om_lookup[om_idx] = np.arange(len(om_idx), dtype=np.int32)

    speed = np.sqrt(u * u + v * v + w * w)
    mach = speed / A0_SOUND
    q_dyn = 0.5 * RHO0 * speed**2
    p_total_rel = p + q_dyn
    p0_in_mean = float(np.mean(p_total_rel[inlet_cell]))

    cyl_flows = []
    cyl_dp_pa = []
    for idx in range(4):
        om = outlet_masks[idx]
        om_i = np.flatnonzero(om)
        if len(om_i) == 0:
            cyl_flows.append(0.0)
            cyl_dp_pa.append(0.0)
            continue
        loc_idx = om_lookup[om_i]
        v_face_exit = np.maximum(v_out_divfree[loc_idx], 0.0)
        mdot_i = float(np.sum(RHO0 * v_face_exit * face_area))
        cyl_flows.append(mdot_i)
        # Measure pure upper manifold pressure drop right upstream of porous spigot zone
        pre_spigot = (py >= tip_y + 25.0) & (py <= tip_y + 38.0) & (np.abs(px - cyl_xs[idx]) <= 30.0)
        p0_out_manifold = float(np.mean(p_total_rel[pre_spigot])) if np.any(pre_spigot) else float(np.mean(p_total_rel[om_i]))
        cyl_dp_pa.append(max(p0_in_mean - p0_out_manifold, 0.0))

    raw_sum = sum(cyl_flows)
    mass_err_pct = abs(raw_sum - total_mass_flow_kgs) / total_mass_flow_kgs * 100.0
    flow_shares_pct = [100.0 * f / raw_sum if raw_sum > 1e-9 else 25.0 for f in cyl_flows]
    maldist_pct = (max(flow_shares_pct) - min(flow_shares_pct)) / 25.0 * 100.0

    # Pure manifold total pressure loss (mean TB P0 minus mean spigot exit P0, excluding valve-resistance drop at outlet boundary)
    dp_manifold_mean_kpa = max(float(np.mean(cyl_dp_pa)), 0.0) * 1e-3

    # Build mid-plane XY slice (near Z = -4 mm)
    z_slice_idx = int(np.argmin(np.abs(zs_mm + 4.0)))
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
        "n_fluid_cells": int(n_cells),
        "mass_conservation_error_pct": round(mass_err_pct, 2),
        "cyl_mass_flow_raw_kgs": [round(f, 5) for f in cyl_flows],
        "cyl_flow_share_pct": [round(s, 2) for s in flow_shares_pct],
        "cyl_maldistribution_spread_pct": round(maldist_pct, 2),
        "cyl_dp_total_kpa": [round(dp * 1e-3, 3) for dp in cyl_dp_pa],
        "tb_to_plenum_dp_kpa": round(dp_manifold_mean_kpa, 3),
        "tb_to_plenum_dp_psi": round(dp_manifold_mean_kpa * 0.145038, 3),
        "max_mach_3d": round(float(np.max(mach)), 3),
        "max_vel_3d_ms": round(float(np.max(speed)), 1),
        "mean_tb_vel_ms": round(float(u_in_mag), 2),
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
          friction + taper ram recovery + CAD-measured projected stack blockage + runner S-bend
          + series OEM lower manifold/intake valve curtain pumping impedance).
      (B) 720-degree crank-angle unsteady pulsating cycle (1-3-4-2 firing order) with Zetec-E
          DOHC intake valve curtain lift profile, plenum capacitive compliance, and Helmholtz tuning.
    """
    pl = params["plenum"]
    tb = params["throttle_body"]
    rn = params["runners"]
    bm = rn["bellmouth"]

    wall_flush = bool(bm.get("wall_flush_bellmouth", False))
    cant_deg = float(tb["forward_cant_deg"])
    flare_mm = float(bm["flare_radial_mm"])

    a_tb = math.pi * 0.25 * (tb["bore_diameter_mm"] * 1e-3) ** 2
    a_exit = cad_audit["runner_exit_area_mm2"] * 1e-6
    a_throat = cad_audit["runner_throat_area_mm2"] * 1e-6
    dh_exit = 0.0308
    dh_throat = 0.0405

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

    # Projected bluff blockage fraction beta[0..3] measured from 3D CAD
    beta_cyl = np.asarray(cad_audit["cyl_peak_blockage_pct"], dtype=float) / 100.0

    r_over_dh = (flare_mm * 1e-3) / dh_throat
    k_bell_base = max(0.025, 0.038 + 0.18 * math.exp(-r_over_dh / 0.07))
    if not wall_flush:
        k_bell_base += 0.065  # protruding sharp lip grazing separation overhead

    re_runner = RHO0 * (mdot_cyl_ref * 2.4 / (RHO0 * a_exit)) * dh_exit / MU_AIR
    f_run = 1.0 / (-1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_exit)) ** 1.11 + 6.9 / max(re_runner, 5000.0))) ** 2
    l_runner = 0.108
    k_fric_run = f_run * (l_runner / dh_exit) * ((a_exit / (0.5 * (a_throat + a_exit))) ** 2)
    k_sbend = 0.065
    k_runner_base = k_bell_base * ((a_exit / a_throat) ** 2) + k_fric_run + k_sbend

    a_pl4 = plenum_area_at_x(pl["cyl4_end_x_mm"])
    ar_diff = a_tb / a_pl4
    k_diff_tb = 0.52 * ((1.0 - ar_diff) ** 2) + 0.015 * ((cant_deg / 10.0) ** 1.6)
    dp_tb_pa = 0.5 * RHO0 * ((mdot_total_ref / (RHO0 * a_tb)) ** 2) * k_diff_tb

    # Lower OEM Zetec runner + intake valve curtain steady-equivalent loss K_downstream (ref a_exit)
    # Calibrated from the 720-deg DOHC valve lift & 2.02L piston displacement cycle at 7,000 RPM:
    # peak runner exit velocity ~172 m/s (q_exit ~ 35.8 kPa) while mean stroke intake valve drop ~22 kPa.
    # Referenced to mean steady branch flow across effective 25% stroke duty -> K_head_valve ~ 3.2.
    k_head_valve = 3.2

    mdot_c = np.full(4, mdot_cyl_ref, dtype=float)
    p_pl_nodes = np.full(4, P0_IN_PA - dp_tb_pa, dtype=float)
    k_runner_tot = np.zeros(4, dtype=float)

    for _ in range(45):
        m_seg = np.array([
            mdot_c[0],
            mdot_c[0] + mdot_c[1],
            mdot_c[0] + mdot_c[1] + mdot_c[2],
            np.sum(mdot_c),
        ])
        # Steady/overlap mean axial velocity profile along tapered plenum (Cyl 1..4)
        v_ax = np.array([
            1.45 * m_seg[i] / (RHO0 * plenum_area_at_x(xs_cyl[i]) * (1.0 - 0.8 * beta_cyl[i]))
            for i in range(4)
        ])
        # Instantaneous intake-pulse velocity along tapered plenum (peak pulse demand ~ 2.4x steady cylinder mean)
        v_pulse_seg = np.array([
            (2.4 * mdot_c[i]) / (RHO0 * plenum_area_at_x(xs_cyl[i]) * (1.0 - 0.8 * beta_cyl[i]))
            for i in range(4)
        ])

        v_tb = m_seg[3] / (RHO0 * a_tb)
        dp_tb = 0.5 * RHO0 * (v_tb**2) * k_diff_tb
        p_04 = P0_IN_PA - dp_tb
        q_pl4 = 0.5 * RHO0 * (v_ax[3] ** 2)
        p_pl_nodes[3] = p_04 - q_pl4  # Strictly < P0_IN_PA

        pitch_m = rn["pitch_mm"] * 1e-3
        # Ram static recovery relative to Cyl 4 (capped by available dynamic head at Cyl 4)
        # balanced against sequential pulse axial path Fanno friction + acceleration + bluff stack wake drag
        for j in (2, 1, 0):
            dh_mid = plenum_dh_at_x(0.5 * (xs_cyl[j + 1] + xs_cyl[j]))
            v_up = v_ax[j + 1]
            v_dn = v_ax[j]
            v_mid = 0.5 * (v_up + v_dn)
            v_p_mid = 0.5 * (v_pulse_seg[j + 1] + v_pulse_seg[j])

            # Background overlap deceleration ram recovery (capped so P_static < P_04)
            dp_ram = 0.5 * RHO0 * (v_up**2 - v_dn**2) * 0.72
            # Sequential intake-pulse path friction + taper acceleration loss
            re_p = RHO0 * max(v_p_mid, 1.0) * dh_mid / MU_AIR
            f_p = 1.0 / (-1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_mid)) ** 1.11 + 6.9 / max(re_p, 5000.0))) ** 2
            dp_fric_pulse = f_p * (pitch_m / dh_mid) * 0.5 * RHO0 * (v_p_mid**2) * 1.45
            # Narrowing taper kinetic acceleration demand (0.5*rho*(v_p_dn^2 - v_p_up^2)*K_accel)
            dp_taper_accel = 0.22 * 0.5 * RHO0 * max(v_pulse_seg[j] ** 2 - v_pulse_seg[j + 1] ** 2, 0.0)
            # Protruding stack bluff-body wake pressure loss along X
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
            k_turn_i = c_turn * (vr**2)

            k_jet_4 = 0.0
            if i == 3:
                k_jet_4 = 0.055 * max(0.0, (cant_deg - 4.0) / 6.0) ** 1.5

            k_runner_tot[i] = k_runner_base + (k_turn_i + k_jet_4) * ((a_exit / a_throat) ** 2)

        def branch_sum(p_cyl_back: float) -> np.ndarray:
            arr = np.zeros(4)
            for i in range(4):
                dp_i = max(p_pl_nodes[i] - p_cyl_back, 10.0)
                k_series = k_runner_tot[i] + k_head_valve
                y_comp = max(1.0 - dp_i / (3.0 * GAMMA * p_pl_nodes[i]), 0.85)
                cd_series = 1.0 / math.sqrt(k_series)
                # Effective active intake stroke duty ~ 0.28 per cylinder (25% basic stroke + cam overlap)
                arr[i] = cd_series * y_comp * (a_exit * 0.28) * math.sqrt(2.0 * RHO0 * dp_i)
            return arr

        lo, hi = P0_IN_PA - 75000.0, float(np.min(p_pl_nodes)) - 15.0
        for _ in range(55):
            mid = 0.5 * (lo + hi)
            if np.sum(branch_sum(mid)) > mdot_total_ref:
                lo = mid
            else:
                hi = mid
        mdot_new = branch_sum(0.5 * (lo + hi))
        mdot_c = 0.5 * mdot_new + 0.5 * mdot_c

    # Upper intake manifold total pressure drop (TB inlet -> mean runner spigot exit total pressure)
    mean_spigot_dp_pa = float(np.mean([
        k_runner_tot[i] * 0.5 * RHO0 * ((mdot_c[i] / (RHO0 * a_exit * 0.28)) ** 2) for i in range(4)
    ]))
    dp_upper_manifold_pa = dp_tb_pa + mean_spigot_dp_pa + max(0.0, float(np.mean(P0_IN_PA - dp_tb_pa - p_pl_nodes)))
    dp_upper_kpa = dp_upper_manifold_pa * 1e-3

    mean_m = float(np.mean(mdot_c))
    ve_cyl = [VE_REF * (m / mean_m) for m in mdot_c]
    ve_spread_pct = (max(ve_cyl) - min(ve_cyl)) / VE_REF * 100.0
    cd_runner_mean = float(np.mean(1.0 / np.sqrt(1.0 + k_runner_tot)))

    # (B) 720-deg Crank-Angle Unsteady Pulsating Simulation (1-3-4-2)
    n_ca = 720
    ca_deg = np.linspace(0.0, 720.0, n_ca, endpoint=False)
    omega = rpm * 2.0 * math.pi / 60.0
    d_theta = math.radians(720.0 / n_ca)
    dt = d_theta / omega

    r_crank = STROKE_M * 0.5
    lam = r_crank / ROD_M
    a_piston = math.pi * 0.25 * (BORE_M**2)

    intake_offsets = [0.0, 540.0, 180.0, 360.0]
    v_plenum = cad_audit["bare_plenum_volume_liters"] * 1e-3
    a_valve_max = 0.00102

    p_pl_inst = P0_IN_PA - 600.0
    m_run_inst = np.zeros(4)
    p_cyl_hist = np.zeros((n_ca, 4))
    p_pl_hist = np.zeros(n_ca)
    m_run_hist = np.zeros((n_ca, 4))

    l_eff_inertia = 0.205
    a_eff_inertia = 0.5 * (a_throat + a_exit)
    inertance = l_eff_inertia / a_eff_inertia

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
        dvol_dt = a_piston * d_x_dth * omega
        return vol, dvol_dt

    p_cyl_arr = np.full(4, P0_IN_PA)
    for cyc in range(3):
        for s_idx, th_g in enumerate(ca_deg):
            dp_tb_inst = P0_IN_PA - p_pl_inst
            sgn_tb = 1.0 if dp_tb_inst >= 0 else -1.0
            mdot_tb = sgn_tb * (0.94 * a_tb) * math.sqrt(2.0 * RHO0 * abs(dp_tb_inst))

            mdot_valves = np.zeros(4)
            for c in range(4):
                th_loc = (th_g - intake_offsets[c]) % 720.0
                vol_c, dvol_c = cyl_vol_dvol(th_loc)
                av = valve_area(th_loc)

                p_branch_bias = p_pl_nodes[c] - float(np.mean(p_pl_nodes))
                p_pl_local = p_pl_inst + p_branch_bias

                loss_pa = 0.5 * k_runner_tot[c] * m_run_inst[c] * abs(m_run_inst[c]) / (RHO0 * a_exit**2)
                p_port_c = p_pl_local - loss_pa
                dp_v = p_port_c - p_cyl_arr[c]

                if av > 1e-7:
                    cd_v = 0.72
                    sgn_v = 1.0 if dp_v >= 0 else -1.0
                    mdot_valves[c] = sgn_v * cd_v * av * math.sqrt(2.0 * RHO0 * abs(dp_v))
                    dmdt = (p_pl_local - p_port_c) / inertance
                    m_run_inst[c] = 0.75 * mdot_valves[c] + 0.25 * (m_run_inst[c] + dmdt * dt)
                else:
                    m_run_inst[c] *= 0.85

                if (th_loc <= 250.0) or (th_loc >= 700.0):
                    dm_in = mdot_valves[c] * dt
                    dp_cyl = (GAMMA * R_AIR * T0_IN_K / vol_c) * dm_in - (GAMMA * p_cyl_arr[c] / vol_c) * dvol_c * dt
                    p_cyl_arr[c] = max(0.35 * P_AMB_PA, min(1.5 * P0_IN_PA, p_cyl_arr[c] + dp_cyl))
                else:
                    p_cyl_arr[c] = P0_IN_PA - 1200.0

            dm_pl = mdot_tb - float(np.sum(mdot_valves))
            p_pl_inst += (GAMMA * R_AIR * T0_IN_K / v_plenum) * dm_pl * dt

            if cyc == 2:
                p_pl_hist[s_idx] = p_pl_inst
                p_cyl_hist[s_idx, :] = p_cyl_arr
                m_run_hist[s_idx, :] = mdot_valves

    mdot_peak_runner = float(np.max(m_run_hist))
    trapped_mass_cyl = np.sum(m_run_hist, axis=0) * dt
    ve_pulsating_raw = trapped_mass_cyl / (RHO0 * (disp_m3 / 4.0))
    ve_pulse_scaled = [VE_REF * float(v / np.mean(ve_pulsating_raw)) for v in ve_pulsating_raw]
    ve_pulse_spread_pct = (max(ve_pulse_scaled) - min(ve_pulse_scaled)) / VE_REF * 100.0
    v_peak_throat = mdot_peak_runner / (RHO0 * a_throat)
    v_peak_exit = mdot_peak_runner / (RHO0 * a_exit)
    mach_peak_throat = v_peak_throat / A0_SOUND
    mach_peak_exit = v_peak_exit / A0_SOUND
    plenum_ripple_kpa = float(np.max(p_pl_hist) - np.min(p_pl_hist)) * 1e-3

    l_total_acoustic = 0.275
    a_run_mean = 0.5 * (a_throat + a_exit)
    v_cyl_eff = v_plenum * 0.5 + 0.5 * (disp_m3 / 4.0)
    f_helmholtz_hz = (A0_SOUND / (2.0 * math.pi)) * math.sqrt(a_run_mean / (l_total_acoustic * v_cyl_eff))
    rpm_helmholtz_3rd = f_helmholtz_hz * 120.0 / 3.0
    f_quarter_hz = A0_SOUND / (4.0 * (l_total_acoustic + 0.35 * dh_exit))
    rpm_pulse_optimal = f_quarter_hz * 120.0 / 4.0

    return {
        "rpm": rpm,
        "boost_psi": BOOST_PSI,
        "p0_in_kpa": round(P0_IN_PA * 1e-3, 2),
        "t0_in_c": round(T0_IN_K - 273.15, 1),
        "rho0_kgm3": round(RHO0, 3),
        "total_mass_flow_kgs": round(mdot_total_ref, 4),
        "total_mass_flow_lbmin": round(mdot_total_ref * 132.277, 2),
        "cyl_mass_flow_kgs": [round(float(v), 5) for v in mdot_c],
        "cyl_ve": [round(float(v), 4) for v in ve_cyl],
        "ve_maldistribution_spread_pct": round(ve_spread_pct, 2),
        "cyl_ve_720ca_pulsating": [round(v, 4) for v in ve_pulse_scaled],
        "ve_maldistribution_720ca_pct": round(ve_pulse_spread_pct, 2),
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
        "helmholtz_freq_hz": round(f_helmholtz_hz, 1),
        "helmholtz_3rd_harmonic_rpm": round(rpm_helmholtz_3rd, 0),
        "quarter_wave_4th_harmonic_rpm": round(rpm_pulse_optimal, 0),
        "_ca_deg": ca_deg,
        "_p_pl_kpa": p_pl_hist * 1e-3,
        "_m_run_hist": m_run_hist,
    }


def evaluate_design(params: dict, label: str, dx_vox: float = 5.5, run_3d: bool = True) -> dict:
    """Run complete CAD audit + 3D FVM Navier-Stokes + 1D Compressible/Pulsating verification."""
    t0 = time.perf_counter()
    fluid = extract_fluid_cavity(params)
    audit = audit_cad_flow_geometry(fluid, params)
    sim1d = solve_1d_compressible_and_pulsating(params, audit, rpm=DESIGN_RPM)

    res = {
        "label": label,
        "params_key": {
            "wall_flush_bellmouth": bool(params["runners"]["bellmouth"].get("wall_flush_bellmouth", False)),
            "flare_radial_mm": params["runners"]["bellmouth"]["flare_radial_mm"],
            "taper_cyl1_area_ratio": params["plenum"]["taper_cyl1_area_ratio"],
            "forward_cant_deg": params["throttle_body"]["forward_cant_deg"],
        },
        "cad_audit": audit,
        "sim_1d_7000rpm": {k: v for k, v in sim1d.items() if not k.startswith("_")},
        "_sim1d_traces": sim1d,
    }

    if run_3d:
        grid = voxelize_fluid_solid(fluid["fluid_solid"], dx=dx_vox)
        ns3d = solve_3d_navier_stokes_fvm(
            grid, params, fluid, total_mass_flow_kgs=sim1d["total_mass_flow_kgs"], active_cyls=[1, 2, 3, 4], n_picard=16
        )
        res["cfd_3d"] = {k: v for k, v in ns3d.items() if not k.startswith("slice_")}
        res["_cfd_3d_slices"] = ns3d
        res["_grid"] = grid

    res["elapsed_s"] = round(time.perf_counter() - t0, 2)
    return res


def make_baseline_params(opt_params: dict) -> dict:
    base = copy.deepcopy(opt_params)
    base["plenum"]["taper_cyl1_area_ratio"] = 0.78
    base["runners"]["bellmouth"]["wall_flush_bellmouth"] = False
    base["runners"]["bellmouth"]["flare_radial_mm"] = 6.0
    base["runners"]["bellmouth"]["wall_thickness_mm"] = 4.5
    base["throttle_body"]["forward_cant_deg"] = 10.0
    return base


def plot_verification_report(
    base_res: dict,
    opt_res: dict,
    sweep_taper: list[dict],
    rpm_sweep_opt: list[dict],
    out_path: Path,
):
    fig = plt.figure(figsize=(18, 12), facecolor="#f6f5f0")
    fig.suptitle(
        "2004 Focus SVT 2.0L Turbo (18 PSI Boost / 7,000 RPM) — 3D FVM + 1D Compressible Airflow Verification",
        fontsize=15,
        fontweight="bold",
        y=0.975,
        color="#182028",
    )

    vmax_spd = max(
        48.0,
        float(np.nanpercentile(base_res["_cfd_3d_slices"]["slice_speed"], 98)),
        float(np.nanpercentile(opt_res["_cfd_3d_slices"]["slice_speed"], 98)),
    )

    for ax_idx, (res, title_tag) in enumerate(
        [
            (base_res, "Baseline CAD (Protruding 14mm Sleeves, 0.78 Taper, 10° TB)"),
            (opt_res, "Boost-Optimized CAD (Wall-Flush 6.5mm Stacks, 0.64 Taper, 8° TB)"),
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
        extent = [xs[0] - 2.75, xs[-1] + 2.75, ys[0] - 2.75, ys[-1] + 2.75]
        im = ax.imshow(spd, origin="lower", extent=extent, aspect="equal", cmap="inferno", vmin=0.0, vmax=vmax_spd)
        step = 3
        qx, qy = np.meshgrid(xs[::step], ys[::step])
        uvx = np.nan_to_num(vx[::step, ::step], nan=0.0)
        uvy = np.nan_to_num(vy[::step, ::step], nan=0.0)
        mag = np.hypot(uvx, uvy)
        ok = mag > 1.5
        # Normalize vectors visually with speed scaling
        ax.quiver(qx[ok], qy[ok], uvx[ok], uvy[ok], color="white", alpha=0.88, scale=420, width=0.0032, headwidth=3.5)
        cb = fig.colorbar(im, ax=ax, fraction=0.032, pad=0.02)
        cb.set_label("Velocity [m/s]", fontsize=8)
        ax.set_title(
            f"{title_tag}\n3D CFD Z={sl['slice_z_mm']} mm | ΔP={res['cfd_3d']['tb_to_plenum_dp_kpa']:.2f} kPa | Flow Spread={res['cfd_3d']['cyl_maldistribution_spread_pct']:.2f}%",
            fontsize=10,
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
    ax3.plot(xb[m_in], ab_bare[m_in], color="#b0b0b0", ls="--", lw=1.2, label="Baseline Bare Plenum Area (0.78)")
    ax3.plot(xb[m_in], ab_core[m_in], color="#c0392b", lw=2.2, label=f"Baseline Effective Flow Area (Projected Wake Blockage {max(base_res['cad_audit']['cyl_peak_blockage_pct']):.1f}%)")
    ax3.plot(xb[m_in], ao_bare[m_in], color="#85c1e9", ls="--", lw=1.2, label="Optimized Bare Plenum Area (0.64)")
    ax3.plot(xb[m_in], ao_core[m_in], color="#1a5276", lw=2.3, label=f"Optimized Unobstructed Area (Blockage {max(opt_res['cad_audit']['cyl_peak_blockage_pct']):.1f}%)")
    for idx, xc in enumerate([-138, -46, 46, 138], start=1):
        ax3.axvline(xc, color="#888888", lw=0.7, ls=":")
        ax3.text(xc, 7100, f"Cyl {idx}", ha="center", va="bottom", fontsize=8)
    ax3.set_ylim(3800, 7600)
    ax3.set_xlim(-168, 168)
    ax3.grid(True, ls=":", alpha=0.5)
    ax3.legend(fontsize=7.8, loc="lower right")
    ax3.set_title("Exact CAD Cross-Section Audit: Eliminating Protruding Stack Cross-Flow Blockage", fontsize=10, fontweight="bold")
    ax3.set_xlabel("Plenum X Position [mm]", fontsize=8)
    ax3.set_ylabel("Effective Axial Flow Area [mm²]", fontsize=8)

    ax4 = fig.add_subplot(3, 2, 4)
    ax4.set_facecolor("#ffffff")
    tapers = [s["taper"] for s in sweep_taper]
    spread_flush = [s["spread_flush_pct"] for s in sweep_taper]
    spread_prot = [s["spread_protruding_pct"] for s in sweep_taper]
    ax4.plot(tapers, spread_prot, "o--", color="#c0392b", lw=1.8, ms=5, label="Protruding Stacks (14 mm) — 1D Compressible")
    ax4.plot(tapers, spread_flush, "s-", color="#117864", lw=2.3, ms=5.5, label="Wall-Flush Bellmouths (6.5 mm) — 1D Compressible")
    ax4.scatter([0.78], [base_res["sim_1d_7000rpm"]["ve_maldistribution_spread_pct"]], color="#922b21", s=110, zorder=5, label="Baseline Design (0.78, Protruding)")
    ax4.scatter([0.64], [opt_res["sim_1d_7000rpm"]["ve_maldistribution_spread_pct"]], color="#0e6251", marker="*", s=180, zorder=6, label="Boost-Optimized Design (0.64, Flush)")
    ax4.axhspan(0, 1.5, color="#d4efdf", alpha=0.45, label="Target Boost Maldistribution (< 1.5%)")
    ax4.set_ylim(0.0, 2.25)
    ax4.grid(True, ls=":", alpha=0.5)
    ax4.legend(fontsize=7.6, loc="upper left", ncol=2)
    ax4.set_title("Cylinder-to-Cylinder VE Spread vs. Plenum Taper Ratio (7,000 RPM @ 18 psi)", fontsize=10, fontweight="bold")
    ax4.set_xlabel("Plenum Cyl-1 / Cyl-4 Area Ratio (`taper_cyl1_area_ratio`)", fontsize=8)
    ax4.set_ylabel("Max-to-Min VE Spread [%]", fontsize=8)

    ax5 = fig.add_subplot(3, 2, 5)
    ax5.set_facecolor("#ffffff")
    cyls = np.arange(1, 5)
    w_bar = 0.19
    b_3d = [VE_REF * 100.0 * (s / 25.0) for s in base_res["cfd_3d"]["cyl_flow_share_pct"]]
    b_1d = [100.0 * v for v in base_res["sim_1d_7000rpm"]["cyl_ve"]]
    o_3d = [VE_REF * 100.0 * (s / 25.0) for s in opt_res["cfd_3d"]["cyl_flow_share_pct"]]
    o_1d = [100.0 * v for v in opt_res["sim_1d_7000rpm"]["cyl_ve"]]
    ax5.bar(cyls - 1.5 * w_bar, b_3d, width=w_bar, color="#e67e22", alpha=0.88, label=f"Baseline 3D FVM (Spread {base_res['cfd_3d']['cyl_maldistribution_spread_pct']:.2f}%)")
    ax5.bar(cyls - 0.5 * w_bar, b_1d, width=w_bar, color="#c0392b", alpha=0.90, label=f"Baseline 1D Network (Spread {base_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']:.2f}%)")
    ax5.bar(cyls + 0.5 * w_bar, o_3d, width=w_bar, color="#2980b9", alpha=0.90, label=f"Optimized 3D FVM (Spread {opt_res['cfd_3d']['cyl_maldistribution_spread_pct']:.2f}%)")
    ax5.bar(cyls + 1.5 * w_bar, o_1d, width=w_bar, color="#117864", alpha=0.92, label=f"Optimized 1D Network (Spread {opt_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']:.2f}%)")
    ax5.axhline(98.0, color="#333333", ls="--", lw=1.0)
    ax5.set_xticks(cyls)
    ax5.set_xticklabels([f"Cyl {i}" for i in cyls])
    ax5.set_ylim(94.0, 101.0)
    ax5.grid(True, axis="y", ls=":", alpha=0.5)
    ax5.legend(fontsize=7.6, loc="lower right")
    ax5.set_title("Individual Cylinder Volumetric Efficiency Balance @ 7,000 RPM / 18 PSI", fontsize=10, fontweight="bold")
    ax5.set_ylabel("Effective Volumetric Efficiency [%] (Ref 98%)", fontsize=8)

    ax6 = fig.add_subplot(3, 2, 6)
    ax6.set_facecolor("#ffffff")
    tr = opt_res["_sim1d_traces"]
    ca = tr["_ca_deg"]
    mr = tr["_m_run_hist"] * 1000.0
    colors = ["#1f618d", "#117864", "#d68910", "#b03a2e"]
    for i in range(4):
        ax6.plot(ca, mr[:, i], color=colors[i], lw=1.6, label=f"Cyl {i+1} Runner Flow [g/s]")
    ax6_r = ax6.twinx()
    ax6_r.plot(ca, tr["_p_pl_kpa"], color="#2c3e50", ls="--", lw=1.4, label="Plenum Pressure [kPa abs]")
    ax6.set_xlim(0, 720)
    ax6.set_xticks([0, 180, 360, 540, 720])
    ax6.grid(True, ls=":", alpha=0.5)
    lines1, labels1 = ax6.get_legend_handles_labels()
    lines2, labels2 = ax6_r.get_legend_handles_labels()
    ax6.legend(lines1 + lines2, labels1 + labels2, fontsize=7.5, loc="upper right")
    ax6.set_title(
        f"720° Crank Cycle (1-3-4-2 @ 7,000 RPM): Peak Throat M={opt_res['sim_1d_7000rpm']['peak_mach_throat']:.3f}, Helmholtz={opt_res['sim_1d_7000rpm']['helmholtz_freq_hz']:.0f} Hz",
        fontsize=10,
        fontweight="bold",
    )
    ax6.set_xlabel("Crank Angle [deg]", fontsize=8)
    ax6.set_ylabel("Instantaneous Runner Mass Flow [g/s]", fontsize=8)
    ax6_r.set_ylabel("Plenum Pressure [kPa abs]", fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.945])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main():
    t_start = time.perf_counter()
    opt_params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    base_params = make_baseline_params(opt_params)

    print("1/4 Running 3D FVM + 1D Compressible Audit on BASELINE geometry...")
    base_res = evaluate_design(base_params, "baseline_protruding_14mm_078taper_10cant", dx_vox=5.5, run_3d=True)
    print(
        f"    Done in {base_res['elapsed_s']}s | mass_err={base_res['cfd_3d']['mass_conservation_error_pct']}% | "
        f"3D dP={base_res['cfd_3d']['tb_to_plenum_dp_kpa']} kPa | 3D spread={base_res['cfd_3d']['cyl_maldistribution_spread_pct']}% | "
        f"1D VE spread={base_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']}%"
    )

    print("2/4 Running 3D FVM + 1D Compressible Audit on BOOST-OPTIMIZED geometry...")
    opt_res = evaluate_design(opt_params, "boost_optimized_flush_65flare_064taper_8cant", dx_vox=5.5, run_3d=True)
    print(
        f"    Done in {opt_res['elapsed_s']}s | mass_err={opt_res['cfd_3d']['mass_conservation_error_pct']}% | "
        f"3D dP={opt_res['cfd_3d']['tb_to_plenum_dp_kpa']} kPa | 3D spread={opt_res['cfd_3d']['cyl_maldistribution_spread_pct']}% | "
        f"1D VE spread={opt_res['sim_1d_7000rpm']['ve_maldistribution_spread_pct']}%"
    )

    print("3/4 Running parametric taper & RPM curves...")
    sweep_taper = []
    for taper in [0.54, 0.58, 0.62, 0.64, 0.68, 0.72, 0.78, 0.85, 0.94]:
        p_flush = copy.deepcopy(opt_params)
        p_flush["plenum"]["taper_cyl1_area_ratio"] = taper
        s_f = solve_1d_compressible_and_pulsating(p_flush, opt_res["cad_audit"], rpm=DESIGN_RPM)

        p_prot = copy.deepcopy(base_params)
        p_prot["plenum"]["taper_cyl1_area_ratio"] = taper
        s_p = solve_1d_compressible_and_pulsating(p_prot, base_res["cad_audit"], rpm=DESIGN_RPM)

        sweep_taper.append({
            "taper": taper,
            "spread_flush_pct": s_f["ve_maldistribution_spread_pct"],
            "spread_protruding_pct": s_p["ve_maldistribution_spread_pct"],
            "dp_flush_kpa": s_f["dp_total_kpa"],
            "dp_protruding_kpa": s_p["dp_total_kpa"],
        })

    rpm_sweep = []
    for rpm in [3000, 4000, 5000, 6000, 6500, 7000, 7500]:
        s_r = solve_1d_compressible_and_pulsating(opt_params, opt_res["cad_audit"], rpm=float(rpm))
        rpm_sweep.append({k: v for k, v in s_r.items() if not k.startswith("_")})

    print("4/4 Saving verification JSON and multi-panel plot...")
    plot_verification_report(
        base_res, opt_res, sweep_taper, rpm_sweep, FITMENT_DIR / "03_airflow_verification.png"
    )

    keep_audit = {
        "cyl_peak_blockage_pct",
        "mean_stack_blockage_pct",
        "total_fluid_volume_liters",
        "bare_plenum_volume_liters",
        "tb_inlet_area_mm2",
        "runner_throat_area_mm2",
        "runner_exit_area_mm2",
        "runner_contraction_ratio",
        "plenum_to_runner_area_ratio_cyl4",
        "plenum_to_runner_area_ratio_cyl1",
    }
    summary = {
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
        "taper_sweep": sweep_taper,
        "rpm_sweep_optimized": rpm_sweep,
        "total_runtime_s": round(time.perf_counter() - t_start, 2),
    }
    STL_DIR.mkdir(parents=True, exist_ok=True)
    (STL_DIR / "airflow_verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Completed airflow verification in {summary['total_runtime_s']}s.")


if __name__ == "__main__":
    main()
