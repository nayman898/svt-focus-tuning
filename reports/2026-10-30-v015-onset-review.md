# v015 first cold-start/onset capture

Owner-confirmed v015 installed. Owner reported small dips; recording stopped
and exported to preserve onset without extending toward another stall. Both
recorders finalized successfully. No new tune or ECU write was performed.

Source paired-20261030-124803-22ef9d06-v015; native files and SQLite API backup
preserved privately under logs/2026-10-30-v015-idle-01. Integrity/finalization
passed, manifest saved with no missing files/errors, all16 cataloged tune
hashes/sizes unchanged.

## Timing and coverage

The owner restarted VCM recording to populate values; SCG continued. The original
manifest VCM start event is not the restarted file origin. Native CSV creation
stamp16:49:04Z gives provisional SCG elapsed = VCM elapsed +60.108634s.
The initial VCM segment is not confirmed preserved. No claim of exact
cross-device synchronization or measured exhaust delay is made.

Saved VCM has19,386rows,1.265–466.089s; all16 requested fields have data.
Gaps occur66.500–73.534,214.223–218.784 and308.096–316.793s.
Engine runtime reaches255s and stays there, consistent with its known limit;
that is not evidence that the engine stopped aging or its timer reset.

## State transitions and dips

| VCM seconds | ECT | Reported closed-loop state |
| ---: | ---: | --- |
| 1.265 | 56F | No |
| 47.040 | 78F | Yes |
| 146.427 | 118F | No |
| 426.842 | 158F | Yes |

The intervening long open-loop portion reports Cold Eng./Startup. The deepest
sample, at420.189s, is799RPM against912 desired, ECT158F, CLNo, startup fuel,
28.5degrees/BaseMBT, IAC38.42%, module13.625V, STIT-0.2833lb/min and LTITzero.
This is6.65s before the recorded CL reentry. These exported states do not prove
the initiating cause, but this dip cannot simply be labeled active closed-loop
fuel hunting. No zero-RPM/stall appears in this retained VCM segment.

Target idle is still descending through warm-up:960–1024RPM in300–360s,
912–960 in360–420s, then896–912 in420–466s. Actual-minus-desired RPM variability
increases across these windows (standard deviation12.6,21.9,32.4RPM), so the
growing dips are not explained merely by the declining requested target.

## New air-adaptation evidence

STIT averages about-0.2995lb/min in300–360s and-0.2953 in360–420s, becoming
less negative at-0.2651 in420–466s. LTIT PN/ACoff stayszero in these windows.
STIT is idle-air correction, not fuel trim. The near-0.30 plateau deserves
comparison with actual controller limits and scheduled base airflow; it is
not yet a verified integrator clamp or proof that additional base air is needed.

Provisional SCG means progress fromlambda0.887 at330–360s,0.907 at360–390,
0.938 at390–420,0.984 at420–450 and1.003 at450–466s. Mixture is changing as
the warm target and reported fuel state change. Do not derive a pointwise
fuel correction from this alignment.

## Next decision

This stopped at approximately162F and is a cold-start/onset test, not the
requested fully warm180–195F parked validation. It provides useful evidence
without requiring another stall. No new numerical tune change selected.

Read-only investigation should now connect:

- Why reported fuel/loop states move Yes→No→Yes during warm-up, including
  the verified158F warm-base enable boundary and other actual conditions.
- The changing desired idle, scheduled base-air multipliers and negative STIT
  as startup support decays; verify applicable integrator limits before edits.
- Fuel-command/trim semantics, actual mixture and sensor readiness, preserving
  the distinction between cold/startup operation and settled feedback.

P0320 timing/resolution remains unverified. Engine shutdown was advised; no
recording or unattended monitoring remains active.
