# v035 staged regression test

Candidate: [WOT Fuel Enleanment & Spark Power Advance Optimization](../tunes/v035-wot-fuel-spark-power.md)
([`v035-wot-fuel-spark-power.hpt`](../tunes/v035-wot-fuel-spark-power.hpt)).  
Exact parent and immediate rollback: [v034](../tunes/v034-wot-power-spark.md)
([`v034-wot-power-spark.hpt`](../tunes/v034-wot-power-spark.hpt)).

## Scope of Calibration
Derived from `paired-20261104-160338-a0c65d0c-v034` telemetry review and owner feedback:
1. **WOT Fuel Enleanment**: Leans `[ECM] 44511` (Fuel Base vs. RPM vs. TPS) Rows 6 and 7 from 0.74 lambda (~10.5 AFR) to 0.76–0.77 lambda (~11.2–11.4 AFR actual) across 4,000–7,400 RPM, accelerating flame front propagation and eliminating high-RPM rich quench.
2. **Spark Power Advance to MBT**: Advances `[ECM] 44583` (Spark Borderline Knock) Row 9 (2.00 Load / Boost) by +0.50° (5,000 RPM -> 13.00°, 5,750–7,200 RPM -> 13.50°), matching the MBT optimum knee with zero knock retard detected in v034.
3. **Inherits Decel Overrun Crackles**: Preserves `[ECM] 44496` (1.40s) and `[ECM] 44605` (-8° at 3k, -10° at 4k–6k) for crisp, loud exhaust pops on overrun.
4. **Preserves Anti-Shuffle Neutralization**: Preserves `[ECM] 44771` Disabled and `[ECM] 44776` OSCMOD = 1.000.

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI4 connected (instance currently open with v035 vs. v034 comparison).
2. Open `tunes/v035-wot-fuel-spark-power.hpt`.
3. Compare against parent: `Compare > Open Compare File` -> select `tunes/v034-wot-power-spark.hpt`.
4. Verify diff: `Compare > View Comparison Log`. Ensure ONLY `Notes`, `Fuel Base vs. RPM vs. TPS [ECM 44511]`, and `Spark Borderline Knock vs. RPM vs. Load [ECM 44583]` changed.
5. Once verified, flash `v035-wot-fuel-spark-power.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
6. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
