# v037 staged regression test

Candidate: [Spool-Advance VCT & High-RPM Thermal Lockout](../tunes/v037-spool-vct.md)
([`v037-spool-vct.hpt`](../tunes/v037-spool-vct.hpt)).  
Exact parent and immediate rollback: [v036](../tunes/v036-zero-boost-vct.md)
([`v036-zero-boost-vct.hpt`](../tunes/v036-zero-boost-vct.hpt)).

## Scope of Calibration
Derived from `paired-20261105-150046-e5d55c90-v036-forrealsies` telemetry review:
1. **Restores Low-RPM Spool-Up Advance (1,000–3,500 RPM)**: Restores **-15.00° to -30.00°** intake cam advance in rows 0.60–1.00 between 1,000 and 3,500 RPM. Eliminates the 2.01s spool lag and 25–30% low-end airflow deficit measured in v036 by closing the intake valve early (early IVC) to trap dynamic cylinder compression before boost builds.
2. **Preserves High-RPM Powerband Lockout (4,500–7,200 RPM)**: Retains **0.00° flat across ALL loads** (0.10–1.00) from 4,500 to 7,200 RPM. Maintains the 0.0°F ECT rise validated in v036 Pull 6, prevents pre-turbine exhaust gas reversion, and eliminates shift lag.
3. **Preserves v035 MBT Spark & WOT Fueling**: Retains Row 9 spark at 13.5° flat across 5,500–7,200 RPM and base fuel targets of 0.76–0.77 lambda.
4. **Preserves Decel Overrun Crackles**: Retains 1.40s DFCO delay and -8° to -10° negative spark on decel.

## Owner Pre-Flash Verification & Safety
> [!IMPORTANT]
> The vehicle owner performs all ECU writes. The assistant NEVER initiates an ECU write, readback, DTC clear, or adaptation reset.

1. Open VCM Editor on desk PC with MPVI connected.
2. Open `tunes/v037-spool-vct.hpt`.
3. Enter `[ECM 44412]` values matching the matrix in `tunes/v037-spool-vct.md`.
4. Compare against parent: `Compare > Open Compare File` -> select `tunes/v036-zero-boost-vct.hpt`.
5. Verify diff: `Compare > View Comparison Log`. Ensure ONLY `Notes` and `VCT Angle vs. RPM vs. Load [ECM 44412]` (exactly 20 cells changed in rows 0.50–1.00 at 1,000–3,500 RPM) are listed.
6. Once verified, flash `v037-spool-vct.hpt` to vehicle using VCM Editor (`Flash > Write Vehicle` - Calibration Only).
7. Keep Innovate SCG-1 set at **8% WGDC (~14.5–15.0 psi)** for direct comparison against v036 Pull 6.
8. Record paired datalog using the trimmed VCM Scanner channel set + SCG-1 Logger.

