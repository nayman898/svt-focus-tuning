# v013 closed-loop follow-up

Source `paired-20261029-181853-592da567-v013-2`, user-entered label `v013-2`.
No separate tune revision or new flash was reported; installed calibration is
carried-forward owner-confirmed v013, not an ECU readback. Owner reports more
instability when closed-loop fueling takes over, with steadier earlier O2
voltage and larger voltage swings afterward. This observation is preserved
alongside the source session without modifying the app manifest.

Both recorders were confirmed active. The session was stopped/exported through
the matched dashboard; app status saved, no errors/missing files. Engine shutdown
was advised. Native files and SQLite API backup are preserved in private
`logs/2026-10-29-v013-idle-02/`; SQLite integrity/finalization passed and all14
cataloged tune hashes/sizes match. No tune, port, profile or setting was changed.

## Recorded behavior

All13 requested VCM fields populated in8,375 rows, VCM elapsed1.099–174.682s.
Closed Loop Active changes No to Yes at16.172s, at999.25RPM and174F. Fuel Source
changes startup to Stoich. Every exported Spark Source row is Idle Feedback:
that label is not the same state as closed-loop fueling.

In the initial1–15s, RPM averages1301, range1035–1430, and O2 averages0.060V,
range0.001–0.240V. This interval does not show a sustained0.5V plateau. It may
not be the exact moment of the owner's visual observation; no event-time mark
was supplied. Desired idle starts at1392RPM and later reaches896. Thus startup
and warm closed-loop idle are different target/temperature/air-control states,
not a controlled O2-feedback-only comparison.

| VCM interval | Mean/minimum RPM | Exported STFT mean | SCG lambda mean/range |
| --- | --- | --- | --- |
| 30–150s | 900.41 /826.75 | -6.12% | 1.0139 /0.973–1.090 |
| 157.329–174.682s | 897.03 /825.5 | -6.10% | 1.0142 /0.970–1.056 |

The recorded portions have mild dips, without the earlier run's545RPM collapse,
brief zero or cranking-state reentry. No stall appears in available VCM rows.
There is a **7.120s VCM data gap at150.209–157.329s**; do not claim continuous
VCM evidence or exclude an event in that gap. Owner report remains meaningful
even when minimum RPM is less severe than earlier.

## Timing and measurement limits

SCG covers elapsed0.742–198.095s, but valid readings do not cover all startup
time. Native metadata suggests SCG elapsed = VCM elapsed +24.631247s. The VCM
CSV creation stamp is22:19:18Z, approximately22s after the app's start-command
timestamp22:18:56Z. Their relation is unverified. Cross-device values in the
table are provisional; do not use them for subsecond transition causality or
pointwise fuel corrections. Do not silently substitute the command timestamp
for the native CSV origin. A common recorded timing mark is needed.

The full pre/post-entry wideband comparison is therefore limited by startup
validity and clock uncertainty. O2 switching after closed-loop entry is expected
for a switching sensor; this observation does not establish sensor health,
feedback tuning correctness or its contribution to felt roughness. Existing
trim/command linkage and P0320 uncertainty remain in the deeper review.

## Decision

No v014 or closed-loop-disable change selected. This recording shows a milder
outcome than the prior warm manual run but does not establish a cure or prove
that closed-loop fueling causes the stall. Next work is read-only verification
of trim/command definitions and applicable fuel-feedback settings, followed by
a targeted evidence plan if needed. Preserve pending P0320 and continue its
basic diagnostic checks alongside the fuel-feedback hypothesis. Do not extend
running merely to reproduce a stall.
