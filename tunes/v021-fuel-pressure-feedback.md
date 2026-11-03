# v021 — fuel-pressure measurement baseline

Owner-designated baseline. A v021-labeled run on2026-11-02 verified consistent
raw/convertedpressure in its operatingrange; warmdips persist. No ECUreadback.
See [baseline review](../reports/2026-11-02-v021-baseline-review.md).
This restores the pressure measurement function, not an
exact recovered factory calibration. All future candidates should use this
baseline once installed/validated unless explicitly documenting another parent.

Candidate: [v021-fuel-pressure-feedback.hpt](v021-fuel-pressure-feedback.hpt).
Exact parent/rollback: [v019](v019-maf-low-flow-trial.hpt). The rejectedv020air
reduction is not inherited. Size247597bytes; SHA256
`078E91786A07793A4EB6607B8B870BDC9558562C0FE75AF95E6D5AB1A1A87ACA`.

## Only calibration change: ECM7596

| Retained input A/D count | v019 psi | Saved v021 psi |
| ---: | ---: | ---: |
| 0 | 40 | 0 |
| 0 | 40 | 0 |
| 0 | 40 | 0 |
| 0 | 40 | 0 |
| 102 | 40 | 0 |
| 921 | 40 | 70 |
| 1023 | 40 | 78.71794891357422 |

Nominal gasolineFordFRP range0.5–4.5V corresponds to0–70psi. Existing rounded
10bitA/D anchors102/921 are retained; working slope70/819psi percount. Below102
clamped0psi; above921same slope extended to1023. These endpoint choices are
explicit engineering handling, not a claim to have recovered original OEM bytes.
The duplicate0axes predate this edit and remain unchanged; all have equal0output.
Below0.5V behavior is not a negative-pressure measurement. Fault thresholds are
unchanged. Use the raw voltage as well when evaluating low/out-of-range inputs.

[Ford gasoline chart](https://www.fordservicecontent.dealerconnection.com/pubs/content/~WVX2/~MUS~LEN/15/VX25013.HTM)
supports the nominal endpoints; [Ford2009OBDsummary, p136](https://www.fordservicecontent.com/ford_content/catalog/motorcraft/OBDSM903.pdf#page=136)
provides the continuous-voltage curve and3.00V/43.75psi example. These are primary
architecture/nominal-transfer sources, not an exact UJAHAS3 factory file. Original
SVTsensor owner-confirmed; its exact markings/VREF/absolute accuracy not separately
bench-verified. OwnerKOEO43psi/~3V andrunning39psi/−13inHg/3.07V provide independent
operating-point consistency. Do not force the curve through approximate gauge data.

Readings are pressure across injectors, not regulator atmospheric-gauge pressure.
At~3V expect~43.75psi; at3.07V expect~45psi. Small differences from continuous
voltage arithmetic arise from roundedcountanchors. Do not add manifoldvacuum
again: the physical sensor reference already supplies that pressure reference.

## Retained and possible consequences

Retain40psi injector characterization reference, slopes/offsets/breakpoint and
all pressure multipliers, pressure compensation switch,6950zero, desiredpressure
tables, pump/diagnostic settings. Retainv019MAF,950targets, baseair, gain1/floor−6,
VCT/dashpot/fans/protections. Methoff andSCGRPMwire disconnected.

The relay-fed pump remains physically outside ECU speed control. Restoring a
measurement does not restore that control authority. However, changed measured
pressure may affect ECU diagnostics/model paths; do not claim the change is
necessarily display-only or guaranteed to fix idle. Exposed pressure multipliers
were previously neutral; no compensating model changes are bundled here.

## First check after owner flash

1. Engineoff/pumpon: compare independent gauge, raw voltage and converted ECU
   pressure simultaneously. At atmospheric manifold pressure the two pressure
   references should agree within measurement/rounding uncertainty. A persistent
   flat40 reading means this integration is not yet verified.
2. If plausible and installation leak-free, short supervised idle with paired
   SCG recording. Log raw/convertedFRP, RPM/target, ECT/TPS, IAC,STIT/LTIT, spark,
   STFT/O2 andCL/FMEm. Stop if pressure conversion is inconsistent, running
   deteriorates or sustained rough/rich operation occurs. No driving/boost check.
3. Compare normal-loop settled behavior withv019 and independently note whether
   FMEm reappears. Do not timestamp a DTC fromFMEm alone or reset adaptations/codes.
4. Rollbackexactv019 for an incorrect conversion or adverse ECU response, while
   preserving raw sensor logging. Keep numberedbaseline and outcome notes even
   if rollback is needed. No repeated unchanged long warmup requested.

Native Scanner definitions6502FuelPressure and6507rawFuelPressureSensor were
saved together in the20-channel pressure-baseline profile. Profile configuration
is verified; fresh20-channel runtime coverage and semantic response are pending.

## File verification

Saved viaEditorSaveAs fromexactv019; reopened7outputs andallaxes verified.
Whole-file comparison onlysensortransfer+Notes. FullparentNotesprefix retained;
all21earlierfilehashes/sizes match. No agentECUwrite/readback/reset. See
[machine delta](../reports/calibration-inventory/v021/delta.json).
