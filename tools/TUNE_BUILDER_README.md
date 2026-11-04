# Streamlined VCM Editor Tune Builder Tools

This directory contains reusable tools for automating HP Tuners VCM Editor calibrations for the SVT Focus repository.

---

## 1. Components

1. **`build_tune.py`** (Primary Entrypoint):
   - High-level Python orchestrator.
   - Validates the tune JSON specification and runs strict privacy checks (zero VINs or serials).
   - Calls `vcm-tune-builder.ps1` to execute the live calibration edits.
   - Automatically generates the candidate markdown guide (`tunes/<candidate>.md`), regression test documentation (`docs/<ver>-regression-test.md`), and run card (`docs/<ver>-run-card.json`).
   - Automatically writes the delta JSON (`reports/calibration-inventory/<ver>/delta.json`).
   - Updates `tunes/revisions.json` and `vehicle.json`.
   - Rebuilds `reports/calibration-inventory/index.html` and `revision-reference.json`.
   - Executes `tools/verify-privacy.py` to ensure 100% compliance.

2. **`vcm-tune-builder.ps1`**:
   - Parameterized PowerShell UI Automation (UIA) engine.
   - **Non-Destructive Process Handling**: Automatically discovers and attaches to any running VCM Editor instance. **Never terminates or restarts VCM Editor**, ensuring hardware/license authorization is preserved when the owner is away from the vehicle/MPVI4.
   - Connects to the interactive user desktop (`WinSta0\default`) via dedicated STA thread helper.
   - Handles `#32770` file dialogs (`File > Save As`, `File > Open`, `Compare > Open Compare File`) with reliable Win32 `WM_CHAR` character-by-character typing.
   - Updates `C1FlexGrid` tables (with full clipboard read/parse/paste/readback verification) and scalar parameters (via Parameter Navigator preview pane).
   - Appends revision history to `Calibration Details > Notes` (`Ctrl+D`).
   - Executes fresh reload verification and whole-file compare against parent, checking difference nodes in the Comparison Log.
   - Leaves VCM Editor open with candidate vs. parent comparison ready for pre-flash inspection.

---

## 2. Specification File Format

Create a JSON spec file (e.g., `scratch/v034_spec.json`):

```json
{
  "version": "v034",
  "name": "v034-sample-refinement",
  "file": "v034-sample-refinement.hpt",
  "parent_version": "v033",
  "parent_file": "v033-loud-crisp-pops.hpt",
  "parent_sha256": "41B8D374770A0F15231EF0D3C8E5DF26C132F3A198B439CEC3E479E821397C23",
  "parent_bytes": 262381,
  "title": "Sample Title for Tune",
  "rationale": "Detailed explanation derived from telemetry...",
  "parameters": [
    {
      "id": 44496,
      "name": "DFCO Closed Throttle Delay",
      "kind": "scalar",
      "old_value": "1.40",
      "new_value": "1.45",
      "units": "s"
    },
    {
      "id": 44605,
      "name": "Spark Decel vs. RPM vs. ECT",
      "kind": "table",
      "changes": [
        { "row": 4, "col": 4, "new_value": "-9.00", "note": "3k decel retard" },
        { "row": 5, "col": 4, "new_value": "-9.00", "note": "3k decel retard" }
      ]
    }
  ],
  "notes_append": "=== V034 (YYYY-MM-DD) ===\r\nSummary of changes..."
}
```

---

## 3. How to Run

From the repository root:

```powershell
python tools/build_tune.py --spec scratch/v034_spec.json
```

Or invoke the PowerShell builder directly:

```powershell
powershell -STA -NoProfile -ExecutionPolicy Bypass -File tools/vcm-tune-builder.ps1 -SpecPath "scratch/v034_spec.json"
```

---

## 4. Strict Safety Guardrails
- **Zero ECU Actions**: The tool NEVER touches `Flash > Write Vehicle`, readback, DTC clear, or adaptation reset. The owner performs all flashes.
- **Privacy Protection**: Zero 17-character VINs or 10-digit MPVI serials allowed.
- **Process Preservation**: VCM Editor is kept alive and running; never terminated without explicit `-KillOnExit`.
