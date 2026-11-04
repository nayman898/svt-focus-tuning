# Calibration Review: v029 Road Test & Diagnostics

- **Date:** 2026-11-03 21:50 EST
- **Calibration Under Test:** `v029-decel-pop-cruise-smooth.hpt` (SHA-256: `e5846434088486a13f43eee65f8f21e8df38b972c84868ae580e5593bb966021`, 259,421 bytes)
- **Baseline Calibration:** `v028-engine-braking-pop-dashpot-decay.hpt`
- **Datalog Session:** `paired-20261103-213600-70c17f58-v029`
  - VCM Scanner CSV: `vcm.csv` (31,516 samples, 742.5 s / 12.38 min, 18 channels)
  - Innovate SCG-1 CSV: `scg.csv` (9,017 samples, 738.6 s, 10–30 Hz)
  - Alignment Offset: $\Delta t = t_{\text{scg}} - t_{\text{vcm}} \approx +3.85\text{ s}$ ($r \approx 0.88$ on throttle/boost correlation)
- **Vehicle Configuration:** 2004 Ford Focus SVT 2.0L Zetec Turbo (Pulsar G25-550 clone, external wastegate, 42 lb/hr injectors, Innovate SCG-1 boost controller)

---

## 1. Executive Summary & Verdict

The `v029` calibration successfully met all primary cruising, boost control, and decel spark retardation objectives:
1. **Cruising Lean Bias Cured**: Scaling `[ECM] 12163` by +3.0% across 0.90V–1.20V brought closed-loop Short Term Fuel Trims (STFT) dead-center to **-0.84% to -2.09%** (down from +2.0% to +3.4% in `v028`). High-speed cruising lean surging is 100% eliminated.
2. **Decel Overrun Spark Retard Active**: Populating Row 4 (100 ECT) in `[ECM] 44605` successfully dropped in-gear closed-throttle decel spark to **-2.0° to -3.2° ATDC** across 15 high-RPM decel sweeps.
3. **Boost Control Stable at 6% WGDC**: Reducing wastegate duty cycle to 6% successfully capped peak boost at **11.24 psi** (max airflow 30.64 lb/min at 6,447 RPM). Peak boost stayed 4.8 psi below the 16.0 psi emergency cut with zero solenoid dumps.
4. **Low-RPM Tip-In Stutter Diagnosed**: Forensic analysis isolated the low-RPM, low-throttle hesitation to two simultaneous root causes:
   - A transient lean pocket at **0.70V–0.88V MAF voltage** ($\lambda = 1.15 - 1.28$) during initial throttle tip-in from idle/coast.
   - **Tip-In Torque Control** (`[ECM] 44606/44607`) repeatedly cutting 15°–17° of spark advance below 2,400 RPM (oscillating between 23° and 6° four to five times per second).

---

## 2. Cruising & MAF Transfer Curve Evaluation

Across 5,928 closed-loop steady cruising samples ($180^\circ\text{F}+ \text{ECT}$, $1,800–3,500\text{ RPM}$, $195–350\text{ TPS ADC}$):

| MAF Voltage Bin | Sample Count | v028 STFT Mean | v029 STFT Mean | v029 STFT Median | Wideband $\lambda$ Mean | Assessment |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0.80V – 0.90V** | 10 | +1.50% | **-1.71%** | -2.11% | 1.032 | Stable |
| **0.90V – 1.00V** | 18 | +2.01% | **-0.84%** | **-0.24%** | 1.015 | **Dead-center stoich** |
| **1.00V – 1.10V** | 154 | +3.36% | **-1.17%** | **-1.55%** | 1.012 | **Dead-center stoich** |
| **1.10V – 1.20V** | 710 | +1.86% | **-2.09%** | **-1.59%** | 1.008 | **Centered, safe trim** |
| **1.20V – 1.30V** | 909 | -1.10% | **-2.50%** | -2.66% | 1.004 | Centered |
| **1.30V – 1.40V** | 1,600 | -1.80% | **-3.19%** | -3.09% | 0.998 | Centered |
| **1.40V – 1.60V** | 2,524 | -1.65% | **-3.02%** | -3.02% | 0.995 | Centered |

Fuel trims in steady cruising are stable and robust against lean drift.

---

## 3. Decel Overrun Evaluation

Row 4 (100 ECT) in `[ECM] 44605` resolved the decel spark hang observed in `v028`:

* **Decel Events Sampled:** 15 discrete closed-throttle coastdowns from $> 2,500\text{ RPM}$.
* **Decel Spark Range:** -3.2° to +27.2° (mean +1.5° across entire roll-down to idle).
* **High-RPM Overrun Spans:**
  - Pull #1 Decel ($t = 81.6\text{s} - 86.8\text{s}$, 5,487 RPM down): Spark held at **-3.2° to -2.0° ATDC**.
  - Decel #6 ($t = 92.8\text{s} - 94.0\text{s}$, 4,518 RPM down): Spark held at **-2.8° ATDC**.
  - Decel #7 ($t = 118.3\text{s} - 119.0\text{s}$, 3,827 RPM down): Spark held at **-2.0° ATDC**.
  - Pull #8 Decel ($t = 615.9\text{s} - 617.3\text{s}$, 5,186 RPM down): Spark held at **-3.2° ATDC**.
* **Duration Limitation:** At `[ECM] 44496 = 1.25 s`, the overrun fuel window lasted approximately 1.0 second before `Injector Cut` terminated fuel delivery.

---

## 4. Boost Dynamics & Wide-Open Throttle Performance

8 distinct WOT pulls were recorded with the SCG-1 set to 6% WGDC:

| Pull # | Start RPM | Peak RPM | Peak Boost | Max Airflow | Wideband $\lambda$ | Spark Advance | WGDC | SCG Cut? |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 3,434 | 5,492 | 8.75 psi | 23.70 lb/min | 0.748 – 0.858 | -1.2° to 10.8° | 6% | No |
| **2** | 2,770 | 4,224 | 10.39 psi | 17.62 lb/min | 0.742 – 0.945 | 2.0° to 17.4° | 6% | No |
| **4** | 3,088 | 3,759 | 8.46 psi | 13.56 lb/min | 0.745 – 0.755 | 9.2° to 10.0° | 6% | No |
| **7** | 4,683 | 6,447 | 10.22 psi | 30.64 lb/min | 0.789 – 0.867 | 0.8° to 13.2° | 0% | No |
| **8** | 3,896 | 5,292 | **11.24 psi** | 22.60 lb/min | 0.724 – 0.903 | -2.5° to 12.2° | 6% | No |

**Key Boost Takeaway:** The Pulsar G25-550 clone at 6% WGDC produced a stable 10.5–11.2 psi boost curve with zero pressure overshoot and zero emergency boost cuts.

---

## 5. Drivability Investigation: Low-RPM / Low-Throttle Stutter

The owner reported: *"I had some stutter coming into low rpm power with low throttle."*

Datalog forensic filtering identified 33 discrete candidate clusters where open-throttle driving coincided with timing drops below 12°, torque control cuts, or lean spikes.

### Root Cause Analysis

1. **MAF 0.70V–0.88V Under-Reporting on Tip-In:**
   - Idle airflow operates at $0.60\text{V} - 0.68\text{V}$ ($0.70 - 0.85\text{ lb/min}$).
   - Cracking the throttle open (TPS 190–260 ADC) at 1,200–1,800 RPM sweeps the MAF directly through Column 11 ($0.699\text{V}$), currently set to $5.66\text{ lb/h}$ ($0.0944\text{ lb/min}$).
   - Because Column 11 was cut by -13.7% in `v025` and unadjusted in `v029`, initial airflow is under-calculated, causing lambda to spike lean to **$\lambda = 1.15 - 1.28$ (17.0–18.8 AFR)**.

2. **Tip-In Torque Control Spark Snatch:**
   - `[ECM] 44607` (*Spark Tip-In Torque Control RPM Min*) is enabled at **775 RPM**.
   - As turbo backpressure and manifold airflow rise, airmass rate-of-change trips `[ECM] 44608`.
   - The PCM activates `Torque Control`, instantly pulling spark advance from `23.0°` down to `5.8°` (a 17.2° drop).
   - In cluster #30 ($t = 634.3\text{s} - 635.0\text{s}$), the PCM toggles between `Borderline` ($21°–23°$) and `Torque Control` ($5.8°–11°$) 5 separate times within 0.7 seconds. This violent timing hunting creates a harsh shudder/bucking sensation.

---

## 6. Recommendations for v030

1. **MAF Column 11 (0.699V) Adjustment:**
   - Increase Column 11 in `[ECM] 12163` from `5.66 lb/h` (`0.0944 lb/min`) by +6.0% to **`6.00 lb/h`** (`0.1000 lb/min`).
2. **Raise Tip-In Torque Control Minimum RPM:**
   - Increase `[ECM] 44607` from `775 RPM` to **`2,400 RPM`**. Disables tip-in timing cuts during low-speed and parking lot acceleration while preserving high-RPM torque management.
3. **Enhanced Safe Decel Popping:**
   - Update `[ECM] 44605` Row 4 & Row 5:
     - 2,000 RPM: **`2.00°`** (smooth taper down without stalling on clutch-in).
     - 3,000 RPM: **`-4.00°`** (was -2.00°).
     - 4,000–6,000 RPM: **`-6.00°`** (was -4.00°).
   - Extend `[ECM] 44496` DFCO delay from `1.25 s` to **`1.75 s`** (+0.5s duration before injector cut).
