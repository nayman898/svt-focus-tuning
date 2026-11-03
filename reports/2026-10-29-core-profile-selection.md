# Core profile selection — 2026-10-29

Five additional stationary captures, no calibration changes. This is selection
among the tested configurations under warm parked conditions, not proof of a
globally optimal polling setup or suitability for driving/cold-start diagnosis.

| Capture | Session | Export rows | Core presence | Blank fields |
| --- | --- | ---: | --- | --- |
| 14-channel A | `paired-20261029-150300-17889ea0-v012` | 4145 | 12/12 | Vehicle Speed, Short Term Fuel Trim Bank 1 |
| 14-channel repeat | `paired-20261029-150433-2c99d8a3-v012` | 4152 | 12/12 | Vehicle Speed, Short Term Fuel Trim Bank 1 |
| 12-channel core | `paired-20261029-150611-39e697b3-v012` | 4138 | 12/12 | none |
| 15-channel idle air | `paired-20261029-150734-8b9aaac8-v012` | 2884 | 12/12 | none |
| 15-channel load | `paired-20261029-150906-2d255f00-v012` | 4138 | 12/12 | AC Requested, AC Clutch Engaged, Fan PWM Duty Cycle |

## Per-channel coverage

Percent populated refers to exported rows, not independent ECU updates. Data
presence is not sensor calibration or fault-detection validation. Requested
intervals/types/addresses are preserved with every private session.

| ID | Channel | 14 A | 14 repeat | Core12 | Air15 | Load15 |
| --- | --- | --- | --- | --- | --- | --- |
| 2135 | Engine RPM | 100% | 100% | 100% | 100% | 100% |
| 2124 | Engine Coolant Temp | 100% | 100% | 100% | 100% | 100% |
| 2500 | Timing Advance | 100% | 100% | 100% | 100% | 100% |
| 19046 | Spark Source | 100% | 100% | 100% | 100% | 100% |
| 2100 | Control Module Voltage | 100% | 100% | 100% | 100% | 100% |
| 19047 | Fuel Source | 100% | 100% | 100% | 100% | 100% |
| 3017 | Throttle Position ADC (Absolute) | 100% | 100% | 100% | 100% | 100% |
| 2300 | Mass Airflow | 100% | 100% | 100% | 100% | 100% |
| 2082 | Idle Air Solenoid DC | 100% | 100% | 100% | 100% | 100% |
| 6100 | O2 Voltage B1S1 | 100% | 100% | 100% | 100% | 100% |
| 8000 | Vehicle Speed | 0% | 0% | not requested | not requested | not requested |
| 6304 | Short Term Fuel Trim Bank 1 | 0% | 0% | not requested | not requested | not requested |
| 2210 | Idle Desired RPM | 100% | 100% | 100% | 100% | 100% |
| 12942 | Closed Loop Active | 100% | 100% | 100% | 100% | 100% |
| 19049 | Idle Speed Source | not requested | not requested | not requested | 100% | not requested |
| 2240 | Idle Adapt (STIT) | not requested | not requested | not requested | 100% | not requested |
| 2231 | LTIT PN/ACoff | not requested | not requested | not requested | 100% | not requested |
| 17611 | AC Requested | not requested | not requested | not requested | not requested | 0% |
| 17603 | AC Clutch Engaged | not requested | not requested | not requested | not requested | 0% |
| 7231 | Fan PWM Duty Cycle | not requested | not requested | not requested | not requested | 0% |

## Acquisition decision

See the saved [operating profile policy](../profiles/operating-profiles.md) for
which profile to select and the acceptance limits. Original HPL, SCG SQLite,
full exports, profile XML and audits are under the private survey archive.
All sessions use the owner-carried-forward v012 label, not a new ECU readback.
Keep the tune unchanged and audit actual coverage on every new recording.

No driving, deliberate load switching, throttle tests, adaptation resets or
calibration writes were performed. Accessory state was not independently
established. A blank load-state channel is not OFF or proof of no load.
