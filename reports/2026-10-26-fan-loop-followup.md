# Fan and fuel-loop follow-up

## Owner-confirmed hardware

Factory fans, stock alternator, original upstream O2 sensor retained separately
from a Bosch LSU wideband, and battery relocated to the trunk. Water/methanol
injection was off during the idle tests. Battery ground routing, cable sizes,
ground-strap condition and directly measured supply voltage remain unknown.
The owner expects the power supply to be stable; this has not been independently
established by measurements.

The owner believes the alternator is clutched. Ford's September 2003 SVT
training reference, SVT Focus FEAD section (printed page 3-21, PDF page 69),
documents a one-way clutch incorporated into the generator to reduce drag
variation/NVH. This supports the original specification; it does not verify
the condition or identity of the installed pulley or explain the voltage dip.
[Ford SVT training reference](https://terminator-cobra.com/SVT%20Training%202003.pdf#page=69)

## Read-only v002 fan inspection

| Setting | Value |
| --- | --- |
| Engine > Idle > RPM: Fan High Speed Idle | Enabled |
| System > Fans: Electric Fan Enabled | Enabled |
| Low speed enable / disable ECT | 195 / 190 F |
| Low speed enable / disable VSS | 48 / 53 mph |
| High speed enable / disable ECT | 225 / 215 F |
| High speed high-load enable RPM | 2,240 |
| High speed high-load enable load | 0.6000 |
| High speed high-load enable VSS / ECT | 35 mph / 235 F |

The exposed idle-airflow page does not show the generic low-speed fan airflow
adder described in HP Tuners' general Ford help. Its existence or editability
for this calibration has not been established. Do not substitute another
controller's parameter or assume high-speed idle enable covers a low-speed event.
[HP Tuners Ford idle reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)

The tests never reached the 225 F high-speed ECT threshold. With A/C requested
No in the recordings, the configured temperature-based low-speed stage is a
plausible explanation for fan starts near 195 F, but actual low/high-speed
operation has not been confirmed. Factory fans alone do not establish resistor,
relay or fan-stage behavior. Logged Fan PWM was zero even at an owner-confirmed
fan start, so it cannot serve as the fan-state measurement here.

## Fuel-loop follow-up

The retained original upstream O2 and water/meth-off state help define the
test setup; they do not prove sensor function or justify immediately enabling
learning. Current known tune values include 254-s closed-loop startup delays,
520 F CL O2 sensor temperature threshold, and LTFT disabled. LTFT learning
being disabled is not, by itself, proof that closed-loop short-term correction
is disabled. The specific open-loop TPS/load/delay table values still need
inspection before choosing a calibration change.

## Measurements to distinguish causes

**New owner clarification:** the factory fan resistor was bypassed long ago
following melting issues. The owner did not then realize its role in the
low/high-speed circuit. The bypass is a strong explanation for high-speed-like
engagement when the calibration requests the low-speed stage. Exact bypass
wiring has not been inspected. It does not prove the full cause of the measured
voltage drop or explain why the original connector/resistor overheated.

Restore a correctly rated factory-style low-speed circuit after inspecting and
repairing heat-damaged terminals/wiring and checking fan-motor current. Do not
simply install a resistor in a damaged connector or assume the original melting
was caused by calibration. The owner requested an interim test because of turbo
heat exposure; [temporary v003](../tunes/v003-temp-fan-stage-match.md) matches the
ECU high-speed temperature pathway to the physical bypass behavior. Its
effectiveness is unverified and it does not replace the hardware repair.

The owner reports that engagement sounds like a high-speed roar. Treat this as
an observation, not confirmation of the actual fan stage. Determine whether
the fans operate correctly at low speed and separately at high speed before
changing fan-related compensation or replacing components.
If a suitable meter is available, compare battery-post voltage and accessible
underhood supply voltage during fan engagement with the ECU-reported trace.
A verified voltage-drop test can then distinguish supply sag from cable/ground
drop. The short recorded drop is not, alone, a diagnosis of a failed alternator
or bad wiring. Keep the existing tune unchanged during these checks.

No parameter changes or ECU writes were performed during this inspection.
