# v033 staged regression test

Candidate: [Loud Crisp Overrun Pops Across Mid/High RPM](../tunes/v033-loud-crisp-pops.md)
([`v033-loud-crisp-pops.hpt`](../tunes/v033-loud-crisp-pops.hpt)).  
Exact parent and immediate rollback: [v032](../tunes/v032-kill-oscillation-crisp-pops.md)
([`v032-kill-oscillation-crisp-pops.hpt`](../tunes/v032-kill-oscillation-crisp-pops.hpt)).

## Scope of Calibration
Derived from paired v032 drive logs (`paired-20261104-122527-75371a04-v032` and `paired-20261104-123109-5f5905f7-v032-2`):
1. **Bucking/Spark Oscillation Confirmed Solved**: Torque Control spark cuts fell from 881 samples in v031 to 0 samples across both test runs. Cruising bucking at 5:38 is completely eradicated.
2. **Deepen Overrun Retard**: Deepens `[ECM] 44605` 3,000 RPM cell to `-8.00°` ATDC (was `-3.00°`) and 4,000–6,000 RPM to `-10.00°` ATDC (was `-8.00°`) for sharp, loud, acoustic crackles on coast-down.
3. **Smooth Return to Idle**: Lowers 2,000 RPM from `+8.00°` to `+2.00°` to eliminate premature positive timing pull during coast-down while cushioning idle drop.
4. **Extend Overrun Fuel**: Extends `[ECM] 44496 DFCO Closed Throttle Delay` from `1.35 s` to `1.40 s` (+50ms) to widen overrun fuel duration.
5. **Preserves Base**: Keeps v032 anti-shuffle fixes and v031 MAF trim.

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI4 connected (instance currently open with v033 vs. v032 comparison).
2. Open `tunes/v033-loud-crisp-pops.hpt`.
3. Compare against parent: `Compare > Open Compare File` -> select `tunes/v032-kill-oscillation-crisp-pops.hpt`.
4. Verify diff: `Compare > View Comparison Log`. Ensure ONLY `Notes`, `DFCO Closed Throttle Delay [ECM 44496]`, and `Spark Decel vs. RPM vs. ECT [ECM 44605]` changed.
5. Once verified, flash `v033-loud-crisp-pops.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
6. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
