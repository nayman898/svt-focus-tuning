# Fan repair baseline and ECT idle-adder contingency

Owner expects the replacement resistor and pigtail on **2026-10-27** and plans
repair/testing. Installation and electrical/stage verification are not yet
confirmed. A repaired resistor alone may not change observed stage behavior
if the current v005 tune still requests high speed at 195 F.

The prepared [v006 post-repair baseline](../tunes/v006-post-repair-fan-baseline.md)
restores high-speed on/off to **225/215 F**, preserving low-speed **195/190 F**
and all later v005 idle/closed-loop work. Use it only with the restored circuit.
The old [temporary-path retirement](../tunes/v003-temp-fan-stage-match.md)
specified this restoration; hardware repair status remains pending.

## Could Idle RPM Adder vs. ECT help?

Yes, as a **temperature-based idle-speed reserve**. Raising desired RPM before
a predictable warm load can be a bounded experiment if load recovery still
needs help after repair. It is not a direct fan-state compensation function.
HP Tuners defines this as an adder to desired RPM based on ECT and separately
describes fan-related idle functions in its
[Ford idle reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm).
Those generic functions are not all established as exposed on this controller.

At 192 F, for example, the low-speed fan can be off while coolant warms toward
195 or on while it cools toward 190. One ECT lookup gives the same RPM adder
in both cases. It also cannot uniquely anticipate an A/C-requested fan at a
different coolant temperature. It is not a guaranteed cure for the measured
fan-off mixture excursion while closed loop remains active.

## Actual v005 table, read without modification

**ECM 32955, Idle RPM Adder vs. ECT:**

| ECT breakpoint, F | RPM adder |
| ---: | ---: |
| -256 | 710 |
| -256 (second entry) | 710 |
| -20 | 710 |
| 5 | 710 |
| 76 | 710 |
| 112 | 350 |
| 162 | 0 |
| 254 | 0 |

The duplicate extreme-low entries are recorded as shown, not reinterpreted
as recommended operating temperatures. The warm interval is very broad:
162-254 F. Adding 50 at the 254 endpoint alone would interpolate to only
**17.93 RPM at 195 F** and **15.22 at 190 F**, not a 50-RPM fan-stage bump.
Increasing the endpoint far more just to obtain a warm-band effect would
also create a larger untested high-temperature adder.

If a later trial is justified, review an explicit warm-temperature curve/
breakpoint arrangement that preserves the current cold-start adder shape,
and start with a modest measured RPM-reserve experiment. An illustrative
50-RPM increase near fan-on is a trial magnitude, not a selected or validated
value for this engine. Verify axis edits/interpolation and every saved value.
No ECT adder or breakpoint was edited in v006.

## Worth preparing a fallback?

Prepare the repair baseline and this contingency plan now. Select actual
adder cells/values after repaired low-speed fan on/off data establishes what
is still wrong:

- If the expected low stage is absent, diagnose stage commands/circuit behavior.
- If a significant supply dip persists, confirm battery/underhood voltage and
  current/connection behavior; an RPM cushion does not constitute repair.
- If supply/stage behavior is acceptable but RPM recovery needs margin, test
  a separate adder/compensation revision while preserving base idle and fuel.
- If RPM improves but the fan-off lean excursion remains, do not accept the
  cushion as a fueling fix. Continue O2/STFT/MAF and commanded-mixture review.

Headlights had no perceptible idle effect and the interior blower had a subtle
effect per the owner. These comparisons help prioritize the fan transition,
but loads/currents and exact accessory timing were not measured. Keep future
fan labels, native logs and timing provenance explicit.
