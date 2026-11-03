# v020 base-air experiment: reject and return to v019

Owner reports more stutters than normal after stopping/exporting v020. This
meets the experiment's rejection criterion. Recommend exactv019 rollback;
not owner-confirmed performed. Do not request another v020 run to reproduce it.

## Data quality

Source `paired-20261102-113442-8c9dcd3e-v020`, preserved in
[logs/2026-11-02-v020-base-air-01](../logs/2026-11-02-v020-base-air-01/).
Manifest saved with no errors/missing files. Both native files andCSVs retained;
SQLite integrityok and finalized. All21catalogued tune identities verified.
VCM18177rows, offsets1.316–423.839s, no row gaps over0.3s; all18channels populated.
Coolant86–170F: requested180–185F warm window not reached. Runtime reaches255
and saturates; use recording time and actualECT, not that saturated timer alone.
SCG elapsed = VCM offset +7.927350s frommetadata, provisional; exhaust transport
delay uncorrected. No new DTC read/clear, ECU write or adaptation reset by agent.

## Actual state chronology

| VCM offset | Recorded state |
| --- | --- |
| 1.316s | CLNo, FMEMNo |
| 54.126s | CLYes |
| 133.178s | CLNo, FMEMYes |
| 307.572s | CLYes, FMEMNo |

The initial live read at152F/FMEmYes could not establish what preceded it.
The owner correctly challenged that inference; the export now establishes the
actual sequence. Do not equateFMEm onset with a verifiedP1132 set timestamp.
The later normal-loop interval is usable but follows fallback and differs from
the prior baseline's thermal/adaptation history.

## Trial result

Use desired944RPM, CLYes, FMEMNo to exclude target decay/fallback from the
idle comparison. Event definition: samples below900RPM grouped when separated
by no more than1s. Counts are descriptive and depend on that rule.

| Window | ECT | Mean RPM / SD | Minimum | Dips per minute | STIT / LTIT mean lb/min |
| --- | --- | --- | ---: | ---: | --- |
| v020328.234–423.839s | 160–170F | 951.45 /32.90 | 836.25 | 25.10 | −0.21888 /−0.00157 |
| v019warm1.427–82.931s | 182–184F | 951.06 /30.05 | 839.75 | 18.98 | −0.19536 /−0.03666 |
| v018166.770–227.909s | 160–170F | 951.85 /20.37 | 886.75 | 3.93 | −0.18036 /−0.00680 |

v02040events in95.605s. v01925events in79.049s observedtime (onegap excluded).
v018temperatureoverlap is not a controlled baseline: its runtime/base-air taper,
MAF curve, mixture and adaptation differ. MatchingECT alone does not make itA/B.
Do not claim v020caused a6x increase from thev018comparison or an accurately
quantified worsening versusv019. Owner report plus failure to improve supports
rejecting the experiment without requiring that stronger causal claim.

v020combinedSTIT+LTIT mean−0.22045 versusv019−0.23203: numerically less negative
by~0.01157, but different temperature, learning distribution and priorFMEm mean
the predicted~0.022nominal base contribution cannot be validated as an observed
controlled correction response. STITalone became more negative; LTITwasnearzero.
Do not report either alone as proof that the model prediction succeeded/failed.

v020latewindow widebandmean1.0085, range0.924–1.144. STFTmean+1.68%, range−3.34
to+5.38. Nearstoichiometric average therefore coexists with repeatedRPMdips.
MeanIAC36.52%, rawMAF0.5823V; sparkmean12.32deg, max29.5. SparkSource63rowsBase/MBT
and4045IdleFeedback; these asynchronously repeated/interpolated rows are not
63distinct events. Average target tracking alone would conceal poor stability.

## Decision and next experiment policy

Reject v020, return to exactv019. No automatic escalation of the same air cut,
no stacking a compensating spark/MAF change onto a rejected trial. This result
does not prove a defectiveIAC or the opposite base-air direction correct.

The next useful intervention should start from the restored parent and isolate
a different mechanism, or use the parent return as a confirmingA/B comparison
if the owner observes recovery. That confirmation is a changed-calibration test,
not another unchanged baseline request. Prepare a further numerical trial only
after assessing what remains at the restored operating point. No v021 prepared
in this review; no demand to repeat this rejected calibration.
