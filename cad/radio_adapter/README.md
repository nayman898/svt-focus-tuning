# 2004 Ford Focus SVT · JVC KW-V830BT Radio Adapter

Custom 3D-printable Double-DIN mounting solution engineered specifically for installing the **JVC KW-V830BT** into the **2004 Ford Focus SVT** center dashboard.

---

## 1. Problem Solved: Metra 95-5806 Pinching

Standard aftermarket Focus installation kits (such as the Metra 95-5806) were molded around legacy domestic DIN standard aperture sizes measuring **173.0 mm × 98.0 mm** (6⅞″ × 3⅞″).

The modern 6.8″ touchscreen faceplate on the **JVC KW-V830BT** measures **179.39 mm wide × 98.43 mm high**.
Because the JVC nose is **6.39 mm wider** than the Metra inner frame, the Metra adapter heavily pinches the sides of the headunit, preventing a clean flush fit and scratching the bezel.

---

## 2. Engineering Specifications

| Parameter | Focus Dash Opening | JVC KW-V830BT Face | Custom Adapter | Clearance / Tolerance |
| :--- | :---: | :---: | :---: | :---: |
| **Width** | 190.50 mm (7.50″) | 179.39 mm | **181.00 mm** | +0.80 mm gap per side (zero binding) |
| **Height** | 101.60 mm (4.00″) | 98.43 mm | **100.00 mm** | +0.78 mm gap top & bottom |
| **Front Flange** | — | — | **196.50 × 107.60 mm** | 3.0 mm overlap lip past dash opening |
| **Alignment Boss** | 190.50 × 101.60 mm | — | **189.50 × 100.80 mm** | 9.5 mm depth insertion into dash cut |
| **Side Arms** | — | 178.0 mm chassis | **75.0 mm depth, 3.6 mm wall** | Dual slotted ISO M5 depth slots (±8mm) |

---

## 3. Files in this Directory

- [`focus_svt_jvc_kw_v830bt_unibody_cage.stl`](focus_svt_jvc_kw_v830bt_unibody_cage.stl): Ready-to-print binary STL of the Full Unibody Cage. Replaces the Metra kit entirely.
- [`focus_svt_jvc_kw_v830bt_bezel.stl`](focus_svt_jvc_kw_v830bt_bezel.stl): Ready-to-print binary STL of the standalone Front Trim Bezel (for use if retaining separate side brackets).
- [`focus_svt_jvc_kw_v830bt_adapter.scad`](focus_svt_jvc_kw_v830bt_adapter.scad): Fully parametric OpenSCAD script supporting Mode 1 (Trim Bezel) and Mode 2 (Unibody Cage).
- [`generate_unibody_cage_stl.py`](generate_unibody_cage_stl.py): Python generator for the unibody cage STL.
- [`generate_adapter_stl.py`](generate_adapter_stl.py): Python generator for the trim bezel STL.

---

## 4. 3D Print Recommendations

1. **Orientation**: Place the front face of the bezel flat down on a textured PEI build plate. This produces a factory-matching matte finish on the visible front surface and eliminates the need for supports.
2. **Material**:
   - **Recommended**: **PETG** (heat deflection 75°C–80°C, zero warping, high UV resistance).
   - **Best**: **ABS / ASA** (heat deflection 95°C–105°C, OEM automotive spec).
   - *Avoid Standard PLA*: Dashboards easily reach 65°C–75°C in summer sun, which will cause standard PLA to soften and sag.
3. **Slicer Settings**:
   - Layer Height: 0.20 mm
   - Wall Perimeters: **4 walls** (makes side mounting arms practically solid)
   - Top / Bottom Layers: 5 layers
   - Infill: 25% Gyroid or Grid

