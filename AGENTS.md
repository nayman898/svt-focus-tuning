# SVT Focus tuning agent

## Current state and sources

Read [README.md](README.md), [vehicle.json](vehicle.json), and the
[revision catalog](tunes/revisions.json) for current state. Keep dated session
narratives in reports rather than prepending them to this instruction file.
Historical agent notes are preserved in [SESSION_HISTORY.md](SESSION_HISTORY.md);
they are not current instructions or evidence of a currently active recording.

As of 2026-11-03, v025 is owner-confirmed tested and provisionally retained
for covered stationary conditions with the new upstream O2 sensor (0 mid-warmup FMEM events,
centered 952 RPM warm idle). v026 is prepared and verified from v025, but not flashed or tested.
Its immediate rollback is v025. Read the [v025 review](reports/2026-11-03-v025-test-review.md) and
[v026 test card](docs/v026-regression-test.md) before further tuning work.
File verification does not establish that a proposed mechanism or fix is proven.

Prioritize stability and drivability; further idle-target reductions remain
deferred. Water/meth stays OFF and the SCG RPM wire remains disconnected unless
the owner explicitly changes that state. Repaired fan thresholds are low
195/190 F and high 225/215 F; earlier bypass logs represent different hardware.
Treat installed state as owner-reported, not an ECU readback. Do not infer
current engine, recorder, Editor, or roadworthiness state from archived notes.

## Iterative logging: fast path

Use the [datalog pathway](docs/datalog-workflow.md) and
[channel coverage register](profiles/channel-coverage.md) for every new run.
These are standing operating instructions, not a reason to delay capture.

- If the owner says "log now", prioritize preserving/starting acquisition.
  Inspect actual recording state first. Never stop an existing VCM recording
  just to create a paired folder. Start the missing recorder and document the
  separate clocks. Do profile research after the event is captured.
- Read current state above, the latest review and the new run card first.
  Use the evidence index to select comparison sessions. Do not reread or
  reprocess the entire archive on each turn. Revisit older evidence when a
  hypothesis, parser correction or hardware change makes it relevant.
- Ask only about changes since the last confirmed run. Carry forward explicit
  owner confirmations, including meth OFF, disconnected RPM wire and installed
  tune; label them owner-reported. A restart does not establish a new flash.
  Unknown fuel/accessory details remain unknown, not silently carried forward.
- Batch Git status and catalog hash/size verification once per analysis or
  candidate-preparation pass. Recheck changed files before use. Do not repeat
  Editor discovery for unchanged parameters with preserved verification.
- Use proven helpers in the logger's ignored `.local/` folder, but inspect their
  guards, expected profile and session arguments before use. Discover fresh
  process/window handles. Never replay a hardcoded handle or old session path.
  When a method times out, use the documented native-window fallback rather
  than repeating the same blocking UI Automation search.
- Identify the recording by the dashboard/session manifest and exact source
  folder, not just the newest modification time. Verify both recorders and
  increasing samples before saying "both recording". Report partial capture
  promptly. Do not promise unattended stop/monitoring unless it is running.
- Preserve originals, the actual saved channel configuration, export settings,
  manifest and owner event notes together. Use the [run card](docs/datalog-run-card.json).
  A candidate profile on disk is not proof it was loaded. Never overwrite a
  completed session or silently replace an original export with a new export.
- Analyze new/changed inputs first. Record input SHA-256, analyzer version/hash,
  selected columns, alignment method, window definitions and output paths in
  the private session analysis record. Reuse prior outputs only when those
  dependencies match. No incremental cache is implemented yet: existing
  `.local/build-roadmap-evidence.py` is a full inventory, not a cached runner.
  Promote a repeated analysis into a parameterized helper when warranted;
  do not keep cloning scripts with hidden session-specific assumptions.
- Inventory all available channels and blank spans before selecting diagnostic
  plots. Keep native HPL/SQLite/raw bytes and full-length exports, including
  startup, transient and recovery periods. Do not crop the only preserved copy.
  Expand coverage through the register; retain reasons for deferred channels.
- Keep core requests fixed during a comparison series. Trial a small group of
  additional channels in a separate stationary capture, audit the saved data,
  and retain additions only if core coverage/timing remains usable. Do not
  assume every exported row is an independent ECU sample or a constant value
  means a dead sensor. Blank, zero, unavailable and invalid are different states.
- Each review must return: capture quality, matched comparison, event chronology,
  competing explanations, decision (retain/change/insufficient evidence), and
  one next run card. Include minima, dip duration/recovery and source transitions,
  not averages alone. Update the evidence index and coverage register with new
  facts; keep uncertain hypotheses separate from verified behavior.
- Make each iteration faster by reusing verified facts and analysis, not by
  shortening the observation window needed to capture the stated event. Never
  claim a fan cycle or post-drive validation if it did not occur.

## Vehicle-specific constraints

- Owner confirms water/meth completely disengaged and directs that all future
  testing assume OFF unless explicitly changed. Activation when enabled is
  owner-reported7psi; that does not establish the tune's boost dependency or
  authorize boost testing. Do not repeatedly ask its state without new evidence.
- Earlier owner feedback included no CEL; later near-stall events and dated test results supersede that early description. No CEL is not a DTC scan. Use current state and dated reviews for installation evidence.
- This is a previous-owner turbo calibration, not an established stock tune.
  Exact injector characterization, MAF identification, boost limits and
  water/meth dependency remain incomplete; consult the vehicle record.
- Respect the 1:1 referenced return fuel system. A nominal injector flow or
  reported 43 psi engine-off pressure is insufficient to derive injector data.
- Keep the temporary fan-resistor-bypass pathway visible in every descendant
  revision until repaired and explicitly retired. v003 introduced 195/190 F
  high-speed thresholds; restoration after repair is 225/215 F, preserving
  unrelated later changes. Calibration does not establish wiring integrity.
- v004 is a stationary warm-idle closed-loop-entry experiment. Read its note
  for the 1,500-2,000 rpm interpolation effect, retained 254-second gates,
  LTFT-disabled state, and rollback. Do not generalize idle results to boost.
- Investigate IMRC after idle/fueling stabilization, before final power work.

## Evidence before calibration

1. Establish the parent actually tested and distinguish prepared, saved,
   compared, owner-reported flashed, log-supported tested, and accepted states.
   A file on disk or open in Editor does not establish the ECU's current tune.
2. Identify one hypothesis, the supporting data, exact proposed parameter IDs,
   units, axes/cells and expected behavior before editing. Check controller-
   specific Editor descriptions and official HP Tuners references when needed.
   A plausible threshold explanation remains a hypothesis until tested.
3. Prefer one causal change per revision. Do not simultaneously alter MAF,
   injector data, closed-loop gates, ignition and boost to chase one symptom.
   Evaluate interpolated regions and inherited changes as well as edited cells.
4. Preserve corrective idle spark behavior unless evidence supports changing it.
   Review voltage, accessory/fan loads, air control, fueling and spark sources
   together. Do not flatten timing merely to make the trace appear steady.
5. Do not invent tune values, sensor scaling, channel IDs, knock limits or
   AFR/boost targets. Obtain missing information when it blocks the next stage;
   continue independent review and documentation without unnecessary approval.

## Files and verification

- Preserve numbered tune binaries and original reads. Assign the next revision
  for calibration edits; never silently overwrite a published numbered tune.
- Check every cataloged file's SHA-256 and byte length before relying on it.
  Stop and reconcile any mismatch. Hash equality verifies identity, not internal
  calibration correctness or successful flashing.
- Use VCM Editor for HPT edits/comparisons; do not hex-edit proprietary files or
  infer calibration differences from binary byte differences.
- Reopen the saved candidate and compare against its explicit parent. Verify
  every intended cell/scalar, all unexpected differences, and embedded Notes.
  An unverified comparison must remain labeled unverified.
- Record the filename, parent, exact changes, retained settings, verification,
  SHA-256, size, scope, rollback and test outcome in the revision catalog and
  revision note. Update vehicle state and the history when evidence changes.
- Treat desktop automation as state-dependent: discover current process/window
  handles and controls, inspect before acting, and verify afterward. Old private
  scripts contain session-specific handles; do not replay them blindly.
- Keep VINs, license/interface IDs, original reads and raw logs in the existing
  ignored private locations. Numbered tune binaries are intentionally tracked
  locally. No remote publication is authorized by ordinary tuning work.

## Logging and analysis

- Use the documented working idle/cruise channels and layout in
  [scanner guidance](profiles/README.md). The generic fuel-diagnostics template
  is unvalidated. A configured channel is not proof of usable recorded data.
- Owner reports some channels populate intermittently or late. Evaluate actual
  coverage within each session; a blank snapshot alone does not establish lack
  of controller support. Historical absolute TPS was about 182-184 counts while
  relative TPS was about 0-1; never substitute one for the other. v005 tests the
  absolute-TPS comparator hypothesis with 200-count low-RPM thresholds and is
  stationary-idle-only, including its changed 1,500-2,000 RPM interpolation.
- Preserve native HPL/LOG plus CSV in a new revision/session directory. Record
  actual flashed filename, fuel, water/meth state, temperatures, accessory
  changes, SCG settings and owner observations. Never merge sessions silently.
- Derive clock offset and assess drift for each VCM/LogWorks session. Label
  metadata-only alignment provisional; do not reuse earlier offsets or derive
  pointwise fuel corrections from unverified synchronization.
- Separate commanded lambda, narrowband O2 voltage and SCG measured mixture.
  Do not treat narrowband voltage as a wideband AFR measurement. LogWorks RPM
  and WGDC previously read zero; verify usability rather than assuming validity.
- Compare temperature/load-matched windows, elapsed time since start, sample
  counts and event ranges as well as averages. CSV rows can be interpolated or
  asynchronously sampled; they do not prove exact event causality.

## Flash-readiness handoff

Give a direct decision with the exact candidate and tested scope, what was
verified now versus inherited evidence, unresolved conditions and rollback.
Distinguish file readiness, write conditions, and engine-operation validation.
Check stable write power, correct controller/file, and Editor prompts; report
unobserved conditions as unverified rather than claiming a guaranteed safe flash.
Preparing or reviewing a tune does not authorize initiating an ECU write.
The owner currently performs writes. If explicitly asked to write, establish
the required connected vehicle state before any write action.

Historical v004 procedures and rollback remain in its revision note. For current testing, use the datalog pathway and actual installed parent; do not apply an old revision-specific test or rollback automatically.

These instructions follow OpenAI's
[repository instruction guidance](https://developers.openai.com/codex/guides/agents-md/).


## Model delegation & UIA workflow

1. **Role separation**:
   - The primary agent (Argon / Pro model) is strictly reserved for datalog analysis, calibration engineering/math, hypothesis validation, and tune decisions.
   - Autonomous subagents (Model: "flash") handle all HP Tuners VCM Editor UI Automation (UIA), bulk table extractions, log copying/hashing, and mechanical catalog/inventory/reference builds.

### VCM Editor handoff for Gemini Flash

Use Windows UI Automation (UIA) to inspect the application and targeted Win32
messages for controls where UIA or ordinary keyboard/clipboard input is
unreliable. These methods come from prior Editor sessions; documenting them
does not establish the current desktop state or constitute a new Editor test.

#### Discover and confirm the current state

- Discover the running VCM Editor process, its current windows, and the target
  controls before acting. Never reuse process IDs, window handles, coordinates,
  or session paths from an earlier run without checking them again.
- Confirm the open filename, intended parent, main-versus-comparison context,
  and any modal dialog before entering data. Identify the intended parameter
  by its ECM ID, name, units, and table axes rather than its screen position.
- Inspect existing helpers before using them. Check their expected file,
  profile, control handles, and assumptions. A helper's successful return is
  not proof that Editor accepted the intended action; inspect the result.
- When UIA discovery times out, rediscover the current native windows and use
  the documented Win32 fallback. Do not repeatedly issue the same blocking
  search or blindly repeat an edit whose outcome is unknown.

#### Open, Save As, and Open Compare File dialogs

- The observed native file dialogs use class `#32770`. Filename Edit controls
  have been observed with IDs `1148` or `1001`; locate and confirm the actual
  control in the active dialog rather than assuming either ID is universal.
- `Ctrl+V` into the filename field proved unreliable in these dialogs. Use
  character-by-character input through Win32 `WM_CHAR` or the existing
  `TypeChars` helper instead.
- Focus the filename Edit control, select its existing contents with `Ctrl+A`,
  then type the complete intended path. Confirm the field contains that path
  before submitting with `WM_KEYDOWN` / `VK_RETURN` or the dialog's `IDOK`
  action. Do not send both submission methods blindly.
- After submission, confirm the dialog closed and Editor opened or saved the
  expected file. Inspect overwrite or other prompts explicitly; do not treat
  a filename-entry success as a completed save.

#### Calibration tables and context menus

- For `C1FlexGrid` tables, invoke the context menu through `WM_CONTEXTMENU`
  instead of a physical right-click, which can disturb the selected cells.
  Confirm the intended selection before applying a table operation.
- Distinguish table body values from axis/header cells. Preserve axes unless
  the approved change explicitly includes them; record the affected cells,
  units, original values, and intended replacements.
- Capture full-precision clipboard values when available, and label display-
  precision captures as such. Rounded screen values alone do not prove exact
  equality. Confirm main-versus-comparison mode before interpreting a capture.

#### PowerShell helper output

- Keep incidental method return values and diagnostics out of the success
  pipeline when a function returns captured table data or structured results.
  Suppress unused returns with `[void]`, `$null = ...`, or `Out-Null` as
  appropriate; use a separate diagnostic stream for progress messages.
- Check the returned data's shape and expected cell count before consuming it.
  Extra pipeline objects must not silently become table rows or values.

#### Save and verify each candidate

1. Verify the exact parent file's cataloged SHA-256 and byte length. Use VCM
   Editor for calibration edits; never hex-edit HPT binaries or infer parameter
   changes from raw binary differences.
2. Apply only the specified changes and append their rationale to Notes while
   retaining the full parent Notes history. Save As a new numbered revision;
   preserve earlier revisions and original reads.
3. Reopen the saved candidate. Recheck every intended scalar or table body
   value, the relevant axes, and the retained Notes prefix. Do not rely solely
   on the pre-save UI state.
4. Open the exact parent as the comparison file and review the whole-file
   comparison. Reconcile every unexpected difference, including Notes, before
   calling the candidate verified. If comparison is incomplete, say so.
5. Record the saved filename, parent, exact changes, verification evidence,
   SHA-256, byte length, rollback, and test scope in the revision note/catalog.
   Keep prepared, installed, tested, and accepted status distinct.

File preparation, comparison, and documentation do not authorize an ECU flash,
engine operation, code clearing, or adaptation reset. The owner currently
performs writes. Follow the flash-readiness handoff above if a write is
explicitly requested; do not infer authorization from a prepared candidate.
