# Reassessment: idle spark handoff and dashpot

The owner's observation is sufficient reason to investigate the Idle Feedback
to Base/MBT handoff as a possible contributor to the deep dips. Calling the
advance solely a harmless recovery response was too strong. A recovery action
and an unstable or delayed handoff can coexist; the current evidence does not
separate them conclusively.

This review uses the [stationary capture](2026-10-27-v009-stationary-idle-dips.md)
and read-only inspection of exact v009 in Editor. All10 calibration hashes and
sizes match the catalog. No value was changed, saved or flashed.

## Recorded sequence

At201.111s, RPM884.9/spark8.75/IAC37.3%. At201.218s, RPM874 with spark−4.25
and IAC34.1%, still Idle Feedback. At201.285s RPM860.7 still reports Idle
Feedback; at201.311s RPM751.8 reports Base/MBT with spark30 and IAC41.6%.
The source briefly returns to Idle Feedback, then Base/MBT reappears before
the629.75RPM minimum at201.494s, with IAC57.7%. Recovery overshoots1043.75RPM
at202.023s and spark reaches the−6degree Idle Feedback Min.Clip.

At211.455s a second late event enters Base/MBT near766RPM and subsequently
reaches667.5. Earlier entries near58.1,86.7,87.7,119.0,180.4 and197.9s do not
all continue into a large fall. The repeated source changes are real recorded
observations, but entering that source is not sufficient by itself to explain
the depth. Several entries represent repeated switching within the same event.
Exported interpolation and asynchronous channel updates prevent assigning
subsecond causal order from row timestamps alone.

Across198–201.8s absolute TPS stays182.821counts, relative TPS0.324counts and
the state Closed. This does not support a throttle-potentiometer glitch in
that window. It does not independently validate the physical sensor in every
condition. The source label Base/MBT alone also does not prove which particular
base or MBT table is responsible for the final spark limit.

## Verified Editor controls

| Control | v009 value / observation |
| --- | --- |
| ECM47996 Idle Spark Proportional Gain | 2.000 |
| ECM44582 Spark Idle Control Minimum | −6.00degrees |
| Idle General Enable / Disable RPM Error | 200 /30RPM; exact state logic not established by these names alone |
| Idle Minimum VSS | 3mph |
| Dashpot Enable VSS / Hysteresis | 4 /2mph |
| Dashpot Enable Airflow | 0.07lb/min |
| Neutral Clip Modifier | 1.00 |
| ECM32984 dashpot decay | Displayed0.00 at airflow0.0/0.2/0.4/0.6;0.06at0.8,0.08at1.0,0.10at3.0 |
| ECM32986 dashpot minimum | Desired-RPM rows0/150/1150/2150/3150:0.04/0.04/0.35/0.78/1.11lb/min |
| ECM32988 pre-position | Same values through3150RPM, plus1.50at4150 |
| ECM32945 max clip versus VSS | 0.10at0/10/15mph;0.60at20/40;1.00at100 |

Editor describes ECM47996 as proportional idle spark control: higher values
make corrections more aggressive, and lowering it can help with large timing
changes. This establishes the parameter's purpose, not that2.000 is wrong or
that a particular replacement is justified.

Under linear interpolation, the unchanged dashpot-minimum curve selects about
0.2725lb/min at900 desired RPM versus0.288at950. The separate base idle-airflow
curve also changes its lookup when the target changes. These are lookups,
not actual total airflow or proof dashpot was active at0mph. Commanded dashpot
airflow and adaptation state were not logged. The target change can therefore
affect inherited behavior without an explicit dashpot-table edit, but this
does not establish the cause of the post-drive stationary dips.

The generic [HP Tuners idle reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm)
describes vehicle-speed-dependent idle/dashpot behavior. Exact controller
units, state gates and hysteresis must be respected before editing decay.

## Next calibration focus

Prioritize the interaction of spark gain/minimum, source switching and available
idle airflow after driving. Do not dismiss the owner's first-drive observation
or assume identical heat/adaptation history across parked tests. It is not
proof that driving caused a persistent adaptation change.

Inspect the relevant enable/re-entry logic, inherited airflow and adaptation
before a controlled, single-variable calibration comparison. Preserve the
MBT table initially rather than reducing its torque-producing spark merely
because its source label appears during a dip. A gain-only comparison is a
candidate hypothesis, not a prepared tune or an instruction to change a number.
No additional near-stall reproduction is required just to repeat this evidence.
