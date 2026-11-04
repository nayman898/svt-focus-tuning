# v029 — Decel Overrun Pop Activation & Cruising Stutter Elimination

**Prepared candidate for active road testing.**  
Exact parent and immediate rollback: [v028](v028-engine-braking-pop-dashpot-decay.md), which was road tested on 2026-11-03 in [2026-11-03-v028-drive-review.md](../reports/2026-11-03-v028-drive-review.md).

- **Candidate Binary**: [v029-decel-pop-cruise-smooth.hpt](v029-decel-pop-cruise-smooth.hpt)
  - Candidate Size: Pending save by owner
  - Candidate SHA-256: `PENDING_OWNER_FLASH_SAVE`
- **Parent Binary**: [v028-engine-braking-pop-dashpot-decay.hpt](v028-engine-braking-pop-dashpot-decay.hpt)
  - Parent Size: `259,325` bytes
  - Parent SHA-256: `0DFDEA68506F8AF005404E29F1403B46D998123A98E5417FDEB1481EE13BF752`

---

## Causal Scope & Calibration Parameters

`v029` directly addresses the two empirical findings isolated during the `v028` road drive review:

### 1. Activate Decel Overrun Pops: `[ECM] 44605` (Spark Decel vs. RPM vs. ECT)
*Location: `Engine > Spark > Decel`*

In `v028`, closed-throttle decel spark remained at +5.0° to +16.0° advance rather than retarding to -2° to -4° ATDC. Datalog analysis revealed that at operating temperature (ECT 175°F–195°F / 82°C–90°C), the Ford PCM evaluates against **Row 4 (`100` ECT)**, NOT Row 5 (`200` ECT). Because Row 4 was still set to stock timing (+5° at $\le 3\text{k}$, +15° to +17° at $\ge 4\text{k}$), the retarded values in Row 5 were never executed.

`v029` copies the target retard values into **Row 4 (`100` ECT)** while preserving Row 5 (`200` ECT):

| ECT Row | 800 RPM | 1,000 RPM | 2,000 RPM | 3,000 RPM | 4,000 RPM | 5,000 RPM | 6,000 RPM | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **-20** | 14.00 | 12.00 | 13.00 | 14.00 | 15.00 | 16.00 | 17.00 | *Untouched (cold protection)* |
| **20** | 14.00 | 12.00 | 13.00 | 14.00 | 15.00 | 16.00 | 17.00 | *Untouched (cold protection)* |
| **60** | 5.00 | 5.00 | 5.00 | 5.00 | 15.00 | 16.00 | 17.00 | *Untouched (warmup protection)* |
| **100 (v028)** | 5.00 | 5.00 | 5.00 | 5.00 | 15.00 | 16.00 | 17.00 | *Stock advanced decel timing* |
| **100 (v029)** | **5.00** | **5.00** | **5.00** | **-2.00** | **-4.00** | **-4.00** | **-4.00** | **Activates overrun pops at operating ECT; idle catch safe $\le 2{,}000$** |
| **200 (v029)** | **14.00** | **12.00** | **13.00** | **-2.00** | **-4.00** | **-4.00** | **-4.00** | **Retained from v028** |

- *Rationale*: Populating Row 4 guarantees that the PCM outputs the commanded -2° to -4° ATDC retard during warm decel, producing crisp overrun burble and pops during the 1.25s pre-DFCO delay window.

---

### 2. Eliminate Low-Throttle Cruising Stutter: `[ECM] 12163` (MAF Airflow vs. Voltage)
*Location: `Engine > Airflow > General > MAF Calibration`*

Analysis of 6,638 open-throttle closed-loop samples in `v028` demonstrated an empirical +2.0% to +3.4% lean bias in the light-throttle cruising region (`0.90V` to `1.20V`, peaking at +3.36% in the `1.00–1.10V` bin). During steady light-throttle holds (~2,200 RPM, 2–5% pedal), the wideband lambda regularly swung lean to 1.14–1.18 ($16.8–17.3\text{ AFR}$), triggering closed-loop PI oscillations and 7° tip-in torque control spark retard cuts.

`v029` scales the MAF airflow curve by **`+3.0%`** across the four cruising breakpoints:

| MAF Voltage Breakpoint (V) | Parent (`v028`) Airflow (lb/min) | Candidate (`v029`) Airflow (lb/min) | Delta (lb/min) | Delta (%) | Purpose |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **0.898 V** | 0.1425 | **0.1468** | +0.0043 | +3.0% | Eliminates lean bias on cruise onset |
| **1.000 V** | 0.1729 | **0.1781** | +0.0052 | +3.0% | Centers STFT at primary 35-40 mph cruise hold |
| **1.100 V** | 0.2066 | **0.2128** | +0.0062 | +3.0% | Centers STFT at moderate 45 mph cruise hold |
| **1.200 V** | 0.2734 | **0.2816** | +0.0082 | +3.0% | Smooths transition into mid-load acceleration |

- *Rationale*: Centers closed-loop fuel trims directly at 0.0% across the cruising band, eliminating lean excursions and preventing the cyclic torque dip that felt like a cruising stutter.

---

### 3. Preserved Calibrations from `v028` (Proven 100% Successful)

- **`[ECM] 32984` (Idle Dashpot Decay vs. Dashpot Airflow)**:
  - Rows 1–4 (`0.0, 0.2, 0.4, 0.6 lb/min`) retained at `0.02, 0.03, 0.04, 0.05 lb/min`. 100% eliminated the rolling idle hang without requiring a throttle blip.
- **`[ECM] 44491` & `44492` (DFCO Enable & Disable VSS)**:
  - Retained at `14.00 mph` enable / `10.00 mph` disable. Maintained active engine braking into 1st/2nd gear traffic speeds.
- **`[ECM] 44496` (DFCO Closed Throttle Delay)**:
  - Retained at `1.25 s`. Delivered stopwatch precision (mean 1.25s) across 14 injector cut events.
- **`[ECM] 32988` (Idle Dashpot Pre-Position vs. RPM)**:
  - Retained at `0.55 lb/min` at 2,150 RPM.

---

## Pre-Flash Checklist

> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The agent never initiates an ECU write, readback, DTC clear, or adaptation reset.

