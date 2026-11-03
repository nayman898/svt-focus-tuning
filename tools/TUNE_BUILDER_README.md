# Reusable VCM Editor Tune Builder Tools

This directory contains reusable tools for automating HP Tuners VCM Editor calibrations for the SVT Focus repository.

---

## 1. Components

1. **`vcm-tune-builder.ps1`**:
   - Parameterized PowerShell UI Automation (UIA) script.
   - Launches VCM Editor, loads parent `.hpt`, executes `File > Save As` (with physical Win32 character typing), navigates to target parameter tables via Parameter Navigator (`[ECM] XXXXX`), updates cells, appends `Calibration Details > Notes`, and saves to disk.
   - Executes fresh reopen verification (`Copy with Axis`) and whole-file VCM Editor `Compare` against parent.
   - Driven entirely by a JSON specification file.

2. **`build_tune.py`**:
   - Python orchestrator.
   - Validates JSON spec, enforces privacy scrub rules (zero VINs or serials), calls `vcm-tune-builder.ps1`, generates delta JSON, runs `build-calibration-reference.ps1`, and updates catalog tracking.

---

## 2. Specification File Format

Create a JSON spec file (e.g., `scratch/v027_spec.json`):

```json
{
  "version": "v027",
  "name": "v027-description",
  "file": "v027-description.hpt",
  "parent_version": "v026",
  "parent_file": "v026-open-loop-tps-threshold.hpt",
  "parent_sha256": "86B10615EB5E032CF4343120A23C6B93DB30FD6CFC558CE863143C32629B1918",
  "parent_bytes": 257885,
  "parameter_id": 32731,
  "parameter_name": "Open Loop Fuel TPS Thresh vs. RPM",
  "rationale": "Description of why this calibration change is being made.",
  "changes": [
    {
      "row": 3,
      "col": 1,
      "old_value": "350.00",
      "new_value": "400.00"
    }
  ],
  "notes_append": "=== V027 (YYYY-MM-DD) ===\r\nSummary of change...",
  "output_result_json": "scratch/v027_verify_result.json"
}
```

---

## 3. How to Run

From the repository root:

```powershell
python tools/build_tune.py --spec scratch/v027_spec.json
```

Or invoke the PowerShell builder directly:

```powershell
powershell -STA -NoProfile -ExecutionPolicy Bypass -File tools/vcm-tune-builder.ps1 -SpecPath "scratch/v027_spec.json"
```

---

## 4. Strict Safety Guardrails
- **Zero ECU Actions**: The tool NEVER touches `Flash > Write Vehicle`, readback, DTC clear, or adaptation reset. The owner performs all flashes.
- **Privacy Protection**: Zero 17-character VINs or 10-digit MPVI serials allowed.
- **Port Checking**: Confirms `COM7` is completely free before opening VCM Editor.
