# v026 staged regression test

Candidate: [v026 Open Loop Fuel TPS Threshold Cleanup](../tunes/v026-open-loop-tps-threshold.md)
([v026-open-loop-tps-threshold.hpt](../tunes/v026-open-loop-tps-threshold.hpt)).
Exact parent and immediate rollback: [v025 MAF transfer convex smoothing](../tunes/v025-maf-idle-offidle-smooth.md)
([v025-maf-idle-offidle-smooth.hpt](../tunes/v025-maf-idle-offidle-smooth.hpt)), tested in
[2026-11-03-v025-test-review.md](../reports/2026-11-03-v025-test-review.md).

`v026` makes a single causal calibration change relative to `v025`: lifting
`ECM 32731` (`Open Loop Fuel TPS Thresh vs. RPM`) **Row 3 (`2,000 RPM`)** and
**Row 4 (`2,500 RPM`)** from `0.00` to `350.00` A/D counts. Water/methanol injection
remains **OFF**, the SCG-1 purple RPM wire remains disconnected, and high-flow
cells (`>= 1.100 V`) are untouched and **not boost-validated**. No ECU write,
recording, or engine action starts automatically from this card; see
[v026-run-card.json](v026-run-card.json) for machine-readable hashes and criteria.

---

## Preparation and owner pre-flash checks

1. **Owner pre-flash verification** (the agent never initiates an ECU write, readback, DTC clear, or adaptation reset):
   - Confirm vehicle ignition is KOEO with stable battery/charger supply (`>= 12.2 V`), accessories/loads OFF, and engine OFF.
   - Confirm VCM Scanner is disconnected before opening VCM Editor's write dialog.
   - Verify exact candidate file `tunes/v026-open-loop-tps-threshold.hpt` and write **Calibration Only**. Do not clear DTCs or reset KAM/adaptations independently of normal flash behavior.
2. **Paired logging setup**:
   - Reuse verified 18-channel profile [2004 Focus SVT - V023 Idle Spark Trial.Channels.xml](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml) and label the session **`v026-tps-threshold`**.
   - Start **both** VCM Scanner and SCG Logger while KOEO before cranking. Confirm all 18 VCM channels populate (`RPM`, `Desired Idle RPM`, `Throttle Position (SAE)`, `ECT`, `FRP (Raw)`, `O2 B1S1`, `STFT`, `Fuel Source`, `Closed Loop Active`, `Open Loop Conditions`, `Open Loop FMEM`, `MAF (lb/min)`, `MAF (V)`, `Spark`, `Spark Source`, `IAC`, `STIT`, `Control Module Voltage`) plus valid SCG-1 wideband lambda.

---

## Stage A — startup, warm idle & fan cycle check

1. **Cold or warm start**:
   - Start engine with untouched throttle and unchanged accessories (`A/C` and defrost OFF).
   - Verify `Open Loop FMEM` remains `No` continuously throughout warmup (preserving the fix validated in `v025`).
2. **Settled warm idle (`180–195°F`, `60–90 s` untouched in neutral, clutch up)**:
   - Confirm warm idle remains centered near `950 RPM` (`v025`: `952.31 RPM` mean, `SD 18.5 RPM`).
   - Confirm `STFT` remains within `±5%` and `SCG Lambda` stays `~1.00 ± 0.02`.
3. **Warm radiator fan cycle + `60 s` post-fan-off recovery**:
   - Confirm clean fan-on/off transition with normal recovery.

---

## Stage B — stationary off-idle holds (`1,500`, `2,000`, `2,500 RPM`) & return-to-idle

Proceed to Stage B once Stage A warm idle and fuel pressure (`FRP ~ 3.06 V`) are healthy.
While parked in neutral, smoothly press the accelerator to hold each target for **`15–20 seconds`**, releasing smoothly back to untouched idle for **`20–30 seconds`** between holds:

1. **Hold #1 — `1,500 RPM` (`TPS ~ 190–200` counts, `MAF_V ~ 0.82–0.86 V`)**:
   - **Expected mode**: **Closed Loop (`Fuel Source = Stoich`, `Closed Loop Active = Yes`)** via `ECM 32731 = 200.00` counts.
   - **What to check**: Settled `STFT` within `±5%`, `SCG Lambda` `~1.00 ± 0.02`, and clean return to idle.
2. **Hold #2 — `2,000 RPM` (`TPS ~ 195–210` counts, `MAF_V ~ 0.94–0.99 V`)**:
   - **Expected mode**: **Closed Loop (`Fuel Source = Stoich`, `Closed Loop Active = Yes`)** via new `ECM 32731 = 350.00` counts.
   - **Primary hypothesis check**: In `v025`, this hold prematurely forced `Power Demand Enrich` open-loop fueling (`0.76` lambda) because the threshold was `0.00`. In `v026`, because `TPS (~200)` is well below `350`, verify the engine **remains in Closed Loop Stoichiometry** (`Fuel Source = Stoich`, `Closed Loop Active = Yes`, `SCG Lambda ~ 1.00 ± 0.03`).
3. **Hold #3 — `2,500 RPM` (`TPS ~ 205–220` counts, `MAF_V ~ 1.05–1.15 V`)**:
   - **Expected mode**: **Closed Loop (`Fuel Source = Stoich`, `Closed Loop Active = Yes`)** via new `ECM 32731 = 350.00` counts.
   - **Primary hypothesis check**: Verify the engine **remains in Closed Loop Stoichiometry** rather than open-loop power enrichment. Evaluate settled `STFT` (`±8%` target) and verify clean return to idle without undershoot or RPM hang.

---

## Stop criteria, evaluation matrix & rollback

Stop the test immediately and let the engine return to idle (or shut down if rough/unsafe) if any of the following occur:
- Stall or near-stall (`< 650 RPM`), or worsening repeated warm-idle stumbles relative to `v025`.
- Steady warm `SCG Lambda > 1.08` for `> 3 seconds` at idle or during holds.
- Warm closed-loop `STFT` pinned positive (`> +18%`) or negative (`< -20%`).
- Fuel rail pressure sensor anomaly (`FRP` collapse or new `P0190`/`P0192`/`P0193` MIL) or any CKP sync fault (`P0320`). Preserve any DTCs for read-only inspection; do not clear codes.

| Check | Target / Pass Criterion | `v025` Reference (`2026-11-03`) |
| --- | --- | --- |
| 18-channel + SCG capture | 100% channel population + valid SCG wideband | 100% populated (`35,324` VCM / `10,480` SCG rows) |
| Mid-warmup CL (`120–165°F`) | `Open Loop FMEM = No` continuously; `STFT` within `±10%` | `0` FMEM events, continuous Closed Loop |
| Settled warm idle (`950 RPM`) | `SD <= 22 RPM`, `STFT` within `±5%`, no deep dips `< 820 RPM` | `952.31 ± 18.5 RPM`, `STFT = -1.8%`, `Lambda = 1.002` |
| `1,500 RPM` hold (`15–20 s`) | `Stoich` CL active, `STFT` within `±5%`, clean return | Closed Loop Stoich active, settled `STFT = -2.1%` |
| `2,000 RPM` hold (`15–20 s`) | **`Stoich` CL active** (`Closed Loop Active = Yes`), `Lambda ~ 1.00` | Premature Open Loop Power Demand Enrich (`Lambda = 0.763`) |
| `2,500 RPM` hold (`15–20 s`) | **`Stoich` CL active** (`Closed Loop Active = Yes`), `Lambda ~ 1.00` | Premature Open Loop Power Demand Enrich (`Lambda = 0.815`) |

**Immediate calibration rollback**: Flash exact [v025-maf-idle-offidle-smooth.hpt](../tunes/v025-maf-idle-offidle-smooth.hpt)
(`SHA-256: 2EFC9FFA0AC51A87E079F68F42AEBB06FECD60E91DC5651D15A805F92A715E17`).
End the test with **Stop both & export** and review the preserved session.

