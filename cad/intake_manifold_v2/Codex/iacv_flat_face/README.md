# V2 flat throttle face with integrated IACV feed

The newest revision trims the round shoulder behind the square throttle flange and opens the split joint to match the tapered plenum. It carries forward the extended cable-bracket neck and the smoother IACV route from the [previous revision](validation/VALIDATION.md). The [airflow regression and design review](overhang_regression/GEMINI_REVIEW.md) covers the assembled split STLs.

- [Corrected full assembly](flange_corrected/stl/svt_intake_manifold_v2_1piece_full_codex.stl)
- [Corrected right print half](flange_corrected/stl/svt_intake_manifold_v2_split_right_print_oriented_codex.stl) and [left print half](flange_corrected/stl/svt_intake_manifold_v2_split_left_print_oriented_codex.stl)
- [Corrected flat-face fit coupon](flange_corrected/stl/svt_v2_flat_face_iacv_fit_coupon.stl)
- [Flange section before and after](overhang_regression/flange_back_comparison.png) and [corrected STL render](validation/flange_corrected_flange_back.png)

## Cable bracket location

The bracket sits on the two round posts beside the IACV pad on the throttle neck. The pilots are 28.00 mm apart, 5.2 mm in diameter and 10 mm deep. The post tops share a horizontal mounting plane 70.21 mm above the manifold datum. [Marked top view](flange_corrected/fitment/cable_bracket_mount.png) · [Combined throttle, IACV and cable bracket fit coupon](flange_corrected/fitment/svt_v2_cable_bracket_fit_coupon.stl)

| Pilot center | X toward cylinder 4 | Y toward firewall | Behind throttle mating plane |
|---|---:|---:|---:|
| A, firewall side | 195.83 mm | −17.38 mm | 23.96 mm |
| B, radiator side | 177.00 mm | −38.10 mm | 28.80 mm |

Coordinates are in the unrotated manifold assembly. Setback is measured perpendicular to the angled throttle mating plane. The exported mesh confirms the pilots at these locations. The bracket seat and cable exit location on the actual factory hardware still need a fit check. Seat the cable housing and both cables if cruise control is installed. With the engine off, check that the throttle reaches both stops and returns freely from full opening with the IACV installed. [Ford SVT accelerator cable service procedure](https://charm.li/Ford/2004/Focus%20L4-2.0L%20DOHC%20VIN%205/Repair%20and%20Diagnosis/Powertrain%20Management/Fuel%20Delivery%20and%20Air%20Induction/Throttle%20Cable%2FLinkage/Service%20and%20Repair/)

The coupon measures 136.39 × 144.29 × 128.73 mm in its print orientation and sliced on the Centauri Carbon 2. [Coupon slice check](validation/slicer_result_cable_bracket_fit.json)

## First flat-face revision

This revision starts from the extended-neck Codex V2. The manifold face is flat so the throttle body's own molded O-ring seals against it. The manifold's center split uses its existing seal.

The secondary face opening follows the [factory photo trace](../fitment/factory_photo_plate/README.md) with a 1.8 mm inset to give the seal and bore divider more material. The opening blends down to an 11.1 mm round passage routed around the cable-bracket pilots and flange sockets. The passage enters the isolated IACV supply pocket above its floor. The valve's separate outlet leads to the plenum. The former external supply tap is closed in this model.

| CAD check | Result |
|---|---:|
| Traced seal centerline to nearest edge on the mating face | 1.60 mm |
| IACV feed to the main air passage | 4.93 mm |
| New passage to the IACV mounting face | 4.83 mm |
| New passage to the cable-bracket pilots | 8.10 mm |
| Smallest sampled main throat section | 3,308.70 mm² |

A local taper of up to 0.67 mm at the bore edge backs the narrow part of the gasket. The sampled area is 8.73 mm² smaller than the extended-neck baseline, a 0.26% reduction. The reloaded STLs passed the shell, wall and socket-access checks. [Geometry validation](verified/geometry_validation.json) · [STL manifest](verified/stl/manifest.json)

- [Flat throttle-face fit coupon](verified/stl/svt_v2_flat_face_iacv_fit_coupon.stl)
- [Full assembly](verified/stl/svt_intake_manifold_v2_1piece_full_codex.stl)
- [Right print half](verified/stl/svt_intake_manifold_v2_split_right_print_oriented_codex.stl) and [left print half](verified/stl/svt_intake_manifold_v2_split_left_print_oriented_codex.stl)

Check the actual factory throttle body and molded seal against the fit coupon. The photo sets the estimated location and outline of the feed, while the coupon lets the actual parts confirm the seal footprint, bolt fit, and passage overlap. The CAD checks are geometric. A bench leak test is needed to check the assembled air path and seal.

## Reproduce

Run from this folder. The export uses one local job and stages the files before publishing them.

```powershell
python -B generate_iacv_revision.py --export verified_rebuild --path wider --cup -27 26
python -B generate_iacv_revision.py --export refined_rebuild --path smoothed --cup -29 24 --polish
python -B generate_iacv_revision.py --export flange_corrected_rebuild --path smoothed --cup -29 24 --polish --flush-flange --clear-split
python -B validation/cable_bracket_fit.py
```
