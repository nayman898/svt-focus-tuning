# v003 — TEMPORARY fan-resistor-bypass stage match

**Prepared for a controlled test; not flashed by the agent.** This attempts to
use the ECU's existing high-speed idle pathway with the present fan wiring.
It is not validated airflow compensation, an electrical repair, or a remedy
for turbo heat exposure.

**Post-test update:** the owner supplied v003 logs and reports a slight
improvement, still noticeable. The [timing and load-event review](../reports/2026-10-26-v003-timing-review.md)
shows a modestly narrower warm RPM spread but persistent voltage/RPM dips.
The pathway remains temporary and its compensation effect is not proven.

Parent: [v002](v002-idle-1100.hpt).
Candidate: [v003](v003-temp-fan-stage-match.hpt).

## Confirmed configuration

The owner confirms factory fans, relays and fuses remain intact. Only the
resistor pigtail was removed and its two wires joined. This followed melting;
the turbo sits close to the resistor location and creates considerable heat.
The exact original cause of melting and present motor current are unverified.

In v002 the low-speed command is 195 F on / 190 F off, whereas the high-speed
command is 225 F on / 215 F off. Fan High Speed Idle is already enabled.
Advanced Parameter Navigator exposes that switch and the fan thresholds,
but no separate low-speed fan airflow adder for this calibration.

The candidate makes the high-speed temperature command coincide with the
existing low-speed request. This should make the high-speed idle feature
eligible when the bypassed hardware starts. Whether it changes desired idle,
airflow or recovery must be measured. Generic documentation describes the
high-speed switch but does not establish this controller's exact response.
[HP Tuners Ford idle reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)

## Exact differences from v002

| Calibration parameter | v002 | v003 |
| --- | ---: | ---: |
| System > Fans > Fan High Speed Enable ECT | 225 F | 195 F |
| System > Fans > Fan High Speed Disable ECT | 215 F | 190 F |

A temporary-path explanation and retirement instructions are also embedded in
**Calibration Details > Notes**. Comparison includes Notes plus exactly these
two calibration parameter differences. Low-speed thresholds, fan master enable,
high-load fan logic, 1,100-rpm idle setpoints, fuel, spark and existing MIL settings
are unchanged. SCG-1 settings were not changed.

## Verification

- v002 hash checked against the revision catalog, then v002 reloaded before work.
- v003 saved separately and reopened from disk.
- Reopened fan page shows 195/190 F for both temperature-controlled stages.
- Reopened-file comparison shows only the two threshold changes and Notes.
- Embedded temporary-path note checked after reopening.
- Previous tune hashes retained in [the catalog](revisions.json).

## Test and decision

After an owner-initiated write, use a new **v003** session folder and record both
Scanner and LogWorks through warm idle and fan engagement. Save HPL/CSV and
native LogWorks LOG/CSV. Review actual versus desired idle, idle source,
available idle-air data, voltage, measured mixture and coolant/fan behavior.
The previously zero Fan PWM channel is not an established fan-state indicator.

Determine whether the idle request responds to the high-speed command and
whether RPM undershoot/recovery improves at comparable voltage and temperature.
If there is no measurable useful response, classify the test as ineffective;
do not call the compensation proven or add unrelated gains/fueling changes.

Fan electrical inrush, damaged connections, motor current and turbo heat remain
hardware issues. Continue the correct resistor, connector and protected-wiring
repair plan, preserving the resistor's required cooling and mounting.

## Retirement and rollback

Use v002 to roll back this isolated test. Once the resistor circuit is restored,
retire this temporary path and restore **high-speed 225/215 F** from v002.
Low-speed 195/190 F remains the original setting. If later revisions have other
useful changes, revert only these two temporary thresholds rather than replacing
the whole tune with v002. Track the repair and retirement as a numbered revision.
