# Stationary stall — 2026-10-29

**Later owner clarification:** v010 also stalled occasionally, uncaptured;
later spark changes felt steadier between random stumbles. The initial rollback
recommendation is withdrawn. See [revised onset/handoff analysis](../docs/post-stall-comparison.md).
The event below remains valid; it does not establish a gain-caused regression.

Source `paired-20261029-154228-0cbfb558-v012`; tune label carried forward from
owner-confirmed v012, not independently read back. Owner reported an engine
stall during the planned five-minute stationary idle-air recording. The test
was terminated; no restart, reset, ECU write or calibration change requested.
Owner accessory/throttle/fan context was requested and remains unconfirmed.

Subsequent owner clarification: untouched idle, A/C and defrost OFF; owner does
not believe fan related, with exact fan state unconfirmed. OEM pressure sensor
still awaiting installation; GlowShift sender at regulator shows41psi engine-off
with pump ON. That is a later static observation, not stall-time fuel pressure.

## Preservation and capture limits

VCM was manually stopped and exported after the report, with acknowledgement
from its original process. Native HPL/CSV are preserved. VCM has9,210 rows over
1.178–185.527s, no export gaps above0.3s. CL Active and STIT are entirely blank;
the other requested fields have data. This profile's earlier complete capture
did not guarantee complete acquisition in this run.

The SCG dashboard/worker was no longer running when stop was attempted. Its
exact exit cause/time is unverified. The five-minute automatic run did not
complete as intended. SQLite integrity returned OK; its committed data was
recovered using the SQLite backup API, preserving WAL content. The backup holds
1,532 samples through SCG elapsed125.964s, including the stall interval.
The database remains unfinalized; CSV exposes that state. Do not relabel it clean.
The original manifest remains unchanged; a separate recovery record marks the
bundle partial and describes manual VCM export/SCG recovery.

Full native files, requested profile, owner context/report, recovery record,
hashes, exports and analysis are under private `logs/2026-10-29-v012-stall-01/`.
The original session and WAL companions remain preserved. No logger processes
were observed at recovery; Scanner stop was acknowledged. No monitoring remains
active, and no new recording was started.

## Lead-up in VCM elapsed time

| Elapsed s | RPM | Spark source | Timing, degrees | IAC command, % | Module voltage |
| ---: | ---: | --- | ---: | ---: | ---: |
| 106.235 | 904.5 | Idle Feedback | 4.5 | 38.64 | 13.375 |
| 107.238 | 936.75 | Idle Feedback | 3.75 | 36.95 | 13.563 |
| 108.231 | 863.25 | Idle Feedback | 7.25 | 39.37 | 13.563 |
| 108.735 | 680.5 | Idle Feedback | 23.25 | 52.43 | 13.375 |
| 109.233 | 255.25 | Base/MBT | 28.0 | 100.0 | 12.688 |
| 110.232 | 0 | Borderline | 23.75 | 45.37 | 12.750 |

ECT is188F; absolute TPS remains about182.82–183.82counts, without an obvious
large throttle opening. Desired idle reports896RPM, as in earlier quantized
exports. LTIT PN/ACoff is about-0.223lb/min and does not make an abrupt step
in the sampled lead-up. STIT is missing, so total adaptive-air behavior is not
known. Idle Speed Source remains Idle RPM Adder vs.IAT. Labels and interpolated
or asynchronous channels cannot establish the exact ECU control chronology.

## Wideband overlap

Native metadata gives provisional SCG elapsed = VCM elapsed +1.236s; drift and
sensor/transport delay are unverified. In nominal VCM107–108s, lambda spans
0.976–1.019;108–109s spans0.970–1.058. Around109.49s it reports1.160 while
pressure rises toward atmospheric as the engine stops. The lean indication
does not clearly precede the RPM collapse on this provisional mapping. Combustion
loss, exhaust oxygen and transport delay prevent calling this proof of inadequate
fuel delivery. There is still no trustworthy measured rail-pressure signal.

## Interpretation and next decision

This is a real worsening of outcome: prior short captures showed recovery,
whereas this event reaches zero RPM. The ECU reports substantial corrective
spark and eventually full IAC command without recovery. That does not prove
the valve delivered the commanded airflow. Voltage loss can follow falling
alternator speed; the trace does not establish it as the initiating fault.
RPM begins falling while Idle Feedback is still reported, before Base/MBT.
Preserve the handoff hypothesis but do not disable corrective spark or cut gain
again solely because of the label.

Leave the engine off for now. Pause further routine running comparisons pending
review of this event and owner context. Do not repeat the stall deliberately.
No v013 numerical change selected. Next work is an offline check of learned/base
idle-air assumptions, air-control authority and the known pressure/fuel-model
uncertainties, plus investigation of the unexpected logger exit before another
long recording. Idle Air15 remains conditional, not a guaranteed complete profile.
