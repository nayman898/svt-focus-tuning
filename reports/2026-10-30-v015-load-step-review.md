# v015 accessory-load comparison — 2026-10-30

Follow-up: owner reports the blower may have been running in the preceding
155954 session. Its accessory baseline is uncertain, so inter-run spark changes
cannot isolate adaptation. Owner subsequently approved a950RPM target trial;
see [v016](../tunes/v016-idle-margin-950.md). The analysis below records the
evidence before that candidate was selected.

The test supports better stability during settled radiator-fan operation, but
not a general conclusion that every accessory load cures the dips. Blower-on
still contains dips, and the deepest dip occurs near the second reported fan
activation. Recommend investigating idle spark/air adaptation and load pickup
before choosing a numeric tune change. Keep v015 unchanged for now.

## Provenance and event labels

Owner confirms v015, Bosch15719 installed, A/C and defrost off. Paired session
160932-b8f13ca4-v015-60-60-60 saved successfully. Preserved native HPL/CSV,
SCG CSV/SQLite API backup and manifest in `logs/2026-10-30-v015-load-step-01`.
SQLite integrity/finalization and catalog tune hashes passed. No tune edited.

Owner times: radiator fan on34s, off approximately50s (uncertain); blower on65s,
off126s; radiator fan on approximately150s, off approximately200s. These are
owner annotations, not recorded electrical switch edges. Timer basis is assumed
VCM elapsed; paired UI timing and approximate reporting can shift them slightly.

9,513 VCM rows span1.312–218.836s; no export gaps; every requested channel has
values. SCG elapsed = VCM elapsed +1.886951s from metadata, provisional. Do not
infer subsecond fuel/air causality across devices. Recording ends only about19s
after the last reported fan-off; the final settled comparison is short.

## Comparison excluding transition margins

| Assumed state / interval | Mean RPM | Minimum RPM | RPM SD | Mean IAC | Mean timing | Mean lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Accessories off,5–29s |900|732|29.6|39.5%|2.0 deg|1.016|
| First fan,39–45s (short) |898|867|14.5|44.0%|1.7 deg|1.013|
| Blower,70–120s |900|748|24.1|45.7%|1.3 deg|1.010|
| Accessories off,132–145s |901|800|28.2|40.9%|0.9 deg|1.011|
| Second fan settled,165–190s |900|856|17.4|44.7%|0.4 deg|1.010|
| Final off,207–218s (short) |902|860|17.2|42.1%|−0.1 deg|1.010|

These are descriptive row-based statistics, not independent observations at
the CSV row rate. Unequal window lengths and uncertain fan edges limit direct
event-count comparisons. The final off window is also steady: load alone cannot
explain the whole trace. Fuel trims are negative in all these windows, averaging
about−5.6 to−8.1%; average mixture remains close to stoichiometric.

## Transitions and fault states

- At68.643s, near the reported blower-on transition, RPM reaches728.25 and
  IAC53.8%. Another blower-period dip reaches747.5. Load does not eliminate dips.
- At156.276s, near the approximate second fan-on time, RPM reaches684.5,
  IAC54.6%, timing15 deg, and ECU voltage12.94V. State remains Idle Feedback.
  The approximate annotation does not prove fan activation occurred at this
  exact instant or establish whether voltage caused the drop.
- Closed Loop Active/Ready stayYes; FMEM, Open Loop Conditions and O2B1Fail
  stayNo; Fuel Source staysStoich. Spark Source is Idle Feedback throughout:
  **this deeper dip occurs without any MBT transition**.
- No captured stall. No fresh DTC read; O2FailNo does not prove storedP1132 cleared.

## Important difference from the preceding run

In the [previous six-minute test](2026-10-30-v015-bosch15719-review.md), actual
idle timing commonly averaged8–9deg. Here it trends from about2deg toward0deg
despite the same owner-confirmed tune, similar temperatures and near900RPM.
LTIT moves from about−0.144 to−0.096lb/min in the examined windows, compared
with approximately−0.194 to−0.171 in the previous run. This is evidence that
the controller's operating/adaptive state changed; it is not proof of why.

One hypothesis is a changing balance between learned airflow and spark torque
control. The logged source is too coarse to identify all spark corrections.
Lower actual timing does not by itself prove inadequate spark reserve, and
advancing a table or increasing base airflow could simply provoke opposing
feedback. The earlier audit found P/N idle spark44579 displayed12deg, floor−6,
and gain1.000, but actual timing includes other corrections. Do not infer a
newly changed calibration from the actual-timing difference.

## Recommended changes and order

1. Change the next diagnostic focus to **idle spark correction/adaptation and
   load pickup**. Audit the exposed idle spark target/corrections, learned air,
   fan airflow adder and delay. Verify actual fan command/status and load timing
   if available without sacrificing reliable core channels. Do not assume a
   blower electrical load uses the same feed-forward path as the PCM-controlled
   radiator fan or A/C compressor.
2. Do not increase global/base idle airflow just to mimic loaded operation.
   The engine holds900RPM and IAC increases strongly during recovery. This run
   does not demonstrate an IAC command ceiling or justify a numeric air increase.
3. Do not reduce spark gain again or change MBT limits: the deepest dip here
   happens entirely in Idle Feedback. First establish why normal actual spark
   shifted downward on unchanged v015.
4. If repeat captures with confirmed fan edges show a repeatable load-on sag
   and an inadequate/delayed commanded air increment, a small single-change fan
   feed-forward experiment is a candidate. This run alone does not establish
   its amount or direction; no v016 is prepared.
5. Keep cold O2 readiness as a separate outstanding test. No urgent NTK purchase
   is supported by the two warm runs, but neither proves cold15719 compatibility
   or rules out the earlier sensor/heater issue.

If voltage depression repeats at the sensor/pump or a mechanical IAC response
lags despite a timely command, hardware testing takes priority over calibration.
ECU voltage alone is not pump or O2-heater supply voltage. Do not change the
regulator, pump logic, fuel tables or fuel-pressure compensation from this trace.

Detailed window statistics are saved beside the preserved logs in
`load-comparison.json`. Owner annotations are retained in `owner-context.json`.
