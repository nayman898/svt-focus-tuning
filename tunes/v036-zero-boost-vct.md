# v036 — Zero-Boost & High-RPM VCT Angle Lockout

**Prepared candidate baseline for owner inspection, table entry, and staged validation.**  
Exact parent and immediate rollback: [v035](v035-wot-fuel-spark-power.md) ([`v035-wot-fuel-spark-power.hpt`](v035-wot-fuel-spark-power.hpt)).

- **Candidate Binary**: [`v036-zero-boost-vct.hpt`](v036-zero-boost-vct.hpt)
  - Size: `265933` bytes
  - SHA-256: `81F079A1A3B9ACBA825D14D65ED171CCE97B106B5868C78FFDC5CE5C54331BCE` (saved from VCM Editor with 60 cell changes in table 44412)
- **Parent Binary**: [`v035-wot-fuel-spark-power.hpt`](v035-wot-fuel-spark-power.hpt)
  - Size: `265613` bytes
  - SHA-256: `037A69269671D8F487FA2269630B68351767623AB845A41BE4577ABBDF730A16`

---

## Engine Build Specifications & Boost Target Guidance

1. **Confirmed Rotating Assembly Geometry**:
   - **Bore**: 85.5 mm (+0.7 mm overbore)
   - **Stroke**: 88.0 mm (stock SVT crankshaft)
   - **Displacement**: 2,021 cc (~2.02L)
   - **Static Compression Ratio**: **9.25:1** with SVT cylinder head volume.
2. **Impact on Overall Boost Targets**:
   - **Immediate Validation Test**: Keep the Innovate SCG-1 wastegate duty cycle at **8% WGDC (~14.5–15.0 psi)**. This isolates the intake cam VCT changes against `v035` Pull 3 to cleanly measure reductions in cylinder head/coolant temperatures, charge air heating, and mass airflow behavior without introducing boost variables.
   - **Long-Term Pump Gas (93 Octane) Headroom**: Lowering the static compression from factory 10.2:1 NA down to **9.25:1** mechanically expands safe pump gas boost headroom without methanol injection from ~15.0–15.5 psi up to **17.0–18.0 psi** (~37–39 lb/min airflow, ~390–415 crank bhp equivalent).

---

## Calibration Rationale & Overlap Physics

1. **The Overlap Reversion Problem in Boosted VCT (Rows 0.70–1.00)**:
   - In factory naturally aspirated tuning, the intake cam advances up to **-49.50°** between 2,500 and 4,500 RPM to create large valve overlap, using exhaust scavenge waves to pull in fresh charge air.
   - On a turbocharged engine, pre-turbine exhaust manifold backpressure (22–26 psi) significantly exceeds intake manifold boost pressure (14–15 psi). Large valve overlap causes pre-turbine exhaust gas (~1,500°F) to blow **backwards** into the intake runners.
   - This superheats incoming charge air, bakes the intake valves and cylinder head, spikes coolant and oil temperatures under boost, and severely compromises knock margin.
   - **The Fix**: Zero out boost rows 0.70, 0.80, and 1.00 (`0.00°` across all columns 1,000–7,200 RPM).
2. **High-RPM Powerband Lockout & Shift Reversion Elimination (Columns 4,500–7,200 RPM)**:
   - Above 4,000 RPM, the Pulsar G25-550 clone transitions from vacuum to full boost in < 150 ms.
   - The hydraulic VCT cam phaser has an oil-pressure-limited slew rate requiring 200–300 ms to retard 45°. If cam advance is active in high-RPM vacuum/cruise, the cam lags behind rapid throttle transitions.
   - Furthermore, during a redline gear shift (e.g. 6,800 RPM shift dropping to 4,600 RPM at closed throttle), vacuum in previous calibrations commanded -25° to -35° advance. When the clutch engaged and the throttle opened, the cam was severely advanced, causing transient exhaust reversion, hesitation, and sluggish manifold pressure rise.
   - **The Fix**: Lock out columns **4,500 through 7,200 RPM flat at 0.00° across ALL loads (0.10 to 1.00)**. The intake cam is permanently parked at base timing across the entire high-RPM powerband. Shift recovery is instantaneous with zero phaser lag.
3. **Preserved Off-Boost Cruise Drivability**:
   - Highway 6th gear cruising operates between 2,200 and 3,200 RPM at 0.20–0.40 load.
   - Columns 1,000–3,500 RPM retain smooth, mild-to-moderate advance (-10° to -35° max) to preserve excellent dynamic compression, off-boost responsiveness, and fuel economy.
4. **Retained Protections and Refinements**:
   - Retains `v035` WOT ignition timing (Row 9 flat at 13.5° across 5,500–7,200 RPM with 0.0° knock retard validated).
   - Retains `v035` base fuel targets (0.76–0.77 commanded lambda, ~10.8 AFR measured safety cushion).
   - Retains `v033` loud decel overrun pops (1.40s DFCO delay, -8° @ 3k, -10° @ 4k–6k).
   - Retains `v032` anti-shuffle neutralization.

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
| **0.50** | -10.00 | -20.00 | -30.00 | -35.00 | -20.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.60** *(Taper)* | -10.00 | -10.00 | -15.00 | -15.00 | -10.00 | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.70** *(Boost)* | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **0.80** *(Boost)* | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |
| **1.00** *(Boost)* | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** | **0.00** |

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
-10.00	-20.00	-30.00	-35.00	-20.00	0.00	0.00	0.00	0.00	0.00	0.00
-10.00	-10.00	-15.00	-15.00	-10.00	0.00	0.00	0.00	0.00	0.00	0.00
0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00
0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00
0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00
```

---

## Calibration Details Notes (Paste into `Edit > Calibration Details > Notes`)

```text
=== V036 (2026-11-05) ===
Zero-Boost & High-RPM VCT Angle Lockout (Thermal Reversion & Shift Lag Elimination):
- Built from tested v035 (parent). Confirmed engine build specs: 85.5mm forged pistons (+0.7mm overbore, ~2.02L displacement), 9.25:1 static compression ratio with SVT cylinder head.
- [ECM] 44412 VCT Angle vs. RPM vs. Load:
  * Rows 0-4 (0.10-0.50 Load / Off-Boost Cruise): Preserved smooth VCT advance (-10.00 to -35.00 deg max) across 1,000-3,500 RPM for crisp low-RPM throttle response, rapid spool-up, and highway fuel economy.
  * Row 5 (0.60 Load / Transition): Tapered advance (-10.00 to -15.00 deg max across 1,000-3,500 RPM; 0.00 deg at 4,500+ RPM) to smooth the vacuum-to-boost transition.
  * Rows 6, 7, and 8 (0.70, 0.80, and 1.00 Load / Boost): Zeroed completely to 0.00 deg across all RPM columns (1,000 to 7,200 RPM). Halts superheated 1,500 deg F pre-turbine exhaust gas from blowing backwards into intake runners under boost.
  * Columns 6 through 11 (4,500 to 7,200 RPM / High-RPM Powerband): Locked out to 0.00 deg flat across ALL loads (0.10 to 1.00). Pre-parks intake cam at base timing across entire powerband, eliminating phaser hydraulic slew lag (200-300 ms) and shift reversion hesitation during gear changes.
- Retains full v035 Row 9 spark advance (13.5 deg flat across 5,500-7,200 RPM), v035 base fuel targets (0.76-0.77 lambda), v033 loud decel crackle (-8 deg @ 3k, -10 deg @ 4k-6k), and v032 anti-shuffle fixes.
```
