"""Measure the released V2 STLs against the frozen pre-Codex parametric V2."""

import hashlib
import json
from pathlib import Path
import sys

import manifold3d as md
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import trimesh
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / "reference"))

import generate_intake_manifold_v2 as original
import generate_intake_manifold_v2_codex as codex
import verify_airflow_v2 as flow


FULL = "svt_intake_manifold_v2_1piece_full"
LEFT = "svt_intake_manifold_v2_split_left_cyl1_2"
RIGHT = "svt_intake_manifold_v2_split_right_cyl3_4_tb"


def mesh_solid(mesh):
    return md.Manifold(md.Mesh64(np.ascontiguousarray(mesh.vertices, dtype="f8"),
                                  np.ascontiguousarray(mesh.faces, dtype="u8")))


def volume_difference(a, b):
    return abs((a-b).volume()) + abs((b-a).volume())


def throat_frame(face, axis):
    u = np.cross([0, 0, 1], axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    return np.stack((u, v, axis)), np.column_stack((u, v))


def area_profile(cavity, face, frame):
    distances = np.arange(0.75, 66, 0.75)
    local = cavity.transform(np.column_stack((frame, -frame@face)))
    areas = np.array([local.slice(-distance).area() for distance in distances])
    slope = np.gradient(areas, 0.75)
    curvature = np.gradient(slope, 0.75)
    return {"distance_behind_face_mm": distances.tolist(), "area_mm2": areas.tolist(),
            "area_slope_mm2_per_mm": slope.tolist(), "min_area_mm2": float(areas.min()),
            "max_area_slope_mm2_per_mm": float(slope.max()),
            "rms_area_second_derivative": float(np.sqrt(np.mean(curvature**2))),
            "peak_abs_area_second_derivative": float(np.max(np.abs(curvature)))}


def rear_socket_checks(gen, body, config):
    *_, back, face, axis = gen.tb_neck_bezier_points(config)
    _, directions = throat_frame(face, axis)
    bx = config["throttle_body"]["bolt_spacing_x_mm"]/2
    by = config["throttle_body"]["bolt_spacing_y_mm"]/2
    bore_offset = config["throttle_body"].get("bore_from_bolt_grid_uv_mm", [0, 0])
    bolt_radius = config["throttle_body"]["bolt_hole_diameter_mm"]/2
    overlaps = []
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        center = back + directions @ (np.array([sx*bx, sy*by])-bore_offset)
        probe = gen.make_cylinder_along(center-12.5*axis, center-0.3*axis, 6.2, 24)
        seat = gen.make_cylinder_along(center+0.04*axis, center+0.28*axis, 6.2, 72)
        pilot = gen.make_cylinder_along(center-axis, center+axis, bolt_radius+0.02, 72)
        annulus = seat - pilot
        overlaps.append({"bolt_uv_signs": [sx, sy], "interference_mm3": abs((body ^ probe).volume()),
                         "rear_washer_annulus_support_fraction": (body ^ annulus).volume()/annulus.volume()})
    return overlaps


def check_fit_gauge(path, tb):
    gauge = mesh_solid(trimesh.load_mesh(path))
    loops = [Polygon(p) for p in gauge.slice(2).to_polygons()]
    assert len(loops) == 6, path
    plate, bore, *holes = sorted(loops, key=lambda p: p.area, reverse=True)
    centers = sorted([[float(h.centroid.x), float(h.centroid.y)] for h in holes])
    bore_center = [float(bore.centroid.x), float(bore.centroid.y)]
    pitch = np.ptp(centers, axis=0)
    diameter = [float(p.bounds[2]-p.bounds[0]) for p in holes]
    assert np.allclose(pitch, [tb["bolt_spacing_x_mm"], tb["bolt_spacing_y_mm"]], atol=0.01, rtol=0)
    assert np.allclose(bore_center, tb["bore_from_bolt_grid_uv_mm"], atol=0.01, rtol=0)
    assert np.allclose(diameter, tb["bolt_hole_diameter_mm"], atol=0.01, rtol=0)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="150mm" height="151mm" viewBox="0 0 150 151">',
        '<rect width="150" height="151" fill="white"/>',
        '<g font-family="sans-serif" fill="#18252e" text-anchor="middle">',
        '<text x="75" y="9" font-size="5" font-weight="bold">BBK throttle-body fit gauge</text>',
        '<text x="75" y="15" font-size="3.1">79 × 79 mm pitch · four Ø7 mm holes · Ø65 mm bore</text>',
        '<text x="75" y="22.5" font-size="3.1">HOOD +V</text>',
        '<text x="75" y="132.5" font-size="3.1">GROUND −V</text>',
        '<text x="22" y="76" font-size="2.8" text-anchor="end">RADIATOR</text>',
        '<text x="127" y="76" font-size="2.8" text-anchor="start">FIREWALL</text>',
        '<text x="75" y="138" font-size="3">Bore center 5 mm toward firewall, 7 mm toward ground</text>',
        '<text x="75" y="143" font-size="2.8">Print at 100% and check the scale bar</text>',
        '<text x="75" y="150" font-size="2.6">25 mm</text></g>',
        '<g fill="none" stroke="#252a34" stroke-width="0.24">',
        '<path d="M62.5 147h25m-25 -0.8v1.6m25 -1.6v1.6"/>',
    ]
    for polygon in (plate, bore, *holes):
        points = " ".join(f"{75+x:.3f},{77-y:.3f}" for x, y in polygon.exterior.coords)
        lines.append(f'<polygon points="{points}"/>')
    lines.append('</g></svg>')
    (HERE/"fitment"/"bbk_throttle_pattern_1to1.svg").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return {"bolt_centers_uv_mm": centers, "bolt_pitch_mm": pitch.tolist(), "measured_hole_diameter_mm": diameter,
            "bore_center_uv_mm": bore_center, "plate_dimensions_mm": list(plate.bounds)}


def draw_sections(cavities, profiles, face, frame):
    out = HERE/"fitment"/"07_throttle_neck_comparison.png"
    fig, ax = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    u, v, axis = frame
    for cavity, stats, label, color, line in zip(cavities, profiles,
                                               ("Current Gemini V2 CAD", "Codex V2"),
                                               ("#596373", "#007b74"), ("--", "-")):
        ax[0, 0].plot(stats["distance_behind_face_mm"], stats["area_mm2"], line,
                      color=color, linewidth=2, label=label)
        ax[0, 1].plot(stats["distance_behind_face_mm"], stats["area_slope_mm2_per_mm"], line,
                      color=color, linewidth=2)
        mesh = codex.manifold_to_trimesh(cavity)
        for axis_plot, normal, radial in ((ax[1, 0], v, u), (ax[1, 1], u, v)):
            xyz = trimesh.intersections.mesh_plane(mesh, normal, face)
            lines = (xyz - face) @ np.column_stack((-axis, radial))
            axis_plot.add_collection(LineCollection(lines, colors=color, linestyles=line, linewidths=1.6))
    for pane, title, ylabel in ((ax[0, 0], "Section area", "Area (mm²)"),
                               (ax[0, 1], "Rate of area expansion", "Area change (mm²/mm)"),
                               (ax[1, 0], "Section through yaw direction", "Lateral offset (mm)"),
                               (ax[1, 1], "Section through pitch direction", "Vertical offset (mm)")):
        pane.set(xlim=(0, 65.3), title=title, xlabel="Distance behind throttle face (mm)", ylabel=ylabel)
        pane.grid(alpha=0.2)
    ax[0, 0].legend()
    ax[1, 0].set_ylim(-68, 49)
    ax[1, 1].set_ylim(-56, 48)
    fig.suptitle("Focus SVT V2 throttle neck | Before and after", fontsize=16)
    fig.savefig(out, dpi=165)
    plt.close(fig)


def cable_clearance(gen, cad, config, iacv):
    bracket = cad["_cable_parts"]
    neck = gen.build_throttle_body_components(config)["outer"]
    *_, back, face, axis = gen.tb_neck_bezier_points(config)
    flange = neck.trim_by_plane(axis, float(axis@back))
    upper_posts = bracket["outer"].trim_by_plane([0,0,1], 55.0)
    upper_pad = iacv["outer"].trim_by_plane([0,0,1], 55.0)
    p = config["throttle_body"]["iacv_mount"]
    valve_footprint = gen.make_rounded_prism(p["pad_length_x_mm"], p["pad_width_y_mm"], p["pad_corner_radius_mm"],
                                           20, segments=128, center=(p["x_center_mm"], p["y_center_mm"], p["top_z_mm"]+10), axis="z")
    result = {
        "bolt_centers_world_xyz_mm": [[float(x),float(y),bracket["top_z"]] for x,y,_ in bracket["hole_bottoms"]],
        "pilot_depth_mm": config["throttle_body"]["cable_bracket_boss"]["bolt_depth_mm"],
        "intersection_with_iacv_pad_mm3": abs((bracket["outer"] ^ iacv["outer"]).volume()),
        "intersection_of_pilots_with_iacv_pad_mm3": abs((bracket["cutters"] ^ iacv["outer"]).volume()),
        "closest_to_iacv_pad_mm": bracket["outer"].min_gap(iacv["outer"], 20),
        "upper_posts_to_iacv_pad_mm": upper_posts.min_gap(iacv["outer"], 20),
        "posts_to_extruded_iacv_mounting_footprint_mm": bracket["outer"].min_gap(valve_footprint, 20),
        "closest_to_throttle_flange_mm": bracket["outer"].min_gap(flange, 20),
    }
    if gen is codex:
        result["post_foot_overlap_with_neck_mm3"] = [abs((post ^ neck).volume()) for post in bracket["posts"]]
        assert result["intersection_with_iacv_pad_mm3"] == 0 and result["intersection_of_pilots_with_iacv_pad_mm3"] == 0
        assert result["closest_to_throttle_flange_mm"] > 0
        assert all(v > 0 for v in result["post_foot_overlap_with_neck_mm3"])
    return result, (upper_pad, upper_posts, flange, result["bolt_centers_world_xyz_mm"])


def draw_cable_sections(views):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), layout="constrained", sharex=True, sharey=True)
    for ax, (iacv, bracket, flange, centers), title in zip(axes, views, ("Frozen Gemini V2", "Codex V2")):
        for solid, color, label in ((flange, "#87929e", "Throttle flange"), (iacv, "#2872a1", "IACV pad"),
                                    (bracket, "#d57b26", "Cable bracket mount")):
            for index, polygon in enumerate(solid.slice(61.0).to_polygons()):
                ax.fill(*np.asarray(polygon).T, color=color, alpha=.46, label=label if index == 0 else None)
        ax.scatter(*np.asarray(centers)[:, :2].T, color="#28190e", s=20, marker="+", zorder=5, label="Pilot centers")
        ax.set(title=title, xlim=(121, 252), ylim=(-93, 55), xlabel="X along plenum (mm)", aspect="equal")
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Y toward firewall (mm)")
    axes[1].legend(loc="lower left", fontsize=8)
    fig.suptitle("Cable bracket clearance | Horizontal section at Z = 61 mm", fontsize=14)
    fig.savefig(HERE/"fitment"/"08_cable_bracket_clearance.png", dpi=170)
    plt.close(fig)


def main():
    hashes = json.loads((HERE/"reference"/"gemini_sha256.json").read_text(encoding="utf-8"))
    source_check = {name: (HERE.parent/name).is_file() and hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest() == digest
                    for name, digest in hashes.items()}
    for name in ("generate_intake_manifold_v2.py", "verify_airflow_v2.py", "intake_manifold_v2_parameters.json", "stl/manifest.json"):
        assert hashlib.sha256((HERE/"reference"/Path(name).name).read_bytes()).hexdigest() == hashes[name], name
    report = {"live_gemini_files_matching_the_frozen_snapshot": source_check, "designs": {}}
    manifest = json.loads((HERE/"stl"/"manifest.json").read_text(encoding="utf-8"))
    cavities, profiles, assemblies, full_bodies, bracket_views = [], [], [], [], []
    for label, gen in (("gemini_v2_current_cad", original), ("codex_v2", codex)):
        config = json.loads(gen.PARAMS_PATH.read_text(encoding="utf-8"))
        print(f"Checking {label}", flush=True)
        cad = gen.assemble_all(config)
        assemblies.append(cad)
        full_body = cad[FULL]
        right_body = cad[RIGHT]
        *_, face, axis = gen.tb_neck_bezier_points(config)
        frame, _ = throat_frame(face, axis)
        # Compare the main neck with the same plenum reference and the physical face plane.
        cavity = gen.m_union([cad["_plenum_inner_cavity"], cad["_tb_bore_solid"]]).trim_by_plane(-axis, float((-axis)@face))
        profile = area_profile(cavity, face, frame)
        cavities.append(cavity)
        profiles.append(profile)
        flow.gen = gen
        air = flow.extract_fluid_cavity(config)["fluid_solid"]
        if gen is codex:
            # Validate re-imported STL volumes in the normal assembly axes.
            checked = {}
            for name, row in manifest["parts"].items():
                path = HERE/row["file"]
                assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], name
                mesh = trimesh.load_mesh(path)
                assert mesh.is_volume and mesh.body_count == 1 and mesh.is_winding_consistent, name
                if name in (FULL, RIGHT):
                    solid = mesh_solid(mesh)
                    assert solid.status() == md.Error.NoError, name
                    checked[name] = solid
            full_body, right_body = checked[FULL], checked[RIGHT]
        full_bodies.append(full_body)
        iacv = gen.build_iacv_components(config)
        bracket_clearance, bracket_view = cable_clearance(gen, cad, config, iacv)
        bracket_views.append(bracket_view)
        pocket_z = config["throttle_body"]["iacv_mount"]["supply_pocket_bottom_z_mm"]
        supply, = [piece for piece in iacv["cutters"].decompose() if abs(piece.bounding_box()[2] - pocket_z) < 1e-4]
        sockets = rear_socket_checks(gen, right_body, config)
        intrusion = abs((full_body ^ air).volume())
        cable = cad["_cable_parts"]["cutters"]
        report["designs"][label] = {
            "throttle_face_center_mm": face.tolist(), "throttle_axis": axis.tolist(),
            "throttle_neck": profile, "air_cavity_volume_cm3": air.volume()/1000,
            "solid_intrusion_in_capped_main_air_domain_mm3": intrusion, "assembly_bounds_mm": full_body.bounding_box(),
            "socket_probe_diameter_mm": 12.4, "socket_probe_axial_reach_mm": 12.5, "socket_probes": sockets,
            "cable_pilot_min_gap_to_main_air_mm": cable.min_gap(air, 25.0),
            "cable_bracket_clearance": bracket_clearance,
            "iacv_supply_min_gap_to_main_air_mm": supply.min_gap(air, 25.0),
        }
        if gen is codex:
            assert all(row["interference_mm3"] < 0.05 for row in sockets), sockets
            assert all(row["rear_washer_annulus_support_fraction"] >= 0.995 for row in sockets), sockets
            assert intrusion < 0.1, intrusion
            assert profile["min_area_mm2"] >= 3317.0, profile["min_area_mm2"]
            assert cable.min_gap(air, 25.0) >= 4.5
            assert supply.min_gap(air, 25.0) >= 4.5
            gauge_name = manifest["parts"]["svt_v2_tb_flange_fit_gauge"]["file"]
            report["fit_gauge"] = check_fit_gauge(HERE/gauge_name, config["throttle_body"])

    a, b = full_bodies
    a_cad, b_cad = assemblies
    # Keep the bore and seal ring in the flange comparison. The attachment pattern and outline intentionally move.
    guard = codex.make_cylinder_along(face-4*axis, face+axis, 40.0, 128)
    report["preserved_interface_symmetric_difference_mm3"] = {
        "complete_left_half_in_assembly_axes": volume_difference(a_cad[LEFT], b_cad[LEFT]),
        "boot_lands_and_retention_beads": volume_difference(a.trim_by_plane([0,-1,0], 119), b.trim_by_plane([0,-1,0], 119)),
        "throttle_bore_and_face_seal_land": volume_difference(a ^ guard, b ^ guard),
    }
    assert max(report["preserved_interface_symmetric_difference_mm3"].values()) < 0.05, report["preserved_interface_symmetric_difference_mm3"]
    old_mesh = trimesh.load_mesh(HERE.parent/"stl"/f"{FULL}.stl")
    representative = int(np.argmax(np.where(old_mesh.face_normals@axis > 0.999999, old_mesh.area_faces, 0)))
    old_datum = float(old_mesh.triangles_center[representative]@axis)
    report["live_export_throttle_plane_datum_mm"] = old_datum
    report["current_parametric_throttle_plane_datum_mm"] = float(face@axis)
    (HERE/"geometry_validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    draw_sections(cavities, profiles, face, frame)
    draw_cable_sections(bracket_views)
    print(report["preserved_interface_symmetric_difference_mm3"], flush=True)


if __name__ == "__main__":
    main()
