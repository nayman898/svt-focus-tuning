# Stability and drivability roadmap

**Stationary only, updated2026-10-29:** driver-side front strut center shaft
reported sheared. Owner now confirms safe stationary operation; parked logging
may proceed when ready. Driving remains on hold pending repair. No agent
inspection or confirmation of repair is implied.

Use the [datalog pathway](datalog-workflow.md) for the next run and the
[channel coverage register](../profiles/channel-coverage.md) to expand capture.

Updated 2026-10-28. **Hold 900 RPM. Establish repeatable stability, then improve
drivability.** The previous 800–850 RPM goal is no longer an active target.

The working calibration is owner-confirmed **v012**, with idle spark gain
**1.000**. Keep that file unchanged for the next comparison. There is currently
no sufficiently supported numerical change for a new v013. The unfinished
875-RPM draft was withdrawn, its unsaved edits discarded, and the file archived
privately. It was never flashed or entered in the revision catalog.

## What the complete history tells us

All 25 preserved vehicle-session folders were inventoried, including 25
recognized VCM exports. Older LogWorks/native recordings are represented by
their existing detailed analyses; recent gain/drive/fan CSV evidence was
revisited. This is not a claim that every proprietary binary was independently
decoded again. See the [coverage index](../reports/2026-10-28-log-evidence-index.md).
Multiple exports/copies are not extra independent tests.

| Evidence group | Finding to retain | Consequence for the plan |
| --- | --- | --- |
| Original 1,200-RPM baseline and v002 at 1,100 | Higher idle still had load/voltage/mixture disturbances | The entire issue did not originate with the 900-RPM target |
| v003 temporary fan-path tests | Some improvement, but electrical/load disturbances and spark handoffs remained | Preserve the later repaired-fan baseline; do not return to bypass compensation |
| v004 and diagnostic follow-ups | The early TPS-threshold trial did not produce reported closed-loop entry; channel gaps complicated interpretation | Do not infer fuel-control state from a setting or absent channel |
| v005 startup, settled idle, load-step and focused recovery | Closed-loop entry occurred, but startup and fan-off mixture problems remained | Keep startup, fueling and load-response questions separate |
| v006 post-repair, longer paired recovery and blower tests | Full warm fan-off recovery improved; early negative trims were not a permanent warm correction | Preserve repaired fan settings; no global MAF correction from warm-up trims |
| v007 1,000 and v008 950 trials | Target tracking was reasonable; v008 included a recovered 835.5-RPM fan/load dip | Useful historical comparisons, not proof of the minimum appropriate idle |
| v009 900 / gain 2.000 | First drive felt smoother at low RPM, but recorded drive and stationary dips reached 391–630 RPM; later repeat reached 571 | Preserve the owner’s improvement report and the severe-event evidence together |
| v010 900 / gain 1.500 | Owner reported good cruise and normal acceleration; drive minimum 737 and final idle mean 901 | Gain reduction is a plausible contributor to improvement, not proven sole cause |
| v011 1.250 | Prepared but not flashed | It contributes no engine-test evidence |
| v012 900 / gain 1.000 | Today’s warm mean 900; inferred fan/recovery minima 818/816, with no Base/MBT switching in those windows | Retain as the current stability baseline; validate its post-drive behavior next |

Detailed references: [initial baseline](../reports/2026-10-26-idle-review.md),
[v002](../reports/2026-10-26-v002-idle-review.md),
[v003](../reports/2026-10-26-v003-timing-review.md),
[v004](../reports/2026-10-26-v004-log-review.md),
[v005 startup](../reports/2026-10-26-v005-startup-review.md),
[v005 fan-off](../reports/2026-10-26-v005-fan-off-review.md),
[v006 recovery](../reports/2026-10-27-v006-paired-idle-review.md),
[v006 blower](../reports/2026-10-27-v006-startup-blower-review.md),
[v007](../reports/2026-10-27-v007-idle-fluctuation-review.md),
[v008](../reports/2026-10-27-v008-fan-recovery-review.md),
[v009 cross-session review](../reports/2026-10-27-v009-cross-session-diagnosis.md),
[v010 drive](../reports/2026-10-27-v010-drive-review.md), and
[today’s v012 result](../reports/2026-10-28-v012-stability-review.md).
Engine-off/channel checks establish measurement availability, not running
fueling quality. Unused, interrupted or explicitly discarded sessions should
not be promoted to evidence of a tune’s success.

## Phase 1 — establish the 900-RPM baseline

**Change nothing in v012.** Today’s fan recovery is encouraging, but it is one
stationary capture with different history from the earlier post-drive logs.
Its earlier warm-period minimum was 751 RPM and the warm RPM SD was about 30;
it is not a perfect-idle or completed-validation claim.

Next comparison:

1. Confirm the loaded logging profile and usable channels in a short saved
   stationary check. Capture v012 hot restart and settling without throttle
   blips; record accessory state and initial temperature.
2. If idle remains tolerable, record one normal accessory step separately from
   a fan transition. No deliberate repeated near-stall reproduction is needed.
3. Retain exact tune identity, raw HPL/SQLite and both CSVs. Label driver actions
   and actual fan observations when available; do not silently call an inferred
   coolant/IAC signature a directly measured fan command.

Assess minimum RPM, dip duration, recovery time, overshoot, sustained hunting,
source transitions, IAC, supply and valid wideband—not just timing smoothness
or an average. Compare like temperatures and loads. Stop the test if near-stalling
returns; reverting to v010 reverses the gain experiment but is not a guarantee
of a cure. Retain v012 provisionally only while its behavior remains satisfactory.

## Phase 2 — validate post-drive stability and ordinary drivability

After the stationary check, the useful next recording is the **same v012 after
a short, gentle, light-load drive**, ending with 3–5 minutes parked at idle.
The key question is whether the improved control survives driving and heat/load
history. Stay out of boost; the recorded 6–8 psi episodes were observations,
not accepted boosted fueling tests. Start/stop the logger while parked and keep
laptop interaction out of driving.

Capture ordinary tip-in, steady light cruise, lift-off, clutch-in/coasting and
return to a stop. Mark clutch/gear actions afterward or through a passenger;
the available Trans In Gear channel is not a validated clutch-position sensor.
Keep one consistent accessory state and avoid combining several experiments.

Decision:

- If cruise, return-to-idle and post-drive idle remain satisfactory, retain v012
  and expand the ordinary-use evidence gradually. A new revision is not required
  merely because another test succeeded.
- If a symptom repeats, identify whether it is parked idle, transition into idle,
  tip-in, or a specific load event. Select one corresponding calibration branch
  only after separating that symptom from pressure, voltage and sensor concerns.
- Preserve the driving controls that already gave the owner smooth cruise and
  acceleration. Torque Source Oscillation and timing reduction do not by themselves
  justify disabling torque management or knock protection.

## Phase 3 — close the measurement gaps

The existing 28-channel profile populated every requested field in today’s
capture, although previous sessions had missing flags. Availability must still
be assessed per session.

A separate [31-channel measurement trial](../profiles/2004%20Focus%20SVT%20-%20Stability%20and%20Drivability%20Trial.Channels.xml)
adds back LTIT P/N-A/C-off, Idle Adapt (STIT) and Idle Speed Source. Definitions
come from existing Scanner-saved XML and preserved CSV headers; their types and
address attributes are retained. It is **prepared, not loaded or live-validated**.
First use it for a brief saved stationary coverage check. If added requests make
core channels sparse, return to the known 28-channel profile. No dedicated
clutch switch, knock-retard or actual dashpot-airflow signal is invented.

We need this because a post-drive change in learned idle airflow is plausible
but was not recorded adequately. IAC duty is a command, not measured valve
position. Stable raw TPS through the parked dips weakens a potentiometer-glitch
explanation for those specific events; it does not validate all wiring.

## Phase 4 — restore trustworthy pressure evidence

The owner confirms a 1:1 manifold-referenced Aeromotive regulator at 43 psi base
and plans to reinstall the OEM sensor at the regulator with its own manifold
reference. Installation is not yet confirmed complete. Water/meth remains OFF.

ECM7596 maps every input to 40 psi, inherited from v001. That reading cannot
diagnose real rail pressure, and a sensor alone will not fix the mapping.
Before changing this path, establish sensor identity/transfer, pressure reference,
actual pressure at the rail/regulator, and the pump/FPDM/relay arrangement.
Then validate raw signal versus known pressure and manifold reference. Do not
blindly change the injector reference from 40 to 43 or turn off compensation.
Follow the [fuel-feedback audit](fuel-pressure-feedback-review.md).

Exact injector characterization and meaningful commanded-mixture semantics are
also needed before a fuel-model correction. The exported command/STFT algebraic
relationship is not two independent measurements. Rich/lean excursions during
lift-off, fuel cut and sensor warm-up are not steady-load correction samples.

## When v013 becomes justified

| Potential branch | Required distinguishing evidence | Current decision |
| --- | --- | --- |
| Idle spark gain or re-entry behavior | Repeated matched-condition regression with source/airflow context; improvement criterion includes RPM recovery | Hold gain 1.000; no further reduction or floor/MBT edit selected |
| Base idle air/adaptation | Usable adaptation/mode data showing persistent correction or loss of authority, with load/mechanical effects checked | Collect the missing measurements first |
| Dashpot/return-to-idle | Reproducible transition-specific dip or hanging RPM tied to speed/throttle/gear state and air decay | Do not infer active dashpot from a long stationary dip alone |
| Pressure feedback | Installed compatible sensor, measured pressure and verified transfer/pump/injector behavior | Strong concrete future integration target, but hardware prerequisites remain |
| Off-idle fuel control | Repeatable transition evidence, validated command/mixture and pressure; review inherited 200-to-0 TPS interpolation | No blanket threshold extension or fuel-table correction |
| Cruise fueling | Repeatable steady-condition error with injector/pressure/sensor models established | No global MAF or injector scaling from current trims |
| Torque intervention | Repeated felt symptom plus an identified requestor/condition | Preserve controls; normal-feeling v010 acceleration is evidence against indiscriminate removal |

HP Tuners documents separate [idle/dashpot controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)
and [injector pressure/offset compensation](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_general.htm).
Those descriptions establish purpose, not vehicle-specific replacement values.

For any future v013: use the actual installed/tested parent, define one hypothesis
and one causal change, preserve Notes, reopen the saved file, compare every
difference and record hash/size, rollback and stop criteria. Preparation never
means the ECU has been flashed or the result accepted.

**Current v013 decision: defer the binary.** No new numerical target clears
that evidence bar today. Keep v012 at 900 RPM/gain 1.000 and use the next
post-drive comparison to select a real change. The withdrawn 875-RPM draft
stays outside the active tune directory and revision catalog.

## Later work

Once ordinary drivability is repeatable, investigate remaining startup/O2
readiness, IMRC and component identification as separate issues. Boost/power
work comes after real pressure evidence, injector/fuel-model checks, wastegate
hardware/settings and the original tune’s water/meth dependency are established.
Do not add a fixed calendar or revision-number schedule to incomplete evidence.
