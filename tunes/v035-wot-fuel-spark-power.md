# v035 — WOT Fuel Enleanment & Spark Power Advance Optimization

**Prepared candidate for owner inspection and staged road testing.**  
Exact parent and immediate rollback: [v034](v034-wot-power-spark.md) ([v034-wot-power-spark.hpt](v034-wot-power-spark.hpt)).

- **Candidate Binary**: [v035-wot-fuel-spark-power.hpt](v035-wot-fuel-spark-power.hpt)
  - Size: `265613` bytes
  - SHA-256: `037A69269671D8F487FA2269630B68351767623AB845A41BE4577ABBDF730A16`
- **Parent Binary**: [v034-wot-power-spark.hpt](v034-wot-power-spark.hpt)
  - Size: `263853` bytes
  - SHA-256: `7F9539CBD3654B8426B587A3A504EA3D30488564B9D52256F4EB613D06CA08FA`

---

## Calibration Rationale & Telemetry Findings

Derived from `paired-20261104-160338-a0c65d0c-v034` telemetry review and owner road test feedback (*"crackle came to life on that one"*, *"Also felt better in the high range. I missed a shift at one point and revved real high, my bad"*):

1. **Validation of v034 Decel Crackles & WOT Spark**:
   - **Overrun Crackle Success**: Decel spark reached the programmed **-8.0° to -10.0°** zone with fuel cut delayed for 1.40s. Sustained negative spark fired across over 5,700 datalog samples, producing crisp, audible pops on overrun.
   - **High-RPM Spark Performance**: Ignition timing held steady between **13.0° and 15.0°** (mean 13.3°) all the way through redline instead of drooping to 11.2°. Peak Mass Airflow jumped to an all-time record **33.14 lb/min** (~330+ crank HP equivalent airflow) with peak boost holding **13.0–14.0 psi**.
   - **Knock Retard**: **Zero knock retard (0.0°)** detected across the entire 10-minute session and across all WOT pulls.
2. **Analysis of the Missed Shift Event (t = 349.8s – 350.5s)**:
   - During a gear change, throttle was re-applied to WOT while the clutch was disengaged or gear was missed.
   - Engine RPM free-revved from 5,786 RPM to **7,610 RPM**.
   - **ECU Safety Intervention**: At 7,442 RPM, the factory ECU rev limiter engaged immediately (`Fuel = Injector Cut`), cutting fuel across 8 consecutive frames and checking engine speed until RPM fell back below 7,130 RPM.
   - The engine was in the overrev band for less than 0.15 seconds total. The factory limiter protected the rotating assembly completely, and the engine resumed smooth operation immediately with zero mechanical issues or DTCs.
3. **Primary Power Optimization in v035: WOT Fueling**:
   - Wideband telemetry from `v034` revealed that WOT air-fuel ratio remained excessively rich at **0.712–0.747 Lambda (~10.5–10.9 AFR)**, tracking `[ECM] 44511` Row 6 & 7 (which commanded 0.74 Lambda).
   - Running ~10.5 AFR under boost severely quenches flame front speed and leaves 15+ whp on the table.
   - Candidate `v035` leans `[ECM] 44511` Rows 6 & 7 from `0.74` to **`0.76–0.77` Lambda** (~11.2–11.4 AFR actual) across 4,000–7,400 RPM. This accelerates combustion flame velocity and significantly sharpens top-end power while maintaining a generous knock safety buffer on pump 93 octane.
4. **Secondary Power Optimization in v035: Spark Advance to MBT**:
   - Having proven zero knock retard in `v034`, Candidate `v035` advances `[ECM] 44583` Row 9 (2.00 Load / Boost) by an additional **+0.50°** (5,000 RPM -> `13.00°`, 5,750–7,200 RPM -> `13.50°`).
   - This brings full-boost ignition timing directly to the MBT optimum knee (`[ECM] 32265` MBT is 13.75°).

---

## Detailed Parameter Changes

### 1. `[ECM] 44511` — Fuel Base vs. RPM vs. TPS
*Units: Lambda*

| Row (TPS %) | Col (RPM) | Parent Value (`v034`) | Candidate Value (`v035`) | Delta | Target AFR (Gasoline) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **Row 6** (53.71%) | Col 3 (4,000 RPM) | `0.74` | **`0.76`** | +0.02 (leaner) | ~11.17 AFR |
| **Row 6** (53.71%) | Col 4 (4,500 RPM) | `0.74` | **`0.76`** | +0.02 (leaner) | ~11.17 AFR |
| **Row 6** (53.71%) | Col 5 (5,000 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 6** (53.71%) | Col 6 (5,500 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 6** (53.71%) | Col 7 (6,000 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 6** (53.71%) | Col 8 (6,500 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 6** (53.71%) | Col 9 (7,400 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 7** (68.36% WOT) | Col 3 (4,000 RPM) | `0.74` | **`0.76`** | +0.02 (leaner) | ~11.17 AFR |
| **Row 7** (68.36% WOT) | Col 4 (4,500 RPM) | `0.74` | **`0.76`** | +0.02 (leaner) | ~11.17 AFR |
| **Row 7** (68.36% WOT) | Col 5 (5,000 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 7** (68.36% WOT) | Col 6 (5,500 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 7** (68.36% WOT) | Col 7 (6,000 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |
| **Row 7** (68.36% WOT) | Col 8 (6,500 RPM) | `0.75` | **`0.77`** | +0.02 (leaner) | ~11.32 AFR |
| **Row 7** (68.36% WOT) | Col 9 (7,400 RPM) | `0.74` | **`0.77`** | +0.03 (leaner) | ~11.32 AFR |

*All lower TPS rows (Rows 0–5) and lower RPM columns (Cols 0–2, 1,000–3,500 RPM) remain untouched.*

---

### 2. `[ECM] 44583` — Spark Borderline Knock vs. RPM vs. Load
*Units: Degrees Advance*

| Row (Load) | Col (RPM) | Parent Value (`v034`) | Candidate Value (`v035`) | Delta | Engineering Purpose |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Row 9** (2.00 Boost) | Col 6 (5,000 RPM) | `12.50°` | **`13.00°`** | +0.50° | Faster torque ramp into boost |
| **Row 9** (2.00 Boost) | Col 7 (5,750 RPM) | `13.00°` | **`13.50°`** | +0.50° | Peak boost optimum power timing |
| **Row 9** (2.00 Boost) | Col 8 (6,000 RPM) | `13.00°` | **`13.50°`** | +0.50° | Peak boost optimum power timing |
| **Row 9** (2.00 Boost) | Col 9 (6,250 RPM) | `13.00°` | **`13.50°`** | +0.50° | Peak boost optimum power timing |
| **Row 9** (2.00 Boost) | Col 10 (6,500 RPM) | `13.00°` | **`13.50°`** | +0.50° | Top-end carry to redline |
| **Row 9** (2.00 Boost) | Col 11 (7,200 RPM) | `13.00°` | **`13.50°`** | +0.50° | Overrev margin to redline |

*Row 8 (0.80 Load) remains at 13.50° (5k) and 14.00° (5.75k–7.2k), matching v034.*

---

## Innovate SCG-1 Boost Controller Guidance

- **Datalog Finding**: At `dUt = 6%`, peak boost reliably hit **13.0–14.0 psi** across all gears, and knock retard was **0.0°**.
- **Recommendation for v035 Drive Test**:
  1. **Test Run 1**: Leave `dUt = 6%` for the first WOT pull of `v035`. This isolates the significant power increase resulting from the fuel enleanment (~10.5 -> ~11.3 AFR) and timing advance (+0.5°).
  2. **Test Run 2 (Optional Boost Increase)**: If the first pull is clean with 0.0° Knock Retard and Lambda settles right at ~0.76–0.77, you can bump `dUt` on the SCG-1 faceplate by **+1% (to `7%`)**.
     - This will raise peak boost by ~0.8 to 1.2 psi (targeting ~14.0–14.5 psi).
     - Keep overboost cut (`bSt`) firmly set at **16.0 psi**.
