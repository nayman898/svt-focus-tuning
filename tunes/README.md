# Tune revisions

Latest prepared candidate: [v025 MAF smoothing](v025-maf-idle-offidle-smooth.md),
from exact v024. Saved, reopened and compared; **not flashed or tested**.
Use the [v025 regression test](../docs/v025-regression-test.md).

Installed working parent and immediate rollback: [v024](v024-fuel-cleanup-diagnostics.md),
owner-confirmed tested on 2026-11-03 with a new upstream O2 sensor. Acceptance
is provisional and limited to covered stationary conditions. See the
[latest review](../reports/2026-11-03-v024-cold-cleanup-review.md).

The table below is historical; each status describes that revision's recorded
outcome, not the current installed file. The [catalog](revisions.json) records
all binary identities and parent relationships.

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
| v006 | [Post-repair fan baseline](v006-post-repair-fan-baseline.hpt) | Restore high-speed ECT 195/190 to earlier 225/215 F; low-speed stays 195/190; Notes appended. [Requirements and verification](v006-post-repair-fan-baseline.md). | Owner explicitly confirms this exact file installed after resistor repair. Warm fan recovery reviewed; [latest blower comparison](../reports/2026-10-27-v006-startup-blower-review.md) supports a separate target trial. Startup O2/supply follow-up remains. No agent write/readback. |
| v007 | [1,000-RPM idle target trial](v007-idle-1000.hpt) | ECM44218 P/N and44217 Drive: 1,100 to1,000 RPM; Notes appended. [Verification and scope](v007-idle-1000.md). | Owner confirms installed. [Unloaded review](../reports/2026-10-27-v007-idle-fluctuation-review.md): mean1,000 after150s, feedback active, no fan/load validation in this clip. v006 fallback. |
| v008 | [950-RPM idle target trial](v008-idle-950.hpt) | Same two targets: 1,000 to950 RPM, plus Notes. [Verification and scope](v008-idle-950.md). | Owner confirms exact file installed. [Monitored review](../reports/2026-10-27-v008-fan-recovery-review.md): one inferred fan cycle and65s recovery; brief835.5 dip recovers within seconds. Separate blower/hot-restart acceptance remains. No agent write/readback. |
| v009 | [900-RPM idle target trial](v009-idle-900.hpt) | Same two targets: 950 to900 RPM, plus Notes. [Verification and scope](v009-idle-900.md). | Owner confirms exact file installed without edits for [latest900 run](../reports/2026-10-27-900-load-capture.md). Last-minute mean900.62; recovered fan/load dip810.75. Hold900 for off-idle review; hot restart and driving unvalidated. No agent write/readback. v008 rollback. |
| v024 | [Fuel cleanup & diagnostics](v024-fuel-cleanup-diagnostics.hpt) | From exact v021. ECM44511 two 2,500-RPM cells (1.07/1.14 -> 1.00); ECM50 P0190/P0192/P0193 to MIL Light; Notes appended. 251,773 bytes; SHA-256 `80EF77A8B1E4DE7E60D3754495A01CEF30C5AB707AD00F789DD520A647363E1E`. [Verification and scope](v024-fuel-cleanup-diagnostics.md). | Tested 2026-11-03 with new upstream O2 sensor; cold start, warm idle, and fan-off recovery clean; [review](../reports/2026-11-03-v024-cold-cleanup-review.md). Provisionally adopted as parent for v025 in covered stationary modes; no ECU readback. |
| v025 | [MAF idle & off-idle smoothing](v025-maf-idle-offidle-smooth.hpt) | From exact v024. Single-table ECM12163 MAF transfer smoothed across columns 6–13 (0.500–1.000 V); all other 22 columns and all 30 voltage breakpoints identical to v024. 255,949 bytes; SHA-256 `2EFC9FFA0AC51A87E079F68F42AEBB06FECD60E91DC5651D15A805F92A715E17`. [Verification and scope](v025-maf-idle-offidle-smooth.md). | Prepared candidate; saved/reopened/compared in VCM Editor; ready for owner flash and staged testing under [v025 regression test](../docs/v025-regression-test.md). Rollback v024. |

Prepared next revision: [v010 gain1.500](v010-idle-spark-gain-1p5.hpt), from
owner-confirmed v009. Only ECM47996 gain2.000 to1.500 plus Notes;900RPM retained.
Saved/reopened/compared and all parent hashes preserved. Not flashed/tested or
accepted for driving. See [trial rationale and stop criteria](v010-idle-spark-gain-1p5.md).

Latest prepared: [v011 gain1.250](v011-idle-spark-gain-1p25.hpt), exact parent
owner-confirmed tested v010. Only ECM47996 gain1.500 to1.250 plus Notes;900RPM
retained. Saved/reopened/compared, all parent hashes preserved. Not flashed or
tested. See [verification and test criteria](v011-idle-spark-gain-1p25.md).

Latest prepared alternative: [v012 gain 1.000](v012-idle-spark-gain-1p0.hpt),
directly from v010. Owner confirms v011 remains unflashed. Only gain and Notes
changed; saved/reopened/compared. See [verification and criteria](v012-idle-spark-gain-1p0.md).

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
