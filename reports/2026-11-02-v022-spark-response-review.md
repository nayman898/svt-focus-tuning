# v022: new oscillation, return to v021

Owner confirmedv022written and later reported "getting new oscillation".
Stopped/exported both recorders immediately on that report. Preserve the report
time as an approximate marker, not a verified onset. Recommend exactv021rollback;
not confirmed performed. v021 remains baseline; do not adoptv022 or reduce gain
further from this result. No engine shutdown or ECUwrite/reset by agent.

## Capture quality

Source `paired-20261102-164644-31b89259-v022-spark075`. Saved/noerrors/allfour
files present; SQLiteintegrityok/finalized; natives andCSVs preserved in
[capture](../logs/2026-11-02-v022-spark075-01/). Initial164601attempt timedout
onSCGwarmup and neverstartedVCM; it remains separate and is not partofthisrun.

VCM12551rows1.295–291.441s; one1.458sgap at123.660–125.118.
DesiredRPM andabsoluteTPS are missing again,16/18requestedpopulated. Do not
claim measuredcommanderror or verified25% sparkresponse at matchederror.
Stored950targets are known but not a substitute for the missingcommandPID.
ECT174–176F beforestart; startup around24.280s, then168–194F through run.
MetadataSCGoffset+2.425674s is provisional; exhaust/sensordelay notcorrected.
CLYes110.481s/FMEmNoentirecapture. EarlyCLagainincludes+25%trim andWBmin0.742;
this entryevent is distinct from later normal-mixture oscillation. NoDTCread.

## Change within this run

Both followingwindows areCLactive/FMEmoff, no driver-input validation because
TPSblank. Event definition: sub900RPMgroups separated<=1s. Recovery means first
return to925afterminimum; rebound is maxRPM in thenext2s. Exportinterpolation,
asynchronous sampling and shortwindows limit precision and causal attribution.

| Metric | 171.459–231.415s | 231.443–291.441s |
| --- | ---: | ---: |
| ECT | 184–188F | 188–194F |
| MeanRPM | 949.24 | 951.13 |
| RPMSD | 19.02 | 33.73 |
| MinimumRPM | 873.5 | 831.75 |
| Sub900groups/min | 7.0 | 15.0 |
| Meanrecoveryto925 | 0.196s | 0.256s |
| Meanreboundpeak | 982.5RPM | 1005.5RPM |
| Timingmean | 3.89deg | 7.67deg |
| IACcommandmean | 42.93% | 39.18% |
| RawFRPmean | 3.05766V | 3.05750V |
| Meanlambda | 1.0111 | 1.0119 |

Pressure is stable across the transition; no recurring loss of fuelpressure
accounts for this particular pattern. Both fuel-feedback dynamics and external
torquedisturbances remain possible; unchangedmeanlambda doesnot prove equal
combustion from cycle to cycle.

v021last60s:RPMSD29.76/min847/diprate19permin, meanrebound997, meanrecovery0.209s.
That window was186–188F andmuchlaterafterstart. v022latehasfewerthresholdgroups
butgreaterSD/lowerminimum/higherrebound/sloweraverage recovery. Do not choose
thelowestdipcountalone ordeclare a perfectly controlledcausalcomparison.
The owner-reported newbehavior is enough to rejectadoption without provinggain
wasthesolecause. The earlier calmerperiod mustnotbeusedaswhole-trialsuccess.

## Warmup handoff is a concrete next target

Rechecked unchangedtable44243/44240:airmultiplier drops from~1.30at165s to
~1.02at200s inthisECTregion. With startup~24s intoVCM, thattransitionwouldfall
roughly189–224s into the recording under the documented engine-runtime meaning.
This precedes theworsening finalminute. Thefinalruntime row is thensteady;
do notclaim a continued runtime-baseairdecline past200s.

Also rechecked44568maximumcoldstartspark vsECT/ERT and44569RPM/loadadder.
Theformercontains−38deg near165s andmuchhigher limits by255s; thelatter is
about+41near1000RPM/lowload. Their documented roles are consistent with anearly
low-spark/high-air operatingperiod andsubsequent release ofspark authority.
Exactactive combination/eligibility is not logged, so this is a testablecontrol-
path hypothesis, not proof of a calculated limiting value. Nominal idlespark
table44579/44578 remainsflat12degrees, gainv0220.75/floor−6.

This explains why matchingECTalone could confuse a gaintrial: timing/air demand
also evolve withruntime andadaptation. Do not flatten coldstartlimits or hold
excess airflow simply because the earlyperiod is smoother.

## Next intervention recommendation

1. Returnexactv021 first; preserve its pressuremeasurement baseline. No further
   gaincut or attemptedfix stackedontov022.
2. Nextcandidate hypothesis to evaluate fromv021: modest reduction in nominal
   idle spark (for example12->10degrees in theP/N/Drive idlesparktables) to test
   a higher-air/lower-spark warm operatingpoint while retaining gain1 and its
   corrective authority. This is a proposedexperiment, **notprepared/flashready**.
   Confirm itsactivepath andfullprecision/temperature scope before savinga
   numberedcandidate. It is not a maximumsparkcap or a globalignitionchange.
3. Predictedconditionalresponse: nominalwarmspark shiftsdown, IAC/air demand
   shiftsup atsameidleRPM, anddip/reboundmayimprove if warmtorquereserve matters.
   Ifnominalshift occurswithoutimprovement, rejectthatmechanism; ifdiprecovery
   orrunningworsens, rollbackv021. Do not inferbadIAC fromlackofresponse.
4. Resolve desiredRPM/TPS acquisition for thattest; thetwo mostrecentprofiles
   havenotfixedtheirabsence. No extraunchangedlongrun requested here.

The proposedoperatingpoint experiment followsnewobservations andtheowner's
boundedintervention policy. It mustremainseparatefromchanges tocoldstartcaps,
airmultipliers, fuel/MAF or injectorcharacterization. No v023 prepared inthisreview.
