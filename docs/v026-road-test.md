# v026 Light-Load Road Test Run Card

**Calibration**: `v026-open-loop-tps-threshold.hpt` (Already installed & verified)  
**Parent**: `v025-maf-idle-offidle-smooth.hpt`  
**Purpose**: Validate light-load drivability, clutch takeoff, steady-state in-gear cruising, clutch-in decel recovery, and post-drive idle stability under real road load.

---

## Safety & Operating Rules
- **Safety First**: Eyes on the road at all times. Do not monitor the laptop screen while operating the vehicle.
- **Part-Throttle Only**: Light to moderate throttle only (< 35–40% throttle / `TPS < 400 counts`). No WOT pulls or high-boost loading yet.
- **Hardware Configuration**: Water/meth injection remains **OFF**. Upstream SCG-1 wideband active.
- **Abort Criteria**: If the vehicle experiences heavy bucking, violent misfires, lean spikes under boost (`AFR > 13.0` under positive pressure), or oil/coolant warning lights, pull over safely and disengage.

---

## Test Sequence (10–15 Minutes Total)

### Stage 1: Stationary Pre-Flight & Logger Arming
1. Engine already warm (`ECT > 175°F`).
2. Start paired session in SCG logger (`scg-logger`).
3. Verify VCM Scanner is polling standard 18 channels.
4. Idle in neutral for 15–30 seconds to capture fresh baseline.

### Stage 2: Low-Speed Takeoff & Neighborhood Driving (1st & 2nd Gear)
1. **Takeoff from Stop**:
   - Engage 1st gear and pull away smoothly with normal light clutch release.
   - *Observe*: Check for hesitation, stumbling, bogging, or jerkiness as clutch engages.
2. **2nd Gear Cruise (1,500–2,500 RPM)**:
   - Shift to 2nd gear and hold steady 20–25 mph for ~15–20 seconds.
   - *Observe*: Check for bucking, surging, or throttle hesitation.

### Stage 3: Steady-State Moderate Cruise (3rd Gear, 30–40 mph)
1. Shift to 3rd gear on a flat, unobstructed street.
2. Hold steady speed (2,200–3,000 RPM) with steady foot for 15–30 seconds.
3. *Goal*: Provides clean closed-loop data across the `1.0V–1.6V` MAF transfer range under light road load.

### Stage 4: Clutch-In Deceleration & Stop Catch
1. While cruising in 2nd or 3rd gear at ~2,500 RPM:
   - Lift off throttle completely and push clutch in to come to a complete stop.
2. *Observe*: Check RPM drop. Verify engine catches cleanly at idle (~950 RPM) without dipping below 750 RPM or stalling.
3. Repeat once or twice at stop signs.

### Stage 5: Post-Drive Parked Idle Check
1. Return to park/driveway.
2. Put gearbox in neutral, clutch out, handbrake up.
3. Let engine idle undisturbed for 30–60 seconds.
4. Stop the paired datalog in SCG logger.

---

## Logged Data We Will Analyze
- **MAF Transfer Error**: STFT across `0.9V–1.8V` under true road load vs stationary holds.
- **Tip-in Transient Fueling**: Short-term lean/rich excursions during clutch release and throttle application.
- **Decel Dashpot & Idle Recovery**: Minimum RPM undershoot on clutch-in.
- **Post-Drive Thermal Recovery**: STFT, STIT, and LTIT with elevated underhood temps.
