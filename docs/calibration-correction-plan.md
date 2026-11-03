# Calibration correction and tuning plan

Implementation update: [v018](../tunes/v018-dfco-recovery-diagnostics.md) is prepared from exact v016 with DFCO exit 1,000 RPM and P0132 MIL reporting, plus Notes. It is not flashed or tested. Other conditional recommendations remain unimplemented.

Based on the complete exposed [v017 inventory](../reports/calibration-inventory/v017/README.md),
the hardware record and saved runs through v017. This is a plan, not a new flashed
calibration. All342 exposed entries were screened;96 table grids were checked
for shape, ranges, constant/duplicate regions and relevant discontinuities.
Focused findings below are not a certification of every operating point.
The [review ledger](../reports/2026-10-30-parameter-review.csv) records each
entry's disposition so retained settings are not confused with validated settings.

## Decisions now

1. Use exactv016 as the working950RPM baseline; v017's600F O2-entry experiment
   failed its stated goal. Rollback remains recommended, not owner-confirmed.
2. Restore useful upstream diagnostic reporting in a separate diagnostic revision:
   Master DTC List P0132 is currently **No Error Reported**. Proposed mode is
   **MIL Light** for the physically present B1S1 sensor. Preserve all other DTC
   rows initially. This improves visibility; it is not an engine-running repair.
3. Keep warm idle oscillation and persistent stopped-idle hang as separate
   workstreams. Neither is solved by changing the O2 readiness threshold.
4. Do not produce an omnibus correction tune. Every behavior-changing revision
   must have one mechanism, an expected result and a rejection condition.

## Findings ranked by relevance

### A. Diagnostic blind spot — correction justified

[Master DTC List,ECM50](../reports/calibration-inventory/v017/256.json) suppresses
P0132 entirely. P0133 slow response, P0135 heater, P1130/P1131/P1132 feedback,
P0320 engine-speed input and P1504/P1506/P1507 IAC codes still requestMIL.
Restoring P0132 reporting is justified while investigating this actual sensor.
It will not detect every false-lean or slow-readiness problem.

The whole list contains55 NoErrorReported,43 NoMILLight and65MILLight entries.
Those counts are not55mistakes: many codes concern nonexistent banks/cylinders
or unsupported equipment. Do not globally enable or disable them. FRP reporting
and transfer restoration must accompany installation of the real pressure sensor.
NoMILLight differs from NoErrorReported; inspect stored/pending codes rather than
equating lamp-off with fault-free operation.

### B. Warm idle control — highest behavior priority

Keep950RPM, gain1.000 and sparkfloor−6 for the diagnostic baseline. The
[warm-event research](../reports/2026-10-30-warm-idle-control-research.md) shows
overspeed/air reduction followed by underspeed, then air/spark rescue. One large
dip occurs with essentially unchanged reportedSTFT. A fuel-gain explanation is
therefore incomplete, and reactive STIT does not exclude control-loop instability.

Two concrete calibration paths need resolution before choosing the next number:

- [ECM44603 low-load spark maximum](../reports/calibration-inventory/v017/205.json):
  displayed breakpoints0/480/600/720/860/1000/65535 with limits60/10/8/4/2/0/0deg.
  This is a time-dependent cap worth checking against extended low-load behavior.
  It is not proof that idle feedback is capped atzero: recorded rescue advance
  exceeds that, and the internal timer/eligibility are not logged. Verify axis
  units and active strategy path before any floor/shape change. Do not flatten
  to60 or add global timing to defeat an unidentified limiter.
- [ECM44243 P/N runtime air multiplier](../reports/calibration-inventory/v017/021.json)
  and identicalDrive44240: at200F the multiplier falls1.30 at165s to1.00 at200s.
  At188F the interpolated base-air contribution falls roughly21% over that interval.
  This can interact with adaptation but cannot explain every later dip after
  the last breakpoint. If the onset follows this transition, a local smoothing
  trial should preserve the final warm value and cold columns; do not make
  the entire warm table1.00 or add a broad percentage to base air.

These are ahead of another spark-gain reduction. The more direct missing controls
are idle-air PI/overspeed response, integration limits/filtering and IAC air-demand
components. Current Editor searches did not expose verified equivalents; obtain
UJAHAS3 definitions from HP Tuners rather than substituting fuel-pump gains.

Next useful action is a definition/control-path audit plus a targeted profile
containing only available needed signals (requested air/corrections, actual cam
angle/error, purge command). If absent, use a verified service IAC-response test
to distinguish command-to-flow mismatch from an unstable controller. No repeat
of the same20-channel idle log is requested without an intervention or new signal.

### C. Hanging idle — likely retained-air path, not DFCO delay

[ECM32984 dashpot decay](../reports/calibration-inventory/v017/026.json) displays
0.00 at airflow0/0.2/0.4/0.6, then0.06/0.08/0.10 at0.8/1.0/3.0. Matching Editor
help says smaller values mean slower decay. This is a strong audit target given
the owner's1100RPM hold until a pedal blip and the stopped v014event with~52%IAC.

Before editing, display these low cells at greater precision:0.00 may be rounded.
Also verify the output units and whether the rate applies in the observed state.
Then define a **small low-airflow decay-rate increase**, retaining the zero-airflow
endpoint and high-airflow values, if the actual low cells/state support it.
No numerical replacement is selected from two-decimal zeros. The test must show
less hanging without worse undershoot; a slower decay change would go the wrong
direction according to the verified description.

Retain minimum/pre-position/maxclip tables initially. Do not zero them together.
Check stoppedVSS, raw/relativeTPS, closed-throttle state and IAC before/after the
releasing blip. TransInferNeutral45824 isEnabled and its help references IAC-state
inference on clutch-switch-only applications. This makes state inference relevant,
not proof that forcing neutral is appropriate. Clutch behavior is owner-uncertain.

### D. DFCO exit below idle — a reasonable separate trial

[ECM2291](../reports/calibration-inventory/v017/165.json) exits fuel cut below750RPM;
entry2290 is1200RPM and speed entry/exit are35/12mph. A concrete optional trial is
**750->1000RPM exit only**, retaining1200entry and all speed/delay/ramp settings.
This gives a nominal50RPM margin above the950target and200RPM entry/exit separation.
It is a chosen test value, not an established optimum.

Purpose: resume fuel earlier during an activeDFCO deceleration that approaches
idle while still above the speed exit threshold. It will not fix a stationary
hang where speed is already below12mph, and it cannot be evaluated in stationary
idle. Defer its moving test until recovery is sufficiently reliable for that
test; don't waste a warm-idle session evaluating a gate that cannot activate.

### E. Fuel model — characterize before correcting trim

The return-conversion vacuum multiplier is already0; retain it. FRP transfer
is flat40psi and pressure multipliers are unity, so current pressure PIDs do not
measure real pressure. Keep the43psi owner-set regulator while identifying actual
injectors. Slopes63/60.12lb/hr, breakpoint0.00003360lb, minPW0.5ms and voltage
offsets are not validated by the label“60lb Siemens.” Exact part/characterization
and pressure basis are necessary before scaling anything.

Do not change injector reference40->43 alone or tune MAF and injector slopes
simultaneously. The low-pulse characterization is directly relevant to good loaded
operation but poor idle; that pattern is a reason to check it, not proof of error.

[Fuel Base44511](../reports/calibration-inventory/v017/132.json) has low-TPS cells
lambda1.07/1.14 at2500RPM and neighboring richer regions; [OLTPS32731](../reports/calibration-inventory/v017/129.json)
is200 at0/1500 and0 at2000+. Establish active table, TPS convention and actual
command before smoothing or changing those values. They deserve an early
drivability review once metering is validated, not arbitrary richer/leaner targets.

LTFT isDisabled; leave it disabled while establishing the base model. Do not
enable it to conceal systematic errors. The inactive learning table has repeated
axes and signed/index-like values: do not interpret it as percentage corrections
or activate it without definition/reference verification.

Cold-base1.03 and final enrichment-decay0.03 nominally cancel under the documented
relationship; zeroing the latter alone is not a justified removal of excess fuel.
Retain these and the loss/transient tables until final commanded fuel is understood.

### F. Spark/load/VCT model — important, not a blind smoothing task

Borderline44583 has a steep load0.70->0.80 transition: at1000RPM6.5->−7deg,
at2450RPM21->6.73deg. This may be intentional boost/load protection. There are
also non-monotonic MBT/load regions. Smoothing upward could remove protection;
neither MBT nor the main spark table is a free idle correction knob.

IAT correction base−20 at100F is multiplied by another table, not automatically
20deg of final retard. At load0.8 the multiplier is0 at2600/3250RPM; check actual
load and temperature corrections before accepting boost operation with methOFF.
Preserve thermal protections, knock reporting and current timing until that
review. No safe boost spark or lambda target is derived from this inventory.

VCT isEnabled/IntakeOnly with nonzero low-speed targets. Verify actual cam
hardware and requested/actual tracking; don't zero the VCT table. MAF delay/
idle filtering0.11 and disabled anticipation need the actual MAF location and
air-path geometry before changing their delay assumptions. Intake-volume5.40
and inertia0.0150 likewise cannot be declared wrong without model conventions
and hardware (including flywheel) information.

### G. Hardware/state configuration and apparent contradictions

- Neutral-limiter load min1.99/max0.00 is an apparent exclusion under documented
 logic. It concerns rev-limiter eligibility, not target idle. Preserve until
 intended design is known; swapping values blindly changes mode selection.
- Power-steering pressure-switch configuration isEnabled despite owner-described
 electric steering. An electrohydraulic conversion may still use a legitimate
 switch. Confirm the physical setup and live input before changing it.
- A/C masterEnabled/pressure-switchDisabled may select a different input scheme;
 it is not proof that compressor protection is absent. Verify installed plumbing/
 control input before correction. No A/C enable/disable edit is proposed.
- TransAutomaticDisabled and ETCNotFitted are consistent with the known manual,
 cable-throttle setup. Retain them. Do not forceNeutral to mask a hang.
- Gear constants/finalDrive1.00 look unusual, but N/V13.98 equals839rev/mile÷60.
 This shows a normalized calculation relationship; the SVT uses a twin-layshaft
 transaxle. Validate actual RPM/speed/gear and tire size before replacing constants
 with brochure ratios. FinalDrive1.00 alone is not proof of a gearing error.
- Low fan195/190 and high225/215 are the post-resistor-repair baseline; preserve
 stage logic while investigating load pickup. Pump gains cannot regulate the
 bypassed fixed-voltage relay pump. Keep existing shutoff hardware intact.
- 7400RPM limits are not validated for unknown cams/valves/rotating hardware.
 Do not raise them or treat forged internals as proof of an acceptable limit.

## Staged execution and exit criteria

| Stage | Work/change | Discriminating check | Stop/rollback condition |
| --- | --- | --- | --- |
|0: baseline|Owner-confirmed exactv016, retain950RPM; preservev017 as failed experiment|File/hash, installed revision and sensor identified|Any unknown manual edit: save and compare before proceeding|
|1: visibility|Separate proposed revision restoring P0132 toMIL; no running-map changes|Verify saved DTC row and full-file comparison; read actual codes|Unexpected changes or unsupported diagnostic behavior|
|2A: warm control|Resolve idle-air control definitions and active low-load spark cap; select one verified intervention|Target-relative RPM error, IAC/STIT and recovery, with a new control/signal rather than unchanged baseline|No new mechanism tested; stop repeating ordinary logs|
|2B: stopped hang|Higher-precision32984 audit, then one local decay trial if supported|Does retainedIAC release atVSS0/closedTPS without a blip?|Worse undershoot/stall or unchanged hang; revert that change|
|3: decel recovery|Optional2291exit750->1000 only|An actual activeDFCO event, fuel resumes before target without objectionable re-entry cycling|NoDFCOevent means inconclusive, not passed; worsen recovery means revert|
|4: metering|Verified injector data/pressure basis first; MAF corrections afterward, by operating cells|Steady-state commanded/measured lambda, repeatability at voltage/load|Don't mix injector/MAF/pressure changes or infer from transient trim|
|5: drivability|Validated warm/cold start, load pickup, stop return, gentle off-idle, then cruise|Separate evidence for each maneuver; actual speed/TPS/fuel states|Faults/stalls or unexplained torque intervention: return to prior stage|
|6: power|Hardware/fuel/pressure/temperature/knock limits established, controlled loaded testing|Actual boost/load/pressure/lambda and safe timing evaluation|No road pull as substitute for missing fuel/knock evidence|

Working acceptance goals (not Ford specifications): no stalls; settled mean near
desired; central95% of steady RPM error within±50RPM; no recurring steady-state
undershoots>100RPM. For an identified accessory transition, aim for recovery
within2s without worsening undershoot/rebound. For a confirmed stopped closed-
throttle event, aim to settle within3s without a releasing blip. Revisit these
goals if verified cam/flywheel characteristics warrant it; never count a raised
target alone as a stability repair.

Each run answers one new question. Save owner events and compare with its exact
parent at similar ECT/accessory/learned-state conditions. Do not reset adaptation
casually between comparisons. A failed trial is rejected and documented, not
stacked into the next candidate. Numerical proposals above are not changes to
the saved files; no newv018 or engine run is created by this planning pass.

## Hardware facts needed for final calibration

Obtain injector part number and supplier data; MAF part number, housing inside
diameter and draw-through/blow-through/BOV arrangement; camshaft/VCT and flywheel
details; current fuel grade; pressure-sensor installation and measured differential
pressure. Record electrical steering and A/C-input arrangements. These are the
remaining physical-model facts, not requests for another identical idle log.

## Sources and scope

- [Inventory and hash](../reports/calibration-inventory/v017/manifest.json).
- [Ford idle controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm):
 generic control roles, not exact Black Oak implementation.
- [Ford spark controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_spark_advance.htm):
 low-load limit, MBT and multiplied temperature corrections.
- [Ford DFCO controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_cutoff.htm):
 separate RPM/speed gates and limiter-load conditions.
- [Injector controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_general.htm):
 pressure reference, flow and offset relationships.
- [Ford SVT supplement](https://www.fordservicecontent.com/Ford_Content/catalog/owner_guides/04focsv1e.pdf):
 twin-layshaft transmission and overall ratios; not software normalization.

Full exposed inventory is not a full ECU algorithm, a decoded stock comparison,
or proof of hardware condition.94 descriptions and some axis units remain absent.
Do not let the completeness of the value list inflate confidence in unsupported
numerical changes. Existing tune binaries were left unchanged.
