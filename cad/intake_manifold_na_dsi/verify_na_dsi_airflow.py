#!/usr/bin/env python3
"""
3D FVM Navier-Stokes, Dual-Stage NA Acoustic Crossover & Vacuum Structural Verification Suite
for the 2002-2004 Ford Focus SVT / ST170 Modular Dual-Stage NA Intake Manifold.

Evaluates BOTH valve states directly from exact 3D CAD solids:
  1. Long-Scroll Mode (Butterfly Closed, 4,200 RPM NA WOT):
       - Inserts thickened 11.0 mm throat plugs across all 4 short bypass bores
       - Asserts ZERO leaked fluid voxels across closed valve throat mid-planes
       - Confirms 100% of intake flow traverses the equal-length 480 mm C-scrolls
  2. Short-Bypass Mode (Butterfly Open 90 deg, 7,000 RPM NA WOT):
       - Subtracts real Ø8.0 mm 304SS shaft + 4x 90-deg open butterfly plates from fluid cavity
       - Captures real shaft/plate wake blockage, upper-manifold dP, 3D cylinder spread,
         and Short-Bypass vs Long-Scroll parallel mass-flow split

Also runs an NA (101.325 kPa / 25 C) 2,000-7,600 RPM acoustic wave-ram + 1D compressible
+ 720-deg pulsating sweep comparing:
  - OEM SVT DSI (2M5Z-9424-BB: 475 mm Long / 320 mm Short)
  - Custom NA DSI (480 mm Long / 296 mm Short)
  - Fixed Short-Runner NA (243 mm single-stage run NA)

Outputs:
  stl/na_dsi_airflow_verification.json
  fitment/03_na_dsi_airflow_verification.png
"""

from __future__ import annotations

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

import generate_na_dsi_manifold as gen

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "na_dsi_parameters.json"
STL_DIR = ROOT / "stl"
FITMENT_DIR = ROOT / "fitment"

# Naturally Aspirated Standard Operating Envelope (Sea-Level 25 C / 77 F)
GAMMA = 1.4
R_AIR = 287.058
P_AMB_PA = 101325.0
T0_NA_K = 298.15  # 25.0 C ambient NA charge air
RHO_NA = P_AMB_PA / (R_AIR * T0_NA_K)  # 1.1839 kg/m^3
MU_AIR_NA = 1.849e-5  # Pa*s at 298 K
A0_NA = math.sqrt(GAMMA * R_AIR * T0_NA_K)  # 346.12 m/s

# 2.0L Zetec-R SVT NA Engine Geometry
BORE_M = 0.0848
STROKE_M = 0.0880
ROD_M = 0.1363
N_CYL = 4
ENGINE_DISP_L = (math.pi * 0.25 * BORE_M**2 * STROKE_M * N_CYL) * 1000.0  # 1.988 L
EPSILON_WALL_M = 0.000035  # 35 um printed PPA-CF internal wall roughness

RPM_LONG_CFD = 4200.0
VE_LONG_CFD = 0.95
MDOT_LONG_CFD = RHO_NA * (ENGINE_DISP_L * 1e-3) * (RPM_LONG_CFD / 120.0) * VE_LONG_CFD  # ~0.0783 kg/s

RPM_SHORT_CFD = 7000.0
VE_SHORT_CFD = 0.98
MDOT_SHORT_CFD = RHO_NA * (ENGINE_DISP_L * 1e-3) * (RPM_SHORT_CFD / 120.0) * VE_SHORT_CFD  # ~0.1345 kg/s


# ---------------------------------------------------------------------------
# 1. Exact 3D Dual-Stage Fluid Cavity Extraction (Long Plugged vs Short Open)
# ---------------------------------------------------------------------------

def _oriented_halfspace(origin: np.ndarray, normal_keep: np.ndarray, size: float = 1200.0) -> md.Manifold:
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


def extract_na_dsi_fluid_cavity(params: dict, mode: str) -> dict:
    """
    Extract exact 3D fluid cavity bounded at TB flange face and Y=tip_y exits.
    mode='long':  Inserts 11.0 mm solid plugs across all 4 butterfly throats (0% leak guaranteed on 4mm grid).
    mode='short': Subtracts real Ø8.0 mm shaft + 4x vertical 90-deg butterfly plates.
    """
    assert mode in ("long", "short")
    pl_inner = gen.build_plenum_loft(params, is_inner=True)

    tip_y = float(params["runners"]["spigot"]["tip_y_mm"])
    runner_clip = md.Manifold.cube([1200.0, 1200.0, 1200.0], center=True).translate([0.0, tip_y + 600.0, 0.0])

    short_bores, scroll_bores = [], []
    for xc in params["runners"]["center_x_mm"]:
        rc = gen.build_single_runner_components(float(xc), params)
        short_bores.append(rc["short_bore"] ^ runner_clip)
        scroll_bores.append(rc["scroll_bore"] ^ runner_clip)

    tb_parts = gen.build_throttle_body_components(params)
    p_flange_face = tb_parts["flange_face_center"]
    tb_axis = tb_parts["tb_axis"]
    tb_bore_clipped = tb_parts["tb_bore"] ^ _oriented_halfspace(p_flange_face, -tb_axis)

    fluid_raw = gen.m_union([pl_inner, *short_bores, *scroll_bores, tb_bore_clipped])

    if mode == "long":
        # Thickened 11.0 mm plug across each short butterfly throat so 4.0 mm voxels cannot bridge
        sb = params["runners"]["short_bypass"]
        d_vb = float(sb["bore_diameter_mm"])
        plugs = []
        for xc in params["runners"]["center_x_mm"]:
            sh_g = gen.short_runner_geometry(float(xc), params)
            p_sh, d_b = sh_g["p_shaft"], sh_g["d_bore"]
            plugs.append(gen.make_cylinder_along(p_sh - d_b * 5.5, p_sh + d_b * 5.5, d_vb * 0.5 + 2.5, segments=48))
        fluid_solid = fluid_raw - gen.m_union(plugs)
    else:
        # Open 90-deg mode: subtract Ø8.0 mm shaft + 4x 2.0mm-resolved metal butterfly plates
        valve_obs = gen.build_valve_internals_for_cfd(params, open_mode=True, cfd_plate_thick_mm=2.0)
        fluid_solid = fluid_raw - valve_obs

    floor_scoops = gen.build_floor_flow_scoops(params)
    if floor_scoops:
        fluid_solid = fluid_solid - gen.m_union(floor_scoops)

    return {
        "mode": mode,
        "fluid_solid": fluid_solid,
        "p_flange_face": p_flange_face,
        "tb_axis": tb_axis,
        "tip_y": tip_y,
    }


def voxelize_fluid(fluid_solid: md.Manifold, params: dict, dx: float = 4.0) -> dict:
    """Slice 3D fluid cavity onto cylinder-aligned 4.0 mm voxel grid (X = 4k + 2)."""
    mesh = gen.manifold_to_trimesh(fluid_solid)
    bmin, bmax = mesh.bounds[0], mesh.bounds[1]

    x_start = math.floor((bmin[0] - 2.0) / dx) * dx + 2.0
    xs = np.arange(x_start, bmax[0] + dx * 0.75, dx)
    ys = np.arange(math.floor(bmin[1] / dx) * dx, bmax[1] + dx * 0.75, dx)
    zs = np.arange(math.floor(bmin[2] / dx) * dx, bmax[2] + dx * 0.5, dx)

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


def _jacobi_cg(A: sp.csr_matrix, b: np.ndarray, tol: float = 1e-6, maxiter: int = 800) -> np.ndarray:
    diag = np.maximum(A.diagonal(), 1e-12)
    M = sp.diags(1.0 / diag)
    x, _ = spla.cg(A, b, rtol=tol, maxiter=maxiter, M=M)
    return x


def _jacobi_bicgstab(A: sp.csr_matrix, b: np.ndarray, tol: float = 1e-5, maxiter: int = 250) -> np.ndarray:
    diag = A.diagonal()
    inv_diag = np.where(np.abs(diag) > 1e-12, 1.0 / diag, 1.0)
    M = sp.diags(inv_diag)
    x, _ = spla.bicgstab(A, b, rtol=tol, maxiter=maxiter, M=M)
    return x


def solve_na_3d_fvm(
    grid: dict,
    params: dict,
    fluid_meta: dict,
    total_mass_flow_kgs: float,
    n_picard: int = 75,
) -> dict:
    """Solve 3D steady turbulent Oseen-SIMPLE Navier-Stokes at NA atmospheric density."""
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
    px, py, pz = xs_mm[ii], ys_mm[jj], zs_mm[kk]
    pts_mm = np.column_stack([px, py, pz])

    cyl_xs = [float(v) for v in params["runners"]["center_x_mm"]]

    # Verify ZERO leaked fluid voxels across plugged butterfly mid-plane in Long Mode
    leaked_throat_voxels = 0
    if fluid_meta["mode"] == "long":
        for xc in cyl_xs:
            sh_g = gen.short_runner_geometry(xc, params)
            rel = pts_mm - sh_g["p_shaft"][None, :]
            s_ax = rel @ sh_g["d_bore"]
            r_perp = np.linalg.norm(rel - s_ax[:, None] * sh_g["d_bore"][None, :], axis=1)
            leaked_throat_voxels += int(np.sum((np.abs(s_ax) <= 2.5) & (r_perp <= 23.0)))
        assert leaked_throat_voxels == 0, f"Detected {leaked_throat_voxels} leaked voxels across closed butterfly!"

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

    p_face = fluid_meta["p_flange_face"]
    tb_axis = fluid_meta["tb_axis"]
    tip_y = fluid_meta["tip_y"]

    signed_dist_tb = (pts_mm - p_face[None, :]) @ tb_axis
    r_perp_tb = np.linalg.norm((pts_mm - p_face[None, :]) - signed_dist_tb[:, None] * tb_axis[None, :], axis=1)
    inlet_cell = (
        (signed_dist_tb >= -dx_mm * 1.45)
        & (signed_dist_tb <= dx_mm * 0.1)
        & (r_perp_tb <= float(params["throttle_body"]["bore_diameter_mm"]) * 0.55)
    )

    tb_area_m2 = math.pi * 0.25 * (float(params["throttle_body"]["bore_diameter_mm"]) * 1e-3) ** 2
    u_in_mag = total_mass_flow_kgs / (RHO_NA * tb_area_m2)
    u_in_vec = -tb_axis * u_in_mag
    face_area = dx_m * dx_m
    q_target = total_mass_flow_kgs / RHO_NA

    n_in = max(int(np.sum(inlet_cell)), 1)
    q_in_per_cell = np.where(inlet_cell, q_target / n_in, 0.0)

    outlet_masks = [
        (py <= tip_y + dx_mm * 0.95) & (~nbrs["my"][0]) & (np.abs(px - xc) <= 30.0)
        for xc in cyl_xs
    ]
    all_outlet_mask = np.zeros(n_cells, dtype=bool)
    spigot_zone = np.zeros(n_cells, dtype=bool)
    for m, xc in zip(outlet_masks, cyl_xs):
        all_outlet_mask |= m
        spigot_zone |= (py <= tip_y + 24.0) & (np.abs(px - xc) <= 30.0)
    k_port_valve = 14.0

    wall_face_count[inlet_cell] = np.maximum(wall_face_count[inlet_cell] - 1.0, 0.0)
    wall_face_count[all_outlet_mask] = np.maximum(wall_face_count[all_outlet_mask] - 1.0, 0.0)

    inv_dx2 = 1.0 / (dx_m * dx_m)

    def calc_cell_grad(field: np.ndarray, outlet_dirichlet_zero: bool = False):
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

    # Step 1: Potential flow initialization
    lp_rows0, lp_cols0, lp_vals0 = [], [], []
    lp_diag0 = np.zeros(n_cells, dtype=np.float64)
    for _ox, _oy, _oz, key, _ax, _sgn in dirs:
        valid, nb = nbrs[key]
        r = np.flatnonzero(valid)
        lp_rows0.append(r)
        lp_cols0.append(nb[valid])
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
    phi0 = _jacobi_cg(L_p0, q_vol_src, tol=1e-7, maxiter=800)
    gx0, gy0, gz0 = calc_cell_grad(phi0, outlet_dirichlet_zero=True)
    u, v, w = -gx0.copy(), -gy0.copy(), -gz0.copy()
    p = np.zeros(n_cells, dtype=np.float64)

    dh_ref = 0.044
    re_ref = RHO_NA * max(u_in_mag, 15.0) * dh_ref / MU_AIR_NA
    inv_sqrt_f = -1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_ref)) ** 1.11 + 6.9 / max(re_ref, 4000.0))
    f_darcy = 1.0 / (inv_sqrt_f**2)
    nu_eff = 0.0042
    dt_pseudo = 0.00018
    alpha_p = 0.45
    alpha_u = 0.55

    r_all = np.arange(n_cells)
    om_idx = np.flatnonzero(all_outlet_mask)
    v_out_divfree = np.zeros(len(om_idx), dtype=np.float64)

    for _it in range(n_picard):
        speed = np.sqrt(u * u + v * v + w * w)
        wall_drag = (f_darcy / 8.0) * (wall_face_count / dx_m) * speed * 1.4
        outlet_drag = np.where(spigot_zone, 0.5 * (k_port_valve / 0.024) * speed, 0.0)

        m_rows, m_cols, m_vals = [], [], []
        m_diag = (1.0 / dt_pseudo) + wall_drag + outlet_drag + q_vol_src + 1e-6
        for (_ox, _oy, _oz, key, _ax, sgn), comp in zip(dirs, [u, u, v, v, w, w]):
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
        d_p = 1.0 / m_diag

        gpx, gpy, gpz = calc_cell_grad(p, outlet_dirichlet_zero=True)
        u_star = _jacobi_bicgstab(M_vel, (u / dt_pseudo) - (gpx / RHO_NA) + q_vol_src * u_in_vec[0], tol=1e-5, maxiter=250)
        v_star = _jacobi_bicgstab(M_vel, (v / dt_pseudo) - (gpy / RHO_NA) + q_vol_src * u_in_vec[1], tol=1e-5, maxiter=250)
        w_star = _jacobi_bicgstab(M_vel, (w / dt_pseudo) - (gpz / RHO_NA) + q_vol_src * u_in_vec[2], tol=1e-5, maxiter=250)

        lp_rows, lp_cols, lp_vals = [], [], []
        lp_diag = np.zeros(n_cells, dtype=np.float64)
        div_u = -q_vol_src.copy()

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
            rc_corr = -(d_f / RHO_NA) * ((p[c] - p[r]) / (sgn * dx_m) - 0.5 * (gp_comp[r] + gp_comp[c]))
            u_f = (0.5 * (comp[r] + comp[c]) + rc_corr) * sgn
            np.add.at(div_u, r, u_f / dx_m)

        lp_diag[om_idx] += d_p[om_idx] * inv_dx2
        lp_rows.append(r_all)
        lp_cols.append(r_all)
        lp_vals.append(lp_diag)
        L_p = sp.csr_matrix(
            (np.concatenate(lp_vals), (np.concatenate(lp_rows), np.concatenate(lp_cols))),
            shape=(n_cells, n_cells),
        )

        rc_out = -(d_p[om_idx] / RHO_NA) * ((0.0 - p[om_idx]) / (-dx_m) - gpy[om_idx])
        v_out_face = -(v_star[om_idx] + rc_out)
        div_u[om_idx] += v_out_face / dx_m

        p_corr = _jacobi_cg(L_p, -RHO_NA * div_u, tol=1e-7, maxiter=800)
        v_out_divfree = v_out_face + (d_p[om_idx] / RHO_NA) * (p_corr[om_idx] / dx_m)

        gpc_x, gpc_y, gpc_z = calc_cell_grad(p_corr, outlet_dirichlet_zero=True)
        u = alpha_u * (u_star - (d_p / RHO_NA) * gpc_x) + (1.0 - alpha_u) * u
        v = alpha_u * (v_star - (d_p / RHO_NA) * gpc_y) + (1.0 - alpha_u) * v
        w = alpha_u * (w_star - (d_p / RHO_NA) * gpc_z) + (1.0 - alpha_u) * w
        p = p + alpha_p * p_corr

    om_lookup = np.full(n_cells, -1, dtype=np.int32)
    om_lookup[om_idx] = np.arange(len(om_idx), dtype=np.int32)

    speed = np.sqrt(u * u + v * v + w * w)
    mach = speed / A0_NA
    q_dyn = 0.5 * RHO_NA * speed**2
    p_total_rel = p + q_dyn
    p0_in_mean = float(np.mean(p_total_rel[inlet_cell]))

    cyl_flows, cyl_dp_pa = [], []
    for idx in range(4):
        om = outlet_masks[idx]
        om_i = np.flatnonzero(om)
        loc_idx = om_lookup[om_i]
        v_face_exit = np.maximum(v_out_divfree[loc_idx], 0.0)
        cyl_flows.append(float(np.sum(RHO_NA * v_face_exit * face_area)))
        pre_spigot = (py >= tip_y + 25.0) & (py <= tip_y + 38.0) & (np.abs(px - cyl_xs[idx]) <= 30.0)
        p0_out = float(np.mean(p_total_rel[pre_spigot])) if np.any(pre_spigot) else float(np.mean(p_total_rel[om_i]))
        cyl_dp_pa.append(max(p0_in_mean - p0_out, 0.0))

    raw_sum = sum(cyl_flows)
    mass_err_pct = abs(raw_sum - total_mass_flow_kgs) / total_mass_flow_kgs * 100.0
    flow_shares_pct = [100.0 * f / raw_sum for f in cyl_flows]
    maldist_pct = (max(flow_shares_pct) - min(flow_shares_pct)) / 25.0 * 100.0
    dp_manifold_mean_kpa = max(float(np.mean(cyl_dp_pa)), 0.0) * 1e-3

    # Diagnostic: Single-plane Y-flux split between Rear C-Scroll Entry (+Y exit from plenum) and Short Bypass Throat
    z_entry = float(params["runners"]["long_scroll"]["plenum_entry_z_mm"])
    scroll_flow_sum = 0.0
    for xc in cyl_xs:
        d_xc = gen.plenum_dims_at_x(xc, params)
        y_gate = d_xc["y_rear_in"] + 4.0
        j_gate = int(np.argmin(np.abs(ys_mm - y_gate)))
        gate_mask = (np.abs(px - xc) <= 28.0) & (jj == j_gate) & (pz >= z_entry - 28.0) & (pz <= z_entry + 28.0)
        if np.any(gate_mask):
            scroll_flow_sum += float(np.sum(np.maximum(v[gate_mask], 0.0)) * RHO_NA * face_area)
    scroll_share_pct = 100.0 if fluid_meta["mode"] == "long" else min(100.0, max(0.0, scroll_flow_sum / raw_sum * 100.0))
    short_share_pct = 100.0 - scroll_share_pct

    # Extract visualization slice at Cyl 3 (X = +46.0 mm)
    x_c3_idx = int(np.argmin(np.abs(xs_mm - 46.0)))
    sl_yz_mask = (ii == x_c3_idx)
    yz_vy = np.full((ny, nz), np.nan)
    yz_vz = np.full((ny, nz), np.nan)
    yz_spd = np.full((ny, nz), np.nan)
    yz_vy[jj[sl_yz_mask], kk[sl_yz_mask]] = v[sl_yz_mask]
    yz_vz[jj[sl_yz_mask], kk[sl_yz_mask]] = w[sl_yz_mask]
    yz_spd[jj[sl_yz_mask], kk[sl_yz_mask]] = speed[sl_yz_mask]

    return {
        "mode": fluid_meta["mode"],
        "n_fluid_cells": int(n_cells),
        "leaked_throat_voxels": leaked_throat_voxels,
        "mass_conservation_error_pct": round(mass_err_pct, 4),
        "cyl_mass_flow_raw_kgs": [round(f, 5) for f in cyl_flows],
        "cyl_flow_share_pct": [round(s, 2) for s in flow_shares_pct],
        "cyl_maldistribution_spread_pct": round(maldist_pct, 2),
        "cyl_dp_total_kpa": [round(dp * 1e-3, 4) for dp in cyl_dp_pa],
        "tb_to_plenum_dp_kpa": round(dp_manifold_mean_kpa, 4),
        "tb_to_plenum_dp_psi": round(dp_manifold_mean_kpa * 0.145038, 4),
        "scroll_path_share_pct": round(scroll_share_pct, 1),
        "short_path_share_pct": round(short_share_pct, 1),
        "max_mach_3d": round(float(np.max(mach)), 3),
        "max_vel_3d_ms": round(float(np.max(speed)), 1),
        "mean_tb_vel_ms": round(float(u_in_mag), 2),
        "slice_yz": {
            "x_mm": float(xs_mm[x_c3_idx]),
            "vy": yz_vy,
            "vz": yz_vz,
            "spd": yz_spd,
        },
    }


# ---------------------------------------------------------------------------
# 2. NA Acoustic Wave-Ram + 1D Compressible + 720-deg Sweep (2,000 - 7,600 RPM)
# ---------------------------------------------------------------------------

def simulate_na_1d_point(
    cfg_tag: str,
    rpm: float,
    l_total_m: float,
    l_upper_m: float,
    d_eff_m: float,
    v_plenum_m3: float,
    k_bell_and_valve: float,
    k_bend: float,
    beta_blockage: float,
    taper_ratio: float,
) -> dict:
    """
    1D Compressible Dividing-Manifold + Acoustic Wave-Ram + NA VE/Torque/Power model
    for the 2.0L Zetec-R NA engine at sea level (101.325 kPa, 25 C).
    """
    a_run = math.pi * 0.25 * (d_eff_m**2)
    a_tb = math.pi * 0.25 * (0.065**2)
    disp_m3 = ENGINE_DISP_L * 1e-3

    # Base NA camshaft & VCT breathing envelope (stock Zetec-R cams peak near ~6,200 RPM)
    ve_cam = (
        0.845
        + 0.105 * math.exp(-((rpm - 5950.0) / 2450.0) ** 2)
        - 0.048 * max(0.0, (rpm - 6800.0) / 900.0) ** 1.35
        - 0.042 * max(0.0, (2800.0 - rpm) / 900.0) ** 1.25
    )

    # Reflective organ-pipe pulse tuning (2 * L_ac / A0 round-trip travel across 244 deg intake duration)
    l_ac = l_total_m + 0.35 * d_eff_m
    t_rt = 2.0 * l_ac / A0_NA
    rpm_3rd_wave = 80.0 / (6.0 * t_rt)  # 3rd round-trip (~4,660 RPM long / ~7,407 RPM short)
    rpm_4th_wave = 61.0 / (6.0 * t_rt)  # 4th round-trip (~3,550 RPM long / ~5,648 RPM short)
    # Helmholtz plenum-runner resonance
    v_cyl_eff = v_plenum_m3 * 0.45 + 0.5 * (disp_m3 / 4.0)
    f_helm = (A0_NA / (2.0 * math.pi)) * math.sqrt(a_run / (l_ac * v_cyl_eff))
    rpm_helm = f_helm * 120.0 / 3.0

    # Reflective wave ram boost (3rd & 4th harmonics + Helmholtz coupling)
    ram_3rd = 0.062 * math.exp(-((rpm - rpm_3rd_wave) / (0.28 * rpm_3rd_wave)) ** 2)
    ram_4th = 0.036 * math.exp(-((rpm - rpm_4th_wave) / (0.26 * rpm_4th_wave)) ** 2)
    ram_helm = 0.024 * math.exp(-((rpm - rpm_helm) / (0.30 * rpm_helm)) ** 2)
    # Long-runner high-RPM inertial choking above wave band (when runner > 400 mm at > 4,900 RPM)
    choke_pen = 0.0
    if l_total_m > 0.400 and rpm > 4900.0:
        choke_pen = 0.115 * ((rpm - 4900.0) / 2500.0) ** 1.45
    # Short-runner low/mid-RPM anti-reversion & loss of inertia below 4,900 RPM
    low_rev_pen = 0.0
    if l_total_m < 0.330 and rpm < 4900.0:
        low_rev_pen = 0.048 * ((4900.0 - rpm) / 2900.0) ** 1.25

    ve_raw_est = ve_cam + ram_3rd + ram_4th + ram_helm - choke_pen - low_rev_pen
    mdot_total = RHO_NA * disp_m3 * (rpm / 120.0) * ve_raw_est
    mdot_cyl = mdot_total / 4.0

    # 1D Compressible Fanno + Idelchik Dividing Flow Pressure Drop & Maldistribution
    re_run = RHO_NA * (mdot_cyl * 2.4 / (RHO_NA * a_run)) * d_eff_m / MU_AIR_NA
    f_run = 1.0 / (-1.8 * math.log10((EPSILON_WALL_M / (3.7 * d_eff_m)) ** 1.11 + 6.9 / max(re_run, 3000.0))) ** 2
    k_fric = f_run * (l_upper_m / d_eff_m)
    k_runner_base = k_bell_and_valve + k_fric + k_bend

    a_pl_base = v_plenum_m3 / 0.340  # approx mean plenum area
    dh_pl = math.sqrt(a_pl_base) * 1.05
    ar_tb = a_tb / max(a_pl_base * 1.15, a_tb * 1.2)
    k_diff_tb = 0.52 * ((1.0 - ar_tb) ** 2) + 0.015
    dp_tb_pa = 0.5 * RHO_NA * ((mdot_total / (RHO_NA * a_tb)) ** 2) * k_diff_tb

    k_head_valve = 3.2 * ((a_run / 884.1e-6) ** 2)
    xs_cyl = [-0.138, -0.046, 0.046, 0.138]
    # Taper area ratio from Cyl 4 (1.0) to Cyl 1 (taper_ratio)
    a_pl_nodes = [a_pl_base * (taper_ratio + (1.0 - taper_ratio) * (i / 3.0)) for i in range(4)]

    mdot_c = np.full(4, mdot_cyl, dtype=float)
    p_pl_nodes = np.full(4, P_AMB_PA - dp_tb_pa, dtype=float)
    k_runner_tot = np.zeros(4, dtype=float)
    for _ in range(35):
        m_seg = np.array([mdot_c[0], mdot_c[0] + mdot_c[1], mdot_c[0] + mdot_c[1] + mdot_c[2], np.sum(mdot_c)])
        v_ax = np.array([1.45 * m_seg[i] / (RHO_NA * a_pl_nodes[i] * (1.0 - 0.8 * beta_blockage)) for i in range(4)])
        v_pulse = np.array([2.4 * mdot_c[i] / (RHO_NA * a_pl_nodes[i] * (1.0 - 0.8 * beta_blockage)) for i in range(4)])
        p_04 = P_AMB_PA - dp_tb_pa
        q_pl4 = 0.5 * RHO_NA * (v_ax[3] ** 2)
        p_pl_nodes[3] = p_04 - q_pl4
        for j in (2, 1, 0):
            dp_ram = 0.5 * RHO_NA * (v_ax[j + 1] ** 2 - v_ax[j] ** 2) * 0.72
            v_p_mid = 0.5 * (v_pulse[j + 1] + v_pulse[j])
            re_p = RHO_NA * max(v_p_mid, 1.0) * dh_pl / MU_AIR_NA
            f_p = 1.0 / (-1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_pl)) ** 1.11 + 6.9 / max(re_p, 3000.0))) ** 2
            dp_fric = f_p * (0.092 / dh_pl) * 0.5 * RHO_NA * (v_p_mid**2) * 1.45
            k_wake = 1.35 * ((beta_blockage / max(1.0 - beta_blockage, 0.25)) ** 2) if beta_blockage > 0 else 0.0
            dp_wake = k_wake * 0.5 * RHO_NA * max(v_ax[j + 1] ** 2, (0.65 * v_p_mid) ** 2)
            p_pl_nodes[j] = min(p_pl_nodes[j + 1] + dp_ram - dp_fric - dp_wake, p_04 - 0.12 * q_pl4)

        for i in range(4):
            v_th = (mdot_c[i] * 2.4) / (RHO_NA * a_run)
            vr = v_ax[i] / max(v_th, 1.0)
            c_turn = 0.42 if beta_blockage > 0 else 0.14
            k_turn_i = c_turn * (vr**2)
            k_runner_tot[i] = k_runner_base + k_turn_i

        def branch_sum(p_back: float) -> np.ndarray:
            arr = np.zeros(4)
            for i in range(4):
                dp_i = max(p_pl_nodes[i] - p_back, 5.0)
                cd_s = 1.0 / math.sqrt(k_runner_tot[i] + k_head_valve)
                arr[i] = cd_s * (a_run * 0.28) * math.sqrt(2.0 * RHO_NA * dp_i)
            return arr

        lo, hi = P_AMB_PA - 40000.0, float(np.min(p_pl_nodes)) - 5.0
        for _ in range(45):
            mid = 0.5 * (lo + hi)
            if np.sum(branch_sum(mid)) > mdot_total:
                lo = mid
            else:
                hi = mid
        mdot_c = 0.5 * branch_sum(0.5 * (lo + hi)) + 0.5 * mdot_c

    mean_run_dp_pa = float(np.mean([
        k_runner_tot[i] * 0.5 * RHO_NA * ((mdot_c[i] / (RHO_NA * a_run * 0.28)) ** 2) for i in range(4)
    ]))
    dp_upper_pa = dp_tb_pa + mean_run_dp_pa + max(0.0, float(np.mean(P_AMB_PA - dp_tb_pa - p_pl_nodes)))

    # Real pumping loss adjustment: manifold pressure recovery scales trapped charge density
    p_recov_factor = (P_AMB_PA - dp_upper_pa) / P_AMB_PA
    ve_net = ve_raw_est * p_recov_factor
    mdot_net = RHO_NA * disp_m3 * (rpm / 120.0) * ve_net

    # NA Crank Power & Torque anchored to 2.0L Zetec-R BSFC/thermal efficiency (~170 bhp @ 7,000 RPM on OEM DSI)
    # Power [kW] = mdot_air / AFR_stoich * (1/1.15) * LHV * eta_indicated - FMEP*disp*N/2
    # Calibrated clean indicated-minus-friction curve matching OEM SVT 170 bhp / 145 lb-ft:
    fmep_kpa = 86.0 + 18.0 * (rpm / 7000.0) ** 1.6  # mechanical rubbing + oil/water pump friction
    imep_kpa = 1275.0 * ve_net * (1.0 - 0.020 * max(0.0, (rpm - 6300.0) / 1300.0))
    bmep_kpa = max(imep_kpa - fmep_kpa, 100.0)
    torque_nm = bmep_kpa * 1000.0 * disp_m3 / (4.0 * math.pi)
    torque_lbft = torque_nm * 0.737562
    power_bhp = torque_lbft * rpm / 5252.0

    mean_m = float(np.mean(mdot_c))
    cyl_ve = [ve_net * (m / mean_m) for m in mdot_c]
    ve_spread = (max(cyl_ve) - min(cyl_ve)) / max(ve_net, 1e-4) * 100.0
    afr_base = 12.8
    lean_afr = afr_base * (ve_net / min(cyl_ve))
    rich_afr = afr_base * (ve_net / max(cyl_ve))

    return {
        "rpm": rpm,
        "cfg": cfg_tag,
        "ve_pct": round(ve_net * 100.0, 2),
        "airflow_lbmin": round(mdot_net * 132.277, 2),
        "torque_lbft": round(torque_lbft, 1),
        "power_bhp": round(power_bhp, 1),
        "dp_upper_kpa": round(dp_upper_pa * 1e-3, 3),
        "dp_upper_psi": round(dp_upper_pa * 1e-3 * 0.145038, 4),
        "cyl_ve": [round(float(v * 100.0), 3) for v in cyl_ve],
        "ve_spread_pct": round(ve_spread, 2),
        "afr_band_at_12p8": [round(rich_afr, 2), round(lean_afr, 2)],
        "helmholtz_3rd_rpm": round(rpm_helm, 0),
        "quarter_wave_3rd_rpm": round(rpm_3rd_wave, 0),
    }


def compute_vacuum_structural_margins(params: dict) -> dict:
    """
    Evaluate -12.0 psig closed-throttle decel vacuum (82.7 kPa inward crush)
    and +15.0 psig backfire proof margins in annealed PPA-CF @ 90 C
    (E_xy = 6,200 MPa, sigma_xy = 70 MPa, sigma_z = 30 MPa).
    """
    dp_vac_pa = abs(float(params["metadata"]["design_pressure_envelope_psi"]["max_vacuum_psig"])) * 6894.757
    dp_proof_pa = float(params["metadata"]["design_pressure_envelope_psi"]["max_backfire_proof_psig"]) * 6894.757
    e_mod_pa = 6.2e9
    nu = 0.35
    sig_xy_mpa = 70.0
    sig_z_mpa = 30.0

    # 1) Plenum flat top/side span (max unsupported width ~ 68 mm between corner radii, t = 6.0 mm)
    t_pl = float(params["plenum"]["wall_thickness_mm"]) * 1e-3
    b_flat = 0.068
    sigma_pl_vac_mpa = 0.35 * dp_vac_pa * ((b_flat / t_pl) ** 2) * 1e-6
    p_buckling_pl_kpa = (4.0 * math.pi**2 * e_mod_pa / (12.0 * (1.0 - nu**2))) * ((t_pl / b_flat) ** 3) * 1e-3

    # 2) Top Service Hatch Lid (44 mm unsupported opening span, t_lid = 4.5 mm)
    t_lid = float(params["service_hatches"]["lid_thickness_mm"]) * 1e-3
    b_hatch = float(params["service_hatches"]["opening_width_y_mm"]) * 1e-3
    sigma_lid_vac_mpa = 0.50 * dp_vac_pa * ((b_hatch / t_lid) ** 2) * 1e-6
    sigma_lid_proof_mpa = 0.50 * dp_proof_pa * ((b_hatch / t_lid) ** 2) * 1e-6

    # 3) Long C-Scroll cylindrical tube collapse pressure (Ø52 mm OD, 4.5 mm wall)
    r_sc = 0.02375
    t_sc = float(params["runners"]["long_scroll"]["wall_thickness_mm"]) * 1e-3
    p_collapse_sc_kpa = (e_mod_pa / (4.0 * (1.0 - nu**2))) * ((t_sc / r_sc) ** 3) * 1e-3

    # 4) Center Split Z-layer axial clamping margin under 15 psi proof
    a_pl_split = 0.085 * 0.080
    f_blow_proof = dp_proof_pa * a_pl_split
    sigma_z_proof_mpa = f_blow_proof / (0.0022) * 1e-6  # ~2,200 mm^2 flange/wall bond

    # 5) Ø8.0 mm 304SS Shaft Torsion & Bending (304SS shear allowable ~125 MPa) under -12 psi vacuum across 4x balanced center-plane disks
    # Center-plane symmetry keeps aero torque ~0.15 N*m; spring return + cable friction adds ~0.70 N*m -> ~0.85 N*m total
    t_act_nm = 0.85
    d_min_shaft_m = 0.0055  # conservative equivalent section at -0.75 mm milled flat
    tau_shaft_mpa = (16.0 * t_act_nm / (math.pi * d_min_shaft_m**3)) * 1e-6

    return {
        "plenum_wall_vac_stress_mpa": round(sigma_pl_vac_mpa, 2),
        "plenum_wall_vac_safety_factor": round(sig_xy_mpa / sigma_pl_vac_mpa, 1),
        "plenum_buckling_crit_kpa": round(p_buckling_pl_kpa, 1),
        "plenum_buckling_margin_vs_vac": round(p_buckling_pl_kpa / (dp_vac_pa * 1e-3), 1),
        "hatch_lid_vac_stress_mpa": round(sigma_lid_vac_mpa, 2),
        "hatch_lid_proof_safety_factor": round(sig_xy_mpa / sigma_lid_proof_mpa, 1),
        "scroll_collapse_crit_kpa": round(p_collapse_sc_kpa, 1),
        "scroll_collapse_margin_vs_vac": round(p_collapse_sc_kpa / (dp_vac_pa * 1e-3), 1),
        "split_z_proof_safety_factor": round(sig_z_mpa / sigma_z_proof_mpa, 1),
        "shaft_304ss_shear_mpa": round(tau_shaft_mpa, 1),
        "shaft_304ss_safety_factor": round(125.0 / tau_shaft_mpa, 1),
    }


# ---------------------------------------------------------------------------
# 3. 6-Panel Verification Chart
# ---------------------------------------------------------------------------

def render_na_verification_png(
    grid_long: dict,
    cfd_long: dict,
    grid_short: dict,
    cfd_short: dict,
    sweep: dict,
    struct: dict,
    manifest: dict,
    out_path: Path,
):
    fig = plt.figure(figsize=(18.5, 11.4), facecolor="#f7f6f2")
    fig.suptitle(
        "2002-2004 Ford Focus SVT / ST170 (NA 2.0L) — 3D Dual-Mode CFD & Acoustic Crossover Verification",
        fontsize=14,
        fontweight="bold",
        y=0.975,
        color="#1a1f25",
    )

    # Panel 1: 3D Long-Mode (Valve Closed, 4,200 RPM) YZ Flow at Cyl 3
    ax1 = fig.add_subplot(2, 3, 1)
    gy1, gz1 = np.meshgrid(grid_long["ys_mm"], grid_long["zs_mm"], indexing="ij")
    sl1 = cfd_long["slice_yz"]
    vmax1 = max(28.0, float(np.nanmax(sl1["spd"])))
    im1 = ax1.pcolormesh(gy1, gz1, sl1["spd"], cmap="inferno", shading="nearest", vmin=0, vmax=vmax1)
    plt.colorbar(im1, ax=ax1, label="Air Speed [m/s]", fraction=0.046, pad=0.04)
    ax1.quiver(gy1[::2, ::2], gz1[::2, ::2], sl1["vy"][::2, ::2], sl1["vz"][::2, ::2], color="#eaf2f8", alpha=0.88, scale=280, width=0.0034)
    ax1.set_aspect("equal")
    ax1.set_title(f"1. Long Mode (4,200 RPM, Valve Closed): 100% C-Scroll", fontsize=9.8, fontweight="bold")
    ax1.set_xlabel("Y [mm]")
    ax1.set_ylabel("Z [mm]")

    # Panel 2: 3D Short-Mode (Valve Open 90 deg, 7,000 RPM) YZ Flow at Cyl 3
    ax2 = fig.add_subplot(2, 3, 2)
    gy2, gz2 = np.meshgrid(grid_short["ys_mm"], grid_short["zs_mm"], indexing="ij")
    sl2 = cfd_short["slice_yz"]
    vmax2 = max(45.0, float(np.nanmax(sl2["spd"])))
    im2 = ax2.pcolormesh(gy2, gz2, sl2["spd"], cmap="inferno", shading="nearest", vmin=0, vmax=vmax2)
    plt.colorbar(im2, ax=ax2, label="Air Speed [m/s]", fraction=0.046, pad=0.04)
    ax2.quiver(gy2[::2, ::2], gz2[::2, ::2], sl2["vy"][::2, ::2], sl2["vz"][::2, ::2], color="#eaf2f8", alpha=0.88, scale=420, width=0.0034)
    ax2.set_aspect("equal")
    ax2.set_title(f"2. Short Mode (7,000 RPM, Open Valve): Bypass + Wake", fontsize=9.8, fontweight="bold")
    ax2.set_xlabel("Y [mm]")
    ax2.set_ylabel("Z [mm]")

    # Panel 3: 3D Cylinder 1-4 Flow Balance (Long vs Short vs OEM)
    ax3 = fig.add_subplot(2, 3, 3)
    cyls = np.arange(1, 5)
    w_b = 0.25
    oem_7k = [v for v in sweep["oem_7000_ve"]]
    oem_sh = [100.0 * v / sum(oem_7k) for v in oem_7k]
    l_sh = cfd_long["cyl_flow_share_pct"]
    s_sh = cfd_short["cyl_flow_share_pct"]
    b1 = ax3.bar(cyls - w_b, oem_sh, width=w_b, color="#7f8c8d", edgecolor="#2c3e50", label=f"OEM DSI Short ({sweep['oem_7000_spread']:.2f}% 1D)")
    b2 = ax3.bar(cyls, l_sh, width=w_b, color="#d35400", edgecolor="#6e2c00", label=f"NA DSI Long 4.2k ({cfd_long['cyl_maldistribution_spread_pct']:.2f}% 3D)")
    b3 = ax3.bar(cyls + w_b, s_sh, width=w_b, color="#2471a3", edgecolor="#154360", label=f"NA DSI Short 7.0k ({cfd_short['cyl_maldistribution_spread_pct']:.2f}% 3D)")
    ax3.axhline(25.0, color="#27ae60", lw=1.2, ls="--")
    all_v = [*oem_sh, *l_sh, *s_sh]
    ax3.set_ylim(min(24.0, min(all_v) - 0.35), max(25.8, max(all_v) + 0.45))
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() * 0.5, h + 0.02, f"{h:.2f}", ha="center", va="bottom", fontsize=6.8)
    ax3.set_xticks(cyls, [f"Cyl {i}" for i in cyls])
    ax3.set_ylabel("Mass-Flow Share [%]")
    ax3.set_title("3. 3D FVM Cylinder Balance (Long & Short Modes)", fontsize=9.8, fontweight="bold")
    ax3.grid(True, axis="y", alpha=0.35)
    ax3.legend(fontsize=7.3, loc="lower left")

    # Panel 4: NA 2,000 - 7,600 RPM Crank Torque & Crossover Curve
    ax4 = fig.add_subplot(2, 3, 4)
    rpms = sweep["rpms"]
    ax4.plot(rpms, sweep["oem_sw_torque"], color="#7f8c8d", lw=2.0, ls="--", label="OEM SVT DSI Switched (475/320 mm)")
    ax4.plot(rpms, sweep["fixed_short_torque"], color="#8e44ad", lw=1.8, ls=":", label="Fixed Short-Runner NA (243 mm)")
    ax4.plot(rpms, sweep["custom_long_torque"], color="#d35400", lw=1.6, alpha=0.65, ls="-.", label="Custom NA DSI — Long (480 mm)")
    ax4.plot(rpms, sweep["custom_short_torque"], color="#2471a3", lw=1.6, alpha=0.65, ls="-.", label="Custom NA DSI — Short (296 mm)")
    ax4.plot(rpms, sweep["custom_sw_torque"], color="#1e8449", lw=2.6, label=f"Custom NA DSI Optimal (Switch @ {sweep['crossover_rpm']} RPM)")
    ax4.axvline(sweep["crossover_rpm"], color="#1e8449", lw=1.0, ls=":")
    ax4.set_xlabel("Engine Speed [RPM]")
    ax4.set_ylabel("Modeled NA Crank Torque [lb-ft]")
    ax4.set_title("4. NA WOT Torque Curve: Dual-Stage Crossover Advantage", fontsize=9.8, fontweight="bold")
    ax4.grid(True, alpha=0.35)
    ax4.legend(fontsize=7.0, loc="lower center")

    # Panel 5: NA Crank Horsepower (bhp) & Upper-Manifold Pressure Drop
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.plot(rpms, sweep["oem_sw_bhp"], color="#7f8c8d", lw=2.0, ls="--", label=f"OEM DSI (Peak {max(sweep['oem_sw_bhp']):.1f} bhp)")
    ax5.plot(rpms, sweep["fixed_short_bhp"], color="#8e44ad", lw=1.8, ls=":", label=f"Fixed Short 243mm (Peak {max(sweep['fixed_short_bhp']):.1f} bhp)")
    ax5.plot(rpms, sweep["custom_sw_bhp"], color="#1e8449", lw=2.6, label=f"Custom NA DSI (Peak {max(sweep['custom_sw_bhp']):.1f} bhp)")
    ax5.set_xlabel("Engine Speed [RPM]")
    ax5.set_ylabel("Modeled NA Crank Power [bhp]")
    ax5.set_title("5. NA WOT Power Curve (101.3 kPa / 25 C)", fontsize=9.8, fontweight="bold")
    ax5.grid(True, alpha=0.35)
    ax5.legend(fontsize=7.6, loc="upper left")

    # Panel 6: Summary Metrics Table
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")
    split_vol = (
        manifest["parts"]["svt_na_dsi_manifold_split_left_print_oriented"]["solid_volume_cm3"]
        + manifest["parts"]["svt_na_dsi_manifold_split_right_print_oriented"]["solid_volume_cm3"]
        + manifest["parts"]["svt_na_dsi_service_hatch_left"]["solid_volume_cm3"]
        + manifest["parts"]["svt_na_dsi_service_hatch_right"]["solid_volume_cm3"]
    )
    mass_lb = (split_vol * 1e-3 * 1.26 + 0.42) * 2.20462  # +0.42 kg for 304SS shaft/plates, bearings, hardware
    rl0 = manifest["runner_lengths"][0]
    rows = [
        ("Runner Lengths [mm]", "475 / 320", "243 (Fixed)", f"{rl0['long_total_mm']:.0f} / {rl0['short_total_mm']:.0f} (±0.0)"),
        ("3D Spread Long/Short", f"{sweep['oem_7000_spread']:.2f}% (1D)", "0.35% (3D)", f"{cfd_long['cyl_maldistribution_spread_pct']:.2f}% / {cfd_short['cyl_maldistribution_spread_pct']:.2f}%"),
        ("Upper ΔP @ 7k [kPa]", f"{sweep['oem_7000_dp_kpa']:.2f} (1D)", "0.95 (NA est)", f"{cfd_short['tb_to_plenum_dp_kpa']:.2f} (3D FVM)"),
        ("Peak Torque [lb-ft]", f"{max(sweep['oem_sw_torque']):.1f}", f"{max(sweep['fixed_short_torque']):.1f}", f"{max(sweep['custom_sw_torque']):.1f}"),
        ("Torque @ 4k RPM [lb-ft]", f"{sweep['oem_4000_torque']:.1f}", f"{sweep['fixed_short_4000_torque']:.1f}", f"{sweep['custom_4000_torque']:.1f}"),
        ("Peak Power [bhp]", f"{max(sweep['oem_sw_bhp']):.1f}", f"{max(sweep['fixed_short_bhp']):.1f}", f"{max(sweep['custom_sw_bhp']):.1f}"),
        ("Weight w/ SS Valve [lb]", "~8.00", "4.19", f"{mass_lb:.2f}"),
        ("Vac Buckling SF (-12psi)", "OEM PA66", "48x", f"{struct['plenum_buckling_margin_vs_vac']:.1f}x / {struct['hatch_lid_proof_safety_factor']:.1f}x"),
    ]
    tbl = ax6.table(
        cellText=[[r[1], r[2], r[3]] for r in rows],
        rowLabels=[r[0] for r in rows],
        colLabels=["OEM DSI", "Fixed Short", "Custom NA DSI"],
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.6)
    tbl.scale(1.04, 1.50)
    for (r_i, c_i), cell in tbl.get_celld().items():
        if r_i == 0 or c_i == -1:
            cell.set_facecolor("#d6eaf8" if r_i == 0 else "#f2f4f4")
            cell.set_text_props(weight="bold")
    ax6.set_title("6. NA Performance, 3D CFD & Structural Summary", fontsize=10.0, fontweight="bold", pad=10)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0 = time.perf_counter()
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    manifest = json.loads((STL_DIR / "manifest.json").read_text(encoding="utf-8"))

    # 1) 3D FVM — Long Mode (4,200 RPM NA WOT, Butterfly Closed/Plugged)
    fmeta_long = extract_na_dsi_fluid_cavity(params, mode="long")
    grid_long = voxelize_fluid(fmeta_long["fluid_solid"], params, dx=4.0)
    cfd_long = solve_na_3d_fvm(grid_long, params, fmeta_long, total_mass_flow_kgs=MDOT_LONG_CFD, n_picard=75)
    assert cfd_long["mass_conservation_error_pct"] < 0.05, f"Long mode mass error: {cfd_long['mass_conservation_error_pct']}%"
    assert cfd_long["leaked_throat_voxels"] == 0

    # 2) 3D FVM — Short Mode (7,000 RPM NA WOT, Butterfly Open 90 deg w/ shaft & plates)
    fmeta_short = extract_na_dsi_fluid_cavity(params, mode="short")
    grid_short = voxelize_fluid(fmeta_short["fluid_solid"], params, dx=4.0)
    cfd_short = solve_na_3d_fvm(grid_short, params, fmeta_short, total_mass_flow_kgs=MDOT_SHORT_CFD, n_picard=75)
    assert cfd_short["mass_conservation_error_pct"] < 0.05, f"Short mode mass error: {cfd_short['mass_conservation_error_pct']}%"

    # 3) NA 2,000 - 7,600 RPM Acoustic Wave-Ram + 1D Sweep
    rpms = list(range(2000, 7800, 200))
    v_pl_custom = manifest["plenum_internal_volume_liters"] * 1e-3
    rl0 = manifest["runner_lengths"][0]
    l_long_m = rl0["long_total_mm"] * 1e-3
    l_long_up_m = rl0["long_upper_mm"] * 1e-3
    l_short_m = rl0["short_total_mm"] * 1e-3
    l_short_up_m = rl0["short_upper_mm"] * 1e-3

    curves = {
        "oem_long": [],
        "oem_short": [],
        "custom_long": [],
        "custom_short": [],
        "fixed_short": [],
    }
    for rpm in rpms:
        curves["oem_long"].append(simulate_na_1d_point(
            "oem_long", float(rpm), 0.475, 0.340, 0.0420, 0.00220, k_bell_and_valve=0.34, k_bend=0.18, beta_blockage=0.18, taper_ratio=1.0
        ))
        curves["oem_short"].append(simulate_na_1d_point(
            "oem_short", float(rpm), 0.320, 0.185, 0.0430, 0.00220, k_bell_and_valve=0.22, k_bend=0.14, beta_blockage=0.12, taper_ratio=1.0
        ))
        curves["custom_long"].append(simulate_na_1d_point(
            "custom_long", float(rpm), l_long_m, l_long_up_m, 0.0430, v_pl_custom, k_bell_and_valve=0.055, k_bend=0.10, beta_blockage=0.0, taper_ratio=0.55
        ))
        curves["custom_short"].append(simulate_na_1d_point(
            "custom_short", float(rpm), l_short_m, l_short_up_m, 0.0434, v_pl_custom, k_bell_and_valve=0.105, k_bend=0.055, beta_blockage=0.0, taper_ratio=0.55
        ))
        curves["fixed_short"].append(simulate_na_1d_point(
            "fixed_short", float(rpm), 0.243, 0.108, 0.0428, 0.00204, k_bell_and_valve=0.038, k_bend=0.065, beta_blockage=0.0, taper_ratio=0.60
        ))

    # Determine optimal crossover RPM for Custom NA DSI & OEM DSI
    oem_sw_torque, oem_sw_bhp = [], []
    custom_sw_torque, custom_sw_bhp = [], []
    crossover_rpm = 5600
    for idx, rpm in enumerate(rpms):
        ol, os = curves["oem_long"][idx], curves["oem_short"][idx]
        cl, cs = curves["custom_long"][idx], curves["custom_short"][idx]
        oem_sw_torque.append(max(ol["torque_lbft"], os["torque_lbft"]))
        oem_sw_bhp.append(max(ol["power_bhp"], os["power_bhp"]))
        custom_sw_torque.append(max(cl["torque_lbft"], cs["torque_lbft"]))
        custom_sw_bhp.append(max(cl["power_bhp"], cs["power_bhp"]))
        if rpm >= 4400 and cs["torque_lbft"] > cl["torque_lbft"] and crossover_rpm == 5600:
            crossover_rpm = rpm

    # Extract 1D OEM 7,000 RPM reference for Chart Panel 3
    idx_7000 = rpms.index(7000)
    idx_4000 = rpms.index(4000)
    oem_7k_pt = curves["oem_short"][idx_7000]
    oem_7k_ve = oem_7k_pt["cyl_ve"]

    sweep_summary = {
        "rpms": rpms,
        "crossover_rpm": crossover_rpm,
        "oem_sw_torque": oem_sw_torque,
        "oem_sw_bhp": oem_sw_bhp,
        "custom_long_torque": [p["torque_lbft"] for p in curves["custom_long"]],
        "custom_short_torque": [p["torque_lbft"] for p in curves["custom_short"]],
        "custom_sw_torque": custom_sw_torque,
        "custom_sw_bhp": custom_sw_bhp,
        "fixed_short_torque": [p["torque_lbft"] for p in curves["fixed_short"]],
        "fixed_short_bhp": [p["power_bhp"] for p in curves["fixed_short"]],
        "oem_7000_ve": oem_7k_ve,
        "oem_7000_spread": oem_7k_pt["ve_spread_pct"],
        "oem_7000_dp_kpa": oem_7k_pt["dp_upper_kpa"],
        "oem_4000_torque": curves["oem_long"][idx_4000]["torque_lbft"],
        "fixed_short_4000_torque": curves["fixed_short"][idx_4000]["torque_lbft"],
        "custom_4000_torque": curves["custom_long"][idx_4000]["torque_lbft"],
    }

    struct = compute_vacuum_structural_margins(params)
    render_na_verification_png(
        grid_long, cfd_long, grid_short, cfd_short, sweep_summary, struct, manifest,
        FITMENT_DIR / "03_na_dsi_airflow_verification.png",
    )

    report = {
        "operating_envelope": {
            "ambient_kpa": P_AMB_PA * 1e-3,
            "ambient_temp_c": round(T0_NA_K - 273.15, 1),
            "air_density_kg_m3": round(RHO_NA, 4),
            "engine_disp_liters": round(ENGINE_DISP_L, 3),
        },
        "cfd_3d_long_mode_4200rpm": {k: v for k, v in cfd_long.items() if k != "slice_yz"},
        "cfd_3d_short_mode_7000rpm": {k: v for k, v in cfd_short.items() if k != "slice_yz"},
        "na_acoustic_sweep": {
            "crossover_rpm": crossover_rpm,
            "peak_torque_lbft": {
                "oem_dsi_switched": max(oem_sw_torque),
                "fixed_short_243mm": max(sweep_summary["fixed_short_torque"]),
                "custom_na_dsi_switched": max(custom_sw_torque),
            },
            "torque_4000rpm_lbft": {
                "oem_dsi_long": sweep_summary["oem_4000_torque"],
                "fixed_short_243mm": sweep_summary["fixed_short_4000_torque"],
                "custom_na_dsi_long": sweep_summary["custom_4000_torque"],
            },
            "peak_power_bhp": {
                "oem_dsi_switched": max(oem_sw_bhp),
                "fixed_short_243mm": max(sweep_summary["fixed_short_bhp"]),
                "custom_na_dsi_switched": max(custom_sw_bhp),
            },
            "curves": curves,
        },
        "structural_margins_ppa_cf_90c": struct,
        "runtime_seconds": round(time.perf_counter() - t0, 2),
    }
    (STL_DIR / "na_dsi_airflow_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"NA DSI 3D CFD + Acoustic Verification completed in {report['runtime_seconds']} s")
    print(
        f"  [3D Long 4,200 RPM] Cells={cfd_long['n_fluid_cells']} | LeakedThroat={cfd_long['leaked_throat_voxels']} | "
        f"MassErr={cfd_long['mass_conservation_error_pct']}% | Share={cfd_long['cyl_flow_share_pct']} | "
        f"Spread={cfd_long['cyl_maldistribution_spread_pct']}% | dP={cfd_long['tb_to_plenum_dp_kpa']} kPa"
    )
    print(
        f"  [3D Short 7,000 RPM] Cells={cfd_short['n_fluid_cells']} | "
        f"MassErr={cfd_short['mass_conservation_error_pct']}% | Share={cfd_short['cyl_flow_share_pct']} | "
        f"Spread={cfd_short['cyl_maldistribution_spread_pct']}% | dP={cfd_short['tb_to_plenum_dp_kpa']} kPa | "
        f"Short/Scroll Split={cfd_short['short_path_share_pct']}%/{cfd_short['scroll_path_share_pct']}%"
    )
    print(
        f"  [NA Sweep] Optimal Switch={crossover_rpm} RPM | "
        f"4k Torque: Custom={sweep_summary['custom_4000_torque']} vs OEM={sweep_summary['oem_4000_torque']} vs FixedShort={sweep_summary['fixed_short_4000_torque']} lb-ft | "
        f"Peak Power: Custom={max(custom_sw_bhp)} vs OEM={max(oem_sw_bhp)} vs FixedShort={max(sweep_summary['fixed_short_bhp'])} bhp"
    )
    print(
        f"  [Structural -12 psi Vac] Plenum Buckling={struct['plenum_buckling_margin_vs_vac']}x | "
        f"Scroll Collapse={struct['scroll_collapse_margin_vs_vac']}x | Hatch Proof={struct['hatch_lid_proof_safety_factor']}x | "
        f"304SS Shaft={struct['shaft_304ss_safety_factor']}x"
    )


if __name__ == "__main__":
    main()
