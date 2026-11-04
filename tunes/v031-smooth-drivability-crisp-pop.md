# v031 — Smooth Low-RPM Drivability & Crisp High-RPM Decel Pops

**Prepared candidate for owner inspection and staged road testing.**  
Exact parent and immediate rollback: [v030](v030.md).

- **Candidate Binary**: [v031-smooth-drivability-crisp-pop.hpt](v031-smooth-drivability-crisp-pop.hpt)
  - Size: `260781` bytes
  - SHA-256: `7A19C33ED9396F8AA356A8BADCAA5A0243409FB008B02C1BBD6AA208DEC02B2A`
- **Parent Binary**: [v030-smooth-tipin-enhanced-pop.hpt](v030-smooth-tipin-enhanced-pop.hpt)
  - Size: `259501` bytes
  - SHA-256: `8607FCBF188FA6C9D5D6A54817DE2893682520A3D0FC95247A57CF82DCF2E467`

---

## Calibration Rationale

Derived from paired-20261104-075425-a8636a50-v030 log analysis: (1) Completely disables Tip-In Torque Control spark chops by raising [ECM] 44607 to 7,500 RPM, eliminating the 2,400 RPM oscillation boundary that caused 561 torque-cut chops; (2) Shortens [ECM] 44496 DFCO delay from 1.75s to 0.90s for a concise, punchy pop burst; (3) Re-cushions [ECM] 44605 decel spark at 2,000 RPM (+10.0 deg) and 3,000 RPM (+2.0 deg) to prevent tip-in bogging, while deepening 4,000-6,000 RPM to -8.0 deg ATDC for louder, sharper pops on overrun; (4) Trims [ECM] 12163 MAF Columns 14-17 by -2.5% to zero out cruising STFT.

---

## Detailed Parameter Changes

### `[ECM] 44607` — Spark Tip-In Torque Control RPM Min
| Parameter | Parent (`v030`) | Candidate (`v031`) | Delta |
| :--- | :---: | :---: | :---: |
| **`[ECM] 44607` Spark Tip-In Torque Control RPM Min** | N/A | **7,500** | `7,500` vs `N/A` |

### `[ECM] 44496` — DFCO Closed Throttle Delay
| Parameter | Parent (`v030`) | Candidate (`v031`) | Delta |
| :--- | :---: | :---: | :---: |
| **`[ECM] 44496` DFCO Closed Throttle Delay** | N/A | **0.90** | `0.90` vs `N/A` |

### `[ECM] 44605` — Spark Decel vs. RPM vs. ECT
| Row | Column | Parent Value | Candidate Value | Delta / Note |
| :---: | :---: | :---: | :---: | :--- |
| 4 | 3 | N/A | **10.00** | Row 4 (100 ECT) 2,000 RPM |
| 4 | 4 | N/A | **2.00** | Row 4 (100 ECT) 3,000 RPM |
| 4 | 5 | N/A | **-8.00** | Row 4 (100 ECT) 4,000 RPM |
| 4 | 6 | N/A | **-8.00** | Row 4 (100 ECT) 5,000 RPM |
| 4 | 7 | N/A | **-8.00** | Row 4 (100 ECT) 6,000 RPM |
| 5 | 3 | N/A | **10.00** | Row 5 (200 ECT) 2,000 RPM |
| 5 | 4 | N/A | **2.00** | Row 5 (200 ECT) 3,000 RPM |
| 5 | 5 | N/A | **-8.00** | Row 5 (200 ECT) 4,000 RPM |
| 5 | 6 | N/A | **-8.00** | Row 5 (200 ECT) 5,000 RPM |
| 5 | 7 | N/A | **-8.00** | Row 5 (200 ECT) 6,000 RPM |

### `[ECM] 12163` — MAF Airflow vs. Voltage
| Row | Column | Parent Value | Candidate Value | Delta / Note |
| :---: | :---: | :---: | :---: | :--- |
| 1 | 14 | N/A | **-2.50%** | Col 14 (1.000V) |
| 1 | 15 | N/A | **-2.50%** | Col 15 (1.100V) |
| 1 | 16 | N/A | **-2.50%** | Col 16 (1.200V) |
| 1 | 17 | N/A | **-2.50%** | Col 17 (1.299V) |

---

## Owner VCM Editor Inspection & Validation Guide

> [!IMPORTANT]
> Always validate candidate changes against the parent calibration before flashing to the vehicle.
> The assistant NEVER initiates live ECU writes or vehicle actuation.

### 30-Second Validation Procedure:
1. **Open Candidate**: Launch VCM Editor and open `tunes/v031-smooth-drivability-crisp-pop.hpt`.
2. **Open Compare**: Click `Compare > Open Compare File` and select `tunes/v030-smooth-tipin-enhanced-pop.hpt`.
3. **View Comparison Log**: Click `Compare > View Comparison Log`.
   - Confirm that **ONLY** the target parameters listed above appear in the difference tree.
   - Confirm that no unintended engine, transmission, or fuel parameters have changed.
4. **Inspect Parameter Tables**: Navigate to each modified parameter (press `Ctrl+N` and enter Parameter ID) and verify the values match the table above.
5. **Verify Notes**: Click `Edit > Calibration Details > Notes` and verify the revision note was appended.

---

## Staged Road Test Protocol

- Flash `v031-smooth-drivability-crisp-pop.hpt` using VCM Editor (`Flash > Write Vehicle`).
- Connect paired VCM Scanner + SCG-1 logger.
- Execute targeted test maneuvers as outlined in the Master Roadmap.
- Return log session for sub-2-minute automated review.
