# Tuning sequence

## Current next step — 2026-11-03

The installed working parent is v024, owner-confirmed tested with a new upstream
O2 sensor. v025 is prepared from v024 but not flashed or tested. Use the
[v025 regression card](v025-regression-test.md) for staged stationary validation;
v024 is its immediate rollback. See the [current repository state](../README.md)
and [latest review](../reports/2026-11-03-v024-cold-cleanup-review.md).

Stability and ordinary drivability remain the priorities; further idle-target
reductions are deferred. Evaluate the candidate before selecting another change.
Broader road/boost validation remains separate unfinished work.

## Historical sequencing — 2026-10-28

The [stability and drivability roadmap](stability-and-drivability-roadmap.md)
records the earlier v012 plan. The sequence below preserves that planning
context; pressure-feedback integration and later trials are now documented in
the [revision catalog](../tunes/revisions.json).

| Order | Work | Decision required |
| --- | --- | --- |
| 1 | Verify useful logging coverage; hot restart and ordinary stationary load recovery | Retain or revert the existing baseline based on actual RPM/mixture/recovery |
| 2 | Same-file light-load drivability and post-drive idle comparison | Identify a repeatable remaining symptom and its operating state |
| 3 | Resolve adaptation/mode and actual fuel-pressure evidence | Choose one supported calibration branch, if needed |
| 4 | OEM pressure-feedback integration after hardware validation | Verified transfer, pump control and injector implications before a separate revision |
| 5 | Broader drivability and remaining startup/IMRC work | Repeatable behavior in each tested condition |
| Later | Boost control and power | Fuel delivery, injector data, hardware settings and water/meth dependency established |

Every future calibration needs an exact tested parent, one causal change,
reopened comparison, preserved Notes, hash/size, rollback and an explicit result.
The owner performs writes; preparing a file does not flash or validate it.
