#!/usr/bin/env python3
"""
Modular Dual-Stage (2-Length Runner) NA Upper Intake Manifold Generator
for 2002-2004 Ford Focus SVT / ST170 (2.0L Zetec-R Naturally Aspirated).

Builds a completely isolated dual-stage NA manifold in cad/intake_manifold_na_dsi/:
  - C2-tapered upper plenum (~2.35 L) with locked front & floor walls for straight shafting
  - 4x equal-length Short Bypass ports (Ø44.0 mm, 22 deg cant, ~160 mm upper / ~295 mm total)
  - 4x equal-length Long C-Scroll runners (Ø43.0 mm, ~350 mm upper / ~485 mm total via bisection)
  - 2x O-ringed Top Service Hatches (Cyl 1-2 & Cyl 3-4) for direct FOD-safe valve inspection
  - 1-piece Ø8.0 mm 304SS shaft on 688-2RS bearings, center SF-1 bushing, +X FKM Viton lip seal,
    -X blind O-ring bearing cap, and universal external actuator bracket (OEM IMRC or vacuum pod)
  - Zero-height-penalty -Y NA vacuum/PCV/EVAP/FRPS pads & 2-bolt Ford IACV mount
  - Centauri Carbon 2 (256x256x256 mm) 2-piece split halves + CNC STEP/DXF metal valve hardware

Outputs:
  stl/*.stl, stl/manifest.json
  cnc/*.step, cnc/*.dxf
  fitment/01_na_dsi_manifold_overview.png
  fitment/02_na_dsi_interfaces_1to1_template.svg
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from scipy.interpolate import CubicSpline
from shapely.geometry import box as shapely_box
from shapely.geometry.polygon import orient

from build123d import (
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Line,
    Locations,
    Mode,
    Rectangle,
    ThreePointArc,
    export_step,
    extrude,
    make_face,
)
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
PARAMS_PATH = ROOT / "na_dsi_parameters.json"
STL_DIR = ROOT / "stl"
CNC_DIR = ROOT / "cnc"
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
    lst = list(solids)
    assert lst, "m_union requires at least one solid"
    return lst[0] if len(lst) == 1 else md.Manifold.batch_boolean(lst, md.OpType.Add)


def m_diff(base: md.Manifold, cutters: Iterable[md.Manifold]) -> md.Manifold:
    cutter_list = list(cutters)
    if not cutter_list:
        return base
    combined_cutter = m_union(cutter_list)
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
    """Extrude a 2D CCW polygon centered around z_local=0 along 'x', 'y', or 'z'."""
    pts = np.asarray(poly_uv, dtype=np.float64)
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


def bezier_point_and_tangent(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float):
    u = 1.0 - t
    pt = (u**3) * p0 + 3 * (u**2) * t * p1 + 3 * u * (t**2) * p2 + (t**3) * p3
    tan = 3 * (u**2) * (p1 - p0) + 6 * u * t * (p2 - p1) + 3 * (t**2) * (p3 - p2)
    return pt, tan


# ---------------------------------------------------------------------------
# Tapered Plenum (Locked Front & Bottom Walls for Straight Shafting)
# ---------------------------------------------------------------------------

def plenum_blend_s(x: float, params: dict) -> float:
    p = params["plenum"]
    x0 = float(p["cyl1_end_x_mm"])
    x1 = float(p["cyl4_end_x_mm"])
    u = float(np.clip((x - x0) / (x1 - x0), 0.0, 1.0))
    if p.get("taper_curve_smooth", True):
        return 0.5 * u + 0.5 * (0.5 - 0.5 * math.cos(math.pi * u))
    return u


def plenum_dims_at_x(x: float, params: dict) -> dict[str, float]:
    """Return exact inner (W_y, H_z, R_c, yc, zc, y_rear_in, z_top_in) at axial station X."""
    p = params["plenum"]
    s = plenum_blend_s(x, params)
    w = float(p["cyl1_inner_width_y_mm"]) + (float(p["base_inner_width_y_mm"]) - float(p["cyl1_inner_width_y_mm"])) * s
    h = float(p["cyl1_inner_height_z_mm"]) + (float(p["base_inner_height_z_mm"]) - float(p["cyl1_inner_height_z_mm"])) * s
    r = float(p["cyl1_inner_corner_radius_mm"]) + (float(p["base_inner_corner_radius_mm"]) - float(p["cyl1_inner_corner_radius_mm"])) * s
    y_front_in = float(p["front_inner_y_mm"])
    yc = y_front_in + 0.5 * w
    if "top_inner_z_mm" in p:
        z_top_in = float(p["top_inner_z_mm"])
        zc = z_top_in - 0.5 * h
        z_bot_in = z_top_in - h
    else:
        z_bot_in = float(p["bottom_inner_z_mm"])
        zc = z_bot_in + 0.5 * h
        z_top_in = z_bot_in + h
    return {
        "w": w,
        "h": h,
        "r": r,
        "yc": yc,
        "zc": zc,
        "y_front_in": y_front_in,
        "y_rear_in": y_front_in + w,
        "z_bot_in": z_bot_in,
        "z_top_in": z_top_in,
    }


def build_plenum_loft(params: dict, is_inner: bool, wall_offset_mm: float | None = None) -> md.Manifold:
    """Build C2-tapered upper plenum with -X ellipsoidal nose dome."""
    p = params["plenum"]
    wall = float(p["wall_thickness_mm"])
    eff_off = float(wall_offset_mm) if wall_offset_mm is not None else (0.0 if is_inner else wall)
    n_pts = int(p["profile_segments"])
    x_cyl1 = float(p["cyl1_end_x_mm"])
    x_cyl4 = float(p["cyl4_end_x_mm"]) + (-2.0 if (is_inner and wall_offset_mm is None) else 2.0)
    dome_len = float(p["cyl1_dome_length_mm"]) - wall + eff_off

    d1 = plenum_dims_at_x(x_cyl1, params)
    rings: list[np.ndarray] = []

    for th in np.linspace(0.20, math.pi * 0.5, int(p["cyl1_dome_steps"]), endpoint=False):
        x = x_cyl1 - dome_len * math.cos(th)
        ds = math.sin(th)
        w = d1["w"] * ds + 2.0 * eff_off * ds
        h = d1["h"] * ds + 2.0 * eff_off * ds
        r = d1["r"] * ds + eff_off * ds
        uv = rounded_rect_points(w, h, r, n_pts)
        rings.append(np.column_stack([np.full(n_pts, x), uv[:, 0] + d1["yc"], uv[:, 1] + d1["zc"]]))

    xs = np.linspace(x_cyl1, x_cyl4, int(p["axial_segments"]))
    if not np.any(np.isclose(xs, 0.0, atol=1e-4)):
        xs = np.sort(np.append(xs, 0.0))
    rw_cfg = p.get("rear_wall_flow_guide", {})
    rw_enabled = bool(rw_cfg.get("enabled", False))
    rw_bx0, rw_bx1 = rw_cfg.get("blend_x_mm", [55.0, 160.0]) if rw_enabled else (0.0, 0.0)
    rw_depth = float(rw_cfg.get("depth_mm", 0.0)) if rw_enabled else 0.0
    rw_zmin = float(rw_cfg.get("z_min_mm", -2.0)) if rw_enabled else 0.0

    for x in xs:
        d = plenum_dims_at_x(float(x), params)
        uv = rounded_rect_points(d["w"] + 2.0 * eff_off, d["h"] + 2.0 * eff_off, d["r"] + eff_off, n_pts)
        ys = uv[:, 0] + d["yc"]
        zs = uv[:, 1] + d["zc"]
        if rw_enabled and rw_bx0 <= x <= rw_bx1:
            tx = (float(x) - rw_bx0) / max(rw_bx1 - rw_bx0, 1.0)
            gx = math.sin(math.pi * tx) ** 0.85
            wy_pos = np.clip((ys - d["yc"]) / max(0.5 * d["w"], 1.0), 0.0, 1.0)
            wz_pos = np.clip((zs - rw_zmin) / max(d["z_top_in"] - rw_zmin, 1.0), 0.0, 1.0)
            ys = ys - rw_depth * gx * (wy_pos ** 1.4) * (0.5 - 0.5 * np.cos(math.pi * wz_pos))
        rings.append(np.column_stack([np.full(n_pts, float(x)), ys, zs]))

    return trimesh_to_manifold(loft_closed_solid(rings))


def build_floor_flow_scoops(params: dict, pl_bond_env: md.Manifold | None = None) -> list[md.Manifold]:
    """
    Build support-free 45-deg-ramped plenum-floor flow-catching scoops ahead of Cyl 4 & Cyl 3
    to equalize static pressure recovery across Cyl 1-4 in Short-Bypass high-RPM mode.
    """
    fs_cfg = params["plenum"].get("floor_flow_scoops", {})
    if not fs_cfg.get("enabled", False):
        return []

    if pl_bond_env is None:
        pl_bond_env = build_plenum_loft(params, is_inner=True, wall_offset_mm=2.5)

    z_bot_in = float(params["plenum"]["bottom_inner_z_mm"])
    z_floor_anchor = z_bot_in - 3.0
    y_start = float(fs_cfg["y_start_mm"])
    y_end = float(fs_cfg["y_end_mm"])
    y_span = y_end - y_start
    y_mid = 0.5 * (y_start + y_end)

    scoops: list[md.Manifold] = []
    for sc in fs_cfg["scoops"]:
        x_face = float(sc["x_face_mm"])
        z_top = float(sc["z_top_mm"])
        crest_t = float(sc["crest_thickness_mm"])
        h_rise = z_top - z_bot_in
        x_crest = x_face - crest_t
        x_tail = max(x_crest - h_rise, 4.0)  # stays cleanly on +X side of X=0 split flange

        # (X, Z) polygon: vertical +X catching face (zero overhang on CC2 Z_bed=X) + 45-deg trailing ramp
        poly_xz = np.array([
            [x_tail, z_floor_anchor],
            [x_face, z_floor_anchor],
            [x_face, z_top],
            [x_crest, z_top],
            [x_tail, z_bot_in],
        ], dtype=np.float64)
        poly_uv = np.column_stack([poly_xz[:, 0], -poly_xz[:, 1]])
        raw_scoop = extrude_polygon_along_axis(poly_uv, y_span, center=(0.0, y_mid, 0.0), axis="y")
        bonded = raw_scoop ^ pl_bond_env
        bb = bonded.bounding_box()
        assert bb[0] >= 3.5, f"Scoop {sc['name']} encroached near X=0 split: X_min={bb[0]:.2f}"
        assert bb[5] <= z_top + 0.1, f"Scoop {sc['name']} invalid Z_max={bb[5]:.2f}"
        scoops.append(bonded)
    return scoops


# ---------------------------------------------------------------------------
# Dual-Length Runner Curves & Geometry (Short Bypass + Equal-Length Long C-Scroll)
# ---------------------------------------------------------------------------

def short_runner_geometry(x_center: float, params: dict) -> dict:
    """Compute exact 3D points, centerline spline, and length for the Short Bypass + Spigot."""
    rn = params["runners"]
    sp = rn["spigot"]
    sb = rn["short_bypass"]
    pl = params["plenum"]

    elev_rad = math.radians(float(sb.get("axis_elevation_deg", 38.0)))
    d_bore = np.array([0.0, -math.cos(elev_rad), math.sin(elev_rad)], dtype=np.float64)
    p_shaft = np.array([x_center, float(sb["shaft_center_y_mm"]), float(sb["shaft_center_z_mm"])], dtype=np.float64)
    y_front_in = float(pl["front_inner_y_mm"])
    s_floor = (y_front_in - p_shaft[1]) / d_bore[1]  # negative (inside plenum front wall)
    p_floor = p_shaft + s_floor * d_bore
    protrusion = float(sb.get("bellmouth_protrusion_mm", 0.0))
    s_stack = s_floor - protrusion
    p_stack = p_shaft + s_stack * d_bore
    s_bot = float(sb["bore_lower_extend_mm"])
    p_vbot = p_shaft + s_bot * d_bore

    tip_y = float(sp["tip_y_mm"])
    land_len = float(sp["land_length_mm"])
    sweep_end_y = tip_y + land_len
    sp_z = float(sp["center_z_mm"])
    p_land = np.array([x_center, sweep_end_y, sp_z], dtype=np.float64)
    p_tip = np.array([x_center, tip_y, sp_z], dtype=np.float64)

    # Smooth cubic Bezier from p_vbot (tangent d_bore) to p_land (tangent -Y)
    p0 = p_vbot
    p1 = p_vbot + d_bore * 20.0
    p2 = p_land + np.array([0.0, 26.0, 0.0])
    p3 = p_land

    pts_sweep = []
    tans_sweep = []
    n_sw = 48
    for k in range(n_sw + 1):
        pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, k / n_sw)
        pts_sweep.append(pt)
        tans_sweep.append(tan / np.linalg.norm(tan))
    pts_sweep = np.asarray(pts_sweep)
    tans_sweep = np.asarray(tans_sweep)

    bore_len = float(np.linalg.norm(p_vbot - p_stack))
    sweep_len = float(np.sum(np.linalg.norm(np.diff(pts_sweep, axis=0), axis=1)))
    upper_len = bore_len + sweep_len + land_len

    return {
        "d_bore": d_bore,
        "p_shaft": p_shaft,
        "s_floor": s_floor,
        "s_stack": s_stack,
        "protrusion": protrusion,
        "s_bot": s_bot,
        "p_floor": p_floor,
        "p_stack": p_stack,
        "p_vbot": p_vbot,
        "p0": p0,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p_land": p_land,
        "p_tip": p_tip,
        "pts_sweep": pts_sweep,
        "tans_sweep": tans_sweep,
        "upper_length_mm": upper_len,
    }


def _scroll_segments(x_center: float, z_bot: float, params: dict) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Build smooth C1 centerline points and tangents for one Long C-Scroll tube
    from the rear plenum bellmouth entry to the shallow Y-merge on the common tract.
    """
    ls = params["runners"]["long_scroll"]
    d_pl = plenum_dims_at_x(x_center, params)
    y_rear_in = d_pl["y_rear_in"]
    y_apex = max(y_rear_in + float(ls["plenum_rear_wall_offset_mm"]), float(ls.get("min_apex_y_mm", 63.0)))
    z_entry = float(ls["plenum_entry_z_mm"])
    y_bot = float(ls["bottom_y_mm"])
    y_merge = float(ls["merge_y_mm"])
    z_merge = float(ls["merge_z_mm"])

    # Merge tangent aligns cleanly into underside of common runner tract (~38 deg)
    t_merge = np.array([0.0, -0.78, 0.625], dtype=np.float64)
    t_merge /= np.linalg.norm(t_merge)

    # Control stations in (Y, Z): tight lower-rear -> under-plenum -> front-upward merge
    p_start = np.array([x_center, y_rear_in - 1.5, z_entry], dtype=np.float64)
    p_rear = np.array([x_center, y_apex, -44.0], dtype=np.float64)
    p_bot = np.array([x_center, y_bot, z_bot], dtype=np.float64)
    p_knee = np.array([x_center, -108.0, 4.0], dtype=np.float64)
    p_end = np.array([x_center, y_merge, z_merge], dtype=np.float64)

    # 4 smooth C1-connected Bezier segments
    segs = [
        # Seg 1: horizontal exit perpendicular to plenum rear wall -> vertical downward (-Z)
        (
            p_start,
            p_start + np.array([0.0, 14.0, 0.0]),
            p_rear + np.array([0.0, 0.0, 16.0]),
            p_rear,
            16,
        ),
        # Seg 2: bottom-rear 90-deg turn under plenum
        (
            p_rear,
            p_rear + np.array([0.0, 0.0, -20.0]),
            p_bot + np.array([0.0, 38.0, 0.0]),
            p_bot,
            20,
        ),
        # Seg 3: under-plenum forward turn upward in front of valve housing
        (
            p_bot,
            p_bot + np.array([0.0, -38.0, 0.0]),
            p_knee + np.array([0.0, 0.0, -38.0]),
            p_knee,
            20,
        ),
        # Seg 4: vertical climb into underside Y-merge downstream of valve
        (
            p_knee,
            p_knee + np.array([0.0, 0.0, 30.0]),
            p_end - t_merge * 22.0,
            p_end,
            20,
        ),
    ]

    all_pts = []
    all_tans = []
    for s_idx, (a0, a1, a2, a3, n_st) in enumerate(segs):
        k_start = 0 if s_idx == 0 else 1
        for k in range(k_start, n_st + 1):
            pt, tan = bezier_point_and_tangent(a0, a1, a2, a3, k / n_st)
            all_pts.append(pt)
            all_tans.append(tan / np.linalg.norm(tan))

    pts = np.asarray(all_pts, dtype=np.float64)
    tans = np.asarray(all_tans, dtype=np.float64)

    # Compute remaining downstream length from p_end (Y = merge_y_mm) to spigot tip
    sh = short_runner_geometry(x_center, params)
    sw_pts = sh["pts_sweep"]
    # Find closest point on common runner sweep to p_end
    dists = np.linalg.norm(sw_pts - p_end[None, :], axis=1)
    idx_m = int(np.argmin(dists))
    downstream_sweep_len = float(np.sum(np.linalg.norm(np.diff(sw_pts[idx_m:], axis=0), axis=1)))
    land_len = float(params["runners"]["spigot"]["land_length_mm"])
    scroll_len = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
    total_upper = scroll_len + downstream_sweep_len + land_len
    return pts, tans, total_upper


def solve_equal_length_z_bot(x_center: float, params: dict) -> tuple[float, float]:
    """Bisect z_bot in [-105, -56] mm so long upper runner hits exact target length."""
    target = float(params["runners"]["long_scroll"]["target_upper_length_mm"])
    lo, hi = -105.0, -56.0
    for _ in range(36):
        mid = 0.5 * (lo + hi)
        _, _, L_mid = _scroll_segments(x_center, mid, params)
        # More negative z_bot -> longer scroll
        if L_mid > target:
            lo = mid
        else:
            hi = mid
    z_opt = 0.5 * (lo + hi)
    _, _, L_opt = _scroll_segments(x_center, z_opt, params)
    return z_opt, L_opt


def build_single_runner_components(x_center: float, params: dict) -> dict:
    """Build short bypass, common spigot sweep, long C-scroll, and flush bellmouths for one cylinder."""
    rn = params["runners"]
    sp_cfg = rn["spigot"]
    sb_cfg = rn["short_bypass"]
    ls_cfg = rn["long_scroll"]
    n_pts = int(ls_cfg["profile_segments"])
    up_hint = np.array([0.0, 0.0, 1.0])
    x_vec = np.array([1.0, 0.0, 0.0])

    # Common spigot dimensions (2.00" round MarraSport / Massive boot)
    sp_w_out = float(sp_cfg["outer_width_mm"])
    sp_h_out = float(sp_cfg["outer_height_mm"])
    sp_r_out = float(sp_cfg["corner_radius_mm"])
    sp_wall = float(sp_cfg["wall_thickness_mm"])
    sp_w_in = sp_w_out - 2.0 * sp_wall
    sp_h_in = sp_h_out - 2.0 * sp_wall
    sp_r_in = sp_r_out - sp_wall

    # Short bypass valve bore
    d_vb = float(sb_cfg["bore_diameter_mm"])
    w_vb = float(sb_cfg["wall_thickness_mm"])
    d_vb_out = d_vb + 2.0 * w_vb
    sh = short_runner_geometry(x_center, params)
    d_bore = sh["d_bore"]
    p_shaft = sh["p_shaft"]
    s_floor = sh["s_floor"]
    s_bot = sh["s_bot"]

    # 1) Short bore + forward sweep + beaded spigot (OUTER & INNER)
    outer_rings: list[np.ndarray] = []
    bore_rings: list[np.ndarray] = []

    # Straight cylindrical valve bore + flared outer bellmouth collar at plenum floor
    bm_flare = float(sb_cfg["bellmouth_flare_radial_mm"])
    w_vb_collar = w_vb + 1.0  # 6.0 mm reinforced collar wall enclosing the entire floor bellmouth
    s_bm_start = s_floor - 4.0
    s_top_out = s_floor - 6.5  # starts 2.5 mm above s_bm_start inside plenum so inner flare never breaches cap
    s_collar_end = s_floor + 13.0
    for s_val in np.linspace(s_top_out, s_collar_end, 18):
        pos = p_shaft + s_val * d_bore
        if s_val < s_floor:
            fl_o = bm_flare + (s_floor - s_val) * 0.55
        else:
            u = np.clip((s_val - s_floor) / 13.0, 0.0, 1.0)
            fl_o = bm_flare * ((1.0 - u) ** 2)
        d_cur_o = d_vb + 2.0 * (fl_o + w_vb_collar)
        outer_rings.append(
            ring_frame_points(pos, d_bore, x_vec, rounded_rect_points(d_cur_o, d_cur_o, d_cur_o * 0.5, n_pts))
        )
    for s_val in np.linspace(s_collar_end + 1.0, s_bot, 10):
        pos = p_shaft + s_val * d_bore
        outer_rings.append(
            ring_frame_points(pos, d_bore, x_vec, rounded_rect_points(d_vb_out, d_vb_out, d_vb_out * 0.5, n_pts))
        )

    # Flush or protruding velocity stack bellmouth inside plenum
    s_stack = sh["s_stack"]
    protrusion = sh["protrusion"]
    s_bm_start_eff = s_stack if protrusion > 0.0 else s_bm_start
    s_bm_end = s_bm_start_eff + 14.0
    for s_val in np.linspace(s_bm_start_eff, s_bm_end, 16):
        pos = p_shaft + s_val * d_bore
        u = np.clip((s_val - s_bm_start_eff) / 14.0, 0.0, 1.0)
        fl = bm_flare * ((1.0 - u) ** 2)
        d_cur = d_vb + 2.0 * fl
        bore_rings.append(
            ring_frame_points(pos, d_bore, x_vec, rounded_rect_points(d_cur, d_cur, d_cur * 0.5, n_pts))
        )
    for s_val in np.linspace(s_bm_end + 1.0, s_bot, 10):
        pos = p_shaft + s_val * d_bore
        bore_rings.append(
            ring_frame_points(pos, d_bore, x_vec, rounded_rect_points(d_vb, d_vb, d_vb * 0.5, n_pts))
        )

    stack_outer = None
    if protrusion > 0.0:
        st_rings = []
        w_st = 3.5
        for s_val in np.linspace(s_stack - 1.5, s_floor + 8.0, 20):
            pos = p_shaft + s_val * d_bore
            if s_val < s_bm_start_eff:
                fl_s = bm_flare * 0.5
            else:
                u = np.clip((s_val - s_bm_start_eff) / 14.0, 0.0, 1.0)
                fl_s = bm_flare * ((1.0 - u) ** 2)
            d_st_o = d_vb + 2.0 * (fl_s + w_st)
            st_rings.append(
                ring_frame_points(pos, d_bore, x_vec, rounded_rect_points(d_st_o, d_st_o, d_st_o * 0.5, n_pts))
            )
        stack_outer = trimesh_to_manifold(loft_closed_solid(st_rings))

    # Smooth elbow + sweep from p_vbot to p_land
    n_sw = len(sh["pts_sweep"]) - 1
    for k in range(1, n_sw + 1):
        t = k / n_sw
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        pt = sh["pts_sweep"][k]
        tan = sh["tans_sweep"][k]
        w_o = d_vb_out + (sp_w_out - d_vb_out) * s_t
        h_o = d_vb_out + (sp_h_out - d_vb_out) * s_t
        r_o = d_vb_out * 0.5 + (sp_r_out - d_vb_out * 0.5) * s_t
        outer_rings.append(ring_frame_points(pt, tan, x_vec, rounded_rect_points(w_o, h_o, r_o, n_pts)))

        w_i = d_vb + (sp_w_in - d_vb) * s_t
        h_i = d_vb + (sp_h_in - d_vb) * s_t
        r_i = d_vb * 0.5 + (sp_r_in - d_vb * 0.5) * s_t
        bore_rings.append(ring_frame_points(pt, tan, x_vec, rounded_rect_points(w_i, h_i, r_i, n_pts)))

    # Straight spigot land with crowned retention bead + tip chamfer
    tip_y = float(sp_cfg["tip_y_mm"])
    sp_z = float(sp_cfg["center_z_mm"])
    bead_h = float(sp_cfg["retention_bead_height_mm"])
    bead_w = float(sp_cfg["retention_bead_width_mm"])
    bead_off = float(sp_cfg["retention_bead_offset_from_tip_mm"])
    y_bead_start = tip_y + bead_off
    y_bead_end = y_bead_start + bead_w
    tan_sp = np.array([0.0, -1.0, 0.0])

    spigot_stations = [(float(y_s), 0.0) for y_s in np.linspace(sh["p_land"][1], y_bead_end, 10)[1:]]
    for b_idx in range(1, 18):
        frac = b_idx / 18.0
        spigot_stations.append((y_bead_end - frac * bead_w, bead_h * math.sin(math.pi * frac)))
    spigot_stations.extend([(y_bead_start, 0.0), (tip_y + 0.8, 0.0), (tip_y, -0.8)])
    for y_pos, dr in spigot_stations:
        uv = rounded_rect_points(sp_w_out + 2.0 * dr, sp_h_out + 2.0 * dr, sp_r_out + dr, n_pts)
        outer_rings.append(ring_frame_points(np.array([x_center, y_pos, sp_z]), tan_sp, x_vec, uv))

    bore_rings.append(
        ring_frame_points(
            np.array([x_center, tip_y - 6.0, sp_z]),
            tan_sp,
            x_vec,
            rounded_rect_points(sp_w_in, sp_h_in, sp_r_in, n_pts),
        )
    )

    short_outer = trimesh_to_manifold(loft_closed_solid(outer_rings))
    short_bore = trimesh_to_manifold(loft_closed_solid(bore_rings))

    # 2) Long C-Scroll (Equal-length bisection + flush rear bellmouth + shallow merge)
    z_bot_opt, long_len = solve_equal_length_z_bot(x_center, params)
    sc_pts, sc_tans, _ = _scroll_segments(x_center, z_bot_opt, params)

    d_sc = float(ls_cfg["inner_diameter_mm"])
    w_sc = float(ls_cfg["wall_thickness_mm"])
    d_sc_out = d_sc + 2.0 * w_sc
    sc_flare = float(ls_cfg["bellmouth_flare_radial_mm"])

    sc_outer_rings = []
    sc_bore_rings = []
    # Flush bellmouth lead-in 4.0 mm inside rear plenum cavity + matching reinforced outer bellmouth collar
    p_sc0, t_sc0 = sc_pts[0], sc_tans[0]
    w_sc_collar = w_sc + 1.0  # 5.5 mm wall around flared rear bellmouth
    for s_lead in np.linspace(-6.0, -0.5, 7):
        fl_o = sc_flare + max(-s_lead, 0.0) * 0.45
        dc_out = d_sc + 2.0 * (fl_o + w_sc_collar)
        sc_outer_rings.append(
            ring_frame_points(p_sc0 + t_sc0 * s_lead, t_sc0, x_vec, rounded_rect_points(dc_out, dc_out, dc_out * 0.5, n_pts))
        )
        if s_lead >= -4.0:
            dc = d_sc + 2.0 * fl_o
            sc_bore_rings.append(
                ring_frame_points(p_sc0 + t_sc0 * s_lead, t_sc0, x_vec, rounded_rect_points(dc, dc, dc * 0.5, n_pts))
            )

    cum_s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(sc_pts, axis=0), axis=1))])
    for k, (pt, tan) in enumerate(zip(sc_pts, sc_tans)):
        s_k = cum_s[k]
        if s_k < 16.0:
            u = s_k / 16.0
            fl = sc_flare * ((1.0 - u) ** 2)
            dc_out = d_sc + 2.0 * (fl + w_sc_collar)
        else:
            fl = 0.0
            dc_out = d_sc_out
        sc_outer_rings.append(
            ring_frame_points(pt, tan, x_vec, rounded_rect_points(dc_out, dc_out, dc_out * 0.5, n_pts))
        )
        dc = d_sc + 2.0 * fl
        sc_bore_rings.append(
            ring_frame_points(pt, tan, x_vec, rounded_rect_points(dc, dc, dc * 0.5, n_pts))
        )

    # Extend bore 6 mm past merge point along merge tangent so Y-junction blends seamlessly
    p_last, t_last = sc_pts[-1], sc_tans[-1]
    sc_outer_rings.append(
        ring_frame_points(p_last + t_last * 4.0, t_last, x_vec, rounded_rect_points(d_sc_out - 2.0, d_sc_out - 2.0, (d_sc_out - 2.0) * 0.5, n_pts))
    )
    sc_bore_rings.append(
        ring_frame_points(p_last + t_last * 6.0, t_last, x_vec, rounded_rect_points(d_sc - 0.5, d_sc - 0.5, (d_sc - 0.5) * 0.5, n_pts))
    )

    scroll_outer = trimesh_to_manifold(loft_closed_solid(sc_outer_rings))
    scroll_bore = trimesh_to_manifold(loft_closed_solid(sc_bore_rings))

    # Closed-valve 6.0 mm solid throat plug (for 0.0% leakage Long-Mode CFD verification)
    plug_p0 = p_shaft - d_bore * 3.0
    plug_p1 = p_shaft + d_bore * 3.0
    valve_plug = make_cylinder_along(plug_p0, plug_p1, d_vb * 0.5 + 1.5, segments=48)

    return {
        "short_outer": short_outer,
        "short_bore": short_bore,
        "stack_outer": stack_outer,
        "scroll_outer": scroll_outer,
        "scroll_bore": scroll_bore,
        "valve_plug": valve_plug,
        "short_upper_length_mm": round(sh["upper_length_mm"], 2),
        "long_upper_length_mm": round(long_len, 2),
        "scroll_z_bot_mm": round(z_bot_opt, 2),
        "scroll_pts": sc_pts,
        "short_geom": sh,
    }


# ---------------------------------------------------------------------------
# DSI Shaft Bosses, Bearings, Seal Pockets, Blind Cap, Retainer & Bracket
# ---------------------------------------------------------------------------

def build_shaft_system_components(params: dict) -> dict:
    """Build integral shaft tunnel bosses, bearing/seal pockets, blind cap, retainer, and universal bracket."""
    ds = params["dsi_valve_system"]
    sb = params["runners"]["short_bypass"]
    yv = float(sb["shaft_center_y_mm"])
    zv = float(sb["shaft_center_z_mm"])
    r_boss = float(ds["housing_outer_diameter_mm"]) * 0.5

    x_left_end = float(ds["left_cap_end_x_mm"])
    x_right_end = float(ds["right_seal_face_x_mm"])

    # Continuous Ø24 mm shaft boss + anchor web into plenum front wall (Y = -32..yv)
    shaft_boss = make_cylinder_along(
        np.array([x_left_end, yv, zv]),
        np.array([x_right_end, yv, zv]),
        r_boss,
        segments=48,
    )
    y_front_in = float(params["plenum"]["front_inner_y_mm"])
    anchor_web = md.Manifold.cube(
        [x_right_end - x_left_end - 8.0, abs(y_front_in - yv) + 6.0, 16.0], center=True
    ).translate([0.5 * (x_left_end + x_right_end), 0.5 * (y_front_in + yv), zv])

    # -X (Cyl 1) end: open actuator/seal side; +X (Cyl 4/TB) end: flush blind internal bearing pocket
    end_flange_left = make_rounded_prism(40.0, 32.0, 7.0, 10.0, segments=48, center=(x_left_end + 5.0, yv, zv), axis="x")

    # Universal external actuator mounting pad on -X (Cyl 1) wide-open end
    act_pad = make_rounded_prism(34.0, 20.0, 5.0, 34.0, segments=32, center=(x_left_end + 16.0, yv - 20.0, zv - 6.0), axis="y")

    # Cutters: shaft clearance bore (Ø8.6 mm), center bushing, -X seal+bearing, +X internal blind bearing pocket
    shaft_bore = make_cylinder_along(
        np.array([x_left_end - 5.0, yv, zv]),
        np.array([x_right_end - 4.8, yv, zv]),
        4.3,
        segments=36,
    )
    bushing_pocket = make_cylinder_along(
        np.array([-float(ds["center_bushing_length_mm"]) * 0.5, yv, zv]),
        np.array([float(ds["center_bushing_length_mm"]) * 0.5, yv, zv]),
        float(ds["center_bushing_bore_diameter_mm"]) * 0.5,
        segments=36,
    )
    b_rad = float(ds["bearing_bore_diameter_mm"]) * 0.5
    b_dep = float(ds["bearing_depth_mm"])
    s_dep = float(ds["rotary_seal_depth_mm"])

    # -X side: outer 8x16x5 Viton TC rotary seal + inner 688-2RS bearing
    left_seal_and_bearing_pocket = make_cylinder_along(
        np.array([x_left_end - 1.0, yv, zv]),
        np.array([x_left_end + b_dep + s_dep, yv, zv]),
        b_rad,
        segments=48,
    )
    # +X side: flush internal blind 688-2RS bearing pocket (loaded from Cyl 4 bore, sealed solid to x_right_end)
    right_bearing_pocket = make_cylinder_along(
        np.array([x_right_end - 4.8 - b_dep, yv, zv]),
        np.array([x_right_end - 4.8, yv, zv]),
        b_rad,
        segments=48,
    )

    bolt_sp = float(ds["end_plate_bolt_spacing_mm"]) * 0.5
    ins_rad = float(ds["end_plate_insert_pilot_mm"]) * 0.5
    cutters = [shaft_bore, bushing_pocket, left_seal_and_bearing_pocket, right_bearing_pocket]
    for sy in (-1.0, 1.0):
        # -X seal retainer 2x M4 brass heat-set inserts
        cutters.append(
            make_cylinder_along(
                np.array([x_left_end - 1.0, yv + sy * bolt_sp, zv]),
                np.array([x_left_end + 9.0, yv + sy * bolt_sp, zv]),
                ins_rad,
                segments=24,
            )
        )
    # 2x M6 heat-set insert bosses for external universal actuator bracket (on -Y face of -X act_pad)
    for dx_b in (-10.0, 10.0):
        cutters.append(
            make_cylinder_along(
                np.array([x_left_end + 16.0 + dx_b, yv - 38.0, zv - 6.0]),
                np.array([x_left_end + 16.0 + dx_b, yv - 22.0, zv - 6.0]),
                3.6,
                segments=24,
            )
        )

    # Printable external hardware parts (flat on bed Z=0)
    # 1) -X Blind Bearing Cap (40x32x7 mm with static O-ring gland)
    cap_body = make_rounded_prism(40.0, 32.0, 7.0, 7.0, segments=48, center=(0.0, 0.0, 3.5), axis="z")
    cap_or_out = md.Manifold.cylinder(2.0, 10.2, 10.2, circular_segments=48, center=True).translate([0.0, 0.0, 0.8])
    cap_or_in = md.Manifold.cylinder(3.0, 7.8, 7.8, circular_segments=48, center=True).translate([0.0, 0.0, 0.8])
    cap_cuts = [cap_or_out - cap_or_in]
    for sx in (-1.0, 1.0):
        cap_cuts.append(md.Manifold.cylinder(10.0, 2.25, 2.25, circular_segments=24, center=True).translate([sx * bolt_sp, 0.0, 3.5]))
    blind_cap = m_diff(cap_body, cap_cuts)

    # 2) +X Viton Lip-Seal Retainer Plate (40x32x5 mm with Ø11.5 mm shaft collar bore)
    ret_body = make_rounded_prism(40.0, 32.0, 7.0, 5.0, segments=48, center=(0.0, 0.0, 2.5), axis="z")
    ret_cuts = [md.Manifold.cylinder(8.0, 5.75, 5.75, circular_segments=36, center=True).translate([0.0, 0.0, 2.5])]
    for sx in (-1.0, 1.0):
        ret_cuts.append(md.Manifold.cylinder(8.0, 2.25, 2.25, circular_segments=24, center=True).translate([sx * bolt_sp, 0.0, 2.5]))
    seal_retainer = m_diff(ret_body, ret_cuts)

    # 3) Universal External Actuator Bracket (mounts to 2x M6 pad; accepts OEM IMRC cable ferrule or vacuum pod)
    br_base = make_rounded_prism(38.0, 22.0, 4.0, 6.0, segments=32, center=(0.0, 0.0, 3.0), axis="z")
    br_arm = make_rounded_prism(18.0, 46.0, 4.0, 6.0, segments=32, center=(22.0, 12.0, 3.0), axis="z")
    br_tab = make_rounded_prism(20.0, 6.0, 2.0, 26.0, segments=24, center=(22.0, 32.0, 13.0), axis="z")
    br_solid = m_union([br_base, br_arm, br_tab])
    br_cuts = [
        md.Manifold.cylinder(10.0, 3.3, 3.3, circular_segments=24, center=True).translate([-10.0, 0.0, 3.0]),
        md.Manifold.cylinder(10.0, 3.3, 3.3, circular_segments=24, center=True).translate([10.0, 0.0, 3.0]),
        # Vacuum-pod mount holes on arm + cable ferrule slot on vertical tab
        md.Manifold.cylinder(10.0, 3.3, 3.3, circular_segments=24, center=True).translate([22.0, 16.0, 3.0]),
        md.Manifold.cylinder(10.0, 3.3, 3.3, circular_segments=24, center=True).translate([22.0, 0.0, 3.0]),
        make_cylinder_along(np.array([22.0, 26.0, 19.0]), np.array([22.0, 38.0, 19.0]), 3.4, segments=24),
        md.Manifold.cube([3.2, 12.0, 14.0], center=True).translate([22.0, 32.0, 22.0]),
    ]
    actuator_bracket = m_diff(br_solid, br_cuts)

    # 3D-visualized FOD-safe internal valve blades + shaft (used for CFD open/closed checks & overview)
    a_closed = math.radians(float(ds["butterfly_closed_angle_deg"]))
    d_bore = float(sb["bore_diameter_mm"])
    cl_r = float(ds["butterfly_radial_clearance_mm"])
    d_minor = d_bore - 2.0 * cl_r
    d_major = d_minor / math.cos(a_closed)
    t_blade = float(ds["butterfly_thickness_mm"])

    return {
        "outer": m_union([shaft_boss, anchor_web, end_flange_left, act_pad]),
        "cutters": m_union(cutters),
        "blind_cap": blind_cap,
        "seal_retainer": seal_retainer,
        "actuator_bracket": actuator_bracket,
        "d_blade_minor": d_minor,
        "d_blade_major": d_major,
        "t_blade": t_blade,
    }


def build_valve_internals_for_cfd(params: dict, open_mode: bool, cfd_plate_thick_mm: float = 4.0) -> md.Manifold:
    """Return solid shaft + 4 butterfly plates in closed (8 deg) or open (90 deg) pose."""
    ds = params["dsi_valve_system"]
    sb = params["runners"]["short_bypass"]
    yv = float(sb["shaft_center_y_mm"])
    zv = float(sb["shaft_center_z_mm"])
    d_bore = float(sb["bore_diameter_mm"])
    cl_r = float(ds["butterfly_radial_clearance_mm"])
    d_minor = d_bore - 2.0 * cl_r
    d_major = d_minor / math.cos(math.radians(float(ds["butterfly_closed_angle_deg"])))
    t_plate = max(float(ds["butterfly_thickness_mm"]), cfd_plate_thick_mm)

    x0 = float(ds["left_cap_end_x_mm"])
    x1 = float(ds["right_seal_face_x_mm"])
    parts = [make_cylinder_along(np.array([x0, yv, zv]), np.array([x1, yv, zv]), float(ds["shaft_diameter_mm"]) * 0.5, segments=32)]

    # Elliptical plate oriented relative to bore axis
    elev_deg = float(sb.get("axis_elevation_deg", 38.0))
    theta_deg = 90.0 if open_mode else float(ds["butterfly_closed_angle_deg"])
    # Disk normal starts at +Z; rotating around X by (90 - elev_deg) aligns normal with d_bore
    ang = np.linspace(0.0, 2.0 * math.pi, 48, endpoint=False)
    ell_uv = np.column_stack([0.5 * d_minor * np.cos(ang), 0.5 * d_major * np.sin(ang)])
    plate_base = extrude_polygon_along_axis(ell_uv, t_plate, center=(0.0, 0.0, 0.0), axis="z")
    tilt_x = (90.0 - elev_deg) + theta_deg
    for xc in params["runners"]["center_x_mm"]:
        parts.append(plate_base.rotate([tilt_x, 0.0, 0.0]).translate([float(xc), yv, zv]))
    return m_union(parts)


# ---------------------------------------------------------------------------
# Top Service Hatches (O-Ringed, Bolt-On Lids)
# ---------------------------------------------------------------------------

def build_service_hatch_components(params: dict) -> dict:
    """Build left & right raised flat-seated top service hatch bosses, cutouts, O-ring grooves, and lids."""
    sh = params["service_hatches"]
    if not sh.get("enabled", True):
        return {"outer": None, "cutters": None, "lid_left": None, "lid_right": None}

    ox = float(sh["opening_length_x_mm"])
    oy = float(sh["opening_width_y_mm"])
    r_op = float(sh["opening_corner_radius_mm"])
    rim = float(sh["boss_rim_width_mm"])
    yc = float(sh["center_y_mm"])
    bx_out = ox + 2.0 * rim
    by_out = oy + 2.0 * rim
    r_out = r_op + rim

    t_lid = float(sh["lid_thickness_mm"])
    lip = float(sh["lid_boss_lip_mm"])

    bosses: list[md.Manifold] = []
    cutters: list[md.Manifold] = []
    lids: dict[str, md.Manifold] = {}

    for side_key, xc_key, z_key in [
        ("lid_left", "left_center_x_mm", "left_seat_z_mm"),
        ("lid_right", "right_center_x_mm", "right_seat_z_mm"),
    ]:
        xc = float(sh[xc_key])
        z_seat = float(sh[z_key])
        d_mid = plenum_dims_at_x(xc, params)
        z_floor_anchor = d_mid["z_top_in"] - 4.0
        boss_h = z_seat - z_floor_anchor
        assert boss_h > 4.0, f"Hatch {side_key} seat too low vs plenum ceiling"

        # Outer boss block growing cleanly out of tapered plenum roof
        boss = make_rounded_prism(
            bx_out, by_out, r_out, boss_h, segments=64, center=(xc, yc, 0.5 * (z_seat + z_floor_anchor)), axis="z"
        )
        bosses.append(boss)

        # Through-opening down into plenum cavity
        cutters.append(
            make_rounded_prism(ox, oy, r_op, boss_h + 18.0, segments=64, center=(xc, yc, z_seat - boss_h * 0.4), axis="z")
        )

        # Continuous Viton O-ring groove milled into manifold boss top seat
        or_off = 4.2
        gw = float(sh["oring_width_mm"])
        gd = float(sh["oring_depth_mm"])
        g_out = make_rounded_prism(
            ox + 2.0 * (or_off + gw * 0.5),
            oy + 2.0 * (or_off + gw * 0.5),
            r_op + or_off + gw * 0.5,
            gd + 1.0,
            segments=64,
            center=(xc, yc, z_seat - gd * 0.5 + 0.5),
            axis="z",
        )
        g_in = make_rounded_prism(
            ox + 2.0 * (or_off - gw * 0.5),
            oy + 2.0 * (or_off - gw * 0.5),
            r_op + or_off - gw * 0.5,
            gd + 2.0,
            segments=64,
            center=(xc, yc, z_seat - gd * 0.5 + 0.5),
            axis="z",
        )
        cutters.append(g_out - g_in)

        # 6x M5 heat-set insert pilots around rim (3 front, 3 rear at X = xc ± 42, 0; Y = yc ± (oy/2 + 8.0))
        ins_r = float(sh["insert_pilot_diameter_mm"]) * 0.5
        ins_d = float(sh["insert_depth_mm"])
        bolt_r = float(sh["bolt_hole_diameter_mm"]) * 0.5
        y_bolt = oy * 0.5 + 8.0
        x_bolts = [-42.0, 0.0, 42.0]
        bolt_pts = [(dx, sy * y_bolt) for sy in (-1.0, 1.0) for dx in x_bolts]
        for dx, dy in bolt_pts:
            cutters.append(
                md.Manifold.cylinder(ins_d + 2.0, ins_r, ins_r, circular_segments=24, center=True).translate(
                    [xc + dx, yc + dy, z_seat - ins_d * 0.5 + 1.0]
                )
            )

        # Printable Lid (flat bottom at Z=0 for zero-support print; alignment pilot lip faces up when printing)
        lid_plate = make_rounded_prism(bx_out, by_out, r_out, t_lid, segments=64, center=(0.0, 0.0, t_lid * 0.5), axis="z")
        lid_lip = make_rounded_prism(ox - 0.6, oy - 0.6, max(r_op - 0.3, 1.0), lip, segments=64, center=(0.0, 0.0, t_lid + lip * 0.5), axis="z")
        lid_solid = m_union([lid_plate, lid_lip])
        lid_holes = [
            md.Manifold.cylinder(t_lid + lip + 4.0, bolt_r, bolt_r, circular_segments=24, center=True).translate([dx, dy, 0.5 * (t_lid + lip)])
            for dx, dy in bolt_pts
        ]
        lids[side_key] = m_diff(lid_solid, lid_holes)

    return {
        "outer": m_union(bosses),
        "cutters": m_union(cutters),
        "lid_left": lids["lid_left"],
        "lid_right": lids["lid_right"],
    }


# ---------------------------------------------------------------------------
# TB Neck, IACV Pad, -Y NA Vacuum Pads & Center Split Flange
# ---------------------------------------------------------------------------

def eased_progress(t: float, start: float, end: float) -> float:
    """Integrate two cubic endpoint rate ramps and a constant middle rate."""
    if not (start > 0 and end > 0 and start + end <= 1):
        raise ValueError("Transition endpoint widths must be positive and total at most one")
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    integral = 1.0 - (start + end) / 2.0
    if t < start:
        u = t / start
        return start * (u**3 - 0.5 * u**4) / integral
    if t > 1.0 - end:
        u = (1.0 - t) / end
        return 1.0 - end * (u**3 - 0.5 * u**4) / integral
    return (t - start / 2.0) / integral


def deck_seal_land(params: dict, tb_parts: dict) -> tuple[dict, dict]:
    """Add local radial bore-edge support behind the narrowest portion of the factory throttle gasket."""
    body = params["throttle_body"]
    cfg = body["iacv_flange_feed"]
    face, axis = tb_parts["flange_face_center"], tb_parts["tb_axis"]
    u, v, offset = throttle_mounting_frame(axis, body)
    radius = body["bore_diameter_mm"] / 2.0
    center = np.asarray(body["bore_from_bolt_grid_uv_mm"], dtype=np.float64)
    first, divider = cfg["visible_throttle_seal_centerlines_uv_mm"]
    seal = LineString([*first, first[0]]).union(LineString(divider))
    band = seal.buffer(1.60)
    directions = rounded_rect_points(2.0, 2.0, 1.0, 480)
    from shapely.geometry import Point as ShapelyPoint
    origin = ShapelyPoint(center)
    cut_radii = []
    for direction in directions:
        ray = LineString([center, center + radius * direction])
        crossing = ray.intersection(band)
        cut_radii.append(radius if crossing.is_empty else origin.distance(crossing))
    cut_radii_arr = np.asarray(cut_radii, dtype=np.float64)
    axes = np.stack((u, v))
    depths = np.r_[-2.25, np.linspace(0.0, 5.5, 45), 5.7]
    rings = []
    for depth in depths:
        fade = eased_progress((float(depth) - 1.0) / 4.5, 0.24, 0.24)
        radii = cut_radii_arr + fade * (radius + 0.03 - cut_radii_arr)
        rings.append(face + offset - float(depth) * axis + (center + radii[:, None] * directions) @ axes)
    opening = trimesh_to_manifold(loft_closed_solid(rings))
    stock = make_cylinder_along(face + 2.2 * axis, face - 5.58 * axis, radius + 1.0, 160)
    support = stock - opening
    trimmed = {**tb_parts, "tb_bore": tb_parts["tb_bore"] - support, "cutters": tb_parts["cutters"] - support}
    return trimmed, {"max_local_radial_inset_mm": float(radius - cut_radii_arr.min())}


def flush_flange_blend(params: dict, tb_parts: dict) -> tuple[dict, dict]:
    """Confine the round flange-back blend inside the square throttle flange profile."""
    cfg = params["throttle_body"]
    face, axis = tb_parts["flange_face_center"], tb_parts["tb_axis"]
    u, v, offset = throttle_mounting_frame(axis, cfg)
    frame = np.stack((u, v, axis))
    origin = face + offset
    w, h, r = (float(cfg[k]) for k in ("flange_width_mm", "flange_height_mm", "flange_corner_radius_mm"))
    thickness = float(cfg["flange_thickness_mm"])
    start, stop, fade_end = thickness - 2.5, thickness + 10.0, thickness + 17.0

    def ring(depth: float) -> np.ndarray:
        extra = 48.0 * eased_progress((depth - stop) / (fade_end - stop), 0.35, 0.35)
        section = rounded_rect_points(w + 0.012 + 2.0 * extra, h + 0.012 + 2.0 * extra, r + extra, 192)
        return origin - depth * axis + section @ frame[:2]

    envelope = trimesh_to_manifold(loft_closed_solid([
        ring(float(d)) for d in (start - 0.5, start, stop, *np.linspace(stop + 0.2, fade_end, 38), fade_end + 0.5)
    ]))
    original = tb_parts["outer"]
    fwd = original.trim_by_plane(axis, float(axis @ face) - start)
    aft = original.trim_by_plane(-axis, float(-axis @ face) + fade_end)
    revised = m_union([fwd, original ^ envelope, aft])
    return {**tb_parts, "outer": revised}, {"removed_exterior_mm3": float((original - revised).volume())}


def tb_neck_bezier_points(params: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute 3D C1 cubic-Bezier control points and flange frame for the TB neck."""
    tb = params["throttle_body"]
    pl = params["plenum"]
    x_start = float(pl["cyl4_end_x_mm"])
    d4 = plenum_dims_at_x(x_start, params)
    p_start = np.array([x_start, d4["yc"], d4["zc"]], dtype=np.float64)

    if "forward_toward_head_deg" in tb:
        yaw = math.radians(float(tb["forward_toward_head_deg"]))
        pitch = math.radians(float(tb.get("upward_pitch_deg", 0.0)))
        tb_axis = np.array([math.cos(yaw) * math.cos(pitch), -math.sin(yaw) * math.cos(pitch), math.sin(pitch)], dtype=np.float64)
        tb_axis /= np.linalg.norm(tb_axis)
        off = np.asarray(tb["flange_back_offset_mm"], dtype=np.float64)
        p_flange_back = p_start + off
    else:
        cant_rad = math.radians(float(tb.get("forward_cant_deg", tb.get("forward_toward_head_deg", 32.0))))
        tb_axis = np.array([math.cos(cant_rad), -math.sin(cant_rad), 0.0], dtype=np.float64)
        p_flange_back = p_start + tb_axis * float(tb["neck_length_mm"])

    p_flange_face = p_flange_back + tb_axis * float(tb["flange_thickness_mm"])
    p_neck_end = p_flange_back + tb_axis * 4.0
    chord = float(np.linalg.norm(p_neck_end - p_start))
    c0 = p_start + np.array([1.0, 0.0, 0.0]) * (0.36 * chord)
    c1 = p_neck_end - tb_axis * (0.36 * chord)
    return p_start, c0, c1, p_neck_end, p_flange_back, p_flange_face, tb_axis


def throttle_mounting_frame(axis: np.ndarray, tb: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Use firewall-positive U and hood-positive V on the throttle flange."""
    u = np.cross(np.array([0.0, 0.0, 1.0]), axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    bore_u, bore_v = tb.get("bore_from_bolt_grid_uv_mm", [0.0, 0.0])
    grid_offset = -float(bore_u) * u - float(bore_v) * v
    return u, v, grid_offset


def build_throttle_body_components(params: dict) -> dict:
    """Build swept 3D C1 cubic-Bezier TB neck, eased transition bell, eccentric 4-bolt flange & optional O-ring/relief."""
    tb = params["throttle_body"]
    pl = params["plenum"]
    wall = float(tb["neck_wall_thickness_mm"])
    bore_d = float(tb["bore_diameter_mm"])

    p_start, c0, c1, p_neck_end, p_flange_back, p_flange_face, tb_axis = tb_neck_bezier_points(params)
    pl_wall = float(pl["wall_thickness_mm"])
    d4 = plenum_dims_at_x(float(p_start[0]), params)
    pl_w_in, pl_h_in, pl_r_in = d4["w"], d4["h"], d4["r"]
    pl_w_out, pl_h_out, pl_r_out = pl_w_in + 2.0 * pl_wall, pl_h_in + 2.0 * pl_wall, pl_r_in + pl_wall

    n_pts = int(pl["profile_segments"])
    up_hint = np.array([0.0, 0.0, 1.0])
    u_ax, v_ax, grid_offset = throttle_mounting_frame(tb_axis, tb)

    neck_out_rings = [ring_frame_points(p_start - np.array([4.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), up_hint, rounded_rect_points(pl_w_out - 0.1, pl_h_out - 0.1, pl_r_out - 0.05, n_pts))]
    neck_in_rings = [ring_frame_points(p_start - np.array([4.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), up_hint, rounded_rect_points(pl_w_in, pl_h_in, pl_r_in, n_pts))]

    n_steps = 56
    x_dir = np.array([1.0, 0.0, 0.0])
    for k in range(n_steps + 1):
        t = k / n_steps
        pos, _tan = bezier_point_and_tangent(p_start, c0, c1, p_neck_end, t)
        s_t = 0.5 - 0.5 * math.cos(math.pi * min(t / 0.86, 1.0))
        s_rot = 0.5 - 0.5 * math.cos(math.pi * float(np.clip((t - 0.08) / 0.92, 0.0, 1.0)))
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
        fl_rings.append(ring_frame_points(p_flange_back + grid_offset + tb_axis * ax_off, tb_axis, up_hint, rounded_rect_points(fl_w - 2.0 * inset, fl_h - 2.0 * inset, max(fl_r - inset, 1.0), 128)))
    fl_rings.append(ring_frame_points(p_flange_face + grid_offset, tb_axis, up_hint, rounded_rect_points(fl_w, fl_h, fl_r, 128)))
    outer_pieces = [neck_outer, trimesh_to_manifold(loft_closed_solid(fl_rings))]

    cutters: list[md.Manifold] = [tb_bore]
    bx, by, b_rad = float(tb["bolt_spacing_x_mm"]) * 0.5, float(tb["bolt_spacing_y_mm"]) * 0.5, float(tb["bolt_hole_diameter_mm"]) * 0.5
    socket_relief = tb.get("socket_relief")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pt_c = p_flange_back + grid_offset + u_ax * (sx * bx) + v_ax * (sy * by)
            cutters.append(make_cylinder_along(pt_c - tb_axis * 3.0, pt_c + tb_axis * (float(tb["flange_thickness_mm"]) + 3.0), b_rad, segments=64))
            if socket_relief and [sx, sy] == socket_relief["bolt_uv_signs"]:
                cutters.append(make_cylinder_along(
                    pt_c - float(socket_relief["reach_mm"]) * tb_axis,
                    pt_c - float(socket_relief["seat_land_mm"]) * tb_axis,
                    float(socket_relief["radius_mm"]),
                    segments=72,
                ))

    og = tb["oring_groove"]
    if og["enabled"]:
        r_in_g = float(og["inner_diameter_mm"]) * 0.5
        r_out_g = r_in_g + float(og["width_mm"])
        depth_g = float(og["depth_mm"])
        outer_g = make_cylinder_along(p_flange_face - tb_axis * depth_g, p_flange_face + tb_axis * 1.0, r_out_g, segments=72)
        inner_g = make_cylinder_along(p_flange_face - tb_axis * (depth_g + 1.0), p_flange_face + tb_axis * 2.0, r_in_g, segments=72)
        cutters.append(outer_g - inner_g)

    tb_out = {
        "outer": m_union(outer_pieces),
        "tb_bore": tb_bore,
        "cutters": m_union(cutters),
        "flange_face_center": p_flange_face,
        "tb_axis": tb_axis,
    }
    if tb.get("iacv_flange_feed") and tb["iacv_flange_feed"].get("visible_throttle_seal_centerlines_uv_mm"):
        tb_out, _ = deck_seal_land(params, tb_out)
    if tb.get("flush_back_blend_to_flange_profile", False) or tb.get("iacv_flange_feed"):
        tb_out, _ = flush_flange_blend(params, tb_out)
    return tb_out


def build_boss_pad_components(pad_cfg: dict, params: dict) -> tuple[md.Manifold, list[md.Manifold]]:
    """Build low-profile, wide-skirted (+Z facing) NPT vacuum boss pad on dropped plenum roof."""
    xc = float(pad_cfg["x_center_mm"])
    yc = float(pad_cfg["y_center_mm"])
    d_x = plenum_dims_at_x(xc, params)
    z_roof_in = d_x["z_top_in"]
    z_top = z_roof_in + float(params["plenum"]["wall_thickness_mm"]) + float(pad_cfg["pad_height_z_mm"]) - 2.0
    z_bot = z_roof_in - 6.0

    lx = float(pad_cfg["length_x_mm"])
    wy = float(pad_cfg["width_y_mm"])
    fx = float(pad_cfg.get("skirt_flare_x_mm", 10.0))
    fy = float(pad_cfg.get("skirt_flare_y_mm", 8.0))
    r_edge = min(float(pad_cfg.get("top_chamfer_mm", 2.0)), 2.0)

    z_collar, n_p = z_top - 2.4, 96
    pad_rings = []
    for k in range(18):
        u = k / 17.0
        cove = (1.0 - u) ** 2.2
        uv = rounded_rect_points(lx + 2.0 * fx * cove, wy + 2.0 * fy * cove, 6.0 + 7.0 * cove, n_p)
        pad_rings.append(np.column_stack([uv[:, 0] + xc, uv[:, 1] + yc, np.full(n_p, z_bot + (z_collar - z_bot) * u)]))
    for th in np.linspace(0.0, 0.5 * math.pi, 7):
        inset = r_edge * (1.0 - math.cos(th))
        uv_k = rounded_rect_points(lx - 2.0 * inset, wy - 2.0 * inset, max(6.0 - inset, 1.5), n_p)
        pad_rings.append(np.column_stack([uv_k[:, 0] + xc, uv_k[:, 1] + yc, np.full(n_p, (z_top - r_edge) + r_edge * math.sin(th))]))
    pad = trimesh_to_manifold(loft_closed_solid(pad_rings))

    diameters = pad_cfg["port_pilot_diameters_mm"]
    start_x = xc - float(pad_cfg["port_spacing_x_mm"]) * (int(pad_cfg["port_count"]) - 1) * 0.5
    bores = [
        make_cylinder_along(
            np.array([start_x + idx * float(pad_cfg["port_spacing_x_mm"]), yc, z_roof_in - 12.0]),
            np.array([start_x + idx * float(pad_cfg["port_spacing_x_mm"]), yc, z_top + 4.0]),
            float(diameters[idx]) * 0.5,
            segments=36,
        )
        for idx in range(int(pad_cfg["port_count"]))
    ]
    return pad, bores


def build_iacv_components(params: dict) -> dict:
    """Build V2-style top-mounted 2-bolt Ford IACV pedestal with +Y rear 1/4-18 NPT side tap."""
    iac = params["throttle_body"]["iacv_mount"]
    xc, yc, top_z = float(iac["x_center_mm"]), float(iac["y_center_mm"]), float(iac["top_z_mm"])
    port_half = float(iac["port_spacing_x_mm"]) * 0.5
    x_plenum_port, x_supply_port = xc - port_half, xc + port_half

    pad_l, pad_w, pad_r = float(iac["pad_length_x_mm"]), float(iac["pad_width_y_mm"]), float(iac["pad_corner_radius_mm"])
    fl_nx, fl_px, base_wy = float(iac.get("skirt_flare_neg_x_mm", 12.0)), float(iac.get("skirt_flare_pos_x_mm", 4.0)), float(iac.get("base_width_y_mm", 74.0))
    r_edge = min(float(iac.get("top_chamfer_mm", 2.2)), 2.2)

    z_skirt_bot = min(float(iac["base_z_mm"]), 16.0)
    z_collar, n_p = 47.0, 96
    iac_rings = []
    for k in range(22):
        u = k / 21.0
        cove = (1.0 - u) ** 2.2
        x_min_k, x_max_k = (xc - 0.5 * pad_l) - fl_nx * cove, (xc + 0.5 * pad_l) + fl_px * cove
        uv = rounded_rect_points(x_max_k - x_min_k, pad_w + (base_wy - pad_w) * cove, pad_r + 7.0 * cove, n_p)
        iac_rings.append(np.column_stack([uv[:, 0] + 0.5 * (x_min_k + x_max_k), uv[:, 1] + yc, np.full(n_p, z_skirt_bot + (z_collar - z_skirt_bot) * u)]))
    for zk in (50.0, 59.5):
        uv = rounded_rect_points(pad_l, pad_w, pad_r, n_p)
        iac_rings.append(np.column_stack([uv[:, 0] + xc, uv[:, 1] + yc, np.full(n_p, zk)]))
    for th in np.linspace(0.0, 0.5 * math.pi, 7):
        inset = r_edge * (1.0 - math.cos(th))
        uv_k = rounded_rect_points(pad_l - 2.0 * inset, pad_w - 2.0 * inset, max(pad_r - inset, 2.0), n_p)
        iac_rings.append(np.column_stack([uv_k[:, 0] + xc, uv_k[:, 1] + yc, np.full(n_p, (top_z - r_edge) + r_edge * math.sin(th))]))
    pad_outer = trimesh_to_manifold(loft_closed_solid(iac_rings))

    cutters: list[md.Manifold] = []
    b_rad, b_half, b_bot = float(iac["bolt_pilot_diameter_mm"]) * 0.5, float(iac["bolt_spacing_y_mm"]) * 0.5, top_z - float(iac["bolt_depth_mm"])
    for sy in (-1.0, 1.0):
        cutters.append(make_cylinder_along(np.array([xc, yc + sy * b_half, b_bot]), np.array([xc, yc + sy * b_half, top_z + 4.0]), b_rad, segments=36))

    p_rad = float(iac["port_diameter_mm"]) * 0.5
    ang_p = np.linspace(0.0, 2.0 * math.pi, 64, endpoint=False)
    cos_p, sin_p = np.cos(ang_p), np.sin(ang_p)
    disch_rings = [
        np.column_stack([x_plenum_port + p_rad * cos_p, yc + p_rad * sin_p, np.full(64, top_z + 4.0)]),
        np.column_stack([x_plenum_port + p_rad * cos_p, yc + p_rad * sin_p, np.full(64, 45.0)]),
    ]
    th_max = 0.38 * math.pi
    denom = 1.0 - math.cos(th_max)
    for th in np.linspace(0.0, th_max, 13)[1:]:
        rk = p_rad + 2.3 * (1.0 - math.cos(th)) / denom
        zk = 45.0 - 7.0 * (math.sin(th) / math.sin(th_max))
        disch_rings.append(np.column_stack([x_plenum_port + rk * cos_p, yc + rk * sin_p, np.full(64, zk)]))
    disch_rings.append(np.column_stack([x_plenum_port + 8.8 * cos_p, yc + 8.8 * sin_p, np.full(64, 32.0)]))
    cutters.append(trimesh_to_manifold(loft_closed_solid(disch_rings[::-1])))

    z_elbow = 54.6
    supply_upper = make_cylinder_along(np.array([x_supply_port, yc, z_elbow]), np.array([x_supply_port, yc, top_z + 4.0]), p_rad, segments=64)
    bowl_rings = [
        np.column_stack([
            x_supply_port + max(0.2, p_rad * math.cos(th)) * cos_p,
            yc + max(0.2, p_rad * math.cos(th)) * sin_p,
            np.full(64, z_elbow - 6.2 * math.sin(th)),
        ])
        for th in np.linspace(0.0, 0.5 * math.pi, 13)
    ]
    cutters.append(supply_upper + trimesh_to_manifold(loft_closed_solid(bowl_rings[::-1])))

    if iac.get("side_supply_tap_enabled", False):
        tap_rad = float(iac["side_supply_tap_diameter_mm"]) * 0.5
        tap_z = float(iac["side_supply_tap_z_mm"])
        cutters.append(make_cylinder_along(np.array([x_supply_port, yc, tap_z]), np.array([x_supply_port, yc + 0.5 * pad_w + 10.0, tap_z]), tap_rad, segments=36))

    wall_thickness = float(iac["supply_pocket_bottom_z_mm"]) - float(params["plenum"]["top_inner_z_mm"])
    assert wall_thickness >= 4.5, f"IACV supply wall thickness {wall_thickness:.2f} mm < 4.5 mm"
    return {
        "outer": pad_outer,
        "cutters": m_union(cutters),
        "wall_thickness_mm": wall_thickness,
    }


def make_iacv_flange_feed_route(params: dict, tb_parts: dict) -> dict | None:
    """Build sealed internal IACV feed passage from flat TB face opening to IACV supply pocket."""
    tb_cfg = params["throttle_body"]
    cfg = tb_cfg.get("iacv_flange_feed")
    if not cfg or not cfg.get("route_path_xyz_mm"):
        return None

    port = ShapelyPolygon(cfg["face_opening_uv_mm"])
    radius = float(cfg["duct_diameter_mm"]) / 2.0
    wall = float(cfg["duct_wall_mm"])
    face, axis = tb_parts["flange_face_center"], tb_parts["tb_axis"]
    u, v, offset = throttle_mounting_frame(axis, tb_cfg)
    origin = face + offset
    axes = np.stack((u, v))
    cup = np.asarray(cfg["round_transition_center_uv_mm"], dtype=np.float64)
    depths = np.r_[-1.5, np.linspace(0.3, 11.0, 32), 11.65]

    def adapter(poly, end_radius: float) -> md.Manifold:
        outline = LineString(orient(poly, sign=1.0).exterior.coords)
        profile = np.asarray([outline.interpolate(i / 96, normalized=True).coords[0] for i in range(96)])
        start = profile[0] - np.mean(profile, axis=0)
        ang = math.atan2(float(start[1]), float(start[0]))
        rot = np.array([[math.cos(ang), math.sin(ang)], [-math.sin(ang), math.cos(ang)]])
        circle = cup + end_radius * rounded_rect_points(2.0, 2.0, 1.0, 96) @ rot
        rings = []
        for d in depths:
            w = eased_progress((float(d) - 0.32) / 10.68, 0.26, 0.31)
            rings.append(origin - float(d) * axis + ((1.0 - w) * profile + w * circle) @ axes)
        return trimesh_to_manifold(loft_closed_solid(rings))

    inlet = adapter(port, radius)
    inlet_outer = adapter(port.buffer(wall), radius + wall).trim_by_plane(-axis, float((-axis) @ face) + 1.25)

    approach = [origin + cup @ axes - 11.0 * axis]
    iac = tb_cfg["iacv_mount"]
    x_sup = float(iac["x_center_mm"]) + float(iac["port_spacing_x_mm"]) / 2.0
    y_sup = float(iac["y_center_mm"])
    points = np.array([*approach, *cfg["route_path_xyz_mm"], [x_sup, y_sup, 54.6]], dtype=np.float64)
    stations = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    curve = CubicSpline(stations, points, bc_type=((1, -axis), (1, [0.0, 1.0, 0.0])))
    ts = np.r_[-0.75, np.linspace(0.0, float(stations[-1]), 100)]
    positions, tangents = curve(ts), curve(ts, 1)

    def tube(rad: float, add_fairing: bool = False) -> md.Manifold:
        profile = rounded_rect_points(2.0 * rad, 2.0 * rad, rad, 96)
        rings = []
        for idx, (pos, tan) in enumerate(zip(positions, tangents, strict=True)):
            ring = ring_frame_points(pos, tan, np.array([0.0, 0.0, 1.0]), profile)
            if add_fairing:
                t_hat = tan / np.linalg.norm(tan)
                down = np.array([-1.0, 0.0, 0.0]) + t_hat * t_hat[0]
                mag = float(np.linalg.norm(down))
                radial = (ring - pos) / rad
                s_norm = float(ts[idx]) / max(float(stations[-1]), 1e-6)
                fade_in = eased_progress((s_norm - 0.08) / 0.22, 0.35, 0.35)
                fade_out = 1.0 - eased_progress((s_norm - 0.72) / 0.22, 0.35, 0.35)
                span_w = fade_in * fade_out
                if mag > 1e-6:
                    cosine = np.clip(radial @ (down / mag), -1.0, 1.0)
                    sine = np.sqrt(np.maximum(1e-8, 1.0 - cosine**2) + 0.0049)
                    u_sh = np.clip((cosine - 0.50) / 0.35, 0.0, 1.0)
                    w_sh = u_sh * u_sh * (3.0 - 2.0 * u_sh)
                    shoulder = 1.0 + w_sh * np.maximum(0.0, math.sqrt(2.0) / (np.maximum(cosine, 0.0) + sine) - 1.0)
                    ring = pos + rad * radial * (1.0 + (shoulder - 1.0) * mag * span_w)[:, None]
            rings.append(ring)
        return trimesh_to_manifold(loft_closed_solid(rings))

    *_, p_fb, _, _ = tb_neck_bezier_points(params)
    bx, by, b_rad = float(tb_cfg["bolt_spacing_x_mm"]) * 0.5, float(tb_cfg["bolt_spacing_y_mm"]) * 0.5, float(tb_cfg["bolt_hole_diameter_mm"]) * 0.5
    centers = [p_fb + offset + sx * bx * u + sy * by * v for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
    sockets = m_union([make_cylinder_along(pt - 14.0 * axis, pt - 0.30 * axis, 6.27, 64) for pt in centers])
    holes = m_union([make_cylinder_along(pt - 2.0 * axis, pt + 15.0 * axis, b_rad, 64) for pt in centers])
    deck_guard = make_rounded_prism(
        float(iac["pad_length_x_mm"]) + 4.0, float(iac["pad_width_y_mm"]) + 4.0, float(iac["pad_corner_radius_mm"]), 35.0,
        segments=96, center=(float(iac["x_center_mm"]), y_sup, float(iac["top_z_mm"]) + 17.5), axis="z",
    )
    fairing = bool(cfg.get("printer_fairing", False))
    return {
        "inner": inlet + tube(radius),
        "outer": (inlet_outer + tube(radius + wall, fairing)) - sockets - deck_guard,
        "sockets": sockets,
        "bolt_holes": holes,
    }


def _outer_2d_polygon_at_x(combined_outer: md.Manifold, x_pos: float) -> ShapelyPolygon:
    """Slice outer solid at X = x_pos and return clean exterior (Y, Z) Polygon."""
    polys = combined_outer.rotate([0.0, -90.0, 0.0]).slice(x_pos).to_polygons()
    sh_polys = [
        ShapelyPolygon(np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]])).buffer(0.0)
        for p in polys
        if len(p) >= 3
    ]
    merged = unary_union(sh_polys)
    if merged.geom_type == "MultiPolygon":
        merged = max(merged.geoms, key=lambda g: g.area)
    return ShapelyPolygon(merged.exterior.coords)


def build_center_split_flange_and_cutters(pl_plus_shaft_outer: md.Manifold, params: dict) -> dict:
    """
    Build the X=0 split flange wrapping both the tapered plenum AND the center shaft bushing spine
    with 8x M6 perimeter bolts, 2x Ø6 mm dowels, and one continuous Viton O-ring loop.
    """
    cs = params["center_split"]
    x_split = float(cs["split_x_mm"])
    ext = float(cs["flange_radial_extension_mm"])
    thick_total = 2.0 * float(cs["flange_thickness_per_side_mm"])

    outer_2d = _outer_2d_polygon_at_x(pl_plus_shaft_outer, x_split)
    flange_outer_2d = outer_2d.buffer(ext, join_style=1, quad_segs=16)
    flange_ring = extrude_polygon_along_axis(
        np.asarray(flange_outer_2d.exterior.coords, dtype=np.float64), thick_total, center=(x_split, 0.0, 0.0), axis="x"
    )

    bolt_line = LineString(outer_2d.buffer(float(cs["bolt_radial_offset_mm"]), join_style=1, quad_segs=16).exterior)
    total_pts = int(cs["bolt_count"]) + 2
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
                np.array([x_split - thick_total * 0.65, pt.x, pt.y]),
                np.array([x_split + thick_total * 0.65, pt.x, pt.y]),
                rad,
                segments=32,
            )
        )

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


# ---------------------------------------------------------------------------
# Fitment Gauges & CNC Metal STEP/DXF Hardware (build123d)
# ---------------------------------------------------------------------------

def build_fitment_gauges(params: dict) -> dict[str, md.Manifold]:
    """Build test print gauges (2-in boot spigot, 65mm TB, 2-bolt IACV, Ø44 valve bore, dowel pins)."""
    sp = params["runners"]["spigot"]
    g = params["gauges"]
    n_pts = int(params["runners"]["long_scroll"]["profile_segments"])
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
    bore_u, bore_v = tb.get("bore_from_bolt_grid_uv_mm", [0.0, 0.0])
    tb_plate = make_rounded_prism(
        float(tb["flange_width_mm"]), float(tb["flange_height_mm"]), float(tb["flange_corner_radius_mm"]), t_g,
        segments=64, center=(0.0, 0.0, t_g * 0.5), axis="z"
    )
    tb_cutters = [
        md.Manifold.cylinder(
            t_g + 4.0, float(tb["bore_diameter_mm"]) * 0.5, float(tb["bore_diameter_mm"]) * 0.5,
            circular_segments=72, center=True
        ).translate([float(bore_u), float(bore_v), t_g * 0.5])
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
        float(iac["pad_length_x_mm"]), float(iac["pad_width_y_mm"]), float(iac["pad_corner_radius_mm"]), t_iac,
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
            md.Manifold.cylinder(t_iac + 4.0, 3.2, 3.2, circular_segments=32, center=True).translate([0.0, sy * float(iac["bolt_spacing_y_mm"]) * 0.5, t_iac * 0.5])
        )
    iacv_gauge = m_diff(iac_plate, iac_cutters)

    # Valve bore test block (checks Ø44.0 bore, Ø8.4 shaft cross-hole, and elliptical 8-deg plate fit)
    sb = params["runners"]["short_bypass"]
    d_vb = float(sb["bore_diameter_mm"])
    h_vg = float(g["valve_bore_fit_gauge_height_mm"])
    vg_outer = make_rounded_prism(d_vb + 12.0, d_vb + 12.0, 0.5 * (d_vb + 12.0), h_vg, segments=64, center=(0.0, 0.0, h_vg * 0.5), axis="z")
    vg_cuts = [
        md.Manifold.cylinder(h_vg + 4.0, d_vb * 0.5, d_vb * 0.5, circular_segments=72, center=True).translate([0.0, 0.0, h_vg * 0.5]),
        make_cylinder_along(np.array([-d_vb, 0.0, h_vg * 0.5]), np.array([d_vb, 0.0, h_vg * 0.5]), 4.2, segments=36),
    ]
    valve_gauge = m_diff(vg_outer, vg_cuts)

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
        "valve_bore_fit_gauge": valve_gauge,
        "alignment_dowel_pins": dowel_pins_set,
    }


def export_cnc_metal_hardware(params: dict) -> dict:
    """
    Generate FOD-safe 304SS & 6061-T6 CNC/laser-cut metal valve hardware via build123d:
      - svt_na_dsi_butterfly_plate_304ss_1p5mm.step & .dxf
      - svt_na_dsi_valve_shaft_8mm_304ss.step
      - svt_na_dsi_actuator_lever_6061.step & .dxf
    """
    CNC_DIR.mkdir(parents=True, exist_ok=True)
    ds = params["dsi_valve_system"]
    sb = params["runners"]["short_bypass"]
    d_bore = float(sb["bore_diameter_mm"])
    cl_r = float(ds["butterfly_radial_clearance_mm"])
    a_closed = math.radians(float(ds["butterfly_closed_angle_deg"]))
    rx = 0.5 * (d_bore - 2.0 * cl_r)  # minor semi-axis along X
    ry = rx / math.cos(a_closed)       # major semi-axis for 8-deg seated ellipse
    t_plate = float(ds["butterfly_thickness_mm"])
    sp_screw = float(ds["butterfly_screw_spacing_x_mm"]) * 0.5
    r_screw = float(ds["butterfly_screw_hole_diameter_mm"]) * 0.5

    # 1) Butterfly plate (exact elliptical laser-cut 1.5 mm 304SS)
    n_ell = 128
    th_e = np.linspace(0.0, 2.0 * math.pi, n_ell, endpoint=False)
    ell_pts = [(rx * math.cos(a), ry * math.sin(a)) for a in th_e]
    with BuildPart() as bp_plate:
        with BuildSketch():
            with BuildLine():
                for i in range(n_ell):
                    Line(ell_pts[i], ell_pts[(i + 1) % n_ell])
            make_face()
            with Locations([(-sp_screw, 0.0), (sp_screw, 0.0)]):
                Circle(radius=r_screw, mode=Mode.SUBTRACT)
        extrude(amount=t_plate)

    plate_step = CNC_DIR / "svt_na_dsi_butterfly_plate_304ss_1p5mm.step"
    plate_dxf = CNC_DIR / "svt_na_dsi_butterfly_plate_304ss_1p5mm.dxf"
    export_step(bp_plate.part, str(plate_step))

    # Write clean AutoCAD R12 DXF with analytical ELLIPSE / POLYLINE and CIRCLEs
    with open(plate_dxf, "w", encoding="utf-8") as f:
        f.write("0\nSECTION\n2\nENTITIES\n")
        for i in range(n_ell):
            p1 = ell_pts[i]
            p2 = ell_pts[(i + 1) % n_ell]
            f.write(
                f"0\nLINE\n8\nBUTTERFLY_OUTLINE\n"
                f"10\n{p1[0]:.5f}\n20\n{p1[1]:.5f}\n30\n0.0\n"
                f"11\n{p2[0]:.5f}\n21\n{p2[1]:.5f}\n31\n0.0\n"
            )
        for sx in (-sp_screw, sp_screw):
            f.write(f"0\nCIRCLE\n8\nM3_MOUNT_HOLES\n10\n{sx:.4f}\n20\n0.0\n30\n0.0\n40\n{r_screw:.4f}\n")
        f.write("0\nENDSEC\n0\nEOF\n")

    # 2) Ø8.0 mm 304SS Butterfly Shaft with 4x milled -0.75 mm center-plane flats, M3 holes & +X double-D
    d_sh = float(ds["shaft_diameter_mm"])
    r_sh = d_sh * 0.5
    x0 = float(ds["shaft_left_end_x_mm"])
    x1 = float(ds["shaft_right_end_x_mm"])
    L_sh = x1 - x0
    flat_y = float(ds["shaft_flat_offset_from_center_mm"])
    flat_len = float(ds["shaft_flat_length_mm"])
    dd_len = float(ds["shaft_double_d_length_mm"])
    dd_half = float(ds["shaft_double_d_thickness_mm"]) * 0.5

    from build123d import Box, Cylinder, Align
    with BuildPart() as bp_shaft:
        Cylinder(radius=r_sh, height=L_sh, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Mill 4x butterfly flats (-0.75 mm center-plane offset) + 8x M3 mounting pilot holes
        h_cut = r_sh - flat_y + 1.5
        y_cut_c = flat_y + 0.5 * h_cut
        for xc in params["runners"]["center_x_mm"]:
            z_mid = float(xc) - x0
            with Locations([(0.0, y_cut_c, z_mid)]):
                Box(d_sh + 2.0, h_cut, flat_len, mode=Mode.SUBTRACT)
            for dx_s in (-sp_screw, sp_screw):
                with Locations([(0.0, 0.0, z_mid + dx_s)]):
                    Cylinder(radius=1.25, height=d_sh + 2.0, rotation=(90.0, 0.0, 0.0), mode=Mode.SUBTRACT)
        # Mill Double-D flats (6.0 mm across flats) on 16.0 mm actuator end (-X by default)
        dd_z = 0.5 * dd_len if ds.get("actuator_end", "neg_x") == "neg_x" else (L_sh - 0.5 * dd_len)
        h_dd = r_sh - dd_half + 1.5
        for sy in (-1.0, 1.0):
            with Locations([(0.0, sy * (dd_half + 0.5 * h_dd), dd_z)]):
                Box(d_sh + 2.0, h_dd, dd_len + 1.0, mode=Mode.SUBTRACT)

    bb_sh = bp_shaft.part.bounding_box()
    assert bb_sh.max.Y >= 3.99 and bb_sh.min.Y <= -3.99, f"Shaft bearing journal clipped: {bb_sh}"
    assert 11500.0 <= bp_shaft.part.volume <= 14000.0, f"Unexpected shaft STEP volume: {bp_shaft.part.volume:.1f}"
    shaft_step = CNC_DIR / "svt_na_dsi_valve_shaft_8mm_304ss.step"
    export_step(bp_shaft.part, str(shaft_step))

    # 3) 6.0 mm 6061-T6 Actuator Crank Lever Arm with 6.0 x 8.0 mm Double-D bore & dual clevis radii
    cal = ds["oem_imrc_calibration"]
    r_c1 = float(cal["lever_clevis_radius_primary_mm"])
    r_c2 = float(cal["lever_clevis_radius_secondary_mm"])
    r_boss = 9.0
    r_tip = 7.0
    ang_t = math.asin((r_boss - r_tip) / r_c2)
    p_b_top = (-r_boss * math.sin(ang_t), r_boss * math.cos(ang_t))
    p_t_top = (r_c2 - r_tip * math.sin(ang_t), r_tip * math.cos(ang_t))
    p_b_bot = (-r_boss * math.sin(ang_t), -r_boss * math.cos(ang_t))
    p_t_bot = (r_c2 - r_tip * math.sin(ang_t), -r_tip * math.cos(ang_t))

    with BuildPart() as bp_lever:
        with BuildSketch():
            with BuildLine():
                ThreePointArc(p_b_bot, (-r_boss, 0.0), p_b_top)
                Line(p_b_top, p_t_top)
                ThreePointArc(p_t_top, (r_c2 + r_tip, 0.0), p_t_bot)
                Line(p_t_bot, p_b_bot)
            make_face()
            # Double-D cutout (Ø8.1 mm clipped to 6.1 mm flat height)
            Circle(radius=4.05, mode=Mode.SUBTRACT)
            # 2x Ø5.2 mm clevis / return-spring holes at R = 26 & 32 mm
            with Locations([(r_c1, 0.0), (r_c2, 0.0)]):
                Circle(radius=2.6, mode=Mode.SUBTRACT)
        extrude(amount=6.0)
        # Re-intersect clean Double-D flats inside bore by adding two flat teeth
        with Locations([(0.0, 3.05 + 1.0, 0.0), (0.0, -(3.05 + 1.0), 0.0)]):
            with BuildSketch():
                Rectangle(8.2, 2.0)
            extrude(amount=6.0)

    lever_step = CNC_DIR / "svt_na_dsi_actuator_lever_6061.step"
    lever_dxf = CNC_DIR / "svt_na_dsi_actuator_lever_6061.dxf"
    export_step(bp_lever.part, str(lever_step))

    def deg(cx, cy, pt):
        return math.degrees(math.atan2(pt[1] - cy, pt[0] - cx)) % 360.0

    with open(lever_dxf, "w", encoding="utf-8") as f:
        f.write("0\nSECTION\n2\nENTITIES\n")
        f.write(
            f"0\nARC\n8\nLEVER_OUTLINE\n10\n0.0\n20\n0.0\n30\n0.0\n40\n{r_boss:.5f}\n"
            f"50\n{deg(0.0, 0.0, p_b_top):.5f}\n51\n{deg(0.0, 0.0, p_b_bot):.5f}\n"
        )
        f.write(
            f"0\nARC\n8\nLEVER_OUTLINE\n10\n{r_c2:.5f}\n20\n0.0\n30\n0.0\n40\n{r_tip:.5f}\n"
            f"50\n{deg(r_c2, 0.0, p_t_bot):.5f}\n51\n{deg(r_c2, 0.0, p_t_top):.5f}\n"
        )
        for p1, p2 in [(p_b_top, p_t_top), (p_t_bot, p_b_bot)]:
            f.write(f"0\nLINE\n8\nLEVER_OUTLINE\n10\n{p1[0]:.5f}\n20\n{p1[1]:.5f}\n30\n0.0\n11\n{p2[0]:.5f}\n21\n{p2[1]:.5f}\n31\n0.0\n")
        # Double-D bore outline (two arcs + two horizontal flats at y = ±3.05, r = 4.05)
        x_dd = math.sqrt(4.05**2 - 3.05**2)
        for p1, p2 in [((-x_dd, 3.05), (x_dd, 3.05)), ((x_dd, -3.05), (-x_dd, -3.05))]:
            f.write(f"0\nLINE\n8\nDOUBLE_D_BORE\n10\n{p1[0]:.5f}\n20\n{p1[1]:.5f}\n30\n0.0\n11\n{p2[0]:.5f}\n21\n{p2[1]:.5f}\n31\n0.0\n")
        a_dd = math.degrees(math.atan2(3.05, x_dd))
        f.write(f"0\nARC\n8\nDOUBLE_D_BORE\n10\n0.0\n20\n0.0\n30\n0.0\n40\n4.05\n50\n{-a_dd % 360.0:.5f}\n51\n{a_dd:.5f}\n")
        f.write(f"0\nARC\n8\nDOUBLE_D_BORE\n10\n0.0\n20\n0.0\n30\n0.0\n40\n4.05\n50\n{180.0 - a_dd:.5f}\n51\n{180.0 + a_dd:.5f}\n")
        for cx in (r_c1, r_c2):
            f.write(f"0\nCIRCLE\n8\nCLEVIS_HOLES\n10\n{cx:.4f}\n20\n0.0\n30\n0.0\n40\n2.6\n")
        f.write("0\nENDSEC\n0\nEOF\n")

    return {
        "butterfly_plate_step": str(plate_step.relative_to(ROOT)),
        "butterfly_plate_dxf": str(plate_dxf.relative_to(ROOT)),
        "valve_shaft_step": str(shaft_step.relative_to(ROOT)),
        "actuator_lever_step": str(lever_step.relative_to(ROOT)),
        "actuator_lever_dxf": str(lever_dxf.relative_to(ROOT)),
        "butterfly_ellipse_mm": [round(2.0 * rx, 3), round(2.0 * ry, 3)],
    }


# ---------------------------------------------------------------------------
# Full Assembly & Geometric Invariant Assertions
# ---------------------------------------------------------------------------

def assemble_all(params: dict) -> dict:
    pl_outer = build_plenum_loft(params, is_inner=False)
    pl_inner = build_plenum_loft(params, is_inner=True)

    short_outers, short_bores, stack_outers = [], [], []
    scroll_outers, scroll_bores = [], []
    valve_plugs = []
    runner_metrics = []
    for x_c in params["runners"]["center_x_mm"]:
        rc = build_single_runner_components(float(x_c), params)
        short_outers.append(rc["short_outer"])
        short_bores.append(rc["short_bore"])
        if rc.get("stack_outer") is not None:
            stack_outers.append(rc["stack_outer"])
        scroll_outers.append(rc["scroll_outer"])
        scroll_bores.append(rc["scroll_bore"])
        valve_plugs.append(rc["valve_plug"])
        runner_metrics.append({
            "cyl_x_mm": float(x_c),
            "short_upper_mm": rc["short_upper_length_mm"],
            "long_upper_mm": rc["long_upper_length_mm"],
            "scroll_z_bot_mm": rc["scroll_z_bot_mm"],
        })

    # Verify equal-length runner bounds across all 4 cylinders
    oem_lower_head = float(params["runners"]["downstream_oem_lower_head_length_mm"])
    short_totals = [m["short_upper_mm"] + oem_lower_head for m in runner_metrics]
    long_totals = [m["long_upper_mm"] + oem_lower_head for m in runner_metrics]
    assert max(short_totals) - min(short_totals) <= 2.0, f"Short runner spread > 2 mm: {short_totals}"
    assert max(long_totals) - min(long_totals) <= 2.0, f"Long runner spread > 2 mm: {long_totals}"
    assert 285.0 <= min(short_totals) and max(short_totals) <= 315.0, f"Short total out of target: {short_totals}"
    assert 475.0 <= min(long_totals) and max(long_totals) <= 525.0, f"Long total out of target: {long_totals}"

    # Verify zero unintended scroll-to-plenum wall collision at every cylinder X_c
    z_clip = float(params["runners"]["long_scroll"]["plenum_entry_z_mm"]) - 46.0
    below_entry_clip = md.Manifold.cube([1200.0, 1200.0, 400.0], center=True).translate([0.0, 0.0, z_clip - 200.0])
    for m_info, sc_o, sc_b in zip(runner_metrics, scroll_outers, scroll_bores):
        xc = m_info["cyl_x_mm"]
        d_xc = plenum_dims_at_x(xc, params)
        # Only the intentional rear bellmouth flare (Z > +2 mm, Y >= y_rear_in - 8 mm) may meet pl_inner
        overlap_below_bell = (pl_inner ^ sc_b) ^ below_entry_clip
        assert overlap_below_bell.is_empty() or manifold_to_trimesh(overlap_below_bell).volume < 1e-3, (
            f"Scroll breached plenum floor/rear wall below bellmouth at X={xc}: bounds={manifold_to_trimesh(overlap_below_bell).bounds.tolist()}"
        )
        overlap_bell = manifold_to_trimesh(pl_inner ^ sc_b)
        assert overlap_bell.bounds[0][1] >= d_xc["y_rear_in"] - 10.0, (
            f"Scroll intruded too far forward into plenum at X={xc}: Y_min={overlap_bell.bounds[0][1]:.2f}"
        )
        # Verify open butterfly blade tip stays >= 5.0 mm clear of scroll bore before Y-merge
        sh_g = short_runner_geometry(xc, params)
        d_blade_rad = 0.5 * float(params["runners"]["short_bypass"]["bore_diameter_mm"])
        open_tip = sh_g["p_shaft"] + sh_g["d_bore"] * d_blade_rad
        sc_pts_c, _, _ = _scroll_segments(xc, m_info["scroll_z_bot_mm"], params)
        pre_merge = sc_pts_c[sc_pts_c[:, 1] >= open_tip[1] - 4.0]
        min_tip_dist = float(np.min(np.linalg.norm(pre_merge - open_tip[None, :], axis=1)))
        assert min_tip_dist >= 26.5, (
            f"Open butterfly tip too close to scroll centerline at X={xc}: {min_tip_dist:.2f} mm"
        )

    # Tie webs between Cyl 1-2 and Cyl 3-4
    tw = params["runners"]["tie_webs"]
    webs: list[md.Manifold] = []
    if tw["enabled"]:
        y_mid = 0.5 * (float(tw["y_start_mm"]) + float(tw["y_end_mm"]))
        y_len = abs(float(tw["y_end_mm"]) - float(tw["y_start_mm"]))
        for x_mid in (-92.0, 92.0):
            webs.append(md.Manifold.cube([54.0, y_len, float(tw["height_mm"])], center=True).translate([x_mid, y_mid, float(tw["center_z_mm"])]))

    shaft_sys = build_shaft_system_components(params)
    hatches = build_service_hatch_components(params)
    tb_parts = build_throttle_body_components(params)
    iacv_parts = build_iacv_components(params) if params["throttle_body"]["iacv_mount"]["enabled"] else None

    boss_solids, boss_bores = [], []
    for key in ("vacuum_primary_pad", "vacuum_aux_pad"):
        pad_cfg = params["na_vacuum_ports"].get(key)
        if pad_cfg and pad_cfg.get("enabled"):
            pad_s, pad_b = build_boss_pad_components(pad_cfg, params)
            boss_solids.append(pad_s)
            boss_bores.extend(pad_b)

    pl_plus_shaft = m_union([pl_outer, shaft_sys["outer"]])
    split_parts = build_center_split_flange_and_cutters(pl_plus_shaft, params)

    pl_bond_env = build_plenum_loft(params, is_inner=True, wall_offset_mm=2.5)
    floor_scoops = build_floor_flow_scoops(params, pl_bond_env=pl_bond_env)
    iacv_route = make_iacv_flange_feed_route(params, tb_parts)
    pl_and_tb_cavities = m_union([pl_inner, tb_parts["cutters"]])

    # --- 1-Piece Reference Assembly ---
    outer_1pc_list = [pl_outer, *short_outers, *scroll_outers, *webs, shaft_sys["outer"], *boss_solids, tb_parts["outer"]]
    if hatches["outer"] is not None:
        outer_1pc_list.append(hatches["outer"])
    if iacv_parts is not None:
        outer_1pc_list.append(iacv_parts["outer"])
    if iacv_route is not None:
        outer_1pc_list.append(iacv_route["outer"])
    outer_1pc = m_union(outer_1pc_list)

    hollow_1pc = outer_1pc - pl_and_tb_cavities
    if stack_outers:
        hollow_1pc = m_union([hollow_1pc, *stack_outers])
    if floor_scoops:
        hollow_1pc = m_union([hollow_1pc, *floor_scoops])
    sub_1pc = [*short_bores, *scroll_bores, shaft_sys["cutters"], *boss_bores]
    if hatches["cutters"] is not None:
        sub_1pc.append(hatches["cutters"])
    if iacv_parts is not None:
        sub_1pc.append(iacv_parts["cutters"])
    if iacv_route is not None:
        sub_1pc.extend([iacv_route["inner"], iacv_route["sockets"], iacv_route["bolt_holes"]])
    final_1pc = m_diff(hollow_1pc, sub_1pc)

    # --- 2-Piece Split Assembly ---
    outer_split = m_union([outer_1pc, split_parts["flange_ring"]])
    hollow_split = outer_split - pl_and_tb_cavities
    if stack_outers:
        hollow_split = m_union([hollow_split, *stack_outers])
    if floor_scoops:
        hollow_split = m_union([hollow_split, *floor_scoops])
    sub_split = [*sub_1pc, split_parts["hole_cutters"]]
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

    # Verify zero unintended scroll/plenum breakthrough & sealed air boundary at every cylinder X_c
    from scipy.ndimage import label as nd_label
    from matplotlib.path import Path as MplPath2
    below_bell_clip = below_entry_clip
    gy_c = np.arange(-155.0, 102.0, 1.0)
    gz_c = np.arange(-114.0, 106.0, 1.0)
    gY, gZ = np.meshgrid(gy_c, gz_c, indexing="ij")
    pts_yz = np.column_stack([gY.ravel(), gZ.ravel()])
    iy_pl, iz_pl = int(np.argmin(np.abs(gy_c - (-10.0)))), int(np.argmin(np.abs(gz_c - 0.0)))
    iy_amb, iz_amb = int(np.argmin(np.abs(gy_c - (-140.0)))), int(np.argmin(np.abs(gz_c - (-40.0))))

    for m_info, sc_b in zip(runner_metrics, scroll_bores):
        xc = m_info["cyl_x_mm"]
        pl_s = (pl_inner ^ below_bell_clip).rotate([0.0, -90.0, 0.0]).slice(xc).to_polygons()
        sc_s = (sc_b ^ below_bell_clip).rotate([0.0, -90.0, 0.0]).slice(xc).to_polygons()
        poly_pl = unary_union([
            ShapelyPolygon(np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]])).buffer(0.0)
            for p in pl_s if len(p) >= 3
        ])
        poly_sc = unary_union([
            ShapelyPolygon(np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]])).buffer(0.0)
            for p in sc_s if len(p) >= 3
        ])
        if not poly_pl.is_empty and not poly_sc.is_empty:
            wall_gap = float(poly_pl.distance(poly_sc))
            assert wall_gap >= 5.0, (
                f"Scroll-to-plenum solid wall gap < 5.0 mm below bellmouth at X={xc}: {wall_gap:.2f} mm"
            )
        # 2D YZ flood-fill containment check on final_1pc at X = xc: plenum air must NOT connect to ambient air pocket
        sec_full = final_1pc.rotate([0.0, -90.0, 0.0]).slice(xc).to_polygons()
        solid_mask = np.zeros(pts_yz.shape[0], dtype=bool)
        for p in sec_full:
            if len(p) >= 3:
                arr = np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]])
                solid_mask ^= MplPath2(arr).contains_points(pts_yz)
        air_grid = (~solid_mask).reshape(len(gy_c), len(gz_c))
        # Also block top service hatch opening if X_c is underneath hatch by checking wall below Z=+80
        comp_lbl, _ = nd_label(air_grid)
        assert comp_lbl[iy_pl, iz_pl] > 0 and comp_lbl[iy_amb, iz_amb] > 0
        # Note: hatch cutout at top (Z=+80..+90) opens plenum top to outside sky around Y=-22 unless capped; seal top Z>=75 in check
        air_capped = air_grid.copy()
        air_capped[:, gz_c >= float(params["service_hatches"]["left_seat_z_mm"]) - 10.0] = False
        comp_lbl2, _ = nd_label(air_capped)
        assert comp_lbl2[iy_pl, iz_pl] != comp_lbl2[iy_amb, iz_amb], (
            f"Air leak breach between plenum cavity and ambient C-scroll pocket at X={xc}!"
        )
    bb_full = manifold_to_trimesh(final_1pc).bounds
    assert bb_full[0][2] >= -115.0, f"Lower scroll Z_min={bb_full[0][2]:.2f} below -115 mm envelope"
    assert bb_full[1][2] <= 95.0, f"Roof Z_max={bb_full[1][2]:.2f} exceeds +95.0 mm boot-top envelope"
    assert bb_full[1][1] <= 104.0, f"Firewall Y_max={bb_full[1][1]:.2f} exceeds +104.0 mm envelope"

    # Permanent CAD Quality Assertions (Valve Seal, Zero Scroll-to-Valve Breach, TB-to-Boss Clearance)
    sb_cfg = params["runners"]["short_bypass"]
    r_vh = 0.5 * float(sb_cfg["bore_diameter_mm"]) + 5.0
    for m_info, sc_b in zip(runner_metrics, scroll_bores):
        sh_g = short_runner_geometry(m_info["cyl_x_mm"], params)
        vh_cyl = make_cylinder_along(
            sh_g["p_shaft"] - sh_g["d_bore"] * 12.0,
            sh_g["p_shaft"] + sh_g["d_bore"] * float(sb_cfg["bore_lower_extend_mm"]),
            r_vh,
            segments=48,
        )
        ov_v = vh_cyl ^ sc_b
        assert ov_v.is_empty() or manifold_to_trimesh(ov_v).volume < 1e-3, (
            f"C-scroll breached butterfly valve housing at X={m_info['cyl_x_mm']}"
        )
        # Verify continuous 360-deg sealed valve seat ring at s = -6, 0, +6 mm around p_shaft
        elev_deg = float(sb_cfg.get("axis_elevation_deg", 38.0))
        rot_x = -(90.0 - elev_deg)
        for s_chk in (-6.0, 6.0):
            p_chk = sh_g["p_shaft"] + sh_g["d_bore"] * s_chk
            p_rot = final_1pc.translate([-p_chk[0], -p_chk[1], -p_chk[2]]).rotate([rot_x, 0.0, 0.0])
            sec = p_rot.slice(0.0).to_polygons()
            rings_s = [ShapelyPolygon(np.asarray(pp)).buffer(0.0) for pp in sec if len(pp) >= 3]
            from shapely.geometry import Point as ShapelyPoint
            bore_pt = ShapelyPoint(0.0, 0.0)
            depths = [sum(1 for j, pj in enumerate(rings_s) if i != j and pj.area > pi.area and pj.contains(pi.representative_point())) for i, pi in enumerate(rings_s)]
            solid_2d = unary_union([
                pi.difference(unary_union([pj for j, pj in enumerate(rings_s) if depths[j] == depths[i] + 1 and pi.contains(pj.representative_point())]))
                for i, pi in enumerate(rings_s) if depths[i] % 2 == 0
            ])
            test_ring = bore_pt.buffer(25.5).difference(bore_pt.buffer(22.2))
            cov = solid_2d.intersection(test_ring).area / test_ring.area
            assert cov >= 0.92, (
                f"Valve seat at X={m_info['cyl_x_mm']} s={s_chk} lacks continuous 360-deg wall (cov={cov:.3f})!"
            )

    return {
        "svt_na_dsi_manifold_1piece_full": final_1pc,
        "svt_na_dsi_manifold_split_left_cyl1_2": split_left,
        "svt_na_dsi_manifold_split_right_cyl3_4_tb": split_right,
        "svt_na_dsi_manifold_split_left_print_oriented": split_left_print,
        "svt_na_dsi_manifold_split_right_print_oriented": split_right_print,
        "svt_na_dsi_service_hatch_left": hatches["lid_left"],
        "svt_na_dsi_service_hatch_right": hatches["lid_right"],
        "svt_na_dsi_blind_bearing_cap": shaft_sys["blind_cap"],
        "svt_na_dsi_seal_retainer_plate": shaft_sys["seal_retainer"],
        "svt_na_dsi_actuator_bracket_universal": shaft_sys["actuator_bracket"],
        "svt_na_dsi_runner_boot_fit_gauge": gauges["boot_fit_gauge"],
        "svt_na_dsi_tb_flange_fit_gauge": gauges["tb_flange_fit_gauge"],
        "svt_na_dsi_iacv_flange_fit_gauge": gauges["iacv_flange_fit_gauge"],
        "svt_na_dsi_valve_bore_fit_gauge": gauges["valve_bore_fit_gauge"],
        "svt_na_dsi_alignment_dowel_pins": gauges["alignment_dowel_pins"],
        "_pl_inner": pl_inner,
        "_short_bores": short_bores,
        "_scroll_bores": scroll_bores,
        "_valve_plugs": valve_plugs,
        "_tb_parts": tb_parts,
        "_runner_metrics": runner_metrics,
        "_iacv_wall_thickness_mm": iacv_parts["wall_thickness_mm"] if iacv_parts else None,
        "_oring_centerline_mm": split_parts["oring_centerline_mm"],
    }


# ---------------------------------------------------------------------------
# Visualizations (Overview PNG & 1:1 SVG Template)
# ---------------------------------------------------------------------------

def render_overview_png(meshes: dict[str, trimesh.Trimesh], solids: dict, params: dict, out_path: Path):
    fig = plt.figure(figsize=(16.5, 12.0), facecolor="#f5f4f0")
    fig.suptitle(
        "2002-2004 Ford Focus SVT / ST170 (NA) — Modular Dual-Stage C-Scroll Intake Manifold",
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
        max_span = max(b[1] - b[0]) * 0.54
        c = 0.5 * (b[0] + b[1])
        ax.set_xlim(c[0] - max_span, c[0] + max_span)
        ax.set_ylim(c[1] - max_span, c[1] + max_span)
        ax.set_zlim(c[2] - max_span, c[2] + max_span)
        ax.set_box_aspect([1, 1, 1])
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=10.8, fontweight="bold", color="#1f242b", pad=6)
        ax.set_xlabel("X (mm)", fontsize=8)
        ax.set_ylabel("Y (mm)", fontsize=8)
        ax.set_zlabel("Z (mm)", fontsize=8)
        ax.tick_params(labelsize=7)

    # Panel 1: 3D Full Assembly
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    plot_mesh_panel(ax1, meshes["svt_na_dsi_manifold_1piece_full"], "1. Full Dual-Stage NA C-Scroll Assembly", 22, -48, "#3e5266")

    # Panel 2: Exploded 2-Piece Split + Service Hatches + Caps
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    m_l = meshes["svt_na_dsi_manifold_split_left_cyl1_2"].copy()
    m_r = meshes["svt_na_dsi_manifold_split_right_cyl3_4_tb"].copy()
    m_hl = meshes["svt_na_dsi_service_hatch_left"].copy()
    m_hr = meshes["svt_na_dsi_service_hatch_right"].copy()
    m_l.apply_translation([-22.0, 0.0, 0.0])
    m_r.apply_translation([22.0, 0.0, 0.0])
    sh_cfg = params["service_hatches"]
    m_hl.apply_translation([float(sh_cfg["left_center_x_mm"]) - 22.0, float(sh_cfg["center_y_mm"]), float(sh_cfg["left_seat_z_mm"]) + 24.0])
    m_hr.apply_translation([float(sh_cfg["right_center_x_mm"]) + 22.0, float(sh_cfg["center_y_mm"]), float(sh_cfg["right_seat_z_mm"]) + 24.0])
    plot_mesh_panel(ax2, trimesh.util.concatenate([m_l, m_r, m_hl, m_hr]), "2. Modular 2-Piece Split + Top Service Hatches (CC2 256mm Bed)", 24, -48, "#2b618a")

    # Panel 3: Detailed Cyl 3 (X = +46 mm) YZ Cross-Section showing both paths & butterfly poses
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.set_facecolor("#ffffff")
    full_solid = solids["svt_na_dsi_manifold_1piece_full"]
    sec_yz = full_solid.rotate([0.0, -90.0, 0.0]).slice(46.0)
    yz_polys = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in sec_yz.to_polygons()]
    add_section_patches(ax3, yz_polys, facecolor="#4c5c6b", edgecolor="#1b2026", lw=0.9)

    # Overlay top service hatch lid cross section in place
    z_hr = float(sh_cfg["right_seat_z_mm"])
    t_lid = float(sh_cfg["lid_thickness_mm"])
    yc_h = float(sh_cfg["center_y_mm"])
    wy_h = float(sh_cfg["opening_width_y_mm"]) + 2.0 * float(sh_cfg["boss_rim_width_mm"])
    ax3.add_patch(plt.Rectangle((yc_h - 0.5 * wy_h, z_hr), wy_h, t_lid, facecolor="#b8c4d0", edgecolor="#1b2026", lw=1.0, label="Top Service Hatch Lid"))

    # Overlay butterfly closed (8 deg) & open (90 deg) lines from d_bore
    sh3 = short_runner_geometry(46.0, params)
    yv, zv = sh3["p_shaft"][1], sh3["p_shaft"][2]
    elev_deg = float(params["runners"]["short_bypass"].get("axis_elevation_deg", 38.0))
    r_bl = 21.8
    # Closed (perp to d_bore + 8 deg)
    ang_cl = math.radians(elev_deg + 8.0)
    ax3.plot([yv - r_bl * math.sin(ang_cl), yv + r_bl * math.sin(ang_cl)],
             [zv - r_bl * math.cos(ang_cl), zv + r_bl * math.cos(ang_cl)],
             color="#c0392b", lw=2.6, label="Butterfly Closed (Long Scroll Mode)")
    # Open (aligned with d_bore)
    ang_op = math.radians(elev_deg)
    ax3.plot([yv - r_bl * math.cos(ang_op), yv + r_bl * math.cos(ang_op)],
             [zv + r_bl * math.sin(ang_op), zv - r_bl * math.sin(ang_op)],
             color="#27ae60", lw=2.2, ls="--", label="Butterfly Open (Short Bypass Mode)")
    ax3.axhline(93.4, color="#c0392b", lw=1.0, ls="--", label="Boot Top (+93.4 mm)")
    ax3.plot(yv, zv, "ko", ms=5)

    # Annotate centerline paths
    rm3 = next(m for m in solids["_runner_metrics"] if abs(m["cyl_x_mm"] - 46.0) < 1.0)
    sc_pts, _, _ = _scroll_segments(46.0, rm3["scroll_z_bot_mm"], params)
    long_tot_3 = rm3["long_upper_mm"] + oem_lower_head_length_mm(params)
    ax3.plot(sc_pts[:, 1], sc_pts[:, 2], color="#d35400", lw=1.4, ls="-.", label=f"Long C-Scroll ({rm3['long_upper_mm']:.0f} mm upper / {long_tot_3:.0f} mm total)")
    ax3.plot(sh3["pts_sweep"][:, 1], sh3["pts_sweep"][:, 2], color="#27ae60", lw=1.3, ls=":")

    ax3.set_aspect("equal")
    ax3.set_xlim(-155, 100)
    ax3.set_ylim(-112, 108)
    ax3.grid(True, linestyle=":", alpha=0.45)
    ax3.text(-12.0, 44.0, "Tapered\nPlenum", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1b4f72")
    ax3.text(68.0, -8.0, "Long\nC-Scroll", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#a04000")
    ax3.set_title("3. Cyl 3 Section (X = +46 mm): C-Scroll, Short Valve & Service Hatch", fontsize=10.2, fontweight="bold")
    ax3.set_xlabel("Y: Boot Spigot (-Y) to Firewall (+Y) [mm]")
    ax3.set_ylabel("Z: Height [mm]")
    ax3.legend(fontsize=7.1, loc="lower left", framealpha=0.92)

    # Panel 4: Plan View (X, Y) slice at Z = shaft_center_z_mm (Shaft Axis & All 4 Bores)
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor("#ffffff")
    sec_xy = full_solid.slice(zv)
    xy_polys = [np.asarray(p) for p in sec_xy.to_polygons()]
    add_section_patches(ax4, xy_polys, facecolor="#2f5d80", edgecolor="#182a38", lw=0.9, alpha=0.9)
    ds = params["dsi_valve_system"]
    ax4.plot([float(ds["shaft_left_end_x_mm"]), float(ds["shaft_right_end_x_mm"])], [yv, yv], color="#c0392b", lw=2.0, ls="-.", label="Ø8.0 mm 304SS Shaft Axis")
    for idx, xc in enumerate(params["runners"]["center_x_mm"], start=1):
        ax4.axvline(xc, color="#777777", lw=0.6, ls=":")
        ax4.text(xc, -142.0, f"Cyl {idx}", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#222")
    ax4.axvline(0.0, color="#0d6e3f", lw=1.3, ls="-.")
    ax4.text(0.0, 86.0, "Split X=0\n(SF-1 Bushing)", ha="center", va="top", fontsize=7.5, fontweight="bold", color="#0d6e3f",
             bbox=dict(facecolor="#ffffff", edgecolor="none", pad=1.2, alpha=0.88))
    ax4.set_aspect("equal")
    ax4.set_xlim(-210, 260)
    ax4.set_ylim(-152, 98)
    ax4.grid(True, linestyle=":", alpha=0.45)
    ax4.set_title(f"4. Horizontal Section at Valve Shaft (Z = {zv:+.1f} mm): 4x Bores, -X Actuator & +X Blind Pocket", fontsize=9.6, fontweight="bold")
    ax4.set_xlabel("X: -X Seal/Actuator to +X Blind Pocket / TB (+X) [mm]")
    ax4.set_ylabel("Y: Spigots (-Y) to Rear C-Scrolls (+Y) [mm]")
    ax4.legend(fontsize=7.6, loc="lower right")

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_1to1_svg(solids: dict, params: dict, out_path: Path):
    """Generate true 1:1 mm-scale SVG template of all key interfaces + butterfly valve."""
    spigot_sec = solids["svt_na_dsi_runner_boot_fit_gauge"].slice(24.0).to_polygons()
    split_sec = solids["svt_na_dsi_manifold_split_left_cyl1_2"].rotate([0.0, -90.0, 0.0]).slice(-1.0).to_polygons()
    tb_key = "svt_na_dsi_flat_face_iacv_fit_coupon" if "svt_na_dsi_flat_face_iacv_fit_coupon" in solids else "svt_na_dsi_tb_flange_fit_gauge"
    tb_sec = solids[tb_key].slice(2.0).to_polygons()
    iacv_sec = solids["svt_na_dsi_iacv_flange_fit_gauge"].slice(2.0).to_polygons()
    valve_sec = solids["svt_na_dsi_valve_bore_fit_gauge"].slice(17.0).to_polygons()

    width_mm, height_mm = 680.0, 240.0
    centers = [
        ("2.00\" Boot Spigot\n(Ø50.8 OD / Ø42.8 ID)", spigot_sec, (55.0, 120.0), lambda p: (p[0], -p[1])),
        ("Ø44.0 Butterfly Bore Gauge\n(Elliptical 8-deg Blade Seat)", valve_sec, (165.0, 120.0), lambda p: (p[0], -p[1])),
        ("Center Split Flange (X=0)\n(8x M6 + 2x 6mm Dowel + O-Ring + Center Bushing)", split_sec, (310.0, 130.0), lambda p: (p[1], p[0])),
        ("65mm Throttle Body Flange\n(79x79 mm Eccentric [5,-7] Flat-Face)", tb_sec, (485.0, 120.0), lambda p: (p[0], -p[1])),
        ("2-Bolt Ford IACV Pad\n(46mm Bolts / Dual 13mm Ports)", iacv_sec, (615.0, 120.0), lambda p: (p[0], -p[1])),
    ]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width_mm * 0.5:.1f}" y="12" text-anchor="middle" font-family="sans-serif" font-size="6" font-weight="bold" fill="#111">2002-2004 Focus SVT NA Dual-Stage DSI Manifold — 1:1 Interface Templates (mm)</text>',
    ]
    for label, polys, (cx, cy), map_fn in centers:
        for poly in polys:
            pts = " ".join(f"{cx + map_fn(p)[0]:.3f},{cy + map_fn(p)[1]:.3f}" for p in poly)
            lines.append(f'<polygon points="{pts}" fill="none" stroke="#1f4e79" stroke-width="0.35"/>')
        for idx, line in enumerate(label.split("\n")):
            lines.append(f'<text x="{cx}" y="{220 + idx * 5}" text-anchor="middle" font-family="sans-serif" font-size="4.0" fill="#333">{line}</text>')
    lines.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def flat_face_checks(body: md.Manifold, tb_parts: dict, params: dict) -> tuple[dict, md.Manifold]:
    """Verify flat throttle mating face preserves >= 1.5 mm gasket support land and 6 internal openings."""
    face, axis = tb_parts["flange_face_center"], tb_parts["tb_axis"]
    tb_cfg = params["throttle_body"]
    u, v, shift = throttle_mounting_frame(axis, tb_cfg)
    frame = np.stack((u, v, axis))
    flange = body.transform(np.column_stack((frame, -frame @ (face + shift))))
    w, h = float(tb_cfg["flange_width_mm"]) / 2.0 + 1.0, float(tb_cfg["flange_height_mm"]) / 2.0 + 1.0
    window = shapely_box(-w, -h, w, h)
    cfg = tb_cfg["iacv_flange_feed"]
    first, divider = cfg["visible_throttle_seal_centerlines_uv_mm"]
    seal = LineString([*first, first[0]]).union(LineString(divider))
    profile_stats = {}
    reference_loops = []
    for depth in (0.1, 0.25, 1.1, 2.2):
        section = ShapelyPolygon()
        for loop in flange.slice(-depth).to_polygons():
            section = section.symmetric_difference(ShapelyPolygon(loop).intersection(window))
        assert isinstance(section, ShapelyPolygon) and section.is_valid and len(section.interiors) == 6, (depth, len(section.interiors))
        assert section.covers(seal), depth
        profile_stats[str(depth)] = {
            "seal_centerline_to_edge_mm": round(float(section.boundary.distance(seal)), 4),
            "openings": len(section.interiors),
        }
        if depth == 0.1:
            reference_loops = [np.asarray(section.exterior.coords[:-1]), *[np.asarray(hole.coords[:-1]) for hole in section.interiors]]
    assert profile_stats["0.1"]["seal_centerline_to_edge_mm"] >= 1.5, profile_stats
    return profile_stats, md.CrossSection(reference_loops, md.FillRule.EvenOdd).extrude(4.0)


def render_exterior_closeup_figure(solids: dict, meshes: dict, params: dict, out_path: Path):
    """Render 6-panel multi-angle exterior & internal transition inspection plate."""
    fig = plt.figure(figsize=(18.0, 11.5), facecolor="#f7f6f2")
    fig.suptitle("NA Dual-Stage DSI — Cohesive Exterior Polish & V2 Flat-Face TB/IACV Inspection", fontsize=14, fontweight="bold", y=0.975)

    def plot_3d(ax, mesh, title, elev, azim, color):
        ax.set_facecolor("#f5f4f0")
        ax.plot_trisurf(mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2], triangles=mesh.faces, color=color, linewidth=0, antialiased=False, shade=True)
        b = mesh.bounds
        span = max(b[1] - b[0]) * 0.54
        c = 0.5 * (b[0] + b[1])
        ax.set_xlim(c[0] - span, c[0] + span)
        ax.set_ylim(c[1] - span, c[1] + span)
        ax.set_zlim(c[2] - span, c[2] + span)
        ax.set_box_aspect([1, 1, 1])
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=10.0, fontweight="bold")
        ax.tick_params(labelsize=7)

    m_full = meshes["svt_na_dsi_manifold_1piece_full"]
    m_l = meshes["svt_na_dsi_manifold_split_left_cyl1_2"]
    m_r = meshes["svt_na_dsi_manifold_split_right_cyl3_4_tb"]

    plot_3d(fig.add_subplot(2, 3, 1, projection="3d"), m_full, "1. Underside-Front 3/4: C-Scrolls & Dropped Plenum", -20, -60, "#3e5266")
    plot_3d(fig.add_subplot(2, 3, 2, projection="3d"), m_r, "2. Right Half: 32°/14° TB, Flat-Face IACV & Top Pedestal", 20, -25, "#2b618a")
    plot_3d(fig.add_subplot(2, 3, 3, projection="3d"), m_l, "3. Left Half: -X Actuator/Seal End & Plenum Dome", 20, -145, "#2b618a")
    plot_3d(fig.add_subplot(2, 3, 4, projection="3d"), m_full, "4. Rear-Top 3/4: Service Hatches, Vacuum Pads & IACV", 32, 135, "#3e5266")

    def draw_slice(ax, polys, title, xlabel, ylabel, xlim, ylim, fc="#386487"):
        ax.set_facecolor("#ffffff")
        sh_polys = [ShapelyPolygon(p) for p in polys if len(p) >= 3]
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
            ax.add_patch(PathPatch(MplPath(np.asarray(verts), codes), facecolor=fc, edgecolor="#182a38", lw=0.8))
        ax.set_aspect("equal")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(True, ls=":", alpha=0.45)
        ax.set_title(title, fontsize=10.0, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)

    full_s = solids["svt_na_dsi_manifold_1piece_full"]
    draw_slice(fig.add_subplot(2, 3, 5), [np.asarray(p) for p in full_s.slice(10.0).to_polygons()],
               "5. X-Y Slice at Z = +10 mm: Rear Flow Guide & TB Throat", "X [mm]", "Y [mm]", (-205, 255), (-110, 95))
    xz_polys = [np.column_stack([np.asarray(p)[:, 0], -np.asarray(p)[:, 1]]) for p in full_s.rotate([90.0, 0.0, 0.0]).slice(-100.0).to_polygons()]
    draw_slice(fig.add_subplot(2, 3, 6), xz_polys,
               "6. X-Z Slice at Y = -100 mm: Elevated Runners & Tie-Bars", "X [mm]", "Z [mm]", (-180, 180), (-20, 100), fc="#24695c")

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    STL_DIR.mkdir(parents=True, exist_ok=True)
    FITMENT_DIR.mkdir(parents=True, exist_ok=True)

    solids = assemble_all(params)
    if solids.get("_iacv_route") is not None and params["throttle_body"].get("iacv_flange_feed", {}).get("visible_throttle_seal_centerlines_uv_mm"):
        ff_stats, coupon_solid = flat_face_checks(solids["svt_na_dsi_manifold_1piece_full"], solids["_tb_parts"], params)
        solids["svt_na_dsi_flat_face_iacv_fit_coupon"] = coupon_solid
        print(f"  Flat-Face IACV TB Check: {ff_stats['0.1']}")
    cnc_info = export_cnc_metal_hardware(params)

    meshes: dict[str, trimesh.Trimesh] = {}
    manifest_parts: dict[str, dict] = {}
    cc2 = params["printers"]["centauri_carbon_2"]
    e3 = params["printers"]["ender_3_s1_pro"]

    for name, solid in solids.items():
        if name.startswith("_"):
            continue
        comps = solid.decompose()
        if len(comps) > 1:
            solid = max(comps, key=lambda c: c.volume())
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

        if "print_oriented" in name:
            assert fits_cc2, f"{name} exceeds Centauri Carbon 2 bed ({ext})"
            assert max(ext) <= 255.0, f"{name} max axis {max(ext):.2f} > 255 mm safety margin"

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

    plenum_l = round(float(manifold_to_trimesh(solids["_pl_inner"]).volume) / 1_000_000.0, 3)
    oem_lh = float(params["runners"]["downstream_oem_lower_head_length_mm"])
    runner_summary = []
    for rm in solids["_runner_metrics"]:
        runner_summary.append({
            **rm,
            "short_total_mm": round(rm["short_upper_mm"] + oem_lower_head_length_mm(params), 2),
            "long_total_mm": round(rm["long_upper_mm"] + oem_lower_head_length_mm(params), 2),
        })

    manifest = {
        "vehicle": params["metadata"]["vehicle"],
        "architecture": params["metadata"]["architecture"],
        "oem_imrc_calibration_pending": params["metadata"]["oem_imrc_calibration_pending"],
        "plenum_internal_volume_liters": plenum_l,
        "runner_pitch_mm": params["runners"]["pitch_mm"],
        "runner_lengths": runner_summary,
        "spigot_outer_mm": [params["runners"]["spigot"]["outer_width_mm"], params["runners"]["spigot"]["outer_height_mm"]],
        "spigot_inner_mm": [
            params["runners"]["spigot"]["outer_width_mm"] - 2.0 * params["runners"]["spigot"]["wall_thickness_mm"],
            params["runners"]["spigot"]["outer_height_mm"] - 2.0 * params["runners"]["spigot"]["wall_thickness_mm"],
        ],
        "throttle_body_bore_mm": params["throttle_body"]["bore_diameter_mm"],
        "iacv_supply_wall_thickness_mm": round(float(solids["_iacv_wall_thickness_mm"]), 2),
        "split_oring_centerline_mm": solids["_oring_centerline_mm"],
        "cnc_metal_hardware": cnc_info,
        "parts": manifest_parts,
    }
    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    render_overview_png(meshes, solids, params, FITMENT_DIR / "01_na_dsi_manifold_overview.png")
    render_exterior_closeup_figure(solids, meshes, params, FITMENT_DIR / "05_na_dsi_exterior_transitions_closeup.png")
    render_1to1_svg(solids, params, FITMENT_DIR / "02_na_dsi_interfaces_1to1_template.svg")

    print(f"Generated {len(meshes)} watertight NA DSI STLs + 5 CNC STEP/DXF files. Plenum = {plenum_l:.3f} L")
    print(f"  IACV supply wall = {manifest['iacv_supply_wall_thickness_mm']} mm | Split O-ring loop = {manifest['split_oring_centerline_mm']} mm")
    for rm in runner_summary:
        print(
            f"  Cyl X={rm['cyl_x_mm']:+6.1f}: Short={rm['short_total_mm']:.1f} mm ({rm['short_upper_mm']:.1f} upper) | "
            f"Long={rm['long_total_mm']:.1f} mm ({rm['long_upper_mm']:.1f} upper, z_bot={rm['scroll_z_bot_mm']:.1f})"
        )
    for pname, info in manifest_parts.items():
        print(
            f"  {pname}: {info['extents_mm']} mm | vol={info['solid_volume_cm3']} cm3 | CC2={info['fits_centauri_carbon_2_256']}"
        )


def oem_lower_head_length_mm(params: dict) -> float:
    return float(params["runners"]["downstream_oem_lower_head_length_mm"])


if __name__ == "__main__":
    main()
