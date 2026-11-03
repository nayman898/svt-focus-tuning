# v026 — Open Loop Fuel TPS Threshold Cleanup

**Prepared and verified; not flashed or tested.** Exact parent and
immediate rollback: [v025](v025-maf-idle-offidle-smooth.md), which was tested
in [2026-11-03-v025-test-review.md](../reports/2026-11-03-v025-test-review.md).

Candidate: [v026-open-loop-tps-threshold.hpt](v026-open-loop-tps-threshold.hpt).
257,885 bytes; SHA-256:
`86B10615EB5E032CF4343120A23C6B93DB30FD6CFC558CE863143C32629B1918`.

Parent: [v025-maf-idle-offidle-smooth.hpt](v025-maf-idle-offidle-smooth.hpt).
255,949 bytes; SHA-256:
`2EFC9FFA0AC51A87E079F68F42AEBB06FECD60E91DC5651D15A805F92A715E17`.

---

## Causal Scope & Calibration Table

`v026` modifies a single calibration table: `[ECM] 32731` (`Open Loop Fuel TPS Thresh vs. RPM`),
located at `Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Fuel TPS Thresh vs. RPM`.
Specifically, it lifts **Row 3 (`2,000 RPM`)** and **Row 4 (`2,500 RPM`)** from `0.00` to `350.00` A/D counts.
All 7 RPM breakpoints and the other 5 table rows are 100% bit-for-bit identical to parent `v025`.

| Row | RPM Breakpoint | v025 Threshold (counts) | v026 Threshold (counts) | Change | Approx. Throttle % | Rationale |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0 | 200.00 | 200.00 | Unchanged | ~19.5% | Retains warm closed-throttle idle closed-loop entry from v005 |
| 2 | 1,500 | 200.00 | 200.00 | Unchanged | ~19.5% | Retains closed-loop eligibility for 1,500 RPM hold and off-idle taper |
| 3 | 2,000 | 0.00 | 350.00 | +350.00 | ~34.2% | Prevents premature Open Loop Power Demand Enrichment during stationary hold / light cruise |
| 4 | 2,500 | 0.00 | 350.00 | +350.00 | ~34.2% | Preserves Closed Loop stoich under light load; enables clean closed-loop evaluation |
| 5 | 5,500 | 0.00 | 0.00 | Unchanged | 0.0% | Retains inherited high-RPM open-loop power enrichment |
| 6 | 6,500 | 0.00 | 0.00 | Unchanged | 0.0% | Retains inherited high-RPM open-loop power enrichment |
| 7 | 16,384 | 0.00 | 0.00 | Unchanged | 0.0% | High-RPM clamp unchanged |

Full-precision comparison is recorded in
[calibration-inventory/v026/delta.json](../reports/calibration-inventory/v026/delta.json).

---

## Empirical Justification

In the `v025` test ([2026-11-03-v025-test-review.md](../reports/2026-11-03-v025-test-review.md)),
the engine demonstrated outstanding improvements from the smoothed MAF transfer curve:
1. **Zero Open Loop FMEM events**: Mid-warmup (`120–165°F`) stayed 100% in Closed Loop without a single rich FMEM excursion (completely resolving the 212-second FMEM issue from `v024`).
2. **Centered warm idle**: Settled idle averaged `952.31 RPM` with normal fan recovery.
3. **1,500 RPM hold in Closed Loop**: Operating at `~195` counts TPS, the 1,500 RPM hold maintained `Fuel Source = Stoich` and active Closed Loop fuel trim correction.

However, during the **2,000 RPM** (`2,150–2,220 RPM`) and **2,500 RPM** (`2,480–2,550 RPM`) stationary holds:
- In `v025` (and prior tunes back to `v005`), `ECM 32731` set rows 3 and 4 (`2,000` and `2,500 RPM`) to `0.00` counts.
- Because the threshold was `0.00` counts, the moment engine speed exceeded `1,500 RPM` and interpolated past `~1,800 RPM`, ANY throttle input above closed-throttle idle exceeded the threshold, causing the ECU to force `Fuel Source = Power Demand Enrich` (`Open Loop Active = Yes`, `Closed Loop Active = No`).
- During neutral holds with pedal barely pressed (`~195–215` counts, `~19–21%` absolute throttle), the ECU commanded rich open-loop power enrichment (`0.76–0.82` lambda), preventing closed-loop fuel trim adaptation and wasting fuel during light stationary holds and light cruising.

`v026` resolves this by setting the 2,000 and 2,500 RPM thresholds to `350.00` counts (~34% absolute throttle). This:
- Allows stationary neutral holds at 2,000 and 2,500 RPM (`~195–215` counts) to remain comfortably in Closed Loop Stoichiometry.
- Preserves full power enrichment: any acceleration requiring throttle above `350` counts (or any engine speed above `5,500 RPM`) immediately enters Open Loop Power Demand Enrichment for full boost protection.

---

## Retained Scope & Unchanged Settings

All other engine controls and protections are strictly preserved:
- Rows 1, 2, 5, 6, and 7 of `ECM 32731` are untouched.
- `ECM 12163` MAF Airflow vs. Voltage retains all 30 points and breakpoints from `v025` (including the verified convex smoothed columns 6–13).
- High-flow cells (`>= 1.100 V`) are **not boost-validated**; water/meth remains **OFF**.
- Base fuel table `ECM 44511` retains `v024/v025` values.
- Idle speed targets (`950 RPM` in P/N and Drive) and idle spark controls (`ECM 47996 = 1.000` gain, floor `-6`, `12.0°` nominal spark) are retained.
- Fuel rail pressure sensor transfer `ECM 7596` and diagnostic trouble code reporting (`ECM 50` P0190, P0192, and P0193 `MIL Light`) are retained from `v024/v025`.
- Cam timing, dashpot, startup multipliers, and radiator fan thresholds (195/190°F low, 225/215°F high) are retained.

---

## Verification Completed

1. **Created via VCM Editor UI**: Built from exact parent `v025-maf-idle-offidle-smooth.hpt` via `File > Save As`, parameters edited in the UI, and saved through VCM Editor.
2. **Saved file properties**: Size `257,885` bytes, SHA-256 `86B10615EB5E032CF4343120A23C6B93DB30FD6CFC558CE863143C32629B1918`.
3. **Reopened table verification**: Saved file reopened fresh from disk. `[ECM] 32731` confirms all 7 RPM breakpoints match parent `v025`, rows 1, 2, 5, 6, and 7 match parent `v025` bit-for-bit (`200.00`, `200.00`, `0.00`, `0.00`, `0.00`), and rows 3 and 4 read exactly `350.00`.
4. **Reopened Notes verification**: Calibration Details Notes retain the complete `v025` parent history plus the `v026` rationale block. Zero VINs or serial numbers are present.
5. **Whole-file comparison**: VCM Editor `Compare > Open Compare File` against exact `v025-maf-idle-offidle-smooth.hpt` confirms that **ONLY** `Notes` and `[ECM] 32731 Open Loop Fuel TPS Thresh vs. RPM` differ across the entire calibration.
6. **Repository integrity**: All 26 prior cataloged tune binaries (`v000`–`v025`) match their documented byte counts and SHA-256 hashes.

---

## Pre-Flash Checklist & Staged Regression Test

> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The agent never initiates an ECU write, readback, DTC clear, or adaptation reset.

