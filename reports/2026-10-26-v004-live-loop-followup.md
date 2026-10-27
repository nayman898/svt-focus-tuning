# v004 live loop-diagnostic follow-up

Subsequently stopped and saved at the owner's request. The
[saved follow-up and channel test](2026-10-26-v004-channel-test.md) confirms
the loop-state observations and documents the current logging limitations.

The owner confirms Scanner is actively recording a follow-up to the first
v004 test. No newer saved desktop log was available at inspection, so these
are live UI observations, not a completed saved-log analysis. The recording
was left running. No calibration or scanner configuration was changed.

Two channel-pane observations showed:

| Channel | First observation | Second observation |
| --- | --- | --- |
| Coolant | 196 F | 186 F |
| RPM / desired | 1,089 / 1,088 | 1,104 / 1,088 |
| Idle Air Solenoid DC | 52.0% | 44.3% |
| Module voltage | 13.31 V | 13.56 V |
| Open Loop Active | Yes | Yes |
| Open Loop Conditions | Yes | Yes |
| Open Loop FMEM | No | No |
| Closed Loop Ready | Yes | Yes |
| Closed Loop Active | No | No |
| Closed Loop with O2Fault | OK | OK |
| O2 B1 Fail | No | No |
| Fuel Source | Power Demand Enrich | Power Demand Enrich |
| Throttle control state | Closed | Closed |

Four of the six added diagnostic channels now show meaningful state labels.
The new observations support investigating an asserted open-loop operating
condition; they do not identify a specific calibration threshold. FMEM and
the B1 O2 failure bit are not asserted in these snapshots, but that does not
rule out all sensor/wiring problems or substitute for a DTC readout.

Idle-air solenoid duty, previously missing from the first export, now has
changing live values. Raw TPS counts remain null. O2 B1S1 heater command and
heater fault remain null; upstream O2 voltage and engine runtime were also
null in these snapshots despite having data in the previous saved recording.
Do not call the profile fully validated or infer heater failure from nulls.
The second snapshot was preserved privately with its observation timestamp.

All six calibration binaries still match cataloged hashes and byte lengths.
Editor tabs were inspected without changing calibration values. The current
comparison-view control readout did not establish the remaining saved
closed-loop gate values; no conclusion or tune change was based on that view.

After warm recording coverage is complete, save the native HPL and export CSV
with all recorded channels under a new v004 follow-up session name. Review the
four new status traces and actual channel coverage over the complete recording
before choosing another calibration test. Read current DTCs without clearing
them. Recheck the remaining gates in a directly opened saved calibration with
an unambiguous file/view state and verify raw TPS availability/scaling before
assigning the cause to the TPS threshold.

Per the agreed scope, this follow-up can use MPVI4 alone to diagnose loop-state
conditions while the owner watches the SCG-1. Recorded wideband is still
needed before fueling corrections or assessing mixture control quality.
