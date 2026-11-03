# v006 - post-repair fan-stage baseline

**Prepared and verified for use after proper fan resistor/pigtail/wiring
restoration.** On 2026-10-27 the owner reported the resistor fixed and supplied
v006-labeled logs, with fan engagement observed at 195 F. The
[earlier post-repair review](../reports/2026-10-27-v006-post-repair-review.md)
finds improved fan-load response. The
[latest paired recording](../reports/2026-10-27-v006-paired-idle-review.md)
adds complete first fan-off recovery, with near-zero late trim and lambda 1.0.
Startup O2 feedback disagreement and a 7.56-V cranking module observation now
remain separate follow-up items. The owner subsequently confirmed this exact
v006 file installed. The [latest blower comparison](../reports/2026-10-27-v006-startup-blower-review.md)
supports preparing the separate [v007 target trial](v007-idle-1000.md); v006
remains its installed parent/rollback. Independent high-stage verification
remains pending. No ECU write was performed by the agent.

The preparation and saved-file verification below describe the original
pending-repair handoff. Embedded Notes retain that historical wording; the
numbered binary has not been rewritten to update test status.

Parent: [v005](v005-idle-absolute-tps-entry-test.hpt).
Candidate: [v006](v006-post-repair-fan-baseline.hpt).

## Purpose and exact difference

v003 deliberately moved the high-speed fan temperature path to the low-speed
thresholds while the resistor was bypassed. After repairing the low-speed
circuit, leaving that software request in place could still command high
speed at the normal low-speed temperature, obscuring the benefit of repair.
This candidate implements the previously documented retirement values while
preserving the later closed-loop entry work.

| Setting | v005 | v006 |
| --- | ---: | ---: |
| Fan High Speed Enable ECT | 195 F | **225 F** |
| Fan High Speed Disable ECT | 190 F | **215 F** |
| Fan Low Speed Enable ECT | 195 F | 195 F, unchanged |
| Fan Low Speed Disable ECT | 190 F | 190 F, unchanged |

The 225/215 values restore the earlier calibration documented in v002. They
are not a newly optimized turbo cooling recommendation or a claim that the
entire parent calibration is factory stock. Fan master enable, high-load and
vehicle-speed conditions remain unchanged.

Calibration Details Notes are appended, preserving v003/v004/v005 history and
stating that repair is pending and this candidate is conditional on repair.
All idle targets (nominal 1,100 RPM), startup air, ECT/IAT idle adders, spark,
injector/MAF/fuel/O2 settings and SCG-1 settings remain unchanged. The inherited
low-RPM 200-count TPS experiment remains stationary-only and unvalidated off
idle. The deferred startup-airflow change is not included.

## Saved-file verification

- Saved v006 was reopened directly and compared against v005 in Editor.
- Comparison lists **only Notes and the two named high-speed thresholds**.
- Reopened main-file values confirmed low 195/190 and high 225/215 F; remaining
  fan fields read the parent values.
- Saved Notes were reopened and checked for pending-repair status and inherited
  temporary-path history.
- An initial draft comparison showed only Notes: threshold edits had not
  committed. Main Fans-page controls were corrected and committed, the file
  was saved/reopened, and final comparison/readback repeated successfully.
- Earlier tune files remain catalog-hash/size verified and unmodified.
- Size: **220,541 bytes**.
- SHA-256: `E2640CBE5DEA20C644479699BF64A2F8CE53916FD4B05FBE17D26261C12EE988`.

## Post-repair test

Confirm proper resistor mounting/cooling, repaired terminals/wiring and actual
low/high-speed functionality using the appropriate service procedure. Do not
intentionally overheat the engine to force a temperature threshold. The
earlier fan-current, wiring/heat and cranking-voltage observations are not
declared solved by installing parts.

After hardware restoration, the owner can write this exact file with the
correct controller, stable write power and Editor's required ignition state.
Record repair details and flashed filename. Capture VCM and measured SCG-1
mixture through warm stationary idle and low-speed fan on/off, noting actual
fan events. Save HPL/LOG and all-channel CSV in a new v006 session directory;
derive that session's clock relationship.

Check that the intended lower-speed operation now occurs near the unchanged
low thresholds. Review RPM undershoot/overshoot, recovery, voltage, coolant,
idle-air command, actual spark/source, loop states and measured mixture.
Compare to v005 with the hardware change explicitly labeled; this is a repair
baseline, not a clean experiment isolating software alone.

If the resistor repair does not give the expected low-stage behavior, verify
actual commands, wiring/stage operation and motor/supply behavior before
concluding another RPM adder is needed. If running or measured mixture
deteriorates, stop the test and investigate. Parent v005 is the calibration
rollback, but it intentionally commands high speed at 195 F and reinstates
the temporary calibration path; it is not a normal post-repair stage baseline.

## ECT idle-adder contingency

An ECT-based RPM cushion can be evaluated later if the repaired fan system is
healthy and additional idle torque margin is needed. See the
[contingency analysis](../docs/fan-repair-and-idle-adder.md). It is not included
in v006. It does not repair fan current/supply behavior or establish a fix for
the fan-off fueling recovery problem. Keep the eventual 800-850 RPM goal as
the warm base target to evaluate in stages; any hot-temperature reserve is a
separate, explicit calibration choice.
