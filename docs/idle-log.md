# First idle log

Use the extended **2004 Focus SVT - Idle and Cruise** channels and layout.
They are loaded in Scanner. Start a new recording for the next idle session.

- Capture a stable warm-idle segment with the throttle untouched. Include
  warm-up too if starting cold, and identify where warm idle begins.
- Note whether A/C and other significant electrical accessories are on.
  If changing accessory loads, note approximately when each change occurs.
- Record symptoms such as hunting, stalling, vibration, or unusually high idle.
- Note the SCG-1's displayed mixture and water/meth state. Neither external
  SCG-1 mixture nor boost is currently included in the scanner profile.
- Save the native `.hpl` log and export CSV with all recorded channels. Keep
  both under `logs/`; do not overwrite an earlier recording.

The first review will check actual versus desired RPM, temperatures, idle-air
duty and adaptations, MAF/counts/voltage, timing and spark source, commanded
mixture, fuel source, and closed-loop status. New channels must be checked for
actual data before using them in an assessment. Missing fuel trims or RPM
are a data issue to resolve, not values to treat as zero.

No ECU or SCG-1 settings were changed as part of preparing this profile.
