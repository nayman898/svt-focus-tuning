# Sensor-check recording review — 2026-10-30

Do not buy another O2 sensor solely on this recording. The completed warm run
shows a responsive upstream signal and near-stoichiometric average wideband
readings at idle. It neither proves a cold-start repair nor isolates the sensor
as the cause of the remaining dips. Installed sensor identity and other changes
are awaiting owner confirmation.

## Recordings distinguished

- `paired-20261030-154014-95b5a024-v015-sensor-check`: saved successfully;
  preserved in `logs/2026-10-30-v015-sensor-check-01`. Native files copied,
  SQLite backed up through its API, integrity/finalization checked, and catalog
  tune hashes verified. 10,882 VCM rows, 1.303–218.829 s, no export gaps.
- `paired-20261030-155435-2a07700a-v015-new-sensor-test`: partial; VCM start
  was rejected as not ready, and no VCM HPL/CSV was saved in that bundle.
  Its short SCG recording cannot establish ECU behavior.
- A separate read-only VCM screen snapshot during review displayed 913 RPM,
  194 F, CL Yes, O2 0.831 V, STFT −4.7%, runtime214 s. This is a displayed
  snapshot, not a saved time-series analysis or evidence of sensor response speed.
  No recording was stopped or restarted during this review.

## Complete warm recording

The run starts at172 F with the engine already running. Throttle/RPM vary greatly
in its first90 s; analyze the later idle separately. SCG pressure reaches about
9.1 psi earlier, and RPM reaches5551; those excursions are not stationary idle
evidence, and no power/boost calibration conclusion is drawn from them.

| VCM elapsed | RPM mean / minimum | Narrowband range | STFT mean | Wideband lambda mean |
| --- | --- | --- | --- | --- |
| 90–120 s | 899 / 838 | 0.000–0.836 V | −8.19% | 1.002 |
| 120–150 s | 899 / 778 | 0.000–0.843 V | −8.45% | 1.017 |
| 150–180 s | 900 / 760 | 0.000–0.762 V | −4.64% | 1.015 |
| 180–210 s | 901 / 837 | 0.103–0.853 V | −6.77% | 1.009 |

Repeated rich/lean crossings show the reported sensor is not stuck throughout
warm idle. O2 B1 Fail is populated as No throughout, but a constant status value
does not establish independent refresh or clear an earlier stored DTC.

Seven channels are entirely blank: Idle Desired RPM, Closed Loop Active,
LTIT PN/ACoff, Open Loop FMEM, Engine Run Time, Closed Loop Ready and Open Loop
Conditions. Their absence must not be interpreted as No/zero. Fuel Source is
Stoich in the analyzed idle interval and STFT varies, consistent with active
feedback, but CL/FMEm transitions cannot be verified from this CSV.

Wideband alignment is metadata-based: SCG elapsed = VCM elapsed +2.201786 s.
Transport delay and clock drift remain unvalidated. Window averages do not
establish event ordering at individual dips.

## Comparison and decision

The [previous P1132 run](2026-10-30-v015-p1132-review.md) already had responsive
narrowband switching once warm: at330–390 s, RPM averaged900–903, minima were
776–786, lambda means1.000–1.002, and STFT means−2.16 to−2.50%. The new warm
run therefore does not demonstrate a clear cure: dips still reach760 RPM and
the ECU removes more fuel on average. Temperatures and preceding throttle/load
history differ, so this is descriptive, not a controlled sensor comparison.

The earlier near-zero O2/rich-wideband cold-start period cannot be tested by a
recording that begins at172 F. A cold-soak comparison with populated state fields
is still needed to assess heater/readiness behavior. Avoid changing v015 or
regulator pressure simultaneously. If the spare15719 was used, observed warm
switching does not establish its application equivalence or heater compatibility.

No urgent NTK purchase is supported by these data alone. Confirm which saved
run contains which sensor, preserve/export any separate newer VCM recording,
then decide whether cold-response/heater testing actually calls for replacement.
