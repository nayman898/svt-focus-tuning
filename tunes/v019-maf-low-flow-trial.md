# v019: bounded low-flow MAF trial

**Prepared, saved, reopened and compared. Not flashed or tested.**

Candidate: [v019-maf-low-flow-trial.hpt](v019-maf-low-flow-trial.hpt).
Parent and rollback: [v018-dfco-recovery-diagnostics.hpt](v018-dfco-recovery-diagnostics.hpt).

Only ECM12163 MAF Airflow vs.Voltage and revision Notes changed. Nine cells
between actual0.400 and0.699V are reduced approximately3.72–4.80%. All voltage
breakpoints and the other21 cells are exactly unchanged after save/reopen,
including0V,0.379V and0.898V/up. This is a small relative experiment, **not** a
complete manufacturer calibration or a resolution of the Editor unit-label issue.

## Exact scope

| Voltage (rounded for reading) | Relative change |
| --- | ---: |
|0.400|−4.80%|
|0.439|−4.80%|
|0.479|−4.80%|
|0.500|−4.80%|
|0.529|−4.30%|
|0.540|−3.83%|
|0.600|−4.80%|
|0.649|−3.72%|
|0.699|−4.80%|

The full-precision parent copy revealed a shallow rise, not an exact zero-slope
plateau: the0.500/0.529 numeric equivalents were3.825064/3.833398. Rounded
inventory cells both displayed3.8. The candidate equivalents are3.641461/3.668473.
These equivalents are for comparing the supported g/s-scale interpretation;
the Editor's unit label remains disputed. No7.94x conversion was applied.

The shape target comes from PMAS's dedicated3ProTubeII worksheet, validated
against its cached values. The formula takes25% of the reference-to-parent
relative difference, with a linear weight taper from the0.649 to0.898V axes,
and caps reduction at4.8% (leaving margin under5%). Cells below the reference
range are retained. This chosen step is an experiment, not a calculated optimum.

Edits preserve the existing calibration scale: full-precision Editor clipboard
values in its currentlb/min display were multiplied by dimensionless factors.
No absolute PMAS unit column was blindly imported. The manufacturer comparison
uses the g/s-equivalent numeric interpretation supported by60.12lb/hr high slope,
63lb/hr low slope, standard air charge and logs. Exact housing revision/serial
flow-sheet and software-definition questions remain open.

[Full-precision requested delta](../reports/2026-10-30-v019-maf-delta.csv) and
[saved-file delta verification](../reports/calibration-inventory/v019/delta.json)
record all points. Higher-flow cells are retained, not newly validated or approved.

## Retained settings and limits

No injector, pressure, MAF-filter, idle950RPM, spark/gain/floor, dashpot, cam,
fan, thermal or other protection change. v018DFCO1000exit andP0132MIL reporting
remain. Adjusting MAF can affect inferred load/air calculations as well as fuel;
closed-loop correction near stoichiometry does not prove those models are correct.

Size:244445bytes. SHA-256:
`C2EDAC9A76F9501A827A7DEF30D4A65C52A62B03D9DE4B6BC08F453E8755CFF5`.

Verified after reopening: same30 voltage points, exactly nine changed flow cells,
all reductions below5%, monotonic curve, and all other values exactly retained
in the full-precision clipboard comparison. Whole-file Editor comparison against
exactv018 lists only MAFtable and Notes; complete parentNotes prefix retained.
All19 earlier cataloged tune identities remain unchanged. No agentECUwrite/readback.

## First test

Owner handles flashing. Use unchanged hardware/regulator/accessories and label
the paired recordingv019-2A with the existing Stage2A profile. This is a parked
idle trial first; no higher-load/boost test until its result is reviewed.

After warm closed-loop operation settles, capture60–90s with throttle untouched
and A/C/defrost/blower off. Annotate any radiator-fan transition. Compare rawMAF,
calculatedMAF, STFT, lambda, STIT/IAC and target-relative RPM dips/rebounds with
v018. Do not require another fan cycle or repeated identical baseline.

A few percentage points of additional fuel correction may occur because the
MAF estimate was reduced. Improved RPM behavior must not come with sustained
mixture error, escalating trim, hunting or worse recovery. Stop early for
persistent lean running or worsening stumble/stall and revert exactv018. Brief
wideband spikes alone need context; do not interpret an instantaneous reading
as a complete fuel diagnosis. Existing startup O2-readiness problems remain
separate and are not claimed fixed by this MAF change.

If this experiment fails, revert rather than accumulate another change. If it
helps, retain the evidence and resolve absolute reference/definition issues
before extending correction into cruise or higher-flow cells. No new injector
or high-load tuning values are derived from this trial.
