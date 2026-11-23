# Focus SVT V2 Codex intake manifold

This candidate combines a smoother throttle neck, an eccentric BBK mounting pattern and two separate cable-bracket posts. The generator and all revised exports are under `Codex/`. The reference folder captures the Gemini V2 geometry used for the comparison. The parent V2’s bolt dimensions were updated independently during the work. The Codex comparison uses the pinned parent with the same neck geometry.

## Fit files

- [Flat factory throttle face with integrated IACV feed](iacv_flat_face/README.md) with a sealing-face coupon and complete manifold.
- [Extended-neck and cable bracket revision](neck_bracket_revision/README.md) with an 8 mm extension and a dedicated fit coupon.
- [BBK throttle fit gauge STL](stl/svt_v2_tb_flange_fit_gauge_codex.stl) and [1:1 paper pattern](fitment/bbk_throttle_pattern_1to1.svg). The plate is 4 mm thick. Check the four fasteners and bore alignment with the actual hardware before printing a half.
- [1:1 throttle bypass tracing sheet](fitment/bypass_capture_1to1.svg) and [idle-air routing notes](fitment/THROTTLE_BYPASS.md). Trace the bypass opening and the gasket against the fitted bolt grid.
- [Right print-oriented half](stl/svt_intake_manifold_v2_split_right_print_oriented_codex.stl) and [matching left half](stl/svt_intake_manifold_v2_split_left_print_oriented_codex.stl). Bounding boxes are **159.59 × 216.75 × 247.15 mm** and **159.59 × 216.75 × 195.98 mm**, respectively. They fit the nominal 256 mm printer cube by geometry. Supports and printer keep-outs are separate slicer checks.
- [One-piece assembly](stl/svt_intake_manifold_v2_1piece_full_codex.stl), [throttle-neck comparison](fitment/07_throttle_neck_comparison.png) and [bracket clearance comparison](fitment/08_cable_bracket_clearance.png).

## BBK flange and throttle neck

The measured 72 mm inside gap and approximately 7 mm hole diameter give **79 × 79 mm** center spacing. The candidate uses Ø7 mm clearance holes and a nominal Ø65 mm bore. The bore center is **5 mm toward the firewall and 7 mm toward the ground** relative to the bolt grid. The 7 mm figure comes from interpreting the lower bolt-center line as tangent to the nominal bore. The gauge is the physical check for that interpretation. The flange remains on the frozen V2 throttle plane with its 32° yaw and 14° upward pitch. The outside plate is 96 × 100 mm with fuller corners to support the wider pattern. The nearest rear bolt has a local socket relief that retains the washer seat and approximately 4.6 mm separation from the main bore.

The revised loft uses eased transitions for both section size and section rotation. The minimum sampled area rose from roughly **3,287 mm² to 3,317 mm²**, eliminating the shallow neck restriction and keeping the nominal throttle bore. The comparison plot uses sections parallel to the throttle face. The geometry checks cover the exported STLs, the bore and face seal, boot lands, and rear socket access. [Geometry results](geometry_validation.json) · [STL manifest and hashes](stl/manifest.json)

## Cable bracket clearance

The previous wide pedestal crowded the IACV pad, and one of its pilot holes entered that pad’s envelope. Two independent **Ø15 mm** posts replace the pedestal. Each blends into the throttle neck through a wider foot. The new center pair retains **28 mm** pitch, orientation and the 69 mm mounting-plane height. It moves **12 mm toward the radiator and 1 mm toward cylinder 1** to get the post next to the IACV out of the pad. The pilot holes are Ø5.2 mm and 10 mm deep. The CAD measures **5.14 mm** minimum separation from the cable pilots to the main air path.

The posts have **1.48 mm** minimum clearance to the modeled IACV pad and **1.85 mm** to the throttle flange. The real cable bracket, valve housing and linkage travel need a physical fit check. Check cable routing and full throttle travel and return with the engine off before vehicle use. [Ford documentation on cable and bracket interference](https://static.nhtsa.gov/odi/inv/2010/INRD-PE10019-48742.pdf)

## Airflow screening

The frozen V2 solver reported convergence on two 4 mm grid alignments at 18 psig, 52 °C and 0.2777 kg/s imposed inlet flow. Modeled pressure loss went from **1.3530 to 1.2566 kPa** on the aligned case and **1.3079 to 1.2438 kPa** on the shifted case. Cylinder spread went from **7.001% to 6.668%** and from **6.344% to 6.139%**, respectively. These are screening comparisons on one grid spacing. Printed-part pressure qualification and on-car performance remain open. [Aligned run](airflow_screen.json) · [Shifted run](airflow_screen_offset_2mm.json) · [NASA grid convergence guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)

## Reproduce

Run from the parent V2 folder with Python 3.11 and `manifold3d`, `matplotlib`, `numpy`, `scipy`, `shapely` and `trimesh`.

```powershell
python -B Codex/generate_intake_manifold_v2_codex.py
python -B Codex/verify_geometry.py
python -B Codex/compare_airflow.py
python -B Codex/compare_airflow.py --offset 2
```
