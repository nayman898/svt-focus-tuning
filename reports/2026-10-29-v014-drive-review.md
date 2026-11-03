# v014 trip: rejected diagnostic, restore v013 behavior

Owner reports much worse drivability than closed loop: no low-end response,
harder pull-away, and severe loss of power. Treat v014 as a failed drivability
experiment. It was prepared for stationary isolation and never accepted for
road/boost use. Do not continue acceleration testing on it.

Both recorders stopped/exported successfully. Source
paired-20261029-190812-6d5aebc2-v014 is saved with no manifest errors or missing
files. Native HPL/CSV, SCG SQLite backup/CSV and context are preserved privately
under logs/2026-10-29-v014-drive-01. SQLite integrity and finalization passed.
No agent ECU write or rollback was performed.

## What the trip establishes

- VCM has51,725 rows over1.637–1220.790s. CL Active No, CL Ready Yes,
  OL Conditions Yes and FMEM No are present throughout. The initial live blank
  field was not an enduring missing export column. Constant flags alone cannot
  independently establish channel freshness.
- Fuel Source is Power Demand Enrich in49,396rows and Injector Cut in2,329.
  The commanded field still duplicates1-STFT/100. Nonzero exported STFT under
  open loop is not proof of active feedback or an independent fuel correction.
- RPM ranges1003–6043; no zero-RPM event is recorded. There is no sustained
 900RPM parked comparison here. No exported misfire flags/counts does not prove
  normal combustion.
- Spark Source frequently reports Cold Start Emiss. Red. during warm driving.
  Pull-away timing is not uniformly suppressed; source semantics and matched
  earlier conditions need checking before any timing adjustment.
- The changed threshold affects low-RPM open-loop requests and1500–2000RPM
  interpolation. Above2000RPM the threshold rows already matched v013.
  Generalized loss of power cannot all be attributed to a new high-RPM table
  value. Neither a fuel quantity correction nor additional spark is selected.

## Important data limits

Air Load Hi Res is exactly0.4664763808 through119.329s despite substantial
RPM/throttle variation. Exclude that initial interval from load-based diagnosis.
No literal blank/null tokens appear in the export, demonstrating why populated
columns alone do not prove fresh measurements.

VCM gaps:114.445–119.196,160.769–164.420,353.617–354.929 and814.108–817.547s.
SCG has14,745valid rows,183oxygen-state rows,4gap/4disconnect markers and a
stop marker. Preserve invalid states; do not interpret whole-trip lambda
extremes or averages as loaded-engine fueling. Overrun/cutoff and missing
intervals require separate treatment.

Metadata alignment is SCG elapsed = VCM elapsed +2.585349s, provisional.
Reconnects, sensor/exhaust delay and acquisition freshness prevent defensible
pointwise enrichment corrections. SCG reports a peak gauge pressure12.71psi;
full-range pressure scaling and this transient's exact alignment are not
independently validated. This trip is not boost validation. No further
acceleration test is requested.

## v015 restoration

Astra's independent review agrees: reverse the isolation without stacking
another speculative change. [v015](../tunes/v015-restore-closed-loop.md)
restores exactv013 calibration, with new Notes documenting the failed v014
test. Compared with v014, only the two ECM32731 thresholds return0 to200;
compared with exactv013, **only Notes differ**.

This restores the behavior the owner preferred. It does not resolve the
previous idle stalls, P0320, warm mixture drift or upstream O2 readiness.
No declaration of road readiness follows from file equivalence.

After owner installation, verify loop state and measured mixture while parked.
Further work should establish injector pulse width/command semantics, actual
fuel pressure, idle-air/runtime behavior and sensor readiness. No v014-based
MAF/injector/timing correction is justified from this trip alone.
