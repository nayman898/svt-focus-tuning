"""Compare the top and bottom flange-back shoulders directly in the exported meshes."""

from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from generate_iacv_revision import RIGHT, gen, mesh_solid, one_job, read_json, write_json

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, box
import trimesh


def load(root):
    params = read_json(root / "parameters.json")
    cfg = params["throttle_body"]
    record = read_json(root / "stl/manifest.json")["parts"][RIGHT]
    stl = root / record["file"]
    assert sha256(stl.read_bytes()).hexdigest() == record["sha256"]
    mesh = trimesh.load_mesh(stl)
    assert mesh.is_volume and mesh.body_count == 1
    *_, face, axis = gen.tb_neck_bezier_points(params)
    u, v, offset = gen.throttle_mounting_frame(axis, cfg)
    frame = np.stack([u, v, axis])
    solid = mesh_solid(mesh).transform(np.column_stack((frame, -frame @ (face + offset))))
    return solid, cfg, record["sha256"]


def section(solid, depth):
    result = Polygon()
    for loop in solid.slice(-depth).to_polygons():
        if len(loop) >= 3:
            result = result.symmetric_difference(Polygon(loop).buffer(0))
    return result


def draw(ax, shape, color):
    polygons = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
    for polygon in polygons:
        if polygon.geom_type != "Polygon" or polygon.is_empty:
            continue
        ax.fill(*polygon.exterior.xy, color=color)
        for hole in polygon.interiors:
            ax.fill(*hole.xy, color="white")


def main():
    previous, a, old_hash = load(HERE.parent / "refined")
    corrected, b, new_hash = load(HERE.parent / "flange_corrected")
    keys = ("flange_width_mm", "flange_height_mm", "flange_corner_radius_mm")
    assert all(a[k] == b[k] for k in keys)
    w, h, r = (b[k] for k in keys)
    profile = Polygon(gen.rounded_rect_points(w, h, r, 192))
    window = profile.buffer(6)
    clearance = profile.buffer(0.03)
    data = []
    for d in (0.1, 9.5, 10.0, 10.8, 11.9, 12.1, 13.0, 14.0, 16.0, 18.0, 20.0, 22.0):
        sections = [section(solid, d).intersection(window) for solid in (previous, corrected)]
        removed = sections[0].difference(sections[1])
        data.append({"behind_face_mm": d, "profile_band_outside_area_before_after_mm2":
                     [s.difference(clearance).area for s in sections], "removed_mm2": removed.area})
    depth = 11.9
    old, new = [section(solid, depth).intersection(window) for solid in (previous, corrected)]
    # The nearby bracket and IACV shell can also intersect this plane. Highlight only removed material.
    removed = old.difference(new).difference(clearance)
    assert removed.area > 75 and (new.difference(old).area < 0.02), removed.area
    figure, axes = plt.subplots(1, 2, figsize=(8.5, 4.3), layout="constrained")
    for ax, solid, title in zip(axes, (old, new), ("Previous flange", "Corrected flange"), strict=True):
        draw(ax, solid, "#258291")
        if ax is axes[0]:
            draw(ax, removed, "#d75828")
        ax.plot(*profile.exterior.xy, color="#172b39", ls="--", lw=1, label="Square face outline")
        ax.set(xlim=(-w/2-7, w/2+7), ylim=(-h/2-7, h/2+7), aspect="equal", title=title,
               xlabel="Bolt-grid U (mm)")
        ax.legend(loc="upper right", fontsize=7)
    axes[0].set_ylabel("Bolt-grid V (mm)")
    figure.suptitle("Exported STL sections 11.9 mm behind the throttle face\nOrange shows the removed lip")
    figure.savefig(HERE / "flange_back_comparison.png", dpi=180)
    write_json(HERE / "flange_sections.json", {"previous_sha256": old_hash, "corrected_sha256": new_hash,
                "sections": data, "highlighted_removed_area_mm2": removed.area})
    print("Removed lip in STL section, mm²", removed.area, flush=True)


if __name__ == "__main__":
    with one_job():
        main()
