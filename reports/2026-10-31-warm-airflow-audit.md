# Warm idle airflow audit after v019

Decision: hold the v019 MAF curve. Audit the idle-air controller and actuator
response before choosing another calibration change. No v020 or ECU write.

Sources: exposed v017 inventory with verified v018/v019 deltas, latest
[warm review](2026-10-31-v019-warm-review.md), and
[HP Tuners Ford idle documentation](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm).
The idle-air settings below were inherited unchanged; the inventory is not ECU
readback. Calculations use displayed precision and linear interpolation.

## Temperature and runtime paths

- ECM44239/44242 Drive/P/N base-air tables are identical. Values at900/1000RPM
  are0.41/0.46, giving approximately0.432 at logged desired944RPM. These are
  nominal table values, not a measured total-air requirement or valve position.
- ECM44240/44243 runtime multipliers are identical. The final row is200s;
  its120F/200F values are1.15/1.00. At180F/184F the interpolated multiplier is
  1.0375/1.0300, a0.72% relative decrease. There is no180F breakpoint or step.
  At184F the nominal base-table contribution is~0.445; do not directly subtract
  measured STIT/LTIT from it without the complete summation/units convention.
- At184F the165s row is1.30 versus1.03 at200s, a20.8% reduction over35s.
  This is an actual warmup taper worth distinguishing from gradual temperature
  movement. The warm VCM export starts at runtime232s, after that taper.
  It cannot explain continued time-driven base-table decrease within the capture
  under the documented engine-runtime interpretation. It may have influenced
  the earlier approach to idle; that interval was not retained in VCM.
- ECM32955 RPM temperature adder is zero from162F through254F. Desired RPM
  remains944 in the warm capture: no evidence of a target step at180F.
- ECM44579 nominal P/N spark table is flat12degrees; actual spark uses idle
  feedback and is not fixed at12. ECM44414 VCT ECT multiplier is1.00 from90F
  onward, and VCT startup delay is2s from160F upward. Neither presents an180F
  enable step. Actual cam tracking remains unavailable, so this does not rule
  out temperature-sensitive hardware or cam-control behavior.

## Adaptation and actuator interpretation

Negative STIT/LTIT and declining mean IAC show the controller removing air in
its correction terms while average RPM stays close to target. They do not prove
that adding more base airflow will help: adaptation may remove the addition.
Nor do they justify subtracting all the correction from the base table, because
the complete air-demand sum, limits and calibrated component units are missing.
IAC duty is a command, not a measurement of valve opening. The log cannot
distinguish valve lag/stiction from controller dynamics by duty alone.

HP Tuners documents idle-air integrator times for underspeed and overspeed,
with smaller values giving faster corrections. No matching air-integrator
rate/limit entry appears in the complete342-entry exposed inventory. Current
ECM47996 gain1.000 controls spark, not the air integrator. ECM12002 coefficient
0.11 filters cylinder-airmass estimation, not an interchangeable IAC gain.
ECM44213/12262 enable/disable RPM errors200/30 are eligibility controls; generic
help is insufficient to reinterpret them as proportional gains or integrator
limits. Do not modify these as substitutes.

## MAF decision

Warm trim averages move toward zero as dips worsen. That is insufficient evidence
for another global or low-voltage MAF cut. Warm coverage is only about0.52–0.64V;
neither higher flow nor the entire v019-edited region is validated. Cold P1132/
FMEM remains a separate unresolved condition, not justification for changing all
high-flow cells. Hold the curve while resolving idle control. Later MAF edits
need repeatable steady-state bias by voltage/load with verified pressure and
injector behavior, not the troughs of an oscillating idle.

## Next discriminating work

1. Ask HP Tuners to identify UJAHAS3 idle-air integrator times/limits and the
   actual base/final IAC demand components. Local ticket addendum prepared;
   nothing submitted. Also request clarification of runtime255 saturation and
   ECT update behavior rather than treating either as a calibration threshold.
2. Verify the stock IAC's mechanical/electrical condition and command-to-air
   response using the applicable service procedure. This is an inspection/test
   target, not a recommendation to buy a valve or unplug it during a running test.
3. Once the relevant control is identified, use one bounded change in the
   overspeed-air response if its operation supports that hypothesis. No numerical
   rate is selected without the definition/current value. Keep MAF,950RPM,
   spark gain1 and all other terms fixed. Compare dip count/depth and recovery
   under matched temperature/accessory conditions; reject worse undershoot,
   stalling, or sustained high idle.

The next capture must retain the full VCM warmup interval if evaluating the
165–200s taper. A recording restart that discards that interval defeats that
question. An unchanged repeat of the existing warm-idle run adds little until
one of the above provides a new signal or controlled intervention.
