# Idle follow-up and mechanical hold

Source: `paired-20261028-093440-0223fe51`. Preserved privately under
`logs/2026-10-28-stationary-02/`, including HPL, CSVs, manifest and a SQLite
backup made with the database backup API. Despite the archive label, this log
includes brief low-speed movement. No road test was requested after discovery
of the suspension failure.

## Decision

Hold the calibration; no v013 is justified from this recording alone. The
parked idle remains close to the earlier v012 result, with recurring short dips
and more exported Base/MBT rows. The center strut shaft failure now takes
priority: pause running/driving tests pending professional assessment and repair.
Do not attempt to restrain the damaged spring with improvised hardware or lift
the vehicle based on an ordinary intact-strut removal procedure.

v012 is carried forward from the last explicit owner confirmation, not
independently verified in the ECU for this run. All 13 cataloged tune files
passed hash/size verification during intake; none was modified.

## Capture quality

- Paired manifest reports saved, no export errors; SQLite integrity is OK and
  the writer finalized cleanly.
- VCM: 24,284 rows, elapsed 1.685–576.767 s. All 28 diagnostic channels contain
  data; the added STIT/LTIT/Idle Speed Source channels are absent. No actual
  active-profile snapshot accompanies this pair, so exact requested intervals
  cannot be confirmed from a candidate XML.
- VCM gaps: 41.259–41.823, 72.846–76.268 and 442.415–448.200 s. The last gap
  interrupts the parked comparison window; it is excluded from duration totals.
- SCG: 7,072 valid rows plus five gap, five disconnected and one stopped marker.
  Metadata gives provisional SCG elapsed = VCM elapsed +2.600 s. Drift and
  physical event synchronization are unverified; no pointwise fuel correction.
- Fractional RPM and other interpolated-looking values occur despite the paired
  manifest's export-interpolation flag being false. Neither row spacing nor
  that flag proves independent synchronous ECU samples.
- Early IAC, voltage and STFT are constant for extended periods. Preserve them
  as reported values; do not establish fresh sensor updates from filled cells.

## Parked comparison, 180–540 s in each recording

Both windows have ECT 182–186 F and zero reported vehicle speed. Accessory/load
history is not confirmed identical; this is a comparable temperature/time window,
not a controlled A/B experiment. Means and SDs below are export-row statistics.

| Measure | Earlier 08:41 run | New 09:34 run |
| --- | ---: | ---: |
| Mean RPM | 900.53 | 900.78 |
| Minimum RPM | 751.00 | 746.00 |
| RPM SD | 33.18 | 34.05 |
| Mean timing, degrees | 9.12 | 9.24 |
| Mean IAC duty, % | 34.57 | 36.14 |
| Mean module voltage | 13.76 | 13.65 |
| Mean STFT, % | -0.86 | -1.38 |
| Base/MBT export rows | 6 | 50 |
| Observed time >100 RPM below reported target | 0.329 s | 1.601 s |

Reported desired RPM is 896, consistent with the existing quantized channel,
not evidence of a new 896-RPM calibration. Duration estimates use the left
sample over adjacent intervals <=0.3 s; exclude longer gaps. Observed totals
are 356.970 and 354.176 s respectively. Neither window reports >200 RPM below
that target. Base/MBT row counts are not counts of independent events.

New parked SCG lambda mean 1.0123, range 0.939–1.182. Broad average near unity
does not resolve individual dip causality. Fuel-source/loop context and the
known command/STFT algebraic dependency still preclude blind fuel correction.

## Deepest parked dip: 5:05.896 VCM elapsed

The exported trace shows about 935 RPM at 304.902 s, 903 at 305.400, and 861
at 305.685 while Spark Source is Idle Feedback. At 305.896 it reaches
746 RPM with Base/MBT, 29.25 degrees, IAC 45.57%, and module voltage 13.50 V.
TPS remains closed, speed zero, CL Active/Ready Yes and Fuel Source Stoich.
At 306.086 it reports 809 RPM with Idle Feedback; at 306.390, 947.5 RPM.

The recorded decline precedes the Base/MBT label, and recovery follows shortly.
This is consistent with corrective intervention; asynchronous acquisition means
it does not settle whether the handoff also contributes to the oscillation.
Do not disable or reshape MBT on this evidence alone. Missing adaptation/mode
measurements still prevent a firm learned-airflow diagnosis. IAC duty and modest
voltage differences could reflect load differences rather than a tune change.

## Other periods

Early throttle inputs and fast-idle/source transitions are separate from the
parked window. At 158.572 s, RPM reaches 700.5 with reported speed 4.05 mph and
Cold Start Emissions Reduction spark source; this is a return-to-idle/movement
event, not the deepest settled-idle event. Maximum reported speed is 11.75 mph.
Movement recurs near the end. ECT reaches only 188 F; this is not a validated
195-F fan-on test. No direct fan command or owner event marker establishes a cycle.

## Next step

Mechanical repair first. Do not collect more running data while the damaged
spring retention is unresolved. Once repaired and cleared for operation, the
first measurement task remains stationary validation of the 31-channel profile,
then a comparable unchanged-tune idle capture with explicit accessory state.
The suspension finding can explain a mechanical clunk; this log does not show
that it caused the engine's parked RPM dips.

Private analysis files `analysis.json`, `followup-analysis.json`, and
`input-manifest.json` retain statistics, chronology, source hashes and analyzer
hash. The reusable private analyzer now accepts explicit source/destination and
calibration-evidence arguments; previous source defaults remain unchanged.
