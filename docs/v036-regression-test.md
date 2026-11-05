# v036 staged regression test

Candidate: [Zero-Boost & High-RPM VCT Angle Lockout](../tunes/v036-zero-boost-vct.md)
([`v036-zero-boost-vct.hpt`](../tunes/v036-zero-boost-vct.hpt)).  
Exact parent and immediate rollback: [v035](../tunes/v035-wot-fuel-spark-power.md)
([`v035-wot-fuel-spark-power.hpt`](../tunes/v035-wot-fuel-spark-power.hpt)).

## Scope of Calibration
Derived from `paired-20261105-104453-2eb3afbb-v035` telemetry review and confirmed built engine specs (85.5mm forged pistons, ~2.02L displacement, 9.25:1 static compression ratio):
1. **Intake Cam Overlap Elimination Under Boost (Rows 0.70–1.00)**: Zeros out `[ECM] 44412` (VCT Angle vs. RPM vs. Load) across boost rows 0.70, 0.80, and 1.00 (`0.00°` across 1,000–7,200 RPM) and tapers row 0.60 (`-10°` to `-15°` max). Stops high-temperature (1,500°F) pre-turbine exhaust gas from blowing backwards into the intake runners under boost, drastically reducing cylinder head, oil, and coolant temperatures.
2. **High-RPM Powerband Lockout (Columns 4,500–7,200 RPM)**: Zeros out `[ECM] 44412` flat to `0.00°` across all load rows (0.10–1.00) from 4,500 to 7,200 RPM. Eliminates hydraulic phaser slew lag (200–300 ms) and shift reversion hesitation during rapid gear changes.
3. **Preserves Off-Boost Cruise VCT (Columns 1,000–3,500 RPM, Rows 0.10–0.50)**: Maintains smooth dynamic advance (-10° to -35° max) for rapid spool-up, crisp throttle response, and highway fuel economy.
4. **Preserves v035 MBT Spark & WOT Fueling**: Retains Row 9 spark at 13.5° flat across 5,500–7,200 RPM (0.0° knock retard validated) and base fuel targets of 0.76–0.77 lambda.
5. **Preserves Decel Overrun Crackles**: Retains 1.40s DFCO delay and -8° to -10° negative spark on decel.

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI connected.
2. Open `tunes/v036-zero-boost-vct.hpt`.
3. Verify or enter `[ECM 44412]` values matching the guide in `tunes/v036-zero-boost-vct.md`.
4. Compare against parent: `Compare > Open Compare File` -> select `tunes/v035-wot-fuel-spark-power.hpt`.
5. Verify diff: `Compare > View Comparison Log`. Ensure ONLY `Notes` and `VCT Angle vs. RPM vs. Load [ECM 44412]` (60 cells changed) are listed.
6. Once verified, flash `v036-zero-boost-vct.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
7. Keep Innovate SCG-1 set at **8% WGDC (~14.5–15.0 psi)** for initial back-to-back thermal and airflow comparison against v035 Pull 3.
8. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.

## Test Protocol & Logging Guidance
1. **Engine Warmup**: Drive normally until ECT reaches 180°F–195°F. Confirm A/C is OFF.
2. **DFCO Re-Engagement Tip-In Technique**: Before starting a 3rd gear pull, avoid stomping 0% to 100% throttle out of deep coasting DFCO. Apply 10–20% throttle for 0.5–1.0s to wake injectors, wet runner walls, and pre-spool turbo before committing to 100% WOT.
3. **WOT Pull Execution**: In 3rd gear, roll into 100% WOT from 2,800 RPM and pull cleanly to 6,800–7,000 RPM.
4. **Stop Conditions (Immediate Abort)**:
   - Knock Retard > 2.0° under boost.
   - Wideband AFR > 12.0:1 (Lambda > 0.82) under boost > 8 psi.
   - Boost spikes > 15.5 psi.
   - ECT > 220°F or rapid unexplained coolant temperature spike.
