# v027 — Engine Braking Restoration & Subtle Overrun Decel Pop

**Prepared, verified by vehicle owner screenshots, and flashed for active road testing.**
Exact parent and immediate rollback: [v026](v026-open-loop-tps-threshold.md), which was tested in [2026-11-03-v026-drive-review.md](../reports/2026-11-03-v026-drive-review.md).

- **Candidate Binary**: [v027-engine-braking-decel-pop.hpt](v027-engine-braking-decel-pop.hpt)
  - Size: `257,981` bytes
  - SHA-256: `3535FDB33BBEB369B2AB36DF22190E7B03EE9ABC9FBCFFEBF56930D41BE59AF5`
- **Parent Binary**: [v026-open-loop-tps-threshold.hpt](v026-open-loop-tps-threshold.hpt)
  - Size: `257,885` bytes
  - SHA-256: `86B10615EB5E032CF4343120A23C6B93DB30FD6CFC558CE863143C32629B1918`

---

## Causal Scope & Calibration Parameters

`v027` targets deceleration drivability, in-gear engine braking responsiveness, and subtle overrun exhaust character while strictly preserving idle recovery and wide-open throttle safety. Four specific parameters were adjusted:

### 1. Deceleration Fuel Cutoff (DFCO) Parameters

| Parameter ID | Parameter Name | Location | Parent (`v026`) | Candidate (`v027`) | Change | Rationale |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `[ECM] 44491` | Minimum VSS to Allow DFCO | `Engine > Fuel > Deceleration Fuel Cutoff` | `35.00 mph` | `18.00 mph` | `-17.00 mph` | Restores in-gear engine braking during typical 2nd/3rd gear street deceleration down to 18 mph instead of freewheeling above 18–34 mph. |
| `[ECM] 44496` | DFCO Closed Throttle Delay | `Engine > Fuel > Deceleration Fuel Cutoff` | `3.00 s` | `1.00 s` | `-2.00 s` | Shortens entry delay from 3.0s to 1.0s so engine braking begins promptly upon lift-off, while providing a 1.0s window for subtle overrun burble before injectors cut completely. |

### 2. Decel Ignition Timing (`[ECM] 44605` Spark Decel vs. RPM vs. ECT)

Located at `Engine > Spark > Decel`. Decel timing at operating temperature (`200°F ECT`) is retarded at $\ge 3{,}000\text{ RPM}$ to produce subtle exhaust burble/pops during the 1.0s pre-DFCO overrun window, while decel timing at $\le 2{,}000\text{ RPM}$ is untouched to safeguard clutch-in idle catch.

| ECT (°F) | 800 RPM | 1,000 RPM | 2,000 RPM | 3,000 RPM | 4,000 RPM | 5,000 RPM | 6,000 RPM | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **-20** | 14.00 | 12.00 | 13.00 | 14.00 | 15.00 | 16.00 | 17.00 | *Untouched (cold protection)* |
| **20** | 14.00 | 12.00 | 13.00 | 14.00 | 15.00 | 16.00 | 17.00 | *Untouched (cold protection)* |
| **60** | 5.00 | 5.00 | 5.00 | 5.00 | 15.00 | 16.00 | 17.00 | *Untouched* |
| **100** | 5.00 | 5.00 | 5.00 | 5.00 | 15.00 | 16.00 | 17.00 | *Untouched* |
| **200 (v026)** | 14.00 | 12.00 | 13.00 | 14.00 | 15.00 | 16.00 | 17.00 | *Stock advanced decel timing* |
| **200 (v027)** | **14.00** | **12.00** | **13.00** | **0.00** | **-2.00** | **-2.00** | **-2.00** | **Subtle overrun burble $\ge 3{,}000\text{ RPM}$; idle catch safe $\le 2{,}000$** |

### 3. Decel Airflow Pre-Position (`[ECM] 32988` Idle Dashpot Pre-Position vs. RPM)

Located at `Engine > Idle > Airflow`. Trims pre-position dashpot air at 3,150 and 4,150 RPM to prevent the IAC valve from holding excess throttle air open upon lift-off, improving immediate engine deceleration torque without compromising low-RPM anti-stall dashpot air.

| Breakpoint (RPM) | Parent (`v026`) (lb/min) | Candidate (`v027`) (lb/min) | Delta | Purpose |
| :---: | :---: | :---: | :---: | :--- |
| **0** | 0.04 | 0.04 | 0.00 | Untouched |
| **150** | 0.04 | 0.04 | 0.00 | Untouched |
| **1,150** | 0.35 | 0.35 | 0.00 | Untouched (crucial anti-stall idle catch) |
| **2,150** | 0.78 | 0.78 | 0.00 | Untouched (anti-stall cushion) |
| **3,150** | 1.11 | **0.80** | -0.31 | Eliminates throttle floating during mid-RPM decel |
| **4,150** | 1.50 | **1.00** | -0.50 | Eliminates throttle floating during high-RPM decel |

---

## Empirical Context & Boost Controller Interaction

1. **Innovate SCG-1 Boost Controller**:
   - The vehicle owner adjusted the SCG-1 duty cycle to **8% WGDC** (from 6%), with `SPG = 7 psi` spring weight, `bSt = 16 psi` boost cut, and `AFr = 12.8` lean cut.
   - In `v026`, 6% WGDC produced 12.09 psi peak boost at 6,962 RPM. With the cleaned solenoid filter flowing freely, 8% WGDC is expected to target ~13.5–14.0 psi peak manifold boost.
2. **Fuel & Spark Safety**:
   - At 12 psi in `v026`, wideband AFR tracked 0.733–0.740 Lambda (~10.8 AFR) with 40 psi rail pressure maintained across the 7,000 RPM pull and zero knock retard (`0.00°`).
   - `v027` preserves the entire MAF curve (`[ECM] 12163`), base fuel table (`[ECM] 44511`), and WOT spark borderline tables without any alterations.

---

## Verification & Integrity

1. **Owner Visual Screenshot Verification**:
   - Owner inspected and verified all 4 calibration tables in VCM Editor before writing:
     - `media_1793750340826_ccaea673.png`: Confirmed `32988` reads 0.80 at 3,150 RPM and 1.00 at 4,150 RPM.
     - `media_1793750375464_31c214c6.png`: Confirmed `44491` reads 18.00 mph and `44496` reads 1.00 s.
     - `media_1793750387132_97dfdd14.png`: Confirmed `44605` reads 0.00 at 3k, -2.00 at 4k/5k/6k for row 200°F ECT, and 14/12/13° intact for $\le 2{,}000\text{ RPM}$.
2. **Binary Fingerprint**:
   - Size: `257,981` bytes
   - SHA-256: `3535FDB33BBEB369B2AB36DF22190E7B03EE9ABC9FBCFFEBF56930D41BE59AF5`
3. **Repository Consistency**:
   - All 27 previous tune binaries (`v000` through `v026`) match documented SHA-256 hashes bit-for-bit.
   - Strict privacy scrub verified: zero 17-character VINs or 10-digit MPVI serials exist in any file or commit.
