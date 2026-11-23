"""Blend exterior junctions on the exported Stage-2 mesh and audit the STL round-trip."""

from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

import manifold3d as md
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
import trimesh

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'reference'
sys.dont_write_bytecode = True
sys.path.insert(0, str(REFERENCE))

import generate_intake_manifold as cad
import verify_airflow as airflow


PREFIX = 'svt_intake_manifold_'
ASSEMBLY_PARTS = ('1piece_full', 'split_left_cyl1_2', 'split_right_cyl3_4_tb')
PRINT_PARTS = ('split_left_print_oriented', 'split_right_print_oriented')
STEP = 0.4  # heightfield spacing, mm
DEPTH = 0.8  # how far the additive patch overlaps the existing exterior, mm
VOLUME_EPS = 0.05  # mm³, tolerance for round-trip and Boolean comparisons


@dataclass(frozen=True)
class Region:
    name: str
    x: tuple[float, float]
    y: tuple[float, float]
    direction: int
    sigma_mm: float
    max_lift_mm: float
    pad: tuple[float, float, float] | None = None


def digest(data):
    return hashlib.sha256(data).hexdigest()


def indexed_stl(path):
    raw = trimesh.load_mesh(path, file_type='stl', process=False)
    vertices, inverse = np.unique(raw.vertices, axis=0, return_inverse=True)
    faces = inverse[raw.faces]
    repeated = np.any(faces == np.roll(faces, 1, axis=1), axis=1)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces[~repeated], process=False)
    mesh.remove_unreferenced_vertices()
    return raw, mesh, int(repeated.sum())


def from_triangles(vertices, faces):
    solid = md.Manifold(md.Mesh64(np.ascontiguousarray(vertices, dtype='f8'),
                                  np.ascontiguousarray(faces, dtype='u8')))
    if solid.status() != md.Error.NoError or solid.is_empty():
        raise ValueError(f'Invalid solid: {solid.status()}')
    return solid


def regions(params):
    for x in (-92, 92):
        for direction in (-1, 1):
            for side in (-1, 1):
                center = x + side * 20
                yield Region(f'Tie-bar {x:+} / {side:+}, Z {direction:+}',
                             (center - 12, center + 12), (-111, -74), direction, 2.3, 1.55)
    for name in ('vacuum_only_boss_pad', 'vacuum_boss_pad'):
        pad = params['plenum'][name]
        x = pad['x_center_mm']
        half_length = pad['length_x_mm'] / 2
        y = pad['y_center_mm']
        bounds = (max(x - half_length - 12, 28), x + half_length + 12) if x > 0 else (
            x - half_length - 12, min(x + half_length + 12, -28))
        for side, y_bounds in (('near', (y - 26, y - 8)), ('far', (y + 8, y + 26))):
            yield Region(f'{name} {side}', bounds, y_bounds, 1, 2.2, 1.8, (x, y, half_length))
        for side in (-1, 1):
            x_end = x + side * half_length
            offsets = (-10, 6) if side < 0 else (-6, 10)
            end_bounds = (max(bounds[0], x_end + offsets[0]), min(bounds[1], x_end + offsets[1]))
            if end_bounds[1] - end_bounds[0] >= 12:
                yield Region(f'{name} X={x_end:g}', end_bounds, (y - 18, y + 18), 1, 2.2, 1.8,
                             (x, y, half_length))


def top_surface(mesh, xs, ys, sign):
    """Rasterize the first surface seen along vertical rays, using triangle planes."""
    surface = np.full((len(xs), len(ys)), -np.inf)
    lo, hi = mesh.bounds
    assert lo[0] <= xs[0] < xs[-1] <= hi[0] and lo[1] <= ys[0] < ys[-1] <= hi[1]
    tri = mesh.triangles
    bounds_low = tri.min(axis=1)
    bounds_high = tri.max(axis=1)
    on_grid = ((bounds_high[:, 0] >= xs[0]) & (bounds_low[:, 0] <= xs[-1]) &
               (bounds_high[:, 1] >= ys[0]) & (bounds_low[:, 1] <= ys[-1]))
    for a, b, c in tri[on_grid]:
        low = np.minimum(np.minimum(a, b), c)
        high = np.maximum(np.maximum(a, b), c)
        i, j = np.searchsorted(xs, [low[0], high[0]], side='left')
        k, l = np.searchsorted(ys, [low[1], high[1]], side='left')
        if i == j or k == l:
            continue
        ab = b - a
        ac = c - a
        det = ab[0] * ac[1] - ab[1] * ac[0]
        if abs(det) < 1e-13:
            continue
        xx = xs[i:j, None] - a[0]
        yy = ys[None, k:l] - a[1]
        u = (xx * ac[1] - yy * ac[0]) / det
        v = (ab[0] * yy - ab[1] * xx) / det
        z = sign * (a[2] + u * ab[2] + v * ac[2])
        in_tri = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        block = surface[i:j, k:l]
        np.maximum(block, z, where=in_tri, out=block)
    return surface


def ramp(distance, width):
    t = np.clip(distance / width, 0, 1)
    return t * t * (3 - 2 * t)


def cap_for_region(mesh, region):
    xs = np.arange(region.x[0] + 0.013, region.x[1], STEP)
    ys = np.arange(region.y[0] + 0.017, region.y[1], STEP)
    h = top_surface(mesh, xs, ys, region.direction)
    valid = np.isfinite(h)
    nearest = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    filled = h[tuple(nearest)]
    xx, yy = np.meshgrid(xs, ys, indexing='ij')
    rim = np.minimum.reduce((xx - xs[0], xs[-1] - xx, yy - ys[0], ys[-1] - yy))
    weights = ramp(rim - 1, 4)
    if not valid.all():
        weights *= ramp(distance_transform_edt(valid) * STEP - 2.5, 2.5)
    if region.pad:
        x0, y0, half_length = region.pad
        # Keep the threaded pilot bores and flat faces outside the blended skirt.
        near_perimeter = np.maximum(np.abs(xx - x0) - half_length, np.abs(yy - y0) - 14)
        weights *= ramp(near_perimeter + 3, 3)
    smooth = gaussian_filter(filled, region.sigma_mm / STEP, mode='nearest')
    # Smooth positive lift with zero slope at contact with the original boundary.
    delta = np.maximum(smooth - filled, 0)
    lift = np.minimum(delta * ramp(delta, 0.18), region.max_lift_mm) * weights
    active = lift > 0.018
    if not active.any():
        raise ValueError(f'No blend relief in {region.name}')
    # Include a recessed border so the union merges the blend without a free edge.
    rows, cols = np.where(active)
    ix = slice(rows.min() - 2, rows.max() + 3)
    iy = slice(cols.min() - 2, cols.max() + 3)
    xy = np.column_stack((xx[ix, iy].ravel(), yy[ix, iy].ravel()))
    low = filled[ix, iy] - DEPTH
    high = filled[ix, iy] + lift[ix, iy] - 0.012
    high[[0, -1], :] = filled[ix, iy][[0, -1], :] - 0.2
    high[:, [0, -1]] = filled[ix, iy][:, [0, -1]] - 0.2
    nx, ny = low.shape
    indices = np.arange(nx * ny).reshape(nx, ny)
    a, b = indices[:-1, :-1].ravel(), indices[1:, :-1].ravel()
    c, d = indices[1:, 1:].ravel(), indices[:-1, 1:].ravel()
    top = np.vstack((np.column_stack((a, b, c)), np.column_stack((a, c, d))))
    n = nx * ny
    rim_vertices = np.concatenate((indices[:-1, 0], indices[-1, :-1],
                                   indices[:0:-1, -1], indices[0, :0:-1]))
    start, end = rim_vertices, np.roll(rim_vertices, -1)
    sides = np.vstack((np.column_stack((start+n, end+n, end)), np.column_stack((start+n, end, start))))
    faces = np.vstack((top, (top+n)[:, ::-1], sides))
    vertices = np.vstack((np.column_stack((xy, high.ravel())), np.column_stack((xy, low.ravel()))))
    vertices[:, 2] *= region.direction
    if region.direction < 0:
        faces = faces[:, ::-1]
    solid = from_triangles(vertices, faces)
    return solid, {'region': region.name, 'max_lift_mm': float(lift.max()), 'cap_bounds_mm': solid.bounding_box()}


def write_solid(solid, path):
    mesh = solid.to_mesh64()
    value = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts, process=False)
    value.export(path)
    _, check, discarded = indexed_stl(path)
    if discarded:
        # Binary STL stores float32 coordinates. Omit any face collapsed by this rounding.
        check.export(path)
        _, check, discarded_again = indexed_stl(path)
        assert discarded_again == 0
    assert check.is_volume and check.body_count == 1
    return check, discarded


def protected_passages(params):
    extras = []
    for name in ('vacuum_boss_pad', 'vacuum_only_boss_pad'):
        _, cutters = cad.build_boss_pad_components(params['plenum'][name], params)
        extras.extend(cutters)
    extras.append(cad.build_iacv_components(params)['cutters'])
    fluid = airflow.extract_fluid_cavity(params)['fluid_solid']
    return cad.m_union([fluid, *extras])


def section_plot(original, candidate):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
    for ax, (origin, normal, keep, xlim, ylim, title, xlabel) in zip(axes.flat, (
        ((0,-92,0), (0,1,0), (0,2), (-123,-100), (-28,-4), 'Tie-bar, cylinder 1 side', 'X (mm)'),
        ((0,-92,0), (0,1,0), (0,2), (100,123), (-49,-26), 'Tie-bar, cylinder 4 side', 'X (mm)'),
        ((-52,0,0), (1,0,0), (1,2), (14,34), (32,53), 'Vacuum-only pad skirt', 'Y (mm)'),
        ((56,0,0), (1,0,0), (1,2), (14,34), (36,57), 'Boost-reference pad skirt', 'Y (mm)'),
    )):
        for mesh, label, color, line, width in ((original, 'Original', '#484d58', '--', 1.2),
                                                 (candidate, 'Codex blend', '#007d83', '-', 1.6)):
            section = mesh.section(plane_origin=origin, plane_normal=normal)
            for i, loop in enumerate(section.discrete):
                ax.plot(loop[:, keep[0]], loop[:, keep[1]], line, color=color, linewidth=width,
                        label=label if i == 0 else None)
        ax.set(xlim=xlim, ylim=ylim, title=title, xlabel=xlabel, ylabel='Z (mm)', aspect='equal')
        ax.grid(alpha=0.2)
    axes[0,0].legend(loc='upper right')
    fig.suptitle('Exterior blend cross-sections | SVT Stage-2 intake manifold', fontsize=15)
    fig.savefig(HERE / 'exterior_sections.png', dpi=170)
    plt.close(fig)


def mesh_metrics(mesh, path):
    return {
        'sha256': digest(path.read_bytes()), 'watertight': bool(mesh.is_watertight),
        'winding_consistent': bool(mesh.is_winding_consistent), 'is_volume': bool(mesh.is_volume),
        'body_count': int(mesh.body_count), 'faces': len(mesh.faces), 'bounds_mm': mesh.bounds.tolist(),
        'extent_mm': mesh.extents.tolist(), 'material_volume_mm3': float(mesh.volume),
    }


def interface_triangles(mesh, has_split_flange):
    triangles = mesh.triangles
    limits = triangles.min(axis=1), triangles.max(axis=1)
    groups = {
        'four_spigot_lands_and_beads': limits[1][:, 1] <= -119.0,
        'throttle_body_and_iacv': limits[0][:, 0] >= 135.0,
    }
    if has_split_flange:
        groups['split_flange_and_seals'] = ((limits[0][:, 0] >= -27.0) & (limits[1][:, 0] <= 27.0))
    result = {}
    for name, mask in groups.items():
        # Canonicalize vertices and face ordering for a coordinate-for-coordinate audit.
        xyz = triangles[mask]
        indices = np.lexsort((xyz[:, :, 2], xyz[:, :, 1], xyz[:, :, 0]), axis=1)
        coords = np.take_along_axis(xyz, indices[:, :, None], axis=1).reshape(-1, 9)
        result[name] = coords[np.lexsort(coords.T)]
    return result


def load_sources(params, names):
    src = HERE.parent / 'stl'
    manifest = json.loads((REFERENCE / 'manifest.json').read_text(encoding='utf-8'))['parts']
    generated = None
    models, metrics = {}, {}
    for name in names:
        expected = manifest[PREFIX + name]['sha256']
        path = src / f'{PREFIX}{name}.stl'
        data = path.read_bytes() if path.is_file() else b''
        if digest(data) != expected:
            if generated is None:
                generated = cad.assemble_all(params)
            data = cad.manifold_to_trimesh(generated[PREFIX + name]).export(file_type='stl')
        assert digest(data) == expected, f'Source version mismatch for {name}'
        raw, mesh, degenerate = indexed_stl(BytesIO(data))
        assert mesh.is_volume and mesh.body_count == 1
        metrics[name] = {'source_sha256': expected, 'source_zero_area_collapsed_faces': degenerate,
                         'source_triangles': len(raw.faces), 'source_bounds_mm': mesh.bounds.tolist()}
        models[name] = mesh
    return models, metrics


def main():
    out = HERE / 'stl'
    out.mkdir(exist_ok=True)
    params = json.loads((REFERENCE / 'intake_manifold_parameters.json').read_text(encoding='utf-8'))
    models, metrics = load_sources(params, (*ASSEMBLY_PARTS, *PRINT_PARTS))
    reference = models[ASSEMBLY_PARTS[0]]
    caps = [cap_for_region(reference, region) for region in regions(params)]
    passages = protected_passages(params)
    for solid, details in caps:
        details['passage_intersection_mm3'] = float((solid ^ passages).volume())
        assert abs(details['passage_intersection_mm3']) < VOLUME_EPS, details
    full_before = from_triangles(reference.vertices, reference.faces)
    print('Auditing and exporting the blend', flush=True)
    for name in ASSEMBLY_PARTS:
        original_mesh = models[name]
        original = full_before if name == ASSEMBLY_PARTS[0] else from_triangles(original_mesh.vertices, original_mesh.faces)
        side = 0 if name == ASSEMBLY_PARTS[0] else (-1 if name == ASSEMBLY_PARTS[1] else 1)
        additions = [solid for solid, _ in caps if side * sum(solid.bounding_box()[::3]) >= 0]
        combined = cad.m_union([original, *additions])
        shells = sorted(combined.decompose(), key=lambda shell: shell.volume(), reverse=True)
        candidate = shells[0]
        # The overlap can bridge a small reentrant crease and enclose a pocket.
        # The original has a single shell. Retain its exterior and test all solid changes below.
        discarded_mm3 = sum(abs(shell.volume()) for shell in shells[1:])
        path = out / f'{PREFIX}{name}_codex.stl'
        mesh, removed_faces = write_solid(candidate, path)
        reread = from_triangles(mesh.vertices, mesh.faces)
        added = reread - original
        removed = original - reread
        loss = float(removed.volume())
        assert abs(loss) < VOLUME_EPS, (name, loss)
        assert np.allclose(mesh.bounds, original_mesh.bounds, atol=0.00005, rtol=0), name
        changed_air = float((added ^ passages).volume())
        assert abs(changed_air) < VOLUME_EPS, (name, changed_air)
        before_interfaces = interface_triangles(original_mesh, has_split_flange=side != 0)
        after_interfaces = interface_triangles(mesh, has_split_flange=side != 0)
        interfaces = {key: {'source_faces': len(before_interfaces[key]),
                            'candidate_faces': len(after_interfaces[key]),
                            'exact_match': bool(np.array_equal(before_interfaces[key], after_interfaces[key]))}
                      for key in before_interfaces}
        seam = interfaces.get('split_flange_and_seals')
        if seam is not None:
            guard = md.Manifold.cube([54, 250, 200], center=True)
            seam['symmetric_difference_mm3'] = abs(float((added ^ guard).volume())) + abs(float((removed ^ guard).volume()))
            assert seam['symmetric_difference_mm3'] < VOLUME_EPS, (name, seam)
        assert all(interfaces[key]['exact_match'] for key in ('four_spigot_lands_and_beads', 'throttle_body_and_iacv')), (name, interfaces)
        metrics[name].update(mesh_metrics(mesh, path))
        metrics[name].update({'export_removed_collapsed_faces': removed_faces, 'added_material_mm3': float(added.volume()),
                              'removed_material_mm3': loss, 'added_material_in_passages_mm3': changed_air,
                              'discarded_secondary_shells': len(shells) - 1,
                              'discarded_secondary_shells_abs_mm3': discarded_mm3,
                              'protected_interface_triangles': interfaces})
        print(name, len(mesh.faces), added.volume(), loss, flush=True)
        if side == 0:
            section_plot(reference, mesh)
            continue
        print_name = PRINT_PARTS[0 if side == -1 else 1]
        print_part = reread.rotate([0, -90 * side, 0])
        bounds = np.asarray(print_part.bounding_box()).reshape(2, 3)
        shift = -bounds.mean(axis=0)
        shift[2] = -bounds[0, 2]
        print_path = out / f'{PREFIX}{print_name}_codex.stl'
        oriented, removed_faces = write_solid(print_part.translate(shift.tolist()), print_path)
        assert np.all(oriented.extents <= 256) and oriented.bounds[0, 2] == 0
        metrics[print_name].update(mesh_metrics(oriented, print_path))
        metrics[print_name]['export_removed_collapsed_faces'] = removed_faces
    evidence = {'blend_regions': [details for _, details in caps], 'parts': metrics}
    (HERE / 'mesh_validation.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
