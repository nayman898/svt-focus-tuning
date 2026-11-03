# v012 short drive and return-to-idle review

Session: `paired-20261029-161604-b543b769-v012`, about4.5minutes. Owner reports
mostly good driving with some instability, and confirms the early driveway
stall occurred **while starting from a stop**. This is not counted as a second
untouched-idle stall. The earlier spontaneous stationary stall remains valid
independent evidence; v010 also stalled occasionally per owner clarification.

Working file is owner-carried-forward v012900RPM/gain1.000, not a new ECU
readback. Regulator was owner-adjusted to43psi engine-off before the preceding
camera run. Actual pressure while driving is not measured in this log. Owner
reports suspension fixed. Meth remains OFF. No calibration or wiring changes
were made during this review.

## Decision

No gain rollback, MBT-table edit, base-air reduction or fuel correction selected
from this trip. The moving-off stall is a different condition from spontaneous
parked instability. Later parked dips occur with **Idle Feedback throughout**,
so MBT switching is not necessary for every stumble. Continue investigating the
initiating disturbance and air/load/fuel response separately from spark-source
arbitration. Average RPM near900 does not mean stability is resolved.

The short moving segments support the owner's mostly-good observation; they
do not establish sustained cruise, road readiness or boosted-fueling acceptance.

## Capture quality

- Both writers finalized/exported; SQLite integrity OK. Native HPL, SCG SQLite,
  CSVs, profile and owner context preserved in private `logs/2026-10-29-v012-drive-01/`.
- VCM11,641rows,1.602–274.525s; no export gaps above0.3s. Air Load HiRes, OL
  Conditions, Throttle State and CL Active/Ready/OL FMEM are entirely blank.
  No STIT/LTIT requests in this28-channel driving profile.
- SCG3,328rows:2,990valid,303warmup,17sensor_error,15oxygen,2gap,1stopped.
  Invalid states are excluded from mixture statistics/plots. Restart-related
  error/warmup spans are not engine AFR measurements.
- Provisional native-clock mapping: SCG elapsed = VCM elapsed +1.733s. Drift,
  exhaust delay and exact transport timing are unverified. Do not infer
  millisecond causality or pointwise fuel corrections from the paired plot.
- Brake Pedal reports No throughout; do not infer that no braking occurred.
  Trans In Gear is not a dedicated clutch measurement. Misfire Detected stays
  No and counts0; sensitivity is unvalidated, not proof of no combustion loss.
- All13 cataloged tune binaries matched size/SHA-256 during analysis.

## Timeline

| VCM elapsed | Observation | Interpretation |
| --- | --- | --- |
| 0:02–0:15 | RPM0, then engine starts | Separate pre-start/crank/runup from idle statistics |
| 1:10.918 | Brief648RPM dip near early low-speed activity; recovers | Context insufficient to call this an untouched parked event |
| 1:49–2:05 | Repeated moving-off/very-low-speed activity;435.75RPM at1:54.517, then zero at2:05.174 | Consistent with owner-reported moving-off stall; no dedicated clutch data |
| 2:05–2:08 | Zero RPM then restart | Do not compare restart/reset conditions to settled idle |
| 2:12–3:44 | Short moving segments, reported maximum35.03mph and4,974RPM | Includes tip-in/lift-off and torque intervention; not sustained cruise validation |
| 3:45–4:34 | Parked return-to-idle window | Recurring recovered dips, all exported Spark Source rows Idle Feedback |

At the moving-off stall, source reports Cold Start Emissions Reduction with
about2degrees timing, not Base/MBT. That label persists during hot-engine
post-restart driving too. It does not by itself identify the exact active
limiter or prove a faulty startup timer; treat launch torque reserve/hot-restart
control as a distinct future question rather than lumping it into parked hunting.

## Later parked idle:225–274.525s

| Measure | Result |
| --- | ---: |
| Mean/min/max RPM | 901.34 /708.5 /1133.75 |
| RPM SD, export-row statistic | 38.79 |
| Reported desired RPM | 896, consistent with prior quantization |
| Spark Source | Idle Feedback in all2,111rows |
| Mean timing | 2.98degrees |
| Mean/range IAC duty | 43.99%;33.80–52.51% |
| Mean/range module voltage | 13.38V;12.69–13.69V |
| ECT | 188–196F |
| Mean/range STFT | -5.73%;-9.73 to-0.80% |
| Valid wideband lambda mean/range | 0.9913;0.842–1.098 |

The2.98degree mean and higher air command differ from earlier warm stationary
windows, but temperature, restart/history, electrical load and regulator setting
are not matched. They do not prove excess base air or justify subtracting an
adaptive value from a table. Commanded-equivalence and STFT remain algebraically
linked; they are not independent command/error measurements. A near-unity
average lambda does not exclude brief combustion or fuel-delivery disturbances.

### Recovered dips

- **233.812s (3:53.8):708.5RPM**, Idle Feedback,13.75degrees, IAC51.00%,13.375V,
  TPS182.82counts, zero speed. Wideband swings across rich/lean around the event
  on provisional alignment; no isolated sustained lean precursor is established.
- **259.440s (4:19.4):754RPM**, Idle Feedback,11.25degrees, IAC52.32%,13.375V,
  TPS182.82counts, zero speed. Within about0.56s the export reports982RPM.

Near252–256s, a load-like transition occurs: mean voltage falls from about13.44V
in248–252s to13.20V, IAC rises from42.69% to45.75% and then47.58% in256–259s;
ECT reaches196F. This is **consistent with fan/electrical loading**, but no usable
fan command or owner marker confirms it. The later754RPM dip recovers without
an observed MBT handoff. Do not label the earlier unrelated188F stall a fan event.

## Mixture and boost limits

SCG error/warmup follows both starts: roughly16.35–28.77s and128.37–141.96s on
the provisional VCM clock, with preceding gap markers. The data does not prove
the exact electrical/sensor cause; check supply during starting if investigated.
An exported5.625V minimum appears during the first crank, not before a running
idle dip. Preserve it separately; no new diagnosis of the battery is made.

Reported pressure peaks7.44psi near175.53s with lambda0.832 at the nearest
SCG sample. Nearby RPM reaches4,974; the surrounding interval also includes
throttle closure/deceleration and source changes. Pressure scaling across its
range and dynamic fuel pressure are unvalidated; this is not a boost target or
acceptance of mixture/ignition safety. Very lean overrun/oxygen readings and
restart-invalid samples must not become steady-load fuel corrections.

## What to do next

1. Receive and review the **preceding stationary gauge video**, not assume it
   records this trip's pressure. Synchronize its gauge movement, sound and logs
   with stated uncertainty. Compare differential-pressure behavior, remembering
   the1:1 regulator follows manifold pressure; a stall-related pressure rise
   alone is not failure. Engine-off43psi is not dynamic validation.
2. For parked control onset, select Target Idle Air15 and verify actual
   STIT/LTIT/source plus core coverage before relying on it. Use driving28 only
   for motion/return-to-idle questions and audit its status fields. Never change
   profiles in an active recording.
3. Separate steady untouched idle from one clearly marked normal load transition
   in a later supervised stationary test, if needed after video review. Stop on
   severe deterioration; deliberate stall reproduction is not requested.
4. Prioritize IAC/air-path operation and electrical/load context alongside real
   fuel-pressure evidence. The recovered708RPM dip under Idle Feedback is a
   useful comparator to the prior stall, rather than justification to disable MBT.

## Plots

[Trip overview](2026-10-29-v012-drive-overview.png) and
[parked recovery detail](2026-10-29-v012-drive-idle.png). SCG alignment is
provisional; only valid nearby samples are plotted. Finite plot axes may clip
extremes; numerical evidence and original exports are authoritative. Plots show
reported signals, not a proof of control execution order.
