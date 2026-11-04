# v027 staged regression test

Candidate: [v027 Engine Braking Restoration & Subtle Overrun Decel Pop](../tunes/v027-engine-braking-decel-pop.md)
([v027-engine-braking-decel-pop.hpt](../tunes/v027-engine-braking-decel-pop.hpt)).
Exact parent and immediate rollback: [v026 Open Loop Fuel TPS Threshold Cleanup](../tunes/v026-open-loop-tps-threshold.md)
([v026-open-loop-tps-threshold.hpt](../tunes/v026-open-loop-tps-threshold.hpt)), tested in
[2026-11-03-v026-drive-review.md](../reports/2026-11-03-v026-drive-review.md).

`v027` targets deceleration drivability, in-gear engine braking responsiveness, and subtle overrun exhaust character:
1. `[ECM] 44491` (Minimum VSS to Allow DFCO): `35.00` -> `18.00 mph`.
2. `[ECM] 44496` (DFCO Closed Throttle Delay): `3.00` -> `1.00 s`.
3. `[ECM] 44605` (Spark Decel vs. RPM vs. ECT): 200°F ECT row retarded above 3,000 RPM (3k = `0.00°`, 4k–6k = `-2.00°` ATDC); $\le 2{,}000\text{ RPM}$ preserved at `14°/12°/13°`.
4. `[ECM] 32988` (Idle Dashpot Pre-Position vs. RPM): trimmed at 3,150 RPM (`0.80 lb/min`) and 4,150 RPM (`1.00 lb/min`).

Innovate SCG-1 boost controller settings for this test:
- `SPG` (Spring Weight): `7 psi`
- `dUt` (Duty Cycle): **`8%`** (stepped up from 6% to evaluate boost response with cleaned solenoid filter)
- `bSt` (Boost Cut): `16 psi`
- `AFr` (Lean Cut): `12.8 AFR`

No ECU write, recording, or engine action starts automatically from this card; see [v027-run-card.json](v027-run-card.json) for machine-readable criteria.

---

## Preparation & Owner Pre-Flash Checks

1. **Owner pre-flash verification** (the agent never initiates an ECU write, readback, DTC clear, or adaptation reset):
   - Confirm vehicle ignition is KOEO with stable battery supply (`>= 12.2 V`), accessories OFF.
   - Confirm VCM Scanner is disconnected before opening VCM Editor's write dialog.
   - Verify exact candidate file `tunes/v027-engine-braking-decel-pop.hpt` and write **Calibration Only**.
2. **Paired logging setup**:
   - Reuse verified 18-channel profile [2004 Focus SVT - V023 Idle Spark Trial.Channels.xml](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml) and label the session **`v027-drive`**.
   - Start **both** VCM Scanner and SCG Logger while KOEO before cranking. Confirm all 18 VCM channels populate plus valid SCG-1 wideband lambda.

---

## Stage A — Startup, Warm Idle & Decel Return Check

1. **Startup & Warm Idle**:
   - Start engine with untouched throttle. Confirm clean startup and stable idle catch.
   - Confirm warm idle settles near `950 RPM` with normal Closed Loop fuel trim (`STFT within ±5%`).
2. **Stationary Free-Rev & Dashpot Return**:
   - In neutral, blip throttle smoothly to `3,500–4,000 RPM` and release instantly.
   - Verify dashpot airflow catches the engine smoothly without hang or stalling below `800 RPM`.
   - Confirm decel spark stays advanced (`12–14°`) below `2,000 RPM` for seamless idle settling.

---

## Stage B — In-Gear Road Test: Engine Braking, Decel Pops & SCG-1 8% Boost Pull

1. **In-Gear Deceleration & Engine Braking (2nd & 3rd Gear, 45 mph down to 15 mph)**:
   - Accelerate to 40–45 mph in 3rd or 2nd gear (`~3,500–4,500 RPM`), then completely lift off throttle.
   - **Hypothesis Check 1 (Engine Braking)**: In `v026`, DFCO was disabled below 35 mph, resulting in zero engine braking. In `v027`, DFCO should remain active down to `18.00 mph`. Verify distinct, positive in-gear deceleration torque.
   - **Hypothesis Check 2 (Overrun Pops/Burble)**: During the 1.0s window between throttle lift and fuel cut, retarded timing (`0°` to `-2°` ATDC) should produce a subtle overrun burble/pop from the exhaust before injectors cut.
   - **Hypothesis Check 3 (Clutch-In Idle Return)**: Push clutch in at 20 mph; confirm engine catches cleanly at `950 RPM` without dips below `800 RPM`.
2. **Progressive Boost Pull (3rd Gear WOT with 8% SCG-1 WGDC)**:
   - From `2,500 RPM` in 3rd gear, smoothly roll into WOT up to ~6,500–7,000 RPM.
   - **SCG-1 Telemetry**: Monitor peak boost (expected `~13.5–14.0 psi` with 8% WGDC). Verify boost cut at `16 psi` is never approached.
   - **Fueling Telemetry**: Verify wideband lambda tracks commanded open-loop target (`0.73–0.75 Lambda` / `10.7–11.0 AFR`). Confirm fuel rail pressure maintains `~40 psi` differential (`FRP >= 50–55 psi` absolute).
   - **Knock Protection**: Confirm zero knock retard (`0.00°`) throughout the pull.

---

## Stop Criteria & Rollback

Stop the test immediately and return to safe driving/idle if:
- Knock retard exceeds `2.0°` under boost.
- Wideband lambda exceeds `0.80 Lambda` (`> 11.7 AFR`) under boost `> 8 psi`.
- Boost spikes above `15.0 psi` (well before the 16.0 psi SCG-1 hard cut).
- Engine stalls or dips `< 700 RPM` upon clutch-in.
- Fuel rail pressure collapses (`< 35 psi` differential).

**Immediate calibration rollback**: Flash exact [v026-open-loop-tps-threshold.hpt](../tunes/v026-open-loop-tps-threshold.hpt)
(`SHA-256: 86B10615EB5E032CF4343120A23C6B93DB30FD6CFC558CE863143C32629B1918`).
SCG-1 rollback: Return duty cycle to `6%` (`dUt = 6`).
