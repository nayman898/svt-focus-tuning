# v023 — nominal idle spark operating-point trial

Prepared 2026-11-02; subsequently tested in an owner-labeled v023 capture. **Not adopted after an owner-confirmed stall.** Exactparent/rollback and continuing
baseline: [v021](v021-fuel-pressure-feedback.hpt). Candidate:
[v023-idle-spark-10deg.hpt](v023-idle-spark-10deg.hpt).
Size250845bytes; SHA256
`BA0E2CD969743295AD0556C6B5EFED6F5B8419D1FD8912887A1B6C2DE6FBBCAD`.

## Exact changes

| Table | v021 | v023 | Scope |
| --- | ---: | ---: | --- |
| ECM44579 Spark Idle P/N vsECT | 12degrees | 10degrees | All5bodycells |
| ECM44578 Spark Idle InGear vsECT | 12degrees | 10degrees | All5bodycells |

Axes not edited; displayed axisvalues match the inherited capturedtables.
Five fullprecisionbodyvalues copiedfromeachparenttable were12; aftersave/reopen
allfive are10ineach. Existing temperatureaxes include repeated254Fbreakpoints;
do not reinterpret them as a newly designed curve or silently normalize them.
The parentcurve was flat12, candidateflat10 over its entire representedrange.
This is not a warm-only edit; it applies whenever theseidle tablesparticipate.

Nominalidle spark is notfixedfinalspark oramaximumsparkcap. Startupretard,
feedback andotherlimits can override it. This edit doesnot reduce allengine
timing by2degrees or deliberatelycap correctiveadvance at10.
[HP Tuners Ford spark descriptions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_spark_advance.htm)
distinguish theseidletables frommainMBT/borderline andmaximumcoldstartlimits.

Gain47996remains1.000, floor44582remains−6.00; target950, baseair, v021pressure
transfer, MAF/fuel/injector/pump, dashpot/VCT/fans/protections unchanged. v020air
cut andv022gain0.75 are notinherited because thisfile derivesdirectlyfromv021.
Fullv021Notes retained witha v023appendix.

## Hypothesis and measurable results

The [v022review](../reports/2026-11-02-v022-spark-response-review.md) identified
increasingtiming/decreasingair demand asoscillation worsened. This mayreflect
theoperatingpoint changing asstartup compensationexpires; it doesnotprove a
particular tablecauses it. v023tests a smalllower-spark/higher-air operatingpoint
while retainingbaselinefeedbackgain andcorrectiveauthority.

| Observation under comparable warm conditions | Decision |
| --- | --- |
| Timingbias movesdown, air/IACdemand movesup whilemeanRPMmaintained, dips/reboundimprove | Supports provisionalretention oftheoperatingpointchange |
| Operatingpointshifts butdips/recoverydo notimprove | Hypothesis insufficient; do notkeeploweringnominalsparkblindly |
| Noobservablepointshift | Verifyactivepath, limits, comparableconditions andfreshchannels beforeconcludinganything |
| Deeper/longerdips,nearstall/stall,morerhythmichunting,slowrecovery orroughrichrunning | Stop andreturnexactv021 |

No exactIACpercentage or2degreefinaltimingshift ispromised. Calmer timingalone
isnotsuccess; judgeRPMdepth/duration/rate,rebound andmixturetogether. Do not
diagnose a defectiveIAC fromtheoutcome. v021remainsthebaselineuntilreview.

## Test card

Ownerflashes; noagentECUwrite/readback. Startpairedrecordinglabel`v023-idle10`
beforeengine start, accessories/throttle unchanged. ConfirmfreshRPM,desiredRPM,
TPS, spark/IAC/STIT/LTIT, ECT, rawFRP, trims/O2/CL/FMEm andvalidSCGdata.
DesiredRPM/TPS wereblank inpriorv021/v022captures; do notinventtargeterror or
driverstate. The loaded [V023 Idle Spark Trial18](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml)
refreshes both from the native ECUselector at200ms; remaining16definitions are
retained. This configuration is saved-back verified, not yet runtime-validated.
Preserveanyadmission/startupsegment; don'tdiscardsamplestogetfreshfields.

If runningisacceptable, compare60–90s settledwarm atsimilarECTandtimeafterstart,
notECTalone. Markanyfan/accessorychange; nofanwaitrequired. Stopsoonerforadverse
criteria. No adaptivereset/codeclear toforcearesponse. No driving/boostvalidation;
methoff andSCGRPMwire disconnected. Returntoexactv021isrollbackifneeded.

## Verification

EditorSaveAsfromexactv021; saved/reopened10bodyvaluesverified, gain1.000/floor−6
readbackinEditor. WholefilecomparisonlistsonlytwoidlesparktablesandNotes.
FullparentNotesprefixverified; all23olderfileidentitieschecked. Thisverifies
savedfiles, not ECUinstallation orrunningimprovement.
[Machine delta](../reports/calibration-inventory/v023/delta.json).

## Recorded outcome

The [stall review](../reports/2026-11-02-v023-stall-review.md) preserves the trial and its limits. All 18 requested channels populated, including desired RPM/TPS. Exact v021 rollback is recommended, not confirmed. The brief zero-RPM report before coastdown warrants signal/circuit diagnosis; it does not establish a failed crank sensor. No further nominal-spark reduction is justified by this trial.
