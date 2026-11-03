# v024 staged regression test

Candidate: [v024 fuel cleanup/diagnostics](../tunes/v024-fuel-cleanup-diagnostics.md).
Parent/rollback: exact v021. Status: prepared, no flash or test confirmed.
Owner's next-start context: cold engine, new upstream O2, pre-crank O2 heater and
CKP/ground inspection recommended before cranking. Water/meth remains off. This is
a test of that combination, not an isolated O2-versus-tune causality experiment. No
recording or engine action starts from this card.
The [machine-readable run card](v024-run-card.json) records the exact tune/profile
hashes, pending installation/coverage and stop conditions for the capture bundle.

## Preparation and capture

1. Owner confirms the exact candidate written, and records:
   - **Upstream O2 install & heater check**: part number/install timing, plus KOEO/connector verification of `12 V` heater supply and heater ground continuity (so an open heater circuit cannot mimic a dead sensor at `0.00 V` during CL entry).
   - **CKP / 36-1 trigger & ground inspection**: physical check of CKP sensor tip (metallic debris), air gap/seating against the SBC flywheel trigger ring, VR harness routing/shielding away from coil/ignition/alternator leads, connector pin tension, and block-to-chassis ground straps (motivated by recurring closed-throttle `+18%` single-frame RPM spikes and `1`-rev `0 RPM` sync dropouts in `v013`–`v023`). Record whether inspected-only, cleaned/adjusted, or untouched.
   - **Initial soak & state**: initial `ECT` (noting `ECM44519` commands leaner cranking lambda `0.886–0.930` below `64.00 F` and richer `0.335–0.430` at `64.00–90.0 F`), approximate soak, fuel/refueling, and accessory state.
   The agent does not perform the ECU write or start the engine.
2. Reuse [V023 Idle Spark Trial18](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml):
   its name is historical; label this new recording **v024-cold-cleanup**.
   Its exact request configuration populated all 18 fields in the last v023 run.
   No channel additions are needed for this stationary test, and the active
   saved configuration still needs verification before capture.
3. Use the logger readiness checks before crank. Require RPM, desired RPM, TPS,
   ECT, raw FRP, O2, STFT, fuel/loop/fallback states, spark/source, IAC/air corrections,
   voltage and valid SCG wideband. Blank is not zero. Keep setup/admission samples
   and preserve the complete recording; no restart simply to discard a bad segment.
4. Retain the exact loaded profile, native HPL/SQLite, full CSV exports, manifest
   and event markers. Derive clock alignment per session and audit data coverage.
   The runtime PID is omitted because it saturated at 255 previously; derive
   elapsed run time from the recorded start, with any gaps/restarts identified.

## Stage A — cold start, closed-loop entry and warm idle

Capture before crank. Keep throttle/accessories unchanged through the initial
assessment; mark any required intervention. Record catch/retry/flare, time and
ECT at CL entry, narrowband response and independent wideband behavior. A new
O2 sensor must not be assumed ready or correct solely because it is new.

If behavior remains acceptable, retain warmup through elapsed running time
greater than 300 seconds and **60–90 seconds of fully warm idle**, approximately
180–195 F, before evaluating the result. This covers the existing air taper and
late startup-control window. Allow up to about 12 minutes of attended capture;
if warm conditions are not reached, record that stage as incomplete rather than
extending indefinitely. End sooner for the stop criteria below.

Mark observed fan on/off. If a natural fan-off occurs while running remains
acceptable, retain 60 seconds afterward. No observed cycle means fan recovery
remains untested. The owner's prior 196/188 F observations are temperature proxies,
not direct switch-state measurements.

### Stage A2 — warm clutch-pedal flywheel/gearbox chatter isolation

After capturing the settled warm-idle window (and outside an active fan on/off
transition), perform a gentle stationary A/B check in neutral:
1. Press and hold the clutch pedal **fully to the floor** for **30–45 seconds**
   (mark `clutch_down`).
2. Release smoothly back to neutral **clutch-up** for **30 seconds** (mark `clutch_up`).

Decoupling the Getrag MT285 dual-layshaft input gears from the lightweight
`SBCSVT-SS-TZ` single-mass aluminum flywheel (while preloading crankshaft axial
thrust) isolates how much of the warm RPM jitter/spikes comes from mechanical
gearbox backlash chatter versus the `0.600 V` `ECM12163` MAF slope kink and VR
sensor noise.

## Stage B — changed fuel region and return to idle

Proceed only after satisfactory warm idle and review of live essentials. If
Stage A is questionable, finish/export it and review before any throttle test.
While parked in neutral, gradually hold approximately 1,500, 2,000 and 2,500 RPM
for 10–15 seconds each, returning to idle for about 20–30 seconds between holds.
Avoid abrupt blips or chasing a particular TPS number. Record actual TPS/RPM,
fuel source, loop state, wideband, trim, pressure and recovery. Stop for worsening
behavior; no driving or boost maneuver is part of this card.

Prior `v014` road logs (`Throttle Position ADC (Relative)` paired with commanded
equivalence/lambda) confirm `ECM44511` indexes TPS as `Relative_ADC / 10.24` (`%`)
and **clamps to the `15.625%` (`160` relative count) first row** for all smaller
throttle openings (`1%–15.6%` relative TPS). Furthermore, because `ECM32731`
(`Open Loop Fuel TPS Thresh vs. RPM`) is `200` counts at `0–1,500 RPM` and **`0.00`
at `>= 2,000 RPM`**, expect distinct loop behavior across the three holds:
- **`1,500 RPM` hold**: Remains in **Closed Loop (`Stoich`, `Closed Loop Active = Yes`)**
  provided relative TPS stays below `200` counts.
- **`2,000 RPM` and `2,500 RPM` holds**: Automatically enter **Open Loop
  (`Power Demand Enrich`, `Closed Loop Active = No`)** via `ECM32731 = 0.00` and
  clamp directly onto the edited `15.625%` row (`1.000` lambda at `2,500 RPM`,
  previously `1.07`). Do **not** mistake `Closed Loop Active = No` at `2,000–2,500 RPM`
  for an O2 fault.

A steady warm open-loop segment at `2,000–2,500 RPM` (`Power Demand Enrich` active,
valid SCG wideband) directly evaluates the `v024` fuel cleanup. Keep any hold with
incomplete acquisition or unexpected mode **untested**, not passed. No attempt to
force open loop by changing the tune or disabling a sensor is requested.

## Stop and evaluation rules

Stop the planned test for a stall/near-stall, repeated worsening dips, abnormal
mechanical behavior, pressure anomaly or new warning. Also stop for sustained
rough rich/lean running. Once warm or established in CL, measured lambda below
0.80 for over 5 seconds, or above 1.10 for over 3 seconds during steady operation,
is a review trigger, not a universal engine limit. Exclude invalid wideband data
and intentional deceleration; do not use these thresholds to reject normal
unvalidated cold enrichment by themselves. Preserve codes; do not clear/reset.

| Check | Evidence needed | Meaning of a satisfactory result |
| --- | --- | --- |
| Capture | All core fields/valid SCG; gaps disclosed | The covered segments are usable; population alone does not prove update rate. |
| Cold start/entry | Catch, flare, O2 response, CL entry and measured mixture | No failed catch/stall or persistent entry excursion; benefit cannot be assigned solely to v024 with the new sensor. |
| Warm idle | Matched ECT, runtime, accessory state and learned-air context | No worse span, central distribution, dip depth/duration, recovery or hunting; mean RPM alone is insufficient. |
| Clutch A/B | Marked `30–45 s` `clutch_down` vs `30 s` `clutch_up` at matched warm ECT/fan state | Quantifies RPM SD, sub-900 dips, and single-frame RPM spikes with MT285 input shafts decoupled vs coupled. |
| Target tracking | Desired RPM actually populated | Report time outside desired +/-50 RPM and undershoots over100; earlier v021 lacks target data, so do not fabricate a matched target-error comparison. |
| Pressure | Raw sensor trend, applicable operating-range conversion, independent gauge if available | No new dropout or repeated pressure collapse; no fault provocation to test DTCs. |
| Fuel cleanup | Warm `1,500 RPM` CL (`Stoich`) and `2,000`/`2,500 RPM` OL (`Power Demand Enrich`) holds with valid SCG | Expected mode switch at `>= 2,000 RPM`; steady `2,500 RPM` wideband tracks near `~1.00` without lean drift or stumble. |
| Return to idle | Each pedal release and subsequent20–30 seconds | No new hang, undershoot or stall. Stationary release is not moving/clutch validation. |
| Diagnostics | Read-only code check before/after when available | New FRP codes are investigated with signals; their visibility is not itself physical regression. |

Compare with the [v021 baseline](../reports/2026-11-02-v021-baseline-review.md),
which had warm RPM 829.5–1,017, SD27.94 and 16.18 sub900 groups/min over267 seconds.
These are historical descriptors, not acceptable stall margins or an exact cold
baseline. Starting temperature and sensor differ. If v024 appears worse or the
result is ambiguous, a v021 comparison retaining the new O2 can isolate the
calibration more effectively. Do not manufacture a quantitative pass where
matching coverage does not exist.

End the run with **Stop both & export**, verify saved/partial status and all
artifacts, then review before adoption. Report one of: regression/revert,
provisionally retained for covered conditions, or insufficient coverage. Hot
restart, road/load/boost and unvisited table regions remain separate tests.
