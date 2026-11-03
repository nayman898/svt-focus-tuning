# v024 — bounded fuel cleanup and pressure diagnostics

**Prepared and verified; not flashed, tested or adopted.** Exact parent and
rollback: [v021](v021-fuel-pressure-feedback.hpt), which remains the baseline.
The owner authorizes a few justified changes with staged regression logging.

Candidate: [v024-fuel-cleanup-diagnostics.hpt](v024-fuel-cleanup-diagnostics.hpt).
251,773 bytes; SHA-256:
`80EF77A8B1E4DE7E60D3754495A01CEF30C5AB707AD00F789DD520A647363E1E`.

| Parameter/location | v021 | v024 |
| --- | --- | --- |
| ECM44511, 2,500 RPM, TPS 15.625% | Lambda 1.0700000524520874 | 1.000 |
| ECM44511, 2,500 RPM, TPS 19.53125% | Lambda 1.1399999856948853 | 1.000 |
| ECM50, P0190 pressure circuit | No Error Reported | MIL Light |
| ECM50, P0192 pressure circuit low | No Error Reported | MIL Light |
| ECM50, P0193 pressure circuit high | No MIL Light | MIL Light |

The two fuel changes remove the strongest low-throttle lean pockets identified
in the [complete audit](../reports/2026-11-02-v021-complete-calibration-audit.md).
Lambda 1.00 is a chosen stoichiometric trial target, not a recovered factory value
or a proven optimum. At equal air mass and exact cell selection, these changes
request approximately 7%/14% more fuel respectively. Other corrections and table
selection can alter the actual command; no exact measured-mixture change is promised.
[HP Tuners identifies this table's output as lambda](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).

The effect interpolates between **1,000–3,500 RPM** and through the low TPS rows
up to the unchanged 23.4375% row; below the first TPS axis, endpoint handling
also matters. It is not confined to exactly 2,500 RPM. All other 78 body values
and axes are retained, including richer cells and the smaller remaining lean
values around 3,500 RPM. The TPS axis is percent; it is not the same number as
logged absolute TPS ADC or relative pedal opening.

Pressure reporting fits the restored sensor and variable transfer in v021.
Monitor enable conditions, pressure thresholds and fallback behavior remain
inherited. A newly visible code is evidence to investigate, not automatic proof
that v024 caused a physical fault or reason to suppress the code again. P0191
has no exposed row and was not invented. No fault injection is requested.

The retained controls include 950-RPM targets, 12-degree nominal idle spark,
gain 1.000, floor -6, base/runtime air, MAF, injector data, pressure conversion,
cranking fuel, O2 entry gates, cam/dashpot, fans and loaded spark protections.
The rejected v020/v022/v023 changes are absent. The 64 F cranking-fuel step
requires a defensible replacement curve; the first cold start with a new O2
sensor is not sufficient justification for guessing that curve.

## Verification completed

- Created through Editor Save As from exact v021; earlier numbered files preserved.
- Saved and reopened all 80 fuel body values at full precision: exactly two
  changed, the other 78 match the parent exactly.
- Axes were not edited; all displayed axes match the parent. Candidate Copy with
  Axis additionally confirms RPM and percent units and precise breakpoint values.
- All 163 DTC rows compared: exactly P0190/P0192/P0193 modes changed.
- Whole-file comparison lists only ECM44511, ECM50 and Notes.
- Saved Notes retain the complete v021 prefix plus the v024 appendix.
- All 24 older tune hashes and lengths still match their catalog identities.
- [Machine delta](../reports/calibration-inventory/v024/delta.json) and the
  [revision browser](../reports/calibration-inventory/index.html) include v024.

This verifies the saved candidate, not ECU installation or regression performance.
No agent ECU write, reset, code clear, engine action or new recording occurred.

## Regression test

Use the [v024 staged test card](../docs/v024-regression-test.md). First planned
start is **cold, with a new upstream O2 sensor and unchanged crank sensor**, per
the owner. Record the exact sensor part/install timing when available. Combining
that hardware change with v024 can establish observed behavior of the combination;
it cannot attribute an improvement solely to this tune.

The existing 18-channel profile retains fuel source, absolute TPS, raw FRP,
RPM/desired, O2/trim/loop/fallback state, spark, air correction and voltage; use
separate valid SCG wideband data. Stage A is cold start through fully warm idle.
Stage B is gentle stationary off-idle coverage only after Stage A is satisfactory.
If the changed fuel region or applicable fuel mode is not visited, label its
validation incomplete. Do not call an idle-only log a full regression pass.

Any adoption is provisional and limited to conditions actually covered. Hot
restart, moving return-to-idle and loaded/boost operation need their own coverage.
For a suspected calibration regression, exact v021 with the **same new O2 sensor**
is the cleaner comparison; do not simultaneously revert hardware and tune or
reset adaptations. Preserve any newly reported code evidence first.
