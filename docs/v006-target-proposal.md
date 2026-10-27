# Deferred option: warm/hot-start airflow flare

**Deferred option; these startup-airflow edits are not implemented.**
v006 is now the separate
[post-repair fan-stage baseline](../tunes/v006-post-repair-fan-baseline.md),
prepared for use after the resistor/pigtail circuit repair. Any future startup
trial needs a later revision based on the accepted post-repair calibration.
The owner's clarified goal is 800-850 RPM fully warm idle. The
[lower-idle roadmap](lower-idle-roadmap.md) puts fan-off fuel/load recovery and
supply checks ahead of this startup-only experiment, followed by staged
target reductions beginning at 1,000 RPM. This document preserves the separate
startup proposal; it is not the selected warm-idle fix or a new tune revision.
The cell values discussed here were inspected in
[v005](../tunes/v005-idle-absolute-tps-entry-test.hpt), SHA-256
`D79A559CC0DC9A9DE8756FC7CA5F7AB89584627071A6A6E615E51AAE42FF6ED6`.

## Target and evidence

Reduce the warm/hot-start RPM flare with one small startup-airflow experiment.
The [startup recording](../reports/2026-10-26-v005-startup-review.md) shows
2,915 RPM against a 1,568-RPM target, approximately 71-74% idle-air duty after
the second catch, and a later elevated idle. Settled RPM in subsequent captures
is close to the nominal 1,100 setpoint, so a permanent idle-target change is
not the recommended first step.

Direct reinspection of v005 confirms **ECM 44243, Idle Airflow Mult (P/N) vs.
ECT vs. ERT**. Table headers visually identify ECT in Fahrenheit across columns
and engine run time in seconds down rows. Official
[HP Tuners idle documentation](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)
describes this as the P/N idle-airflow multiplier versus ECT/runtime. The
documentation establishes the parameter's purpose, not an optimal value for
this modified engine.

## Exact proposed change

Copy the existing 30-second value at 200 F into that column at 2 s:

| ERT row | ECT column | v005 | Proposed v006 | Initial change |
| ---: | ---: | ---: | ---: | ---: |
| 2 s | 200 F | 1.60 | **1.50** | -6.25% |

The 210 F cell remains unchanged at 1.40. It is not needed to influence the
logged 186-196 F range, so the proposal has been narrowed to one cell.

This is a deliberately small diagnostic change using values already present
in the next runtime row, not a claim that the 30-second values are optimal
at initial catch. Do not scale the entire table or combine this with dashpot,
idle target, spark, injector, MAF or closed-loop feedback changes.

The effect interpolates across the first approximately 30 seconds and the
temperature region between the unchanged 120 F and 210 F columns. It is **not
limited to reaching 200 F or an engine-state-only code gate**. At the recorded
188 F and 2 s, linear table interpolation would change approximately 1.630
to 1.545, about a 5.2% reduction in this multiplier; that does not predict
the same percentage change in actual valve duty, airflow or peak RPM.
At logged 186-196 F and 2 s, the proposed multiplier reduction is approximately
5.0-5.9%; the engine does not need to reach 200 F for this cell to contribute.
Later runtime rows, including the 30-second row, remain unchanged. This proposal
does not change the sustained fan-off event after the startup period.

Retain 1,100-RPM nominal idle targets, the v005 low-RPM 200-count TPS thresholds,
all fuel/spark/O2 settings, LTFT state and the temporary fan pathway. Preserve
the existing stationary-only/no-throttle/no-boost scope and fan-circuit repair
and retirement requirements. Use v005 as rollback for this experiment.

## Conditions before testing

The same startup trace also shows a failed initial catch and reported supply
voltage down to 7 V. **Confirm cranking supply voltage independently before
testing a startup-air reduction.** If the low supply is confirmed, address it
first. A startup-air change cannot repair an electrical supply collapse and
could worsen the marginal first catch. There is no measured AFR trace for
that original startup, so its mixture cannot be diagnosed retrospectively.

A future built candidate must be saved separately, reopened, compared against
its accepted parent and checked for exactly this one cell plus explanatory Notes. Verify
all inherited settings, record its hash/size and preserve every prior binary.
This proposal is not a flash-ready calibration or authorization to write ECU.

## Test and acceptance

Record both Scanner and LogWorks **before key-on/cranking**, with matched warm
coolant, fuel/water-meth state and accessory conditions. Keep stationary and
throttle untouched. Capture successful first catch, RPM peak, time to settle,
idle-air command, actual spark/source, voltage, measured AFR and loop states.
Repeat under comparable conditions before accepting an apparent improvement.

The desired result is a smaller startup overshoot and shorter settling time
with reliable starting and no worse mixture/underspeed behavior. A lower peak
accompanied by a worse catch or stall is a failed test. Stop if starting or
operation deteriorates and return to v005 under proper write conditions.

## Separate fan-off priority

The [owner-marked fan-off recording](../reports/2026-10-26-v005-fan-off-review.md)
shows a sustained measured mixture excursion while CL remains active. That
is the main remaining running-idle investigation. It does not yet establish
which fuel correction, airflow model, O2 feedback setting or sensor behavior
causes the excursion. No numerical MAF, injector, spark-gain or O2-delay change
is supported merely by the average AFR or the apparent command ramp.

Use the prepared
[focused fuel-recovery channels](../profiles/2004%20Focus%20SVT%20-%20Idle%20Fuel%20Recovery.Channels.xml)
to obtain O2 voltage, B1 STFT and MAF with the working commanded-mixture/spark
channels through a labeled fan cycle. Verify saved data and channel semantics
before choosing that separate calibration experiment. Do not bundle an
unverified fan-off fueling change into the startup-air trial.
