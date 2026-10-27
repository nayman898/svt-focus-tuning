# Engine-off channel validation and low-RPM enrichment review

Owner confirmed the vehicle connected with engine off. No calibration edit,
ECU write, engine start or throttle exercise was performed. Editor was open
on prepared v006; this does not establish the ECU's installed revision.
Session folder uses v005 as the last owner-attributed running revision.

## Scanner changes and saved evidence

Saved the current 60-row configuration to
`.local/before-focused-progress.Channels.xml`, then loaded the existing
`profiles/2004 Focus SVT - Idle Fuel Recovery.Channels.xml` (27 channels).
Performed a brief engine-off scan and stopped it. Preserved native HPL and
Entire Log CSV under `logs/2026-10-26-v005-koeo-channel-check/VCM/`, with
size/SHA-256 manifest in the parent directory. Focused profile remains loaded;
scanning is stopped. Original profile files and tune binaries are unchanged.

CSV contains 929 exported rows, offsets 1.537-23.030 s. These include
interpolated/asynchronous rows, not 929 independent sensor observations.
CSV creation clock says 21:01:31 without timezone; do not interpret that as
local time or use it to align another recording. No wideband pairing applies.

| Channel | Saved coverage | Range |
| --- | --- | --- |
| RPM | 929/929 | 0 throughout |
| Absolute TPS ADC | 929/929 | 182.8213-183.8203 counts |
| Upstream O2 | 929/929 | 0.0029297 V throughout |
| B1 STFT | 929/929 | 16.5955-16.9281% |
| MAF flow | 929/929 | 0 lb/min throughout |
| Module voltage | 929/929 | 12.25-12.3125 V |
| Relative TPS | 0/929 | Missing |
| Coolant temperature | 0/929 | Missing |

This establishes recorded channel population, not engine-running accuracy.
Engine-off O2 and STFT cannot diagnose mixture or justify fuel corrections.
MAF zero at zero RPM does not validate its running scaling. Closed Loop Active
and Ready remain No, consistent with this engine-off capture. No conclusion
about battery health follows from the module-voltage snapshot.

The previous fan-off CSV independently rechecked today has O2, MAF voltage
and relative TPS empty in all 8,822 rows, while commanded mixture and actual
spark populate throughout. The focused profile is therefore useful progress,
but reduced request count is not proven to cause the improved population.
Coolant populated before the profile change and is missing in this short
capture. Restore/verify coolant acquisition before an engine-running test;
do not declare it unsupported or diagnose a sensor fault from this result.

## Quantified inherited TPS transition

The previously Editor-verified v005/v006 ECM 32731 rows are 200 counts at
1,500 RPM and 0 at 2,000 RPM. Under linear interpolation:

`threshold = 200 - 0.4 * (RPM - 1500)`

| RPM | Interpolated threshold, counts |
| ---: | ---: |
| 1500 | 200 |
| 1540 | 184 |
| 1545 | 182 |
| 1600 | 160 |
| 1750 | 100 |
| 2000 | 0 |

The historical closed-throttle range 181.8223-183.8203 crosses this curve
around 1540.45-1545.44 RPM. Today's engine-off absolute TPS is consistent with
that historical range. If this strategy compares absolute TPS as hypothesized,
a closed throttle could satisfy this TPS open-loop request above roughly
1,540-1,545 RPM. This is a conditional lookup calculation, not a measured
switching threshold: comparator semantics, interpolation implementation,
other gates and delays require verification. No throttle sweep is authorized
by this review. Do not extrapolate parked closed-loop success to driving.

HP Tuners documents the table as the TPS threshold for open-loop fuel versus
RPM, and separately lists delay/blending controls. Its generic reference does
not establish this controller's absolute/relative comparator:
https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm

Next calibration inspection should capture the existing open-loop delay vs.
RPM/gear, maximum, ramp/blending controls and base fuel tables in Editor,
without selecting replacement values from this crossing calculation alone.

## Next useful measurement

Recover saved coolant data first. Then a separate owner-started stationary
session with the existing running calibration and paired wideband can test
whether O2/STFT/MAF remain populated during actual closed-loop operation.
Record actual fan on/off events and fresh session timing. The engine-off STFT
value is not an instruction to add or subtract fuel. v006 remains conditional
on circuit repair and fan-stage verification; no new tune was created.
