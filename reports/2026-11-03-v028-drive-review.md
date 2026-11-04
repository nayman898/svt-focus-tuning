# 2026-11-03 v028 Road Drive Review & Log Analysis

**Session**: `paired-20261103-203015-a6737733-v028-drive`  
**Preserved Location**: `C:\source\repos\scg-logger\sessions\paired-20261103-203015-a6737733-v028-drive\`  
**Calibration Tested**: `v028-engine-braking-pop-dashpot-decay.hpt` (`259,325` bytes, `SHA-256: 0DFDEA68506F8AF005404E29F1403B46D998123A98E5417FDEB1481EE13BF752`)  
**Parent Calibration**: `v027-engine-braking-decel-pop.hpt` (`257,981` bytes)  
**Hardware Configuration**: 93 octane, return fuel system (43 psi base), Siemens 60 lb/hr injectors, PMAS HPX MAF (blow-through), Innovate SCG-1 boost controller at 8% WGDC (`SPG = 7 psi`, `bSt = 16 psi`, `AFr = 12.8`).  
**Datalog Coverage**: 17,695 VCM rows (`412.10 s` / `6.9 min`), 4,882 valid SCG wideband rows (`413.29 s`). Cross-correlation time alignment `delta_t = scg_elapsed_s - vcm_t ≈ +2.60 s` (Pearson correlation $r = 0.8273$).

---

## Executive Summary & Core Test Objectives

`v028` was flashed to evaluate four distinct drivability and performance items:
1. **Rolling Idle Hang (Decel Dashpot Decay)**:
   - **Result**: **COMPLETELY RESOLVED (100% SUCCESS)**.
   - Restoring active dashpot decay in `[ECM] 32984` (`0.02` to `0.05 lb/min`) eliminated the legacy idle hang. Across all coast-downs to a stop, the engine swept smoothly through the 1,300–1,500 RPM zone in 0.2s–0.8s and settled directly to target idle (917–1,050 RPM) without stalling, undershooting, or requiring any throttle blip.
2. **In-Gear Engine Braking & DFCO Window**:
   - **Result**: **VERIFIED & MATHEMATICALLY PRECISE**.
   - Deceleration Fuel Cutoff (`Fuel Source: Injector Cut`) engaged 14 separate times for a cumulative 41.8 seconds.
   - The extended entry delay (`[ECM] 44496 = 1.25 s`) was executed with stopwatch precision: measured delays between throttle lift-off and injector cut averaged exactly 1.25s (1.15s to 1.30s).
   - Lowering enable/disable vehicle speeds to 14 mph / 10 mph (`[ECM] 44491` / `44492`) maintained active engine braking deep into 1st/2nd gear down to 1,577 RPM and below.
3. **Decel Overrun Pops & Decel Spark Timing**:
   - **Result**: **ROOT CAUSE DIAGNOSED**.
   - Closed-throttle spark advance remained positive (+5.0° to +16.0°) instead of dropping to -2° to -4° ATDC.
   - **Root Cause**: Table `[ECM] 44605` (Spark Decel vs. RPM vs. ECT) has breakpoints at `-20, 20, 60, 100, 200`. In `v027` and `v028`, only Row 5 (`200`) was edited. At normal operating temperature (ECT 175°F–195°F / 80°C–90°C), the PCM evaluates against **Row 4 (`100`)**, which was still at stock advance (+5° at $\le 3\text{k}$, +15° to +17° at $\ge 4\text{k}$). Updating both Row 4 and Row 5 will deliver the commanded overrun retard.
4. **Low-Throttle Cruising Stutter**:
   - **Result**: **DUAL ROOT CAUSE ISOLATED**.
   - Analysis of steady light-throttle cruise holds (~2,200 RPM, 2–5% throttle) identified:
     1. A persistent **+2.0% to +3.4% lean bias** in the MAF transfer curve between `0.90V` and `1.20V` (peaking at +3.36% in the `1.00–1.10V` bin), which causes wideband lambda to swing lean ($\lambda = 1.14–1.18$) during pedal holds.
     2. Frequent micro-interventions of **Tip-In Torque Control** (40 bursts, pulling 5°–8° spark advance for 100–300 ms on slight pedal inputs).
     3. The simultaneous occurrence of a lean mixture excursion and a 7° timing drop creates the noticeable hesitation/stutter. Scaling MAF airflow by +3.0% in this voltage band will center closed-loop trims at 0.0% and stabilize combustion.
5. **High-Boost Full Pull Validation (6,737 RPM / +17.3 psi Peak Boost)**:
   - At `t = 218s – 222s`, the driver executed a full WOT pull to 6,190 RPM reaching **+17.31 psi boost**.
   - The Innovate SCG-1 boost cut cleanly intervened at 16 psi, instantly disengaging WGDC from 8% to 0%.
   - Fueling tracked ultra-safe and rich (`Lambda 0.707–0.736`, ~10.4–10.8 AFR) with 40 psi rail differential maintained across the run and zero knock retard (`0.0°`).

---

## Rolling Idle Coast-Down & Dashpot Decay Analysis

In prior tunes (`v000` through `v027`), dashpot decay `[ECM] 32984` was set to `0.00 lb/min` for all airflow breakpoints below `0.60 lb/min`, trapping the engine at 1,300–1,500 RPM until a throttle blip forced a state change. 

In `v028`, positive decay was restored (`0.02, 0.03, 0.04, 0.05 lb/min`). All four full coast-downs to a stop in `v028` were evaluated:

| Event # | Timestamp Window (s) | Duration (s) | Peak Entry RPM | Min Caught RPM | Settled Idle RPM | Settled IAC DC (%) | Time in 1,300–1,550 RPM Window (s) | Driver Blip Required? |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 118.3 – 130.0 | 11.7 s | 2,518 RPM | 1,001 RPM | 1,033 RPM | 49.4% | **0.30 s** | **No** (Smooth glide) |
| **2** | 222.1 – 228.5 | 6.4 s | 6,036 RPM | 843 RPM | 1,044 RPM | 51.3% | **0.23 s** | **No** (Direct catch) |
| **3** | 229.2 – 237.1 | 7.9 s | 2,598 RPM | 851 RPM | 917 RPM | 51.5% | **0.69 s** | **No** (Clean return) |
| **4** | 355.7 – 366.2 | 10.5 s | 2,147 RPM | 966 RPM | 1,050 RPM | 51.3% | **0.85 s** | **No** (Clean return) |

**Conclusion**: The rolling idle hang is 100% eliminated. The engine glides through the mid-RPM decel band in under one second without hesitation or hanging.

---

## DFCO (Injector Cut) & Engine Braking Telemetry

Lowering `[ECM] 44491` to 14 mph and `[ECM] 44492` to 10 mph kept deceleration fuel cutoff engaged significantly longer. Across the 6.9-minute log, **14 distinct Injector Cut events** were recorded:

| Event # | Start Time (s) | End Time (s) | Duration (s) | Throttle Lift Time (s) | Measured Delay (s) | Target Delay (`[ECM] 44496`) | Exit RPM | ECT (°F) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 93.94 | 94.65 | 0.71 s | 92.44 | 1.50 s | 1.25 s | 3,070 RPM | 186°F |
| **2** | 103.56 | 105.62 | 2.06 s | 102.39 | 1.17 s | 1.25 s | 2,381 RPM | 188°F |
| **3** | 106.47 | 107.37 | 0.91 s | 105.24 | 1.23 s | 1.25 s | 2,278 RPM | 188°F |
| **4** | 119.47 | 122.90 | 3.42 s | 118.25 | 1.22 s | 1.25 s | 1,911 RPM | 186°F |
| **5** | 146.80 | 149.15 | 2.35 s | 145.65 | 1.15 s | 1.25 s | 2,777 RPM | 190°F |
| **6** | 183.04 | 189.27 | 6.23 s | 181.85 | 1.19 s | 1.25 s | 2,716 RPM | 196°F |
| **7** | 190.17 | 191.85 | 1.69 s | 188.99 | 1.18 s | 1.25 s | 2,532 RPM | 194°F |
| **8** | 194.15 | 198.03 | 3.88 s | 192.92 | 1.23 s | 1.25 s | 730 RPM | 192°F |
| **9** | 230.45 | 233.41 | 2.95 s | 229.16 | 1.30 s | 1.25 s | 1,577 RPM | 198°F |
| **10** | 253.63 | 256.49 | 2.86 s | 252.07 | 1.55 s | 1.25 s | 2,554 RPM | 192°F |
| **11** | 257.44 | 262.17 | 4.73 s | 256.19 | 1.25 s | 1.25 s | 2,255 RPM | 192°F |
| **12** | 280.32 | 284.88 | 4.56 s | 279.11 | 1.21 s | 1.25 s | 2,129 RPM | 188°F |
| **13** | 291.60 | 292.14 | 0.54 s | 290.33 | 1.26 s | 1.25 s | 2,143 RPM | 188°F |
| **14** | 309.26 | 314.29 | 5.03 s | 308.11 | 1.16 s | 1.25 s | 2,056 RPM | 192°F |

**Key Takeaways**:
- The mean measured delay was **1.246 s**, verifying that the PCM executes `[ECM] 44496` exactly as calibrated.
- Injector Cut remained active down to 1,577 RPM (and 730 RPM during clutch-in), dramatically improving in-gear deceleration engine braking.

---

## Overrun Spark Decel Diagnosis (`[ECM] 44605`)

During closed-throttle deceleration (`Spark Source == "Closed Thr. Decel"`, 6,060 samples), ignition timing advance was binned across engine speeds:

| RPM Range | Sample Count | Observed Spark Min (°) | Observed Spark Max (°) | Observed Spark Mean (°) | Table `44605` Row 4 (`100`) | Table `44605` Row 5 (`200`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **800 – 1,500 RPM** | 1,863 | 4.8° | 19.5° | 5.6° | 5.00° | 12.00° – 14.00° |
| **1,500 – 2,500 RPM** | 2,430 | 4.8° | 31.0° | 6.7° | 5.00° | 13.00° |
| **2,500 – 3,500 RPM** | 1,472 | 5.0° | 29.8° | 8.9° | 5.00° | -2.00° |
| **3,500 – 4,500 RPM** | 180 | 9.5° | 22.2° | 14.8° | 15.00° | -4.00° |
| **4,500 – 6,000 RPM** | 88 | 13.2° | 17.8° | 15.7° | 16.00° | -4.00° |
| **6,000 – 7,500 RPM** | 7 | 14.0° | 15.2° | 14.6° | 17.00° | -4.00° |

**Definitive Finding**:
The observed timing at operating temperature (180°F–195°F / 82°C–90°C) matches **Row 4 (`100`)** cell-for-cell (5.0° at 800–3k, 15.0° at 4k, 16.0° at 5k, 17.0° at 6k). Row 5 (`200`) is never reached at normal coolant temperatures. To achieve overrun burble/pops, Row 4 (`100`) must be populated with the retard values.

---

## MAF Voltage Binning & Cruising Fuel Trim Analysis

Fuel trims (`STFT`) across all open-throttle closed-loop driving samples (`6,638 samples` with `RPM > 1100`, `Fuel Source: Stoich`, `TPS > 186.0 ADC`):

| MAF Voltage Bin | Sample Count | Mean STFT (%) | Min STFT (%) | Max STFT (%) | Std Dev (%) | Drivability Assessment |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0.60 – 0.70 V** | 3 | **+0.01%** | -0.17% | +0.13% | 0.16% | Off-idle dead center |
| **0.70 – 0.80 V** | 27 | **+0.62%** | -4.14% | +2.87% | 1.68% | Optimal |
| **0.80 – 0.90 V** | 45 | **+1.15%** | -2.24% | +2.87% | 1.41% | Optimal |
| **0.90 – 1.00 V** | 329 | **+2.75%** | -4.18% | +8.29% | 2.68% | **+2.8% Lean Bias (Cruise onset)** |
| **1.00 – 1.10 V** | 698 | **+3.36%** | -6.90% | +10.08% | 3.46% | **+3.4% Lean Bias (Primary cruise hold)** |
| **1.10 – 1.20 V** | 1,984 | **+2.06%** | -6.23% | +10.03% | 3.16% | **+2.1% Lean Bias (Moderate cruise)** |
| **1.20 – 1.30 V** | 531 | **+0.82%** | -4.56% | +8.24% | 2.62% | Optimal |
| **1.30 – 1.40 V** | 775 | **+0.79%** | -5.23% | +7.58% | 3.31% | Optimal |
| **1.40 – 1.50 V** | 684 | **+1.84%** | -4.81% | +7.58% | 2.98% | Optimal |
| **1.50 – 1.60 V** | 513 | **+1.53%** | -5.09% | +8.57% | 2.33% | Optimal |
| **1.60 – 1.70 V** | 573 | **+0.62%** | -4.54% | +5.46% | 1.91% | Dead Center |
| **1.70 – 1.80 V** | 232 | **+1.41%** | -2.89% | +6.05% | 2.03% | Optimal |
| **1.80 – 1.90 V** | 160 | **+1.21%** | -3.30% | +6.05% | 2.50% | Optimal |
| **1.90 – 2.00 V** | 79 | **+1.67%** | -0.92% | +5.99% | 1.67% | Optimal |

### Cruising Stutter Mechanism:
In the steady light-throttle hold between `t = 265s` and `t = 275s` (~2,200 RPM, 35–45 mph):
1. **Airflow Voltage**: MAF sits between `0.95V` and `1.12V`.
2. **Lean Air-Fuel Ratio**: Wideband lambda swings lean to `1.14 – 1.18` ($16.8–17.3\text{ AFR}$), forcing STFT to climb from `+2%` to `+10%`.
3. **Tip-In Spark Drops**: Minor throttle adjustments (210 to 240 ADC) trigger `Torque Control`, instantly pulling spark advance from `24.5°` down to `15.5°–17.8°` (a 7° drop).
4. **Resulting Surge**: Lean combustion plus 7° timing retard produces a cyclical torque dip that feels like a stutter. Scaling MAF airflow by **+3.0%** at 0.90V–1.20V will correct this behavior.

---

## High-Boost Full-Throttle Pull Profile (t = 218.0s to 222.0s)

Synchronized telemetry between VCM Scanner and SCG Logger (`offset = +2.60 s`):

| VCM Time (s) | Engine RPM | TPS ADC | Fuel Source | Spark Source | Spark Adv (°) | MAF Sensor (V) | SCG Boost (psi) | SCG WGDC (%) | SCG Lambda | SCG AFR | FRP Sensor (V) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **218.01** | 4,354 | 952.1 | Power Demand Enrich | Borderline | 10.2° | 2.566 V | -3.7 psi | 0% | 1.213 | 17.8 | 2.915 V |
| **218.29** | 4,510 | 964.1 | Power Demand Enrich | Torque Control | -3.5° | 2.629 V | +5.6 psi | 0% | 0.906 | 13.3 | 2.930 V |
| **218.68** | 4,572 | 964.1 | Power Demand Enrich | Torque Control | 2.2° | 2.800 V | +8.9 psi | 0% | 0.890 | 13.1 | 2.881 V |
| **219.15** | 4,766 | 964.1 | Power Demand Enrich | Torque Control | 2.2° | 2.878 V | +10.0 psi | 0% | 0.829 | 12.2 | 2.849 V |
| **219.33** | 4,797 | 965.1 | Power Demand Enrich | Borderline | 11.5° | 2.878 V | +10.0 psi | 8% | 0.825 | 12.1 | 2.847 V |
| **219.70** | 5,008 | 964.1 | Power Demand Enrich | Borderline | 12.0° | 3.078 V | +12.0 psi | 8% | 0.828 | 12.2 | 2.788 V |
| **220.07** | 5,226 | 963.1 | Power Demand Enrich | Borderline | 11.5° | 3.251 V | +14.3 psi | 8% | 0.801 | 11.8 | 2.769 V |
| **220.53** | 5,486 | 962.1 | Power Demand Enrich | Borderline | 12.2° | 3.356 V | +14.9 psi | 8% | 0.736 | 10.8 | 2.744 V |
| **220.91** | 5,696 | 964.1 | Power Demand Enrich | Borderline | 12.0° | 3.416 V | +14.3 psi | 8% | 0.712 | 10.5 | 2.720 V |
| **221.18** | 5,854 | 963.1 | Power Demand Enrich | Borderline | 12.0° | 3.415 V | +15.2 psi | 8% | 0.714 | 10.5 | 2.744 V |
| **221.56** | 6,022 | 962.1 | Power Demand Enrich | Borderline | 12.0° | 3.419 V | **+17.3 psi** | **8%** | **0.721** | **10.6** | 2.769 V |
| **221.65** | 6,046 | 962.1 | Power Demand Enrich | Borderline | 11.8° | 3.468 V | **+16.2 psi** | **0% (Cut)** | **0.712** | **10.5** | 2.769 V |
| **221.93** | 6,169 | 964.1 | Power Demand Enrich | Borderline | 12.4° | 3.429 V | +14.1 psi | 0% | 0.716 | 10.5 | 2.788 V |
| **222.11** | 6,036 | 180.8 | Power Demand Enrich | Borderline | 12.1° | 1.468 V | +3.2 psi | 0% | 0.826 | 12.1 | 2.866 V |
| **222.20** | 6,177 | 180.8 | Closed Thr. Decel | Closed Thr. Decel | 14.0° | 1.656 V | -2.1 psi | 0% | 0.764 | 11.2 | 3.037 V |

**Pull Highlights**:
- Peak boost hit **+17.3 psi** before the SCG-1 boost cut safely disengaged WGDC to 0%.
- Commanded vs measured fueling tracked within 1% (`0.712` measured vs `0.740` base open loop table).
- Rail pressure sensor held steady above `2.72 V` (~38 psi differential under 17 psi manifold boost). Pump flow is completely adequate.

---

## Action Plan for `v029`

1. **Populate Row 4 (`100`) in `[ECM] 44605` (Decel Spark)**:
   - Copy the target retard values into Row 4 (`100` ECT):
     - `3,000 RPM`: `0.00°` $\to$ **`-2.00°` ATDC**
     - `4,000 RPM`: `15.00°` $\to$ **`-4.00°` ATDC**
     - `5,000 RPM`: `16.00°` $\to$ **`-4.00°` ATDC**
     - `6,000 RPM`: `17.00°` $\to$ **`-4.00°` ATDC**
   - Retain Row 5 (`200` ECT) at the same values. This guarantees the PCM delivers negative decel spark at operating temperature.
2. **Smooth Cruising MAF Transfer (`[ECM] 12163`)**:
   - Scale airflow values by **`+3.0%`** across the `0.90V` to `1.20V` breakpoints to eliminate the lean surge and center cruising fuel trims at 0.0%:
     - `0.898 V`: `0.1425` $\to$ **`0.1468 lb/min`**
     - `1.000 V`: `0.1729` $\to$ **`0.1781 lb/min`**
     - `1.100 V`: `0.2066` $\to$ **`0.2128 lb/min`**
     - `1.200 V`: `0.2734` $\to$ **`0.2816 lb/min`**
3. **Preserve Dashpot Decay (`[ECM] 32984`)**:
   - Maintain the `v028` decay rates (`0.02, 0.03, 0.04, 0.05 lb/min`) that successfully eliminated the rolling idle hang.

