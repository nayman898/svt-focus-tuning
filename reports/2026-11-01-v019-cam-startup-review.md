# v019 cam-context startup capture

Source `paired-20261101-124910-59b4fd79-v019-testing-cam`, preserved under
[logs/2026-11-01-v019-cam-01](../logs/2026-11-01-v019-cam-01/).
Owner requested autonomous stop/analysis before leaving to shower. Both recorders
were stopped and exported; engine shutdown remains owner-controlled and unconfirmed.
No calibration, DTC clear, adaptation reset or output-control command performed.

## Preservation and acquisition

Native VCM HPL156252bytes and CSV1056267bytes are present, along with SCG CSV
and SQLite. SQLite integrity_check returnedok and closed_cleanly=true. Source
copies match byte-for-byte; SQLite preserved via backupAPI. Input hashes recorded.
The original manifest remains **partial** because a Windows access-denied error
occurred replacing session.tmp with session.json. All four expected data files
exist and recorded exports succeeded. Do not erase the error or silently promote
the manifest to saved. Cause of the transient lock has not been established.

VCM has5155rows, offsets1.624–121.327s, no row gaps above0.3s. Of24 requested
channels,22 have data; coolant and absoluteTPS are blank throughout. Therefore
this24-channel combination is not accepted as the default. Cam angle/error/duty
all populated, but duty is constant0, which does not prove an electrical output
measurement or active VCT control. Runtime advances0–114s in this export despite
an earlier separate-run display stuck at17. Preserve these separate observations.

SCG quality:1153valid,466warmup,10sensor_error,1gap,1stopped. Only valid samples
used for mixture summaries. Metadata clock alignment is SCG elapsed = VCM offset
+13.779261s, provisional; sensor/exhaust transport delay remains uncorrected.
Warmup makes early wideband coverage sparse. Do not use unsupported values.

The earlier manual VCM recording was not saved per owner. Its separate SCG file
scg1-20261101-124724-04041a0a.sqlite is not merged into this paired capture.

## Timeline

| VCM offset | Observation |
| --- | --- |
| Start–~7s | RPM0/crank/runup then startup; exclude transient cam angles from mechanical diagnosis |
| 20–40s | RPM1217–1329; validWBmean0.809; CLoff/startup; reportedSTFT~+1.34% |
| 47.900s | Closed Loop Active becomesYes; fuel source becomesStoich at47.928s |
| 60–80s | WBmean0.983, range0.906–1.021; STFTmean−23.52%, min−24.05% |
| 91.334s | CLNo and FMEMYes; fuel source returnsCold Eng./Startup |
| 100–120s | WBmean0.791, range0.776–0.805; displayedSTFT~+3.42% whileCLoff |
| End | DesiredRPM1088, actual~1095; not settled950RPM warm idle |

O2B1Fail isNo throughout. No new DTC read was performed; FMEM transition is not
a proven P1132 set timestamp. DisplayedSTFT while CLoff must not be assumed to
represent an actively applied feedback correction.

After20s cam angle stays about1.875–3.125deg and error approximately opposite,
with duty0 throughout. Do not infer exact requested angle by adding actual/error
without its definition. This run shows neither a large sustained cam excursion
nor the warmed-up repeated dips we intended to correlate. It cannot clear VCT
under warm conditions or identify the cause of earlier idle fluctuations.

## Decision

Stop this run rather than extend unattended through recurrent rich fallback.
The useful new finding is a repeatable CL-to-FMEM transition after large negative
trim, with simultaneous wideband evidence. Warm-cam causality remains untested.
No further MAF or idle gain adjustment is justified from these startup windows.

For acquisition, reduce the next cam trial channel burden before another engine
run and require ECT/TPS plus essential feedback channels to populate. Keep the
saved original profile and this failed24-channel admission in the coverage record.
Do not retry the same unchanged24-channel cold run. Resolve the cold feedback/
fallback issue and missing measurement context before requesting another warmup.
