#!/usr/bin/env python3
"""
Dual-Chamber WRC Tapered Slot-Diffuser Upper Intake Manifold Generator
for 2004 Ford Focus SVT (2.0L Zetec-E Turbo).

Builds a twin-chamber motorsport plenum completely separate from cad/intake_manifold/:
  - Primary (upper-front) tapered diffuser tube fed straight by the 65 mm TB
  - Full-length venturi-flared tapered transfer slot (wider toward Cyl 1)
  - Secondary (lower) runner chamber with 4 wall-flush bellmouths & 2.00" round spigots
  - Zero-height-penalty -Y vacuum/boost pads & 2-bolt Ford IACV mount
  - 8-bolt + 2-dowel X=0 split flange with single continuous twin-chamber Viton O-ring loop

Outputs:
  stl/svt_wrc_manifold_1piece_full.stl
  stl/svt_wrc_manifold_split_left_cyl1_2.stl
  stl/svt_wrc_manifold_split_right_cyl3_4_tb.stl
  stl/svt_wrc_manifold_split_left_print_oriented.stl
  stl/svt_wrc_manifold_split_right_print_oriented.stl
  stl/svt_wrc_runner_boot_fit_gauge.stl
  stl/svt_wrc_tb_flange_fit_gauge.stl
  stl/svt_wrc_iacv_flange_fit_gauge.stl
  stl/svt_wrc_alignment_dowel_pins.stl
  stl/manifest.json
  fitment/01_wrc_manifold_overview.png
  fitment/02_wrc_interfaces_1to1_template.svg
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
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, Polygon as ShapelyPolygon
from shapely.ops import unary_union
import trimesh

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "wrc_manifold_parameters.json"
STL_DIR = ROOT / "stl"
FITMENT_DIR = ROOT / "fitment"


# ---------------------------------------------------------------------------
# Mesh & Manifold3D Geometry Primitives
# ---------------------------------------------------------------------------

def rounded_rect_points(width: float, height: float, radius: float, total_pts: int) -> np.ndarray:
    """Return (total_pts, 2) CCW points for a centered rounded rectangle."""
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


def ring_frame_points(
    center: np.ndarray,
    tangent: np.ndarray,
    up_hint: np.ndarray,
    profile_uv: np.ndarray,
) -> np.ndarray:
    """Embed a 2D (N, 2) profile into a right-handed 3D frame (u, v, +tangent)."""
    t_hat = tangent / np.linalg.norm(tangent)
    u_axis = np.cross(up_hint, t_hat)
    if np.linalg.norm(u_axis) < 1e-6:
        fallback = np.array([1.0, 0.0, 0.0]) if abs(t_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u_axis = np.cross(fallback, t_hat)
    u_axis /= np.linalg.norm(u_axis)
    v_axis = np.cross(t_hat, u_axis)
    v_axis /= np.linalg.norm(v_axis)
    return center[None, :] + profile_uv[:, 0:1] * u_axis[None, :] + profile_uv[:, 1:2] * v_axis[None, :]


def loft_closed_solid(rings: list[np.ndarray]) -> trimesh.Trimesh:
    """Loft a sequence of 3D rings into a closed, watertight Trimesh."""
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
        j = (i + 1) % n_pts
        faces.append([c_start_idx, j, i])

    c_end_idx = len(verts)
    verts.append(rings[-1].mean(axis=0))
    last_base = (n_rings - 1) * n_pts
    for i in range(n_pts):
        j = (i + 1) % n_pts
        faces.append([c_end_idx, last_base + i, last_base + j])

    mesh = trimesh.Trimesh(
        vertices=np.asarray(verts, dtype=np.float64),
        faces=np.asarray(faces, dtype=np.int64),
        process=True,
    )
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
    return extrude_polygon_along_axis(uv, length, center=center, axis=axis)


def extrude_polygon_along_axis(
    poly_uv: np.ndarray,
    length: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    axis: str = "x",
) -> md.Manifold:
    """
    Extrude a 2D CCW polygon centered around z_local=0:
      - axis='x': u -> Y, v -> Z, z_loc -> X
      - axis='y': u -> X, v -> Z, z_loc -> Y
      - axis='z': u -> X, v -> Y, z_loc -> Z
    """
    pts = np.asarray(poly_uv, dtype=np.float64)
    # Remove duplicate closing vertex if present
    if len(pts) > 2 and np.allclose(pts[0], pts[-1], atol=1e-6):
        pts = pts[:-1]
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    if area < 0.0:
        pts = pts[::-1]
    cs = md.CrossSection([pts.tolist()])
    solid = md.Manifold.extrude(cs, length).translate([0.0, 0.0, -length * 0.5])
    if axis == "x":
        solid = solid.rotate([0.0, 0.0, 90.0]).rotate([0.0, 90.0, 0.0])
    elif axis == "y":
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
    mat = trimesh.geometry.align_vectors(np.array([0.0, 0.0, 1.0]), vec / length)
    mesh.apply_transform(mat)
    mesh.apply_translation((p0 + p1) * 0.5)
    return trimesh_to_manifold(mesh)


# ---------------------------------------------------------------------------
# Twin-Chamber Plenum, Waist Bridge & Tapered Transfer Slot
# ---------------------------------------------------------------------------

def primary_area_scale(x: float, params: dict) -> float:
    p = params["primary_plenum"]
    x0 = float(p["cyl1_end_x_mm"])
    x1 = float(p["cyl4_end_x_mm"])
    r_cyl1 = float(p["taper_cyl1_area_ratio"])
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return float(r_cyl1 + (1.0 - r_cyl1) * t)


def primary_center_z(x: float, params: dict, is_inner: bool) -> float:
    """Hold inner bottom of Primary Chamber fixed at inner_bottom_z_mm so bridge thickness stays uniform."""
    p = params["primary_plenum"]
    s = math.sqrt(primary_area_scale(x, params))
    z_bot_in = float(p["inner_bottom_z_mm"])
    h_in_x = float(p["base_inner_height_z_mm"]) * s
    # Outer wall expands symmetrically around the same center Z so bottom stays at z_bot_in - wall
    return z_bot_in + 0.5 * h_in_x


def build_secondary_plenum_loft(params: dict, is_inner: bool, wall_offset_mm: float = 0.0) -> md.Manifold:
    """Build Secondary (lower) Runner Chamber with smooth domes on BOTH ends (-X and +X)."""
    sp = params["secondary_plenum"]
    wall = float(sp["wall_thickness_mm"])
    eff_off = float(wall_offset_mm) if is_inner else wall
    w = float(sp["inner_width_y_mm"]) + 2.0 * eff_off
    h = float(sp["inner_height_z_mm"]) + 2.0 * eff_off
    r = float(sp["inner_corner_radius_mm"]) + eff_off
    yc = float(sp["center_y_mm"])
    zc = float(sp["center_z_mm"])
    n_pts = int(sp["profile_segments"])

    x_left = float(sp["cyl1_end_x_mm"])
    x_right = float(sp["cyl4_end_x_mm"])
    dome_len = float(sp["end_dome_length_mm"]) - wall + eff_off
    dome_steps = 12
    thetas = np.linspace(0.22, math.pi * 0.5, dome_steps, endpoint=False)

    rings: list[np.ndarray] = []
    # 1) -X end dome
    for th in thetas:
        x = x_left - dome_len * math.cos(th)
        ds = math.sin(th)
        uv = rounded_rect_points(w * ds, h * ds, r * ds, n_pts)
        rings.append(np.column_stack([np.full(n_pts, x), uv[:, 0] + yc, uv[:, 1] + zc]))

    # 2) Constant central barrel spanning [x_left, x_right]
    for x in np.linspace(x_left, x_right, int(sp["axial_segments"])):
        uv = rounded_rect_points(w, h, r, n_pts)
        rings.append(np.column_stack([np.full(n_pts, float(x)), uv[:, 0] + yc, uv[:, 1] + zc]))

    # 3) +X end dome (closed end behind TB neck; TB feeds Primary Chamber only)
    for th in thetas[::-1]:
        x = x_right + dome_len * math.cos(th)
        ds = math.sin(th)
        uv = rounded_rect_points(w * ds, h * ds, r * ds, n_pts)
        rings.append(np.column_stack([np.full(n_pts, x), uv[:, 0] + yc, uv[:, 1] + zc]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def build_primary_plenum_loft(params: dict, is_inner: bool, wall_offset_mm: float = 0.0) -> md.Manifold:
    """Build Primary (upper-front) Tapered Diffuser Chamber with -X dome and open +X TB feed."""
    p = params["primary_plenum"]
    wall = float(p["wall_thickness_mm"])
    eff_off = float(wall_offset_mm) if is_inner else wall
    w_base = float(p["base_inner_width_y_mm"])
    h_base = float(p["base_inner_height_z_mm"])
    r_base = float(p["base_inner_corner_radius_mm"])
    yc = float(p["center_y_mm"])
    n_pts = int(p["profile_segments"])

    x_cyl1 = float(p["cyl1_end_x_mm"])
    x_cyl4 = float(p["cyl4_end_x_mm"]) + (-2.0 if is_inner else 2.0)
    dome_len = float(p["cyl1_dome_length_mm"]) - wall + eff_off
    s_cyl1 = math.sqrt(float(p["taper_cyl1_area_ratio"]))
    zc_cyl1 = primary_center_z(x_cyl1, params, is_inner)

    rings: list[np.ndarray] = []
    # 1) Smooth ellipsoidal dome on Cyl 1 (-X) end
    for th in np.linspace(0.22, math.pi * 0.5, 12, endpoint=False):
        x = x_cyl1 - dome_len * math.cos(th)
        ds = math.sin(th) * s_cyl1
        w = w_base * ds + 2.0 * eff_off * math.sin(th)
        h = h_base * ds + 2.0 * eff_off * math.sin(th)
        r = r_base * ds + eff_off * math.sin(th)
        uv = rounded_rect_points(w, h, r, n_pts)
        rings.append(np.column_stack([np.full(n_pts, x), uv[:, 0] + yc, uv[:, 1] + zc_cyl1]))

    # 2) Linear-area tapered barrel from Cyl 1 to Cyl 4 (+X)
    xs = np.linspace(x_cyl1, x_cyl4, int(p["axial_segments"]))
    if not np.any(np.isclose(xs, 0.0, atol=1e-4)):
        xs = np.sort(np.append(xs, 0.0))
    for x in xs:
        s = math.sqrt(primary_area_scale(float(x), params))
        zc = primary_center_z(float(x), params, is_inner)
        w = w_base * s + 2.0 * eff_off
        h = h_base * s + 2.0 * eff_off
        r = r_base * s + eff_off
        uv = rounded_rect_points(w, h, r, n_pts)
        rings.append(np.column_stack([np.full(n_pts, float(x)), uv[:, 0] + yc, uv[:, 1] + zc]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def _bridge_z_bounds(params: dict) -> tuple[float, float, float]:
    """Return (z_sec_top_in, z_bridge_mid, z_prim_bot_in) from active chamber parameters."""
    sec = params["secondary_plenum"]
    prim = params["primary_plenum"]
    z_sec_top = float(sec["center_z_mm"]) + 0.5 * float(sec["inner_height_z_mm"])
    z_prim_bot = float(prim["inner_bottom_z_mm"])
    z_mid = 0.5 * (z_sec_top + z_prim_bot)
    return z_sec_top, z_mid, z_prim_bot


def build_waist_bridge(params: dict) -> md.Manifold:
    """
    Loft a tapered solid aerodynamic fillet bridge along X in the waist zone
    between the Secondary and Primary outer walls so hoop loads distribute cleanly without
    sharp V-grooves while preserving the twin-chamber exterior silhouette.
    """
    p = params["primary_plenum"]
    sp = params["secondary_plenum"]
    z_sec_top, _z_mid, z_prim_bot = _bridge_z_bounds(params)
    x0 = float(p["cyl1_end_x_mm"])
    x1 = float(sp["cyl4_end_x_mm"]) + 2.0
    yc_p = float(p["center_y_mm"])
    yc_s = float(sp["center_y_mm"])
    wall = float(p["wall_thickness_mm"])
    w_p_base = float(p["base_inner_width_y_mm"])
    half_w_s_bot = 0.5 * float(sp["inner_width_y_mm"]) - 6.0

    rings: list[np.ndarray] = []
    xs = np.linspace(x0, x1, 44)
    if not np.any(np.isclose(xs, 0.0, atol=1e-4)):
        xs = np.sort(np.append(xs, 0.0))

    z_bot = z_sec_top - 8.0
    z_top = z_prim_bot + 6.0
    for x in xs:
        s = math.sqrt(primary_area_scale(float(x), params))
        w_p_out = w_p_base * s + 2.0 * wall
        y_top_l = yc_p - w_p_out * 0.44
        y_top_r = yc_p + w_p_out * 0.44
        y_bot_l = yc_s - half_w_s_bot
        y_bot_r = yc_s + half_w_s_bot
        pts_yz = np.array([
            [y_bot_r, z_bot],
            [y_top_r, z_top],
            [y_top_l, z_top],
            [y_bot_l, z_bot],
        ], dtype=np.float64)
        sub = []
        for idx in range(4):
            a = pts_yz[idx]
            b = pts_yz[(idx + 1) % 4]
            for f in (0.05, 0.35, 0.65, 0.95):
                sub.append(a * (1.0 - f) + b * f)
        arr = np.asarray(sub, dtype=np.float64)
        rings.append(np.column_stack([np.full(len(arr), float(x)), arr[:, 0], arr[:, 1]]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def build_transfer_slot_cavity(params: dict) -> md.Manifold:
    """
    Build the full-length venturi-flared tapered transfer slot linking Primary Chamber
    to Secondary Chamber across the 8 mm divider bridge.
    """
    sl = params["transfer_slot"]
    z_sec_top, z_mid, z_prim_bot = _bridge_z_bounds(params)
    x0 = float(sl["x_start_mm"])
    x1 = float(sl["x_end_mm"])
    yc = float(sl["center_y_mm"])
    w0 = float(sl["width_cyl1_mm"])
    w1 = float(sl["width_cyl4_mm"])
    flare_max = float(sl["venturi_flare_mm"])
    z_tmin = float(sl["throat_z_min_mm"])
    z_tmax = float(sl["throat_z_max_mm"])
    n_cap = int(sl["cap_segments"])

    z_levels = [
        z_sec_top - 5.0, z_sec_top - 1.0, z_sec_top + 0.3,
        z_tmin, z_mid, z_tmax,
        z_prim_bot - 0.3, z_prim_bot + 1.0, z_prim_bot + 5.0,
    ]
    flares = [flare_max + 1.5, flare_max * 0.65, flare_max * 0.25, 0.0, 0.0, 0.0, flare_max * 0.25, flare_max * 0.65, flare_max + 1.5]

    rings: list[np.ndarray] = []
    for zv, fl in zip(z_levels, flares):
        r0 = 0.5 * w0 + fl
        r1 = 0.5 * w1 + fl
        cx0 = x0 + 0.5 * w0
        cx1 = x1 - 0.5 * w1
        pts_xy: list[list[float]] = []
        for a in np.radians(np.linspace(-89.0, 89.0, n_cap)):
            pts_xy.append([cx1 + r1 * math.cos(a), yc + r1 * math.sin(a)])
        for t in np.linspace(0.08, 0.92, 10):
            pts_xy.append([cx1 * (1.0 - t) + cx0 * t, yc + r1 * (1.0 - t) + r0 * t])
        for a in np.radians(np.linspace(91.0, 269.0, n_cap)):
            pts_xy.append([cx0 + r0 * math.cos(a), yc + r0 * math.sin(a)])
        for t in np.linspace(0.08, 0.92, 10):
            pts_xy.append([cx0 * (1.0 - t) + cx1 * t, yc - (r0 * (1.0 - t) + r1 * t)])

        arr = np.asarray(pts_xy, dtype=np.float64)
        rings.append(np.column_stack([arr[:, 0], arr[:, 1], np.full(len(arr), zv)]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def build_interior_bond_envelope(params: dict, wall_offset_mm: float = 2.8) -> md.Manifold:
    """Return the twin-chamber interior envelope expanded by `wall_offset_mm` inside the 6 mm walls."""
    _z_sec_top, z_mid, _z_prim_bot = _bridge_z_bounds(params)
    sec_mid = build_secondary_plenum_loft(params, is_inner=True, wall_offset_mm=wall_offset_mm)
    prim_mid = build_primary_plenum_loft(params, is_inner=True, wall_offset_mm=wall_offset_mm)
    slot_in = build_transfer_slot_cavity(params)
    yc_p = float(params["primary_plenum"]["center_y_mm"])
    bridge_mid = md.Manifold.cube([320.0, 62.0, 14.0], center=True).translate([2.0, yc_p, z_mid])
    return m_union([sec_mid, prim_mid, slot_in, bridge_mid])


def build_turning_vanes(params: dict, bond_env: md.Manifold | None = None) -> list[md.Manifold]:
    """
    Build integral wall-to-wall curved turning-vane scoops / cross-flow baffles
    clipped cleanly to `bond_env`.
    """
    tv = params.get("turning_vanes", {})
    if not tv.get("enabled", False):
        return []

    _z_sec_top, z_mid, z_prim_bot = _bridge_z_bounds(params)
    t_half = float(tv["thickness_x_mm"]) * 0.5
    span_y = float(tv["span_y_mm"])
    yc = float(tv["center_y_mm"])
    vanes: list[md.Manifold] = []

    for v_cfg in tv["vanes"]:
        xb = float(v_cfg["x_base_mm"])
        zb = float(v_cfg["z_bottom_mm"])
        prim_h = float(v_cfg["primary_height_mm"])
        lean_x = float(v_cfg["upstream_lean_x_mm"])
        z_top = z_prim_bot + prim_h

        spine: list[np.ndarray] = []
        for z in np.linspace(zb, z_mid, 8, endpoint=False):
            spine.append(np.array([xb, float(z)], dtype=np.float64))
        for k in range(13):
            s = k / 12.0
            x_cur = xb + lean_x * (1.0 - math.cos(0.5 * math.pi * s))
            z_cur = z_mid + (z_top - z_mid) * s
            spine.append(np.array([x_cur, z_cur], dtype=np.float64))

        pts = np.asarray(spine, dtype=np.float64)
        n_sp = len(pts)
        tangents = np.zeros_like(pts)
        for i in range(n_sp):
            if i == 0:
                d = pts[1] - pts[0]
            elif i == n_sp - 1:
                d = pts[-1] - pts[-2]
            else:
                d = pts[i + 1] - pts[i - 1]
            tangents[i] = d / np.linalg.norm(d)
        normals = np.column_stack([tangents[:, 1], -tangents[:, 0]])

        right_side = pts + t_half * normals
        left_side = pts - t_half * normals

        top_dir = tangents[-1]
        ang_top0 = math.atan2(-top_dir[0], top_dir[1])
        top_cap = [
            pts[-1] + t_half * np.array([math.cos(a), math.sin(a)])
            for a in np.linspace(ang_top0, ang_top0 + math.pi, 10)[1:-1]
        ]
        bot_cap = [
            pts[0] + t_half * np.array([math.cos(a), math.sin(a)])
            for a in np.linspace(math.pi, 2.0 * math.pi, 10)[1:-1]
        ]

        poly_xz = np.vstack([
            right_side,
            np.asarray(top_cap) if top_cap else np.empty((0, 2)),
            left_side[::-1],
            np.asarray(bot_cap) if bot_cap else np.empty((0, 2)),
        ])
        poly_uv = np.column_stack([poly_xz[:, 0], -poly_xz[:, 1]])
        vane_raw = extrude_polygon_along_axis(poly_uv, span_y, center=(0.0, yc, 0.0), axis="y")
        vane_solid = (vane_raw ^ bond_env) if bond_env is not None else vane_raw
        bb_v = vane_solid.bounding_box()
        assert bb_v[2] >= zb - t_half - 1.5 and bb_v[5] <= z_top + t_half + 1.5, (
            f"Turning vane {v_cfg['name']} Z bounds invalid: [{bb_v[2]:.1f}, {bb_v[5]:.1f}]"
        )
        vanes.append(vane_solid)

    return vanes


# ---------------------------------------------------------------------------
# Runners, Straight Diffuser TB Neck, IACV, Boss Pads & Split Flange
# ---------------------------------------------------------------------------

def bezier_point_and_tangent(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float):
    u = 1.0 - t
    pt = (u**3) * p0 + 3 * (u**2) * t * p1 + 3 * u * (t**2) * p2 + (t**3) * p3
    tan = 3 * (u**2) * (p1 - p0) + 6 * u * t * (p2 - p1) + 3 * (t**2) * (p3 - p2)
    return pt, tan


def build_single_runner_components(x_center: float, params: dict) -> dict[str, md.Manifold]:
    """Build runner sweep, 2.00-inch round beaded spigot, and wall-flush bellmouth into Secondary Chamber."""
    r_cfg = params["runners"]
    sp_cfg = r_cfg["spigot"]
    sw = r_cfg["sweep"]
    bm = r_cfg["bellmouth"]
    sec = params["secondary_plenum"]

    n_pts = int(sw["profile_segments"])
    wall = float(sp_cfg["wall_thickness_mm"])

    sp_w_out = float(sp_cfg["outer_width_mm"])
    sp_h_out = float(sp_cfg["outer_height_mm"])
    sp_r_out = float(sp_cfg["corner_radius_mm"])
    sp_w_in = sp_w_out - 2.0 * wall
    sp_h_in = sp_h_out - 2.0 * wall
    sp_r_in = sp_r_out - wall

    entry_d = float(sw["plenum_entry_diameter_mm"])
    entry_w_in = entry_d
    entry_h_in = entry_d - 6.0  # 46 x 40 mm oval throat
    entry_r_in = entry_h_in * 0.48
    entry_wall = max(wall, 5.0)
    entry_w_out = entry_w_in + 2.0 * entry_wall
    entry_h_out = entry_h_in + 2.0 * entry_wall
    entry_r_out = entry_r_in + entry_wall

    tip_y = float(sp_cfg["tip_y_mm"])
    land_len = float(sp_cfg["land_length_mm"])
    sweep_end_y = tip_y + land_len
    sp_z = float(sp_cfg["center_z_mm"])

    y_sec_rear_in = float(sec["center_y_mm"]) - 0.5 * float(sec["inner_width_y_mm"])
    entry_z = float(sw.get("plenum_entry_z_mm", -56.0))
    el_rad = math.radians(float(sw.get("entry_elevation_deg", -14.0)))
    inlet_dir = np.array([0.0, -math.cos(el_rad), -math.sin(el_rad)])

    p_bm_tip = np.array([x_center, y_sec_rear_in + 8.5, entry_z])
    p0 = p_bm_tip + inlet_dir * 16.0
    p3 = np.array([x_center, sweep_end_y, sp_z])
    p1 = p0 + inlet_dir * 26.0
    p2 = p3 + np.array([0.0, 32.0, 0.0])

    up_hint = np.array([0.0, 0.0, 1.0])

    # 1) Outer runner sweep + straight spigot land + retention bead
    outer_rings: list[np.ndarray] = []
    n_loft = int(sw["loft_segments"])
    for k in range(n_loft + 1):
        t = k / n_loft
        pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        w = entry_w_out + (sp_w_out - entry_w_out) * s_t
        h = entry_h_out + (sp_h_out - entry_h_out) * s_t
        r = entry_r_out + (sp_r_out - entry_r_out) * s_t
        outer_rings.append(ring_frame_points(pt, tan, up_hint, rounded_rect_points(w, h, r, n_pts)))

    bead_h = float(sp_cfg["retention_bead_height_mm"])
    bead_w = float(sp_cfg["retention_bead_width_mm"])
    bead_off = float(sp_cfg["retention_bead_offset_from_tip_mm"])
    y_bead_start = tip_y + bead_off
    y_bead_peak1 = y_bead_start + 1.5
    y_bead_peak2 = y_bead_start + bead_w - 1.5
    y_bead_end = y_bead_start + bead_w
    tan_sp = np.array([0.0, -1.0, 0.0])
    for y_pos, dr in [
        (y_bead_end + 4.0, 0.0),
        (y_bead_end, 0.0),
        (y_bead_peak2, bead_h),
        (y_bead_peak1, bead_h),
        (y_bead_start, 0.0),
        (tip_y, 0.0),
    ]:
        uv = rounded_rect_points(sp_w_out + 2.0 * dr, sp_h_out + 2.0 * dr, sp_r_out + dr, n_pts)
        outer_rings.append(ring_frame_points(np.array([x_center, y_pos, sp_z]), tan_sp, up_hint, uv))
    outer_solid = trimesh_to_manifold(loft_closed_solid(outer_rings))

    # 2) Flush velocity-stack bellmouth reinforcement collar
    bm_len = float(bm["protrusion_into_plenum_mm"])
    bm_flare = float(bm["flare_radial_mm"])
    bm_wall = float(bm["wall_thickness_mm"])
    p_bm_anchor = p0 + inlet_dir * 10.0
    bm_total_len = float(np.linalg.norm(p_bm_anchor - p_bm_tip))
    bm_rings: list[np.ndarray] = []
    n_bm = 20
    for k in range(n_bm + 1):
        s_dist = -2.2 + (k / n_bm) * (bm_total_len + 2.2)
        pos = p_bm_tip + inlet_dir * float(s_dist)
        if s_dist < 0.0:
            inner_flare = bm_flare + (-s_dist) * 0.40
        else:
            u = np.clip(s_dist / bm_len, 0.0, 1.0)
            inner_flare = bm_flare * ((1.0 - u) ** 2)
        uv = rounded_rect_points(
            entry_w_in + 2.0 * (inner_flare + bm_wall),
            entry_h_in + 2.0 * (inner_flare + bm_wall),
            entry_r_in + inner_flare + bm_wall,
            n_pts,
        )
        bm_rings.append(ring_frame_points(pos, inlet_dir, up_hint, uv))
    bellmouth_outer = trimesh_to_manifold(loft_closed_solid(bm_rings))

    # 3) Continuous inner air bore
    bore_rings: list[np.ndarray] = []
    throat_len = float(np.linalg.norm(p0 - p_bm_tip))
    for s_dist in np.linspace(-3.0, throat_len - 0.8, 17):
        pos = p_bm_tip + inlet_dir * float(s_dist)
        if s_dist < 0.0:
            flare_r = bm_flare + (-s_dist) * 0.45
        else:
            u = np.clip(s_dist / bm_len, 0.0, 1.0)
            flare_r = bm_flare * ((1.0 - u) ** 2)
        uv = rounded_rect_points(
            entry_w_in + 2.0 * flare_r, entry_h_in + 2.0 * flare_r, entry_r_in + flare_r, n_pts
        )
        bore_rings.append(ring_frame_points(pos, inlet_dir, up_hint, uv))

    for k in range(1, n_loft + 1):
        t = k / n_loft
        pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        w = entry_w_in + (sp_w_in - entry_w_in) * s_t
        h = entry_h_in + (sp_h_in - entry_h_in) * s_t
        r = entry_r_in + (sp_r_in - entry_r_in) * s_t
        bore_rings.append(ring_frame_points(pt, tan, up_hint, rounded_rect_points(w, h, r, n_pts)))

    bore_rings.append(
        ring_frame_points(
            np.array([x_center, tip_y - 6.0, sp_z]),
            tan_sp,
            up_hint,
            rounded_rect_points(sp_w_in, sp_h_in, sp_r_in, n_pts),
        )
    )
    inner_bore = trimesh_to_manifold(loft_closed_solid(bore_rings))

    return {
        "outer": outer_solid,
        "bellmouth_outer": bellmouth_outer,
        "inner_bore": inner_bore,
    }


def build_throttle_body_components(params: dict) -> dict[str, md.Manifold]:
    """Build low-angle conical diffuser neck feeding straight into the +X end of Primary Chamber."""
    tb = params["throttle_body"]
    pl = params["primary_plenum"]
    wall = float(tb["neck_wall_thickness_mm"])
    bore_d = float(tb["bore_diameter_mm"])
    neck_len = float(tb["neck_length_mm"])
    cant_rad = math.radians(float(tb["forward_cant_deg"]))

    x_start = float(pl["cyl4_end_x_mm"])
    yc = float(pl["center_y_mm"])
    zc = primary_center_z(x_start, params, is_inner=True)

    p_start = np.array([x_start - 4.0, yc, zc])
    tb_axis = np.array([math.cos(cant_rad), math.sin(cant_rad), 0.0])
    p_flange_back = np.array([x_start, yc, zc]) + tb_axis * neck_len
    p_flange_face = p_flange_back + tb_axis * float(tb["flange_thickness_mm"])

    pl_wall = float(pl["wall_thickness_mm"])
    pl_w_in = float(pl["base_inner_width_y_mm"])
    pl_h_in = float(pl["base_inner_height_z_mm"])
    pl_r_in = float(pl["base_inner_corner_radius_mm"])
    pl_w_out = pl_w_in + 2.0 * pl_wall
    pl_h_out = pl_h_in + 2.0 * pl_wall
    pl_r_out = pl_r_in + pl_wall

    n_pts = int(pl["profile_segments"])
    up_hint = np.array([0.0, 0.0, 1.0])

    neck_out_rings = []
    neck_in_rings = []
    n_steps = 20
    for k in range(n_steps + 1):
        t = k / n_steps
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        pos = p_start + (p_flange_back + tb_axis * 4.0 - p_start) * t
        tan = np.array([1.0, 0.0, 0.0]) * (1.0 - s_t) + tb_axis * s_t
        w_out = pl_w_out + (bore_d + 2.0 * wall - pl_w_out) * s_t
        h_out = pl_h_out + (bore_d + 2.0 * wall - pl_h_out) * s_t
        r_out = pl_r_out + ((bore_d + 2.0 * wall) * 0.5 - pl_r_out) * s_t
        neck_out_rings.append(ring_frame_points(pos, tan, up_hint, rounded_rect_points(w_out, h_out, r_out, n_pts)))

        w_in = pl_w_in + (bore_d - pl_w_in) * s_t
        h_in = pl_h_in + (bore_d - pl_h_in) * s_t
        r_in = pl_r_in + (bore_d * 0.5 - pl_r_in) * s_t
        neck_in_rings.append(ring_frame_points(pos, tan, up_hint, rounded_rect_points(w_in, h_in, r_in, n_pts)))

    neck_in_rings.append(
        ring_frame_points(
            p_flange_face + tb_axis * 6.0,
            tb_axis,
            up_hint,
            rounded_rect_points(bore_d, bore_d, bore_d * 0.5, n_pts),
        )
    )
    neck_outer = trimesh_to_manifold(loft_closed_solid(neck_out_rings))
    tb_bore = trimesh_to_manifold(loft_closed_solid(neck_in_rings))

    fl_uv = rounded_rect_points(
        float(tb["flange_width_mm"]),
        float(tb["flange_height_mm"]),
        float(tb["flange_corner_radius_mm"]),
        64,
    )
    flange_outer = trimesh_to_manifold(
        loft_closed_solid([
            ring_frame_points(p_flange_back, tb_axis, up_hint, fl_uv),
            ring_frame_points(p_flange_face, tb_axis, up_hint, fl_uv),
        ])
    )

    u_ax = np.cross(up_hint, tb_axis)
    u_ax /= np.linalg.norm(u_ax)
    v_ax = np.cross(tb_axis, u_ax)
    v_ax /= np.linalg.norm(v_ax)

    cutters: list[md.Manifold] = [tb_bore]
    bx = float(tb["bolt_spacing_x_mm"]) * 0.5
    by = float(tb["bolt_spacing_y_mm"]) * 0.5
    b_rad = float(tb["bolt_hole_diameter_mm"]) * 0.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pt_center = p_flange_back + u_ax * (sx * bx) + v_ax * (sy * by)
            cutters.append(
                make_cylinder_along(
                    pt_center - tb_axis * 3.0,
                    pt_center + tb_axis * (float(tb["flange_thickness_mm"]) + 3.0),
                    b_rad,
                    segments=32,
                )
            )

    og = tb["oring_groove"]
    if og["enabled"]:
        r_in_g = float(og["inner_diameter_mm"]) * 0.5
        r_out_g = r_in_g + float(og["width_mm"])
        depth_g = float(og["depth_mm"])
        outer_g = make_cylinder_along(p_flange_face - tb_axis * depth_g, p_flange_face + tb_axis * 1.0, r_out_g, segments=72)
        inner_g = make_cylinder_along(p_flange_face - tb_axis * (depth_g + 1.0), p_flange_face + tb_axis * 2.0, r_in_g, segments=72)
        cutters.append(outer_g - inner_g)

    return {
        "outer": m_union([neck_outer, flange_outer]),
        "cutters": m_union(cutters),
        "flange_face_center": p_flange_face,
        "tb_axis": tb_axis,
    }


def build_boss_pad_components(pad_cfg: dict, params: dict) -> tuple[md.Manifold, list[md.Manifold]]:
    """
    Build a zero-height-penalty horizontal (-Y facing) NPT boss pad on the rear face
    of Primary Chamber, keeping Z_max below the roof/TB envelope.
    """
    pl = params["primary_plenum"]
    xc = float(pad_cfg["x_center_mm"])
    zc = float(pad_cfg["z_center_mm"])
    yc_p = float(pl["center_y_mm"])
    s_bp = math.sqrt(primary_area_scale(xc, params))
    y_rear_in = yc_p - 0.5 * float(pl["base_inner_width_y_mm"]) * s_bp
    y_out = float(pad_cfg["y_outer_face_mm"])
    y_in_anchor = y_rear_in + 4.0  # overlaps primary rear wall; trimmed cleanly inside by prim_inner

    pad = make_rounded_prism(
        float(pad_cfg["length_x_mm"]),
        float(pad_cfg["height_z_mm"]),
        6.0,
        y_in_anchor - y_out,
        segments=48,
        center=(xc, 0.5 * (y_out + y_in_anchor), zc),
        axis="y",
    )
    diameters = pad_cfg["port_pilot_diameters_mm"]
    start_x = xc - float(pad_cfg["port_spacing_x_mm"]) * (int(pad_cfg["port_count"]) - 1) * 0.5
    bores: list[md.Manifold] = []
    for idx in range(int(pad_cfg["port_count"])):
        px = start_x + idx * float(pad_cfg["port_spacing_x_mm"])
        p_rad = float(diameters[idx]) * 0.5
        bores.append(
            make_cylinder_along(
                np.array([px, y_out - 4.0, zc]),
                np.array([px, y_rear_in + 12.0, zc]),
                p_rad,
                segments=32,
            )
        )
    return pad, bores


def build_iacv_components(params: dict) -> dict[str, md.Manifold]:
    """
    Build the 2-bolt Ford IACV mounting pad on the -Y rear wall of the TB neck / Cyl 4 Primary junction:
      - Downstream port (-X side): punches cleanly into Primary Chamber.
      - Upstream metered supply port (+X side): blind pocket stopping >= 4.5 mm clear of TB bore,
        intersected vertically (+Z face) by a 1/4"-18 NPT (Ø11.1 mm) blow-through MAF supply tap.
    """
    iac = params["throttle_body"]["iacv_mount"]
    pl = params["primary_plenum"]
    tb = params["throttle_body"]

    xc = float(iac["x_center_mm"])
    zc = float(iac["z_center_mm"])
    y_out = float(iac["y_outer_face_mm"])
    y_anchor = float(iac["y_inner_anchor_mm"])
    pad_len_x = float(iac["pad_length_x_mm"])
    pad_h_z = float(iac["pad_height_z_mm"])

    port_half = float(iac["port_spacing_x_mm"]) * 0.5
    x_plenum_port = xc - port_half
    x_supply_port = xc + port_half

    # Check solid wall thickness between blind supply pocket end and TB inner bore (-Y wall)
    cant_rad = math.radians(float(tb["forward_cant_deg"]))
    x_neck_start = float(pl["cyl4_end_x_mm"]) - 4.0
    x_neck_end = float(pl["cyl4_end_x_mm"]) + (float(tb["neck_length_mm"]) + 4.0) * math.cos(cant_rad)
    t_supply = np.clip((x_supply_port - x_neck_start) / (x_neck_end - x_neck_start), 0.0, 1.0)
    s_t = 0.5 - 0.5 * math.cos(math.pi * float(t_supply))
    w_in_at_supply = float(pl["base_inner_width_y_mm"]) + (float(tb["bore_diameter_mm"]) - float(pl["base_inner_width_y_mm"])) * s_t
    tb_inner_rear_y = float(pl["center_y_mm"]) - 0.5 * w_in_at_supply
    wall_thickness = tb_inner_rear_y - float(iac["supply_pocket_end_y_mm"])
    assert wall_thickness >= 4.5, (
        f"IACV supply wall thickness {wall_thickness:.2f} mm < 4.5 mm at X={x_supply_port}"
    )

    pad_outer = make_rounded_prism(
        pad_len_x,
        pad_h_z,
        float(iac["pad_corner_radius_mm"]),
        y_anchor - y_out,
        segments=48,
        center=(xc, 0.5 * (y_out + y_anchor), zc),
        axis="y",
    )

    cutters: list[md.Manifold] = []
    # 2x M6 blind bolt pilot holes along Z
    b_rad = float(iac["bolt_pilot_diameter_mm"]) * 0.5
    b_half = float(iac["bolt_spacing_z_mm"]) * 0.5
    b_end_y = y_out + float(iac["bolt_depth_mm"])
    for sz in (-1.0, 1.0):
        cutters.append(
            make_cylinder_along(
                np.array([xc, y_out - 4.0, zc + sz * b_half]),
                np.array([xc, b_end_y, zc + sz * b_half]),
                b_rad,
                segments=32,
            )
        )

    p_rad = float(iac["port_diameter_mm"]) * 0.5
    # Downstream IAC discharge port -> punches straight into Primary Chamber
    cutters.append(
        make_cylinder_along(
            np.array([x_plenum_port, y_out - 4.0, zc]),
            np.array([x_plenum_port, float(pl["center_y_mm"]) - 16.0, zc]),
            p_rad,
            segments=36,
        )
    )
    # Upstream metered IAC supply pocket -> stops cleanly before TB bore
    cutters.append(
        make_cylinder_along(
            np.array([x_supply_port, y_out - 4.0, zc]),
            np.array([x_supply_port, float(iac["supply_pocket_end_y_mm"]), zc]),
            p_rad,
            segments=36,
        )
    )
    # Top-facing (+Z) 1/4"-18 NPT (Ø11.1 mm) supply tap intersecting supply pocket
    z_top_face = zc + 0.5 * pad_h_z
    tap_rad = float(iac["top_supply_tap_diameter_mm"]) * 0.5
    cutters.append(
        make_cylinder_along(
            np.array([x_supply_port, float(iac["top_supply_tap_y_mm"]), z_top_face + 4.0]),
            np.array([x_supply_port, float(iac["top_supply_tap_y_mm"]), zc - 3.0]),
            tap_rad,
            segments=36,
        )
    )

    return {
        "outer": pad_outer,
        "cutters": m_union(cutters),
        "wall_thickness_mm": wall_thickness,
    }


def _outer_2d_polygon_at_x(pl_combined_outer: md.Manifold, x_pos: float) -> ShapelyPolygon:
    """Slice combined twin-chamber outer solid at X = x_pos and return clean exterior (Y, Z) Polygon."""
    polys = pl_combined_outer.rotate([0.0, -90.0, 0.0]).slice(x_pos).to_polygons()
    sh_polys = [
        ShapelyPolygon(np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]])).buffer(0.0)
        for p in polys
        if len(p) >= 3
    ]
    merged = unary_union(sh_polys)
    if merged.geom_type == "MultiPolygon":
        merged = max(merged.geoms, key=lambda g: g.area)
    return ShapelyPolygon(merged.exterior.coords)


def build_hoop_ribs(pl_combined_outer: md.Manifold, params: dict) -> list[md.Manifold]:
    """Build exact contour-following twin-chamber hoop stiffening ribs at X = ±92 mm."""
    hr = params["plenum_ribs_and_bosses"]["hoop_ribs"]
    if not hr["enabled"]:
        return []
    ribs: list[md.Manifold] = []
    width_x = float(hr["width_mm"])
    h_rad = float(hr["radial_height_mm"])
    for xr in hr["x_positions_mm"]:
        outer_2d = _outer_2d_polygon_at_x(pl_combined_outer, float(xr))
        rib_2d = outer_2d.buffer(h_rad, join_style=1, quad_segs=16)
        coords = np.asarray(rib_2d.exterior.coords, dtype=np.float64)
        ribs.append(extrude_polygon_along_axis(coords, width_x, center=(float(xr), 0.0, 0.0), axis="x"))
    return ribs


def build_center_split_flange_and_cutters(pl_combined_outer: md.Manifold, params: dict) -> dict:
    """
    Build the twin-chamber split flange ring at X = 0, 8x M6 bolts, 2x Ø6 mm dowel pins,
    and one continuous Viton O-ring groove wrapping both chambers with zero T-junctions.
    """
    cs = params["center_split"]
    x_split = float(cs["split_x_mm"])
    ext = float(cs["flange_radial_extension_mm"])
    thick_total = 2.0 * float(cs["flange_thickness_per_side_mm"])

    outer_2d = _outer_2d_polygon_at_x(pl_combined_outer, x_split)
    flange_outer_2d = outer_2d.buffer(ext, join_style=1, quad_segs=16)
    flange_poly_coords = np.asarray(flange_outer_2d.exterior.coords, dtype=np.float64)
    inner_poly_coords = np.asarray(outer_2d.buffer(-8.0, join_style=1, quad_segs=12).exterior.coords, dtype=np.float64)

    flange_solid = extrude_polygon_along_axis(flange_poly_coords, thick_total, center=(x_split, 0.0, 0.0), axis="x")
    inner_clear = extrude_polygon_along_axis(inner_poly_coords, thick_total + 4.0, center=(x_split, 0.0, 0.0), axis="x")
    flange_ring = flange_solid - inner_clear

    # Evenly distribute (8 bolts + 2 dowels = 10 stations) along the +10.5 mm perimeter centerline
    bolt_line = LineString(outer_2d.buffer(float(cs["bolt_radial_offset_mm"]), join_style=1, quad_segs=16).exterior)
    total_pts = int(cs["bolt_count"]) + 2
    # Start offset by 0.05 of perimeter so stations straddle the top/bottom crests symmetrically
    cutters: list[md.Manifold] = []
    b_rad = float(cs["bolt_hole_diameter_mm"]) * 0.5
    p_rad = float(cs["dowel_pin_diameter_mm"]) * 0.5
    dowel_indices = {1, 6}
    for idx in range(total_pts):
        frac = ((idx + 0.5) / total_pts) % 1.0
        pt = bolt_line.interpolate(frac, normalized=True)
        rad = p_rad if idx in dowel_indices else b_rad
        cutters.append(
            make_cylinder_along(
                np.array([x_split - thick_total * 0.6, pt.x, pt.y]),
                np.array([x_split + thick_total * 0.6, pt.x, pt.y]),
                rad,
                segments=32,
            )
        )

    # Continuous single-loop Viton O-ring groove on -X face
    og = cs["oring_groove"]
    og_cut = None
    oring_len_mm = 0.0
    if og["enabled"]:
        r_mid = float(og["radial_offset_from_outer_shell_mm"])
        gw = float(og["width_mm"])
        gd = float(og["depth_mm"])
        or_center_poly = outer_2d.buffer(r_mid, join_style=1, quad_segs=16)
        oring_len_mm = float(or_center_poly.exterior.length)
        g_outer = extrude_polygon_along_axis(
            np.asarray(outer_2d.buffer(r_mid + gw * 0.5, join_style=1, quad_segs=16).exterior.coords),
            gd + 0.8,
            center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0),
            axis="x",
        )
        g_inner = extrude_polygon_along_axis(
            np.asarray(outer_2d.buffer(r_mid - gw * 0.5, join_style=1, quad_segs=16).exterior.coords),
            gd + 2.0,
            center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0),
            axis="x",
        )
        og_cut = g_outer - g_inner

    return {
        "flange_ring": flange_ring,
        "hole_cutters": m_union(cutters),
        "oring_cutter": og_cut,
        "oring_centerline_mm": round(oring_len_mm, 1),
    }


def build_fitment_gauges(params: dict) -> dict[str, md.Manifold]:
    """Build test print gauges (2-inch round boot, 65 mm TB flange, 2-bolt Ford IACV, dowel pins)."""
    sp = params["runners"]["spigot"]
    g = params["gauges"]
    n_pts = int(params["runners"]["sweep"]["profile_segments"])
    wall = float(sp["wall_thickness_mm"])

    w_out = float(sp["outer_width_mm"])
    h_out = float(sp["outer_height_mm"])
    r_out = float(sp["corner_radius_mm"])
    w_in = w_out - 2.0 * wall
    h_in = h_out - 2.0 * wall
    r_in = r_out - wall

    bead_h = float(sp["retention_bead_height_mm"])
    bead_w = float(sp["retention_bead_width_mm"])
    bead_off = float(sp["retention_bead_offset_from_tip_mm"])
    total_len = float(g["boot_fit_gauge_length_mm"])

    z_tip = total_len
    z_b_start = z_tip - bead_off
    z_b_p1 = z_b_start - 1.5
    z_b_p2 = z_b_start - bead_w + 1.5
    z_b_end = z_b_start - bead_w
    rings = []
    for z, dr in [
        (0.0, 3.0), (5.0, 3.0), (6.5, 0.0), (z_b_end, 0.0),
        (z_b_p2, bead_h), (z_b_p1, bead_h), (z_b_start, 0.0), (z_tip, 0.0),
    ]:
        uv = rounded_rect_points(w_out + 2.0 * dr, h_out + 2.0 * dr, r_out + dr, n_pts)
        rings.append(np.column_stack([uv[:, 0], uv[:, 1], np.full(n_pts, z)]))
    boot_outer = trimesh_to_manifold(loft_closed_solid(rings))
    boot_bore = make_rounded_prism(w_in, h_in, r_in, total_len + 4.0, segments=n_pts, center=(0.0, 0.0, total_len * 0.5), axis="z")
    boot_gauge = boot_outer - boot_bore

    tb = params["throttle_body"]
    t_g = float(g["tb_fit_gauge_thickness_mm"])
    tb_plate = make_rounded_prism(
        float(tb["flange_width_mm"]), float(tb["flange_height_mm"]), float(tb["flange_corner_radius_mm"]), t_g,
        segments=64, center=(0.0, 0.0, t_g * 0.5), axis="z"
    )
    tb_cutters = [
        md.Manifold.cylinder(
            t_g + 4.0, float(tb["bore_diameter_mm"]) * 0.5, float(tb["bore_diameter_mm"]) * 0.5,
            circular_segments=72, center=True
        ).translate([0.0, 0.0, t_g * 0.5])
    ]
    bx = float(tb["bolt_spacing_x_mm"]) * 0.5
    by = float(tb["bolt_spacing_y_mm"]) * 0.5
    b_rad = float(tb["bolt_hole_diameter_mm"]) * 0.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            tb_cutters.append(
                md.Manifold.cylinder(t_g + 4.0, b_rad, b_rad, circular_segments=32, center=True).translate([sx * bx, sy * by, t_g * 0.5])
            )
    tb_gauge = m_diff(tb_plate, tb_cutters)

    iac = params["throttle_body"]["iacv_mount"]
    t_iac = float(g["iacv_fit_gauge_thickness_mm"])
    iac_plate = make_rounded_prism(
        float(iac["pad_length_x_mm"]), float(iac["pad_height_z_mm"]), float(iac["pad_corner_radius_mm"]), t_iac,
        segments=48, center=(0.0, 0.0, t_iac * 0.5), axis="z"
    )
    iac_cutters: list[md.Manifold] = []
    for sx in (-1.0, 1.0):
        iac_cutters.append(
            md.Manifold.cylinder(
                t_iac + 4.0, float(iac["port_diameter_mm"]) * 0.5, float(iac["port_diameter_mm"]) * 0.5,
                circular_segments=36, center=True
            ).translate([sx * float(iac["port_spacing_x_mm"]) * 0.5, 0.0, t_iac * 0.5])
        )
    for sy in (-1.0, 1.0):
        iac_cutters.append(
            md.Manifold.cylinder(t_iac + 4.0, 3.2, 3.2, circular_segments=32, center=True).translate([0.0, sy * float(iac["bolt_spacing_z_mm"]) * 0.5, t_iac * 0.5])
        )
    iacv_gauge = m_diff(iac_plate, iac_cutters)

    pin_len = float(g["dowel_pin_length_mm"])
    pin_diams = g["dowel_pin_diameters_mm"]
    pin_list = [float(pin_diams[0]), float(pin_diams[0]), float(pin_diams[-1]), float(pin_diams[-1])]
    y_offsets = [-18.0, -6.0, 6.0, 18.0]
    pin_solids: list[md.Manifold] = []
    for d_pin, y_off in zip(pin_list, y_offsets):
        r_pin = d_pin * 0.5
        r_ch = max(r_pin - 0.85, 0.5)
        p_rings = []
        for z_loc, rad in [(0.0, r_ch), (0.9, r_pin), (pin_len - 0.9, r_pin), (pin_len, r_ch)]:
            uv = rounded_rect_points(2.0 * rad, 2.0 * rad, rad, 48)
            p_rings.append(np.column_stack([uv[:, 0], uv[:, 1], np.full(48, z_loc)]))
        pin_v = trimesh_to_manifold(loft_closed_solid(p_rings))
        pin_solids.append(pin_v.rotate([0.0, 90.0, 0.0]).translate([-pin_len * 0.5, y_off, r_pin - 0.35]))
    runner_tab = md.Manifold.cube([1.8, 38.0, 0.85], center=True).translate([0.0, 0.0, 0.425])
    flat_bed_clip = md.Manifold.cube([200.0, 200.0, 200.0], center=True).translate([0.0, 0.0, 100.0])
    dowel_pins_set = m_union([*pin_solids, runner_tab]) ^ flat_bed_clip

    return {
        "boot_fit_gauge": boot_gauge,
        "tb_flange_fit_gauge": tb_gauge,
        "iacv_flange_fit_gauge": iacv_gauge,
        "alignment_dowel_pins": dowel_pins_set,
    }


# ---------------------------------------------------------------------------
# Full Assembly Pipeline
# ---------------------------------------------------------------------------

def assemble_all(params: dict) -> dict:
    sec_outer = build_secondary_plenum_loft(params, is_inner=False)
    sec_inner = build_secondary_plenum_loft(params, is_inner=True)
    prim_outer = build_primary_plenum_loft(params, is_inner=False)
    prim_inner = build_primary_plenum_loft(params, is_inner=True)
    waist_bridge = build_waist_bridge(params)
    slot_cavity = build_transfer_slot_cavity(params)

    pl_combined_outer = m_union([sec_outer, prim_outer, waist_bridge])

    runner_outers: list[md.Manifold] = []
    bellmouth_outers: list[md.Manifold] = []
    runner_bores: list[md.Manifold] = []
    for x_c in params["runners"]["center_x_mm"]:
        rc = build_single_runner_components(float(x_c), params)
        runner_outers.append(rc["outer"])
        bellmouth_outers.append(rc["bellmouth_outer"])
        runner_bores.append(rc["inner_bore"])

    # External runner tie webs
    tw = params["runners"]["tie_webs"]
    webs: list[md.Manifold] = []
    if tw["enabled"]:
        y_mid = 0.5 * (float(tw["y_start_mm"]) + float(tw["y_end_mm"]))
        y_len = abs(float(tw["y_end_mm"]) - float(tw["y_start_mm"]))
        z_mid = 0.5 * (
            float(params["runners"]["spigot"]["center_z_mm"])
            + float(params["runners"]["sweep"]["plenum_entry_z_mm"])
        )
        for x_mid in (-92.0, 92.0):
            webs.append(md.Manifold.cube([54.0, y_len, float(tw["height_mm"])], center=True).translate([x_mid, y_mid, z_mid]))

    ribs = build_hoop_ribs(pl_combined_outer, params)

    # -Y horizontal NPT pads on Primary Chamber
    boss_solids: list[md.Manifold] = []
    boss_bores: list[md.Manifold] = []
    rb_cfg = params["plenum_ribs_and_bosses"]
    for key in ("vacuum_boss_pad", "vacuum_only_boss_pad"):
        pad_cfg = rb_cfg.get(key)
        if pad_cfg and pad_cfg.get("enabled"):
            pad_s, pad_b = build_boss_pad_components(pad_cfg, params)
            boss_solids.append(pad_s)
            boss_bores.extend(pad_b)

    tb_parts = build_throttle_body_components(params)
    iacv_parts = build_iacv_components(params) if params["throttle_body"]["iacv_mount"]["enabled"] else None

    # Center rib for 1-piece reference stiffness
    hr = rb_cfg["hoop_ribs"]
    center_outer_2d = _outer_2d_polygon_at_x(pl_combined_outer, 0.0)
    center_rib = extrude_polygon_along_axis(
        np.asarray(center_outer_2d.buffer(float(hr["radial_height_mm"]), join_style=1, quad_segs=16).exterior.coords),
        float(hr["width_mm"]),
        center=(0.0, 0.0, 0.0),
        axis="x",
    )

    bond_env = build_interior_bond_envelope(params, wall_offset_mm=2.8)
    turning_vanes = build_turning_vanes(params, bond_env=bond_env)
    internal_cavities = m_union([sec_inner, prim_inner, slot_cavity, tb_parts["cutters"]])

    # --- 1-Piece Reference Solid ---
    outer_1pc = m_union(
        [pl_combined_outer, *runner_outers, *bellmouth_outers, *webs, *ribs, center_rib, *boss_solids, tb_parts["outer"]]
        + ([iacv_parts["outer"]] if iacv_parts else [])
    )
    hollow_1pc = outer_1pc - internal_cavities
    if turning_vanes:
        hollow_1pc = m_union([hollow_1pc, *turning_vanes])
    sub_1pc = [*runner_bores, *boss_bores] + ([iacv_parts["cutters"]] if iacv_parts else [])
    final_1pc = m_diff(hollow_1pc, sub_1pc)

    # --- 2-Piece Split Solid ---
    split_parts = build_center_split_flange_and_cutters(pl_combined_outer, params)
    outer_split = m_union(
        [pl_combined_outer, *runner_outers, *bellmouth_outers, *webs, *ribs, *boss_solids, tb_parts["outer"], split_parts["flange_ring"]]
        + ([iacv_parts["outer"]] if iacv_parts else [])
    )
    hollow_split = outer_split - internal_cavities
    if turning_vanes:
        hollow_split = m_union([hollow_split, *turning_vanes])
    sub_split = [*runner_bores, *boss_bores, split_parts["hole_cutters"]] + ([iacv_parts["cutters"]] if iacv_parts else [])
    full_for_split = m_diff(hollow_split, sub_split)

    x_split = float(params["center_split"]["split_x_mm"])
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
        "svt_wrc_manifold_1piece_full": final_1pc,
        "svt_wrc_manifold_split_left_cyl1_2": split_left,
        "svt_wrc_manifold_split_right_cyl3_4_tb": split_right,
        "svt_wrc_manifold_split_left_print_oriented": split_left_print,
        "svt_wrc_manifold_split_right_print_oriented": split_right_print,
        "svt_wrc_runner_boot_fit_gauge": gauges["boot_fit_gauge"],
        "svt_wrc_tb_flange_fit_gauge": gauges["tb_flange_fit_gauge"],
        "svt_wrc_iacv_flange_fit_gauge": gauges["iacv_flange_fit_gauge"],
        "svt_wrc_alignment_dowel_pins": gauges["alignment_dowel_pins"],
        "_prim_inner": prim_inner,
        "_sec_inner": sec_inner,
        "_slot_cavity": slot_cavity,
        "_plenum_inner_total": m_union([prim_inner, sec_inner, slot_cavity]),
        "_iacv_wall_thickness_mm": iacv_parts["wall_thickness_mm"] if iacv_parts else None,
        "_oring_centerline_mm": split_parts["oring_centerline_mm"],
    }


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

def render_overview_png(meshes: dict[str, trimesh.Trimesh], solids: dict[str, md.Manifold], params: dict, out_path: Path):
    fig = plt.figure(figsize=(16, 11.5), facecolor="#f5f4f0")
    fig.suptitle(
        "2004 Ford Focus SVT Turbo — Dual-Chamber WRC Tapered Slot-Diffuser Intake Manifold",
        fontsize=14.5,
        fontweight="bold",
        y=0.97,
        color="#1f242b",
    )

    def add_section_patches(ax, polys_2d: list[np.ndarray], facecolor: str, edgecolor: str, lw: float = 0.9, alpha: float = 1.0):
        if not polys_2d:
            return
        sh_polys = [ShapelyPolygon(p) for p in polys_2d if len(p) >= 3]
        depths = [
            sum(1 for j, pj in enumerate(sh_polys) if i != j and pj.area > pi.area and pj.contains(pi.representative_point()))
            for i, pi in enumerate(sh_polys)
        ]
        for i, pi in enumerate(sh_polys):
            if depths[i] % 2 != 0:
                continue
            rings = [np.asarray(pi.exterior.coords)]
            for j, pj in enumerate(sh_polys):
                if depths[j] == depths[i] + 1 and pi.contains(pj.representative_point()):
                    rings.append(np.asarray(pj.exterior.coords))
            verts, codes = [], []
            for r_idx, r in enumerate(rings):
                area = 0.5 * np.sum(r[:-1, 0] * r[1:, 1] - r[1:, 0] * r[:-1, 1])
                if (r_idx == 0 and area < 0) or (r_idx > 0 and area > 0):
                    r = r[::-1]
                verts.extend(r)
                codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(r) - 2) + [MplPath.CLOSEPOLY])
            ax.add_patch(PathPatch(MplPath(np.asarray(verts), codes), facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, alpha=alpha))

    def plot_mesh_panel(ax, mesh: trimesh.Trimesh, title: str, elev: float, azim: float, color: str):
        ax.set_facecolor("#f5f4f0")
        ax.plot_trisurf(
            mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2],
            triangles=mesh.faces, color=color, linewidth=0, antialiased=False, shade=True,
        )
        b = mesh.bounds
        max_span = max(b[1] - b[0]) * 0.55
        c = 0.5 * (b[0] + b[1])
        ax.set_xlim(c[0] - max_span, c[0] + max_span)
        ax.set_ylim(c[1] - max_span, c[1] + max_span)
        ax.set_zlim(c[2] - max_span, c[2] + max_span)
        ax.set_box_aspect([1, 1, 1])
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=11, fontweight="bold", color="#1f242b", pad=6)
        ax.set_xlabel("X (mm)", fontsize=8)
        ax.set_ylabel("Y (mm)", fontsize=8)
        ax.set_zlabel("Z (mm)", fontsize=8)
        ax.tick_params(labelsize=7)

    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    plot_mesh_panel(ax1, meshes["svt_wrc_manifold_1piece_full"], "1-Piece Reference WRC Assembly (Dual Chamber)", 25, -55, "#4a5460")

    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    m_l = meshes["svt_wrc_manifold_split_left_cyl1_2"].copy()
    m_r = meshes["svt_wrc_manifold_split_right_cyl3_4_tb"].copy()
    m_l.apply_translation([-26.0, 0.0, 0.0])
    m_r.apply_translation([26.0, 0.0, 0.0])
    plot_mesh_panel(ax2, trimesh.util.concatenate([m_l, m_r]), "2-Piece Split Assembly (256x256x256 CC2 Bed Fit)", 25, -55, "#2b618a")

    # Panel 3: Transverse YZ section at Cyl 3 (X = +46 mm)
    _z_sec_top, z_br_mid, z_prim_bot = _bridge_z_bounds(params)
    z_sec_c = float(params["secondary_plenum"]["center_z_mm"])
    z_prim_c = primary_center_z(46.0, params, is_inner=True)
    y_prim_c = float(params["primary_plenum"]["center_y_mm"])
    y_sec_c = float(params["secondary_plenum"]["center_y_mm"])
    z_min_p = z_sec_c - 0.5 * float(params["secondary_plenum"]["inner_height_z_mm"]) - 14.0
    z_max_p = z_prim_bot + float(params["primary_plenum"]["base_inner_height_z_mm"]) + 20.0

    ax3 = fig.add_subplot(2, 2, 3)
    ax3.set_facecolor("#ffffff")
    full_solid = solids["svt_wrc_manifold_1piece_full"]
    sec_yz = full_solid.rotate([0.0, -90.0, 0.0]).slice(46.0)
    yz_polys = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in sec_yz.to_polygons()]
    add_section_patches(ax3, yz_polys, facecolor="#4c5c6b", edgecolor="#1b2026", lw=0.9)
    ax3.axhline(z_br_mid, color="#c04b2b", lw=0.9, ls="--", label="Divider Bridge / Venturi Slot")
    ax3.axhline(z_sec_c, color="#888888", lw=0.6, ls=":")
    ax3.set_aspect("equal")
    ax3.set_xlim(-160, 82)
    ax3.set_ylim(z_min_p, z_max_p)
    ax3.grid(True, linestyle=":", alpha=0.45)
    ax3.text(y_prim_c, z_prim_c, "Primary Diffuser\nChamber", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#b03a2e")
    ax3.text(y_sec_c, z_sec_c, "Secondary\nChamber", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1b4f72")
    ax3.set_title("Section at Cyl 3 (X = +46 mm): Twin Chambers, Slot & Beaded Spigot", fontsize=10.5, fontweight="bold")
    ax3.set_xlabel("Y: Spigot (-Y) to Firewall (+Y) [mm]")
    ax3.set_ylabel("Z: Height [mm]")

    # Panel 4: Longitudinal XZ section along transfer slot centerline
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor("#ffffff")
    y_slot_c = float(params["transfer_slot"]["center_y_mm"])
    sec_xz = full_solid.rotate([90.0, 0.0, 0.0]).slice(y_slot_c)
    xz_polys = [np.column_stack([np.asarray(p)[:, 0], -np.asarray(p)[:, 1]]) for p in sec_xz.to_polygons()]
    add_section_patches(ax4, xz_polys, facecolor="#2f5d80", edgecolor="#182a38", lw=0.9, alpha=0.9)
    for idx, xc in enumerate(params["runners"]["center_x_mm"], start=1):
        ax4.axvline(xc, color="#777777", lw=0.6, ls=":")
        ax4.text(xc, z_min_p + 2.0, f"Cyl {idx}", ha="center", va="top", fontsize=8, fontweight="bold", color="#222")
    ax4.axvline(0.0, color="#0d6e3f", lw=1.3, ls="-.")
    ax4.text(0.0, z_max_p - 6.0, "Split X=0", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#0d6e3f", bbox=dict(facecolor="#ffffff", edgecolor="none", pad=1.2, alpha=0.88))
    ax4.set_aspect("equal")
    ax4.set_xlim(-200, 248)
    ax4.set_ylim(z_min_p - 8.0, z_max_p + 8.0)
    ax4.grid(True, linestyle=":", alpha=0.45)
    ax4.set_title(f"Longitudinal Section (Y = {y_slot_c:+.0f} mm): Sloped Primary Diffuser & Scoops", fontsize=10.2, fontweight="bold")
    ax4.set_xlabel("X: Cyl 1 (-X) to Straight 65 mm TB (+X) [mm]")
    ax4.set_ylabel("Z: Height [mm]")

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_1to1_svg(solids: dict[str, md.Manifold], params: dict, out_path: Path):
    """Generate a true 1:1 mm-scale SVG template for physical caliper comparison."""
    spigot_sec = solids["svt_wrc_runner_boot_fit_gauge"].slice(24.0).to_polygons()
    split_sec = solids["svt_wrc_manifold_split_left_cyl1_2"].rotate([0.0, -90.0, 0.0]).slice(-1.0).to_polygons()
    tb_sec = solids["svt_wrc_tb_flange_fit_gauge"].slice(2.0).to_polygons()
    iacv_sec = solids["svt_wrc_iacv_flange_fit_gauge"].slice(2.0).to_polygons()

    width_mm, height_mm = 560.0, 235.0
    sp_cfg = params["runners"]["spigot"]
    sp_out_w = float(sp_cfg["outer_width_mm"])
    sp_in_w = sp_out_w - 2.0 * float(sp_cfg["wall_thickness_mm"])
    spigot_label = f'Silicone Boot Spigot\n(Ø{sp_out_w:.1f} outer / Ø{sp_in_w:.1f} inner — 2" Boot)'
    centers = [
        (spigot_label, spigot_sec, (55.0, 118.0), lambda p: (p[0], -p[1])),
        ("WRC Twin-Chamber Split Flange\n(8x M6 + 2x 6mm Dowel + Continuous O-Ring)", split_sec, (215.0, 132.0), lambda p: (p[1], p[0])),
        ("65mm Throttle Body Flange\n(70x70 mm 4-Bolt Pattern)", tb_sec, (380.0, 118.0), lambda p: (p[0], -p[1])),
        ("2-Bolt Ford IACV Flange\n(46mm Bolts / Dual 13mm Ports)", iacv_sec, (500.0, 118.0), lambda p: (p[0], -p[1])),
    ]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width_mm * 0.5:.1f}" y="12" text-anchor="middle" font-family="sans-serif" font-size="6" font-weight="bold" fill="#111">2004 Focus SVT Dual-Chamber WRC Manifold — 1:1 Interface Templates (mm)</text>',
    ]
    for label, polys, (cx, cy), map_fn in centers:
        for poly in polys:
            pts = " ".join(f"{cx + map_fn(p)[0]:.3f},{cy + map_fn(p)[1]:.3f}" for p in poly)
            lines.append(f'<polygon points="{pts}" fill="none" stroke="#1f4e79" stroke-width="0.35"/>')
        for idx, line in enumerate(label.split("\n")):
            lines.append(f'<text x="{cx}" y="{218 + idx * 5}" text-anchor="middle" font-family="sans-serif" font-size="4.2" fill="#333">{line}</text>')
    lines.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    STL_DIR.mkdir(parents=True, exist_ok=True)
    FITMENT_DIR.mkdir(parents=True, exist_ok=True)

    solids = assemble_all(params)
    meshes: dict[str, trimesh.Trimesh] = {}
    manifest_parts: dict[str, dict] = {}

    cc2 = params["printers"]["centauri_carbon_2"]
    e3 = params["printers"]["ender_3_s1_pro"]

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

    prim_l = round(float(manifold_to_trimesh(solids["_prim_inner"]).volume) / 1_000_000.0, 3)
    sec_l = round(float(manifold_to_trimesh(solids["_sec_inner"]).volume) / 1_000_000.0, 3)
    tot_l = round(float(manifold_to_trimesh(solids["_plenum_inner_total"]).volume) / 1_000_000.0, 3)
    slot_l = round(max(tot_l - prim_l - sec_l, 0.0), 3)

    manifest = {
        "vehicle": params["metadata"]["vehicle"],
        "architecture": params["metadata"]["architecture"],
        "primary_chamber_volume_liters": prim_l,
        "secondary_chamber_volume_liters": sec_l,
        "transfer_slot_volume_liters": slot_l,
        "plenum_internal_volume_liters": tot_l,
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
        "iacv_supply_wall_thickness_mm": round(float(solids["_iacv_wall_thickness_mm"]), 2),
        "split_oring_centerline_mm": solids["_oring_centerline_mm"],
        "parts": manifest_parts,
    }
    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    render_overview_png(meshes, solids, params, FITMENT_DIR / "01_wrc_manifold_overview.png")
    render_1to1_svg(solids, params, FITMENT_DIR / "02_wrc_interfaces_1to1_template.svg")

    print(
        f"Generated {len(meshes)} watertight WRC STLs. "
        f"Plenum volume: {tot_l:.3f} L (Primary={prim_l:.3f} L, Secondary={sec_l:.3f} L, Slot={slot_l:.3f} L)"
    )
    print(
        f"  IACV supply bore separation wall = {manifest['iacv_supply_wall_thickness_mm']} mm | "
        f"Split O-ring loop = {manifest['split_oring_centerline_mm']} mm"
    )
    for pname, info in manifest_parts.items():
        print(
            f"  {pname}: {info['extents_mm']} mm | "
            f"vol={info['solid_volume_cm3']} cm3 | "
            f"CC2={info['fits_centauri_carbon_2_256']} | E3={info['fits_ender_3_s1_pro_220']}"
        )


if __name__ == "__main__":
    main()
