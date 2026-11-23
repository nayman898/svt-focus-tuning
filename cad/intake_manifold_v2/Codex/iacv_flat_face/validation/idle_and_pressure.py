"""Measure the actual IACV passage and screen flow and pressure loads."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from generate_iacv_revision import deck_seal_land, gen, make_route, one_job, read_json, write_json

import numpy as np
from shapely.geometry import Point, Polygon

PA_PER_PSI = 6894.757
GRAMS_SEC_PER_LB_MIN = 453.59237 / 60


def section(solid, center, normal, pick_center):
    normal = normal / np.linalg.norm(normal)
    u = np.cross([0, 0, 1], normal)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    frame = np.stack((u, v, normal))
    loops = solid.transform(np.column_stack((frame, -frame @ center))).slice(0).to_polygons()
    polygons = [Polygon(p) for p in loops]
    if pick_center:
        polygons = [p for p in polygons if p.covers(Point(0, 0))]
    assert polygons
    selected = max(polygons, key=lambda p: p.area)
    return selected.area, selected.length


def loss_at_flow(grams_s, area, diameter, length, minor_k, roughness, temp, pressure):
    r_air = 287.05
    mu = 1.90e-5
    mass = grams_s / 1000
    re = mass * diameter / (mu * area)
    friction_factor = (-1.8 * np.log10((roughness / (3.7 * diameter))**1.11 + 6.9 / re))**-2
    loss_coefficient = minor_k + friction_factor * length / diameter
    density = pressure / (r_air * temp)
    velocity = mass / (density * area)
    p_sq = pressure**2 - loss_coefficient * r_air * temp * (mass / area)**2
    return {"reynolds": re, "inlet_velocity_m_s": velocity, "friction_factor": friction_factor,
            "total_loss_coefficient": loss_coefficient,
            "duct_pressure_loss_kpa": None if p_sq < 0 else (pressure - np.sqrt(p_sq))/1000}


def analyze(params_path, output):
    params = read_json(params_path)
    cfg = params["throttle_body"]["iacv_flange_feed"]
    tb, _ = deck_seal_land(params, gen.build_throttle_body_components(params))
    route = make_route(params, tb, cfg["round_transition_center_uv_mm"], cfg["route_path_xyz_mm"])
    duct = route["inner"]
    assert len(duct.decompose()) == 1
    face, axis = tb["flange_face_center"], tb["tb_axis"]
    points = []
    for depth in np.linspace(0, 10.75, 24):
        area, perimeter = section(duct, face - axis * depth, axis, pick_center=False)
        points.append({"section": "face_adapter", "station_mm": float(depth), "area_mm2": area,
                       "hydraulic_diameter_mm": 4 * area / perimeter})
    t = np.linspace(0.5, route["centerline_length_mm"] - 0.5, 81)
    curve = route["centerline"]
    for distance, position, direction in zip(t, curve(t), curve(t, 1), strict=True):
        area, perimeter = section(duct, position, direction, pick_center=True)
        points.append({"section": "duct_centerline", "station_mm": distance, "area_mm2": area,
                       "hydraulic_diameter_mm": 4 * area / perimeter})
    worst_section = min(points, key=lambda row: row["area_mm2"])
    diameter_min = min(row["hydraulic_diameter_mm"] for row in points)
    sample = np.unique(np.r_[np.linspace(0, route["centerline_length_mm"], 1201), curve.x])
    length = 11 + float(np.linalg.norm(np.diff(curve(sample), axis=0), axis=1).sum())
    derivative = curve(sample, 1)
    curvature = np.linalg.norm(np.cross(derivative, curve(sample, 2)), axis=1) / np.linalg.norm(derivative, axis=1)**3
    area_m2 = worst_section["area_mm2"] * 1e-6
    diameter_m = diameter_min * 1e-3

    air_pressure, air_temperature, gas_r, gamma = 101325, 320, 287.05, 1.4
    ideal_choked = (area_m2 * air_pressure / np.sqrt(air_temperature) *
                    np.sqrt(gamma / gas_r) * (2 / (gamma + 1))**((gamma + 1) / (2 * (gamma - 1))))
    idle_loss_cases = []
    for lb_min in (0.587, 0.85, 1.39):
        demand = lb_min * GRAMS_SEC_PER_LB_MIN
        for minor_k in (2, 5, 10):
            modeled = loss_at_flow(demand, area_m2, diameter_m, length / 1000, minor_k, 0.00015,
                                   air_temperature, air_pressure)
            idle_loss_cases.append({"engine_airflow_lb_min": lb_min, "all_through_duct_g_s": demand,
                                    "assumed_minor_loss_coefficient": minor_k, **modeled})
    plenum = gen.build_plenum_loft(params, is_inner=True)
    split_bore = plenum.rotate([0, -90, 0]).slice(0).area()
    bore_section, _ = section(tb["tb_bore"], face - 0.5 * axis, axis, pick_center=True)
    feed_section = points[0]["area_mm2"]
    r_inner = cfg["duct_diameter_mm"] / 2
    r_outer = r_inner + cfg["duct_wall_mm"]
    pressure_cases = []
    for psi in (18, 25):
        p_mpa = psi * PA_PER_PSI / 1e6
        pressure_cases.append({
            "differential_pressure_psig": psi,
            "nominal_isolated_duct_hoop_stress_mpa": p_mpa * (r_inner**2 + r_outer**2) / (r_outer**2 - r_inner**2),
            "main_flange_force_n_pressure_only": p_mpa * bore_section,
            "iacv_feed_force_n_pressure_only": p_mpa * feed_section,
            "plenum_split_force_n_pressure_only": p_mpa * split_bore,
        })
    report = {
        "source_params_sha256": sha256(params_path.read_bytes()).hexdigest(),
        "centerline_length_mm_including_adapter": length, "minimum_spline_centerline_bend_radius_mm": 1 / curvature.max(),
        "minimum_sampled_flow_section": worst_section, "minimum_sampled_hydraulic_diameter_mm": diameter_min,
        "sampled_sections": points, "inlet_pressure_kpa_abs": air_pressure / 1000, "inlet_temperature_k": air_temperature,
        "logged_v024_return_vacuum_psig": -7.29, "tapped_pressure_difference_at_logged_return_kpa": 7.29 * PA_PER_PSI / 1000,
        "ideal_choked_flow_g_s_assuming_cd_1": ideal_choked * 1000,
        "duct_roughness_assumption_mm": 0.15, "duct_loss_screens": idle_loss_cases,
        "pressure_load_screens": pressure_cases,
    }
    write_json(output, report)
    print({k: v for k, v in report.items() if k != "sampled_sections"}, flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("parameters", type=Path)
    cli.add_argument("--output", type=Path, default=HERE / "idle_and_pressure_results.json")
    args = cli.parse_args()
    with one_job():
        analyze(args.parameters, args.output)
