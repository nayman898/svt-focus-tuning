# V2 airflow regression and design review

The corrected candidate is in [`flange_corrected/stl`](../flange_corrected/stl/). Its manifold-side throttle face is flat. Use the molded O-ring in the factory throttle body. The stock throttle body's idle-air opening feeds the isolated IACV supply pocket through an 11.1 mm passage. The separate valve outlet leads to the plenum. The opening contour and seal footprint came from a perspective-corrected factory reference photo. Verify their overlap with the actual throttle body using the [fit coupon](../flange_corrected/stl/svt_v2_flat_face_iacv_fit_coupon.stl).

## Geometry corrections

- The offset circular flange-back blend extended about 3 mm beyond the square throttle flange. The blend is now clipped and eased into the square outline in the bolt-grid frame. The exported STL section 11.9 mm behind the face shows about 104 mm² removed outside the outline. The shortest distance from the removed material to the bore is 10.1 mm. The 79 × 79 mm pattern, 7 mm holes and flat face stay registered to the previous revision. All four rear sockets passed the tool and washer clearance checks. [Before and after STL sections](flange_back_comparison.png) · [Geometry checks](../flange_corrected/geometry_validation.json)
- The split-flange ring had a constant opening and was added after the generator cut the tapered plenum. This put about 2.57 cm³ of solid back into the intended passage on the right half. The revised generator subtracts the tapered plenum from the split ring before assembly. The corrected split exports intersect their intended WOT cavity by 0.00085 mm³ total. The largest air section recovered is 175.5 mm². The trim stays 2.42 mm from the split O-ring groove and 10.74 mm from the bolt, dowel and tool cuts. [Previous split geometry](refined_throat_check.json) · [Corrected split domain](corrected_domain.json) · [Split sections](split_joint_sections.json)
- The IACV route remains continuous with 5.06 mm of material between it and the main passage, 4.73 mm at the IACV mounting face, and 4.97 mm to the rear socket clearances. The reloaded right half has less than 0.00003 mm³ of solid in the capped feed. The minimum sampled main inlet area remains 3,308.70 mm². Both split halves are watertight closed volumes and within the CC2 nominal build envelope. [STL manifest](../flange_corrected/stl/manifest.json) · [Exported passage checks](flange_corrected_throat_check.json)

## What the airflow tests measure

The 3D model uses the frozen V2 pressure equations, 18 psig, 52 °C, and 0.2777 kg/s for the 7,000 rpm case. The WOT domain is capped at the throttle face and the four runner exits with the IACV and vacuum taps sealed. For each pair of split STLs, the regression verifies the manifest hashes and subtracts any solid that enters the capped CAD passage. For the four candidate cases that reused archived solutions, the script verified equality of all three grid coordinate arrays, every fluid cell, the inlet plane/axis, the runner definition, and the runner exit position.

Pressure loss is the average of the four differences in flux-weighted total pressure between the throttle reference region and the runner reference regions. Spread is `(maximum share − minimum share) / 25% × 100` with all four outlets open. The standard 3D runs use an outlet valve-loss coefficient of 14, with a sensitivity run at 7. The wall-drag multiplier is 1.4. The quasi-1D solver uses its own valve and loss assumptions. The two models give different estimates of cylinder balance.

## Airflow results

Primary baseline is the earlier fit-verified Codex V2 with the shorter neck. The original Gemini V2 split design, rebuilt from the pinned generator and parameters, provides a second reference at the two 4 mm grid alignments. The pinned split solids passed the native volume check. They enter the comparison as reconstructed CAD because serializing and reloading those baseline meshes failed the closed-volume check. Each case file includes the provenance and all four runner flows, pressure losses and boundary counts.

| Grid at 7,000 rpm | Fitted V2 pressure loss | Corrected pressure loss | Fitted V2 spread | Corrected spread |
|---|---:|---:|---:|---:|
| 4 mm aligned | 1.2571 kPa | 1.3563 kPa | 6.659% | 6.788% |
| 4 mm shifted 2 mm | 1.2428 kPa | 1.2280 kPa | 6.145% | 6.343% |
| 3 mm aligned | 1.1976 kPa | 1.2227 kPa | 6.091% | 6.209% |
| 2.5 mm aligned | 1.2232 kPa | 1.2351 kPa | 6.110% | 6.310% |

At the finest matched grid the corrected pressure loss is 0.0119 kPa higher, about 1.0%. The normalized spread is 0.200 percentage points higher, equal to a 0.050 percentage-point increase in the gap between the highest and lowest cylinder shares. The corrected C1–C4 shares are 25.553%, 25.470%, 25.002% and 23.975%. These results put the candidate close to fitted V2 at the design flow. The matched cases show a small increase in spread on every tested grid. [Fitted finest case](cases/fitted_dx2.5_shift0_rpm7000.json) · [Corrected finest case](cases/corrected_dx2.5_shift0_rpm7000.json)

Pressure loss changes direction between the two 4 mm alignments. The corrected candidate's aligned pressure and spread also reverse direction between the 4→3 and 3→2.5 mm steps. Both facts limit the precision of any global ranking. A finer-grid model with controlled boundary-area error or matched flow-bench data is needed to resolve the small differences. [NASA spatial convergence guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)

Against the pinned Gemini V2 CAD, the corrected pressure loss is 1.3563 vs. 1.3536 kPa aligned and 1.2280 vs. 1.3068 kPa shifted. The corrected spread is 6.788% vs. 6.992% aligned and 6.343% vs. 6.349% shifted. [Pinned Gemini aligned case](cases/gemini_dx4_shift0_rpm7000.json) · [Pinned Gemini shifted case](cases/gemini_dx4_shift2_rpm7000.json)

| Aligned 4 mm RPM sweep | Fitted V2 pressure loss | Corrected pressure loss | Fitted V2 spread | Corrected spread |
|---|---:|---:|---:|---:|
| 3,000 rpm | 0.2607 kPa | 0.2826 kPa | 6.318% | 6.345% |
| 5,000 rpm | 0.6649 kPa | 0.7185 kPa | 6.675% | 6.794% |
| 7,000 rpm | 1.2571 kPa | 1.3563 kPa | 6.659% | 6.788% |
| 7,500 rpm | 1.4356 kPa | 1.5554 kPa | 6.631% | 6.720% |

On the aligned 4 mm grid the corrected design shows 0.022–0.120 kPa more loss over the RPM sweep. Use the matched phase and refinement checks above when interpreting that result. [Individual case outputs](cases/)

All 24 matched steady cases passed the solver's convergence checks. The fit and corrected models both passed the four single-cylinder cases at 0.097195 kg/s. Each solver assigned all flow to the enabled cylinder and zero to the three masks. Single-cylinder losses range from 0.9740 to 1.1993 kPa for fitted V2 and 0.9876 to 1.2167 kPa for the corrected model. Both put the highest loss on C4. [Fitted C4](cases/fitted_dx4_shift0_rpm7000_c4.json) · [Corrected C4](cases/corrected_dx4_shift0_rpm7000_c4.json)

Reducing the outlet loss coefficient from 14 to 7 increases the corrected design's spread from 6.788% to 11.951%. Fitted V2 rises from 6.659% to 11.708%. This sensitivity is larger than the spread difference between the two designs. The matched cases report zero mass error and reverse outlet flow to their output precision. The separate cell-velocity imbalance ratio stays between 1.47 and 1.86. Projected face-flux closure is stronger than the underlying cell-velocity field, so local separation and fine details of runner balance need independent validation. [Fitted K7 case](cases/fitted_dx4_shift0_rpm7000_k7.json) · [Corrected K7 case](cases/corrected_dx4_shift0_rpm7000_k7.json)

The two 2 mm grid phases passed the boundary-only connectivity checks. Each corrected runner has 362 tagged faces in the aligned grid and 360 in the shifted grid. Each test has separate outlet masks and four outlets connected to the inlet. An empty outlet list was rejected. The 2 mm rows run boundary setup with zero outer iterations. [Fitted V2 boundary cases](fitted_boundary.json) · [Corrected boundary cases](corrected_boundary.json)

Across the seven quasi-1D operating points from 3,000 to 7,500 rpm, the fitted and corrected numbers match at the precision the model reports. At 7,000 rpm each model reports 2.184 kPa pressure loss, 0.96% quasi-steady spread and 0.77% pulsating spread. The quasi-1D model uses empirical geometry and valve loss terms. Its values differ markedly from the corresponding 3D steady spread. [Fitted V2 section audit and 1D sweep](fitted_domain.json) · [Corrected section audit and 1D sweep](corrected_domain.json)

## Audit of Gemini's verification suite

- The straight-duct control converged at 80.8 Pa against its 74.9 Pa Darcy estimate, an 8% difference. The test's pass window permits 0.5–6 times that estimate. Keep recording the actual discrepancy so this broad window cannot hide drift.
- The symmetric four-way control passed on both phases. Left-right paired flow shares matched to output precision and pressure loss shifted 2.34%. The symmetry check verifies mirrored pairs. It gives limited evidence for the phase response of the oblique production inlet.
- The all-open, one-open and empty-outlet cases and both fine-grid boundary phases were repeated against the export-adjusted air domains. The original verification compares the analytic cavity to the one-piece STL only. The current test shows why a one-piece overlap result cannot stand in for the assembled split parts. [Control results](solver_controls.json) · [Original solver](../../reference/verify_airflow_v2.py)
- The pinned, hypothetical 14 mm protruding-bellmouth version converged at 1.788 kPa loss and 2.498% spread on the aligned 4 mm grid. It represents a pressure-loss versus distribution trade-off. Across the eight-point analytic taper sweep, the flush design's quasi-1D spread rises from 0.94% to 1.05% as the ratio increases from 0.54 to 0.84. Its lowest modeled pressure loss appears at 0.72 in that sweep. [Retested baseline and taper sweep](legacy_comparisons.json)
- The newer 12.4 mm-feed Gemini working revision appeared during this audit. Both as-exported split STLs matched their manifest hashes, but independently reloading them found 6 and 351 edges with more than two incident faces. Neither half reloaded as a watertight volume. The secondary airflow comparison therefore uses the pinned original Gemini V2 geometry. Gemini should read the files back after STL serialization and fix the mesh before comparing the newer split revision numerically. [Working-revision export audit](live_gemini_stl_integrity.json)

## Print geometry

Both corrected print-oriented halves sliced on the Centauri Carbon 2 with the 0.4 mm nozzle and 0.20 mm layers, using automatic supports from the build plate. The right half occupies 253.73 mm of the printer's 256 mm nominal height. The Blender views show the finished face, exterior shoulder and IACV integration. The geometry-only PLA preset verifies toolpath generation. Printed internal finish, material strength and sealing still need physical validation. [Corrected STL render](../validation/flange_corrected_flange_back.png) · [Right slicer result](../validation/slicer_result_flange_corrected_right.json) · [Left slicer result](../validation/slicer_result_flange_corrected_left.json)

## Idle-air passage and pressure loads

The connected feed reaches a minimum sampled area of 96.58 mm² and a minimum hydraulic diameter of 11.08 mm over 105 sections. The 117.5 mm path has a 9.24 mm minimum centerline bend radius. If the whole 0.85 lb/min logged warm-idle demand goes through the feed, the modeled duct loss is 5.06–23.78 kPa with assumed minor-loss coefficients of 2–10 and 0.15 mm roughness. The logged −7.29 psig return pressure supplies about 50.3 kPa of pressure difference at a near-atmospheric inlet. That supports the passage size for warm idle. At 10.51 g/s the high-loss end of the screen consumes the available head. Actual valve position, the throttle-body passage, deposits and cold-start flow remain unmeasured.

Pressure-only loading on the main opening is about 411 N at 18 psig and 570 N at 25 psig. The exported geometry retains the sampled wall clearances and separate IACV passages. These load calculations have no printed-material strength data, temperature derating, fastener preload or fatigue model. [IACV and pressure calculations](corrected_idle_and_pressure.json)

## Changes for Gemini to carry forward

1. Check each release against the intended air domain using the joined split exports and the one-piece shell. Include dense cross-sections through the split and checks for seal land, bolt and dowel clearances. State the tolerance used for mesh-serialization differences and use section checks to catch localized obstructions.
2. Keep the diffuser and runner internals fixed when changing the exterior flange. Require a pressure-wall clearance check and compare production STLs against the intended air domain. The IACV feed needs its own connected area and pressure-loss analysis under idle conditions.
3. Run both voxel-grid phases, the fine-grid boundary checks, and the single-outlet matrix with the same inlet, outlet and valve settings before making a change to runner balance. Inspect both projected face-mass closure and cell-velocity imbalance. Use exact-grid equality to reuse archived solutions. Report grid reversal or phase sensitivity alongside any claimed improvement.
4. Validate against physical data before treating modeled pressure loss or spread as engine performance. Bench-test the actual throttle face seal and the split joint, measure the IACV flow with the valve and throttle body installed, and confirm cable travel through full closure and opening. For flow balance, compare all four runner flows at matched total flow and inlet pressure. For structural qualification, include boost, temperature, fasteners and the printed material's layer orientation and creep.

## Reproduce

Run these commands from this folder with the project's Python dependencies and PyAMG available. Each script shares the same local job lock. The solver writes individual case files as they finish.

```powershell
python -B full_regression.py --design corrected fitted
python -B solver_controls.py
python -B gemini_reference.py
python -B legacy_comparisons.py
python -B throat_check.py ../flange_corrected flange_corrected --split
python -B flange_section.py
```
