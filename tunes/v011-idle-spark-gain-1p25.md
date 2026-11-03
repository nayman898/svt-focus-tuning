# v011: smaller idle spark-gain step

Candidate: [v011-idle-spark-gain-1p25.hpt](v011-idle-spark-gain-1p25.hpt).
Exact parent and rollback: [v010](v010-idle-spark-gain-1p5.hpt), explicitly
confirmed installed by the owner. **Prepared and verified; not flashed or
engine-tested.**

| Parameter | v010 | v011 |
| --- | ---: | ---: |
| ECM47996 Idle Spark Proportional Gain | 1.500 | **1.250** |
| Calibration Notes | Prior history | Prior history plus trial explanation |

Both targets remain900RPM and idle spark minimum stays−6deg. MBT/borderline,
torque/oscillation/TipIn controls, dashpot, base airflow/adaptation, fueling,
injector/pressure conversion, fans and SCG settings are unchanged.

The [v010 drive review](../reports/2026-10-27-v010-drive-review.md) shows a
737.25RPM minimum with quick recovery and owner-reported smooth cruise and
acceleration. The16.7% reduction is a smaller diagnostic step to test remaining
idle correction/overshoot. It is not a validated optimum; a lower gain can
also worsen dip depth or recovery. Pressure uncertainty is not repaired by it.

## Verification

Saved through Editor as a separate file, reopened and checked: gain1.250,
minimum−6.00, P/N and Drive900RPM, complete parent Notes prefix preserved.
Comparison against exact v010 lists only Idle Spark Proportional Gain and
Notes. All11 prior binaries retain their cataloged hashes and sizes.

Size: **230,397 bytes**.
SHA-256: `703A5B9E7061BE733B43665DF1F30F44E2E4CA29F51BD3B07D9272A5BA20A9C3`.

## First test

The owner confirms correct file/controller and stable write conditions before
performing any write. The agent has not flashed this file. Begin with paired
logging from hot restart through5–6minutes of stationary warm idle, untouched
throttle and consistent accessories. Include a natural fan cycle and60seconds
afterward if reached; do not keep reproducing near-stalls for more samples.

Compare temperature/load-matched dip depth/duration, overshoot, recovery time,
spark/source transitions, IAC, voltage and valid wideband readings. Stop/revert
to v010 if near-stalling recurs, recovery slows or hunting worsens. Smoother
spark alone is not success. If the smaller gain does not help, retain v010 and
revisit airflow/adaptation and measured pressure instead of repeatedly lowering
gain. No blanket road or boost acceptance follows from this file preparation.
