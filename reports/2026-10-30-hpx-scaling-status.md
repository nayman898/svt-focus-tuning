# HPX scaling verification and application status

## Follow-up: injector scaling cross-check

ECM12011 high slope is0.016700000lb/s =60.12lb/hr; low slope12010 is
0.017500000lb/s =63.00lb/hr. These are consistent in scale with the owner-reported
60lb/hr injectors, not a large deliberate reduction. StandardAirCharge44205 is
0.00136lb =0.616886g per cylinder with4cylinders, plausible for the unscaled
2.0L engine. All exposed injector pressure slope/breakpoint multipliers are1.00
and offset multipliers1.0000. No evidence of a compensating approximately7.94x
MAF/injector scaling scheme was found.

This makes the g/s-equivalent numerical interpretation materially better supported
than treating an8x conversion as an equally plausible correction. A proportional
7.94x reduction of a60.12lb/hr high slope would be about7.57lb/hr, which is not
what is present. The prior headline blocker overstated the equality of those
two possibilities. Do not multiply the current MAF curve by7.94.

Editor's unit presentation remains inconsistent, and slope magnitude alone does
not prove the exact injector characterization or every PCM conversion. The
manufacturer comparison should proceed using the supported g/s-equivalent
interpretation, explicitly documenting the UI-label discrepancy. The measured
housing reference and installed-system steady-state corrections still matter;
this does not automatically authorize replacing all voltage regions as a validated
tune. No binary changes were made in this cross-check.

The manufacturer reference has been calculated and checked, but it has **not
been applied to an HPT candidate** because the ECU definition/scaling is unresolved.
The user's authorization covers preparation; it does not make an unknown unit
conversion correct. No claim is made that this task is fully resolved.

## Verified work

- Used the official PMASHPX2014.2 workbook's dedicatedPMAS3ProTubeII sheet,
  rather than the generic3.000inch tube assumption. The sheet's2.8inch input and
  area treatment reproduce all30cached outputs within6e-11g/s. No macros ran.
- Generated [reference values at the existing voltage points](2026-10-30-hpx-protube-reference.csv)
  in g/s,kg/h,lb/h andlb/min. The0V endpoint is outside the supplied reference
  range and is flagged, not extrapolated. [Assumptions and verification](2026-10-30-hpx-protube-reference.json)
  are stored separately. The housing/sensor revision still needs its exact
  flow sheet for authoritative application confirmation.
- Reopened untouchedv018 after the display-unit change. At0.60V, Editor shows
  approximately0.082lb/min (original4.9lb/h), while its parameter description
  explicitly says airflow(g/sec). This discrepancy is reproducible, not merely
  a stale initial label.
- The logged flow/voltage relationship is inconsistent with taking thelb/h
  numeric value literally. It does not independently prove which conversion
  is wrong; corrections, Scanner definitions and strategy scaling require review.

At0.60V, the dedicated PMAS reference is3.81661g/s=30.2910lb/h=0.50485lb/min.
Entering30.291 where the current display says4.9 would be a6.18-fold change.
Entering3.81661 instead would be a22% reduction in the existing numeric value.
Those are radically different interventions. Neither is justified solely by
the conflicting label/help/log observations, and neither was written.

## Exact remaining blocker

[HP Tuners definition question](../docs/hpt-maf-scaling-question.md) is prepared,
not submitted. It asks for ECM12163engineering conversion, Scanner2300/2302
semantics and any coupled MAF/injector/load scaling on UJAHAS3. PMAS supplies
serial-specific flow sheets via its [transfer-function page](https://pmas-maf.com/transfer-function/).
No external message was sent. A vendor-confirmed conversion or independent,
validated strategy mapping is needed before declaring a replacement correct.

There is no v019flashable file. The CSV is reference-only and explicitly marked
as such; do not import it by guessing the unit column. Existing19cataloged tune
binaries remain unchanged. No engine run, ECU write or code clearing occurred.
