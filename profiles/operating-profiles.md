# Profile selection for iterative testing

**Later stall-test update:** Target Idle Air15 lost CL Active and STIT in the
[five-minute run](../reports/2026-10-29-v012-stall-review.md). Its earlier complete
capture remains valid only for that capture. Do not treat any profile as
guaranteed; pause running tests while the stall and logger exit are reviewed.

Updated2026-10-29. Stationary operation is owner-confirmed; driving remains on
hold. This policy selects among tested acquisition settings, not an engine tune.
It does not certify a globally optimal polling rate or unsupported channels.

## Default parked core

[Core Stationary](2004%20Focus%20SVT%20-%20Core%20Stationary.Channels.xml) requests
12 channels: RPM, desired RPM, ECT, module voltage, timing, Spark Source, Fuel
Source, absolute TPS, MAF, IAC duty, upstream O2 and CL Active. Original saved
types/addresses/intervals are retained. SCG lambda/AFR/boost/WGDC stays in its
separate stream; no serial RPM wire is needed.

All12 fields populated in two14-channel captures and a dedicated12-channel
capture on2026-10-29. The two extra requests, speed and STFT, were blank in both
14-channel captures. The12-channel export had no time gaps above0.3s. This is
short warm-idle coverage evidence, not independent measurement validation.
The [selection report](../reports/2026-10-29-core-profile-selection.md) records
the individual runs and targeted-profile results.

The15-channel Target Idle Air profile also populated all15 fields in its first
dedicated warm parked capture, with no export gaps above0.3s. STIT ranged
-0.0208 to+0.0644lb/min; LTIT PN/ACoff about-0.2112 to-0.2092lb/min. Use it
provisionally for the next learned-airflow/idle-state comparison and audit each
session. These values do not alone establish incorrect base airflow or justify
resetting adaptation. The12-field core has repeated presence evidence; the
three additions have one complete targeted capture so far.

Final selection: all12 required fields populated in all five additional captures
(two14-channel, one12-channel and two targeted15-channel runs), with no exported
gaps above0.3s. Core Stationary is loaded and saved; Scanner is stopped. All
recordings finalized/exported. Target Idle Air is provisionally usable for warm
parked adaptation work. Target Electrical Load retained core coverage but all
three optional fields were blank; it is **not accepted for load attribution**.
Use the core plus owner event marks for that purpose until another survey
establishes useful load-state data. Do not repeatedly switch to the failed load
profile during ordinary tuning logs.

## Choose the profile before the session

| Question | Saved profile | Use and limits |
| --- | --- | --- |
| Routine stationary idle or an unspecified parked dip | [Core Stationary](2004%20Focus%20SVT%20-%20Core%20Stationary.Channels.xml) | Default; audit all12 fields before tuning interpretation |
| Learned-air correction or idle-state handoff | [Target Idle Air](2004%20Focus%20SVT%20-%20Target%20Idle%20Air.Channels.xml) | Core12 plus STIT2240, LTIT2231 and Idle Speed Source19049; actual acceptance follows saved coverage, not the filename |
| Fan/A/C electrical load attribution | [Target Electrical Load](2004%20Focus%20SVT%20-%20Target%20Electrical%20Load.Channels.xml) | Core12 plus AC Requested17611, AC Clutch17603 and Fan PWM7231 at1s; blank remains unknown and owner event marks remain necessary |
| Fuel-control diagnosis | [Drive Torque Diagnostics](2004%20Focus%20SVT%20-%20Drive%20Torque%20Diagnostics.Channels.xml) | Earlier28-channel fallback can provide trim/command, but availability varies; first verify those actual fields. No fuel correction without valid measurements |
| Driving/return-to-idle | Earlier28-channel profile, after repair and a saved coverage check | The12-channel core omits speed, brake, gear and torque source; it is not a driving substitute |

The31/34-channel broad trials are diagnostic archives, not default profiles.
Earlier14/17-channel trial files are intermediate candidates; use the specific
Core Stationary / Target names above, with the selection report's limitations.
Warm-idle success does not establish cold-start, moving, fault or A/C-on coverage.

## Agent owns the switches

1. State the question, exact profile and event needed. Check current Scanner
   and dashboard state; preserve any recording already in progress.
2. Stop and export the current pair before changing channels. Verify manifest
   saved/partial and native files, then close only that stopped, exported log.
3. Save the actual active configuration if not already preserved. Load the
   selected XML through Scanner; verify the requested count and control state.
   Keep a copy/hash with each session. A saved candidate is not proof of loading.
4. Start a fresh pair with the owner-confirmed tune label. Check real samples
   from both sources before announcing logging. Do not restart or reset the ECU
   for a profile switch.
5. Inspect a short saved capture for required fields, gaps and meaningful changes.
   At least99% populated required fields and no export gaps above0.3s is the
   present screening rule, not a guarantee of sensor rate or causality. Report
   categorical/constant channels without pretending they prove fresh updates.
6. Retain a targeted profile only if required core coverage is preserved and
   the question's diagnostic fields populate. Partially useful optional fields
   can be kept explicitly, while blank ones remain unresolved. Fall back to the
   tested core for parked control analysis if target requests break it.
7. Finish with stopped/exported sessions and the core restored unless the next
   explicit question requires a different profile. Update the register and give
   the owner a clear completion message; engine shutdown remains with the owner.

Do not silently switch profiles mid-run, reuse clock offsets between recordings,
infer a fan cycle from ECT alone, or change tune values to make a logging trial
appear successful. Preserve full native recordings and both exports.
