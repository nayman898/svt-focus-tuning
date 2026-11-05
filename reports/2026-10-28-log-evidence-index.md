# Preserved log coverage for the stability roadmap

Every preserved vehicle-session folder was inventoried. Recognized VCM CSVs were read for headers, row counts, time ranges and missing fields. Existing detailed reviews supply interpretation of older LogWorks/native recordings; this is not a claim to have independently re-decoded every HPL/LOG binary. Derived CSVs and duplicate copies are not treated as additional independent runs.

| Session folder | Native files | CSV files | Recognized VCM exports |
| --- | ---: | ---: | ---: |
| `2026-10-26-idle-01` | 2 | 3 | 1 |
| `2026-10-26-v002-idle-01` | 2 | 3 | 1 |
| `2026-10-26-v003-idle-01` | 2 | 3 | 1 |
| `2026-10-26-v004-channel-test-01` | 1 | 1 | 1 |
| `2026-10-26-v004-idle-01` | 2 | 2 | 1 |
| `2026-10-26-v004-idle-02` | 1 | 1 | 1 |
| `2026-10-26-v005-closed-loop-01` | 2 | 4 | 1 |
| `2026-10-26-v005-closed-loop-02` | 2 | 3 | 1 |
| `2026-10-26-v005-fuel-recovery-01` | 2 | 2 | 1 |
| `2026-10-26-v005-koeo-channel-check` | 1 | 1 | 1 |
| `2026-10-26-v005-load-step-01` | 2 | 3 | 1 |
| `2026-10-26-v005-startup-01` | 1 | 1 | 1 |
| `2026-10-27-900-load-01` | 2 | 3 | 1 |
| `2026-10-27-v006-paired-idle-01` | 2 | 3 | 1 |
| `2026-10-27-v006-post-repair-01` | 2 | 3 | 1 |
| `2026-10-27-v006-startup-blower-01` | 2 | 3 | 1 |
| `2026-10-27-v007-idle-01` | 2 | 3 | 1 |
| `2026-10-27-v008-idle-01` | 2 | 3 | 1 |
| `2026-10-27-v009-drive-01` | 2 | 4 | 1 |
| `2026-10-27-v009-hot-restart-01` | 2 | 3 | 1 |
| `2026-10-27-v009-idle-dips-01` | 2 | 3 | 1 |
| `2026-10-27-v009-repeat-idle-01` | 2 | 3 | 1 |
| `2026-10-27-v010-drive-01` | 2 | 3 | 1 |
| `2026-10-27-v010-idle-01` | 2 | 2 | 1 |
| `2026-10-28-v012-fan-01` | 2 | 3 | 1 |

Native count includes HPL, LOG and SQLite; multiple files can be copies or separate segments. This table is coverage, not a pooled performance ranking. Hardware state, tune identity, temperatures, loads and clock alignment must stay attached to each recording.

The private inventory includes export hashes, row counts, time ranges and missing columns. The [roadmap](../docs/stability-and-drivability-roadmap.md) links the relevant detailed reviews.
# Subsequent intake: 09:34 on 2026-10-28

One additional session, `paired-20261028-093440-0223fe51`, was preserved and
reviewed after the inventory below. See the
[idle follow-up](2026-10-28-idle-followup-and-mechanical-hold.md). This brings
the preserved session-folder count to 26; the earlier 25-folder inventory below
is a dated snapshot. The new log includes brief low-speed movement and parked
idle, not a completed post-drive/fan validation. Running tests are now paused
for the owner-reported driver-side strut center-shaft failure.

# Subsequent survey: 2026-10-29

Three additional parked survey pairs are preserved under
`logs/2026-10-29-channel-survey/`; see [coverage results](2026-10-29-channel-survey.md).
These are three capture sessions inside one survey archive directory, not three
new top-level folders. Their native recordings, CSVs and requested profiles are
retained. Do not count this acquisition survey as three accepted tune validations.

# Later drive intake: 2026-10-29

`paired-20261029-161604-b543b769-v012` is preserved in
`logs/2026-10-29-v012-drive-01/`; see the [drive review](2026-10-29-v012-drive-review.md).
Owner confirms driveway stall while moving off; later parked dips recovered.
The earlier stationary gauge-video capture is separate, preserved under
`logs/2026-10-29-pressure-video-01/`; its video has not been received/reviewed.
Neither capture is a new accepted tune or dynamic fuel-pressure validation.

# Video evidence added: 2026-10-29

The preceding stationary pair now includes preserved phone video, manual gauge
readings and a [pressure/video review](2026-10-29-pressure-video-review.md).
This is added evidence for that existing session, not another engine test or
filmed evidence of the earlier spontaneous stall.

## 2026-11-05 — v035

[Pull review](2026-11-05-v035-pull-review.md): preserved paired-20261105-104453-2eb3afbb-v035; pull 1 6%, pull 2 invalid, pull 3 8%. Peak boost 13.85/15.32 psi for valid pulls; modest leaner shift versus selected v034 pull. No validated knock-retard channel; insufficient evidence for further power changes.
