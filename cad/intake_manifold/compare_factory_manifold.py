#!/usr/bin/env python3
"""
Engineering & Airflow Comparison:
Custom Stage-2 Max-Boost Upper Manifold (Ø50.8/Ø42.8 mm Round Boot)
vs. Factory 2002-2004 Ford Focus SVT / ST170 Dual-Stage Intake (DSI) Manifold.

Anchors:
  - Custom manifold CAD, 3D FVM, and 1D/720-deg specs loaded directly from
    intake_manifold_parameters.json, stl/manifest.json, and stl/airflow_verification.json.
  - Real vehicle telemetry anchor from v037 Pull 2 & Pull 6 logs:
    35.91 lb/min @ 5,978 RPM (18.33 psi) and 37.85 lb/min @ 6,397 RPM (18.04 psi).
  - OEM SVT/ST170 DSI Long-Runner (IMRC closed) & Short-Runner (IMRC open/pinned)
    approximated via literature/physical geometry (non-laser-scanned OEM baseline).

Outputs:
  stl/factory_comparison.json
  fitment/04_factory_vs_custom_comparison.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import verify_airflow as va

ROOT = Path(__file__).resolve().parent
PARAMS_PATH = ROOT / "intake_manifold_parameters.json"
MANIFEST_PATH = ROOT / "stl" / "manifest.json"
VERIF_PATH = ROOT / "stl" / "airflow_verification.json"
OUT_JSON = ROOT / "stl" / "factory_comparison.json"
OUT_PNG = ROOT / "fitment" / "04_factory_vs_custom_comparison.png"

# v037 Pull 2 / Pull 6 logged telemetry anchors (18.0-18.3 psi, 2.012 L forged Zetec)
LOGGED_V037_POINTS = [
    {"label": "v037 Pull 5 (10.2 psi)", "rpm": 4886.0, "lbmin": 22.32, "boost_psi": 10.22},
    {"label": "v037 Pull 2 (18.33 psi)", "rpm": 5978.0, "lbmin": 35.91, "boost_psi": 18.33},
    {"label": "v037 Pull 6 Peak (18.04 psi)", "rpm": 6397.0, "lbmin": 37.85, "boost_psi": 18.04},
]

# Approximate physical constants (OEM SVT PA66-GF30 plastic hardware specs)
OEM_UPPER_DSI_MASS_KG = 3.63  # Molded PA66-GF30 upper + IMRC box/cable/bracket (~8.0 lb installed; ~8.6 lb ship)
OEM_PA66_GF30_K_W_MK = 0.40   # Injection-molded PA66-GF30 nylon thermal conductivity [W/(m*K)]
CUSTOM_CF_PA_DENSITY_G_CM3 = 1.26  # Annealed PAHT-CF / PPA-CF density
CUSTOM_HARDWARE_MASS_KG = 0.18     # 6x M6 bolts/washers/nuts + 2x dowels + brass NPT barbs + O-rings
CUSTOM_CF_PA_K_W_MK = 0.90         # Transverse printed CF-Nylon thermal conductivity [W/(m*K)]


def simulate_oem_dsi_point(mode: str, rpm: float) -> dict:
    """
    1D Compressible Dividing-Manifold + 720-deg Crank-Angle Pulsating model for
    the Factory Molded-Plastic (PA66-GF30) Focus SVT / ST170 DSI upper manifold.
    Modes:
      - 'long':  IMRC closed (scroll long runner ~340 mm upper / ~475 mm total)
      - 'short': IMRC open/pinned (short runner ~185 mm upper / ~320 mm total)
    """
    is_long = mode == "long"
    l_upper_m = 0.340 if is_long else 0.185
    l_total_acoustic_m = 0.475 if is_long else 0.320
    # Lower plastic injector housing exit interface matches ~42.8 mm round boot (1,438.7 mm^2)
    d_exit_m = 0.0428
    a_exit = math.pi * 0.25 * d_exit_m**2
    d_throat_m = 0.0420 if is_long else 0.0430
    a_throat = math.pi * 0.25 * d_throat_m**2

    # Smooth injection-molded PA66-GF30 composite surface (~18 um); untapered drum chamber ~2.20 L
    eps_molded_m = 0.000018
    v_plenum = 0.00220
    a_pl = 0.00580
    perim_pl = 0.290
    dh_pl = 4.0 * a_pl / perim_pl
    beta_cyl = np.full(4, 0.18 if is_long else 0.12)  # Internal rotary drum wake blockage

    a_tb = math.pi * 0.25 * (0.065**2)
    disp_m3 = va.ENGINE_DISP_L * 1e-3
    mdot_total_ref = va.RHO0 * disp_m3 * (rpm / 120.0) * va.VE_REF
    mdot_cyl_ref = mdot_total_ref / 4.0

    # Molded entry, scroll/drum turn, and vibration-welded clamshell step
    k_bell_and_drum = 0.34 if is_long else 0.22
    re_run = va.RHO0 * (mdot_cyl_ref * 2.4 / (va.RHO0 * a_exit)) * d_exit_m / va.MU_AIR
    f_run = 1.0 / (-1.8 * math.log10((eps_molded_m / (3.7 * d_exit_m)) ** 1.11 + 6.9 / max(re_run, 5000.0))) ** 2
    k_fric = f_run * (l_upper_m / d_exit_m) * ((a_exit / (0.5 * (a_throat + a_exit))) ** 2)
    k_runner_base = k_bell_and_drum + k_fric

    # Side-entry TB diffuser into untapered box/drum plenum
    k_diff_tb = 0.62 * ((1.0 - a_tb / a_pl) ** 2) + 0.03
    dp_tb_pa = 0.5 * va.RHO0 * ((mdot_total_ref / (va.RHO0 * a_tb)) ** 2) * k_diff_tb

    # Fixed downstream OEM Zetec lower/head/valve curtain impedance (identical for fair comparison)
    k_head_valve = 3.2 * ((a_exit / 884.1e-6) ** 2)

    mdot_c = np.full(4, mdot_cyl_ref, dtype=float)
    p_pl_nodes = np.full(4, va.P0_IN_PA - dp_tb_pa, dtype=float)
    k_runner_tot = np.zeros(4, dtype=float)

    for _ in range(45):
        m_seg = np.array([
            mdot_c[0],
            mdot_c[0] + mdot_c[1],
            mdot_c[0] + mdot_c[1] + mdot_c[2],
            np.sum(mdot_c),
        ])
        # Untapered plenum: velocity drops sharply from Cyl 4 toward Cyl 1 -> strong ram pressure rise at Cyl 1
        v_ax = np.array([1.45 * m_seg[i] / (va.RHO0 * a_pl * (1.0 - 0.8 * beta_cyl[i])) for i in range(4)])
        v_pulse_seg = np.array([(2.4 * mdot_c[i]) / (va.RHO0 * a_pl * (1.0 - 0.8 * beta_cyl[i])) for i in range(4)])

        v_tb = m_seg[3] / (va.RHO0 * a_tb)
        dp_tb = 0.5 * va.RHO0 * (v_tb**2) * k_diff_tb
        p_04 = va.P0_IN_PA - dp_tb
        q_pl4 = 0.5 * va.RHO0 * (v_ax[3] ** 2)
        p_pl_nodes[3] = p_04 - q_pl4

        pitch_m = 0.092
        for j in (2, 1, 0):
            v_up = v_ax[j + 1]
            v_dn = v_ax[j]
            v_p_mid = 0.5 * (v_pulse_seg[j + 1] + v_pulse_seg[j])
            dp_ram = 0.5 * va.RHO0 * (v_up**2 - v_dn**2) * 0.72
            re_p = va.RHO0 * max(v_p_mid, 1.0) * dh_pl / va.MU_AIR
            f_p = 1.0 / (-1.8 * math.log10((eps_molded_m / (3.7 * dh_pl)) ** 1.11 + 6.9 / max(re_p, 5000.0))) ** 2
            dp_fric = f_p * (pitch_m / dh_pl) * 0.5 * va.RHO0 * (v_p_mid**2) * 1.45
            b_k = beta_cyl[j + 1]
            k_wake = 1.35 * ((b_k / max(1.0 - b_k, 0.25)) ** 2)
            dp_wake = k_wake * 0.5 * va.RHO0 * max(v_up**2, (0.65 * v_p_mid) ** 2)
            p_raw = p_pl_nodes[j + 1] + dp_ram - dp_fric - dp_wake
            p_pl_nodes[j] = min(p_raw, p_04 - 0.12 * q_pl4)

        for i in range(4):
            v_throat_i = (mdot_c[i] * 2.4) / (va.RHO0 * a_throat)
            vr = v_ax[i] / max(v_throat_i, 1.0)
            k_turn_i = 0.45 * (vr**2)  # Sharp 90-deg rotary-drum turn without bellmouth or scoop
            k_jet_4 = 0.08 if i == 3 else 0.0
            k_runner_tot[i] = k_runner_base + (k_turn_i + k_jet_4) * ((a_exit / a_throat) ** 2)

        def branch_sum(p_cyl_back: float) -> np.ndarray:
            arr = np.zeros(4)
            for i in range(4):
                dp_i = max(p_pl_nodes[i] - p_cyl_back, 10.0)
                k_series = k_runner_tot[i] + k_head_valve
                y_comp = max(1.0 - dp_i / (3.0 * va.GAMMA * p_pl_nodes[i]), 0.85)
                cd_series = 1.0 / math.sqrt(k_series)
                arr[i] = cd_series * y_comp * (a_exit * 0.28) * math.sqrt(2.0 * va.RHO0 * dp_i)
            return arr

        lo, hi = va.P0_IN_PA - 75000.0, float(np.min(p_pl_nodes)) - 15.0
        for _ in range(55):
            mid = 0.5 * (lo + hi)
            if np.sum(branch_sum(mid)) > mdot_total_ref:
                lo = mid
            else:
                hi = mid
        mdot_c = 0.5 * branch_sum(0.5 * (lo + hi)) + 0.5 * mdot_c

    mean_spigot_dp_pa = float(np.mean([
        k_runner_tot[i] * 0.5 * va.RHO0 * ((mdot_c[i] / (va.RHO0 * a_exit * 0.28)) ** 2) for i in range(4)
    ]))
    dp_upper_pa = dp_tb_pa + mean_spigot_dp_pa + max(0.0, float(np.mean(va.P0_IN_PA - dp_tb_pa - p_pl_nodes)))
    dp_upper_kpa = dp_upper_pa * 1e-3

    mean_m = float(np.mean(mdot_c))
    ve_cyl = [va.VE_REF * (m / mean_m) for m in mdot_c]
    ve_spread_pct = (max(ve_cyl) - min(ve_cyl)) / va.VE_REF * 100.0
    cd_runner = float(np.mean(1.0 / np.sqrt(1.0 + k_runner_tot)))

    a_run_mean = 0.5 * (a_throat + a_exit)
    v_cyl_eff = v_plenum * 0.5 + 0.5 * (disp_m3 / 4.0)
    f_helmholtz_hz = (va.A0_SOUND / (2.0 * math.pi)) * math.sqrt(a_run_mean / (l_total_acoustic_m * v_cyl_eff))
    rpm_helmholtz_3rd = f_helmholtz_hz * 120.0 / 3.0
    f_quarter_hz = va.A0_SOUND / (4.0 * (l_total_acoustic_m + 0.35 * d_exit_m))
    rpm_pulse_4th = f_quarter_hz * 120.0 / 4.0

    # (B) Matching 720-deg Crank-Angle Unsteady Pulsating Simulation (identical solver to verify_airflow.py)
    n_ca = 720
    ca_deg = np.linspace(0.0, 720.0, n_ca, endpoint=False)
    omega = rpm * 2.0 * math.pi / 60.0
    d_theta = math.radians(720.0 / n_ca)
    dt = d_theta / omega

    r_crank = va.STROKE_M * 0.5
    lam = r_crank / va.ROD_M
    a_piston = math.pi * 0.25 * (va.BORE_M**2)
    intake_offsets = [0.0, 540.0, 180.0, 360.0]
    a_valve_max = 0.00102

    p_pl_inst = va.P0_IN_PA - 600.0
    m_run_inst = np.zeros(4)
    m_run_hist = np.zeros((n_ca, 4))

    l_eff_inertia = l_upper_m + 0.097
    a_eff_inertia = 0.5 * (a_throat + a_exit)
    inertance = l_eff_inertia / a_eff_inertia

    def valve_area(theta_local: float) -> float:
        if theta_local <= 232.0:
            u = (theta_local + 12.0) / 244.0
        elif theta_local >= 708.0:
            u = (theta_local - 708.0) / 244.0
        else:
            return 0.0
        return a_valve_max * (math.sin(math.pi * max(0.0, min(1.0, u))) ** 1.35)

    def cyl_vol_dvol(theta_local: float) -> tuple[float, float]:
        th = math.radians(theta_local)
        cr = 10.2
        v_clear = (disp_m3 / 4.0) / (cr - 1.0)
        disp_x = r_crank * ((1.0 - math.cos(th)) + (1.0 / lam) * (1.0 - math.sqrt(1.0 - (lam * math.sin(th)) ** 2)))
        vol = v_clear + a_piston * disp_x
        d_x_dth = r_crank * (math.sin(th) + (lam * math.sin(th) * math.cos(th)) / math.sqrt(1.0 - (lam * math.sin(th)) ** 2))
        return vol, a_piston * d_x_dth * omega

    p_pl_bias_ref = p_pl_nodes - float(np.mean(p_pl_nodes))
    p_cyl_arr = np.full(4, va.P0_IN_PA)
    for cyc in range(3):
        for s_idx, th_g in enumerate(ca_deg):
            dp_tb_inst = va.P0_IN_PA - p_pl_inst
            sgn_tb = 1.0 if dp_tb_inst >= 0 else -1.0
            mdot_tb = sgn_tb * (0.94 * a_tb) * math.sqrt(2.0 * va.RHO0 * abs(dp_tb_inst))
            mdot_valves = np.zeros(4)
            for c in range(4):
                th_loc = (th_g - intake_offsets[c]) % 720.0
                vol_c, dvol_c = cyl_vol_dvol(th_loc)
                av = valve_area(th_loc)
                p_pl_local = p_pl_inst + p_pl_bias_ref[c]
                loss_pa = 0.5 * k_runner_tot[c] * m_run_inst[c] * abs(m_run_inst[c]) / (va.RHO0 * a_exit**2)
                dp_v = (p_pl_local - loss_pa) - p_cyl_arr[c]
                if av > 1e-7:
                    sgn_v = 1.0 if dp_v >= 0 else -1.0
                    mdot_valves[c] = sgn_v * 0.72 * av * math.sqrt(2.0 * va.RHO0 * abs(dp_v))
                    dmdt = loss_pa / inertance
                    m_run_inst[c] = 0.75 * mdot_valves[c] + 0.25 * (m_run_inst[c] + dmdt * dt)
                else:
                    m_run_inst[c] *= 0.85
                if (th_loc <= 250.0) or (th_loc >= 700.0):
                    dm_in = mdot_valves[c] * dt
                    dp_cyl = (va.GAMMA * va.R_AIR * va.T0_IN_K / vol_c) * dm_in - (va.GAMMA * p_cyl_arr[c] / vol_c) * dvol_c * dt
                    p_cyl_arr[c] = max(0.35 * va.P_AMB_PA, min(1.5 * va.P0_IN_PA, p_cyl_arr[c] + dp_cyl))
                else:
                    p_cyl_arr[c] = va.P0_IN_PA - 1200.0
            dm_pl = mdot_tb - float(np.sum(mdot_valves))
            p_pl_inst += (va.GAMMA * va.R_AIR * va.T0_IN_K / v_plenum) * dm_pl * dt
            if cyc == 2:
                m_run_hist[s_idx, :] = mdot_valves

    v_peak_exit = float(np.max(m_run_hist)) / (va.RHO0 * a_exit)
    mach_peak_exit = v_peak_exit / va.A0_SOUND

    return {
        "rpm": rpm,
        "dp_total_kpa": round(dp_upper_kpa, 3),
        "dp_total_psi": round(dp_upper_kpa * 0.145038, 3),
        "cyl_ve": [round(float(v), 4) for v in ve_cyl],
        "ve_maldistribution_spread_pct": round(ve_spread_pct, 2),
        "runner_discharge_coeff_cd": round(cd_runner, 4),
        "peak_mach_exit": round(mach_peak_exit, 3),
        "helmholtz_freq_hz": round(f_helmholtz_hz, 1),
        "helmholtz_3rd_harmonic_rpm": round(rpm_helmholtz_3rd, 0),
        "quarter_wave_4th_harmonic_rpm": round(rpm_pulse_4th, 0),
        "runner_length_total_mm": round(l_total_acoustic_m * 1000.0, 0),
    }


def estimate_boosted_airflow_lbmin(rpm: float, sim: dict, mode_tag: str) -> float:
    """
    Estimate WOT 18.0 psi turbo mass airflow [lb/min] across 3,000-7,500 RPM,
    anchored directly to the car's logged v037 telemetry (37.85 lb/min @ 6,397 RPM,
    18.04 psi boost, 72 deg F IAT -> rho = 2.660 kg/m^3), scaled by upper-manifold
    pressure recovery (P0 - dP) and runner inertial/acoustic response.
    """
    # At v037 Pull 6 logged IAT (72 F = 295.37 K) and 18.04 psi boost (225.7 kPa abs):
    rho_v037 = 225700.0 / (va.R_AIR * 295.37)  # 2.662 kg/m^3
    cam_env = 0.915 + 0.085 * math.exp(-((rpm - 6350.0) / 2150.0) ** 2) - 0.030 * max(0.0, (rpm - 6700.0) / 800.0) ** 1.4
    p_plenum_ratio = (va.P0_IN_PA - sim["dp_total_kpa"] * 1e3) / va.P0_IN_PA

    if mode_tag == "oem_long":
        acoustic = 1.0 + 0.024 * math.exp(-((rpm - 4350.0) / 1350.0) ** 2) - 0.078 * max(0.0, (rpm - 4900.0) / 2600.0) ** 1.55
    elif mode_tag == "oem_short":
        acoustic = 1.000
    else:
        low_tradeoff = -0.008 * max(0.0, (3900.0 - rpm) / 900.0)
        high_gain = 0.020 * (1.0 / (1.0 + math.exp(-(rpm - 5300.0) / 550.0)))
        acoustic = 1.000 + low_tradeoff + high_gain

    disp_m3 = va.ENGINE_DISP_L * 1e-3
    # Calibration factor 1.004 anchors OEM Short-Runner directly through v037 Pull 6 (37.85 lb/min @ 6,397 RPM)
    mdot_raw_kgs = rho_v037 * disp_m3 * (rpm / 120.0) * cam_env * p_plenum_ratio * acoustic * 1.004
    return round(mdot_raw_kgs * 132.277, 2)


def main():
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    verif = json.loads(VERIF_PATH.read_text(encoding="utf-8"))

    custom_audit = verif["boost_optimized"]["cad_audit"]
    left_vol_cm3 = manifest["parts"]["svt_intake_manifold_split_left_cyl1_2"]["solid_volume_cm3"]
    right_vol_cm3 = manifest["parts"]["svt_intake_manifold_split_right_cyl3_4_tb"]["solid_volume_cm3"]
    custom_plastic_mass_kg = (left_vol_cm3 + right_vol_cm3) * CUSTOM_CF_PA_DENSITY_G_CM3 / 1000.0
    custom_total_mass_kg = custom_plastic_mass_kg + CUSTOM_HARDWARE_MASS_KG

    rpms = list(range(3000, 7750, 250))
    curves = {"oem_long": [], "oem_short": [], "custom": []}

    for rpm in rpms:
        r_long = simulate_oem_dsi_point("long", float(rpm))
        r_long["est_airflow_lbmin"] = estimate_boosted_airflow_lbmin(float(rpm), r_long, "oem_long")
        curves["oem_long"].append(r_long)

        r_short = simulate_oem_dsi_point("short", float(rpm))
        r_short["est_airflow_lbmin"] = estimate_boosted_airflow_lbmin(float(rpm), r_short, "oem_short")
        curves["oem_short"].append(r_short)

        s_cust = va.solve_1d_compressible_and_pulsating(params, custom_audit, rpm=float(rpm))
        c_entry = {k: v for k, v in s_cust.items() if not k.startswith("_")}
        c_entry["est_airflow_lbmin"] = estimate_boosted_airflow_lbmin(float(rpm), c_entry, "custom")
        c_entry["runner_length_total_mm"] = 243.0
        curves["custom"].append(c_entry)

    # Extract 6,500 RPM (closest grid to v037 Pull 6 6,397 RPM) & 7,000 RPM snapshots
    idx_6500 = rpms.index(6500)
    idx_7000 = rpms.index(7000)

    def summarize_7000(pt: dict, tag: str) -> dict:
        ve_arr = pt["cyl_ve"]
        afr_target = 11.0
        # At constant injected fuel per cylinder (batch/sequential equal pulsewidth), leanest cyl AFR ~ 11.0 * (mean_ve / min_ve)
        mean_ve = sum(ve_arr) / 4.0
        lean_afr = afr_target * (mean_ve / min(ve_arr))
        rich_afr = afr_target * (mean_ve / max(ve_arr))
        return {
            "mode": tag,
            "dp_7000_kpa": pt["dp_total_kpa"],
            "dp_7000_psi": pt["dp_total_psi"],
            "ve_spread_7000_pct": pt["ve_maldistribution_spread_pct"],
            "cyl_ve_7000": ve_arr,
            "leanest_to_richest_afr_at_11p0": [round(rich_afr, 2), round(lean_afr, 2)],
            "afr_spread_band": round(lean_afr - rich_afr, 2),
            "peak_mach_exit_7000": pt["peak_mach_exit"],
            "est_airflow_6500_lbmin": curves[tag if tag != "custom_round" else "custom"][idx_6500]["est_airflow_lbmin"],
            "est_airflow_7000_lbmin": pt["est_airflow_lbmin"],
            "helmholtz_3rd_harmonic_rpm": pt["helmholtz_3rd_harmonic_rpm"],
            "runner_length_total_mm": pt.get("runner_length_total_mm", 243.0),
        }

    summary_7000 = {
        "oem_dsi_long": summarize_7000(curves["oem_long"][idx_7000], "oem_long"),
        "oem_dsi_short": summarize_7000(curves["oem_short"][idx_7000], "oem_short"),
        "custom_round_2in": summarize_7000(curves["custom"][idx_7000], "custom_round"),
    }

    # Add exact 3D FVM figures for custom
    summary_7000["custom_round_2in"]["cfd_3d_spread_pct"] = verif["boost_optimized"]["cfd_3d"]["cyl_maldistribution_spread_pct"]
    summary_7000["custom_round_2in"]["cfd_3d_dp_psi"] = verif["boost_optimized"]["cfd_3d"]["tb_to_plenum_dp_psi"]
    summary_7000["custom_round_2in"]["cfd_3d_cyl_share_pct"] = verif["boost_optimized"]["cfd_3d"]["cyl_flow_share_pct"]

    hp_per_lbmin = 10.75  # Anchored to v037 Pull 6: 37.85 lb/min -> ~407 bhp
    dl_short = round(curves["custom"][idx_7000]["est_airflow_lbmin"] - curves["oem_short"][idx_7000]["est_airflow_lbmin"], 2)
    dl_long = round(curves["custom"][idx_7000]["est_airflow_lbmin"] - curves["oem_long"][idx_7000]["est_airflow_lbmin"], 2)

    hardware_comp = {
        "oem_upper_dsi": {
            "material": "Molded PA66-GF30 Plastic Clamshell (2M5Z-9424-BB) + IMRC Cable/Box",
            "estimated_mass_kg": round(OEM_UPPER_DSI_MASS_KG, 2),
            "estimated_mass_lb": round(OEM_UPPER_DSI_MASS_KG * 2.20462, 2),
            "thermal_conductivity_w_mk": OEM_PA66_GF30_K_W_MK,
            "plenum_volume_liters": 2.20,
            "imrc_drum_and_shaft_seals": "Vibration-welded NA seams + 2x rotary drum shaft seals (common boost leak source)",
            "vac_boost_reference_ports": "Shared OEM tee fittings (requires aftermarket vac block)",
            "iacv_metering": "Integrated to OEM upper molding; recirculated internally",
        },
        "custom_stage2_round": {
            "material": "Annealed PPA-CF / PAHT-CF (3D Printed 2-Piece Split) + Epoxy Exterior Seal",
            "printed_volume_cm3": round(left_vol_cm3 + right_vol_cm3, 2),
            "estimated_mass_kg": round(custom_total_mass_kg, 2),
            "estimated_mass_lb": round(custom_total_mass_kg * 2.20462, 2),
            "mass_savings_lb": round((OEM_UPPER_DSI_MASS_KG - custom_total_mass_kg) * 2.20462, 2),
            "thermal_conductivity_w_mk": CUSTOM_CF_PA_K_W_MK,
            "plenum_volume_liters": verif["boost_optimized"]["cad_audit"]["bare_plenum_volume_liters"],
            "imrc_drum_and_shaft_seals": "Deleted (0 rotating shafts; dual Viton O-rings + 2x dowels)",
            "vac_boost_reference_ports": "5 dedicated NPT pads (3x boost/vac + 2x check-valved vac-only)",
            "iacv_metering": "OEM 2-bolt Ford IACV with isolated 1/4 NPT blow-through MAF supply barb",
        },
        "estimated_gains_7000rpm_18psi": {
            "airflow_gain_vs_oem_short_lbmin": dl_short,
            "estimated_bhp_gain_vs_oem_short": round(dl_short * hp_per_lbmin, 1),
            "airflow_gain_vs_oem_long_lbmin": dl_long,
            "estimated_bhp_gain_vs_oem_long": round(dl_long * hp_per_lbmin, 1),
        },
    }

    report = {
        "methodology_note": (
            "Custom manifold specs & 3D CFD values come directly from CAD solids and verify_airflow.py. "
            "OEM Focus SVT/ST170 DSI values represent physics-modeled estimates based on documented "
            "runner/drum architecture (no laser scan of OEM clamshell on file). Real car telemetry "
            "points are taken from reports/2026-11-06-v037-iat-thermal-and-power-review.md."
        ),
        "logged_v037_points": LOGGED_V037_POINTS,
        "summary_7000rpm": summary_7000,
        "hardware_comparison": hardware_comp,
        "rpm_curves": curves,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    render_comparison_figure(rpms, curves, summary_7000, hardware_comp, OUT_PNG)
    print(f"Saved {OUT_JSON.relative_to(ROOT)} and {OUT_PNG.relative_to(ROOT)}")
    print(
        f"7000 RPM @ 18 psi: "
        f"OEM Long dP={summary_7000['oem_dsi_long']['dp_7000_psi']} psi (VE spread {summary_7000['oem_dsi_long']['ve_spread_7000_pct']}%) | "
        f"OEM Short dP={summary_7000['oem_dsi_short']['dp_7000_psi']} psi (VE spread {summary_7000['oem_dsi_short']['ve_spread_7000_pct']}%) | "
        f"Custom dP={summary_7000['custom_round_2in']['dp_7000_psi']} psi (1D spread {summary_7000['custom_round_2in']['ve_spread_7000_pct']}%, 3D spread {summary_7000['custom_round_2in']['cfd_3d_spread_pct']}%)"
    )
    print(
        f"Weight: Custom {hardware_comp['custom_stage2_round']['estimated_mass_lb']} lb vs OEM {hardware_comp['oem_upper_dsi']['estimated_mass_lb']} lb "
        f"(saves {hardware_comp['custom_stage2_round']['mass_savings_lb']} lb) | "
        f"Est Gain @ 7k: +{dl_short} lb/min (~+{round(dl_short*hp_per_lbmin,1)} bhp) vs Short, +{dl_long} lb/min (~+{round(dl_long*hp_per_lbmin,1)} bhp) vs Long"
    )


def render_comparison_figure(rpms, curves, s7k, hw, out_path: Path):
    fig = plt.figure(figsize=(18, 12), facecolor="#f5f4f0")
    fig.suptitle(
        'Custom Stage-2 Max-Boost (Ø50.8 / Ø42.8 mm Round) vs. Factory 2004 Focus SVT DSI Manifold — 18 PSI Boost',
        fontsize=14.5,
        fontweight="bold",
        y=0.975,
        color="#182028",
    )

    c_long = "#c0392b"
    c_short = "#d68910"
    c_cust = "#117864"

    # Panel 1: Upper-Manifold Pressure Drop vs RPM
    ax1 = fig.add_subplot(3, 2, 1)
    ax1.set_facecolor("#ffffff")
    dp_long = [p["dp_total_psi"] for p in curves["oem_long"]]
    dp_short = [p["dp_total_psi"] for p in curves["oem_short"]]
    dp_cust = [p["dp_total_psi"] for p in curves["custom"]]
    ax1.plot(rpms, dp_long, "o--", color=c_long, lw=2.0, ms=4, label="Factory DSI — Long Runner (~475 mm scroll)")
    ax1.plot(rpms, dp_short, "s-.", color=c_short, lw=2.0, ms=4, label="Factory DSI — Short Runner (~320 mm, IMRC Open)")
    ax1.plot(rpms, dp_cust, "^-", color=c_cust, lw=2.6, ms=5.5, label='Custom Stage-2 (243 mm, Flush Bellmouth, Ø42.8 Round)')
    ax1.axvspan(5500, 6000, color="#ebedef", alpha=0.8, label="Stock IMRC Switch Window (5.5k–6k RPM)")
    ax1.set_title("1. Upper-Manifold Pressure Drop (ΔP) @ 18.0 PSI Boost", fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Engine Speed [RPM]", fontsize=8.5)
    ax1.set_ylabel("Upper Manifold Loss ΔP [psi]", fontsize=8.5)
    ax1.set_ylim(0.0, max(dp_long) * 1.15)
    ax1.grid(True, ls=":", alpha=0.55)
    ax1.legend(fontsize=7.8, loc="upper left")

    # Panel 2: Estimated Boosted Mass Airflow vs RPM + v037 Real Car Telemetry
    ax2 = fig.add_subplot(3, 2, 2)
    ax2.set_facecolor("#ffffff")
    m_long = [p["est_airflow_lbmin"] for p in curves["oem_long"]]
    m_short = [p["est_airflow_lbmin"] for p in curves["oem_short"]]
    m_cust = [p["est_airflow_lbmin"] for p in curves["custom"]]
    ax2.plot(rpms, m_long, "o--", color=c_long, lw=2.0, ms=4, label="Modeled OEM DSI (Stuck Long — IMRC Disabled)")
    ax2.plot(rpms, m_short, "s-.", color=c_short, lw=2.0, ms=4, label="Modeled OEM DSI (Short / Pinned Open)")
    ax2.plot(rpms, m_cust, "^-", color=c_cust, lw=2.6, ms=5.5, label="Modeled Custom Stage-2 (Ø42.8 mm Round)")
    # Plot real v037 high-boost points (Pull 2 & Pull 6)
    hi_boost_logs = [pt for pt in LOGGED_V037_POINTS if pt["boost_psi"] >= 18.0]
    ax2.scatter(
        [pt["rpm"] for pt in hi_boost_logs],
        [pt["lbmin"] for pt in hi_boost_logs],
        color="#1b2631",
        marker="*",
        s=190,
        zorder=7,
        label="Actual Car Logs (v037 Pull 2 & Pull 6 @ 18.0–18.3 psi)",
    )
    ax2.annotate(
        "v037 Pull 6\n37.85 lb/min @ 6,397 RPM",
        xy=(6397, 37.85),
        xytext=(4850, 41.2),
        fontsize=8,
        fontweight="bold",
        color="#1b2631",
        arrowprops=dict(arrowstyle="->", color="#1b2631", lw=1.1),
    )
    ax2.set_title("2. Modeled WOT Airflow @ v037 72°F IAT (18 PSI) + Car Logs", fontsize=10.5, fontweight="bold")
    ax2.set_xlabel("Engine Speed [RPM]", fontsize=8.5)
    ax2.set_ylabel("Mass Airflow [lb/min]", fontsize=8.5)
    ax2.set_ylim(16, max(m_cust) + 4.5)
    ax2.grid(True, ls=":", alpha=0.55)
    ax2.legend(fontsize=7.6, loc="lower right")

    # Panel 3: Cylinder-to-Cylinder Balance & Lean-Cylinder AFR Safety @ 7,000 RPM
    ax3 = fig.add_subplot(3, 2, 3)
    ax3.set_facecolor("#ffffff")
    cyls = np.arange(1, 5)
    w = 0.24
    ve_l = [100.0 * v for v in s7k["oem_dsi_long"]["cyl_ve_7000"]]
    ve_s = [100.0 * v for v in s7k["oem_dsi_short"]["cyl_ve_7000"]]
    ve_c = [100.0 * v for v in s7k["custom_round_2in"]["cyl_ve_7000"]]
    ax3.bar(cyls - w, ve_l, width=w, color=c_long, alpha=0.88, label=f"OEM Long (Spread {s7k['oem_dsi_long']['ve_spread_7000_pct']:.2f}%)")
    ax3.bar(cyls, ve_s, width=w, color=c_short, alpha=0.90, label=f"OEM Short (Spread {s7k['oem_dsi_short']['ve_spread_7000_pct']:.2f}%)")
    ax3.bar(cyls + w, ve_c, width=w, color=c_cust, alpha=0.92, label=f"Custom Ø42.8 (1D {s7k['custom_round_2in']['ve_spread_7000_pct']:.2f}% | 3D {s7k['custom_round_2in']['cfd_3d_spread_pct']:.2f}%)")
    ax3.axhline(98.0, color="#444444", ls="--", lw=1.0)
    ax3.set_xticks(cyls)
    ax3.set_xticklabels([f"Cyl {i}" for i in cyls])
    ax3.set_ylim(92.0, 102.5)
    ax3.set_title("3. Cylinder-to-Cylinder VE Balance @ 7,000 RPM / 18 PSI", fontsize=10.5, fontweight="bold")
    ax3.set_ylabel("Effective Volumetric Efficiency [%]", fontsize=8.5)
    ax3.grid(True, axis="y", ls=":", alpha=0.55)
    ax3.legend(fontsize=7.6, loc="lower right")

    # Panel 4: Acoustic Helmholtz & Mach Comparison
    ax4 = fig.add_subplot(3, 2, 4)
    ax4.set_facecolor("#ffffff")
    mach_l = [p["peak_mach_exit"] for p in curves["oem_long"]]
    mach_s = [p["peak_mach_exit"] for p in curves["oem_short"]]
    mach_c = [p["peak_mach_exit"] for p in curves["custom"]]
    ax4.plot(rpms, mach_l, "o--", color=c_long, lw=2.0, ms=4, label=f"OEM Long (Helmholtz 3rd @ {int(s7k['oem_dsi_long']['helmholtz_3rd_harmonic_rpm'])} RPM)")
    ax4.plot(rpms, mach_s, "s-.", color=c_short, lw=2.0, ms=4, label=f"OEM Short (Helmholtz 3rd @ {int(s7k['oem_dsi_short']['helmholtz_3rd_harmonic_rpm'])} RPM)")
    ax4.plot(rpms, mach_c, "^-", color=c_cust, lw=2.6, ms=5.5, label=f"Custom Stage-2 (Helmholtz 3rd @ {int(s7k['custom_round_2in']['helmholtz_3rd_harmonic_rpm'])} RPM)")
    ax4.axvline(s7k["custom_round_2in"]["helmholtz_3rd_harmonic_rpm"], color=c_cust, ls=":", lw=1.3, alpha=0.8)
    ax4.axhspan(0.0, 0.32, color="#d4efdf", alpha=0.45, label="Low-Drag Subsonic Zone (M < 0.32)")
    ax4.set_title("4. Peak Runner-Exit Mach Number & Plenum Resonance", fontsize=10.5, fontweight="bold")
    ax4.set_xlabel("Engine Speed [RPM]", fontsize=8.5)
    ax4.set_ylabel("Peak Instantaneous Exit Mach", fontsize=8.5)
    ax4.set_ylim(0.08, max(max(mach_l), max(mach_s), max(mach_c)) * 1.15)
    ax4.grid(True, ls=":", alpha=0.55)
    ax4.legend(fontsize=7.6, loc="upper left")

    # Panel 5: Weight, Internal Blockage, ΔP, & AFR Margin Bars
    ax5 = fig.add_subplot(3, 2, 5)
    ax5.set_facecolor("#ffffff")
    categories = [
        "Upper Weight\n[lb]",
        "Internal Blockage\n[%]",
        "1D ΔP @ 7k\n[psi × 10]",
        "Cyl Spread\n[%]",
        "AFR Spread\n[@ 11.0 AFR × 10]",
    ]
    oem_vals = [
        hw["oem_upper_dsi"]["estimated_mass_lb"],
        12.0,  # Short-runner rotary drum internal wake blockage (%)
        s7k["oem_dsi_short"]["dp_7000_psi"] * 10.0,
        s7k["oem_dsi_short"]["ve_spread_7000_pct"],
        s7k["oem_dsi_short"]["afr_spread_band"] * 10.0,
    ]
    cust_vals = [
        hw["custom_stage2_round"]["estimated_mass_lb"],
        0.0,  # Wall-flush bellmouths (0.00% blockage CAD verified)
        s7k["custom_round_2in"]["dp_7000_psi"] * 10.0,
        s7k["custom_round_2in"]["ve_spread_7000_pct"],
        s7k["custom_round_2in"]["afr_spread_band"] * 10.0,
    ]
    x_pos = np.arange(len(categories))
    bw = 0.34
    b1 = ax5.bar(x_pos - bw * 0.5, oem_vals, width=bw, color="#7f8c8d", alpha=0.90, label="Factory PA66-GF30 DSI (Short Runner)")
    b2 = ax5.bar(x_pos + bw * 0.5, cust_vals, width=bw, color=c_cust, alpha=0.92, label="Custom Stage-2 (CF-Nylon, Ø42.8 Round)")
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            ax5.text(rect.get_x() + rect.get_width() * 0.5, h + 0.25, f"{h:.2f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(categories, fontsize=8)
    ax5.set_ylim(0, max(oem_vals) * 1.25)
    ax5.set_title("5. Weight, Internal Blockage & 18 PSI Safety Margins (Lower is Better)", fontsize=10.5, fontweight="bold")
    ax5.grid(True, axis="y", ls=":", alpha=0.55)
    ax5.legend(fontsize=8, loc="upper right")

    # Panel 6: Side-by-Side Executive Summary Table
    ax6 = fig.add_subplot(3, 2, 6)
    ax6.axis("off")
    ax6.set_title("6. Side-by-Side Comparison Summary (7,000 RPM @ 18.0 PSI)", fontsize=10.5, fontweight="bold", pad=8)
    table_rows = [
        ["Upper Manifold Material", "PA66-GF30 Plastic", "PA66-GF30 Plastic", "PPA-CF / PAHT-CF*"],
        ["Upper Mass (w/ Hardware)", f"{hw['oem_upper_dsi']['estimated_mass_lb']:.1f} lb", f"{hw['oem_upper_dsi']['estimated_mass_lb']:.1f} lb", f"{hw['custom_stage2_round']['estimated_mass_lb']:.2f} lb (-{hw['custom_stage2_round']['mass_savings_lb']:.1f} lb)"],
        ["Thermal Cond. [W/(m·K)]", "~0.40 (molded)", "~0.40 (molded)", "~0.90 (both low soak)"],
        ["Total Runner Length [mm]", "~475 mm", "~320 mm", "243 mm (108 mm upper)"],
        ["Internal Cross-Flow Blockage", "~18% (drum)", "~12% (drum)", "0.00% (CAD verified)"],
        ["Upper ΔP @ 7,000 RPM", f"{s7k['oem_dsi_long']['dp_7000_psi']:.3f} psi", f"{s7k['oem_dsi_short']['dp_7000_psi']:.3f} psi", f"{s7k['custom_round_2in']['dp_7000_psi']:.3f} psi (3D {s7k['custom_round_2in']['cfd_3d_dp_psi']:.3f})"],
        ["1D Cyl VE Spread @ 7k", f"{s7k['oem_dsi_long']['ve_spread_7000_pct']:.2f}%", f"{s7k['oem_dsi_short']['ve_spread_7000_pct']:.2f}%", f"{s7k['custom_round_2in']['ve_spread_7000_pct']:.2f}% (3D {s7k['custom_round_2in']['cfd_3d_spread_pct']:.2f}%)"],
        ["AFR Spread @ 11.0 Target", f"{s7k['oem_dsi_long']['leanest_to_richest_afr_at_11p0'][0]:.2f}–{s7k['oem_dsi_long']['leanest_to_richest_afr_at_11p0'][1]:.2f}", f"{s7k['oem_dsi_short']['leanest_to_richest_afr_at_11p0'][0]:.2f}–{s7k['oem_dsi_short']['leanest_to_richest_afr_at_11p0'][1]:.2f}", f"{s7k['custom_round_2in']['leanest_to_richest_afr_at_11p0'][0]:.2f}–{s7k['custom_round_2in']['leanest_to_richest_afr_at_11p0'][1]:.2f}"],
        ["Helmholtz 3rd Harmonic", f"{int(s7k['oem_dsi_long']['helmholtz_3rd_harmonic_rpm'])} RPM", f"{int(s7k['oem_dsi_short']['helmholtz_3rd_harmonic_rpm'])} RPM", f"{int(s7k['custom_round_2in']['helmholtz_3rd_harmonic_rpm'])} RPM"],
        ["Est. WOT Flow / ΔBHP @ 7k", f"{s7k['oem_dsi_long']['est_airflow_7000_lbmin']} lb/m", f"{s7k['oem_dsi_short']['est_airflow_7000_lbmin']} lb/m", f"{s7k['custom_round_2in']['est_airflow_7000_lbmin']} lb/m (+{hw['estimated_gains_7000rpm_18psi']['estimated_bhp_gain_vs_oem_short']:.0f} vs S)"],
    ]
    tbl = ax6.table(
        cellText=table_rows,
        colLabels=["Metric / Parameter", "OEM DSI Long", "OEM DSI Short", "Custom Ø42.8 Round"],
        cellLoc="center",
        loc="center",
        colWidths=[0.28, 0.21, 0.21, 0.30],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.9)
    tbl.scale(1.0, 1.48)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1f2d3d")
            cell.set_text_props(color="white", fontweight="bold")
        elif c == 3:
            cell.set_facecolor("#e8f8f5")
            cell.set_text_props(fontweight="bold", color="#0e6251")
        else:
            cell.set_facecolor("#ffffff" if r % 2 == 1 else "#f8f9f9")
        cell.set_edgecolor("#d5d8dc")

    fig.text(
        0.5,
        0.012,
        "*Custom printed part requires annealed CF-Nylon (PPA-CF/PAHT-CF) + epoxy exterior seal & 20–25 psi leak test before under-hood boost service. "
        "OEM curves modeled from SVT DSI architecture; v037 telemetry points anchored to car logs.",
        ha="center",
        fontsize=8,
        color="#444444",
    )
    plt.tight_layout(rect=[0, 0.025, 1, 0.945])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
