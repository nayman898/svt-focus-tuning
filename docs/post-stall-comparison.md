# Post-stall diagnosis: initiating disturbance and control handoff

Later evidence: [stationary pressure video reviewed](../reports/2026-10-29-pressure-video-review.md).
No large visible pressure collapse near the nominally aligned recovered dip.
Earlier stall pressure remains unknown. All15 fields populated in this later
run; LTIT stable and STIT/IAC rise through recovery under Idle Feedback. No
pressure-based tune change selected. Video does not cover the trip or earlier stall.

Updated2026-10-29: owner confirms **v010 also stalled occasionally, without
captured logs**. Later spark changes felt steadier between apparently random
stumbles. These observations supersede the earlier comparison rationale.

**The v010 rollback recommendation is withdrawn.** The first captured v012
stall does not establish a gain regression. Stability remains unresolved.
No gain, RPM, airflow or fuel change is selected; no new v013 or flash performed.
The carried-forward installed file remains v012.

## Owner context and new measurement opportunity

Owner confirms the stall occurred untouched, A/C and defrost OFF, and does not
believe it was radiator-fan related. Exact fan state is unconfirmed. OEM pressure
sensor is still awaiting installation. A digital GlowShift gauge has its sender
at the regulator; owner reports41psi engine OFF/pump ON. Keep this observation
separate from the earlier43psi base report. Gauge calibration/reference and
pressure at each injector have not been established. Do not adjust the regulator,
injector model or flat40psi ECU transfer solely to reconcile these numbers.

For a future supervised parked log, a securely positioned phone view of the
gauge with an identifiable timing reference and engine sound could show whether
an abnormal pressure change precedes the stumble. Video availability is not yet
confirmed. Display/sender refresh delay and cross-stream timing must be stated;
normal1:1 regulation also changes pressure as manifold vacuum changes. A rise
toward base pressure as the engine stalls is not by itself regulator failure.
No new engine run is requested by this preparation.

## Detached launch check

A hardware-free Qt/demo recording launched through Windows Start-Process ran
145s, recorded1635rows over144.4s and finalized cleanly. It outlasted the prior
unexpected exit point. This validates that launch path for the simulation, not
live serial/VCM recovery and not the original exit cause. Keep stdout/stderr and
process/session evidence for the next real capture. No production code fix is
claimed. The earlier requirement to establish a persistent launch is partly
addressed by this measured result; hardware behavior still needs observation.

## Separate the initiating disturbance from the recovery response

First determine what initiates torque loss: combustion/fuel delivery, actual air
path/IAC behavior, electrical/mechanical load, or a control-state/command change.
Then determine whether idle/main-spark arbitration helps recovery or aggravates
it. A response can still contribute to instability; the owner's handoff concern
is not dismissed merely because the first RPM decline precedes MBT.

## Closer stall trace

| VCM elapsed s | RPM | Source | Timing degrees | IAC command % |
| ---: | ---: | --- | ---: | ---: |
| 108.231 | 863.25 | Idle Feedback | 7.25 | 39.37 |
| 108.536 | 816 | Idle Feedback | 3 | 42.65 |
| 108.575 | 798 | Idle Feedback | 13 | 43.25 |
| 108.616 | 757 | Base/MBT | 30 | 47.82 |
| 108.694 | 738.5 | Idle Feedback | 8 | 47.58 |
| 108.735 | 680.5 | Idle Feedback | 23.25 | 52.43 |
| 108.793 | 585.5 | Base/MBT | 30 | 63.84 |
| 109.233 | 255.25 | Base/MBT | 28 | 100 |

This is an asynchronous/interpolated export, **not a proven millisecond ECU
execution trace**. Nevertheless, the brief reported return to8degrees at738.5RPM
is a specific feature to compare with nonstall dips. Inspect source/update timing
and control eligibility before selecting a spark table or threshold change.

Reported target896RPM gives139RPM error at first MBT entry; Idle Feedback later
appears at215.5RPM error. Previously inspected inherited enable/disable error
scalars are200/30RPM. Those two scalars alone do not explain the sequence; do not
assume they directly select the Spark Source label or adjust them blindly.

LTIT PN/ACoff remains about-0.223lb/min across the event, without an abrupt
step. STIT is blank, so total adaptive-air behavior/gating cannot be reconstructed.
IAC duty is an electrical command, not measured valve position or delivered flow.
TPS stays near closed and ECT188F does not establish fan state. Voltage loss may
follow falling alternator speed rather than initiate it. Provisionally aligned
wideband is near unity before the collapse and lean during it; this does not
rule out fuel delivery, ignition or air-path faults. Rail pressure is unmeasured.

## Diagnostic branches

| Branch | Distinguishing evidence / next work |
| --- | --- |
| Idle/main-spark arbitration | Compare leading windows in stall and recovered dips; inspect controller-specific eligibility, limits and integrator descriptions read-only. Verify a source/retard change actually precedes or amplifies torque loss |
| Air path/IAC | Engine-off inspection of connector, bypass plumbing and vacuum/PCV connections; targeted STIT/LTIT/MAF capture with real coverage. Rising duty alone cannot diagnose sticking or prove insufficient base air |
| Electrical/load | Owner fan/accessory timestamps plus suitable independent supply/load observations; current fan/A/C channels are unreliable |
| Fuel/combustion | Actual differential pressure or ignition/combustion evidence before RPM loss. Restore OEM pressure feedback with verified transfer/reference/pump arrangement or use suitable independent measurement; flat40psi PID cannot answer this |

HP Tuners describes separate [idle airflow/integrator and enable controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)
and [MBT torque/advance limits](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_spark_advance.htm).
These describe functions, not this Black Oak calibration's exact arbitration
state machine. Do not substitute a GM or standalone-ECU algorithm.

## Next capture when ready

Keep the tune unchanged while identifying the disturbance. First establish a
persistent logger launch; the previous unexpected process exit is undiagnosed.
Require actual coverage in a short saved export. Target Idle Air15 is conditional:
STIT and CL Active were blank in the stall capture despite earlier success.
Any added Torque Source or other control-state request needs a separate
acquisition check. Preserve whole native files and derive timing per recording.

No deliberate stall reproduction, adaptation reset or throttle/load cycling is
currently requested. Continue saved-trace review and engine-off checks. A later
owner-ready stationary capture needs explicit event notes, fixed accessory
state and termination at renewed severe stumbling. Driving remains on hold.
This is not acceptance of continued stalling operation.
