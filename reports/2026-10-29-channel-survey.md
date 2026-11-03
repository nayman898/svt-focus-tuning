# Stationary channel survey — 2026-10-29

Three consecutive short parked captures. Labels indicate data presence in these
specific exports, not sensor validity or universal controller support. Original
HPL/SQLite, CSV, requested profiles and per-channel JSON audits are preserved
privately under `logs/2026-10-29-channel-survey/`.

Owner confirmed safe stationary operation; driving remains on hold. v012 is
carried forward from the last owner confirmation, not independently read back.
Accessory state was not supplied; fan operation is not directly established.

| Capture | Profile | VCM rows | Elapsed range, s | Gaps >0.3 s |
| --- | --- | ---: | --- | ---: |
| A: `paired-20261029-145438-961a976b-v012` | 31 channels | 2853 | 1.793–68.132 | 0 |
| B: `paired-20261029-145613-7430673c-v012` | 28 channels | 2862 | 1.603–68.023 | 0 |
| C: `paired-20261029-145739-2b51f12b-v012` | 34 channels | 2873 | 1.873–68.478 | 0 |

## Per-channel results

Present = nonblank fraction of exported rows; constant values remain unvalidated.
Missing means the channel was not requested/exported in that capture. CSV row
spacing does not establish independent ECU sampling.

| Native ID | Channel | A:31 | B:28 | C:34 |
| --- | --- | --- | --- | --- |
| 2135 | Engine RPM | 100% present; 739 distinct | 100% present; 906 distinct | 100% present; 851 distinct |
| 12700 | Torque Source | 100% present; 1 distinct | 100% present; 1 distinct | 100% present; 1 distinct |
| 2124 | Engine Coolant Temp | 100% present; 6 distinct | 100% present; 4 distinct | 100% present; 5 distinct |
| 2500 | Timing Advance | 100% present; 210 distinct | 100% present; 312 distinct | 100% present; 318 distinct |
| 19046 | Spark Source | 100% present; 1 distinct | 100% present; 2 distinct | 100% present; 1 distinct |
| 3018 | Throttle Position ADC (Relative) | 100% present; 6 distinct | 100% present; 6 distinct | 100% present; 7 distinct |
| 3017 | Throttle Position ADC (Absolute) | 100% present; 1 distinct | 100% present; 3 distinct | 100% present; 5 distinct |
| 2300 | Mass Airflow | 100% present; 387 distinct | 100% present; 394 distinct | 100% present; 332 distinct |
| 2082 | Idle Air Solenoid DC | blank | 100% present; 1613 distinct | 100% present; 1393 distinct |
| 6100 | O2 Voltage B1S1 | blank | 100% present; 470 distinct | blank |
| 6005 | Equivalence Ratio Commanded - Bank 1 | blank | 100% present; 1713 distinct | blank |
| 19047 | Fuel Source | 100% present; 1 distinct | 100% present; 1 distinct | 100% present; 1 distinct |
| 19049 | Idle Speed Source | 100% present; 1 distinct | not requested | 100% present; 1 distinct |
| 12812 | Misfire Detected | 100% present; 1 distinct | 100% present; 1 distinct | 100% present; 1 distinct |
| 14510 | Trans In Gear | blank | 100% present; 1 distinct | 100% present; 1 distinct |
| 17500 | Brake Pedal | blank | 100% present; 1 distinct | blank |
| 8000 | Vehicle Speed | blank | 100% present; 1 distinct | 100% present; 1 distinct |
| 2100 | Control Module Voltage | 100% present; 142 distinct | 100% present; 135 distinct | 100% present; 136 distinct |
| 3130 | Total Misfires | 100% present; 1 distinct | 100% present; 1 distinct | 100% present; 1 distinct |
| 18008 | Air Load (Hi Res) | 100% present; 2343 distinct | blank | 100% present; 2358 distinct |
| 6304 | Short Term Fuel Trim Bank 1 | blank | 100% present; 1713 distinct | blank |
| 2302 | Mass Airflow Sensor | 100% present; 431 distinct | 100% present; 410 distinct | 100% present; 402 distinct |
| 16408 | Mass Airflow AD Counts | 100% present; 431 distinct | 100% present; 410 distinct | 100% present; 402 distinct |
| 2240 | Idle Adapt (STIT) | 100% present; 1311 distinct | not requested | blank |
| 12304 | Throttle Control TPS State | 100% present; 1 distinct | blank | blank |
| 12942 | Closed Loop Active | 100% present; 1 distinct | blank | blank |
| 12944 | Closed Loop Ready | 100% present; 1 distinct | blank | blank |
| 12978 | Open Loop Conditions | 100% present; 1 distinct | blank | blank |
| 2231 | LTIT PN/ACoff | blank | not requested | blank |
| 2210 | Idle Desired RPM | blank | 100% present; 1 distinct | 100% present; 1 distinct |
| 12947 | Open Loop FMEM | 100% present; 1 distinct | blank | blank |
| 17603 | AC Clutch Engaged | not requested | not requested | blank |
| 17611 | AC Requested | not requested | not requested | 100% present; 1 distinct |
| 7231 | Fan PWM Duty Cycle | not requested | not requested | blank |

## Decisions and limits

- Do not label a channel unsupported from one blank capture. Coverage changed
  between profiles/sessions and even the previous baseline lost status fields.
- STIT and Idle Speed Source produced data in A. LTIT PN/ACoff was blank in A.
  The31-channel combination did not retain required core coverage, so it is not
  accepted as the routine tuning profile.
- B restored IAC, desired RPM, O2 and trim, while several status fields were blank.
  Keep this28-channel profile as the comparison fallback, with per-run audits.
- B minimum709.25RPM at26.984s: TPS182.82counts, ECT194F, voltage12.875V,
  IAC50.14%, timing30degrees, Spark Source Idle Feedback. About0.5s earlier
  RPM942; about0.5s later930. The dip occurs without an exported Base/MBT label
  at its minimum. That weakens a diagnosis requiring MBT handoff for every dip.
  Voltage/load correlation does not determine which disturbance came first.
- No calibration edits, ECU writes, boost commands or driving tests performed.
  Engine shutdown remains with the owner.
- Next: isolate additional diagnostic groups around a smaller fixed core, repeat
  blank channels, and test selected longer request intervals. Change one acquisition
  variable at a time; no adaptation resets or engine restarts solely for this survey.
  This is an initial31/28/34 survey, not an audit of every controller-listed channel.
