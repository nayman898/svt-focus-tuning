# HP Tuners channel request: research before ticket creation

Status2026-10-30: **no support ticket created or submitted**. This is the
proposed scope for owner review, not a claim that all requested signals exist
in this controller. No channels were added to the active profile or vehicle
commands sent for this research.

Target:2004 Ford Focus SVT2.0L, manual, ECM0x10, Black Oak1472K PWM,
calibration/strategy UJAHAS3. Installed Scanner5.3.1332 Beta verified from
executable version. MPVI4 previously identified; obtain a fresh vehicle-connected
Info Log before eventual submission. v015 is owner-confirmed installed.

## Priority1: missing data or definition clarification

| Rank | Signal requested | Units/definition needed | Why it matters here |
| --- | --- | --- | --- |
| 1 | Bank1 injector pulse width / FUELPW1; investigate owner-supplied Ford enhanced identifier0x1141 | ms, final ECU electrical on-time; clarify dead-time inclusion, minimum clamp, cutoff/invalid/stale behavior; duty% is separate | Distinguish changing injector command from changing actual pressure or combustion during onset |
| 2 | Base and final commanded fuel mixture/LAMBSE, plus applied correction terms if accessible | Explicit lambda versus equivalence ratio versus AFR; sign and reference fuel; startup/runtime/temperature, O2 correction and pressure/voltage contributions | Existing command and STFT exports follow1-STFT/100; need semantics and independent terms, not another renamed copy |
| 3 | Desired/base idle airflow, dashpot/preposition airflow, and idle-air integrator limit/state | Mass-flow units and whether total includesSTIT/LTIT; saturation/limit flag if exposed | STIT plateaus near-0.30lb/min as target/air/mixture change; current duty is not actual valve position |
| 4 | Desired injector differential pressure, pressure actually used by injector model, selected pressure source/fallback state | Distinguish requested, measured, substituted and modeled values; psi/kPa and reference basis | Pump bypasses FPDM; transfer is flat40psi and exposed multipliers neutral, but desired-temperature pressure path remains uncertain |
| 5 | Calculated fuel-rail/ambient model temperature and applied fuel-temperature/runtime enrichment | F/C, source/validity and actual applied factor; not only a generic external temperature input | Mixture drifts with runtime even with CL off; need to identify command/model drift |
| 6 | EVAP purge command/duty, and modeled purge flow/fuel correction if present | Duty%, flow units, correction convention; fault flag alone is insufficient | Purge switches are enabled in calibration, but command/flow history is missing |

Ranks1–3 are the essential request. Ranks4–6 are valuable strategy-dependent
follow-ups; ask HP Tuners whether these exist as enhanced PIDs or internal
RAM/DMR channels rather than promising that an address can simply be added.

## What0x1141 establishes—and what it does not

The owner supplied0x1141. Generic Ford PID compilations associate it with
FUELPW1, bank1 injector pulse width, in milliseconds. Those compilations are
leads, **not verified UJAHAS3 definitions**. No raw response, byte length,
endianness, conversion or live validation has been obtained from this ECU.
Do not copy a generic equation or protocol header into a vehicle request.

Primary-source confirmation of the signal name/meaning is available in
[Snap-on's Ford parameter documentation](https://www.snapontools.com.au/wp-content/uploads/2021/12/US_Domestic_Vehicle_Communication_Software_Manual.pdf):
FUELPW1/FUELPW2 report commanded injector on-time in milliseconds. It also
notes that some applications retain the last value after engine rotation stops.
This does not confirm the numerical identifier or support on this specific ECU.

For eventual vendor investigation, phrase0x1141 as a **candidate Ford enhanced
identifier to verify**, not a guaranteed standard SAE PID. It is not an HP
Tuners internal ParameterID, a DTC, an injector calibration parameter, or a
duty-cycle percentage. Do not insert decimal4417 into the XML as a substitute.
This inline-four needs bank1; bank2 is not a priority unless HP identifies a
specific valid meaning for it.

## Already in the saved ECU selector: test before requesting additions

The retained native channel-selector snapshot explicitly identifies
ECM0x10/Black Oak1472K PWM/UJAHAS3. It already lists:

- Engine > Fuel > **O2 Transport Delay Total** and **Fuel Flow Rate**.
- Engine > Camshaft & Crankshaft > **Cam Angle, Cam Angle Error, Cam Duty Cycle**
  and cam fault/control-state channels.
- Fuel System > Fuel Rail > **Fuel Rail Differential Pressure, Fail Rail Press
  Unreliable, Fail Rail Temp Unreliable**.
- **Idle Speed Control Mode**, existing idle target/source, IAC duty and
  STIT/LTIT channels.
- Fuel pressure/raw sensor voltage, pump commands, EVAP purge fault, fan duty,
  A/C status, IAT, loop readiness/conditions/FMEm and O2 heater/fault channels.

These names are not proof of live support or freshness. Validate them in small
groups before calling them missing. Requested intake-cam angle itself may still
need addition if it cannot be separately obtained; do not derive it by adding
actual and error without a documented error convention.

Injector pulse-width names found elsewhere in the selector belong to external
**DSX Atlas PFI** and **MegaSquirt** branches. They do not establish a native
Ford injector-PW channel. Generic external Fuel Temperature entries likewise
are not evidence of a Ford rail-temperature signal.

Snap-on also documents actual cam angle, error and duty as distinct Ford data
types. This supports asking for their meanings, not assigning generic numeric
IDs or claiming that every version supports all three on this SVT.

## Lower-priority additions

- CKP/CMP synchronization-loss status/counts and engine-run/cranking reason,
  if exposed, to correlate pendingP0320 without treating it as proven cause.
- Dedicated clutch switch/neutral input for pull-away and idle eligibility;
  Trans In Gear and Brake Pedal are already present and are not substitutes.
- Per-cylinder misfire information or monitor-valid/enabled status if supported;
  the existing total/boolean channels reportingzero/No do not validate detection.

Do not crowd the primary pulse-width request with unsupported platform features.
These are a second tier, with no proposed numeric IDs yet.

## Existing-channel questions, not new-PID requests

1. Some channels populate only after recording restart. Retain an example HPL
   and exact channel XML showing which fields were blank versus populated.
2. Air Load HiRes held exactly0.4664763808 through119.329s in the v014 trip
   despite changing RPM/throttle. Ask about acquisition/cache behavior using
   that example; do not claim every constant channel is stale.
3. Engine Run Time reaches255s. Ask whether this is the source's intended
   range and whether an alternate extended runtime is available.
4. Explain source and convention for command channel6005 versus STFT6304.
   Their algebraic relationship may be intentional; do not present it as a
   confirmed software defect or wrong-sign feedback.

Numbers6005/6304/etc here are HP Tuners channel IDs from saved XML, not Ford
on-wire identifiers. Names alone should never be used to cross those namespaces.

## Evidence to assemble after scope review

Private candidate attachments, not uploaded:

- Fresh VCM Suite Info Log with interface connected and ignitionON/engineOFF.
  The old2026-10-26 report was captured without vehicle power and is not enough
  for a current support packet. Follow
  [HP Tuners' Info Log guidance](https://www.hptuners.eu/help/introduction_customersupport.htm).
- Exact v015 HPT file to identify the controller/strategy; a relevant native
  HPL and its actual Channels XML. Select focused examples, not the entire
  private log archive.
- Scanner debug log if requested. HP lists its location under Documents >
  HP Tuners > VCM Scanner > Logs in
  [its diagnostic-file guidance](https://support.hptuners.com/support/solutions/articles/153000064308-locating-a-debug-dat-and-license-dat-file).
- Screenshot of native ECU Fuel selector showing missingPW, with unrelated
  external-device branches distinguished. LiveLink could not validate the
  alternative because the SCT has a separate device-identification problem.

Do not upload VIN, interface/license identifiers, tune/log files or license.dat
publicly. Do not attach license.dat automatically to a channel request. Nothing
has been sent, and no live Info Log gathering or vehicle connection was started.
