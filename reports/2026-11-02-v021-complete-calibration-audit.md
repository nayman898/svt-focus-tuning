# v021 complete exposed-calibration audit

Reviewed November 2, 2026. **v021 is a useful diagnostic baseline, but it does
have unresolved table anomalies and configuration gaps. It is not a finished,
validated tune.** The most actionable new findings are the remaining fuel-pressure
diagnostic suppression and the almost vertical cranking-fuel change at 64 F.
The existing warm-idle problem remains unresolved; neither finding proves its cause.

This is an offline review of the saved v021 calibration. No VCM session was
needed. No HPT file, ECU setting, logger, adaptation or diagnostic state changed.
The latest historical trial was v023; this report evaluates **v021**, not a
claim that the owner has already restored it in the car.

## Coverage and identity

- File: `tunes/v021-fuel-pressure-feedback.hpt`, 247,597 bytes.
- SHA-256: `078E91786A07793A4EB6607B8B870BDC9558562C0FE75AF95E6D5AB1A1A87ACA`.
- All 24 cataloged tune files match their recorded byte lengths and SHA-256.
- Reviewed all **342 exposed parameters: 96 tables and 246 scalars/switches**,
  including all 4,692 captured table cells/headers and all 163 DTC rows.
- All table grids are rectangular and complete; scalar values are populated.
  Numeric axes are nondecreasing. Thirty tables contain repeated numeric axes;
  these are not automatically mistakes. Only the inactive LTFT learning table
  has different displayed outputs on adjacent repeated numeric breakpoints.
- Evidence: immutable v017 inventory, verified v017-to-v016 comparison, and
  v018/v019/v021 deltas. Full-precision MAF evidence and the pre-v020 base-air
  readings supplement rounded original captures. The reconstruction builder
  and revision relationships were checked.
- v021 inherits v016's 520 F O2 threshold, v018's 1,000 RPM DFCO exit and P0132
  MIL reporting, v019's nine-cell MAF adjustment, and v021's pressure transfer.
  It excludes v020's air cut, v022's 0.750 spark gain and v023's 10-degree idle spark.

The [342-entry ledger](2026-11-02-v021-parameter-review.csv) records source,
screening results and finding IDs. The [check results](2026-11-02-v021-audit-checks.json)
record input hashes, identity checks, coverage and revision differences.
“Screened” means reviewed for an identifiable issue; it does not mean optimized
or validated throughout the engine's operating range.

The inventory covers exposed calibrations, not every hidden strategy constant.
Ninety-four descriptions and some axis units are unavailable. Display rounding,
generic help and missing exact stock-reference decoding limit interpretation;
none prevents identifying the concrete anomalies below.

## Findings and decisions

### F01 — Live pressure sensing still has diagnostic blind spots

**Priority: address in a separate diagnostic correction.** In ECM50, P0190 and
P0192 are `No Error Reported`; P0193 is `No MIL Light`. The physical sensor is
now installed and ECM7596 has a variable transfer. Suppressing circuit/low-input
reporting no longer fits the intended measurement baseline. Recommend restoring
applicable P0190/P0192/P0193 reporting to MIL in a separate candidate after
confirming strategy-specific monitor applicability. Do not change pressure-test
thresholds or enable every DTC as part of that correction.

P0191 has no row in this exposed list; do not invent one. The diagnostic timing
and pressure-test conditions still govern whether any code runs or sets.
`No MIL Light` is distinct from suppressing reporting. Pump-driver codes are
also a separate question because the owner-confirmed relay bypass removes ECU
control of physical pump speed.

P0132 was already restored in v018 and remains MIL in v021. P0320, P0340,
P0133/P0135, P1130/P1131/P1132, cylinder 1–4 misfires and IAC P1504/P1506/P1507
also request MIL. Current counts are 66 MIL / 43 no-MIL / 54 no-error; the older
v017 counts must not be reused. Generic captured DTC descriptions are not an
exact Ford diagnostic manual, and reporting configuration is not a current code scan.

### F02 — Cranking fuel has an extreme 64 F discontinuity

**Priority: investigate/correct the starting map once its intended shape is
established.** ECM44519 has:

| ECT, F | Displayed cranking value |
| ---: | ---: |
| 40 | 0.886 |
| 63.990 | 0.930 |
| 64.000 | 0.335 |
| 90 | 0.430 |
| 120 | 0.647 |
| 150 | 0.764 |
| 180 | 1.000 |

That is a 64% drop across 0.01 F. HP Tuners describes this table as commanded
cranking lambda; on that interpretation the lower number requests **more** fuel,
approximately 2.78 times as much at equal air mass across the edge. This is a
command-model comparison, not a measured injector or delivered-fuel ratio.
[HP Tuners fuel definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).

The near-coincident breakpoints look like an intentional step or inherited
workaround, rather than an ordinary smooth temperature correction. Intent and
correct replacement values are unknown. The earlier ledger merely retained this
table; this audit explicitly elevates it. It can affect starting around/above
64 F, not ordinary warm running after cranking ends. Do not explain the late
idle dips with this table unless a genuine cranking-state re-entry is established.
Use injector characterization and a valid starting reference to choose a later
local correction; arbitrarily replacing 0.335 with 0.930 is not justified.

### F03 — Open-loop fuel has lean pockets and a sharp low-RPM mode boundary

**Priority: resolve before declaring drivability/load calibration complete.**
ECM44511 has lambda 1.07 and 1.14 at 2,500 RPM on displayed TPS rows 15.6 and
19.5. On the 19.5 row it then moves 1.02 at 3,500, 0.85 at 4,000 and 1.00 at
4,500. At 2,500, moving from TPS row 23.4 to 31.2 changes 1.00 to 0.80.
These are real lean/rich pockets, not a uniformly rich turbo map.

ECM32731 is 200 counts at 0/1,500 RPM and zero at 2,000 RPM upward. Linear
interpolation gives 180 counts at 1,550 RPM and 100 at 1,750. With historical
closed-throttle absolute TPS around 180, that makes the 1,500–2,000 transition
particularly relevant. This is a conditional comparator calculation, not proof
of the active TPS convention in every strategy path. It also does not make the
TPS axis of ECM44511 interchangeable with raw absolute counts.

The high-load region includes 0.73–0.80 lambda values, but a TPS-based map alone
does not demonstrate suitable mixture at every boost/load combination. Validate
the active fuel source and final command before selecting local replacements.
The rejected v014 open-loop experiment is evidence against globally removing
closed loop as a cure. Retain the current baseline while preparing targeted
corrections. [Fuel-table and mode definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).

### F04 — The MAF curve is monotonic but still markedly uneven

**Priority: characterize, then make local metering corrections.** ECM12163 has
no reversed flow points. It nevertheless has alternating shallow and steep
segments in the observed idle-voltage region. Using the saved common Editor
display units, the slope at 0.540–0.600 V is about **5.60 times** the slope at
0.600–0.649 V; 0.649–0.699 is about **11.98 times** the preceding slope.
The 0.500–0.529 segment is also unusually shallow. These ratios are independent
of a common units conversion and can change calculated-air sensitivity to voltage.

At the upper end, the slope from 3.799–4.800 V is only about 36% of the preceding
3.400–3.799 segment, with a large final voltage gap. This is a separate high-flow
review item; idle data cannot validate it. v019 only made bounded low-flow changes
and did not establish that the whole curve matches the installed HPX/housing.

Do not mistake the shallow regions for exact plateaus, or multiply the curve by
7.94 to repair the display-label discrepancy. The existing injector/aircharge
cross-check favors the g/s-equivalent numerical interpretation. The exact housing
reference and steady-state metering evidence still determine corrections.
[Existing scaling evidence](2026-10-30-hpx-scaling-status.md).

### F05 — Warmup air and spark transitions remain major idle-control leads

**Priority: highest relevance to the warm deterioration, causality unresolved.**
ECM44240/44243 are identical. At 188 F, interpolation gives 1.30 at 165 seconds
and 1.0225 at 200 seconds: a **21.35% decrease** in this base-air contribution.
At a fixed 188 F there is no further runtime decrease after 200 seconds.
The underlying P/N/Drive base tables are identical and monotonic; v020's rejected
5% cut is absent.

ECM44568's cold-start maximum spark map has a substantial late-runtime rise,
and its separate ECM44569 adder is about +41 degrees near 1,000 RPM/light load.
The documented base-plus-adder roles make a change in available spark authority
plausible. A negative value in 44568 is not, by itself, final commanded timing.
Eligibility, actual limiter selection and feedback arbitration are not recorded.
[HP Tuners spark definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_spark_advance.htm).

ECM44603 also decays from 60 to 10/8/4/2/0 degrees at displayed time breakpoints
0/480/600/720/860/1,000. Its exact time units and active path remain unresolved;
do not equate that axis with logged engine runtime or claim it limits all idle
spark to zero. No idle-air integrator gain/limit is exposed in this inventory.

Retain 950 RPM, nominal idle spark 12 degrees, gain 1.000 and floor -6 for the
baseline. v022/v023 failed adoption; neither proves that further spark reduction
will help. A future air-runtime trial should alter one transition while preserving
the final warm endpoint, with a stated prediction and rollback. Continued dips
long after 200 seconds cannot be attributed to a continuously decaying runtime
multiplier. Fan/load release, adaptation, metering and actuator behavior remain
competing explanations.

### F06 — Dashpot decay is suspicious for the separate hanging-idle symptom

ECM32984 displays 0.00 at airflow 0/0.2/0.4/0.6, then 0.06/0.08/0.10 at
0.8/1.0/3.0. Identity-matched captured help says smaller numbers decay more
slowly. The low cells could retain air; two-decimal zero does not establish an
exact zero. Generic web dashpot descriptions do not consistently describe this
strategy, so they are insufficient to choose rates.

Retain the minimum/pre-position/clip tables until rate precision and active state
are known. Check inferred-neutral behavior (45824 enabled), closed throttle and
speed state as part of a later local decay trial. DFCO exit is already 1,000 RPM,
with 1,200 RPM entry and 35/12 mph gates; that coherent hysteresis is not a fix
for an already-stationary hang and remains unvalidated in an active DFCO event.

### F07 — Injector and pressure models are not yet characterized as a set

Slopes are 63.00/60.12 lb/hr, breakpoint 0.00003360 lb, minimum PW 0.5 ms and
reference pressure 40 psi. Voltage offsets decrease with voltage as expected
in shape, but the exact Siemens injector part/characterization remains missing.
At idle, offset/breakpoint errors can matter even with a plausible nominal slope.

Pressure compensation is enabled, while the exposed slope/breakpoint/offset
pressure multipliers are unity at repeated 40-psi axes. Restoring the sensor
does not establish a properly characterized pressure-dependent injector model.
For scale only, sqrt(45/40) is 1.061: pressure-basis differences of this size can
matter. This is not a recommendation for a 6.1% slope correction or a claim that
the strategy applies that exact law through these tables.

Retain 40 psi reference and the owner-set regulator until the injector rating
basis is known. The new pressure transfer is monotonic, agrees around the tested
operating range, and is explicitly a nominal curve with low clamp/high extension,
not a recovered factory transfer. No broad change follows from “43 versus 40.”
[Injector parameter roles](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_general.htm).

### F08 — O2 startup control still needs attention independently of warm idle

ECM12115 is 520 F, not the rejected v017 600 F. ECM32916 heater duty steps
100% -> 75% at displayed 30–31, and 50% -> 35% at 72–73. The axis unit was
not captured; this is not proof those are engine seconds or that actual heater
power follows those numbers. The 2,000–4,000 RPM O2 monitor window also does not
establish sensor readiness at idle or describe every O2-related diagnostic.

The three 254-second delay scalars coexist with a separate delay table; v021
actually enters CL much earlier, so do not interpret them as a universal
254-second gate. In the saved v021 warm-start run, CL entry still reaches +25%
trim and measured lambda 0.733. Later near-stoichiometric idle does not erase that
failure. Physical heater/signal verification and the planned known-good sensor
comparison remain useful; repeating the 600 F gate trial is unsupported.

ECM44512's warm 1.03 and ECM44516's final 0.03 nominally cancel. Do not zero
the decay tail alone. Additional shape flags: ECM32748 rises to 0.06 on its final
warm startup-enleanment row; ECM32742 has a 60/90 F startup trough followed by
larger 1–1.5-second values; ECM44211 has a local nonmonotonic 30-duty row. Their
active roles/units require confirmation before assigning a delivered-mixture
effect. They are not established causes of late warm dips.

### F09 — Loaded spark and temperature protection require separate validation

ECM44583 drops from 6.5 to -7 degrees at 1,000 RPM between load 0.70 and 0.80;
at 2,450 RPM the corresponding change is 21 to 6.73. That is a real torque
transition, potentially deliberate load protection. The MBT map also has
nonmonotonic regions. Do not smooth either upward to improve appearance.

ECM44587's IAT base correction is multiplied by ECM44588. At load 0.80 and
2,600/3,250 RPM the multiplier is zero, so this particular IAT-retard contribution
is zero at those exact nodes even at high IAT. That is an unresolved protection
coverage issue, not proof all thermal protection is disabled. The coolant
correction has a similar zero at load 0.80/2,600 RPM. Validate the total active
timing/protection behavior before accepting loaded operation with meth off.
The temperature multiplier relationship and MBT role are documented by
[HP Tuners](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_spark_advance.htm).

Flange, catalyst and O2 thermal fuel controls remain enabled with ordered
enable/disable thresholds. Global spark adder/multiplier are 0/1, one knock sensor
is configured, and RPM limits are 7,400. These settings do not independently
validate thermal models, knock response, hardware RPM capability or boost safety.
Tip-in fuel multipliers and the tip-in detonation-retard table are zero; this
removes those particular contributions, not necessarily every transient strategy.

### F10 — VCT and IMRC need an actual hardware/operating-state match

VCT is enabled/intake-only. ECM44412 contains -22/-25 degrees at 1,000 RPM,
load 0.20/0.30, and strong -49.5 regions at 2,500–3,500 RPM/load 0.40–0.80.
At 2,500 RPM, load 0.80 -> 1.00 moves -49.5 -> -13: a large phasing change.
The highest load breakpoint is 1.00 while main spark maps extend to 2.00.
This requires an intended high-load phasing review, not an invented extrapolation
or a blanket VCT disable. The ECT multiplier is flat 1.00 from 90 F onward,
so it supplies no discrete 180/188 F switch.

IMRC control and sensor switches are disabled. Confirm that this matches the
physical runner arrangement before final drivability work; the enabled VCT
system is separate. The prior short cam capture did not establish commanded/
actual tracking or clear the entire cam system.

### F11 — Definition-sensitive oddities should stay on the ledger

| Item | v021 observation | Disposition |
| --- | --- | --- |
| 44801 traction-control scalar | 135; captured help describes displacement in liters x10 | Apparent definition/value mismatch for a 2.0L application. Verify strategy encoding; do not blindly set 20 or zero. |
| 7277 crank-sensor maximum | 4,500 RPM in Diagnostics, versus 7,400 limiter | Verify diagnostic versus acquisition meaning. Not proof the CKP stops working above 4,500, or an explanation for idle RPM dropouts. |
| 12215/12216 neutral-limiter load window | Min 1.99 / max 0.00 | Apparently excludes the mode under captured logic; both main/neutral cutoffs are 7,400. Do not swap to “repair” idle control. |
| 18224 peak-load curve | 0.83 at 2,000 -> 2.00 at 2,500 | Large model transition; selected load mode is MAF Corrected. Verify dependent load/clipping paths before changing. |
| 14683 LTFT learning | Repeated load=1.00 with differing signed/index-like outputs; limits 0.75/0.25 | Learning disabled. Do not interpret as live percentage trims or activate casually. |
| 43010 rail-temp time constant | 3.17 at flow 0.68 -> 24.30 at 0.90 | Nonmonotonic model feature; actual injector-temperature dependency unresolved. |
| 43005 desired-pressure AAT “adder” | 40–62 despite base desired pressure 40 | Definition/combination needs confirmation; do not conclude an 80-psi physical command. |
| 23010–23017 ambient model | Several zeros, soak factor 1 | Could affect inferred ambient/rail models. No established instantaneous-temperature behavior from a zero display alone. |
| 4227/4228 OSS limiter | On 16,380 / off 0; ratio table unity | Extreme apparently unused limit path. Do not test the limit or infer a normal-driving fault without state evidence. |

### F12 — Remaining system groups: no supported numerical correction identified

Four cylinders, firing order 1-3-4-2, manual transmission, ETC not fitted and
force-neutral disabled are internally consistent with the recorded setup.
Final-drive 1.00 and the gear constants require the existing normalized/twin-shaft
interpretation check, not substitution of brochure ratios. N/V 13.98 matches
839 tire rev/mile divided by 60 within display rounding; actual speed calibration
and tire fitment remain independent validation items.

Low fan 195/190 F and high 225/215 F have sensible threshold ordering and retain
the repaired-fan baseline. Owner-observed approximately 196 on/188 off is not
proof the saved thresholds are wrong. Airflow/load pickup and release still need
operating evidence. A/C enabled with pressure-switch disabled and steering-input
enabled need hardware-input matching; neither alone proves faulty control.

EVAP purge is enabled; actual purge operation is an unmeasured potential airflow/
fuel disturbance, not a newly identified failed valve. Pump gains, duty values
and adaptive voltage cannot command physical pump speed through the reported
relay bypass. Keep that fact separate from ECU fuel/pressure modeling and fault
monitoring. Failed-sensor airflow tables and misfire models have no newly proven
error, but their presence is not a validation of fallback operation under boost.

## What to address first

1. **Keep v021 as the comparison baseline.** Its warm run still had a 187.5-RPM
   full span (829.5–1,017) and 72 sub-900 groups in 267 seconds, despite mean
   950.72 and mean lambda 1.0104. Mean RPM/mixture are not stability acceptance.
   Desired RPM/TPS were missing, so this is not measured target-error coverage.
   [Saved v021 review](2026-11-02-v021-baseline-review.md).
2. **Restore applicable pressure-sensor diagnostic visibility in an isolated
   candidate**, then verify only the selected DTC rows changed. It improves
   detection; it is not an idle fix. No candidate was created by this review.
3. **For starting, resolve the 64 F cranking discontinuity and O2 readiness as
   separate mechanisms.** Neither justifies changing the warm spark/air maps.
4. **For warm dips, retain the planned one-component hardware comparison**, with
   exact revision and installed sensor identity recorded. If a calibration trial
   follows, the air/runtime transition is a concrete remaining target, with one
   change and explicit keep/revert criteria. Do not stack rejected air/spark trials.
5. **Before broader drivability/power acceptance**, resolve MAF/injector matching,
   fuel pockets/mode transition, VCT/IMRC configuration and loaded thermal spark
   behavior. A complete value inventory cannot establish those physical matches.

Next run card, when the owner is ready for the already-planned hardware comparison:
confirm exact v021 and the single changed component; capture before start using
the existing readiness-checked profile with desired RPM/TPS, raw FRP, loop state,
wideband, spark and IAC present. Retain the full warmup so startup, 165–200-second
air taper and later behavior can be distinguished. Mark fan/load changes rather
than inferring actual switching from ECT alone. Compare matched temperature,
runtime and load windows using span/distribution, time outside target, dip depth
and recovery; reject a worse or stalling result. This card does not initiate a run
or request another unchanged baseline recording.

No single arbitrary table edit is supported as a demonstrated cure. The concrete
follow-up list is now broader than idle spark gain, and the cranking discontinuity
and pressure diagnostic omissions should no longer be treated as “screened, fine.”
