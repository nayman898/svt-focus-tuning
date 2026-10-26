# Tune revisions

Tune binaries in this directory are versioned in local Git at the owner's
request. No remote repository or publication has been configured.

| Revision | File | Basis and changes | Flash status |
| --- | --- | --- | --- |
| v000 | [Earlier ECU read](v000-ecu-read-20261026-102710.hpt) | Archived HP Tuners vehicle-cache read dated 2026-10-26 10:27:10. Differences from v001 have not been cataloged. | Historical capture; not a test candidate |
| v001 | [Current baseline](v001-baseline-with-mil.hpt) | Exact copy of SVT Base (from chuck). Owner confirms this is a fresh ECU read plus their MIL changes. | Owner-confirmed current baseline |
| v002 | [Idle 1100 test](v002-idle-1100.hpt) | Derived from v001. P/N idle target 1,200 to 1,100 rpm; Drive idle target 1,200 to 1,100 rpm. | Prepared; not flashed by the agent |

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

## Test and rollback

This is an isolated idle-target trial, not an established optimum. After a
deliberate user-initiated write, record the flashed revision name and repeat
warm idle plus a radiator-fan cycle using both VCM Scanner and LogWorks. Label
both recordings with the tune revision. The previous fan-start voltage dip
still needs investigation. Use v001 for rollback to the supplied baseline.

Keep separate recordings from different revisions in separate session folders.
Record keep/revert decisions here or in the next revision's notes. Never
overwrite a numbered revision with later edits; assign the next version number.
Committing a tune file does not mean it has been flashed or validated on the car.
