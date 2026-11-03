# PMAS HPX transfer review

Owner follow-up: the housing is PMAS, supplied with the plainHPX by LMR as the
1996–2004Mustang4.6 kit. This matches [LMR LRS-MH30HPXS](https://lmr.com/item/LRS-MH30HPXS/mustang-pmas-hpx-3-inch-maf-wiring-adapter-96-04):
HPX, PMAS3-inch blow-through housing and ADPT-VX adapter. PMAS lists the housing/
sensor assembly as [MH30-HPX](https://pmas-maf.com/product/mh30-hpx-3inch-housing-w-hpx-mass-airflow-sensor/).
Receipt/serial and exact housing revision remain uninspected. The dedicated
PMAS3-inchProTubeII workbook sheet is now the better candidate reference, rather
than assuming a generic3.000-inch bore. Its cached reference is2.89874g/s at0.50V
and3.81661g/s at0.60V. Applicability to the actual kit revision still needs its
flow sheet or manufacturer confirmation. Prior generic-curve percentages below
are retained as explicitly hypothetical and are not the selected replacement.
The Editor/Scanner unit discrepancy remains unresolved. No tune edit performed.

Owner now confirms plainHPX (not an extended-range variant), blow-through,
after the turbo near the throttle body, in a nominal3-inch housing. Actual
inside diameter, housing brand, sensor insertion geometry, nearby bends and
recirculation/blowoff arrangement remain unverified.

## Manufacturer reference obtained

The [PMAS HPX product page](https://pmas-maf.com/product/hpx-mass-airflow-sensor-ford-universal-tune-required/)
links its [transfer generator](https://pmas-maf.com/wp-content/uploads/2019/01/PMASHPXTOOL2014_2.xls).
The [transfer page](https://pmas-maf.com/transfer-function/) separates plainHPX,
HPX-N andHPX-E tools and offers serial-specific flow-sheet requests.

Downloaded workbook retained privately as `.local/PMASHPXTOOL2014_2.xls`,
SHA256 `14B7DB48BA6F12098173FF02BA12F41F579D5B7E117E257583F67B0A565969D3`.
Read with xlrd/olefile; no Excel macro or executable was run. The standardHPX
polynomial and generic tube-area formula were decoded from spreadsheet records.
Reproducing all30 cached default-sheet g/s outputs gave maximum absolute error
below8e-11g/s. Comparison uses3.000-inch generic tube input, multiplier1, and the
workbook's0.91 generic-area factor. This is a hypothetical housing assumption,
not confirmation of the installed dimensions.

The downloaded main sheet defaults to3.4inches. Its dedicated PMAS3-inchProTubeII
sheet instead uses2.8inches and a different area treatment. Therefore do not use
the workbook's unchanged defaults or assume every3-inch housing is equivalent.

## Saved curve shape in the idle region

The [saved ECM12163 grid](calibration-inventory/v017/034.json), inherited byv018,
contains these displayed pairs:

| Volts | Displayed flow number |
| --- | ---: |
|0.50|3.8|
|0.53|3.8|
|0.54|3.9|
|0.60|4.9|
|0.65|5.0|
|0.70|6.9|

Thus there is a displayed plateau at0.50–0.53V and strongly differing slopes
around0.60–0.70V. The v018 warm rawMAF range was0.517–0.639V, directly overlapping
these features. Display rounding limits how precisely the smallest slopes can
be inferred; it does not remove the broad unevenness. This is a concrete reason
to prioritize MAF characterization in2A, without assuming it explains every dip.

## Important unresolved unit/definition discrepancy

Read-only inspection of the savedv018 table shows an **lb/h** unit label beside
the numeric grid. Changing display units tolb/min changes0.60V's4.9 toabout0.082,
consistent with division by60. No calibration value or file was saved/changed.

However, the same-run logged MAF is near0.58lb/min at raw voltage near0.58V.
Across the warm samples, logged flow converted tolb/h divided by the interpolated
table number has median7.58. The physical g/s-to-lb/h conversion is about7.94.
Asynchronous values, display precision and MAF corrections limit this comparison,
but it strongly flags an Editor/Scanner definition, scaling or unit disagreement.
It is not acceptable to declare the curve85%low and multiply it from that label.

The following comparison is explicitly **conditional on the table numbers being
g/s-equivalent**, as their scale resembles the logged flow. It is not a ready-
to-flash replacement or a resolved unit interpretation:

| Voltage | Tune numeric | PMAS generic3.000-inch g/s | Conditional difference |
| --- | ---: | ---: | ---: |
|0.50|3.8|3.028|+25.5%|
|0.53|3.8|3.325|+14.3%|
|0.60|4.9|3.987|+22.9%|
|0.65|5.0|4.471|+11.8%|
|0.70|6.9|4.991|+38.2%|
|1.00|11.4|9.616|+18.6%|
|2.00|49.8|49.629|+0.3%|
|3.00|165.1|151.836|+8.7%|
|4.80|410.6|598.651|−31.4%|

The shape difference varies with voltage rather than being one constant factor.
But the manufacturer curve itself depends on correct housing assumptions, and
existing injector/model errors may have been compensated in the inherited curve.
Do not blindly install the complete PMAS curve or globally rescale this one.

## What changes the tuning plan

MAF transfer/installation is now a higher-priority branch than guessing hidden
idle-air gain. A nonlinear local transfer can affect inferred air/load and fueling
in the precise voltage band where warm fluctuations occur. That is a plausible
mechanism, not proof: the observed raw-voltage changes can also be genuine flow
changes caused by IAC action, pulsation or nearby throttle geometry.

Before selecting the next MAF revision:

1. Establish actual housing inside diameter and whether it is PMASProTube or a
   generic welded slot housing. Confirm sensor positioning/flow direction and
   distance from bends/throttle/BOV. Nominal outside diameter is insufficient.
2. Resolve ECM12163 Editor units versus Scanner2300 and raw-voltage2302 semantics
   forUJAHAS3. The current inventory originally lacked table units; this new
   discrepancy must be carried forward rather than silently interpreting its
   numbers asg/s. A vendor definition check or independent raw calibration mapping
   is needed before an absolute rewrite. No vendor message was sent.
3. Verify injector characterization before using transient trims to force a curve
   fit. Do not change injector slopes, regulator pressure and MAF together.
4. With units/housing settled, prepare a separate low-voltage-only correction
   informed by the manufacturer reference and steady measurements. Retain high-
   voltage regions during the initial idle test; don't apply this nominal comparison
   as a boost calibration. Judge rawMAF/load/fuel correction/RPM together.

No v019 or new log is requested by this review. No ECU writes, DTC resets,
controller changes or file saves were performed. All existing tune identities
remain unchanged. See [numerical comparison](2026-10-30-hpx-maf-comparison.csv)
and [formula/assumption verification](2026-10-30-hpx-maf-comparison.json).
