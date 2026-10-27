# v004 follow-up preservation and short channel test

At the owner's request, stopped scanning, saved the existing recording, added
controller-listed channels, restarted scanning for a short test, then stopped
and saved that test. No ECU write, calibration edit or SCG-1 change occurred.
Scanner is left stopped with the short test saved.

## Preserved recordings

- Follow-up: `logs/2026-10-26-v004-idle-02/VCM/v004-followup.hpl` and CSV.
  10,788 exported rows at offsets 2.436-255.371 s (252.935 s coverage).
- Short channel test:
  `logs/2026-10-26-v004-channel-test-01/VCM/channel-test.hpl` and CSV.
  1,251 exported rows at offsets 2.419-33.349 s (30.930 s coverage).

Both sessions have SHA-256/byte-length manifests. CSV exports cover Entire
Log. Exported row counts are not independent sensor-sample counts; no measured
polling-rate or interpolation guarantees are inferred. No LogWorks capture
was required for these loop-state-only tests, as agreed with the owner.

In both recordings, Open Loop Active and Open Loop Conditions are Yes,
Closed Loop Active is No, Open Loop FMEM is No, and O2 B1 Fail is No in every
exported row. These observations confirm the live follow-up states in saved
data. They do not reveal a specific open-loop threshold or rule out all faults.

## Channel investigation and test results

The controller selector's throttle branch exposes only memory-address TPS
ADC 3017/3018 plus the existing throttle-state label. The inspected Fuel and
Open & Closed Loop branches offer no more specific enrichment-reason flag
than the existing Fuel Source and loop-condition channels. No guessed IDs
or external sensor scales were introduced.

Added through the selector after verifying Common ID metadata:

| Channel | ID | Requested interval | Short-test result |
| --- | ---: | --- | --- |
| Air Load | 2323 | 200 ms | Configured but absent from CSV; not usable evidence |
| Coolant Temperature Sensor Fail | 12972 | 1 s | Present, Pass in all 1,251 exported rows |

Saved the active configuration through Scanner and updated the repository
[profile](../profiles/2004%20Focus%20SVT%20-%20Idle%20and%20Cruise.Channels.xml).
Comparison against the preserved preceding configuration shows exactly these
two additions. Air Load is retained as an explicitly unsuccessful channel
trial, not a working measurement. Metadata also confirms runtime ID 2131 is
one byte, consistent with the previously observed 255-second cap.

Both saved recordings have varying idle-air duty. The follow-up also has
STIT, vehicle speed, fan-duty and A/C-clutch observations, which were missing
from the first v004 export. Availability varies across sessions: the short
test does not establish those channels remain usable. Upstream O2 voltage
and raw relative TPS are present but empty in both new exports. The short
test also has empty O2-heater/fault channels; do not interpret null as Off/OK.

## Next work

Additional long idle recordings with this channel set are not the next useful
step. Preserve the two sessions and inspect remaining open-loop conditions
in a directly opened, hash-verified v004 calibration. Investigate why O2
voltage, TPS and other requested channels are absent despite earlier partial
availability; check current DTCs/acquisition support before changing gates.
A coolant-failure Pass and an unasserted O2 failure bit are limited status
evidence, not a complete sensor-health diagnosis. Recorded wideband remains
necessary before fueling corrections or mixture-quality validation.
