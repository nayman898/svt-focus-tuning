# v030 staged regression test

Candidate: [v030 Smooth Tip-In & Enhanced Safe Decel Pops](../tunes/v030-smooth-tipin-enhanced-pop.md)
([v030-smooth-tipin-enhanced-pop.hpt](../tunes/v030-smooth-tipin-enhanced-pop.hpt)).  
Exact parent and immediate rollback: [v029 Decel Pop Activation & Cruising Stutter Elimination](../tunes/v029-decel-pop-cruise-smooth.md)
([v029-decel-pop-cruise-smooth.hpt](../tunes/v029-decel-pop-cruise-smooth.hpt)).

`v030` addresses the findings from the `v029` road test review ([2026-11-03-v029-drive-review.md](../reports/2026-11-03-v029-drive-review.md)):
1. **Eliminate Low-RPM Tip-In Torque Snatch**: `[ECM] 44607` (Spark Tip-In Torque Control RPM Min):
   - In `v029`, tip-in torque control was active down to 775 RPM. Light throttle modulation between 1,200 and 2,400 RPM triggered severe 15°–17° timing chops (toggling between 23° and 6° four to five times within 0.7s), causing low-speed hesitation/bucking.
   - `v030` raises `[ECM] 44607` from `775` to **`2,400 RPM`**, disabling tip-in spark cuts during low-gear creeping and light acceleration while retaining full high-RPM torque protection.
2. **Bridge Low-Throttle MAF Lean Gap**: `[ECM] 12163` (MAF Airflow vs. Voltage):
   - In `v029`, cracking the throttle open from idle/coast (0.70V–0.88V MAF) produced lean excursions ($\lambda = 1.15–1.28$).
   - `v030` bumps Column 11 (`0.699V`) from `5.66 lb/h` (`0.0944 lb/min`) by +6.0% to **`6.00 lb/h`** (`0.1000 lb/min`), eliminating the tip-in flat spot.
3. **Enhanced Safe Decel Overrun Pops**: `[ECM] 44605` (Spark Decel vs. RPM vs. ECT):
   - In `v029`, decel spark retarded to -2° (3k) and -4° (4k–6k), giving subtle pops.
   - `v030` enhances the crackle safely:
     - `2,000 RPM`: `2.00°` (smooth taper down to ~2,200 RPM while keeping idle catch safe)
     - `3,000 RPM`: **`-4.00°` ATDC** (was -2.00°)
     - `4,000–6,000 RPM`: **`-6.00°` ATDC** (was -4.00°)
     - Entered across both Row 4 (`100` ECT) and Row 5 (`200` ECT).
4. **Extended Overrun Window**: `[ECM] 44496` (Minimum Time to Delay DFCO):
   - Extended from `1.25 s` to **`1.75 s`**, giving an extra 0.5s of audible overrun burble before DFCO injector cut engages.
5. **Preserve Validated `v029` Baseline**:
   - `[ECM] 12163` MAF 0.90V–1.20V cruising values 100% retained (centered STFT at -0.8% to -2.0%).
   - `[ECM] 32984` Dashpot Decay rates (`0.02, 0.03, 0.04, 0.05 lb/min`) 100% retained (zero rolling idle hang).
   - `[ECM] 44491` (14 mph) / `44492` (10 mph) DFCO enable/disable speeds 100% retained.
   - Innovate SCG-1 boost controller settings: `WG Duty = 6%`, `Active Press = 5.0–5.5 psi`, `Boost Cut = 16.0 psi / 100% cut` (peak boost 11.2 psi).

No ECU write, recording, or engine action starts automatically from this card; see [v030-run-card.json](v030-run-card.json) for machine-readable criteria.

---

## Preparation & Owner Pre-Flash Checks

1. **Owner pre-flash verification** (the agent never initiates an ECU write, readback, DTC clear, or adaptation reset):
   - Confirm vehicle ignition is KOEO with stable battery supply (`>= 12.2 V`), accessories OFF.
   - Confirm VCM Scanner is disconnected before opening VCM Editor's write dialog.
   - Verify candidate file `tunes/v030-smooth-tipin-enhanced-pop.hpt` and write **Calibration Only**.
2. **Paired logging setup**:
   - Reuse verified 18-channel profile [2004 Focus SVT - V023 Idle Spark Trial.Channels.xml](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml) and label the session **`v030-drive`**.
   - Start **both** VCM Scanner and SCG Logger while KOEO before cranking.

---

## Stage A — Low-RPM Tip-In & Low-Speed Drivability (Stutter Elimination Check)

1. **Procedure**:
   - In 1st and 2nd gear from low speeds (1,200–2,000 RPM), lightly depress and modulate the throttle (10% to 25% pedal).
   - Accelerate gently from a slow roll up to 2,500 RPM multiple times.
2. **Success Criteria**:
   - Smooth, linear power delivery without hesitation, jerking, or bucking.
   - Telemetry confirms spark advance stays smooth ($18°–26°$) with zero `Torque Control` drops below 2,400 RPM.
   - Wideband lambda on tip-in stays within $0.95–1.05$ without lean spikes above $1.10$.

---

## Stage B — Enhanced Decel Overrun Pop & Burble Check

1. **Procedure**:
   - In 2nd or 3rd gear, accelerate up to 4,500–5,500 RPM.
   - Fully lift off the throttle while staying in gear and let the engine engine-brake down to 2,000 RPM.
2. **Success Criteria**:
   - Crisp, audible, pleasant sports-car crackles and burbles are heard for approximately 1.5–1.7 seconds after lift-off.
   - Spark advance holds steadily between -4° and -6° ATDC down through 3,000 RPM, then gracefully tapers positive through 2,000 RPM.
   - Clean transition into DFCO (`Fuel Source: Injector Cut`) after 1.75 seconds.

---

## Stage C — Steady Cruise & Rolling Idle Verification

1. **Procedure**:
   - Hold steady 35–45 mph cruise for 15 seconds.
   - Clutch-in from 35 mph to a full stop.
2. **Success Criteria**:
   - Cruise STFTs remain centered within $\pm 3.0\%$.
   - Idle glides cleanly to 950 RPM without hanging or dipping.

---

## Rollback & Abort Thresholds

Immediately discontinue road testing, transition to neutral, and pull over safely if any of the following occur:
- Wideband AFR exceeds `12.0` ($\lambda > 0.82$) under manifold boost $> 8\text{ psi}$.
- Manifold boost exceeds `16.0 psi` (SCG-1 boost cut threshold).
- Knock retard exceeds `2.0°` in VCM Scanner.
- Engine stalls or undershoots below `700 RPM` on clutch-in.
- Fuel rail pressure differential drops below `35 psi` (`FRP sensor voltage < 2.50 V`).

**Immediate Rollback Target**: `v029-decel-pop-cruise-smooth.hpt` (`259,421` bytes, SHA-256 `E5846434088486A13F43EEE65F8F21E8DF38B972C84868AE580E5593BB966021`).
