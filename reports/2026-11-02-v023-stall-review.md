# v023 idle trial: fluctuations and stall

The v023-labeled trial ended in an owner-confirmed stall. Do not adopt v023 as
the baseline or lower nominal idle spark further on this evidence. Return to
[v021](../tunes/v021-fuel-pressure-feedback.md) for the next controlled hardware
comparison; that rollback has been recommended, not confirmed performed.
No v024 was prepared and no ECU write, code clear, adaptation reset or engine
operation was performed for this review.

## Recording and coverage

Source: `paired-20261102-171032-65205513-v023` in the logger's local sessions.
Preserved natives, CSVs, manifest and analysis are in the ignored
`logs/2026-11-02-v023-idle10-01/` directory. The bundle was already stopped and
saved when checked. Its manifest reports saved with no missing files/errors;
the SCG database is finalized and passes integrity checking.

VCM contains 13,394 rows from 1.311 to 321.607 seconds. All 18 requested channels
have values, including desired RPM and absolute TPS, which were absent in the
v021/v022 exports. There are gaps at 64.943-72.137 and 125.979-128.680 seconds;
neither overlaps the stall. Export rows are asynchronous/interpolated and are
not independent high-speed measurements of every PID.

SCG elapsed = VCM offset + 1.155303 seconds from recording metadata. This alignment
is provisional and does not correct exhaust transport or sensor delay.
The new logger readiness feature was not active in this already-running app.

## What changed around 4:20?

Closed loop began at 85.386 seconds. FMEM remained No throughout. Desired idle
settled at 944 RPM and remained there through the event. Fluctuations existed
earlier too, so 4:20 is an increase in severity rather than the first dip.

| VCM window | RPM min / mean / max | Mean IAC duty | Mean spark | Mean FRP voltage |
| --- | --- | --- | --- | --- |
| 240-260 s | 912 / 951 / 984 | 43.50% | 8.23 degrees | 3.057 V |
| 260-280 s | 836 / 951 / 1016 | 40.78% | 9.09 degrees | 3.059 V |
| 280-300 s | 845 / 951 / 1014 | 39.17% | 9.11 degrees | 3.060 V |

Mean RPM conceals the worsening excursions. Mean wideband lambda stays near
1.01-1.02 across these windows; pressure does not show a preceding collapse.

ECT first reaches 196 F at 235.924 seconds, then falls to 190 F at 257.431.
That is close to the configured low-fan off threshold and the owner's reported
onset. Actual fan state was not logged, so a fan load release is a hypothesis.
The first running RPM occurs at 4.575 seconds; estimated engine runtime reaches
255 seconds near VCM 259.575, also close to the onset. The inherited maximum
cold-start spark table has a final runtime breakpoint at 255 seconds, but its
active eligibility is not measured. These two correlations cannot distinguish
a fan/load handoff from a startup-control transition. The idle-air runtime
taper's final 200-second row is reached earlier, around VCM 204.6 seconds.

The expected sustained two-degree final-spark reduction from the nominal-table
edit is not established by this comparison. Do not assume another nominal-spark
reduction would resolve the problem.

## Stall chronology: a distinct engine-speed reporting anomaly

### Owner fan-marker clarification and severity comparison

Owner subsequently identifies observed fan operation as approximately 196 F on
and 188 F off. In this capture the first markers on the relevant warming/cooling
cycle occur at 235.924 and 269.853 seconds. Use these owner-supported temperature
proxies in preference to treating the configured 190 F threshold as the observed
off edge. There is still no direct fan command/current measurement.

Equal 30-second windows around the 188 F marker, before the stall:

| Metric | Before: 239.853-269.853 s | After: 269.853-299.853 s |
| --- | ---: | ---: |
| Full RPM range | 912.25-984.25 | 836.25-1016.00 |
| Peak-to-peak span | 72.00 RPM | 179.75 RPM |
| Central 90% range, row-weighted | 924.50-974.50 | 888.25-991.50 |
| Time outside desired 944 +/- 50 RPM | 0% | 9.94% |
| Time below desired by more than 100 RPM | 0 s | 0.097 s |

Time fractions use left-sample intervals, exclude gaps above 0.3 seconds and
exclude the final sample without a following interval in each window. Quantiles
are descriptive export-row percentiles, not independent acquisition samples.
The later window has about 2.5 times the full span and 2.1 times the central
90% width. Similar mean RPM must not classify these as equally stable. The
short deepest excursion alone also understates the repeated broader movement.
The stall remains a separate severe outcome, outside these comparison windows.
This supports a load/operating-point investigation without isolating causality
from startup runtime and temperature. No additional recording was requested.

| VCM offset | Reported RPM | Other observations |
| --- | ---: | --- |
| 303.747 s | 948.25 | Desired 944; spark 9 degrees, Idle Feedback; IAC 38.36%; FRP 3.057 V; battery 13.75 V; lambda 1.004 |
| 304.004-304.053 s | 0 | Brief zero report; Base/MBT spark source; FRP 3.042 V; battery 13.50 V; lambda 1.006 |
| 304.101 s | 789.75 | RPM returns; Borderline spark source; FRP 3.037 V; lambda about 1.010 |
| 304.501 s | 572.75 | Spark 22.5 degrees; FRP 3.022 V; battery 13.44 V; lambda about 1.004 |
| 304.991 s | 269 | Battery falls to 12.19 V; lambda about 1.151 |
| 305.665 s onward | 0 | Sustained stop; closed loop switches off at 305.712 s |

The brief zero followed by roughly 790 RPM is a signal/reporting clue, not proof
the crankshaft physically stopped and restarted in that interval. CKP/PIP signal,
connector/harness, PCM power/grounds, and acquisition artifacts remain candidates.
The owner confirms the subsequent physical stall. MBT appears with the reported
RPM collapse; these rows do not establish MBT as its cause.

Ford's [2004 OBD operation summary, pages 66-67](https://www.fordservicecontent.com/ford_content/catalog/motorcraft/OBDSM407.pdf#page=66)
describes the crank-derived PIP timing reference and P0320 monitoring for missing
or noisy events. Historical P0320 makes this circuit worth prioritizing, but
neither that historical code nor this log identifies a failed CKP sensor.
Generic monitor thresholds are not verified UJAHAS3-specific specifications.

FRP voltage and wideband mixture are stable immediately before the first zero.
Pressure/charging voltage change after RPM collapses, which is consistent with
loss of manifold vacuum and alternator speed. This lowers the priority of a
pressure-collapse explanation; it does not exclude injector/combustion faults
or events shorter than the measurements can resolve.

A read-only post-stall diagnostic attempt displayed "No DTC's detected."
Completion freshness and pending-code coverage were not independently verified;
no fresh P0320 is confirmed and this is not a verified absence of pending faults.
No codes were cleared. A saved-log cursor reading is not evidence of a restart.

## Next intervention and decision criteria

1. Retain this capture. Use exact v021 as the comparison calibration after the
   owner performs and confirms the rollback. v021 is a reference, not a stall fix.
2. Owner plans a correct known-good upstream O2 sensor; installation is not yet
   confirmed. Record the exact part number and change only that hardware first.
   Keep the current regulator, MAF, injector data, idle gain and fan thresholds.
3. With the engine off and cool, inspect CKP connector security, harness damage
   or heat exposure, and engine/PCM ground connections. Do not assume a sensor
   replacement repairs its circuit. A qualified waveform check of CKP and PCM
   power during a hot stumble is more discriminating than another identical CSV.
4. On the next supervised stationary comparison, retain the 18 working channels,
   mark actual fan transitions, and save fresh confirmed/pending DTC results if
   a stumble occurs. Judge dip depth/duration and stalling, not O2 switching alone.
   Stop for another stall or progressively severe stumbling; no need to wait for
   a fan cycle. Do not drive to reproduce a stall.
5. If the correct O2 changes the symptom, compare hot matched windows before
   making fueling changes. If the abrupt zero-RPM pattern or fresh P0320 recurs,
   prioritize CKP circuit/waveform diagnosis before further idle tuning. Replace
   CKP only with supporting evidence or as a separately documented substitution.

This is a defined hardware A/B comparison followed by a signal test if needed,
not another unchanged baseline run. Water/meth remains off and the SCG RPM lead
remains disconnected. Numbered tune binaries remain unchanged.
