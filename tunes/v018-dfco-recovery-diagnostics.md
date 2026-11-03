# v018: DFCO recovery and diagnostic coverage

**Prepared, saved, reopened and verified. Not flashed or tested.**

Candidate: [v018-dfco-recovery-diagnostics.hpt](v018-dfco-recovery-diagnostics.hpt).
Exact parent and rollback: [v016-idle-margin-950.hpt](v016-idle-margin-950.hpt).

| Parameter | v016 | v018 | Purpose |
| --- | --- | --- | --- |
| ECM2291 Maximum RPM to Disable DFCO |750 RPM|1000 RPM|Restore fuel earlier when active deceleration cutoff approaches idle |
| ECM50 Master DTC List: P0132 |No Error Reported|MIL Light|Restore upstream O2 high-voltage diagnostic reporting |
| Notes |Parent history|History plus v018 scope|Document the experiment |

This combines one behavior trial with a diagnostic-reporting correction at the
owner's request. A newly reported fault must be investigated rather than suppressed.
Retained:950RPM P/N and Drive targets, DFCO entry1200RPM, speed gates35/12mph,
v016 O2-entry threshold520F, gain1.000, idle spark floor−6 and all other parent
settings. The failed v017600F threshold is not inherited. All other162 DTC rows
are unchanged. Dashpot, base airflow, spark limits, fuel/pressure models, cams,
fan settings and protections are not altered.

## Verification

Created through Editor Save As from exactv016. Saved file reopened; scalar reads
confirm1000exit/1200entry/950idle/520FO2threshold. All163 DTC rows compared before
and after, then again after reopening: onlyP0132 mode changed. Saved Notes retain
the full parent prefix. Whole-file Editor comparison lists only DFCOexit, Master
DTC List and Notes. All18 previous tune hashes and lengths remain unchanged.

Size:241645bytes. SHA-256:
`2E4E3711B2E6AFA5A343D54CBA9331CB48FB6B3774882CB0446B569ACCD9A082`.

## What to test

The1000RPM exit is an experimental setting, not a proven optimum. It retains
200RPM entry/exit separation and nominal50RPM margin above idle. It matters only
while DFCO is active and another condition has not already restored fuel. The
12mph speed exit may make some decelerations unaffected.

Owner handles flashing with the correct vehicle/file and stable write conditions.
No agent ECU write/readback occurred. Keep sensor, regulator and other hardware
unchanged. Meth remainsOFF; SCGpurpleRPM stays disconnected.

After installation, confirm ordinary idle and inspect actual fault reporting.
Do not repeat a long stationary baseline to judge DFCO: its35mph entry gate
cannot activate parked. Require acceptable stall/recovery behavior before a
controlled moving test; this candidate itself does not establish road readiness.

The relevant test records speed,RPM,TPS/state,fuel-source/cutoff evidence and
wideband during suitable deceleration, with clutch/neutral actions noted. Check
that fuel restoration and RPM recovery improve without abrupt torque return or
cutoff re-entry cycling. No actualDFCO event means inconclusive, not passed.
Worsening dip/stall or return behavior means stop/review and revert exactv016.
No boost test is part of this trial. A newP0132 is evidence to investigate.

This does not directly fix the stationary1100RPM hang or warm idle-air/spark
oscillation. Those conditional recommendations in the
[correction plan](../docs/calibration-correction-plan.md) remain separate.

## Reference update

[v018 delta](../reports/calibration-inventory/v018/delta.json) records the verified
changes; the fullv017 inventory remains immutable. Relative to that inventory,
v018 has12115=520F,2291=1000RPM,P0132=MILLight and differentNotes. This is derived
from verified saved-file comparisons, not a fresh342-entry capture or ECU readback.
