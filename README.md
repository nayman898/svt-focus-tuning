# SVT Focus tuning

Calibration history, diagnostic reviews, and scanner profiles for a modified
2004 Ford Focus SVT.

## Current state — 2026-11-03

- **Installed working parent:** [v024](tunes/v024-fuel-cleanup-diagnostics.md),
  owner-confirmed flashed and tested with a new upstream O2 sensor. It is
  provisionally retained for the stationary conditions covered by the
  [latest review](reports/2026-11-03-v024-cold-cleanup-review.md).
- **Prepared candidate:** [v025](tunes/v025-maf-idle-offidle-smooth.md), derived
  from v024 with MAF transfer changes at 0.500–1.000 V. Saved, reopened and
  compared in Editor; **not flashed or tested**. Its immediate rollback is v024.
- **Next test:** [v025 regression card](docs/v025-regression-test.md) and
  [session run card](docs/v025-run-card.json). Verify the active profile and
  actual channel coverage before using a capture for comparison.
- **Scope:** stability and drivability remain unfinished. Stationary evidence
  does not establish road/boost validation or a proven root cause. Water/meth
  remains OFF; the SCG RPM wire remains disconnected.

The [revision catalog](tunes/revisions.json) records file identities, parents,
verification and outcomes. [vehicle.json](vehicle.json) retains hardware and
owner observations. Prepared, installed, tested and accepted are distinct states;
there is no new ECU readback implied by this repository update.

## Working references

- [Tune revision history](tunes/README.md) and [calibration reference](docs/calibration-reference.md).
- [Datalog workflow](docs/datalog-workflow.md), [operating profiles](profiles/operating-profiles.md),
  and [channel coverage](profiles/channel-coverage.md).
- [v021 complete calibration audit](reports/2026-11-02-v021-complete-calibration-audit.md).
- [Agent instructions](AGENTS.md) and [archived session notes](SESSION_HISTORY.md).

## Project layout

- [Historical lower-idle roadmap](docs/lower-idle-roadmap.md): previous 800-850 RPM goal, now deferred;
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
