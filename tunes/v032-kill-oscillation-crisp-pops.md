# v032 — Kill Cruising Spark Oscillation & Restore Crisp Overrun Pops

**Prepared candidate for owner inspection and staged road testing.**  
Exact parent and immediate rollback: [v031](v031-smooth-drivability-crisp-pop.md).

- **Candidate Binary**: [v032-kill-oscillation-crisp-pops.hpt](v032-kill-oscillation-crisp-pops.hpt)
  - Size: `260813` bytes
  - SHA-256: `4C9D3DF100C49265632DAF2AC6C14D5065685C3025E308376E33DB8D56781BC3`
- **Parent Binary**: [v031-smooth-drivability-crisp-pop.hpt](v031-smooth-drivability-crisp-pop.hpt)
  - Size: `260781` bytes
  - SHA-256: `7A19C33ED9396F8AA356A8BADCAA5A0243409FB008B02C1BBD6AA208DEC02B2A`

---

## Calibration Rationale

Derived from `paired-20261104-095419-1f8e78f4-v031-drive` log analysis:
1. **Kill Cruising Spark Oscillation**: Disables `[ECM] 44771 Torque Oscillation Module` and neutralizes `[ECM] 44776` Row 14 (`OSCMOD / Anti-Shuffle`) to `1.000`. This eliminates the 12–15 Hz rapid spark chop limit cycle (`24° <-> 4°`) captured at 5:38 (`t=340s`), where the factory anti-shuffle module mistook part-throttle turbo torque rise for driveline shunt. Confirms `[ECM] 44607 Tip-In Torque Control RPM Min` raised to `7,500 RPM`.
2. **Restore Crisp Overrun Pops**: Extends `[ECM] 44496 DFCO Closed Throttle Delay` from `0.90 s` to **`1.35 s`**. In v031, the 0.90s delay left only ~300ms of fuel after throttle closure (yielding only 1–2 pops before fuel cut). A 1.35s delay provides the ideal 3-to-5 pop cadence before clean injector cutoff.
3. **Broaden Overrun Decel RPM Window**: Deepens `[ECM] 44605` 3,000 RPM decel cells to **`-3.00°` ATDC** (Rows 4 & 5), restoring crackles across typical 2,800–3,800 RPM driving coast-downs. Retains loud **`-8.00°` ATDC** from 4,000–6,000 RPM, and cushions 2,000 RPM at **`+8.00°`** for smooth idle drop.
4. **Preserves v031 MAF Centering**: Keeps MAF Columns 14–17 -2.5% scaling which successfully centered cruising STFT between `+0.5%` and `+1.5%`.

---

## Detailed Parameter Changes

### `[ECM] 44771` — Torque Oscillation Module
| Parameter | Parent (`v031`) | Candidate (`v032`) | Delta |
| :--- | :---: | :---: | :---: |
| **`[ECM] 44771` Torque Oscillation Module** | `Enabled` | **`Disabled`** | Anti-shuffle spark chop hunting eliminated |

### `[ECM] 44776` — Spark Torque Ratio Limit vs. Requestor
| Row | Requestor | Parent Value (`v031`) | Candidate Value (`v032`) | Note |
| :---: | :--- | :---: | :---: | :--- |
| 14 | **OSCMOD / Anti-Shuffle** | `0.250` | **`1.000`** | Failsafe: forbids torque-ratio spark retard |

### `[ECM] 44607` — Spark Tip-In Torque Control RPM Min
| Parameter | Parent (`v031`) | Candidate (`v032`) | Delta |
| :--- | :---: | :---: | :---: |
| **`[ECM] 44607` Spark Tip-In Torque Control RPM Min** | `7,500` | **`7,500`** | Confirmed disabled well above redline |

### `[ECM] 44496` — DFCO Closed Throttle Delay
| Parameter | Parent (`v031`) | Candidate (`v032`) | Delta |
| :--- | :---: | :---: | :---: |
| **`[ECM] 44496` DFCO Closed Throttle Delay** | `0.90` | **`1.35`** | +0.45s overrun window for crisp 3–5 pop cadence |

### `[ECM] 44605` — Spark Decel vs. RPM vs. ECT
| Row | Column | Parent Value (`v031`) | Candidate Value (`v032`) | Delta / Note |
| :---: | :---: | :---: | :---: | :--- |
| 4 | 3 | `10.00` | **`8.00`** | Row 4 (100 ECT) 2,000 RPM cushion |
| 4 | 4 | `2.00` | **`-3.00`** | Row 4 (100 ECT) 3,000 RPM pop enable |
| 4 | 5 | `-8.00` | **`-8.00`** | Row 4 (100 ECT) 4,000 RPM loud crackle |
| 4 | 6 | `-8.00` | **`-8.00`** | Row 4 (100 ECT) 5,000 RPM loud crackle |
| 4 | 7 | `-8.00` | **`-8.00`** | Row 4 (100 ECT) 6,000 RPM loud crackle |
| 5 | 3 | `10.00` | **`8.00`** | Row 5 (200 ECT) 2,000 RPM cushion |
| 5 | 4 | `2.00` | **`-3.00`** | Row 5 (200 ECT) 3,000 RPM pop enable |
| 5 | 5 | `-8.00` | **`-8.00`** | Row 5 (200 ECT) 4,000 RPM loud crackle |
| 5 | 6 | `-8.00` | **`-8.00`** | Row 5 (200 ECT) 5,000 RPM loud crackle |
| 5 | 7 | `-8.00` | **`-8.00`** | Row 5 (200 ECT) 6,000 RPM loud crackle |

---

## Owner VCM Editor Inspection & Validation Guide

> [!IMPORTANT]
> Always validate candidate changes against the parent calibration before flashing to the vehicle.
> The assistant NEVER initiates live ECU writes or vehicle actuation.

### 30-Second Validation Procedure:
1. **Open Candidate**: Launch VCM Editor and open `tunes/v032-kill-oscillation-crisp-pops.hpt`.
2. **Open Compare**: Click `Compare > Open Compare File` and select `tunes/v031-smooth-drivability-crisp-pop.hpt`.
3. **View Comparison Log**: Click `Compare > View Comparison Log`.
   - Confirm that **ONLY** the target parameters listed above appear in the difference tree.
   - Confirm that no unintended engine, transmission, or fuel parameters have changed.
4. **Inspect Parameter Tables**: Navigate to each modified parameter (press `Ctrl+N` and enter Parameter ID) and verify the values match the table above.
5. **Verify Notes**: Click `Edit > Calibration Details > Notes` and verify the revision note was appended.

---

## Staged Road Test Protocol

- Flash `v032-kill-oscillation-crisp-pops.hpt` using VCM Editor (`Flash > Write Vehicle`).
- Connect paired VCM Scanner + SCG-1 logger.
- Test 1: Cruise at 2,800–3,200 RPM and modulate throttle across 30%–45% pedal (confirm zero spark chop / no bucking).
- Test 2: Decelerate from 4,500 RPM down through 2,500 RPM (confirm crisp 3–5 pop cadence terminating cleanly at 1.35s).
- Return log session for sub-2-minute automated review.
