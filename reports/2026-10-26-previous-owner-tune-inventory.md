# Previous-owner tune inventory and first comparison

2026-10-26: Owner identified Downloads as their previous owner's tune archive.
Found 26 HPT files named SVTv29.01 through SVTv29.26, all with distinct SHA-256
hashes. None is byte-identical to a cataloged v000-v006 file. Filenames indicate
an apparent sequence, not verified chronology, parentage or test acceptance.
No original archive file was edited or moved. All current revision hashes and
sizes were checked and match the catalog; archive hashes were rechecked after
Editor inspection. Full archive manifest: `.local/previous-owner-tune-inventory.json`.

## Actual Editor comparison

Main: `tunes/v006-post-repair-fan-baseline.hpt`.
Compare: `C:/Users/nlm89/Downloads/SVTv29.26.hpt`.
VCM Editor Comparison Log - Differences listed these leaves:

- Notes
- Target Idle Speed Park/Neutral
- Target Idle Speed Drive
- Open Loop Fuel TPS Thresh vs. RPM
- Master DTC List

No other parameter differences were listed. This is a parameter comparison,
not binary equality, vehicle compatibility validation, evidence of previous
successful testing or proof of which file the ECU currently runs. Exact DTC
cells and archive Notes were not inspected in this pass. The difference set
is consistent with .26 being close to our inherited calibration before the
owner's diagnostic edits and the documented idle/TPS experiments. Actual
lineage remains unproven. There is no listed injector, MAF, spark or other fuel
table difference in this comparison; this does not establish those settings
as correct. Private UI capture: `.local/v006-vs-owner26-comparison-ui.txt`.
Comparison file was closed after review; no save or ECU write was performed.

## Highest-value next comparisons

1. .23 versus .24-Summer-Idle: identify the actual idle changes behind the name.
2. .24 versus .25-Summer-Idle-CGT-VCT: identify added changes without assuming
   what CGT means or that every named feature was changed.
3. .25 versus .26: determine which late changes were retained or revised.
4. .19 versus .20nvct versus .21: inspect VCT history separately from IMRC;
   names alone do not identify the engine's installed hardware or strategy.

Use Editor comparisons and embedded Notes. Do not infer parameter values from
binary differences or copy an older calibration into the current vehicle.

## Logging alternatives

Owner reports intermittent SVT channel population and suggests SCT X3 with
analog wideband. Record this as owner experience, not a proven platform-wide
cause. Our own session evidence shows channels can disappear and return.
No MPVI4 replug was needed for this offline review.

SCT's X3 manual documents PC pass-through logging of up to two external 0-5 V
analog sources, including wideband AFR. This makes an X3/LiveLink comparison
plausible, but availability/rate of this vehicle's required PIDs and installed
software/device compatibility are unverified. Before analog use, verify the
actual SCG-1 output configuration, X3 input/cable pinout, signal grounds and
conversion equation; preserve raw voltage alongside converted mixture where
supported. A shared log timebase helps clock pairing but does not remove
sensor/exhaust/filter delays. No device swap, wiring or firmware work occurred.

Source: https://derivepower.freshdesk.com/support/solutions/articles/72000583016-x3-manual

HP Tuners documents repolling supported parameters for missing selector
entries; this is not a documented guarantee of repairing intermittent blank
values in already configured channels.
Source: https://support.hptuners.com/support/solutions/articles/153000193776-repoll-for-supported-parameters

## Inventory

| File | Bytes |
| --- | ---: |
| SVTv29.01.hpt | 208093 |
| SVTv29.02.hpt | 208317 |
| SVTv29.03.hpt | 208365 |
| SVTv29.04.hpt | 208461 |
| SVTv29.05.hpt | 208525 |
| SVTv29.06.hpt | 208813 |
| SVTv29.07.hpt | 208957 |
| SVTv29.08.hpt | 209021 |
| SVTv29.09.hpt | 209133 |
| SVTv29.10.hpt | 209885 |
| SVTv29.11.hpt | 210013 |
| SVTv29.12.hpt | 210125 |
| SVTv29.13.hpt | 210237 |
| SVTv29.14.hpt | 210333 |
| SVTv29.15.hpt | 210573 |
| SVTv29.16.hpt | 210701 |
| SVTv29.17.hpt | 210861 |
| SVTv29.18.hpt | 211021 |
| SVTv29.19.hpt | 211165 |
| SVTv29.20nvct.hpt | 211581 |
| SVTv29.21.hpt | 211725 |
| SVTv29.22.hpt | 211949 |
| SVTv29.23.hpt | 211997 |
| SVTv29.24-Summer-Idle.hpt | 212045 |
| SVTv29.25-Summer-Idle-CGT-VCT.hpt | 212253 |
| SVTv29.26.hpt | 212349 |
