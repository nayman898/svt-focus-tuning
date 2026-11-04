# v033 — Loud Crisp Overrun Pops Across Mid/High RPM

**Prepared candidate for owner inspection and staged road testing.**  
Exact parent and immediate rollback: [v032](v032-kill-oscillation-crisp-pops.md).

- **Candidate Binary**: [v033-loud-crisp-pops.hpt](v033-loud-crisp-pops.hpt)
  - Size: `262381` bytes
  - SHA-256: `41B8D374770A0F15231EF0D3C8E5DF26C132F3A198B439CEC3E479E821397C23`
- **Parent Binary**: [v032-kill-oscillation-crisp-pops.hpt](v032-kill-oscillation-crisp-pops.hpt)
  - Size: `260813` bytes
  - SHA-256: `4C9D3DF100C49265632DAF2AC6C14D5065685C3025E308376E33DB8D56781BC3`

---

## Calibration Rationale

Derived from `paired-20261104-122527-75371a04-v032` and `paired-20261104-123109-5f5905f7-v032-2` road test telemetry:
1. **Bucking/Spark Oscillation Confirmed Solved**: In v032, Torque Control spark cuts fell from 881 samples in v031 to **0 samples** across both test runs. Disabling `[ECM] 44771 Torque Oscillation Module` and setting `[ECM] 44776` Row 14 (`OSCMOD / Anti-Shuffle`) to `1.000` completely eradicated part-throttle cruising bucking.
2. **Deepen Decel Retard for Loud, Sharp Pops**: Owner feedback noted pops in v032 were "super quiet". Mathematical analysis revealed that `[ECM] 44605` 3,000 RPM cell at `-3.00°` ATDC was too shallow to produce explosive acoustic wavefronts, and 2,000 RPM at `+8.00°` pulled timing positive below 2,727 RPM. Candidate v033 deepens 3,000 RPM to **`-8.00°` ATDC** and 4,000–6,000 RPM to **`-10.00°` ATDC**, creating sharp, explosive combustion shockwaves in the exhaust manifold during coast-down.
3. **Smooth Return to Idle**: Lowers 2,000 RPM from `+8.00°` to **`+2.00°`**, preventing premature positive timing while maintaining a non-bogging cushion as engine speed falls toward warm idle (900 RPM).
4. **Extend Overrun Fuel Window**: Extends `[ECM] 44496 DFCO Closed Throttle Delay` from `1.35 s` to **`1.40 s`** (+50ms), widening the fuel injection duration after throttle lift to ensure a consistent 4-to-6 pop cadence before clean injector cutoff.
5. **Preserves Proven Base**: Retains v032 anti-shuffle fixes and v031 MAF Columns 14–17 -2.5% scaling.

---

## Detailed Parameter Changes

### `[ECM] 44496` — DFCO Closed Throttle Delay
| Parameter | Parent (`v032`) | Candidate (`v033`) | Delta |
| :--- | :---: | :---: | :---: |
| **`[ECM] 44496` DFCO Closed Throttle Delay** | `1.35 s` | **`1.40 s`** | +0.05s extension for sustained overrun pop cadence |

### `[ECM] 44605` — Spark Decel vs. RPM vs. ECT
| Row | Column | ECT (°F) | RPM | Parent Value (`v032`) | Candidate Value (`v033`) | Delta / Note |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 4 | 3 | 100 | 2,000 | `8.00` | **`2.00`** | -6.00°: Prevents premature positive timing pull |
| 4 | 4 | 100 | 3,000 | `-3.00` | **`-8.00`** | -5.00°: Deep retard for loud, crisp pops |
| 4 | 5 | 100 | 4,000 | `-8.00` | **`-10.00`** | -2.00°: Explosive high-RPM overrun pops |
| 4 | 6 | 100 | 5,000 | `-8.00` | **`-10.00`** | -2.00°: Explosive high-RPM overrun pops |
| 4 | 7 | 100 | 6,000 | `-8.00` | **`-10.00`** | -2.00°: Explosive high-RPM overrun pops |
| 5 | 3 | 200 | 2,000 | `8.00` | **`2.00`** | -6.00°: Warm engine cushion for smooth idle drop |
| 5 | 4 | 200 | 3,000 | `-3.00` | **`-8.00`** | -5.00°: Deep retard for loud, crisp pops |
| 5 | 5 | 200 | 4,000 | `-8.00` | **`-10.00`** | -2.00°: Explosive high-RPM overrun pops |
| 5 | 6 | 200 | 5,000 | `-8.00` | **`-10.00`** | -2.00°: Explosive high-RPM overrun pops |
| 5 | 7 | 200 | 6,000 | `-8.00` | **`-10.00`** | -2.00°: Explosive high-RPM overrun pops |

---

## In-Editor Verification Evidence

1. **Reopened Candidate**: Reopened directly from disk into VCM Editor. Recheck confirmed:
   - `[ECM] 44496`: `1.40`
   - `[ECM] 44605` Row 4 & 5: `2.00` at 2k, `-8.00` at 3k, `-10.00` at 4k–6k
   - Unedited cells (Rows 1–3, Columns 1–2): 100% preserved
2. **Whole-File Comparison vs Parent (`v032`)**:
   - `Compare > View Comparison Log` confirmed exactly 3 differences:
     * `Notes`
     * `DFCO Closed Throttle Delay [ECM 44496]`
     * `Spark Decel vs. RPM vs. ECT [ECM 44605]`
   - Zero unintended table or scalar differences across the entire calibration.

---

## Staged Road Test Protocol

- Flash `v033-loud-crisp-pops.hpt` using VCM Editor (`Flash > Write Vehicle`).
- Connect paired VCM Scanner + SCG-1 logger.
- Test 1: Decelerate from 4,500 RPM down to 2,000 RPM in 2nd and 3rd gears (verify loud, sharp, acoustic crackles across 4.5k–2.5k RPM).
- Test 2: Cruising check at 2,800–3,200 RPM part-throttle (confirm spark stays steady and bucking remains zero).
- Test 3: Observe idle return after decel (verify smooth settling to 900 RPM without undershoot).
- Return log session for automated review.

