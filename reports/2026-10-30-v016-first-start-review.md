# v016 first-start recording review

Stopped/exported at the owner's request; pair164926-7de5bc89-v016 finalized
successfully. Preserved native files and SQLite API backup in
`logs/2026-10-30-v016-idle-01`; integrity/finalization and catalog hashes passed.
Owner confirmed v016 first startup and Bosch15719 remains the last confirmed
sensor. No ECU writes, resets or code clearing performed by agent.

## Capture limits

VCM has10,309rows from1.309–238.852s, all20channels populated, one gap
216.783–218.163s. SCG started approximately102.016s before the exported VCM file
origin (20:51:09UTC). Manifest start was20:49:29UTC, consistent with a later
VCM recording restart, but exact owner actions are unconfirmed. Use the exported
file origin for alignment, not the initial paired-start event. Do not describe
this as complete synchronized cranking/cold-start data. First VCM ECT is172F.

SCG elapsed = VCM elapsed +102.016394s is provisional metadata alignment.
Sensor/exhaust delay and drift remain unverified; sustained windows are more
reliable than individual subsecond lead/lag conclusions.

## v016 result

After90s: RPMmean950.10, minimum821, SD30.27; logged desired944RPM (nominal
Editor950). No stall captured. Compared with v015load-step minimum684.5 at
desired896, absolute margin is better and the worst target error is smaller
(123 vs211.5RPM), but conditions/accessories differ. It is promising margin,
not proof of a root-cause repair or a controlled improvement in variability.

CL enters16.367s at174F. FMEM/O2B1Fail remainNo in captured samples. Initial
O2 averages0.0016V during0–15s,0.0083V during15–30s; only later rises, averaging
0.322 during30–45s and0.799 during45–60s. During30–60s, STFT reaches+25%,
wideband averageslambda0.777 and reaches0.722. RPMminimum in that window is918,
so this major early fueling excursion is not explained by a deep RPM collapse
at that moment. The sequence again supports unusable/delayed early O2 feedback,
not merely warm normal switching. It still does not identify the heater/sensor
or measurement path as faulty without independent testing.

Later30s-window lambda means are1.002–1.017. STFT moves from negative values
toward+4% by the end. IACmean decreases fromabout40–42% to35%; actual timing
increases fromnear0 to9deg, while learned air changes. Do not conflate fuel trim
with idle-air adaptation or infer a conventional PID gain from this coupling.

## Selected experiment

Live Editor inspection of the main v016 file confirms ECM12115 Closed Loop O2
Sensor Temp520F, with matching help: entry requires calculated O2 temperature
above that value. This is not ECT or an actual heater-temperature measurement.
The cold/warm/hot delay scalars display254s, but observed entry does not support
treating them as the complete delay mechanism. Leave those unchanged.

Navigator searches Feedback/Gain/O2 did not expose a verified fuel-feedback
proportional/integral control. Returned gains belong to idle spark or fuel pump;
neither is a substitute. Transport-delay learning has1000RPM minimum, above
current idle, but no validated idle transport-delay measurement supports changing
its learning range or time limits now.

Prepared [v017](../tunes/v017-o2-readiness-600.md): only ECM12115520->600F and
Notes relative to v016. An80F increment is a chosen experimental step, not a
computed optimum or known extra number of seconds. Its purpose is to delay
feedback entry until a more credible sensor operating state; it does not alter
warm correction gains and is not claimed to cure later dips or hanging idle.

The next test must establish actual CL entry movement and the early correction
excursion. If the modeled gate does not move entry appropriately, do not keep
raising it blindly. If a rich excursion persists or closed loop fails to return,
stop/revert v016 and prioritize the sensor/heater/input-path diagnosis. The
previous failed v014 prolonged-open-loop result remains relevant; v017 is a
parked diagnostic, not an approved driving tune.

Reference: [HP Tuners Ford loop definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).
