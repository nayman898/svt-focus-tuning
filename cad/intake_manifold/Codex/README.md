# SVT Stage-2 intake manifold | Exterior smoothing and validation

The Codex revision blends the top and bottom of all four tie-bar roots and the accessible vacuum and boost pad skirts. The one-piece model gained **2.244 cm³** of material, about **0.19%**. The exported solid intersection checks found **0.000 mm³** of added material in the modeled air and accessory passages. The measured source-to-candidate material loss was **0.00050 mm³**, at STL export and Boolean round-off scale. All five exported STLs reopen as watertight, consistently wound single solids.

The current geometry supports a **fit-check candidate**. The claimed 18 psig service rating remains unverified. The STL shows a thinner IACV pocket floor than the centerline figure suggests, and two runner sections show sharp internal lips. The airflow solver reproduces the published 1D metrics at the stated operating point, but cylinder balance changes with the iteration count and the finer 3D grid diverges.

## Models

| STL | Intended use | Bounding box, mm |
|---|---|---:|
| [Full one-piece manifold](stl/svt_intake_manifold_1piece_full_codex.stl) | Vehicle-layout reference and whole-manifold sections | 425.42 × 200.50 × 122.50 |
| [Left half](stl/svt_intake_manifold_split_left_cyl1_2_codex.stl) and [right half](stl/svt_intake_manifold_split_right_cyl3_4_tb_codex.stl) | Assembly orientation | See mesh validation JSON |
| [Left print-oriented half](stl/svt_intake_manifold_split_left_print_oriented_codex.stl) | Cylinders 1 and 2, flange on the bed | 130.19 × 216.75 × 195.98 |
| [Right print-oriented half](stl/svt_intake_manifold_split_right_print_oriented_codex.stl) | Cylinders 3 and 4, TB and IACV, flange on the bed | 130.19 × 216.75 × 229.45 |

Use the two matching Codex print-oriented files for the split fit check. Their model bounds fit the geometric 256 mm cube. Actual sliced support, brim and machine keep-outs were outside this check. The original source STL hashes match the captured manifest. The source files had between 12 and 98 triangles with repeated vertices after export. Dropping those zero-area triangles recovered all five as closed solids before comparison. The Codex STLs pass both exact-coordinate welding and default Trimesh reload. [Before-and-after sections](exterior_sections.png) · [Mesh validation and hashes](mesh_validation.json)

## Geometry and structural findings

| Claim or check | Result on the exported STL |
|---|---|
| 92 mm runner pitch, nominal Ø50.8 mm land and Ø42.8 mm bore | The four land sections at Y = −130.3 mm measure Ø50.790–50.798 mm outside and Ø42.792–42.798 mm inside. The ~0.01 mm range reflects the STL facets. The land and retention-bead triangles are identical to the source. |
| Ø65 mm throttle bore and protected mounting features | The bore measures Ø64.987–64.999 mm 1.33 mm behind the mating face. The throttle-body and IACV interface triangles are identical to the source. The split flange and sealing region have zero measurable Boolean volume difference. A few coplanar triangles near the split are triangulated differently. |
| M6 washer / socket clearance | 0.000 mm³ interference for the specified Ø12.4 mm cylindrical probes at all six split-bolt positions on both halves and all four throttle-body positions. |
| Uniform 6.5 mm plenum barrel | The front barrel sampled **5.11–6.50 mm**. The generator scales the outer and inner profiles together, so 6.5 mm is the nominal thickness at the wide end. The narrow end is thinner by design. |
| 4.91 mm isolated IACV supply floor | **4.94 mm at the pocket center** and **3.41 mm at the thinnest sampled point**, near X = 179.25 mm, Y = 0.25 mm. This is below the generator's 4.5 mm centerline check if 4.5 mm is intended to be a minimum across the floor. The source and candidate measurements agree. |
| Tooth-free bellmouths with ≥5.22 mm wall in the transition zone | The sampled sections show **0.68 mm and 0.75 mm solid spans** through internal lips where the cylinder 3 and 4 runner bores meet the plenum. The ray passes back into the plenum after crossing each lip. These are measurements of a solid feature between air spaces. The minimum exterior pressure-wall thickness in that zone remains unverified. |
| 18 psig structural rating | The parameter file says **16 psig**, and the airflow case uses **18 psig**. Neither value is supported here by printed-material allowables, stress or fatigue data for the loaded assembly, or test results. The additive blends preserve the existing material to measurement tolerance. Qualification of the actual print, seals, hardware and support remains open. |

The geometry audit used transverse STL sections, 12 bellmouth and early-runner stations per cylinder, 72 ray directions per station where they intersected the local wall, and 468 vertical measurements across the IACV pocket. These are sampled values. Pressure qualification would need the selected material and print process, bolt and clamp loads, operating temperature, and evidence from the assembled part. The Ford fit, O-ring squeeze and installed clearances still require physical checks. [Section measurements and witness coordinates](geometry_measurements.json) · [Internal lip close-ups](bellmouth_sections.png) · [NIST polymer additive manufacturing materials testing review](https://nvlpubs.nist.gov/nistpubs/ir/2015/NIST.IR.8059.pdf)

## Airflow findings at 18 psig, 7,000 RPM and 52 °C IAT

The solver applies **0.2777 kg/s (36.74 lb/min)** as its operating point. The rerun uses the current Stage-2 CAD air domain. The STL comparison tied that domain to the smoothing by checking both the additive solids and the exported volume differences against the main cavity, vacuum pilots and IACV cutters. No added volume intersected those passages. This establishes geometry equivalence for the model inputs within the check tolerance. The 3D solver omits the accessory branches and treats the downstream runners and valves as modeled resistance.

| Metric | Published Stage-2 | Current CAD at the same settings |
|---|---:|---:|
| Bare plenum volume | 2.024 L | 2.024 L |
| Clipped main-path volume | 2.933 L | 2.934 L |
| 1D pressure drop | 1.836 kPa / 0.266 psi | 1.836 kPa / 0.266 psi |
| 1D VE spread / 720° trapped-mass spread | 0.44% / 0.20% | 0.44% / 0.20% |
| Mean runner discharge coefficient | 0.9197 | 0.9197 |
| Peak throat / exit Mach | 0.279 / 0.296 | 0.279 / 0.296 |
| Helmholtz frequency / modeled harmonic RPM | 118.8 Hz / 4,751 RPM | 118.8 Hz / 4,751 RPM |
| 3D pressure drop at 4 mm and 40 iterations | 2.429 kPa / 0.352 psi | 2.427 kPa / 0.352 psi |
| 3D cylinder spread at 4 mm and 40 iterations | 0.33% | 0.35% |
| 3D pressure drop and cylinder spread at 4 mm and 80 iterations | — | 2.477 kPa / 0.359 psi and 1.45% |
| 3D solver at 2 mm and 80 iterations | — | Diverged, 100% mass imbalance |

The 40-iteration 3D rerun used **45,540 cells**, versus **45,526** in the archived README, and agrees with the later factory comparison document's reported cell count and **0.35%** spread. The solver reported 0.00% rounded mass imbalance at both 4 mm iteration counts. Balance still shifted by 1.10 percentage points. The reported **0.00% stack blockage** is assigned when the model uses the flush option with no separate protruding sleeve. It does not measure the local sharp lips observed in the exported geometry. [Solver output and sensitivities](airflow_reproduction.json) · [Archived results](reference/airflow_verification.json) · [NASA CFD verification guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html)

The factory comparison's estimated **41.30 lb/min at 7,000 RPM and 72 °F IAT**, **+10–12 crank HP** and per-cylinder AFR spread are outputs of an OEM-versus-custom model. The logged **37.85 lb/min at 6,397 RPM** anchors the OEM-side estimate. The custom predictions remain unvalidated by a flow bench, cylinder-resolved measurements or a back-to-back dyno run. [Factory comparison snapshot](reference/FACTORY_VS_CUSTOM_COMPARISON.md) · [Vehicle log review](../../../reports/2026-11-06-v037-iat-thermal-and-power-review.md)

## Reproduce

Run from the parent intake-manifold folder with Python 3.11 and `manifold3d`, `matplotlib`, `numpy`, `scipy`, `shapely` and `trimesh`. The CAD code, parameters, manifest and published results used for the audit are captured in `reference/`. The archived Markdown keeps the links from its original location. The 2 mm solver case can take several minutes.

```powershell
python -B Codex/smooth_manifold.py
python -B Codex/check_geometry.py
python -B Codex/check_airflow.py
```
