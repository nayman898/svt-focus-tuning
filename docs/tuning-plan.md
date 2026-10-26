# Tuning sequence

Owner priorities recorded 2026-10-26: optimize idle and cruise first, then work
on SCG-1 WGDC and gain, and pursue power after selecting a stable boost-control
setup the owner is comfortable with. No numerical targets or changes have yet
been selected.

| Stage | Work to document | Evidence before moving on |
| --- | --- | --- |
| Baseline | Preserve the existing ECU read; record faults, hardware identifiers, fuel, SCG-1 settings, and wideband logging setup | Original calibration saved; available channels and missing hardware information identified |
| Idle | Record cold start, warm-up, fully warm idle, hot restart, and response to normal accessory loads | Logs and owner observations show acceptable starting and idle behavior; remaining faults explained |
| Cruise | Record steady light-load operation and gentle transitions under repeatable conditions | Logs and owner observations show acceptable fueling and drivability in the tested conditions |
| Boost control | Document wastegate hardware/plumbing, spring pressure, all existing SCG-1 settings, intended boost range, and water/meth operation; then assess WGDC and gain changes individually | Measured boost response is repeatable and acceptable; limits and fallback behavior documented |
| Power | Review fueling, ignition, boost, and repeatability using the established baseline | Each revision has corresponding measurements and an explicit keep/revert decision |

## First data still needed

- Untouched ECU read and initial diagnostic codes.
- Injector part number and characterization source; exact PMAS sensor model
  and installation location.
- SCG-1 logging connection and configured output scaling.
- Turbo, wastegate, spring pressure, current boost, and current controller settings.
- Water/meth mixture, flow, activation, failsafe, and whether the current tune
  depends on injection.

The reported fuel pressure is **43 psi with the engine off**. This records the
measurement conditions provided; pump operation and regulator reference hose
state during the measurement remain unconfirmed.

## Revision record

For each test, record the tune filename, exact changes, SCG-1 settings, fuel,
water/meth state, temperatures, observed symptoms, log filenames, and keep/revert
decision. Preserve the previous calibration and controller settings. Identify
ECU calibration revisions separately from SCG-1 controller changes.

This is a sequencing and evidence plan. Specific settings and test procedures
will follow review of the actual tune, logs, hardware, and controller documentation.
