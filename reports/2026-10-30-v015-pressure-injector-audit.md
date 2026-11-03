# v015 pressure and injector audit

Read-only VCM Editor inspection of owner-installed v015,2026-10-30.
All16 cataloged tune binaries matched hashes/sizes before and after. No
calibration save, ECU write/readback, code clearing, wiring change or running
test occurred. Astra independently reviewed the evidence and documentation.

**Finding:** the exposed calibration does not currently establish a mechanism
where the bypassed pump's failure to follow a command progressively changes
injector fueling. Pressure-related injector multipliers are displayed neutral.
There is still temperature-dependent desired-pressure logic, but its link to
injector calculations and fault substitution is not exposed. Do not equate
these findings with a fully validated return conversion or normal fuel delivery.

## Physical control boundary

Owner confirms battery-fed pump relay triggered by ignition-on power, with
fuel-shutoff-switch interruption. ECU/FPDM speed modulation cannot operate the
pump through the bypassed module. Actual terminal voltage and pressure under
load remain unmeasured. The shutdown implementation is owner-reported, not
independently inspected; no alteration is proposed.

The regulator is owner-confirmed1:1 manifold referenced,43psi engine-off base.
The OEM pressure sensor is still not confirmed installed. ECU pressure PID
values must not substitute for the independent gauge.

## Verified injector and pressure entries

| Item | Editor observation | Consequence for this hypothesis |
| --- | --- | --- |
| ECM7596 sensor transfer | All7 displayed outputs40psi | No dynamic pressure measurement through this mapping |
| Injector pressure reference | 40.00psi | Must match the actual injector characterization/model; not automatically changed to43 |
| ECM32047 pressure compensation | Enabled | Switch alone does not establish a varying correction |
| ECM32062 low-flow pressure multiplier | All6 values1.00 | No varying correction evident at displayed precision |
| ECM32060 high-flow pressure multiplier | All6 values1.00 | Same |
| ECM32064 breakpoint pressure multiplier | All6 values1.00 | Same |
| ECM32052 offset pressure multiplier | All7 values1.0000 | Same |
| ECM6950 vacuum multiplier | Retained0 via verifiedv015=v013 calibration | Previous0.484 issue is not the current value |
| Low/high injector slopes | 0.017500000 /0.016700000lb/s | 63.00 /60.12lb/hr tune values; physical injector characterization unverified |
| Breakpoint / minimum PW | 0.00003360lb /0.00050000s | Actual operating PW is still missing |

The pressure-multiplier axes display repeated40psi breakpoints. Record that as
an Editor observation, not a reconstructed raw firmware axis or interpolation
algorithm. All tables above were read in the current file rather than inferred
from the enabled switch. Private table captures are under .local/v015-*.

Voltage offset ECM32050 remains active/nonflat: at12,13,14,15V it displays
0.000636,0.000517,0.000429,0.000327s respectively. That must correspond to the
real injectors. Logged module voltage does not measure pump voltage, and no
actual injector PW trace is available to quantify its contribution to a dip.

HP Tuners documents pressure slope/offset multipliers separately from voltage
offset and injector reference pressure. These general definitions do not
document the exact UJAHAS3 input-selection/fallback algorithm.
[Injector parameter definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_general.htm).

## Pump commands and temperature-dependent pressure

Fuel Pump page displays Adaptive Voltage Enabled, Fixed Duty Cycle Disabled,
P/I/D gains0.0600/0.0996/0.0000, update time2s, duty bounds10–48% and secondary
monitor Enabled. FPDM KOEO/KOER tests are Enabled. Those existing settings
show retained factory control/diagnostic logic; they do not give that logic
physical pump-speed authority through the reported bypass. A diagnostic
expectation is not by itself proof of a fueling fallback.

ECM43000 Desired Fuel Pressure Over Injector displays40.00 at all7 rows.
ECM43005 Desired Fuel Pressure Over Injector AAT Adder displays:

| Displayed temperature breakpoint | Displayed pressure value |
| ---: | ---: |
| -127 (three rows) | 40.00 |
| 144 | 40.00 |
| 150 | 42.00 |
| 170 | 57.00 |
| 200 | 62.00 |
| 254 | 62.00 |

Matching Editor help says this adds to injector pressure drop versus ambient
air temperature. This is a real nonconstant calibration entry worth retaining
in the audit. **Do not simply add40+40 and claim the ECU requests80psi.**
The displayed table's scaling/combination, active ambient model value, final
requested pressure and injector-side use have not been independently verified.
It is not an ECT-axis table; crossing158F coolant does not prove crossing its
ambient-temperature breakpoint.

ECM43010 Ambient Rail Temp Time Constant versus Fuel Flow is nonflat (displayed
values175,155.09,112.28,50,15,3.17,24.30,24.30 across its8 rows). This establishes
a modeled thermal path, not the actual rail temperature or a demonstrated
minute-scale injector-fueling change. No direct rail-temperature trace exists.

Navigator searches for Injector, Enrich, Soak, Rail, FMEM, Substitute, Hot Enrich
and Engine Run Time Enrich did not expose the generic injector hot/soak/runtime
enrichment tables or an FRP substitution control in this installed definition.
Absence from this UI search is not proof that the firmware has no such logic.
No public primary UJAHAS3 control-law reference was verified. Later Ford GDI
descriptions must not be substituted for this port-injection controller.

## Cold/warm fuel tables: important correction

Current warm-base enable is158F, disable90F and enable time10s. Manual fuel
control is Disabled. In ECM44512 Fuel Base Cold, the120–190F columns display
lambda1.03 across every displayed load row. ECM44516 Cold Enrich Decay's final
60s row displays0.03 in those columns. Matching Editor help says decay is
subtracted from base lambda: **1.03 minus0.03 =1.00**.

This corrects the earlier suggestion that the residual0.03 entry alone
established persistent rich enrichment. The paired values must be considered.
Zeroing that row alone could instead produce a nominal1.03 cold-path target.
Actual branch eligibility, other corrections and emitted mixture still require
verification; this arithmetic is not proof of the final commanded lambda.

The latest v015 log left CL near118F and returned near158F, with its deepest
dip just before reentry. The158F boundary is relevant context, but this audit
does not prove why CL dropped at118F. The actual state flags and idle-air
adaptation remain the most immediate next measurements.

## Decision and next work

1. Keep v015 unchanged. No pump-gain, pressure-reference, compensation-disable,
   injector-slope or cold-decay edit is justified from this audit.
2. Validate the prepared Loop State20 profile to clarify the CL transitions.
   Preserve the working16 fields if optional additions fail. Use Heater State18
   separately if sensor-readiness evidence is needed.
3. Obtain same-interval pressure-gauge/video evidence with manifold pressure,
   and actual pump-terminal voltage if delivery variation is suspected.
   Independent differential pressure is needed before treating40/43psi as a
   calibration correction. Avoid another throttle/boost test to obtain it.
4. Highest-value missing ECU measurement remains actual injector PW alongside
   a verified fuel-command definition. Requested pressure, rail/ambient model
   and FRP validity could help if genuinely supported; do not invent channels.
5. If the exposed Editor definition cannot establish the pressure input path,
   obtain exact strategy documentation/HP Tuners clarification before changing
   the ambiguous AAT entry. No upload or support message has been sent.

The return conversion may still contain a static injector/model mismatch or
a hidden fallback. This audit narrows the suspicion; it does not certify the
conversion or explain every stall. Pending P0320 and upstream O2 readiness
remain separate unresolved evidence.
