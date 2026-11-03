# Identify the initiating idle disturbance

2026-11-01. Keep owner-confirmed v019 unchanged. No v020 prepared and no claim
of a failed IAC. This test adds cam tracking to the existing air/spark/fuel data.

## What the existing evidence now says

Re-screened all25 grouped sub900RPM events in the v019warm capture using the
already-preserved event points. From0.5 to0.25seconds before the minimum,
RPM was falling in21events. IAC command was increasing in19 of those21, spark
was increasing in20, and reportedSTFT changed by at most0.1percentage point in7.
These points are nearest asynchronous samples, not synchronized ECU updates.
The window is before the minimum, not necessarily before the onset. It cannot
establish a causal delay or identify the initial trigger.

This screening corrects the earlier overemphasis on decreasing average IAC:
longer-window average duty and individual recovery action are different things.
The controller is often already adding air/spark while RPM continues downward.
That can occur with response lag, an external torque disturbance or a feedback
oscillation. It does not establish bad hardware or a reason to reduce rescue gain.
Mean-trim convergence still does not justify another MAF cut.

Evidence: [warm review](../reports/2026-10-31-v019-warm-review.md), private
`logs/2026-10-31-v019-warm-01/pre-minimum-screen.json` and
`correlation-review.json`. Window-split counts in the earlier report can split
one grouped event; this screen uses the25 whole-capture groups.

## New measurement prepared

[Idle Cause Cam Trial](../profiles/2004%20Focus%20SVT%20-%20Idle%20Cause%20Cam%20Trial.Channels.xml)
contains24 channels. The21 Warm Air Response requests are unchanged. Added via
the current Scanner native ECM0x10/BlackOak1472KPWM/UJAHAS3 selector, then saved:

| Channel | Saved ParameterID | Requested interval |
| --- | ---: | --- |
| Cam Angle | 2151 | 200ms |
| Cam Angle Error | 2152 | 200ms |
| Cam Duty Cycle | 2153 | 200ms |

These are exported Scanner request IDs, not guessed Ford PIDs or copied external
device channels. They are present in the loaded configuration, but dynamic
support, resolution and update rate are unvalidated. Do not derive desired cam
angle by adding actual and error without confirming the error sign convention.
Cam duty is also a command, not measured cam movement.

## Next owner-assisted session

1. Keep v019, fuel pressure and accessories unchanged. Use label
   `v019-cam-cause`. Engine remains off until the owner is ready; no remote start.
2. Start paired logging before the engine. Check SCG quality and the essential
   idle fields, including cam angle/error/duty. KOEO zeros alone don't validate
   dynamic operation. If additions remain blank after a short running check or
   cause core fields to disappear, preserve/export that admission capture and
   revert the21-channel profile. Do not idle indefinitely to force availability.
3. If coverage is good and running is acceptable, leave throttle untouched,
   A/C/defrost and accessories off. Retain the continuous warmup through170–190F
   and the first few dips. Stop after three representative dips or60–90seconds
   of settled warm idle; no fan wait required. Stop earlier for sustained rough
   running, rich fallback, near-stall or another concerning symptom.
4. Note the first felt stumble using recording elapsed time and any fan/load
   change. Do not restart/discard the running VCM recording to refresh channels;
   save the earlier segment first. RPM/runtime/ECT freshness must be checked in
   the export; runtime255 does not establish an internal calibration trigger.

This capture is justified by the new cam measurements, not by a tune change or
a need to reproduce the same symptom indefinitely. It tests a previously
unobserved torque/airflow branch. No deliberate actuator unplugging, spray test,
throttle-stop adjustment, resets or load-provoking near-stall test is requested.

## Analysis and decision rules

Align each event at its preceding local RPM peak and first sustained decline,
not only at the minimum. Retain raw channel changes; exclude gaps and intervals
without fresh data. Compare onset sequences against nearby non-dip periods.
Do not equate the exported20–30ms row spacing with200ms cam measurement timing.

| Repeatable observation | Next action |
| --- | --- |
| Cam angle/error deviates before RPM loss, with duty changing or saturated | Investigate requested/actual VCT tracking and its control path before idle-air tuning; do not zero the cam table from correlation alone |
| Cam stable; IAC command falls before the decline repeatedly | Air feedback/base-demand path becomes a stronger target; resolve gains, limits and demand components before selecting a value |
| IAC already adds air, but flow does not respond consistently | Check electrical drive and bypass response; IAC inspection becomes targeted rather than presumptive |
| Mixture excursion precedes the decline consistently after defensible timing alignment | Prioritize measured differential fuel pressure and injector command/characterization; do not treat unchangedSTFT as unchanged delivered fuel |
| All additions static/blank, or ordering is within acquisition uncertainty | Test is inconclusive; do not repeat it unchanged or invent a tune correction |

Wideband is in a separate clock domain and includes exhaust transport/sensor
delay. Do not claim a subsecond fuel lead from uncorrected timestamps or tune
the alignment to obtain a preferred result. Direct pressure/injectorPW and purge
remain absent, so even usable cam data will not exclude every disturbance.

If cam tracking is stable and the distinction remains air response versus
combustion, proceed to measured pressure once the sensor installation and
calibration are verified, or a properly instrumented IAC electrical-response
test. Do not spend the next revision on another arbitrary MAF or spark adjustment.
