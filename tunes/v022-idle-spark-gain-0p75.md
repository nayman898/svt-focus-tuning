# v022 — idle spark response experiment

**Tested and rejected for adoption2026-11-02 after owner-reported newoscillation.**
Latewindowminimum831.75/SD33.73, recovery/reboundworsenedrelative toearlierv022window;
conditions/timepathsconfoundexactgaincausality. Returnexactv021recommended, notconfirmed.
See [trial review](../reports/2026-11-02-v022-spark-response-review.md).
Original preparation and testcriteria below are preserved. Exactparent/rollback and ongoing
baseline: [v021](v021-fuel-pressure-feedback.hpt). Candidate:
[v022-idle-spark-gain-0p75.hpt](v022-idle-spark-gain-0p75.hpt).
Size250669bytes; SHA256
`577F775782A98705C2F3A6205BBC32BF7461238967255CCD1105303A0C7DD29F`.

## Change and question

OnlyECM47996 Idle Spark Proportional Gain **1.000->0.750**, a25%coefficient
reduction, plusNotes. Retain pressuretransferv021,950targets, originalv019baseair,
sparkfloor−6, nominalidlesparktables, MAF/fuel/injector/pressure/pump, dashpot,
VCT/fans/protections. The rejectedv020aircut is not inherited.

The [v021review](../reports/2026-11-02-v021-baseline-review.md) shows continued
warmdips despite steady45psi differential and meanlambda~1.01. This experiment
tests whether sparkfeedback reinforces rebound versus providing needed recovery;
it does not prove badIAC, excesstotalgain or incorrect fuelcalibration. Earlier
gain reductions helped ownerperception but did not eliminate stumbles; this
smaller furtherstep needs its own acceptance, not extrapolated success.

MatchingEditorhelp for47996 says highergain produces moreaggressiveidle-spark
correction and lowergain can help large timingchanges. This is a proportional
coefficient, not fixeddegrees.25%lesscoefficient does notmean25%less actualspark
or25%fewerstumbles, particularly whenclipping/otherpaths override it.

| Result | Decision |
| --- | --- |
| Smaller spark excursions at comparableRPMerror, lessrebound/fewershallowerdips, recovery maintained | Supports provisionalretention; notproofrootcause |
| Calmer timing butdeeper/longerRPMdrops orslowerrecovery | Reject; correction was useful, returnexactv021 |
| Calmer timing butsameRPMcycling | Do not keepreducinggain; investigate remainingdisturbance/airresponse |
| No measurable response | Check activepath, sampling/comparableerror andlimits; noautomatic hardwarediagnosis |

## Test

Ownerflashes; noagentECUwrite/readback. Stationarysupervisedwarm60–90s at about
180–188F, no combinedaccessory/throttlechanges and nofanwait. PairSCGwithVCM,
label`v022-spark075`. Keep fuelpressure/regulator unchanged. Stop/revertv021
forworseningdipdepth/duration, nearstall/stall, hunting orrecovery. Endforpersistent
rough/richfallback rather thanrunningthrough it toreachthewarmwindow.

Loaded [Spark Response Trial18](../profiles/2004%20Focus%20SVT%20-%20Spark%20Response%20Trial.Channels.xml)
keeps rawpressure6507, RPM/desired, ECT/TPS, spark/source, IAC/STIT/LTIT, trims/O2,
CL/FMEm/voltage/MAF/rawMAF. Removesconvertedpressure6502andruntime2131 fromprior20.
Allretaineddefinitions match; saved-back verified. Runtimecoveragepending.
VerifydesiredRPM/TPS populate beforeactualcomparison. Ifnot, preserveadmission
capture and fixcoverage; don'tinventcommanderror ordiscardstartup byrestarting.

Compare actualdipfrequency/depth/duration, reboundpeak andtime-to-returntoband,
andtiming atsimilarRPMerror. Usebothpressureandmixturetoexcludeobviousdifferent
conditions. Adaptationafterflashmaydiffer; separate settling. Noreset toforcefit.
Ifneeded a returntov021is theconfirmingA/B step, notalongunchangedrepeat.

## Verification

EditorSaveAsfromexactv021; gain0.750/floor−6 verifiedaftersave/reopen. Wholefile
comparisononly47996andNotes; fullparentNotesprefixretained. All22olderidentities
checked. No engine/meth/SCGsettings changes. No driving/boostvalidation.
