# Next stationary test: investigate stall and self-recovery

## Next candidate: v019 bounded MAF low-flow trial

[v019](../tunes/v019-maf-low-flow-trial.md) is prepared from exactv018, not flashed
or tested. Nine low-voltage cells reduced3.72–4.80%; higher-flow cells and axes
retained. No absolute unit conversion or other control change. After owner
installation, one60–90s warm settled2A comparison is the discriminating test.
Review mixture/trim together with target-relative RPM fluctuations. No load or
boost acceptance is established by retaining the upper curve.

## Stage 2A preparation while v018 is being written

Follow the [bounded air/spark test](stage-2a-air-spark-test.md) after the owner
confirms the write complete. The new20-channel profile is prepared offline,
not loaded or validated. It adds rawMAF and faster requestedSTIT/STFT sampling;
no redundant ordinary idle run is requested. No engine/connection actions during
the write. No v019 candidate exists yet.

## Latest prepared candidate: v018

[v018](../tunes/v018-dfco-recovery-diagnostics.md) is saved/reopened/compared,
not flashed or tested. Parent is exactv016; only DFCOexit1000RPM andP0132MIL
reporting, plus Notes. Check ordinary operation and actual codes after owner
installation, but do not request a long parked idle log to test DFCO. Its moving
test requires acceptable recovery and an actual cutoff event; see candidate
instructions. Warm oscillation and stationary hanging idle are not claimed fixed.

## Use the full correction plan

The [inventory-based correction plan](calibration-correction-plan.md) now governs
the next work. Warm air/spark fluctuation remains primary; no unchanged baseline
repeat is requested. Select one supported intervention or a genuinely new signal.
P0132 reporting restoration is proposed separately; no new file has been prepared.
DFCO exit testing, if selected later, requires an actual DFCO event and cannot
be judged from parked idle. Preserve all older test descriptions below as history.

## v017 outcome: do not repeat the threshold trial

[v017 result](../reports/2026-10-30-v017-entry-review.md) failed the intended
prevention of early rich overshoot: positive trim again reached25% and lambda
0.723. Recommend exactv016 rollback; owner has not yet confirmed it. No automatic
increase of the calculated-temperature threshold and no identical repeat log.
Prioritize physical upstreamO2 signal/heater measurements versus the recorded
near-zero channel, using correct wiring/specifications. No recording is active.

## Next: v017 feedback-entry experiment

v016 first-start session has been stopped/exported and reviewed. The next
prepared candidate is [v017](../tunes/v017-o2-readiness-600.md): calculated O2
entry threshold520->600F only, retaining950RPM. It is not installed yet. One
parked startup/entry comparison, then60–90s afterCL entry, is sufficient; no
repeated fan-cycle baseline is requested. Review the candidate's stop rules.

## Next: owner-approved v016 950 RPM trial

[v016 and test criteria](../tunes/v016-idle-margin-950.md) are prepared, saved,
reopened and compared againstv015. Only both idle targets900->950 and Notes
changed. Owner has not yet confirmed flashing; v015 remains installed as last
reported. After installation, perform one warm off/blower/off comparison with
fan annotations. Assess target-relative undershoot and recovery, not merely a
higher minimum RPM. This supersedes the earlier no-candidate plan below.

Owner reports blower may have been running in the155954 comparison, weakening
the assumption that its spark/air difference reflects adaptation alone. Retain
the cold O2 question separately; do not bundle fuel, gain or sensor changes.

## After the Bosch15719 warm test — 2026-10-30

The [six-minute review](../reports/2026-10-30-v015-bosch15719-review.md) shows
switching O2, CL active and no logged FMEM/O2Fail assertion, but remaining brief
idle dips. No urgent sensor purchase or tune change is selected. After a full
cool-down, capture the same tune/pressure from before engine start with populated
LoopState20 channels. This specifically tests the missing cold readiness interval.
Keep the run attended and stop for worsening stumbling. Hardware heater/signal
checks below remain appropriate if delayed feedback/fallback repeats. The warm
test does not certify15719 application equivalence or prove priorP1132 cleared.

## Updated priority after P1132 — 2026-10-30

The [latest review](../reports/2026-10-30-v015-p1132-review.md) supersedes the
earlier running-test sequence below. LoopState20 successfully captured fault
fallback and an O2 failure flag. Keep v015 unchanged. Check upstream O2 heater
power/control/current and signal/return integrity using the correct SVT wiring
before another tuning experiment. Begin with a cool, engine-off inspection of
the sensor, extensions, connectors and nearby exhaust joints.

A later attended cold-to-warm capture should accompany those measurements,
not simply reproduce another stall. Heater18 remains a prepared, unvalidated
profile; commanded heater status does not prove electrical operation. No logging
is active. Preserve P1132; no codes were cleared. The exact failed component,
if any, is not established, and no v016 has been selected.

## Today's sequence — 2026-10-30

The [HP Tuners ticket draft](hpt-support-ticket-draft.md) and private attachment
bundle are prepared, not submitted. Obtain a fresh vehicle-connected VCM Suite
Info Log before submission; the old vehicle-unpowered report is excluded.

1. Leave v015 unchanged and set the SCT issue aside for this session. With
   engine off, close LiveLink/Device Updater, disconnect SCT from the vehicle
   and reconnect MPVI4. IgnitionON, engineOFF for the Info Log.
2. Gather/save the Info Log without clearing DTCs, resetting adaptations or
   flashing anything. Check current/pending DTCs read-only if available; CEL
   being off is not proof of resolution. Review draft before external submission.
3. When ready at the controls, save the current profile and load LoopState20.
   Do one short approximately60s coverage trial with paired SCG logging.
   Check actual exported fields and core freshness before the main comparison.
   If optional fields fail, retain files and restore working16.
4. Only if behavior remains suitable and core data works, make one parked
   warm-idle comparison: same v015, unchanged accessories, no intentional
   throttle blips. Record pressure-gauge video and a common event/time mark if
   practical. Aim for180–195F with about3minutes settled near900RPM, but stop
   early for deterioration; no requirement to wait for a fan or reproduce a stall.

No road/power test or new tune is selected today. First objective is a usable
profile and evidence of what precedes a dip. This plan does not start recording
or provide unattended monitoring.

**SCT/LiveLink availability check in progress:** Windows recognizes the SCT
driver; installed LiveLinkGenII2.26.294.2 fails CheckCommunication with
"No part number found in SCT device. Please contact SCT support for help."
No vehicle-supported SCT channel list is validated yet. VCMScanner was
disconnected to avoid competing access; no recording is active.
Obtain handheld model/partnumber/firmware info before deciding next steps.
No firmware update/recovery/stock restore/ECU write has been performed.

**Fuel-system audit finished:** [findings](../reports/2026-10-30-v015-pressure-injector-audit.md).
Keep v015 unchanged. Exposed injector pressure multipliers are neutral; the
temperature-dependent desired-pressure entry and hidden fallback path remain
unverified. Do not change pump gains or pressure compensation from the bypass
alone. Cold base1.03 and decay0.03 nominallycancelto1.00, so no isolated decay
change is selected. Next running work remains short LoopState20 validation,
with independent pressure evidence if available; no recording is active.

**Fuel-pump clarification2026-10-30:** owner confirms direct battery feed through
a relay, bypassing ECU/FPDM speed control. Next electrical detail is the relay
coil trigger source; actual pump-terminal voltage under load is unmeasured.
Do not infer pump voltage from the ECU module-voltage channel. Keep existing
shutdown/interlock behavior intact. Actual pressure and voltage evidence still
matter; ECU injector-pressure compensation remains distinct from pump control.

## Channel preparation before the next run — 2026-10-30

Keep the16-field Fuel Air Runtime baseline that populated in the last capture.
First try the [20-field Loop State profile](../profiles/2004%20Focus%20SVT%20-%20Target%20Loop%20State%20Trial.Channels.xml):
adds CL Ready12944, Open Loop Conditions12978, Open Loop FMEM12947 and
O2 B1 Fail12923 at1s from the existing saved controller definitions. These
provide context for the unexpected CLYes→No→Yes transition. They are status
flags, not a guaranteed causal explanation.

Prepared separately: [18-field Heater State profile](../profiles/2004%20Focus%20SVT%20-%20Target%20Heater%20State%20Trial.Channels.xml)
adds O2 B1S1 Heater12933 and Htr Fault12925 at1s to the same baseline. Use
as a separate short check if readiness remains unexplained; do not combine
all optional groups before validating core acquisition. Heater command/status
does not measure heater current, voltage at the sensor or actual temperature.

Both XML files preserve all16 baseline definitions and intervals, contain unique
IDs and parse successfully. Neither has been loaded or live-tested. Save the
active profile before switching, verify core values, and audit a separate
approximately60s saved trial. If additions are blank or core data deteriorates,
retain the evidence and return to16. Do not extend unstable running for coverage.

Injector pulse width is still a high-value missing measurement; no verified
usable controller definition is available from prior inspection. Do not add
an invented or unrelated external-device PID. Commanded equivalence is already
known to duplicate the displayed trim algebraically, so it is not prioritized
as independent evidence. The ECU's flat40psi pressure signal remains invalid.

Keep v015 unchanged. Start both recordings before the relevant interval; film
the regulator pressure gauge if possible and record a common timing mark.
Any manual VCM restart must be noted; preserve earlier data where possible
and establish a fresh native timing relationship. No test started by this edit.

**v015 onset capture completed:** [review](../reports/2026-10-30-v015-onset-review.md).
Small dips prompted stop/export; all16 fields populated. No recording active.
Deepest799RPM sample occurred whileCLNo/startup fueling, before CLreturned158F.
STITnear-0.30lb/min/LTITzero is new evidence; limit/clamp not verified. EndECT162F
means this is not yet fullywarm validation. Next: read-only review of reported
loop/fuel transitions, warm-base boundary, scheduled air and idle adaptation
before another numerical adjustment or running test.

**Retry recording active:** paired-20261030-124803-22ef9d06-v015, both recorders
confirmed12:48:37 local,600s automatic-stop backstop. SCG data resumed with
ignitionON; owner confirms ignitionOFF caused the prior missingstream.
Fuel Air Runtime16 loaded. Verify live/saved coverage; inspectmanifest for
currentstate. No agentECUwrite; v015 owner-confirmed installed.

**2026-10-30 current state:** owner confirms v015 write complete. No ECU readback
by agent. First logging startup124621 failed because COM4 opened but no valid
SCG data arrived within20s; VCM recording was never started. Engine should
remain off while checking ignition-on SCG power and serialOUT. No recording
is active. Fuel Air Runtime16 is loaded with actual config snapshot saved;
live channel validity remains to be checked. CEL-off owner report is not
confirmation that pending P0320 has resolved.

**Latest decision: v014 rejected after poor trip drivability.**
Both trip logs saved/exported; nothing recording. Owner reports no low-end,
harder pull-away and severe power loss. [v015 restoration](../tunes/v015-restore-closed-loop.md)
is prepared/reopened/compared, not flashed: calibration identical to exactv013,
only Notes differ. Last owner-confirmed installed remainsv014.
Owner handles any write; no agent ECU operation. After installation, verify
revision, loop state, mixture and idle while parked. No further acceleration
test or extra gain/fuel/timing change selected. v013/v015 still have unresolved
idle-stall history; restoring preferred behavior is not a road-readiness claim.
See [trip evidence](../reports/2026-10-29-v014-drive-review.md).

**Active owner-requested trip capture:** paired-20261029-190812-6d5aebc2-v014,
Drive Torque Diagnostics28; both recorders confirmed, no automatic cutoff.
Last installedv014 carried forward; no newer flash reported. Stop/export when
owner reports safely parked/arrival. Initial CL Active channel blank, so state
unknown. Owner advised diagnosticv014 is not accepted for road/boost use and
unresolved stalling remains; recording does not establish road readiness.
v015 investigation is authorized, but no numerical change/file is ready yet.

**v014 test completed:** [result](../reports/2026-10-29-v014-open-loop-review.md).
Open loop persisted with zeroSTFT, but later dips grew as lambda drifted from
about0.94 to1.04. No recorded poststartstall, but idle is not fixed. Both logs
saved; nothing recording. No v015 selected. Owner-confirmedv014 remains installed;
its diagnostic-only scope and exactv013 rollback remain.

Next evidence: actual injector pulse width/verified command if available,
runtime and idle-air adaptation, same-interval pressure video, and an upstream
O2 heater/readiness/signal check. Early O2 near0.005V while wideband was rich
remains unexplained. Use correct vehicle electrical data; do not replace the
sensor from this observation alone.

[Fuel Air Runtime16](../profiles/2004%20Focus%20SVT%20-%20Target%20Fuel%20Air%20Runtime%20Trial.Channels.xml)
is prepared/XML-checked, not loaded or live-validated: retains13 current fields
and adds saved2131runtime/2240STIT/2231LTIT. Verify acquisition before another
comparison. No new running test is started by this plan.

**Current selected diagnostic: [v014 warm-idle open-loop isolation](v014-open-loop-isolation-test.md).**
The owner requested Astra review and adjustments focused on progressive
closed-loop instability. The candidate is saved/reopened/compared, not flashed
or tested. It changes only two ECM32731 TPS thresholds200 to0 plus Notes,
retaining900RPM and all other v013 settings. Installed state remains v013.
Use the linked test card; older no-candidate statements below are historical.
This is a stationary comparison at similar measured lambda, not a permanent
open-loop repair or road/boost calibration. No recording is active.

**Latest follow-up saved:** [closed-loop observation review](../reports/2026-10-29-v013-closed-loop-followup.md).
Owner's active run labeledv013-2 was stopped/exported successfully; no new
calibration revision/flash verified. All13 VCM fields recorded, CL entered16.172s,
no stall in available rows, minimum825.5RPM;7.12s VCM gap and clock uncertainty
limit the comparison. Startup target1392 then896 is a confound. No new run or
closed-loop-disable tune selected. Next: read-only fuel-feedback/definition
review alongside the unresolved P0320 evidence; nothing recording.

Updated after the [v013 deep review](../reports/2026-10-29-v013-deep-review.md).
**New owner-reported diagnostic evidence: pending P0320, Ignition/Distributor
Engine Speed Input Circuit.** Owner further confirms the engine genuinely
stopped, then recovered without starter use. Treat this as an actual stall;
zero reported RPM alone is not evidence of a signal dropout. Preserve the
complete code report and available
freeze-frame; its occurrence time is not yet tied to the42.5s log event.
P0320 remains unresolved, not a proven cause or proven consequence of the stall.
Review pre-stall fuel/air/spark behavior alongside the code; do not make a
crank-sensor diagnosis or exclude narrowband/control behavior from this evidence.
The code does not identify a failed crank sensor by itself. No new routine
running/fan-cycle comparison or closed-loop-disable tune is selected.

**v013 is owner-confirmed installed and tested, but remains unaccepted. No v014
is selected. Both latest captures are saved and nothing is recording.**

The owner reports a stall with self-recovery and no starter input. VCM shows
brief zero RPM near42.5s, then cranking/startup states; wideband began too late
to cover that event. Later idle dips and a lean excursion persist under Idle
Feedback. Do not treat later smooth timing or average900RPM as a successful
stall fix. The following plan supersedes the historical sections below.

## Before another running capture

1. Preserve stored/pending DTCs and any available freeze-frame. No clearing,
   adaptation reset, regulator adjustment or tune change.
2. Engine off: inspect accessible CKP/CMP wiring/connectors, engine/ECU power
   and grounds, and modified ignition wiring. Leave purple SCG RPM disconnected.
   Include the old coil tach-tap area, coil/HT leads/plugs and routing of nearby
   modified wiring; previous SCG resets make inspection worthwhile but do not
   establish a shared fault. Use the exact2004 SVT wiring/pinpoint procedure
   before electrical measurements. Do not disconnect ignition while running.
   A brief zero scan value does not identify a failed sensor. If available,
   arrange qualified CKP/CMP/power scope diagnosis using correct circuit data.
3. Review Scanner trim/command definitions and relevant fuel-feedback calibration
   read-only. Their historical algebraic linkage is not independent confirmation
   of fuel correction. No MAF/injector change from the-19.3%/lean excursion alone.
   Narrowband feedback remains a separate hypothesis: normal switching is
   expected; bias, delay, wiring/heater trouble or exhaust leaks need evidence.
   Earlier closed-loop disabling does not establish the previous owner's reason.

## Next capture, if appropriate after those checks

- Keep the installed file unchanged for the diagnostic; record exact filename
  and initial ECT/soak. No road/boost or deliberate load/throttle experiment.
- Use [Target Fuel Runtime Trial14](../profiles/2004%20Focus%20SVT%20-%20Target%20Fuel%20Runtime%20Trial.Channels.xml):
  existing13 fuel/core fields plus exact saved Engine Run Time2131 at1s. This
  profile is XML-checked only, not loaded/live-tested. Runtime can cap at255s;
  a reset would indicate a runtime/state event, not prove an ECU power reset.
- Verify both VCM and SCG recording before the test interval. If engine is
  already running, do not restart it just to reset clocks. Check STFT, RPM,
  source/loop, IAC, voltage and SCG quality immediately. Restore the13-field
  Return Fuel Trial profile if the addition degrades acquisition. Missing is
  unknown; preserve the export instead of inferring unsupported channels.
- Record a short supervised parked interval, at most2–3minutes, with accessories
  constant, A/C/defrost off and no intentional throttle blips. Water/meth stays
  OFF. A fan cycle is not required. Keep pressure-gauge video if available;
  include an audible time mark for alignment and avoid interpreting static43psi
  base as the expected vacuum-referenced idle gauge reading.
- End at the first severe stumble/stall or worsening behavior; shut down safely
  and stop/export both. Do not repeat failures to fill the planned duration.
  Owner marks felt event, starter/key use and observed fan/load changes.

The review must separate pre-event, startup-state recovery and settled closed
loop, and check fresh channel coverage. Capture native HPL/SQLite, full CSVs,
profile snapshot, tune label and event notes. This card does not start a test
or establish unattended monitoring.

## Historical preparation and earlier decisions

The entries below retain earlier evidence; installed-state and next-test
instructions above take precedence.

**SCT reference received:** [BEF intake](../reports/2026-10-29-sct-backup-intake.md).
Preserved and hashed, but no supported decoded table comparison yet. A readable
export/matching reference is needed; do not flash stock or assume conversion
from changing the extension. Continue from the measured current-tune audit.

**Tune audit now available:** [ranked findings](../reports/2026-10-29-v012-calibration-audit.md).
Next priority is the coupled return-system model (6950/pressure/injectors),
runtime-dependent base-air multipliers and VCT tracking. A16-channel runtime
trial is prepared but not loaded/tested. Original SCT backup awaits transfer
from the other laptop; keep tune unchanged and compare reference/provenance
before selecting a change. No new engine test started during the audit.

**Video now reviewed:** [findings](../reports/2026-10-29-pressure-video-review.md).
No large gauge-visible pressure collapse around recovered764RPM dip; earlier
stall was not filmed and clock/display limits remain. LTIT stayed steady while
STIT/IAC responded under Idle Feedback. Next work is offline integrator/
eligibility and actual air-path/load review, not a new run or calibration edit.

**After trip review:** see [v012 drive findings](../reports/2026-10-29-v012-drive-review.md).
Owner's driveway stall was moving off, distinct from earlier untouched-idle
failure. Final parked dips recovered under Idle Feedback without observed MBT.
No tune change selected. Review preceding gauge video when received, then
choose a coverage-checked parked adaptation/load test. Both trip logs stopped
and finalized; earlier live-start messages below are historical.

**Latest status:** owner reports suspension repaired and requested continuous
trip logging. Driving profile28 is loaded, pair
`paired-20261029-161604-b543b769-v012` started; inspect its manifest for current
state. Stop/export when safely parked on return, no automatic cutoff. Engine
stalling remains unresolved; this is not road-readiness or boost validation.
The preceding three-minute gauge-camera run saved cleanly without a recorded
stall; its video is pending and pressure setting was owner-adjusted43psi.

**Post-stall next step, corrected history:** v010 also stalled, uncaptured.
The rollback recommendation is withdrawn. Follow the [onset/handoff diagnosis](post-stall-comparison.md)
with the file unchanged; no further recording requested yet. Review why torque
is lost and how spark/air arbitration responds, with coverage and timing limits.
Establish logger persistence before another unattended long capture.

**Five-minute test interrupted by stall,2026-10-29.** See the
[preserved stall review](../reports/2026-10-29-v012-stall-review.md). Leave the
engine off pending review; no next running test is currently requested. CL Active
and STIT were blank this time. SCG exited unexpectedly, but its recovered data
covers the stall and VCM was stopped/exported manually. No monitoring remains.

## Current selection after the second survey

Five more captures are complete: [results](../reports/2026-10-29-core-profile-selection.md).
The12-channel Core Stationary profile is now the saved/loaded parked default;
all12 fields populated across all five captures. The15-channel Target Idle Air
profile also recorded all three adaptation/source additions in its test. Use it
for the next warm parked learned-air/control-state comparison, with a fresh
coverage check. The agent handles switches under the
[operating policy](../profiles/operating-profiles.md). Electrical-load additions
remained blank; use owner event marks, not an inferred direct fan command.
All sessions are stopped/exported; no monitor remains running. Older trial
instructions below are historical, not the current profile selection.

## Completed first survey,2026-10-29

PartsA and the optional load-context check have now been captured, with a28-channel
control: [results](../reports/2026-10-29-channel-survey.md). All three65-second
pairs saved; logging is stopped. Neither expanded profile retains enough core
coverage for the longer comparison yet. The28-channel fallback is restored.
Next: a separate smaller-core/grouped acquisition survey and repeated blank-field
checks before the long tuning comparison. Do not simply repeat the prepared-only
sequence below or assume it validated the31/34 combinations.

Updated2026-10-29. **Not started. Owner confirms safe stationary operation.**
Parked engine-running/channel-survey tests may proceed when the owner is ready.
This is owner confirmation, not an agent inspection or confirmation of repair.
Driving tests remain on hold for the damaged front strut/spring assembly.

## What stands out

No newer paired session was found after `paired-20261028-093440-0223fe51`.
The [latest review](../reports/2026-10-28-idle-followup-and-mechanical-hold.md)
remains the basis for this card. Warm parked idle averaged 900.78 RPM, minimum
746, versus 900.53/min751 in the earlier comparable window. This supports
investigating the remaining oscillation, not another target or gain reduction.

1. **Air/control state:** warm dips recur with closed TPS. At the deepest dip,
   IAC rises to45.57% and spark reaches29.25 degrees/Base-MBT; RPM had already
   started falling. We need STIT, LTIT and Idle Speed Source before attributing
   this to adaptation, insufficient base air or a mode transition. None was
   recorded in the latest28-channel export.
2. **Startup/warm-up fuel behavior:** the first30s reports STFT fixed at-25%
   while provisionally aligned wideband lambda averages0.80. Later parked
   STFT averages-1.38% and lambda1.012. Separate startup/transient behavior
   from the settled fuel model; do not apply a global MAF/injector correction.
   Early voltage/IAC/trim hold constant and may not represent fresh updates.
3. **Load attribution and acquisition:** accessory state was not documented,
   direct fan command is absent, and data has gaps. Neither the source label
   nor a full CSV column alone establishes the cause. The reported40psi fuel
   pressure remains invalid as a real pressure measurement.

## Setup before the next start

- Retain owner-confirmed v012,900RPM/gain1.000 unless an actual later flash is
  reported. Meth stays OFF; SCG purple RPM wire stays disconnected. No adaptation
  reset, DTC clearing or controller-setting change for this comparison.
- Use SCG Logger's new **Start both** tune prompt: enter `v012` if unchanged.
  This names the paired folder and labels its manifest/SCG CSV. Verify the app
  was reopened to load the update. A label is owner input, not ECU readback.
- Save the active Scanner channel configuration into the new session's private
  folder. Preserve native HPL/SQLite, full CSVs, manifest and event notes.
- Record fuel/refueling changes, initial ECT, soak duration and accessory state.
  A warm start is not a cold-start test. No special engine restart just to reset
  the log clock; retain pre-start data when available.

## Part A: validate the missing measurements

Use the [31-channel trial](../profiles/2004%20Focus%20SVT%20-%20Stability%20and%20Drivability%20Trial.Channels.xml)
for a separate60-second stationary recording. **It is prepared only, not loaded
or live-validated.** Inspect its saved export before the longer test. Require
usable RPM, target, ECT, spark/source, IAC, TPS, voltage and SCG mixture. Check
all other fields too, including STIT2240, LTIT2231 and Idle Speed Source19049.
Report missing/partial/frozen-looking data explicitly; no inferred replacements.

If the additions are blank, preserve the trial and investigate availability.
If core capture deteriorates, restore the28-channel profile. Do not make an
engine calibration change merely because a diagnostic field is missing.

## Part B: one unchanged-tune parked comparison

After PartA data review, start a fresh pair using the accepted profile. Keep
headlights, blower and A/C/defrost state stated and constant. Let the engine
settle without intentional throttle blips; retain the whole warm-up if present.

Capture at least3minutes of warm settled idle, then a natural fan-on/off cycle
and60seconds recovery if it occurs within a10-minute observation window. Stop
after that window if no cycle occurs and mark the fan test incomplete. Do not
force heat with throttle or combine deliberate accessory steps into this run.
If instability worsens or near-stalling returns, stop the planned test and
preserve the data rather than waiting for another event.

Owner notes: approximate elapsed time and which clock, felt dips, observed fan
on/off and any unavoidable accessory/throttle changes. **Stop both & export**
uses the tune label from start without another prompt. Confirm saved/partial
status and provide the exact folder name. No unattended monitor is running
merely because this card exists.

## Optional separate load-context trial

The new [34-channel Load Context Trial](../profiles/2004%20Focus%20SVT%20-%20Load%20Context%20Trial.Channels.xml)
preserves all31 definitions/intervals and adds AC Requested17611, AC Clutch
Engaged17603 and Fan PWM7231 at1s from saved Scanner definitions. It is
**offline-prepared/XML-checked only**, not loaded, supported-data validated or
approved as the next comparison profile. These signals were historically blank.

After the31-channel check, try it in another separate60-second capture if load
attribution still needs it. Compare actual core coverage and gaps before keeping
it. A1-second context request cannot establish subsecond event causality. If
fan/A/C remain blank, owner timestamps remain the evidence; do not replace
unknown with OFF. Do not switch profiles inside the main comparison run.

## Decision after review

Compare matched warm windows, dip duration/recovery, air command/adaptation,
spark/source, voltage, TPS, loop/fuel state and wideband. Explain timing and
coverage limitations. A gain change requires repeatable evidence of control
behavior, an air change requires meaningful air/adaptation evidence, and a fuel
change requires valid command/pressure/injector context. Until then, retainv012.
Ordinary drivability validation resumes as a later separate test after mechanical
repair and a satisfactory stationary result.
