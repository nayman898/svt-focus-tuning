# v025 staged regression test

Candidate: [v025 MAF idle and off-idle smoothing](../tunes/v025-maf-idle-offidle-smooth.md)
([v025-maf-idle-offidle-smooth.hpt](../tunes/v025-maf-idle-offidle-smooth.hpt)).
Exact parent and immediate rollback: [v024 fuel cleanup and pressure diagnostics](../tunes/v024-fuel-cleanup-diagnostics.md)
([v024-fuel-cleanup-diagnostics.hpt](../tunes/v024-fuel-cleanup-diagnostics.hpt)), tested with the
new upstream O2 sensor in [2026-11-03-v024-cold-cleanup-review.md](../reports/2026-11-03-v024-cold-cleanup-review.md).

`v025` makes a single causal calibration change relative to `v024`: smoothing
`ECM12163` (`MAF Airflow vs. Voltage`) across **columns `6–13` (`0.500–1.000 V`)**
between untouched `0.479 V` and untouched `1.100 V`. Water/methanol injection
remains **OFF**, the SCG-1 purple RPM wire remains disconnected, and high-flow
cells (`>= 1.100 V`) are untouched and **not boost-validated**. No ECU write,
recording, or engine action starts automatically from this card; see
[v025-run-card.json](v025-run-card.json) for machine-readable hashes and criteria.

---

## Preparation and owner pre-flash checks

1. **Owner pre-flash verification** (the agent never initiates an ECU write, readback, DTC clear, or adaptation reset):
   - Confirm vehicle ignition is KOEO with stable battery/charger supply (`>= 12.2 V`), accessories/loads OFF, and engine OFF.
   - Confirm VCM Scanner is disconnected before opening VCM Editor's write dialog.
   - Verify exact candidate file `tunes/v025-maf-idle-offidle-smooth.hpt` and write **Calibration Only**. Do not clear DTCs or reset KAM/adaptations independently of normal flash behavior.
2. **Paired logging setup**:
   - Reuse verified 18-channel profile [2004 Focus SVT - V023 Idle Spark Trial.Channels.xml](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml) and label the session **`v025-maf-smooth`**.
   - Start **both** VCM Scanner and SCG Logger while KOEO before cranking. Confirm all 18 VCM channels populate (`RPM`, `Desired Idle RPM`, `Throttle Position (SAE)`, `ECT`, `FRP (Raw)`, `O2 B1S1`, `STFT`, `Fuel Source`, `Closed Loop Active`, `Open Loop Conditions`, `Open Loop FMEM`, `MAF (lb/min)`, `MAF (V)`, `Spark`, `Spark Source`, `IAC`, `STIT`, `Control Module Voltage`) plus valid SCG-1 wideband lambda.

---

## Stage A — startup, mid-warmup closed-loop retention, warm idle & fan cycle

1. **Cold or cool start (`ECT < 90°F` preferred)**:
   - Start with untouched throttle and unchanged accessories (`A/C` and defrost OFF).
   - **Primary warmup check (`115–165°F`, `1,100–1,350 RPM`, `MAF_V ~ 0.80–0.93 V`)**:
     In `v024`, `+24–26%` excess airflow in `ECM12163` (`0.699–0.898 V`) drove `STFT` to `-23.92%`, pinning the new narrowband O2 above `0.87 V` and tripping `Open Loop FMEM = Yes` from `177.5–390.0 s` (`128–162°F`, `SCG Lambda = 0.783`). With `v025`'s `-13.7%` to `-15.8%` reduction across `0.699–0.898 V`, verify `STFT` stays well within authority (expected `-5%` to `-10%`) and **`Open Loop FMEM` remains `No` continuously through warmup**.
   - *(If the first post-flash start is warm rather than cold, record the mid-warmup `FMEM` check as pending the next cold soak rather than passed.)*
2. **Settled warm idle (`180–195°F`, `60–90 s` untouched in neutral, clutch up)**:
   - `v025` replaces the `4.5x` slope discontinuity at `0.600 V` (`5.35` -> `24.64` -> `2.89 g/s/V`) with a continuous `10.17` -> `10.57 g/s/V` slope (`-2.74%` at `0.600 V`, `+5.13%` at `0.649 V`).
   - Evaluate warm `RPM` standard deviation (`v024`: `22.23 RPM`), sub-`900 RPM` group rate (`v024`: `11.66/min`), minimum RPM (`v024`: `816.5 RPM`), time outside `Desired ± 50 RPM` (`v024`: `3.8%`), `STFT` (`±5%` target), and `SCG Lambda` (`~1.00 ± 0.02`).
3. **Warm radiator fan cycle + full `60 s` post-fan-off recovery**:
   - Mark `fan_on` (`~196°F`) and `fan_off` (`~188°F`).
   - Retain **at least `60 seconds` of untouched idle after `fan_off`** before ending or touching the pedal (`v024` survived `fan_off` cleanly with `min 871.2 RPM`, `SD 18.13 RPM` during `fan_on`, but stopped `17.6 s` after `fan_off`).

---

## Stage B — stationary off-idle holds (`1,500`, `2,000`, `2,500 RPM`) & return-to-idle

Proceed to Stage B only if Stage A warm idle, fuel pressure (`FRP ~ 3.06 V`), and mixture are healthy. While parked in neutral, smoothly press the accelerator to hold each target for **`15–20 seconds`**, releasing smoothly back to untouched idle for **`20–30 seconds`** between holds:

1. **Hold #1 — `1,500 RPM` (`MAF_V ~ 0.82–0.86 V`)**:
   - **Expected mode**: **Closed Loop (`Fuel Source = Stoich`, `Closed Loop Active = Yes`)** via `ECM32731 = 200` counts at `0–1,500 RPM`.
   - **What to check**: Settled `STFT` (`v024` reached `-19.1%`, min `-21.91%`; `v025` predicts **`~ -1% to -5%`**, acceptable within `±8%`) and **return-to-idle mixture** (verifying removal of `v024`'s `1.260` lambda lean tip-out spike).
2. **Hold #2 — `2,000 RPM` (`MAF_V ~ 0.94–0.99 V`)**:
   - **Expected mode**: **Open Loop (`Fuel Source = Power Demand Enrich`, `Closed Loop Active = No`)** via `ECM32731 = 0.00` at `>= 2,000 RPM` (`Commanded Eq Ratio ~ 1.000` on `ECM44511` `15.625%` clamped first row).
   - **What to check**: `SCG Lambda` (`v024` ran overly rich at **`0.735`**; `v025`'s `-12.5%` reduction around `0.974 V` predicts **`~0.83–0.88`**, moving substantially toward stoichiometry without risking lean misfire while tying smoothly into untouched `1.100 V`).
3. **Hold #3 — `2,500 RPM` (`MAF_V ~ 1.05–1.15 V`)**:
   - **Expected mode**: **Open Loop (`Fuel Source = Power Demand Enrich`, `Closed Loop Active = No`)** directly on `v024`/`v025`'s cleaned-up `2,500 RPM` / `15.625%` `1.000` lambda cell (missed in `v024` Hold #2, which peaked at `2,212 RPM`).
   - **What to check**: Steady `SCG Lambda` across the `1.000 V` -> `1.100 V` tie-in (`~0.80–1.02`, **no steady excursion `> 1.05`**) and clean dashpot return to `950 RPM` without undershoot below `830 RPM` or hang.

---

## Stop criteria, evaluation matrix & rollback

Stop the test immediately and let the engine return to idle (or shut down if rough/unsafe) if any of the following occur:
- Stall or near-stall (`< 650 RPM`), or worsening repeated warm-idle stumbles relative to `v024` (`min 816.5 RPM`).
- Steady warm `SCG Lambda > 1.08` for `> 3 seconds` at idle/CL, or steady **`SCG Lambda > 1.05` for `> 3 seconds`** during `2,000–2,500 RPM` open-loop holds (excluding normal brief tip-out deceleration transients).
- Warm closed-loop `STFT` pinned positive (`> +18%`) or negative (`< -20%`).
- Fuel rail pressure sensor anomaly (`FRP` collapse or new `P0190`/`P0192`/`P0193` MIL) or any CKP sync fault (`P0320`). Preserve any DTCs for read-only inspection; do not clear codes.

| Check | Target / Pass Criterion | `v024` Reference (`2026-11-03`) |
| --- | --- | --- |
| 18-channel + SCG capture | 100% channel population + valid SCG wideband; clock offset derived | 100% populated (`38,438` VCM / `10,670` SCG rows) |
| Mid-warmup CL (`115–165°F`) | `Open Loop FMEM = No` continuously; fast-idle `STFT` within `±12%` | `STFT = -23.92%` -> tripped `FMEM = Yes` (`128–162°F`, `0.783` lambda) |
| Settled warm idle (`950 RPM`) | `SD <= 22 RPM`, `STFT` within `±5%`, no new deep dips `< 820 RPM` | `950.28 ± 22.23 RPM`, `min 816.5`, `11.66` sub-`900` groups/min, `STFT = -2.6%` |
| Fan ON & `60 s` post-fan OFF | Clean fan-on/off transition + full `60 s` post-fan-off recovery without stall | Fan-on `SD 18.13 RPM`; fan-off `min 871.2 RPM` (`17.6 s` captured) |
| `1,500 RPM` CL hold (`15–20 s`) | `Stoich` CL active, settled `STFT` within `±8%`, reduced tip-out lean spike | Settled `STFT = -19.1%` (`min -21.91%`), tip-out spike `1.260` lambda |
| `2,000 RPM` OL hold (`15–20 s`) | `Power Demand Enrich` OL, steady `SCG Lambda` `~0.82–0.95` (`<= 1.05`) | `SCG Lambda = 0.735` (`0.712–0.760` at `2,181 RPM`) |
| `2,500 RPM` OL hold (`15–20 s`) | `Power Demand Enrich` OL, steady `SCG Lambda` `~0.80–1.02` (`<= 1.05`), clean return | Untested (`v024` Hold #2 peaked at `2,212 RPM`) |

**Immediate calibration rollback**: Flash exact [v024-fuel-cleanup-diagnostics.hpt](../tunes/v024-fuel-cleanup-diagnostics.hpt)
(`SHA-256: 80EF77A8B1E4DE7E60D3754495A01CEF30C5AB707AD00F789DD520A647363E1E`)
retaining the same upstream O2 sensor and hardware state. End the test with
**Stop both & export** and review the preserved session before any moving road
test or `>= 1.100 V` MAF extension.
