# v005 focused fuel-recovery recording

## Decision

Keep v005 as the existing stationary test calibration until the fan circuit
repair. The prepared v006 remains the next post-repair baseline, not a file
to install with the bypass still present. This capture improves the diagnosis
but does not justify a numerical MAF, injector, O2 gain/delay, startup-air or
idle-target edit. No calibration was edited or flashed in this session.

The most specific follow-up is to compare fan-load fuel-correction buildup
and fan-off recovery after repair. If the same behavior persists with healthy
supply and proper staging, investigate fuel characterization versus changing
load/voltage and feedback response before selecting a separate revision.

## Session and preservation

Owner reconfirmed v005, outdoors, neutral, parking brake applied and water/meth
off. Fuel was previously reported as 93 octane, not explicitly reconfirmed
this session. Owner reports successful first-attempt start. Fan ON was marked
at VCM elapsed **543 s (9:03)** and OFF at **570 s (9:30)**. These replace the
earlier ambiguous fan messages and initial mistaken LogWorks timebase.

Both native and CSV files are preserved under
`logs/2026-10-26-v005-fuel-recovery-01/`, with hashes/sizes, session context,
analysis and alignment JSON. Scanner contains 26,399 exported rows spanning
1.512-616.855 s. Exported rows can be interpolated/asynchronously sampled.
The last saved RPM is 1,104: shutdown was requested but is not in this log.
Scanner recording was stopped for saving; no vehicle Disconnect command was
issued. Its title still reported Connected during the follow-up check.

Loaded a private copy of the focused 27-channel profile with ECT interval
restored from 1 second to the prior 50 ms request. ECT returned, but the
interval change is not proven to be the cause. All key RPM, ECT, voltage,
actual spark, MAF, absolute TPS, O2, STFT and loop-state channels populate.
Relative TPS, IAT and O2 B1 Fail remain blank; blanks are not sensor diagnoses.

LogWorks export includes two sessions. Analyze Session 1 only: 5,612 samples,
0-459.65311 s. Session 2 is a separate later 119-sample/9.66656-second capture
and was excluded rather than merged into Session 1.

## Clock relationship

VCM Creation Time is 21:09:49 with timezone unstated. Two native LogWorks
Unix candidates (byte offsets 81467/87975) decode to 21:12:34 UTC. Under the
same-PC-clock interpretation, the provisional mapping is:

`LogWorks elapsed = VCM offset - 165 seconds`

Timestamp meanings, latency, drift and wideband transport delay remain
unvalidated. AFR values below describe windows under that candidate mapping;
they are not pointwise fuel errors. No earlier session offset was reused.
Fan event labels themselves are on the VCM timebase and do not need pairing.

## Fan-cycle results

| VCM window | Mean RPM | Mean STFT | Mean displayed AFR, provisional |
| --- | ---: | ---: | ---: |
| 510-540 s, before fan | 1099.6 | +1.32% | 14.81 |
| 543-570 s, fan on | 1098.2 | -4.06% | 14.05 |
| 570-580 s, first 10 s after off | 1101.6 | -10.97% | 15.42 |
| 580-600 s, 10-30 s after off | 1102.3 | -4.51% | 15.17 |
| 600-616.855 s, remaining recovery | 1100.6 | +0.38% | 14.95 |

Fan-on window contains **854.25 RPM minimum**, **1247.5 maximum**, and module
voltage **11.5625 V minimum**. Those are window extrema, not a claim of exact
simultaneous sampling. Mean RPM alone hides a substantial disturbance.

After fan-off, STFT reaches -13.94% in the first 10 seconds. The upstream O2
median in that interval is 0.142 V, while provisionally paired wideband AFR
peaks at 18.07. Correction subsequently returns toward zero. This supports
investigating load-dependent correction buildup and recovery; it does not
uniquely identify integrator windup, injector offset, MAF error, sensor bias,
transport delay or any optimal replacement calibration value.

Settled pre-fan and late-recovery trims are near zero. They do not support a
global fuel/MAF change to compensate for the transient. The fan repair will
change the load transition itself, so its new baseline is needed before
choosing a compensation change from this event.

## Commanded-mixture channel is not independent evidence

Across all **26,399 exported rows**, the reported commanded-mixture field
satisfies **commanded field = 1 - STFT/100**, with maximum absolute residual
approximately **5e-11** (CSV rounding). The earlier 929-row engine-off capture
has the same relationship.

This proves algebraic redundancy in these exported readings; it does not
prove the underlying PCM's internal equations or the optimal interpretation
of the generic channel label. A ramp in this field and a ramp in STFT are not
two independent observations. In particular, do not interpret the earlier
0.94-1.15 field range alone as evidence that a base lambda table is requesting
that lean/rich range. Prior fan-off reviews should be read with this finding.

## Startup and electrical follow-up

RPM first exceeds 500 at VCM 184.208 s; closed loop becomes active at 230.330 s,
about 46.1 seconds later. Initial 30-second startup window peaks at 2010.5 RPM.
This is not a temperature-matched improvement comparison against the prior
2915-RPM hot restart: current start coolant is roughly 148-154 F.

Reported cranking module voltage reaches **6.5625 V**. The first-attempt catch
is encouraging, but the repeat low module-voltage observation still needs
independent battery-post/underhood voltage-drop measurement. Do not diagnose
which battery/cable/starter component is responsible from Scanner alone.

The startup wideband includes a prolonged exact 7.35 display value. Treat
that as potentially saturated/invalid until SCG operating status is checked;
do not infer an accurate startup AFR or select cranking-fuel corrections from
that plateau. Session 2 also contains this value and is excluded.

## Next calibration boundary

v006 remains the verified post-repair high-stage restoration (225/215 F,
low-stage 195/190 unchanged). Keep the 1100-RPM idle and current fuel/spark
settings for that hardware baseline. This session supplies a useful comparison
for the repair: transient RPM/voltage minima, STFT buildup, measured-mixture
recovery and approximately near-zero settled trim.

If post-repair operation is repeatable and acceptable, the documented next
idle-target experiment remains 1000 RPM in a later numbered revision, followed
by staged reductions. Current evidence does not support combining that with
arbitrary base-airflow, O2 feedback or injector edits. Off-idle enrichment from
the 200-count TPS experiment still needs review before road/boost testing.
