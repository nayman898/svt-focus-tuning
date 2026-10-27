# SVT Focus tuning

Calibration history, diagnostic reviews, and scanner profiles for a modified
2004 Ford Focus SVT.

## Current baseline

- Prepared next file: [v006 post-repair fan baseline](tunes/v006-post-repair-fan-baseline.md),
  for use after the pending resistor/pigtail repair. It restores high-speed
  225/215 F while retaining low-speed 195/190 F and v005's other settings.
  [ECT idle-adder contingency](docs/fan-repair-and-idle-adder.md) is documented
  separately; no RPM adder was changed.
- Latest running experiment: [v005 absolute-TPS entry test](tunes/v005-idle-absolute-tps-entry-test.md).
  [Startup review](reports/2026-10-26-v005-startup-review.md) confirms closed-loop
  entry, but records a failed initial catch, large startup flare and reported
  cranking supply dip. Stationary idle scope remains; mixture is not validated.
  The [closed-loop AFR review](reports/2026-10-26-v005-closed-loop-review.md)
  provisionally pairs the delayed LogWorks capture and documents remaining
  electrical/load disturbances and measured mixture excursions.
- Earlier test: [v004 closed-loop-entry test](tunes/v004-idle-closed-loop-entry-test.md).
  Owner-supplied logs confirm no closed-loop entry. See the
  [result and logging audit](reports/2026-10-26-v004-log-review.md) for observed
  states, missing measurements and six added diagnostic channels. Stationary
  idle scope was retained for the following experiment.
- [Agent instructions](AGENTS.md) define calibration evidence, revision
  verification, logging and flash-readiness handoffs for this repository.
- MPVI4 communication confirmed over USB on 2026-10-26.
- VCM Editor 5.3.1332 Beta is installed.
- MPVI4 firmware is 1.33.1 Release; Pro Feature Set is licensed.
- One existing Ford controller license is present. Two credits purchased, two
  used, zero available. The connected vehicle VIN was subsequently confirmed
  to match that license; identifiers remain private.
- The initial device-only inspection was followed by vehicle connection,
  saved calibration revisions and owner-supplied post-write logs. Flash status
  is tracked per revision in the tune history.
- Owner reports a 2004 Focus SVT with a turbocharger, hardened rods, forged
  pistons, return-style fuel system, upgraded Stealth pump, blade-style MAF,
  water/methanol injection, LSD, SBC Stage 3 clutch, electric power steering,
  tubular lower control arms, fully adjustable rear suspension, and relocated
  battery. The modification list is incomplete; exact component specs, fuel,
  boost, and tuning goals remain to be confirmed in [the vehicle record](vehicle.json).
- Additional owner-reported specs: Siemens 60 lb/hr injectors, 93-octane fuel,
  43 psi base fuel pressure, Aeromotive 1:1 boost/vacuum-referenced regulator,
  PMAS blade-style MAF in a nominal 3-inch housing, and Innovate SCG-1 AFR/boost
  controller. The current tune was supplied by the previous owner; the goal is
  to improve it. Exact injector/MAF identifiers, boost settings, water/meth details,
  and wideband logging integration remain unconfirmed.

## Project layout

- [Lower-idle roadmap](docs/lower-idle-roadmap.md): owner goal of 800-850 RPM
  warm idle, priority checks and staged target-only trials; startup-airflow
  proposal deferred as a separate experiment.
- [v003 timing review](reports/2026-10-26-v003-timing-review.md): how idle spark
  responds during RPM dips, temporary fan-path results and IMRC follow-up.
- [v002 idle review](reports/2026-10-26-v002-idle-review.md): first post-write
  comparison, temperature-matched idle statistics and the remaining load/AFR issues.
- [First idle review](reports/2026-10-26-idle-review.md): ECU RPM is recorded,
  high commanded idle, inactive closed-loop reporting, AFR variation, a voltage/RPM
  event, and missing-channel follow-up.
- [Clock and calibration review](reports/2026-10-26-clock-and-calibration-review.md):
  provisional six-second clock pairing, inspected idle/fuel settings, and a
  proposed idle-target test.
- [Device baseline](docs/device-baseline.md): verified software and hardware state.
- [First vehicle session](docs/first-connection.md): backup and initial log procedure.
- [Tuning plan](docs/tuning-plan.md): idle, cruise, SCG-1 boost control, then power.
- [Scanner setup](profiles/README.md): saved idle/cruise channels and layout,
  working Vehicle Defaults captured with live data confirmed; individual
  channels and layout mappings still need full saved-log validation.
- [Vehicle record](vehicle.json): vehicle details to confirm before tuning.
- `backups/`: original ECU reads, preserved without overwriting.
- `logs/`: scanner recordings and CSV exports.
- [Tune revisions](tunes/README.md): versioned HPT binaries, parent revisions,
  SHA-256 catalog, changes and test/flash status.
- `.local/`: private interface reports and vehicle identifiers.

Raw logs, working backups and private reports are ignored by Git. Numbered tune
binaries under `tunes/` are tracked at the owner's request in the private
[GitHub repository](https://github.com/nayman898/svt-focus-tuning).
The revision catalog records each file's SHA-256 hash and size; committing a
revision does not mean it has been flashed or validated.
