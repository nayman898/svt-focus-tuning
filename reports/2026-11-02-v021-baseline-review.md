# v021 baseline review and next experiment

Stopped/exported on owner request once188F/normalCL pressure/mixture data were
available. Source `paired-20261102-161921-6cda66ce-v021-pressure-baseline`.
Preserved [capture](../logs/2026-11-02-v021-baseline-01/), both natives/CSVs,
hashes and SQLitebackup. Manifest saved/noerrors; database integrityok/finalized.
No engine shutdown, ECUwrite/readback, code clear or adaptation reset by agent.

## Measurement baseline

KOEORPM0, voltage2.99V and converted43.7psi were observed before owner engine
start, consistent with independent~43psi. In180–188F normal-loop rows, converted
FRP44.52–45.30psi, mean44.898; raw3.042–3.086V. Conversion now responds instead
of being flat40. Retainv021 as the owner-designated pressure-aware baseline.
This is operating-range consistency, not full-range bench sensor certification.

VCM21827rows1.396–505.965s; one2.157sgap36.317–38.474 near cranking. Engine
did not run for the initial~36s ofrecording. ECT146F beforestart then142F during
start; this is a warm start, not an overnightcoldstart. CLYes at122.403s;
FMEmNo throughout. Prior coldFMEm is not proven repaired by this different start.
EarlyCL positive trim reached25% and widebandmin0.733 in120–150swindow; warm
settled readings should not conceal that entryexcursion. No DTC read performed.

20requestedchannels,18populated. DesiredRPM andabsoluteTPS blank throughout;
do not invent target-relative error, driver-input state or actual951vs944tracking
from absent data. Stored targets remain950 but are a calibration fact, not a
measured dynamic command. Runtime saturated255. Pressure channel freshness is
limited by asynchronous delivery; rowspacing is not a20ms ECUchannel sample rate.
SCGclockalignment frommetadata+1.508305s is provisional; sensor/exhaustdelay
uncorrected. Wideband means use validquality only.

## Warm result

NormalCL/FMEmoff andECT180–188F cover238.916–505.965s,267.049s:

| Measure | v021 |
| --- | ---: |
| ActualRPMmean /SD | 950.72 /27.94RPM |
| Minimum /maximum | 829.5 /1017RPM |
| Sub900RPM groups | 72;16.18perminute |
| Widebandmean /range | 1.0104 /0.940–1.174lambda |
| STFTmean | −0.27% |
| IACmean | 39.20% |
| STIT /LTIT mean | −0.14367 /−0.04654lb/min |
| Timingmean /range | 8.73 /3.75–29.5degrees |

Groupingsamplesbelow900 separated<=1s is the same descriptive event definition
used in priorreviews. Pressure stable through continued dips. SparkSource almost
entirelyIdleFeedback:11605rows versus4Base/MBTrows, not4independent events.

ECT182–184F comparison: v021SD27.86/min838 and~16.11dips/min, versus priorv019
SD30.05/min839.75/~18.98dips/min. These are small descriptive differences across
unequal durations, different adaptation/history and incompletev021driver/target
data; no causal claim that sensor scaling improvedidle. Temperature band can be
noncontinuous; do not equate its first-to-last range with observed in-bandtime.
Pressure integration is useful; the idle oscillation remains unresolved.

## Next bounded intervention

Prepare [v022](../tunes/v022-idle-spark-gain-0p75.md) fromexactv021: onlyECM47996
idle spark proportional gain1.000->0.750 plusNotes. Parent remains baseline;
this experiment is not automatically adopted. The feedback coefficient is
exposed/verified; no hidden air-controller mapping is claimed.

Question: does a smaller fast spark correction reduce rebound/cycling, or does
it remove useful underspeedrecovery? Expectedconditionalresponse: smaller spark
correction forcomparableRPMerror ifthispath isactive andnotclipped. Not25%less
alltiming, dipdepth orfrequency. Judge both correction response andRPMoutcome.
Reject fordeeper/longerundershoots orslowerrecovery eveniftiminglookscalmer.
IfsparkswingreducesbutRPMdoesnotimprove, don'tkeepcuttinggainblindly.

No furtherMAF/baseair/injector/pump/VCT edits bundled. Nextprofile18retains rawFRP,
removes redundantconvertedFRP6502and saturatedruntime2131 to reduce requestload,
and keepsdesiredRPM/TPS requests. Saved configuration verified; runtimecoverage
pending. Confirmessentialfields before the actualrunningcomparison. Do not
claim reducing requestcount guarantees delivery or restart/discardrecordings.
