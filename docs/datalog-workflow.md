# Datalog pathway

**Stationary only, updated2026-10-29:** following the reported strut center-shaft
failure, the owner confirms safe stationary operation. Parked logging/channel
checks may proceed when ready. All driving portions below remain deferred until
repair. This records owner confirmation; it is not an agent inspection.

Current baseline: owner-confirmed v012, 900 RPM, idle spark gain 1.000.
Keep it unchanged for the next comparison. Water/meth stays OFF. The current
question is whether idle stability holds after driving and through load changes.
This pathway does not establish that the car is validated for boost or power work.

## Before each run

The agent supplies a short card: exact tune, purpose, profile, actions, completion
event, stop conditions and comparison session. Use the reusable
[run card](datalog-run-card.json); completed cards belong beside the private logs.
Only report what changed since the previous run: flash, hardware, fuel/refueling,
accessories or new symptoms. We will not repeatedly ask about settled facts.

While parked, connect VCM Scanner and select the SCG adapter. Save any existing
recording before closing it. Start both from SCG Logger and verify that both
recorders are running and receiving data. The keyboard shortcuts work with the
logger focused: Ctrl+Shift+R starts both; Ctrl+Shift+E stops and exports both.
If one recorder is already running, preserve it and start the missing one.
Separate start times can be documented; losing the event cannot be repaired.

For a startup test, start capture before starting the engine when the connected
devices permit it. Retain the complete warm-up. Do not use throttle to speed
warming unless that is the stated test; label any necessary input afterward.
The agent records initial ECT, profile identity and actual coverage. No engine
restart, adaptation reset or flash is required simply to begin a log.

## Next run: validate measurement, then compare v012

1. **Profile check, stationary, 60 seconds.** Trial the prepared 31-channel
   Stability and Drivability profile. It adds idle adaptation and source data.
   Save and inspect the export before relying on it. Verify RPM, desired RPM,
   ECT, spark/source, IAC, TPS, voltage, speed and valid SCG data; audit all
   other requested fields too. If core coverage deteriorates, return to the
   known 28-channel profile and retain the failed trial for diagnosis.
2. **Stationary settling.** Begin a new paired recording with the chosen
   profile. Hold accessories at one stated setting and allow at least two
   minutes of settled idle. If near-stalling returns, end the driving portion
   of the plan and preserve the symptom recording.
3. **Gentle ordinary drive, only if stationary behavior remains satisfactory.**
   Use a short familiar route at light load, staying out of boost. Capture
   normal tip-in, steady cruise, lift-off and return to a stop. Do not deliberately
   reproduce the old 4,000-RPM issue. No laptop interaction while moving; mark
   observations afterward or have a passenger note them.
4. **Post-drive idle, 3–5 minutes.** Park and keep recording without throttle
   blips. Keep the same accessory state. If a natural fan cycle occurs, retain
   at least 60 seconds after fan-off. If it does not occur, label the fan check
   incomplete rather than extending indefinitely or forcing heat with throttle.
5. **Stop both & export while parked.** Wait for saved/partial status. Give the
   exact session folder and observations. A partial export is recoverable from
   native files; do not delete or overwrite it.

The 31-channel profile is currently **prepared, not loaded or live-validated**.
This document does not start a recording or establish a running monitor.

## Follow-up cards: one question at a time

| Card | Conditions and action | Completion evidence |
| --- | --- | --- |
| Hot restart | Warm engine, stated accessory state; record before restart, no intentional throttle | Startup and at least two minutes of settled idle; distinguish from cold start |
| Natural fan cycle | Parked warm idle, accessories held constant | Observed fan-on/off and 60 seconds recovery; inferred fan state labeled separately |
| Electrical load | Stable parked idle, fan state noted; headlights on 30 s, off 30 s, then blower on 30 s, off 60 s | Separate on/off timestamps and recovery for each; keep A/C/defrost setting explicit |
| Return to idle | Ordinary light-load drive, normal deceleration/clutch action | Approach to stop and 3–5 minutes parked, including any dips |
| Cold startup | Genuine cold soak; initial ECT/IAT where available | Startup through warm settling; report soak duration and any throttle input |

If the radiator fan overlaps an accessory step, label the overlap and analyze
it separately; do not pretend the electrical loads were isolated. Do not add
all cards to one run by default. Change neither tune nor profile midway through
a comparison run. A severe dip, repeated near-stall, overheating indication,
new warning or abnormal mechanical sound ends the planned test; stop safely
and preserve the available data instead of trying to collect another event.

## What to send afterward

```text
Session: paired-...
Tune: unchanged v012 / exact newly flashed filename
Changes: none / fuel added, hardware, settings
Events: elapsed time + clock used (VCM, SCG, or approximate wall time)
        fan on/off; headlights/blower/A/C; throttle/clutch; felt symptom
Feel: idle, cruise, tip-in, return to idle
Export: saved / partial + message
```

“About 3:20 in VCM” is useful. Approximate event times are labeled approximate;
they are not used to prove millisecond causality. We retain both what you felt
and what the data shows, including when they disagree.

## What gets preserved and checked

Keep the native VCM HPL, SCG SQLite plus any active WAL/SHM files, both full CSVs,
paired manifest, actual channel configuration and completed run card. Back up
an active SQLite database through its backup API rather than copying only its
main file. Record software/export versions and settings when known. Never
remove original rows, smooth away dips, fill missing data or clear DTCs/adaptives
as part of routine intake. Save a read-only DTC/status snapshot when available;
no MIL is not the same as a completed fault scan.

The agent checks each channel's populated fraction, first/last available time,
blank spans, units and plausible behavior, plus time ordering and gaps in both
streams. Export row spacing is reported separately from actual sensor update
rate, which may be unknown. Clock offset and possible drift are assessed anew
for each paired recording. Timestamp-only alignment remains provisional.

Compare temperature/load-matched windows with the closest prior run. Report RPM
minimum, time below desired RPM by 50/100/200 RPM, recovery/overshoot, spark/source,
IAC/adaptation, TPS, voltage, mixture and loop/fuel state together. Those RPM
bands are analysis descriptors, not safety thresholds. Missing or quantized
desired RPM and asynchronous samples must be stated. Each review ends with a
retain/change/insufficient-evidence decision and one defined next test.

Broader coverage follows the [channel register](../profiles/channel-coverage.md).

## Oscillation severity and fan-cycle windows

Owner clarification 2026-11-02: fan operation is observed around 196 F on and
188 F off. Use those markers to segment warming/cooling cycles when direct fan
status is absent. Label them owner-supported temperature proxies, not measured
electrical switch edges; configured thresholds alone are not observed events.
Do not replace the configured fan thresholds with these observations.

Mean RPM describes centering, not stability. Lead comparisons with the full
minimum/maximum span, central 90% range (P5-P95), and time-weighted absolute RPM
error relative to logged desired RPM. Include percent of valid time outside
plus/minus 50 and 100 RPM, seconds below target by 100/200 RPM, longest dip,
event rate and recovery/overshoot. Repeated 800-1100 excursions must rank worse
than 910-980 even if both average near target. Those ranges are illustrative
owner examples, not recorded measurements or acceptance limits.

Report stalls and zero-RPM signal anomalies separately; do not hide them inside
a normal-idle average. Preserve transition windows and isolated extremes as well
as settled distributions. Count events using hysteresis/minimum duration rather
than every threshold crossing of interpolated rows. Exclude acquisition gaps
from time denominators and report missing coverage. Quantiles calculated from
export rows must be labeled row-weighted unless explicitly time-weighted.

Compare equal-duration fan-on/off windows and also whole valid phases. Separate
startup/runtime transitions, changing target, throttle input and loop state;
temperature proxies do not remove those confounds. Do not silently discard a
severe episode to make a settled window look representative.

HP Tuners notes that adding polled parameters can reduce acquisition rate; external
serial data does not add vehicle polling load. Preserve fast event capture while
trialing slower context channels. See [Scanner channels](https://docs.hptuners.com/VCM_Scanner/Channels/Channels/).

Analysis reuse is governed by [AGENTS.md](../AGENTS.md): input hashes, analyzer
version, alignment and window definitions must match. The existing evidence
inventory is not an automatic incremental cache. The aim is less repeated
discovery on each run, with a growing comparable body of evidence.
