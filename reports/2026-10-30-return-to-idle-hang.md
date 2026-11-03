# Return-to-idle hang investigation — 2026-10-30

Owner reports idle hangs when coming to a stop until a throttle blip releases
it. Investigate independently of the prepared v016950RPM target trial; no dashpot
or throttle adjustment is bundled into that file. Owner intends to flashv016;
completion has not been confirmed. Editor and vehicle controls were not touched
during this investigation while the owner may be writing.

## Existing-log evidence

Searched the two preserved drive CSVs with speed and throttle channels:
`logs/2026-10-29-v012-drive-01` and `logs/2026-10-29-v014-drive-01`.
Screened for speed<=0.5mph, RPM>=1150, absoluteTPS<=190counts, lasting>=2s,
without joining across gaps>0.3s. These are review filters, not ECU thresholds.

- v01216.194–39.328s: stationary elevated RPM, but desiredRPM itself starts1376
  and declines; actual settles without a subsequent blip. This is startup
  context, not evidence of the owner's stop-and-hang symptom.
- v0141215.803–1220.143s (about20:16–20:20): reported speed0–0.5mph, actual
  RPM1150–1223, desired896, TPSabout184counts and throttle stateClosed. IAC is
  approximately51.8–52.0%, Spark SourceClosed Thr.Decel, TransInGearNo. Recording
  ends1220.790s, so persistence beyond this stop and release behavior are unknown.

The second event is a real candidate for commanded return-to-idle air remaining
high after stopping. It does not prove the exact dashpot component, and it comes
from the rejected v014 open-loop experiment rather than currentv015/v016. The
latest v015 logs lack speed/closed-throttle-state channels and cannot establish
the same condition. A blip releasing the hang is owner testimony; no confirmed
matching before/after blip is isolated in these files.

## Calibration evidence already preserved

Earlier Editor audits identify the inherited controls:

- Idle minimumVSS3mph; dashpot enableVSS4mph and hysteresis2mph.
- Dashpot enableairflow0.07lb/min, neutralclipmodifier1.00.
- ECM32984 Idle Dashpot Decay vs.Dashpot Airflow: displayed output0.00 at
  axes0/0.2/0.4/0.6;0.06 at0.8;0.08 at1.0;0.10 at3.0.
- ECM32945 MaxClipvsVSS:0.10 at0/10/15mph,0.60 at20/40,1.00 at100.
- ECM32986 minimum table:0.04 at0/150,0.35 at1150,0.78 at2150,1.11 at3150.

These are archived Editor values, not fresh reads during the owner's flash.
The saved revision comparisons show intervening changes did not target these
tables. Zero display may be rounded, and generic documentation does not resolve
whether this strategy's decay output is a delay or decrement with special cases.
Do not call these zero values an infinite hold or select a replacement rate
without matching strategy-specific help/units. The minimum table axis labeling
also needs care; do not assume the name alone reconstructs arbitration.

HP Tuners' [Ford idle documentation](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)
connects low-speed idle eligibility and dashpot operation to vehicle speed.
It is general guidance, not proof of this Black Oak strategy's exact state logic.

## Priorities and decision branches

1. Establish whether the ECU requests the hang: at a confirmed stopped event,
   compare desiredRPM, actualRPM, speed, TPSraw/relative/state, IAC, MAF and
   SparkSource. The existing DriveTorqueDiagnostics profile has most of these;
   the stationary20 profile lacks the speed/throttle-state context. Do not load
   or switch profiles mid-write or mid-recording.
2. If speed is zero and TPSstateClosed but IAC remains elevated in decel until
   a blip, prioritize dashpot decay/minimum/clip and idle-entry state audit. This
   is the leading calibration hypothesis from the candidate event.
3. If rawTPS or closed-state changes after a blip, inspect throttle cable/linkage,
   return spring, plate closure and TPS signal/learned closed reference. A blip
   can change physical closure as well as ECU state; no mechanical failure is
   proven yet. Check linkage with engine off; do not adjust the stop screw.
4. If IAC command falls but air/RPM remain high, inspect IAC response and unintended
   airflow. If desiredRPM rises, investigate the target/adders instead of treating
   all elevated idle as dashpot. A speed signal that persists at rest is another
   input fault to separate before editing calibration.
5. Dedicated clutch state remains unvalidated. TransInGearNo is not an adequate
   substitute for a measured clutch switch. Owner clutch/neutral context matters.

Do not zero dashpot tables indiscriminately: this vehicle already has undershoot
and stall history. Reducing retained air may improve a hang while worsening
deceleration recovery. Any subsequent edit should target the verified retained-
air mechanism as a separate revision after v016's target trial, with comparison
and rollback. No extra engine run, code clearing, ECU write or calibration edit
was performed here.
