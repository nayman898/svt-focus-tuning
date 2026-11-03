# Fuel-pressure video and stationary idle review

Video: `PXL_20261029_200524935.mp4`,218.513s, owner GlowShift pressure sender
at the regulator. Original download preserved; byte-identical copy and SHA-256
recorded privately with the stationary pair under `logs/2026-10-29-pressure-video-01/`.
This is the **preceding stationary run**, not the food-trip pressure and not
the earlier spontaneous-stall recording.

## Finding

**No large pressure collapse is visible in the reviewed frames around the
recovered764RPM dip.** Pressure is mostly37–38psi while idling. The early
survey shows40, then39, then38psi as displayed vacuum develops. Around the
nominally aligned deepest dip, detailed frames remain near37psi.

This weakens a sustained, gauge-visible regulator-pressure collapse as the
explanation for **this recovered dip**. It does not rule out rapid changes below
the gauge's response/resolution, a different pressure at the rail/injectors,
injector/ignition/combustion faults, or pressure loss during the earlier stall.
No actual stall occurs in this stationary recording. No pressure or tune
adjustment is selected from the video.

## Alignment and method

- Filename implies start20:05:24.935UTC. Container creation_time20:09:04UTC is
  near the clip's end, not a usable start timestamp. VCM creation is20:05:59UTC.
  The nominal relation is **video elapsed = VCM elapsed +34.065s**.
- Phone/host clocks were not independently synchronized. No subsecond video
  marker or audio alignment was established; metadata alone is provisional.
  Approximate correspondence is consistent with the visual warm-up progression.
-44five-second survey frames were extracted and visually inspected, followed
  by12detailed frames between190–200s, including half-second samples near the
  nominal dip. Crop position was adjusted after camera movement so the gauge
  remained readable. This is sampled inspection, not a continuous digitized
  pressure trace or an assessment of engine sound.
- Pressure values were manually read, not automatically inferred by OCR.
  Whole-psi display quantization, sender accuracy, filtering and refresh rate
  remain unverified. Some small secondary-gauge values are approximate.
- During review the small SCG AFR text was initially misread as HLD AFR.
  Enlargement shows a numeric AFR readout; **no hold mode is established**.
  Do not use that discarded reading as evidence. Pressure units visible on
  the SCG are inHg under vacuum, whereas logged pressure is psi.

## Representative observations

| Video elapsed s | GlowShift pressure psi | Context |
| ---: | ---: | --- |
| about2.5 | 40 | Before VCM recording; vacuum still developing |
| about7.5–12.5 | 39 | Before VCM recording |
| 35 | 38 | Near beginning of nominal VCM overlap |
| about72.5 | 37 | During warm-up |
| 150 | 38 | Later steady running |
| 190 | 38 | Before nominal dip |
| 192 | 37 | Before nominal dip |
| 194 | 38 | Before nominal dip |
| 195–199 inspected samples | 37 | Includes nominal dip at video196.5s |
| 200 | 38 | After nominal dip |
| 205 | 37 | Later recovered running |

The gauge being below the owner-set43psi engine-off value is not by itself
failure: the1:1 manifold-referenced regulator should lower pressure under vacuum.
[Aeromotive's explanation](https://help.aeromotiveinc.com/article/253/tb202--efi-fuel-pressure-regulators-vacuum-and-boost-reference)
describes that relationship. A rough comparison of visible pressure and vacuum
does not independently establish an exact43psi injector differential: there are
gauge/sensor offsets, quantization, location and timing uncertainties. Verify
references before using those numbers to change injector characterization.

## What the stationary log adds

All15 requested channels have data in this run, including STIT, LTIT and CL
Active. VCM7,738rows over1.188–182.699s; one gap132.265–136.264s. Both recorders
finalized and exported. SCG timing relative to VCM remains provisional.
ECT166–188F; this is warming/hot-idle evidence, not a completed fan-cycle test.
Static pressure had been adjusted from the prior reported41psi to43psi, so
comparison with older recordings is not a matched pressure A/B test.

### Dip at VCM162.435s

| Elapsed s | RPM | Spark degrees | IAC command % | STIT lb/min | LTIT lb/min |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 161.503 | 905 | 4.5 | 40.39 | +0.0393 | -0.2014 |
| 161.993 | 880.5 | 5.75 | 40.66 | +0.0361 | -0.2014 |
| 162.197 | 865.25 | 6.75 | 41.29 | +0.0414 | -0.2012 |
| 162.435 | 763.75 | 15 | 46.54 | +0.0548 | -0.2012 |
| 162.591 | 865.75 | 6.75 | 42.40 | +0.0665 | -0.2012 |
| 162.903 | 953.5 | 1.75 | 39.83 | +0.0567 | -0.2012 |
| 163.191 | 899 | 4.75 | 40.43 | +0.0476 | -0.2012 |

Spark Source stays Idle Feedback; CL Active Yes and Fuel Source Stoich in these
rows. LTIT does not abruptly step. STIT and IAC rise through recovery, without
an observed correction collapse before the dip. Their different request/update
rates and export interpolation prevent claiming precise actuator or integrator
delay from the table. The IAC command still is not actual valve-flow measurement.

## Next focus

Keep the existing spark gain, target and fuel model unchanged while separating
the disturbance from corrective action. For this captured dip, stable-looking
displayed fuel pressure and no MBT switch make actual air-path/IAC response,
load changes and combustion consistency useful diagnostic priorities. They do
not establish a particular failed component or a replacement table value.

Next offline work should inspect the inherited idle-air integrator timing,
learning limits/eligibility and airflow/spark interaction using controller-
specific descriptions; inspect IAC connector/bypass and vacuum/reference paths
with the engine off. Preserve pressure feedback restoration as a separate
hardware/transfer task. No adaptation reset or deliberate repeat stall requested.

For any later targeted running capture: fixed camera showing fuel pressure and
tachometer together if possible, plus a clearly recorded common timing marker;
preserve full log/quality flags. No additional engine run was started for this
video review. No gain rollback or v013 is selected.

Manual readings, nominal alignment, source hashes and the detailed frame sheet
are preserved privately beside the original recordings. Raw video is not
published or placed in the tracked reports directory.
