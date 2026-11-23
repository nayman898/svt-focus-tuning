"""Measure internal down-facing surfaces and solid intrusion into the exported WOT cavity."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "validation"), str(HERE.parent)]
from wot_check import extract
from generate_iacv_revision import FULL, RIGHT, gen, make_route, mesh_solid, one_job, read_json, write_json

import numpy as np
import trimesh


def throat_mask(mesh, face, axis, base_x):
    xy = mesh.triangles_center
    behind = (face - xy) @ axis
    # Trim the two cap planes and use the physical plenum/neck junction as the rear boundary.
    return (behind > 0.1) & (xy[:, 0] >= base_x - 4) & (xy[:, 1] > -86)


def surface_audit(air, face, axis, params):
    mesh = gen.manifold_to_trimesh(air)
    mask = throat_mask(mesh, face, axis, params["plenum"]["cyl4_end_x_mm"])
    # The air-surface normal points toward the solid wall. Reverse its sign for printing.
    cosine = mesh.face_normals[:, 0]
    area = mesh.area_faces
    rows = {}
    for angle in (40, 45, 50, 55, 60, 65, 75, 80, 85):
        chosen = mask & (cosine > np.sin(np.deg2rad(angle)))
        depth = (face - mesh.triangles_center[chosen]) @ axis
        rows[str(angle)] = {"area_mm2": float(area[chosen].sum()), "faces": int(chosen.sum()),
                            "depth_mm": [float(depth.min()), float(depth.max())] if len(depth) else []}
    return rows


def check(folder, label):
    params = read_json(folder / "parameters.json")
    manifest = read_json(folder / "stl/manifest.json")
    fluid = extract(params)
    air = fluid["fluid_solid"]
    cfg = params["throttle_body"]["iacv_flange_feed"]
    tb = gen.build_throttle_body_components(params)
    feed = make_route(params, tb, cfg["round_transition_center_uv_mm"], cfg["route_path_xyz_mm"])["inner"]
    inward = -fluid["tb_axis"]
    feed = feed.trim_by_plane(inward, float(inward @ fluid["p_flange_face"]) + 0.02)
    result = {"design": label, "fluid_volume_cm3": air.volume() / 1000,
              "internal_downward_surfaces": surface_audit(
                  air, fluid["p_flange_face"], fluid["tb_axis"], params), "stl": {}}
    for key in (FULL, RIGHT):
        record = manifest["parts"][key]
        case = folder / record["file"]
        assert sha256(case.read_bytes()).hexdigest() == record["sha256"], case
        mesh = trimesh.load_mesh(case)
        assert mesh.is_volume and mesh.body_count == 1
        casting = mesh_solid(mesh)
        intrusion = casting ^ air
        feed_obstruction = abs((casting ^ feed).volume())
        assert feed_obstruction < 0.02, (case, feed_obstruction)
        # Ignore the mating seam and inspect the throttle neck pocket independently.
        near_neck = intrusion.trim_by_plane([1, 0, 0], params["plenum"]["cyl4_end_x_mm"] - 4)
        result["stl"][key] = {
            "sha256": record["sha256"], "solid_in_full_capped_wot_air_mm3": abs(intrusion.volume()),
            "solid_in_capped_iacv_feed_mm3": feed_obstruction,
            "solid_in_capped_neck_air_mm3": abs(near_neck.volume()),
            "neck_intrusions_over_0_001_mm3": [part.bounding_box() for part in near_neck.decompose()
                                               if abs(part.volume()) > 0.001],
        }
    write_json(HERE / f"{label}_throat_check.json", result)
    print(result, flush=True)


def split_check(folder):
    params = read_json(folder / "parameters.json")
    plenum = gen.build_plenum_loft(params, is_inner=True)
    split = gen.build_center_split_flange_and_cutters(params)
    removed = split["flange_ring"] ^ plenum
    seal_gap = removed.min_gap(split["oring_cutter"], 50)
    hardware_gap = removed.min_gap(split["hole_cutters"], 50)
    assert seal_gap > 0 and hardware_gap > 0, (seal_gap, hardware_gap)

    def stock(root):
        entry = read_json(root / "stl/manifest.json")["parts"][RIGHT]
        path = root / entry["file"]
        assert sha256(path.read_bytes()).hexdigest() == entry["sha256"], path
        return mesh_solid(trimesh.load_mesh(path))

    previous = stock(folder.parent / "refined")
    current = stock(folder)
    x_bounds = removed.bounding_box()[0], removed.bounding_box()[3]
    before, after, bare = (solid.rotate([0, -90, 0]) for solid in (plenum - previous, plenum - current, plenum))
    samples = []
    for x in np.linspace(0.05, x_bounds[1] + 0.5, 81):
        a, b, c = (solid.slice(float(x)).area() for solid in (before, after, bare))
        samples.append({"x_mm": x, "previous_open_mm2": a, "corrected_open_mm2": b, "bare_plenum_mm2": c})
    assert max(row["bare_plenum_mm2"] - row["corrected_open_mm2"] for row in samples) < 0.02
    output = {"split_trim_volume_native_mm3": removed.volume(), "trim_x_bounds_mm": x_bounds,
              "gap_to_split_seal_groove_mm": seal_gap, "gap_to_bolt_dowel_and_tool_cuts_mm": hardware_gap,
              "peak_area_recovered_mm2": max(row["corrected_open_mm2"] - row["previous_open_mm2"] for row in samples),
              "sections": samples}
    write_json(HERE / "split_joint_sections.json", output)
    print({k: v for k, v in output.items() if k != "sections"}, flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder", type=Path)
    cli.add_argument("label")
    cli.add_argument("--split", action="store_true")
    args = cli.parse_args()
    with one_job():
        check(args.folder, args.label)
        if args.split:
            split_check(args.folder)
