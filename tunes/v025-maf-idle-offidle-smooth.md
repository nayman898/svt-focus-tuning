# v025 — MAF transfer idle and off-idle convex smoothing

**Prepared and verified; not flashed or tested.** Exact parent and
immediate rollback: [v024](v024-fuel-cleanup-diagnostics.md), which was tested
with the new upstream O2 sensor in
[2026-11-03-v024-cold-cleanup-review.md](../reports/2026-11-03-v024-cold-cleanup-review.md).

Candidate: [v025-maf-idle-offidle-smooth.hpt](v025-maf-idle-offidle-smooth.hpt).
255,949 bytes; SHA-256:
`2EFC9FFA0AC51A87E079F68F42AEBB06FECD60E91DC5651D15A805F92A715E17`.

Parent: [v024-fuel-cleanup-diagnostics.hpt](v024-fuel-cleanup-diagnostics.hpt).
251,773 bytes; SHA-256:
`80EF77A8B1E4DE7E60D3754495A01CEF30C5AB707AD00F789DD520A647363E1E`.

---

## Causal Scope & Calibration Table

`v025` modifies a single calibration table: `[ECM] 12163` (`MAF Airflow vs. Voltage`),
specifically smoothing **columns `6–13` (`0.500–1.000 V`)** between untouched `0.479 V`
and untouched `1.100 V`. All 30 voltage breakpoints and all other 22 flow cells
are 100% bit-for-bit identical to parent `v024`.

| Col | Voltage (V) | v024 Editor lb/min | v025 Editor lb/min | Ratio | % Change | v024 g/s-eq (lb/h) | v025 g/s-eq (lb/h) | Rationale |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6 | 0.500 | 0.060691 | 0.061203 | 1.0084 | +0.84% | 3.641 | 3.672 | Smooth monotonic rise from untouched 0.479 V (3.515 lb/h) |
| 7 | 0.529 | 0.061141 | 0.065106 | 1.0648 | +6.48% | 3.668 | 3.906 | Eliminates severe flat shelf below 0.540 V |
| 8 | 0.540 | 0.061980 | 0.066669 | 1.0757 | +7.57% | 3.719 | 4.000 | Smooth convex curvature entering idle flow range |
| 9 | 0.600 | 0.078145 | 0.076000 | 0.9726 | -2.74% | 4.689 | 4.560 | Eliminates 4.5x slope discontinuity (was 24.64 g/s/V jump) |
| 10 | 0.649 | 0.080501 | 0.084629 | 1.0513 | +5.13% | 4.830 | 5.078 | Smooth monotonic bridge (10.57 g/s/V slope) across idle/fan recovery |
| 11 | 0.699 | 0.109306 | 0.094368 | 0.8633 | -13.67% | 6.558 | 5.662 | Reduces mid-warmup excess airflow (was driving STFT to -23.9%) |
| 12 | 0.898 | 0.169183 | 0.142484 | 0.8422 | -15.78% | 10.151 | 8.549 | Eliminates rich FMEM trigger during warmup and 1,500 RPM hold |
| 13 | 1.000 | 0.189289 | 0.172943 | 0.9136 | -8.64% | 11.357 | 10.377 | Corrects 2,000 RPM OL hold (was 0.735 lambda); ties into 1.100 V |

Full-precision requested vs reopened comparisons are recorded in
[2026-11-03-v025-maf-delta.csv](../reports/2026-11-03-v025-maf-delta.csv) and
[calibration-inventory/v025/delta.json](../reports/calibration-inventory/v025/delta.json).

---

## Empirical Justification

In the `v024` cold cleanup trial ([2026-11-03-v024-cold-cleanup-review.md](../reports/2026-11-03-v024-cold-cleanup-review.md)),
with the new upstream O2 sensor actively switching, the engine revealed three
closely related fueling and airflow symptoms attributable directly to `ECM12163`:

1. **Mid-warmup Open Loop FMEM trip (`128–162°F`, runtime `177.5–390.0 s`)**:
   At `1,100–1,350 RPM` fast idle (`MAF_V ~ 0.80–0.93 V`), `STFT` was forced down to
   `-23.92%`, pinning the new narrowband O2 above `0.87 V` and triggering
   `Open Loop FMEM = Yes` for `212.5 seconds` (`0.783` SCG lambda) before clearing
   when engine speed dropped into the warm idle region. The inherited MAF transfer
   at `0.699–0.898 V` overreported airflow by `+24%` to `+26%`.
   `v025` cuts columns 11 and 12 by `-13.7%` and `-15.8%`, predicting warmup `STFT`
   within `-5%` to `-10%` and preventing `FMEM` invocation.
2. **2,000 RPM stationary open-loop hold richness (`0.735` lambda)**:
   During the 2,181 RPM stationary hold, open-loop fueling (`Power Demand Enrich`,
   commanded lambda `1.000`) delivered an excessively rich `0.735` measured lambda
   at `0.974 V` average MAF. `v025`'s `-12.5%` interpolated reduction around `0.97 V`
   predicts `~0.83–0.88` lambda, moving toward stoichiometry without lean misfire risk.
3. **Severe slope discontinuity at warm idle (`0.600 V`)**:
   The `v019/v024` MAF table contained a severe local derivative artifact: the slope
   jumped from `5.35 g/s/V` (`0.540–0.600 V`) to `24.64 g/s/V` (`0.600–0.649 V`)
   and dropped abruptly to `2.89 g/s/V` (`0.649–0.699 V`) — a `4.5x` slope surge
   right at warm idle and radiator-fan recovery airflow (`0.58–0.64 V`).
   `v025` smooths this into a continuous, monotonically increasing slope
   (`10.17` -> `10.57 g/s/V`), stabilizing mass airflow calculations during idle
   and load transitions.

---

## Retained Scope & Unchanged Settings

All other engine controls and protections are strictly preserved:
- Columns 1–5 (`0.000–0.479 V`) and columns 14–30 (`1.100–4.800 V`) are untouched.
- High-flow cells (`>= 1.100 V`) are **not boost-validated**; water/meth remains **OFF**.
- Base fuel table `ECM44511` retains the two cleaned-up 2,500 RPM low-throttle cells (`1.000` lambda) and all other 78 cells from `v024`.
- Idle speed targets (`950 RPM` in P/N and Drive) and idle spark controls (`ECM47996 = 1.000` gain, floor `-6`, `12.0°` nominal spark) are retained.
- Fuel rail pressure sensor transfer `ECM7596` and diagnostic trouble code reporting (`ECM50` P0190, P0192, and P0193 `MIL Light`) are retained from `v024`.
- Cam timing, dashpot, startup multipliers, and radiator fan thresholds (195/190°F low, 225/215°F high) are retained.
- The rejected modifications from `v020` (base air cut), `v022` (spark gain cut), and `v023` (10° spark) are completely absent.

---

## Verification Completed

1. **Created via VCM Editor UI**: Built from exact parent `v024-fuel-cleanup-diagnostics.hpt` via `File > Save As`, parameters edited in the UI, and saved through VCM Editor.
2. **Saved file properties**: Size `255,949` bytes, SHA-256 `2EFC9FFA0AC51A87E079F68F42AEBB06FECD60E91DC5651D15A805F92A715E17`.
3. **Reopened table verification**: Saved file reopened fresh from disk. `Copy with Axis` confirms all 30 voltage breakpoints match parent `v024`, columns 1–5 and 14–30 match parent `v024` bit-for-bit, and columns 6–13 match the smoothing specification within `< 1e-6` in `lb/min` (Editor active display unit `lb/h`).
4. **Reopened Notes verification**: Calibration Details Notes retain the complete `v024` parent history plus the `v025` rationale block. Zero VINs or serial numbers are present.
5. **Whole-file comparison**: VCM Editor `Compare > Open Compare File` against exact `v024-fuel-cleanup-diagnostics.hpt` confirms that **ONLY** `Notes` and `[ECM] 12163 MAF Airflow vs. Voltage` differ across the entire calibration.
6. **Repository integrity**: All 25 prior cataloged tune binaries (`v000`–`v024`) match their documented byte counts and SHA-256 hashes.

---

## Pre-Flash Checklist & Staged Regression Test

> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The agent never initiates an ECU write, readback, DTC clear, or adaptation reset.

1. **Owner pre-flash checks**:
   - Ignition KOEO, battery/charger voltage `>= 12.2 V`, accessories/loads OFF.
   - Close VCM Scanner before opening VCM Editor's write dialog.
   - Select `tunes/v025-maf-idle-offidle-smooth.hpt` and write **Calibration Only**. Do not clear DTCs or reset adaptations.
2. **Paired logging profile**:
   - Reuse verified 18-channel profile `profiles/2004 Focus SVT - V023 Idle Spark Trial.Channels.xml` (`SHA-256: 683479070FEB9468239316F7F36036DEB6D40E6B6660A73EF2A0F1C3B99F7DCA`).
   - Pair with Innovate SCG-1 wideband logger; confirm all 18 channels populate.
3. **Staged execution**:
   - Follow [docs/v025-regression-test.md](../docs/v025-regression-test.md) and [docs/v025-run-card.json](../docs/v025-run-card.json).
   - **Stage A**: Cold/cool start, mid-warmup closed-loop retention check (`FMEM = No`), settled warm idle (`950 RPM`, 60–90 s), radiator fan cycle and **full 60 s post-fan-off recovery**.
   - **Stage B**: Parked off-idle holds at `1,500 RPM` (CL), `2,000 RPM` (OL), and `2,500 RPM` (OL) for 15–20 s each with 20–30 s idle returns.
4. **Immediate rollback**:
   - Flash exact [v024-fuel-cleanup-diagnostics.hpt](v024-fuel-cleanup-diagnostics.hpt) (`SHA-256: 80EF77A8B1E4DE7E60D3754495A01CEF30C5AB707AD00F789DD520A647363E1E`) retaining the same new upstream O2 sensor.
