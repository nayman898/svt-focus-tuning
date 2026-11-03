# Calibration reference

Latest complete offline review: [v021 calibration audit, November 2, 2026](../reports/2026-11-02-v021-complete-calibration-audit.md),
with a [342-entry disposition ledger](../reports/2026-11-02-v021-parameter-review.csv)
and [identity/structure checks](../reports/2026-11-02-v021-audit-checks.json).
All exposed values reviewed from repo evidence; no VCM or tune edits. Notable
follow-ups include FRP diagnostic suppression, the 64 F cranking-fuel step,
fuel/MAF shape and warmup air/spark transitions. This audit supersedes older
blanket-retain dispositions for those findings. Latest v023 trial stalled and
was not adopted; exact v021 restoration remains recommended, not confirmed.

Open the [revision comparison page](../reports/calibration-inventory/index.html).
It includes all25 cataloged revisions, search by name/path/ID/help, changed-only
filtering, highlighted grid differences, and selected-comparison CSV export.
Latest reviewed recording isv023, not an ECUreadback. v020 was tested/rejected.
[v021](../tunes/v021-fuel-pressure-feedback.md) remains the baseline: pressure
conversion operates plausibly, warmdips remain. [v022](../tunes/v022-idle-spark-gain-0p75.md)
was tested and not adopted after newoscillation; returnv021recommended, notconfirmed.
Its onlychange was47996gain1->0.75+Notes.
[v023](../tunes/v023-idle-spark-10deg.md) was tested and not adopted after a stall:
44579/44578 nominalidlespark12->10 inallfivecells each, withgain1.000retained.
Its saved18-channel capture populated desiredRPM/TPS; the v021/v022 captures
did not. Future capture coverage still requires per-run readiness checks.

Prepared successor: [v024 fuel cleanup and pressure diagnostics](../tunes/v024-fuel-cleanup-diagnostics.md),
saved/reopened/compared from exact v021, not flashed or tested. Only two low-TPS
fuel cells at2500RPM and three FRP DTC reporting modes changed, plus Notes.
See the [staged regression card](v024-regression-test.md). Full-precision44511
body evidence is now normalized across v016–v024 for accurate comparisons;
the immutable original v017 capture is preserved.

Complete exposed parameter comparisons are available forv016–v024 through the
v017 capture and verified whole-file comparisons/deltas. Earlier revisions show
cataloged history and changes, with unknown full parameter values explicitly
marked. Do not claim those revisions have complete snapshots. MAF grids use
the saved full-precision clipboard evidence in common Editorlb/min display units;
this does not resolve physical scaling. Human display rounds that curve to seven
significant digits; CSV and JSON retain source precision. Notes differences live
in revision metadata, outside the342-parameter comparison.

Rebuild with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
tools/build-calibration-reference.ps1` from the repository root. The builder
checks all numbered tune hashes/sizes and MAF delta consistency before writing
the standaloneHTML and machine-readableJSON. No server/network is required.
For a new revision, add its verified change evidence and extend the builder's
snapshot reconstruction; catalog presence alone must not imply full coverage.
The original v017 snapshot remains immutable.

Start with the [searchable v017 viewer](../reports/calibration-inventory/v017/index.html)
or [parameter index](../reports/calibration-inventory/v017/index.csv). Search by
parameter name, Editor path or ECM ID. Every entry links to its captured record;
tables include all displayed cells and axes in their original grid positions.

## Baseline

Exact saved file: `tunes/v017-o2-readiness-600.hpt`,241517bytes,
SHA-256 `9597BAB2DB9DEB063298C7814F8B9930C530DBDB3FE114D80F8EE44B6463E7CE`.
Captured in Editor Advanced view with comparison closed. This is not an ECU
readback and does not establish which file is currently installed.

-342/342 exposed parameter leaves captured across Engine, Engine Diagnostics,
 Transmission, Fuel System, System and Speedometer.
-96 tables and246 scalar/switch entries;4692 cells including axes/headers.
-All342 parameter IDs identified; all96 table grids pass rectangular address
 coverage checks, and every scalar/switch entry has a displayed value.
-Master DTC List includes163 DTC rows plus its header; its ID-column addresses
 were normalized to Column0 without changing displayed values. Generic Editor
 DTC descriptions are preserved verbatim, not independently validated against
 the vehicle's diagnostic manual. These are configured reporting modes, not
 codes read from the car.
-94 matching descriptions were not captured. Table-axis units are not universally
 exposed by UI Automation. These metadata limits are explicit, not guessed.

Values are strings at Editor display precision. A displayed0.00 is not proof
of an exact binary zero. Raw controls can contain stale tooltip/help text and
display checkboxes; use the top-level verified description and normalized index,
not arbitrary raw help or A/B toggle states as calibration facts.

The saved-file comparison establishes that v016 differs only at ECM12115:
520F rather than600F, plus Notes. Do not treat the v017 inventory as a fresh
capture of v016 or of an unknown later revision. The unsuccessful v017 trial
does not become accepted simply because it is the inventory baseline.

## Files

-[Index and scope](../reports/calibration-inventory/v017/README.md)
-[CSV parameter index](../reports/calibration-inventory/v017/index.csv)
-[CSV table cells](../reports/calibration-inventory/v017/table-cells.csv)
-[Combined machine-readable inventory](../reports/calibration-inventory/v017/inventory.json)
-[Coverage manifest](../reports/calibration-inventory/v017/manifest.json)

## Iterative workflow

1. Verify the saved-file hash against the inventory before quoting values.
2. Look up the ID/path in the CSV, then read its individual numbered JSON. Avoid
   dumping the whole combined inventory for a single question.
3. A parameter being exposed does not mean it should change. Attach a concrete
   symptom, hardware fact, proposed change and acceptance/rollback criterion.
4. Keep this baseline immutable. For a later revision, capture changed entries
   and a verified whole-file Editor comparison; mark unchanged values as inherited
   evidence. If the difference scope is unknown, recapture the exposed inventory.
5. Preserve source hash, main-versus-comparison mode and display precision. Recheck
   table values after saving/reopening any candidate; never silently overwrite
   a numbered tune or use the inventory to modify binary offsets.

Capture helpers are retained locally: `.local/catalog-nav.ps1`,
`.local/capture-nav-batch.ps1`, `.local/build-inventory-index.ps1` and
`.local/build-inventory-viewer.ps1`. They depend on this machine's Editor/UI helper;
they are not a portable HPT decoder. Master DTC List needed separate inline-grid
capture, and three IDs/descriptions required a targeted hover verification.
No tune file or ECU setting was changed by the inventory pass.
