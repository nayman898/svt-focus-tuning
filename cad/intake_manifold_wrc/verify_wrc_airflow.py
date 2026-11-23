#!/usr/bin/env python3
"""
3D FVM Navier-Stokes & Dual-Chamber Acoustic Verification Suite for the
2004 Ford Focus SVT Dual-Chamber WRC Slot-Diffuser Upper Intake Manifold.

Reads the current parametric WRC geometry, extracts its exact 3D twin-chamber
fluid cavity (Primary Diffuser -> Tapered Venturi Slot -> Secondary Chamber -> 4 Runners),
solves the conservative 3D Oseen-SIMPLE Navier-Stokes equations at 7,000 RPM / 18.0 psi,
and compares performance against both:
  1. OEM Plastic DSI Short (Pinned) — read-only from ../intake_manifold/stl/factory_comparison.json
  2. Custom Stage-2 Single-Chamber  — read-only from ../intake_manifold/stl/airflow_verification.json

Outputs:
  stl/wrc_airflow_verification.json
  fitment/03_wrc_airflow_verification.png
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

import generate_wrc_manifold as gen

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "wrc_manifold_parameters.json"
STL_DIR = ROOT / "stl"
FITMENT_DIR = ROOT / "fitment"
ORIG_DIR = ROOT.parent / "intake_manifold"

# Gas & Engine Operating Envelope (identical to cad/intake_manifold/verify_airflow.py)
GAMMA = 1.4
R_AIR = 287.058
P_AMB_PA = 101325.0
BOOST_PSI = 18.0
PSI_TO_PA = 6894.757
P0_IN_PA = P_AMB_PA + BOOST_PSI * PSI_TO_PA  # 225,431 Pa abs
T0_IN_K = 325.15  # 52 C intercooled charge air at 18 psi
RHO0 = P0_IN_PA / (R_AIR * T0_IN_K)  # 2.415 kg/m^3
MU_AIR = 1.96e-5
A0_SOUND = math.sqrt(GAMMA * R_AIR * T0_IN_K)  # 361.5 m/s
TOTAL_MASS_FLOW_KGS = 0.2777  # 36.74 lb/min @ 7,000 RPM / 18.0 psi (98% VE)
DESIGN_RPM = 7000.0
EPSILON_WALL_M = 0.000035


# ---------------------------------------------------------------------------
# 1. Exact 3D WRC Dual-Chamber Fluid Cavity Extraction
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


def extract_wrc_fluid_cavity(params: dict) -> dict:
    """Extract exact 3D twin-chamber internal air volume bounded at TB face and Y=tip_y exits."""
    sec_in = gen.build_secondary_plenum_loft(params, is_inner=True)
    prim_in = gen.build_primary_plenum_loft(params, is_inner=True)
    slot_in = gen.build_transfer_slot_cavity(params)

    tip_y = float(params["runners"]["spigot"]["tip_y_mm"])
    runner_clip = md.Manifold.cube([1200.0, 1200.0, 1200.0], center=True).translate([0.0, tip_y + 600.0, 0.0])
    runner_bores = [
        gen.build_single_runner_components(float(xc), params)["inner_bore"] ^ runner_clip
        for xc in params["runners"]["center_x_mm"]
    ]

    # Exact TB neck + bore cavity bounded at flange face
    tb = params["throttle_body"]
    pl = params["primary_plenum"]
    cant_rad = math.radians(float(tb["forward_cant_deg"]))
    tb_axis = np.array([math.cos(cant_rad), math.sin(cant_rad), 0.0])
    yc_p = float(pl["center_y_mm"])
    zc_p = gen.primary_center_z(float(pl["cyl4_end_x_mm"]), params, is_inner=True)
    p_start = np.array([float(pl["cyl4_end_x_mm"]) - 4.0, yc_p, zc_p])
    p_flange_back = np.array([float(pl["cyl4_end_x_mm"]), yc_p, zc_p]) + tb_axis * float(tb["neck_length_mm"])
    p_flange_face = p_flange_back + tb_axis * float(tb["flange_thickness_mm"])

    n_pts = int(pl["profile_segments"])
    up_hint = np.array([0.0, 0.0, 1.0])
    bore_d = float(tb["bore_diameter_mm"])
    neck_in_rings = []
    for k in range(21):
        t = k / 20.0
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        pos = p_start + (p_flange_back + tb_axis * 4.0 - p_start) * t
        tan = np.array([1.0, 0.0, 0.0]) * (1.0 - s_t) + tb_axis * s_t
        w_in = float(pl["base_inner_width_y_mm"]) + (bore_d - float(pl["base_inner_width_y_mm"])) * s_t
        h_in = float(pl["base_inner_height_z_mm"]) + (bore_d - float(pl["base_inner_height_z_mm"])) * s_t
        r_in = float(pl["base_inner_corner_radius_mm"]) + (bore_d * 0.5 - float(pl["base_inner_corner_radius_mm"])) * s_t
        neck_in_rings.append(
            gen.ring_frame_points(pos, tan, up_hint, gen.rounded_rect_points(w_in, h_in, r_in, n_pts))
        )
    neck_in_rings.append(
        gen.ring_frame_points(
            p_flange_face + tb_axis * 6.0, tb_axis, up_hint, gen.rounded_rect_points(bore_d, bore_d, bore_d * 0.5, n_pts)
        )
    )
    tb_bore_full = gen.trimesh_to_manifold(gen.loft_closed_solid(neck_in_rings))
    tb_bore_clipped = tb_bore_full ^ _oriented_halfspace(p_flange_face, -tb_axis)

    fluid_raw = gen.m_union([sec_in, prim_in, slot_in, tb_bore_clipped, *runner_bores])
    bond_env = gen.build_interior_bond_envelope(params, wall_offset_mm=2.8)
    vanes = gen.build_turning_vanes(params, bond_env=bond_env)
    fluid_solid = fluid_raw - gen.m_union(vanes) if vanes else fluid_raw
    return {
        "fluid_solid": fluid_solid,
        "prim_inner": prim_in,
        "sec_inner": sec_in,
        "slot_inner": slot_in,
        "tb_bore": tb_bore_clipped,
        "p_flange_face": p_flange_face,
        "tb_axis": tb_axis,
        "tip_y": tip_y,
    }


# ---------------------------------------------------------------------------
# 2. Voxelization & Conservative 3D Finite-Volume Navier-Stokes Solver
# ---------------------------------------------------------------------------

def voxelize_wrc_fluid(fluid_solid: md.Manifold, params: dict, dx: float = 4.0) -> dict:
    """
    Classify 3D grid aligned both to cylinder pitch in X (4k + 2) and divider bridge in Z.
    """
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

    # Verify zero divider bridge leakage outside the transfer slot
    z_sec_top, _z_br_mid, z_prim_bot = gen._bridge_z_bounds(params)
    z_bridge_target = round((z_sec_top + 2.0) / dx) * dx
    assert z_sec_top < z_bridge_target < z_prim_bot, (
        f"Divider bridge target {z_bridge_target} not inside ({z_sec_top}, {z_prim_bot})"
    )
    zb_idx = int(np.argmin(np.abs(zs - z_bridge_target)))
    assert abs(zs[zb_idx] - z_bridge_target) < 1e-3, f"Z grid must hit {z_bridge_target:.1f} mm inside bridge"
    leak_beyond_slot = inside[:, :, zb_idx] & ((gx < -158.0) | (gx > 163.0))
    assert not np.any(leak_beyond_slot), "Bridge leakage detected outside transfer slot!"

    return {
        "dx_m": dx * 1e-3,
        "dx_mm": dx,
        "xs_mm": xs,
        "ys_mm": ys,
        "zs_mm": zs,
        "inside": inside,
    }


def _jacobi_cg(A: sp.csr_matrix, b: np.ndarray, tol: float = 1e-6, maxiter: int = 700) -> np.ndarray:
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


def solve_wrc_3d_fvm(
    grid: dict,
    params: dict,
    fluid_meta: dict,
    total_mass_flow_kgs: float = TOTAL_MASS_FLOW_KGS,
    n_picard: int = 60,
) -> dict:
    """Solve 3D steady turbulent Oseen-SIMPLE Navier-Stokes on the twin-chamber WRC domain."""
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

    p_face = fluid_meta["p_flange_face"]
    tb_axis = fluid_meta["tb_axis"]
    tip_y = fluid_meta["tip_y"]
    cyl_xs = [float(v) for v in params["runners"]["center_x_mm"]]

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

    signed_dist_tb = (pts_mm - p_face[None, :]) @ tb_axis
    r_perp_tb = np.linalg.norm((pts_mm - p_face[None, :]) - signed_dist_tb[:, None] * tb_axis[None, :], axis=1)
    inlet_cell = (
        (signed_dist_tb >= -dx_mm * 1.45)
        & (signed_dist_tb <= dx_mm * 0.1)
        & (r_perp_tb <= float(params["throttle_body"]["bore_diameter_mm"]) * 0.55)
    )

    tb_area_m2 = math.pi * 0.25 * (float(params["throttle_body"]["bore_diameter_mm"]) * 1e-3) ** 2
    u_in_mag = total_mass_flow_kgs / (RHO0 * tb_area_m2)
    u_in_vec = -tb_axis * u_in_mag
    face_area = dx_m * dx_m
    q_target = total_mass_flow_kgs / RHO0

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

    dh_ref = 0.052
    re_ref = RHO0 * max(u_in_mag, 15.0) * dh_ref / MU_AIR
    inv_sqrt_f = -1.8 * math.log10((EPSILON_WALL_M / (3.7 * dh_ref)) ** 1.11 + 6.9 / max(re_ref, 5000.0))
    f_darcy = 1.0 / (inv_sqrt_f**2)
    nu_eff = 0.0045
    dt_pseudo = 0.00016
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
        u_star = _jacobi_bicgstab(M_vel, (u / dt_pseudo) - (gpx / RHO0) + q_vol_src * u_in_vec[0], tol=1e-5, maxiter=200)
        v_star = _jacobi_bicgstab(M_vel, (v / dt_pseudo) - (gpy / RHO0) + q_vol_src * u_in_vec[1], tol=1e-5, maxiter=200)
        w_star = _jacobi_bicgstab(M_vel, (w / dt_pseudo) - (gpz / RHO0) + q_vol_src * u_in_vec[2], tol=1e-5, maxiter=200)

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
            rc_corr = -(d_f / RHO0) * ((p[c] - p[r]) / (sgn * dx_m) - 0.5 * (gp_comp[r] + gp_comp[c]))
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

        rc_out = -(d_p[om_idx] / RHO0) * ((0.0 - p[om_idx]) / (-dx_m) - gpy[om_idx])
        v_out_face = -(v_star[om_idx] + rc_out)
        div_u[om_idx] += v_out_face / dx_m

        p_corr = _jacobi_cg(L_p, -RHO0 * div_u, tol=1e-7, maxiter=700)
        v_out_divfree = v_out_face + (d_p[om_idx] / RHO0) * (p_corr[om_idx] / dx_m)

        gpc_x, gpc_y, gpc_z = calc_cell_grad(p_corr, outlet_dirichlet_zero=True)
        u = alpha_u * (u_star - (d_p / RHO0) * gpc_x) + (1.0 - alpha_u) * u
        v = alpha_u * (v_star - (d_p / RHO0) * gpc_y) + (1.0 - alpha_u) * v
        w = alpha_u * (w_star - (d_p / RHO0) * gpc_z) + (1.0 - alpha_u) * w
        p = p + alpha_p * p_corr

    om_lookup = np.full(n_cells, -1, dtype=np.int32)
    om_lookup[om_idx] = np.arange(len(om_idx), dtype=np.int32)

    speed = np.sqrt(u * u + v * v + w * w)
    mach = speed / A0_SOUND
    q_dyn = 0.5 * RHO0 * speed**2
    p_total_rel = p + q_dyn
    p0_in_mean = float(np.mean(p_total_rel[inlet_cell]))

    cyl_flows, cyl_dp_pa = [], []
    for idx in range(4):
        om = outlet_masks[idx]
        om_i = np.flatnonzero(om)
        loc_idx = om_lookup[om_i]
        v_face_exit = np.maximum(v_out_divfree[loc_idx], 0.0)
        cyl_flows.append(float(np.sum(RHO0 * v_face_exit * face_area)))
        pre_spigot = (py >= tip_y + 25.0) & (py <= tip_y + 38.0) & (np.abs(px - cyl_xs[idx]) <= 30.0)
        p0_out = float(np.mean(p_total_rel[pre_spigot])) if np.any(pre_spigot) else float(np.mean(p_total_rel[om_i]))
        cyl_dp_pa.append(max(p0_in_mean - p0_out, 0.0))

    raw_sum = sum(cyl_flows)
    mass_err_pct = abs(raw_sum - total_mass_flow_kgs) / total_mass_flow_kgs * 100.0
    flow_shares_pct = [100.0 * f / raw_sum for f in cyl_flows]
    maldist_pct = (max(flow_shares_pct) - min(flow_shares_pct)) / 25.0 * 100.0
    dp_manifold_mean_kpa = max(float(np.mean(cyl_dp_pa)), 0.0) * 1e-3

    # Slot vertical mass velocity diagnostic across Cyl 1..4 stations (+Z -> -Z down into Secondary)
    _z_st, z_br_mid, _z_pb = gen._bridge_z_bounds(params)
    slot_vy_z34 = []
    for xc in cyl_xs:
        sm = (np.abs(px - xc) <= 16.0) & (np.abs(pz - z_br_mid) <= 3.0)
        slot_vy_z34.append(round(float(-np.mean(w[sm])) if np.any(sm) else 0.0, 2))

    # Extract 3 visualization slices cleanly
    # 1) Longitudinal (X, Z) slice through transfer slot centerline
    y_slot_idx = int(np.argmin(np.abs(ys_mm - float(params["transfer_slot"]["center_y_mm"]))))
    sl_xz_mask = (jj == y_slot_idx)
    xz_vx = np.full((nx, nz), np.nan)
    xz_vz = np.full((nx, nz), np.nan)
    xz_spd = np.full((nx, nz), np.nan)
    xz_vx[ii[sl_xz_mask], kk[sl_xz_mask]] = u[sl_xz_mask]
    xz_vz[ii[sl_xz_mask], kk[sl_xz_mask]] = w[sl_xz_mask]
    xz_spd[ii[sl_xz_mask], kk[sl_xz_mask]] = speed[sl_xz_mask]

    # 2) Transverse (Y, Z) slice at Cyl 3 (X = +46.0 mm)
    x_c3_idx = int(np.argmin(np.abs(xs_mm - 46.0)))
    sl_yz_mask = (ii == x_c3_idx)
    yz_vy = np.full((ny, nz), np.nan)
    yz_vz = np.full((ny, nz), np.nan)
    yz_spd = np.full((ny, nz), np.nan)
    yz_vy[jj[sl_yz_mask], kk[sl_yz_mask]] = v[sl_yz_mask]
    yz_vz[jj[sl_yz_mask], kk[sl_yz_mask]] = w[sl_yz_mask]
    yz_spd[jj[sl_yz_mask], kk[sl_yz_mask]] = speed[sl_yz_mask]

    # 3) Runner horizontal/sloped plane slice in Secondary Chamber
    z_sec_slice = float(params["secondary_plenum"]["center_z_mm"]) - 4.0
    z_sec_idx = int(np.argmin(np.abs(zs_mm - z_sec_slice)))
    sl_xy_mask = (kk == z_sec_idx)
    xy_vx = np.full((nx, ny), np.nan)
    xy_vy = np.full((nx, ny), np.nan)
    xy_spd = np.full((nx, ny), np.nan)
    xy_vx[ii[sl_xy_mask], jj[sl_xy_mask]] = u[sl_xy_mask]
    xy_vy[ii[sl_xy_mask], jj[sl_xy_mask]] = v[sl_xy_mask]
    xy_spd[ii[sl_xy_mask], jj[sl_xy_mask]] = speed[sl_xy_mask]

    return {
        "n_fluid_cells": int(n_cells),
        "mass_conservation_error_pct": round(mass_err_pct, 2),
        "cyl_mass_flow_raw_kgs": [round(f, 5) for f in cyl_flows],
        "cyl_flow_share_pct": [round(s, 2) for s in flow_shares_pct],
        "cyl_maldistribution_spread_pct": round(maldist_pct, 2),
        "cyl_dp_total_kpa": [round(dp * 1e-3, 3) for dp in cyl_dp_pa],
        "tb_to_plenum_dp_kpa": round(dp_manifold_mean_kpa, 3),
        "tb_to_plenum_dp_psi": round(dp_manifold_mean_kpa * 0.145038, 3),
        "slot_downward_vel_cyl1to4_ms": slot_vy_z34,
        "max_mach_3d": round(float(np.max(mach)), 3),
        "max_vel_3d_ms": round(float(np.max(speed)), 1),
        "mean_tb_vel_ms": round(float(u_in_mag), 2),
        "slices": {
            "y_xz_mm": float(ys_mm[y_slot_idx]),
            "x_yz_mm": float(xs_mm[x_c3_idx]),
            "z_xy_mm": float(zs_mm[z_sec_idx]),
            "xz_vx": xz_vx, "xz_vz": xz_vz, "xz_spd": xz_spd,
            "yz_vy": yz_vy, "yz_vz": yz_vz, "yz_spd": yz_spd,
            "xy_vx": xy_vx, "xy_vy": xy_vy, "xy_spd": xy_spd,
        },
    }


# ---------------------------------------------------------------------------
# 3. Acoustic & 3-Way Comparative Plot
# ---------------------------------------------------------------------------

def render_wrc_verification_png(
    grid: dict,
    cfd: dict,
    metrics: dict,
    baselines: dict,
    out_path: Path,
):
    fig = plt.figure(figsize=(18.5, 11.2), facecolor="#f7f6f2")
    fig.suptitle(
        "2004 Ford Focus SVT Turbo (7,000 RPM @ 18.0 PSI) — Dual-Chamber WRC 3D FVM Verification & 3-Way Comparison",
        fontsize=14,
        fontweight="bold",
        y=0.975,
        color="#1a1f25",
    )
    sl = cfd["slices"]
    xs, ys, zs = grid["xs_mm"], grid["ys_mm"], grid["zs_mm"]

    # Panel 1: Longitudinal (X, Z) Flow Field through Primary Diffuser -> Slot -> Secondary Chamber
    ax1 = fig.add_subplot(2, 3, 1)
    gx, gz = np.meshgrid(xs, zs, indexing="ij")
    im1 = ax1.pcolormesh(gx, gz, sl["xz_spd"], cmap="inferno", shading="nearest", vmin=0, vmax=max(50.0, float(np.nanmax(sl["xz_spd"]))))
    plt.colorbar(im1, ax=ax1, label="Air Speed [m/s]", fraction=0.046, pad=0.04)
    stx, stz = 3, 2
    ax1.quiver(gx[::stx, ::stz], gz[::stx, ::stz], sl["xz_vx"][::stx, ::stz], sl["xz_vz"][::stx, ::stz], color="#eaf2f8", alpha=0.85, scale=550, width=0.0032)
    ax1.set_aspect("equal")
    ax1.set_title(f"1. Longitudinal Diffuser & Slot (Y = +{sl['y_xz_mm']:.0f} mm)", fontsize=10, fontweight="bold")
    ax1.set_xlabel("X: Cyl 1 (-X) to Straight TB (+X) [mm]")
    ax1.set_ylabel("Z [mm]")

    # Panel 2: Transverse (Y, Z) Flow at Cyl 3 (X = +46 mm)
    ax2 = fig.add_subplot(2, 3, 2)
    gy2, gz2 = np.meshgrid(ys, zs, indexing="ij")
    im2 = ax2.pcolormesh(gy2, gz2, sl["yz_spd"], cmap="inferno", shading="nearest", vmin=0, vmax=max(50.0, float(np.nanmax(sl["yz_spd"]))))
    plt.colorbar(im2, ax=ax2, label="Air Speed [m/s]", fraction=0.046, pad=0.04)
    st = 2
    ax2.quiver(gy2[::st, ::st], gz2[::st, ::st], sl["yz_vy"][::st, ::st], sl["yz_vz"][::st, ::st], color="#eaf2f8", alpha=0.88, scale=520, width=0.0034)
    ax2.set_aspect("equal")
    ax2.set_title(f"2. Transverse Slot -> Runner (X = +{sl['x_yz_mm']:.0f} mm)", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Y: Spigot (-Y) to Front (+Y) [mm]")
    ax2.set_ylabel("Z [mm]")

    # Panel 3: Horizontal (X, Y) Secondary Chamber -> 4 Runners Field
    ax3 = fig.add_subplot(2, 3, 3)
    gx3, gy3 = np.meshgrid(xs, ys, indexing="ij")
    im3 = ax3.pcolormesh(gx3, gy3, sl["xy_spd"], cmap="inferno", shading="nearest", vmin=0, vmax=max(45.0, float(np.nanmax(sl["xy_spd"]))))
    plt.colorbar(im3, ax=ax3, label="Air Speed [m/s]", fraction=0.046, pad=0.04)
    ax3.quiver(gx3[::3, ::3], gy3[::3, ::3], sl["xy_vx"][::3, ::3], sl["xy_vy"][::3, ::3], color="#eaf2f8", alpha=0.85, scale=420, width=0.003)
    ax3.set_aspect("equal")
    ax3.set_title(f"3. Secondary Runner Feed (Z = {sl['z_xy_mm']:.0f} mm)", fontsize=10, fontweight="bold")
    ax3.set_xlabel("X [mm]")
    ax3.set_ylabel("Y [mm]")

    # Panel 4: 3-Way Cylinder Flow Share Comparison (%)
    ax4 = fig.add_subplot(2, 3, 4)
    cyls = np.arange(1, 5)
    w_bar = 0.25
    oem_ve = baselines["oem_short_ve"]
    oem_share = [100.0 * v / sum(oem_ve) for v in oem_ve]
    s2_share = baselines["stage2_3d_share_pct"]
    wrc_share = cfd["cyl_flow_share_pct"]

    b1 = ax4.bar(cyls - w_bar, oem_share, width=w_bar, color="#7f8c8d", edgecolor="#2c3e50", label=f"OEM Plastic Short ({baselines['oem_short_spread_pct']:.2f}% 1D)")
    b2 = ax4.bar(cyls, s2_share, width=w_bar, color="#2471a3", edgecolor="#154360", label=f"Stage-2 Single ({baselines['stage2_3d_spread_pct']:.2f}% 3D)")
    b3 = ax4.bar(cyls + w_bar, wrc_share, width=w_bar, color="#c0392b", edgecolor="#641e16", label=f"WRC Dual-Chamber ({cfd['cyl_maldistribution_spread_pct']:.2f}% 3D)")
    ax4.axhline(25.0, color="#27ae60", lw=1.2, ls="--", label="Ideal 25.00%")
    all_shares = [*oem_share, *s2_share, *wrc_share]
    y_lo = min(24.1, min(all_shares) - 0.35)
    y_hi = max(25.75, max(all_shares) + 0.35)
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width() * 0.5, h + 0.025, f"{h:.2f}", ha="center", va="bottom", fontsize=7.0)
    ax4.set_xticks(cyls, [f"Cyl {i}" for i in cyls])
    ax4.set_ylim(y_lo, y_hi)
    ax4.set_ylabel("Mass-Flow Share [%]")
    ax4.set_title("4. Cylinder 1-4 Flow Balance (7,000 RPM @ 18 PSI)", fontsize=10, fontweight="bold")
    ax4.grid(True, axis="y", alpha=0.35)
    ax4.legend(fontsize=7.8, loc="lower left")

    # Panel 5: Upper-Manifold Pressure Drop (psi) & Weight (lb) Trade-Off
    ax5 = fig.add_subplot(2, 3, 5)
    names = ["OEM Plastic\nShort (Pinned)", "Stage-2 Single\n(Ø42.8 Round)", "WRC Dual-Chamber\n(Slot Diffuser)"]
    x_pos = np.arange(3)
    dps = [baselines["oem_short_dp_psi"], baselines["stage2_3d_dp_psi"], cfd["tb_to_plenum_dp_psi"]]
    colors_p = ["#7f8c8d", "#2471a3", "#c0392b"]
    bars_dp = ax5.bar(x_pos, dps, width=0.52, color=colors_p, edgecolor="#1c2833")
    for bar, val in zip(bars_dp, dps):
        ax5.text(bar.get_x() + bar.get_width() * 0.5, val + 0.015, f"{val:.3f} psi", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax5.set_xticks(x_pos, names)
    ax5.set_ylim(0.0, max(dps) * 1.34)
    ax5.set_ylabel("Upper-Manifold Total Pressure Drop [psi]")
    ax5.set_title("5. Upper-Manifold Pumping Loss (7,000 RPM @ 18 PSI)", fontsize=10, fontweight="bold")
    ax5.grid(True, axis="y", alpha=0.35)
    ax5.text(
        0.5, 0.96,
        f"Cascaded scoop-vane WRC twin chamber\n(3D Spread = {cfd['cyl_maldistribution_spread_pct']:.2f}% | ΔP = {cfd['tb_to_plenum_dp_psi']:.3f} vs {baselines['stage2_3d_dp_psi']:.3f} psi)",
        transform=ax5.transAxes, ha="center", va="top", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.32", facecolor="#ffffff", edgecolor="#cccccc"),
    )

    # Panel 6: Packaging, Mass & Acoustics Summary
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis("off")
    rows = [
        ("Plenum Volume [L]", f"{baselines['oem_vol_l']:.2f}", f"{baselines['stage2_vol_l']:.3f}", f"{metrics['plenum_vol_l']:.3f}"),
        ("Total Weight [lb]", f"{baselines['oem_mass_lb']:.2f}", f"{baselines['stage2_mass_lb']:.2f}", f"{metrics['est_split_mass_lb']:.2f}"),
        ("3D Spread [%]", f"{baselines['oem_short_spread_pct']:.2f} (1D)", f"{baselines['stage2_3d_spread_pct']:.2f}", f"{cfd['cyl_maldistribution_spread_pct']:.2f}"),
        ("Upper ΔP [psi]", f"{baselines['oem_short_dp_psi']:.3f} (1D)", f"{baselines['stage2_3d_dp_psi']:.3f}", f"{cfd['tb_to_plenum_dp_psi']:.3f}"),
        ("Hood Roof (+Z) [mm]", "~118 (w/ IMRC)", "61.0 (122.5 span)", f"{metrics['max_z_above_datum_mm']:.1f} ({metrics['total_z_span_mm']:.1f} span)"),
        ("Firewall (+Y) [mm]", "~55", "70.2", f"{metrics['max_y_firewall_mm']:.1f}"),
        ("Helmholtz 3rd [RPM]", "4,207", "4,785", f"{metrics['sec_helmholtz_3rd_rpm']:.0f}"),
        ("CC2 256mm Bed Fit", "N/A (OEM)", "Yes (229.5)", f"Yes ({metrics['max_print_z_mm']:.1f})"),
    ]
    tbl = ax6.table(
        cellText=[[r[1], r[2], r[3]] for r in rows],
        rowLabels=[r[0] for r in rows],
        colLabels=["OEM Short", "Stage-2 Single", "WRC Sloped"],
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.8)
    tbl.scale(1.05, 1.52)
    for (r_i, c_i), cell in tbl.get_celld().items():
        if r_i == 0 or c_i == -1:
            cell.set_facecolor("#d6eaf8" if r_i == 0 else "#f2f4f4")
            cell.set_text_props(weight="bold")
    ax6.set_title("6. Packaging, Weight, Acoustics & Print Fit", fontsize=10.5, fontweight="bold", pad=10)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main Verification Workflow
# ---------------------------------------------------------------------------

def tune_turning_vanes(params: dict) -> dict:
    """Closed-loop 3D FVM calibration at n_picard=55 for the sloped-down Secondary geometry."""
    import copy
    h4 = float(params["turning_vanes"]["vanes"][0]["primary_height_mm"])
    zb4 = float(params["turning_vanes"]["vanes"][0]["z_bottom_mm"])
    h3 = float(params["turning_vanes"]["vanes"][1]["primary_height_mm"])
    best_cfg = (h4, zb4, h3)
    best_res = None

    print("=== Closed-Loop Turning-Vane 3D FVM Calibration (n_picard=55) ===")
    for it_tune in range(1, 6):
        cand_p = copy.deepcopy(params)
        cand_p["turning_vanes"]["vanes"][0]["primary_height_mm"] = round(h4, 2)
        cand_p["turning_vanes"]["vanes"][0]["z_bottom_mm"] = round(zb4, 2)
        cand_p["turning_vanes"]["vanes"][1]["primary_height_mm"] = round(h3, 2)
        fmeta = extract_wrc_fluid_cavity(cand_p)
        gr = voxelize_wrc_fluid(fmeta["fluid_solid"], cand_p, dx=4.0)
        res = solve_wrc_3d_fvm(gr, cand_p, fmeta, total_mass_flow_kgs=TOTAL_MASS_FLOW_KGS, n_picard=55)
        s1, s2, s3, s4 = res["cyl_flow_share_pct"]
        spread = res["cyl_maldistribution_spread_pct"]
        print(
            f"  Iter {it_tune}: (h4={h4:5.2f}, zb4={zb4:6.2f}, h3={h3:5.2f}) mm -> "
            f"Shares={[s1, s2, s3, s4]} | Spread={spread:.2f}% | dP={res['tb_to_plenum_dp_psi']:.3f} psi"
        )
        if best_res is None or spread < best_res["cyl_maldistribution_spread_pct"]:
            best_res = res
            best_cfg = (round(h4, 2), round(zb4, 2), round(h3, 2))
        if spread <= 0.45:
            break
        h4 = float(np.clip(h4 + 4.5 * (25.0 - s4), 6.0, 48.0))
        zb4 = float(np.clip(zb4 - 3.5 * (25.0 - s4), -85.0, -45.0))
        h3 = float(np.clip(h3 + 4.0 * (25.0 - s3), 2.0, 32.0))

    h4_opt, zb4_opt, h3_opt = best_cfg
    print(f"Selected lowest-spread vane config: h4={h4_opt}, zb4={zb4_opt}, h3={h3_opt} mm (Spread={best_res['cyl_maldistribution_spread_pct']:.2f}%)")
    params["turning_vanes"]["vanes"][0]["primary_height_mm"] = h4_opt
    params["turning_vanes"]["vanes"][0]["z_bottom_mm"] = zb4_opt
    params["turning_vanes"]["vanes"][1]["primary_height_mm"] = h3_opt
    PARAMS_PATH.write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    return params


def main():
    import sys
    t0 = time.perf_counter()
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    if "--tune" in sys.argv:
        params = tune_turning_vanes(params)
        gen.main()
    manifest = json.loads((STL_DIR / "manifest.json").read_text(encoding="utf-8"))

    # Read-only baseline loads from sibling cad/intake_manifold/
    orig_av = json.loads((ORIG_DIR / "stl" / "airflow_verification.json").read_text(encoding="utf-8"))
    orig_fc = json.loads((ORIG_DIR / "stl" / "factory_comparison.json").read_text(encoding="utf-8"))

    baselines = {
        "oem_short_ve": orig_fc["summary_7000rpm"]["oem_dsi_short"]["cyl_ve_7000"],
        "oem_short_spread_pct": orig_fc["summary_7000rpm"]["oem_dsi_short"]["ve_spread_7000_pct"],
        "oem_short_dp_psi": orig_fc["summary_7000rpm"]["oem_dsi_short"]["dp_7000_psi"],
        "oem_vol_l": orig_fc["hardware_comparison"]["oem_upper_dsi"]["plenum_volume_liters"],
        "oem_mass_lb": orig_fc["hardware_comparison"]["oem_upper_dsi"]["estimated_mass_lb"],
        "stage2_3d_share_pct": orig_av["boost_optimized"]["cfd_3d"]["cyl_flow_share_pct"],
        "stage2_3d_spread_pct": orig_av["boost_optimized"]["cfd_3d"]["cyl_maldistribution_spread_pct"],
        "stage2_3d_dp_psi": orig_av["boost_optimized"]["cfd_3d"]["tb_to_plenum_dp_psi"],
        "stage2_vol_l": orig_av["boost_optimized"]["cad_audit"]["bare_plenum_volume_liters"],
        "stage2_mass_lb": orig_fc["hardware_comparison"]["custom_stage2_round"]["estimated_mass_lb"],
    }

    fluid_meta = extract_wrc_fluid_cavity(params)
    grid = voxelize_wrc_fluid(fluid_meta["fluid_solid"], params, dx=4.0)
    cfd = solve_wrc_3d_fvm(grid, params, fluid_meta, total_mass_flow_kgs=TOTAL_MASS_FLOW_KGS, n_picard=75)

    # Secondary chamber acoustic Helmholtz & dual-chamber compliance estimates
    sec_vol_m3 = manifest["secondary_chamber_volume_liters"] * 1e-3
    sp = params["runners"]["spigot"]
    d_in = (float(sp["outer_width_mm"]) - 2.0 * float(sp["wall_thickness_mm"])) * 1e-3
    a_exit = math.pi * 0.25 * (d_in**2)
    l_eff = 0.243 + 0.85 * d_in
    f_helm_sec = (A0_SOUND / (2.0 * math.pi)) * math.sqrt((a_exit * 1.04) / (sec_vol_m3 * l_eff))
    rpm_helm_sec = f_helm_sec * 120.0 / 3.0

    # Weight estimate (PPA-CF 1.26 g/cm3 + 0.22 kg for 8x M6, 2x dowels, Viton O-ring, barbs)
    split_vol_cm3 = (
        manifest["parts"]["svt_wrc_manifold_split_left_print_oriented"]["solid_volume_cm3"]
        + manifest["parts"]["svt_wrc_manifold_split_right_print_oriented"]["solid_volume_cm3"]
    )
    est_mass_kg = split_vol_cm3 * 1e-3 * 1.26 + 0.22
    est_mass_lb = est_mass_kg * 2.20462

    right_1pc_info = manifest["parts"]["svt_wrc_manifold_1piece_full"]
    right_sp_info = manifest["parts"]["svt_wrc_manifold_split_right_cyl3_4_tb"]
    metrics = {
        "plenum_vol_l": manifest["plenum_internal_volume_liters"],
        "primary_vol_l": manifest["primary_chamber_volume_liters"],
        "secondary_vol_l": manifest["secondary_chamber_volume_liters"],
        "split_solid_vol_cm3": round(split_vol_cm3, 2),
        "est_split_mass_kg": round(est_mass_kg, 2),
        "est_split_mass_lb": round(est_mass_lb, 2),
        "sec_helmholtz_freq_hz": round(f_helm_sec, 1),
        "sec_helmholtz_3rd_rpm": round(rpm_helm_sec, 0),
        "max_z_above_datum_mm": round(float(right_1pc_info["bounds_max_mm"][2]), 1),
        "total_z_span_mm": round(float(right_1pc_info["extents_mm"][2]), 1),
        "max_y_firewall_mm": round(float(right_sp_info["bounds_max_mm"][1]), 1),
        "max_print_z_mm": max(
            manifest["parts"]["svt_wrc_manifold_split_left_print_oriented"]["extents_mm"][2],
            manifest["parts"]["svt_wrc_manifold_split_right_print_oriented"]["extents_mm"][2],
        ),
    }

    render_wrc_verification_png(grid, cfd, metrics, baselines, FITMENT_DIR / "03_wrc_airflow_verification.png")

    report = {
        "operating_point": {
            "rpm": DESIGN_RPM,
            "boost_psi": BOOST_PSI,
            "iat_c": round(T0_IN_K - 273.15, 1),
            "mass_flow_kgs": TOTAL_MASS_FLOW_KGS,
            "mass_flow_lbmin": round(TOTAL_MASS_FLOW_KGS * 132.277, 2),
        },
        "cfd_3d": {k: v for k, v in cfd.items() if k != "slices"},
        "packaging_and_acoustics": metrics,
        "baselines": baselines,
        "runtime_seconds": round(time.perf_counter() - t0, 2),
    }
    (STL_DIR / "wrc_airflow_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"WRC 3D FVM Verification completed in {report['runtime_seconds']} s")
    print(f"  Cells: {cfd['n_fluid_cells']} | Mass Err: {cfd['mass_conservation_error_pct']}%")
    print(f"  Cyl Flow Share [%]: {cfd['cyl_flow_share_pct']} | 3D Spread: {cfd['cyl_maldistribution_spread_pct']}%")
    print(f"  Upper dP: {cfd['tb_to_plenum_dp_kpa']} kPa ({cfd['tb_to_plenum_dp_psi']} psi)")
    print(f"  Slot downward velocity @ Z=34mm [Cyl 1..4 m/s]: {cfd['slot_downward_vel_cyl1to4_ms']}")
    print(f"  Total Split Weight: {metrics['est_split_mass_lb']:.2f} lb ({metrics['est_split_mass_kg']:.2f} kg)")


if __name__ == "__main__":
    main()
