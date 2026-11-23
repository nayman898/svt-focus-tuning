"""Locate the cable-bracket pilots and export a coupon from the released right half."""

from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from generate_iacv_revision import RIGHT, gen, mesh_solid, one_job, read_json

import manifold3d as md
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
import trimesh


def plot_mount(path, blank, plate, pad, holes, face):
    figure, ax = plt.subplots(figsize=(7.8, 7), layout="constrained")
    outline = md.CrossSection(blank.project().to_polygons(), md.FillRule.Positive)
    for loop in outline.to_polygons():
        ax.fill(*np.asarray(loop).T, color="#dce5ec", ec="#7990a2", lw=1)
    ax.plot(*plate.T, lw=2, color="#415b70")
    ax.plot(*pad.T, ls="--", color="#738a9b", lw=1.3)
    ax.text(float(pad[:, 0].mean()), float(pad[:, 1].mean()), "IACV pad", ha="center", va="center")
    ax.text(234, -68, "Throttle\nmating face", color="#415b70", ha="left")
    ax.annotate("", xy=face[:2], xytext=(235, -58), arrowprops={"arrowstyle": "->", "color": "#415b70"})
    for i, ((x, y, _), label) in enumerate(zip(holes, ("A · firewall side", "B · radiator side"), strict=True)):
        ax.add_patch(plt.Circle((x, y), 7.5, color="#137a74", alpha=0.24))
        ax.add_patch(plt.Circle((x, y), 2.6, color="#137a74"))
        pos = (201, 11) if i == 0 else (131, -68)
        ax.annotate(label, xy=(x, y), xytext=pos, color="#12544e", weight="bold",
                    arrowprops={"arrowstyle": "->", "color": "#12544e"})
    ax.plot(*holes[:, :2].T, lw=1, ls=":", color="#12544e")
    ax.text(182, -51, "28.00 mm", color="#12544e", fontsize=10)
    ax.set(xlabel="X toward cylinder 4 (mm)", ylabel="Y toward firewall (mm)",
           aspect="equal", xlim=(119, 262), ylim=(-96, 64))
    ax.grid(alpha=0.18)
    figure.suptitle("Throttle cable bracket on the corrected Codex V2\nTop view with the pilot centers marked")
    figure.savefig(path, dpi=180)
    plt.close(figure)


def main():
    root = HERE.parent / "flange_corrected"
    params = read_json(root / "parameters.json")
    cfg = params["throttle_body"]
    entry = read_json(root / "stl/manifest.json")["parts"][RIGHT]
    stl = root / entry["file"]
    assert sha256(stl.read_bytes()).hexdigest() == entry["sha256"]
    casting = mesh_solid(trimesh.load_mesh(stl))
    throttle = gen.build_throttle_body_components(params)
    cable = gen.build_cable_bracket_boss_components(params, throttle["outer"])
    holes = np.asarray(cable["hole_bottoms"])
    holes[:, 2] = cable["top_z"]
    assert np.isclose(np.linalg.norm(holes[0] - holes[1]), 28)
    # Confirm the holes in the exported part at the seating plane and below each blind pilot.
    for z in (cable["top_z"] - 0.2, cable["top_z"] - 9.85):
        contours = [Polygon(loop) for loop in casting.slice(z).to_polygons() if len(loop) >= 3]
        for x, y, _ in holes:
            nearest = min(contours, key=lambda p: (p.centroid.x - x)**2 + (p.centroid.y - y)**2)
            assert np.allclose(nearest.centroid.coords[0], (x, y), atol=0.01, rtol=0)
            assert np.isclose(nearest.bounds[2] - nearest.bounds[0], 5.2, atol=0.03)

    face, axis = throttle["flange_face_center"], throttle["tb_axis"]
    u, v, offset = gen.throttle_mounting_frame(axis, cfg)
    plate = gen.rounded_rect_points(cfg["flange_width_mm"], cfg["flange_height_mm"],
                                   cfg["flange_corner_radius_mm"], 96)
    plate = face + offset + np.concatenate((plate, plate[:1])) @ np.stack([u, v])
    iacv = cfg["iacv_mount"]
    pad = gen.rounded_rect_points(iacv["pad_length_x_mm"], iacv["pad_width_y_mm"], iacv["pad_corner_radius_mm"], 96)
    pad = np.concatenate((pad, pad[:1])) + [iacv["x_center_mm"], iacv["y_center_mm"]]

    # Match the neck coupon's crop and keep the full IACV mounting deck.
    x_cut = min(125, float(pad[:, 0].min()) - 2)
    y_cut = float(throttle["outer"].bounding_box()[1]) - 2
    blank = casting.trim_by_plane([1, 0, 0], x_cut).trim_by_plane([0, 1, 0], y_cut)
    assert len(blank.decompose()) == 1
    assert np.min(plate[:, 0]) > x_cut and np.min(plate[:, 1]) > y_cut
    assert np.min(pad[:, 0]) > x_cut and np.min(pad[:, 1]) > y_cut
    coupon = blank.rotate([0, -90, 0])
    x0, y0, z0, x1, y1, _ = coupon.bounding_box()
    coupon = coupon.translate([-(x0 + x1) / 2, -(y0 + y1) / 2, -z0])

    folder = root / "fitment"
    with TemporaryDirectory(prefix=".cable-bracket-", dir=folder) as work:
        sample = Path(work) / "svt_v2_cable_bracket_fit_coupon.stl"
        view = Path(work) / "cable_bracket_mount.png"
        try:
            mesh, _ = gen.export_checked_stl(coupon, sample)
        except ValueError:
            mesh, _ = gen.export_checked_stl(coupon.simplify(0.0001), sample)
        plot_mount(view, blank, plate[:, :2], pad, holes, face)
        sample.replace(folder / sample.name)
        view.replace(folder / view.name)
    print("Pilot centers in assembly XYZ (mm)", holes.tolist())
    print("Perpendicular setbacks from the throttle mating plane (mm)", ((face - holes) @ axis).tolist())
    print("Coupon size (mm)", mesh.extents.tolist())


if __name__ == "__main__":
    with one_job():
        main()
