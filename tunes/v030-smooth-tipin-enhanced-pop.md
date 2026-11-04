# v030 — Smooth Tip-In & Enhanced Safe Decel Pops

**Prepared candidate for active road testing.**  
Exact parent and immediate rollback: [v029](v029-decel-pop-cruise-smooth.md), which was road tested on 2026-11-03 in [2026-11-03-v029-drive-review.md](../reports/2026-11-03-v029-drive-review.md).

- **Candidate Binary**: [v030-smooth-tipin-enhanced-pop.hpt](v030-smooth-tipin-enhanced-pop.hpt)
  - Candidate Size: Pending save by owner
  - Candidate SHA-256: `PENDING_OWNER_FLASH_SAVE`
- **Parent Binary**: [v029-decel-pop-cruise-smooth.hpt](v029-decel-pop-cruise-smooth.hpt)
  - Parent Size: `259,421` bytes
  - Parent SHA-256: `E5846434088486A13F43EEE65F8F21E8DF38B972C84868AE580E5593BB966021`

---

## Causal Scope & Calibration Parameters

`v030` delivers two key upgrades: it eliminates the low-RPM, low-throttle tip-in stutter diagnosed in `v029`, and enhances the overrun decel crackle safely without placing excessive thermal stress on the turbo or exhaust valves.

### 1. Eliminate Low-RPM Tip-In Torque Snatch: `[ECM] 44607` (Spark Tip-In Torque Control RPM Min)
*Location: `Engine > Spark > Advance > Transient > Spark Tip-In Torque Control RPM Min`*

In `v029`, tip-in torque control was active all the way down to **775 RPM**. When modulating the throttle at low speeds (1,200–2,400 RPM), the rapid airflow delta from the turbo tripped `[ECM] 44608`, causing the PCM to repeatedly cut 15°–17° of ignition timing (oscillating between 23° and 6° four to five times within 0.7 seconds).

`v030` raises `[ECM] 44607` to **`2,400 RPM`**:

| Parameter | Parent (`v029`) | Candidate (`v030`) | Delta | Purpose |
| :---: | :---: | :---: | :---: | :--- |
| **`[ECM] 44607` Spark Tip-In Torque Control RPM Min** | 775 RPM | **2,400 RPM** | +1,625 RPM | Completely disables violent tip-in timing cuts during parking-lot, low-gear, and creeping acceleration; preserves normal torque control above 2,400 RPM |

---

### 2. Bridge the Low-Throttle MAF Lean Pocket: `[ECM] 12163` (MAF Airflow vs. Voltage)
*Location: `Engine > Airflow > General > MAF Calibration > MAF Airflow vs. Voltage`*

In `v029`, cracking open the throttle from idle/coast (TPS 190–260 ADC) swept through `0.70V–0.88V` MAF voltage, causing wideband lambda to spike lean to **1.15–1.28** (17.0–18.8 AFR) due to Column 11 (`0.699V`) remaining at its reduced `v025` value.

`v030` bumps Column 11 by **`+6.0%`**:

| Breakpoint | Parent (`v029`) Airflow (`lb/min`) | Parent (`v029`) Airflow (`lb/h`) | Candidate (`v030`) Airflow (`lb/min`) | Candidate (`v030`) Airflow (`lb/h`) | Delta | Purpose |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Column 11 (`0.699V`)** | 0.0944 | 5.66 | **0.1000** | **6.00** | +6.0% | Bridges the lean tip-in transition between idle (0.60V) and cruise (0.90V) |

---

### 3. Enhanced Safe Decel Overrun Pops: `[ECM] 44605` (Spark Decel vs. RPM vs. ECT)
*Location: `Engine > Spark > Decel`*

In `v029`, decel spark retarded to `-2.0°` at 3,000 RPM and `-4.0°` at 4,000–6,000 RPM, producing subtle overrun pops. To make the crackle more distinct and audible without risking exhaust valve or turbo integrity:
* We deepen retard from `-4.00°` to **`-6.00°` ATDC** at 4,000–6,000 RPM (a moderate, crisp crackle, well clear of aggressive -20° flame maps).
* We deepen retard from `-2.00°` to **`-4.00°` ATDC** at 3,000 RPM.
* We smooth 2,000 RPM down to **`+2.00°`** (from +5° / +13°), allowing the crackle to taper naturally down toward 2,200 RPM while maintaining positive timing for idle catch:

#### Row 4 (`100` ECT) & Row 5 (`200` ECT) Matrix:

| RPM Column | v029 Value (deg) | v030 Value (deg) | Delta | Behavioral Effect |
| :---: | :---: | :---: | :---: | :--- |
| **Column 1 (`800 RPM`)** | 5.00 (Row 4) / 14.00 (Row 5) | **5.00** / **14.00** | 0.00° | *Untouched (idle catch protection)* |
| **Column 2 (`1,000 RPM`)** | 5.00 (Row 4) / 12.00 (Row 5) | **5.00** / **12.00** | 0.00° | *Untouched (anti-stall protection)* |
| **Column 3 (`2,000 RPM`)** | 5.00 (Row 4) / 13.00 (Row 5) | **2.00** | -3.0° / -11.0° | Extends burble smoothly down to ~2,200 RPM |
| **Column 4 (`3,000 RPM`)** | -2.00 | **-4.00** | -2.00° | Deeper, more defined mid-range pop |
| **Column 5 (`4,000 RPM`)** | -4.00 | **-6.00** | -2.00° | Crisp, audible sports-car overrun crackle |
| **Column 6 (`5,000 RPM`)** | -4.00 | **-6.00** | -2.00° | Crisp, audible sports-car overrun crackle |
| **Column 7 (`6,000 RPM`)** | -4.00 | **-6.00** | -2.00° | Crisp, audible sports-car overrun crackle |

---

### 4. Extended Overrun Window: `[ECM] 44496` (Minimum Time to Delay DFCO)
*Location: `Engine > Fuel > Cutoff, DFCO > Deceleration Fuel Cutoff > Minimum Time to Delay DFCO`*

In `v029`, DFCO fuel cut activated after 1.25 seconds, limiting the popping window to ~1.0 second.

`v030` extends `[ECM] 44496` from **`1.25 s`** to **`1.75 s`**:

| Parameter | Parent (`v029`) | Candidate (`v030`) | Delta | Purpose |
| :---: | :---: | :---: | :---: | :--- |
| **`[ECM] 44496` DFCO Delay** | 1.25 s | **1.75 s** | +0.50 s | Gives a clean, enjoyable 1.5–1.7s window of overrun burble before injectors shut off |

---

### 5. Preserved Calibrations from `v028` and `v029`

- **`[ECM] 12163` (MAF Airflow vs. Voltage - 0.90V to 1.20V)**:
  - Columns 12–15 (`0.898V`, `1.000V`, `1.100V`, `1.200V`) preserved at `8.81`, `10.69`, `12.77`, `16.90 lb/h` (`0.1468`, `0.1781`, `0.2128`, `0.2816 lb/min`). Verified in `v029` to maintain closed-loop fuel trims between -0.8% and -2.0%.
- **`[ECM] 32984` (Idle Dashpot Decay vs. Dashpot Airflow)**:
  - Preserved at `0.02, 0.03, 0.04, 0.05 lb/min`. Rolling idle hang remains 100% eliminated.
- **`[ECM] 44491` & `44492` (DFCO Enable & Disable VSS)**:
  - Preserved at `14.00 mph` enable / `10.00 mph` disable.
- **Boost Control**:
  - SCG-1 settings preserved: `WG Duty = 6%`, `Active Press = 5.0–5.5 psi`, `Boost Cut = 16.0 psi / 100% cut` (peak boost ~11.2 psi).

---

## Pre-Flash Checklist

> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The agent never initiates an ECU write, readback, DTC clear, or adaptation reset.

- [ ] Open `v029-decel-pop-cruise-smooth.hpt` in VCM Editor.
- [ ] Save As `v030-smooth-tipin-enhanced-pop.hpt`.
- [ ] In `[ECM] 44607` (*Spark Tip-In Torque Control RPM Min*), change `775` to **`2400`**.
- [ ] In `[ECM] 12163` (*MAF Airflow vs. Voltage*), change Column 11 (`0.699V`) from `5.66` to **`6.00 lb/h`** (or `0.0944` to **`0.1000 lb/min`**).
- [ ] In `[ECM] 44605` (*Spark Decel vs. RPM vs. ECT*):
  - Row 4 (`100` ECT): enter `2.00` (2k), `-4.00` (3k), `-6.00` (4k, 5k, 6k).
  - Row 5 (`200` ECT): enter `2.00` (2k), `-4.00` (3k), `-6.00` (4k, 5k, 6k).
- [ ] In `[ECM] 44496` (*Minimum Time to Delay DFCO*), change `1.25` to **`1.75 s`**.
- [ ] Save file and confirm changes via **Compare > Open Compare File** against `v029`.
- [ ] Flash to vehicle via **Flash > Write Vehicle**.
