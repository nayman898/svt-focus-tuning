"""Rectify hand-picked features in the supplied photo and build a fit-only plate."""

import json
import os
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

import manifold3d as md
import numpy as np
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString, Point, Polygon, box
import trimesh


HERE = Path(__file__).resolve().parent
CODEX = HERE.parents[1]


def plane_map(photo_bolts, bolts):
    rows, target = [], []
    for (x, y), (u, v) in zip(photo_bolts, bolts, strict=True):
        rows.extend(([x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]))
        target.extend((u, v))
    return np.r_[np.linalg.solve(rows, target), 1].reshape(3, 3)


def project(points, transform):
    xyz = np.c_[points, np.ones(len(points))] @ transform.T
    return xyz[:, :2] / xyz[:, 2:]


def smooth_curve(points, closed):
    points = np.vstack([points, points[0]]) if closed else points
    distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    curve = CubicSpline(distance, points, bc_type="periodic" if closed else "natural")
    return curve(np.linspace(0, distance[-1], 180, endpoint=not closed))


def svg_outline(path, bolts, fit_bore, feed, gasket, divider, plate, tb):
    def points(values):
        return " ".join(f"{x:.4f},{y:.4f}" for x, y in values)

    bolt_radius = tb["bolt_hole_diameter_mm"] / 2
    bore_diameter = tb["bore_diameter_mm"]
    circles = "".join(f'<circle cx="{x}" cy="{y}" r="{bolt_radius:g}"/>' for x, y in bolts)
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="215.9mm" height="279.4mm" viewBox="0 0 215.9 279.4">
<title>Factory throttle body IACV photo trace</title>
<rect width="215.9" height="279.4" fill="white"/>
<defs><g id="pattern" fill="none" stroke="#1c252e" stroke-width=".28">
<polygon points="{points(plate)}"/>
{circles}
<circle cx="{fit_bore[0]:.4f}" cy="{fit_bore[1]:.4f}" r="{bore_diameter / 2:g}"/>
<polygon points="{points(feed)}" stroke="#075d87" fill="#e5f4fa"/>
<polygon points="{points(gasket)}" stroke="#38724a" stroke-dasharray="1.25 .8"/>
<polyline points="{points(divider)}" stroke="#38724a" stroke-dasharray="1.25 .8"/>
<path d="M-2 0h4M0 -2v4" stroke="#64717b"/>
</g></defs>
<use href="#pattern" transform="translate(66 84)"/>
<use href="#pattern" transform="translate(66 204) scale(1 -1)"/>
<g fill="#18252e" font-family="sans-serif">
<text x="12" y="12" font-size="5" font-weight="bold">Factory throttle-body photo trace</text>
<text x="12" y="19" font-size="3.4">Print at actual size. Check the 50 mm scale bar.</text>
<text x="18" y="29" font-size="3.4" font-weight="bold">Hardware face as photographed</text>
<text x="18" y="148" font-size="3.4" font-weight="bold">Mating plate face with linkage up</text>
<g font-size="3.25">
<text x="122" y="53">{tb["bolt_spacing_x_mm"]:g} × {tb["bolt_spacing_y_mm"]:g} mm bolt center pitch</text>
<text x="122" y="61">Ø{bore_diameter:g} mm plate bore</text>
<text x="122" y="69">Blue shows the IACV feed outline</text>
<text x="122" y="77">Green shows the gasket centerline</text>
<text x="122" y="93">Linkage at the bottom in this view</text>
<text x="122" y="174">This view matches the assumed</text>
<text x="122" y="181">installed clocking of the plate.</text>
<text x="122" y="197">Check the bore, feed and gasket</text>
<text x="122" y="204">against your actual throttle body.</text>
<text x="122" y="226">Fit check only</text>
<text x="122" y="247">50 mm scale check</text>
</g></g>
<path d="M122 252h50m-50-1.5v3m50-3v3" fill="none" stroke="#18252e" stroke-width=".3"/>
</svg>
''', encoding="utf-8")


def build():
    picks = json.loads((HERE / "photo_points.json").read_text(encoding="utf-8"))
    params = json.loads((CODEX / "intake_manifold_v2_codex_parameters.json").read_text(encoding="utf-8"))
    tb = params["throttle_body"]
    dx, dy = (tb[key] / 2 for key in ("bolt_spacing_x_mm", "bolt_spacing_y_mm"))
    bolts = np.array([[-dx, -dy], [dx, -dy], [dx, dy], [-dx, dy]])
    transform = plane_map(picks["bolt_centers_tl_tr_br_bl_px"], bolts)
    assert np.allclose(project(picks["bolt_centers_tl_tr_br_bl_px"], transform), bolts)
    x, y = project(picks["bore_lip_px"], transform).T
    u, v, constant = np.linalg.lstsq(np.c_[2*x, 2*y, np.ones(len(x))], x*x + y*y, rcond=None)[0]
    radius = np.sqrt(constant + u*u + v*v)
    bore_center = np.array([u, v])
    radial_error = np.hypot(x-u, y-v) - radius
    feed = smooth_curve(project(picks["iacv_opening_lip_px"], transform), closed=True)
    gasket = smooth_curve(project(picks["outer_gasket_centerline_px"], transform), closed=True)
    divider = smooth_curve(project(picks["iacv_gasket_divider_centerline_px"], transform), closed=False)
    feed_shape = Polygon(feed)
    assert feed_shape.is_valid and feed_shape.area > 0
    w, h, fillet = (tb[key] for key in ("flange_width_mm", "flange_height_mm", "flange_corner_radius_mm"))
    plate = box(-w/2 + fillet, -h/2 + fillet, w/2 - fillet, h/2 - fillet).buffer(fillet, quad_segs=24)
    bore = Point(u, v).buffer(tb["bore_diameter_mm"] / 2, quad_segs=48)
    gasket_lines = LineString(np.vstack([gasket, gasket[0]])).union(LineString(divider))
    holes = [Point(*bolt).buffer(tb["bolt_hole_diameter_mm"] / 2, quad_segs=24) for bolt in bolts]
    assert plate.covers(gasket_lines) and plate.covers(feed_shape) and plate.covers(bore)
    assert feed_shape.disjoint(gasket_lines) and feed_shape.disjoint(bore)
    assert all(feed_shape.disjoint(hole) for hole in holes)

    # CAD +Y follows the photo downward, so the plate's top view mirrors the photo vertically.
    def cross(shape):
        return md.CrossSection([np.asarray(shape.exterior.coords[:-1])], md.FillRule.EvenOdd)

    slab = cross(plate)
    for void in (bore, feed_shape, *holes):
        slab -= cross(void)
    solid = slab.extrude(4)
    indexed = solid.to_mesh()
    mesh = trimesh.Trimesh(vertices=indexed.vert_properties[:, :3], faces=indexed.tri_verts, process=False)
    mesh_path = HERE / "factory_iacv_photo_fit_plate.stl"
    mesh.export(mesh_path)
    check = trimesh.load_mesh(mesh_path)
    assert check.is_volume and check.body_count == 1 and check.is_winding_consistent
    assert np.allclose(check.extents, [w, h, 4], atol=0.01, rtol=0)
    reloaded = md.Manifold(md.Mesh(
        np.ascontiguousarray(check.vertices, dtype=np.float32),
        np.ascontiguousarray(check.faces, dtype=np.uint32),
    ))
    assert reloaded.status() == md.Error.NoError and len(reloaded.slice(2).to_polygons()) == 7
    svg_outline(HERE / "factory_iacv_photo_pattern_1to1.svg", bolts, bore_center, feed, gasket, divider,
                list(plate.exterior.coords), tb)

    bx0, by0, bx1, by1 = feed_shape.bounds
    gx0, gy0, gx1, gy1 = gasket_lines.bounds
    report = {
        "view_axes": "Viewed as photographed. +X right, +Y down. Origin at bolt-grid center. Plate STL +Y follows photo down.",
        "assumed_bolt_pitch_mm": [2*dx, 2*dy],
        "bore_center_xy_mm": bore_center.tolist(),
        "photo_bore_circle_fit_diameter_mm": radius * 2,
        "photo_bore_circle_fit_rms_error_mm": float(np.sqrt(np.mean(radial_error**2))),
        "nominal_plate_bore_diameter_mm": tb["bore_diameter_mm"],
        "iacv_opening_bounds_xy_mm": [[bx0, by0], [bx1, by1]],
        "iacv_opening_bounding_size_mm": [bx1-bx0, by1-by0],
        "iacv_opening_centroid_mm": list(feed_shape.centroid.coords[0]),
        "iacv_opening_traced_area_mm2": feed_shape.area,
        "gasket_centerline_bounding_size_mm": [gx1-gx0, gy1-gy0],
        "planar_gaps_mm": {"iacv_to_nominal_bore": feed_shape.distance(bore),
                           "iacv_to_gasket_centerline": feed_shape.distance(gasket_lines),
                           "gasket_centerline_to_plate_edge": gasket_lines.distance(plate.boundary)},
        "photo_to_mm_matrix": transform.tolist(),
        "fit_plate_extents_mm": check.extents.tolist(),
    }
    (HERE / "photo_measurements.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
