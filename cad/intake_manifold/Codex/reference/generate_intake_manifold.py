#!/usr/bin/env python3
"""
Parametric 3D-Printable Intake Manifold Generator for 2004 Ford Focus SVT (2.0L Zetec Turbo).

Replaces the OEM upper plastic IMRC/DSI manifold between the throttle body (TB)
and the 4 silicone coupler boots attached to the retained cylinder-head lower
manifold (which holds the OEM fuel rail and injectors).

Outputs:
  stl/svt_intake_manifold_1piece_full.stl
  stl/svt_intake_manifold_split_left_cyl1_2.stl
  stl/svt_intake_manifold_split_right_cyl3_4_tb.stl
  stl/svt_intake_manifold_split_left_print_oriented.stl
  stl/svt_intake_manifold_split_right_print_oriented.stl
  stl/svt_runner_boot_fit_gauge.stl
  stl/svt_tb_flange_fit_gauge.stl
  stl/manifest.json
  fitment/01_intake_manifold_overview.png
  fitment/02_interfaces_1to1_template.svg
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
from matplotlib.colors import LightSource
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon as ShapelyPolygon
import trimesh

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_parameters.json"
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
    # Corner centers: Q1 (+,+), Q2 (-,+), Q3 (-,-), Q4 (+,-)
    corners = [
        (width * 0.5 - r, height * 0.5 - r),
        (-(width * 0.5 - r), height * 0.5 - r),
        (-(width * 0.5 - r), -(height * 0.5 - r)),
        (width * 0.5 - r, -(height * 0.5 - r)),
    ]
    for c_idx, (cx, cy) in enumerate(corners):
        angles = np.linspace(c_idx * 90.0 + 0.25, (c_idx + 1) * 90.0 - 0.25, per_corner)
        rad = np.radians(angles)
        for a in rad:
            pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return np.asarray(pts, dtype=np.float64)


def ellipse_points(width: float, height: float, total_pts: int = 64) -> np.ndarray:
    """
    Generate (N, 2) CCW points for a smooth ellipse of full extents `width` x `height`.
    When `width == height`, produces an exact circle.
    """
    angles = np.linspace(0.0, 2.0 * math.pi, total_pts, endpoint=False)
    a = 0.5 * width
    b = 0.5 * height
    return np.column_stack([a * np.cos(angles), b * np.sin(angles)]).astype(np.float64)


def ring_frame_points(
    center: np.ndarray,
    tangent: np.ndarray,
    up_hint: np.ndarray,
    profile_uv: np.ndarray,
) -> np.ndarray:
    """
    Embed a 2D (N, 2) profile onto a 3D frame orthogonal to `tangent`.
    `u` aligns with `right = tangent x up_hint`, `v` aligns with `binormal = right x tangent`.
    Looking in the `-tangent` direction (from ring i+1 back to i), `(u, v)` is CCW if
    frame is right-handed `(u, v, tangent)`.
    Let's enforce right-handed basis: `u_axis` x `v_axis` == `+tangent_hat`.
    """
    t_hat = tangent / np.linalg.norm(tangent)
    u_axis = np.cross(up_hint, t_hat)
    if np.linalg.norm(u_axis) < 1e-6:
        fallback = np.array([1.0, 0.0, 0.0]) if abs(t_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u_axis = np.cross(fallback, t_hat)
    u_axis = u_axis / np.linalg.norm(u_axis)
    v_axis = np.cross(t_hat, u_axis)
    v_axis = v_axis / np.linalg.norm(v_axis)
    # Right-handed check: u x v == t_hat
    return center[None, :] + profile_uv[:, 0:1] * u_axis[None, :] + profile_uv[:, 1:2] * v_axis[None, :]


def loft_closed_solid(rings: list[np.ndarray]) -> trimesh.Trimesh:
    """
    Loft a sequence of 3D rings (each shape (N, 3) with right-handed CCW order
    around the forward path direction) into a closed, watertight Trimesh.
    """
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
            # Outward normal for right-handed CCW rings advancing along +tangent
            faces.append([base0 + i, base0 + j, base1 + j])
            faces.append([base0 + i, base1 + j, base1 + i])

    # Cap start ring (ring 0, normal pointing -tangent)
    c_start_idx = len(verts)
    verts.append(rings[0].mean(axis=0))
    for i in range(n_pts):
        j = (i + 1) % n_pts
        faces.append([c_start_idx, j, i])

    # Cap end ring (ring -1, normal pointing +tangent)
    c_end_idx = len(verts)
    verts.append(rings[-1].mean(axis=0))
    last_base = (n_rings - 1) * n_pts
    for i in range(n_pts):
        j = (i + 1) % n_pts
        faces.append([c_end_idx, last_base + i, last_base + j])

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
    verts = np.asarray(m.vert_properties[:, :3], dtype=np.float64)
    faces = np.asarray(m.tri_verts, dtype=np.int64)
    # Keep exact manifold vertex/face indexing (process=True can merge close float32 cuts)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    return mesh


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
    cs = md.CrossSection([uv.tolist()])
    solid = md.Manifold.extrude(cs, length).translate([0.0, 0.0, -length * 0.5])
    if axis == "x":
        # Rotate +90 around Z (X->+Y, Y->-X), then +90 around Y (-X->+Z, +Z->+X):
        # Result: width->Y, height->Z, length->X
        solid = solid.rotate([0.0, 0.0, 90.0]).rotate([0.0, 90.0, 0.0])
    elif axis == "y":
        # Rotate -90 deg around X maps +Z -> +Y
        solid = solid.rotate([-90.0, 0.0, 0.0])
    elif axis == "z":
        pass
    else:
        raise ValueError(f"Unsupported axis {axis}")
    if center != (0.0, 0.0, 0.0):
        solid = solid.translate(list(center))
    return solid


def make_cylinder_along(
    p0: np.ndarray,
    p1: np.ndarray,
    radius: float,
    segments: int = 48,
) -> md.Manifold:
    """Create a cylinder spanning from 3D point p0 to p1."""
    vec = p1 - p0
    length = float(np.linalg.norm(vec))
    assert length > 1e-4
    cyl = md.Manifold.cylinder(length, radius, radius, circular_segments=segments, center=True)
    mesh = manifold_to_trimesh(cyl)
    z_axis = np.array([0.0, 0.0, 1.0])
    t_hat = vec / length
    mat = trimesh.geometry.align_vectors(z_axis, t_hat)
    mesh.apply_transform(mat)
    mesh.apply_translation((p0 + p1) * 0.5)
    return trimesh_to_manifold(mesh)


# ---------------------------------------------------------------------------
# Parametric Sub-Assemblies
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
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0))
    inside = min(max(qx, qy), 0.0)
    return outside + inside - r_c


def plenum_outer_sdf(pt: np.ndarray, params: dict) -> float:
    """Signed distance to outer plenum barrel surface (>0 outside, <0 inside)."""
    p = params["plenum"]
    wall = float(p["wall_thickness_mm"])
    w_base = float(p["inner_width_y_mm"]) + 2.0 * wall
    h_base = float(p["inner_height_z_mm"]) + 2.0 * wall
    r_base = float(p["inner_corner_radius_mm"]) + wall
    x_clamped = float(np.clip(pt[0], p["cyl1_end_x_mm"], p["cyl4_end_x_mm"]))
    scale = math.sqrt(plenum_area_scale(x_clamped, params))
    return _rounded_rect_sdf_2d(float(pt[1]), float(pt[2]), w_base * scale, h_base * scale, r_base * scale)


def plenum_outer_sdf_and_normal(pt: np.ndarray, params: dict) -> tuple[float, np.ndarray]:
    """Return (signed_distance_mm, unit_outward_normal_3d) to outer plenum barrel surface."""
    d0 = plenum_outer_sdf(pt, params)
    eps = 0.2
    dx = (plenum_outer_sdf(pt + np.array([eps, 0.0, 0.0]), params) - d0) / eps
    dy = (plenum_outer_sdf(pt + np.array([0.0, eps, 0.0]), params) - d0) / eps
    dz = (plenum_outer_sdf(pt + np.array([0.0, 0.0, eps]), params) - d0) / eps
    g = np.array([dx, dy, dz], dtype=np.float64)
    n_len = float(np.linalg.norm(g))
    if n_len < 1e-8:
        return d0, np.array([0.0, -1.0, 0.0], dtype=np.float64)
    return d0, g / n_len


def build_plenum_loft(params: dict, is_inner: bool) -> md.Manifold:
    """
    Build either the outer plenum shell or the inner plenum cavity.
    Includes smooth ellipsoidal dome on the Cyl 1 (-X) end and tapered barrel
    extending to Cyl 4 (+X) end.
    """
    p = params["plenum"]
    wall = p["wall_thickness_mm"]
    w_base = p["inner_width_y_mm"] + (0.0 if is_inner else 2.0 * wall)
    h_base = p["inner_height_z_mm"] + (0.0 if is_inner else 2.0 * wall)
    r_base = p["inner_corner_radius_mm"] + (0.0 if is_inner else wall)
    n_pts = p["profile_segments"]

    x_dome_tip = p["cyl1_end_x_mm"] - (p["cyl1_dome_length_mm"] - (wall if is_inner else 0.0))
    x_cyl1 = p["cyl1_end_x_mm"]
    x_cyl4 = p["cyl4_end_x_mm"] + (-2.0 if is_inner else 2.0)

    rings: list[np.ndarray] = []
    # 1) Ellipsoidal dome from tip to cyl1 end
    dome_len = x_cyl1 - x_dome_tip
    dome_steps = int(p.get("cyl1_dome_steps", 44))
    thetas = np.linspace(0.04, math.pi * 0.5, dome_steps, endpoint=False)
    s_cyl1 = math.sqrt(p["taper_cyl1_area_ratio"])
    for th in thetas:
        x = x_cyl1 - dome_len * math.cos(th)
        dome_scale = math.sin(th) * s_cyl1
        uv = rounded_rect_points(w_base * dome_scale, h_base * dome_scale, r_base * dome_scale, n_pts)
        # In (X, Y, Z) with +X tangent: right-handed u=+Y, v=+Z => (x, u, v)
        ring = np.column_stack([np.full(n_pts, x), uv[:, 0], uv[:, 1]])
        rings.append(ring)

    # 2) Tapered plenum barrel from x_cyl1 to x_cyl4
    xs = np.linspace(x_cyl1, x_cyl4, p["axial_segments"])
    x_split = float(params.get("center_split", {}).get("split_x_mm", 0.0))
    if p.get("split_x_area_ratio") is not None and x_cyl1 < x_split < x_cyl4:
        if not np.any(np.isclose(xs, x_split, atol=1e-4)):
            xs = np.sort(np.append(xs, x_split))
    for x in xs:
        s = math.sqrt(plenum_area_scale(float(x), params))
        uv = rounded_rect_points(w_base * s, h_base * s, r_base * s, n_pts)
        ring = np.column_stack([np.full(n_pts, float(x)), uv[:, 0], uv[:, 1]])
        rings.append(ring)

    mesh = loft_closed_solid(rings)
    return trimesh_to_manifold(mesh)


def bezier_point_and_tangent(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float):
    u = 1.0 - t
    pt = (u**3) * p0 + 3 * (u**2) * t * p1 + 3 * u * (t**2) * p2 + (t**3) * p3
    tan = 3 * (u**2) * (p1 - p0) + 6 * u * t * (p2 - p1) + 3 * (t**2) * (p3 - p2)
    return pt, tan


def tb_neck_bezier_points(params: dict) -> tuple[np.ndarray, ...]:
    """Return cubic-Bezier control points and endpoints for the throttle body neck."""
    tb = params["throttle_body"]
    pl = params["plenum"]
    x_start = float(pl["cyl4_end_x_mm"])
    p_start = np.array([x_start - 4.0, 0.0, 0.0])
    cant_rad = math.radians(tb["forward_cant_deg"])
    tb_axis = np.array([math.cos(cant_rad), math.sin(cant_rad), 0.0])
    p_flange_back = np.array([x_start, 0.0, 0.0]) + tb_axis * float(tb["neck_length_mm"])
    p_flange_face = p_flange_back + tb_axis * float(tb["flange_thickness_mm"])
    p_neck_end = p_flange_back + tb_axis * 4.0
    chord = float(np.linalg.norm(p_neck_end - p_start))
    c0 = p_start + np.array([1.0, 0.0, 0.0]) * (0.38 * chord)
    c1 = p_neck_end - tb_axis * (0.38 * chord)
    return p_start, c0, c1, p_neck_end, p_flange_back, p_flange_face, tb_axis


def runner_bezier_points(x_center: float, params: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (p_bm_tip, inlet_dir, p0, p1, p2, p3) for a runner at `x_center`."""
    r_cfg = params["runners"]
    sp = r_cfg["spigot"]
    bm = r_cfg["bellmouth"]
    wall_flush = bool(bm.get("wall_flush_bellmouth", False))
    cyl_idx = min(range(len(r_cfg["center_x_mm"])), key=lambda idx: abs(r_cfg["center_x_mm"][idx] - x_center))
    scoop_angles = bm.get("axial_entry_angles_deg", [0.0, 0.0, 0.0, 0.0])
    alpha_x_deg = float(scoop_angles[cyl_idx]) if (wall_flush and cyl_idx < len(scoop_angles)) else 0.0
    ax_rad = math.radians(alpha_x_deg)
    el_rad = math.radians(18.0)
    inlet_dir = np.array([
        -math.sin(ax_rad),
        -math.cos(el_rad) * math.cos(ax_rad),
        -math.sin(el_rad) * math.cos(ax_rad),
    ])
    if wall_flush:
        s_x = math.sqrt(plenum_area_scale(x_center, params))
        y_plenum_rear_in = -0.5 * params["plenum"]["inner_width_y_mm"] * s_x
        p_bm_tip = np.array([x_center + 14.0 * math.sin(ax_rad), y_plenum_rear_in + 9.0, -5.0])
        p0 = p_bm_tip + inlet_dir * 18.0
    else:
        p_bm_tip = np.array([x_center, -24.0, -10.0])
        p0 = p_bm_tip + inlet_dir * 16.0
    sweep_end_y = float(sp["tip_y_mm"]) + float(sp["land_length_mm"])
    p3 = np.array([x_center, sweep_end_y, float(sp["center_z_mm"])])
    p1 = p0 + inlet_dir * 26.0
    p2 = p3 + np.array([0.0, 32.0, 0.0])
    return p_bm_tip, inlet_dir, p0, p1, p2, p3


def build_single_runner_components(x_center: float, params: dict) -> dict[str, md.Manifold]:
    """
    For one cylinder at `x_center`, build:
      - `outer`: smooth swept outer runner + C^inf curvature-compensated root fillet + straight spigot + crowned bead
      - `bellmouth_outer`: protruding bellmouth sleeve outer (None when wall_flush=True, integrated in `outer`)
      - `inner_bore`: continuous bore from flared bellmouth lip inside plenum to past spigot tip
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
    entry_wall = max(wall, 5.5)
    entry_w_out = entry_w_in + 2.0 * entry_wall
    entry_h_out = entry_h_in + 2.0 * entry_wall
    entry_r_out = entry_r_in + entry_wall

    tip_y = sp["tip_y_mm"]
    land_len = sp["land_length_mm"]
    sweep_end_y = tip_y + land_len
    sp_z = sp["center_z_mm"]

    p_bm_tip, inlet_dir, p0, p1, p2, p3 = runner_bezier_points(x_center, params)
    throat_len = float(np.linalg.norm(p0 - p_bm_tip))

    up_hint = np.array([0.0, 0.0, 1.0])
    n_loft = sw["loft_segments"]
    bm_len = bm["protrusion_into_plenum_mm"]
    bm_flare = bm["flare_radial_mm"]
    bm_wall = bm["wall_thickness_mm"]

    s_x = math.sqrt(plenum_area_scale(x_center, params)) if wall_flush else 1.0
    bm_flare_eff = bm_flare * (0.75 + 0.25 * s_x) if wall_flush else bm_flare

    def _profile_pts(w: float, h: float, r: float) -> np.ndarray:
        return ellipse_points(w, h, n_pts) if wall_flush else rounded_rect_points(w, h, r, n_pts)

    # 1) Outer runner skin
    outer_rings: list[np.ndarray] = []
    if wall_flush:
        r_f = float(bm.get("exterior_fillet_z_mm", 11.0)) * s_x

        def fillet_ring_smooth(
            ring_pts: np.ndarray,
            uv: np.ndarray,
            tangent: np.ndarray,
            f_wt: float = 1.0,
        ) -> np.ndarray:
            if f_wt <= 1e-4:
                return ring_pts
            t_hat = tangent / np.linalg.norm(tangent)
            u_ax = np.cross(up_hint, t_hat)
            if np.linalg.norm(u_ax) < 1e-6:
                u_ax = np.array([1.0, 0.0, 0.0])
            u_ax = u_ax / np.linalg.norm(u_ax)
            v_ax = np.cross(t_hat, u_ax)
            v_ax = v_ax / np.linalg.norm(v_ax)

            out = ring_pts.copy()
            for idx in range(len(out)):
                p_base = out[idx]
                d, n_pl = plenum_outer_sdf_and_normal(p_base, params)
                if d >= r_f:
                    continue
                n_rad = uv[idx, 0] * u_ax + uv[idx, 1] * v_ax
                nr_len = float(np.linalg.norm(n_rad))
                if nr_len < 1e-6:
                    continue
                n_rad = n_rad / nr_len
                t_surf = n_rad - float(np.dot(n_rad, n_pl)) * n_pl
                ts_len = float(np.linalg.norm(t_surf))
                t_surf = (t_surf / ts_len) if ts_len > 1e-6 else n_rad

                u = float(np.clip(1.0 - max(d, 0.0) / r_f, 0.0, 1.0))
                fade_in = float(np.clip((d + 6.0) / 6.0, 0.0, 1.0))
                fade_in = f_wt * fade_in * fade_in * (3.0 - 2.0 * fade_in)
                delta_t = fade_in * r_f * (1.0 - math.sqrt(max(0.0, 1.0 - (0.82 * u) ** 2)))
                p_tang = p_base + delta_t * t_surf
                d_tang, n_tang = plenum_outer_sdf_and_normal(p_tang, params)
                d_target = d - fade_in * 0.15 * (u ** 4)
                out[idx] = p_tang + (d_target - d_tang) * n_tang
            return out

        # Clean constant elliptical entry stub + branch-free C^inf root fillet (s_dist = -4.0 -> throat_len)
        uv_entry_out = ellipse_points(entry_w_out, entry_h_out, n_pts)
        for s_dist in np.linspace(-4.0, throat_len, 32):
            pos = p_bm_tip + inlet_dir * float(s_dist)
            ring = ring_frame_points(pos, inlet_dir, up_hint, uv_entry_out)
            outer_rings.append(fillet_ring_smooth(ring, uv_entry_out, inlet_dir, f_wt=1.0))

        # Bezier sweep from k=1..n_loft with smooth taper-out of root fillet over t <= 0.42
        for k in range(1, n_loft + 1):
            t = k / n_loft
            pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
            s_t = 0.5 - 0.5 * math.cos(math.pi * t)
            w = entry_w_out + (sp_w_out - entry_w_out) * s_t
            h = entry_h_out + (sp_h_out - entry_h_out) * s_t
            uv = ellipse_points(w, h, n_pts)
            ring = ring_frame_points(pt, tan, up_hint, uv)
            if t < 0.42:
                f_wt = 0.5 + 0.5 * math.cos(math.pi * (t / 0.42))
                ring = fillet_ring_smooth(ring, uv, tan, f_wt=f_wt)
            outer_rings.append(ring)
    else:
        for k in range(n_loft + 1):
            t = k / n_loft
            pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
            s_t = 0.5 - 0.5 * math.cos(math.pi * t)
            w = entry_w_out + (sp_w_out - entry_w_out) * s_t
            h = entry_h_out + (sp_h_out - entry_h_out) * s_t
            r = entry_r_out + (sp_r_out - entry_r_out) * s_t
            uv = rounded_rect_points(w, h, r, n_pts)
            outer_rings.append(ring_frame_points(pt, tan, up_hint, uv))

    # Straight spigot land from sweep_end_y to tip_y with smooth crowned retention bead & tip chamfer
    bead_h = sp["retention_bead_height_mm"]
    bead_w = sp["retention_bead_width_mm"]
    bead_off = sp["retention_bead_offset_from_tip_mm"]
    y_bead_start = tip_y + bead_off
    y_bead_end = y_bead_start + bead_w
    spigot_stations: list[tuple[float, float]] = [
        (float(y_s), 0.0) for y_s in np.linspace(sweep_end_y, y_bead_end, 12)[1:]
    ]
    for b_idx in range(1, 20):
        frac = b_idx / 20.0
        yb = y_bead_end - frac * bead_w
        dr = bead_h * math.sin(math.pi * frac)
        spigot_stations.append((yb, dr))
    spigot_stations.extend([
        (y_bead_start, 0.0),
        (tip_y + 0.8, 0.0),
        (tip_y, -0.8),
    ])
    tan_sp = np.array([0.0, -1.0, 0.0])
    for y_pos, dr in spigot_stations:
        uv = _profile_pts(sp_w_out + 2.0 * dr, sp_h_out + 2.0 * dr, sp_r_out + dr)
        outer_rings.append(ring_frame_points(np.array([x_center, y_pos, sp_z]), tan_sp, up_hint, uv))

    outer_solid = trimesh_to_manifold(loft_closed_solid(outer_rings))

    # 2) Internal velocity-stack bellmouth outer solid (only needed when protruding inside plenum)
    bellmouth_outer = None
    if not wall_flush:
        bm_rings: list[np.ndarray] = []
        p_bm_anchor = p0 + inlet_dir * 10.0  # inside runner stub
        bm_total_len = float(np.linalg.norm(p_bm_anchor - p_bm_tip))
        n_bm = 20
        for k in range(n_bm + 1):
            s_dist = (k / n_bm) * bm_total_len
            pos = p_bm_tip + inlet_dir * float(s_dist)
            u = np.clip(s_dist / bm_len, 0.0, 1.0)
            inner_flare = bm_flare * ((1.0 - u) ** 2)
            w_out = entry_w_in + 2.0 * inner_flare + 2.0 * bm_wall
            h_out = entry_h_in + 2.0 * inner_flare + 2.0 * bm_wall
            r_out = entry_r_in + inner_flare + bm_wall
            if k == 0:
                w_out -= 2.2
                h_out -= 2.2
                r_out -= 1.1
            uv = rounded_rect_points(w_out, h_out, r_out, n_pts)
            bm_rings.append(ring_frame_points(pos, inlet_dir, up_hint, uv))
        bellmouth_outer = trimesh_to_manifold(loft_closed_solid(bm_rings))

    # 3) Continuous inner air bore (inside plenum -> bellmouth -> Bezier sweep -> past spigot tip)
    bore_rings: list[np.ndarray] = []
    if wall_flush:
        s_lead = -4.5
        s_samples = np.linspace(s_lead, throat_len - 0.8, 40)
        angles = np.linspace(0.0, 2.0 * math.pi, n_pts, endpoint=False)
        cos_a = np.cos(angles)
        sin_a = np.sin(angles)
        v_flare_wt = np.where(sin_a > 0.0, 1.0 - 0.78 * sin_a, 1.0)
        for s_dist in s_samples:
            pos = p_bm_tip + inlet_dir * float(s_dist)
            if s_dist < 0.0:
                flare_r = bm_flare_eff + 1.5 * (1.0 - math.exp(float(s_dist) / 1.5))
            else:
                u = np.clip(s_dist / bm_len, 0.0, 1.0)
                flare_r = bm_flare_eff * ((1.0 - u) ** 2)
            u_pts = (0.5 * entry_w_in + flare_r) * cos_a
            v_pts = (0.5 * entry_h_in + flare_r * v_flare_wt) * sin_a
            uv = np.column_stack([u_pts, v_pts]).astype(np.float64)
            bore_rings.append(ring_frame_points(pos, inlet_dir, up_hint, uv))
    else:
        s_lead = -3.5
        s_samples = np.linspace(s_lead, throat_len - 0.8, 17)
        for s_dist in s_samples:
            pos = p_bm_tip + inlet_dir * float(s_dist)
            if s_dist < 0.0:
                flare_r = bm_flare + (-s_dist) * 0.85
            else:
                u = np.clip(s_dist / bm_len, 0.0, 1.0)
                flare_r = bm_flare * ((1.0 - u) ** 2)
            uv = rounded_rect_points(entry_w_in + 2.0 * flare_r, entry_h_in + 2.0 * flare_r, entry_r_in + flare_r, n_pts)
            bore_rings.append(ring_frame_points(pos, inlet_dir, up_hint, uv))

    # Sweep bore from p0 (t>0) to p3
    for k in range(1, n_loft + 1):
        t = k / n_loft
        pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        w = entry_w_in + (sp_w_in - entry_w_in) * s_t
        h = entry_h_in + (sp_h_in - entry_h_in) * s_t
        r = entry_r_in + (sp_r_in - entry_r_in) * s_t
        uv = _profile_pts(w, h, r)
        bore_rings.append(ring_frame_points(pt, tan, up_hint, uv))

    # Extend straight bore 6 mm past spigot tip so exit is clean and open
    uv_exit = _profile_pts(sp_w_in, sp_h_in, sp_r_in)
    bore_rings.append(ring_frame_points(np.array([x_center, tip_y - 6.0, sp_z]), tan_sp, up_hint, uv_exit))

    inner_bore = trimesh_to_manifold(loft_closed_solid(bore_rings))

    return {
        "outer": outer_solid,
        "bellmouth_outer": bellmouth_outer,
        "inner_bore": inner_bore,
    }


def build_throttle_body_components(params: dict) -> dict[str, md.Manifold]:
    """
    Build C1 cubic-Bezier TB neck, radiused 4-bolt flange with continuous 360-deg lofted
    transition bell & spot-faced bolt pockets, bore cutter, bolt holes, and face O-ring groove.
    """
    tb = params["throttle_body"]
    pl = params["plenum"]
    wall = tb["neck_wall_thickness_mm"]
    bore_d = tb["bore_diameter_mm"]

    p_start, c0, c1, p_neck_end, p_flange_back, p_flange_face, tb_axis = tb_neck_bezier_points(params)

    pl_wall = pl["wall_thickness_mm"]
    pl_w_in = pl["inner_width_y_mm"]
    pl_h_in = pl["inner_height_z_mm"]
    pl_r_in = pl["inner_corner_radius_mm"]
    pl_w_out = pl_w_in + 2.0 * pl_wall
    pl_h_out = pl_h_in + 2.0 * pl_wall
    pl_r_out = pl_r_in + pl_wall

    n_pts = pl["profile_segments"]
    up_hint = np.array([0.0, 0.0, 1.0])

    # Smooth cubic-Bezier neck outer & inner lofts
    neck_out_rings = []
    neck_in_rings = []
    n_steps = 56
    for k in range(n_steps + 1):
        t = k / n_steps
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        pos, tan = bezier_point_and_tangent(p_start, c0, c1, p_neck_end, t)
        w_out = pl_w_out + (bore_d + 2.0 * wall - pl_w_out) * s_t
        h_out = pl_h_out + (bore_d + 2.0 * wall - pl_h_out) * s_t
        r_out = pl_r_out + ((bore_d + 2.0 * wall) * 0.5 - pl_r_out) * s_t
        neck_out_rings.append(ring_frame_points(pos, tan, up_hint, rounded_rect_points(w_out, h_out, r_out, n_pts)))

        w_in = pl_w_in + (bore_d - pl_w_in) * s_t
        h_in = pl_h_in + (bore_d - pl_h_in) * s_t
        r_in = pl_r_in + (bore_d * 0.5 - pl_r_in) * s_t
        neck_in_rings.append(ring_frame_points(pos, tan, up_hint, rounded_rect_points(w_in, h_in, r_in, n_pts)))

    uv_bore_end = rounded_rect_points(bore_d, bore_d, bore_d * 0.5, n_pts)
    neck_in_rings.append(ring_frame_points(p_flange_face + tb_axis * 6.0, tb_axis, up_hint, uv_bore_end))

    neck_outer = trimesh_to_manifold(loft_closed_solid(neck_out_rings))
    tb_bore = trimesh_to_manifold(loft_closed_solid(neck_in_rings))

    # Flange plate extruded along tb_axis with smooth quarter-round back rim edge
    fl_w = float(tb["flange_width_mm"])
    fl_h = float(tb["flange_height_mm"])
    fl_r = float(tb["flange_corner_radius_mm"])
    fl_ch = float(tb.get("flange_back_chamfer_mm", 2.0))
    fl_rings = []
    for th in np.linspace(0.0, 0.5 * math.pi, 10):
        ax_off = fl_ch * (1.0 - math.cos(th))
        inset = fl_ch * (1.0 - math.sin(th))
        uv_k = rounded_rect_points(fl_w - 2.0 * inset, fl_h - 2.0 * inset, max(fl_r - inset, 1.0), 128)
        fl_rings.append(ring_frame_points(p_flange_back + tb_axis * ax_off, tb_axis, up_hint, uv_k))
    fl_uv_full = rounded_rect_points(fl_w, fl_h, fl_r, 128)
    fl_rings.append(ring_frame_points(p_flange_face, tb_axis, up_hint, fl_uv_full))
    flange_outer = trimesh_to_manifold(loft_closed_solid(fl_rings))

    outer_pieces = [neck_outer, flange_outer]

    u_ax = np.cross(up_hint, tb_axis)
    u_ax /= np.linalg.norm(u_ax)
    v_ax = np.cross(tb_axis, u_ax)
    v_ax /= np.linalg.norm(v_ax)

    # Continuous 360-deg lofted transition bell from round neck into rounded-square flange back face
    bf_ax = float(tb.get("flange_back_fillet_axial_mm", 14.0))
    if bf_ax > 0.0:
        neck_od = bore_d + 2.0 * wall
        w_start = neck_od - 0.8
        h_start = neck_od - 0.8
        r_start = 0.5 * w_start
        w_end = fl_w - 2.0 * fl_ch
        h_end = fl_h - 2.0 * fl_ch
        r_end = fl_r
        bell_peak = 1.0 - math.sqrt(1.0 - 0.94 ** 2)
        bell_rings = []
        for k in range(28):
            u = k / 27.0
            pos_k = p_flange_back - tb_axis * (bf_ax * (1.0 - u))
            fac = (1.0 - math.sqrt(max(0.0, 1.0 - (0.94 * u) ** 2))) / bell_peak
            wk = w_start + (w_end - w_start) * fac
            hk = h_start + (h_end - h_start) * fac
            rk = r_start + (r_end - r_start) * fac
            bell_rings.append(ring_frame_points(pos_k, tb_axis, up_hint, rounded_rect_points(wk, hk, rk, 128)))
        bell_rings.append(
            ring_frame_points(
                p_flange_back + tb_axis * 1.8,
                tb_axis,
                up_hint,
                rounded_rect_points(w_end, h_end, r_end, 128),
            )
        )
        outer_pieces.append(trimesh_to_manifold(loft_closed_solid(bell_rings)))

    # 4 M6 bolt holes + Ø14.0 mm spot-faced nut/washer pockets in transition bell
    bx = tb["bolt_spacing_x_mm"] * 0.5
    by = tb["bolt_spacing_y_mm"] * 0.5
    b_rad = tb["bolt_hole_diameter_mm"] * 0.5

    cutters: list[md.Manifold] = [tb_bore]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pt_center = p_flange_back + u_ax * (sx * bx) + v_ax * (sy * by)
            c0_b = pt_center - tb_axis * (bf_ax + 6.0)
            c1_b = pt_center + tb_axis * (tb["flange_thickness_mm"] + 3.0)
            cutters.append(make_cylinder_along(c0_b, c1_b, b_rad, segments=64))
            if bf_ax > 0.0:
                cutters.append(
                    make_cylinder_along(
                        pt_center - tb_axis * (bf_ax + 4.0),
                        pt_center - tb_axis * 0.02,
                        7.0,
                        segments=64,
                    )
                )

    og = tb["oring_groove"]
    if og["enabled"]:
        r_in_g = og["inner_diameter_mm"] * 0.5
        r_out_g = r_in_g + og["width_mm"]
        depth_g = og["depth_mm"]
        outer_g = make_cylinder_along(
            p_flange_face - tb_axis * depth_g,
            p_flange_face + tb_axis * 1.0,
            r_out_g,
            segments=128,
        )
        inner_g = make_cylinder_along(
            p_flange_face - tb_axis * (depth_g + 1.0),
            p_flange_face + tb_axis * 2.0,
            r_in_g,
            segments=128,
        )
        cutters.append(outer_g - inner_g)

    return {
        "outer": m_union(outer_pieces),
        "tb_bore": tb_bore,
        "cutters": m_union(cutters),
        "flange_face_center": p_flange_face,
        "tb_axis": tb_axis,
    }


def build_center_split_flange_and_cutters(params: dict) -> dict[str, md.Manifold]:
    """
    Build the center split flange ring centered at X = split_x_mm with quarter-round
    outer rims, sweeping concave back-fillet collars, spot-faced washer seats,
    through-bolt holes, alignment dowel holes, and left-half face O-ring groove.
    """
    cs = params["center_split"]
    pl = params["plenum"]
    x_split = cs["split_x_mm"]
    s = math.sqrt(plenum_area_scale(x_split, params))
    wall = pl["wall_thickness_mm"]
    w_in = pl["inner_width_y_mm"] * s
    h_in = pl["inner_height_z_mm"] * s
    r_in = pl["inner_corner_radius_mm"] * s
    w_out = w_in + 2.0 * wall
    h_out = h_in + 2.0 * wall

    ext = cs["flange_radial_extension_mm"]
    w_fl = w_out + 2.0 * ext
    h_fl = h_out + 2.0 * ext
    r_fl = cs["flange_outer_corner_radius_mm"]
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

    bf_rad = float(cs.get("back_fillet_radial_mm", 0.0))
    bf_ax = float(cs.get("back_fillet_axial_mm", 0.0))
    if bf_rad > 0.0 and bf_ax > 0.0:
        col_peak = 1.0 - math.sqrt(1.0 - 0.95 ** 2)
        for side_sign in (-1.0, 1.0):
            col_rings = []
            u_vals = np.linspace(0.0, 1.0, 28)
            xs_col = [x_split + side_sign * (t_half + bf_ax * (1.0 - u)) for u in u_vals]
            if side_sign > 0:
                xs_col = list(reversed(xs_col))
                u_vals = list(reversed(u_vals))
            for x_loc, u in zip(xs_col, u_vals):
                s_loc = math.sqrt(plenum_area_scale(float(x_loc), params))
                fac = (1.0 - math.sqrt(max(0.0, 1.0 - (0.95 * float(u)) ** 2))) / col_peak
                dr = -1.2 + (bf_rad + 1.2) * fac
                w_c = pl["inner_width_y_mm"] * s_loc + 2.0 * (wall + dr)
                h_c = pl["inner_height_z_mm"] * s_loc + 2.0 * (wall + dr)
                r_c = pl["inner_corner_radius_mm"] * s_loc + wall + dr
                uv = rounded_rect_points(w_c, h_c, r_c, n_fl)
                col_rings.append(np.column_stack([np.full(n_fl, float(x_loc)), uv[:, 0], uv[:, 1]]))
            x_anc = float(x_split + side_sign * (t_half - 1.5))
            s_anc = math.sqrt(plenum_area_scale(x_anc, params))
            uv_e = rounded_rect_points(
                pl["inner_width_y_mm"] * s_anc + 2.0 * (wall + bf_rad),
                pl["inner_height_z_mm"] * s_anc + 2.0 * (wall + bf_rad),
                pl["inner_corner_radius_mm"] * s_anc + wall + bf_rad,
                n_fl,
            )
            ring_anchor = np.column_stack([np.full(n_fl, x_anc), uv_e[:, 0], uv_e[:, 1]])
            if side_sign < 0:
                col_rings.append(ring_anchor)
            else:
                col_rings.insert(0, ring_anchor)
            flange_pieces.append(trimesh_to_manifold(loft_closed_solid(col_rings)))

    flange_solid = m_union(flange_pieces)
    plenum_bore_clear = make_rounded_prism(
        w_in, h_in, r_in, thick_total + 2.0 * bf_ax + 6.0, segments=160, center=(x_split, 0.0, 0.0), axis="x"
    )
    flange_ring = flange_solid - plenum_bore_clear

    def perimeter_point(angle_deg: float, radial_offset_from_inner: float) -> tuple[float, float]:
        pts = rounded_rect_points(w_in, h_in, r_in, 720)
        angles = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) % 360.0
        target = angle_deg % 360.0
        diffs = np.abs(((angles - target + 180.0) % 360.0) - 180.0)
        idx = int(np.argmin(diffs))
        p_curr = pts[idx]
        p_prev = pts[(idx - 1) % len(pts)]
        p_next = pts[(idx + 1) % len(pts)]
        tang = p_next - p_prev
        nrm = np.array([tang[1], -tang[0]])
        nrm /= np.linalg.norm(nrm)
        out = p_curr + nrm * radial_offset_from_inner
        return float(out[0]), float(out[1])

    cutters: list[md.Manifold] = []
    bolt_offset_from_inner = wall + cs["bolt_radial_offset_mm"]
    b_rad = cs["bolt_hole_diameter_mm"] * 0.5
    spot_reach = t_half + max(bf_ax, 6.0) + 4.0
    for ang in cs["bolt_angles_deg"]:
        by, bz = perimeter_point(ang, bolt_offset_from_inner)
        cutters.append(
            make_cylinder_along(
                np.array([x_split - thick_total * 0.65, by, bz]),
                np.array([x_split + thick_total * 0.65, by, bz]),
                b_rad,
                segments=64,
            )
        )
        # Spot-faced Ø13.0 mm flat washer pockets on both flange back faces
        cutters.append(
            make_cylinder_along(
                np.array([x_split - spot_reach, by, bz]),
                np.array([x_split - t_half - 0.02, by, bz]),
                6.5,
                segments=64,
            )
        )
        cutters.append(
            make_cylinder_along(
                np.array([x_split + t_half + 0.02, by, bz]),
                np.array([x_split + spot_reach, by, bz]),
                6.5,
                segments=64,
            )
        )

    pin_offset_from_inner = wall + cs["dowel_pin_radial_offset_mm"]
    p_rad = cs["dowel_pin_diameter_mm"] * 0.5
    for ang in cs["dowel_pin_angles_deg"]:
        py, pz = perimeter_point(ang, pin_offset_from_inner)
        cutters.append(
            make_cylinder_along(
                np.array([x_split - thick_total * 0.65, py, pz]),
                np.array([x_split + thick_total * 0.65, py, pz]),
                p_rad,
                segments=64,
            )
        )

    og_cut = None
    og = cs["oring_groove"]
    if og["enabled"]:
        r_mid = og["radial_offset_from_inner_wall_mm"]
        gw = og["width_mm"]
        gd = og["depth_mm"]
        d_in = r_mid - gw * 0.5
        d_out = r_mid + gw * 0.5
        g_outer = make_rounded_prism(
            w_in + 2.0 * d_out, h_in + 2.0 * d_out, r_in + d_out, gd + 0.8,
            segments=160, center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0), axis="x"
        )
        g_inner = make_rounded_prism(
            w_in + 2.0 * d_in, h_in + 2.0 * d_in, r_in + d_in, gd + 2.0,
            segments=160, center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0), axis="x"
        )
        og_cut = g_outer - g_inner

    return {
        "flange_ring": flange_ring,
        "hole_cutters": m_union(cutters),
        "oring_cutter": og_cut,
    }


def build_boss_pad_components(pad_cfg: dict, params: dict) -> tuple[md.Manifold, list[md.Manifold]]:
    """Build a low-profile, wide-skirted, radius-topped NPT vacuum/boost boss pad."""
    s_bp = math.sqrt(plenum_area_scale(pad_cfg["x_center_mm"], params))
    z_roof_in = params["plenum"]["inner_height_z_mm"] * 0.5 * s_bp
    z_top = z_roof_in + params["plenum"]["wall_thickness_mm"] + pad_cfg["pad_height_z_mm"] - 2.0
    z_bot = z_roof_in - 6.0

    xc = float(pad_cfg["x_center_mm"])
    yc = float(pad_cfg["y_center_mm"])
    lx = float(pad_cfg["length_x_mm"])
    wy = float(pad_cfg["width_y_mm"])
    fx = float(pad_cfg.get("skirt_flare_x_mm", 12.0))
    fy = float(pad_cfg.get("skirt_flare_y_mm", 11.0))
    r_edge = min(float(pad_cfg.get("top_chamfer_mm", 2.2)), 2.2)

    z_collar = z_top - 2.8
    n_p = 128
    pad_rings: list[np.ndarray] = []
    for k in range(22):
        u = k / 21.0
        zk = z_bot + (z_collar - z_bot) * u
        cove = (1.0 - u) ** 2.2
        wk = lx + 2.0 * fx * cove
        hk = wy + 2.0 * fy * cove
        rk = 6.5 + 8.5 * cove
        uv = rounded_rect_points(wk, hk, rk, n_p)
        pad_rings.append(np.column_stack([uv[:, 0] + xc, uv[:, 1] + yc, np.full(n_p, zk)]))

    # Smooth 9-station quarter-round top perimeter radius
    for th in np.linspace(0.0, 0.5 * math.pi, 9):
        zk = (z_top - r_edge) + r_edge * math.sin(th)
        inset = r_edge * (1.0 - math.cos(th))
        uv_k = rounded_rect_points(lx - 2.0 * inset, wy - 2.0 * inset, max(6.5 - inset, 1.5), n_p)
        pad_rings.append(np.column_stack([uv_k[:, 0] + xc, uv_k[:, 1] + yc, np.full(n_p, zk)]))

    pad = trimesh_to_manifold(loft_closed_solid(pad_rings))

    diameters = pad_cfg.get("port_pilot_diameters_mm") or [pad_cfg["port_pilot_diameter_mm"]] * pad_cfg["port_count"]
    assert len(diameters) == pad_cfg["port_count"]
    start_x = pad_cfg["x_center_mm"] - pad_cfg["port_spacing_x_mm"] * (pad_cfg["port_count"] - 1) * 0.5
    bores: list[md.Manifold] = []
    for idx in range(pad_cfg["port_count"]):
        px = start_x + idx * pad_cfg["port_spacing_x_mm"]
        p_rad = float(diameters[idx]) * 0.5
        bores.append(
            make_cylinder_along(
                np.array([px, pad_cfg["y_center_mm"], z_roof_in - 12.0]),
                np.array([px, pad_cfg["y_center_mm"], z_top + 4.0]),
                p_rad,
                segments=64,
            )
        )
    return pad, bores


def build_iacv_components(params: dict) -> dict[str, md.Manifold]:
    """
    Build outward-flared, overhang-free 2-bolt Ford IACV pedestal on top of the TB neck / Cyl 4 junction:
      - Downstream port (-X side): punches cleanly into the plenum chamber.
      - Upstream metered supply port (+X side): blind pocket >= 4.5 mm above the TB bore,
        intersected by a flat-faced rear 1/4"-18 NPT (Ø11.1 mm) side tap.
      - 2x M6 blind bolt pilot holes (Ø5.2 mm) along Y.
    """
    iac = params["throttle_body"]["iacv_mount"]
    pl = params["plenum"]
    tb = params["throttle_body"]

    xc = float(iac["x_center_mm"])
    yc = float(iac["y_center_mm"])
    top_z = float(iac["top_z_mm"])
    port_half = float(iac["port_spacing_x_mm"]) * 0.5
    x_plenum_port = xc - port_half
    x_supply_port = xc + port_half

    # Verify solid floor between isolated IAC supply pocket and exact Bezier TB inner bore (>= 4.5 mm)
    p_start, c0, c1, p_neck_end, _, _, _ = tb_neck_bezier_points(params)
    t_lo, t_hi = 0.0, 1.0
    for _ in range(30):
        t_mid = 0.5 * (t_lo + t_hi)
        pt_m, _ = bezier_point_and_tangent(p_start, c0, c1, p_neck_end, t_mid)
        if pt_m[0] < x_supply_port:
            t_lo = t_mid
        else:
            t_hi = t_mid
    t_supply = 0.5 * (t_lo + t_hi)
    s_t = 0.5 - 0.5 * math.cos(math.pi * t_supply)
    h_in_at_supply = pl["inner_height_z_mm"] + (tb["bore_diameter_mm"] - pl["inner_height_z_mm"]) * s_t
    tb_inner_roof_z = 0.5 * h_in_at_supply
    floor_thickness = iac["supply_pocket_bottom_z_mm"] - tb_inner_roof_z
    assert floor_thickness >= 4.5, (
        f"IACV supply floor {floor_thickness:.2f} mm < 4.5 mm at X={x_supply_port}"
    )

    pad_l = float(iac["pad_length_x_mm"])
    pad_w = float(iac["pad_width_y_mm"])
    pad_r = float(iac["pad_corner_radius_mm"])
    fl_nx = float(iac.get("skirt_flare_neg_x_mm", 16.0))
    fl_px = float(iac.get("skirt_flare_pos_x_mm", 7.0))
    base_wy = float(iac.get("base_width_y_mm", 82.0))
    r_edge = min(float(iac.get("top_chamfer_mm", 2.2)), 2.2)

    z_skirt_bot = min(float(iac["base_z_mm"]), 22.0)
    z_collar = 45.0
    n_p = 128
    iac_rings: list[np.ndarray] = []

    # Outward-flared base skirt (Z = 22.0 -> 45.0) smoothly seating wider base (82 mm) into upper 68 mm pad
    for k in range(26):
        u = k / 25.0
        cove = (1.0 - u) ** 2.2
        zk = z_skirt_bot + (z_collar - z_skirt_bot) * u
        x_min_k = (xc - 0.5 * pad_l) - fl_nx * cove
        x_max_k = (xc + 0.5 * pad_l) + fl_px * cove
        wy_k = pad_w + (base_wy - pad_w) * cove
        rk = pad_r + 8.0 * cove
        uv = rounded_rect_points(x_max_k - x_min_k, wy_k, rk, n_p)
        cx_k = 0.5 * (x_min_k + x_max_k)
        iac_rings.append(np.column_stack([uv[:, 0] + cx_k, uv[:, 1] + yc, np.full(n_p, zk)]))

    # Vertical upper collar for flat -Y 1/4-18 NPT tap + quarter-round top perimeter edge
    for zk in (48.0, 56.0):
        uv = rounded_rect_points(pad_l, pad_w, pad_r, n_p)
        iac_rings.append(np.column_stack([uv[:, 0] + xc, uv[:, 1] + yc, np.full(n_p, zk)]))

    for th in np.linspace(0.0, 0.5 * math.pi, 9):
        zk = (top_z - r_edge) + r_edge * math.sin(th)
        inset = r_edge * (1.0 - math.cos(th))
        uv_k = rounded_rect_points(pad_l - 2.0 * inset, pad_w - 2.0 * inset, max(pad_r - inset, 2.0), n_p)
        iac_rings.append(np.column_stack([uv_k[:, 0] + xc, uv_k[:, 1] + yc, np.full(n_p, zk)]))

    pad_outer = trimesh_to_manifold(loft_closed_solid(iac_rings))

    cutters: list[md.Manifold] = []
    b_rad = iac["bolt_pilot_diameter_mm"] * 0.5
    b_half = iac["bolt_spacing_y_mm"] * 0.5
    b_bot = top_z - iac["bolt_depth_mm"]
    for sy in (-1.0, 1.0):
        cutters.append(
            make_cylinder_along(
                np.array([xc, yc + sy * b_half, b_bot]),
                np.array([xc, yc + sy * b_half, top_z + 4.0]),
                b_rad,
                segments=64,
            )
        )

    p_rad = iac["port_diameter_mm"] * 0.5
    cutters.append(
        make_cylinder_along(
            np.array([x_plenum_port, yc, 20.0]),
            np.array([x_plenum_port, yc, top_z + 4.0]),
            p_rad,
            segments=64,
        )
    )
    cutters.append(
        make_cylinder_along(
            np.array([x_supply_port, yc, iac["supply_pocket_bottom_z_mm"]]),
            np.array([x_supply_port, yc, top_z + 4.0]),
            p_rad,
            segments=64,
        )
    )
    tap_rad = iac["side_supply_tap_diameter_mm"] * 0.5
    y_rear_face = yc - iac["pad_width_y_mm"] * 0.5
    cutters.append(
        make_cylinder_along(
            np.array([x_supply_port, y_rear_face - 4.0, iac["side_supply_tap_z_mm"]]),
            np.array([x_supply_port, yc + 3.0, iac["side_supply_tap_z_mm"]]),
            tap_rad,
            segments=64,
        )
    )

    return {
        "outer": pad_outer,
        "cutters": m_union(cutters),
        "floor_thickness_mm": floor_thickness,
    }


def build_sculpted_runner_tie_web(x_left: float, x_right: float, params: dict) -> md.Manifold:
    """
    Build a trimmed-down straight runner tie-bar between adjacent runners,
    smoothly filleted into the cylindrical runner flanks over the outer 8 mm at each end.
    """
    tw = params["runners"]["tie_webs"]
    sp = params["runners"]["spigot"]
    tip_y = float(sp["tip_y_mm"])
    sp_z = float(sp["center_z_mm"])

    def sample_runner_zy(xc: float) -> tuple[np.ndarray, np.ndarray]:
        _, _, p0, p1, p2, p3 = runner_bezier_points(xc, params)
        pts = [bezier_point_and_tangent(p0, p1, p2, p3, i / 120.0)[0] for i in range(121)]
        pts.append(np.array([xc, tip_y, sp_z]))
        arr = np.asarray(pts)
        order = np.argsort(arr[:, 1])
        return arr[order, 1], arr[order, 2]

    yl, zl = sample_runner_zy(x_left)
    yr, zr = sample_runner_zy(x_right)

    y_w_start = float(tw.get("waist_y_start_mm", -108.0))
    y_w_end = float(tw.get("waist_y_end_mm", -78.0))
    y_r_start = float(tw.get("root_y_start_mm", -113.5))
    y_r_end = float(tw.get("root_y_end_mm", -72.5))
    h_w = float(tw.get("waist_height_mm", 18.0))
    h_r = float(tw.get("root_height_mm", 28.0))
    edge_r = float(tw.get("edge_radius_mm", 5.5))
    fil_span = float(tw.get("root_fillet_span_mm", 8.0))

    x_start = x_left + 14.0
    x_end = x_right - 14.0
    x_mid = 0.5 * (x_left + x_right)
    root_peak = 1.0 - math.sqrt(1.0 - 0.92 ** 2)
    rings: list[np.ndarray] = []

    for x in np.linspace(x_start, x_end, 96):
        frac_lr = (x - x_left) / (x_right - x_left)
        # Straight constant tie-bar across central |dx| <= 12 mm; concave root fillet over 12..20 mm
        v = float(np.clip((abs(x - x_mid) - 12.0) / max(fil_span, 1e-4), 0.0, 1.0))
        arch = (1.0 - math.sqrt(max(0.0, 1.0 - (0.92 * v) ** 2))) / root_peak
        y0 = y_w_start + (y_r_start - y_w_start) * arch
        y1 = y_w_end + (y_r_end - y_w_end) * arch
        hz = 0.5 * (h_w + (h_r - h_w) * arch)
        r_end = min(edge_r + (hz - 0.5 * h_w) * 0.5, hz * 0.92, 0.36 * (y1 - y0))

        def z_c(y_val: np.ndarray | float) -> np.ndarray | float:
            zl_v = np.interp(y_val, yl, zl)
            zr_v = np.interp(y_val, yr, zr)
            return (1.0 - frac_lr) * zl_v + frac_lr * zr_v

        y_inner0 = y0 + r_end
        y_inner1 = y1 - r_end
        n_edge = 24
        n_arc = 24
        pts_yz: list[list[float]] = []
        ys_bot = np.linspace(y_inner0, y_inner1, n_edge, endpoint=False)
        zs_bot = z_c(ys_bot) - hz
        for yy, zz in zip(ys_bot, zs_bot):
            pts_yz.append([float(yy), float(zz)])
        z_rear_c = float(z_c(y_inner1))
        for ang in np.linspace(-0.5 * math.pi, 0.5 * math.pi, n_arc, endpoint=False):
            pts_yz.append([y_inner1 + r_end * math.cos(ang), z_rear_c + hz * math.sin(ang)])
        ys_top = np.linspace(y_inner1, y_inner0, n_edge, endpoint=False)
        zs_top = z_c(ys_top) + hz
        for yy, zz in zip(ys_top, zs_top):
            pts_yz.append([float(yy), float(zz)])
        z_front_c = float(z_c(y_inner0))
        for ang in np.linspace(0.5 * math.pi, 1.5 * math.pi, n_arc, endpoint=False):
            pts_yz.append([y_inner0 + r_end * math.cos(ang), z_front_c + hz * math.sin(ang)])

        rings.append(np.column_stack([np.full(len(pts_yz), float(x)), np.asarray(pts_yz)]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def build_sculpted_hoop_rib(x_center: float, params: dict) -> md.Manifold:
    """Build a support-free ~45 deg beveled and crowned circumferential hoop rib."""
    pl = params["plenum"]
    hr = pl["hoop_ribs"]
    wall = float(pl["wall_thickness_mm"])
    base_half = float(hr.get("base_width_mm", 16.0)) * 0.5
    crest_half = float(hr.get("crest_width_mm", 4.0)) * 0.5
    rad_h = float(hr["radial_height_mm"])

    stations = [
        (-base_half, -1.5),
        (-0.88 * base_half, 0.2),
        (-0.62 * base_half, 0.52 * rad_h),
        (-crest_half, 0.92 * rad_h),
        (0.0, rad_h),
        (crest_half, 0.92 * rad_h),
        (0.62 * base_half, 0.52 * rad_h),
        (0.88 * base_half, 0.2),
        (base_half, -1.5),
    ]
    n_p = 72
    rings: list[np.ndarray] = []
    for dx, dr in stations:
        x_loc = x_center + dx
        s = math.sqrt(plenum_area_scale(x_loc, params))
        w_r = pl["inner_width_y_mm"] * s + 2.0 * (wall + dr)
        h_r = pl["inner_height_z_mm"] * s + 2.0 * (wall + dr)
        r_r = pl["inner_corner_radius_mm"] * s + wall + dr
        uv = rounded_rect_points(w_r, h_r, r_r, n_p)
        rings.append(np.column_stack([np.full(n_p, x_loc), uv[:, 0], uv[:, 1]]))
    return trimesh_to_manifold(loft_closed_solid(rings))


def build_fitment_gauges(params: dict) -> dict[str, md.Manifold]:
    """Build quick-print runner boot spigot gauge and TB flange pattern gauge."""
    sp = params["runners"]["spigot"]
    g = params["gauges"]
    n_pts = params["runners"]["sweep"]["profile_segments"]
    wall = sp["wall_thickness_mm"]

    w_out = sp["outer_width_mm"]
    h_out = sp["outer_height_mm"]
    r_out = sp["corner_radius_mm"]
    w_in = w_out - 2.0 * wall
    h_in = h_out - 2.0 * wall
    r_in = r_out - wall

    bead_h = sp["retention_bead_height_mm"]
    bead_w = sp["retention_bead_width_mm"]
    bead_off = sp["retention_bead_offset_from_tip_mm"]
    total_len = g["boot_fit_gauge_length_mm"]

    z_tip = total_len
    z_b_start = z_tip - bead_off
    z_b_end = z_b_start - bead_w
    stations: list[tuple[float, float]] = [
        (0.0, 3.0),
        (5.0, 3.0),
        (6.5, 0.0),
        (z_b_end, 0.0),
    ]
    for b_idx in range(1, 20):
        frac = b_idx / 20.0
        stations.append((z_b_end + frac * bead_w, bead_h * math.sin(math.pi * frac)))
    stations.extend([
        (z_b_start, 0.0),
        (z_tip - 0.8, 0.0),
        (z_tip, -0.8),
    ])
    rings = []
    for z, dr in stations:
        uv = rounded_rect_points(w_out + 2.0 * dr, h_out + 2.0 * dr, r_out + dr, n_pts)
        rings.append(np.column_stack([uv[:, 0], uv[:, 1], np.full(n_pts, z)]))
    boot_outer = trimesh_to_manifold(loft_closed_solid(rings))
    boot_bore = make_rounded_prism(w_in, h_in, r_in, total_len + 4.0, segments=n_pts, center=(0.0, 0.0, total_len * 0.5), axis="z")
    boot_gauge = boot_outer - boot_bore

    # TB flange fit gauge (flat plate on Z = [0, tb_fit_gauge_thickness_mm])
    tb = params["throttle_body"]
    t_g = g["tb_fit_gauge_thickness_mm"]
    tb_plate = make_rounded_prism(
        tb["flange_width_mm"], tb["flange_height_mm"], tb["flange_corner_radius_mm"], t_g,
        segments=128, center=(0.0, 0.0, t_g * 0.5), axis="z"
    )
    tb_cutters = [
        md.Manifold.cylinder(t_g + 4.0, tb["bore_diameter_mm"] * 0.5, tb["bore_diameter_mm"] * 0.5, circular_segments=128, center=True).translate([0.0, 0.0, t_g * 0.5])
    ]
    bx = tb["bolt_spacing_x_mm"] * 0.5
    by = tb["bolt_spacing_y_mm"] * 0.5
    b_rad = tb["bolt_hole_diameter_mm"] * 0.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            tb_cutters.append(
                md.Manifold.cylinder(t_g + 4.0, b_rad, b_rad, circular_segments=64, center=True).translate([sx * bx, sy * by, t_g * 0.5])
            )
    tb_gauge = m_diff(tb_plate, tb_cutters)

    # 2-bolt Ford IACV flange fit gauge (46 mm bolt centers, dual Ø13 mm ports at 22 mm centers)
    iac = params["throttle_body"]["iacv_mount"]
    t_iac = g["iacv_fit_gauge_thickness_mm"]
    iac_plate = make_rounded_prism(
        iac["pad_length_x_mm"], iac["pad_width_y_mm"], iac["pad_corner_radius_mm"], t_iac,
        segments=128, center=(0.0, 0.0, t_iac * 0.5), axis="z"
    )
    iac_cutters: list[md.Manifold] = []
    for sx in (-1.0, 1.0):
        iac_cutters.append(
            md.Manifold.cylinder(
                t_iac + 4.0, iac["port_diameter_mm"] * 0.5, iac["port_diameter_mm"] * 0.5,
                circular_segments=64, center=True
            ).translate([sx * iac["port_spacing_x_mm"] * 0.5, 0.0, t_iac * 0.5])
        )
    for sy in (-1.0, 1.0):
        iac_cutters.append(
            md.Manifold.cylinder(
                t_iac + 4.0, 3.2, 3.2, circular_segments=64, center=True
            ).translate([0.0, sy * iac["bolt_spacing_y_mm"] * 0.5, t_iac * 0.5])
        )
    iacv_gauge = m_diff(iac_plate, iac_cutters)

    # Printable horizontal flat-bottom alignment dowel pins (4x pins connected by breakaway tab)
    pin_len = float(g.get("dowel_pin_length_mm", 20.0))
    pin_diams = g.get("dowel_pin_diameters_mm", [5.85, 5.75])
    # Build 2 pins of each diameter along Y = [-18, -6, +6, +18], laid horizontally along X
    pin_list_diams = [float(pin_diams[0]), float(pin_diams[0]), float(pin_diams[-1]), float(pin_diams[-1])]
    y_offsets = [-18.0, -6.0, 6.0, 18.0]
    pin_solids: list[md.Manifold] = []
    for d_pin, y_off in zip(pin_list_diams, y_offsets):
        r_pin = d_pin * 0.5
        r_ch = max(r_pin - 0.85, 0.5)
        p_rings = []
        for z_loc, rad in [(0.0, r_ch), (0.9, r_pin), (pin_len - 0.9, r_pin), (pin_len, r_ch)]:
            uv = rounded_rect_points(2.0 * rad, 2.0 * rad, rad, 48)
            p_rings.append(np.column_stack([uv[:, 0], uv[:, 1], np.full(48, z_loc)]))
        pin_v = trimesh_to_manifold(loft_closed_solid(p_rings))
        # Rotate +90 deg around Y (Z -> +X), center in X, and place bottom -0.35 mm below Z=0 for flat pad
        pin_h = pin_v.rotate([0.0, 90.0, 0.0]).translate([-pin_len * 0.5, y_off, r_pin - 0.35])
        pin_solids.append(pin_h)

    runner_tab = md.Manifold.cube([1.8, 38.0, 0.85], center=True).translate([0.0, 0.0, 0.425])
    pins_raw = m_union([*pin_solids, runner_tab])
    flat_bed_clip = md.Manifold.cube([200.0, 200.0, 200.0], center=True).translate([0.0, 0.0, 100.0])
    dowel_pins_set = pins_raw ^ flat_bed_clip

    return {
        "boot_fit_gauge": boot_gauge,
        "tb_flange_fit_gauge": tb_gauge,
        "iacv_flange_fit_gauge": iacv_gauge,
        "alignment_dowel_pins": dowel_pins_set,
    }


# ---------------------------------------------------------------------------
# Full Assembly Pipeline
# ---------------------------------------------------------------------------

def assemble_all(params: dict):
    pl_outer = build_plenum_loft(params, is_inner=False)
    pl_inner = build_plenum_loft(params, is_inner=True)

    runner_outers: list[md.Manifold] = []
    bellmouth_outers: list[md.Manifold] = []
    runner_bores: list[md.Manifold] = []
    for x_c in params["runners"]["center_x_mm"]:
        rc = build_single_runner_components(x_c, params)
        runner_outers.append(rc["outer"])
        if rc["bellmouth_outer"] is not None:
            bellmouth_outers.append(rc["bellmouth_outer"])
        runner_bores.append(rc["inner_bore"])

    # External runner tie webs between Cyl 1-2 (X=-92) and Cyl 3-4 (X=+92)
    tw = params["runners"]["tie_webs"]
    webs: list[md.Manifold] = []
    if tw["enabled"]:
        if tw.get("sculpted", False):
            cxs = params["runners"]["center_x_mm"]
            webs.append(build_sculpted_runner_tie_web(float(cxs[0]), float(cxs[1]), params))
            webs.append(build_sculpted_runner_tie_web(float(cxs[2]), float(cxs[3]), params))
        else:
            y_mid = 0.5 * (tw["y_start_mm"] + tw["y_end_mm"])
            y_len = abs(tw["y_end_mm"] - tw["y_start_mm"])
            z_mid = params["runners"]["spigot"]["center_z_mm"] + 4.0
            for x_mid in (-92.0, 92.0):
                web = md.Manifold.cube([54.0, y_len, tw["height_mm"]], center=True).translate([x_mid, y_mid, z_mid])
                webs.append(web)

    # Plenum external hoop stiffening ribs
    ribs: list[md.Manifold] = []
    hr = params["plenum"]["hoop_ribs"]
    if hr["enabled"]:
        for xr in hr["x_positions_mm"]:
            ribs.append(build_sculpted_hoop_rib(float(xr), params))

    # Vacuum & Boost NPT boss pads on top of plenum (Right = direct boost/vac, Left = check-valved vacuum-only)
    boss_solids: list[md.Manifold] = []
    boss_bores: list[md.Manifold] = []
    for key in ("vacuum_boss_pad", "vacuum_only_boss_pad"):
        pad_cfg = params["plenum"].get(key)
        if pad_cfg and pad_cfg.get("enabled"):
            pad_solid, pad_bores = build_boss_pad_components(pad_cfg, params)
            boss_solids.append(pad_solid)
            boss_bores.extend(pad_bores)

    # Throttle body neck + flange + 2-bolt Ford IACV mounting pad
    tb_parts = build_throttle_body_components(params)
    iacv_parts = build_iacv_components(params) if params["throttle_body"]["iacv_mount"]["enabled"] else None

    # --- 3-Stage Watertight Boolean Assembly ---
    # 1. Outer monolithic body (center rib only when hoop_ribs are enabled)
    wall_flush = bool(params["runners"]["bellmouth"].get("wall_flush_bellmouth", False))
    outer_parts_1pc = [pl_outer, *runner_outers, *webs, *ribs, *boss_solids, tb_parts["outer"]]
    if hr["enabled"]:
        outer_parts_1pc.append(build_sculpted_hoop_rib(float(params["center_split"]["split_x_mm"]), params))
    if iacv_parts is not None:
        outer_parts_1pc.append(iacv_parts["outer"])
    outer_1pc = m_union(outer_parts_1pc)
    # 2. Hollow plenum & TB bore
    hollow_1pc = outer_1pc - m_union([pl_inner, tb_parts["cutters"]])
    # 3. Union internal velocity-stack bellmouths (when protruding inside plenum)
    with_bm_1pc = hollow_1pc if (wall_flush or not bellmouth_outers) else m_union([hollow_1pc, *bellmouth_outers])
    # 4. Subtract runner bores (with bellmouth flare), vacuum pilot bores, and IACV passages
    sub_parts_1pc = [*runner_bores, *boss_bores]
    if iacv_parts is not None:
        sub_parts_1pc.append(iacv_parts["cutters"])
    final_1pc = m_diff(with_bm_1pc, sub_parts_1pc)

    # --- 2-Piece Split Version (add center split flange at X=0, omit simple center rib) ---
    split_parts = build_center_split_flange_and_cutters(params)
    outer_parts_split = [pl_outer, *runner_outers, *webs, *ribs, *boss_solids, tb_parts["outer"]]
    if iacv_parts is not None:
        outer_parts_split.append(iacv_parts["outer"])
    outer_split_base = m_union(outer_parts_split)
    hollow_split = outer_split_base - m_union([pl_inner, tb_parts["cutters"]])
    split_add_parts = [split_parts["flange_ring"]] if (wall_flush or not bellmouth_outers) else [*bellmouth_outers, split_parts["flange_ring"]]
    with_bm_split = m_union([hollow_split, *split_add_parts])
    sub_parts_split = [*runner_bores, *boss_bores, split_parts["hole_cutters"]]
    if iacv_parts is not None:
        sub_parts_split.append(iacv_parts["cutters"])
    full_for_split = m_diff(with_bm_split, sub_parts_split)

    x_split = params["center_split"]["split_x_mm"]
    big = 1000.0
    left_box = md.Manifold.cube([big, big, big], center=True).translate([x_split - big * 0.5, 0.0, 0.0])
    right_box = md.Manifold.cube([big, big, big], center=True).translate([x_split + big * 0.5, 0.0, 0.0])

    split_left = full_for_split ^ left_box
    if split_parts["oring_cutter"] is not None:
        split_left = split_left - split_parts["oring_cutter"]
    split_right = full_for_split ^ right_box

    # Print-oriented copies (flat center split flange sitting at Z=0)
    split_left_print = split_left.rotate([0.0, 90.0, 0.0])
    split_right_print = split_right.rotate([0.0, -90.0, 0.0])

    def center_xy_on_bed(solid: md.Manifold) -> md.Manifold:
        bb = solid.bounding_box()
        cx = 0.5 * (bb[0] + bb[3])
        cy = 0.5 * (bb[1] + bb[4])
        return solid.translate([-cx, -cy, -bb[2]])

    split_left_print = center_xy_on_bed(split_left_print)
    split_right_print = center_xy_on_bed(split_right_print)

    gauges = build_fitment_gauges(params)

    return {
        "svt_intake_manifold_1piece_full": final_1pc,
        "svt_intake_manifold_split_left_cyl1_2": split_left,
        "svt_intake_manifold_split_right_cyl3_4_tb": split_right,
        "svt_intake_manifold_split_left_print_oriented": split_left_print,
        "svt_intake_manifold_split_right_print_oriented": split_right_print,
        "svt_runner_boot_fit_gauge": gauges["boot_fit_gauge"],
        "svt_tb_flange_fit_gauge": gauges["tb_flange_fit_gauge"],
        "svt_iacv_flange_fit_gauge": gauges["iacv_flange_fit_gauge"],
        "svt_alignment_dowel_pins": gauges["alignment_dowel_pins"],
        "_plenum_inner_cavity": pl_inner,
        "_iacv_floor_thickness_mm": iacv_parts["floor_thickness_mm"] if iacv_parts else None,
    }


# ---------------------------------------------------------------------------
# Visualization & Documentation Generators
# ---------------------------------------------------------------------------

def _add_section_patches(
    ax,
    polys_2d: list[np.ndarray],
    facecolor: str,
    edgecolor: str,
    lw: float = 0.9,
    alpha: float = 1.0,
    ls: str = "-",
):
    """Render 2D cross-section polygons with true outer/hole nesting via PathPatch."""
    if not polys_2d:
        return
    sh_polys = [ShapelyPolygon(p) for p in polys_2d if len(p) >= 3]
    depths = []
    for i, pi in enumerate(sh_polys):
        d = sum(1 for j, pj in enumerate(sh_polys) if i != j and pj.area > pi.area and pj.contains(pi.representative_point()))
        depths.append(d)
    for i, pi in enumerate(sh_polys):
        if depths[i] % 2 != 0:
            continue
        rings = [np.asarray(pi.exterior.coords)]
        for j, pj in enumerate(sh_polys):
            if depths[j] == depths[i] + 1 and pi.contains(pj.representative_point()):
                rings.append(np.asarray(pj.exterior.coords))
        verts = []
        codes = []
        for r_idx, r in enumerate(rings):
            area = 0.5 * np.sum(r[:-1, 0] * r[1:, 1] - r[1:, 0] * r[:-1, 1])
            if (r_idx == 0 and area < 0) or (r_idx > 0 and area > 0):
                r = r[::-1]
            verts.extend(r)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(r) - 2) + [MplPath.CLOSEPOLY])
        path = MplPath(np.asarray(verts), codes)
        ax.add_patch(PathPatch(path, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, alpha=alpha, linestyle=ls))


def _plot_mesh_panel(
    ax,
    mesh: trimesh.Trimesh,
    title: str,
    elev: float,
    azim: float,
    color: str = "#3a434e",
    bounds_override: tuple[np.ndarray, np.ndarray] | None = None,
    zoom_scale: float = 0.44,
    lightsource: LightSource | None = None,
    bg_color: str = "#f5f4f0",
    hide_axes: bool = False,
):
    ax.set_facecolor(bg_color)
    kwargs = {}
    if lightsource is not None:
        kwargs["lightsource"] = lightsource
    ax.plot_trisurf(
        mesh.vertices[:, 0],
        mesh.vertices[:, 1],
        mesh.vertices[:, 2],
        triangles=mesh.faces,
        color=color,
        linewidth=0,
        antialiased=False,
        shade=True,
        **kwargs,
    )
    if bounds_override is not None:
        mins, maxs = bounds_override
    else:
        b = mesh.bounds
        mins, maxs = b[0], b[1]
    spans = maxs - mins
    max_span = max(spans) * zoom_scale
    c = 0.5 * (mins + maxs)
    ax.set_xlim(c[0] - max_span, c[0] + max_span)
    ax.set_ylim(c[1] - max_span, c[1] + max_span)
    ax.set_zlim(c[2] - max_span, c[2] + max_span)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=11, fontweight="bold", color="#1f242b", pad=6)
    if hide_axes:
        ax.set_axis_off()
    else:
        ax.set_xlabel("X (mm)", fontsize=8)
        ax.set_ylabel("Y (mm)", fontsize=8)
        ax.set_zlabel("Z (mm)", fontsize=8)
        ax.tick_params(labelsize=7)


def render_overview_png(meshes: dict[str, trimesh.Trimesh], solids: dict[str, md.Manifold], params: dict, out_path: Path):
    fig = plt.figure(figsize=(16, 11), facecolor="#f5f4f0")
    fig.suptitle(
        "2004 Ford Focus SVT Turbo — Stage-2 Production Intake Manifold (Sculpted Exterior)",
        fontsize=15,
        fontweight="bold",
        y=0.97,
        color="#1f242b",
    )

    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    _plot_mesh_panel(ax1, meshes["svt_intake_manifold_1piece_full"], "1-Piece Reference Assembly (IMRC Deleted)", 26, -55, "#4d5661", zoom_scale=0.44)

    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    m_l = meshes["svt_intake_manifold_split_left_cyl1_2"].copy()
    m_r = meshes["svt_intake_manifold_split_right_cyl3_4_tb"].copy()
    m_l.apply_translation([-24.0, 0.0, 0.0])
    m_r.apply_translation([24.0, 0.0, 0.0])
    _plot_mesh_panel(ax2, trimesh.util.concatenate([m_l, m_r]), "2-Piece Split Assembly (256x256x256 Bed Fit)", 26, -55, "#36688d", zoom_scale=0.44)

    ax3 = fig.add_subplot(2, 2, 3)
    ax3.set_facecolor("#ffffff")
    full_solid = solids["svt_intake_manifold_1piece_full"]
    rot_x = full_solid.rotate([0.0, -90.0, 0.0])
    sec_yz = rot_x.slice(46.0)
    yz_polys = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in sec_yz.to_polygons()]
    _add_section_patches(ax3, yz_polys, facecolor="#4c5c6b", edgecolor="#1b2026", lw=0.9)
    ax3.axhline(0, color="#999999", lw=0.6, ls="--")
    ax3.axvline(0, color="#999999", lw=0.6, ls="--")
    ax3.set_aspect("equal")
    ax3.set_xlim(-160, 75)
    ax3.set_ylim(-65, 75)
    ax3.grid(True, linestyle=":", alpha=0.5)
    ax3.set_title("Section at Cyl 3 (X = +46 mm): Plenum, Bellmouth & Crowned Spigot", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Y: Spigot (-Y) to Front (+Y) [mm]")
    ax3.set_ylabel("Z: Height [mm]")

    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor("#ffffff")
    sec_xy = [np.asarray(p) for p in full_solid.slice(-35.0).to_polygons()]
    _add_section_patches(ax4, sec_xy, facecolor="#2f5d80", edgecolor="#182a38", lw=0.9, alpha=0.88)
    sec_xy0 = [np.asarray(p) for p in full_solid.slice(0.0).to_polygons()]
    for pts in sec_xy0:
        closed = np.vstack([pts, pts[0]])
        ax4.plot(closed[:, 0], closed[:, 1], color="#c04b2b", linewidth=1.1, ls="--")
    for idx, xc in enumerate(params["runners"]["center_x_mm"], start=1):
        ax4.axvline(xc, color="#777777", lw=0.6, ls=":")
        ax4.text(xc, -156, f"Cyl {idx}\n({xc:+.0f})", ha="center", va="top", fontsize=8, color="#222222")
    ax4.axvline(0.0, color="#0d6e3f", lw=1.4, ls="-.")
    ax4.text(0.0, 74, "Split Plane X=0", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#0d6e3f")
    ax4.set_aspect("equal")
    ax4.set_xlim(-210, 250)
    ax4.set_ylim(-172, 92)
    ax4.grid(True, linestyle=":", alpha=0.5)
    ax4.set_title("Plan Layout: 92 mm Pitch Spigots (Blue) & C2 Plenum/TB Bore (Red)", fontsize=11, fontweight="bold")
    ax4.set_xlabel("X: Cyl 1 (-X) to TB (+X) [mm]")
    ax4.set_ylabel("Y [mm]")

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_exterior_closeup_png(meshes: dict[str, trimesh.Trimesh], solids: dict[str, md.Manifold], params: dict, out_path: Path):
    """Render 4-panel high-resolution inspection sheet including bottom-rear viewer angle."""
    fig = plt.figure(figsize=(16, 12), facecolor="#f5f4f0")
    fig.suptitle(
        "Stage-2 Production Manifold — Polished Exterior, Root Transition & Tie-Bar Inspection",
        fontsize=15,
        fontweight="bold",
        y=0.97,
        color="#1f242b",
    )
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.22, left=0.06, right=0.97, top=0.91, bottom=0.06)

    full_mesh = meshes["svt_intake_manifold_1piece_full"]
    full_solid = solids["svt_intake_manifold_1piece_full"]
    right_mesh = meshes["svt_intake_manifold_split_right_cyl3_4_tb"]

    # Panel 1: Exact bottom-rear camera angle matching user's 3D viewer screenshot
    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    ls = LightSource(azdeg=210, altdeg=48)
    _plot_mesh_panel(
        ax1,
        full_mesh,
        "Bottom-Rear View: Smooth Plenum, Eyebrow-Free Roots & Straight Tie-Bars",
        elev=-18,
        azim=-90,
        color="#3c4046",
        bounds_override=(np.array([-195.0, -148.0, -65.0]), np.array([225.0, 62.0, 68.0])),
        zoom_scale=0.28,
        lightsource=ls,
        hide_axes=True,
    )

    # Panel 2: Right half close-up showing outward-flared IACV pedestal, lofted TB bell & spot-faces
    ax2 = fig.add_subplot(gs[0, 1], projection="3d")
    _plot_mesh_panel(
        ax2,
        right_mesh,
        "Right Half: Outward-Flared IACV Pedestal, Lofted TB Bell & Spot-Faced Pockets",
        elev=26,
        azim=-48,
        color="#46586b",
        bounds_override=(np.array([25.0, -110.0, -65.0]), np.array([235.0, 75.0, 75.0])),
        zoom_scale=0.47,
        lightsource=ls,
    )

    # Panel 3: Overlaid Y-Z cross-sections at Cyl 3 (X=+46) and Cyl 1 (X=-138)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor("#ffffff")
    rot_x = full_solid.rotate([0.0, -90.0, 0.0])
    sec3 = rot_x.slice(46.0)
    polys3 = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in sec3.to_polygons()]
    _add_section_patches(ax3, polys3, facecolor="#4c5c6b", edgecolor="#161b22", lw=1.0, alpha=0.88)

    sec1 = rot_x.slice(-138.0)
    polys1 = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in sec1.to_polygons()]
    for p1 in polys1:
        closed = np.vstack([p1, p1[0]])
        ax3.plot(closed[:, 0], closed[:, 1], color="#d95f02", lw=1.35, ls="--", label="Cyl 1 (X=-138)" if p1 is polys1[0] else None)

    ax3.axhline(0, color="#999999", lw=0.6, ls=":")
    ax3.axvline(0, color="#999999", lw=0.6, ls=":")
    ax3.set_aspect("equal")
    ax3.set_xlim(-152, 62)
    ax3.set_ylim(-64, 68)
    ax3.grid(True, linestyle=":", alpha=0.5)
    ax3.legend(loc="upper right", fontsize=8.5)
    ax3.set_title("Tooth-Free Bellmouth & Low-Profile Boss Sections: Cyl 3 (Solid) vs Cyl 1 (Dashed)", fontsize=10.5, fontweight="bold")
    ax3.set_xlabel("Y: Spigot (-Y) to Front (+Y) [mm]")
    ax3.set_ylabel("Z [mm]")

    # Panel 4: Two stacked sections showing trimmed straight tie-bars in X-Y (Z=-22) and X-Z (Y=-92)
    sub = gs[1, 1].subgridspec(2, 1, hspace=0.38)
    ax4a = fig.add_subplot(sub[0, 0])
    ax4a.set_facecolor("#ffffff")
    sec_xy_web = [np.asarray(p) for p in full_solid.slice(-22.0).to_polygons()]
    _add_section_patches(ax4a, sec_xy_web, facecolor="#2f5d80", edgecolor="#162836", lw=0.9)
    ax4a.set_aspect("equal")
    ax4a.set_xlim(-195, 230)
    ax4a.set_ylim(-145, 50)
    ax4a.grid(True, linestyle=":", alpha=0.5)
    ax4a.set_title("X-Y Slice at Z = -22 mm: Trimmed Straight Tie-Bars & Uninterrupted Barrel", fontsize=10, fontweight="bold")
    ax4a.set_ylabel("Y [mm]")

    ax4b = fig.add_subplot(sub[1, 0])
    ax4b.set_facecolor("#ffffff")
    rot_y = full_solid.rotate([90.0, 0.0, 0.0])
    sec_xz_web = [np.column_stack([np.asarray(p)[:, 0], -np.asarray(p)[:, 1]]) for p in rot_y.slice(-92.0).to_polygons()]
    _add_section_patches(ax4b, sec_xz_web, facecolor="#1f7a68", edgecolor="#0f3d34", lw=0.9)
    ax4b.set_aspect("equal")
    ax4b.set_xlim(-175, 175)
    ax4b.set_ylim(-55, 10)
    ax4b.grid(True, linestyle=":", alpha=0.5)
    ax4b.set_title("X-Z Slice at Y = -92 mm: Straight Tie-Bar Bridging Runners w/ Root Fillets", fontsize=10, fontweight="bold")
    ax4b.set_xlabel("X [mm]")
    ax4b.set_ylabel("Z [mm]")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_1to1_svg(solids: dict[str, md.Manifold], params: dict, out_path: Path):
    """Generate a true 1:1 mm-unit SVG template for physical caliper comparison of key interfaces."""
    # 1) Boot Spigot face section (from boot_fit_gauge at Z=24mm clean clamping land)
    spigot_sec = solids["svt_runner_boot_fit_gauge"].slice(24.0).to_polygons()
    # 2) Center split flange face (from split_left at X=-1 mm, rotated so X->Z)
    split_sec = solids["svt_intake_manifold_split_left_cyl1_2"].rotate([0.0, -90.0, 0.0]).slice(-1.0).to_polygons()
    # 3) TB flange face (from tb_flange_fit_gauge at Z=2 mm)
    tb_sec = solids["svt_tb_flange_fit_gauge"].slice(2.0).to_polygons()
    # 4) 2-bolt Ford IACV flange face (from iacv_flange_fit_gauge at Z=2 mm)
    iacv_sec = solids["svt_iacv_flange_fit_gauge"].slice(2.0).to_polygons()

    # Arrange horizontally across a 530 x 175 mm SVG canvas
    width_mm, height_mm = 530.0, 175.0
    sp_cfg = params["runners"]["spigot"]
    sp_out_w = sp_cfg["outer_width_mm"]
    sp_out_h = sp_cfg["outer_height_mm"]
    sp_in_w = sp_out_w - 2.0 * sp_cfg["wall_thickness_mm"]
    sp_in_h = sp_out_h - 2.0 * sp_cfg["wall_thickness_mm"]
    if abs(sp_out_w - sp_out_h) < 1e-3:
        spigot_label = f'Silicone Boot Spigot\n(Ø{sp_out_w:.1f} outer / Ø{sp_in_w:.1f} inner — 2" Boot)'
    else:
        spigot_label = (
            f"Silicone Boot Spigot\n"
            f"({int(round(sp_out_w))}x{int(round(sp_out_h))} outer / {int(round(sp_in_w))}x{int(round(sp_in_h))} inner)"
        )
    centers = [
        (spigot_label, spigot_sec, (55.0, 88.0), lambda p: (p[0], -p[1])),
        ("Center Split Flange\n(6x M6 + 2x 6mm Dowel + O-Ring)", split_sec, (195.0, 88.0), lambda p: (p[1], p[0])),
        ("65mm Throttle Body Flange\n(70x70 mm 4-Bolt Pattern)", tb_sec, (345.0, 88.0), lambda p: (p[0], -p[1])),
        ("2-Bolt Ford IACV Flange\n(46mm Bolts / Dual 13mm Ports)", iacv_sec, (465.0, 88.0), lambda p: (p[0], -p[1])),
    ]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width_mm * 0.5:.1f}" y="12" text-anchor="middle" font-family="sans-serif" font-size="6" font-weight="bold" fill="#111">2004 Focus SVT Intake Manifold — 1:1 Interface Templates (mm)</text>',
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
# Export & Verification
# ---------------------------------------------------------------------------

def main():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    STL_DIR.mkdir(parents=True, exist_ok=True)
    FITMENT_DIR.mkdir(parents=True, exist_ok=True)

    solids = assemble_all(params)
    meshes: dict[str, trimesh.Trimesh] = {}
    manifest_parts: dict[str, dict] = {}

    printers = params["printers"]
    cc2 = printers["centauri_carbon_2"]
    e3 = printers["ender_3_s1_pro"]

    for name, solid in solids.items():
        if name.startswith("_"):
            continue
        mesh = manifold_to_trimesh(solid)
        assert mesh.is_watertight, f"{name} failed watertight check"
        assert mesh.is_volume, f"{name} failed closed-volume check"
        assert mesh.body_count == 1, f"{name} has {mesh.body_count} bodies (expected 1)"
        meshes[name] = mesh

        stl_path = STL_DIR / f"{name}.stl"
        mesh.export(stl_path)
        sha256 = hashlib.sha256(stl_path.read_bytes()).hexdigest()

        bmin, bmax = mesh.bounds[0], mesh.bounds[1]
        ext = bmax - bmin
        fits_cc2 = bool(ext[0] <= cc2["bed_x_mm"] and ext[1] <= cc2["bed_y_mm"] and ext[2] <= cc2["bed_z_mm"])
        fits_e3 = bool(ext[0] <= e3["bed_x_mm"] and ext[1] <= e3["bed_y_mm"] and ext[2] <= e3["bed_z_mm"])

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
            "fits_centauri_carbon_2_256": fits_cc2,
            "fits_ender_3_s1_pro_220": fits_e3,
        }

    # Internal plenum volume metric
    pl_mesh = manifold_to_trimesh(solids["_plenum_inner_cavity"])
    plenum_liters = round(float(pl_mesh.volume) / 1_000_000.0, 3)

    manifest = {
        "vehicle": params["metadata"]["vehicle"],
        "plenum_internal_volume_liters": plenum_liters,
        "runner_pitch_mm": params["runners"]["pitch_mm"],
        "spigot_outer_mm": [
            params["runners"]["spigot"]["outer_width_mm"],
            params["runners"]["spigot"]["outer_height_mm"],
        ],
        "spigot_inner_mm": [
            params["runners"]["spigot"]["outer_width_mm"] - 2.0 * params["runners"]["spigot"]["wall_thickness_mm"],
            params["runners"]["spigot"]["outer_height_mm"] - 2.0 * params["runners"]["spigot"]["wall_thickness_mm"],
        ],
        "throttle_body_bore_mm": params["throttle_body"]["bore_diameter_mm"],
        "iacv_supply_floor_thickness_mm": round(float(solids["_iacv_floor_thickness_mm"]), 2)
        if solids.get("_iacv_floor_thickness_mm") is not None
        else None,
        "parts": manifest_parts,
    }
    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Programmatic section sanity checks across all 4 cylinders:
    # Cutting straight down each open runner centerline must yield 1 continuous C-section polygon.
    rot_x = solids["svt_intake_manifold_1piece_full"].rotate([0.0, -90.0, 0.0])
    for xc_check in params["runners"]["center_x_mm"]:
        polys_chk = [ShapelyPolygon(p) for p in rot_x.slice(xc_check).to_polygons() if len(p) >= 3]
        assert len(polys_chk) == 1 and polys_chk[0].area > 1500.0 and polys_chk[0].is_valid, (
            f"Section at X={xc_check} has {len(polys_chk)} polygons (areas={[round(pg.area, 1) for pg in polys_chk]})"
        )
    for half_name in ("svt_intake_manifold_split_left_print_oriented", "svt_intake_manifold_split_right_print_oriented"):
        assert manifest_parts[half_name]["fits_centauri_carbon_2_256"], f"{half_name} exceeds CC2 256 mm cube!"

    # Programmatic bolt/washer & socket clearance audit (Ø12.4 mm wrench envelope)
    cs = params["center_split"]
    pl = params["plenum"]
    x_sp = float(cs["split_x_mm"])
    t_half = float(cs["flange_thickness_per_side_mm"])
    s_sp = math.sqrt(plenum_area_scale(x_sp, params))
    w_in_sp = pl["inner_width_y_mm"] * s_sp
    h_in_sp = pl["inner_height_z_mm"] * s_sp
    r_in_sp = pl["inner_corner_radius_mm"] * s_sp
    pts_sp = rounded_rect_points(w_in_sp, h_in_sp, r_in_sp, 720)
    angs_sp = np.degrees(np.arctan2(pts_sp[:, 1], pts_sp[:, 0])) % 360.0
    sp_l = solids["svt_intake_manifold_split_left_cyl1_2"]
    sp_r = solids["svt_intake_manifold_split_right_cyl3_4_tb"]
    for ang in cs["bolt_angles_deg"]:
        diffs = np.abs(((angs_sp - (ang % 360.0) + 180.0) % 360.0) - 180.0)
        idx = int(np.argmin(diffs))
        tang = pts_sp[(idx + 1) % 720] - pts_sp[(idx - 1) % 720]
        nrm = np.array([tang[1], -tang[0]])
        nrm /= np.linalg.norm(nrm)
        by, bz = pts_sp[idx] + nrm * (pl["wall_thickness_mm"] + cs["bolt_radial_offset_mm"])
        cyl_l = make_cylinder_along(np.array([x_sp - t_half - 18.0, by, bz]), np.array([x_sp - t_half - 0.3, by, bz]), 6.2, segments=24)
        cyl_r = make_cylinder_along(np.array([x_sp + t_half + 0.3, by, bz]), np.array([x_sp + t_half + 18.0, by, bz]), 6.2, segments=24)
        assert (sp_l ^ cyl_l).volume() < 0.1 and (sp_r ^ cyl_r).volume() < 0.1, (
            f"Split bolt {ang} deg socket/washer interference!"
        )
    _, _, _, _, p_fb, _, tb_axis = tb_neck_bezier_points(params)
    up_chk = np.array([0.0, 0.0, 1.0])
    u_chk = np.cross(up_chk, tb_axis)
    u_chk /= np.linalg.norm(u_chk)
    v_chk = np.cross(tb_axis, u_chk)
    v_chk /= np.linalg.norm(v_chk)
    bx_tb = params["throttle_body"]["bolt_spacing_x_mm"] * 0.5
    by_tb = params["throttle_body"]["bolt_spacing_y_mm"] * 0.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pc = p_fb + u_chk * (sx * bx_tb) + v_chk * (sy * by_tb)
            cyl_tb = make_cylinder_along(pc - tb_axis * 10.5, pc - tb_axis * 0.3, 6.2, segments=24)
            iv_tb = float((sp_r ^ cyl_tb).volume())
            assert iv_tb < 0.1, f"TB bolt ({sx:+.0f},{sy:+.0f}) nut/washer interference: {iv_tb:.2f} mm3"

    render_overview_png(meshes, solids, params, FITMENT_DIR / "01_intake_manifold_overview.png")
    render_1to1_svg(solids, params, FITMENT_DIR / "02_interfaces_1to1_template.svg")
    render_exterior_closeup_png(meshes, solids, params, FITMENT_DIR / "05_exterior_transitions_closeup.png")

    print(f"Generated {len(meshes)} watertight STLs. Plenum volume: {plenum_liters:.3f} L")
    for pname, info in manifest_parts.items():
        print(
            f"  {pname}: {info['extents_mm']} mm | "
            f"vol={info['solid_volume_cm3']} cm3 | "
            f"CC2={info['fits_centauri_carbon_2_256']} | E3={info['fits_ender_3_s1_pro_220']}"
        )


if __name__ == "__main__":
    main()
