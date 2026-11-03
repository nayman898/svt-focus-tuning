# v018 Stage2A: warm air/spark capture

Owner-started pair181640-1786acd8-v018-2A stopped/exported under the agreed bounded
test. Owner-confirmed v018, SBCSVT-SS-TZ single-mass kit and stockIAC. Native files
and SQLite API backup preserved in `logs/2026-10-30-v018-stage2a-01`; integrity,
finalization and catalog hashes passed. No ECU write or code clearing performed.

## Acquisition outcome

All20 requested fields populated across17,114VCM rows1.446–399.692s; no export
gaps. Saved-after-stop profile is retained beside the logs. RawMAF2302 and idle
mode12200 both populated, so this trial adds information absent from prior20.
STIT100ms/STFT100ms are request intervals, not a claim of measured ECU delivery
rates. The CSV contains repeated/interpolated values; row rate does not prove
100ms sensor freshness. Do not use it for precise subsecond causal phase estimates.

SCG metadata offset+2.282720s is provisional. During startup it recorded warmup,
sensor_error and one gap; only valid samples are used. Warm interval300s onward
has valid mixture data. Engine started around128F and first reached180F at290.589s;
most of the run was warming up. The final approximately100s is the warm comparison,
not399s of settled idle.

## Warm results, VCM300–399.692s

| Measurement | Result |
| --- | --- |
| Actual RPM |Mean950.64, minimum834.75, maximum1021, SD30.77 |
| Desired RPM |944 reported (nominal950 Editor target) |
| STIT |Mean−0.2013lb/min, range−0.2306 to−0.1680 |
| Raw MAF voltage |0.517–0.639V, mean0.584V |
| STFT |Mean−1.56%, range−5.79 to+1.39% |
| Wideband lambda |Mean1.010, range0.942–1.133 |
| Idle control mode |RPM Ctrl throughout |
| CL Active / Fuel Source |Yes / Stoich throughout |
| FMEM / O2B1Fail |No throughout |

No warm stall captured. Persistent dips remain. This stationary run does not
test the v018DFCO change or prove P0132 cleared; no post-run DTC read performed.

## What the added fields show

At375.874s: RPM983.25, IAC36.36%, rawMAF0.5609V, STIT−0.2004, STFT−0.247%.
At376.363s: RPM853.25, IAC41.43%, rawMAF0.6195V, STIT−0.1869, STFT−0.177%.
Spark increases7.25->18.5deg. RPM recovers to1012 by376.875s.

At338.342s: RPM979.75, IAC35.86%, rawMAF0.5941V. Before the dip, at338.847s,
IAC is35.34% and rawMAF0.5560V while RPM remains977.75. Air/spark corrections
then increase as the engine undershoots. These samples are compatible with the
air-command/flow/recovery sequence seen previously; asynchronous acquisition
prevents declaring the exact initiating edge.

The raw signal does not drop to zero and idle mode does not leaveRPMCtrl during
the warm dips. That weakens a simple complete MAF dropout or mode-exit explanation.
It does not exclude MAF dynamics, IAC hysteresis, unmetered air, cam/purge/combustion
disturbances, or a controller/actuator mismatch. The nearly unchanged fuel trim
during the376s event again means a new large trim command is not required for a
dip. STFT is not injectorPW, so fuel delivery remains incompletely measured.

STIT remains substantially negative, but this is not enough to subtract0.20lb/min
from base airflow. Total commanded idle-air components and adaptation semantics
are not all available. Commanded IAC duty is not measured valve position.

## Decision

Keep the 2A profile as a useful conditional warm diagnostic profile; it is not
validated for driving or actual100ms acquisition. Do not repeat an unchanged
warm run. The next work is offline verification of the low-load spark-limit
units/active path and availability of idle-air proportional/integral/overspeed
controls, plus IAC command-to-flow characterization if definitions are absent.
Current data selects that branch but not a defensible numerical gain value.
No v019 was created during this run.

Startup still contains the separate near-zero narrowband/positive-trim/rich
wideband event: CL entry91.117s, runtime86s,144F, narrowband0.001V;90–120s
wideband reaches0.672. Preserve that evidence, but do not let it replace the
warm-fluctuation investigation. No extra recording is requested now.

Detailed warm event samples: `.local/stage2a-dip-sequence.json` and script
`.local/stage2a-dip-sequence.py`. Minimum selection is the three deepest groups
below desired−75RPM after300s, separated by more than1s; this is selected-event
analysis, not proof that every dip shares a cause.
