# 2004 Ford Focus SVT Turbo — 3D-Printable Intake Manifold (Rough Draft)

Parametric CAD generator for a boost-rated, single-stage upper intake manifold designed to replace the OEM plastic IMRC/DSI upper manifold on a **2004 Ford Focus SVT (2.0L Zetec-E Turbo)** while retaining the lower cylinder-head plenum/fuel-rail manifold and its 4 silicone coupler boots.

## Architecture Summary

- **Retained Interface:** Slides directly into the 4 silicone coupler boots on the retained lower cylinder-head manifold (`92.0 mm` center-to-center cylinder spacing).
- **Spigots (`48.0 × 36.0 mm` outer / `38.0 × 26.0 mm` inner, `5.0 mm` wall):** Include a `28.0 mm` clamping land and a `1.5 mm` radial boost-retention bead near the tip so clamps and silicone couplers stay sealed under `12–16 psi` boost.
- **Boost-Optimized Single-Stage Runners & Bellmouths:** IMRC tumble flaps/drum deleted; smooth swept runners (`95.0 mm` axial sweep, `35.0 mm` drop) fed by flared internal velocity-stack bellmouths (`+6.0 mm` radial flare, `14.0 mm` protrusion inside the plenum).
- **Tapered Plenum (`2.110 L` internal volume):** `6.0 mm` wall thickness, rounded-stadium cross-section tapering from `100%` area at Cylinder 4 (TB inlet) down to `78%` area at Cylinder 1 with an ellipsoidal end dome and external stiffening ribs (`6.0 × 5.0 mm`) to resist wall ballooning under boost.
- **Vacuum / Boost Boss Pad:** Thick top boss pad (`70 × 28 × 12 mm`) with `3×` `Ø8.5 mm` pilot bores ready to tap for `1/8"-27 NPT` (or `M10×1.0`) fittings for:
  1. `1:1` Aeromotive Fuel Pressure Regulator / OEM FRPS reference
  2. Blow-Off Valve (BOV) / Wastegate reference
  3. Innovate SCG-1 MAP / Boost Gauge reference
- **Throttle Body Inlet (`Ø65.0 mm`):** Angled `10°` forward neck terminating in a `12.0 mm` thick, `96 × 96 mm` 4-bolt flange (`70 × 70 mm` bolt spacing, `M6` holes) with an integrated face O-ring groove (`Ø73.0 mm` ID).

## Generated Files

All STLs are exported to `stl/` and verified watertight (`is_watertight: true`, `is_volume: true`, `body_count: 1` in `stl/manifest.json`):

| File | Purpose | Extents (mm) | Centauri Carbon 2 (`256×256×256`) |
|---|---|---|---|
| [`svt_runner_boot_fit_gauge.stl`](stl/svt_runner_boot_fit_gauge.stl) | Fast test print of 1 beaded spigot to verify silicone boot fitment | `54.0 × 42.0 × 44.0` | Yes |
| [`svt_tb_flange_fit_gauge.stl`](stl/svt_tb_flange_fit_gauge.stl) | Fast 4 mm check plate for 65 mm TB bore & 4-bolt pattern | `96.0 × 96.0 × 4.0` | Yes |
| [`svt_intake_manifold_split_left_print_oriented.stl`](stl/svt_intake_manifold_split_left_print_oriented.stl) | Cyl 1 & 2 half stood vertically on its flat center split flange (`Z = 0`) | `129.19 × 216.25 × 195.28` | Yes |
| [`svt_intake_manifold_split_right_print_oriented.stl`](stl/svt_intake_manifold_split_right_print_oriented.stl) | Cyl 3 & 4 + TB half stood vertically on its flat center split flange (`Z = 0`) | `129.19 × 216.25 × 231.51` | Yes |
| [`svt_intake_manifold_split_left_cyl1_2.stl`](stl/svt_intake_manifold_split_left_cyl1_2.stl) | Left half in vehicle assembly orientation (`X <= 0`) | `195.28 × 216.25 × 129.19` | Yes |
| [`svt_intake_manifold_split_right_cyl3_4_tb.stl`](stl/svt_intake_manifold_split_right_cyl3_4_tb.stl) | Right half in vehicle assembly orientation (`X >= 0`) | `231.51 × 216.25 × 129.19` | Yes |
| [`svt_intake_manifold_1piece_full.stl`](stl/svt_intake_manifold_1piece_full.stl) | Full 1-piece reference assembly (for packaging study or large SLS/MJF) | `426.79 × 203.76 × 110.87` | No (needs 430 mm bed) |

Diagrams:
- [`fitment/01_intake_manifold_overview.png`](fitment/01_intake_manifold_overview.png) — 3D views, Cyl 3 cross-section (plenum + velocity stack + beaded spigot), and plan layout.
- [`fitment/02_interfaces_1to1_template.svg`](fitment/02_interfaces_1to1_template.svg) — 1:1 mm-scale template of the boot spigot, center split flange, and 65 mm TB flange.

## Regenerating After Parameter Edits

Edit [`intake_manifold_parameters.json`](intake_manifold_parameters.json) and run:

```powershell
python C:\Users\nlm89\source\repos\svt-focus-tuning\cad\intake_manifold\generate_intake_manifold.py
```

## Validation & Measurement Checklist Before Full Print

Because this rough draft uses nominal SVT/Zetec dimensions (`92 mm` pitch, `48 × 36 mm` boot spigot, `70 × 70 mm` TB pattern), verify these measurements on your physical hardware first:

1. **Print both fast gauges in PLA first (`~30 min` total):**
   - Test-fit `svt_runner_boot_fit_gauge.stl` inside your actual silicone coupler boots on the car. Adjust `runners.spigot.outer_width_mm`, `outer_height_mm`, and `corner_radius_mm` in JSON until the boot slides firmly over the `1.5 mm` retention bead without pinching.
   - Bolt/hold `svt_tb_flange_fit_gauge.stl` against your actual throttle body flange. Adjust `throttle_body.bore_diameter_mm`, `bolt_spacing_x_mm`, and `bolt_spacing_y_mm` to match.
2. **Measure on the car with calipers / ruler:**
   - Center-to-center distance between all 4 lower manifold spigots (confirm `92.0 mm` pitch and check if all 4 sit inline).
   - Clearance from the lower manifold spigots back to the firewall, brake booster, strut tower, and hood (`Y` and `Z` space for `95 mm` sweep + `108 mm` plenum depth).
   - Throttle body clearance to battery tray/charge pipe/brake reservoir (`X` position and `10°` forward cant angle).
   - Whether `throttle_body.forward_cant_deg` should be positive (`+10°` away from head) or negative (`-10°` toward firewall/charge pipe routing).

## Printing & Hardware Notes (Centauri Carbon 2)

- **PLA Pro Demo & Fitment Prints (ElegooSlicer Presets Included):**
  - Install the matching presets into ElegooSlicer by closing ElegooSlicer and running [`Install-SVTManifoldProfiles.cmd`](Install-SVTManifoldProfiles.cmd) (or [`Install-SVTManifoldProfiles.ps1`](Install-SVTManifoldProfiles.ps1)).
  - **Main Demo Process:** `PLAPro_0.4_0.24_SVTManifold_Demo_TreeSupport_CC2` (`0.24 mm` layers, `3` Arachne walls, `15%` gyroid infill, `140/190 mm/s` outer/inner walls, `5 mm` outer brim, build-plate-only Tree Supports so internal plenum/velocity-stack/O-ring passages remain clear).
  - **Fitment Gauges Process:** `PLAPro_0.4_0.20_SVTManifold_FitGauges_NoSupport_CC2` (`0.20 mm` layers, `3` walls, `18%` gyroid infill, no brim, no supports).
  - **Filament Preset:** `PLAPro_SVTManifold_Demo_CC2` (inherits `Elegoo PLA PRO @ECC2`: `220 °C` nozzle, `60/55 °C` textured PEI, `0.99` flow, `0.032` PA, `20 mm³/s` max volumetric flow, `80–100%` cooling + `M106 P3 S180` auxiliary fan).
  - **Ready Project File:** [`svt_intake_manifold_PLAPro_Demo_CC2.3mf`](svt_intake_manifold_PLAPro_Demo_CC2.3mf) is pre-configured with all 4 parts on Slot 2 (`PLAPro_SVTManifold_Demo_CC2`), build-plate-only tree supports on the manifold halves, and per-object support-free/0.20 mm overrides on the gauges.
- **Test Fit Only:** PLA / PLA Pro (do **not** run PLA/PLA Pro under-hood on a hot turbocharged engine).
- **Engine-Bay / Boost Service Material:** **PA6-CF / PA12-CF (Carbon-Fiber Nylon)**, **PPA-CF**, or **ASA-CF / ASA** (heat-deflection temperature >= 100–150 °C; anneal nylon parts per filament datasheet before boost testing).
- **Recommended Slicer Settings (for pressure retention in CF-Nylon / ASA):**
  - `6–8` wall perimeters (`>= 2.8–3.2 mm` solid shell)
  - `50–65%` gyroid infill (or `100%` walls around flanges and spigots)
  - `0.16–0.20 mm` layer height, slow outer wall speed for airtight layer adhesion
  - Light tree supports touching buildplate only under the lower runner overhang and TB flange
- **Assembly Hardware (2-Piece Split):**
  - `6×` M6 × 30 mm Socket Head Cap Screws (Grade 10.9 or A2-70) + M6 washers & nuts/threaded inserts
  - `2×` Ø6.0 × 20 mm steel alignment dowel pins
  - `1×` 3.0 mm Viton O-ring cord (cut & CA-glued to length in the left-half center split groove)
  - `1×` 3.0 mm Viton O-ring cord (`Ø73.0 mm` ID) for the throttle body face groove
  - `3×` `1/8"-27 NPT` brass hose barbs / push-to-connect fittings (tap/seal with PTFE paste or high-temp Loctite thread sealant)
  - Recommended post-print pressure check: epoxy or B-45/Permatex thin sealer coat on the external seam or internal vacuum-impregnation resin, followed by a soapy-water `20 psi` bench boost-leak test before installing on the car.
