# Focus scanner setup

## Current test reference — 2026-11-03

Use the [v025 regression card](../docs/v025-regression-test.md) and
[run card](../docs/v025-run-card.json). The latest v024 capture populated all
18 requested channels in the V023 Idle Spark Trial profile. Verify the actual
active profile and capture coverage each time; saved XML does not establish
current Scanner or recording state.

## Historical setup and profile trials

The dated notes below preserve earlier profile selections and their validation
limits. References to loaded profiles or stopped recordings describe those
sessions, not the current desktop state.

For the prepared v013 fuel-model experiment, use the separate
[Target Return Fuel Trial13](2004%20Focus%20SVT%20-%20Target%20Return%20Fuel%20Trial.Channels.xml):
Core Stationary12 plus existing B1 STFT6304 at200ms. Prepared/XML-checked only;
not loaded or live-validated. Require actual data before extending the test.
See the [v013 card](../docs/v013-stationary-test.md); do not silently switch inside
a recording or interpret linked trim/command fields as independent measurements.

Prepared-only addition: [Target Idle Runtime Trial](2004%20Focus%20SVT%20-%20Target%20Idle%20Runtime%20Trial.Channels.xml)
preserves Target Idle Air15 and adds saved Engine Run Time2131 at1s. Not loaded
or live-validated. Runtime previously capped255s; use it for the early airflow
multiplier question, not as an unlimited clock. See the
[calibration audit](../reports/2026-10-29-v012-calibration-audit.md).

**Selected profiles:** follow the [operating policy](operating-profiles.md).
Core Stationary12 is loaded/saved and stopped. The [second survey](../reports/2026-10-29-core-profile-selection.md)
retained all12 core fields across five captures; Target Idle Air15 additionally
recorded STIT/LTIT/source. Load-context fields still need acquisition work.
This supersedes the first survey's28-channel fallback below.

**Latest status,2026-10-29:** the [stationary survey](../reports/2026-10-29-channel-survey.md)
tested31,28 and34 channels. All pairs saved; availability varied and expanded
profiles lost core fields. The28-channel fallback is restored, Scanner stopped.
The older prepared-only statements below describe pre-survey status.

The [next stationary test card](../docs/next-stationary-test.md) stages the
31-channel adaptation check before a longer comparison. A separate
[34-channel Load Context Trial](2004%20Focus%20SVT%20-%20Load%20Context%20Trial.Channels.xml)
adds fan/A/C context at1s, with all31 parent entries unchanged. Both trials are
offline-prepared only. Owner confirms stationary operation is safe as of
2026-10-29; parked validation may proceed when ready. Driving remains on hold.

For current operations, use the [datalog pathway](../docs/datalog-workflow.md)
and [channel coverage register](channel-coverage.md). The dated sections below
preserve historical setup and validation; statements that a profile was loaded
describe that session, not necessarily the current Scanner configuration.

Working Vehicle Defaults captured from VCM Scanner on 2026-10-26 after the
initial generic SAE template did not produce a working scan. The connected
vehicle was identified as a 2004 Ford Focus ZX3 SVT,
2.0 L I4. Its VIN matched the interface's existing controller license. The
Scanner vehicle profile is already associated with that VIN; no duplicate VIN
profile was created. A private copy of its existing profile data is in `.local/`.

## Idle and cruise

- [Channels](2004%20Focus%20SVT%20-%20Idle%20and%20Cruise.Channels.xml)
- [Layout](2004%20Focus%20SVT%20-%20Idle%20and%20Cruise.Layout.xml)

The idle/cruise channel file now contains a snapshot of the current working
configuration based on Vehicle Defaults, also saved separately as
[Vehicle Defaults](2004%20Focus%20SVT%20-%20Vehicle%20Defaults.Channels.xml).
It includes idle desired RPM, idle adapt, idle speed source, idle air solenoid
duty, MAF and MAF counts, temperatures, load, spark and fuel sources, commanded
mixture, closed-loop status, oxygen-sensor voltage, fuel trims and fuel-system
channels. Zero-ID entries are visual separators. Native parameter IDs, the
application's `ParamterType` attributes, and requested intervals are preserved.
Actual channel update rates have not been measured.

The layout provides gauges, time charts, and Bank 1 fuel-trim tables. These
tables display observations and are not automatic calibration corrections.

Live scanning is confirmed with Vehicle Defaults. Two observations showed
coolant changing from 106 to 118 F, MAF from 1.50 to 1.43 lb/min, and desired
idle from 1,616 to 1,520 rpm. These are snapshots, not a completed idle analysis.
Closed Loop Active reported No. Some cells, including actual RPM and LTFT B1,
were blank through Windows automation; inspect the saved log before deciding
whether those channels are unsupported or merely inaccessible through the UI.
The active configuration continued to change during this session; the latest
available version was captured again before completion. The existing layout's gauges and tables still need full validation against
recorded data. Vehicle speed and voltage from the old template have not been
established as working channels in this defaults configuration.

The unsuccessful generic SAE idle/cruise template is preserved only under
`.local/unsuccessful-sae-idle-cruise.Channels.xml`. The active scan was left
running; configuration files were copied without changing its channel list.

## Fuel diagnostics

[Additional channels](2004%20Focus%20SVT%20-%20Fuel%20Diagnostics.Channels.xml)
preserve the older, unvalidated generic SAE fuel-diagnostics template, including commanded equivalence
ratio, upstream O2 voltage, fuel rail pressure, MAP, absolute load and barometric
pressure. Their presence in a template does not establish vehicle support or
sensor accuracy. This template is not the working baseline and should not be
loaded for current logging; use the Vehicle Defaults copy instead.

SCG-1 measured wideband AFR/lambda and boost have not been added. Wiring and
output scaling must be established first; upstream O2 voltage is a separate
measurement.

## Idle additions

The idle/cruise configuration has now been extended through the connected
controller's Channel Selector. The separate Vehicle Defaults file remains the
pre-extension rollback snapshot. New entries were selected from Common ID
parameters listed for this Black Oak controller, not from generic SAE IDs.

| Added channel | Native ID | Purpose |
| --- | --- | --- |
| Control Module Voltage | 2100 | Relate idle behavior to electrical supply |
| Engine Run Time | 2131 | Locate events after starting |
| LTIT PN/ACon | 2236 | Observe the controller's A/C-on long-term idle-air correction |
| LTIT PN/ACoff | 2231 | Observe the controller's A/C-off long-term idle-air correction |
| AC Requested | 17611 | Identify A/C requests |
| AC Clutch Engaged | 17603 | Identify compressor load events |
| Fan PWM Duty Cycle | 7231 | Identify commanded fan load events |
| Vehicle Speed | 8000 | Distinguish stationary idle from moving operation |
| Mass Airflow Sensor | 2302, Common ID | Record MAF sensor voltage alongside existing airflow and counts |
| Closed Loop Ready | 12944 | Observe readiness separately from active status |
| Closed Loop with O2Fault | 12945 | Record the controller's O2-fault-related loop status |

The application accepted these additions and they appear in the channel pane.
Live response for each new channel is still pending the next idle recording.
Labels such as fan duty and fuel pressure describe controller data; sensor and
wiring validity on this modified car still need checking.

The updated layout replaces the speed gauge with an Idle Target gauge, places
actual and desired RPM together on a 0-3,000 rpm chart, and adds an idle-air
solenoid-duty chart. It was loaded and visually checked. The chart scale is
for idle; higher RPM values remain in the recorded channels. Existing actual
RPM and other previously blank channels still require saved-log validation.

Injector pulse width was not found in the inspected Fuel > Flow list; it was
not added with a guessed identifier. External wideband/boost remain pending.
See [idle log notes](../docs/idle-log.md) before the next recording.

## v004 loop-diagnostic update (2026-10-26)

The [v004 logging audit](../reports/2026-10-26-v004-log-review.md) confirms
Ready=Yes, Active=No and Power Demand Enrich through the recording, including
fully warm operation beyond the startup gate. The idle/cruise profile and
active Scanner now also request Open Loop Active (12946), Open Loop Conditions
(12978), Open Loop FMEM (12947), O2 B1 Fail (12923), O2 B1S1 Heater (12933) and
O2 B1S1 Htr Fault (12925), all at 1 s. IDs/types were verified in the connected
controller's selector and the active configuration was saved through Scanner.
The [active follow-up observations](../reports/2026-10-26-v004-live-loop-followup.md)
now show live values for Open Loop Active/Conditions/FMEM and O2 B1 Fail;
the two heater channels remain null. Idle-air duty also now shows live values.
These live observations have since been checked against saved exports below.

The follow-up and a subsequent 31-second test are now saved and audited in the
[channel-test report](../reports/2026-10-26-v004-channel-test.md). Both confirm
the four new loop/O2-failure status channels in CSV. Two more controller-listed
Common ID trials were added: Air Load (2323, 200 ms), which is absent from the
test export, and Coolant Temperature Sensor Fail (12972, 1 s), which records
Pass. The load trial remains unvalidated and must not be treated as a working
measurement. Upstream O2 voltage and raw TPS remain empty in both new exports.

Fuel trims, idle-air duty/STIT, vehicle speed and several existing channels
remain absent or empty in v004. Raw TPS counts, MAF volts/counts, fuel pressure,
fan PWM and A/C clutch are empty. Engine Run Time caps at 255 seconds; use log
elapsed time after that point. A populated channel file does not establish
complete logging. Confirm actual values during acquisition and in a short
all-channel export before the next extended test. Keep the working measured
RPM source despite the separate empty duplicate. Continue LogWorks for AFR;
its RPM and WGDC remain unvalidated zero signals.

## Focused idle fuel-recovery trial

[Idle Fuel Recovery channels](2004%20Focus%20SVT%20-%20Idle%20Fuel%20Recovery.Channels.xml)
is a separate 27-channel trial prepared after the owner-marked fan-off event.
It retains existing parameter types and requests moderate intervals for
RPM/target, voltage, actual spark/source, commanded mixture, O2 B1S1, B1 STFT,
MAF flow/volts/counts, load/TPS, idle air and loop states. It has been parsed
and checked against existing IDs, but **has not been loaded or live-validated**.
The established idle/cruise profile is preserved unchanged. A smaller request
list is a data-acquisition experiment, not proof that missing channels will
populate. See the [fan-off review](../reports/2026-10-26-v005-fan-off-review.md).

## Loading a channel configuration

In the Channels pane, open its configuration menu and select **Open Channel
Config**, then choose the idle/cruise channels file. Use **Layout > Open Layout**
to choose the corresponding layout file. The prior active configuration and
layout were preserved privately under `.local/before-focus-profile.*`.

No ECU calibration, SCG-1 setting, firmware or licensing change was performed.

## Focused profile engine-off check, 2026-10-26

The Idle Fuel Recovery profile was loaded and tested with the engine off.
Saved HPL/CSV confirms absolute TPS, upstream O2, B1 STFT and MAF populate;
this does not validate running fuel control. Coolant and relative TPS were
empty in this short capture. Restore/verify coolant acquisition before a
running test. Scanner was left stopped with the focused profile loaded.
The previous configuration is backed up privately. See the
[engine-off validation and enrichment review](../reports/2026-10-26-koeo-channel-and-enrichment-review.md).

The subsequent [running focused-channel test](../reports/2026-10-26-v005-focused-fuel-recovery-review.md)
restored ECT acquisition after loading `.local/fuel-recovery-ect-fast.Channels.xml`,
a copy with only the ECT request interval changed to the previous 50 ms.
Interval causality remains unproven. O2/STFT/MAF/absolute TPS and ECT were
recorded through startup and a fan cycle; IAT/relative TPS/O2 B1 Fail remained
blank. The private trial profile remains loaded and Scanner is stopped.

## Startup O2 readiness profile

[Startup O2 Readiness channels](2004%20Focus%20SVT%20-%20Startup%20O2%20Readiness.Channels.xml)
is prepared for the [paired startup finding](../reports/2026-10-27-v006-paired-idle-review.md).
It preserves the private focused profile's existing 27 channels and intervals,
including ECT at 50 ms, and adds two status channels at their earlier 1-s interval:

| Parameter ID | Recorded channel name | Evidence |
| --- | --- | --- |
| 12933 | O2 B1S1 Heater | Prior saved startup CSV and existing idle/cruise XML; values populated historically |
| 12925 | O2 B1S1 Htr Fault | Prior saved startup CSV and existing idle/cruise XML; values populated historically |

The new 29-channel combination was XML-checked and loaded into Scanner on
2026-10-27. Both heater channel names were visible, and the next paired recording
started successfully with SCG samples increasing. A copy of the profile is saved
with the session. The later owner-marked blower recording exported both heater
columns blank in all18,808 rows. Their names being visible did not establish
usable acquisition. Do not interpret those blanks as heater OFF or a fault;
controller/request-type support or alternative measurement remains to be checked.
Existing profiles are preserved. Heater command/fault status does not establish
measured heater current or wiring integrity. Retain the wideband, upstream O2,
trim and supply observations alongside these status bits.

## Drive torque diagnostics

[Drive Torque Diagnostics](2004%20Focus%20SVT%20-%20Drive%20Torque%20Diagnostics.Channels.xml)
is the new28-channel template. Core engine channels are retained alongside
Torque Source, Total Misfires, Misfire Detected, Vehicle Speed, Brake Pedal
and Trans In Gear. It was built from the controller selector and Scanner's
saved parameter definitions, preserving type/address attributes.

An exploratory33-channel stationary capture populated those additions, but
pressure stayed40psi with sensor voltage near5V, MAP stayed0, and Borderline
Knock was blank. Those five fields were removed from the reusable version.
No dedicated knock-retard or clutch-switch channel was exposed. Trans In Gear
is not clutch state, and zero misfires does not validate counter sensitivity.
Four loop-status fields were blank; request intervals returned to their earlier
500ms values. The final28-channel profile is loaded but still needs saved-log
coverage validation. See the [idle-dip review](../reports/2026-10-27-v009-stationary-idle-dips.md).
The previous profile and exploratory capture profile remain backed up privately.

The subsequent v010 drive populated changing Vehicle Speed and Torque Source
(Driver Dem, Oscillation, TipOut Limit, TipIn Limit), and throttle state values.
Air Load and four loop-state fields remained blank. Reported misfire counts
stayed zero; that is not sensitivity validation. See the
[v010 drive review](../reports/2026-10-27-v010-drive-review.md).

## Stability and drivability measurement trial

The [31-channel trial](2004%20Focus%20SVT%20-%20Stability%20and%20Drivability%20Trial.Channels.xml)
preserves the28-channel diagnostic profile and restores LTIT PN/ACoff(2231),
Idle Adapt/STIT(2240), and Idle Speed Source(19049). Definitions were copied
from the earlier Scanner-saved Idle and Cruise XML; names were independently
matched to preserved VCM CSV headers. Type/address attributes are preserved;
LTIT/STIT request500ms, Idle Speed Source100ms.

Prepared and XML-validated only; not loaded or live-validated. First perform a
short stationary export and check coverage/timing before using it for driving.
Return to the working28-channel profile if core fields become sparse. The
purpose is to distinguish learned idle-air and control-state effects, not to
infer valid adaptation from a channel name alone. See the
[current roadmap](../docs/stability-and-drivability-roadmap.md).
