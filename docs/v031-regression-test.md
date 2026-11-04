# v031 staged regression test

Candidate: [Smooth Low-RPM Drivability & Crisp High-RPM Decel Pops](../tunes/v031-smooth-drivability-crisp-pop.md)
([`v031-smooth-drivability-crisp-pop.hpt`](../tunes/v031-smooth-drivability-crisp-pop.hpt)).  
Exact parent and immediate rollback: [v030](../tunes/v030-smooth-tipin-enhanced-pop.md)
([`v030-smooth-tipin-enhanced-pop.hpt`](../tunes/v030-smooth-tipin-enhanced-pop.hpt)).

## Scope of Calibration
Derived from paired-20261104-075425-a8636a50-v030 log analysis: (1) Completely disables Tip-In Torque Control spark chops by raising [ECM] 44607 to 7,500 RPM, eliminating the 2,400 RPM oscillation boundary that caused 561 torque-cut chops; (2) Shortens [ECM] 44496 DFCO delay from 1.75s to 0.90s for a concise, punchy pop burst; (3) Re-cushions [ECM] 44605 decel spark at 2,000 RPM (+10.0 deg) and 3,000 RPM (+2.0 deg) to prevent tip-in bogging, while deepening 4,000-6,000 RPM to -8.0 deg ATDC for louder, sharper pops on overrun; (4) Trims [ECM] 12163 MAF Columns 14-17 by -2.5% to zero out cruising STFT.

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI4 connected.
2. Open `tunes/v031-smooth-drivability-crisp-pop.hpt`.
3. Compare against parent: `Compare > Open Compare File` -> select `tunes/v030-smooth-tipin-enhanced-pop.hpt`.
4. Verify diff: `Compare > View Comparison Log`. Ensure ONLY expected parameters changed.
5. Once verified, flash `v031-smooth-drivability-crisp-pop.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
6. Record paired datalog using 18-channel VCM Scanner + SCG-1 Logger.
