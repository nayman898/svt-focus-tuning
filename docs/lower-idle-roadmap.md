# Working toward an 800-850 RPM warm idle

Owner goal: a smoother, more comfortable **800-850 RPM fully warm idle**.
Start by evaluating 850 as the eventual target; 800 is a later possibility,
not a guaranteed requirement for this modified engine. Camshaft details,
injector characterization, hot oil pressure and charging behavior still limit
what can be promised. Cold-start and initial catch speeds are a separate
calibration requirement from fully warm idle.

## Current position and revised priority

v005 averages approximately 1,100 RPM and sustains closed loop. It also has
brief dips into approximately 870-930 RPM in reviewed recordings, a separate
899-RPM minimum, fan-off displayed-AFR excursions around 16-18, and unresolved
module-supply observations during fan engagement and cranking. These are not
good conditions for a direct change to 850. The same numerical RPM loss is
not assumed to repeat at a lower setpoint, but the disturbances show why
recovery margin must be demonstrated rather than inferred from mean RPM.

The [owner-marked fan-off review](../reports/2026-10-26-v005-fan-off-review.md)
now takes priority for the warm-idle goal. The proposed
[startup-airflow cell change](v006-target-proposal.md) remains a separate,
deferred option; it would not solve the later fan-off fuel excursion.
v006 has since been prepared as a
[post-repair fan-stage baseline](../tunes/v006-post-repair-fan-baseline.md),
for use after the resistor/pigtail repair. It is not a lower-idle or
fuel-correction trial; those still follow the measurements below.

## Work before the first lower-target trial

1. **Resolve the fan-related supply/load observations.** Independently compare
   battery-post and underhood/ECU-supply voltage during cranking and fan
   engagement; inspect the relocated battery's cable/ground path as indicated
   by measured drops. Keep the existing fan-resistor bypass and its repair/
   retirement plan explicit. Do not call the 7-V Scanner observation a measured
   battery failure or use tune changes as its presumed repair.
2. **Identify fan-off fuel recovery.** Capture one labeled fan on/off cycle
   with measured wideband and usable upstream O2, B1 STFT, MAF, commanded-mixture
   and actual spark data. Verify the commanded-mixture channel's meaning before
   treating its 0.94-1.15 lambda-unit ramp as a base-target or fuel-trim error.
   The [focused logging profile](../profiles/2004%20Focus%20SVT%20-%20Idle%20Fuel%20Recovery.Channels.xml)
   is staged but not live-validated. Do not choose arbitrary O2 gains/delays,
   MAF corrections or injector values from the current wideband excursions.
3. **Check low-flow fuel control.** Obtain the exact Siemens injector part
   number and proper offset/short-pulse/minimum-pulse data, together with the
   actual pressure-reference conditions. The installed 60 lb/hr injectors do
   not by themselves rule out 850 RPM, and current logs do not establish that
   minimum pulse width is causing the problem. Verify it if lower-flow operation
   becomes the limiting condition; do not invent a new injector calibration.

## Staged target experiments

Once the current idle/fuel/load response is repeatable and acceptable:

| Candidate stage | Nominal warm idle target | Scope |
| --- | ---: | --- |
| First lower-target trial | **1,000 RPM** | Change the relevant P/N and Drive target scalars only, retaining v005's other settings. Confirm which targets apply on this manual-transmission controller. |
| Next | **950 RPM** | Proceed only after the 1,000-RPM capture passes. |
| Next | **900 RPM** | Repeat the same load/restart comparisons. |
| Initial goal | **850 RPM** | Accept only if starting, mixture, load recovery and supply/oil-pressure conditions remain satisfactory. |
| Optional later goal | **800 RPM** | Evaluate separately if 850 has demonstrated sufficient operating margin. A comfortable stable 875-900 may be the right result for the actual hardware. |

These are proposed diagnostic increments, not verified operating limits or
preassigned revision numbers. Assign each actual calibration its own revision,
parent, comparison, hash and rollback. Keep startup multipliers, fan thresholds,
fuel tables and spark gains unchanged during the first target-only comparison.

## Why the target change must not be combined with an arbitrary air reduction

The saved v005 **ECM 44242** P/N base-airflow curve is already indexed by desired
RPM: 0.29 lb/min at 700, 0.41 at 900, 0.46 at 1,000, and 0.60 at 1,250. Linear
interpolation gives the following base lookup estimates:

| Desired RPM | Existing base-airflow lookup, lb/min |
| ---: | ---: |
| 1,100 | 0.516 |
| 1,000 | 0.460 |
| 950 | 0.435 |
| 900 | 0.410 |
| 850 | 0.380 |
| 800 | 0.350 |

These are calibration lookups, not measured total engine airflow, actual IAC
duty, or proof the curve is correct at lower RPM. The controller also applies
startup/temperature/adaptive and other corrections. Moving from 1,100 to 850
already selects approximately 26% less base airflow on this curve; independently
cutting it another guessed percentage would confound the target trial.
HP Tuners describes this
[desired-RPM-based base-airflow relationship](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm).
If settled corrections or saturation later show a base-airflow mismatch, adjust
the relevant portion in its own measured revision.

## Acceptance at each stage

- Same documented fuel, water/meth state, warm coolant range and accessory
  conditions; preserve native HPL/LOG and all-channel CSV with fresh timing.
- Stable starting and hot restart; acceptable time to settle, without stalls
  or persistent hunting. Match initial temperature/state when comparing starts.
- Repeatable fan on **and off**, blower and other normally used loads, including
  real A/C compressor engagement if applicable. Record actual event times.
- Measured mixture and available fuel corrections remain acceptable through
  transitions. A good mean AFR or CL Active flag alone is insufficient.
- Idle-air control retains adjustment room, and spark is not continuously
  limited trying to rescue RPM. Preserve corrective spark; tune gains only
  after measured response supports it.
- Charging and hot oil pressure meet the actual vehicle/engine requirements.
  No numeric minimum is invented here. Stop/revert if these conditions or
  starting/load recovery worsen; retain the previous accepted target.

All present testing remains stationary and throttle untouched under the v005
scope. Before later moving/return-to-idle or road validation, review the inherited
200-count low-RPM open-loop TPS experiment and its off-idle interpolation,
plus boost/enrichment behavior. A successful 850-RPM parked idle does not
validate the current tune for road or boost use.
