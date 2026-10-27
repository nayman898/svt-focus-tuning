# Tune revisions

Numbered tune binaries are preserved in this private repository at the owner's
request. Original working backups and raw logs remain local and are ignored
by Git.

| Revision | File | Basis and changes | Flash status |
| --- | --- | --- | --- |
| v000 | [Earlier ECU read](v000-ecu-read-20261026-102710.hpt) | Archived HP Tuners vehicle-cache read dated 2026-10-26 10:27:10. Differences from v001 have not been cataloged. | Historical capture; not a test candidate |
| v001 | [Current baseline](v001-baseline-with-mil.hpt) | Exact copy of SVT Base (from chuck). Owner confirms this is a fresh ECU read plus their MIL changes. | Owner-confirmed current baseline |
| v002 | [Idle 1100 test](v002-idle-1100.hpt) | Derived from v001. P/N idle target 1,200 to 1,100 rpm; Drive idle target 1,200 to 1,100 rpm. | Owner reports write completed; [first post-write review](../reports/2026-10-26-v002-idle-review.md) supports retaining as test baseline; fan/load and AFR issues remain |
| v003 | [TEMP fan-stage match](v003-temp-fan-stage-match.hpt) | High-speed temperature thresholds 225/215 to 195/190 F, plus embedded temporary-path notes. [Test and retirement](v003-temp-fan-stage-match.md). | Owner supplied test logs; [review](../reports/2026-10-26-v003-timing-review.md) shows modest observed improvement but persistent voltage/RPM disturbance; remains temporary |
| v004 | [Idle closed-loop entry test](v004-idle-closed-loop-entry-test.hpt) | OL TPS threshold at 0/1,500 rpm: 0 to 8 counts. Other cells unchanged; inherited temp fan path. [Scope, verification and test](v004-idle-closed-loop-entry-test.md). | Owner supplied test logs; [review](../reports/2026-10-26-v004-log-review.md) confirms no closed-loop entry, including fully warm operation beyond startup delay. Not accepted as a fix; stationary idle scope retained. |
| v005 | [Absolute TPS entry test](v005-idle-absolute-tps-entry-test.hpt) | Same two low-RPM TPS cells: 8 to 200 counts, based on historical closed-throttle absolute TPS of about 182-184. [Hypothesis, verification and test](v005-idle-absolute-tps-entry-test.md). | Owner running session; [saved startup review](../reports/2026-10-26-v005-startup-review.md) shows CL entry at 75.636 s, an initial failed catch, a 2,915-RPM flare and reported cranking voltage down to 7 V. Stationary-only experiment; not accepted as a finished tune. |
| v006 | [Post-repair fan baseline](v006-post-repair-fan-baseline.hpt) | Restore high-speed ECT 195/190 to earlier 225/215 F; low-speed stays 195/190; Notes appended. [Requirements and verification](v006-post-repair-fan-baseline.md). | Saved, reopened and compared against v005; only two high-speed thresholds and Notes differ. For use after proper resistor/pigtail circuit restoration; hardware repair pending, not flashed by agent. |

## v002 verification

- VCM Editor's comparison log against v001 listed exactly two changed
  parameters: Target Idle Speed Park/Neutral and Target Idle Speed Drive.
- Both changed values were checked as 1,100 rpm in the main file.
- The saved v002 file was reopened from disk and both values still read
  1,100 rpm.
- No other calibration differences were reported by the comparison log,
  including no additional MIL changes.
- The original owner source and v001 have matching SHA-256 hashes.
- [Revision catalog](revisions.json) records hashes and parent revisions.

## v002 test and rollback

The v002 revision is an isolated idle-target trial, not an established optimum. After a
deliberate user-initiated write, record the flashed revision name and repeat
warm idle plus a radiator-fan cycle using both VCM Scanner and LogWorks. Label
both recordings with the tune revision. The previous fan-start voltage dip
still needs investigation. Use v001 for rollback to the supplied baseline.

Keep separate recordings from different revisions in separate session folders.
Record keep/revert decisions here or in the next revision's notes. Never
overwrite a numbered revision with later edits; assign the next version number.
Committing a tune file does not mean it has been flashed or validated on the car.
