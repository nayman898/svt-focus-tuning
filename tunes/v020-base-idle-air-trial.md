# v020 — base idle-air bias trial

**Rejected after owner-reported installed test2026-11-02.** Owner reports increased
stuttering; saved capture shows25sub900RPM dips/minute in the160–170F normal-loop
window. Conditions differ fromv019, so causality is not quantified. Return to
exactv019 recommended, not confirmed. See [test review](../reports/2026-11-02-v020-base-air-review.md).
The preparation/verification and original prediction below are preserved.

- Candidate: [v020-base-idle-air-trial.hpt](v020-base-idle-air-trial.hpt)
- Exact parent/rollback: [v019](v019-maf-low-flow-trial.hpt)
- Size:247277bytes
- SHA256:`17F421379EA038CE1938EDD8A080F6D517DCF90CE60CABC340B4CFB8C3ACADDA`

## Question and intervention

Does reducing the base-air contribution around the current target reduce the
negative idle-air correction and alter the repeated dip/rebound behavior?
This tests a model bias/operating-point hypothesis; it does not tune hidden PI
gains and does not presume a faulty IAC. The owner explicitly requests bounded
intervention-led testing rather than a proven root cause before every experiment.

Only these four body cells change, plus appended Notes:

| Table | Desired RPM | Parent lb/min | Saved v020 lb/min |
| --- | ---: | ---: | ---: |
| P/N44242 | 900 | 0.40537700057029724 | 0.3851081430912018 |
| P/N44242 | 1000 | 0.46118998527526855 | 0.4381304979324341 |
| Drive44239 | 900 | 0.40537700057029724 | 0.3851081430912018 |
| Drive44239 | 1000 | 0.46118998527526855 | 0.4381304979324341 |

Requested reduction5%; tiny differences reflect saved numerical precision.
All10RPM axes and other8body values in each table remain exact. Both branches
receive the same edit to avoid an unobserved P/N-versus-Drive transition changing
the experiment. Adjacent interpolation700–900 and1000–1250 is affected too;
this is not gated only by warm temperature and can affect late warmup/hot-start.

Nominal base-table value at logged desired944 falls about0.429935 to0.408438,
a0.02150lb/min difference before temperature/runtime multipliers. At184F/final
runtime row, the nominal difference is~0.02214lb/min. These are table arithmetic,
not a guaranteed change in total flow, duty percentage or observed corrections.

Retain nominal950RPM targets, spark gain1/floor−6, v019MAF, injector/pressure/
closed-loop/fueling settings, VCT, dashpot, fans, diagnostics and protections.
MethOFF and SCG RPM wire disconnected. No boost/driving test in this trial.

## Predicted observations and decisions

| Result under matched warm conditions | Meaning / decision |
| --- | --- |
| Idle-air correction becomes less negative, dips fewer/shallower, recovery no worse | Supports retaining this operating-point change provisionally; not proof of root cause |
| Correction becomes less negative, dips unchanged | Base-air bias responds as expected but is not sufficient to fix oscillation; do not keep cutting air blindly |
| No reproducible correction shift | First verify branch, fresh channels, adaptation/learning and conditions; result is inconclusive, not proof of hardware failure |
| Mean RPM falls, dip depth/duration or recovery worsens, near-stall/stall or hunting increases | Reject and roll back exactv019 |
| Cold rich/FMEm occurs again | End test; this revision does not address that mechanism and must not be judged as warm-idle evidence |

Corrections may redistribute between STIT and LTIT; evaluate both and their
combined trend, without assuming a complete known demand sum. Do not reset
adaptations solely to force the predicted result. If flashing/relearn changes
the learning state, separate early settling from the comparable interval.
Compare target-relative RPM error, event rate, depth/duration, rebound and
wideband/trims, not smooth spark alone. Different starting conditions restrict
causal attribution; a subsequent return tov019 is the confirming A/B step if needed.

## Short supervised test

The loaded [Base Air Trial18 profile](../profiles/2004%20Focus%20SVT%20-%20Base%20Air%20Trial.Channels.xml)
requests RPM/target/ECT/voltage, timing/source, fuel source, TPS, MAF/rawMAF,
IAC, O2, CL, STFT, runtime, STIT/LTIT andFMEm. Saved-back definitions match.
No live admission yet; the preceding24-channel profile lostECT/TPS and is not
used here. This profile deliberately has no new cam requests.

1. Owner confirms correct candidate flashed; no agent write/readback. Start
   paired recording labelled`v020-base-air` before engine start.
2. Verify ECT/TPS/essential channels and valid SCG readings. If coverage fails,
   save that admission attempt; do not use a blind long warmup or discard startup.
3. Warm supervised only if running is acceptable. ColdCL/FMEm problem remains;
   do not continue sustained rich/rough running just to reach this trial.
4. Once warm, target is settled, CLactive/FMEmoff and mixture reasonably settled,
   record60–90seconds with accessories/throttle unchanged or a few dips. Do not
   wait for a fan event; mark one if it occurs. Stop sooner for worsening behavior.
5. Stopboth/export, verify both natives andCSVs. Judge against matchedv019warm
   conditions. No extra unchanged run without a new question.

## Verification

Created using EditorSaveAs from exactv019. Saved/reopened, full-precision axes
and body points verified. Whole-file comparison lists exactly two base-air
tables andNotes. Full parentNotesprefix retained. All20prior binaries match
cataloged hash/size. [Machine delta](../reports/calibration-inventory/v020/delta.json).
This verifies saved-file edits, not ECU installation or improved operation.
