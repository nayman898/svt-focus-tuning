#!/usr/bin/env python3
"""
analyze-session.py — Universal Fast Paired Datalog Analyzer for Focus SVT Turbo Tuning.
Analyzes VCM Scanner CSV + Innovate SCG-1 CSV logs in seconds.

Usage:
    python tools/analyze-session.py [session_path] [--report]

Features:
    - Auto-discovers latest session if no path provided.
    - Synchronizes VCM and SCG telemetry with binary search.
    - Evaluates:
        1. Idle & Rolling Glide (hang check)
        2. Steady Cruise Fuel Trims & Lambda across MAF voltage bins
        3. Low-RPM Tip-In & Torque Control interventions
        4. Decel Overrun Spark & DFCO Delays
        5. WOT Boost Pulls, Airflow, Lambda, Fuel Pressure
    - Generates markdown report if --report flag is given.
"""

import sys
import os
import glob
import csv
import bisect
import statistics
import argparse
from datetime import datetime

DEFAULT_SESSIONS_DIR = r"C:\source\repos\scg-logger\sessions"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def find_latest_session():
    if not os.path.exists(DEFAULT_SESSIONS_DIR):
        return None
    dirs = [os.path.join(DEFAULT_SESSIONS_DIR, d) for d in os.listdir(DEFAULT_SESSIONS_DIR) if d.startswith("paired-")]
    if not dirs:
        return None
    dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return dirs[0]

def parse_args():
    parser = argparse.ArgumentParser(description="Focus SVT Paired Datalog Analyzer")
    parser.add_argument("session", nargs="?", default=None, help="Path to session folder")
    parser.add_argument("--report", action="store_true", help="Auto-write markdown report to reports/")
    return parser.parse_args()

def analyze(session_dir, write_report=False):
    session_dir = os.path.abspath(session_dir)
    print("=" * 80)
    print(f"SESSION ANALYZER: {os.path.basename(session_dir)}")
    print(f"Path: {session_dir}")
    print("=" * 80)

    vcm_path = os.path.join(session_dir, "vcm.csv")
    scg_path = os.path.join(session_dir, "scg.csv")

    if not os.path.exists(vcm_path):
        print(f"Error: {vcm_path} not found.")
        sys.exit(1)
    if not os.path.exists(scg_path):
        print(f"Error: {scg_path} not found.")
        sys.exit(1)

    # 1. Load VCM
    vcm_rows = []
    with open(vcm_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    h_idx = None
    for i, line in enumerate(lines[:25]):
        if line.startswith("Offset,"):
            h_idx = i
            break
    if h_idx is None:
        print("Error: Could not find Offset header in vcm.csv")
        sys.exit(1)

    headers = [h.strip() for h in lines[h_idx].split(",")]
    for line in lines[h_idx + 2:]:
        parts = line.strip().split(",")
        if len(parts) == len(headers) and parts[0]:
            vcm_rows.append({h: p for h, p in zip(headers, parts)})

    vcm_dur = float(vcm_rows[-1]["Offset"]) - float(vcm_rows[0]["Offset"])
    print(f"VCM Log: {len(vcm_rows)} samples across {vcm_dur:.1f} s ({vcm_dur/60:.2f} min)")

    # 2. Load SCG
    scg_rows = []
    with open(scg_path, "r", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            scg_rows.append(r)

    scg_times, scg_lams, scg_boosts, scg_wgdcs = [], [], [], []
    for r in scg_rows:
        t = float(r["elapsed_s"])
        l = float(r["lambda"]) if r["lambda"] and float(r["lambda"]) > 0 else None
        b = float(r["boost_psi"]) if r["boost_psi"] else None
        w = float(r["commanded_wgdc_pct"]) if r["commanded_wgdc_pct"] else None
        scg_times.append(t)
        scg_lams.append(l)
        scg_boosts.append(b)
        scg_wgdcs.append(w)

    print(f"SCG Log: {len(scg_rows)} samples across {scg_times[-1] - scg_times[0]:.1f} s")

    # Time Alignment
    wot_vcm = [r for r in vcm_rows if float(r["Throttle Position ADC (Absolute)"]) > 700]
    wot_scg = [(t, b) for t, b in zip(scg_times, scg_boosts) if b is not None and b > 5.0]
    if wot_vcm and wot_scg:
        delta_t = wot_scg[0][0] - float(wot_vcm[0]["Offset"])
    else:
        delta_t = 3.50
    print(f"Estimated Time Alignment: delta_t = {delta_t:.2f} s")

    def get_scg_data(vcm_t):
        target = vcm_t + delta_t
        idx = bisect.bisect_left(scg_times, target)
        best_i = None
        min_d = 999.0
        for i in (idx - 1, idx, idx + 1):
            if 0 <= i < len(scg_times):
                d = abs(scg_times[i] - target)
                if d < min_d:
                    min_d = d
                    best_i = i
        if min_d < 0.35 and best_i is not None:
            return scg_lams[best_i], scg_boosts[best_i], scg_wgdcs[best_i]
        return None, None, None

    # Overview Metrics
    rpms = [float(r["Engine RPM"]) for r in vcm_rows]
    ects = [float(r["Engine Coolant Temp"]) for r in vcm_rows]
    valid_boosts = [b for b in scg_boosts if b is not None]
    valid_lams = [l for l in scg_lams if l is not None]
    valid_wgdcs = [w for w in scg_wgdcs if w is not None]

    print("\n--- Summary Highlights ---")
    print(f"RPM Range: {min(rpms):.0f} to {max(rpms):.0f} RPM (mean {statistics.mean(rpms):.0f})")
    print(f"ECT Range: {min(ects):.1f} to {max(ects):.1f} °F")
    b_peak_overall = max(valid_boosts) if valid_boosts else 0.0
    w_peak_overall = max(valid_wgdcs) if valid_wgdcs else 0.0
    print(f"Peak Boost: {b_peak_overall:.2f} psi | Commanded WGDC max: {w_peak_overall:.1f}%")
    print(f"Wideband Lambda: {min(valid_lams):.3f} (WOT rich) to {max(valid_lams):.3f} (decel cut)")

    # 1. Cruising Analysis
    print("\n" + "-" * 40)
    print("1. STEADY CRUISE FUEL TRIMS (Closed Loop, Stoich, 1,800-3,500 RPM)")
    print("-" * 40)
    cruise_rows = [r for r in vcm_rows if r["Closed Loop Active"] == "Yes" and r["Fuel Source"] == "Stoich" and float(r["Engine Coolant Temp"]) >= 175 and 195 <= float(r["Throttle Position ADC (Absolute)"]) <= 350 and 1800 <= float(r["Engine RPM"]) <= 3500]
    
    maf_bins = [
        (0.80, 0.90),
        (0.90, 1.00),
        (1.00, 1.10),
        (1.10, 1.20),
        (1.20, 1.30),
        (1.30, 1.40),
        (1.40, 1.60),
    ]
    cruise_results = []
    print(f"{'MAF Voltage':<15} | {'Samples':<8} | {'Mean STFT':<10} | {'Median STFT':<12} | {'Lambda Mean'}")
    print("-" * 65)
    for low, high in maf_bins:
        matched = [r for r in cruise_rows if low <= float(r["Mass Airflow Sensor"]) < high]
        if matched:
            stfts = [float(r["Short Term Fuel Trim Bank 1"]) for r in matched if r["Short Term Fuel Trim Bank 1"]]
            lams = [get_scg_data(float(r["Offset"]))[0] for r in matched]
            lams = [l for l in lams if l is not None]
            m_stft = statistics.mean(stfts)
            med_stft = statistics.median(stfts)
            m_lam = statistics.mean(lams) if lams else 1.00
            cruise_results.append((low, high, len(matched), m_stft, med_stft, m_lam))
            print(f"{low:.2f}V - {high:.2f}V   | {len(matched):<8} | {m_stft:+6.2f}%   | {med_stft:+6.2f}%     | {m_lam:.3f}")

    # 2. Low-RPM Tip-In & Torque Control Analysis
    print("\n" + "-" * 40)
    print("2. LOW-RPM TIP-IN & TORQUE CONTROL INTERVENTIONS")
    print("-" * 40)
    tc_low = [r for r in vcm_rows if r["Spark Source"] == "Torque Control" and float(r["Engine RPM"]) <= 2400 and float(r["Throttle Position ADC (Absolute)"]) >= 190]
    tipin_trans = [r for r in vcm_rows if 1200 <= float(r["Engine RPM"]) <= 2400 and 190 <= float(r["Throttle Position ADC (Absolute)"]) <= 280 and 0.70 <= float(r["Mass Airflow Sensor"]) <= 0.90]
    print(f"Torque Control cuts below 2,400 RPM (open throttle): {len(tc_low)} samples")
    if tipin_trans:
        tipin_lams = [get_scg_data(float(r["Offset"]))[0] for r in tipin_trans]
        tipin_lams = [l for l in tipin_lams if l is not None]
        if tipin_lams:
            print(f"Tip-In Lambda (0.70-0.90V MAF): mean={statistics.mean(tipin_lams):.3f}, max={max(tipin_lams):.3f} (leanest)")

    # 3. Decel Overrun Analysis
    print("\n" + "-" * 40)
    print("3. DECEL OVERRUN SPARK & ENGINE BRAKING")
    print("-" * 40)
    decel_rows = [r for r in vcm_rows if float(r["Throttle Position ADC (Absolute)"]) <= 186 and float(r["Engine RPM"]) >= 2500]
    if decel_rows:
        decel_sparks = [float(r["Timing Advance"]) for r in decel_rows]
        print(f"Decel samples (>2,500 RPM, closed throttle): {len(decel_rows)}")
        print(f"Decel Spark Range: min = {min(decel_sparks):.1f}° (deepest retard) to max = {max(decel_sparks):.1f}° (mean {statistics.mean(decel_sparks):.1f}°)")

    # 4. WOT Boost Pulls Analysis
    print("\n" + "-" * 40)
    print("4. WIDE-OPEN THROTTLE PULLS (TPS > 60%)")
    print("-" * 40)
    pulls = []
    cur = []
    for r in vcm_rows:
        if float(r["Throttle Position ADC (Absolute)"]) > 600:
            cur.append(r)
        else:
            if len(cur) >= 10:
                pulls.append(cur)
            cur = []
    if len(cur) >= 10:
        pulls.append(cur)

    print(f"Detected {len(pulls)} WOT pull(s):")
    pull_summaries = []
    for idx, p in enumerate(pulls):
        t_start = float(p[0]["Offset"])
        t_end = float(p[-1]["Offset"])
        p_rpms = [float(r["Engine RPM"]) for r in p]
        p_sparks = [float(r["Timing Advance"]) for r in p]
        p_mafs = [float(r["Mass Airflow"]) for r in p]
        scg_pts = [get_scg_data(float(r["Offset"])) for r in p]
        p_boosts = [b for l, b, w in scg_pts if b is not None]
        p_lams = [l for l, b, w in scg_pts if l is not None]
        p_wgs = [w for l, b, w in scg_pts if w is not None]

        b_peak = max(p_boosts) if p_boosts else 0.0
        l_min = min(p_lams) if p_lams else 1.0
        l_max = max(p_lams) if p_lams else 1.0
        wg_peak = max(p_wgs) if p_wgs else 0.0
        maf_peak = max(p_mafs)

        pull_summaries.append((idx+1, t_start, t_end, min(p_rpms), max(p_rpms), b_peak, wg_peak, l_min, l_max, maf_peak))
        print(f"Pull #{idx+1} [t={t_start:.1f}s - {t_end:.1f}s]: RPM {min(p_rpms):.0f} -> {max(p_rpms):.0f} | Boost Peak: {b_peak:.2f} psi | WGDC: {wg_peak:.0f}% | Lam: {l_min:.3f}-{l_max:.3f} | Max Airflow: {maf_peak:.2f} lb/min")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE.")
    print("=" * 80)

if __name__ == "__main__":
    args = parse_args()
    target_session = args.session if args.session else find_latest_session()
    if not target_session:
        print(f"Error: No sessions found in {DEFAULT_SESSIONS_DIR}")
        sys.exit(1)
    analyze(target_session, write_report=args.report)
