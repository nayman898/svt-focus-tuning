# Clock pairing and calibration review

## Paired recording workflow

The owner wants both applications recorded on every session: VCM Scanner for
ECU data, and LogWorks for SCG-1 WGDC, manifold pressure and wideband output.
The PROLINK+ cable is ordered and has not arrived. Once measured AFR is recorded
in both applications, that shared trace can help validate offset and drift;
analog scaling and response/filter differences still need checking.

The stock-coil tach tap caused SCG-1 disruption and unreliable RPM, resolving
when disconnected. No further direct coil-tap experiments are required for
this clock-based analysis.

## Current clock evidence

- VCM CSV Creation Time: **2026-10-26 15:19:41**. The CSV does not state a
  timezone; UTC is consistent with the desktop's four-hour local offset and
  file times, but remains an interpretation of that field.
- The original native LogWorks file was provided at
  `C:/Program Files (x86)/LogWorks3/Log Files/Realtimelog.log` and copied to
  the session archive before inspection.
- Two little-endian Unix timestamp values in that file, at byte offsets
  **34636** and **37880**, decode to **2026-10-26 15:19:35 UTC**.
- This is a plausible original-session start timestamp. It has not yet been
  confirmed against **Sessions > Edit Session Info** in LogWorks. Native files
  also contain other timestamps, including channel-configuration times.
- Export/file-save times are not recording start times and were not used.

The candidate mapping is:

```text
SCG-1 elapsed seconds = VCM offset seconds + 6.000
```

This means the SCG-1 recording began six seconds before the Scanner time
origin, assuming both identified metadata fields are session start times.
The first VCM row at offset 2.203 s would pair with LogWorks at about 8.203 s.

A provisional paired CSV with **8,094 overlapping rows** is saved under
`logs/2026-10-26-idle-01/provisional-clock-paired.csv`, alongside a provenance
JSON describing the assumptions. Each row is marked provisional and includes
the selected SCG sample time and nearest-sample difference. A small sample-time
difference does **not** establish true cross-application timing accuracy.

No clock drift, application latency, or AFR transport delay has been corrected.
The pair is suitable for an initial contextual review, not validated transient
fuel-error calculations. LogWorks documentation states that original sessions
can retain recording date/time, which is why the native session info is the
next confirmation rather than relying on the CSV save time.
[LogWorks manual, sessions](https://www.innovatemotorsports.com/wp/content/uploads/2022/08/LogWorks3_Manual.pdf)

## Calibration inspected

Read-only inspection used a preserved copy of **SVT Base (from chuck)** in
VCM Editor 5.3.1332 Beta. The owner subsequently clarified that this file is
the fresh ECU read with their MIL changes already included. This is
owner-reported correspondence,
not a byte-for-byte verification against the currently flashed ECU.
The earlier ECU-read cache was also preserved separately under `backups/`.

| Editor location / setting | Observed value |
| --- | --- |
| Engine > Idle > RPM: P/N | 1,200 rpm |
| Engine > Idle > RPM: Drive | 1,200 rpm |
| Startup idle Max Time / Startup Adder | 0.0 s / 0 rpm |
| Engine > Fuel > General: Stoich AFR | 14.64 |
| Injector Pressure Drop Ref | 40.00 psi |
| Injector Flow Rate Low | 0.017500000 lb/s (63 lb/hr) |
| Injector Flow Rate High | 0.016700000 lb/s (60.12 lb/hr) |
| Injector Pressure Compensation | Enabled |
| Injector PW Minimum | 0.00050000 s |
| Fuel > Oxygen Sensors: CL O2 Sensor Temp | 520 F |
| ECT Cold / Warm / Hot closed-loop delays | 254 s each |
| LTFT | Disabled |
| Fuel > Open Loop / Base: Enable Time | 10.00 s |
| Fuel Base Cold Enable / Disable ECT | 158 / 90 F |
| Fuel Adaptive WOT | Disabled |

The explicit 1,200-rpm setpoints explain the logged idle target without needing
to infer a large IAT adder from the source label. The actual IAT/ECT adder tables
have not yet been read. Closed-loop delay values and disabled LTFT are concrete
review items; they do not alone prove the reason for the logged open-loop state.
Do not enable learning or shorten delays without checking the intended fueling
strategy and upstream O2 behavior.

The injector reference pressure is 40 psi while the owner reports 43 psi
engine-off fuel pressure. This is a characterization/pressure-reference check,
not evidence that changing the reference alone will fix AFR. Exact injector
part number, rating pressure, pressure-compensation tables and sensor behavior
with the return conversion remain unverified.

## First candidate test

A small isolated idle-target test would change P/N and Drive setpoints from
**1,200 to 1,100 rpm**, with a repeat recording of stable warm idle and fan
engagement. This is a proposed trial target, not an established optimum. Do not
combine it with MAF, injector, spark, loop-mode or boost-controller changes in
the same comparison. Reassess if there was a specific hardware reason for the
existing 1,200-rpm target.

Following the owner's clarification and request to prepare the test, the file
was preserved as v001 and [v002 was prepared](../tunes/README.md). Comparison
against v001 showed only the two idle targets changed. The saved test file
was reopened and both values read 1,100 rpm. No ECU write or SCG-1 setting
change was performed. The brief fan-start voltage dip remains an item to verify.
