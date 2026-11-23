"""Measure the exported manifold STL and check its functional interfaces."""

import json
import math

import matplotlib.pyplot as plt
import numpy as np
import trimesh

from smooth_manifold import (ASSEMBLY_PARTS, HERE, PREFIX, REFERENCE, cad, digest,
                             from_triangles, indexed_stl, load_sources)


def section(mesh, origin, axis):
    """Return 2D line segments in the transverse plane and its up-directed basis."""
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    up = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(up, axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    lines = trimesh.intersections.mesh_plane(mesh, axis, origin)
    return (lines - origin) @ np.column_stack((u, v))


def ray_distances(lines, direction, origin=(0, 0)):
    a, b = (lines - np.asarray(origin)).transpose(1, 0, 2)
    e = b - a
    dx, dy = direction
    determinant = dx * e[:, 1] - dy * e[:, 0]
    valid = np.abs(determinant) > 1e-10
    a, e, determinant = a[valid], e[valid], determinant[valid]
    t = (a[:, 0] * e[:, 1] - a[:, 1] * e[:, 0]) / determinant
    fraction = (a[:, 0] * dy - a[:, 1] * dx) / determinant
    hits = np.sort(t[(t > 0) & (fraction >= -1e-9) & (fraction <= 1 + 1e-9)])
    return hits[np.r_[True, np.diff(hits) > 0.0001]] if len(hits) else hits


def local_x(mesh, center, span):
    x = mesh.triangles[:, :, 0]
    keep = (x.min(axis=1) <= center + span) & (x.max(axis=1) >= center - span)
    return trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces[keep], process=False)


def runner_measurements(mesh, params):
    result = []
    angles = np.deg2rad(np.arange(72) * 5 + 0.37)
    rays = np.column_stack((np.cos(angles), np.sin(angles)))
    sp = params['runners']['spigot']
    for xc in params['runners']['center_x_mm']:
        local = local_x(mesh, xc, 36)
        tip, axis, *controls = cad.runner_bezier_points(xc, params)
        roots = [(f'{s:g} mm after lip', tip + s * axis, axis) for s in (6, 8, 10, 12, 14, 16, 18)]
        roots.extend((f'Bezier t={t:g}', *cad.bezier_point_and_tangent(*controls, t))
                     for t in (0.025, 0.05, 0.1, 0.15, 0.2))
        audit = []
        for label, position, normal in roots:
            pairs = []
            lines = section(local, position, normal)
            for angle, ray in zip(angles, rays):
                d = ray_distances(lines, ray)
                # Skip rays that continue through the plenum outside the local root window.
                if len(d) >= 2 and 8 < d[0] < 34 and d[1] < 39:
                    pairs.append((float(d[1] - d[0]), float(np.rad2deg(angle))))
            minimum, angle = min(pairs)
            audit.append({'station': label, 'min_radial_wall_mm': minimum, 'angle_deg': angle,
                          'local_wall_rays': len(pairs)})
        spigot_plane = section(local, np.array([xc, -130.3, sp['center_z_mm']]), (0, -1, 0))
        hits = np.array([ray_distances(spigot_plane, ray)[:2] for ray in rays])
        points = rays * hits[:,1,None]
        circle = np.column_stack((2*points, np.ones(len(points))))
        u, v, _ = np.linalg.lstsq(circle, np.sum(points**2, axis=1), rcond=None)[0]
        result.append({'cylinder_x_mm': xc, 'roots': audit,
                       'minimum_in_sample': min(audit, key=lambda s: s['min_radial_wall_mm']),
                       'spigot_center_from_circle_fit_xz_mm': [xc + float(u), sp['center_z_mm'] + float(v)],
                       'spigot_inner_diameter_min_max_mm': (2*hits[:,0]).take([hits[:,0].argmin(), hits[:,0].argmax()]).tolist(),
                       'spigot_outer_diameter_min_max_mm': (2*hits[:,1]).take([hits[:,1].argmin(), hits[:,1].argmax()]).tolist(),
                       'spigot_min_radial_wall_mm': float(np.min(hits[:,1] - hits[:,0]))})
    return result


def barrel_measurements(mesh, params):
    vals = []
    for x in (-157.3, -115.7, 2.13, 114.7, 167.8):
        lines = section(local_x(mesh, x, 1), np.array([x, 0, 0]), (1, 0, 0))
        # With an X-directed section, +u is +Y. Sample the front barrel, away from runner openings.
        angles = np.deg2rad(np.linspace(-65, 65, 41))
        rays = np.column_stack((np.cos(angles), np.sin(angles)))
        hits = np.array([ray_distances(lines, ray)[:2] for ray in rays])
        vals.append({'x_mm': x, 'front_barrel_wall_min_mm': float(np.min(hits[:,1] - hits[:,0])),
                     'nominal_wall_after_taper_scale_mm': 6.5 * math.sqrt(cad.plenum_area_scale(x, params))})
    return vals


def iacv_floor(mesh, params):
    cfg = params['throttle_body']['iacv_mount']
    x0 = cfg['x_center_mm'] + cfg['port_spacing_x_mm'] / 2
    y0 = cfg['y_center_mm']
    sampled = []
    for dx in np.arange(-5.75, 6, 0.5):
        x = x0 + dx
        lines = section(local_x(mesh, x, 0.5), np.array([x, 0, 0]), (1, 0, 0))
        for dy in np.arange(-5.75, 6, 0.5):
            if dx**2 + dy**2 >= 6.1**2:
                continue
            z = ray_distances(lines, (0, 1), origin=(y0+dy, 0))
            assert len(z) >= 2 and abs(z[1]-cfg['supply_pocket_bottom_z_mm']) < 0.01, (x, y0+dy, z)
            sampled.append({'x_mm': x, 'y_mm': y0+dy, 'wall_mm': float(z[1] - z[0])})
    center_plane = section(local_x(mesh, x0, 1), np.array([x0, 0, 0]), (1, 0, 0))
    center_hits = ray_distances(center_plane, (0, 1), origin=(y0, 0))
    return {'samples': len(sampled), 'centerline_wall_mm': float(center_hits[1] - center_hits[0]),
            'minimum': min(sampled, key=lambda s: s['wall_mm'])}


def throttle_bore(mesh, params):
    _, _, _, _, _, face, axis = cad.tb_neck_bezier_points(params)
    lines = section(local_x(mesh, face[0], 8), face - 1.33*axis, axis)
    angles = np.deg2rad(np.arange(72) * 5 + 0.37)
    radii = np.array([ray_distances(lines, (math.cos(a), math.sin(a)))[0] for a in angles])
    return [float(2*radii.min()), float(2*radii.max())]


def root_witnesses(mesh, params, plot_path=None):
    result = []
    if plot_path:
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    for i, (xc, station) in enumerate(((46.0, 10.0), (138.0, 14.0))):
        tip, axis, *_ = cad.runner_bezier_points(xc, params)
        origin = tip + station*axis
        lines = section(mesh, origin, axis)
        angle = math.radians(175.37)
        ray = np.array([math.cos(angle), math.sin(angle)])
        hits = ray_distances(lines, ray)
        u = np.cross([0, 0, 1], axis)
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        direction = ray[0]*u + ray[1]*v
        endpoints = origin + hits[:2, None]*direction
        result.append({'cylinder': i+3, 'section_after_bellmouth_lip_mm': station,
                       'angle_deg': 175.37, 'world_endpoints_mm': endpoints.tolist(),
                       'distance_from_runner_center_to_crossings_mm': hits.tolist(),
                       'material_span_mm': float(hits[1] - hits[0])})
        if plot_path:
            from matplotlib.collections import LineCollection
            ax = axes[i]
            ax.add_collection(LineCollection(lines, colors='#414d59', linewidths=1.4))
            points = hits[:2, None]*ray
            ax.plot(*points.T, 'o-', color='#bb421f', markersize=3, label=f'{hits[1]-hits[0]:.2f} mm solid span')
            a, b = np.array([hits[0]-5, hits[1]+5])[:, None]*ray
            ax.plot(*np.stack([a,b]).T, '--', color='#bb421f', linewidth=0.7)
            center = points.mean(axis=0)
            ax.set(xlim=(center[0]-6, center[0]+6), ylim=(center[1]-5, center[1]+5), aspect='equal',
                   title=f'Cylinder {i+3} | {station:g} mm into the bellmouth', xlabel='Local U (mm)', ylabel='Local V (mm)')
            ax.grid(alpha=0.2)
            ax.legend(loc='lower left')
    if plot_path:
        fig.suptitle('Thin internal material at the runner-to-plenum junctions')
        fig.savefig(plot_path, dpi=170)
        plt.close(fig)
    return result


def washer_clearance(left, right, params):
    cs, pl, tb = (params[k] for k in ('center_split', 'plenum', 'throttle_body'))
    x = cs['split_x_mm']
    thick = cs['flange_thickness_per_side_mm']
    scale = math.sqrt(cad.plenum_area_scale(x, params))
    points = cad.rounded_rect_points(pl['inner_width_y_mm']*scale, pl['inner_height_z_mm']*scale,
                                    pl['inner_corner_radius_mm']*scale, 720)
    angles = np.rad2deg(np.arctan2(points[:,1], points[:,0]))
    split = []
    for angle in cs['bolt_angles_deg']:
        i = int(np.argmin(np.abs((angles-angle+180) % 360-180)))
        du, dv = points[(i+1) % 720] - points[(i-1) % 720]
        u, v = points[i] + np.array([dv, -du]) / math.hypot(du, dv) * (
            pl['wall_thickness_mm'] + cs['bolt_radial_offset_mm'])
        row = {'clock_deg': angle}
        for side, part in ((-1, left), (1, right)):
            probe = cad.make_cylinder_along(np.array([x + side*(thick+0.3), u, v]),
                                            np.array([x + side*(thick+18.0), u, v]), 6.2, segments=24)
            row['left_mm3' if side < 0 else 'right_mm3'] = float((part ^ probe).volume())
        split.append(row)
    _, _, _, _, back, _, axis = cad.tb_neck_bezier_points(params)
    u = np.cross([0,0,1], axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    throttle = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = back + sx*0.5*tb['bolt_spacing_x_mm']*u + sy*0.5*tb['bolt_spacing_y_mm']*v
            probe = cad.make_cylinder_along(p - 10.5*axis, p - 0.3*axis, 6.2, segments=24)
            throttle.append({'bolt_uv_sign': [sx, sy], 'interference_mm3': float((right ^ probe).volume())})
    return {'split': split, 'throttle_body': throttle}


def main():
    params = json.loads((REFERENCE / 'intake_manifold_parameters.json').read_text(encoding='utf-8'))
    validation = json.loads((HERE / 'mesh_validation.json').read_text(encoding='utf-8'))['parts']
    baseline, _ = load_sources(params, ASSEMBLY_PARTS)
    candidates = {}
    for name in ASSEMBLY_PARTS:
        path = HERE / 'stl' / f'{PREFIX}{name}_codex.stl'
        assert digest(path.read_bytes()) == validation[name]['sha256'], name
        candidates[name] = indexed_stl(path)[1]
    report = {}
    for key, models in (('source', baseline), ('codex', candidates)):
        full = models[ASSEMBLY_PARTS[0]]
        left, right = (from_triangles(models[name].vertices, models[name].faces) for name in ASSEMBLY_PARTS[1:])
        print(f'Checking {key} STL sections', flush=True)
        runners = runner_measurements(full, params)
        pitches = np.diff([r['spigot_center_from_circle_fit_xz_mm'][0] for r in runners]).tolist()
        report[key] = {'runner_samples': runners, 'adjacent_spigot_pitches_mm': pitches,
                       'plenum_front_barrel': barrel_measurements(full, params),
                       'iacv_floor': iacv_floor(full, params),
                       'throttle_bore_measured_diameter_range_mm': throttle_bore(full, params),
                       'thin_internal_lip_crossings': root_witnesses(
                           full, params, plot_path=HERE/'bellmouth_sections.png' if key == 'codex' else None),
                       'washer_and_socket_clearance': washer_clearance(left, right, params)}
        (HERE / 'geometry_measurements.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
