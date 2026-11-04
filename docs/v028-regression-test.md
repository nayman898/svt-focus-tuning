# v028 staged regression test

Candidate: [v028 Engine Braking, Overrun Decel Pop & Dashpot Decay Fix](../tunes/v028-engine-braking-pop-dashpot-decay.md)
([v028-engine-braking-pop-dashpot-decay.hpt](../tunes/v028-engine-braking-pop-dashpot-decay.hpt)).
Exact parent and immediate rollback: [v027 Engine Braking Restoration & Subtle Overrun Decel Pop](../tunes/v027-engine-braking-decel-pop.md)
([v027-engine-braking-decel-pop.hpt](../tunes/v027-engine-braking-decel-pop.hpt)).

`v028` addresses three key feedback items from the `v027` road test:
1. **Fix Hanging Idle**: `[ECM] 32984` (Idle Dashpot Decay vs. Dashpot Airflow): Restores positive decay rates across rows 1–4 (0.00 -> 0.02, 0.03, 0.04, 0.05). Eliminates floating high idle (~1,300–1,500 RPM) when rolling to a stop without needing a throttle blip.
2. **More In-Gear Engine Braking**: 
   - `[ECM] 44491` (Minimum VSS to Allow DFCO): `18.00` -> **`14.00 mph`**.
   - `[ECM] 44492` (Maximum VSS to Disable DFCO): `12.00` -> **`10.00 mph`**.
   - `[ECM] 32988` (Idle Dashpot Pre-Position vs. RPM): `2,150 RPM` trimmed from `0.78` -> **`0.55 lb/min`**.
3. **Slightly More Overrun Pops**:
   - `[ECM] 44496` (DFCO Closed Throttle Delay): `1.00` -> **`1.25 s`**.
   - `[ECM] 44605` (Spark Decel vs. RPM vs. ECT, 200°F ECT row): 3,000 RPM retarded from `0.00°` -> **`-2.00°` ATDC**; 4,000–6,000 RPM retarded from `-2.00°` -> **`-4.00°` ATDC**. RPM $\le 2{,}000$ remains untouched at 14/12/13° to protect idle return.
4. **Low-Throttle Cruising Stutter Diagnostic**:
   - Dedicated steady light-throttle hold to capture telemetry on the pre-existing cruise stutter reported by owner.

Innovate SCG-1 boost controller settings:
- `SPG` (Spring Weight): `7 psi`
- `dUt` (Duty Cycle): **`8%`**
- `bSt` (Boost Cut): `16 psi`
- `AFr` (Lean Cut): `12.8 AFR`

No ECU write, recording, or engine action starts automatically from this card; see [v028-run-card.json](v028-run-card.json) for machine-readable criteria.

---

## Preparation & Owner Pre-Flash Checks

1. **Owner pre-flash verification** (the agent never initiates an ECU write, readback, DTC clear, or adaptation reset):
   - Confirm vehicle ignition is KOEO with stable battery supply (`>= 12.2 V`), accessories OFF.
   - Confirm VCM Scanner is disconnected before opening VCM Editor's write dialog.
   - Verify candidate file `tunes/v028-engine-braking-pop-dashpot-decay.hpt` and write **Calibration Only**.
2. **Paired logging setup**:
   - Reuse verified 18-channel profile [2004 Focus SVT - V023 Idle Spark Trial.Channels.xml](../profiles/2004%20Focus%20SVT%20-%20V023%20Idle%20Spark%20Trial.Channels.xml) and label the session **`v028-drive`**.
   - Start **both** VCM Scanner and SCG Logger while KOEO before cranking.

---

## Stage A — Rolling Stop Idle Decay Check (The Throttle Blip Test)

1. **Stationary Warm Check**:
   - Confirm warm idle settles at `950 RPM` with closed-loop `STFT within ±5%`.
2. **Rolling Stop Coast-Down**:
   - Accelerate to 30–35 mph, put transmission in neutral (or push clutch in), and coast down smoothly to a complete stop **without touching the throttle pedal**.
   - **Hypothesis Check**: In `v027` and earlier tunes, the idle hovered at ~1,300–1,500 RPM until blipping the throttle. In `v028`, with `[ECM] 32984` positive decay restored down to 0.0 lb/min airflow, idle should smoothly glide down to ~950–1,000 RPM as vehicle speed drops, landing firmly at 950 RPM at 0 mph without any throttle blip required.

---

## Stage B — In-Gear Road Test: Engine Braking & Decel Pops

1. **Extended In-Gear Engine Braking (2nd & 1st Gear down to 10 mph)**:
   - In 2nd gear, coast down from 35 mph down through 15 mph to 10 mph.
   - Confirm positive engine braking deceleration drag remains active down past 18 mph to 10 mph before fuel cuts back in.
2. **Audition Overrun Pops**:
   - In 2nd or 3rd gear, accelerate above 3,500 RPM, then abruptly close throttle.
   - During the 1.25s delay window, listen for crisp, slightly more pronounced exhaust pops with -4° spark retard before fuel cutoff engages.
   - Confirm smooth re-entry when depressing throttle again.

---

## Stage C — Low-Throttle Cruise Stutter Diagnostic Hold

1. **Steady Light-Throttle Hold**:
   - On a level road at 35–45 mph in 4th or 5th gear, hold steady, light throttle (`2–5% TPS`, `~2,000–2,500 RPM`) for 10–15 seconds.
   - Allow any micro-stutters or hesitations to occur during this steady hold while both loggers are recording.
2. **Telemetry to be Analyzed**:
   - `MAF Sensor Voltage` vs airflow lookup stability.
   - `Short Term Fuel Trim` oscillation vs `SCG-1 Wideband Lambda`.
   - Fuel pulse width stability in the Siemens 60 low-pulse-width region.
   - Spark advance stability (Borderline vs MBT vs torque management intervention).

---

## Stop Conditions & Immediate Rollback

Stop the test immediately and return to safe driving/idle if:
1. Knock retard exceeds `2.0°` under boost.
2. Wideband lambda exceeds `0.80` (> 11.7 AFR) under boost > 8 psi.
3. Boost spike exceeds `15.0 psi` (approaching 16 psi cut).
4. Any sudden lean surge or fuel rail pressure drop below 35 psi differential.

**Immediate calibration rollback**: Flash exact [v027-engine-braking-decel-pop.hpt](../tunes/v027-engine-braking-decel-pop.hpt)
(`SHA-256: 3535FDB33BBEB369B2AB36DF22190E7B03EE9ABC9FBCFFEBF56930D41BE59AF5`).

