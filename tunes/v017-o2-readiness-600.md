# v017: later O2 feedback-entry trial

**Test outcome:** [v017-labeled capture reviewed](../reports/2026-10-30-v017-entry-review.md).
The rich-entry excursion remains (+25%trim, lambda0.723). Not accepted as a fix;
recommend rollback to exactv016. No agent write or confirmed owner rollback.
The preparation and original test plan below are retained as history.

**Prepared, saved, reopened and compared; not flashed or tested.**

Candidate: [v017-o2-readiness-600.hpt](v017-o2-readiness-600.hpt).
Parent and rollback: [v016-idle-margin-950.hpt](v016-idle-margin-950.hpt).

Only calibration change: **ECM12115 Closed Loop O2 Sensor Temp520 ->600F**.
This threshold uses calculated O2 temperature, not coolant temperature. The
950RPM idle targets remain. Fuel maps, O2 bias, heater commands, delay scalars,
spark/air controls, dashpot, fan settings and diagnostics are unchanged.

Saved/reopened threshold600.00F verified. Full parent Notes prefix retained.
Editor comparison against exactv016 lists only Notes and Closed Loop O2 Sensor
Temp under Engine/Fuel/Oxygen Sensors/Feedback. All17 older binaries verified
unchanged. Size241517bytes; SHA-256:
`9597BAB2DB9DEB063298C7814F8B9930C530DBDB3FE114D80F8EE44B6463E7CE`.

## Evidence and limitation

In the [v016 recording](../reports/2026-10-30-v016-first-start-review.md), CL
entered while the narrowband remained nearzero; trim reached+25% while aligned
wideband reachedlambda0.722. This is a specific entry/readiness problem to test,
not enough evidence to invent a fuel-PID gain. Raising the calculated-temperature
threshold is intended to delay entry.600F is an experimental step; actual delay
is unknown. It does not prove the sensor/heater is sound or correct a physical
fault. Warm dips and stop-related hanging idle remain separate issues.

## One discriminating test

Owner handles flashing; no agent write/readback. Keep sensor, fuel pressure,
accessories and other calibration unchanged. This is a **parked diagnostic**;
do not use it for a drive or boost test before reviewing its result.

1. Start paired recording before engine start, labelv017, and verify the actual
   saved VCM start if Scanner needs a recording restart. Use similar starting
   ECT to the v016 test where practical, and record it. Do not claim a controlled
   delay comparison across very different startup temperatures.
2. Watch narrowband response, CLReady/Active, STFT and wideband. Success means
   entry occurs with responsive O2 feedback, the initial positive-trim/rich
   excursion is reduced, and closed loop still becomes active normally afterward.
3. Once entry and approximately60–90s afterward are captured, stop/export.
   No fan cycle or repeated accessory sequence is needed for this experiment.
4. Stop earlier for stumbling or sustained worsening mixture. If the sensor
   appears responsive but CL remains absent for about60s, stop and inspect the
   result rather than prolong open-loop running. That is a test stop rule, not
   a verified controller timeout. Revert exactv016 if behavior deteriorates or
   entry remains unsuitable; do not keep escalating the threshold blindly.

No cold-start cure, sensor compatibility, road readiness or stable-driveability
claim is made. PriorP1132 remains historically confirmed; no fresh DTC read or
clearing was performed in this preparation.
