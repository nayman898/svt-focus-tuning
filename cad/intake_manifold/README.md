# 2004 Ford Focus SVT Turbo — 3D-Printable Intake Manifold (Rough Draft)

Parametric CAD generator for a boost-rated, single-stage upper intake manifold designed to replace the OEM plastic IMRC/DSI upper manifold on a **2004 Ford Focus SVT (2.0L Zetec-E Turbo)** while retaining the lower cylinder-head plenum/fuel-rail manifold and its 4 silicone coupler boots.

## Architecture Summary

- **Retained Interface:** Slides directly into the 4 silicone coupler boots on the retained lower cylinder-head manifold (`92.0 mm` center-to-center cylinder spacing).
- **Spigots (`Ø50.8 mm` / `2.00"` outer, `Ø42.8 mm` inner, `4.0 mm` clamped boot wall):** Sized to match **MarraSport / Massive Speed System `2.00" ID × 2.00"` round 4-ply Kevlar/Samco silicone intake boots** with `NORMA 40-60` clamps. Includes a `27.0 mm` clamping land (`25.4 mm` half-boot engagement + `1.6 mm` sweep clearance) and a `1.1 mm` radial × `5.0 mm` wide boost-retention bead at `3.5 mm` from the tip (`53.0 mm` bead OD, leaving `16.9 mm` flat clamping land behind the bead). Moving from the `38 × 26 mm` baseline (`884.1 mm²`) to a `Ø42.8 mm` round bore (`1,438.7 mm²`, **+62.7%** flow area) drops peak exit Mach from `0.474` to **`0.296`** at `7,000 RPM` / `18 psi`.
- **Stage-2 Max-Boost Runners & Progressive Scoop Velocity-Stack Bellmouths:** IMRC tumble flaps/drum deleted; expanded `46 × 40 mm` runner throats (`1,523.6 mm²`) with wall-flush `+7.0 mm` radial flare bellmouths and progressive upstream scoop cant (`[0.0°, 2.5°, 5.0°, 7.5°]` across Cyl 1–4) blended into the tapered plenum wall (`0.0%` cross-flow blockage).
- **Tapered Plenum (`1.989 L` internal volume, Compatible Center Split Seam):** `6.0 mm` wall thickness, `96.0 × 84.0 mm` (`R = 38.0 mm`) base section tapering piecewise from `100%` area at Cylinder 4 (`X = +170 mm`) through **exact `88.87%` (`90.50 × 79.19 mm` ID / `140.50 × 129.19 mm` flange OD) at the `X = 0` split flange** down to `60%` area at Cylinder 1 (`X = -166 mm`). This locks the center split joint (`6×` M6 bolts, `2×` Ø6 mm dowel pins, and O-ring groove) identically to the original `commit 62e02fc` half (`0.000 mm` step) so a new right half bolts directly onto an already-printed original left half.
- **5-Port Top Vacuum & Boost Reference Pads:**
  - **Right Pad (Direct Boost + Vacuum — NO check valves):** `70 × 28 × 12 mm`, `3×` `Ø8.5 mm` (`1/8"-27 NPT`):
    1. Dedicated **Blow-Off Valve (BOV)** reference line
    2. **`1:1` Aeromotive FPR & OEM FRPS** reference
    3. **Innovate SCG-1 MAP / Boost Gauge** reference
  - **Left Pad (Check-Valved Vacuum-Only Systems — Protected from 18 psi Boost):** `52 × 28 × 12 mm`:
    4. **Brake Booster:** `Ø11.1 mm` (`1/4"-18 NPT`) for `3/8"` hose + **inline boost-rated check valve**
    5. **EVAP Canister Purge:** `Ø8.5 mm` (`1/8"-27 NPT`) + **inline boost-rated check valve**
- **2-Bolt Ford IACV Mount (`46.0 mm` bolt centers, `M6` blind pilots, dual `Ø13.0 mm` ports):** Located on top of the TB neck / Cyl 4 junction (`48 × 68 mm` pad):
  - **Downstream port (`X = 163 mm`):** Discharges directly into the plenum chamber.
  - **Upstream metered supply port (`X = 185 mm`):** Isolated blind pocket (`5.04 mm` solid floor above the TB bore) fed via a rear-facing **`1/4"-18 NPT` (`Ø11.1 mm` pilot)** barb port. Route a `3/8"` or `1/2"` hose from the charge pipe **between the blow-through PMAS HPX MAF and the throttle body** into this side barb so idle air remains accurately metered by the MAF.
- **Throttle Body Inlet (`Ø65.0 mm`):** Angled `7°` forward neck (reduced from `10°` to minimize oblique jet separation into Cyl 4) terminating in a `12.0 mm` thick, `96 × 96 mm` 4-bolt flange (`70 × 70 mm` bolt spacing, `M6` holes) with an integrated face O-ring groove (`Ø73.0 mm` ID).

## Airflow & 18 PSI Boost Verification (`verify_airflow.py`)

Verified via [`verify_airflow.py`](verify_airflow.py) at **18.0 psig boost (`225.43 kPa` abs, `52.0 °C` IAT, `7,000 RPM`, `0.2777 kg/s` / `36.74 lb/min`)** using exact `manifold3d` CAD fluid-cavity slicing, a cylinder-aligned `4.0 mm` (`45,194` cells, `0.0%` mass error) conservative 3D Finite-Volume Navier-Stokes solver, and a 1D compressible + `720°` crank-angle pulsating cycle model (`1-3-4-2` firing order):

| Metric (7,000 RPM @ 18 PSI Boost) | Baseline (`14 mm` Sleeves, `38×26`, `96×84`, `0.78` Taper, `10°` TB) | Stage-2 Compatible Max-Boost (Flush `+7 mm`, Scoop, `Ø42.8` Round Boot, `0.60/0.889` Taper, `7°` TB) | Result |
|---|---:|---:|---|
| **Plenum Cross-Flow Wake Blockage (CAD Slice)** | `14.32%` mean (`14.66%` peak) | `0.00%` | **Eliminated** |
| **1D Upper-Manifold Pressure Drop ($\Delta P$)** | `4.042 kPa` (`0.586 psi`) | `1.864 kPa` (`0.270 psi`) | **-53.9% loss** |
| **3D FVM Manifold Pressure Drop ($\Delta P$)** | `2.778 kPa` (`0.403 psi`) | `2.437 kPa` (`0.353 psi`) | **-12.3% loss** |
| **3D FVM Cylinder Flow Balance Spread** | `0.80%` (`[25.09, 25.05, 24.96, 24.89]%`) | `0.36%` (`[25.05, 25.00, 24.98, 24.96]%`) | **-55% spread** |
| **1D Compressible Network VE Spread** | `1.44%` | `0.50%` | **-65% spread** |
| **720° CA Pulsating Trapped-Mass Spread** | `0.55%` | `0.23%` | **-58% spread** |
| **Mean Runner Discharge Coefficient ($C_d$)** | `0.9159` | `0.9192` | **+0.4% ($C_d$)** |
| **Peak Instantaneous Throat / Exit Mach** | `0.302` / `0.474` | `0.279` / `0.296` | **-37.6% exit Mach** |
| **Plenum Helmholtz Resonance (3rd Harmonic)** | `102.3 Hz` (`4,091 RPM`) | `119.6 Hz` (`4,785 RPM`) | Spool-band boost assist |

- Multi-panel verification plot: [`fitment/03_airflow_verification.png`](fitment/03_airflow_verification.png)
- Full simulation JSON report (including `3,000–7,500 RPM` and taper sweeps): [`stl/airflow_verification.json`](stl/airflow_verification.json)
- Factory SVT DSI comparison report & chart: [`FACTORY_VS_CUSTOM_COMPARISON.md`](FACTORY_VS_CUSTOM_COMPARISON.md) / [`fitment/04_factory_vs_custom_comparison.png`](fitment/04_factory_vs_custom_comparison.png) / [`stl/factory_comparison.json`](stl/factory_comparison.json)
- Companion sloped dual-chamber WRC variant (isolated): [`../intake_manifold_wrc/README.md`](../intake_manifold_wrc/README.md)

## Generated Files

All STLs are exported to `stl/` and verified watertight (`is_watertight: true`, `is_volume: true`, `body_count: 1` in `stl/manifest.json`):

| File | Purpose | Extents (mm) | Centauri Carbon 2 (`256×256×256`) |
|---|---|---|---|
| [`svt_runner_boot_fit_gauge.stl`](stl/svt_runner_boot_fit_gauge.stl) | Fast test print of 1 beaded round spigot (`Ø50.8 outer / Ø42.8 inner` for `2"` boot) | `56.8 × 56.8 × 44.0` | Yes |
| [`svt_tb_flange_fit_gauge.stl`](stl/svt_tb_flange_fit_gauge.stl) | Fast 4 mm check plate for 65 mm TB bore & 4-bolt pattern | `96.0 × 96.0 × 4.0` | Yes |
| [`svt_iacv_flange_fit_gauge.stl`](stl/svt_iacv_flange_fit_gauge.stl) | Fast 4 mm check plate for 2-bolt Ford IACV (`46 mm` bolts / dual `13 mm` ports) | `48.0 × 68.0 × 4.0` | Yes |
| [`svt_alignment_dowel_pins.stl`](stl/svt_alignment_dowel_pins.stl) | Printable horizontal flat-bottom alignment dowel pins (`2× Ø5.85 mm` + `2× Ø5.75 mm`, mockup only) | `20.0 × 41.8 × 5.5` | Yes |
| [`svt_intake_manifold_split_left_print_oriented.stl`](stl/svt_intake_manifold_split_left_print_oriented.stl) | Cyl 1 & 2 half stood vertically on its flat center split flange (`Z = 0`) | `129.19 × 216.25 × 195.28` | Yes |
| [`svt_intake_manifold_split_right_print_oriented.stl`](stl/svt_intake_manifold_split_right_print_oriented.stl) | Cyl 3 & 4 + TB + IACV half stood vertically on its flat center split flange (`Z = 0`) | `129.19 × 216.25 × 229.45` | Yes |
| [`svt_intake_manifold_split_left_cyl1_2.stl`](stl/svt_intake_manifold_split_left_cyl1_2.stl) | Left half in vehicle assembly orientation (`X <= 0`) | `195.28 × 216.25 × 129.19` | Yes |
| [`svt_intake_manifold_split_right_cyl3_4_tb.stl`](stl/svt_intake_manifold_split_right_cyl3_4_tb.stl) | Right half in vehicle assembly orientation (`X >= 0`) | `229.45 × 216.25 × 129.19` | Yes |
| [`svt_intake_manifold_1piece_full.stl`](stl/svt_intake_manifold_1piece_full.stl) | Full 1-piece reference assembly (for packaging study or large SLS/MJF) | `424.72 × 203.76 × 122.50` | No (needs 425 mm bed) |

Diagrams:
- [`fitment/01_intake_manifold_overview.png`](fitment/01_intake_manifold_overview.png) — 3D views, Cyl 3 cross-section (plenum + velocity stack + beaded spigot), and plan layout.
- [`fitment/02_interfaces_1to1_template.svg`](fitment/02_interfaces_1to1_template.svg) — 1:1 mm-scale template of the boot spigot, center split flange, 65 mm TB flange, and 2-bolt Ford IACV flange.
- [`fitment/03_airflow_verification.png`](fitment/03_airflow_verification.png) — 3D FVM flow fields, CAD blockage audit, taper sweep, cylinder VE balance, and `720°` crank cycle plots.

## Regenerating After Parameter Edits

Edit [`intake_manifold_parameters.json`](intake_manifold_parameters.json) and run:

```powershell
python cad/intake_manifold/generate_intake_manifold.py
python cad/intake_manifold/update_3mf_project.py
```

## Validation & Measurement Checklist Before Full Print

Because this rough draft uses nominal SVT/Zetec dimensions (`92 mm` pitch, `Ø50.8 mm` / `2.00"` round boot spigot, `70 × 70 mm` TB pattern, `46 mm` IACV bolt spacing), verify these measurements on your physical hardware first:

1. **Print all three fast gauges in PLA Pro first (`~45 min` total):**
   - Test-fit `svt_runner_boot_fit_gauge.stl` inside your actual `2.00"` MarraSport silicone coupler boots (and/or test against an OEM lower manifold bore). Adjust `runners.spigot.outer_width_mm`, `outer_height_mm`, and `corner_radius_mm` in JSON until the boot slides cleanly over the `1.1 mm` retention bead (`53.0 mm` OD) without bunching.
   - Bolt/hold `svt_tb_flange_fit_gauge.stl` against your actual throttle body flange. Adjust `throttle_body.bore_diameter_mm`, `bolt_spacing_x_mm`, and `bolt_spacing_y_mm` to match.
   - Bolt/hold `svt_iacv_flange_fit_gauge.stl` against your 2-bolt Ford IAC valve and Motorcraft CG-756 gasket. Adjust `throttle_body.iacv_mount.bolt_spacing_y_mm`, `port_spacing_x_mm`, and `port_diameter_mm` if needed.
2. **Measure on the car with calipers / ruler:**
   - Center-to-center distance between all 4 lower manifold spigots (confirm `92.0 mm` pitch and check if all 4 sit inline).
   - Clearance from the lower manifold spigots back to the firewall, brake booster, strut tower, and hood (`Y` and `Z` space for `95 mm` sweep + `108 mm` plenum depth).
   - Throttle body clearance to battery tray/charge pipe/brake reservoir (`X` position and `7°` forward cant angle).
   - Whether `throttle_body.forward_cant_deg` should be positive (`+7°` away from head) or negative (`-7°` toward firewall/charge pipe routing).

## Printing & Hardware Notes (Centauri Carbon 2)

- **PLA Pro Demo & Fitment Prints (ElegooSlicer Presets Included):**
  - Install the matching presets into ElegooSlicer by closing ElegooSlicer and running [`Install-SVTManifoldProfiles.cmd`](Install-SVTManifoldProfiles.cmd) (or [`Install-SVTManifoldProfiles.ps1`](Install-SVTManifoldProfiles.ps1)).
  - **Main Demo Process:** `PLAPro_0.4_0.24_SVTManifold_Demo_TreeSupport_CC2` (`0.24 mm` layers, `3` Arachne walls, `15%` gyroid infill, `140/190 mm/s` outer/inner walls, `5 mm` outer brim, build-plate-only Tree Supports so internal plenum/velocity-stack/O-ring passages remain clear).
  - **Fitment Gauges Process:** `PLAPro_0.4_0.20_SVTManifold_FitGauges_NoSupport_CC2` (`0.20 mm` layers, `3` walls, `18%` gyroid infill, no brim, no supports).
  - **Filament Preset:** `PLAPro_SVTManifold_Demo_CC2` (inherits `Elegoo PLA PRO @ECC2`: `220 °C` nozzle, `60/55 °C` textured PEI, `0.99` flow, `0.032` PA, `20 mm³/s` max volumetric flow, `80–100%` cooling + `M106 P3 S180` auxiliary fan).
  - **Ready Project File:** [`svt_intake_manifold_PLAPro_Demo_CC2.3mf`](svt_intake_manifold_PLAPro_Demo_CC2.3mf) is pre-configured with all 6 parts (`split_right`, `split_left`, `runner_boot_fit_gauge`, `tb_flange_fit_gauge`, `iacv_flange_fit_gauge`, and `alignment_dowel_pins`) on Slot 2 (`PLAPro_SVTManifold_Demo_CC2`), build-plate-only tree supports on the manifold halves, and per-object support-free/0.20 mm overrides on the 3 gauges and alignment dowel pins.
- **Test Fit Only:** PLA / PLA Pro (do **not** run PLA/PLA Pro under-hood on a hot turbocharged engine).
- **Engine-Bay / Boost Service Material:** **PPA-CF**, **PAHT-CF (PA12-CF)**, or **PET-CF** (heat-deflection temperature >= 150–225 °C; anneal in a foil-shielded oven at `95–100 °C` for `6 hours` and seal layer lines with fuel-resistant high-temp epoxy before 18 psi boost testing).
- **Recommended Slicer Settings (for 18 psi retention in CF-Nylon):**
  - `8–10` wall perimeters (`100%` solid plenum/runner walls)
  - `0.16–0.20 mm` layer height, `295–300 °C` hot & slow outer walls, `0%` cooling fan except steep overhangs
  - Light tree supports touching buildplate only under the lower runner overhang and TB flange
- **Assembly Hardware & Check Valves (2-Piece Split, 18 psi Boost):**
  - `6×` M6 × 30 mm Socket Head Cap Screws (Grade 10.9 or A2-70) + M6 washers & nuts/threaded inserts (center flange)
  - `2×` M6 × 20–25 mm bolts + M6 brass heat-set inserts (for the 2-bolt IACV pad) + Motorcraft CG-756 IACV gasket
  - `2×` Ø6.0 × 20 mm steel alignment dowel pins
  - `1×` 3.0 mm Viton O-ring cord (cut & CA-glued to `~294 mm` in the left-half center split groove; or `94 mm ID × 3.0 mm` Viton O-ring)
  - `1×` 3.0 mm Viton O-ring (`73 mm ID × 3.0 mm`, AS568-151) for the throttle body face groove
  - `4×` `1/8"-27 NPT` brass hose barbs (BOV, FPR/FRPS, SCG-1 MAP, EVAP purge) + `2×` `1/4"-18 NPT` brass hose barbs (Brake booster + IACV charge-pipe supply) sealed with PTFE paste / high-temp thread sealant
  - **Required One-Way Check Valves (for 18 psi boost protection):**
    - **Brake Booster Line:** Inline **`3/8"` aluminum/Viton boost check valve** rated >= `30+ psi` reverse pressure (flow arrow pointing **toward the intake manifold** — holds vacuum in the booster, blocks boost). Note: the factory plastic OEM booster check valve is often weak/leaking at 18 psi, so add an aluminum/Viton inline check valve on the `3/8"` hose.
    - **EVAP Canister Purge Line:** Inline **`1/4"` or `5/16"` Viton-diaphragm aluminum check valve** rated >= `30+ psi` (flow arrow pointing **toward the intake manifold**, placed between the intake manifold EVAP barb and the OEM EVAP purge solenoid so 18 psi boost never pressurizes the EVAP solenoid or charcoal canister/fuel tank).
    - **Do NOT put check valves** on the **BOV**, **1:1 FPR/FRPS**, or **SCG-1 MAP/Boost Gauge** lines — those must read both vacuum and full `18 psi` positive boost directly.
  - Recommended post-print pressure check: seal exterior walls with fuel-resistant high-temp epoxy and run a soapy-water `20–25 psi` bench boost-leak test before installing on the car.
