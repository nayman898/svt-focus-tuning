# v004 recovery and flash-readiness review

Historical pre-test assessment. Subsequently supplied v004 logs showed no
closed-loop entry; see the [post-test review](2026-10-26-v004-log-review.md)
for current status and logging changes.

## Decision

**Prepared candidate for an owner-initiated stationary warm-idle experiment.**
The available evidence supports proceeding within the existing v004 test scope,
conditional on correct vehicle/file selection, stable write power, working
SCG-1 measurement and no active condition preventing the test. Those live
conditions were not verified in this review. Driving and boost are unvalidated.

Candidate: [v004](../tunes/v004-idle-closed-loop-entry-test.hpt).
Rollback: [v003](../tunes/v003-temp-fan-stage-match.hpt).
Full test rationale: [v004 notes](../tunes/v004-idle-closed-loop-entry-test.md).

## Where work stopped

- Latest commit at review start: `0c378a2`, preparing v004.
- v003 has owner-supplied test recordings and a
  [timing/fueling review](2026-10-26-v003-timing-review.md).
- v004 was saved, reopened and compared; no agent write was recorded.
  No v004 session recordings were found in the repository. Its actual ECU
  installation is therefore unconfirmed; do not label it tested or accepted.
- Prior verification found an accidental injector-pressure-compensation toggle,
  restored Enabled to match v003, and repeated saved-file verification.

## Checks performed in this review

All six HPT revisions match both SHA-256 and byte length in the
[catalog](../tunes/revisions.json). v004 is 217,053 bytes with SHA-256:

`0AAB020810888ABDE0A029E60199AB4D2A1DFD97B24A19E1BE566EB115517B18`

The private saved comparison lists only Notes and Open Loop Fuel TPS Thresh
vs. RPM. The saved seven-row extraction contains 8.00 at 0/1,500 rpm and 0.00
at 2,000/2,500/5,500/6,500/16,384 rpm. The running Editor's title identifies
v004 in comparison mode; its visible comparison log lists Notes and this table.
This review inspected that existing comparison and historical row extraction;
it did not independently reopen the binary or repeat every cell inspection.
Hashes establish that the saved binary has not changed since cataloging.

The change tests whether the zero TPS open-loop threshold explains persistent
Power Demand Enrich at warm idle. Eight A/D counts is a trial boundary, not a
verified universal threshold. Interpolation also changes 1,500-2,000 rpm.
The 1,100 rpm idle settings, temporary 195/190 F fan thresholds, 254-second
startup gates, disabled LTFT and enabled injector pressure compensation remain
documented as inherited. The fan voltage/RPM disturbance is unresolved.

## Owner's next session

1. Select the exact candidate above, verify the correct controller and stable
   write power, and follow Editor's ignition/engine-state prompts.
2. After the write, record the flashed filename. Start VCM Scanner and LogWorks
   recordings from restart and keep the initial test stationary, without throttle.
3. Capture fully warm idle beyond 254 seconds after start: approximately 6-8
   minutes total, extending if necessary for warm coolant and a settled segment.
   Record fan/accessory events and observe SCG mixture, RPM and voltage.
4. Check whether Closed Loop Active becomes Yes; also inspect fuel source,
   O2 response, commanded lambda, measured mixture and usable STFT. A loop flag
   alone does not demonstrate good fueling or a completed tune.
5. Stop if idle/mixture deteriorates or cooling/electrical behavior becomes
   abnormal. Use v003 as calibration rollback; unresolved hardware problems
   still require repair. Save native files and CSV in a fresh v004 session.

No calibration binary, scanner profile, SCG-1 setting or ECU state was changed
by this review. Repository agent guidance was added in [AGENTS.md](../AGENTS.md).
