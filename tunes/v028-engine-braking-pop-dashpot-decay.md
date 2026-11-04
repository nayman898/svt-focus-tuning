# v028 — Engine Braking, Overrun Decel Pop & Dashpot Decay Fix

**Prepared candidate for active road testing.**
Exact parent and immediate rollback: [v027](v027-engine-braking-decel-pop.md), which was road tested on 2026-11-03.

- **Candidate Binary**: [v028-engine-braking-pop-dashpot-decay.hpt](v028-engine-braking-pop-dashpot-decay.hpt)
  - Candidate Size: `259,325` bytes
  - Candidate SHA-256: `0DFDEA68506F8AF005404E29F1403B46D998123A98E5417FDEB1481EE13BF752`
- **Parent Binary**: [v027-engine-braking-decel-pop.hpt](v027-engine-braking-decel-pop.hpt)
  - Parent Size: `257,981` bytes
  - Parent SHA-256: `3535FDB33BBEB369B2AB36DF22190E7B03EE9ABC9FBCFFEBF56930D41BE59AF5`

---

## Causal Scope & Calibration Parameters

`v028` addresses three specific drivability items reported from the `v027` road test:

### 1. Fix Hanging Idle: `[ECM] 32984` (Idle Dashpot Decay vs. Dashpot Airflow)
*Location: `Engine > Idle > Airflow > Dashpot Airflow`*

In all prior tunes back to the previous tuner's baseline, the dashpot decay rate was zeroed out (`0.00`) below `0.60 lb/min`. As a result, when rolling to a stop, the IAC valve stopped decaying dashpot air once it reached `0.60 lb/min`, locking the engine at ~1,300–1,500 RPM until a throttle blip forced a transition out of closed throttle. Restoring active decay across the bottom rows allows dashpot airflow to smoothly and continuously bleed down to zero as you roll to a stop.

| Airflow Breakpoint (lb/min) | Parent (`v027`) Decay Rate | Candidate (`v028`) Decay Rate | Change | Effect |
| :---: | :---: | :---: | :---: | :--- |
| **0.0** | 0.00 | **0.02** | +0.02 | Smooth decay all the way to zero idle airflow |
| **0.2** | 0.00 | **0.03** | +0.03 | Active decay near settled idle |
| **0.4** | 0.00 | **0.04** | +0.04 | Eliminates dashpot freeze below 0.6 lb/min |
| **0.6** | 0.00 | **0.05** | +0.05 | Eliminates 1,300–1,500 RPM floating on coast-down |
| **0.8** | 0.06 | 0.06 | Unchanged | Retained |
| **1.0** | 0.08 | 0.08 | Unchanged | Retained |
| **3.0** | 0.10 | 0.10 | Unchanged | Retained |

---

### 2. More Engine Braking: `[ECM] 32988`, `[ECM] 44491`, and `[ECM] 44492`

1. **`[ECM] 32988` (Idle Dashpot Pre-Position vs. RPM)**:
   *Location: `Engine > Idle > Airflow > Dashpot Airflow`*
   - Row 4 (`2,150 RPM`): `0.78` $\to$ **`0.55 lb/min`** (`-0.23 lb/min`).
   - *Rationale*: Reduces IAC cushion air in 2nd/3rd gear decel, increasing engine braking vacuum drag.
2. **`[ECM] 44491` (Minimum VSS to Allow DFCO)**:
   *Location: `Engine > Fuel > Deceleration Fuel Cutoff`*
   - `18.00` $\to$ **`14.00 mph`** (`-4.00 mph`).
3. **`[ECM] 44492` (Maximum VSS to Disable DFCO)**:
   *Location: `Engine > Fuel > Deceleration Fuel Cutoff`*
   - `12.00` $\to$ **`10.00 mph`** (`-2.00 mph`).
   - *Rationale*: Keeps deceleration fuel cutoff active down into 1st/2nd gear traffic speeds instead of cutting out at 18/12 mph.

---

### 3. Slightly More Overrun Pops: `[ECM] 44496` and `[ECM] 44605`

1. **`[ECM] 44496` (DFCO Closed Throttle Delay)**:
   *Location: `Engine > Fuel > Deceleration Fuel Cutoff`*
   - `1.00 s` $\to$ **`1.25 s`** (`+0.25 s`).
   - *Rationale*: Extends the overrun window by 250 ms so the burble/pops are slightly more audible and sustained before fuel cuts completely.
2. **`[ECM] 44605` (Spark Decel vs. RPM vs. ECT)**:
   *Location: `Engine > Spark > Decel`*
   *Row 5 (`200°F ECT`)*:
   - `800 RPM`: `14.00°` (Unchanged — protects idle return)
   - `1,000 RPM`: `12.00°` (Unchanged — protects idle return)
   - `2,000 RPM`: `13.00°` (Unchanged — protects clutch-in anti-stall cushion)
   - `3,000 RPM`: `0.00°` $\to$ **`-2.00°` ATDC**
   - `4,000 RPM`: `-2.00°` $\to$ **`-4.00°` ATDC**
   - `5,000 RPM`: `-2.00°` $\to$ **`-4.00°` ATDC**
   - `6,000 RPM`: `-2.00°` $\to$ **`-4.00°` ATDC**
   - *Rationale*: Retards decel spark by an additional 2 degrees above 3,000 RPM for crisper, slightly more pronounced overrun pops without thermal risk to the exhaust turbine.

---

### 4. Cruising Stutter Investigation

On the `v028` road test, hold steady light-throttle cruise (~35–45 mph, 2,000–2,500 RPM, 2–5% throttle) for 10–15 seconds with both VCM Scanner and SCG Logger recording. This will allow precise diagnosis of:
- STFT closed-loop trim vs wideband lambda
- MAF transfer airflow voltage in the light cruise region (~0.90–1.20 V)
- Spark borderline advance and spark source

---

## Pre-Flash Checklist

> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The agent never initiates an ECU write, readback, DTC clear, or adaptation reset.

