#!/usr/bin/env python3
"""
Parametric 3D-Printable Stage-2 V2 (Engine-Bay Packaged) Intake Manifold Generator
for 2004 Ford Focus SVT (2.0L Zetec Turbo).

Key Engine-Bay Packaging & Codex Review Updates vs V1:
  1. Dropped Plenum (-68 mm below runner boot centers): keeps plenum, center split flange,
     top NPT vacuum/boost bosses & check-valve barbs safely beneath the hanging OEM FRPS,
     Aeromotive FPR, and FocusSport strut tower bar.
  2. Swept Forward & Upward TB Neck (32 deg toward -Y front + 14 deg upward pitch): clears the
     brake fluid reservoir and coil pack while aligning cleanly toward the charge pipe.
  3. Integrated Twin-M6 Throttle/Cruise Cable Bracket Boss on upper-front TB neck shoulder.
  4. Outward-Flared 2-Bolt Ford IACV Pedestal with +Y rear 1/4-18 NPT charge-pipe supply tap
     and verified >= 4.5 mm solid floor across all 468 sampled rays.
  5. Conformal internal bellmouth quarter-circle filleting eliminating sharp < 2 mm internal
     junction lips across Cylinders 1-4 (verified via 72-ray root wall audit).

Outputs (inside cad/intake_manifold_v2/):
  stl/svt_intake_manifold_v2_1piece_full.stl
  stl/svt_intake_manifold_v2_split_left_cyl1_2.stl
  stl/svt_intake_manifold_v2_split_right_cyl3_4_tb.stl
  stl/svt_intake_manifold_v2_split_left_print_oriented.stl
  stl/svt_intake_manifold_v2_split_right_print_oriented.stl
  stl/svt_v2_runner_boot_fit_gauge.stl
  stl/svt_v2_tb_flange_fit_gauge.stl
  stl/svt_v2_iacv_flange_fit_gauge.stl
  stl/svt_v2_alignment_dowel_pins.stl
  stl/manifest.json
  fitment/01_intake_manifold_v2_overview.png
  fitment/02_interfaces_1to1_template_v2.svg
  fitment/05_exterior_transitions_closeup.png
  fitment/06_bellmouth_internal_sections.png
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import manifold3d as md
import matplotlib

matplotlib.use("Agg")
from matplotlib.collections import LineCollection
from matplotlib.colors import LightSource
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon as ShapelyPolygon
import trimesh

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_v2_parameters.json"
STL_DIR = ROOT / "stl"
FITMENT_DIR = ROOT / "fitment"


# ---------------------------------------------------------------------------
# Mesh & Manifold3D Geometry Primitives
# ---------------------------------------------------------------------------

def rounded_rect_points(width: float, height: float, radius: float, total_pts: int) -> np.ndarray:
    """
    Return (total_pts, 2) CCW points for a centered rounded rectangle.
    Uses open-interval corner sampling to guarantee zero duplicate vertices even
    when radius == width/2 == height/2 (circle).
    """
    assert total_pts % 4 == 0 and total_pts >= 16, "total_pts must be a multiple of 4 >= 16"
    per_corner = total_pts // 4
    r = min(radius, width * 0.5 - 1e-4, height * 0.5 - 1e-4)
    r = max(r, 0.2)
    pts = []
    corners = [
        (width * 0.5 - r, height * 0.5 - r),
        (-(width * 0.5 - r), height * 0.5 - r),
        (-(width * 0.5 - r), -(height * 0.5 - r)),
        (width * 0.5 - r, -(height * 0.5 - r)),
    ]
    for c_idx, (cx, cy) in enumerate(corners):
        angles = np.linspace(c_idx * 90.0 + 0.25, (c_idx + 1) * 90.0 - 0.25, per_corner)
        for a in np.radians(angles):
            pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return np.asarray(pts, dtype=np.float64)


def ellipse_points(width: float, height: float, total_pts: int = 64) -> np.ndarray:
    """Generate (N, 2) CCW points for a smooth ellipse of full extents `width` x `height`."""
    angles = np.linspace(0.0, 2.0 * math.pi, total_pts, endpoint=False)
    return np.column_stack([0.5 * width * np.cos(angles), 0.5 * height * np.sin(angles)]).astype(np.float64)


def ring_frame_points(
    center: np.ndarray,
    tangent: np.ndarray,
    up_hint: np.ndarray,
    profile_uv: np.ndarray,
) -> np.ndarray:
    """Embed a 2D (N, 2) profile onto a right-handed 3D frame orthogonal to `tangent`."""
    t_hat = tangent / np.linalg.norm(tangent)
    u_axis = np.cross(up_hint, t_hat)
    if np.linalg.norm(u_axis) < 1e-6:
        fallback = np.array([1.0, 0.0, 0.0]) if abs(t_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u_axis = np.cross(fallback, t_hat)
    u_axis = u_axis / np.linalg.norm(u_axis)
    v_axis = np.cross(t_hat, u_axis)
    v_axis = v_axis / np.linalg.norm(v_axis)
    return center[None, :] + profile_uv[:, 0:1] * u_axis[None, :] + profile_uv[:, 1:2] * v_axis[None, :]


def loft_closed_solid(rings: list[np.ndarray]) -> trimesh.Trimesh:
    """Loft a sequence of 3D rings (shape (N, 3)) into a closed, watertight Trimesh."""
    n_rings = len(rings)
    n_pts = rings[0].shape[0]
    assert n_rings >= 2
    for r in rings:
        assert r.shape == (n_pts, 3)

    verts = list(np.vstack(rings))
    faces: list[list[int]] = []
    for k in range(n_rings - 1):
        base0 = k * n_pts
        base1 = (k + 1) * n_pts
        for i in range(n_pts):
            j = (i + 1) % n_pts
            faces.append([base0 + i, base0 + j, base1 + j])
            faces.append([base0 + i, base1 + j, base1 + i])

    c_start_idx = len(verts)
    verts.append(rings[0].mean(axis=0))
    for i in range(n_pts):
        faces.append([c_start_idx, (i + 1) % n_pts, i])

    c_end_idx = len(verts)
    verts.append(rings[-1].mean(axis=0))
    last_base = (n_rings - 1) * n_pts
    for i in range(n_pts):
        faces.append([c_end_idx, last_base + i, last_base + ((i + 1) % n_pts)])

    mesh = trimesh.Trimesh(vertices=np.asarray(verts, dtype=np.float64), faces=np.asarray(faces, dtype=np.int64), process=True)
    mesh.fix_normals()
    assert mesh.is_watertight, "Lofted mesh is not watertight"
    assert mesh.is_volume, "Lofted mesh is not a valid closed volume"
    return mesh


def trimesh_to_manifold(mesh: trimesh.Trimesh) -> md.Manifold:
    m = md.Mesh(
        vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
        tri_verts=np.asarray(mesh.faces, dtype=np.uint32),
    )
    solid = md.Manifold(m)
    assert solid.status() == md.Error.NoError, f"Manifold conversion error: {solid.status()}"
    return solid


def manifold_to_trimesh(solid: md.Manifold) -> trimesh.Trimesh:
    assert solid.status() == md.Error.NoError, f"Manifold error: {solid.status()}"
    m = solid.to_mesh()
    return trimesh.Trimesh(
        vertices=np.asarray(m.vert_properties[:, :3], dtype=np.float64),
        faces=np.asarray(m.tri_verts, dtype=np.int64),
        process=False,
    )


def m_union(solids: Iterable[md.Manifold]) -> md.Manifold:
    return md.Manifold.batch_boolean(list(solids), md.OpType.Add)


def m_diff(base: md.Manifold, cutters: Iterable[md.Manifold]) -> md.Manifold:
    cutter_list = list(cutters)
    if not cutter_list:
        return base
    combined_cutter = m_union(cutter_list) if len(cutter_list) > 1 else cutter_list[0]
    return base - combined_cutter


def make_rounded_prism(
    width: float,
    height: float,
    radius: float,
    length: float,
    segments: int = 64,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    axis: str = "x",
) -> md.Manifold:
    """Extrude a centered rounded rectangle along 'x', 'y', or 'z'."""
    uv = rounded_rect_points(width, height, radius, segments)
    solid = md.Manifold.extrude(md.CrossSection([uv.tolist()]), length).translate([0.0, 0.0, -length * 0.5])
    if axis == "x":
        solid = solid.rotate([0.0, 0.0, 90.0]).rotate([0.0, 90.0, 0.0])
    elif axis == "y":
        solid = solid.rotate([-90.0, 0.0, 0.0])
    elif axis != "z":
        raise ValueError(f"Unsupported axis {axis}")
    if center != (0.0, 0.0, 0.0):
        solid = solid.translate(list(center))
    return solid


def make_cylinder_along(p0: np.ndarray, p1: np.ndarray, radius: float, segments: int = 48) -> md.Manifold:
    """Create a cylinder spanning from 3D point p0 to p1."""
    vec = p1 - p0
    length = float(np.linalg.norm(vec))
    assert length > 1e-4
    mesh = manifold_to_trimesh(md.Manifold.cylinder(length, radius, radius, circular_segments=segments, center=True))
    mesh.apply_transform(trimesh.geometry.align_vectors(np.array([0.0, 0.0, 1.0]), vec / length))
    mesh.apply_translation((p0 + p1) * 0.5)
    return trimesh_to_manifold(mesh)


# ---------------------------------------------------------------------------
# Parametric Plenum SDF & Curves
# ---------------------------------------------------------------------------

def plenum_area_scale(x: float, params: dict) -> float:
    p = params["plenum"]
    x0 = float(p["cyl1_end_x_mm"])
    x1 = float(p["cyl4_end_x_mm"])
    r_cyl1 = float(p["taper_cyl1_area_ratio"])
    r_split = p.get("split_x_area_ratio")
    if r_split is None:
        t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
        return float(r_cyl1 + (1.0 - r_cyl1) * t)
    r_split = float(r_split)
    x_split = float(params.get("center_split", {}).get("split_x_mm", 0.0))
    if p.get("taper_curve_smooth", False) and (x0 < x_split < x1) and (r_cyl1 < r_split < 1.0):
        t = float(np.clip((x - x0) / (x1 - x0), 0.0, 1.0))
        t_s = (x_split - x0) / (x1 - x0)
        exponent = math.log((1.0 - r_split) / (1.0 - r_cyl1)) / math.log(1.0 - t_s)
        return float(r_cyl1 + (1.0 - r_cyl1) * (1.0 - (1.0 - t) ** exponent))
    if x <= x_split:
        t = np.clip((x - x0) / (x_split - x0), 0.0, 1.0)
        return float(r_cyl1 + (r_split - r_cyl1) * t)
    t = np.clip((x - x_split) / (x1 - x_split), 0.0, 1.0)
    return float(r_split + (1.0 - r_split) * t)


def _rounded_rect_sdf_2d(y: float, z: float, w: float, h: float, r: float) -> float:
    r_c = min(r, 0.5 * min(w, h) - 1e-3)
    qx = abs(y) - (0.5 * w - r_c)
    qy = abs(z) - (0.5 * h - r_c)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r_c


def _plenum_sdf(pt: np.ndarray, params: dict, use_outer: bool) -> float:
    p = params["plenum"]
    wall = float(p["wall_thickness_mm"]) if use_outer else 0.0
    w_base = float(p["inner_width_y_mm"]) + 2.0 * wall
    h_base = float(p["inner_height_z_mm"]) + 2.0 * wall
    r_base = float(p["inner_corner_radius_mm"]) + wall
    x_clamped = float(np.clip(pt[0], p["cyl1_end_x_mm"], p["cyl4_end_x_mm"]))
    scale = math.sqrt(plenum_area_scale(x_clamped, params))
    return _rounded_rect_sdf_2d(float(pt[1]), float(pt[2]), w_base * scale, h_base * scale, r_base * scale)


def _plenum_sdf_and_normal(pt: np.ndarray, params: dict, use_outer: bool) -> tuple[float, np.ndarray]:
    d0 = _plenum_sdf(pt, params, use_outer)
    eps = 0.2
    g = np.array(
        [
            (_plenum_sdf(pt + np.array([eps, 0.0, 0.0]), params, use_outer) - d0) / eps,
            (_plenum_sdf(pt + np.array([0.0, eps, 0.0]), params, use_outer) - d0) / eps,
            (_plenum_sdf(pt + np.array([0.0, 0.0, eps]), params, use_outer) - d0) / eps,
        ],
        dtype=np.float64,
    )
    n_len = float(np.linalg.norm(g))
    if n_len < 1e-8:
        return d0, np.array([0.0, -1.0, 0.0], dtype=np.float64)
    return d0, g / n_len


def plenum_outer_sdf_and_normal(pt: np.ndarray, params: dict) -> tuple[float, np.ndarray]:
    return _plenum_sdf_and_normal(pt, params, use_outer=True)


def plenum_inner_sdf_and_normal(pt: np.ndarray, params: dict) -> tuple[float, np.ndarray]:
    return _plenum_sdf_and_normal(pt, params, use_outer=False)


def build_plenum_loft(params: dict, is_inner: bool) -> md.Manifold:
    """Build either the outer plenum shell or inner plenum cavity with Cyl 1 ellipsoidal dome."""
    p = params["plenum"]
    wall = p["wall_thickness_mm"]
    w_base = p["inner_width_y_mm"] + (0.0 if is_inner else 2.0 * wall)
    h_base = p["inner_height_z_mm"] + (0.0 if is_inner else 2.0 * wall)
    r_base = p["inner_corner_radius_mm"] + (0.0 if is_inner else wall)
    n_pts = p["profile_segments"]

    x_dome_tip = p["cyl1_end_x_mm"] - (p["cyl1_dome_length_mm"] - (wall if is_inner else 0.0))
    x_cyl1 = p["cyl1_end_x_mm"]
    x_cyl4 = float(p["cyl4_end_x_mm"])

    rings: list[np.ndarray] = []
    dome_len = x_cyl1 - x_dome_tip
    dome_steps = int(p.get("cyl1_dome_steps", 44))
    thetas = np.linspace(0.04, math.pi * 0.5, dome_steps, endpoint=False)
    s_cyl1 = math.sqrt(p["taper_cyl1_area_ratio"])
    for th in thetas:
        x = x_cyl1 - dome_len * math.cos(th)
        ds = math.sin(th) * s_cyl1
        uv = rounded_rect_points(w_base * ds, h_base * ds, r_base * ds, n_pts)
        rings.append(np.column_stack([np.full(n_pts, x), uv[:, 0], uv[:, 1]]))

    xs = np.linspace(x_cyl1, x_cyl4, p["axial_segments"])
    x_split = float(params.get("center_split", {}).get("split_x_mm", 0.0))
    if p.get("split_x_area_ratio") is not None and x_cyl1 < x_split < x_cyl4:
        if not np.any(np.isclose(xs, x_split, atol=1e-4)):
            xs = np.sort(np.append(xs, x_split))
    for x in xs:
        s = math.sqrt(plenum_area_scale(float(x), params))
        uv = rounded_rect_points(w_base * s, h_base * s, r_base * s, n_pts)
        rings.append(np.column_stack([np.full(n_pts, float(x)), uv[:, 0], uv[:, 1]]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def bezier_point_and_tangent(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float):
    u = 1.0 - t
    pt = (u**3) * p0 + 3 * (u**2) * t * p1 + 3 * u * (t**2) * p2 + (t**3) * p3
    tan = 3 * (u**2) * (p1 - p0) + 6 * u * t * (p2 - p1) + 3 * (t**2) * (p3 - p2)
    return pt, tan


def tb_neck_bezier_points(params: dict) -> tuple[np.ndarray, ...]:
    """
    Return cubic-Bezier control points and endpoints for the 3D swept TB neck.
    Sweeps forward (-Y, toward head/charge pipe) and upward (+Z) from cyl4_end_x_mm.
    """
    tb = params["throttle_body"]
    pl = params["plenum"]
    x_start = float(pl["cyl4_end_x_mm"])
    p_start = np.array([x_start, 0.0, 0.0])

    if "forward_toward_head_deg" in tb:
        yaw = math.radians(float(tb["forward_toward_head_deg"]))
        pitch = math.radians(float(tb.get("upward_pitch_deg", 0.0)))
        tb_axis = np.array([math.cos(yaw) * math.cos(pitch), -math.sin(yaw) * math.cos(pitch), math.sin(pitch)])
        tb_axis /= np.linalg.norm(tb_axis)
        off = np.asarray(tb["flange_back_offset_mm"], dtype=np.float64)
        p_flange_back = p_start + off
        chord_scale_0 = 0.42
    else:
        cant_rad = math.radians(float(tb["forward_cant_deg"]))
        tb_axis = np.array([math.cos(cant_rad), math.sin(cant_rad), 0.0])
        p_flange_back = p_start + tb_axis * float(tb["neck_length_mm"])
        chord_scale_0 = 0.38

    p_flange_face = p_flange_back + tb_axis * float(tb["flange_thickness_mm"])
    p_neck_end = p_flange_back + tb_axis * 4.0
    chord = float(np.linalg.norm(p_neck_end - p_start))
    c0 = p_start + np.array([1.0, 0.0, 0.0]) * (0.36 * chord)
    c1 = p_neck_end - tb_axis * (0.36 * chord)
    return p_start, c0, c1, p_neck_end, p_flange_back, p_flange_face, tb_axis


def runner_bezier_points(x_center: float, params: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (p_bm_tip, inlet_dir, p0, p1, p2, p3) for a dropped-plenum rising runner at `x_center`."""
    r_cfg = params["runners"]
    sp = r_cfg["spigot"]
    sw = r_cfg["sweep"]
    bm = r_cfg["bellmouth"]
    wall_flush = bool(bm.get("wall_flush_bellmouth", False))
    cyl_idx = min(range(len(r_cfg["center_x_mm"])), key=lambda idx: abs(r_cfg["center_x_mm"][idx] - x_center))
    scoop_angles = bm.get("axial_entry_angles_deg", [0.0, 0.0, 0.0, 0.0])
    alpha_x_deg = float(scoop_angles[cyl_idx]) if (wall_flush and cyl_idx < len(scoop_angles)) else 0.0
    ax_rad = math.radians(alpha_x_deg)
    el_rad = math.radians(float(sw.get("entry_elevation_deg", 32.0)))

    # Positive +Z component rises from dropped Z=0 plenum toward Z=+68 mm boots
    inlet_dir = np.array([
        -math.sin(ax_rad),
        -math.cos(el_rad) * math.cos(ax_rad),
        math.sin(el_rad) * math.cos(ax_rad),
    ])
    s_x = math.sqrt(plenum_area_scale(x_center, params))
    y_plenum_front_in = -0.5 * float(params["plenum"]["inner_width_y_mm"]) * s_x
    z_entry = float(sw.get("plenum_entry_z_mm", 10.0)) * s_x
    p_bm_tip = np.array([x_center + 14.0 * math.sin(ax_rad), y_plenum_front_in + 9.0, z_entry])
    p0 = p_bm_tip + inlet_dir * 18.0
    sweep_end_y = float(sp["tip_y_mm"]) + float(sp["land_length_mm"])
    p3 = np.array([x_center, sweep_end_y, float(sp["center_z_mm"])])
    p1 = p0 + inlet_dir * 30.0
    p2 = p3 + np.array([0.0, 38.0, 0.0])
    return p_bm_tip, inlet_dir, p0, p1, p2, p3


# ---------------------------------------------------------------------------
# Sub-Assemblies
# ---------------------------------------------------------------------------

def build_single_runner_components(x_center: float, params: dict) -> dict[str, md.Manifold]:
    """
    Build one runner's outer skin (with C^inf conformal root fillet), optional protruding
    bellmouth outer, and continuous conformal quarter-circle bellmouth inner bore.
    """
    r_cfg = params["runners"]
    sp = r_cfg["spigot"]
    sw = r_cfg["sweep"]
    bm = r_cfg["bellmouth"]
    n_pts = sw["profile_segments"]
    wall = sp["wall_thickness_mm"]

    sp_w_out = sp["outer_width_mm"]
    sp_h_out = sp["outer_height_mm"]
    sp_r_out = sp["corner_radius_mm"]
    sp_w_in = sp_w_out - 2.0 * wall
    sp_h_in = sp_h_out - 2.0 * wall
    sp_r_in = sp_r_out - wall

    wall_flush = bool(bm.get("wall_flush_bellmouth", False))
    entry_d = sw["plenum_entry_diameter_mm"]
    entry_w_in = (entry_d + 0.4) if wall_flush else entry_d
    entry_h_in = (entry_d - 4.2) if wall_flush else (entry_d - 6.0)
    entry_r_in = entry_h_in * 0.48
    entry_wall = max(wall, 6.5)
    entry_w_out = entry_w_in + 2.0 * entry_wall
    entry_h_out = entry_h_in + 2.0 * entry_wall

    tip_y = sp["tip_y_mm"]
    sweep_end_y = tip_y + sp["land_length_mm"]
    sp_z = sp["center_z_mm"]

    p_bm_tip, inlet_dir, p0, p1, p2, p3 = runner_bezier_points(x_center, params)
    throat_len = float(np.linalg.norm(p0 - p_bm_tip))

    up_hint = np.array([0.0, 0.0, 1.0])
    n_loft = sw["loft_segments"]
    bm_flare = bm["flare_radial_mm"]
    s_x = math.sqrt(plenum_area_scale(x_center, params))

    def _sdf_fillet_ring(
        ring_pts: np.ndarray,
        uv: np.ndarray,
        tangent: np.ndarray,
        sdf_fn,
        r_base_arr: np.ndarray | float,
        f_wt: float,
        inner_mode: bool,
    ) -> np.ndarray:
        if f_wt <= 1e-4:
            return ring_pts
        t_hat = tangent / np.linalg.norm(tangent)
        u_ax = np.cross(up_hint, t_hat)
        if np.linalg.norm(u_ax) < 1e-6:
            u_ax = np.array([1.0, 0.0, 0.0])
        u_ax /= np.linalg.norm(u_ax)
        v_ax = np.cross(t_hat, u_ax)
        v_ax /= np.linalg.norm(v_ax)

        out = ring_pts.copy()
        for idx in range(len(out)):
            r_loc = float(r_base_arr[idx]) if isinstance(r_base_arr, np.ndarray) else float(r_base_arr)
            p_base = out[idx]
            d, n_pl = sdf_fn(p_base, params)
            if d >= r_loc:
                continue
            n_rad = uv[idx, 0] * u_ax + uv[idx, 1] * v_ax
            nr_len = float(np.linalg.norm(n_rad))
            if nr_len < 1e-6:
                continue
            n_rad /= nr_len
            t_surf = n_rad - float(np.dot(n_rad, n_pl)) * n_pl
            ts_len = float(np.linalg.norm(t_surf))
            t_surf = (t_surf / ts_len) if ts_len > 1e-6 else n_rad

            if inner_mode:
                if d >= 0.0:
                    u_c = 1.0 - d / r_loc
                    delta_t = f_wt * r_loc * (1.0 - math.sqrt(max(0.0, 1.0 - u_c * u_c)))
                    p_tang = p_base + delta_t * t_surf
                    d_tang, n_tang = sdf_fn(p_tang, params)
                    d_target = d - f_wt * 0.25 * (u_c**3)
                else:
                    delta_t = f_wt * (r_loc + 0.35 * (-d))
                    p_tang = p_base + delta_t * t_surf
                    d_tang, n_tang = sdf_fn(p_tang, params)
                    d_target = d - 0.25 * f_wt
            else:
                u_c = float(np.clip(1.0 - max(d, 0.0) / r_loc, 0.0, 1.0))
                fade_in = float(np.clip((d + 6.0) / 6.0, 0.0, 1.0))
                fade_in = f_wt * fade_in * fade_in * (3.0 - 2.0 * fade_in)
                delta_t = fade_in * r_loc * (1.0 - math.sqrt(max(0.0, 1.0 - (0.82 * u_c) ** 2)))
                p_tang = p_base + delta_t * t_surf
                d_tang, n_tang = sdf_fn(p_tang, params)
                d_target = d - fade_in * 0.45 * u_c
            out[idx] = p_tang + (d_target - d_tang) * n_tang
        return out

    # 1) Outer runner skin
    outer_rings: list[np.ndarray] = []
    r_f_out = float(bm.get("exterior_fillet_z_mm", 13.5)) * (0.85 + 0.15 * s_x)
    uv_entry_out = ellipse_points(entry_w_out, entry_h_out, n_pts)
    for s_dist in np.linspace(-4.0, throat_len, 32):
        ring = ring_frame_points(p_bm_tip + inlet_dir * float(s_dist), inlet_dir, up_hint, uv_entry_out)
        outer_rings.append(_sdf_fillet_ring(ring, uv_entry_out, inlet_dir, plenum_outer_sdf_and_normal, r_f_out, 1.0, False))

    for k in range(1, n_loft + 1):
        t = k / n_loft
        pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        uv = ellipse_points(entry_w_out + (sp_w_out - entry_w_out) * s_t, entry_h_out + (sp_h_out - entry_h_out) * s_t, n_pts)
        ring = ring_frame_points(pt, tan, up_hint, uv)
        if t < 0.42:
            f_wt = 0.5 + 0.5 * math.cos(math.pi * (t / 0.42))
            ring = _sdf_fillet_ring(ring, uv, tan, plenum_outer_sdf_and_normal, r_f_out, f_wt, False)
        outer_rings.append(ring)

    # Straight spigot land + crowned retention bead + tip chamfer
    bead_h = sp["retention_bead_height_mm"]
    bead_w = sp["retention_bead_width_mm"]
    y_bead_start = tip_y + sp["retention_bead_offset_from_tip_mm"]
    y_bead_end = y_bead_start + bead_w
    spigot_stations: list[tuple[float, float]] = [(float(y_s), 0.0) for y_s in np.linspace(sweep_end_y, y_bead_end, 12)[1:]]
    for b_idx in range(1, 20):
        frac = b_idx / 20.0
        spigot_stations.append((y_bead_end - frac * bead_w, bead_h * math.sin(math.pi * frac)))
    spigot_stations.extend([(y_bead_start, 0.0), (tip_y + 0.8, 0.0), (tip_y, -0.8)])
    tan_sp = np.array([0.0, -1.0, 0.0])
    for y_pos, dr in spigot_stations:
        uv = ellipse_points(sp_w_out + 2.0 * dr, sp_h_out + 2.0 * dr, n_pts)
        outer_rings.append(ring_frame_points(np.array([x_center, y_pos, sp_z]), tan_sp, up_hint, uv))

    outer_solid = trimesh_to_manifold(loft_closed_solid(outer_rings))

    # 2) Internal velocity-stack bellmouth outer solid (when protruding inside plenum)
    bellmouth_outer = None
    bm_len = bm["protrusion_into_plenum_mm"]
    bm_wall = bm["wall_thickness_mm"]
    if not wall_flush:
        bm_rings: list[np.ndarray] = []
        p_bm_anchor = p0 + inlet_dir * 10.0
        bm_total_len = float(np.linalg.norm(p_bm_anchor - p_bm_tip))
        for k in range(21):
            s_dist = (k / 20.0) * bm_total_len
            u_b = float(np.clip(s_dist / bm_len, 0.0, 1.0))
            inner_flare = bm_flare * ((1.0 - u_b) ** 2)
            w_o = entry_w_in + 2.0 * inner_flare + 2.0 * bm_wall - (2.2 if k == 0 else 0.0)
            h_o = entry_h_in + 2.0 * inner_flare + 2.0 * bm_wall - (2.2 if k == 0 else 0.0)
            r_o = entry_r_in + inner_flare + bm_wall - (1.1 if k == 0 else 0.0)
            bm_rings.append(ring_frame_points(p_bm_tip + inlet_dir * float(s_dist), inlet_dir, up_hint, rounded_rect_points(w_o, h_o, r_o, n_pts)))
        bellmouth_outer = trimesh_to_manifold(loft_closed_solid(bm_rings))

    # 3) Conformal internal bellmouth inner bore (tooth-free quarter-circle blend)
    bore_rings: list[np.ndarray] = []
    if wall_flush:
        angles = np.linspace(0.0, 2.0 * math.pi, n_pts, endpoint=False)
        cos_a = np.cos(angles)
        sin_a = np.sin(angles)
        # Preserve >= 5.0 mm roof shoulder and >= 5.5 mm Cyl 1 outer wall while eliminating Cyl 3/4 acute -u internal lips
        r_in_arr = (5.0 + 2.4 * np.maximum(0.0, -cos_a) * (1.0 if x_center > 0 else 0.0)) * (0.88 + 0.12 * s_x) * (1.0 - 0.50 * np.maximum(0.0, sin_a))
        uv_entry_in = ellipse_points(entry_w_in, entry_h_in, n_pts)
        for s_dist in np.linspace(-4.5, throat_len, 42):
            ring = ring_frame_points(p_bm_tip + inlet_dir * float(s_dist), inlet_dir, up_hint, uv_entry_in)
            bore_rings.append(_sdf_fillet_ring(ring, uv_entry_in, inlet_dir, plenum_inner_sdf_and_normal, r_in_arr, 1.0, True))
        for k in range(1, n_loft + 1):
            t = k / n_loft
            pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
            s_t = 0.5 - 0.5 * math.cos(math.pi * t)
            uv = ellipse_points(entry_w_in + (sp_w_in - entry_w_in) * s_t, entry_h_in + (sp_h_in - entry_h_in) * s_t, n_pts)
            ring = ring_frame_points(pt, tan, up_hint, uv)
            if t < 0.28:
                f_wt = 0.5 + 0.5 * math.cos(math.pi * (t / 0.28))
                ring = _sdf_fillet_ring(ring, uv, tan, plenum_inner_sdf_and_normal, r_in_arr, f_wt, True)
            bore_rings.append(ring)
    else:
        for s_dist in np.linspace(-3.5, throat_len - 0.8, 17):
            flare_r = bm_flare + (-s_dist) * 0.85 if s_dist < 0.0 else bm_flare * ((1.0 - float(np.clip(s_dist / bm_len, 0.0, 1.0))) ** 2)
            uv = rounded_rect_points(entry_w_in + 2.0 * flare_r, entry_h_in + 2.0 * flare_r, entry_r_in + flare_r, n_pts)
            bore_rings.append(ring_frame_points(p_bm_tip + inlet_dir * float(s_dist), inlet_dir, up_hint, uv))
        for k in range(1, n_loft + 1):
            t = k / n_loft
            pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
            s_t = 0.5 - 0.5 * math.cos(math.pi * t)
            w, h, r = entry_w_in + (sp_w_in - entry_w_in) * s_t, entry_h_in + (sp_h_in - entry_h_in) * s_t, entry_r_in + (sp_r_in - entry_r_in) * s_t
            bore_rings.append(ring_frame_points(pt, tan, up_hint, rounded_rect_points(w, h, r, n_pts)))

    bore_rings.append(ring_frame_points(np.array([x_center, tip_y - 6.0, sp_z]), tan_sp, up_hint, ellipse_points(sp_w_in, sp_h_in, n_pts) if wall_flush else rounded_rect_points(sp_w_in, sp_h_in, sp_r_in, n_pts)))
    inner_bore = trimesh_to_manifold(loft_closed_solid(bore_rings))

    return {"outer": outer_solid, "bellmouth_outer": bellmouth_outer, "inner_bore": inner_bore}


def build_throttle_body_components(params: dict) -> dict[str, md.Manifold]:
    """Build swept 3D C1 cubic-Bezier TB neck, 4-lobed transition bell, 4-bolt flange & O-ring groove."""
    tb = params["throttle_body"]
    pl = params["plenum"]
    wall = tb["neck_wall_thickness_mm"]
    bore_d = tb["bore_diameter_mm"]

    p_start, c0, c1, p_neck_end, p_flange_back, p_flange_face, tb_axis = tb_neck_bezier_points(params)
    pl_wall = pl["wall_thickness_mm"]
    pl_w_in, pl_h_in, pl_r_in = pl["inner_width_y_mm"], pl["inner_height_z_mm"], pl["inner_corner_radius_mm"]
    pl_w_out, pl_h_out, pl_r_out = pl_w_in + 2.0 * pl_wall, pl_h_in + 2.0 * pl_wall, pl_r_in + pl_wall

    n_pts = pl["profile_segments"]
    up_hint = np.array([0.0, 0.0, 1.0])

    neck_out_rings = [ring_frame_points(p_start - np.array([2.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), up_hint, rounded_rect_points(pl_w_out - 0.12, pl_h_out - 0.12, pl_r_out - 0.06, n_pts))]
    neck_in_rings = [ring_frame_points(p_start - np.array([4.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), up_hint, rounded_rect_points(pl_w_in, pl_h_in, pl_r_in, n_pts))]

    n_steps = 56
    x_dir = np.array([1.0, 0.0, 0.0])
    for k in range(n_steps + 1):
        t = k / n_steps
        s_t = 0.5 - 0.5 * math.cos(math.pi * min(t / 0.86, 1.0))
        s_rot = 0.5 - 0.5 * math.cos(math.pi * float(np.clip((t - 0.08) / 0.92, 0.0, 1.0)))
        pos, _tan = bezier_point_and_tangent(p_start, c0, c1, p_neck_end, t)
        nrm_frame = (1.0 - s_rot) * x_dir + s_rot * tb_axis
        nrm_frame /= np.linalg.norm(nrm_frame)
        neck_out_rings.append(ring_frame_points(
            pos, nrm_frame, up_hint,
            rounded_rect_points(pl_w_out + (bore_d + 2.0 * wall - pl_w_out) * s_t, pl_h_out + (bore_d + 2.0 * wall - pl_h_out) * s_t, pl_r_out + ((bore_d + 2.0 * wall) * 0.5 - pl_r_out) * s_t, n_pts),
        ))
        neck_in_rings.append(ring_frame_points(
            pos, nrm_frame, up_hint,
            rounded_rect_points(pl_w_in + (bore_d - pl_w_in) * s_t, pl_h_in + (bore_d - pl_h_in) * s_t, pl_r_in + (bore_d * 0.5 - pl_r_in) * s_t, n_pts),
        ))

    neck_in_rings.append(ring_frame_points(p_flange_face + tb_axis * 6.0, tb_axis, up_hint, rounded_rect_points(bore_d, bore_d, bore_d * 0.5, n_pts)))
    neck_outer = trimesh_to_manifold(loft_closed_solid(neck_out_rings))
    tb_bore = trimesh_to_manifold(loft_closed_solid(neck_in_rings))

    fl_w, fl_h, fl_r = float(tb["flange_width_mm"]), float(tb["flange_height_mm"]), float(tb["flange_corner_radius_mm"])
    fl_ch = float(tb.get("flange_back_chamfer_mm", 2.0))
    fl_rings = []
    for th in np.linspace(0.0, 0.5 * math.pi, 10):
        ax_off = fl_ch * (1.0 - math.cos(th))
        inset = fl_ch * (1.0 - math.sin(th))
        fl_rings.append(ring_frame_points(p_flange_back + tb_axis * ax_off, tb_axis, up_hint, rounded_rect_points(fl_w - 2.0 * inset, fl_h - 2.0 * inset, max(fl_r - inset, 1.0), 128)))
    fl_rings.append(ring_frame_points(p_flange_face, tb_axis, up_hint, rounded_rect_points(fl_w, fl_h, fl_r, 128)))
    outer_pieces = [neck_outer, trimesh_to_manifold(loft_closed_solid(fl_rings))]

    u_ax = np.cross(up_hint, tb_axis)
    u_ax /= np.linalg.norm(u_ax)
    v_ax = np.cross(tb_axis, u_ax)
    v_ax /= np.linalg.norm(v_ax)

    bf_ax = float(tb.get("flange_back_fillet_axial_mm", 10.0))
    if bf_ax > 0.0:
        angles_b = np.linspace(0.0, 2.0 * math.pi, 160, endpoint=False)
        r_start = 0.5 * (bore_d + 2.0 * wall) - 0.4
        r_end_theta = 44.4 + 1.6 * np.cos(4.0 * angles_b)
        bell_peak = 1.0 - math.sqrt(1.0 - 0.94**2)
        bell_rings = []
        for k in range(28):
            u = k / 27.0
            fac = (1.0 - math.sqrt(max(0.0, 1.0 - (0.94 * u) ** 2))) / bell_peak
            rk = r_start + (r_end_theta - r_start) * fac
            bell_rings.append(ring_frame_points(p_flange_back - tb_axis * (bf_ax * (1.0 - u)), tb_axis, up_hint, np.column_stack([rk * np.cos(angles_b), rk * np.sin(angles_b)])))
        bell_rings.append(ring_frame_points(p_flange_back + tb_axis * 2.0, tb_axis, up_hint, np.column_stack([r_end_theta * np.cos(angles_b), r_end_theta * np.sin(angles_b)])))
        outer_pieces.append(trimesh_to_manifold(loft_closed_solid(bell_rings)))

    cutters: list[md.Manifold] = [tb_bore]
    bx, by, b_rad = tb["bolt_spacing_x_mm"] * 0.5, tb["bolt_spacing_y_mm"] * 0.5, tb["bolt_hole_diameter_mm"] * 0.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pt_c = p_flange_back + u_ax * (sx * bx) + v_ax * (sy * by)
            cutters.append(make_cylinder_along(pt_c - tb_axis * 2.0, pt_c + tb_axis * (tb["flange_thickness_mm"] + 3.0), b_rad, segments=64))

    og = tb["oring_groove"]
    if og["enabled"]:
        r_in_g = og["inner_diameter_mm"] * 0.5
        r_out_g = r_in_g + og["width_mm"]
        depth_g = og["depth_mm"]
        outer_g = make_cylinder_along(p_flange_face - tb_axis * depth_g, p_flange_face + tb_axis * 1.0, r_out_g, segments=128)
        inner_g = make_cylinder_along(p_flange_face - tb_axis * (depth_g + 1.0), p_flange_face + tb_axis * 2.0, r_in_g, segments=128)
        cutters.append(outer_g - inner_g)

    return {"outer": m_union(outer_pieces), "tb_bore": tb_bore, "cutters": m_union(cutters), "flange_face_center": p_flange_face, "tb_axis": tb_axis}


def build_center_split_flange_and_cutters(params: dict) -> dict[str, md.Manifold]:
    """Build center split flange at X=0 with spot-faces, dowels, and left-half Viton O-ring groove."""
    cs, pl = params["center_split"], params["plenum"]
    x_split = cs["split_x_mm"]
    s = math.sqrt(plenum_area_scale(x_split, params))
    wall = pl["wall_thickness_mm"]
    w_in, h_in, r_in = pl["inner_width_y_mm"] * s, pl["inner_height_z_mm"] * s, pl["inner_corner_radius_mm"] * s
    w_out, h_out = w_in + 2.0 * wall, h_in + 2.0 * wall

    ext = cs["flange_radial_extension_mm"]
    w_fl, h_fl, r_fl = w_out + 2.0 * ext, h_out + 2.0 * ext, cs["flange_outer_corner_radius_mm"]
    t_half = float(cs["flange_thickness_per_side_mm"])
    thick_total = 2.0 * t_half
    r_edge = float(cs.get("outer_rim_chamfer_mm", 2.5))

    n_fl = 160
    fl_stations: list[tuple[float, float]] = []
    if r_edge > 0.0:
        for th in np.linspace(0.0, 0.5 * math.pi, 9):
            fl_stations.append((x_split - t_half + r_edge * (1.0 - math.cos(th)), r_edge * (1.0 - math.sin(th))))
        for th in np.linspace(0.5 * math.pi, 0.0, 9):
            fl_stations.append((x_split + t_half - r_edge * (1.0 - math.cos(th)), r_edge * (1.0 - math.sin(th))))
    else:
        fl_stations = [(x_split - t_half, 0.0), (x_split + t_half, 0.0)]

    fl_rings = []
    for x_loc, inset in fl_stations:
        uv = rounded_rect_points(w_fl - 2.0 * inset, h_fl - 2.0 * inset, max(r_fl - inset, 2.0), n_fl)
        fl_rings.append(np.column_stack([np.full(n_fl, x_loc), uv[:, 0], uv[:, 1]]))
    flange_pieces = [trimesh_to_manifold(loft_closed_solid(fl_rings))]

    bf_rad, bf_ax = float(cs.get("back_fillet_radial_mm", 0.0)), float(cs.get("back_fillet_axial_mm", 0.0))
    if bf_rad > 0.0 and bf_ax > 0.0:
        col_peak = 1.0 - math.sqrt(1.0 - 0.95**2)
        for side_sign in (-1.0, 1.0):
            col_rings = []
            u_vals = np.linspace(0.0, 1.0, 28)
            xs_col = [x_split + side_sign * (t_half + bf_ax * (1.0 - u)) for u in u_vals]
            if side_sign > 0:
                xs_col, u_vals = list(reversed(xs_col)), list(reversed(u_vals))
            for x_loc, u in zip(xs_col, u_vals):
                s_loc = math.sqrt(plenum_area_scale(float(x_loc), params))
                fac = (1.0 - math.sqrt(max(0.0, 1.0 - (0.95 * float(u)) ** 2))) / col_peak
                dr = -1.2 + (bf_rad + 1.2) * fac
                uv = rounded_rect_points(pl["inner_width_y_mm"] * s_loc + 2.0 * (wall + dr), pl["inner_height_z_mm"] * s_loc + 2.0 * (wall + dr), pl["inner_corner_radius_mm"] * s_loc + wall + dr, n_fl)
                col_rings.append(np.column_stack([np.full(n_fl, float(x_loc)), uv[:, 0], uv[:, 1]]))
            x_anc = float(x_split + side_sign * (t_half - 1.5))
            s_anc = math.sqrt(plenum_area_scale(x_anc, params))
            uv_e = rounded_rect_points(pl["inner_width_y_mm"] * s_anc + 2.0 * (wall + bf_rad), pl["inner_height_z_mm"] * s_anc + 2.0 * (wall + bf_rad), pl["inner_corner_radius_mm"] * s_anc + wall + bf_rad, n_fl)
            ring_anchor = np.column_stack([np.full(n_fl, x_anc), uv_e[:, 0], uv_e[:, 1]])
            if side_sign < 0:
                col_rings.append(ring_anchor)
            else:
                col_rings.insert(0, ring_anchor)
            flange_pieces.append(trimesh_to_manifold(loft_closed_solid(col_rings)))

    flange_solid = m_union(flange_pieces)
    flange_ring = flange_solid - make_rounded_prism(w_in, h_in, r_in, thick_total + 2.0 * bf_ax + 6.0, segments=160, center=(x_split, 0.0, 0.0), axis="x")

    def perimeter_point(angle_deg: float, radial_offset_from_inner: float) -> tuple[float, float]:
        pts = rounded_rect_points(w_in, h_in, r_in, 720)
        angles = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) % 360.0
        idx = int(np.argmin(np.abs(((angles - (angle_deg % 360.0) + 180.0) % 360.0) - 180.0)))
        tang = pts[(idx + 1) % 720] - pts[(idx - 1) % 720]
        nrm = np.array([tang[1], -tang[0]])
        out = pts[idx] + (nrm / np.linalg.norm(nrm)) * radial_offset_from_inner
        return float(out[0]), float(out[1])

    cutters: list[md.Manifold] = []
    b_rad = cs["bolt_hole_diameter_mm"] * 0.5
    spot_reach = t_half + max(bf_ax, 6.0) + 4.0
    for ang in cs["bolt_angles_deg"]:
        by, bz = perimeter_point(ang, wall + cs["bolt_radial_offset_mm"])
        cutters.append(make_cylinder_along(np.array([x_split - thick_total * 0.65, by, bz]), np.array([x_split + thick_total * 0.65, by, bz]), b_rad, segments=64))
        cutters.append(make_cylinder_along(np.array([x_split - spot_reach, by, bz]), np.array([x_split - t_half - 0.02, by, bz]), 6.5, segments=64))
        cutters.append(make_cylinder_along(np.array([x_split + t_half + 0.02, by, bz]), np.array([x_split + spot_reach, by, bz]), 6.5, segments=64))

    p_rad = cs["dowel_pin_diameter_mm"] * 0.5
    for ang in cs["dowel_pin_angles_deg"]:
        py, pz = perimeter_point(ang, wall + cs["dowel_pin_radial_offset_mm"])
        cutters.append(make_cylinder_along(np.array([x_split - thick_total * 0.65, py, pz]), np.array([x_split + thick_total * 0.65, py, pz]), p_rad, segments=64))

    og_cut = None
    og = cs["oring_groove"]
    if og["enabled"]:
        r_mid, gw, gd = og["radial_offset_from_inner_wall_mm"], og["width_mm"], og["depth_mm"]
        d_in, d_out = r_mid - gw * 0.5, r_mid + gw * 0.5
        og_cut = make_rounded_prism(w_in + 2.0 * d_out, h_in + 2.0 * d_out, r_in + d_out, gd + 0.8, segments=160, center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0), axis="x") - make_rounded_prism(w_in + 2.0 * d_in, h_in + 2.0 * d_in, r_in + d_in, gd + 2.0, segments=160, center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0), axis="x")

    return {"flange_ring": flange_ring, "hole_cutters": m_union(cutters), "oring_cutter": og_cut}


def build_boss_pad_components(pad_cfg: dict, params: dict) -> tuple[md.Manifold, list[md.Manifold]]:
    """Build a low-profile, wide-skirted, radius-topped NPT vacuum/boost boss pad."""
    s_bp = math.sqrt(plenum_area_scale(pad_cfg["x_center_mm"], params))
    z_roof_in = params["plenum"]["inner_height_z_mm"] * 0.5 * s_bp
    z_top = z_roof_in + params["plenum"]["wall_thickness_mm"] + pad_cfg["pad_height_z_mm"] - 2.0
    z_bot = z_roof_in - 6.0

    xc, yc = float(pad_cfg["x_center_mm"]), float(pad_cfg["y_center_mm"])
    lx, wy = float(pad_cfg["length_x_mm"]), float(pad_cfg["width_y_mm"])
    fx, fy = float(pad_cfg.get("skirt_flare_x_mm", 12.0)), float(pad_cfg.get("skirt_flare_y_mm", 11.0))
    r_edge = min(float(pad_cfg.get("top_chamfer_mm", 2.2)), 2.2)

    z_collar, n_p = z_top - 2.8, 128
    pad_rings = []
    for k in range(22):
        u = k / 21.0
        cove = (1.0 - u) ** 2.2
        uv = rounded_rect_points(lx + 2.0 * fx * cove, wy + 2.0 * fy * cove, 6.5 + 8.5 * cove, n_p)
        pad_rings.append(np.column_stack([uv[:, 0] + xc, uv[:, 1] + yc, np.full(n_p, z_bot + (z_collar - z_bot) * u)]))
    for th in np.linspace(0.0, 0.5 * math.pi, 9):
        inset = r_edge * (1.0 - math.cos(th))
        uv_k = rounded_rect_points(lx - 2.0 * inset, wy - 2.0 * inset, max(6.5 - inset, 1.5), n_p)
        pad_rings.append(np.column_stack([uv_k[:, 0] + xc, uv_k[:, 1] + yc, np.full(n_p, (z_top - r_edge) + r_edge * math.sin(th))]))
    pad = trimesh_to_manifold(loft_closed_solid(pad_rings))

    diameters = pad_cfg.get("port_pilot_diameters_mm") or [pad_cfg["port_pilot_diameter_mm"]] * pad_cfg["port_count"]
    start_x = pad_cfg["x_center_mm"] - pad_cfg["port_spacing_x_mm"] * (pad_cfg["port_count"] - 1) * 0.5
    bores = [
        make_cylinder_along(np.array([start_x + idx * pad_cfg["port_spacing_x_mm"], yc, z_roof_in - 12.0]), np.array([start_x + idx * pad_cfg["port_spacing_x_mm"], yc, z_top + 4.0]), float(diameters[idx]) * 0.5, segments=64)
        for idx in range(pad_cfg["port_count"])
    ]
    return pad, bores


def build_iacv_components(params: dict) -> dict[str, md.Manifold]:
    """
    Build outward-flared 2-bolt Ford IACV pedestal on top of the plenum/TB junction:
      - Downstream port (-X): punches cleanly into plenum chamber.
      - Upstream metered supply port (+X): isolated blind pocket >= 4.5 mm above plenum/TB roof,
        intersected by a flat-faced +Y rear 1/4"-18 NPT (Ø11.1 mm) side tap.
    """
    iac, pl = params["throttle_body"]["iacv_mount"], params["plenum"]
    xc, yc, top_z = float(iac["x_center_mm"]), float(iac["y_center_mm"]), float(iac["top_z_mm"])
    port_half = float(iac["port_spacing_x_mm"]) * 0.5
    x_plenum_port, x_supply_port = xc - port_half, xc + port_half

    pad_l, pad_w, pad_r = float(iac["pad_length_x_mm"]), float(iac["pad_width_y_mm"]), float(iac["pad_corner_radius_mm"])
    fl_nx, fl_px, base_wy = float(iac.get("skirt_flare_neg_x_mm", 14.0)), float(iac.get("skirt_flare_pos_x_mm", 4.0)), float(iac.get("base_width_y_mm", 80.0))
    r_edge = min(float(iac.get("top_chamfer_mm", 2.2)), 2.2)

    z_skirt_bot = min(float(iac["base_z_mm"]), 16.0)
    z_collar, n_p = 47.0, 128
    iac_rings = []
    for k in range(26):
        u = k / 25.0
        cove = (1.0 - u) ** 2.2
        x_min_k, x_max_k = (xc - 0.5 * pad_l) - fl_nx * cove, (xc + 0.5 * pad_l) + fl_px * cove
        uv = rounded_rect_points(x_max_k - x_min_k, pad_w + (base_wy - pad_w) * cove, pad_r + 8.0 * cove, n_p)
        iac_rings.append(np.column_stack([uv[:, 0] + 0.5 * (x_min_k + x_max_k), uv[:, 1] + yc, np.full(n_p, z_skirt_bot + (z_collar - z_skirt_bot) * u)]))
    for zk in (50.0, 59.5):
        uv = rounded_rect_points(pad_l, pad_w, pad_r, n_p)
        iac_rings.append(np.column_stack([uv[:, 0] + xc, uv[:, 1] + yc, np.full(n_p, zk)]))
    for th in np.linspace(0.0, 0.5 * math.pi, 9):
        inset = r_edge * (1.0 - math.cos(th))
        uv_k = rounded_rect_points(pad_l - 2.0 * inset, pad_w - 2.0 * inset, max(pad_r - inset, 2.0), n_p)
        iac_rings.append(np.column_stack([uv_k[:, 0] + xc, uv_k[:, 1] + yc, np.full(n_p, (top_z - r_edge) + r_edge * math.sin(th))]))

    pad_outer = trimesh_to_manifold(loft_closed_solid(iac_rings))

    cutters: list[md.Manifold] = []
    b_rad, b_half, b_bot = iac["bolt_pilot_diameter_mm"] * 0.5, iac["bolt_spacing_y_mm"] * 0.5, top_z - iac["bolt_depth_mm"]
    for sy in (-1.0, 1.0):
        cutters.append(make_cylinder_along(np.array([xc, yc + sy * b_half, b_bot]), np.array([xc, yc + sy * b_half, top_z + 4.0]), b_rad, segments=64))

    p_rad = iac["port_diameter_mm"] * 0.5
    cutters.append(make_cylinder_along(np.array([x_plenum_port, yc, 18.0]), np.array([x_plenum_port, yc, top_z + 4.0]), p_rad, segments=64))
    cutters.append(make_cylinder_along(np.array([x_supply_port, yc, iac["supply_pocket_bottom_z_mm"]]), np.array([x_supply_port, yc, top_z + 4.0]), p_rad, segments=64))

    tap_rad, tap_z = iac["side_supply_tap_diameter_mm"] * 0.5, float(iac["side_supply_tap_z_mm"])
    tap_face = iac.get("side_supply_tap_face", "pos_y")
    if tap_face == "pos_y":
        cutters.append(make_cylinder_along(np.array([x_supply_port, yc - 2.0, tap_z]), np.array([x_supply_port, yc + 0.5 * pad_w + 4.0, tap_z]), tap_rad, segments=64))
    elif tap_face == "neg_y":
        cutters.append(make_cylinder_along(np.array([x_supply_port, yc - 0.5 * pad_w - 4.0, tap_z]), np.array([x_supply_port, yc + 2.0, tap_z]), tap_rad, segments=64))
    else:
        cutters.append(make_cylinder_along(np.array([x_supply_port - 2.0, yc, tap_z]), np.array([xc + 0.5 * pad_l + 4.0, yc, tap_z]), tap_rad, segments=64))

    return {"outer": pad_outer, "cutters": m_union(cutters), "tap_face": tap_face}


def build_cable_bracket_boss_components(params: dict) -> dict[str, md.Manifold] | None:
    """
    Build integrated twin-M6 throttle/cruise cable bracket mounting boss atop the rising TB neck.
    Transverse M6 holes (32 mm spacing) stay >= 4.5 mm clear of the TB inner bore and clear of
    both TB flange bolts and the IACV pedestal.
    """
    cfg = params["throttle_body"].get("cable_bracket_boss")
    if not cfg or not cfg.get("enabled", False):
        return None

    p_start, c0, c1, p_neck_end, _, _, _ = tb_neck_bezier_points(params)
    pc, tanc = bezier_point_and_tangent(p_start, c0, c1, p_neck_end, float(cfg["neck_t_center"]))
    t_horiz = np.array([tanc[0], tanc[1], 0.0])
    t_horiz /= np.linalg.norm(t_horiz)
    u_lat = np.array([t_horiz[1], -t_horiz[0], 0.0])  # points across neck toward -Y/-X front
    pc = pc + u_lat * float(cfg.get("lateral_front_offset_mm", 0.0))

    # Local 2D frame rotated to align width along t_horiz and length along u_lat
    rot_ang = math.atan2(u_lat[1], u_lat[0])
    cos_r, sin_r = math.cos(rot_ang), math.sin(rot_ang)

    def _world_ring(w_along_len: float, h_along_width: float, r_c: float, z_val: float) -> np.ndarray:
        uv = rounded_rect_points(w_along_len, h_along_width, r_c, 96)
        xw = pc[0] + uv[:, 0] * cos_r - uv[:, 1] * sin_r
        yw = pc[1] + uv[:, 0] * sin_r + uv[:, 1] * cos_r
        return np.column_stack([xw, yw, np.full(len(uv), z_val)])

    lx, wy, cr = float(cfg["length_mm"]), float(cfg["width_mm"]), float(cfg["corner_radius_mm"])
    top_z, r_edge = float(cfg["top_z_mm"]), 2.0
    z_bot = float(pc[2]) + 18.0  # cleanly buried inside TB neck outer shell
    z_collar = top_z - 3.0

    rings = []
    for k in range(20):
        u = k / 19.0
        cove = (1.0 - u) ** 2.2
        rings.append(_world_ring(lx + 10.0 * cove, wy + 12.0 * cove, cr + 3.0 * cove, z_bot + (z_collar - z_bot) * u))
    for th in np.linspace(0.0, 0.5 * math.pi, 9):
        inset = r_edge * (1.0 - math.cos(th))
        rings.append(_world_ring(lx - 2.0 * inset, wy - 2.0 * inset, max(cr - inset, 1.5), (top_z - r_edge) + r_edge * math.sin(th)))
    pad_outer = trimesh_to_manifold(loft_closed_solid(rings))

    b_half = float(cfg["bolt_spacing_mm"]) * 0.5
    b_rad = float(cfg["bolt_pilot_diameter_mm"]) * 0.5
    b_bot_z = top_z - float(cfg["bolt_depth_mm"])
    hole_centers = [np.array([pc[0] + sgn * b_half * u_lat[0], pc[1] + sgn * b_half * u_lat[1], b_bot_z]) for sgn in (-1.0, 1.0)]
    cutters = [make_cylinder_along(pt_b, np.array([pt_b[0], pt_b[1], top_z + 4.0]), b_rad, segments=48) for pt_b in hole_centers]

    return {"outer": pad_outer, "cutters": m_union(cutters), "hole_bottoms": hole_centers, "top_z": top_z}


def build_sculpted_runner_tie_web(x_left: float, x_right: float, params: dict) -> md.Manifold:
    """Build straight runner tie-bar with 360-deg conformal SDF rolling-ball fillets onto curved barrels."""
    r_cfg = params["runners"]
    tw, sp, sw, bm = r_cfg["tie_webs"], r_cfg["spigot"], r_cfg["sweep"], r_cfg["bellmouth"]
    wall, tip_y, sp_z = float(sp["wall_thickness_mm"]), float(sp["tip_y_mm"]), float(sp["center_z_mm"])
    sp_w_out, sp_h_out = float(sp["outer_width_mm"]), float(sp["outer_height_mm"])
    sweep_end_y = tip_y + float(sp["land_length_mm"])
    wall_flush = bool(bm.get("wall_flush_bellmouth", False))
    entry_d = float(sw["plenum_entry_diameter_mm"])
    entry_w_in = (entry_d + 0.4) if wall_flush else entry_d
    entry_h_in = (entry_d - 4.2) if wall_flush else (entry_d - 6.0)
    entry_wall = max(wall, 6.5)
    entry_w_out, entry_h_out = entry_w_in + 2.0 * entry_wall, entry_h_in + 2.0 * entry_wall
    up_hint = np.array([0.0, 0.0, 1.0])

    def sample_runner_sdf_data(xc: float):
        _, _, p0, p1, p2, p3 = runner_bezier_points(xc, params)
        centers_l, tans_l, u_l, v_l, a_l, b_l = [], [], [], [], [], []

        def _push(pt, tan, w_o, h_o):
            t_hat = tan / np.linalg.norm(tan)
            u_ax = np.cross(up_hint, t_hat)
            u_ax /= np.linalg.norm(u_ax)
            v_ax = np.cross(t_hat, u_ax)
            v_ax /= np.linalg.norm(v_ax)
            centers_l.append(pt)
            tans_l.append(t_hat)
            u_l.append(u_ax)
            v_l.append(v_ax)
            a_l.append(0.5 * w_o)
            b_l.append(0.5 * h_o)

        for k in range(121):
            t = k / 120.0
            pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
            s_t = 0.5 - 0.5 * math.cos(math.pi * t)
            _push(pt, tan, entry_w_out + (sp_w_out - entry_w_out) * s_t, entry_h_out + (sp_h_out - entry_h_out) * s_t)
        tan_sp = np.array([0.0, -1.0, 0.0])
        for y_s in np.linspace(sweep_end_y, tip_y, 21)[1:]:
            _push(np.array([xc, float(y_s), sp_z]), tan_sp, sp_w_out, sp_h_out)

        arr_c = np.asarray(centers_l, dtype=np.float64)
        order_y = np.argsort(arr_c[:, 1])
        data = {
            "centers": arr_c,
            "tangents": np.asarray(tans_l, dtype=np.float64),
            "u_axes": np.asarray(u_l, dtype=np.float64),
            "v_axes": np.asarray(v_l, dtype=np.float64),
            "a_out": np.asarray(a_l, dtype=np.float64),
            "b_out": np.asarray(b_l, dtype=np.float64),
        }
        return data, arr_c[order_y, 1], arr_c[order_y, 2]

    left_data, yl, zl = sample_runner_sdf_data(x_left)
    right_data, yr, zr = sample_runner_sdf_data(x_right)

    def runner_outer_sdf(pt: np.ndarray, rdata: dict[str, np.ndarray]) -> float:
        centers, tans = rdata["centers"], rdata["tangents"]
        diffs = centers - pt[None, :]
        idx = int(np.argmin(np.einsum("ij,ij->i", diffs, diffs)))
        m_cnt = len(centers)
        ds = float(np.dot(pt - centers[idx], tans[idx]))
        if ds >= 0.0 and idx < m_cnt - 1:
            idx2 = idx + 1
            alpha = float(np.clip(ds / max(float(np.linalg.norm(centers[idx2] - centers[idx])), 1e-6), 0.0, 1.0))
        elif ds < 0.0 and idx > 0:
            idx2 = idx - 1
            alpha = float(np.clip(-ds / max(float(np.linalg.norm(centers[idx] - centers[idx2])), 1e-6), 0.0, 1.0))
        else:
            idx2, alpha = idx, 0.0
        c_loc = (1.0 - alpha) * centers[idx] + alpha * centers[idx2]
        u_loc = (1.0 - alpha) * rdata["u_axes"][idx] + alpha * rdata["u_axes"][idx2]
        v_loc = (1.0 - alpha) * rdata["v_axes"][idx] + alpha * rdata["v_axes"][idx2]
        u_loc /= np.linalg.norm(u_loc)
        v_loc /= np.linalg.norm(v_loc)
        a_loc = float((1.0 - alpha) * rdata["a_out"][idx] + alpha * rdata["a_out"][idx2])
        b_loc = float((1.0 - alpha) * rdata["b_out"][idx] + alpha * rdata["b_out"][idx2])
        rel = pt - c_loc
        du, dv = float(np.dot(rel, u_loc)), float(np.dot(rel, v_loc))
        q = math.hypot(du / a_loc, dv / b_loc)
        if q < 1e-8:
            return -min(a_loc, b_loc)
        return q * (q - 1.0) / math.hypot(du / (a_loc * a_loc), dv / (b_loc * b_loc))

    def nearest_runner_sdf_and_normal(pt: np.ndarray) -> tuple[float, np.ndarray]:
        d0 = min(runner_outer_sdf(pt, left_data), runner_outer_sdf(pt, right_data))
        eps = 0.15
        gx = (min(runner_outer_sdf(pt + np.array([eps, 0.0, 0.0]), left_data), runner_outer_sdf(pt + np.array([eps, 0.0, 0.0]), right_data)) - d0) / eps
        gy = (min(runner_outer_sdf(pt + np.array([0.0, eps, 0.0]), left_data), runner_outer_sdf(pt + np.array([0.0, eps, 0.0]), right_data)) - d0) / eps
        gz = (min(runner_outer_sdf(pt + np.array([0.0, 0.0, eps]), left_data), runner_outer_sdf(pt + np.array([0.0, 0.0, eps]), right_data)) - d0) / eps
        g = np.array([gx, gy, gz], dtype=np.float64)
        nl = float(np.linalg.norm(g))
        return (d0, g / nl) if nl >= 1e-8 else (d0, np.array([1.0, 0.0, 0.0]))

    y0, y1 = float(tw.get("waist_y_start_mm", -108.0)), float(tw.get("waist_y_end_mm", -78.0))
    hz = 0.5 * float(tw.get("waist_height_mm", 18.0))
    r_end = min(float(tw.get("edge_radius_mm", 5.5)), hz * 0.92, 0.36 * (y1 - y0))
    r_fil = float(tw.get("root_fillet_span_mm", 9.0))
    y_inner0, y_inner1 = y0 + r_end, y1 - r_end
    n_edge, n_arc = 28, 28
    rings = []

    for x in np.linspace(x_left + 16.0, x_right - 16.0, 120):
        frac_lr = (x - x_left) / (x_right - x_left)
        z_c = lambda yv: (1.0 - frac_lr) * np.interp(yv, yl, zl) + frac_lr * np.interp(yv, yr, zr)
        pts_yz, nrms_yz = [], []

        ys_bot = np.linspace(y_inner0, y_inner1, n_edge, endpoint=False)
        zs_bot = z_c(ys_bot) - hz
        for yy, zz, sl in zip(ys_bot, zs_bot, np.gradient(zs_bot, ys_bot)):
            nm = math.hypot(float(sl), 1.0)
            pts_yz.append([float(yy), float(zz)])
            nrms_yz.append([float(sl) / nm, -1.0 / nm])

        z_rc = float(z_c(y_inner1))
        for ang in np.linspace(-0.5 * math.pi, 0.5 * math.pi, n_arc, endpoint=False):
            nm = math.hypot(math.cos(ang) / r_end, math.sin(ang) / hz)
            pts_yz.append([y_inner1 + r_end * math.cos(ang), z_rc + hz * math.sin(ang)])
            nrms_yz.append([(math.cos(ang) / r_end) / nm, (math.sin(ang) / hz) / nm])

        ys_top = np.linspace(y_inner1, y_inner0, n_edge, endpoint=False)
        zs_top = z_c(ys_top) + hz
        for yy, zz, sl in zip(ys_top, zs_top, np.gradient(zs_top, ys_top)):
            nm = math.hypot(float(sl), 1.0)
            pts_yz.append([float(yy), float(zz)])
            nrms_yz.append([-float(sl) / nm, 1.0 / nm])

        z_fc = float(z_c(y_inner0))
        for ang in np.linspace(0.5 * math.pi, 1.5 * math.pi, n_arc, endpoint=False):
            nm = math.hypot(math.cos(ang) / r_end, math.sin(ang) / hz)
            pts_yz.append([y_inner0 + r_end * math.cos(ang), z_fc + hz * math.sin(ang)])
            nrms_yz.append([(math.cos(ang) / r_end) / nm, (math.sin(ang) / hz) / nm])

        ring = np.column_stack([np.full(len(pts_yz), float(x)), np.asarray(pts_yz, dtype=np.float64)])
        for idx in range(len(ring)):
            p_base = ring[idx]
            d_run, n_run = nearest_runner_sdf_and_normal(p_base)
            if d_run >= r_fil:
                continue
            n_bar = np.array([0.0, nrms_yz[idx][0], nrms_yz[idx][1]], dtype=np.float64)
            t_surf = n_bar - float(np.dot(n_bar, n_run)) * n_run
            ts_len = float(np.linalg.norm(t_surf))
            t_surf = (t_surf / ts_len) if ts_len > 1e-6 else n_bar
            u = float(np.clip(1.0 - max(d_run, 0.0) / r_fil, 0.0, 1.0))
            fade_in = float(np.clip((d_run + 6.5) / 6.5, 0.0, 1.0))
            fade_in = fade_in * fade_in * (3.0 - 2.0 * fade_in)
            delta_t = fade_in * r_fil * (1.0 - math.sqrt(max(0.0, 1.0 - (0.88 * u) ** 2)))
            p_tang = p_base + delta_t * t_surf
            d_tang, n_tang = nearest_runner_sdf_and_normal(p_tang)
            ring[idx] = p_tang + ((d_run - fade_in * 0.3 * (u**0.5)) - d_tang) * n_tang
        rings.append(ring)

    return trimesh_to_manifold(loft_closed_solid(rings))


def build_fitment_gauges(params: dict) -> dict[str, md.Manifold]:
    """Build quick-print runner boot gauge, TB flange gauge, IACV gauge, and alignment dowels."""
    sp, g = params["runners"]["spigot"], params["gauges"]
    n_pts, wall = params["runners"]["sweep"]["profile_segments"], sp["wall_thickness_mm"]
    w_out, h_out, r_out = sp["outer_width_mm"], sp["outer_height_mm"], sp["corner_radius_mm"]
    w_in, h_in, r_in = w_out - 2.0 * wall, h_out - 2.0 * wall, r_out - wall

    bead_h, bead_w, total_len = sp["retention_bead_height_mm"], sp["retention_bead_width_mm"], g["boot_fit_gauge_length_mm"]
    z_tip = total_len
    z_b_start = z_tip - sp["retention_bead_offset_from_tip_mm"]
    z_b_end = z_b_start - bead_w
    stations = [(0.0, 3.0), (5.0, 3.0), (6.5, 0.0), (z_b_end, 0.0)]
    for b_idx in range(1, 20):
        frac = b_idx / 20.0
        stations.append((z_b_end + frac * bead_w, bead_h * math.sin(math.pi * frac)))
    stations.extend([(z_b_start, 0.0), (z_tip - 0.8, 0.0), (z_tip, -0.8)])
    rings = [np.column_stack([uv[:, 0], uv[:, 1], np.full(n_pts, z)]) for z, dr in stations for uv in [rounded_rect_points(w_out + 2.0 * dr, h_out + 2.0 * dr, r_out + dr, n_pts)]]
    boot_gauge = trimesh_to_manifold(loft_closed_solid(rings)) - make_rounded_prism(w_in, h_in, r_in, total_len + 4.0, segments=n_pts, center=(0.0, 0.0, total_len * 0.5), axis="z")

    tb, t_g = params["throttle_body"], g["tb_fit_gauge_thickness_mm"]
    tb_plate = make_rounded_prism(tb["flange_width_mm"], tb["flange_height_mm"], tb["flange_corner_radius_mm"], t_g, segments=128, center=(0.0, 0.0, t_g * 0.5), axis="z")
    bx, by, b_rad = tb["bolt_spacing_x_mm"] * 0.5, tb["bolt_spacing_y_mm"] * 0.5, tb["bolt_hole_diameter_mm"] * 0.5
    tb_cutters = [md.Manifold.cylinder(t_g + 4.0, tb["bore_diameter_mm"] * 0.5, tb["bore_diameter_mm"] * 0.5, circular_segments=128, center=True).translate([0.0, 0.0, t_g * 0.5])]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            tb_cutters.append(md.Manifold.cylinder(t_g + 4.0, b_rad, b_rad, circular_segments=64, center=True).translate([sx * bx, sy * by, t_g * 0.5]))
    tb_gauge = m_diff(tb_plate, tb_cutters)

    iac, t_iac = params["throttle_body"]["iacv_mount"], g["iacv_fit_gauge_thickness_mm"]
    iac_plate = make_rounded_prism(iac["pad_length_x_mm"], iac["pad_width_y_mm"], iac["pad_corner_radius_mm"], t_iac, segments=128, center=(0.0, 0.0, t_iac * 0.5), axis="z")
    iac_cutters = [
        md.Manifold.cylinder(t_iac + 4.0, iac["port_diameter_mm"] * 0.5, iac["port_diameter_mm"] * 0.5, circular_segments=64, center=True).translate([sx * iac["port_spacing_x_mm"] * 0.5, 0.0, t_iac * 0.5])
        for sx in (-1.0, 1.0)
    ] + [
        md.Manifold.cylinder(t_iac + 4.0, 3.2, 3.2, circular_segments=64, center=True).translate([0.0, sy * iac["bolt_spacing_y_mm"] * 0.5, t_iac * 0.5])
        for sy in (-1.0, 1.0)
    ]
    iacv_gauge = m_diff(iac_plate, iac_cutters)

    pin_len, pin_diams = float(g.get("dowel_pin_length_mm", 20.0)), g.get("dowel_pin_diameters_mm", [5.85, 5.75])
    pin_solids = []
    for d_pin, y_off in zip([float(pin_diams[0]), float(pin_diams[0]), float(pin_diams[-1]), float(pin_diams[-1])], [-18.0, -6.0, 6.0, 18.0]):
        rp = d_pin * 0.5
        rc = max(rp - 0.85, 0.5)
        p_rings = [np.column_stack([uv[:, 0], uv[:, 1], np.full(48, zl)]) for zl, rad in [(0.0, rc), (0.9, rp), (pin_len - 0.9, rp), (pin_len, rc)] for uv in [rounded_rect_points(2.0 * rad, 2.0 * rad, rad, 48)]]
        pin_solids.append(trimesh_to_manifold(loft_closed_solid(p_rings)).rotate([0.0, 90.0, 0.0]).translate([-pin_len * 0.5, y_off, rp - 0.35]))
    dowel_pins = m_union([*pin_solids, md.Manifold.cube([1.8, 38.0, 0.85], center=True).translate([0.0, 0.0, 0.425])]) ^ md.Manifold.cube([200.0, 200.0, 200.0], center=True).translate([0.0, 0.0, 100.0])

    return {"boot_fit_gauge": boot_gauge, "tb_flange_fit_gauge": tb_gauge, "iacv_flange_fit_gauge": iacv_gauge, "alignment_dowel_pins": dowel_pins}


# ---------------------------------------------------------------------------
# Full Assembly Pipeline
# ---------------------------------------------------------------------------

def assemble_all(params: dict):
    pl_outer = build_plenum_loft(params, is_inner=False)
    pl_inner = build_plenum_loft(params, is_inner=True)

    runner_outers, runner_bores = [], []
    for x_c in params["runners"]["center_x_mm"]:
        rc = build_single_runner_components(x_c, params)
        runner_outers.append(rc["outer"])
        runner_bores.append(rc["inner_bore"])

    cxs = params["runners"]["center_x_mm"]
    webs = []
    if params["runners"]["tie_webs"]["enabled"]:
        webs.append(build_sculpted_runner_tie_web(float(cxs[0]), float(cxs[1]), params))
        webs.append(build_sculpted_runner_tie_web(float(cxs[2]), float(cxs[3]), params))

    boss_solids, boss_bores = [], []
    for key in ("vacuum_boss_pad", "vacuum_only_boss_pad"):
        pad_cfg = params["plenum"].get(key)
        if pad_cfg and pad_cfg.get("enabled"):
            pad_s, pad_b = build_boss_pad_components(pad_cfg, params)
            boss_solids.append(pad_s)
            boss_bores.extend(pad_b)

    tb_parts = build_throttle_body_components(params)
    iacv_parts = build_iacv_components(params) if params["throttle_body"]["iacv_mount"]["enabled"] else None
    cable_parts = build_cable_bracket_boss_components(params)

    # 1-piece full assembly
    outer_1pc = [pl_outer, *runner_outers, *webs, *boss_solids, tb_parts["outer"]]
    if iacv_parts is not None:
        outer_1pc.append(iacv_parts["outer"])
    if cable_parts is not None:
        outer_1pc.append(cable_parts["outer"])
    hollow_1pc = m_union(outer_1pc) - m_union([pl_inner, tb_parts["cutters"]])
    sub_1pc = [*runner_bores, *boss_bores]
    if iacv_parts is not None:
        sub_1pc.append(iacv_parts["cutters"])
    if cable_parts is not None:
        sub_1pc.append(cable_parts["cutters"])
    final_1pc = m_diff(hollow_1pc, sub_1pc)

    # 2-piece split assembly (with center split flange at X=0)
    split_parts = build_center_split_flange_and_cutters(params)
    outer_split = m_union([pl_outer, *runner_outers, *webs, *boss_solids, tb_parts["outer"], *([iacv_parts["outer"]] if iacv_parts else []), *([cable_parts["outer"]] if cable_parts else [])])
    hollow_split = outer_split - m_union([pl_inner, tb_parts["cutters"]])
    with_flange = m_union([hollow_split, split_parts["flange_ring"]])
    sub_split = [*runner_bores, *boss_bores, split_parts["hole_cutters"], *([iacv_parts["cutters"]] if iacv_parts else []), *([cable_parts["cutters"]] if cable_parts else [])]
    full_for_split = m_diff(with_flange, sub_split)

    x_split = params["center_split"]["split_x_mm"]
    big = 1000.0
    left_box = md.Manifold.cube([big, big, big], center=True).translate([x_split - big * 0.5, 0.0, 0.0])
    right_box = md.Manifold.cube([big, big, big], center=True).translate([x_split + big * 0.5, 0.0, 0.0])

    split_left = full_for_split ^ left_box
    if split_parts["oring_cutter"] is not None:
        split_left = split_left - split_parts["oring_cutter"]
    split_right = full_for_split ^ right_box

    def center_xy_on_bed(solid: md.Manifold) -> md.Manifold:
        bb = solid.bounding_box()
        return solid.translate([-0.5 * (bb[0] + bb[3]), -0.5 * (bb[1] + bb[4]), -bb[2]])

    split_left_print = center_xy_on_bed(split_left.rotate([0.0, 90.0, 0.0]))
    split_right_print = center_xy_on_bed(split_right.rotate([0.0, -90.0, 0.0]))
    gauges = build_fitment_gauges(params)

    return {
        "svt_intake_manifold_v2_1piece_full": final_1pc,
        "svt_intake_manifold_v2_split_left_cyl1_2": split_left,
        "svt_intake_manifold_v2_split_right_cyl3_4_tb": split_right,
        "svt_intake_manifold_v2_split_left_print_oriented": split_left_print,
        "svt_intake_manifold_v2_split_right_print_oriented": split_right_print,
        "svt_v2_runner_boot_fit_gauge": gauges["boot_fit_gauge"],
        "svt_v2_tb_flange_fit_gauge": gauges["tb_flange_fit_gauge"],
        "svt_v2_iacv_flange_fit_gauge": gauges["iacv_flange_fit_gauge"],
        "svt_v2_alignment_dowel_pins": gauges["alignment_dowel_pins"],
        "_plenum_inner_cavity": pl_inner,
        "_tb_bore_solid": tb_parts["tb_bore"],
        "_cable_parts": cable_parts,
    }


# ---------------------------------------------------------------------------
# Section & Ray Audit Helpers (Codex Check Geometry Equivalents)
# ---------------------------------------------------------------------------

def _section_2d(mesh: trimesh.Trimesh, origin: np.ndarray, axis: np.ndarray) -> np.ndarray:
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    up = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(up, axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    lines = trimesh.intersections.mesh_plane(mesh, axis, origin)
    if len(lines) == 0:
        return np.zeros((0, 2, 2), dtype=float)
    return (lines - origin) @ np.column_stack((u, v))


def _ray_distances(lines: np.ndarray, direction: np.ndarray, origin=(0.0, 0.0)) -> np.ndarray:
    if len(lines) == 0:
        return np.zeros(0, dtype=float)
    a, b = (lines - np.asarray(origin)).transpose(1, 0, 2)
    e = b - a
    dx, dy = direction
    det = dx * e[:, 1] - dy * e[:, 0]
    valid = np.abs(det) > 1e-10
    a, e, det = a[valid], e[valid], det[valid]
    t = (a[:, 0] * e[:, 1] - a[:, 1] * e[:, 0]) / det
    frac = (a[:, 0] * dy - a[:, 1] * dx) / det
    hits = np.sort(t[(t > 0.0) & (fraction_ok := (frac >= -1e-9) & (frac <= 1.0 + 1e-9))])
    _ = fraction_ok
    return hits[np.r_[True, np.diff(hits) > 0.0001]] if len(hits) else hits


def audit_runner_root_walls_72ray(mesh: trimesh.Trimesh, params: dict) -> list[dict]:
    angles = np.deg2rad(np.arange(72) * 5.0 + 0.37)
    rays = np.column_stack((np.cos(angles), np.sin(angles)))
    results = []
    for cyl_idx, xc in enumerate(params["runners"]["center_x_mm"], start=1):
        tip, axis, *controls = runner_bezier_points(xc, params)
        stations = [(f"{s:g} mm after lip", tip + s * axis, axis) for s in (6, 8, 10, 12, 14, 16, 18)]
        stations += [(f"Bezier t={t:g}", *bezier_point_and_tangent(*controls, t)) for t in (0.025, 0.05, 0.10, 0.15, 0.20)]

        min_press_wall = 999.0
        min_press_info = None
        min_all_span = 999.0
        min_all_info = None
        for label, pos, nrm in stations:
            lines = _section_2d(mesh, pos, nrm)
            for ang, ray in zip(angles, rays):
                d = _ray_distances(lines, ray)
                if len(d) >= 2 and 8.0 < d[0] < 34.0 and d[1] < 39.0:
                    w = float(d[1] - d[0])
                    if w < min_all_span:
                        min_all_span = w
                        min_all_info = {"station": label, "angle_deg": round(float(np.rad2deg(ang)), 2)}
                    if len(d) == 2 and w < min_press_wall:
                        min_press_wall = w
                        min_press_info = {"station": label, "angle_deg": round(float(np.rad2deg(ang)), 2)}
        results.append({
            "cylinder": cyl_idx,
            "x_mm": xc,
            "min_pressure_wall_mm": round(min_press_wall, 3),
            "min_pressure_loc": min_press_info,
            "min_all_ray_span_mm": round(min_all_span, 3),
            "min_all_ray_loc": min_all_info,
        })
    return results


def audit_iacv_floor_468ray(mesh: trimesh.Trimesh, params: dict) -> dict:
    cfg = params["throttle_body"]["iacv_mount"]
    x0 = float(cfg["x_center_mm"]) + float(cfg["port_spacing_x_mm"]) * 0.5
    y0 = float(cfg["y_center_mm"])
    z_pocket = float(cfg["supply_pocket_bottom_z_mm"])
    sampled = []
    for dx in np.arange(-5.75, 6.0, 0.5):
        x = x0 + dx
        keep = (mesh.triangles[:, :, 0].min(axis=1) <= x + 0.5) & (mesh.triangles[:, :, 0].max(axis=1) >= x - 0.5)
        loc = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces[keep], process=False)
        lines = _section_2d(loc, np.array([x, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
        for dy in np.arange(-5.75, 6.0, 0.5):
            if dx * dx + dy * dy >= 6.1**2:
                continue
            z_hits = _ray_distances(lines, (0.0, 1.0), origin=(y0 + dy, 0.0))
            assert len(z_hits) >= 2 and abs(float(z_hits[1]) - z_pocket) < 0.02, f"IACV pocket floor miss at ({x},{y0+dy}): {z_hits}"
            sampled.append({"x_mm": round(float(x), 3), "y_mm": round(float(y0 + dy), 3), "wall_mm": float(z_hits[1] - z_hits[0])})
    c_lines = _section_2d(mesh, np.array([x0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
    c_hits = _ray_distances(c_lines, (0.0, 1.0), origin=(y0, 0.0))
    m_min = min(sampled, key=lambda s: s["wall_mm"])
    return {
        "samples": len(sampled),
        "centerline_wall_mm": round(float(c_hits[1] - c_hits[0]), 3),
        "min_wall_mm": round(float(m_min["wall_mm"]), 3),
        "min_location_mm": [m_min["x_mm"], m_min["y_mm"]],
    }


def audit_cable_boss_walls(solids: dict, params: dict) -> dict | None:
    cp = solids.get("_cable_parts")
    if not cp:
        return None
    tb_bore_mesh = manifold_to_trimesh(m_union([solids["_tb_bore_solid"], solids["_plenum_inner_cavity"]]))
    pts = np.asarray(cp["hole_bottoms"], dtype=np.float64)
    _, dists, _ = trimesh.proximity.closest_point(tb_bore_mesh, pts)
    return {"min_solid_wall_to_bore_mm": round(float(np.min(dists)), 3), "per_hole_wall_mm": [round(float(d), 3) for d in dists]}


# ---------------------------------------------------------------------------
# Visualization & Documentation Generators
# ---------------------------------------------------------------------------

def _add_section_patches(ax, polys_2d, facecolor: str, edgecolor: str, lw: float = 0.9, alpha: float = 1.0, ls: str = "-"):
    if not polys_2d:
        return
    sh_polys = [ShapelyPolygon(p) for p in polys_2d if len(p) >= 3]
    depths = [sum(1 for j, pj in enumerate(sh_polys) if i != j and pj.area > pi.area and pj.contains(pi.representative_point())) for i, pi in enumerate(sh_polys)]
    for i, pi in enumerate(sh_polys):
        if depths[i] % 2 != 0:
            continue
        rings = [np.asarray(pi.exterior.coords)] + [np.asarray(pj.exterior.coords) for j, pj in enumerate(sh_polys) if depths[j] == depths[i] + 1 and pi.contains(pj.representative_point())]
        verts, codes = [], []
        for r_idx, r in enumerate(rings):
            area = 0.5 * np.sum(r[:-1, 0] * r[1:, 1] - r[1:, 0] * r[:-1, 1])
            if (r_idx == 0 and area < 0) or (r_idx > 0 and area > 0):
                r = r[::-1]
            verts.extend(r)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(r) - 2) + [MplPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MplPath(np.asarray(verts), codes), facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, alpha=alpha, linestyle=ls))


def _plot_mesh_panel(ax, mesh: trimesh.Trimesh, title: str, elev: float, azim: float, color: str = "#3a434e", bounds_override=None, zoom_scale: float = 0.44, lightsource: LightSource | None = None, hide_axes: bool = False):
    ax.set_facecolor("#f5f4f0")
    kwargs = {"lightsource": lightsource} if lightsource is not None else {}
    ax.plot_trisurf(mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2], triangles=mesh.faces, color=color, linewidth=0, antialiased=False, shade=True, **kwargs)
    mins, maxs = bounds_override if bounds_override is not None else (mesh.bounds[0], mesh.bounds[1])
    max_span = max(maxs - mins) * zoom_scale
    c = 0.5 * (mins + maxs)
    ax.set_xlim(c[0] - max_span, c[0] + max_span)
    ax.set_ylim(c[1] - max_span, c[1] + max_span)
    ax.set_zlim(c[2] - max_span, c[2] + max_span)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=10.5, fontweight="bold", color="#1f242b", pad=6)
    if hide_axes:
        ax.set_axis_off()
    else:
        ax.set_xlabel("X (mm)", fontsize=8)
        ax.set_ylabel("Y (mm)", fontsize=8)
        ax.set_zlabel("Z (mm)", fontsize=8)
        ax.tick_params(labelsize=7)


def render_overview_png(meshes: dict, solids: dict, params: dict, out_path: Path):
    fig = plt.figure(figsize=(16, 11), facecolor="#f5f4f0")
    fig.suptitle("2004 Ford Focus SVT Turbo — Stage-2 V2 (Dropped Plenum + 32° Forward / +14° Upward TB + Cable Boss)", fontsize=14.5, fontweight="bold", y=0.97, color="#1f242b")

    ls = LightSource(azdeg=210, altdeg=48)
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    _plot_mesh_panel(ax1, meshes["svt_intake_manifold_v2_1piece_full"], "Front-Top 3D View: Dropped Plenum, Rising Runners & Swept TB", 24, -62, "#46515c", zoom_scale=0.45, lightsource=ls)

    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    m_l, m_r = meshes["svt_intake_manifold_v2_split_left_cyl1_2"].copy(), meshes["svt_intake_manifold_v2_split_right_cyl3_4_tb"].copy()
    m_l.apply_translation([-22.0, 0.0, 0.0])
    m_r.apply_translation([22.0, 0.0, 0.0])
    _plot_mesh_panel(ax2, trimesh.util.concatenate([m_l, m_r]), "2-Piece Split Assembly (Centauri Carbon 2 Bed Fit)", 26, -32, "#346488", zoom_scale=0.45, lightsource=ls)

    ax3 = fig.add_subplot(2, 2, 3)
    ax3.set_facecolor("#ffffff")
    full_solid = solids["svt_intake_manifold_v2_1piece_full"]
    rot_x = full_solid.rotate([0.0, -90.0, 0.0])
    yz_polys = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in rot_x.slice(46.0).to_polygons()]
    _add_section_patches(ax3, yz_polys, facecolor="#4c5c6b", edgecolor="#1b2026", lw=0.9)
    sp_z = float(params["runners"]["spigot"]["center_z_mm"])
    boot_top_z = sp_z + 0.5 * float(params["runners"]["spigot"]["outer_height_mm"])
    ax3.axhline(boot_top_z, color="#c0392b", lw=1.3, ls="--", label=f"Top of 2\" Boot (+{boot_top_z:.1f} mm — Below FRPS/Strut Bar)")
    ax3.axhline(0.0, color="#999999", lw=0.6, ls=":")
    ax3.axvline(0.0, color="#999999", lw=0.6, ls=":")
    ax3.set_aspect("equal")
    ax3.set_xlim(-160, 75)
    ax3.set_ylim(-60, 110)
    ax3.grid(True, linestyle=":", alpha=0.5)
    ax3.legend(loc="lower right", fontsize=8)
    ax3.set_title("Section at Cyl 3 (X = +46 mm): Plenum Dropped -68 mm Below Boots", fontsize=10.8, fontweight="bold")
    ax3.set_xlabel("Y: Boots/Block (-Y) to Firewall (+Y) [mm]")
    ax3.set_ylabel("Z: Height [mm]")

    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor("#ffffff")
    _add_section_patches(ax4, [np.asarray(p) for p in full_solid.slice(sp_z).to_polygons()], facecolor="#2f5d80", edgecolor="#182a38", lw=0.9, alpha=0.88)
    for pts in [np.asarray(p) for p in full_solid.slice(0.0).to_polygons()]:
        closed = np.vstack([pts, pts[0]])
        ax4.plot(closed[:, 0], closed[:, 1], color="#c04b2b", lw=1.1, ls="--")
    for idx, xc in enumerate(params["runners"]["center_x_mm"], start=1):
        ax4.axvline(xc, color="#777777", lw=0.6, ls=":")
        ax4.text(xc, -156, f"Cyl {idx}\n({xc:+.0f})", ha="center", va="top", fontsize=8)
    ax4.axvline(0.0, color="#0d6e3f", lw=1.4, ls="-.")
    ax4.text(0.0, 62, "Split X=0", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#0d6e3f")
    ax4.text(215, -75, "TB -> -Y\n(Away from\nBrake Res)", ha="center", fontsize=8, color="#8b2500", fontweight="bold")
    ax4.set_aspect("equal")
    ax4.set_xlim(-210, 260)
    ax4.set_ylim(-172, 82)
    ax4.grid(True, linestyle=":", alpha=0.5)
    ax4.set_title("Plan Layout: Boot Spigots Z=+68 (Blue) & Plenum Z=0 (Dashed Red)", fontsize=10.8, fontweight="bold")
    ax4.set_xlabel("X: Cyl 1 (-X) to TB (+X) [mm]")
    ax4.set_ylabel("Y [mm]")

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_exterior_closeup_png(meshes: dict, solids: dict, params: dict, out_path: Path):
    fig = plt.figure(figsize=(16, 12), facecolor="#f5f4f0")
    fig.suptitle("Stage-2 V2 Packaging & Exterior Transition Inspection", fontsize=15, fontweight="bold", y=0.97, color="#1f242b")
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.22, left=0.06, right=0.97, top=0.91, bottom=0.06)

    full_mesh, right_mesh = meshes["svt_intake_manifold_v2_1piece_full"], meshes["svt_intake_manifold_v2_split_right_cyl3_4_tb"]
    full_solid = solids["svt_intake_manifold_v2_1piece_full"]
    ls = LightSource(azdeg=210, altdeg=48)

    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    _plot_mesh_panel(ax1, full_mesh, "Underside-Front View: Dropped Plenum, Root Fillets & Tie-Bars", -16, -95, "#3c4046", zoom_scale=0.40, lightsource=ls, hide_axes=True)

    ax2 = fig.add_subplot(gs[0, 1], projection="3d")
    _plot_mesh_panel(ax2, right_mesh, "Right Half: 32° Forward/+14° Up TB, Cable Boss & IACV (+Y Tap)", 26, -38, "#46586b", bounds_override=(np.array([15.0, -130.0, -45.0]), np.array([250.0, 75.0, 100.0])), zoom_scale=0.48, lightsource=ls)

    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor("#ffffff")
    rot_x = full_solid.rotate([0.0, -90.0, 0.0])
    polys3 = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in rot_x.slice(46.0).to_polygons()]
    _add_section_patches(ax3, polys3, facecolor="#4c5c6b", edgecolor="#161b22", lw=1.0, alpha=0.88)
    polys1 = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in rot_x.slice(-138.0).to_polygons()]
    for idx_p, p1 in enumerate(polys1):
        closed = np.vstack([p1, p1[0]])
        ax3.plot(closed[:, 0], closed[:, 1], color="#d95f02", lw=1.35, ls="--", label="Cyl 1 (X=-138)" if idx_p == 0 else None)
    ax3.axhline(93.4, color="#c0392b", lw=1.1, ls=":", label="Boot Top (+93.4 mm)")
    ax3.set_aspect("equal")
    ax3.set_xlim(-155, 62)
    ax3.set_ylim(-55, 105)
    ax3.grid(True, linestyle=":", alpha=0.5)
    ax3.legend(loc="upper right", fontsize=8.5)
    ax3.set_title("Conformal Rising Bellmouths: Cyl 3 (Solid) vs Cyl 1 (Dashed)", fontsize=10.5, fontweight="bold")
    ax3.set_xlabel("Y [mm]")
    ax3.set_ylabel("Z [mm]")

    sub = gs[1, 1].subgridspec(2, 1, hspace=0.38)
    ax4a = fig.add_subplot(sub[0, 0])
    ax4a.set_facecolor("#ffffff")
    _add_section_patches(ax4a, [np.asarray(p) for p in full_solid.slice(0.0).to_polygons()], facecolor="#2f5d80", edgecolor="#162836", lw=0.9)
    ax4a.set_aspect("equal")
    ax4a.set_xlim(-195, 230)
    ax4a.set_ylim(-90, 65)
    ax4a.grid(True, linestyle=":", alpha=0.5)
    ax4a.set_title("X-Y Slice at Z = 0 mm: C2 Tapered Plenum & Forward-Turning TB Throat", fontsize=10, fontweight="bold")
    ax4a.set_ylabel("Y [mm]")

    ax4b = fig.add_subplot(sub[1, 0])
    ax4b.set_facecolor("#ffffff")
    rot_y = full_solid.rotate([90.0, 0.0, 0.0])
    _add_section_patches(ax4b, [np.column_stack([np.asarray(p)[:, 0], -np.asarray(p)[:, 1]]) for p in rot_y.slice(-98.0).to_polygons()], facecolor="#1f7a68", edgecolor="#0f3d34", lw=0.9)
    ax4b.set_aspect("equal")
    ax4b.set_xlim(-175, 175)
    ax4b.set_ylim(10, 88)
    ax4b.grid(True, linestyle=":", alpha=0.5)
    ax4b.set_title("X-Z Slice at Y = -98 mm: SDF Tie-Bars Bridging Rising Runners", fontsize=10, fontweight="bold")
    ax4b.set_xlabel("X [mm]")
    ax4b.set_ylabel("Z [mm]")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_bellmouth_sections_png(mesh: trimesh.Trimesh, params: dict, root_audit: list[dict], out_path: Path):
    """Render Cyl 3 (s=10) and Cyl 4 (s=14) transverse root sections confirming elimination of sharp internal lips."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained")
    ang_deg = 175.37
    ang_rad = math.radians(ang_deg)
    ray = np.array([math.cos(ang_rad), math.sin(ang_rad)])
    for ax, (cyl, xc, st) in zip(axes, [(3, 46.0, 10.0), (4, 138.0, 14.0)]):
        tip, axis, *_ = runner_bezier_points(xc, params)
        lines = _section_2d(mesh, tip + st * axis, axis)
        hits = _ray_distances(lines, ray)
        ax.add_collection(LineCollection(lines, colors="#384452", linewidths=1.3))
        if len(hits) >= 2:
            pts = hits[:2, None] * ray
            ax.plot(*pts.T, "o-", color="#117864", markersize=4, lw=2.0, label=f"{hits[1]-hits[0]:.2f} mm continuous wall @ {ang_deg}°")
            c_xy = pts.mean(axis=0)
            ax.set(xlim=(c_xy[0] - 8, c_xy[0] + 8), ylim=(c_xy[1] - 7, c_xy[1] + 7), aspect="equal")
        rec = next(r for r in root_audit if r["cylinder"] == cyl)
        ax.set_title(f"Cyl {cyl} | {st:g} mm (min_wall={rec['min_pressure_wall_mm']:.2f} mm, all_span={rec['min_all_ray_span_mm']:.2f} mm)", fontsize=10, fontweight="bold")
        ax.set_xlabel("Local U (mm)")
        ax.set_ylabel("Local V (mm)")
        ax.grid(alpha=0.25)
        ax.legend(loc="lower left", fontsize=8.5)
    fig.suptitle("Stage-2 V2 Conformal Quarter-Circle Bellmouth Root Audit (Zero Sharp Internal Lips)", fontsize=11.5, fontweight="bold")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=170)
    plt.close(fig)


def render_1to1_svg(solids: dict[str, md.Manifold], params: dict, out_path: Path):
    spigot_sec = solids["svt_v2_runner_boot_fit_gauge"].slice(24.0).to_polygons()
    split_sec = solids["svt_intake_manifold_v2_split_left_cyl1_2"].rotate([0.0, -90.0, 0.0]).slice(-1.0).to_polygons()
    tb_sec = solids["svt_v2_tb_flange_fit_gauge"].slice(2.0).to_polygons()
    iacv_sec = solids["svt_v2_iacv_flange_fit_gauge"].slice(2.0).to_polygons()

    sp_cfg = params["runners"]["spigot"]
    sp_out_w, sp_in_w = sp_cfg["outer_width_mm"], sp_cfg["outer_width_mm"] - 2.0 * sp_cfg["wall_thickness_mm"]
    centers = [
        (f'Silicone Boot Spigot\n(Ø{sp_out_w:.1f} outer / Ø{sp_in_w:.1f} inner — 2" Boot)', spigot_sec, (55.0, 88.0), lambda p: (p[0], -p[1])),
        ("Center Split Flange\n(6x M6 + 2x 6mm Dowel + O-Ring)", split_sec, (195.0, 88.0), lambda p: (p[1], p[0])),
        ("65mm Throttle Body Flange\n(70x70 mm 4-Bolt Pattern)", tb_sec, (345.0, 88.0), lambda p: (p[0], -p[1])),
        ("2-Bolt Ford IACV Flange\n(46mm Bolts / Dual 13mm Ports)", iacv_sec, (465.0, 88.0), lambda p: (p[0], -p[1])),
    ]
    width_mm, height_mm = 530.0, 175.0
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width_mm * 0.5:.1f}" y="12" text-anchor="middle" font-family="sans-serif" font-size="6" font-weight="bold" fill="#111">2004 Focus SVT V2 Intake Manifold — 1:1 Interface Templates (mm)</text>',
    ]
    for label, polys, (cx, cy), map_fn in centers:
        for poly in polys:
            pts = " ".join(f"{cx + map_fn(p)[0]:.3f},{cy + map_fn(p)[1]:.3f}" for p in poly)
            lines.append(f'<polygon points="{pts}" fill="none" stroke="#1f4e79" stroke-width="0.35"/>')
        for idx, line in enumerate(label.split("\n")):
            lines.append(f'<text x="{cx}" y="{162 + idx * 5}" text-anchor="middle" font-family="sans-serif" font-size="4.2" fill="#333">{line}</text>')
    lines.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Export & Production Audit
# ---------------------------------------------------------------------------

def main():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    STL_DIR.mkdir(parents=True, exist_ok=True)
    FITMENT_DIR.mkdir(parents=True, exist_ok=True)

    solids = assemble_all(params)
    meshes: dict[str, trimesh.Trimesh] = {}
    manifest_parts: dict[str, dict] = {}
    printers = params["printers"]
    cc2, e3 = printers["centauri_carbon_2"], printers["ender_3_s1_pro"]

    for name, solid in solids.items():
        if name.startswith("_"):
            continue
        mesh = manifold_to_trimesh(solid)
        assert mesh.is_watertight and mesh.is_volume and mesh.body_count == 1, f"{name} failed mesh integrity check"
        meshes[name] = mesh

        stl_path = STL_DIR / f"{name}.stl"
        mesh.export(stl_path)
        sha256 = hashlib.sha256(stl_path.read_bytes()).hexdigest()
        bmin, bmax = mesh.bounds[0], mesh.bounds[1]
        ext = bmax - bmin
        manifest_parts[name] = {
            "file": f"stl/{name}.stl",
            "sha256": sha256,
            "is_watertight": bool(mesh.is_watertight),
            "is_volume": bool(mesh.is_volume),
            "body_count": int(mesh.body_count),
            "triangle_count": int(len(mesh.faces)),
            "extents_mm": [round(float(v), 2) for v in ext],
            "bounds_min_mm": [round(float(v), 2) for v in bmin],
            "bounds_max_mm": [round(float(v), 2) for v in bmax],
            "solid_volume_cm3": round(float(mesh.volume) / 1000.0, 2),
            "fits_centauri_carbon_2_256": bool(ext[0] <= cc2["bed_x_mm"] and ext[1] <= cc2["bed_y_mm"] and ext[2] <= cc2["bed_z_mm"]),
            "fits_ender_3_s1_pro_220": bool(ext[0] <= e3["bed_x_mm"] and ext[1] <= e3["bed_y_mm"] and ext[2] <= e3["bed_z_mm"]),
        }

    full_mesh = meshes["svt_intake_manifold_v2_1piece_full"]

    # 1) Single continuous C-section check across all 4 cylinders
    rot_x = solids["svt_intake_manifold_v2_1piece_full"].rotate([0.0, -90.0, 0.0])
    for xc_check in params["runners"]["center_x_mm"]:
        polys_chk = [ShapelyPolygon(p) for p in rot_x.slice(xc_check).to_polygons() if len(p) >= 3]
        assert len(polys_chk) == 1 and polys_chk[0].area > 1500.0 and polys_chk[0].is_valid, f"Section X={xc_check} invalid"

    # 2) Bed fit on CC2 (256 mm cube)
    for half_name in ("svt_intake_manifold_v2_split_left_print_oriented", "svt_intake_manifold_v2_split_right_print_oriented"):
        assert manifest_parts[half_name]["fits_centauri_carbon_2_256"], f"{half_name} exceeds CC2 256 mm bed: {manifest_parts[half_name]['extents_mm']}"

    # 3) Washer & Ø12.4 mm socket clearance on split bolts and TB bolts
    cs, pl = params["center_split"], params["plenum"]
    x_sp, t_half = float(cs["split_x_mm"]), float(cs["flange_thickness_per_side_mm"])
    s_sp = math.sqrt(plenum_area_scale(x_sp, params))
    pts_sp = rounded_rect_points(pl["inner_width_y_mm"] * s_sp, pl["inner_height_z_mm"] * s_sp, pl["inner_corner_radius_mm"] * s_sp, 720)
    angs_sp = np.degrees(np.arctan2(pts_sp[:, 1], pts_sp[:, 0])) % 360.0
    sp_l, sp_r = solids["svt_intake_manifold_v2_split_left_cyl1_2"], solids["svt_intake_manifold_v2_split_right_cyl3_4_tb"]
    for ang in cs["bolt_angles_deg"]:
        idx = int(np.argmin(np.abs(((angs_sp - (ang % 360.0) + 180.0) % 360.0) - 180.0)))
        tang = pts_sp[(idx + 1) % 720] - pts_sp[(idx - 1) % 720]
        nrm = np.array([tang[1], -tang[0]])
        by, bz = pts_sp[idx] + (nrm / np.linalg.norm(nrm)) * (pl["wall_thickness_mm"] + cs["bolt_radial_offset_mm"])
        assert (sp_l ^ make_cylinder_along(np.array([x_sp - t_half - 18.0, by, bz]), np.array([x_sp - t_half - 0.3, by, bz]), 6.2, 24)).volume() < 0.1
        assert (sp_r ^ make_cylinder_along(np.array([x_sp + t_half + 0.3, by, bz]), np.array([x_sp + t_half + 18.0, by, bz]), 6.2, 24)).volume() < 0.1

    _, _, _, _, p_fb, _, tb_axis = tb_neck_bezier_points(params)
    u_chk = np.cross(np.array([0.0, 0.0, 1.0]), tb_axis)
    u_chk /= np.linalg.norm(u_chk)
    v_chk = np.cross(tb_axis, u_chk)
    v_chk /= np.linalg.norm(v_chk)
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pc_b = p_fb + u_chk * (sx * params["throttle_body"]["bolt_spacing_x_mm"] * 0.5) + v_chk * (sy * params["throttle_body"]["bolt_spacing_y_mm"] * 0.5)
            iv_tb = float((sp_r ^ make_cylinder_along(pc_b - tb_axis * 12.5, pc_b - tb_axis * 0.3, 6.2, 24)).volume())
            assert iv_tb < 0.1, f"TB bolt ({sx},{sy}) socket interference: {iv_tb:.2f} mm3"

    # 4) Codex 72-ray transverse runner root wall audit (all 4 cyls x 12 stations)
    root_audit = audit_runner_root_walls_72ray(full_mesh, params)
    for rec in root_audit:
        assert rec["min_pressure_wall_mm"] >= 4.5, f"Cyl {rec['cylinder']} thin pressure wall: {rec}"
        assert rec["min_all_ray_span_mm"] >= 2.5, f"Cyl {rec['cylinder']} thin internal chord: {rec}"

    # 5) Codex 468-ray 2D IACV pocket floor audit
    iacv_audit = audit_iacv_floor_468ray(full_mesh, params)
    assert iacv_audit["samples"] == 468 and iacv_audit["min_wall_mm"] >= 4.5, f"IACV 468-ray audit failed: {iacv_audit}"

    # 6) Cable bracket boss wall audit
    cable_audit = audit_cable_boss_walls(solids, params)
    assert cable_audit is None or cable_audit["min_solid_wall_to_bore_mm"] >= 4.5, f"Cable boss thin wall: {cable_audit}"

    pl_mesh = manifold_to_trimesh(solids["_plenum_inner_cavity"])
    plenum_liters = round(float(pl_mesh.volume) / 1_000_000.0, 3)

    manifest = {
        "vehicle": params["metadata"]["vehicle"],
        "revision": params["metadata"]["revision"],
        "plenum_internal_volume_liters": plenum_liters,
        "runner_pitch_mm": params["runners"]["pitch_mm"],
        "spigot_outer_mm": [params["runners"]["spigot"]["outer_width_mm"], params["runners"]["spigot"]["outer_height_mm"]],
        "spigot_inner_mm": [params["runners"]["spigot"]["outer_width_mm"] - 2.0 * params["runners"]["spigot"]["wall_thickness_mm"], params["runners"]["spigot"]["outer_height_mm"] - 2.0 * params["runners"]["spigot"]["wall_thickness_mm"]],
        "throttle_body_bore_mm": params["throttle_body"]["bore_diameter_mm"],
        "runner_root_wall_audit": root_audit,
        "iacv_floor_468ray_audit": iacv_audit,
        "cable_bracket_boss_audit": cable_audit,
        "parts": manifest_parts,
    }
    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    render_overview_png(meshes, solids, params, FITMENT_DIR / "01_intake_manifold_v2_overview.png")
    render_1to1_svg(solids, params, FITMENT_DIR / "02_interfaces_1to1_template_v2.svg")
    render_exterior_closeup_png(meshes, solids, params, FITMENT_DIR / "05_exterior_transitions_closeup.png")
    render_bellmouth_sections_png(full_mesh, params, root_audit, FITMENT_DIR / "06_bellmouth_internal_sections.png")

    print(f"Generated {len(meshes)} watertight V2 STLs. Plenum volume: {plenum_liters:.3f} L")
    print(f"IACV 468-ray floor: center={iacv_audit['centerline_wall_mm']} mm, min={iacv_audit['min_wall_mm']} mm")
    print(f"Cable boss wall: {cable_audit}")
    for rec in root_audit:
        print(f"  Cyl {rec['cylinder']} root audit: press_wall_min={rec['min_pressure_wall_mm']} mm, all_ray_min={rec['min_all_ray_span_mm']} mm")
    for pname, info in manifest_parts.items():
        print(f"  {pname}: {info['extents_mm']} mm | vol={info['solid_volume_cm3']} cm3 | CC2={info['fits_centauri_carbon_2_256']}")


if __name__ == "__main__":
    main()
