# v015 — restore v013 closed-loop eligibility

**Prepared, saved, reopened and compared; not flashed or tested.**
[Candidate](v015-restore-closed-loop.hpt).

This is a restoration after the owner's severe v014 drivability regression,
not a new idle-stall remedy. See the [trip review](../reports/2026-10-29-v014-drive-review.md).

## Exact relationship

Built from a byte-identical copy of
[v013-return-vacuum-comp-zero.hpt](v013-return-vacuum-comp-zero.hpt), then
appended Notes through VCM Editor. Saved-file comparison against exactv013
contains **only Notes**. The full v013 Notes prefix was verified after reopening.

Relative to v014, ECM32731 Open Loop Fuel TPS Thresh at0 and1500RPM restores
0.00 to200.00AD counts. Other five rows remain0.00. This also restores
v013's1500–2000RPM interpolation; it does not force closed loop in every mode.

Retains all v013 settings:900RPM targets, gain1.000, idlefloor-6,
manifold-vacuum multiplier0, MAF/injector/pressure model, fuel and airflow
tables, runtime corrections, O2 gates/bias/learning, VCT/IMRC, spark/torque and
fans. No extra reset, DTC clearing or controller-setting change was performed.

Size: **236,525bytes**.
SHA-256: **9D3C4FF9CD68D24665957CC6FDB310C51B246E8DD3D0F439A0E33D2EFA936EFD**.

## Owner handoff

Owner performs any write after confirming exact file/controller, stable write
power and the ignition/engine conditions required by Editor. Offline verification
does not verify those live conditions. No agent flash/readback.

After installation, confirm actual revision and verify parked loop state,
mixture and idle before additional testing. Preserve pending P0320 and existing
logs. No extra timing/fuel adjustment or acceleration test is requested.

Exactv013 is the calibration-equivalent reference if needed. Returning to the
failed v014 diagnostic is not recommended. v013 itself had unresolved stalls;
v015 therefore is not an established stall cure or road/boost acceptance.
