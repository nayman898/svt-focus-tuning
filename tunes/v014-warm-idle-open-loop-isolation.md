# v014 — warm-idle open-loop isolation

**Prepared, saved, reopened and compared. Not flashed or engine-tested.**
Candidate: [v014-warm-idle-open-loop-isolation.hpt](v014-warm-idle-open-loop-isolation.hpt).
Exact parent/rollback: [v013-return-vacuum-comp-zero.hpt](v013-return-vacuum-comp-zero.hpt).

The owner reports acceptable startup operation, then progressively worsening
stumbling after several minutes in closed loop, sometimes ending in a stall.
This experiment treats closed-loop fuel control as the main hypothesis.
Astra independently reviewed the recent data and supported this isolation test
after checking the inherited base fuel and startup settings. It did not identify
a justified numerical O2 gain, bias or transport-delay correction.

## Exact change

ECM32731, Open Loop Fuel TPS Thresh vs. RPM:

| RPM breakpoint | v013 AD counts | v014 AD counts |
| ---: | ---: | ---: |
| 0 | 200.00 | 0.00 |
| 1,500 | 200.00 | 0.00 |
| 2,000 | 0.00 | 0.00 |
| 2,500 | 0.00 | 0.00 |
| 5,500 | 0.00 | 0.00 |
| 6,500 | 0.00 | 0.00 |
| 16,384 | 0.00 | 0.00 |

The two changed cells restore the historically effective TPS-based open-loop
request. Actual loop state must still be verified in the test. This also changes
1,500–2,000RPM interpolation: it is not an idle-only gate. **Stationary diagnostic
only; no road/boost use and no permanent closed-loop disabling recommendation.**
HP Tuners documents this as the TPS threshold for requesting open loop.
[Parameter reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).

All other calibration content is retained, including 900RPM targets, gain1.000,
idle spark floor-6, v013's zero manifold-vacuum multiplier, base air/runtime
tables, MAF/injector/pressure model, VCT/IMRC, O2 settings, fans and torque/spark.
Full parent Notes are retained with a diagnostic appendix.

## What the review established

- The captured42.5s stall and later negative-trim excursion are separate.
  Before the stall, exported trim was roughly-2.44 to+4.75%, not the later-19.3%.
- At approximately125–133s, O2 remained around0.23–0.33V while displayed trim
  became increasingly negative. Later low-O2 plateaus deserve investigation.
  Earlier normal-direction trim response argues against a globally reversed
  trim sign. The historical commanded field duplicates1-STFT/100 and is not
  independent proof of the base target.
- Current Editor shows LTFT learning Disabled and B1 bias ECM32905 all25
  displayed values zero. No arbitrary LTFT/bias/gain change is bundled.
- Current warm base ECM44511 at1000RPM is lambda1.00 in its lowest four TPS
  rows. This is a table value, not a promise of actual idle mixture.
- Cold enrichment ECM44516 still has0.03 in the final60s row at warm ECT.
  Enable Time10s and warm Enable ECT158F were displayed. Startup/cold-path
  applicability and other corrections must be observed; do not assume the
  base table alone determines measured lambda.
- Transport-learning minimum RPM is1000, above the900RPM target. The generic
  help mentions a base transport-delay table, but it was not exposed in the
  current Navigator search. No guessed delay was edited.
- P0320 remains owner-reported pending, with unknown occurrence time. Treat
  the actual stall observation seriously without declaring either a failed
  crank sensor or a harmless code.

The decision question is whether **warm900RPM idle remains stable with feedback
inactive at comparable measured mixture**, beyond the reported deterioration
interval. If open loop is significantly richer, smoother operation alone cannot
separate a feedback-control issue from enrichment masking another problem.

## Verification and test

The first UI Automation cell edit did not persist. It was corrected using actual
Editor keyboard entry, then saved and reopened. All seven saved values were
verified; full comparison against exactv013 contains only Notes and ECM32731.
Parent Notes prefix was verified. No ECU write or adaptive reset was performed.

Size: **236,733bytes**.
SHA-256: **ACA288B1BA25A87A6C92824D00E2028468DBEDE6279ED00420C3271BB3521790**.

Follow the [v014 test card](../docs/v014-open-loop-isolation-test.md).
Owner performs any ECU write after confirming the correct file/controller,
stable write power and Editor-required engine/ignition state; these conditions
are not verified by an offline file comparison.
Return to exactv013 after the diagnostic; that parent remains unaccepted with
unresolved stalling and is not a guaranteed cure. No automatic flash or rollback.
