# v016: 950 RPM idle-margin trial

Prepared and verified, **not flashed or tested**. The owner approved a950RPM
trial to make a controlled change after repeated900RPM dips.

Candidate: [v016-idle-margin-950.hpt](v016-idle-margin-950.hpt).
Parent and rollback: [v015-restore-closed-loop.hpt](v015-restore-closed-loop.hpt).

| Editor setting | v015 | v016 |
| --- | ---: | ---: |
| ECM44218 Target Idle Speed Park/Neutral |900 RPM|950 RPM|
| ECM44217 Target Idle Speed Drive |900 RPM|950 RPM|

These are the only calibration differences; revision Notes were appended while
retaining the complete parent history. Saved candidate was reopened, both targets
read950, and Editor comparison against exactv015 listed only these two settings
and Notes. All16 earlier cataloged tune files retain their sizes and hashes.

Size:239085bytes.
SHA-256: `7F069587C62FACC4A2E79556A48131A2DF7D527BFE0B9ECA5E388291BF410D14`.

## Why this change

The [load-step test](../reports/2026-10-30-v015-load-step-review.md) held900RPM
on average but dipped to684.5 near a reported fan activation. Settled fan periods
were steadier, but blower-on and unloaded operation both contained dips. This
supports testing a modest speed-margin increase, not declaring an airflow or
sensor fault solved. Earlier v008 testing demonstrated950RPM operation on a
different calibration, so it is context rather than validation of this candidate.

The owner subsequently reported the blower may have been running during the
preceding six-minute test. Its accessory baseline is therefore uncertain; the
inter-run timing difference is not a controlled adaptation comparison.

No changes to fuel/closed-loop settings, injector or MAF characterization,
pressure compensation, spark gain1.000, idle spark floor−6, fan thresholds,
dashpot or VCT. The existing desired-RPM airflow lookup will follow the new
target; no independent airflow-table change is added. These target scalars can
also affect total idle demand outside fully warm operation through existing
adders. This is a margin experiment, not an identified repair for P1132 or stalls.

## Test and acceptance

Owner handles flashing with the correct vehicle/file and required write-power
conditions. Agent has not flashed or performed ECU readback. Keep Bosch15719,
regulator setting and other hardware unchanged for the comparison. Water/meth
remains off and SCG purple RPM lead disconnected.

1. After owner-confirmed installation, start paired logging labeledv016. Verify
   fresh RPM, desiredRPM, O2, trims, IAC, voltage and loop/fault-state fields.
2. Once warm and settled, repeat one off/blower/off sequence:60s each, A/C and
   defrost off. Annotate actual radiator-fan edges; do not prolong a deteriorating
   run just to obtain a fan cycle. Remain at the controls with throttle untouched.
3. Stop/export after the sequence. Stop earlier for worsening stumble or stall.

Judge RPM error relative to the logged desiredRPM, variability and recovery,
not only an absolute minimum that rose with the target. Look for less undershoot
and no new hunting/hanging idle, persistent mixture departure, or fault fallback.
A floor above800RPM is useful practical margin but is not sufficient evidence
by itself. If the same relative dips remain, retain the result and investigate
air/load response; do not automatically keep increasing targets or alter several
controls at once. Revert to exactv015 if behavior worsens; it retains unresolved
stall history and is not a guarantee of safe operation.

Cold-start O2 readiness remains a separate outstanding comparison. No road/boost
acceptance or long-term sensor compatibility is established by this candidate.
