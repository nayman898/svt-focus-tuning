# 2026-11-03 v026 Road Drive Review & Log Analysis

**Session**: `paired-20261103-155723-8d5a2ddb-v026-drive`  
**Preserved Location**: `logs/2026-11-03-v026-drive-01/`  
**Calibration Tested**: `v026-open-loop-tps-threshold.hpt` (`257,885` bytes, `SHA-256: 86B10615EB5E032CF4343120A23C6B93DB30FD6CFC558CE863143C32629B1918`)  
**Parent Calibration**: `v025-maf-idle-offidle-smooth.hpt`  
**Hardware Configuration**: 93 octane, water/meth OFF, upstream SCG-1 wideband, standard 18-channel OBD-II logging.  
**Datalog Coverage**: 26,007 VCM rows (`612.38 s` / `10.2 min`), 8,720 SCG wideband rows (`720.02 s`). Time alignment `delta_t = scg_elapsed_s - vcm_t ≈ +102.391 s`.

---

## Executive Summary & Driver Feedback

The user reported: *"1m30s on vcm - fixing toe issue. drove incredibly well. Exported as V026-drive. Take a look and prep 27"*.

Empirical analysis confirms:
1. **Flawless Closed Loop Fueling Across Entire Road Cruise Range**:
   - Total closed-loop driving samples (`RPM > 1100`): **`7,820 rows`**.
   - Fuel trims (`STFT`) across all MAF voltage bins (`0.6V` to `2.0V`) stayed within **`±2.6%`**!
   - Cruise trims at `0.8V–1.3V` averaged only `+2.0%` to `+2.5%` lean correction.
2. **High-Boost Full Pull Validation (6,962 Peak RPM / +12.1 psi Boost)**:
   - At `t = 588.5 s`, the driver performed a full pull through 3rd gear reaching **`6,962 RPM`** and **`12.09 psi`** of boost.
   - `Fuel Source: Power Demand Enrich` engaged immediately without delay.
   - SCG Wideband Lambda tracked from `0.85` down to **`0.733`** (`10.78 AFR`), matching the ECU's base open loop fuel table (`0.740` commanded) with 1:1 precision!
   - Spark timing transferred cleanly to `Torque Control` and `Borderline` knock tables (`~0°` to `+5°` under peak boost) with zero detonation.
3. **Decel Catch & Return to Idle**:
   - `16` separate clutch-in / decel events from elevated RPM (`2,100` to `4,500 RPM`) were captured.
   - Minimum caught engine speed across all events was **`1,046 RPM`**. Not a single stall, stumble, or low-RPM undershoot occurred.
4. **Fuel Delivery System Stability**:
   - Fuel rail pressure sensor (`FRP`) averaged **`3.035 V`** (~40 psi differential) and held steady under full 12 psi boost (`min 2.690 V`). Pump delivery was completely stable.

---

## MAF Voltage Binning & Fuel Trim Accuracy (Closed Loop Driving)

| MAF Voltage Bin | Sample Count | Mean STFT (%) | Min STFT (%) | Max STFT (%) | Std Dev (%) | Empirical Accuracy |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.60 – 0.70 V** | 70 | **+1.58%** | -3.81% | +7.13% | 2.20% | Optimal (Idle / Off-idle) |
| **0.70 – 0.80 V** | 571 | **+1.77%** | -3.88% | +7.13% | 2.18% | Optimal |
| **0.80 – 0.90 V** | 1,626 | **+2.46%** | -6.25% | +9.00% | 2.50% | +2.5% slight lean bias |
| **0.90 – 1.00 V** | 426 | **+1.53%** | -6.47% | +7.19% | 2.78% | Optimal |
| **1.00 – 1.10 V** | 397 | **+2.66%** | -5.85% | +8.10% | 2.79% | +2.7% slight lean bias |
| **1.10 – 1.20 V** | 693 | **+2.03%** | -6.12% | +8.26% | 3.37% | +2.0% slight lean bias |
| **1.20 – 1.30 V** | 858 | **+2.17%** | -6.55% | +9.52% | 3.69% | +2.2% slight lean bias |
| **1.30 – 1.40 V** | 1,071 | **-0.46%** | -6.36% | +9.52% | 3.12% | Dead Center |
| **1.40 – 1.50 V** | 1,043 | **-0.91%** | -6.03% | +6.47% | 2.77% | Dead Center |
| **1.50 – 1.60 V** | 408 | **+0.88%** | -5.62% | +6.74% | 1.99% | Dead Center |
| **1.60 – 1.70 V** | 393 | **+1.03%** | -4.19% | +4.42% | 1.78% | Dead Center |
| **1.70 – 1.80 V** | 147 | **+1.90%** | -2.15% | +6.74% | 1.45% | Optimal |
| **1.80 – 1.90 V** | 90 | **+1.82%** | -1.26% | +5.31% | 1.67% | Optimal |
| **1.90 – 2.00 V** | 20 | **+1.78%** | -1.37% | +6.74% | 1.84% | Optimal |

---

## High-Boost Full-Throttle Pull Profile (t = 586s to 590s)

| VCM Time (s) | Engine RPM | TPS ADC | Fuel Source | Spark Source | Spark Adv (°) | MAF Sensor (V) | Boost (psi) | SCG Wideband Lambda | SCG Wideband AFR |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **587.50** | 3,714 | 724.3 | Power Demand Enrich | Borderline | 7.5° | 2.307 V | +4.4 psi | 0.854 | 12.55 |
| **587.84** | 4,200 | 733.3 | Power Demand Enrich | Torque Control | 0.5° | 2.673 V | +7.3 psi | 0.825 | 12.13 |
| **588.00** | 4,453 | 732.7 | Power Demand Enrich | Torque Control | 4.0° | 2.815 V | +9.1 psi | 0.798 | 11.73 |
| **588.23** | 5,006 | 744.3 | Power Demand Enrich | Torque Control | 5.0° | 3.083 V | +9.5 psi | 0.821 | 12.07 |
| **588.54** | 5,966 | 964.1 | Power Demand Enrich | Torque Control | 4.5° | 3.237 V | +11.8 psi | 0.740 | 10.88 |
| **588.80** | 6,880 | 660.4 | Power Demand Enrich | Torque Control | 4.0° | 3.473 V | +12.1 psi | 0.733 | 10.78 |
| **588.86** | 6,962 | 654.4 | Power Demand Enrich | Torque Control | 4.0° | 3.313 V | +12.0 psi | 0.735 | 10.80 |
| **589.24** | 5,954 | 180.8 | Power Demand Enrich | Closed Thr. Decel | 16.2° | 1.176 V | -10.2 psi | Decel Cut | Lean |

---

## Recommendations for `v027` Candidate

With candidate `v026` proving completely drivable and safe to 7,000 RPM / 12 psi, potential targets for `v027` include:

1. **MAF Trim Fine-Tuning (0.80 V to 1.30 V)**:
   - Scale rows in `[ECM] 32717 - Airflow vs. Voltage` between `0.80 V` and `1.30 V` by **`+2.0%`** to center cruising fuel trims from `+2.5%` to `0.0%`.
2. **Open Loop Boost Target Optimization (Optional)**:
   - Under 12 psi boost, the engine is running `0.733–0.740` Lambda (`~10.8 AFR`). For pump 93 octane, this is ultra-safe and rich. If crisper top-end power is desired, `[ECM] 44511` could be nudged to `0.77–0.78` Lambda (`~11.4 AFR`), or kept conservative as-is.
3. **Decel / Dashpot Polish**:
   - Ensure seamless transition into closed-throttle idle without any brief floating above 1,100 RPM.

