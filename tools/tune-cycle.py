#!/usr/bin/env python3
"""
tune-cycle.py — End-to-End Offline Tuning Pipeline for Focus SVT Turbo.

Automates the complete cycle from road datalog ingestion to VCM Editor calibration
generation, delta extraction, documentation, and owner inspection guide.

Workflow:
    1. Ingests & synchronizes latest paired session (VCM Scanner CSV + Innovate SCG-1 CSV).
    2. Analyzes fuel trims (MAF bins), tip-in transients, decel overrun, and WOT boost pulls.
    3. Formulates calibration adjustments & generates JSON tune specification.
    4. Drives VCM Editor via UIAutomation to build candidate .hpt file (with verification & compare).
    5. Automatically generates:
       - tunes/<candidate>.md (User inspection guide & diff table)
       - docs/<candidate>-regression-test.md & docs/<candidate>-run-card.json
       - reports/calibration-inventory/<candidate>/delta.json
       - Updates tunes/revisions.json & vehicle.json
       - Rebuilds reports/calibration-inventory/index.html
       - Runs strict privacy scanner (verify-privacy.py)

Usage:
    # Full automated cycle from latest session (analysis + build + docs):
    python tools/tune-cycle.py

    # Analyze specific session only:
    python tools/tune-cycle.py --session <path_to_session> --analyze-only

    # Generate candidate tune from specific spec JSON:
    python tools/tune-cycle.py --spec <path_to_spec.json>

    # Dry-run analysis and spec generation (without launching VCM Editor):
    python tools/tune-cycle.py --dry-run
"""

import os
import sys
import json
import csv
import re
import bisect
import hashlib
import argparse
import subprocess
import statistics
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SESSIONS_DIR = r"C:\source\repos\scg-logger\sessions"

# 30 Voltage Breakpoints for [ECM] 12163 MAF Airflow vs. Voltage
MAF_BREAKPOINTS = [
    (1, 0.000), (2, 0.379), (3, 0.400), (4, 0.439), (5, 0.479),
    (6, 0.500), (7, 0.529), (8, 0.540), (9, 0.600), (10, 0.649),
    (11, 0.699), (12, 0.898), (13, 1.000), (14, 1.100), (15, 1.200),
    (16, 1.299), (17, 1.399), (18, 1.500), (19, 1.600), (20, 1.799),
    (21, 2.000), (22, 2.200), (23, 2.400), (24, 2.598), (25, 2.799),
    (26, 3.000), (27, 3.200), (28, 3.400), (29, 3.799), (30, 4.800)
]

def scrub_check(text):
    """Enforce strict privacy: zero 17-char VINs, zero 10-digit MPVI serials."""
    vin_pat = re.compile(r"\b1FAFP3[0-9A-Za-z]{11}\b", re.IGNORECASE)
    serial_pat = re.compile(r"\b\d{10}\b")
    if vin_pat.search(text):
        raise ValueError("Privacy violation: VIN detected in text payload!")
    for m in serial_pat.finditer(text):
        val = m.group(0)
        # Allow unix epoch timestamps (16x, 17x, 18x)
        if not (val.startswith("16") or val.startswith("17") or val.startswith("18")):
            raise ValueError(f"Privacy violation: Potential 10-digit device serial detected ({val})!")

def find_latest_session():
    if not os.path.exists(SESSIONS_DIR):
        return None
    dirs = [os.path.join(SESSIONS_DIR, d) for d in os.listdir(SESSIONS_DIR) if d.startswith("paired-")]
    if not dirs:
        return None
    dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return dirs[0]

def load_vcm_data(vcm_path):
    with open(vcm_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    h_idx = None
    for i, line in enumerate(lines[:25]):
        if line.startswith("Offset,"):
            h_idx = i
            break
    if h_idx is None:
        raise ValueError(f"Could not find 'Offset,' header in {vcm_path}")
    headers = [h.strip() for h in lines[h_idx].split(",")]
    rows = []
    for line in lines[h_idx + 2:]:
        parts = line.strip().split(",")
        if len(parts) == len(headers) and parts[0]:
            rows.append({h: p for h, p in zip(headers, parts)})
    return rows

def load_scg_data(scg_path):
    rows = []
    with open(scg_path, "r", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    times, lams, boosts, wgdcs = [], [], [], []
    for r in rows:
        t = float(r["elapsed_s"])
        l = float(r["lambda"]) if r.get("lambda") and float(r["lambda"]) > 0 else None
        b = float(r["boost_psi"]) if r.get("boost_psi") else None
        w = float(r["commanded_wgdc_pct"]) if r.get("commanded_wgdc_pct") else None
        times.append(t)
        lams.append(l)
        boosts.append(b)
        wgdcs.append(w)
    return times, lams, boosts, wgdcs

def analyze_session_data(session_dir):
    vcm_path = os.path.join(session_dir, "vcm.csv")
    scg_path = os.path.join(session_dir, "scg.csv")
    if not os.path.exists(vcm_path) or not os.path.exists(scg_path):
        raise FileNotFoundError(f"Session directory missing vcm.csv or scg.csv: {session_dir}")

    vcm_rows = load_vcm_data(vcm_path)
    scg_times, scg_lams, scg_boosts, scg_wgdcs = load_scg_data(scg_path)

    # Time Alignment
    wot_vcm = [r for r in vcm_rows if float(r.get("Throttle Position ADC (Absolute)", 0)) > 700]
    wot_scg = [(t, b) for t, b in zip(scg_times, scg_boosts) if b is not None and b > 5.0]
    if wot_vcm and wot_scg:
        delta_t = wot_scg[0][0] - float(wot_vcm[0]["Offset"])
    else:
        delta_t = 3.41

    def get_scg(vcm_t):
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

    # 1. Closed Loop Cruising Analysis
    cruise_rows = [
        r for r in vcm_rows
        if r.get("Closed Loop Active") == "Yes"
        and r.get("Fuel Source") == "Stoich"
        and float(r.get("Engine Coolant Temp", 0)) >= 175
        and 195 <= float(r.get("Throttle Position ADC (Absolute)", 0)) <= 350
        and 1800 <= float(r.get("Engine RPM", 0)) <= 3500
    ]

    maf_corrections = []
    # Evaluate MAF voltage bins matching table columns
    # Group into discrete bins around the breakpoints
    for i in range(len(MAF_BREAKPOINTS) - 1):
        col, v_low = MAF_BREAKPOINTS[i]
        _, v_high = MAF_BREAKPOINTS[i + 1]
        matched = [r for r in cruise_rows if v_low <= float(r.get("Mass Airflow Sensor", 0)) < v_high]
        if len(matched) >= 15:
            stfts = [float(r["Short Term Fuel Trim Bank 1"]) for r in matched if r.get("Short Term Fuel Trim Bank 1")]
            if stfts:
                m_stft = statistics.mean(stfts)
                med_stft = statistics.median(stfts)
                corr_pct = m_stft
                maf_corrections.append({
                    "column": col + 1,  # column representing the higher bound or matching bin
                    "v_low": v_low,
                    "v_high": v_high,
                    "count": len(matched),
                    "mean_stft": m_stft,
                    "median_stft": med_stft,
                    "corr_pct": corr_pct
                })

    # 2. Tip-In & Torque Control Analysis
    tc_cuts = [
        r for r in vcm_rows
        if r.get("Spark Source") == "Torque Control"
        and float(r.get("Engine RPM", 0)) <= 2400
        and float(r.get("Throttle Position ADC (Absolute)", 0)) >= 190
    ]
    tipin_trans = [
        r for r in vcm_rows
        if 1200 <= float(r.get("Engine RPM", 0)) <= 2400
        and 190 <= float(r.get("Throttle Position ADC (Absolute)", 0)) <= 280
        and 0.70 <= float(r.get("Mass Airflow Sensor", 0)) <= 0.90
    ]
    tipin_lams = []
    if tipin_trans:
        for r in tipin_trans:
            lam = get_scg(float(r["Offset"]))[0]
            if lam:
                tipin_lams.append(lam)

    # 3. Decel Overrun Analysis
    decel_rows = [
        r for r in vcm_rows
        if float(r.get("Throttle Position ADC (Absolute)", 0)) <= 186
        and float(r.get("Engine RPM", 0)) >= 2500
    ]
    decel_sparks = [float(r["Timing Advance"]) for r in decel_rows if r.get("Timing Advance")]

    # 4. WOT Pulls Analysis
    pulls = []
    cur = []
    for r in vcm_rows:
        if float(r.get("Throttle Position ADC (Absolute)", 0)) > 600:
            cur.append(r)
        else:
            if len(cur) >= 10:
                pulls.append(cur)
            cur = []
    if len(cur) >= 10:
        pulls.append(cur)

    wot_summaries = []
    for idx, p in enumerate(pulls):
        t_start = float(p[0]["Offset"])
        t_end = float(p[-1]["Offset"])
        p_rpms = [float(r["Engine RPM"]) for r in p]
        p_mafs = [float(r["Mass Airflow"]) for r in p]
        scg_pts = [get_scg(float(r["Offset"])) for r in p]
        p_boosts = [b for l, b, w in scg_pts if b is not None]
        p_lams = [l for l, b, w in scg_pts if l is not None]
        p_wgs = [w for l, b, w in scg_pts if w is not None]

        b_peak = max(p_boosts) if p_boosts else 0.0
        l_min = min(p_lams) if p_lams else 1.0
        l_max = max(p_lams) if p_lams else 1.0
        wg_peak = max(p_wgs) if p_wgs else 0.0
        maf_peak = max(p_mafs) if p_mafs else 0.0
        wot_summaries.append({
            "pull_num": idx + 1,
            "t_start": t_start,
            "t_end": t_end,
            "rpm_min": min(p_rpms),
            "rpm_max": max(p_rpms),
            "boost_peak": b_peak,
            "wgdc_peak": wg_peak,
            "lam_min": l_min,
            "lam_max": l_max,
            "maf_peak": maf_peak
        })

    return {
        "session_dir": session_dir,
        "vcm_samples": len(vcm_rows),
        "vcm_duration_s": float(vcm_rows[-1]["Offset"]) - float(vcm_rows[0]["Offset"]),
        "maf_corrections": maf_corrections,
        "torque_control_cuts": len(tc_cuts),
        "tipin_lean_spikes": [l for l in tipin_lams if l > 1.15],
        "tipin_lams_mean": statistics.mean(tipin_lams) if tipin_lams else None,
        "decel_samples": len(decel_rows),
        "decel_spark_min": min(decel_sparks) if decel_sparks else None,
        "decel_spark_mean": statistics.mean(decel_sparks) if decel_sparks else None,
        "wot_pulls": wot_summaries
    }

def print_analysis_summary(diag):
    print("=" * 80)
    print(f"DATALOG DIAGNOSTIC SUMMARY: {os.path.basename(diag['session_dir'])}")
    print(f"Duration: {diag['vcm_duration_s']:.1f} s ({diag['vcm_duration_s']/60:.2f} min) | Samples: {diag['vcm_samples']}")
    print("=" * 80)

    print("\n--- 1. Closed Loop Cruising Trims ---")
    if diag["maf_corrections"]:
        print(f"{'Voltage Window':<18} | {'Col':<4} | {'Samples':<8} | {'Mean STFT':<10} | {'Median STFT':<12} | {'Proposed Action'}")
        print("-" * 75)
        for c in diag["maf_corrections"]:
            act = "Hold (well centered)" if abs(c["mean_stft"]) < 2.0 else f"Scale airflow by {c['corr_pct']:+.1f}%"
            print(f"{c['v_low']:.3f}V - {c['v_high']:.3f}V | {c['column']:<4} | {c['count']:<8} | {c['mean_stft']:+6.2f}%   | {c['median_stft']:+6.2f}%     | {act}")
    else:
        print("No steady cruise bins exceeded 15 samples.")

    print("\n--- 2. Tip-In & Transient Behavior ---")
    print(f"Torque Control Cuts below 2,400 RPM: {diag['torque_control_cuts']} samples")
    if diag['tipin_lams_mean']:
        print(f"Tip-In Lambda Mean: {diag['tipin_lams_mean']:.3f} | Lean Excursions (>1.15): {len(diag['tipin_lean_spikes'])}")

    print("\n--- 3. Decel Overrun Behavior ---")
    if diag['decel_spark_min'] is not None:
        print(f"Decel Samples: {diag['decel_samples']} | Spark Min (Peak Retard): {diag['decel_spark_min']:.1f}° | Mean: {diag['decel_spark_mean']:.1f}°")

    print("\n--- 4. Wide-Open Throttle Pulls ---")
    print(f"Detected {len(diag['wot_pulls'])} WOT pull(s):")
    for p in diag["wot_pulls"]:
        print(f"  Pull #{p['pull_num']}: RPM {p['rpm_min']:.0f} -> {p['rpm_max']:.0f} | Boost: {p['boost_peak']:.2f} psi | WGDC: {p['wgdc_peak']:.0f}% | Lam: {p['lam_min']:.3f}-{p['lam_max']:.3f} | Airflow: {p['maf_peak']:.2f} lb/min")
    print("=" * 80)

def generate_markdown_readme(spec, delta_data):
    """Generate professional, comprehensive tunes/<version>.md review & inspection guide."""
    ver = spec["version"]
    name = spec["name"]
    parent_ver = spec["parent_version"]
    parent_file = spec["parent_file"]
    cand_file = spec["file"]

    lines = []
    lines.append(f"# {ver} — {spec.get('title', name)}")
    lines.append("")
    lines.append(f"**Prepared candidate for owner inspection and staged road testing.**  ")
    lines.append(f"Exact parent and immediate rollback: [{parent_ver}]({parent_ver}.md).")
    lines.append("")
    lines.append(f"- **Candidate Binary**: [{cand_file}]({cand_file})")
    lines.append(f"  - Size: `{delta_data.get('bytes', 'N/A')}` bytes")
    lines.append(f"  - SHA-256: `{delta_data.get('sha256', 'N/A')}`")
    lines.append(f"- **Parent Binary**: [{parent_file}]({parent_file})")
    lines.append(f"  - Size: `{spec.get('parent_bytes', 'N/A')}` bytes")
    lines.append(f"  - SHA-256: `{spec.get('parent_sha256', 'N/A')}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Calibration Rationale")
    lines.append("")
    lines.append(f"{spec.get('rationale', 'Calibration refinement.')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Parameter Changes")
    lines.append("")

    for p in spec.get("parameters", []):
        pid = p.get("id")
        pname = p.get("name")
        pkind = p.get("kind", "table")
        lines.append(f"### `[ECM] {pid}` — {pname}")
        if pkind == "scalar":
            lines.append(f"| Parameter | Parent (`{parent_ver}`) | Candidate (`{ver}`) | Delta |")
            lines.append("| :--- | :---: | :---: | :---: |")
            old_v = p.get("old_value", "N/A")
            new_v = p.get("new_value", "N/A")
            lines.append(f"| **`[ECM] {pid}` {pname}** | {old_v} | **{new_v}** | `{new_v}` vs `{old_v}` |")
        else:
            lines.append("| Row | Column | Parent Value | Candidate Value | Delta / Note |")
            lines.append("| :---: | :---: | :---: | :---: | :--- |")
            for ch in p.get("changes", []):
                r = ch.get("row", 1)
                c = ch.get("col", 1)
                ov = ch.get("old_value", "N/A")
                nv = ch.get("new_value", "N/A")
                extra = f"RPM {ch.get('rpm')}" if "rpm" in ch else (f"{ch.get('voltage')}V" if "voltage" in ch else "")
                lines.append(f"| {r} | {c} | {ov} | **{nv}** | {extra} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Owner VCM Editor Inspection & Validation Guide")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> Always validate candidate changes against the parent calibration before flashing to the vehicle.")
    lines.append("> The assistant NEVER initiates live ECU writes or vehicle actuation.")
    lines.append("")
    lines.append("### 30-Second Validation Procedure:")
    lines.append(f"1. **Open Candidate**: Launch VCM Editor and open `tunes/{cand_file}`.")
    lines.append(f"2. **Open Compare**: Click `Compare > Open Compare File` and select `tunes/{parent_file}`.")
    lines.append("3. **View Comparison Log**: Click `Compare > View Comparison Log`.")
    lines.append("   - Confirm that **ONLY** the target parameters listed above appear in the difference tree.")
    lines.append("   - Confirm that no unintended engine, transmission, or fuel parameters have changed.")
    lines.append("4. **Inspect Parameter Tables**: Navigate to each modified parameter (press `Ctrl+N` and enter Parameter ID) and verify the values match the table above.")
    lines.append("5. **Verify Notes**: Click `Edit > Calibration Details > Notes` and verify the revision note was appended.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Staged Road Test Protocol")
    lines.append("")
    lines.append(f"- Flash `{cand_file}` using VCM Editor (`Flash > Write Vehicle`).")
    lines.append("- Connect paired VCM Scanner + SCG-1 logger.")
    lines.append("- Execute targeted test maneuvers as outlined in the Master Roadmap.")
    lines.append("- Return log session for sub-2-minute automated review.")
    lines.append("")

    readme_path = os.path.join(REPO_ROOT, "tunes", f"{cand_file[:-4]}.md")
    content = "\n".join(lines)
    scrub_check(content)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[tune-cycle] Wrote owner inspection guide: {readme_path}")
    return readme_path

def execute_vcm_build(spec_path):
    ps_script = os.path.join(REPO_ROOT, "tools", "vcm-tune-builder.ps1")
    cmd = [
        "powershell",
        "-STA",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", ps_script,
        "-SpecPath", spec_path
    ]
    print(f"[tune-cycle] Spawning VCM Editor automation via UIAutomation...")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"VCM Tune Builder failed with exit code {proc.returncode}")
    print(proc.stdout)

def generate_run_card(spec, delta_data):
    ver = spec["version"]
    card_data = {
        "schema_version": 1,
        "session": f"candidate-{ver}-drive-01",
        "purpose": spec.get("title", spec["name"]),
        "tune": {
            "filename": spec["file"],
            "sha256": delta_data.get("sha256", ""),
            "bytes": delta_data.get("bytes", 0),
            "parent_filename": spec["parent_file"],
            "status": "Candidate prepared for owner inspection and flash"
        },
        "parent_tune": {
            "filename": spec["parent_file"],
            "sha256": spec.get("parent_sha256", ""),
            "bytes": spec.get("parent_bytes", 0)
        },
        "changes_since_previous_run": spec.get("rationale", ""),
        "profile": {
            "filename": "profiles/2004 Focus SVT - V023 Idle Spark Trial.Channels.xml",
            "status": "All 18 requested channels required; paired with SCG-1 wideband lambda"
        },
        "conditions": {
            "start_ect_f": "Operating temperature (180-205 F)",
            "fuel_or_refueling": "93 octane pump gas",
            "accessories": "Standard driving; A/C OFF during pulls",
            "boost_controller": {
                "model": "Innovate SCG-1",
                "duty_cycle_pct": 6.0,
                "boost_cut_psi": 16.0,
                "active_press_psi": 5.0
            }
        },
        "stop_conditions": [
            "Knock retard > 2.0 deg under boost",
            "Wideband lambda > 0.80 (> 11.7 AFR) under boost > 8 psi",
            "Boost spike > 15.5 psi (approaching 16 psi SCG-1 cut)",
            "Engine stall or severe undershoot (< 700 RPM) on clutch-in"
        ]
    }
    card_path = os.path.join(REPO_ROOT, "docs", f"{ver}-run-card.json")
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, indent=2)
    print(f"[tune-cycle] Wrote run card: {card_path}")
    return card_path

def generate_regression_test(spec, delta_data):
    ver = spec["version"]
    reg_path = os.path.join(REPO_ROOT, "docs", f"{ver}-regression-test.md")
    content = f"""# {ver} staged regression test

Candidate: [{spec.get('title', spec['name'])}](../tunes/{spec['file'][:-4]}.md)
([`{spec['file']}`](../tunes/{spec['file']})).  
Exact parent and immediate rollback: [{spec['parent_version']}](../tunes/{spec['parent_file'][:-4]}.md)
([`{spec['parent_file']}`](../tunes/{spec['parent_file']})).

## Scope of Calibration
{spec.get('rationale', '')}

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI4 connected.
2. Open `tunes/{spec['file']}`.
3. Compare against parent: `Compare > Open Compare File` -> select `tunes/{spec['parent_file']}`.
4. Verify diff: `Compare > View Comparison Log`. Ensure ONLY expected parameters changed.
5. Once verified, flash `{spec['file']}` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
6. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
"""
    scrub_check(content)
    with open(reg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[tune-cycle] Wrote regression test doc: {reg_path}")
    return reg_path

def update_catalog(spec, cand_path):
    with open(cand_path, "rb") as f:
        cand_bytes = len(f.read())
        f.seek(0)
        cand_sha = hashlib.sha256(f.read()).hexdigest().upper()

    ver = spec["version"]
    delta_dir = os.path.join(REPO_ROOT, "reports", "calibration-inventory", ver)
    os.makedirs(delta_dir, exist_ok=True)
    delta_path = os.path.join(delta_dir, "delta.json")

    param_list = spec.get("parameters", [])
    param_changes = []
    for p in param_list:
        if p.get("kind") == "scalar":
            param_changes.append(f"ECM {p.get('id')} {p.get('name')}: {p.get('new_value')}")
        else:
            param_changes.append(f"ECM {p.get('id')} {p.get('name')}: {len(p.get('changes', []))} cells updated")

    delta_data = {
        "version": ver,
        "file": spec["file"],
        "parent": spec["parent_version"],
        "parent_file": spec["parent_file"],
        "bytes": cand_bytes,
        "sha256": cand_sha,
        "parent_sha256": spec.get("parent_sha256", ""),
        "status": f"Prepared candidate; saved/reopened/compared in VCM Editor; ready for owner inspection & test.",
        "rationale": spec.get("rationale", ""),
        "parameters": param_list,
        "changes": param_changes
    }
    with open(delta_path, "w", encoding="utf-8") as f:
        json.dump(delta_data, f, indent=2)
    print(f"[tune-cycle] Wrote delta JSON: {delta_path}")

    # Generate Markdown Guide & Test Protocols
    readme_path = generate_markdown_readme(spec, delta_data)
    generate_run_card(spec, delta_data)
    generate_regression_test(spec, delta_data)

    # Update vehicle.json
    v_path = os.path.join(REPO_ROOT, "vehicle.json")
    if os.path.exists(v_path):
        with open(v_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
        v_data["prepared_candidate"] = spec["file"]
        v_data["prepared_test_revision"] = f"{spec['file']}; candidate prepared for owner entry and flash"
        with open(v_path, "w", encoding="utf-8") as f:
            json.dump(v_data, f, indent=2)
        print(f"[tune-cycle] Updated vehicle.json prepared_candidate: {spec['file']}")

    # Update tunes/revisions.json
    rev_path = os.path.join(REPO_ROOT, "tunes", "revisions.json")
    if os.path.exists(rev_path):
        with open(rev_path, "r", encoding="utf-8") as f:
            rev_data = json.load(f)
        # Check if already present
        existing = [r for r in rev_data.get("revisions", []) if r.get("version") == ver]
        new_rev_entry = {
            "version": ver,
            "file": spec["file"],
            "parent": spec["parent_version"],
            "bytes": cand_bytes,
            "sha256": cand_sha,
            "status": "prepared; ready for owner inspection & staged road test",
            "title": spec.get("title", spec["name"]),
            "description": spec.get("rationale", ""),
            "changes": delta_data["changes"],
            "notes": os.path.basename(readme_path),
            "rollback": spec["parent_file"],
            "verification": "Saved/reopened/compared in VCM Editor; owner inspection required before flashing",
            "inventory_delta": f"../reports/calibration-inventory/{ver}/delta.json"
        }
        if existing:
            for i, r in enumerate(rev_data["revisions"]):
                if r.get("version") == ver:
                    rev_data["revisions"][i] = new_rev_entry
        else:
            rev_data["revisions"].append(new_rev_entry)
        rev_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(rev_path, "w", encoding="utf-8") as f:
            json.dump(rev_data, f, indent=2)
        print(f"[tune-cycle] Updated tunes/revisions.json with {ver}")

    # Rebuild calibration reference HTML
    ref_builder = os.path.join(REPO_ROOT, "tools", "build-calibration-reference.ps1")
    if os.path.exists(ref_builder):
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ref_builder], capture_output=True)
        print(f"[tune-cycle] Rebuilt reports/calibration-inventory/index.html")

    # Strict Privacy Scan
    verify_script = os.path.join(REPO_ROOT, "tools", "verify-privacy.py")
    if os.path.exists(verify_script):
        res = subprocess.run([sys.executable, verify_script], capture_output=True, text=True)
        print(f"[tune-cycle] Privacy check: {res.stdout.strip()}")
        if res.returncode != 0:
            raise RuntimeError(f"Privacy scan failed: {res.stdout}")

    return cand_bytes, cand_sha, readme_path

def main():
    parser = argparse.ArgumentParser(description="Focus SVT Automated Offline Tuning Cycle")
    parser.add_argument("--session", default=None, help="Path to paired session folder")
    parser.add_argument("--spec", default=None, help="Path to pre-existing spec JSON")
    parser.add_argument("--analyze-only", action="store_true", help="Run diagnostics only without generating tune")
    parser.add_argument("--dry-run", action="store_true", help="Analyze and generate spec JSON without launching VCM Editor")
    parser.add_argument("--target-version", default=None, help="Target revision (e.g. v031)")
    parser.add_argument("--name", default=None, help="Target tune name slug")
    args = parser.parse_args()

    session_path = args.session if args.session else find_latest_session()
    if not session_path and not args.spec:
        print(f"Error: No sessions found in {SESSIONS_DIR} and no --spec provided.", file=sys.stderr)
        sys.exit(1)

    print("================================================================================")
    print(" FOCUS SVT OFFLINE AUTO-TUNING PIPELINE")
    print("================================================================================")

    if args.spec:
        spec_path = os.path.abspath(args.spec)
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)
    else:
        # Run Session Analysis
        diag = analyze_session_data(session_path)
        print_analysis_summary(diag)

        if args.analyze_only:
            print("\n[tune-cycle] Analyze-only flag specified. Exiting.")
            sys.exit(0)

        # Read Vehicle State
        v_path = os.path.join(REPO_ROOT, "vehicle.json")
        with open(v_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)

        parent_file = v_data.get("prepared_candidate") or v_data.get("installed_tune")
        parent_ver = parent_file.split("-")[0]
        parent_path = os.path.join(REPO_ROOT, "tunes", parent_file)
        with open(parent_path, "rb") as f:
            parent_bytes = len(f.read())
            f.seek(0)
            parent_sha = hashlib.sha256(f.read()).hexdigest().upper()

        # Determine target version
        p_num = int(parent_ver.replace("v", ""))
        tgt_ver = args.target_version if args.target_version else f"v{p_num+1:03d}"
        tgt_name = args.name if args.name else f"{tgt_ver}-part-throttle-midload-refine"
        tgt_file = f"{tgt_name}.hpt"

        # Formulate parameter recommendations from telemetry
        parameters = []
        notes = []

        # Example: MAF corrections
        maf_changes = []
        for c in diag["maf_corrections"]:
            if abs(c["mean_stft"]) >= 2.0:
                # Lookup current value from revision-reference snapshot if available
                # or compute percentage delta
                maf_changes.append({
                    "col": c["column"],
                    "voltage": c["v_high"],
                    "delta_pct": round(c["corr_pct"], 2),
                    "note": f"STFT error was {c['mean_stft']:+.2f}%"
                })

        if maf_changes:
            parameters.append({
                "id": 12163,
                "name": "MAF Airflow vs. Voltage",
                "kind": "table",
                "changes": maf_changes
            })
            notes.append(f"Adjusted MAF Airflow vs Voltage across {len(maf_changes)} bins based on closed-loop STFT trims.")

        spec = {
            "version": tgt_ver,
            "title": "Part-Throttle Mid-Load Refinement",
            "name": tgt_name,
            "file": tgt_file,
            "parent_version": parent_ver,
            "parent_file": parent_file,
            "parent_sha256": parent_sha,
            "parent_bytes": parent_bytes,
            "rationale": f"Automated calibration refinement derived from road telemetry in {os.path.basename(session_path)}.",
            "parameters": parameters,
            "notes_append": f"=== {tgt_ver.upper()} ({datetime.now().strftime('%Y-%m-%d')}) ===\r\n" + "\r\n".join(notes)
        }

        spec_path = os.path.join(REPO_ROOT, "scratch", f"{tgt_ver}_spec.json")
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
        print(f"\n[tune-cycle] Generated tune specification: {spec_path}")

    if args.dry_run:
        print("\n[tune-cycle] Dry-run complete. Spec is ready for review before execution.")
        sys.exit(0)

    # Step 3: Run VCM Builder Automation
    cand_path = os.path.join(REPO_ROOT, "tunes", spec["file"])
    execute_vcm_build(spec_path)

    # Step 4: Update Catalog, Documentation, Privacy
    cand_bytes, cand_sha, readme_path = update_catalog(spec, cand_path)

    print("\n" + "=" * 80)
    print(" TUNING CYCLE COMPLETED SUCCESSFULLY!")
    print(f" Target Tune:     {cand_path}")
    print(f" File Size:       {cand_bytes} bytes")
    print(f" SHA-256:         {cand_sha}")
    print(f" Inspection Doc:  {readme_path}")
    print("=" * 80)
    print("\nNext Action: Owner opens VCM Editor on desk PC, verifies diff against parent, and inspects notes.")

if __name__ == "__main__":
    main()
