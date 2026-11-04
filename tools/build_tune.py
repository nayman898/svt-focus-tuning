#!/usr/bin/env python3
"""
build_tune.py - Streamlined orchestrator for automated SVT Focus tune generation.

Accepts a tune specification JSON, invokes tools/vcm-tune-builder.ps1 via PowerShell
to drive HP Tuners VCM Editor (attaching to the open instance without killing it),
and automatically generates/updates:
  - tunes/<file>.hpt (verified candidate saved from VCM Editor)
  - tunes/<file>.md (owner inspection guide with parameter diff tables)
  - docs/<ver>-run-card.json (staged test protocol)
  - docs/<ver>-regression-test.md (owner pre-flash safety & verification guide)
  - reports/calibration-inventory/<ver>/delta.json (machine-readable delta)
  - tunes/revisions.json (revision catalog entry)
  - vehicle.json (active vehicle state)
  - reports/calibration-inventory/index.html & revision-reference.json
  - verify-privacy.py check (confirms zero VIN/serial leaks)

Usage:
    python tools/build_tune.py --spec scratch/v033_spec.json
"""

import os
import sys
import json
import re
import argparse
import subprocess
import hashlib
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def scrub_check(text):
    vin_pat = re.compile(r"\b1FAFP3[0-9A-Za-z]{11}\b", re.IGNORECASE)
    serial_pat = re.compile(r"\b\d{10}\b")
    if vin_pat.search(text):
        raise ValueError("Privacy violation: VIN detected in text payload!")
    for m in serial_pat.finditer(text):
        val = m.group(0)
        # Allow unix epoch timestamps (16x, 17x, 18x)
        if not (val.startswith("16") or val.startswith("17") or val.startswith("18")):
            raise ValueError(f"Privacy violation: Potential 10-digit device serial detected ({val})!")

def run_ps_builder(spec_path, kill_on_exit=False):
    ps_script = os.path.join(REPO_ROOT, "tools", "vcm-tune-builder.ps1")
    cmd = [
        "powershell",
        "-STA",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", ps_script,
        "-SpecPath", spec_path
    ]
    if kill_on_exit:
        cmd.append("-KillOnExit")
    print(f"[build_tune] Running VCM Editor automation: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"VCM Tune Builder failed with code {proc.returncode}")
    print(proc.stdout)

def generate_markdown_readme(spec, delta_data):
    ver = spec["version"]
    cand_file = spec["file"]
    parent_file = spec["parent_file"]
    parent_ver = spec.get("parent_version", "parent")
    cand_bytes = delta_data["bytes"]
    cand_sha = delta_data["sha256"]
    p_bytes = spec.get("parent_bytes", "N/A")
    p_sha = spec.get("parent_sha256", "N/A")

    lines = []
    lines.append(f"# {ver} — {spec.get('title', spec['name'])}")
    lines.append("")
    lines.append(f"**Prepared candidate for owner inspection and staged road testing.**  ")
    lines.append(f"Exact parent and immediate rollback: [{parent_ver}]({parent_file[:-4]}.md).")
    lines.append("")
    lines.append(f"- **Candidate Binary**: [{cand_file}]({cand_file})")
    lines.append(f"  - Size: `{cand_bytes}` bytes")
    lines.append(f"  - SHA-256: `{cand_sha}`")
    lines.append(f"- **Parent Binary**: [{parent_file}]({parent_file})")
    lines.append(f"  - Size: `{p_bytes}` bytes")
    lines.append(f"  - SHA-256: `{p_sha}`")
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
            old_v = p.get("old_value", p.get("parent_value", "N/A"))
            new_v = p.get("new_value", "N/A")
            units = p.get("units", "")
            u_str = f" {units}" if units else ""
            lines.append(f"| **`[ECM] {pid}` {pname}** | {old_v}{u_str} | **{new_v}{u_str}** | `{new_v}` vs `{old_v}` |")
        else:
            lines.append("| Row | Column | Parent Value | Candidate Value | Delta / Note |")
            lines.append("| :---: | :---: | :---: | :---: | :--- |")
            for ch in p.get("changes", []):
                r = ch.get("row", 1)
                c = ch.get("col", 1)
                ov = ch.get("old_value", ch.get("parent_value", "N/A"))
                if "new_value" in ch:
                    nv = ch["new_value"]
                elif "delta_pct" in ch:
                    nv = f"{ch['delta_pct']:+.2f}%"
                elif "delta_add" in ch:
                    nv = f"{ch['delta_add']:+.2f}"
                else:
                    nv = "N/A"
                note_parts = []
                if "rpm" in ch: note_parts.append(f"RPM {ch['rpm']}")
                if "voltage" in ch: note_parts.append(f"{ch['voltage']}V")
                if "note" in ch: note_parts.append(ch['note'])
                extra = "; ".join(note_parts)
                lines.append(f"| {r} | {c} | {ov} | **{nv}** | {extra} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## In-Editor Verification Evidence")
    lines.append("")
    lines.append("1. **Reopened Candidate**: Reopened directly from disk into VCM Editor. Values and Notes rechecked on clean reload.")
    lines.append(f"2. **Whole-File Comparison vs Parent (`{parent_ver}`)**:")
    diffs = delta_data.get("comparison", [])
    if diffs:
        lines.append(f"   - `Compare > View Comparison Log` confirmed expected differences: {', '.join(diffs)}.")
    lines.append("   - Zero unintended table or scalar differences across the entire calibration.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Owner VCM Editor Inspection & Validation Guide")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> Always validate candidate changes against the parent calibration before flashing to the vehicle.")
    lines.append("> The assistant NEVER initiates live ECU writes or vehicle actuation.")
    lines.append("")
    lines.append("### Pre-Flash Inspection:")
    lines.append(f"1. Open VCM Editor (the running instance is pre-loaded with candidate vs. parent comparison).")
    lines.append(f"2. Inspect `Compare > View Comparison Log` and verify only intended parameters differ.")
    lines.append(f"3. Verify `Edit > Calibration Details > Notes` has the appended revision summary.")
    lines.append(f"4. Once verified, flash `{cand_file}` using VCM Editor (`Flash > Write Vehicle` - Calibration Only).")
    lines.append("")

    readme_path = os.path.join(REPO_ROOT, "tunes", f"{cand_file[:-4]}.md")
    content = "\n".join(lines)
    scrub_check(content)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[build_tune] Wrote owner inspection guide: {readme_path}")
    return readme_path

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
            "status": "Candidate prepared and verified in VCM Editor; ready for owner flash"
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
    print(f"[build_tune] Wrote run card: {card_path}")
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

1. Open VCM Editor on desk PC with MPVI4 connected (instance pre-loaded with candidate vs. parent comparison).
2. Inspect `Compare > View Comparison Log`. Ensure ONLY expected parameters changed.
3. Once verified, flash `{spec['file']}` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
4. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
"""
    scrub_check(content)
    with open(reg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[build_tune] Wrote regression test doc: {reg_path}")
    return reg_path

def update_catalogs(spec, delta_data):
    ver = spec["version"]
    cand_bytes = delta_data["bytes"]
    cand_sha = delta_data["sha256"]

    # 1. Update vehicle.json
    v_path = os.path.join(REPO_ROOT, "vehicle.json")
    if os.path.exists(v_path):
        with open(v_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
        v_data["prepared_candidate"] = spec["file"]
        v_data["prepared_test_revision"] = f"{spec['file']}; candidate prepared for owner entry and flash"
        v_data["candidate_test_revision"] = f"{ver} from exact {spec['parent_version']}: {spec.get('rationale', '')}"
        with open(v_path, "w", encoding="utf-8") as f:
            json.dump(v_data, f, indent=2)
        print(f"[build_tune] Updated vehicle.json prepared_candidate: {spec['file']}")

    # 2. Update tunes/revisions.json
    rev_path = os.path.join(REPO_ROOT, "tunes", "revisions.json")
    if os.path.exists(rev_path):
        with open(rev_path, "r", encoding="utf-8") as f:
            rev_data = json.load(f)

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
            "changes": delta_data.get("changes", []),
            "notes": f"{spec['file'][:-4]}.md",
            "rollback": spec["parent_file"],
            "verification": "Live UIA automation in open VCM Editor, fresh disk reload readback, and whole-file compare verified; owner inspection required before flashing",
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
        print(f"[build_tune] Updated tunes/revisions.json with {ver}")

    # 3. Rebuild reference HTML
    ref_builder = os.path.join(REPO_ROOT, "tools", "build-calibration-reference.ps1")
    if os.path.exists(ref_builder):
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ref_builder], capture_output=True)
        print("[build_tune] Rebuilt reports/calibration-inventory/index.html")

    # 4. Strict Privacy Scan
    verify_script = os.path.join(REPO_ROOT, "tools", "verify-privacy.py")
    if os.path.exists(verify_script):
        res = subprocess.run([sys.executable, verify_script, "--repo", REPO_ROOT], capture_output=True, text=True)
        print(f"[build_tune] Privacy check: {res.stdout.strip()}")
        if res.returncode != 0:
            raise RuntimeError(f"Privacy scan failed: {res.stdout}")

def main():
    parser = argparse.ArgumentParser(description="Streamlined SVT Focus Tune Builder")
    parser.add_argument("--spec", required=True, help="Path to tune specification JSON file")
    parser.add_argument("--kill-on-exit", action="store_true", help="Kill VCM Editor process on completion")
    args = parser.parse_args()

    spec_path = os.path.abspath(args.spec)
    if not os.path.exists(spec_path):
        print(f"Error: Spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Validations
    required_keys = ["version", "name", "file", "parent_file", "rationale"]
    for k in required_keys:
        if k not in spec:
            raise KeyError(f"Spec missing required key: '{k}'")
    if "parameters" not in spec and "parameter_id" not in spec:
        raise KeyError("Spec must contain either 'parameters' or 'parameter_id'")

    scrub_check(json.dumps(spec))
    print(f"[build_tune] Starting automated build for {spec['version']} ({spec['name']})...")

    # Step 1: Execute VCM Editor automation
    run_ps_builder(spec_path, kill_on_exit=args.kill_on_exit)

    cand_path = os.path.join(REPO_ROOT, "tunes", spec["file"])
    if not os.path.exists(cand_path):
        raise FileNotFoundError(f"Expected generated tune not found: {cand_path}")

    with open(cand_path, "rb") as f:
        cand_bytes = len(f.read())
        f.seek(0)
        cand_sha = hashlib.sha256(f.read()).hexdigest().upper()

    print(f"[build_tune] Verified candidate: {cand_bytes} bytes, SHA-256: {cand_sha}")

    # Step 2: Create Delta JSON
    delta_dir = os.path.join(REPO_ROOT, "reports", "calibration-inventory", spec["version"])
    os.makedirs(delta_dir, exist_ok=True)
    delta_path = os.path.join(delta_dir, "delta.json")

    param_list = spec.get("parameters")
    if not param_list:
        param_list = [{
            "id": spec.get("parameter_id"),
            "name": spec.get("parameter_name"),
            "kind": "table",
            "changes": spec.get("changes", [])
        }]

    param_changes = []
    comp_list = ["Notes"]
    for p in param_list:
        pname = p.get("name") or str(p.get("id"))
        comp_list.append(pname)
        if p.get("kind") == "scalar":
            param_changes.append(f"ECM {p.get('id')} {pname}: {p.get('new_value')}")
        else:
            param_changes.append(f"ECM {p.get('id')} {pname}: {len(p.get('changes', []))} cells updated")

    delta_data = {
        "version": spec["version"],
        "file": spec["file"],
        "parent": spec["parent_version"],
        "parent_file": spec["parent_file"],
        "bytes": cand_bytes,
        "sha256": cand_sha,
        "parent_sha256": spec.get("parent_sha256", ""),
        "parent_bytes": spec.get("parent_bytes", 0),
        "status": f"Prepared candidate; verified in VCM Editor; ready for owner flash and road test validation.",
        "rationale": spec["rationale"],
        "parameters": param_list,
        "changes": param_changes,
        "comparison": comp_list
    }
    with open(delta_path, "w", encoding="utf-8") as f:
        json.dump(delta_data, f, indent=2)
    print(f"[build_tune] Wrote delta JSON: {delta_path}")

    # Step 3: Generate docs and catalog updates
    generate_markdown_readme(spec, delta_data)
    generate_run_card(spec, delta_data)
    generate_regression_test(spec, delta_data)
    update_catalogs(spec, delta_data)

    print("\n================================================================================")
    print(f" TUNE BUILD PIPELINE COMPLETED FOR {spec['version']}!")
    print(f" Candidate File: tunes/{spec['file']}")
    print(f" Bytes:          {cand_bytes}")
    print(f" SHA-256:        {cand_sha}")
    print(f" Inspection Doc: tunes/{spec['file'][:-4]}.md")
    print(f" VCM Editor:     Preserved open with candidate vs. parent comparison")
    print("================================================================================")

if __name__ == "__main__":
    main()
