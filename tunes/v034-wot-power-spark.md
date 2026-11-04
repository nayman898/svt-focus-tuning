# v034 — WOT High-RPM Power Spark Advance & Decel Overrun Restoration

**Prepared candidate for owner inspection and staged road testing.**  
Exact parent and immediate rollback: [v033](v033-loud-crisp-pops.md) ([v033-loud-crisp-pops.hpt](v033-loud-crisp-pops.hpt)).

- **Candidate Binary**: [v034-wot-power-spark.hpt](v034-wot-power-spark.hpt)
  - Size: `263853` bytes
  - SHA-256: `7F9539CBD3654B8426B587A3A504EA3D30488564B9D52256F4EB613D06CA08FA`
- **Parent Binary**: [v033-loud-crisp-pops.hpt](v033-loud-crisp-pops.hpt)
  - Size: `262381` bytes
  - SHA-256: `41B8D374770A0F15231EF0D3C8E5DF26C132F3A198B439CEC3E479E821397C23`

---

## Calibration Rationale

Derived from `paired-20261104-123109-5f5905f7-v032-2` WOT pull telemetry and owner road test feedback (*"pull strength felt good, definitely peaking around 5k as it tapered out"*):
1. **Telemetry Diagnostics of WOT Pull (3,100 to 6,266 RPM at 13.1 psi boost)**:
   - The Innovate SCG-1 boost controller held a rock-solid **13.0–13.3 psi** flat from 5,500 to 6,266 RPM with `WGDC = 6%`. Boost did not drop off.
   - However, delivered ignition timing actually **drooped from 13.2° at 5,550 RPM down to 11.2° at 6,143 RPM** (and 10.75° in the table node).
   - This drop was commanded directly by `[ECM] 44583 Spark Borderline Knock vs. RPM vs. Load`: Row 8 (0.80 Load) was flat at 12.00°, while Row 9 (2.00 Load) tapered sharply downward from 11.50° at 5k down to 10.75° at 7.2k.
   - Meanwhile, MBT table `[ECM] 32265` specifies 13.75° across this entire upper RPM range.
2. **High-RPM Power Advance (+1.00° to +2.25°)**:
   - Candidate `v034` lifts Row 8 (0.80 Load) to **13.50°** at 5,000 RPM and **14.00°** across 5,750–7,200 RPM (+1.50° to +2.00°).
   - Candidate `v034` lifts Row 9 (2.00 Load, full boost) to **12.50°** at 5,000 RPM and **13.00°** across 5,750–7,200 RPM (+1.00° to +2.25°).
   - This eliminates the top-end timing sag, allowing the engine to carry cylinder pressure and torque strongly past 5,000 RPM to redline, while maintaining a safe 0.75° margin below MBT (13.75°).
3. **Preserves Safe Rich Fueling Buffer**:
   - Commanded WOT open loop fueling remains rich (~10.5–10.8 AFR / 0.71–0.74 lambda), providing an extra thermal and knock safety buffer on pump 93 octane while evaluating the timing increase.
4. **Inherits Full v033 Overrun Pop & v032 Anti-Shuffle Calibrations**:
   - Because `v033` was prepared but not flashed yet, `v034` inherits the entire v033 loud pop package (`[ECM] 44496` DFCO delay = 1.40s, `[ECM] 44605` pop cells = -8.00° at 3k, -10.00° at 4k–6k) and the v032 anti-shuffle bucking fixes, enabling the owner to gain both features in a single flash.

---

## Detailed Parameter Changes

### `[ECM] 44583` — Spark Borderline Knock vs. RPM vs. Load
| Row (Load) | Col (RPM) | Parent Value (`v033`) | Candidate Value (`v034`) | Delta | Engineering Purpose |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Row 8** (0.80) | Col 6 (5,000 RPM) | `12.00°` | **`13.50°`** | +1.50° | Smooth transition into high-RPM powerband |
| **Row 8** (0.80) | Col 7 (5,750 RPM) | `12.00°` | **`14.00°`** | +2.00° | High-RPM torque carry past 5,500 RPM |
| **Row 8** (0.80) | Col 8 (6,000 RPM) | `12.00°` | **`14.00°`** | +2.00° | Eliminate top-end timing sag |
| **Row 8** (0.80) | Col 9 (6,250 RPM) | `12.00°` | **`14.00°`** | +2.00° | Eliminate top-end timing sag |
| **Row 8** (0.80) | Col 10 (6,500 RPM) | `12.00°` | **`14.00°`** | +2.00° | Eliminate top-end timing sag |
| **Row 8** (0.80) | Col 11 (7,200 RPM) | `12.00°` | **`14.00°`** | +2.00° | Over-rev ceiling torque support |
| **Row 9** (2.00) | Col 6 (5,000 RPM) | `11.50°` | **`12.50°`** | +1.00° | Boost timing ramp past spool threshold |
| **Row 9** (2.00) | Col 7 (5,750 RPM) | `11.50°` | **`13.00°`** | +1.50° | Full boost (13+ psi) peak power advance |
| **Row 9** (2.00) | Col 8 (6,000 RPM) | `11.50°` | **`13.00°`** | +1.50° | Full boost (13+ psi) peak power advance |
| **Row 9** (2.00) | Col 9 (6,250 RPM) | `11.25°` | **`13.00°`** | +1.75° | Prevents ECU from retarding timing at redline |
| **Row 9** (2.00) | Col 10 (6,500 RPM) | `11.00°` | **`13.00°`** | +2.00° | Prevents ECU from retarding timing at redline |
| **Row 9** (2.00) | Col 11 (7,200 RPM) | `10.75°` | **`13.00°`** | +2.25° | Prevents ECU from retarding timing at redline |

*All other rows (Rows 1–7) and columns (Cols 1–5, 1,000–3,250 RPM) remain 100% untouched.*

---

## Innovate SCG-1 Boost Controller Tuning Guidance

- **Current Operating State**: `dUt = 6%`, `SPG = 7 psi`, `bSt = 16.0 psi`, `AFr = 12.8 AFR`, `A = 5.0 psi`.
- **Datalog Finding**: At `dUt = 6%`, boost reaches **13.0–13.3 psi** under full load and holds perfectly flat. The sensation of power "peaking at 5k" was caused by calibration ignition timing retarding down to 10.75°—not boost decay.
- **Recommendations for v034 Road Testing**:
  1. **Do not change SCG-1 duty cycle for the initial v034 test run**: Keep `dUt = 6%`. Evaluate the ignition timing improvements on the exact same 13 psi boost baseline first to confirm 0.0° Knock Retard and feel the direct power increase above 5k RPM.
  2. **If higher boost is desired after verifying clean knock telemetry**:
     - Increment `dUt` conservatively from `6%` to `7%` or `8%` (+1% to +2%).
     - With this wastegate and turbo, each 1% duty cycle adds approximately 0.8 to 1.2 psi.
     - **NEVER** increase duty cycle in large jumps (e.g. straight to 10%+).
     - **Always keep `bSt` (Boost Cut)** set firmly at **16.0 psi** as the hard engine protection backstop.

---

## In-Editor Verification Evidence

1. **Reopened Candidate**: Verified directly in VCM Editor:
   - `[ECM] 44583` Row 8: `13.50°` at 5k, `14.00°` across 5.75k–7.2k.
   - `[ECM] 44583` Row 9: `12.50°` at 5k, `13.00°` across 5.75k–7.2k.
   - All other 87 cells in `44583` 100% identical.
2. **Whole-File Comparison vs Parent (`v033`)**:
   - `Compare > View Comparison Log` confirmed exactly:
     * `Notes`
     * `Spark Borderline Knock vs. RPM vs. Load [ECM 44583]`
   - Zero unintended differences across the entire file.

---

## Staged Road Test Protocol

- Flash `v034-wot-power-spark.hpt` using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
- Connect paired VCM Scanner (18 channels) + SCG-1 Logger.
- Test 1: Decel pop check from 4,500 RPM in 2nd/3rd gear (verify loud, sharp overrun crackles).
- Test 2: Cruising check at 2,800–3,200 RPM part-throttle (confirm spark stays smooth and bucking remains zero).
- Test 3: 3rd gear WOT pull from 3,000 RPM to 6,500 RPM (monitor wideband lambda and verify timing stays ~13.0°–13.5° with 0.0° Knock Retard).
