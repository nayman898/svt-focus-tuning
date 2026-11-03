# HP Tuners support ticket draft

**Not submitted.** Attach a fresh vehicle-connected VCM Suite Info Log before
sending. The private preparation bundle contains selected supporting files.

## Subject

2026-11-01 observed capability check: with Scanner connected to the2004SVT and
scanning stopped, Controls and Special Functions opens an empty window with no
idle/IAC control. No output command executed. Does this OS support bidirectional
IAC duty or desired-idle control through VCM Scanner, and if so what prerequisites
or support update are required? Please distinguish parameter editing support
from diagnostic output-control support. This observation supplements, not
replaces, the definition questions below.

Strategy-specific refinement2026-10-31: generic TC_OVER/TC_UNDER labels may not
describe this SCP implementation. Please check UJAHAS3 for the candidate symbols
and architecture recorded in [idle-air control map](idle-air-control-map.md),
especially FN_IAC_KP/FN_IAC_KI, FN854/FN855/FN856, ID_DB_CAL and TC_IDI__A.
These names come from an independent SCP definition listing, not validated
addresses for our ECU. Please confirm compatibility, axes, units and current
values, the relationship to STIT/LTIT, and whether they can be exposed in Editor.
The source's mixed1472K/2048K labels require clarification; do not assume the
separate CAN definition applies. No requested gain values or raw patches.

Local follow-up for the warm-idle investigation (not submitted): please identify
whether UJAHAS3 exposes **Idle Airflow Integrator Time Underspeed/Overspeed** and
the associated limits. These appear in the generic Ford idle help but not our
342-entry Advanced View inventory. Please distinguish them from spark gain47996,
cylinder-airmass filter12002 and idle eligibility errors44213/12262. We need the
base/final IAC airflow sum and how STIT2240/LTIT2231 enter it, including units,
clamping, update intervals and learning enable conditions. In the latest native
HPL/export, Engine Run Time2131 advances232->255 then remains255; ECT2124
reports182->184 and stays184 while RPM/IAC continue updating. Please confirm
range/saturation and update behavior. These observations do not establish that
the ECU's internal timers or actual coolant temperature stopped changing.

VCM Scanner: native injector pulse width and channel definitions — 2004 Focus SVT, Black Oak UJAHAS3

## Message

Hello HP Tuners Support,

I am diagnosing intermittent idle stumbling/stalling on a modified 2004 Ford
Focus SVT, 2.0L inline-four, manual transmission. I use an MPVI4 and VCM Scanner
5.3.1332 Beta. The connected ECU was identified as ECM (0x10), Black Oak 1472K
PWM, strategy/calibration UJAHAS3.

My primary request is native ECU **bank-one injector pulse width in milliseconds**.
It was not found under this ECU's Fuel/Flow channel selection. Injector-PW
entries under external DSX/MegaSquirt devices are not applicable.

Could you verify whether Ford enhanced identifier **0x1141 / FUELPW1** is
supported on this strategy and expose it, or identify the appropriate PID/DMR?
This is a candidate identifier, not a validated response from this ECU.
Please confirm units/scaling, update behavior, and whether the value includes
injector voltage offset and minimum-PW limiting. Injector duty cycle is useful
as a separate signal, but would not replace on-time.

The next most useful signals or definition clarifications would be:

1. Base/final commanded mixture or LAMBSE and applied fuel corrections. In our
   exports, channel6005 (commanded equivalence, displayed with lambda units)
   follows1-STFT/100 using6304. Please clarify the source/convention and whether
   independent base target, startup/temperature enrichment and closed-loop
   correction terms are available.
2. Desired/base idle airflow, dashpot/preposition airflow and idle-air integrator
   limit/status. STIT2240 and LTIT2231 are available; we need context for a
   near-0.30lb/min STIT plateau, not duplicate channels.
3. If supported: desired injector differential pressure, pressure/source actually
   used in injector calculations, calculated rail/ambient temperature and applied
   temperature compensation, plus EVAP purge command/fueling contribution.

I am not assuming all these signals exist on UJAHAS3. Please identify any
existing channel names/requirements or feasible additions, prioritizing pulse
width and fuel-command definitions.

Relevant hardware context: this car has a manifold-referenced mechanical return
regulator and battery/relay pump feed that bypasses FPDM speed control. The OEM
FRP sensor is not confirmed installed; the current calibration retains a flat
40psi transfer, so that pressure channel is not independent measured pressure.
An Innovate SCG-1 records wideband mixture separately. This request is for
diagnostic data/definitions, not calibration recommendations.

Additional acquisition observations, if these should be handled separately:

- Some channels populate only after a recording restart. The supplied v015 HPL
  is the retained populated segment after such a restart; it does not reproduce
  the missing pre-restart segment.
- Air Load HiRes held exactly0.4664763808 through119.329s of the optional v014
  trip HPL while RPM/throttle changed.
- Engine Run Time2131 stops increasing at255s. Is that the source's intended
  range, and is an extended runtime available?

The saved ECU selector already lists O2 Transport Delay Total, Fuel Flow Rate,
cam angle/error/duty and rail validity flags. I will validate those separately
rather than request duplicate additions.

I can provide further debug data or perform a specific stationary read-only
test if needed. Please advise which additional files you require.

Thank you.

## Attachment readiness

Included in private preparation bundle:

- Current v015 HPT, with unchanged calibration relative to v013.
- v015 onset native HPL and its actual16-channel configuration.
- Optional v014 trip native HPL and actual driving profile, demonstrating
  the initial stale load interval.
- This draft and a SHA256 manifest identifying the copied files.

**Still needed:** fresh VCM Suite Info Log, with MPVI connected to the actual
vehicle, ignitionON/engineOFF. The old2026-10-26 Info Log reported no vehicle
power and is deliberately excluded. Follow
[HP Tuners' Info Log instructions](https://www.hptuners.eu/help/introduction_customersupport.htm).

VIN/interface IDs belong only in the private support submission or Info Log.
No license.dat is included; provide it only if specifically requested.
No SCT identifiers or firmware files are included.

## Draft addendum: idle-air and spark definitions (not submitted)

The warm idle fluctuation investigation also needs UJAHAS3-specific Editor and
Scanner definitions for idle-air proportional/integral response, overspeed air
removal, integrator filtering/limits, base/final idle-air request, and active spark
limit/correction sources. Current Navigator searches expose idle-spark proportional
gain and fuel-pump gains but no verified idle-air equivalent. Please clarify
ECM44603 Spark Low Load Maximum vs.Time axis units, timer/reset conditions and
whether/how it constrains Idle Feedback. We are not assuming another Black Oak
variant's symbols or addresses apply. STIT2240 requested at500ms is too coarse
for some subsecond dips; a targeted faster request trial is prepared, not yet
validated. Advice on supported acquisition rates and signal semantics would help.

The original attachment bundle above contains older v015 material. It has not
been refreshed for this addendum; review and refresh relevant files before any
external submission. No ticket or external message has been sent.
