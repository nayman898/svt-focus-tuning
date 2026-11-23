# Focus SVT V2 throttle neck and cable bracket

This revision moves the throttle face **8 mm along its existing axis**. In the manifold coordinates, that is 6.58 mm toward cylinder 4, 4.11 mm toward the radiator, and 1.94 mm up. The bolts for the cable bracket move 5 mm along the same axis. The bracket therefore sits 3 mm farther from the throttle body, toward the plenum, relative to the fitted V2.

The 79 × 79 mm BBK bolt grid, Ø7 mm holes, Ø65 mm bore and bore offset are carried over from the fitted flange. The two bracket posts use the original 28 mm pitch and a matched bolt-line orientation. The mounting plane is 70.21 mm above the manifold datum, with Ø5.2 mm pilots 10 mm deep. The cable bracket position is a CAD estimate based on the fitted V2 and the modeled IACV pad.

The [neck survey](neck_bracket_survey.json) compares nine combinations of extension and bracket setback. The 8 mm option provides nearly the same smaller of the two measured bracket clearances as the 9 mm option and requires less charge-pipe movement.

| CAD check | Fitted V2 | Extended neck |
|---|---:|---:|
| Cable posts to IACV pad | 1.48 mm | 4.70 mm |
| Cable posts to throttle flange | 1.85 mm | 4.85 mm |
| Minimum cable pilot to main air passage | 5.14 mm | 5.40 mm |
| Minimum sampled throttle-neck section | 3,317.43 mm² | 3,317.43 mm² |

The reloaded STLs passed the shell, bolt-access and wall checks. The first 3 mm of the flange was compared with the fitted V2 in matched face coordinates to check the bore, bolt holes and seal land. The right print half measures 159.59 × 216.75 × 253.73 mm. [Geometry validation](verified/geometry_validation.json) · [STL and wall-audit manifest](verified/stl/manifest.json)

- [Neck and cable-bracket fit coupon](verified/stl/svt_v2_neck_bracket_fit_coupon.stl) for a bench check of the BBK, IACV, and cable bracket. Use the actual hardware to check cable alignment and full linkage travel.
- [Complete assembly](verified/stl/svt_intake_manifold_v2_1piece_full_codex.stl)
- [Right print-oriented half](verified/stl/svt_intake_manifold_v2_split_right_print_oriented_codex.stl) and [left print-oriented half](verified/stl/svt_intake_manifold_v2_split_left_print_oriented_codex.stl)

The [bypass tracing sheet](../fitment/bypass_capture_1to1.svg) applies to this flange. Trace the actual throttle body's IACV feed and seal to lay out a sealed passage to the manifold's IACV supply pocket. Airflow regression remains paused.

## Reproduce

Run one job at a time.

```powershell
python -B generate_neck_revision.py
python -B generate_neck_revision.py --export verified_rebuild
```
