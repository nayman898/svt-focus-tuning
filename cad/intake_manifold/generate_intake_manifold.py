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
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
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
    x0 = p["cyl1_end_x_mm"]
    x1 = p["cyl4_end_x_mm"]
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return float(p["taper_cyl1_area_ratio"] + (1.0 - p["taper_cyl1_area_ratio"]) * t)


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
    dome_steps = 12
    # Start at theta=0.22 rad (~12.6 deg) so end cap stays broad and smoothly closed
    thetas = np.linspace(0.22, math.pi * 0.5, dome_steps, endpoint=False)
    s_cyl1 = math.sqrt(p["taper_cyl1_area_ratio"])
    for th in thetas:
        x = x_cyl1 - dome_len * math.cos(th)
        dome_scale = math.sin(th) * s_cyl1
        uv = rounded_rect_points(w_base * dome_scale, h_base * dome_scale, r_base * dome_scale, n_pts)
        # In (X, Y, Z) with +X tangent: right-handed u=+Y, v=+Z => (x, u, v)
        ring = np.column_stack([np.full(n_pts, x), uv[:, 0], uv[:, 1]])
        rings.append(ring)

    # 2) Linearly tapered plenum barrel from x_cyl1 to x_cyl4
    xs = np.linspace(x_cyl1, x_cyl4, p["axial_segments"])
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


def build_single_runner_components(x_center: float, params: dict) -> dict[str, md.Manifold]:
    """
    For one cylinder at `x_center`, build:
      - `outer`: smooth swept outer runner + straight spigot clamping land + retention bead
      - `bellmouth_outer`: flared velocity-stack trumpet overlapping plenum wall and protruding inside
      - `inner_bore`: full continuous bore from flared bellmouth lip inside plenum to past spigot tip
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

    entry_d = sw["plenum_entry_diameter_mm"]
    entry_w_in = entry_d
    entry_h_in = entry_d - 6.0  # slightly oval (44 x 38 mm) for vertical plenum breathing margin
    entry_r_in = entry_h_in * 0.48
    entry_w_out = entry_w_in + 2.0 * wall
    entry_h_out = entry_h_in + 2.0 * wall
    entry_r_out = entry_r_in + wall

    tip_y = sp["tip_y_mm"]
    land_len = sp["land_length_mm"]
    sweep_end_y = tip_y + land_len
    sp_z = sp["center_z_mm"]

    # Curve points in (X, Y, Z) starting inside plenum wall (overlapping cleanly) -> sweep_end
    # Plenum rear inner wall is around Y = -42.4 (Cyl 1) to -48.0 (Cyl 4).
    # Place bellmouth entry tip at Y = -24.0, Z = -10.0 so top & bottom lips clear plenum walls generously
    p_bm_tip = np.array([x_center, -24.0, -10.0])
    # Direction into sweep: tilted ~18 deg downward from plenum toward rear
    inlet_dir = np.array([0.0, -math.cos(math.radians(18.0)), -math.sin(math.radians(18.0))])
    # Wall anchor inside plenum wall where sweep begins (overlapping plenum outer shell)
    p0 = p_bm_tip + inlet_dir * 16.0  # Starts at Y = -39.2, Z = -14.9 inside plenum wall
    p3 = np.array([x_center, sweep_end_y, sp_z])
    p1 = p0 + inlet_dir * 26.0
    p2 = p3 + np.array([0.0, 32.0, 0.0])  # enters spigot tangentially along -Y

    up_hint = np.array([0.0, 0.0, 1.0])
    # Wait: let's check u/v alignment!
    # At spigot: tangent = (0, -1, 0). up_hint = (0, 0, 1).
    # u_axis = up_hint x tangent = (0,0,1) x (0,-1,0) = (+1, 0, 0) -> X axis (width)!
    # v_axis = tangent x u_axis = (0,-1,0) x (1,0,0) = (0, 0, +1) -> Z axis (height)!
    # That matches outer_width_mm along X and outer_height_mm along Z!

    # 1) Outer runner sweep (from p0 to p3, then straight spigot land to tip_y with retention bead)
    outer_rings: list[np.ndarray] = []
    n_loft = sw["loft_segments"]
    for k in range(n_loft + 1):
        t = k / n_loft
        pt, tan = bezier_point_and_tangent(p0, p1, p2, p3, t)
        s_t = 0.5 - 0.5 * math.cos(math.pi * t)
        w = entry_w_out + (sp_w_out - entry_w_out) * s_t
        h = entry_h_out + (sp_h_out - entry_h_out) * s_t
        r = entry_r_out + (sp_r_out - entry_r_out) * s_t
        uv = rounded_rect_points(w, h, r, n_pts)
        outer_rings.append(ring_frame_points(pt, tan, up_hint, uv))

    # Straight spigot land from sweep_end_y to tip_y with boost retention bead
    bead_h = sp["retention_bead_height_mm"]
    bead_w = sp["retention_bead_width_mm"]
    bead_off = sp["retention_bead_offset_from_tip_mm"]
    # Stations measured back from tip_y toward sweep_end_y:
    # (y_from_tip, radial_expansion)
    y_bead_start = tip_y + bead_off
    y_bead_peak1 = y_bead_start + 1.5
    y_bead_peak2 = y_bead_start + bead_w - 1.5
    y_bead_end = y_bead_start + bead_w
    spigot_stations = [
        (y_bead_end + 4.0, 0.0),
        (y_bead_end, 0.0),
        (y_bead_peak2, bead_h),
        (y_bead_peak1, bead_h),
        (y_bead_start, 0.0),
        (tip_y, 0.0),
    ]
    tan_sp = np.array([0.0, -1.0, 0.0])
    for y_pos, dr in spigot_stations:
        uv = rounded_rect_points(sp_w_out + 2.0 * dr, sp_h_out + 2.0 * dr, sp_r_out + dr, n_pts)
        outer_rings.append(ring_frame_points(np.array([x_center, y_pos, sp_z]), tan_sp, up_hint, uv))

    outer_solid = trimesh_to_manifold(loft_closed_solid(outer_rings))

    # 2) Internal velocity-stack bellmouth outer solid
    # Starts 10 mm past p0 into the runner wall (so solid union is deep) and extends to p_bm_tip
    # Wait: let's sweep from p_bm_tip (inside plenum) -> p0 + 10*inlet_dir (inside plenum wall/runner)
    bm_len = bm["protrusion_into_plenum_mm"]
    bm_flare = bm["flare_radial_mm"]
    bm_wall = bm["wall_thickness_mm"]
    bm_rings: list[np.ndarray] = []

    p_bm_anchor = p0 + inlet_dir * 10.0  # inside runner stub
    # Flare curve from tip (p_bm_tip) back into wall (p_bm_anchor)
    # Use rounded lip profile at tip so the bellmouth edge is thick & printable
    bm_total_len = float(np.linalg.norm(p_bm_anchor - p_bm_tip))
    # Parametric stations from 0 (tip) to bm_total_len (anchor)
    # Flare mostly in the front 14 mm (`bm_len`)
    n_bm = 18
    for k in range(n_bm + 1):
        s_dist = (k / n_bm) * bm_total_len
        pos = p_bm_tip + inlet_dir * s_dist
        # Bellmouth flare decay: 1 at s_dist=0, 0 by s_dist >= bm_len
        u = np.clip(s_dist / bm_len, 0.0, 1.0)
        flare_factor = (1.0 - u) ** 2
        # Add smooth lip roll right at s_dist in [0, 2.5 mm]
        inner_flare = bm_flare * flare_factor
        # Outer profile tracks inner bore + wall + flare, tapering cleanly at tip
        w_out = entry_w_in + 2.0 * inner_flare + 2.0 * bm_wall
        h_out = entry_h_in + 2.0 * inner_flare + 2.0 * bm_wall
        r_out = entry_r_in + inner_flare + bm_wall
        if k == 0:
            # Slightly rounded front rim bevel (1.5 mm inward inset on face)
            w_out -= 2.2
            h_out -= 2.2
            r_out -= 1.1
        uv = rounded_rect_points(w_out, h_out, r_out, n_pts)
        bm_rings.append(ring_frame_points(pos, inlet_dir, up_hint, uv))

    bellmouth_outer = trimesh_to_manifold(loft_closed_solid(bm_rings))

    # 3) Continuous inner air bore (starts 3 mm in front of p_bm_tip -> passes smoothly through bellmouth -> sweeps to 6 mm past tip_y)
    # Avoid placing a ring coplanar with p_bm_tip (s=0) or p0 so booleans have zero coplanar sliver triangles
    bore_rings: list[np.ndarray] = []
    throat_len = float(np.linalg.norm(p0 - p_bm_tip))
    s_samples = np.linspace(-3.5, throat_len - 0.8, 15)
    for s_dist in s_samples:
        pos = p_bm_tip + inlet_dir * float(s_dist)
        if s_dist < 0.0:
            # Smooth trumpet lead-in ahead of bellmouth rim
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
        uv = rounded_rect_points(w, h, r, n_pts)
        bore_rings.append(ring_frame_points(pt, tan, up_hint, uv))

    # Extend straight bore 6 mm past spigot tip so exit is clean and open
    uv_exit = rounded_rect_points(sp_w_in, sp_h_in, sp_r_in, n_pts)
    bore_rings.append(ring_frame_points(np.array([x_center, tip_y - 6.0, sp_z]), tan_sp, up_hint, uv_exit))

    inner_bore = trimesh_to_manifold(loft_closed_solid(bore_rings))

    return {
        "outer": outer_solid,
        "bellmouth_outer": bellmouth_outer,
        "inner_bore": inner_bore,
    }


def build_throttle_body_components(params: dict) -> dict[str, md.Manifold]:
    """
    Build angled TB neck, 4-bolt flange, bore cutter, bolt holes, and face O-ring groove.
    """
    tb = params["throttle_body"]
    pl = params["plenum"]
    wall = tb["neck_wall_thickness_mm"]
    bore_d = tb["bore_diameter_mm"]
    neck_len = tb["neck_length_mm"]
    cant_rad = math.radians(tb["forward_cant_deg"])

    # Plenum ends at x_plenum = cyl4_end_x_mm (170 mm). Overlap 4 mm inside plenum.
    x_start = pl["cyl4_end_x_mm"]
    p_start = np.array([x_start - 4.0, 0.0, 0.0])
    # Cant toward +Y (away from head)
    tb_axis = np.array([math.cos(cant_rad), math.sin(cant_rad), 0.0])
    p_flange_back = np.array([x_start, 0.0, 0.0]) + tb_axis * neck_len
    p_flange_face = p_flange_back + tb_axis * tb["flange_thickness_mm"]

    pl_wall = pl["wall_thickness_mm"]
    pl_w_in = pl["inner_width_y_mm"]
    pl_h_in = pl["inner_height_z_mm"]
    pl_r_in = pl["inner_corner_radius_mm"]
    pl_w_out = pl_w_in + 2.0 * pl_wall
    pl_h_out = pl_h_in + 2.0 * pl_wall
    pl_r_out = pl_r_in + pl_wall

    n_pts = pl["profile_segments"]
    up_hint = np.array([0.0, 0.0, 1.0])

    # Neck outer loft
    neck_out_rings = []
    neck_in_rings = []
    n_steps = 18
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

    # Extend inner bore cleanly 6 mm past outer flange face
    uv_bore_end = rounded_rect_points(bore_d, bore_d, bore_d * 0.5, n_pts)
    neck_in_rings.append(ring_frame_points(p_flange_face + tb_axis * 6.0, tb_axis, up_hint, uv_bore_end))

    neck_outer = trimesh_to_manifold(loft_closed_solid(neck_out_rings))
    tb_bore = trimesh_to_manifold(loft_closed_solid(neck_in_rings))

    # Flange plate extruded along tb_axis
    fl_uv = rounded_rect_points(tb["flange_width_mm"], tb["flange_height_mm"], tb["flange_corner_radius_mm"], 64)
    fl_rings = [
        ring_frame_points(p_flange_back, tb_axis, up_hint, fl_uv),
        ring_frame_points(p_flange_face, tb_axis, up_hint, fl_uv),
    ]
    flange_outer = trimesh_to_manifold(loft_closed_solid(fl_rings))

    # 4 M6 bolt holes
    bx = tb["bolt_spacing_x_mm"] * 0.5
    by = tb["bolt_spacing_y_mm"] * 0.5
    b_rad = tb["bolt_hole_diameter_mm"] * 0.5
    u_ax = np.cross(up_hint, tb_axis)
    u_ax /= np.linalg.norm(u_ax)
    v_ax = np.cross(tb_axis, u_ax)
    v_ax /= np.linalg.norm(v_ax)

    cutters: list[md.Manifold] = [tb_bore]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            pt_center = p_flange_back + u_ax * (sx * bx) + v_ax * (sy * by)
            c0 = pt_center - tb_axis * 3.0
            c1 = pt_center + tb_axis * (tb["flange_thickness_mm"] + 3.0)
            cutters.append(make_cylinder_along(c0, c1, b_rad, segments=32))

    # Face O-ring groove on outer flange face
    og = tb["oring_groove"]
    if og["enabled"]:
        r_in_g = og["inner_diameter_mm"] * 0.5
        r_out_g = r_in_g + og["width_mm"]
        depth_g = og["depth_mm"]
        outer_g = make_cylinder_along(
            p_flange_face - tb_axis * depth_g,
            p_flange_face + tb_axis * 1.0,
            r_out_g,
            segments=72,
        )
        inner_g = make_cylinder_along(
            p_flange_face - tb_axis * (depth_g + 1.0),
            p_flange_face + tb_axis * 2.0,
            r_in_g,
            segments=72,
        )
        cutters.append(outer_g - inner_g)

    return {
        "outer": m_union([neck_outer, flange_outer]),
        "cutters": m_union(cutters),
        "flange_face_center": p_flange_face,
        "tb_axis": tb_axis,
    }


def build_center_split_flange_and_cutters(params: dict) -> dict[str, md.Manifold]:
    """
    Build the center split flange ring centered at X = split_x_mm, plus
    through-bolt holes, alignment dowel pin holes, and face O-ring groove on the -X half.
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
    r_out = r_in + wall

    ext = cs["flange_radial_extension_mm"]
    w_fl = w_out + 2.0 * ext
    h_fl = h_out + 2.0 * ext
    r_fl = cs["flange_outer_corner_radius_mm"]
    thick_total = 2.0 * cs["flange_thickness_per_side_mm"]

    flange_solid = make_rounded_prism(
        w_fl, h_fl, r_fl, thick_total, segments=72, center=(x_split, 0.0, 0.0), axis="x"
    )
    plenum_bore_clear = make_rounded_prism(
        w_in, h_in, r_in, thick_total + 4.0, segments=72, center=(x_split, 0.0, 0.0), axis="x"
    )
    flange_ring = flange_solid - plenum_bore_clear

    # Helper to compute offset point along rounded-rect normal direction
    def perimeter_point(angle_deg: float, radial_offset_from_inner: float) -> tuple[float, float]:
        # Sample dense loop of the inner rounded-rect and pick point at angle_deg,
        # then step outward along local outward normal
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
    # M6 bolt holes
    bolt_offset_from_inner = wall + cs["bolt_radial_offset_mm"]
    b_rad = cs["bolt_hole_diameter_mm"] * 0.5
    for ang in cs["bolt_angles_deg"]:
        by, bz = perimeter_point(ang, bolt_offset_from_inner)
        cutters.append(
            make_cylinder_along(
                np.array([x_split - thick_total * 0.6, by, bz]),
                np.array([x_split + thick_total * 0.6, by, bz]),
                b_rad,
                segments=32,
            )
        )

    # Alignment dowel pin holes
    pin_offset_from_inner = wall + cs["dowel_pin_radial_offset_mm"]
    p_rad = cs["dowel_pin_diameter_mm"] * 0.5
    for ang in cs["dowel_pin_angles_deg"]:
        py, pz = perimeter_point(ang, pin_offset_from_inner)
        cutters.append(
            make_cylinder_along(
                np.array([x_split - thick_total * 0.6, py, pz]),
                np.array([x_split + thick_total * 0.6, py, pz]),
                p_rad,
                segments=32,
            )
        )

    # Continuous O-ring groove on the -X face (recessed into left half from x_split to x_split - depth)
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
            segments=72, center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0), axis="x"
        )
        g_inner = make_rounded_prism(
            w_in + 2.0 * d_in, h_in + 2.0 * d_in, r_in + d_in, gd + 2.0,
            segments=72, center=(x_split - gd * 0.5 + 0.4, 0.0, 0.0), axis="x"
        )
        og_cut = g_outer - g_inner

    return {
        "flange_ring": flange_ring,
        "hole_cutters": m_union(cutters),
        "oring_cutter": og_cut,
    }


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

    # Build vertically along +Z from Z=0 (base grip collar) to Z=total_len (spigot tip)
    z_tip = total_len
    z_b_start = z_tip - bead_off
    z_b_p1 = z_b_start - 1.5
    z_b_p2 = z_b_start - bead_w + 1.5
    z_b_end = z_b_start - bead_w
    stations = [
        (0.0, 3.0),
        (5.0, 3.0),
        (6.5, 0.0),
        (z_b_end, 0.0),
        (z_b_p2, bead_h),
        (z_b_p1, bead_h),
        (z_b_start, 0.0),
        (z_tip, 0.0),
    ]
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
        segments=64, center=(0.0, 0.0, t_g * 0.5), axis="z"
    )
    tb_cutters = [
        md.Manifold.cylinder(t_g + 4.0, tb["bore_diameter_mm"] * 0.5, tb["bore_diameter_mm"] * 0.5, circular_segments=72, center=True).translate([0.0, 0.0, t_g * 0.5])
    ]
    bx = tb["bolt_spacing_x_mm"] * 0.5
    by = tb["bolt_spacing_y_mm"] * 0.5
    b_rad = tb["bolt_hole_diameter_mm"] * 0.5
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            tb_cutters.append(
                md.Manifold.cylinder(t_g + 4.0, b_rad, b_rad, circular_segments=32, center=True).translate([sx * bx, sy * by, t_g * 0.5])
            )
    tb_gauge = m_diff(tb_plate, tb_cutters)

    return {
        "boot_fit_gauge": boot_gauge,
        "tb_flange_fit_gauge": tb_gauge,
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
        bellmouth_outers.append(rc["bellmouth_outer"])
        runner_bores.append(rc["inner_bore"])

    # External runner tie webs between Cyl 1-2 (X=-92) and Cyl 3-4 (X=+92)
    tw = params["runners"]["tie_webs"]
    webs: list[md.Manifold] = []
    if tw["enabled"]:
        y_mid = 0.5 * (tw["y_start_mm"] + tw["y_end_mm"])
        y_len = abs(tw["y_end_mm"] - tw["y_start_mm"])
        z_mid = params["runners"]["spigot"]["center_z_mm"] + 4.0
        for x_mid in (-92.0, 92.0):
            # Span 54 mm across X (overlaps into both adjacent runner walls cleanly)
            web = md.Manifold.cube([54.0, y_len, tw["height_mm"]], center=True).translate([x_mid, y_mid, z_mid])
            webs.append(web)

    # Plenum external hoop stiffening ribs
    ribs: list[md.Manifold] = []
    hr = params["plenum"]["hoop_ribs"]
    if hr["enabled"]:
        pl = params["plenum"]
        wall = pl["wall_thickness_mm"]
        for xr in hr["x_positions_mm"]:
            s = math.sqrt(plenum_area_scale(xr, params))
            w_rib = pl["inner_width_y_mm"] * s + 2.0 * (wall + hr["radial_height_mm"])
            h_rib = pl["inner_height_z_mm"] * s + 2.0 * (wall + hr["radial_height_mm"])
            r_rib = pl["inner_corner_radius_mm"] * s + wall + hr["radial_height_mm"]
            ribs.append(make_rounded_prism(w_rib, h_rib, r_rib, hr["width_mm"], segments=64, center=(xr, 0.0, 0.0), axis="x"))

    # Vacuum/Boost NPT boss pad on top of plenum
    bp = params["plenum"]["vacuum_boss_pad"]
    boss_solids: list[md.Manifold] = []
    boss_bores: list[md.Manifold] = []
    if bp["enabled"]:
        s_bp = math.sqrt(plenum_area_scale(bp["x_center_mm"], params))
        z_roof_in = params["plenum"]["inner_height_z_mm"] * 0.5 * s_bp
        z_top = z_roof_in + params["plenum"]["wall_thickness_mm"] + bp["pad_height_z_mm"] - 2.0
        z_bot = z_roof_in - 4.0  # overlaps into plenum wall; plenum_cavity trims cleanly underneath
        pad = make_rounded_prism(
            bp["length_x_mm"], bp["width_y_mm"], 6.0, z_top - z_bot,
            segments=48, center=(bp["x_center_mm"], bp["y_center_mm"], 0.5 * (z_top + z_bot)), axis="z"
        )
        boss_solids.append(pad)
        p_rad = bp["port_pilot_diameter_mm"] * 0.5
        start_x = bp["x_center_mm"] - bp["port_spacing_x_mm"] * (bp["port_count"] - 1) * 0.5
        for idx in range(bp["port_count"]):
            px = start_x + idx * bp["port_spacing_x_mm"]
            boss_bores.append(
                make_cylinder_along(
                    np.array([px, bp["y_center_mm"], z_roof_in - 12.0]),
                    np.array([px, bp["y_center_mm"], z_top + 4.0]),
                    p_rad,
                    segments=32,
                )
            )

    # Throttle body neck + flange
    tb_parts = build_throttle_body_components(params)

    # --- 3-Stage Watertight Boolean Assembly ---
    # 1. Outer monolithic body (with center rib at X=0 for 1-piece stiffness)
    s_0 = math.sqrt(plenum_area_scale(0.0, params))
    pl_w0 = params["plenum"]["inner_width_y_mm"] * s_0 + 2.0 * (params["plenum"]["wall_thickness_mm"] + hr["radial_height_mm"])
    pl_h0 = params["plenum"]["inner_height_z_mm"] * s_0 + 2.0 * (params["plenum"]["wall_thickness_mm"] + hr["radial_height_mm"])
    pl_r0 = params["plenum"]["inner_corner_radius_mm"] * s_0 + params["plenum"]["wall_thickness_mm"] + hr["radial_height_mm"]
    center_rib = make_rounded_prism(pl_w0, pl_h0, pl_r0, hr["width_mm"], segments=64, center=(0.0, 0.0, 0.0), axis="x")

    outer_1pc = m_union([pl_outer, *runner_outers, *webs, *ribs, center_rib, *boss_solids, tb_parts["outer"]])
    # 2. Hollow plenum & TB bore
    hollow_1pc = outer_1pc - m_union([pl_inner, tb_parts["cutters"]])
    # 3. Union internal velocity-stack bellmouths inside plenum
    with_bm_1pc = m_union([hollow_1pc, *bellmouth_outers])
    # 4. Subtract runner bores (with bellmouth flare) and vacuum pilot bores
    final_1pc = m_diff(with_bm_1pc, [*runner_bores, *boss_bores])

    # --- 2-Piece Split Version (add center split flange at X=0, omit simple center rib) ---
    split_parts = build_center_split_flange_and_cutters(params)
    outer_split_base = m_union([pl_outer, *runner_outers, *webs, *ribs, *boss_solids, tb_parts["outer"]])
    hollow_split = outer_split_base - m_union([pl_inner, tb_parts["cutters"]])
    with_bm_split = m_union([hollow_split, *bellmouth_outers, split_parts["flange_ring"]])
    full_for_split = m_diff(with_bm_split, [*runner_bores, *boss_bores, split_parts["hole_cutters"]])

    x_split = params["center_split"]["split_x_mm"]
    big = 1000.0
    left_box = md.Manifold.cube([big, big, big], center=True).translate([x_split - big * 0.5, 0.0, 0.0])
    right_box = md.Manifold.cube([big, big, big], center=True).translate([x_split + big * 0.5, 0.0, 0.0])

    split_left = full_for_split ^ left_box
    if split_parts["oring_cutter"] is not None:
        split_left = split_left - split_parts["oring_cutter"]
    split_right = full_for_split ^ right_box

    # Print-oriented copies (flat center split flange sitting at Z=0)
    # Left half (x <= 0): rotate +90 deg around Y -> z' = -x >= 0
    split_left_print = split_left.rotate([0.0, 90.0, 0.0])
    # Right half (x >= 0): rotate -90 deg around Y -> z' = +x >= 0
    split_right_print = split_right.rotate([0.0, -90.0, 0.0])

    # Shift print-oriented copies into positive X/Y quadrant for clean bed placement
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
        "_plenum_inner_cavity": pl_inner,
    }


# ---------------------------------------------------------------------------
# Visualization & Documentation Generators
# ---------------------------------------------------------------------------

def render_overview_png(meshes: dict[str, trimesh.Trimesh], solids: dict[str, md.Manifold], params: dict, out_path: Path):
    fig = plt.figure(figsize=(16, 11), facecolor="#f5f4f0")
    fig.suptitle(
        "2004 Ford Focus SVT Turbo — 3D-Printable Upper Intake Manifold (Rough Draft)",
        fontsize=15,
        fontweight="bold",
        y=0.97,
        color="#1f242b",
    )

    def add_section_patches(ax, polys_2d: list[np.ndarray], facecolor: str, edgecolor: str, lw: float = 0.9, alpha: float = 1.0):
        """Render 2D cross-section polygons with true outer/hole nesting via PathPatch."""
        if not polys_2d:
            return
        sh_polys = [ShapelyPolygon(p) for p in polys_2d if len(p) >= 3]
        # Determine nesting depth: even depth = solid outer ring, odd depth = hole
        depths = []
        for i, pi in enumerate(sh_polys):
            d = sum(1 for j, pj in enumerate(sh_polys) if i != j and pj.area > pi.area and pj.contains(pi.representative_point()))
            depths.append(d)
        # Pair each even-depth outer with its direct odd-depth holes (depth == d + 1)
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
                # Ensure outer is CCW and holes are CW for non-zero winding rule
                area = 0.5 * np.sum(r[:-1, 0] * r[1:, 1] - r[1:, 0] * r[:-1, 1])
                if (r_idx == 0 and area < 0) or (r_idx > 0 and area > 0):
                    r = r[::-1]
                verts.extend(r)
                codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(r) - 2) + [MplPath.CLOSEPOLY])
            path = MplPath(np.asarray(verts), codes)
            ax.add_patch(PathPatch(path, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, alpha=alpha))

    def plot_mesh_panel(ax, mesh: trimesh.Trimesh, title: str, elev: float, azim: float, color="#3a434e"):
        ax.set_facecolor("#f5f4f0")
        ax.plot_trisurf(
            mesh.vertices[:, 0],
            mesh.vertices[:, 1],
            mesh.vertices[:, 2],
            triangles=mesh.faces,
            color=color,
            linewidth=0,
            antialiased=False,
            shade=True,
        )
        b = mesh.bounds
        mins, maxs = b[0], b[1]
        spans = maxs - mins
        max_span = max(spans) * 0.55
        c = 0.5 * (mins + maxs)
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

    # Panel 1: 1-piece full isometric
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    plot_mesh_panel(ax1, meshes["svt_intake_manifold_1piece_full"], "1-Piece Reference Assembly (IMRC Deleted)", 26, -55, "#4d5661")

    # Panel 2: 2-piece exploded isometric (split left & right offset by 48 mm)
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    m_l = meshes["svt_intake_manifold_split_left_cyl1_2"].copy()
    m_r = meshes["svt_intake_manifold_split_right_cyl3_4_tb"].copy()
    m_l.apply_translation([-24.0, 0.0, 0.0])
    m_r.apply_translation([24.0, 0.0, 0.0])
    plot_mesh_panel(ax2, trimesh.util.concatenate([m_l, m_r]), "2-Piece Split Assembly (256x256x256 Bed Fit)", 26, -55, "#36688d")

    # Panel 3: Cross-section at X = +46 mm (Cyl 3) showing plenum + velocity stack + swept runner + beaded spigot
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.set_facecolor("#ffffff")
    full_solid = solids["svt_intake_manifold_1piece_full"]
    rot_x = full_solid.rotate([0.0, -90.0, 0.0])
    sec_yz = rot_x.slice(46.0)
    yz_polys = [np.column_stack([np.asarray(p)[:, 1], -np.asarray(p)[:, 0]]) for p in sec_yz.to_polygons()]
    add_section_patches(ax3, yz_polys, facecolor="#4c5c6b", edgecolor="#1b2026", lw=0.9)
    ax3.axhline(0, color="#999999", lw=0.6, ls="--")
    ax3.axvline(0, color="#999999", lw=0.6, ls="--")
    ax3.set_aspect("equal")
    ax3.set_xlim(-160, 75)
    ax3.set_ylim(-65, 75)
    ax3.grid(True, linestyle=":", alpha=0.5)
    ax3.set_title("Section at Cyl 3 (X = +46 mm): Plenum, Bellmouth & Beaded Spigot", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Y: Spigot (-Y) to Front (+Y) [mm]")
    ax3.set_ylabel("Z: Height [mm]")

    # Panel 4: Top/Front overview slice + print-envelope annotations
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor("#ffffff")
    sec_xy = [np.asarray(p) for p in full_solid.slice(-35.0).to_polygons()]
    add_section_patches(ax4, sec_xy, facecolor="#2f5d80", edgecolor="#182a38", lw=0.9, alpha=0.88)
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
    ax4.set_title("Plan Layout: 92 mm Pitch Spigots (Blue) & Plenum/TB Bore (Red Dashed)", fontsize=11, fontweight="bold")
    ax4.set_xlabel("X: Cyl 1 (-X) to TB (+X) [mm]")
    ax4.set_ylabel("Y [mm]")

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def render_1to1_svg(solids: dict[str, md.Manifold], params: dict, out_path: Path):
    """Generate a true 1:1 mm-unit SVG template for physical caliper comparison of key interfaces."""
    # 1) Boot Spigot face section (from boot_fit_gauge at Z=38mm)
    spigot_sec = solids["svt_runner_boot_fit_gauge"].slice(38.0).to_polygons()
    # 2) Center split flange face (from split_left at X=-1 mm, rotated so X->Z)
    split_sec = solids["svt_intake_manifold_split_left_cyl1_2"].rotate([0.0, -90.0, 0.0]).slice(-1.0).to_polygons()
    # 3) TB flange face (from tb_flange_fit_gauge at Z=2 mm)
    tb_sec = solids["svt_tb_flange_fit_gauge"].slice(2.0).to_polygons()

    # Arrange horizontally across a 420 x 180 mm SVG canvas
    width_mm, height_mm = 420.0, 175.0
    centers = [
        ("Silicone Boot Spigot\n(48x36 outer / 38x26 inner)", spigot_sec, (55.0, 88.0), lambda p: (p[0], -p[1])),
        ("Center Split Flange\n(6x M6 + 2x 6mm Dowel + O-Ring)", split_sec, (195.0, 88.0), lambda p: (p[1], p[0])),
        ("65mm Throttle Body Flange\n(70x70 mm 4-Bolt Pattern)", tb_sec, (345.0, 88.0), lambda p: (p[0], -p[1])),
    ]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="210" y="12" text-anchor="middle" font-family="sans-serif" font-size="6" font-weight="bold" fill="#111">2004 Focus SVT Intake Manifold — 1:1 Interface Templates (mm)</text>',
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
        "parts": manifest_parts,
    }
    (STL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    render_overview_png(meshes, solids, params, FITMENT_DIR / "01_intake_manifold_overview.png")
    render_1to1_svg(solids, params, FITMENT_DIR / "02_interfaces_1to1_template.svg")

    print(f"Generated {len(meshes)} watertight STLs. Plenum volume: {plenum_liters:.3f} L")
    for pname, info in manifest_parts.items():
        print(
            f"  {pname}: {info['extents_mm']} mm | "
            f"vol={info['solid_volume_cm3']} cm3 | "
            f"CC2={info['fits_centauri_carbon_2_256']} | E3={info['fits_ender_3_s1_pro_220']}"
        )


if __name__ == "__main__":
    main()
