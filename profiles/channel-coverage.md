# Channel coverage register

Latest driving28 capture `paired-20261029-161604-b543b769-v012`:11,641rows,
no VCM export gaps above0.3s. Air Load HiRes, OL Conditions, Throttle State,
CL Active/Ready and OL FMEM blank; core driving/air/trim/source values populated.
Brake Pedal reported No throughout and is not established as a reliable event
marker. See [drive review](../reports/2026-10-29-v012-drive-review.md).

Later five-minute Idle Air15 run: CL Active and STIT entirely blank; LTIT/source
populated. The engine stalled; VCM was stopped/exported and SCG committed data
recovered after unexpected process exit. See [stall review](../reports/2026-10-29-v012-stall-review.md).
Do not reuse the earlier all15-present assumption for this recording.

## Current operating choice — after second survey

[Core selection results](../reports/2026-10-29-core-profile-selection.md) add five
captures: the same12 core fields populated in all five, with no export gaps above
0.3s. Core Stationary12 is loaded/saved, logging stopped. Target Idle Air15 had
complete data, including LTIT PN/ACoff previously blank in broad profiles; it is
provisional for warm parked diagnosis. Target Electrical Load15 kept core data
but all fan/A/C additions were blank. Presence is conditional and is not sensor
validation. The machine register now contains171 channel observations across
all eight survey sessions. Follow the [selection policy](operating-profiles.md),
which supersedes the initial28-channel fallback choice below.

## Completed survey — 2026-10-29

The [per-channel results](../reports/2026-10-29-channel-survey.md) now supersede
the prepared-only status of the31/34-channel profiles below. Both were loaded
and recorded in separate65-second stationary tests, with a28-channel comparison.
All three pairs finalized and exported. STIT populated in31 but not34; Idle
Speed Source populated in both; A/C Requested populated in34. LTIT PN/ACoff,
A/C clutch and fan PWM stayed blank in their trials. Availability is conditional,
not proven unsupported. Expanded profiles lost core fields and are not accepted
for routine tuning. The28-channel fallback is restored and saved; Scanner stopped.

Private `.local/channel-survey-20261029.json` contains96 observations (including
Offset) with units, full request attributes, populated fraction, distinct count,
numeric range, condition and source session. The report tabulates all requested
channels. No movement, A/C cycling, cold start or fault sensitivity was tested.

Updated 2026-10-28. Capture the broadest useful evidence that preserves event
resolution. A named channel is not necessarily a working measurement. Record
coverage per session; retain originals even when a channel is unusable.

09:34 follow-up: all 28 diagnostic columns contain data; STIT/LTIT/Idle Speed
Source additions remain absent. No saved active-profile snapshot accompanies
the recording, so the 31-channel combination remains unvalidated. Updated
2026-10-29: owner confirms safe stationary operation; parked profile tests may
proceed when ready. Driving remains on hold for the strut center-shaft failure.

## Working baseline and next trial

The [28-channel profile](2004%20Focus%20SVT%20-%20Drive%20Torque%20Diagnostics.Channels.xml)
had some populated data in every requested field in the latest v012 fan log.
That does not establish complete coverage, update rate or measurement validity.
Keep its existing IDs, types, addresses and intervals unchanged for comparisons.

| Group | Preserve in each stability/drivability run | Interpretation limit |
| --- | --- | --- |
| Idle/air | RPM, desired RPM, IAC duty, MAF airflow/volts/counts, load | IAC command is not measured valve position; load was blank in some runs |
| Spark/control | Timing, Spark Source, Torque Source | Base/MBT may be recovery and/or part of a control cycle; label alone is not causality |
| Driver/motion | Speed, absolute and relative TPS, Throttle State, Brake Pedal, Trans In Gear | Gear flag is not a dedicated clutch switch |
| Fuel/loop | Fuel Source, commanded equivalence, upstream O2, STFT, CL Active/Ready, OL Conditions/FMEM | Command/STFT exports are algebraically linked; O2 is narrowband |
| Context/faults | ECT, module voltage, Total Misfires, Misfire Detected | Zero misfires does not validate detection sensitivity |
| Separate SCG stream | Lambda/AFR, boost, commanded WGDC, quality, raw bytes, connection events | Pressure range/nonzero duty validation remains incomplete; no SCG RPM wiring |

The [31-channel trial](2004%20Focus%20SVT%20-%20Stability%20and%20Drivability%20Trial.Channels.xml)
adds LTIT PN/ACoff (2231, 500 ms), STIT/Idle Adapt (2240, 500 ms), and Idle Speed
Source (19049, 100 ms). Definitions come from saved Scanner XML and channel
names from preserved exports. **Prepared only; not loaded/live-validated.**

## Additional coverage queue

2026-10-29: the three load-context definitions below are now copied into a
separate [34-channel trial](2004%20Focus%20SVT%20-%20Load%20Context%20Trial.Channels.xml).
All31 parent definitions/intervals are unchanged; the three additions request1s.
XML and preservation checks passed. Not loaded/live-validated. Follow the
[stationary test card](../docs/next-stationary-test.md) under stationary-only scope.

Do not silently abandon these channels. Trial small groups separately, starting
with load context after the 31-channel check. Copy exact saved definitions;
IDs below are references, not sufficient XML definitions on their own.

| Priority | Desired evidence | Known status / next action |
| --- | --- | --- |
| Next: load context | AC Requested 17611, AC Clutch Engaged 17603, Fan PWM 7231 | Existing controller-selected definitions; historical missing values. Trial at 1 s for load context; owner timestamps remain necessary if blank |
| Next: thermal context | IAT 2127 | Historical blank data; verify full definition and trial at 1 s. Do not infer IAT from ECT |
| Adaptation extension | LTIT PN/ACon 2236 | Existing saved definition; trial at 500 ms if A/C-load diagnosis is needed, preserving A/C-off and STIT evidence |
| Startup/fault bank | O2 heater 12933, heater fault 12925, O2 fail 12923, ECT fail 12972, OL Active 12946, CL with O2Fault 12945 | Prior mixed/blank coverage. Separate 1-s context trial; preserve blank as unknown, never OFF/Pass |
| Pressure hardware | Fuel pressure 6502, differential pressure 12532, sensor voltage 6507 | Prior pressure fixed at 40 psi, raw near 5 V; inherited flat transfer invalidates pressure inference. Restore raw/pressure capture during sensor integration; verify against independent pressure |
| Manifold pressure | MAP HiRes 2335 | Prior zero; not a valid boost reference. Retain SCG and verify a real sensor/source before reuse |
| Still unlocated | Dedicated clutch state, validated knock retard, per-cylinder misfire, ECU injector pulse width, actual dashpot/adaptive-air demand | Do not guess IDs or substitute external-device definitions. Inspect controller availability when relevant; record missing support explicitly |
| Not knock retard | Borderline Knock 19074 | Previously blank; spark-table value is not measured knock retard |
| Limited runtime | Engine Run Time 2131 | Previously capped at 255 s; retain log elapsed time as timing basis |

These optional groups are a queue, not a new loaded profile. No current pressure,
clutch or knock measurement is claimed merely because it is desirable.

## Admission check for a broader profile

1. Save the active configuration and identify the baseline. Change only the
   candidate channel group. Preserve requested intervals for existing channels.
2. Record a separate stationary 60-second comparison at similar conditions.
   Do not deliberately provoke a near-stall or boost event for validation.
3. Audit full saved CSV headers and data, not just the live pane. Record each
   requested field as absent, all blank, partial, populated but unvalidated,
   or independently validated. Keep categorical values as categorical.
4. Compare core coverage, blank spans and time gaps to the baseline; inspect
   whether changing signals still resolve events. CSV row rate alone cannot
   certify ECU update rate. A steady signal cannot prove stale acquisition.
5. If core data deteriorates or timing is unresolved, retain the trial files
   but use the proven profile for the next engine comparison. Slow the optional
   group or split it into another diagnostic capture; do not discard core fields.
6. Append the session, actual profile hash, coverage result, measured limitations
   and keep/revert decision here. Update current-state instructions only after
   saved-log validation. Unsupported is stronger than blank in one run.

See the [datalog pathway](../docs/datalog-workflow.md) for owner actions and the
[historical scanner notes](README.md) for definition and validation provenance.


## Initial v013 outcome, 2026-10-29

Both captures are stopped and saved. STFT was blank in the first capture and
populated after an owner recording-only restart using the same13-field profile.
A stumble in the manual warm recording includes brief zero-RPM/cranking-state
reports with no starter use; v013 remains unaccepted. See the
[initial review](../reports/2026-10-29-v013-first-review.md).
## 2026-10-30 targeted additions after v015 onset

Fuel Air Runtime16 populated all16 fields in retained v015124803 export after
owner VCM-recording restart. Runtime saturates255s; VCM gaps and manual restart
limit timing. Core16 is the retained baseline, not a guarantee of future coverage.

Prepared/XML-checked only, not loaded or live-tested:

- Target Loop State Trial20: baseline16 plus12944CLReady,12978OLConditions,
  12947OLFMEM,12923O2B1Fail, all1s.
- Target Heater State Trial18: baseline16 plus12933O2Heater and12925HeaterFault,
  all1s.

Definitions copied from saved Idle and Cruise XML; parent16 unchanged and
IDs unique. Prior optional-channel population was intermittent. Admit a profile
only after saved-log coverage/freshness checks; heater status is not electrical
measurement. See the current next-stationary test card for sequence.


## Stage 2A air/spark profile — prepared 2026-10-30

`2004 Focus SVT - Stage 2A Air Spark Trial.Channels.xml`:20unique IDs, XMLchecked,
not loaded or live-validated. Parent LoopState20 preserved. Adds rawMAF2302 with
saved ParamterType2/200ms and IdleControlMode12200/1s from saved original XML;
removesCLReady12944 andOLConditions12978. RequestsSTIT100ms, STFT100ms, ECT500ms.
Other parent requests retained. Requested rates are not guaranteed delivery rates.
See ../docs/stage-2a-air-spark-test.md for admission and branching criteria.
SHA25621BC63D6629A30C7D033E97D3E3FAC774B4BD59EF63161634014D36D3A5EAC25.

Stage2A v018181640 completed: all20fields populated, noVCMexportgaps; rawMAF andIdleMode available. Requested100msSTIT/STFT is not independently verified ECUdelivery. Savedactualprofile beside logs/2026-10-30-v018-stage2a-01. See reports/2026-10-30-v018-stage2a-review.md. No active recording.

## v035 capture — 2026-11-05

19 of 20 requested VCM channels populated; LTIT PN/ACoff entirely blank. Borderline Knock 19074 is not validated knock retard. Fuel Pressure Sensor remains raw volts; exported injector pulse-width units require verification. SCG pull 2 is warmup with no lambda and zero duty; exclude it. See [review](../reports/2026-11-05-v035-pull-review.md) for clocks, gaps and comparison limits.
