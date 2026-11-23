# Complete Dual-Stage NA Intake Manifold Parts List (BOM)

Everything required to print, machine, assemble, seal, actuate, and bench-test the **2002–2004 Ford Focus SVT / ST170 (2.0L Zetec-R NA)** Modular Dual-Stage (DSI) Intake Manifold.

---

## 1. 3D-Printed Composite Parts & Print/Cure Consumables

| Qty | Item / File | Material / Spec | Notes |
| :---: | --- | --- | --- |
| `1` | `stl/svt_na_dsi_manifold_split_left_print_oriented.stl` | **PPA-CF** or **PAHT-CF** (`1002.58 cm³`, `~1.26 kg` w/ right) | Left half (`203.62 × 232.00 × 193.48 mm`, CC2 `256³` fit) |
| `1` | `stl/svt_na_dsi_manifold_split_right_print_oriented.stl` | **PPA-CF** or **PAHT-CF** (`1195.72 cm³`) | Right half + V2 flat-face TB/IACV (`197.94 × 246.69 × 253.73 mm`, CC2 `256³` fit) |
| `2` | `stl/svt_na_dsi_service_hatch_left.stl` & `right.stl` | **PPA-CF** or **PAHT-CF** (`28.35 cm³` each) | Top service hatch lids (`122.0 × 48.0 × 5.7 mm`) |
| `1` | `stl/svt_na_dsi_seal_retainer_plate.stl` | **PPA-CF** or **PAHT-CF** (`5.51 cm³`) | `+X` (TB-side) Viton lip-seal retainer plate (`40.0 × 32.0 × 5.0 mm`) |
| `1` | `stl/svt_na_dsi_actuator_bracket_universal.stl` | **PPA-CF** or **PAHT-CF** (`10.39 cm³`) | `+X` (TB-side) IMRC actuator bracket (`51.0 × 46.0 × 26.0 mm`) |
| `1` set | Fitment Gauges (`5×` STLs in `stl/`) | PLA / PETG / PPA-CF | `runner_boot`, `tb_flange` / `flat_face_iacv_fit_coupon`, `iacv_flange`, `valve_bore`, `alignment_dowel_pins` |
| `2.5–3 kg` | **PPA-CF** or **PAHT-CF** filament (`1.75 mm`) | Dried `< 15% RH` | `6` perimeters, `40–50%` gyroid infill, `290–310 °C` hardened nozzle |
| `1` | High-temp penetrating epoxy | **Loctite E-120HP**, **3M DP420**, or **JB Weld HighHeat** | External porosity seal coat (keep gasket grooves & bearing pockets masked) |

---

## 2. Custom CNC / Laser Metal Valve Hardware (`cnc/`)

> **FOD Safety Rule:** Never 3D-print internal butterfly plates or the valve shaft.

| Qty | File | Material & Process | Key Spec |
| :---: | --- | --- | --- |
| `4` | `cnc/svt_na_dsi_butterfly_plate_304ss_1p5mm.step` / `.dxf` | **304 Stainless Steel**, `1.5 mm` laser/waterjet | `43.5 × 43.927 mm` ellipse matched to `8°` slanted `Ø44.0 mm` bore |
| `1` | `cnc/svt_na_dsi_valve_shaft_8mm_304ss.step` | **304 Stainless Steel** round bar, CNC milled | `Ø8.0 mm × 363.0 mm` (`+X` double-D flat `6.0 × 16.0 mm`, `4×` `-0.75 mm` blade flats, `8× M3` holes) |
| `1` | `cnc/svt_na_dsi_actuator_lever_6061.step` / `.dxf` | **6061-T6 Aluminum**, `6.0 mm` CNC/waterjet | `6.0 × 8.0 mm` Double-D bore, dual clevis holes (`R = 26 & 32 mm`) |

---

## 3. Bearings, Shaft Seal, O-Rings & OEM Gaskets

| Qty | Part | Exact Specification | Where Used |
| :---: | --- | --- | --- |
| `2` | Ball Bearing **`688-2RS`** | `8 × 16 × 5 mm` rubber-sealed | `-X` outer seal end & `+X` internal blind bearing pocket |
| `1` | Split/Sleeve Bushing **`SF-1 0812`** | `8 × 10 × 12 mm` PTFE/bronze | `X = 0` center split shaft support |
| `1` | Rotary Lip Seal **`8 × 16 × 5 mm` FKM/Viton TC** | Double-lip Viton w/ garter spring | `-X` actuator end behind `svt_na_dsi_seal_retainer_plate.stl` |
| `1` | **Factory Ford SVT / BBK `65 mm` Flat TB Gasket** | OEM SVT flat gasket w/ kidney IACV cutout | Seals `79 × 79 mm` flat TB face + internal `Ø12.4 mm` IACV feed |
| `1` | **Motorcraft `CG-756`** (or Fel-Pro `61066`) | 2-bolt Ford IACV gasket (`46 mm` pitch) | Top-mounted IACV pedestal (`156, 22, 65.6 mm`) |
| `1.2 m` | **`3.0–3.5 mm` Viton (FKM) O-ring cord** | `75A` durometer + thin CA / Permatex Ultra Black splice | Center split (`356.5 mm` loop) + Left & Right top service hatches |

---

## 4. Fasteners, Brass Heat-Set Inserts & FOD Retention

| Qty | Item | Specification | Where Used |
| :---: | --- | --- | --- |
| `8` | **`M3 × 6 mm` Stainless SHCS / Button Head** | `304SS` / `18-8` + **Loctite 271/272 + mechanical thread stake/peen** | Secures `4×` butterfly plates to `Ø8.0 mm` shaft |
| `8` | **`M6 × 45 mm` SHCS + washers + nyloc nuts** | Class `10.9` or `18-8` SS | `X = 0` center split flange |
| `2` | **`Ø6.0 × 20 mm` Hardened Dowel Pins** | `ISO 2338` / `DIN 6325` | `X = 0` center split alignment |
| `12` | **`M5 × 12 mm` SHCS + `12× M5` brass heat-set inserts** | `6.4 mm` pilot (`OD 7.0–7.2 mm`) | Top Service Hatch Lids (`6×` per lid) |
| `2` | **`M4 × 14 mm` SHCS + `2× M4` brass heat-set inserts** | `5.4 mm` pilot | `-X` Viton lip-seal retainer plate |
| `4` | **`M6 × 35 mm` SHCS + `4×` hardened washers + nuts** | `Ø7.0 mm` holes, `6.25 mm` rear socket relief | `79 × 79 mm` `65 mm` Throttle Body flange |
| `2` | **`M6 × 20 mm` SHCS + `2× M6` brass heat-set inserts** | `5.2 mm` pilot | Top-mounted 2-bolt Ford IACV pedestal |
| `2` | **`M6 × 16 mm` SHCS + `2× M6` brass heat-set inserts** | `7.2 mm` pilot | `-X` Universal Actuator Bracket pad |

---

## 5. Couplers, Clamps & NA Vacuum/PCV/Sensor Fittings

*(Note: Zero external IACV supply hose required — idle air feeds internally through the flat TB plate!)*

| Qty | Item | Specification | Where Used |
| :---: | --- | --- | --- |
| `4` | **Silicone Runner Couplers** | **MarraSport / Massive `2.00" ID × 2.00" L`** straight | Joins `Ø50.8 mm` spigots to OEM SVT lower manifold |
| `8` | **T-Bolt or Murray Constant-Tension Clamps** | `2.00"` (`51–59 mm` range) | `2×` per silicone coupler |
| `2` | **`1/4-18 NPT` Brass Hose Barbs** | `3/8"` (Brake Booster) & `3/8"` or `1/2"` (PCV) | Rear-top Primary Vacuum Pad (`X = +56, Y = +38 mm`) |
| `3` | **`1/8-27 NPT` Brass Hose Barbs** | `3/16"` / `1/4"` barb (FRPS, EVAP, DSI Pod/Aux MAP) | Primary Pad (`FRPS`) + Aux Pad (`X = -52, Y = +26 mm`) |
| `1` roll | **PTFE Thread Sealant Paste / Tape** | Fuel/oil-resistant (e.g., Loctite 565) | Seals all NPT fittings into tapped bosses |

---

## 6. Dual-Stage Actuation Hardware (Choose Path A or Path B)

### Path A — Reuse OEM Focus SVT IMRC Motor Box & Cable
- OEM Focus SVT IMRC actuator box + cable (removed during Stage-2 swap)
- Custom/updated `-X` cable bracket & lever clevis pin (verify dimensions via Section 7 Caliper Checklist in `README.md`)
- Uses factory ECU IMRC output pin (`~4,800–6,000 RPM` switchover; `5,000 RPM` optimal)

### Path B — Standalone Vacuum Actuator Pod + 12V 3-Port Solenoid (Recommended Modular Setup)
| Qty | Item | Specification | Notes |
| :---: | --- | --- | --- |
| `1` | **Push-Pull Vacuum Actuator Pod** | `~25–35 mm` stroke, `-5 to -15 inHg` full travel (e.g., Pierburg / Ford universal) | Bolts to `svt_na_dsi_actuator_bracket_universal.stl` on `-X` end |
| `1` | **12V 3-Port Solenoid Valve** | **MAC 35A-AAA-DDBA-1BA** (or Pierburg `7.02256.04.0`) | Switches pod between vacuum reservoir & atmospheric vent |
| `1` | **Inline Vacuum Check Valve + Mini Reservoir** | `1/4"` inline check valve + `~150–300 mL` vacuum canister | Holds vacuum at WOT so valves stay actuated cleanly |
| `1` | **External Return Spring** | Light stainless torsion/extension spring | Guarantees fail-safe return to `Long` or `Short` resting stop |
| `1` | **RPM Window Switch / ECU Trigger** | Triggered by OEM IMRC pin or aftermarket `5,000 RPM` switch | Drives `12V` solenoid ground |

---

## 7. Bench Qualification & Leak-Testing Supplies
- `4×` `2.00"` rubber/PVC test caps + `1×` `65 mm` TB block-off plate
- Hand vacuum/pressure pump with gauge (`-12 inHg` / `-12 psig` vacuum hold + `+15 psig` soap-bubble backfire proof check)
