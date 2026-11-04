# v029 staged regression test

Candidate: [v029 Decel Pop Activation & Cruising Stutter Elimination](../tunes/v029-decel-pop-cruise-smooth.md)
([v029-decel-pop-cruise-smooth.hpt](../tunes/v029-decel-pop-cruise-smooth.hpt)).
Exact parent and immediate rollback: [v028 Engine Braking, Overrun Decel Pop & Dashpot Decay Fix](../tunes/v028-engine-braking-pop-dashpot-decay.md)
([v028-engine-braking-pop-dashpot-decay.hpt](../tunes/v028-engine-braking-pop-dashpot-decay.hpt)).

`v029` addresses two empirical findings from the `v028` road drive review ([2026-11-03-v028-drive-review.md](../reports/2026-11-03-v028-drive-review.md)):
1. **Activate Decel Overrun Pops**: `[ECM] 44605` (Spark Decel vs. RPM vs. ECT):
   - In `v028`, only Row 5 (`200` ECT) was modified, but telemetry proved the PCM operates against **Row 4 (`100` ECT)** at normal coolant temperatures (175°F–195°F / 82°C–90°C), resulting in +5° to +16° spark instead of retard.
   - `v029` updates Row 4 (`100` ECT) to the target retard values:
     - `3,000 RPM`: `5.00°` $\to$ **`-2.00°` ATDC**
     - `4,000 RPM`: `15.00°` $\to$ **`-4.00°` ATDC**
     - `5,000 RPM`: `16.00°` $\to$ **`-4.00°` ATDC**
     - `6,000 RPM`: `17.00°` $\to$ **`-4.00°` ATDC**
   - Retains Row 5 (`200` ECT) at identical retard values. RPM $\le 2{,}000$ remains untouched (5.0° / 12.0° / 13.0°) to safeguard clutch-in idle catch.
2. **Eliminate Low-Throttle Cruising Stutter**: `[ECM] 12163` (MAF Airflow vs. Voltage):
   - Telemetry revealed an empirical +2.0% to +3.4% lean fuel trim bias in the light-throttle cruising region (`0.90V` to `1.20V`), causing wideband lambda lean excursions ($\lambda = 1.14–1.18$) and triggering rapid tip-in torque control spark drops (7° cuts).
   - `v029` scales the MAF airflow curve by **`+3.0%`** across four breakpoints:
     - `0.898 V`: `0.1425` $\to$ **`0.1468 lb/min`**
     - `1.000 V`: `0.1729` $\to$ **`0.1781 lb/min`**
     - `1.100 V`: `0.2066` $\to$ **`0.2128 lb/min`**
     - `1.200 V`: `0.2734` $\to$ **`0.2816 lb/min`**
   - This centers closed-loop fuel trims directly at 0.0% and prevents the lean-surge stutter cycle.
3. **Preserve Validated `v028` Baseline**:
   - `[ECM] 32984` Dashpot Decay rates (`0.02, 0.03, 0.04, 0.05 lb/min`) 100% retained (fixed rolling idle hang).
   - `[ECM] 44491` (14 mph) / `44492` (10 mph) / `44496` (1.25s) DFCO settings 100% retained (delivered strong engine braking).
   - `[ECM] 32988` trimmed dashpot air 100% retained.

Innovate SCG-1 boost controller settings:
- `SPG` (Spring Weight): `7 psi`
- `dUt` (Duty Cycle): **`8%`**
- `bSt` (Boost Cut): `16 psi` (proven safe and functional during the +17.3 psi pull in v028)
- `AFr` (Lean Cut): `12.8 AFR`

No ECU write, recording, or engine action starts automatically from this card; see [v029-run-card.json](v029-run-card.json) for machine-readable criteria.

---

## Preparation & Owner Pre-Flash Checks

1. **Owner pre-flash verification** (the agent never initiates an ECU write, readback, DTC clear, or adaptation reset):
   - Confirm vehicle ignition is KOEO with stable battery supply (`>= 12.2 V`), accessories OFF.
   - Confirm VCM Scanner is disconnected before opening VCM Editor's write dialog.
   - Verify candidate file `tunes/v029-decel-pop-cruise-smooth.hpt` and write **Calibration Only**.
2. **Paired logging setup**:
   - Reuse verified 18-channel profile [2004 Focus SVT - V023 Idle Spark Trial.Channels.xml](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml) and label the session **`v029-drive`**.
   - Start **both** VCM Scanner and SCG Logger while KOEO before cranking.

---

## Stage A — Steady Light-Throttle Cruise Evaluation (Cruising Stutter Check)

1. **Procedure**:
   - Warm engine to operating temperature ($ECT \ge 175^\circ\text{F}$).
   - Accelerate to a comfortable secondary road cruise speed (35–45 mph) in 3rd or 4th gear.
   - Hold steady light throttle (~2,000–2,500 RPM, 2–5% pedal position) for **15–20 continuous seconds**.
2. **Success Criteria**:
   - The low-throttle rhythmic stutter/hesitation reported on earlier drives is eliminated.
   - The engine pulls smoothly and seamlessly without surging.
   - Telemetry confirms STFT hovers within $\pm 2.5\%$ (mean 0.0%) and wideband lambda remains stable around $1.00$ ($\sim 14.7\text{ AFR}$) without lean spikes above $1.08$.

---

## Stage B — Decel Overrun Pop & Burble Check

1. **Procedure**:
   - Accelerate in 2nd or 3rd gear up to 4,500–5,000 RPM.
   - Completely lift off the throttle pedal while remaining in gear.
   - Allow the engine to decelerate in gear down to ~2,500 RPM before clutching in or braking.
2. **Success Criteria**:
   - During the first 1.25 seconds of closed throttle (before injectors cut), crisp, audible exhaust burble/pops are heard from the exhaust.
   - Exhaust pops are distinct yet thermally safe (retarded to -2°/-4° ATDC rather than aggressive ignition cuts).
   - Fueling cleanly transitions into DFCO (`Fuel Source: Injector Cut`) after 1.25s, providing strong engine braking down into low speeds.

---

## Stage C — Rolling Stop Idle Glide Re-Verification

1. **Procedure**:
   - From 35 mph, depress the clutch (or shift to neutral) and glide to a complete stop without touching the accelerator.
2. **Success Criteria**:
   - Engine RPM glides smoothly through the 1,300–1,500 RPM region in under 1 second.
   - Lands squarely on the commanded 950 RPM warm idle without hanging, dipping below 800 RPM, or needing a throttle blip.

---

## Rollback & Abort Thresholds

Immediately discontinue road testing, transition to neutral, and pull over safely if any of the following occur:
- Wideband AFR exceeds `12.0` ($\lambda > 0.82$) under manifold boost $> 8\text{ psi}$.
- Manifold boost exceeds `16.0 psi` (SCG-1 boost cut threshold).
- Knock retard exceeds `2.0°` in VCM Scanner.
- Engine stalls or undershoots below `700 RPM` on clutch-in.
- Fuel rail pressure differential drops below `35 psi` (`FRP sensor voltage < 2.50 V`).

**Immediate Rollback Target**: `v028-engine-braking-pop-dashpot-decay.hpt` (`259,325` bytes, SHA-256 `0DFDEA68506F8AF005404E29F1403B46D998123A98E5417FDEB1481EE13BF752`).
