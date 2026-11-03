# v013 initial stationary review

The owner confirms v013 installed. Both recordings are stopped, saved and
exported. No further calibration change or ECU write was performed.

**Later owner clarification:** engine stalled and recovered by itself, with no
starter input. The [deeper review](2026-10-29-v013-deep-review.md) supersedes
stumble-only interpretation below and includes the full earlier VCM interval.

## Coverage

- First pair `paired-20261029-175003-5d0f1b29-v013`: 11,341 VCM rows,
  approximately 183 seconds. STFT is entirely blank; coolant reaches only 170F.
  Minimum RPM after the initial start plus five seconds is 843.75. This is a
  startup observation, not a fully warm comparison.
- The owner restarted recording only, with the engine already running. The same
  Return Fuel Trial 13 profile then supplied all 13 fields. A late independent
  SCG recording was added without restarting VCM.
- Manual source `manual-v013-20261029-175707`: 8,899 VCM rows over
  1.091â€“178.811 seconds and 1,455 SCG rows. Preserved privately in
  `logs/2026-10-29-v013-warm-manual-01/`. SQLite integrity is `ok` and SCG is
  finalized. Native VCM and both CSV exports are present and nonempty.
- Metadata alignment is provisional: SCG elapsed = VCM elapsed -56.581945s.
  Wideband overlap begins at approximately VCM 57.30s. There is no wideband
  measurement for the earlier stumble. No drift validation or pressure video
  comparison has been completed for this run.

## Earlier stumble needs investigation

At VCM 42.504s, reported RPM is 835.5. At 42.525â€“42.585s it reports zero,
then 751.25 at 42.606s. Fuel Source changes to Cranking at 42.568s and Cold
Eng. / Startup at 42.626s; Spark Source briefly changes to Crank / Runup.
Closed Loop Active becomes No and returns to Yes at 69.404s.

The owner explicitly reports a stumble with **no starter use**. This is not an
owner-confirmed shutdown/restart. The exported zero-RPM interval is about 60ms
between its first and last zero rows; asynchronous/interpolated CSV rows do not
establish the true duration of a missing engine-speed signal. Reported voltage
is 13.75â€“13.625V at the zero interval, but that sampled channel cannot exclude a
brief electrical interruption.

The RPM discontinuity and accompanying cranking-state changes warrant checking
RPM acquisition, ECU run-state transitions and engine-speed signal integrity.
They do not prove a failed crank sensor, ECU reset, fuel-pressure failure or a
v013-caused regression. The engine was already unstable on v012. Review the
same pattern in prior native recordings before selecting a hardware diagnosis
or another calibration experiment. Do not tune around an unexplained zero-RPM
report or interpret subsequent startup fueling as normal settled closed loop.

## Later wideband overlap

Over approximately VCM 57.30â€“176.41s: mean RPM 898.77, minimum 745, maximum
1045.25; ECT 186â€“196F. All exported Spark Source rows are Idle Feedback.
Lambda mean is 1.0104, range 0.898â€“1.281. STFT averages -6.60%, range
-19.30 to -0.48%. These aggregate ranges include both startup-state and
closed-loop observations; they are not a fuel correction prescription or proof
of improved stability. The earlier zero-RPM episode is outside this overlap.

## Decision

v013 remains an experimental stationary trial, not an accepted stall fix or a
driving/boost calibration. Preserve both captures and investigate the stumble's
RPM/state sequence before preparing another tune. No additional gain, airflow,
MAF, injector or fuel-pressure change is justified by these aggregate results.
The owner may shut the engine down; no recording remains active.
