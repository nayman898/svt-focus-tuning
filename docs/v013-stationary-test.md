# v013 first stationary test

**Not started. Owner flash confirmation required before labeling any log v013.**
Use [v013-return-vacuum-comp-zero.hpt](../tunes/v013-return-vacuum-comp-zero.hpt)
only for this defined diagnostic scope. The [revision note](../tunes/v013-return-vacuum-comp-zero.md)
records the exact change, verification and rollback. No agent ECU write.

## Before starting

1. Owner completes the write with the correct file/controller, suitable stable
   write power and Editor-required ignition/engine state. Tell the agent which
   file was actually installed. Keep regulator at the owner-set43psi base;
   do not adjust it again for this comparison.
2. Remain parked. Keep A/C/defrost OFF and other accessories at a stated,
   constant setting. No adaptation reset beyond any normal effect of the write;
   document known resets rather than assuming learned values were retained.
3. Start a fixed camera on the pressure gauge and tachometer where practical,
   with a clear common time reference. Pressure is observed at the regulator;
   display resolution/delay and clock uncertainty remain limitations.
4. Agent starts paired logging with actual tune label `v013`, confirms both
   streams and sets a three-minute stop/export. Start recording before engine
   start when the connected devices permit it. Owner stays able to stop the
   engine/test; no unattended stall reproduction.

## Logging profile

Prepared [Target Return Fuel Trial13](../profiles/2004%20Focus%20SVT%20-%20Target%20Return%20Fuel%20Trial.Channels.xml)
preserves the tested12-channel parked core and adds B1 STFT6304 at its saved
200ms interval. It is **XML-checked only, not loaded/live-validated**. Its purpose
is to assess mixture/model response rather than add every idle/drive signal.
No independent commanded-lambda claim is made from the linked STFT/command export.

First inspect actual RPM, target, ECT, voltage, timing/source, TPS, MAF, IAC,
upstream O2, fuel source, CL state, trim and valid SCG lambda. A listed channel
does not prove data. If required feedback is blank/stale, stop/export and
resolve acquisition before extending the tuning experiment. Existing28-channel
fuel/drive capture is a fallback request list, not a reason to change profiles
inside a running recording.

## First minute and remainder

Observe starting and settled idle without throttle blips or deliberate load
steps. Separate warmup enrichment, sensor-invalid periods and actual closed-loop
operation. Watch valid lambda and pressure behavior and listen for worsening
operation before continuing toward three minutes. Do not target43psi on the
running gauge:1:1 regulation changes gauge pressure with manifold vacuum.

End the test for worsening roughness, persistent unexplained mixture departure
from comparable v012 conditions, severe stumble or stall. Stop safely rather
than wait for a fan cycle. Shut down if deteriorating; save/export the available
data. No repeated deliberate stall and no driving/boost test on this candidate.

If satisfactory, allow automatic stop/export at three minutes, then review.
The first test does not need a fan cycle. Any extension to warm load recovery
is a separate decision after data quality and behavior are checked.

## Review and decision

Primary comparison is the v012/43psi stationary run
`paired-20261029-160556-870a7d58-v012`, with temperature/runtime/accessory limits
stated. Do not attribute differences from the earlier41psi run solely to v013.
Compare valid mixture/trim/loop context, gauge pressure versus vacuum, minimum
RPM, dip duration, recovery/overshoot, IAC and spark/source. Preserve all native
files, full CSVs, profile snapshot, camera timing and event notes.

Keep v013 only provisionally if engine response and usable feedback improve
without a new persistent mixture problem. A null or worse result is not a reason
to stack MAF, injector, VCT, gain or airflow edits. Revert exact v012 if needed;
that rollback retains its known unresolved instability. No broader acceptance
until the return-system model and remaining symptoms are resolved.


## Initial v013 outcome, 2026-10-29

Both captures are stopped and saved. STFT was blank in the first capture and
populated after an owner recording-only restart using the same13-field profile.
A stumble in the manual warm recording includes brief zero-RPM/cranking-state
reports with no starter use; v013 remains unaccepted. See the
[initial review](../reports/2026-10-29-v013-first-review.md).
