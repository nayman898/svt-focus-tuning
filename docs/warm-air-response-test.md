# Warm air response: next capture setup

Profile: [Warm Air Response21](../profiles/2004%20Focus%20SVT%20-%20Warm%20Air%20Response%20Trial.Channels.xml).
Loaded in Scanner on2026-10-31 and saved back; all21 request definitions match.
Recording stopped. This is not a v020 validation: no v020 binary exists.

The20 Stage2A requests and intervals remain unchanged. The single addition is
Idle Speed Source19049 at100ms, copied verbatim from the prior Target Idle Air
profile. It populated in earlier surveys but is not guaranteed in this profile.
It adds control-source context alongside Idle Speed Control Mode12200. It does
not expose the missing IAC integrator, commanded total air or valve position.
Do not add speculative IDs for those signals or for cam/purge/fan channels.

Before a new test, require populated RPM, desired RPM, IAC, STIT, LTIT, rawMAF,
spark/source, trims, O2, loop state, ECT and the new source. With ignition on and
engine off, settle any missing channels before starting the actual cold recording.
If recording must restart after engine start, stop/export the earlier segment
under a distinct name first. Do not discard the temperature-crossing evidence.
Do not deliberately run an extra cold start just to populate fields.

For the next justified intervention: owner stays at controls; accessories fixed,
stationary neutral, no throttle blips. Capture the start and passage through
165–200s runtime and170–190F, then up to60–90s of settled warm operation or a few
dips. End sooner for sustained rough/rich running, fallback or near-stall. No
fan wait is required. Mark accessory changes if unavoidable. Owner controls
engine shutdown; stopping logging does not stop the engine.

Keep the ignition-start timestamp and record elapsed time externally if channel
2131 saturates255 again. ECT184 plateau must be checked for freshness rather than
assumed a real plateau. Save nativeHPL, CSV, SCG database/CSV and loaded profile.
Compare dip frequency/depth and recovery under matched conditions, with separate
cold feedback-entry and warm control analyses.

Do not repeat the same run simply because this profile is ready. Next tune value
depends on verified idle-air controller definitions or an IAC-response finding.
Keep v019 MAF/spark fixed while resolving that target.
