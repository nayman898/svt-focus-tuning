# Archived agent session history

Preserved during repository cleanup on 2026-11-03. This is historical context,
not current operating instructions. Entries describe different points in time
and can supersede one another. Use [README.md](README.md), the revision catalog,
and dated reports for the latest state. Original relative links remain valid.

LATEST 2026-11-02 v024 successor PREPARED/VERIFIED, NOT FLASHED/TESTED: tunes/v024-fuel-cleanup-diagnostics.hpt exactv021parent. Only44511 at2500RPM TPS15.625/19.53125% lambda1.0700000524520874/1.1399999856948853->1 plus50P0190/P0192 NoErrorReported->MIL, P0193NoMIL->MIL, Notes. All80fuelbody values checked afterreopen(other78exact),163DTCrows(other160unchanged), displayedaxesmatch/axesnotedited, wholecomparisonexact44511/50/Notes, fullparentNotesprefixretained. 251773bytes SHA80EF77A8B1E4DE7E60D3754495A01CEF30C5AB707AD00F789DD520A647363E1E. All24olderidentitiespreserved. Userauthorizesfewcorrections; firststart plannedcold/newupstreamO2/unchangedCKP, newO2part/installtimingunrecorded. Do not attributeimprovementsolelytocalibration. docs/v024-regression-test.md and docs/v024-run-card.json: existingV023IdleSparkTrial18 reused, actualactiveprofile/admissioncheckbeforecapture. StageAcoldthroughruntime>300and60-90swarm, stageBgentleparked1500/2000/2500holds onlyifsatisfactory; affectedfuelmode/TPScoverageoruntested, notidle-onlypass. No newprofileload/recording/engine/ECUwrite/reset/codeclear. v021baseline/rollbackretained, v024notadopted. Otherauditissuesincludingcrankingstepdeferred. Reference25revisions/9snapshots; fullprecision44511bodyevidencenormalizedforv016-v023comparisons.

LATEST 2026-11-02 complete v021 OFFLINE calibration audit: reports/2026-11-02-v021-complete-calibration-audit.md; 342-entry ledger reports/2026-11-02-v021-parameter-review.csv and audit-checks JSON. All24 binary hashes/sizes match; independent reconstruction from v017 plus verified deltas matches all342 entries/96 tables/4692 gridcells. No VCM/ECU/tune changes. Newly escalated: 44519 cranking0.930@63.990F->0.335@64.000F (documented lambda, not warm-running cause); liveFRP still P0190/P0192 NoErrorReported, P0193 NoMIL. P0132 alreadyMIL. MAF monotonic but uneven lowflow/highflow slopes; fuel44511 leanpockets with32731 modeboundary; runtimeair/spark and dashpot remain leads. No omnibus fixes/numeric replacement asserted; no v024 prepared. v021 baseline retained; installed rollback unconfirmed. Latest audit supersedes older blanket-retain dispositions for flagged parameters.

LATEST fan/severity clarification: owner observes196F ON/~188F OFF. v023 markers235.924/269.853s; temperatureproxies, not directswitchfeedback. Equal30s before/afteroff: RPMrange912.25-984.25 vs836.25-1016; spans72vs179.75; P5/P95(rowweighted)924.5/974.5vs888.25/991.5; timeoutside944+/-50=0vs9.94%. Do notequate meanswithstability. Leadseveritywithspan/distribution/timeoutsidetarget/dipduration/recovery, stallsseparate. Report/workflowupdated; no newlogs/tunechanges.

LATEST 2026-11-02 v023 trial ENDED/SAVED/REVIEWED: reports/2026-11-02-v023-stall-review.md.
Preserved logs/2026-11-02-v023-idle10-01; source paired171032-65205513-v023 saved,
SCG finalized/integrityok; VCM13394rows1.311-321.607, all18 populated incl target/TPS.
Ownerphysicalstall. RPM948 at303.747 -> brief0 at304.004 ->790 at304.101 -> sustained0
305.665. Signal/reporting anomaly, NOT proof CKPbad or instantphysicalrestart.
Pressure~3.05V/lambda~1 beforecollapse; MBT followsRPMreportcollapse, causalunproven.
CL85.386 through305.712; FMEMNo. Onset~260 nearECT190fanoffthreshold AND estimated
runtime255; actualfanstate/activecoldstartpathunmeasured. No isolatedcauseclaimed.
Read-onlyDTCattemptdisplayedNoDTCs butfreshness/pendingcoverageunverified; nofreshP0320.
v023notadopted; exactv021rollbackrecommendedNOTconfirmed. No v024prepared. All24
catalogedbinaryidentitiesverifiedunchanged. O2known-goodreplacementPLANNEDnotconfirmed;
CKPsubstitutionconsiderednotperformed. Onehardwarechangeatime, circuit/waveformcheck
beforeclaimingsensorfailure. NoECUwrite/reset/engineactions; no activelogrestarted.
2026-11-02 SCGLOGGER READINESS FEATURE implemented forFUTUREappstarts. Userexplicit
DONOTrestartcurrentv023log/app toapply; no logsstarted/stopped/restarted byfeaturework.
Read-onlyUIAgridinspection duringcurrentcapture showedall18valuespresent including
freshlookingdesiredRPM944/TPS179.8; populationnotindependentupdate-ageproof.
scg-logger/scg_logger/paired.py readinesspreparingphase keepssetupcapture, freezes
expectednamecounts, needs3completesnapshots+freshSCG, markersofficial_windows; monitors
5s, closeswindowonlosswithoutstoppingfiles.60sadmissionbudgetthenmanualRecheckchannels.
Publicwindows/scanner.ps1 -Actionchannels isreadonly/no menu/start/stop/config changes,
GridPatternallconfiguredrows, separate6sprobeprocess. NewUIreadinesslabel/button.
CLIexportauditsactualVCMCSV inexportchild, writesvcm-coverage.json, marksincomplete
ifmissingcolumns/neverfields/laterblanks; noUIfileIO. FullCSV retained/notcropped.
CurrentrunningappstilloldPairedSession; applybyreopeningONLYaftercurrentrunends.
Futurestarthelpersmustdistinguishpreparing(activecaptures)fromrecording(officialready);
neverclaimallfieldsreadyfromrowlabels alone. VCMperfieldageunexposed/constantvaluesvalid.
60tests+ruffpass, readonlyprobe18present; actualoldv021blanktarget/TPSauditfails,
completev020auditpasses. Noexternalpush/merge/engine/ECUactionsinfeaturework.
V023 LOGPREP2026-11-02 COMPLETE: V023 Idle Spark Trial18profile LOADED/SAVEDBACK
verifiedall18. Desired2210andabsoluteTPS3017 removed/readdedfromactualnativeECM
selector, nowboth200ms; noID/typedifference, no claimmissingdatafixed. Remaining
16requestsunchanged. RecordingSTOPPED; noengine/ECU/flashactions. Preparedhelper
scg-logger/.local/start-v023-pair.ps1 labelv023-idle10, NOTexecuted. Awaitowner
flashcomplete/startrequest. Verifydesired/TPSfreshatadmissionbeforeruntimeclaims.
Currentprofilepath profiles/2004 Focus SVT - V023 Idle Spark Trial.Channels.xml.
No oldrecordingdiscarded; v022exportsalreadyretained; no activelogtosave/close.
LATEST2026-11-02 v023-idle-spark-10deg.hpt PREPAREDNOTFLASHED exactv021parent,
ownerexplicitrequest. Only44579P/N+44578InGear all5bodycells each12->10deg+Notes.
Axesnotedited/displayedaxesmatchinheritedcapture; fullprecisionbodycopiedbefore,
saved/reopened10valuesverified; gain1.000/floor-6readinEditor. Wholefilecompareonly
2idlesparktables+Notes; entirev021Notesprefixretained. All23olderhashes unchanged.
250845bytes SHABA0E2CD969743295AD0556C6B5EFED6F5B8419D1FD8912887A1B6C2DE6FBBCAD.
Nominalsparkoperatingpointexperiment: ifactive lowernominaltiming/moreair atsameRPM,
notfixed10finalspark/maxcap/globalchange. FlatallECTscope, notwarmonly; startupcaps
andairhandoffunchanged. Rejectworsedips/recovery/hunting/richroughrunning, rollback21.
No v020aircut orv022gaincut inherited. v021baseline; currentlastownerwritev022until
newconfirmation. NoagentECUwrite/reset/readback. Current18profilestillmissingdesired/
TPS inrecentcaptures; notsolved, requireadmission/coveragecorrectionbeforenextcomparison.
Referencebrowser24revisions/8snapshots includesv021->v023only2tables10cells.
LATESTv022 newoscillation ownerreport, STOPPED/SAVED+REVIEWED2026-11-02. NoFMEm;
CL110.481. Sourcepaired164644-31b89259-v022-spark075; logs/2026-11-02-v022-spark075-01;
report reports/2026-11-02-v022-spark-response-review.md.12551rows1.295-291.441gap1.458s;
desiredRPM/TPSstillblank16/18. Nominal950notmeasuredtarget. Newoscillationmatcheslate
window: prior60SD19.02/min873.5/7dipsmin/rebound982.5 vsfinal60SD33.73/min831.75/
15dipsmin/rebound1005.5; recovery.196->.256s. ECT184-188vs188-194,timeconfounded.
Rawpressuremeans3.05766/3.05750,WBmeans1.0111/1.0119 stablemean. Do notadoptv022;
returnexactv021recommendedNOTconfirmed. Do notreducegainfurther/stackontorejectedtrial.
Offline44243airmulttaper165-200s maps~VCM189-224 afterstart24s;44568coldmax+44569
adder roles fit earlylow-spark/highairthenrelease, activeeligibilitynotproven.
NextPROPOSEDnominalidlespark12->10torquereservetrialfromv021gain1; NOTpreparedv023.
Needactivepath/scopeandchannelcoveragebeforecandidate. Notcaprescue/globaltiming.
Noengine/ECUwrite/reset/readback. Baselinev021retained, currentownerwrittenv022.
Initial164601pairneverVCMstarted(widebandwarmup), keptseparate. Bothnatives/CSVs
andintegritypassedfor164644pair. No continuedrecording.
LATEST2026-11-02 v021baselinecapture STOPPED/SAVED+REVIEWED ownerrequest: report
reports/2026-11-02-v021-baseline-review.md, logs/2026-11-02-v021-baseline-01.
Warm180-188267smean950.72/SD27.94/min829.5,72sub900groups16.18/min;FRPmean44.898psi,
WBmean1.0104/STFT-.27; CL122.403/FMEmNoentirecapture. Warmstart146F notcoldfixproof.
DesiredRPM/TPSblank (18/20), no inventedtargeterror. NativeHPL/CSV/SCG integrityok.
v021 RETAINEDbaseline. v022-idle-spark-gain-0p75.hpt PREPAREDNOTFLASHED fromexactv021:
only47996gain1.000->0.750+Notes. Predictionlesssparkcorrection/comparableerror,
lessrebound ifgainamplifies; rejectdeeper/longerdips/slowerrecovery, notcalmtracesalone.
No v020aircut, MAF/pressure/floor/targets/protectionschanged. Saved/reopenedgain/floor,
fullcompareonlygain+Notes, parentNotesprefixverified; all22priorhashes unchanged.
250669bytes SHA577F775782A98705C2F3A6205BBC32BF7461238967255CCD1105303A0C7DD29F.
SparkResponse18loaded+savedbackexact; removes6502convertedand2131runtime, retains
raw6507+desired/TPSrequests; dynamicpending, stopped. No furtherunchangedbaseline
runrequested; nextiscontrolledcandidateafterownerflash andcoverageadmission.
Noagentengine/ECUwrite/reset/readback. Referencebrowser23revs/7snapshotsupdated.
LATEST2026-11-02 v021-fuel-pressure-feedback.hpt PREPAREDNOTFLASHED/VALIDATED.
Ownerdesignates nextbaseline; futurecandidatesparentv021afterinstall/verification.
Exactparentv019 (v020aircut NOTinherited), only7596transfer+Notes. ADCaxes retained
0/0/0/0/102/921/1023, outputs0/0/0/0/0/70/78.71794891357422psi. NominalFordgasoline
.5-4.5V/0-70 workingrange; below102zero clamp, upperlinear extension explicitdesign,
NOTrecoveredfactorybinary. Originalsensor/manifoldreference+independentchecks support
nominalcurve; exactmarkings/VREF notbenchverified. See tunes/v021-fuel-pressure-feedback.md.
Saved/reopened7outputs/axes, fullcompareonly7596+Notes, parentNotesprefixverified;
all21priorbinaryidentitiesunchanged.247597bytes SHA
078E91786A07793A4EB6607B8B870BDC9558562C0FE75AF95E6D5AB1A1A87ACA.
NativePressureBaseline20configured/saved6502converted+6507raw, dynamicpending,
stopped. FirstafterflashKOEOcomparegauge/raw/converted, thenshortsupervisedidle.
Do notpromiseidlefix ordisplayonly: model/diagnosticpaths mayusepressure. Keepinjector
ref40/neutralmultipliers/pump/6950zero/MAFv019/idlecontrols unchanged. NoagentECUwrite,
reset/readback. Currentlatestownerlabelv019 untilownerconfirmsv021installed.
Referencebrowser22revisions/6snapshots updated, v019->v021 only7596sevenbodycells.
LATEST2026-11-02 v019pressuretest reviewed: reports/2026-11-02-v019-pressure-review.md;
logs/2026-11-02-v019-pressure-01. Ownerlabelsreturnv019(noECUreadback). Sensororiginal
SVTinstalled, sharedmanifoldreferenceconfirmed. Raw6507signal3.046875-3.0859375V,
mean3.06871; nominal44.57-45.25psi, absolutecurveunverified.17targetrelativedips,
8FMEM/9CL; no repeatedsampledpressurecollapse. Lowerspressureinstabilitypriority,
notallfueling/airhardwareexclusion. ECT128-152/target1184->1024, notwarm950test.
Partialmanifestexportfailed; laterCSVpresentbutHPLMISSING. SCGvalidendsVCM~99.596s,
VCMends121.165; do notextendAFRintoend.5163rows/all19present;gap5.984-7.385.
No repeatunchangedpressurelogneeded. No newtune/pump/regulator/MAFchange. Nextpressure
integration verifiedtransferalone+modelaudit, notpromisedidlefix. v020stillrejected.
LATEST2026-11-02 v020saved/reviewed/REJECTED onownerincreasedstutters. Exactv019rollback
recommendedNOTconfirmed. Report reports/2026-11-02-v020-base-air-review.md, preserved
logs/2026-11-02-v020-base-air-01. All18populated/no>.3sVCMgaps/integrityok/saved.
VCM18177rows1.316-423.839,ECT86-170(not180window). CL54.126,FMEM133.178,CLreturn307.572.
PriorliveFMEMinferencewaspremature; exportsnowconfirmsequence, notDTCtimestamp.
NormalCLdesired944/ECT160-170 interval328.234-423.839:40sub900groups/95.605s=25.10/min,
min836.25,SD32.90,mean951.45; WBmean1.0085 STFTmean+1.68. v019hotter182-18419/min,
notcontrolledAB. STIT-.21888/LTIT-.00157 combined-.22045 vsprior-.23203, learning/temp
confounds preventclaimingpredictedshift. Do notescalateaircut orstacknewchangetofix
rejectedcandidate; returnparentasconfirmingintervention. Noengineflash/reset performed.
LATEST2026-11-02 OWNER requests moreliberal bounded causal experiments. Supersedes
blanketno-v020/no-baseairhold: experiments allowedwithoutprovenrootcause whenone
mechanism,prediction,rollback explicit. v020-base-idle-air-trial.hpt PREPAREDNOTFLASHED
fromexactv019:44242/44239 only900/1000points-5percent+Notes. Interpolation700-1250also
affected; notthermalgate. Predictedlessnegativeaircorrection(s) atmatchedRPM/load;
notpromiseexactSTIshift orrootcausefix. Ifshiftbutdipsunchanged, biasnotfullsolution;
ifworse rejectv019. See tunes/v020-base-idle-air-trial.md fulltest/limits.
Saved/reopenedfullprecision4cells/axes/rest exact; wholeEditorcomparison onlytwo
baseairtables+Notes; parentNotesprefixverified; all20olderhashes unchanged.
247277bytes SHA17F421379EA038CE1938EDD8A080F6D517DCF90CE60CABC340B4CFB8C3ACADDA.
NoECUwrite/reset/readback. Currentinstalled remainsownerreportedv019.
Base Air Trial18 loaded+savedback exact; dynamicpending, stopped. Removescamtrial
corelossproblem; ECT500ms,STIT100ms. DonotcontinuecoldrichFMEmjusttoreachwarmtrial.
Referencebrowserupdatedv020,21revisions/5fullsnapshots; originalv017immutable.
LATEST2026-11-01 cam124910 STOPPED/EXPORTED onownerdelegatedrequest. Engineoffadvised,
notconfirmed; loggingstopdoesnotstopengine. reports/2026-11-01-v019-cam-startup-review.md.
Preservedlogs/2026-11-01-v019-cam-01. ManifestPARTIAL WinError5sessionreplace, all4files
present/readable; SQLiteintegrityok/cleantrue. Do noteraseerror. VCM5155rows1.624-121.327,
ECT/TPSblank,22/24present, no>.3srowgaps. CL47.900,FMEM91.334, WB~.983withSTFT-24
thenWB~.791fallback. Notwarm950trial. Cam1.875-3.125after20s,duty0constant:notVCTclear.
Do notrequestunchanged24repeat; failscorecoverage. EarliermanualVCMlostperowner,
separateSCGpreserved/notmerged. No v020/noECUwrite/DTCclear/newDTCread.
2026-11-01 idle-cause investigation: docs/idle-cause-test.md supersedes blanket
no-new-log instruction: next justified capture adds CAM TRACKING, notunchangedrepeat.
24profile loaded/saved: profiles/2004 Focus SVT - Idle Cause Cam Trial.Channels.xml.
Parent21requests unchanged; native ECM selector addedCamAngle2151/Error2152/Duty2153
all200ms. IDs fromactualsavedXML, notguessed. Live/dynamiccoveragePENDING; stopped.
No v020, retainv019. Next ownerready shortadmission, continuouswarmup/3dips ifgood;
stop/export/revert21ifblanks/coreloss. Noengine action performed. Old screenshot
private only; containsVIN. No external ticket sent.
Preminimumreview25groups:21RPMfalling between-.5/-.25s;19IACincreasing,20sparkincreasing,
7STFTwithin.1pp. Notonsetproof; async. Do not inferIACfailure fromaverageairdecline.
2026-11-01 IAC action check COMPLETE: docs/iac-diagnostic-next-step.md.
Connected Scanner stopped; Controls/SpecialFunctions visuallyEMPTY, UIA blanktab/
status only. Opened/closed window, NOoutputcommand. No supportedIACoverride found
in this session; not proof alltools lack capability. Exact2004SVTpinpoint procedure
notverified; FordTSB03-3-5 excludesFocus, neverapply itsengine-specificlimits.
Next owner task engineoffcoolvisualIACpart/connector/bypassPCVplumbing; regulated
smoketest ifneeded; dynamiccommand/currentvsflow test needs confirmedtool/wiring.
Owner lastKOEOconfirmed; source19049populated, notwarmvalidation. No newlogneeded
before intervention. No v020/noECUwrite/reset; supportdraft updatedNOTsubmitted.
LATEST reference/workflow update2026-10-31: reports/calibration-inventory/index.html
is the shared revision browser. All20revisions cataloged; full342parameter snapshots
v016-v019 reconstructed ONLY through verified deltas; earlierfullvalues UNKNOWN.
Machine reference revision-reference.json; builder tools/build-calibration-reference.ps1
verifies all20tunehashes/sizes and MAFclipboard/delta agreement. Originalv017immutable.
Browser checks: v018->v019onlyMAF9cells; v016->v018only2291/DTC; reverse17->16only12115.
NO v020 created or flash-ready: currentEditorIntegratorsearch returned no entries;
no verified airintegrator/currentvalue, no inventedgain/baseair/MAFchange. Userasked
v020 but this part remains blocked on mechanism/value verification, not permission.
Warm Air Response21 profile LOADED/SAVEDBACK exact; Stage2A20 unchanged plus
IdleSpeedSource19049@100ms copied from priorworkingdefinition. Livepending; stopped.
See docs/warm-air-response-test.md. Preserve pre-restartVCMsegments; no repeated
unchangedcold/warmrun until meaningful intervention/newsignal. NoECUwrite/clear.
LATEST v019 warm exported/reviewed: reports/2026-10-31-v019-warm-review.md;
logs/2026-10-31-v019-warm-01. VCM only1.427-82.931s starts182F/runtime232,
not180Fcrossing. OffsetSCG+101.942729 provisional; gap57.250-59.805. All20populated,
ECT184constant after1.738, runtime255after23.868 (freshness/saturationunverified).
WarmRPM SD24.8->32.8/32.5; below900events rates16.8->19.8->23.4/min (1sgrouping).
Firstsub87524.320s/856.5, deepest32.664/839.75. CLYes/FMEmNo/RPMCtrl/IdleFeedback
throughout; some dips STFTunchanged. MeanIAC/MAF/adaptedairdecline, fuelmeanmoves
nearzero butWBoscillationwidens. No180Ftriggerproof, no255stimerproof, noMBTswitch.
No newtune. Nextauditwarmbaseair/adaptation/IAC response; no repeatunchangedlog.
# SVT Focus tuning agent

NEW OWNER REPORT afterv019coldstop and earlier no-DTCread: "P1132 just fired."
Preserved logs/2026-10-31-v019-cold-01/p1132-owner-report.json. Exact onset/status
notverified; do notrewrite earlier no-code observation or equateFMEMtimestamp
withDTCsettime. Preservecodes; engineoff advised, read-onlyDTC/freezeframe next
when ignitionon available. No clearing/reset authorized or performed.

LATEST v019cold111128 STOPPED/SAVED afterFMEM warmup; report
reports/2026-10-31-v019-cold-review.md; logs/2026-10-31-v019-cold-01. CL70.102s
(runtime74/76F), FMEM174.309s(runtime178/120F), ends128F. WarmtrialNOTREACHED.
Earlyrichminlambda.709 around1V unchangedMAFregion; later entersinterpolation
near.785V atFMEM, so don'tdeclarev019exonerated/accepted. O2FailNo. Onepostrun
ReadDTCs returned0confirmed/MILFalse/NoDTCsdetected; noclear, causeunidentified.
All20fields; oneVCMgap; SCGoffset+23.751223provisional. Noactivepair/no newtune.

2026-10-31 OWNERCONFIRMED v019flashed, coldstartpending. Stage2AAirSpark20 already
loaded; saved-back .local/before-v019-20261031.Channels.xml matches allrequested
definitions/intervals. Prior stoppedexportedlog closed. Noagentrecordingstart or
ECUreadback. Labelnext v019-2A-cold; capturebeforecrank, treatstartupseparately
fromwarmsettled60–90scomparison. User toconfirm loggingstarted; nofanwaitrequired.

LATEST v019 PREPARED NOTFLASHED/TESTED: tunes/v019-maf-low-flow-trial.hpt fromv018.
OnlyMAF12163ninecells~.400–.699V reduced3.72–4.80% plusNotes. Bounded25%blend
towardPMASProTube reference, taperby.898V, cap4.8%; retain0/.379 and.898/up EXACT.
Fullprecision CopyWithAxis revealedprior3.8/3.8was shallowrise3.825064/3.833398,
notexactflat. Relative edits preserveexisting scaling; no7.94xconversion orfull
manufacturercurve claim. Allaxes/other21cells exactafterreopen; fullcomparison
onlyMAF+Notes, parentNotesprefixverified.244445bytes SHA
C2EDAC9A76F9501A827A7DEF30D4A65C52A62B03D9DE4B6BC08F453E8755CFF5.
All19olderbinariesunchanged. Stationary60–90ssettledtest first; nohigherloaduntil
review. Seev019notes/delta. Nounitresolutionclaim orenginewrite/readback.

MAFSCALINGFOLLOWUP: highinjectorslope12011=.0167lb/s=60.12lb/hr; low63lb/hr;
standardaircharge.00136lb=.616886g/cyl,4cyl; pressuremultipliersall1. No evidence
of7.94xglobalMAF/injectorscaling. g/s-equivalent numericcurve interpretation
stronglyfavored; DON'T multiplyMAFby7.94. Earlierstatusoverstatedequalplausibility
of8xconversionvs~22%numericchange. UIlabeldiscrepancy remains but isnot evidence
ofproperglobalconversion. Physicalinjectorcharacterization/MAFreference fitstill
unverified. See follow-up in reports/2026-10-30-hpx-scaling-status.md.

HPXAPPLICATION BLOCKED byspecificunits/definition issue, notlackofreference:
reports/2026-10-30-hpx-scaling-status.md. OfficialPMAS3ProTubeII formula validated
all30cachedoutputs; reports/2026-10-30-hpx-protube-reference.csv hasg/s,kg/h,lb/h,
lb/min atcurrentaxes, REFERENCEONLYNOTFLASHABLE. No v019created. Reopenedv018
shows.6V=.082lb/min (original4.9lb/h) butEditorhelp saysg/sec andlogsflow~.58lb/min
at~.58V. NeedverifiedECM12163/Scanner2300,2302conversion/globalcoupledscaling;
draftdocs/hpt-maf-scaling-question.md NOTSENT. No blind6–8xfactor or22%cut.
All19tuneidentitiesunchanged; PMASserial/housingrevisionflow sheetunverified.

MAFhousing OWNERCONFIRMED PMAS3inch boughtwithplainHPX fromLMR96–04Mustang4.6kit.
Seller listingmatchesLRS-MH30HPXS; manufacturerassemblyMH30-HPX. DedicatedPMAS
3ProTubeII workbook is strongerreference than generic3.000in; installedrevision/
serialsheetunverified. Don'treusegeneric14–25%asactualcorrection. Units/scaling
discrepancy remains; nocurvewritten. SeeupdatedHPXreview andvehicle.maf.

HPXMAF REVIEW: ownerconfirmsplainHPX blowthrough afterturbo nearTB nominal3inch.
reports/2026-10-30-hpx-maf-review.md. OfficialPMAS2014.2workbook downloaded/read
withoutmacros; generic3inchreference computed andvalidatedcachedformula. ActualID
unconfirmed; PMAS3ProTube sheetuses2.8in+differentareatreatment. KEY units unresolved:
Editor12163label lb/h (displaycyclelb/min yields4.9/60 at.6V) but rawMAF/logflow
scale resemblesg/s table numerics. DoNOTblindlyconvert/reflashwholecurve. LowV
plateau/slopes overlapwarm.517–.639V. Conditionalg/snumericvsPMAS+14–25%nearidle,
notvalidatedcorrection. Prioritizehousing/definition/injectorverification before
v019. Nocalibrationedits/ECUactions; reportdetails supersede guessedunits.

LATEST2A v018181640 STOPPED/SAVED; report reports/2026-10-30-v018-stage2a-review.md,
logs/2026-10-30-v018-stage2a-01. All20fields populated/noVCMgaps; rawMAF+IdleMode
available, exact100msdelivery NOTverified (async/interpolatedCSV). Warm300–399.7s
RPMmean950.64/min834.75/SD30.77, WBmean1.010, STFTmean−1.56, STITmean−.201.
RPMCtrl/CLYes/FMEmNo/O2FailNo throughoutwarm. RawMAFmovements support air/spark
branch, nozero dropout;376sdip983->853 withSTFTessentiallyunchanged. No next
unchangedbaseline; offline44603units/path andairPI/IACresponse next. No v019.
StartupO2richissue stillpresent, separate. Noactivepair/noDTCclear/read orflash.

OWNER v018WRITE COMPLETE confirmed; SBCSVT-SS-TZ kit identity ownerconfirmed.
No ECUreadback. Scannerwasstopped; Stage2AAirSpark20 nowloaded andsaved-back
definitions/intervals match exactly. Before/afterXML .local/before-stage2a-v018.
Channels.xml and .local/stage2a-v018-loaded.Channels.xml. No recording started.
Actual channelavailability/rates notyetvalidated. Await owner session/engine
start; shortwarmsettled2–3dips/max90s, notanotherlongbaseline. KitMOIstillunknown.

SBC clutch research: docs/south-bend-svt-clutch-research.md. Likely catalogmatch
SBCSVT-SS-TZ, historicStage3Endurance425ft-lb/includedaluminumflywheel; current
manufacturerfamily page calls sameMPN KevlarStage3Single, crossrefSD3-2636-45,
but pagehasDiesel/title andSport/Endurance inconsistencies. InstalledPNunverified.
Catalog24weight is kit-row, NOTverifiedbareflywheelmass. No verifiedMOI; don't
replace inertia0.0150 frommassguess. Writecompletion stillnotconfirmed; noUI/ECU
actions or manufacturercontact duringlookup.

OWNER UPDATE: v018 still writing; NO Editor/Scanner/vehicle actions until write
completion confirmed. Flywheel SBC single-mass; IAC stock, owner reported.
Part numbers, actual flywheel inertia and IAC condition unverified. Do not call
single-mass automatically lightweight or derive a replacement inertia scalar.
Use this hardware context for2A air/spark dynamics, not proof of a failed valve.

OWNER BEGINNING v018WRITE (not yetcompleteconfirmed). Do not touchEditor/Scanner/
vehicle connection until ownerconfirmscompletion. Offline2Aprepared:
docs/stage-2a-air-spark-test.md; profiles/2004 Focus SVT - Stage 2A Air Spark Trial.Channels.xml.
20channels, XMLvalidated only/notloaded; rawMAF2302type2@200ms, IdleMode12200@1s
added; CLReady/OLConditionsremoved; STIT500->100ms/STFT200->100ms/ECT50->500ms.
Actualratesunverified. One bounded20–30sadmission then2–3dips/max90ssettled,
notunchangedbaselinerepeat. Cam/purge/idleairIDsnotverified; don'tguess. Need44603
units/activepath andairPIdefinitions beforev019; IAC/flywheel infoasked. No v019.

LATEST v018 PREPARED NOTFLASHED/TESTED: tunes/v018-dfco-recovery-diagnostics.hpt
from exactv016. Only2291DFCOexit750->1000RPM, ECM50P0132NoErrorReported->MILLight,
andNotes. Reopened1000exit/1200entry/950targets/520FO2threshold; all163DTCrows
verified with onlyP0132changed; parentNotes retained; exactEditor diff verified.
241645bytes SHA2E4E3711B2E6AFA5A343D54CBA9331CB48FB6B3774882CB0446B569ACCD9A082.
All18olderbinaryidentities unchanged. Inventorydelta reports/calibration-inventory/
v018/delta.json; v017inventoryimmutable. Doesnotfixparkedhang/warmoscillation;
DFCOtestrequiresactivecutoff, notanotherparkedbaseline. NoagentECUwrite/readback.

FULL INVENTORY REVIEW/PLAN: docs/calibration-correction-plan.md and
reports/2026-10-30-parameter-review.csv (342entry dispositions). No newtune/flash.
New verified finding: ECM50P0132 NoErrorReported on actualB1S1; proposeMILreporting
only, notblanketDTCenable. ECM44603lowloadsparkcap60/10/8/4/2/0/0 at displayed
0/480/600/720/860/1000/65535 requiresactive-path/unitverification, notglobaladvance.
Warm air/spark is primary. Dashpot32984 lowcells needhigherprecision before rate
trial. Optional distinct DFCO2291750->1000exit trial retains1200entry; cannotfix
stationaryhang. Use nominal950RPM v016 as the proposed working baseline.
Hardwaremapping (injectorPN/MAFgeometry/cams/flywheel/pressure/inputswitches)
stillmissing; inventoryisnotcompletephysicalpicture. Keepboost/thermalprotections.
All18binariesunchanged. Reviewledger saysscreened, notoptimized/validated.

CALIBRATION INVENTORY COMPLETE for savedv017 Advancedview: read
docs/calibration-reference.md FIRST before further table hunting. Index:
reports/calibration-inventory/v017/index.csv; interactiveindex.html; per-entry
NNN.json; table-cells.csv and combinedinventory.json.342/342 entries,96tables,
246scalars/switches,4692gridcells inclaxes, allIDs resolved; DTC163rows captured.
SourceSHA9597BAB2DB9DEB063298C7814F8B9930C530DBDB3FE114D80F8EE44B6463E7CE.
Values atEditorprecision;94descriptions and someaxisunits unavailable. Rawhelp
maybestale; top-leveldescription is identitymatched. No calibration edits/ECUread.
UseCSVID lookup thenindividualJSON tosave time; verifyhash/currentrevision.
v016difference only12115520vs600+Notes via verifieddiff. Do not repeatfullUIaudit
for knownunchangedvalues; preservebaseline and captureverifiedrevisiondeltas.

WARM FLUCTUATIONS PRIMARY: reports/2026-10-30-warm-idle-control-research.md
and v017warm-dip chart. User rightly objects to focusing onlyO2entry. Sixwarm
event sequences support possibleair/spark looposcillation orIAC response:
overspeed/reducedduty/airflow -> underspeed -> spark/IAC/STITrescue/rebound.
v017217.17–217.666s RPM1011->839 whileSTFT~+4.38constant; notall dipsrequire
newfueltrimcommand. STITreactive doesnotexcludefeedbackinstability; noexactcausal
phaseclaim fromasyncPID. Nextresearchtarget idleairPI/filter/overspeedresponse
andIACcharacterization; HPTNavigatoronlyexposesspark/pumpgains. ExternalBlackOak
SCPdefinitionlistsaircontrols but NOTverifiedUJAHAS3mapping. No blindgain/baseair
edit orsame20channelrepeat; coldO2problem separate. No v018 orengineactions.

LATEST v017test STOPPED/SAVED170859 ownerauthorization. Report
reports/2026-10-30-v017-entry-review.md; preservedlogs/2026-10-30-v017-entry-01.
600Fgate FAILED goal: CLruntime98s(v01691s), NBatentry.003V, STFT+25/WBmin.723.
DifferentCSVorigins/ECT mean apparent44sfiledelay misleading; runtime difference
only7s, notcontrolledcausalestimate. NoFMEm/O2Fail; laterRPMmean950/min836.
Recommendrollbackexactv016, notmorethresholdescalation; no agentwrite or owner
rollbackconfirmation. Noactivepair. Next usefulwork physicalO2signal/heater vs
PID/readiness measurement, notidenticalidlelog. No v018 prepared.

LATEST v016STOPPED/saved ownerrequest, logs/2026-10-30-v016-idle-01. VCM restarted
relative pairedorigin: metadataSCGoffset+102.016394s provisional; starts172F,
notcompletecoldstart. CL16.367s whileNBlow; STFT+25/WBmin.722 thenwarm~1.01.
RPMafter90s mean950.1/min821/desired944, no stall. All20fields; oneVCMgap.
v017 PREPARED NOTFLASHED: tunes/v017-o2-readiness-600.hpt exactv016 parent,
onlyECM12115calculatedO2entrytemp520->600F plusNotes. Reopened600 and exactdiff
verified; noverifiedfuelPIDgainexposed. Experimentalgate notheaterrepair or
warmdipfix; retain950RPM. Test parked entry+60–90s, stopifrich/rough or noCLafter
sensorresponse; rollbackv016. See tunes/v017-o2-readiness-600.md. User wants
discriminatingchanges, notunchangedrepeatlogs. No agentECUwrite/codeclear.

RETURN-TO-IDLE HANG: owner says RPM stays up approaching stop until throttleblip.
See reports/2026-10-30-return-to-idle-hang.md. Existingv014drive1215.803–1220.143s
speed<=.5mph/RPM1150–1223/desired896/TPSClosed/IAC~52/SparkClosedThrDecel;
log ends before resolution. Candidate commanded retainedair, not proven cause
or verified blip-release. v015stationary lacksVSS/TPSstate. Dashpot32984 zeros
atlowaxis require strategy semantics/rounding verification, not blindzero/edit.
Owner plansv016flash; not confirmed complete. No Editor/vehicle actions during
this investigation. Keep v016 target-only; do not silently add dashpot changes.

LATEST v016 PREPARED, NOT FLASHED/TESTED: tunes/v016-idle-margin-950.hpt from
exactv015. Owner explicitly accepts950RPM trial. Only ECM44218/44217 targets
900->950 plus Notes; reopened950/950, saved parentNotes prefix and Editor diff
verified.239085bytes SHA2567F069587C62FACC4A2E79556A48131A2DF7D527BFE0B9ECA5E388291BF410D14.
All16 prior binary hashes unchanged. See tunes/v016-idle-margin-950.md for test.
Installed remains owner-confirmedv015 until owner confirms write. Owner says
blower MAY have run during preceding155954 recording; inter-run spark comparison
has uncertain load context. Do not repeat unchanged baseline; next test is one
v016 matched warm off/blower/off with relativeRPM error and recovery assessment.
No engine write, code clearing, new sensor purchase or hardware change performed.

LATEST load-step review: reports/2026-10-30-v015-load-step-review.md. Pair160932
saved/preserved logs/2026-10-30-v015-load-step-01. Owner confirmsv015/15719,
AC/defrostoff. Owner events fanon34/off~50uncertain, bloweron65/off126,
fanon~150/off~200. Allchannels populated/noVCMgaps; CLYes/FMEmNo/O2FailNo.
Settled fan steadier, blower still dips; worst684.5RPM156.276s entirely Idle
Feedback (no MBT anywhere). Actual spark~2to0deg versus preceding~8–9deg;
learned air shifts. Next audit spark/air adaptation and fan feed-forward timing,
not another gain reduction/globalairincrease. No numeric tunechange/v016 chosen.
No active run from this saved session; no freshDTCread. Cold O2 test outstanding.

LATEST completed review: reports/2026-10-30-v015-bosch15719-review.md. Owner
confirmed15719 pair155954 now saved, no active paired recording inferred from
that session. All20channels populated; CLYes/FMEmNo/O2FailNo in recorded samples.
TwoVCMgaps57.892–60.544/67.053–68.620. Warm188F start, RPMmean899.64/min763.5,
WBmean1.0162, STFTmean−5.62%. Dip177.626s: RPMfall precedesMBT; no gain edit.
No urgent NTK purchase justified by warm data; no cold readiness/electrical
equivalence proven. Next attended cold-soak same-calibration comparison. No DTC
clear/read this review; earlierP1132 status not newlyverified. Preserve prior notes.

OWNER CONFIRMED Bosch15719 installed for active paired-20261030-155954-154a4cd3-
v015-new-sensor-test. Sensor confirmation saved in bundle sidecar. Earlier154014
sensor identity remains unconfirmed; do not label it old/new by inference. Do not
interrupt active run. Warm test does not verify cold heater/readiness equivalence.

LATEST SENSOR CHECK REVIEW — 2026-10-30: reports/2026-10-30-v015-sensor-check-review.md.
154014 pair saved/preserved as logs/2026-10-30-v015-sensor-check-01; starts172F,
warm NB switches, idleWBmean1.002–1.017, RPMdip760 remains. Seven state fields
blank including CL/FMEm; do not infer No. 155435 new-sensor-test pair partial:
VCM start failed, noVCMfiles. Separate VCM screen showed warm CLYes; no recording
stopped. Sensor identity/change timing awaits owner. No urgent NTK purchase or
tune edit justified; warm trace cannot verify prior cold readiness problem.

LATEST REVIEW — 2026-10-30: see reports/2026-10-30-v015-p1132-review.md.
Keep v015 unchanged; prioritize upstream O2 heater/signal-path testing with exact
2004 SVT wiring. New LoopState20 capture: CL enters84.468s, FMEMYes/CLNo160.942s,
O2B1FailYes239.196s, CLYes/FMEMNo311.199s, O2FailNo317.096s. Early near-zero NB
with rich WB, trim+26.9 then-24.4; later warm WBmean~1 and normal switching.
Actual P1132 Current confirmed, no freeze-frame. Flag times are not DTCset times.
This supersedes the pending-review and active-recording entries below. No active
recording; no v016 selected. Hardware fault plausible, component not proven.
Do not substitute another unattended idle run or blanket fuel/spark edit for
heater/current and physical signal verification. LoopState20 populated; Heater18
still unvalidated. InjectorPW/actual differential pressure remain missing.

LATEST P1132 CAPTURE STOPPED/SAVED: owner parked/shutdown; pair151051v015
saved/exported. Retry read independently confirmed0x10P1132Current,
ConfirmedEmissionsDTCs1/MILTrue. ReadFreezeFrames returned"No Freeze Frames
detected." No codes cleared/reset. NativeHPL/CSV/SQLitebackup and DTC evidence
preserved logs/2026-10-30-v015-p1132-01; integrity/finalization passed.22961VCM
rows1.306-527.314s, no exportgaps, provisionalSCGoffset+.388894s. Actualprofile
saved afterstop, not guaranteed initialsnapshot. No active recording. Deep
rich-fault review pending; no faultcause/sensorreplacement/tunechange inferred.

NEW CURRENT DTC OWNER REPORT during active151051v015 run:0x10P1132 LackOf
HO2S11Switches SensorIndicatesRich. Reportmarked2026-10-30~15:17local;
occurrence/freeze-frame unverified. VCMsnapshot1595RPM170F,CLYes,Stoich,
O2.791V,displayedSTFT-16.6%. Do not equate with routineO2switching or provebad
sensor; distinguish actualrich versus biased/stuckinput using saved aligned
WB/pressure/wiring evidence. Preservecodes; no clearing/reset or tuningedit.
Vehiclemotion/parking notconfirmed, keepactivecapture; no diagnosticdialog
or profilechange while potentiallydriving. Owner advised safelypark/stopengine
if stumbling/powerloss, and postpone departure if stillparked.

ACTIVE OWNER STARTED2026-10-30: pair151051-2c4afe95-v015-idle-drive-off.
Bothrecorders confirmed; engineon owner planspizza tripafterwarmup. Livecheck
1244RPM124F/CLYes, ERT103,STIT+.20/LTIT-.06; SCGvalidlambda.974 atelapsed145.6.
Do not restart, switchprofile or interruptrecording; actualactiveprofile snapshot
notyetinbundle, preserveafterstop. User advised unresolvedstalls/no roadreadiness
confirmation. On parked/arrival report stop/export matchedsession. Ticketdraft
not submitted; freshInfoLog stillpending and canwaituntilcapturecomplete.

HP TICKET DRAFT PREPARED, NOT SUBMITTED: docs/hpt-support-ticket-draft.md;
private .local/support-prep/hpt-channel-request-20261030.zip includesv015HPT,
latestv015nativeHPL+actual16XML, optionalv014stale-loadHPL+actualXML andhashes.
Fresh vehicle-connectedInfoLog stillmissing; oldunpoweredreportexcluded.
Useraskedtodayplan: reconnectMPVIafterSCT, engineoffInfoLog, shortLoopState20
coverage trial thenonlyifappropriateonewarmparkedcomparison. v015unchanged.
No externalmessage/ticket created; no active recording or ECUwrite.

HP SUPPORT PREPARATION2026-10-30: user wants research FIRST, before making or
submittingticket. [Channel scope](docs/hpt-channel-request-research.md) prepared.
0x1141 ownerlead plausiblyFUELPW1 ms, NOT verifiedUJAHAS3 wireID/scaling and NOT
HPTinternalParameterID. No ticketcreated/sent. Prioritize PW, definedbase/final
fuelcommand/corrections, desired/baseidleair/limits, modelpressure/temp,purge.
CachedECMselector alreadylists O2TransportDelayTotal,FuelFlow,CamAngle/Error/
Duty,Railvalidityflags; testbeforeaskingadd. ExternalDSX/MegaSquirtPW names
aren'tnativeFord. Runtime255/staleload/restartpopulation are separate definition/
acquisition questions. FreshprivateInfoLog neededlater; no vehicleactions now.

SCT FIRMWARE SOURCE FOUND: archived officialPNID3000/RVCODEXP page20141029
lists1.2.159 release2014-04-28 for enhancedXP. Vendor explicitly withdrew
standalone firmwaredownloads, directsautomaticupdater. No correctXPpayload
retrieved. Shared1.1.155 GoogleDrive uploader expressly excludesXP; reject
for owner'sdevice. No firmwarewrite. See updated SCTcompatibilityresearch.

SCT OBJECTIVE UPDATE: owner only needs SCTdatalogging, HPT handlesflashing,
and is open to suitablefirmware recovery. Do not insist on retainingSCTflash
capability. Still require correctX3/3000 firmware provenance/hardwarematch
and vehiclelogging compatibility. No verifiedrecoveryimage/path yet; no write
started. SavedBEF hash/size reverified. Updater drivercheck passes but partnumber
missing/deviceblackboxes unresolved. Device-only repair, novehicle stockrestore.

SCT RESEARCH2026-10-30: [compatibility findings](docs/sct-x3-compatibility-research.md).
Historical SCTX3 application guide lists2002-2004FocusSVT CustomOnly. No verified
patchnote identifies firmware removingSVTsupport or proves1.2.159lastcompatible.
OfficialSCT X3Manual page modifiedMay17,2024 says X3/partnumbers unsupported,
includingtroubleshooting/unlock/assistance; modificationdate notexactEOLdate.
Correct prior assurancesSCTwillrepair/recover. Keepfirmwareunchanged; distinguish
vehiclefirmwarecoverage, LiveLinkcompatibility andproductservicewithdrawal.

SCT identity owner-confirmed: X3 part3000, firmware1.2.159. Serial provided
privately; omit from tracked docs/output. LiveLink still fails part-number
identification; not proof missing vehiclePIDs or firmwaretoo old. Older
Herrod/SCT GenII manual lists Ford1.2.131 minimum, not proof compatibility
with current2.26.294.2. Next boundedconnection retry after full device
power cycle/mainmenu; no updater firmware/reset/stockrestore action.

LIVELINK ATTEMPT2026-10-30: owner connected SCT USB+vehicle to seek injectorPW/
fuel model channels. Windows SCTDriverV10.11 reportsOK; LiveLinkGenII2.26.294.2
installed/launched. VCMScanner disconnected and not recording, verifiedmenu.
LiveLink controls reject programmaticclicks Win32AccessDenied5; user clicked
CheckCommunication and received "No part number found in SCT device. Please
contact SCT support for help." Device/vehicle identity not validated; no usable
SCTPID list yet. Need handheld model/partnumber/firmware info and supported
connection troubleshooting. No firmware update, recovery, stock restore or
ECU write performed. Do not infer SCTdevice type from pre-checkdefaultlabel.

LATEST AUDIT2026-10-30: [v015 pressure/injector audit](reports/2026-10-30-v015-pressure-injector-audit.md).
Read-only, all16 binary hashes unchanged. Pressure multipliers32062/32060/
32064 all6values1.00; offset32052 all7values1.0000; repeateddisplayaxis40psi.
Transfer7596 all40, ref40, compEnabled,6950zero. Desired43000 all40;43005AAT
Adder variesdisplay40to62, matchinghelpadds vsambient, but do NOT sum40+40
or infer actual command/fallback from UI.43010railtempconstant nonflat; no
verified UJAHAS3 command/measured/substitute injector-pressure path.
CRITICAL CORRECTION: coldbase44512 at120-190F=1.03 and decay44516final60s=.03
nominallycancelto1.00. Do not zero decay alone as an assumed rich-fueling fix.
Generic hot/soak/runtimeinjector tables not exposed inNavigator searches.
No new tune. NextLoopState20 validation plus realpressure evidence; PWmissing.

RELAY TRIGGER RESOLVED2026-10-30: owner confirms ignition-on trigger and
fuel-shutoff-switch interruption, battery relay pump feed bypasses ECU/FPDM
speed control. No repeat trigger-source question. Owner asks about expected
fuel/pressure response mismatch; investigate actual injector model input
(requested vs reported/modeled pressure), not unused duty alone. v015 retains
flat40transfer/reference, enabledpressurecomp and6950zero. No proven causal
model fault or authorized wiring change; physical pressure/voltage unmeasured.

PUMP WIRING OWNER-CONFIRMED2026-10-30: direct battery feed through relay,
bypasses ECU/FPDM speed control. Do not re-ask whether FPDM still modulates
pump power. Relay coil trigger source and actual loaded pump-terminal voltage
remain unknown. Battery relay feed is not regulated constant voltage. Preserve
shutdown/interlock behavior; no wiring changes authorized by this clarification.
ECU injector-pressure compensation/model remains a separate issue (enabled,
flat40psi transfer/reference retained); no automatic calibration edit.

NEXT CHANNEL PLAN2026-10-30: baselineFuelAirRuntime16 retained. Prepared
LoopState20 adds saved12944/12978/12947/12923 at1s; HeaterState18 separately
adds12933/12925 at1s. XML/unchangedparent/uniqueID checks passed; NOT loaded or
live-tested. Validate short separatetrial, preservecore16 if optionaldatafails.
No injectorPW definition verified; no inventedPID or use of flat40psi as actual
pressure. v015unchanged, nothingrecording. Currentcard describes sequence.

LATEST v015124803 SAVED/STOPPED at owner-reported small-dip onset. See
[onset review](reports/2026-10-30-v015-onset-review.md). All16 fields populated;
VCMrestart nativeoffset+60.108634s provisional,3VCMgaps. CLNo initially,
Yes47.040s/78F, No146.427s/118F, Yes426.842s/158F. Minimum799RPM420.189s
whileCLNo/startup fuel, desired912; no retainedzero/stall. STITnear-.30lb/min
while LTITzero, thenlessnegative; not verifiedclamp. Runtimecaps255. EndECT162F,
not fullywarm validation. Nextread-onlycold/warmfuel-state and baseair/STIT
investigation; no new numerical tune. v015 remainsowner-installed; no logactive.

OWNER VCM RESTART DURING v015124803: owner restarted only VCM recording to
populate all values; SCG left running. Separate restart note saved in bundle.
Original manifest vcm_start timestamp no longer defines VCM origin; establish
new native alignment and do not assume earlier VCM startup segment preserved.
Live afterrestart1518RPM/88F, FuelStoich/CLYes, STFT9%,O2.752V. Engine running
and warming, not yet900RPM settled. Do not infer engine restart from log restart.

CURRENT LIVE v015: owner clarified prior missingSCG was ignitionOFF, not
adapter fault evidence. Retry pair20261030-124803-22ef9d06-v015 confirmed both
recording12:48:37 local, Fuel Air Runtime16. Automatic600s stop/export about
12:58:37 is backstop; inspectmanifestcurrentstate. Logger tracker
.local/current-v015-capture.json. VCM start acknowledgement took32s; use native
metadata and event marks carefully. v015 owner-installed; no agent ECUwrite.

LATEST2026-10-30: owner confirms v015 write complete; installedv015, no agent
ECUreadback. Owner reports CEL off; P0320 resolution not established. Loaded
Fuel Air Runtime16 after saving prior28 config. Read-only DTC request made;
accessible display did not expose counts/status, so no clean-code assertion.
Pair124621-456b4410-v015 startup FAILED: COM4 opened, no valid SCG stream in20s,
bounded attempt ended; Scanner recording never started. No active recording.
Owner asked to check SCG ignition-on power/serialOUT, keep engine off.
Tracker logger .local/current-v015-capture.json. Retry only after readiness;
do not call partial startup an engine validation. Actual profile snapshot saved.

LATEST: v014 trip190812 saved/exported; owner reports terrible versusCL,
no low-end, hard pull-away and severe power loss. v014 rejected; no further
acceleration testing. [Trip review](reports/2026-10-29-v014-drive-review.md).
Prepared [v015 restoration](tunes/v015-restore-closed-loop.md), NOT FLASHED.
Built from exactv013; saved/reopened fullcomparison onlyNotes vs v013. Relative
to v014 restores ECM32731 two0->200 cells, nothing else.236525bytes,
SHA2569D3C4FF9CD68D24665957CC6FDB310C51B246E8DD3D0F439A0E33D2EFA936EFD.
All prior binaries preserved. Last owner-installed remainsv014 until confirmed.
No logging active. v015 restorespreferredbehavior, NOT stallcure/roadacceptance.
Trip CLNo all51725rows; AirLoad frozenfirst119.3s, command/STFT redundant,
SCG4disconnects and provisionaloffset+2.585s. No blind timing/fuel correction.

LATEST ACTIVE TRIP: owner requested logging trip to girlfriend house and next
tune investigation. Pair paired-20261029-190812-6d5aebc2-v014 confirmed recording,
Drive Torque Diagnostics28 loaded after saving previous13 profile. No automatic
cutoff; on owner parked/arrival report stop/export through matched dashboard.
Tracker logger .local/current-trip-capture.json. Last confirmed installedv014
carried forward; no subsequent flash reported. Owner advised v014 is stationary
diagnostic-only, stalling unresolved and driving not recommended; recording is
not road/boost acceptance. At livecheck2734RPM/192F, CL Active blank; unknown,
not No. Preserve run/profile; don't switch while driving. v015 investigation
authorized but no numeric change selected/prepared; wait for completed trip
evidence and do not stack speculative fuel/air edits. No agent flash.

LATEST RESULT: [v014 review](reports/2026-10-29-v014-open-loop-review.md).
Pair185239 saved/exported after360s; nothing recording. Owner-confirmedv014
remains installed, not accepted. CLNo all17897rows; STFT0 after60s. Dips grow
despite open loop:60-150s lambda.938/RPMsd11.2;200-260 lambda.999/min756/sd32;
late lambda1.043/sd36. No poststartzero in recordeddata;3.422s VCMgap315.895-319.317.
Astra independently confirms feedback not necessary for this deterioration;
does not establish stall cause or exclude feedback aggravation. Early O2 near
.005V despite richwideband is a separate heater/readiness/input-validity lead.
Next focus startup compensation/delivered fueling, actual injectorPW if available,
pressure video and runtime/idle adaptation. New Fuel Air Runtime16 XML checked
only, NOT loaded. No v015 or road/boost acceptance; no automatic rollback.
Older active-capture/prepared-only states below are historical.

LATEST LIVE STATE: owner confirms v014 installed, engine not started at that
confirmation. Pair paired-20261029-185239-7271be01-v014 started; both recorders
confirmed22:52:42Z. Active saved Return Fuel Trial13 copied to bundle. Native
detached helper auto-stops after360s (about18:58:42 local); inspect manifest,
not this note, for current state. Owner must remain at controls; compare loop
state/mixture after start, no throttle/load changes. No agent flash/readback.
v014 is installed but not accepted. Tracker in logger .local/current-v014-capture.json.

CURRENT DECISION: owner explicitly requests Astra review and adjustments for
progressive closed-loop-specific deterioration. Astra independently reviewed;
closed-loop fuel control is the primary test hypothesis, not a proven failed O2.
[v014 isolation](tunes/v014-warm-idle-open-loop-isolation.md) is now prepared,
saved/reopened/compared, NOT FLASHED/TESTED. Exact parentv013; only ECM32731
0/1500RPM200->0 and Notes. Full comparison verified; all7 saved threshold
cells0; other5 were already0. All14 previous hashes preserved. Installed remains
owner-confirmedv013. No active recording. [Test card](docs/v014-open-loop-isolation-test.md).
Warm900RPM stationary-only; no road/boost. Same measured-lambda comparison
essential: richer OL stability does not prove loop dynamics. Existing cold
decay ends0.03 at60s warm ECT; no correction bundled. LTFT learning Disabled,
B1bias table32905 allzero; no justified feedback gain/delay edit identified.
P0320 timing unknown; actual stall owner-confirmed. No agent ECU writes.
Earlier no-v014/loop-disable statements below are superseded only by this
bounded diagnostic candidate; no permanent OL recommendation.

Latest capture completed: paired-20261029-181853-592da567-v013-2 saved/exported;
owner reports increased instability on closed-loop entry. No separate v013-2
tune/flash verified, label only. See [follow-up](reports/2026-10-29-v013-closed-loop-followup.md).
All13 VCM fields; CL enters16.172s/999RPM/174F, all Spark Source Idle Feedback.
Later30-150s mean900.41/min826.75; last interval min825.5, no stall in recorded
rows but7.12s export gap150.209-157.329. Native metadata offset+24.631s disagrees
with using command timestamp byabout22s; provisional cross-device alignment.
Initial fast-idle target1392 then896 confounds a closed-loop-only comparison.
No v014/loop-disable change. Both stopped; engine shutdown advised. No monitor.

Latest clarification supersedes dropout emphasis: owner confirms engine
genuinely STOPPED and recovered without starter use. Treat as actual stall;
zero scan RPM alone does not prove speed-signal loss. P0320 occurrence time
unknown: neither proven cause nor proven consequence/red herring. Review
pre-stall air/fuel/spark and narrowband-feedback hypothesis alongside code
evidence; no sensor replacement, loop-disable or tune change selected.

Latest owner evidence: pending P0320 Ignition/Distributor Engine Speed Input
Circuit, reported after v013 review. Occurrence time/freeze-frame unknown;
do not claim code set at42.5s. Prioritize ignition/engine-speed input diagnosis,
preserve codes, inspect CKP/CMP/coil/HT wiring and power/grounds, including old
tach-tap area; purple SCG RPM remains disconnected. No proven failed sensor or
confirmed common cause. Use exact2004 SVT wiring/pinpoint data. No routine
running comparison, v014 or closed-loop-disable experiment selected. Owner's
narrowband-hunting concern remains a separate hypothesis; original disabling
intent unknown. See updated next-stationary-test and v013 deep review.

## Current vehicle and logging state -- updated 2026-10-29

Latest deeper review: [v013 diagnosis](reports/2026-10-29-v013-deep-review.md).
Owner now clarifies STALL WITH SELF-RECOVERY, NO STARTER INPUT. This supersedes
stumble-only wording below; it does not prove crankshaft rotation stopped.
Full manual VCM includes544.5RPM before SCG starts;745minimum describes only
late overlap. ECU reports zero RPM then cranking/startup; closed loop returns
69.404s. No confirmed CKP fault/reset or v013 cure/regression. Later132.619s
745RPM dip and nominal133.684s lambda1.281 occur under Idle Feedback. Need
DTC preservation, RPM/run-state integrity and trim/command definition review
before another tune. New Fuel Runtime Trial14 adds exact saved2131 at1s to
existing13; XML checked, NOT loaded/live-tested. Next-stationary card updated.
No recording or v014. Both captures saved. Original context preserved.

Latest completed test: owner confirms v013 installed. First pair175003 and
manual-v013-20261029-175707 are saved/exported; nothing recording. See
[initial v013 review](reports/2026-10-29-v013-first-review.md). First pair STFT
blank/ECT only170F; recording-only restart restored STFT with unchanged13-field
Return Fuel Trial profile. Manual warm capture has all13 fields. SCG starts
late, approximately VCM57.3s; metadata-only alignment, not sample synchronization.
At VCM42.525-42.585s reported RPM briefly zero with Cranking/Crank Runup then
startup state. Owner confirms stumble, NO starter use. Do not label this a
confirmed shutdown/restart. Investigate RPM/state discontinuity before another
tune; no proof of crank-sensor failure or ECU reset. Later overlap mean899RPM,
minimum745; does not describe earlier event. Both SQLite finalization and
integrity verified. Engine shutdown advised.

v013 remains experimental, not accepted for driving/boost or established stall
fix. Exact parent v012; only ECM6950 multiplier0.484to0 plus Notes. Saved,
reopened and compared; targets900/900, gain1.000 and floor-6 retained. File
233629bytes, SHA25678AAD3DC86BE89835C333BC95EF5CE1359DD5B4CAAD2645032C1A64F49505B70.
Flat40psi transfer/reference and enabled compensation unchanged. No further
calibration edit or agent ECU write. Owner performs flashing.

**SCT backup received:** [intake/format status](reports/2026-10-29-sct-backup-intake.md).
Owner-supplied desktop BEF copied unchanged to ignored
`backups/sct-original-20261029.bef`,7,420,760bytes, hash verified. Full source
identifier/path remains private. BEF is a device backup; no decoded strategy,
table values or direct supported conversion established. Device Updater/drivers
installed, no SCT calibration editor identified. No companion readable export
beside it. Do not claim a factory comparison, rename it to HPT/BIN, upload it,
buy conversion or restore stock. A supported readable export/matching strategy
reference is needed. Current-tune audit remains valid; no ECU actions.

**Read-only tune audit completed:** [calibration findings](reports/2026-10-29-v012-calibration-audit.md).
Highest-priority model concern: ECM6950 Manifold Vacuum Multiplier0.484, whose
matching Editor help gives zero for a return-style conversion, versus the
owner's1:1 return system. Audit together with flat40psi transfer/reference and
enabled compensation; no isolated scalar flip selected. Warm airflow matrices
44240/44243 reduce the pre-correction contribution roughly21% from165to200s
at188F; real engine runtime must be measured, not assumed from recording time.
VCT enabled/intake-only with low-RPM angle values-22/-25deg at1000RPM/load.2/.3;
actual cam tracking absent. These are leads, not established causes or final
commands. Cylinder-airmass idle filtering0.11 enabled; anticipation/ACDC disabled.
Numerical idle integrator/learning limits were not found; no values inferred.
No tune edits/saves or ECU actions. SCT original/stock backup is on another
laptop, not yet available; copy file unchanged, check format/strategy, never
flash stock to obtain comparison. New runtime16 profile is prepared only.

**Gauge video received/reviewed:** [pressure/video analysis](reports/2026-10-29-pressure-video-review.md).
File PXL_20261029_200524935.mp4 matches preceding stationary run, not food trip
or earlier stall. Manual frames mostly37â€“38psi at idle, near37 around nominal
764RPM dip; no large visible collapse. Video alignment is metadata-only
(video=VCM+34.065s nominal), not synchronized telemetry. No actual stall in
clip. Earlier stall pressure remains unknown. Numeric AFR text was initially
misread as HLD; no hold mode established. All15 channels populated here; LTIT
steady near-0.201lb/min, STIT/IAC rise through recovery under Idle Feedback.
Next focus: offline integrator/eligibility and actual IAC/air-path/load review.
No new run or tune change. Video/manual readings preserved privately.

Latest completed review: [v012 short drive](reports/2026-10-29-v012-drive-review.md).
Owner clarifies driveway stall was while starting from a stop, not untouched
idle. Full stall125.174s/restart; final parked225â€“274.5s mean901.34/min708.5,
all exported Spark Source rows Idle Feedback. Additional754RPM recovered dip
and load-like IAC/voltage transition near252â€“256s; fan unconfirmed. No gain/MBT/
air/fuel edit selected. Previous spontaneous parked stall remains separate.
Both logs saved/finalized; no active recording. Prior stationary gauge video
still pending; do not treat it as trip-time pressure evidence. Owner reports
mostly good driving with instability. Mechanical repair remains owner-confirmed.

**Latest owner update:** car/suspension reported fixed; mechanical driving hold
retired on owner report, not agent inspection. Owner requested logging a food
trip despite unresolved stalling. Continuous paired capture
`paired-20261029-161604-b543b769-v012` started with Drive Torque Diagnostics28,
both recorders confirmed. No automatic cutoff; stop/export on owner's return
while parked. Inspect manifest for current state. This is capture authorization,
not road-readiness/boost acceptance. User cautioned about unresolved stall and
no laptop interaction while driving. No new tune flash reported.

Prior pressure-video capture `paired-20261029-160556-870a7d58-v012` finalized
cleanly on detached launch, all15 fields populated, no recorded stall/min763.75RPM,
ECT166â€“188F, one132.265â€“136.264s export gap. Owner video still transferring/not
received. Owner adjusted regulator back to43psi engine off before that run;
this supersedes41psi as latest reported setting, not the ECU flat40psi transfer.

Latest owner context: stall untouched, A/C and defrost OFF; owner does not
believe radiator fan related (not a measured fan-state confirmation). OEM
pressure sensor still awaiting installation. Digital GlowShift sender is at
regulator; owner reports41psi with engine OFF/pump ON. Keep this static reading
separate from earlier43psi base report and ECU's invalid flat40psi transfer.
No pressure/injector adjustment justified from that one reading. Do not ask
these same context questions again. Gauge video availability is not confirmed.

Logger launch evidence: detached Windows Start-Process launch survived145s
with Qt/simulated worker,1635rows,144.4s sample span and clean exit. No hardware
capture exercised; original exit cause remains unknown. For future sustained
capture use persistent native launch with stdout/stderr/status evidence rather
than assuming a tool-owned long-running process survives the turn. No real
recording is active. Test evidence is under the logger's ignored `.local/`.

**Owner correction: v010 also stalled occasionally, uncaptured.** Owner says
spark changes improved steadiness between random stumbles. Withdraw the v010
rollback recommendation; absence of a captured v010 stall was not absence of
stalling. No gain regression established. Current plan is the revised
[onset/handoff diagnosis](docs/post-stall-comparison.md), not a tune change.
Inspect initiating disturbance and recovery arbitration separately. Latest
trace includes30degrees/Base-MBT then8degrees/Idle Feedback near739RPM before
further collapse; asynchronous export is not proof of exact ECU chronology.
No new recording, reset, gain/air/fuel change, RPM change or v013 selected.

The earlier v010 rollback proposal is superseded by the owner correction above.
All13 hashes matched the last check; no tune created/flashed. Installed state
remains owner-carried-forward v012. Its actual stall is a failed stability
outcome, not proof gain caused the failure. Establish logger persistence before
another unattended long recording. No recording is active.

**Latest event: actual stall in the five-minute test.** See
[stall review](reports/2026-10-29-v012-stall-review.md). Owner advised leave engine
off; routine running comparisons paused pending event review/context. VCM stall
around109â€“110s captured; SCG committed data covers it but its process exited
unexpectedly and database was not finalized. Both sources preserved; VCM manually
stopped/exported. No monitoring active. Do not repeat a stall deliberately.
Idle Air15 had CL Active/STIT blank in this run despite a prior complete test.
No tune edit or ECU write performed. This supersedes the running-plan text below.

Current acquisition selection: [operating profile policy](profiles/operating-profiles.md)
and [second survey](reports/2026-10-29-core-profile-selection.md). Core Stationary12
is the default parked profile and is loaded/saved; Scanner/logging stopped.
All12 fields populated in five additional65-second captures. Target Idle Air15
populated all15 once and is the next provisional choice for adaptation/source
analysis. Target Electrical Load15 retained core but fan/A/C fields were blank;
do not use it as a load measurement. The agent selects/loads/saves profiles
between stopped/exported sessions, according to the policy. No tune changes.
The28-channel file is a historical driving/fuel diagnostic fallback, not the
default parked core. Its speed/trim/status coverage still needs per-run checks.

Latest completed work: [31/28/34-channel survey](reports/2026-10-29-channel-survey.md).
Three65-second parked pairs saved on2026-10-29; logging stopped and28-channel
fallback restored/saved. STIT populated in31 but blank in34; Idle Speed Source
populated in both. LTIT, fan PWM and A/C clutch remained blank. Neither expanded
profile is accepted for routine tuning capture because core coverage was lost.
The28 capture reached709.25RPM with Idle Feedback, not Base/MBT, at its minimum.
Use per-session coverage; do not assume adding/removing channels alone caused
the changing availability. Next is a smaller-core acquisition survey, not an
automatic tune edit or repeated full archive review.

Owner reports the driver-side front strut's large center shaft has sheared,
with spring retention compromised. On2026-10-29 the owner explicitly confirmed
the vehicle is safe for stationary operation. Accept that confirmation for parked
engine-running/channel-survey tests; do not repeatedly request it. This is an
owner report, not an agent inspection or confirmation of repair. Driving tests
remain on hold. Do not suggest lifting, loosening the damaged assembly or
improvised spring restraint. No log has been started by this state update.
Latest review: [09:34 recording](reports/2026-10-28-idle-followup-and-mechanical-hold.md).
Prepared next test: [stationary card](docs/next-stationary-test.md),2026-10-29.
The31/34-channel trials were loaded and captured, but are not accepted as routine
profiles. The later12/15-channel selection above supersedes the initial28 fallback.
No recording remains active; no road portion.

## Iterative logging: fast path

Use the [datalog pathway](docs/datalog-workflow.md) and
[channel coverage register](profiles/channel-coverage.md) for every new run.
These are standing operating instructions, not a reason to delay capture.

- If the owner says "log now", prioritize preserving/starting acquisition.
  Inspect actual recording state first. Never stop an existing VCM recording
  just to create a paired folder. Start the missing recorder and document the
  separate clocks. Do profile research after the event is captured.
- Read current state below, the latest review and the new run card first.
  Use the evidence index to select comparison sessions. Do not reread or
  reprocess the entire archive on each turn. Revisit older evidence when a
  hypothesis, parser correction or hardware change makes it relevant.
- Ask only about changes since the last confirmed run. Carry forward explicit
  owner confirmations, including meth OFF, disconnected RPM wire and installed
  tune; label them owner-reported. A restart does not establish a new flash.
  Unknown fuel/accessory details remain unknown, not silently carried forward.
- Batch Git status and catalog hash/size verification once per analysis or
  candidate-preparation pass. Recheck changed files before use. Do not repeat
  Editor discovery for unchanged parameters with preserved verification.
- Use proven helpers in the logger's ignored `.local/` folder, but inspect their
  guards, expected profile and session arguments before use. Discover fresh
  process/window handles. Never replay a hardcoded handle or old session path.
  When a method times out, use the documented native-window fallback rather
  than repeating the same blocking UI Automation search.
- Identify the recording by the dashboard/session manifest and exact source
  folder, not just the newest modification time. Verify both recorders and
  increasing samples before saying "both recording". Report partial capture
  promptly. Do not promise unattended stop/monitoring unless it is running.
- Preserve originals, the actual saved channel configuration, export settings,
  manifest and owner event notes together. Use the [run card](docs/datalog-run-card.json).
  A candidate profile on disk is not proof it was loaded. Never overwrite a
  completed session or silently replace an original export with a new export.
- Analyze new/changed inputs first. Record input SHA-256, analyzer version/hash,
  selected columns, alignment method, window definitions and output paths in
  the private session analysis record. Reuse prior outputs only when those
  dependencies match. No incremental cache is implemented yet: existing
  `.local/build-roadmap-evidence.py` is a full inventory, not a cached runner.
  Promote a repeated analysis into a parameterized helper when warranted;
  do not keep cloning scripts with hidden session-specific assumptions.
- Inventory all available channels and blank spans before selecting diagnostic
  plots. Keep native HPL/SQLite/raw bytes and full-length exports, including
  startup, transient and recovery periods. Do not crop the only preserved copy.
  Expand coverage through the register; retain reasons for deferred channels.
- Keep core requests fixed during a comparison series. Trial a small group of
  additional channels in a separate stationary capture, audit the saved data,
  and retain additions only if core coverage/timing remains usable. Do not
  assume every exported row is an independent ECU sample or a constant value
  means a dead sensor. Blank, zero, unavailable and invalid are different states.
- Each review must return: capture quality, matched comparison, event chronology,
  competing explanations, decision (retain/change/insufficient evidence), and
  one next run card. Include minima, dip duration/recovery and source transitions,
  not averages alone. Update the evidence index and coverage register with new
  facts; keep uncertain hypotheses separate from verified behavior.
- Make each iteration faster by reusing verified facts and analysis, not by
  shortening the observation window needed to capture the stated event. Never
  claim a fan cycle or post-drive validation if it did not occur.

## Current objective and state -- 2026-10-28

Hold **900 RPM**. The owner explicitly prioritizes stability, then drivability,
and is comfortable with900 on this turbo application. Do not resume the older
800â€“850 goal or lower the target without a new explicit owner request.

Read the [stability/drivability roadmap](docs/stability-and-drivability-roadmap.md),
[vehicle record](vehicle.json), [catalog](tunes/revisions.json),
[coverage index](reports/2026-10-28-log-evidence-index.md), and relevant dated
reviews before choosing changes. Check Git status/history and every cataloged
HPT hash/size before relying on a calibration. Preserve the existing safeguards
below; ordinary tuning work does not authorize publication or ECU writing.

- Owner-confirmed installed file: **v012-idle-spark-gain-1p0.hpt**,900RPM and
  idle spark proportional gain1.000. No agent ECU write or readback.
- [Latest v012 review](reports/2026-10-28-v012-stability-review.md): warm mean
  900.33RPM,min751; inferred fan/load min817.75 and recovery min816, with
  no Base/MBT rows in those two windows. Timing improved observationally;
  loads/history are not fully matched. Post-drive v012 validation remains.
- The owner-directed875 draft was withdrawn before completion/flashing, never
  cataloged, and archived under ignored `.local/withdrawn-candidates/`.
  Editor was restored to verified v012. **No v013 tune is currently justified.**
  Do not create a duplicate/no-op revision or revive the875 draft.
- v010 gain1.500 is the earlier tested comparison/rollback; owner reported good
  cruise and acceleration. v011 gain1.250 was prepared but never flashed.
- Preserve repaired-fan baseline: low195/190F, high225/215F. Old resistor-bypass
  logs are a different hardware condition; don't pool them as matched tests.
- v009 had severe driving/parked dips. The repeated Base/MBT handoff can be a
  recovery response and still participate in an unstable cycle. Preserve
  corrective spark and investigate evidence rather than dismissing the owner
  or disabling controls based on a label. See the cross-session/handoff reviews.
- Fuel regulator: owner-confirmed43psi base,1:1 manifold reference. OEM sensor
  installation at the regulator with its own reference is planned, not complete.
  ECM7596 is flat40psi across all inputs, inherited from v001; injector pressure
  reference40psi/compensationEnabled. The40psi PID is not measured pressure.
  Preserve pressure calibration until compatible hardware/signal and pump/
  injector behavior are verified; do not blindly change40to43.
- Water/meth is completely OFF for all future tests unless owner changes it.
  Purple SCG RPM wire stays disconnected; no controller-setting writes.
- A separate31-channel Stability and Drivability Trial XML restores LTIT,
  STIT and Idle Speed Source using actual saved definitions/header provenance.
  It is prepared only, not loaded/live-validated. Current28-channel profile
  populated every requested field in today's run; availability varies by run.
- Commanded-equivalence and STFT exports are algebraically linked. Do not use
  them as independent fuel command/error measurements. SCG/VCM timing is
  provisional and recalculated per session. No direct fan command, dedicated
  clutch switch or validated knock-retard/cylinder misfire evidence is assumed.

The next work is measurement and unchanged-v012 comparison, not an automatic
parameter change. Define one causal hypothesis and a measurable keep/revert
criterion before a future v013; owner handles flashing.

## Vehicle-specific constraints

- Owner confirms water/meth completely disengaged and directs that all future
  testing assume OFF unless explicitly changed. Activation when enabled is
  owner-reported7psi; that does not establish the tune's boost dependency or
  authorize boost testing. Do not repeatedly ask its state without new evidence.
- Earlier owner feedback included no CEL; later near-stall events and current v012 results supersede that early description. No CEL is not a DTC scan. Use current state and dated reviews for installation evidence.
- This is a previous-owner turbo calibration, not an established stock tune.
  Exact injector characterization, MAF identification, boost limits and
  water/meth dependency remain incomplete; consult the vehicle record.
- Respect the 1:1 referenced return fuel system. A nominal injector flow or
  reported 43 psi engine-off pressure is insufficient to derive injector data.
- Keep the temporary fan-resistor-bypass pathway visible in every descendant
  revision until repaired and explicitly retired. v003 introduced 195/190 F
  high-speed thresholds; restoration after repair is 225/215 F, preserving
  unrelated later changes. Calibration does not establish wiring integrity.
- v004 is a stationary warm-idle closed-loop-entry experiment. Read its note
  for the 1,500-2,000 rpm interpolation effect, retained 254-second gates,
  LTFT-disabled state, and rollback. Do not generalize idle results to boost.
- Investigate IMRC after idle/fueling stabilization, before final power work.

## Evidence before calibration

1. Establish the parent actually tested and distinguish prepared, saved,
   compared, owner-reported flashed, log-supported tested, and accepted states.
   A file on disk or open in Editor does not establish the ECU's current tune.
2. Identify one hypothesis, the supporting data, exact proposed parameter IDs,
   units, axes/cells and expected behavior before editing. Check controller-
   specific Editor descriptions and official HP Tuners references when needed.
   A plausible threshold explanation remains a hypothesis until tested.
3. Prefer one causal change per revision. Do not simultaneously alter MAF,
   injector data, closed-loop gates, ignition and boost to chase one symptom.
   Evaluate interpolated regions and inherited changes as well as edited cells.
4. Preserve corrective idle spark behavior unless evidence supports changing it.
   Review voltage, accessory/fan loads, air control, fueling and spark sources
   together. Do not flatten timing merely to make the trace appear steady.
5. Do not invent tune values, sensor scaling, channel IDs, knock limits or
   AFR/boost targets. Obtain missing information when it blocks the next stage;
   continue independent review and documentation without unnecessary approval.

## Files and verification

- Preserve numbered tune binaries and original reads. Assign the next revision
  for calibration edits; never silently overwrite a published numbered tune.
- Check every cataloged file's SHA-256 and byte length before relying on it.
  Stop and reconcile any mismatch. Hash equality verifies identity, not internal
  calibration correctness or successful flashing.
- Use VCM Editor for HPT edits/comparisons; do not hex-edit proprietary files or
  infer calibration differences from binary byte differences.
- Reopen the saved candidate and compare against its explicit parent. Verify
  every intended cell/scalar, all unexpected differences, and embedded Notes.
  An unverified comparison must remain labeled unverified.
- Record the filename, parent, exact changes, retained settings, verification,
  SHA-256, size, scope, rollback and test outcome in the revision catalog and
  revision note. Update vehicle state and the history when evidence changes.
- Treat desktop automation as state-dependent: discover current process/window
  handles and controls, inspect before acting, and verify afterward. Old private
  scripts contain session-specific handles; do not replay them blindly.
- Keep VINs, license/interface IDs, original reads and raw logs in the existing
  ignored private locations. Numbered tune binaries are intentionally tracked
  locally. No remote publication is authorized by ordinary tuning work.

## Logging and analysis

- Use the documented working idle/cruise channels and layout in
  [scanner guidance](profiles/README.md). The generic fuel-diagnostics template
  is unvalidated. A configured channel is not proof of usable recorded data.
- Owner reports some channels populate intermittently or late. Evaluate actual
  coverage within each session; a blank snapshot alone does not establish lack
  of controller support. Historical absolute TPS was about 182-184 counts while
  relative TPS was about 0-1; never substitute one for the other. v005 tests the
  absolute-TPS comparator hypothesis with 200-count low-RPM thresholds and is
  stationary-idle-only, including its changed 1,500-2,000 RPM interpolation.
- Preserve native HPL/LOG plus CSV in a new revision/session directory. Record
  actual flashed filename, fuel, water/meth state, temperatures, accessory
  changes, SCG settings and owner observations. Never merge sessions silently.
- Derive clock offset and assess drift for each VCM/LogWorks session. Label
  metadata-only alignment provisional; do not reuse earlier offsets or derive
  pointwise fuel corrections from unverified synchronization.
- Separate commanded lambda, narrowband O2 voltage and SCG measured mixture.
  Do not treat narrowband voltage as a wideband AFR measurement. LogWorks RPM
  and WGDC previously read zero; verify usability rather than assuming validity.
- Compare temperature/load-matched windows, elapsed time since start, sample
  counts and event ranges as well as averages. CSV rows can be interpolated or
  asynchronously sampled; they do not prove exact event causality.

## Flash-readiness handoff

Give a direct decision with the exact candidate and tested scope, what was
verified now versus inherited evidence, unresolved conditions and rollback.
Distinguish file readiness, write conditions, and engine-operation validation.
Check stable write power, correct controller/file, and Editor prompts; report
unobserved conditions as unverified rather than claiming a guaranteed safe flash.
Preparing or reviewing a tune does not authorize initiating an ECU write.
The owner currently performs writes. If explicitly asked to write, establish
the required connected vehicle state before any write action.

Historical v004 procedures and rollback remain in its revision note. For current testing, use the datalog pathway and actual installed parent; do not apply an old revision-specific test or rollback automatically.

These instructions follow OpenAI's
[repository instruction guidance](https://developers.openai.com/codex/guides/agents-md/).


## Model delegation & UIA workflow

1. **Role separation**:
   - The primary agent (Argon / Pro model) is strictly reserved for datalog analysis, calibration engineering/math, hypothesis validation, and tune decisions.
   - Autonomous subagents (Model: "flash") handle all HP Tuners VCM Editor UI Automation (UIA), bulk table extractions, log copying/hashing, and mechanical catalog/inventory/reference builds.
2. **VCM Editor #32770 file dialog automation**:
   - In VCM Editor #32770 file dialogs (File > Save As, Compare > Open Compare File, and File > Open), pasting (Ctrl+V) into the filename edit box (id=1148 or 1001) does not work -- common item dialogs ignore or fail clipboard paste without native notifications.
   - Always locate the filename Edit control, click or set focus, select existing text (^a or WM_CHAR), and type character-by-character using Win32 WM_CHAR / TypeChars before submitting (WM_KEYDOWN VK_RETURN / IDOK).
3. **Table & context menu hygiene**:
   - Table context menus on C1FlexGrid must be invoked via direct WM_CONTEXTMENU messages rather than right-clicks, preserving selection states across all cells/axes.
   - Automation scripts must avoid polluting PowerShell pipeline returns when capturing table data.
