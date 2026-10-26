# v004 — stationary warm-idle closed-loop entry test

**Prepared; not flashed by the agent.** Parent:
[v003](v003-temp-fan-stage-match.hpt). Candidate:
[v004](v004-idle-closed-loop-entry-test.hpt).

## Evidence and purpose

The prior recordings reported Closed Loop Ready = Yes at warm idle but
Closed Loop Active = No, with Fuel Source = Power Demand Enrich. Read-only
inspection of v003 found [ECM] **32731, Open Loop Fuel TPS Thresh vs. RPM**,
set to **0.00 at every breakpoint**. The parameter's Editor description says
it is the TPS threshold required to enable open-loop fueling by RPM and A/D
counts. Zero is therefore a concrete candidate for a persistent TPS-based
open-loop request even at closed throttle.

This test raises only the lowest two breakpoints, using **8.00 A/D counts**
because that is already the parent calibration's Part Throttle TPS Enable
setting. The v002 log's relative TPS was approximately one count at idle.
This is a trial boundary, not a universal recommended threshold or proof of
the controller's internal scaling/comparator behavior. Other closed-loop gates
remain in force. Verify actual behavior in the recording.
[HP Tuners Ford fuel-loop reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm)

## Exact calibration difference

| RPM breakpoint | v003 OL TPS threshold | v004 OL TPS threshold |
| ---: | ---: | ---: |
| 0 | 0.00 | **8.00** |
| 1,500 | 0.00 | **8.00** |
| 2,000 | 0.00 | 0.00 |
| 2,500 | 0.00 | 0.00 |
| 5,500 | 0.00 | 0.00 |
| 6,500 | 0.00 | 0.00 |
| 16,384 | 0.00 | 0.00 |

The interpolated region between **1,500 and 2,000 rpm also changes**. This is
not a strict idle-state-only code gate: it is a table indexed by RPM with a TPS
threshold. Testing is limited to stationary warm idle. Driving/boost behavior
has not been validated. Cells at 2,000 rpm and above are untouched, but that
does not establish every off-idle transition as safe or unchanged.

Explanatory notes were appended in **Calibration Details > Notes**, preserving
the inherited temporary fan-path explanation.

## Deliberately retained

- 1,100-rpm idle setpoints.
- v003's temporary high-speed fan temperature thresholds, **195 F on / 190 F
  off**, with stock relays/fuses and the owner's resistor-wire bypass.
- **254-second** cold/warm/hot closed-loop startup delays and other enable gates.
- **LTFT disabled**; no long-term learning switch was enabled.
- Injector pressure compensation **Enabled**, matching v003.
- Injector/MAF data, base fuel, spark tables/gains, fan master enable,
  diagnostics/MIL settings and SCG-1 settings.
- IMRC unchanged; its review remains queued after engine stabilization.

## Verification and history

- Parent hashes were checked against the revision catalog.
- The saved draft was reopened for verification.
- Comparison initially detected an unintended injector-pressure-compensation
  toggle in the draft. The parent was opened directly to verify Enabled, the
  draft was restored to Enabled, saved and reopened again.
- Final comparison contains **only Notes and one calibration table**:
  Open Loop Fuel TPS Thresh vs. RPM. No injector-compensation difference remains.
- All seven saved table rows were checked: the two low-speed cells are 8.00;
  all five higher-speed cells remain 0.00.
- No ECU write was performed.

## Controlled test

After an owner-initiated write, start both Scanner and LogWorks recordings from
the restart. Capture fully warm idle and continue beyond the retained
254-second startup delay; approximately **6–8 minutes** provides time to observe
entry and a settled segment. Include fan engagement if it occurs, and note
accessory changes. Keep the throttle untouched for the initial comparison.

Watch and record Closed Loop Ready/Active, fuel source, upstream O2 voltage,
commanded lambda, measured SCG mixture, RPM/target, spark source/advance and
voltage. Capture B1 short-term fuel trim if the controller provides it. The
available profile has not yet delivered usable fuel trims/idle-air duty in CSV;
recorded channel presence must be checked, not assumed.

The first success criterion is whether **Closed Loop Active changes to Yes**
at warm closed-throttle idle. Then assess measured mixture, idle behavior and
correction activity. A flag change alone is not proof of a finished tune.
If closed loop never activates, record the state and investigate the remaining
gates; do not change delays, sensor thresholds and fuel tables at the same time.
If idle or measured mixture deteriorates, stop the test and use v003 as rollback.

Save native HPL/LOG and CSV exports in a new **v004** session folder. Do not
reuse a prior recording's clock offset; derive and qualify this session's timing.

## Temporary fan-path retirement

This candidate inherits the fan-resistor-bypass test. Electrical inrush and
turbo heat exposure remain hardware matters. After proper resistor/wiring
repair, restore the original high-speed **225/215 F** thresholds while preserving
any later useful calibration changes, and record the retirement as a revision.
