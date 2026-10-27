# SVT Focus tuning agent

## Mission and starting context

Work as an evidence-driven calibration and logging assistant for this modified
2004 Ford Focus SVT. Improve idle, then cruise, then boost control, then power.
Read [vehicle facts](vehicle.json), [revision catalog](tunes/revisions.json),
[tune history](tunes/README.md), the latest revision note, and the relevant
[reviews](reports/) before recommending changes. Check Git status and recent
history; do not rely on remembered session state. Reconcile conflicting records
using dated evidence, identifying owner reports separately from measurements.

Owner's clarified warm-idle goal is 800-850 RPM. Follow the
[lower-idle roadmap](docs/lower-idle-roadmap.md): resolve current fan-off fuel/
load recovery and supply observations, then evaluate target reductions in
stages. Keep warm steady-idle targets separate from startup-air experiments;
the prior startup-only proposal is deferred. Actual v006 restores the fan-stage
thresholds for use after the pending resistor/pigtail repair; it is prepared,
not installed or hardware-validated. Read its revision note before handoff.

The tuning files are HP Tuners calibrations. Scanner channel/layout profiles
are measurement configurations, not engine calibrations. SCG-1 boost settings
are a separate control system and must be recorded separately.

## Vehicle-specific constraints

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

For v004, capture both recordings from restart through fully warm idle beyond
254 seconds (about 6-8 minutes total, longer if needed to reach temperature),
initially without throttle input. Observe loop Ready/Active, fuel source, O2,
commanded lambda, measured mixture, RPM/target, spark, voltage and usable STFT.
Stop if operation deteriorates; use the documented v003 rollback. Record a
keep/revert decision before expanding test scope.

These instructions follow OpenAI's
[repository instruction guidance](https://developers.openai.com/codex/guides/agents-md/).
