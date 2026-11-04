# v032 staged regression test

Candidate: [Kill Cruising Spark Oscillation & Restore Crisp Overrun Pops](../tunes/v032-kill-oscillation-crisp-pops.md)
([`v032-kill-oscillation-crisp-pops.hpt`](../tunes/v032-kill-oscillation-crisp-pops.hpt)).  
Exact parent and immediate rollback: [v031](../tunes/v031-smooth-drivability-crisp-pop.md)
([`v031-smooth-drivability-crisp-pop.hpt`](../tunes/v031-smooth-drivability-crisp-pop.hpt)).

## Scope of Calibration
Derived from paired-20261104-095419-1f8e78f4-v031-drive log analysis: (1) Permanently disables [ECM] 44771 Torque Oscillation Module and sets [ECM] 44776 Row 14 OSCMOD / Anti-Shuffle to 1.000 to eliminate the 12-15 Hz rapid spark chop limit cycle (24 deg <-> 4 deg) observed at 5:38 (t=340s); (2) Confirms [ECM] 44607 Tip-In Torque Control RPM Min raised to 7,500 RPM; (3) Extends [ECM] 44496 DFCO delay from 0.90s to 1.35s to widen the post-lift overrun pop window from ~300ms to ~850ms; (4) Calibrates [ECM] 44605 Spark Decel 3,000 RPM cell to -3.00 deg ATDC (Row 4 & 5) to restore crisp pops across typical 2,800-3,800 RPM driving coast-downs while keeping 4k-6k at -8.00 deg for loud crackles and 2k cushioned at +8.00 deg. Preserves v031 MAF -2.5% cruising trim centering.

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI4 connected.
2. Open `tunes/v032-kill-oscillation-crisp-pops.hpt`.
3. Compare against parent: `Compare > Open Compare File` -> select `tunes/v031-smooth-drivability-crisp-pop.hpt`.
4. Verify diff: `Compare > View Comparison Log`. Ensure ONLY expected parameters changed.
5. Once verified, flash `v032-kill-oscillation-crisp-pops.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
6. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
