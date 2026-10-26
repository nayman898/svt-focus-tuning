# Focus scanner setup

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

## Reloading

In the Channels pane, open its configuration menu and select **Open Channel
Config**, then choose the idle/cruise channels file. Use **Layout > Open Layout**
to choose the corresponding layout file. The prior active configuration and
layout were preserved privately under `.local/before-focus-profile.*`.

No ECU calibration, SCG-1 setting, firmware or licensing change was performed.
