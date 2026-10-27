# v005 - stationary warm-idle absolute-TPS threshold test

**Owner supplied a fresh running session after handoff; saved recording shows
closed-loop entry, with a startup disturbance still unresolved.** See the
[startup review](../reports/2026-10-26-v005-startup-review.md). No agent write or
ECU readback was performed; stationary-only scope remains.
The [delayed-wideband warm-idle review](../reports/2026-10-26-v005-closed-loop-review.md)
confirms sustained CL with remaining voltage/RPM disturbances and AFR
excursions. Metadata pairing is provisional; no fuel-table correction follows
from this result alone.
The [settled-idle follow-up](../reports/2026-10-26-v005-settled-idle-review.md)
finds mean RPM near 1,100 and smaller settled idle-air corrections; the next
comparison is a marked electrical-load step, with v005 unchanged.
The [owner-marked fan-off review](../reports/2026-10-26-v005-fan-off-review.md)
finds sustained measured mixture excursions while CL stays active; the next
priority is fuel-control/airflow recovery evidence, with no new tune yet.
Parent: [v004](v004-idle-closed-loop-entry-test.hpt).
Candidate: [v005](v005-idle-absolute-tps-entry-test.hpt).

## Evidence and hypothesis

v004 did not produce closed-loop entry. Subsequent saved recordings confirm
Open Loop Active/Conditions Yes, Closed Loop Ready Yes and Active No, Fuel
Source Power Demand Enrich, FMEM No and O2 B1 Fail No. See the
[follow-up and channel test](../reports/2026-10-26-v004-channel-test.md).

Reinspection of the first baseline CSV found **8,333 exported observations**
with throttle state Closed and populated **absolute TPS ADC**: minimum
181.8223, maximum 183.8203, mean 182.8235 counts. The v002 CSV's **relative**
TPS spans 0-0.9980 counts. These are different sessions and channel forms;
their values must not be substituted for each other. Counts describe exported
observations, not independent sensor samples or a current sensor calibration.

v004 selected 8 counts from the calibration's Part Throttle TPS Enable and
the relative idle reading. **If ECM 32731 compares absolute TPS**, 8 remains
well below the historical closed-throttle signal and would still permit a
TPS-based open-loop request. That is the working hypothesis, not a proven
internal comparator definition. Official documentation identifies a TPS/RPM
open-loop threshold but does not establish the absolute/relative choice for
this controller. [HP Tuners Ford loop reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm)

This test uses **200 counts**, approximately 16.18 above the largest historical
closed-throttle absolute reading. This is a diagnostic trial boundary derived
from this car's recording, not a universal tuning value or an established
off-idle enrichment threshold. Current raw TPS readings are intermittent;
the owner reports channels can eventually populate. Blank values are missing
observations, not automatically unsupported channels or failed sensors.

## Exact difference from v004

| RPM breakpoint | v004 TPS threshold | v005 TPS threshold |
| ---: | ---: | ---: |
| 0 | 8.00 | **200.00** |
| 1,500 | 8.00 | **200.00** |
| 2,000 | 0.00 | 0.00 |
| 2,500 | 0.00 | 0.00 |
| 5,500 | 0.00 | 0.00 |
| 6,500 | 0.00 | 0.00 |
| 16,384 | 0.00 | 0.00 |

Only **ECM 32731, Open Loop Fuel TPS Thresh vs. RPM**, and appended
Calibration Details Notes differ. Inherited v003/v004 Notes are preserved.

**The 1,500-2,000 RPM interpolation also changes.** Raising this threshold can
postpone TPS-requested open-loop enrichment at low RPM and under throttle.
This is not an idle-state-only gate. No throttle exercises, road use or boost
testing are part of this candidate's scope. Untouched higher cells do not
establish safe transitions.

## Retained settings and review

Directly reopening v004 confirmed CL O2 sensor temperature 520 F and all three
closed-loop startup delays 254 s. OL/CL hot/cold start ECT boundaries read
150/56 F. ECM 32720 Open Loop Decel Load vs. RPM reads 0.13 at every row;
historical v002 high-resolution load was approximately 0.205-0.287. These
observations do not prove every remaining gate is satisfied in the current
session. No delay, O2-temperature or deceleration-load edit is bundled here.

Also retained: LTFT Disabled; injector pressure compensation Enabled; injector,
MAF, base fueling and spark settings; 1,100 RPM idle setpoints; diagnostics;
SCG-1 settings; and the temporary 195/190 F high-speed fan pathway. The fan
voltage/RPM disturbance and wiring repair remain unresolved. After proper
fan resistor/wiring repair, restore 225/215 F high-speed thresholds in a new
revision while preserving unrelated changes.

## Saved-file verification

- All six earlier calibration files still match their cataloged sizes/hashes.
- Saved v005 was reopened directly from disk.
- All seven saved rows were checked: two 200.00 values and five 0.00 values.
- Editor comparison against v004 lists only Notes and the ECM 32731 table.
- Saved Notes were inspected; inherited temporary-fan and v004 history remain.
- Size: **218,621 bytes**.
- SHA-256: `D79A559CC0DC9A9DE8756FC7CA5F7AB89584627071A6A6E615E51AAE42FF6ED6`.
- No ECU write or controller readback was performed. File verification does
  not establish stable write power, the ECU's installed file or engine safety.

## Owner's stationary test

Use the exact candidate above with the correct controller, stable write power
and Editor's required ignition/engine state. The owner performs the write.
After restart, keep the car stationary and throttle untouched. Record Scanner
from restart through fully warm idle beyond the retained 254-second startup
gate, approximately 6-8 minutes total or longer if coolant is not yet warm.

Watch SCG-1 measured mixture. MPVI4 alone can answer the gate-state question,
but recorded wideband is required before accepting mixture quality or making
fueling corrections; use LogWorks too if assessing those outcomes. Keep fuel
and water/meth state documented. Stop if mixture/idle deteriorates or cooling/
electrical behavior is abnormal. Do not extend the test to driving or boost.

Capture OL Active/Conditions/FMEM, CL Ready/Active/O2Fault, O2 B1 Fail,
fuel source, absolute and relative TPS when they populate, O2 voltage,
commanded lambda, STFT if it populates, ECT/IAT, RPM/target, idle-air duty/STIT,
spark and voltage. Observe channels during acquisition and check the saved
export; a late-populating channel may have only partial coverage. Runtime ID
2131 caps at 255, so use elapsed log time after that point.

First question: do OL Conditions/Active clear and CL Active become Yes?
A flag transition alone is not tune acceptance. If no transition occurs,
record it and revisit comparator scaling and other gates rather than stacking
unrelated edits. Immediate calibration rollback is
[v004](v004-idle-closed-loop-entry-test.hpt); that parent itself did not fix
closed-loop entry. v003 remains the earlier documented rollback baseline.

Save HPL and all-channel CSV to a fresh v005 session directory. If recording
LogWorks, save native LOG and CSV separately and derive that session's timing;
do not carry forward prior offsets.
