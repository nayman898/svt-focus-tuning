# v017 feedback-entry trial: rich excursion remains

Stopped and exported pair170859-32f4d94f-v017 under the owner's authorization.
Session label identifiesv017; no ECU readback performed. Preserved native files,
CSV and SQLite API backup in `logs/2026-10-30-v017-entry-01`. Export saved,
SQLite integrity/finalization passed, all requested20channels populated.

## Result against the stated test

**The600F calculated-temperature entry threshold did not prevent the early
positive-trim/rich-mixture excursion. Do not retain it as a demonstrated fix or
increase it again blindly. Recommend rollback to exactv016.**

| Measurement | v016 | v017-labeled run |
| --- | ---: | ---: |
| First recorded engine runtime |76s|39s|
| First recorded ECT |172F|182F|
| CL entry: VCM elapsed |16.367s|60.155s|
| CL entry: engine runtime |91s|98s|
| CL entry: ECT |174F|186F|
| CL entry: upstreamO2 |0.000V|0.00293V|
| Peak positiveSTFT |+25%|+25%|
| Wideband minimum in early excursion |0.722|0.723|

The different CSV origins make a44s delay comparison invalid. Runtime shows
only7s difference, with different thermal histories, so the causal contribution
of the threshold change is not isolated. A progress update during first-pass
analysis said entry timing changed; this table is the qualified final comparison.
Engine runtime is below its255s cap at both entry points.

v017O2 remains about0.003V through its first minute while wideband is already
rich (30–60s lambda mean0.918). CL enters60.155s; STFT climbs to+25%, and60–90s
wideband mean is0.792, minimum0.723. O2 rises later, followed by fuel removal.
Thus the test failed its principal goal even though CL eventually operates.

After120s, RPMmean950.25, minimum835.75, SD28.10; no captured stall. These are
not a controlled idle-improvement comparison. Later lambda window means are
approximately1.009–1.017. No recorded FMEM or O2B1Fail assertion. That does not
prove historicalP1132 cleared; no DTC read/clear was performed.

## Data quality

9,533 VCM rows1.312–221.517s; gap160.361–161.908s. SCG elapsed = VCM elapsed
+11.828065s, provisional metadata alignment. Neither record contains the full
VCM crank/start interval. No validated physical exhaust/sensor delay. Conclusions
use sustained windows, not subsecond causal ordering. State absence is limited
to recorded samples and this short test.

## Next action, not another identical idle run

The repeat under both thresholds makes independently checking the upstream
sensor signal/heater and Scanner interpretation more useful than another blind
entry threshold or gain edit. The Bosch15719 warm response has been observed,
but its cold/heater behavior and application equivalence remain unverified.

Use exact vehicle wiring and suitable equipment to compare physical upstream
O2 signal/return with the ECU channel during the near-zero period, and measure
heater supply/control/current. Also validate wideband installation/measurement.
If the physical signal is already responsive while the channel remains nearzero,
investigate wiring/PCM input or acquisition/definition. If both remain nearzero
despite independently verified rich exhaust, investigate sensor/heater/installation.
The logs alone cannot distinguish those branches or prove fuel PID tuning needed.

No newv018 created. v016 retains the950RPM margin experiment and unresolved
feedback problem; rollback is not a claim of road/boost readiness. The separate
return-to-idle hang investigation remains open. No ECU write, code clearing or
hardware change performed by the agent.
