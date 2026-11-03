# v019 pressure test: no captured pressure collapse before the dips

Owner supplied `paired-20261102-155806-f2d1104a-v019-fuel-press-test` and reports
stable pressure before the dips. Recording label indicates return tov019; no
ECU readback or independent verification of installed file identity.

## Capture quality

Preserved available originals and input hashes in
[logs/2026-11-02-v019-pressure-01](../logs/2026-11-02-v019-pressure-01/).
Manifest ispartial: Scanner control/export initially failed. LaterVCMCSV exists,
but nativeVCMHPL is absent from the supplied folder. Original error retained.
SCGCSV and SQLite are present; SQLite integrityok/finalized; backupAPI used.

VCM5163rows,1.374–121.165s; all19requested fields populated. One1.401s gap at
5.984–7.385. Raw Fuel Pressure Sensor6507 has348distinct exported values; this
supports a varying signal rather than a fixed40psi substitute. Interpolated
values are present, so348values and row spacing do not prove sensor update rate.
ECT128–152F and desiredRPM1184->1024: this is not the950RPM settled warm comparison.

SCG valid samples span0.702–101.139s elapsed. Metadata alignment is
SCGelapsed=VCMoffset+1.542894s, provisional. Thus validwideband ends around
VCM99.596s; do not attach laterAFR values to the final21.6s ofVCM. Sensor/exhaust
transport delay remains uncorrected. No new run or tune change performed.

## Pressure result

Raw voltage range3.046875–3.0859375V, mean3.068710V, SD0.006073V.
Using the provisional nominal low-pressure Ford curve17.5*(V−0.5), this corresponds
to44.57–45.25psi differential, mean44.95psi, SD0.106psi. Absolute scaling is not
fully verified for the exact part/VREF; voltage stability is the primary evidence.
Owner independently reportedKOEO43psi/~3V andrunning39psi/−13inHg/3.07V,
which imply~45.39psi differential and~44.98psi from the nominal curve. Sensor and
regulator reference hoses share manifold pressure via a distribution manifold.

There are17groups withRPMmore than40below contemporaneous desiredRPM, grouping
such samples separated by<=1s. From0.5s before each minimum to that minimum,
nominal pressure changes range approximately−0.256to+0.171psi. No repeated
pressure collapse precedes the sampled dips; both signs occur. These sampled
windows do not exclude very brief transients between ECU updates or a rail-to-
regulator pressure difference under higher flow. No higher-flow validation.

This substantially lowers pressure-instability priority for these particular
events. It does not rule out injector characterization/PW, ignition, cam/purge
disturbances or control-loop interaction. No basis to change pump duty/gains,
the mechanical regulator, or increase base pressure to treat this capture.

## Event evidence

CLNo/FMEmYes atstart. At82.585s CLYes/FMEmNo; O2/trim behavior is not summarized
as though the entire run were closedloop. Eight of17dipgroups have their minima
before this return toCL, nine afterward.

At56.618s RPM1122/desired1104, IAC42.86%, spark11deg, STFT3.159%, rawpressure
3.071289V. At56.882s RPM1019, IAC45.05%, spark17.75deg, STFT3.171%, rawpressure
still3.071289V. FMEmisYes. This event does not require a new closedloopSTFT
correction or a measuredpressure drop.

At94.309s RPM1044/desired1056, IAC43.93%, spark12.75deg; at94.564s RPM950.5,
IAC45.94%, spark30deg, rawpressure3.061523V versus3.071289V a quartersecond
earlier (~0.171psi nominal difference). Closedloop isactive; this is corrective
air/spark during underspeed, not evidence that the labelMBT caused the decline.

Both examples support separating the initiating torque loss from recovery.
RawMAF remains nonzero, but totalflow changes cannot identify bypass valve
motion independently of engineRPM. Existing asynchronous channels still cannot
uniquely identify airfeedback gain or valve lag.

## Decision

Accept this as useful new pressure evidence. Do not ask for an unchanged repeat
just to confirm that pressure is steady. Retainv019 as owner-reported baseline;
v020 remains rejected. Do not revive its air cut or changeMAF based on this run.

The next pressure integration step is restoring a verified sensor transfer in
a separate calibration/measurement revision, with an audit of its injector-model
use. This removes the deliberately flat40psi conversion but is not a promised
idle repair. Keep measurement validation separate from changes to injector
reference/slopes or pump strategy. No new candidate prepared in this review.

For a further behavior experiment, pressure is now a measured control variable;
choose one available torque/air/spark intervention with an explicit expected
response. Pressure stability alone is not a reason to declare a particular gain
or table wrong. Existing support questions about hidden air controls remain.
