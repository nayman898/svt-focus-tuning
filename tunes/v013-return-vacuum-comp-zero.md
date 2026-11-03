# v013: return-system vacuum-compensation diagnostic

Candidate: [v013-return-vacuum-comp-zero.hpt](v013-return-vacuum-comp-zero.hpt).
Exact parent and rollback: [v012](v012-idle-spark-gain-1p0.hpt).

**Prepared, saved, reopened and compared. Not flashed, engine-tested or accepted.**
Owner requested a new diagnostic iteration after the read-only audit. This is
one calibration change plus Notes; it is not a complete fuel-system conversion.

| Parameter | v012 | v013 |
| --- | ---: | ---: |
| ECM6950 Manifold Vacuum Multiplier |0.484 |**0.000** |
| Calibration Notes | Parent history | Full parent history plus test scope |

The matching installed Editor help says zero for a return-style conversion.
Owner confirms a1:1 manifold-referenced Aeromotive return regulator. That is a
specific documented basis for this diagnostic value, not a replacement value
derived from trim averages. See the [audit](../reports/2026-10-29-v012-calibration-audit.md).

## Hypothesis and unresolved assumptions

If the inherited vacuum-compensation path is inconsistent with the physical
return system, removing that term may change reported mixture/trim response
and reduce vacuum-correlated torque disturbances. Its exact effective path and
the direction/magnitude of change are not established. A null result may mean
it is inactive or not a dominant cause; improvement alone does not prove the
entire fuel model is correct.

Both targets remain900RPM, gain1.000 and idle spark floor-6degrees. Airflow,
runtime/adaptation, VCT/IMRC, MBT/borderline/torque controls, MAF and injector
tables, fuel-pressure transfer/reference/compensation, fan and SCG settings are
unchanged. Regulator remains at the latest owner-set43psi engine-off setting.
The software still has inherited flat40psi pressure transfer,40psi injector
reference and enabled injector pressure compensation. These remain unresolved
assumptions, deliberately retained to isolate this scalar's effect. The SCT
BEF has not yielded a decoded stock comparison.

**The parameter can affect behavior beyond idle.** Restricting the first test
to stationary operation does not make this an idle-only calibration edit.
No road/boost/power acceptance is implied. Water/meth remains OFF; SCG RPM wire
stays disconnected. Do not combine this with pressure, gain or airflow changes.

## Saved-file verification

- Created a separate file through Editor Save As from exact v012.
- Saved candidate reopened from disk; multiplier reads0.000.
- Both900RPM targets, gain1.000 and idle spark floor-6 verified after reopening.
- Saved Notes retain the complete parent prefix and append this trial.
- Editor comparison against exact v012 lists only Manifold Vacuum Multiplier
  and Notes. No unexpected calibration difference was listed.
- All13 earlier cataloged tune hashes and sizes remain unchanged.

Size: **233,629bytes**.
SHA-256: `78AAD3DC86BE89835C333BC95EF5CE1359DD5B4CAAD2645032C1A64F49505B70`.
Private verification captures are retained under `.local/v013-*`.

## Owner write and first test

Owner verifies exact file/controller, stable write power and the engine-off/
ignition state required by Editor, and performs any ECU write. Those live
conditions have not been verified by the file comparison. No agent write.
Confirm the actual flashed filename before attributing a new log to v013.

Use the [v013 stationary test card](../docs/v013-stationary-test.md). Initial
scope is a supervised three-minute parked capture with valid wideband and
pressure-gauge video, consistent accessories and no throttle/load steps.
Check valid core data and usable fuel feedback before extending operation.
Separate startup/temperature effects from settled comparison windows.

Stop for worsening roughness, persistent unexplained mixture departure, severe
stumble or stall; do not wait for a fan cycle or repeatedly reproduce failure.
Stop the engine if deteriorating, then stop/export both recorders. A failed
trial reverts to exact v012 under appropriate owner-controlled write conditions;
v012 itself has unresolved stalling and is not a guaranteed cure.

If initial operation is satisfactory, compare matched conditions with the
latest unchanged-v012/43psi stationary run, then decide whether to keep the
candidate provisional or revert. Available STFT and command exports are linked;
use valid wideband, pressure, loop/fuel state, RPM recovery and air/spark together.
No keep decision from smooth timing or averaged lambda alone.


## Initial v013 outcome, 2026-10-29

Both captures are stopped and saved. STFT was blank in the first capture and
populated after an owner recording-only restart using the same13-field profile.
A stumble in the manual warm recording includes brief zero-RPM/cranking-state
reports with no starter use; v013 remains unaccepted. See the
[initial review](../reports/2026-10-29-v013-first-review.md).
