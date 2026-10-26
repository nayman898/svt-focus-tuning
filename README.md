# SVT Focus tuning

Local project for the Ford SVT Focus: original calibration backups, diagnostic
baselines, scan logs, and documented calibration changes.

## Current baseline

- MPVI4 communication confirmed over USB on 2026-10-26.
- VCM Editor 5.3.1332 Beta is installed.
- MPVI4 firmware is 1.33.1 Release; Pro Feature Set is licensed.
- One existing Ford controller license is present. Two credits purchased, two
  used, zero available. Whether that license matches this car remains unverified.
- The interface was not connected to the car. No ECU read, scan, flash, firmware
  update, or credit purchase was performed.
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
binaries under `tunes/` are tracked at the owner's request. This repository is
local; no GitHub repository or remote has been created.
