# Closed loop startup delay and coolant temperature

The current tune already has a coolant-temperature-based enable-delay table.
The three 254-second cold/warm/hot scalars are only part of the available
startup controls; they do not establish a fixed 254-second wait in the logged
operating conditions. No calibration setting was changed in this inspection.

## Verified controls

Editor's Engine > Fuel > Oxygen Sensors page shows ECT Cold Delay, ECT Warm
Delay and ECT Hot Delay at 254 seconds each, with CL O2 Sensor Temp at 520 F.
The separate Delay button opens **ECM 12462 Closed Loop Enable Delay**.
Its axis explicitly reads Startup ECT in Fahrenheit, and its values are seconds.
The Editor description says it sets the delay after startup before closed loop
can be enabled.

| Startup ECT | ECM 12462 delay |
| --- | ---: |
| -20 F | 150 s |
| -5 F | 120 s |
| 25 F | 100 s |
| 40 F | 78 s |
| 50 F | 72 s |
| 62 F | 48 s |
| 85 F | 48 s |
| 120 F | 40 s |
| 200 F | 24 s |

Linear interpolation between the 120-F and 200-F cells gives about 33.2 s at
154 F and 32 s at 160 F. Those are table lookup estimates, not guarantees of
the exact closed-loop transition: other enable conditions still apply.
The exact roles of the three separate scalars in every controller path have
not been established, so do not declare them globally unused.

The owner-confirmed v006 run entered reported closed loop about 37.9 s after
the first running RPM. The preceding paired capture entered about 43.4 s
after its first running RPM. These observations are consistent with a shorter
temperature-dependent path plus other gates, rather than a universal 254-s wait.
The earlier documentation emphasizing retained 254-second scalars was incomplete
without this table.

## Direction for the next startup change

The owner's intended direction is less unnecessary waiting on a warm start
while retaining what a cold start needs. The existing curve already follows
that direction. Shortening it further is not selected from the current data:
both recent runs show positive correction adding fuel while the status-valid
wideband is rich, before upstream O2 has developed its later response. Reducing
a feedback-enable delay would not establish that the upstream signal is ready.

HP Tuners describes both the
[startup-temperature delay and calculated O2-temperature gate](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).
Keep the sensor-readiness gate intact while assessing this behavior. Do not
derive replacement timing cells from coolant alone or infer heater operation
from the latest blank heater-status columns.

This setting governs fuel feedback. Elevated initial idle has separate
[startup RPM adders and airflow controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm).
If the concern is how long the engine remains at elevated RPM, inspect those
controls against desired-RPM traces rather than treating 254 as a fast-idle timer.

The prepared [v007 target-only file](../tunes/v007-idle-1000.md) remains unchanged.
A later startup revision should have its own hypothesis, exact cells and
saved-file comparison. The owner considers the cranking reading likely related
to the battery and requests that this work focus on temperature/startup behavior;
that is recorded as an owner assessment, not a confirmed battery diagnosis.
