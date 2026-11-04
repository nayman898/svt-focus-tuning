# v034 staged regression test

Candidate: [WOT High-RPM Power Spark Advance & Decel Overrun Restoration](../tunes/v034-wot-power-spark.md)
([`v034-wot-power-spark.hpt`](../tunes/v034-wot-power-spark.hpt)).  
Exact parent and immediate rollback: [v033](../tunes/v033-loud-crisp-pops.md)
([`v033-loud-crisp-pops.hpt`](../tunes/v033-loud-crisp-pops.hpt)).

## Scope of Calibration
Derived from `paired-20261104-123109-5f5905f7-v032-2` WOT pull telemetry and owner feedback:
1. **WOT Power Spark Advance**: Advances `[ECM] 44583` (Spark Borderline Knock) across 5,000–7,200 RPM in Row 8 (+1.5° to +2.0°) and Row 9 (+1.0° to +2.25°), eliminating the top-end timing drop from 13.2° down to 10.75° and allowing power to carry strongly past 5,000 RPM.
2. **Safe Clearance**: High-RPM timing advance under full boost (13.00°) stays safely 0.75° below MBT ceiling (13.75°).
3. **Preserves Safe Rich Fueling**: Keeps the ~10.5–10.8 AFR open-loop enrichment cushion intact for thermal and knock safety.
4. **Inherits Decel Overrun Pops**: Carries `[ECM] 44496` (1.40s) and `[ECM] 44605` (-8° at 3k, -10° at 4k–6k) for crisp, loud exhaust pops on overrun.
5. **Preserves Anti-Shuffle Neutralization**: Preserves `[ECM] 44771` Disabled and `[ECM] 44776` OSCMOD = 1.000 (zero cruising bucking).

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI4 connected (instance currently open with v034 vs. v033 comparison).
2. Open `tunes/v034-wot-power-spark.hpt`.
3. Compare against parent: `Compare > Open Compare File` -> select `tunes/v033-loud-crisp-pops.hpt`.
4. Verify diff: `Compare > View Comparison Log`. Ensure ONLY `Notes` and `Spark Borderline Knock vs. RPM vs. Load [ECM 44583]` changed.
5. Once verified, flash `v034-wot-power-spark.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
6. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
