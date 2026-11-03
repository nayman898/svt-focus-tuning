# v014 stationary comparison

**Owner update2026-10-29:** v014 installed; engine initially not started.
First pair185239-7271be01-v014 confirmed both recording at18:52:42 local.
Automatic stop/export after360s is a backstop, not an instruction to continue
through instability. Inspect session manifest for current recording state.
Installed status supersedes the original preparation text below.

Candidate [v014](../tunes/v014-warm-idle-open-loop-isolation.md) is prepared,
not flashed/tested. Owner handles ECU writes. Installed state remains v013
until the owner confirms otherwise. No recording is active.

## Purpose

Test the owner's closed-loop-specific deterioration hypothesis with warm idle
targeted at900RPM. Only the known TPS-based open-loop request changes. Do not
use startup fast idle as the comparison and do not call richer open-loop
operation proof of a defective narrowband sensor.

## Acquisition and operation

1. Preserve pending/stored DTCs and any freeze-frame; record actual installed
   filename. No DTC clearing, extra adaptation reset, regulator adjustment or
   sensor disconnection. Water/meth OFF; SCG purple RPM disconnected.
2. Start both recorders with tune label v014 before the test interval. Prefer
   the existing Return Fuel Trial13 profile for the first comparison; all13
   worked in the latest run. Runtime14 is optional and prepared-only, with a
   fresh acquisition check required. Do not sacrifice STFT/loop/RPM/wideband
   coverage for more channels. Save actual profile and native files.
3. Confirm valid SCG data, CL Active No and appropriate open-loop Fuel Source.
   Warm startup may show Cold Eng./Startup; that is not the comparison window.
   If feedback remains active, the intended isolation was not achieved—do not
   adjust other gates mid-test.
4. Compare once coolant is approximately180–195F, desired/actual idle is near900
   and startup trends have settled. Keep A/C/defrost off, other accessories
   constant, no intentional throttle or load steps. Note actual fan events.
   Record pressure-gauge video and a common visible/audible time mark when
   available. Native creation time and app start-command time differed in the
   latest recording, so those alone do not prove exact synchronization.
5. Remain at the controls. Capture up to3minutes of settled warm idle; extend
   only while behavior and measured mixture remain acceptable, to a maximum
   of5minutes of the comparison interval. This is a ceiling, not a requirement
   to endure deterioration. End immediately for severe stumble/stall, worsening
   roughness or sustained unexplained rich/lean departure. A fan cycle is not
   required and repeated stalls are not the objective.
6. Stop both and export. Verify saved/partial status, full native files and CSVs.
   Note felt changes, exact clock/event times and any key/starter use. No
   unattended monitoring is implied by this document.

## Interpretation before any next adjustment

- Stable warm OL at similar measured lambda supports feedback involvement,
  without identifying whether the cause is sensor response, delay, calibration,
  wiring or acquisition. Compare against temperature/load-matched v013 data.
- Stable OL only at richer lambda supports mixture sensitivity; it does not
  isolate a faulty feedback loop. Do not permanently disable CL on that basis.
- Similar deterioration in OL means closed-loop operation is not necessary for
  that failure; retain air/runtime, fuel delivery, ignition and mechanical leads.
- No deterioration in a short run is provisional; no road/boost acceptance.
- A numeric O2 gain/delay/bias edit requires a verified exposed parameter and
  evidence for its direction/size. Injector pulse width and a verified trim/
  LAMBSE definition remain useful missing measurements, not invented channels.

Return to the exactv013 parent after this isolated test; it also has unresolved
instability. No road/boost use on the diagnostic candidate.
