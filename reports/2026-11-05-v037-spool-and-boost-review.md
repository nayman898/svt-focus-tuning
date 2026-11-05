# v037 Spool-Advance & Boost Review — 2026-11-05

**Decision**: Accept candidate **v037** as the verified production calibration baseline. 

## Summary of Results
Following the regression test of v036 (where zeroing all boost rows eliminated thermal reversion but introduced a 2.01s spool delay), candidate **v037** restored moderate intake cam advance (-15° to -30°) across 1,000–3,500 RPM while strictly preserving the 0.00° high-RPM lockout across 4,500–7,200 RPM.

Testing was conducted across three staged boost controller passes:
1. **Pass 1 (8% WGDC)**: `paired-20261105-175422-6cbce4b6-v037`
   - Peak Boost: **15.72 psi**
   - Peak MAF: **35.35 lb/min**
   - Wideband AFR: 10.67–11.25 AFR (mean 10.92 AFR)
   - ECT: 192.0°F → 194.0°F (+2.0°F net rise)
   - Spool: Immediate recovery of dynamic low-end compression.
2. **Pass 2 (10% WGDC, 19.5 psi Cap)**: `paired-20261105-180235-971d7164-v037-10wgdc-19dot5cap`
   - Peak Boost: **15.89 psi** (sustained plateau across 5,200–6,700 RPM)
   - Wideband AFR: 10.51–11.33 AFR (mean 10.97 AFR)
   - Fuel Pressure: 2.69V–2.92V stable
   - Knock Retard: 0.0°
3. **Pass 3 (12% WGDC, 19.5 psi Cap)**: `paired-20261105-180658-1e20916e-v037-12wgdc`
   - Peak Boost: **17.31 psi** (15.5–16.2 psi sustained)
   - Peak MAF: **35.63 lb/min** (~380 crank bhp equivalent)
   - Spool Time (3,500 → 4,500 RPM): **2.12 seconds** (fastest acceleration on record)
   - Wideband AFR: 10.67–11.48 AFR (mean 11.07 AFR, 0.753 lambda)
   - Timing Advance: 11.2°–13.5° Base / MBT
   - Knock Retard: **0.0°**
   - ECT: **190.0°F → 192.0°F** (+2.0°F rise across full 17.3 psi sweep)

## Calibration Status
- **Low-RPM Spool**: Resolved. Dynamic compression restored at 2,000–3,500 RPM with -25° advance.
- **Top-End Thermal Protection**: Validated. Zero reversion of 1,500°F exhaust gas; ECT stays at 190°–192°F.
- **WOT Fueling**: Validated. Commanded lambda 0.76–0.77 delivers a protective 10.9–11.1 measured AFR cushion.
- **WOT Ignition**: Validated. Row 9 13.5° flat delivers knock-free MBT timing.
- **Idle & Low-Speed**: Validated. 900–950 RPM warm idle, anti-shuffle neutralized, loud decel crackle retained.
- **Boost Recommendation**: Lock Innovate SCG-1 at **12% WGDC** (~16.2–17.3 psi) for long-term engine longevity on 93 pump gas.

