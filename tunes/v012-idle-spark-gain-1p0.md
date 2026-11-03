# v012: larger idle spark-gain experiment

**Later outcome,2026-10-29:** an owner-reported stationary stall is supported by
[VCM and recovered SCG evidence](../reports/2026-10-29-v012-stall-review.md).
The run is labeledv012 from carried-forward owner confirmation, not ECU readback.
This meets the trial failure criterion. Owner subsequently confirms v010 also
stalled occasionally without captured evidence. The initial rollback suggestion
is withdrawn; see [revised diagnosis](../docs/post-stall-comparison.md).
No gain regression established; no rollback flash confirmed.

Candidate: [v012-idle-spark-gain-1p0.hpt](v012-idle-spark-gain-1p0.hpt).
Parent and earlier rollback: [v010](v010-idle-spark-gain-1p5.hpt).

The owner proposed a larger step before flashing the prepared v011. This file
was therefore made directly from v010. [v011 at 1.250](v011-idle-spark-gain-1p25.hpt)
is preserved as an unflashed alternative, not used as the parent.

**Owner-confirmed installed and tested on2026-10-28.** The
[fan/recovery recording](../reports/2026-10-28-v012-stability-review.md) supports
retaining900RPM/gain1.000 as the working stability baseline. It does not finish
post-drive or boost validation. No agent ECU write/readback was performed.

The owner now prioritizes stability and drivability at900RPM. The875RPM draft
was withdrawn unflashed, and no v013 is selected. See the
[current roadmap](../docs/stability-and-drivability-roadmap.md).

| Change | v010 | v012 |
| --- | ---: | ---: |
| ECM 47996 Idle Spark Proportional Gain | 1.500 | **1.000** |
| Calibration Notes | Prior history | Prior history plus this trial |

This is a 33.3% reduction from the installed gain and half the original 2.000.
It is an experimental perturbation, not a demonstrated optimum. The aim is to
test whether less aggressive proportional correction reduces the remaining
idle dip/overshoot cycle seen in the [v010 drive](../reports/2026-10-27-v010-drive-review.md).
Lower gain can also weaken disturbance rejection or slow recovery; a smoother
spark trace alone is not evidence of success.

Both idle targets remain 900 RPM, and idle spark minimum remains −6°. MBT,
borderline, torque controls, base airflow, adaptation, dashpot, startup,
fuel/injector/pressure conversion, fan and SCG settings are unchanged. The
planned OEM pressure-sensor installation and flat-40-psi calibration remain
separate unresolved work.

## Verification

- Saved separately through VCM Editor, then reopened from disk.
- Gain 1.000, idle spark minimum −6.00 and both 900-RPM targets verified.
- Saved Notes preserve the full v010 prefix and append this experiment.
- Exact-v010 comparison lists only Idle Spark Proportional Gain and Notes.
- All 12 earlier calibration hashes and sizes remain unchanged.

Size: **230,685 bytes**.
SHA-256: `77EDEBF355AB432BEB56C08BF3041E97C155FDAF2FC446BB3A30CA461F341082`.

## Stationary comparison first

The owner performs any write after verifying the correct file/controller and
stable write conditions. The agent has not initiated an ECU write.

Record hot restart and 5–6 minutes of warm stationary idle with consistent
accessories and no throttle blips. Include a natural fan cycle and at least
60 seconds of recovery if reached. Stop rather than repeatedly reproduce
near-stalls. Compare temperature/load-matched minimum RPM, dip duration,
overshoot, hunting, recovery, spark/source changes, IAC, voltage and wideband.

Revert to v010 if dips deepen, near-stalling returns, recovery slows or hunting
increases. If it is merely different without a clear improvement, retain v010;
do not continue reducing gain automatically. v011 remains available for a
smaller separate comparison. No road or boost acceptance follows from making
this file, and the change cannot compensate for unmeasured fuel-pressure faults.
