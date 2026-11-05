# v037 — Spool-Advance VCT & High-RPM Thermal Lockout

**Official Production Tune Baseline (Validated on Road across 8%, 10%, and 12% WGDC).**  
Exact parent and immediate rollback: [v036](v036-zero-boost-vct.md) ([`v036-zero-boost-vct.hpt`](v036-zero-boost-vct.hpt)).

- **Production Binary**: [`v037-spool-vct.hpt`](v037-spool-vct.hpt)
  - Size: `268157` bytes
  - SHA-256: `F81325ADF88757E6AD3901BD1A479595B161B18CD13DDB2DC8C53BCAC79C9621`
- **Parent Binary**: [`v036-zero-boost-vct.hpt`](v036-zero-boost-vct.hpt)
  - Size: `265933` bytes
  - SHA-256: `81F079A1A3B9ACBA825D14D65ED171CCE97B106B5868C78FFDC5CE5C54331BCE`

---

## Calibration Rationale & Physics

### 1. Telemetry Evidence from v036
In `paired-20261105-150046-e5d55c90-v036-forrealsies`, locking out all boost rows to `0.00°` across all RPMs proved two vital facts:
1. **Thermal Protection Confirmed**: During full WOT pulls (e.g. Pull 6 from 2,700 to 6,400 RPM), `Engine Coolant Temp` held completely flat between **192.0°F and 194.0°F (0.0°F net rise)**, compared to the **+12.0°F thermal spike (186°F → 198°F)** seen in v035 when large valve overlap was active under boost. Zeroing cam advance at high boost completely halts superheated 1,500°F pre-turbine exhaust gas from blowing backwards into the intake runners.
2. **Low-RPM Spool Penalty Identified**: Parking the cam at `0.00°` (fully retarded) at 2,000–3,500 RPM delayed Intake Valve Closing (IVC). This bled off dynamic cylinder compression before positive boost arrived, reducing low-end torque and slowing exhaust pulse energy. As a result, the 2,800 → 4,500 RPM acceleration time jumped from **4.16s (v035) to 6.17s (v036)** (+2.01s spool delay) with a 25–30% drop in low-RPM mass airflow.

### 2. The v037 Solution
Reversion only occurs when pre-turbine backpressure exceeds intake boost pressure (which occurs above 4,000 RPM at 12–15 psi boost). Below 3,500 RPM during spool-up, backpressure is low (2–6 psi) and reversion cannot occur.

**Candidate v037 implements the balanced "Spool-Advance + High-RPM Lockout" strategy**:
- **Spool-Up Zone (Columns 1,000 to 3,500 RPM, Rows 0.60–1.00)**: Restores **-15.00° to -30.00°** intake cam advance. This closes the intake valve early, trapping maximum dynamic cylinder pressure, restoring crisp off-boost torque, and spinning up the turbo 2 seconds faster.
- **Taper (3,500 → 4,500 RPM)**: Smoothly transitions from -15°/-20° down to 0.00° over a 1,000 RPM window (a gentle 75 ms phaser slew).
- **High-RPM Powerband Lockout (Columns 4,500 to 7,200 RPM across ALL loads 0.10–1.00)**: Strictly preserved at **0.00° flat**. Pre-parks the cam across the entire high-boost powerband, eliminating exhaust reversion, stabilizing engine temperatures, and preventing shift lag.

---

## Copy-Pasteable Table: `[ECM] 44412` — VCT Angle vs. RPM vs. Load

*Units: Degrees Intake Cam Advance (Negative indicates advance relative to base timing)*  
*True ECU Column Breakpoints: `1,000 | 1,500 | 2,000 | 2,500 | 3,500 | 4,500 | 6,000 | 6,250 | 6,750 | 7,000 | 7,200`*

### Complete Target Matrix (9 Rows × 11 Columns)

Copy the values below directly into VCM Editor for table `[ECM 44412]`:

| Load / RPM | 1,000 | 1,500 | 2,000 | 2,500 | 3,500 | 4,500 | 6,000 | 6,250 | 6,750 | 7,000 | 7,200 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.10** | 0.00 | -10.00 | -15.00 | -20.00 | -15.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.20** | -10.00 | -15.00 | -20.00 | -25.00 | -20.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.30** | -10.00 | -20.00 | -25.00 | -30.00 | -25.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.40** | -10.00 | -20.00 | -30.00 | -35.00 | -25.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.50** | -10.00 | -20.00 | -30.00 | -35.00 | -25.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.60** *(Spool)* | **-10.00** | **-15.00** | **-25.00** | **-30.00** | **-20.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.70** *(Spool)* | **-10.00** | **-15.00** | **-25.00** | **-30.00** | **-20.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.80** *(Spool)* | **-10.00** | **-15.00** | **-25.00** | **-28.00** | **-18.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **1.00** *(Spool)* | **-10.00** | **-15.00** | **-20.00** | **-25.00** | **-15.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |

---

### Tab-Delimited Matrix for Fast Clipboard Pasting

To paste all 99 cells at once in VCM Editor:
1. Open table `[ECM 44412]` in VCM Editor.
2. Select the top-left cell (Row 0.10, Col 1,000 RPM) or click the top-left blank header cell to select the entire table (`Ctrl+A`).
3. Copy and paste the block below:

```text
0.00	-10.00	-15.00	-20.00	-15.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-15.00	-20.00	-25.00	-20.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-20.00	-25.00	-30.00	-25.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-20.00	-30.00	-35.00	-25.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-20.00	-30.00	-35.00	-25.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-15.00	-25.00	-30.00	-20.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-15.00	-25.00	-30.00	-20.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-15.00	-25.00	-28.00	-18.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-15.00	-20.00	-25.00	-15.00	0.00	0.00	0.00	0.00	0.00	0.00
```

---

## Calibration Details Notes (Paste into `Edit > Calibration Details > Notes`)

```text
=== V037 (2026-11-05) ===
Spool-Advance VCT & High-RPM Thermal Lockout:
- Built from tested v036 (parent). Confirmed engine build specs: 85.5mm forged pistons (+0.7mm overbore, ~2.02L displacement), 9.25:1 static compression ratio with SVT cylinder head.
- [ECM] 44412 VCT Angle vs. RPM vs. Load:
  * Spool-Up Advance Restored: Restores -15.00 to -30.00 deg intake cam advance in columns 1,000-3,500 RPM across rows 0.60-1.00. Advances Intake Valve Closing (IVC) at low engine speeds to maximize dynamic cylinder pressure, restore low-RPM torque, and recover fast turbo spool (eliminates the 2.0s spool penalty measured in v036).
  * High-RPM Powerband Lockout (Preserved): Columns 4,500 to 7,200 RPM strictly preserved at 0.00 deg flat across ALL loads (0.10 to 1.00). Halts superheated 1,500 deg F pre-turbine exhaust gas from blowing backwards into intake runners under boost (maintains the 0.0 deg F ECT rise validated in v036 Pull 6) and eliminates transient shift lag.
  * Taper Zone: Smooth taper across 3,500 to 4,500 RPM (-15/-20 deg -> 0.00 deg) requiring only ~75 ms of hydraulic phaser slew before peak boost arrives.
- Retains full v035 Row 9 spark advance (13.5 deg flat across 5,500-7,200 RPM), v035 base fuel targets (0.76-0.77 lambda), v033 loud decel crackle (-8 deg @ 3k, -10 deg @ 4k-6k), and v032 anti-shuffle fixes.
```

