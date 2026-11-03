# IAC diagnostic next step — 2026-11-01

## Completed checks

- VCM Scanner is connected to the SVT and stopped. Opened Controls and Special
  Functions without executing a vehicle command. Its window is visually empty;
  accessibility exposes only a blank tab container and status controls. There is
  no available idle-RPM or IAC-output control in this connection/session. This
  does not prove that another diagnostic tool cannot support one.
- The added Idle Speed Source populated during the owner's engine-off check.
  RPM0/runtime0/50F were consistent with that condition; the displayed source
  does not explain warm oscillation. No engine run is needed to repeat this check.
- Rechecked Ford TSB03-3-5 at the manufacturer's original URL. Focus/SVT is not
  among its listed applications. Do not apply its other-engine duty percentages,
  trim limits or target idle speeds to this modified SVT. Exact2004SVT pinpoint
  test details were not verified from the accessible references.

## Immediate physical check: engine off, ignition off, cool engine

This is a visual inspection, not an engine-running actuator test.

1. Identify the installed IAC part number and whether its mounting and air
   plumbing remain stock. Record it before buying or replacing anything.
2. Check the connector latch, visible terminal corrosion/recession and nearby
   wiring for damage or heat exposure. Do not bridge terminals or power the valve
   directly. Do not turn the throttle stop or clean the valve as an experiment.
3. Trace the actual bypass-air path, throttle-body joints and PCV connections
   relative to the relocated blow-through MAF. Record which air enters upstream
   and downstream of the meter. The stock-plumbing assumption is not sufficient
   for this turbo conversion; this check does not presume a leak exists.
4. If visual inspection is inconclusive, use a properly regulated automotive
   smoke test of the intake/bypass/PCV system with the engine off. Follow the
   tester and modified plumbing's pressure limits; do not use unregulated shop
   air or combustible spray around a running engine. Record the actual leak
   location rather than just a smoke-present verdict.

Repair a found connector, bypass-path or leak defect first, retain v019, then
capture one comparison with the loaded21-channel profile. That is an actual
intervention, not another unchanged warm-idle run. No leak found does not prove
the IAC's dynamic operation is good.

## Dynamic test if inspection is clean

The next useful distinction is electrical command versus mechanical airflow
response. Use a tool with confirmed SVT bidirectional IAC support, or a technician
with a scope/current clamp and the exact wiring diagram. No generic pin numbers,
coil resistance limits or duty steps are authorized by this document.

Record PCM duty PID, actual valve-drive waveform/current, RPM, rawMAF, spark,
STIT/LTIT, voltage and wideband together around an event. Before running, secure
test leads away from belts/fans and establish how the commanded test is released.

| Observation | Interpretation / next branch |
| --- | --- |
| Scanner duty changes but electrical drive/current drops out | Investigate feed, connector, harness, coil and driver; not a gain-tuning conclusion |
| Electrical command follows normally but airflow response is delayed or inconsistent under matched conditions | Suspect valve/bypass behavior; confirm with a known-correct part or service test before replacement |
| Repeatable airflow response, but air/spark corrections alternate and overshoot | Controller dynamics remain plausible; obtain strategy-specific gain/filter definitions |
| Torque/RPM falls while command/air delivery remain consistent | Investigate combustion, fuel pressure, cam tracking or external load instead of condemning the IAC |

These are discriminating observations, not sufficient proofs individually.
MAF measures total flow, not only IAC flow; engine speed also affects flow.
An ordinary multimeter's average voltage cannot establish subsecond PWM response.

## Calibration branch

The local HP Tuners request now includes the exact observed absence of actuator
controls and the SCP-symbol candidates in [idle-air-control-map.md](idle-air-control-map.md).
It asks for current values, axes, units and supported diagnostics. No ticket
was submitted and no paid definition was purchased. v020 remains uncreated;
the available evidence does not justify substituting a MAF/base-air change for
the missing controller test.

## Sources and scope

- [HP Tuners Controls and Special Functions](https://support.hptuners.com/support/solutions/articles/153000173612-controls-and-special-functions-in-vcm-scanner): capability varies by controller and operating system. The local empty-window inspection is the evidence for this session.
- [Ford TSB03-3-5](https://www.fordservicecontent.com/pubs/content/~WT/~MUS~LEN/3569/tsb03-03-05.pdf): general diagnostic context only; listed applications exclude this SVT. Supports checking other causes rather than diagnosing an IAC from symptoms alone.
- [Ford1999 PCED KE](https://www.fordservicecontent.dealerconnection.com/pubs/content/~WVX2/~MUS~LEN/15/VX25090.HTM): older general diagnostic framework, not an exact2004SVT specification. Its numerical limits are not applied here.
