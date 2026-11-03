# Stage 2A: choose the next warm-idle intervention

Status update: owner confirmed v018 write complete and SBCSVT-SS-TZ kit identity.
Scanner was stopped; this profile is now loaded and its saved-back20definitions/
intervals match the prepared XML. No recording started; live coverage and actual
rates remain unvalidated. The earlier write-in-progress notes below are history.

Owner update: SBC single-mass flywheel and stock IAC confirmed by owner.
Part numbers, flywheel inertia and valve condition remain unverified. A single-
mass conversion is relevant to torque-response/damping assumptions, but does
not establish a numeric inertia correction or prove the valve works correctly.
Owner explicitly reports the write is still underway; continue offline only.

Owner is beginning the v018 write. Completion/installation is not yet confirmed.
Preparation here is offline only: no Editor/Scanner navigation, vehicle connection,
engine command or profile load during the write. No v019 candidate is prepared.

## Question

Warm RPM dips remain after entry behavior is separated. Existing v016/v017
sequences show overspeed, reduced IAC/airflow, underspeed, and air/spark recovery.
Those asynchronous exports do not prove which disturbance initiates the loop.
STIT is requested at500ms in the current profile, comparable with the whole
undershoot. The next short capture must improve that measurement, not repeat
the same20 channels at the same rates.

## Prepared profile

[Stage 2A Air Spark Trial](../profiles/2004%20Focus%20SVT%20-%20Stage%202A%20Air%20Spark%20Trial.Channels.xml)
has20 distinct channel IDs. XML validated; not loaded or live-validated.
SHA-256 `21BC63D6629A30C7D033E97D3E3FAC774B4BD59EF63161634014D36D3A5EAC25`.

Changes relative to Target Loop State20:

| Channel | Change | Purpose |
| --- | --- | --- |
| STIT2240 |500ms ->100ms request|Resolve air correction around short RPM events |
| STFT6304 |200ms ->100ms request|Separate fuel-correction changes from air response |
| ECT2124 |50ms ->500ms request|Reduce unnecessary temperature polling |
| Raw MAF voltage2302 |Add at200ms, original ParamterType2 preserved|Compare actual MAF signal with calculated flow |
| Idle Speed Control Mode12200 |Add at1s|Optional state context; previously unreliable/blank in broad profiles |
| CLReady12944, OLConditions12978 |Remove from this warm-only profile|Keep channel count bounded |

Retains RPM, desiredRPM, spark/source, fuel source, absoluteTPS, calculatedMAF,
IACduty, voltage, upstreamO2, CLActive, engine runtime, LTITPN/ACoff, FMEM and
O2B1Fail. SCG supplies independent lambda. The two new definitions are copied
from previously saved Scanner XML, not guessed wirePIDs. RawMAF2302 previously
populated in survey captures; that does not guarantee it will populate now.

Requested-rate total is approximately unchanged, but bus cost is not simply
request count. Actual timing/coverage must be checked. A100ms request is not
proof of100ms ECU delivery; repeated or interpolated CSV rows are not fresh data.
Idle mode at1s can provide state context, not subsecond transition order.

## One bounded measurement after the write

1. Confirm write complete and intended v018 installed; preserve the current
   Scanner profile. Only then load this new profile. Keep the known sensor,
   regulator, throttle and accessory settings unchanged.
2. Use settled warm closed-loop idle, A/C/defrost off, hands off throttle. Record
   fan edges if they occur. This is not a DFCO test and needs no drive or boost.
3. The first20–30s are an admission check within the same recording: essential
   fields populated and changing where expected, no new large gaps. Optional
   IdleMode blank is recorded as missing; do not keep restarting to force it.
4. Capture two or three representative dips, with a maximum90s once settled.
   If no dips occur, stop and mark not reproduced. Stop earlier for deterioration.
   No fan cycle or several-minute unchanged baseline is required.
5. Export once. Inspect native data/actual per-channel changes and excluded gaps
   before any timing conclusions. Compare against saved warm windows rather than
   automatically demanding another baseline. Don't clear learned state casually.

If STIT still arrives too slowly, use a smaller acquisition group or vendor
guidance; another identical run won't solve a bandwidth/definition limitation.
Actual IAC airflow demand and physical valve position/current remain unmeasured.

## Revision decision rules

| Observation | Next revision/test target | What it does not justify |
| --- | --- | --- |
| Air command repeatedly retracts after overspeed, rawMAF follows, then RPM undershoots and correction reverses | Verify idle-air overspeed response, PI/integration/filter controls and IAC duty-to-flow behavior; choose one calibrated intervention once the parameter is defined | Treating spark proportional gain as an air gain, or globally adding base airflow |
| RawMAF changes without a preceding commanded-air reduction | Investigate MAF/air path, IAC physical response, or an unlogged torque disturbance; select cam/purge additions only with actual definitions | Declaring a sensor failed from one asynchronous sample |
| Actual spark baseline follows the low-load cap with verified active eligibility/timer and air state | A local cap/transition trial may be justified after verifying44603 units and active branch | Flattening44603 to60deg or adding global spark |
| Onset follows the165–200s runtime-air handoff, with confirmed timer and consistent load | Smooth that specific warm transition while preserving final warm value and cold columns | Flattening the entire startup-air table or attributing all late dips to this timer |
| Fuel command/mixture consistently changes before torque loss with adequate timing evidence | Return to injector/MAF/pressure/feedback-delay branch with actual metering evidence | Assuming a fixed STFT means injectorPW is fixed or inventing a fuel PID gain |

No numerical air-gain/cap change is currently verified. That is the remaining
definition gap, not a request for endless warm logs. The next revision must name
the exposed parameter and expected effect before the engine test begins.

## Offline work to finish before selecting a candidate

[South Bend kit research](south-bend-svt-clutch-research.md) identifies likely
SBCSVT-SS-TZ with an aluminum flywheel. Bare flywheel mass and rotational inertia
remain unverified; the catalog's24 weight is not a bare-flywheel specification.

- Use the full inventory; do not rescan342 entries. After the write, inspect
  ECM44603 axis units/description and any active limiter/correction signals.
  Its displayed0/480/600/... breakpoints are not automatically engine-runtime
  seconds; establish internal low-load timer semantics.
- Ask HP Tuners for UJAHAS3 idle-air PI/filter/overspeed controls, base/final
  idle-air request, integrator limit/status, and spark-limit/correction sources.
  Existing support draft is local only; no message sent.
- CamAngle/CamError/CamDuty names exist in cached controller selection, but their
  exact request definitions were not saved here. Obtain those after the write
  before making a cam-specific profile. Never copy external ECU IDs or guess them.
- EVAP purge command and actual idle-air demand need confirmed definitions.
  A purge-fault flag is not purge flow. Do not substitute it as that measurement.
- Establish IAC part identity and flywheel type. This affects actuator-response
  and torque/inertia hypotheses. No part purchase is requested by this plan.

Success is less target-relative undershoot/rebound at the same950RPM target,
not merely changing the average RPM. No new stall/hanging idle or adverse mixture
behavior is acceptable. Record the exact parent and revert a failed intervention.
