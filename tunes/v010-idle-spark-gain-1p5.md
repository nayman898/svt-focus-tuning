# v010: stationary idle spark-gain experiment

**Owner correction,2026-10-29:** v010 also stalled occasionally, uncaptured.
The saved clip does not establish stall-free operation. Owner reports later
spark changes improved steadiness between random stumbles. See the
[revised diagnosis](../docs/post-stall-comparison.md); no gain regression established.

Candidate: [v010-idle-spark-gain-1p5.hpt](v010-idle-spark-gain-1p5.hpt).
Exact parent: owner-confirmed installed [v009](v009-idle-900.hpt).
Prepared, saved, reopened and compared. The owner now explicitly confirms this
exact file installed for the [cruise/drive/idle log](../reports/2026-10-27-v010-drive-review.md),
reporting good cruise and normal acceleration with residual idle dips. The
737.25RPM minimum is improved observationally but not complete idle or boost
acceptance. No agent ECU write/readback. This trial leaves the fuel-system
conversion unchanged. v010 is rollback for the next v011 gain experiment.

## One-variable change

| Parameter | v009 | v010 |
| --- | ---: | ---: |
| ECM47996 Idle Spark Proportional Gain | 2.000 | **1.500** |
| Calibration Details Notes | Prior history | Prior history plus trial explanation |

The25% reduction is a deliberately bounded experimental step, not a documented
optimum. Editor describes higher gain as making more aggressive spark changes
and suggests lowering it when idle timing swings are large. The
[cross-session diagnosis](../reports/2026-10-27-v009-cross-session-diagnosis.md)
and [handoff review](../reports/2026-10-27-v009-idle-handoff-review.md) show large
retard/advance swings, repeated source switching and overshoot. They support
testing this hypothesis but do not establish gain as the root cause.

Hypothesis: less aggressive proportional spark correction reduces overshoot
and repeated excursions into the idle minimum clip without making load recovery
slower or deeper. Alternative outcome: the gain was compensating for another
problem, and reducing it worsens recovery. Lower gain does not guarantee that
Base/MBT switching or the near-stalls disappear.

Both targets remain900RPM and idle spark minimum remains−6degrees. MBT and
borderline tables, base airflow, adaptation settings, dashpot, startup, fueling,
injector characterization, pressure transfer/compensation, fan thresholds and
SCG settings are retained. No simultaneous target or airflow reduction is made.

## Saved-file verification

- Created separately in VCM Editor through Save As from exact v009.
- Reopened saved gain1.500 and idle spark minimum−6.00 verified.
- Reopened main P/N and Drive targets both read900RPM.
- Saved Notes retain the complete parent prefix and append the trial scope.
- Editor comparison against v009 lists only Notes and Idle Spark Proportional Gain.
- All10 earlier tune files match their cataloged SHA-256 hashes and byte lengths.

Size: **228,029 bytes**.
SHA-256: `E2A2650F93CD9084BC41353ADAEBE5D69E23AB238F0F9B9A48A382786331BC47`.

## First test and decision

The owner performs any write after confirming the correct file/controller,
stable write power and the state required by Editor. File comparison does not
establish those live conditions; the agent has not initiated an ECU write.

Use paired logging from hot restart through5–6minutes of warm stationary idle,
with consistent accessory and fuel conditions and no throttle blips. If a normal
fan cycle occurs, retain at least60seconds of recovery. Do not extend the test
to repeatedly reproduce near-stalls. Shut down and end the trial if near-stalling
recurs or the response is clearly worse.

Compare temperature/load-matched periods against v009: minimum RPM, duration
below target, overshoot, oscillation, recovery time, spark/source transitions,
IAC, supply and valid wideband readings. Smoother spark alone is not success.
Retain the trial only if actual engine behavior and load recovery improve.
Stationary success is a prerequisite for later drivability evaluation, not
proof of safe short-distance, road or boost operation.

Reverting to v009 reverses this experiment but restores its known near-stall
behavior. v008950 remains the earlier stationary fallback; neither rollback
is represented as a proven cure for the separate driving disturbance.

## Unresolved fuel-pressure work

The inherited ECM7596 transfer still reports40psi for every input. Owner
confirms43psi base/1:1 manifold reference and plans OEM sensor restoration.
Actual dynamic pressure remains unmeasured. This trial does not repair missing
feedback, certify fuel delivery or change injector compensation. Keep that
hardware/calibration integration separate as described in the
[fuel-feedback audit](../docs/fuel-pressure-feedback-review.md).
