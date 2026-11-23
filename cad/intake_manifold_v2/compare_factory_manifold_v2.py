#!/usr/bin/env python3
"""
Engineering & Airflow Comparison:
Custom Stage-2 V2 Engine-Bay Packaged Upper Manifold (Dropped -68 mm Plenum, 32°/-Y + 14°/+Z TB, Ø50.8/Ø42.8 Round)
vs. Factory 2002-2004 Ford Focus SVT / ST170 Dual-Stage Intake (DSI) Manifold.

Outputs (inside cad/intake_manifold_v2/):
  stl/factory_comparison.json
  fitment/04_factory_vs_custom_comparison_v2.png
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_airflow_v2 as va

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_v2_parameters.json"
MANIFEST_PATH = ROOT / "stl" / "manifest.json"
VERIF_PATH = ROOT / "stl" / "airflow_verification.json"
STL_1PC_PATH = ROOT / "stl" / "svt_intake_manifold_v2_1piece_full.stl"
OUT_JSON = ROOT / "stl" / "factory_comparison.json"
OUT_PNG = ROOT / "fitment" / "04_factory_vs_custom_comparison_v2.png"

LOGGED_V037_POINTS = [
    {"label": "v037 Pull 5 (10.2 psi)", "rpm": 4886.0, "lbmin": 22.32, "boost_psi": 10.22},
    {"label": "v037 Pull 2 (18.33 psi)", "rpm": 5978.0, "lbmin": 35.91, "boost_psi": 18.33},
    {"label": "v037 Pull 6 Peak (18.04 psi)", "rpm": 6397.0, "lbmin": 37.85, "boost_psi": 18.04},
]

OEM_UPPER_DSI_MASS_KG = 3.63
OEM_PA66_GF30_K_W_MK = 0.40
CUSTOM_CF_PA_DENSITY_G_CM3 = 1.26
CUSTOM_HARDWARE_MASS_KG = 0.18
CUSTOM_CF_PA_K_W_MK = 0.90


def simulate_oem_dsi_point(mode: str, rpm: float) -> dict:
    """1D Compressible + 720-deg Crank-Angle Pulsating solver for Factory SVT DSI upper manifold."""
    is_long = mode == "long"
    l_upper_m = 0.340 if is_long else 0.185
    l_total_acoustic_m = 0.475 if is_long else 0.320
    d_exit_m = 0.0428
    a_exit = math.pi * 0.25 * d_exit_m**2
    a_throat = math.pi * 0.25 * (0.0420 if is_long else 0.0430) ** 2

    eps_molded_m = 0.000018
    v_plenum, a_pl, dh_pl = 0.00220, 0.00580, 4.0 * 0.00580 / 0.290
    beta_cyl = np.full(4, 0.18 if is_long else 0.12)
    a_tb = math.pi * 0.25 * (0.065**2)
    disp_m3 = va.ENGINE_DISP_L * 1e-3
    mdot_total_ref = va.RHO0 * disp_m3 * (rpm / 120.0) * va.VE_REF
    mdot_cyl_ref = mdot_total_ref / 4.0

    re_run = va.RHO0 * (mdot_cyl_ref * 2.4 / (va.RHO0 * a_exit)) * d_exit_m / va.MU_AIR
    f_run = 1.0 / (-1.8 * math.log10((eps_molded_m / (3.7 * d_exit_m)) ** 1.11 + 6.9 / max(re_run, 5000.0))) ** 2
    k_runner_base = (0.34 if is_long else 0.22) + f_run * (l_upper_m / d_exit_m) * ((a_exit / (0.5 * (a_throat + a_exit))) ** 2)
    k_diff_tb = 0.62 * ((1.0 - a_tb / a_pl) ** 2) + 0.03
    dp_tb_pa = 0.5 * va.RHO0 * ((mdot_total_ref / (va.RHO0 * a_tb)) ** 2) * k_diff_tb
    k_head_valve = 3.2 * ((a_exit / 884.1e-6) ** 2)

    mdot_c = np.full(4, mdot_cyl_ref, dtype=float)
    p_pl_nodes = np.full(4, va.P0_IN_PA - dp_tb_pa, dtype=float)
    k_runner_tot = np.zeros(4, dtype=float)

    for _ in range(45):
        m_seg = np.array([mdot_c[0], mdot_c[0] + mdot_c[1], mdot_c[0] + mdot_c[1] + mdot_c[2], np.sum(mdot_c)])
        v_ax = np.array([1.45 * m_seg[i] / (va.RHO0 * a_pl * (1.0 - 0.8 * beta_cyl[i])) for i in range(4)])
        v_pulse_seg = np.array([(2.4 * mdot_c[i]) / (va.RHO0 * a_pl * (1.0 - 0.8 * beta_cyl[i])) for i in range(4)])
        dp_tb = 0.5 * va.RHO0 * ((m_seg[3] / (va.RHO0 * a_tb)) ** 2) * k_diff_tb
        p_04 = va.P0_IN_PA - dp_tb
        q_pl4 = 0.5 * va.RHO0 * (v_ax[3] ** 2)
        p_pl_nodes[3] = p_04 - q_pl4
        for j in (2, 1, 0):
            v_up, v_dn, v_p_mid = v_ax[j + 1], v_ax[j], 0.5 * (v_pulse_seg[j + 1] + v_pulse_seg[j])
            f_p = 1.0 / (-1.8 * math.log10((eps_molded_m / (3.7 * dh_pl)) ** 1.11 + 6.9 / max(va.RHO0 * max(v_p_mid, 1.0) * dh_pl / va.MU_AIR, 5000.0))) ** 2
            dp_ram = 0.5 * va.RHO0 * (v_up**2 - v_dn**2) * 0.72
            dp_fric = f_p * (0.092 / dh_pl) * 0.5 * va.RHO0 * (v_p_mid**2) * 1.45
            b_k = beta_cyl[j + 1]
            dp_wake = 1.35 * ((b_k / max(1.0 - b_k, 0.25)) ** 2) * 0.5 * va.RHO0 * max(v_up**2, (0.65 * v_p_mid) ** 2)
            p_pl_nodes[j] = min(p_pl_nodes[j + 1] + dp_ram - dp_fric - dp_wake, p_04 - 0.12 * q_pl4)
        for i in range(4):
            vr = v_ax[i] / max((mdot_c[i] * 2.4) / (va.RHO0 * a_throat), 1.0)
            k_runner_tot[i] = k_runner_base + (0.45 * (vr**2) + (0.08 if i == 3 else 0.0)) * ((a_exit / a_throat) ** 2)

        def branch_sum(p_cyl_back: float) -> np.ndarray:
            return np.array([
                (1.0 / math.sqrt(k_runner_tot[i] + k_head_valve)) * max(1.0 - max(p_pl_nodes[i] - p_cyl_back, 10.0) / (3.0 * va.GAMMA * p_pl_nodes[i]), 0.85) * (a_exit * 0.28) * math.sqrt(2.0 * va.RHO0 * max(p_pl_nodes[i] - p_cyl_back, 10.0))
                for i in range(4)
            ])

        lo, hi = va.P0_IN_PA - 75000.0, float(np.min(p_pl_nodes)) - 15.0
        for _ in range(55):
            mid = 0.5 * (lo + hi)
            if np.sum(branch_sum(mid)) > mdot_total_ref:
                lo = mid
            else:
                hi = mid
        mdot_c = 0.5 * branch_sum(0.5 * (lo + hi)) + 0.5 * mdot_c

    mean_sp_dp = float(np.mean([k_runner_tot[i] * 0.5 * va.RHO0 * ((mdot_c[i] / (va.RHO0 * a_exit * 0.28)) ** 2) for i in range(4)]))
    dp_upper_kpa = (dp_tb_pa + mean_sp_dp + max(0.0, float(np.mean(va.P0_IN_PA - dp_tb_pa - p_pl_nodes)))) * 1e-3
    ve_cyl = [va.VE_REF * (m / float(np.mean(mdot_c))) for m in mdot_c]

    a_run_mean = 0.5 * (a_throat + a_exit)
    l_acoustic_eff_m = l_total_acoustic_m + 0.6 * d_exit_m
    f_helmholtz_hz = (va.A0_SOUND / (2.0 * math.pi)) * math.sqrt(a_run_mean / (l_acoustic_eff_m * (v_plenum * 0.5 + 0.5 * (disp_m3 / 4.0))))

    # 720-deg Crank-Angle Unsteady Pulsating Simulation (0.5-deg steps x 6 cycles, signed momentum ODE + port capacitance)
    n_ca, n_cycles = 1440, 6
    ca_deg = np.linspace(0.0, 720.0, n_ca, endpoint=False)
    omega = rpm * 2.0 * math.pi / 60.0
    dt = math.radians(720.0 / n_ca) / omega
    r_crank, lam, a_piston = va.STROKE_M * 0.5, (va.STROKE_M * 0.5) / va.ROD_M, math.pi * 0.25 * (va.BORE_M**2)
    intake_offsets = [0.0, 540.0, 180.0, 360.0]
    a_valve_max = 0.00102
    p_pl_inst, m_run_inst = va.P0_IN_PA - 600.0, np.zeros(4, dtype=float)
    p_port_arr, p_cyl_arr = np.full(4, va.P0_IN_PA - 600.0, dtype=float), np.full(4, va.P0_IN_PA, dtype=float)
    m_run_hist = np.zeros((n_ca, 4), dtype=float)
    inertance, v_port = (l_upper_m + 0.135) / a_run_mean, a_run_mean * l_upper_m

    def valve_area(th_l: float) -> float:
        u = ((th_l + 12.0) / 244.0) if th_l <= 232.0 else (((th_l - 708.0) / 244.0) if th_l >= 708.0 else -1.0)
        return a_valve_max * (math.sin(math.pi * max(0.0, min(1.0, u))) ** 1.35) if u >= 0.0 else 0.0

    def cyl_vol_dvol(th_l: float) -> tuple[float, float]:
        th = math.radians(th_l)
        sq = math.sqrt(1.0 - (lam * math.sin(th)) ** 2)
        return (disp_m3 / 4.0) / 9.2 + a_piston * r_crank * ((1.0 - math.cos(th)) + (1.0 / lam) * (1.0 - sq)), a_piston * r_crank * (math.sin(th) + (lam * math.sin(th) * math.cos(th)) / sq) * omega

    p_pl_bias_ref = p_pl_nodes - float(np.mean(p_pl_nodes))
    last_net, periodic_res_pct = None, 0.0
    for cyc in range(n_cycles):
        cyc_m = np.zeros(4, dtype=float)
        for s_idx, th_g in enumerate(ca_deg):
            dp_tb_i = va.P0_IN_PA - p_pl_inst
            mdot_tb = (1.0 if dp_tb_i >= 0 else -1.0) * (0.94 * a_tb) * math.sqrt(2.0 * va.RHO0 * abs(dp_tb_i))
            mdot_v, mdot_r = np.zeros(4), np.zeros(4)
            for c in range(4):
                th_loc = (th_g - intake_offsets[c]) % 720.0
                vol_c, dvol_c = cyl_vol_dvol(th_loc)
                av = valve_area(th_loc)
                c_drag = 0.5 * k_runner_tot[c] * abs(m_run_inst[c]) / (va.RHO0 * a_exit**2)
                m_run_inst[c] = (m_run_inst[c] + dt * ((p_pl_inst + p_pl_bias_ref[c]) - p_port_arr[c]) / inertance) / (1.0 + dt * c_drag / inertance)
                mdot_r[c] = m_run_inst[c]
                dp_v = p_port_arr[c] - p_cyl_arr[c]
                if av > 1e-7:
                    mdot_v[c] = (1.0 if dp_v >= 0 else -1.0) * 0.72 * av * math.sqrt(2.0 * va.RHO0 * abs(dp_v))
                p_port_arr[c] = max(0.35 * va.P_AMB_PA, min(1.5 * va.P0_IN_PA, p_port_arr[c] + (va.GAMMA * va.R_AIR * va.T0_IN_K / v_port) * (m_run_inst[c] - mdot_v[c]) * dt))
                if (th_loc <= 250.0) or (th_loc >= 700.0):
                    p_cyl_arr[c] = max(0.35 * va.P_AMB_PA, min(1.5 * va.P0_IN_PA, p_cyl_arr[c] + (va.GAMMA * va.R_AIR * va.T0_IN_K / vol_c) * (mdot_v[c] * dt) - (va.GAMMA * p_cyl_arr[c] / vol_c) * dvol_c * dt))
                else:
                    p_cyl_arr[c] = va.P0_IN_PA - 1200.0
                cyc_m[c] += mdot_v[c] * dt
            p_pl_inst += (va.GAMMA * va.R_AIR * va.T0_IN_K / v_plenum) * (mdot_tb - float(np.sum(mdot_r))) * dt
            if cyc == n_cycles - 1:
                m_run_hist[s_idx, :] = mdot_v
        prev, last_net = last_net, cyc_m
        if prev is not None:
            periodic_res_pct = float(np.max(np.abs(last_net - prev))) / max(float(np.mean(np.abs(last_net))), 1e-9) * 100.0

    return {
        "rpm": rpm,
        "dp_total_kpa": round(dp_upper_kpa, 3),
        "dp_total_psi": round(dp_upper_kpa * 0.145038, 3),
        "cyl_ve": [round(float(v), 4) for v in ve_cyl],
        "ve_maldistribution_spread_pct": round((max(ve_cyl) - min(ve_cyl)) / va.VE_REF * 100.0, 2),
        "periodic_state_residual_pct": round(periodic_res_pct, 4),
        "runner_discharge_coeff_cd": round(float(np.mean(1.0 / np.sqrt(1.0 + k_runner_tot))), 4),
        "peak_mach_exit": round((float(np.max(m_run_hist)) / (va.RHO0 * a_exit)) / va.A0_SOUND, 3),
        "helmholtz_freq_hz": round(f_helmholtz_hz, 1),
        "helmholtz_3rd_harmonic_rpm": round(f_helmholtz_hz * 120.0 / 3.0, 0),
        "quarter_wave_4th_harmonic_rpm": round((va.A0_SOUND / (4.0 * l_acoustic_eff_m)) * 120.0 / 4.0, 0),
        "physical_runner_length_mm": round(l_total_acoustic_m * 1000.0, 1),
        "effective_acoustic_length_mm": round(l_acoustic_eff_m * 1000.0, 1),
    }


def _cam_envelope(rpm: float) -> float:
    return 0.915 + 0.085 * math.exp(-((rpm - 6350.0) / 2150.0) ** 2) - 0.030 * max(0.0, (rpm - 6700.0) / 800.0) ** 1.4


def _compute_v037_anchor_scale() -> float:
    rho_v037 = 225700.0 / (va.R_AIR * 295.37)
    sim_anchor = simulate_oem_dsi_point("short", 6397.0)
    p_plenum_ratio = (va.P0_IN_PA - sim_anchor["dp_total_kpa"] * 1e3) / va.P0_IN_PA
    raw_lbmin = rho_v037 * (va.ENGINE_DISP_L * 1e-3) * (6397.0 / 120.0) * _cam_envelope(6397.0) * p_plenum_ratio * 132.277
    return 37.85 / raw_lbmin


V037_ANCHOR_SCALE = _compute_v037_anchor_scale()


def estimate_boosted_airflow_lbmin(rpm: float, sim: dict, mode_tag: str) -> float:
    rho_v037 = 225700.0 / (va.R_AIR * 295.37)
    p_plenum_ratio = (va.P0_IN_PA - sim["dp_total_kpa"] * 1e3) / va.P0_IN_PA
    acoustic = (1.0 + 0.024 * math.exp(-((rpm - 4350.0) / 1350.0) ** 2) - 0.078 * max(0.0, (rpm - 4900.0) / 2600.0) ** 1.55) if mode_tag == "oem_long" else 1.000
    mdot_raw_kgs = rho_v037 * (va.ENGINE_DISP_L * 1e-3) * (rpm / 120.0) * _cam_envelope(rpm) * p_plenum_ratio * acoustic * V037_ANCHOR_SCALE
    return round(mdot_raw_kgs * 132.277, 2)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    verif = json.loads(VERIF_PATH.read_text(encoding="utf-8"))

    prov = verif.get("provenance") or {}
    if (
        prov.get("intake_manifold_v2_parameters_sha256") != _sha256_file(PARAMS_PATH)
        or prov.get("manifest_sha256") != _sha256_file(MANIFEST_PATH)
        or prov.get("stl_1piece_full_sha256") != _sha256_file(STL_1PC_PATH)
    ):
        raise RuntimeError("Stale V2 airflow_verification.json: provenance hashes mismatch current parameters/manifest/STL.")
    cfd3d = verif["boost_optimized"]["cfd_3d"]
    if not cfd3d.get("converged") or cfd3d.get("status") != "CONVERGED":
        raise RuntimeError(f"Cannot compare factory vs custom V2: 3D FVM did not converge ({cfd3d.get('status')}).")

    anchor_pred = estimate_boosted_airflow_lbmin(6397.0, simulate_oem_dsi_point("short", 6397.0), "oem_short")
    assert abs(anchor_pred - 37.85) < 0.05, f"v037 calibration drift: {anchor_pred}"

    custom_audit = verif["boost_optimized"]["cad_audit"]
    left_v = manifest["parts"]["svt_intake_manifold_v2_split_left_cyl1_2"]["solid_volume_cm3"]
    right_v = manifest["parts"]["svt_intake_manifold_v2_split_right_cyl3_4_tb"]["solid_volume_cm3"]
    custom_total_mass_kg = (left_v + right_v) * CUSTOM_CF_PA_DENSITY_G_CM3 / 1000.0 + CUSTOM_HARDWARE_MASS_KG

    rpms = list(range(3000, 7750, 250))
    curves = {"oem_long": [], "oem_short": [], "custom": []}
    for rpm in rpms:
        r_long = simulate_oem_dsi_point("long", float(rpm)); r_long["est_airflow_lbmin"] = estimate_boosted_airflow_lbmin(float(rpm), r_long, "oem_long"); curves["oem_long"].append(r_long)
        r_short = simulate_oem_dsi_point("short", float(rpm)); r_short["est_airflow_lbmin"] = estimate_boosted_airflow_lbmin(float(rpm), r_short, "oem_short"); curves["oem_short"].append(r_short)
        s_cust = va.solve_1d_compressible_and_pulsating(params, custom_audit, rpm=float(rpm))
        c_entry = {k: v for k, v in s_cust.items() if not k.startswith("_")}
        c_entry["est_airflow_lbmin"] = estimate_boosted_airflow_lbmin(float(rpm), c_entry, "custom")
        curves["custom"].append(c_entry)

    idx_6500, idx_7000 = rpms.index(6500), rpms.index(7000)

    def summarize_7000(pt: dict, tag: str) -> dict:
        ve_arr = pt["cyl_ve"]
        mean_ve = sum(ve_arr) / 4.0
        cyl_afr = [11.0 * (v / mean_ve) for v in ve_arr]
        rich_afr, lean_afr = min(cyl_afr), max(cyl_afr)
        return {
            "mode": tag,
            "dp_7000_kpa": pt["dp_total_kpa"],
            "dp_7000_psi": pt["dp_total_psi"],
            "ve_spread_7000_pct": pt["ve_maldistribution_spread_pct"],
            "cyl_ve_7000": ve_arr,
            "cyl_afr_at_11p0": [round(a, 2) for a in cyl_afr],
            "richest_to_leanest_afr_at_11p0": [round(rich_afr, 2), round(lean_afr, 2)],
            "afr_spread_band": round(lean_afr - rich_afr, 2),
            "afr_projection_note": "Equal-fueling projection from 1D VE distribution; not a measured knock margin",
            "peak_mach_exit_7000": pt["peak_mach_exit"],
            "est_airflow_6500_lbmin": curves[tag if tag != "custom_round" else "custom"][idx_6500]["est_airflow_lbmin"],
            "est_airflow_7000_lbmin": pt["est_airflow_lbmin"],
            "helmholtz_3rd_harmonic_rpm": pt["helmholtz_3rd_harmonic_rpm"],
            "upper_runner_arc_length_mm": pt.get("upper_runner_arc_length_mm"),
            "physical_runner_length_mm": pt["physical_runner_length_mm"],
            "effective_acoustic_length_mm": pt["effective_acoustic_length_mm"],
        }

    summary_7000 = {
        "oem_dsi_long": summarize_7000(curves["oem_long"][idx_7000], "oem_long"),
        "oem_dsi_short": summarize_7000(curves["oem_short"][idx_7000], "oem_short"),
        "custom_round_2in": summarize_7000(curves["custom"][idx_7000], "custom_round"),
    }
    summary_7000["custom_round_2in"].update({
        "cfd_3d_spread_pct": cfd3d["cyl_maldistribution_spread_pct"],
        "cfd_3d_dp_psi": cfd3d["tb_to_plenum_dp_psi"],
        "cfd_3d_cyl_share_pct": cfd3d["cyl_flow_share_pct"],
    })

    dl_short = round(curves["custom"][idx_7000]["est_airflow_lbmin"] - curves["oem_short"][idx_7000]["est_airflow_lbmin"], 2)
    dl_long = round(curves["custom"][idx_7000]["est_airflow_lbmin"] - curves["oem_long"][idx_7000]["est_airflow_lbmin"], 2)
    pct_short = round(dl_short / max(curves["oem_short"][idx_7000]["est_airflow_lbmin"], 1e-6) * 100.0, 2)
    pct_long = round(dl_long / max(curves["oem_long"][idx_7000]["est_airflow_lbmin"], 1e-6) * 100.0, 2)

    hardware_comp = {
        "oem_upper_dsi": {"material": "Molded PA66-GF30 (2M5Z-9424-BB) + IMRC", "estimated_mass_kg": round(OEM_UPPER_DSI_MASS_KG, 2), "estimated_mass_lb": round(OEM_UPPER_DSI_MASS_KG * 2.20462, 2), "thermal_conductivity_w_mk": OEM_PA66_GF30_K_W_MK, "plenum_volume_liters": 2.20},
        "custom_stage2_v2": {"material": "Annealed PPA-CF / PAHT-CF (2-Piece Split) + Epoxy Seal", "printed_volume_cm3": round(left_v + right_v, 2), "estimated_mass_kg": round(custom_total_mass_kg, 2), "estimated_mass_lb": round(custom_total_mass_kg * 2.20462, 2), "mass_savings_lb": round((OEM_UPPER_DSI_MASS_KG - custom_total_mass_kg) * 2.20462, 2), "thermal_conductivity_w_mk": CUSTOM_CF_PA_K_W_MK, "plenum_volume_liters": custom_audit["bare_plenum_volume_liters"]},
        "estimated_gains_7000rpm_18psi": {"basis": "Matched pressure-loss recovery only (acoustic=1.000 for OEM Short & Custom V2)", "airflow_gain_vs_oem_short_lbmin": dl_short, "airflow_gain_vs_oem_short_pct": pct_short, "airflow_gain_vs_oem_long_lbmin": dl_long, "airflow_gain_vs_oem_long_pct": pct_long},
    }
    report = {"provenance": prov, "methodology_note": "Custom V2 specs & 3D CFD directly from CAD solids & verify_airflow_v2.py; OEM SVT DSI estimated from geometry; v037 logs from 2026-11-06 review.", "logged_v037_points": LOGGED_V037_POINTS, "summary_7000rpm": summary_7000, "hardware_comparison": hardware_comp, "rpm_curves": curves}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    render_comparison_figure(rpms, curves, summary_7000, hardware_comp, OUT_PNG, case_id=prov.get("case_id", ""))
    print(f"Saved {OUT_JSON.relative_to(ROOT)} and {OUT_PNG.relative_to(ROOT)}")
    print(f"7000 RPM @ 18 psi: OEM Short dP={summary_7000['oem_dsi_short']['dp_7000_psi']} psi ({summary_7000['oem_dsi_short']['ve_spread_7000_pct']}%) | V2 dP={summary_7000['custom_round_2in']['dp_7000_psi']} psi (1D {summary_7000['custom_round_2in']['ve_spread_7000_pct']}%, 3D {cfd3d['cyl_maldistribution_spread_pct']}%)")
    print(f"Modeled Pressure-Loss Flow Diff @ 7k: +{dl_short} lb/min (+{pct_short}%) vs Short, +{dl_long} lb/min (+{pct_long}%) vs Long")


def render_comparison_figure(rpms, curves, s7k, hw, out_path: Path, case_id: str = ""):
    fig = plt.figure(figsize=(18, 12), facecolor="#f5f4f0")
    fig.suptitle("Custom Stage-2 V2 (Dropped Plenum, 32°/-Y + 14°/+Z TB, Ø42.8) vs. Factory 2004 Focus SVT DSI — 18 PSI Boost", fontsize=14, fontweight="bold", y=0.975, color="#182028")
    c_long, c_short, c_cust = "#c0392b", "#d68910", "#117864"

    ax1 = fig.add_subplot(3, 2, 1); ax1.set_facecolor("#ffffff")
    ax1.plot(rpms, [p["dp_total_psi"] for p in curves["oem_long"]], "o--", color=c_long, lw=2.0, ms=4, label="Factory DSI — Long (~475 mm)")
    ax1.plot(rpms, [p["dp_total_psi"] for p in curves["oem_short"]], "s-.", color=c_short, lw=2.0, ms=4, label="Factory DSI — Short (~320 mm)")
    ax1.plot(rpms, [p["dp_total_psi"] for p in curves["custom"]], "^-", color=c_cust, lw=2.6, ms=5.5, label=f"Custom V2 ({s7k['custom_round_2in']['physical_runner_length_mm']:.0f} mm, Flush Bellmouth)")
    ax1.axvspan(5500, 6000, color="#ebedef", alpha=0.8, label="OEM IMRC Switch (5.5k–6k)")
    ax1.set_title("1. Upper-Manifold Pressure Drop (ΔP) @ 18.0 PSI", fontsize=10.5, fontweight="bold"); ax1.set_xlabel("RPM"); ax1.set_ylabel("ΔP [psi]"); ax1.set_ylim(0, max(p["dp_total_psi"] for p in curves["oem_long"]) * 1.15); ax1.grid(True, ls=":", alpha=0.55); ax1.legend(fontsize=7.6, loc="upper left")

    ax2 = fig.add_subplot(3, 2, 2); ax2.set_facecolor("#ffffff")
    ax2.plot(rpms, [p["est_airflow_lbmin"] for p in curves["oem_long"]], "o--", color=c_long, lw=2.0, ms=4, label="Modeled OEM Long (IMRC Closed)")
    ax2.plot(rpms, [p["est_airflow_lbmin"] for p in curves["oem_short"]], "s-.", color=c_short, lw=2.0, ms=4, label="Modeled OEM Short (Pinned Open)")
    ax2.plot(rpms, [p["est_airflow_lbmin"] for p in curves["custom"]], "^-", color=c_cust, lw=2.6, ms=5.5, label="Modeled Custom V2 (Matched ΔP Only)")
    hi = [pt for pt in LOGGED_V037_POINTS if pt["boost_psi"] >= 18.0]
    ax2.scatter([pt["rpm"] for pt in hi], [pt["lbmin"] for pt in hi], color="#1b2631", marker="*", s=190, zorder=7, label="v037 Car Logs (Pull 2 & 6 @ 18 psi)")
    ax2.set_title("2. Modeled WOT Flow @ 72°F IAT (Matched ΔP-Only Recovery)", fontsize=10.5, fontweight="bold"); ax2.set_xlabel("RPM"); ax2.set_ylabel("Mass Airflow [lb/min]"); ax2.grid(True, ls=":", alpha=0.55); ax2.legend(fontsize=7.6, loc="lower right")

    ax3 = fig.add_subplot(3, 2, 3); ax3.set_facecolor("#ffffff")
    cyls, w = np.arange(1, 5), 0.24
    ax3.bar(cyls - w, [100 * v for v in s7k["oem_dsi_long"]["cyl_ve_7000"]], width=w, color=c_long, alpha=0.88, label=f"OEM Long ({s7k['oem_dsi_long']['ve_spread_7000_pct']:.2f}%)")
    ax3.bar(cyls, [100 * v for v in s7k["oem_dsi_short"]["cyl_ve_7000"]], width=w, color=c_short, alpha=0.90, label=f"OEM Short ({s7k['oem_dsi_short']['ve_spread_7000_pct']:.2f}%)")
    ax3.bar(cyls + w, [100 * v for v in s7k["custom_round_2in"]["cyl_ve_7000"]], width=w, color=c_cust, alpha=0.92, label=f"Custom V2 (1D {s7k['custom_round_2in']['ve_spread_7000_pct']:.2f}% | 3D {s7k['custom_round_2in']['cfd_3d_spread_pct']:.2f}%)")
    ax3.set_xticks(cyls); ax3.set_xticklabels([f"Cyl {i}" for i in cyls]); ax3.set_ylim(92, 102.5); ax3.grid(True, axis="y", ls=":", alpha=0.55); ax3.legend(fontsize=7.5, loc="lower right")
    ax3.set_title("3. Cylinder-to-Cylinder 1D VE Balance @ 7,000 RPM", fontsize=10.5, fontweight="bold"); ax3.set_ylabel("Effective VE [%]")

    ax4 = fig.add_subplot(3, 2, 4); ax4.set_facecolor("#ffffff")
    ax4.plot(rpms, [p["peak_mach_exit"] for p in curves["oem_long"]], "o--", color=c_long, lw=2.0, ms=4, label=f"OEM Long (3rd @ {int(s7k['oem_dsi_long']['helmholtz_3rd_harmonic_rpm'])} RPM)")
    ax4.plot(rpms, [p["peak_mach_exit"] for p in curves["oem_short"]], "s-.", color=c_short, lw=2.0, ms=4, label=f"OEM Short (3rd @ {int(s7k['oem_dsi_short']['helmholtz_3rd_harmonic_rpm'])} RPM)")
    ax4.plot(rpms, [p["peak_mach_exit"] for p in curves["custom"]], "^-", color=c_cust, lw=2.6, ms=5.5, label=f"Custom V2 (3rd @ {int(s7k['custom_round_2in']['helmholtz_3rd_harmonic_rpm'])} RPM)")
    ax4.axhspan(0.0, 0.32, color="#d4efdf", alpha=0.45, label="Subsonic Zone (M < 0.32)")
    ax4.set_title("4. Peak Runner-Exit Mach Number & Plenum Resonance", fontsize=10.5, fontweight="bold"); ax4.set_xlabel("RPM"); ax4.set_ylabel("Peak Exit Mach"); ax4.grid(True, ls=":", alpha=0.55); ax4.legend(fontsize=7.6, loc="upper left")

    ax5 = fig.add_subplot(3, 2, 5); ax5.set_facecolor("#ffffff")
    cats = ["Weight [lb]", "Blockage [%]", "ΔP×10 [psi]", "Spread [%]", "AFR Band×10"]
    oem_v = [hw["oem_upper_dsi"]["estimated_mass_lb"], 12.0, s7k["oem_dsi_short"]["dp_7000_psi"] * 10, s7k["oem_dsi_short"]["ve_spread_7000_pct"], s7k["oem_dsi_short"]["afr_spread_band"] * 10]
    cus_v = [hw["custom_stage2_v2"]["estimated_mass_lb"], 0.0, s7k["custom_round_2in"]["dp_7000_psi"] * 10, s7k["custom_round_2in"]["ve_spread_7000_pct"], s7k["custom_round_2in"]["afr_spread_band"] * 10]
    xp = np.arange(len(cats))
    b1, b2 = ax5.bar(xp - 0.17, oem_v, 0.34, color="#7f8c8d", label="OEM Short"), ax5.bar(xp + 0.17, cus_v, 0.34, color=c_cust, label="Custom V2")
    for bars in (b1, b2):
        for r in bars:
            ax5.text(r.get_x() + r.get_width() * 0.5, r.get_height() + 0.2, f"{r.get_height():.2f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")
    ax5.set_xticks(xp); ax5.set_xticklabels(cats, fontsize=8); ax5.set_ylim(0, max(oem_v) * 1.25); ax5.grid(True, axis="y", ls=":", alpha=0.55); ax5.legend(fontsize=8)
    ax5.set_title("5. Weight, Internal Blockage & ΔP Margins (Lower is Better)", fontsize=10.5, fontweight="bold")

    ax6 = fig.add_subplot(3, 2, 6); ax6.axis("off"); ax6.set_title("6. Side-by-Side Comparison Summary (7,000 RPM @ 18.0 PSI)", fontsize=10.5, fontweight="bold", pad=8)
    rows = [
        ["Upper Material", "PA66-GF30", "PA66-GF30", "PPA-CF / PAHT-CF*"],
        ["Mass (w/ Hardware)", f"{hw['oem_upper_dsi']['estimated_mass_lb']:.1f} lb", f"{hw['oem_upper_dsi']['estimated_mass_lb']:.1f} lb", f"{hw['custom_stage2_v2']['estimated_mass_lb']:.2f} lb (-{hw['custom_stage2_v2']['mass_savings_lb']:.1f} lb)"],
        ["Physical / Eff Length", "~475 mm", "~320 mm", f"{s7k['custom_round_2in']['physical_runner_length_mm']:.0f} / {s7k['custom_round_2in']['effective_acoustic_length_mm']:.0f} mm"],
        ["Internal Blockage", "~18% (drum)", "~12% (drum)", "0.00% (CAD verified)"],
        ["Upper ΔP @ 7k RPM", f"{s7k['oem_dsi_long']['dp_7000_psi']:.3f} psi", f"{s7k['oem_dsi_short']['dp_7000_psi']:.3f} psi", f"{s7k['custom_round_2in']['dp_7000_psi']:.3f} psi (3D {s7k['custom_round_2in']['cfd_3d_dp_psi']:.3f})"],
        ["Cyl Spread @ 7k", f"{s7k['oem_dsi_long']['ve_spread_7000_pct']:.2f}%", f"{s7k['oem_dsi_short']['ve_spread_7000_pct']:.2f}%", f"{s7k['custom_round_2in']['ve_spread_7000_pct']:.2f}% (3D {s7k['custom_round_2in']['cfd_3d_spread_pct']:.2f}%)"],
        ["Equal-Fuel AFR (R–L)", f"{s7k['oem_dsi_long']['richest_to_leanest_afr_at_11p0'][0]:.2f}–{s7k['oem_dsi_long']['richest_to_leanest_afr_at_11p0'][1]:.2f}", f"{s7k['oem_dsi_short']['richest_to_leanest_afr_at_11p0'][0]:.2f}–{s7k['oem_dsi_short']['richest_to_leanest_afr_at_11p0'][1]:.2f}", f"{s7k['custom_round_2in']['richest_to_leanest_afr_at_11p0'][0]:.2f}–{s7k['custom_round_2in']['richest_to_leanest_afr_at_11p0'][1]:.2f}"],
        ["Modeled ΔFlow (ΔP-Only)", f"{s7k['oem_dsi_long']['est_airflow_7000_lbmin']} lb/m", f"{s7k['oem_dsi_short']['est_airflow_7000_lbmin']} lb/m", f"{s7k['custom_round_2in']['est_airflow_7000_lbmin']} lb/m (+{hw['estimated_gains_7000rpm_18psi']['airflow_gain_vs_oem_short_lbmin']:.2f})"],
    ]
    tbl = ax6.table(cellText=rows, colLabels=["Metric", "OEM Long", "OEM Short", "Custom Stage-2 V2"], cellLoc="center", loc="center", colWidths=[0.28, 0.21, 0.21, 0.30])
    tbl.auto_set_font_size(False); tbl.set_fontsize(7.9); tbl.scale(1.0, 1.55)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1f2d3d"); cell.set_text_props(color="white", fontweight="bold")
        elif c == 3:
            cell.set_facecolor("#e8f8f5"); cell.set_text_props(fontweight="bold", color="#0e6251")
        cell.set_edgecolor("#d5d8dc")

    fig.text(0.5, 0.010, f"Case ID: {case_id} | *Printed CF-Nylon requires anneal + epoxy seal & 20–25 psi bench test; OEM modeled from DSI geometry; matched ΔP-only (acoustic=1.000).", ha="center", fontsize=7.8, color="#444444")
    plt.tight_layout(rect=[0, 0.025, 1, 0.945])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
