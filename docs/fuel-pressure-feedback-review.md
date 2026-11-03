# Fuel-pressure feedback and return-system conversion

**Current v015 audit completed:** [pressure/injector findings](../reports/2026-10-30-v015-pressure-injector-audit.md).
All exposed pressure multipliers display1.00 (offset1.0000), despite the master
switch beingEnabled. Desired-pressure AAT table is nonconstant; active model,
scaling/combination and injector-side input selection remain unverified.
No justification to change pump gains/pressure compensation/reference.
Cold base1.03 and final decay0.03 cancel nominally to1.00; the residual decay
alone is not proof of persistent rich fueling. All tune files unchanged.

## Current clarification — 2026-10-30

Owner confirms battery-fed pump relay triggered by ignition-on power with a
fuel-shutoff-switch interruption. ECU/FPDM speed modulation is bypassed; do
not re-ask trigger source or attribute physical speed changes to unused duty
commands. Shutoff implementation and loaded pump-terminal voltage have not
been independently inspected. No wiring change is proposed.

Installed v015 retains v013 calibration, including ECM6950 zero. Historical
0.484 and unresolved-pump-wiring statements below are superseded. Flat40psi
sensor transfer,40psi injector reference and enabled pressure compensation
remain. Pump adaptive voltage was previously displayed Enabled, but physical
control authority is absent through the reported bypass.

Owner asks whether the ECU could expect a pressure/fueling change that never
occurs. This is a legitimate model-consistency hypothesis, not established
behavior in this Black Oak strategy. Separate unused pump commands from
pressure assumptions used in injector calculations. The flat transfer hides
actual pressure response; do not claim it accurately reports a failed response.
Determine which requested/reported/modeled pressure actually feeds injector
flow/offset and whether runtime/rail-temperature corrections change it before
editing compensation or reference values. Also verify real differential
pressure under operation. Do not infer that a pump-duty command alone changes
delivered fuel or justifies disabling injector compensation.

**New2026-10-29 finding:** current v012 ECM6950 Manifold Vacuum Multiplier
is0.484; its matching Editor help calls for zero in a return-style conversion.
See the [read-only audit](../reports/2026-10-29-v012-calibration-audit.md).
This adds a specific model-consistency concern to the flat transfer/reference
issues below. No isolated6950/reference/compensation edit selected; check the
coupled implementation, actual differential pressure and injector data first.

Owner update: regulator is confirmed1:1 manifold-referenced with43psi base.
The owner plans an adapter to reinstall the OEM sensor at the regulator with
its own manifold reference. This is planned hardware work, not a completed or
validated installation. Preserve the existing calibration until the sensor's
identity, signal and pressure behavior can be checked; restoring its exact
transfer and auditing pump/injector implications is a separate revision.
The43psi confirmation does not justify simply changing the injector reference
or replacing the flat40 transfer with a flat43 transfer.

## Verified v009 findings

Read-only Editor inspection found:

- ECM7596 Fuel Pressure Sensor Transfer Function has40psi at every displayed
  breakpoint:0,0,0,0,102,921 and1023input counts. The conversion therefore has
  an explicit constant-pressure mapping; a flat40psi PID is not a measurement
  of actual rail pressure.
- Injector Pressure Drop Reference is40.00psi and Pressure Compensation is
  Enabled. The enabled switch alone does not establish that a real pressure
  measurement is controlling injector compensation.
- Fuel Pump Adaptive Voltage is displayed Enabled; Fixed Duty Cycle manual
  control is Disabled. Whether the factory driver module still controls the
  physical pump, or is bypassed by a relay, remains unconfirmed.
- Editor comparison of v009 against exact v001 lists only Notes, the two idle
  targets and the Open Loop Fuel TPS Thresh vs.RPM table. These pressure-system
  settings were inherited from the owner's original baseline, not introduced
  by the recent idle work.

The live/logged sensor voltage near5V does not establish whether the sensor is
missing, disconnected, failed or otherwise electrically modified. Physical
wiring confirmation was requested. No sensor transfer, pump, injector, spark
or idle setting was changed during this inspection.

## Could missing feedback contribute?

A properly configured return-style system can use a mechanical manifold-
referenced regulator to maintain injector differential pressure and a matching
fixed-pressure injector model. Missing live ECU pressure feedback is therefore
not automatically a fault in such a conversion. However, a real pressure drop,
reference-hose problem, incorrect base pressure or mismatched injector model
could affect fueling while the ECU continues to assume40psi. The current
recordings cannot distinguish these cases.

The constant transfer weakens a theory that a varying sensor voltage is itself
driving a varying pressure calculation through that table. It does not exclude
other fault/wiring paths, pump-control mismatch or actual fuel-delivery trouble.
Enabled injector compensation also does not justify turning it off blindly:
pressure affects injector flow, breakpoint and offset models. See
[HP Tuners injector parameter definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_general.htm).

The owner's43psi engine-off observation does not yet establish operating
differential pressure or the injector characterization reference. Do not change
the regulator or40psi calibration reference to make a number match without
confirming the measurement conditions and injector data.

## Sensor choice

For restoring the original ECU feedback path, a correct SVT-compatible Ford
fuel-rail pressure sensor or a documented exact functional equivalent is the
most direct route. It need not carry an original Ford brand if compatibility
is established. It must match pressure reference, transfer function, voltage
supply/ground/pinout, range, fuel compatibility and response—not simply have
a0.5–4.5V output or the same connector. The correct replacement part and
calibration cannot be selected until the existing hardware is identified.

Ford's manifold-referenced FRP description distinguishes pressure across the
injectors from an atmospheric-reference gauge. See the port-injection FRP
section around printed pages189–190 of
[Ford's OBD system summary](https://www.fordservicecontent.com/Ford_Content/Catalog/OBDII/OBDSM1404.pdf).
That reference is architectural guidance, not a part-number or transfer-table
specification for this exact2004SVT. Do not copy a newer Ford or direct-injection
sensor's scaling into this ECU.

Using gauge pressure consistently:

`injector differential pressure = fuel rail pressure − manifold pressure`

An illustrative40psi differential means33psi rail gauge at−7psi manifold,
and47psi rail gauge at+7psi manifold. Those are examples, not selected operating
targets. A generic gauge transducer and a differential Ford sensor do not
report the same quantity. A single rescaling cannot generally turn gauge
pressure into manifold-relative pressure across changing vacuum/boost without
the appropriate reference input and strategy support.

A suitable transducer on the regulator's fuel-pressure/gauge port can be useful
for independent logging, provided its pressure represents the rail under flow.
The vacuum/boost reference port is a different connection. A separate logging
input avoids altering ECU fueling while the physical pressure behavior is
established. Feeding the stock ECU input is a separate calibration/hardware
integration task. With the current flat transfer, plugging in any new sensor
alone would still leave the ECU conversion at40psi.

Aeromotive describes manifold referencing and1:1 pressure behavior for its EFI
bypass regulators in its [FAQ](https://aeromotiveinc.com/pages/faqs). Actual
regulator model, plumbing, pump control and sensor electrical details remain
to be confirmed; no adapter/thread/pinout is assumed here.

## Iteration order

1. Confirm original FRPS wiring state, pump/FPDM/relay arrangement, regulator
   model, manifold-reference connection and injector identification.
2. Independently measure actual pressure under the existing warm-idle condition
   and relate it to manifold pressure. Keep the tune unchanged for this check.
   Correct hardware instability before trying to compensate with spark or gains.
3. Choose explicitly between the existing fixed-pressure return architecture
   and verified live-feedback restoration. If restoring feedback, validate the
   physical sensor and transfer at known pressures and audit pump/injector
   behavior together before a separate numbered revision is used.
4. Once pressure/model assumptions are established, use a single-variable idle
   comparison: previous950 target for margin, or a separately justified idle
   gain experiment. Keep MBT, dashpot, injector and gain edits separated.

This is a concrete audit and test order, not a diagnosis that replacing the
sensor will cure the near-stalls. No v010 or ECU write was made here.
