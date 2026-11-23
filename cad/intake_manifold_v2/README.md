# 2004 Ford Focus SVT Turbo — Stage-2 V2 Intake Manifold (`iacv_flat_face` + WOT/IACV Optimized)

Custom 2-piece 3D-printed composite intake manifold upper (`PPA-CF` / `PAHT-CF`) for the 2.0L Zetec-E Turbo (`Pulsar G25-550`, `18 psig` boost), integrating Codex's `iacv_flat_face` throttle-body and IACV architecture with WOT 3D plenum/runner flow optimization, an enlarged `Ø12.4 mm` internal IACV feed duct, and verified zero-leak/zero-ridge internal geometry.

## Key Engineering Highlights

- **Throttle Body & Flat-Face IACV Architecture (BBK / OEM SVT `65 mm`):**
  - `79 × 79 mm` square bolt pattern (`72 mm` inner edge-to-edge + `Ø7.0 mm` mounting holes) with `5.0 mm` firewall / `7.0 mm` ground bore eccentricity (`bore_from_bolt_grid_uv_mm = [5.0, -7.0]`).
  - Flat sealing face (`oring_groove.enabled = false`) with traced kidney IACV bypass opening (`1.8 mm` inset, `1.596 mm` seal land at `0.1–0.25 mm` depth), `+8 mm` extended neck, and `6.25 mm` rear socket relief (`0.0 mm³` interference, `100%` washer support on all 4 corners).
  - `cable_bracket_boss` is currently disabled (`enabled = false`) pending physical cable-bracket placement verification.
- **Enlarged `Ø12.4 mm` Internal IACV Feed Duct, Swept Elbow & Flared Discharge:**
  - Enlarged from `Ø11.1 mm` to `Ø12.4 mm` with a direct 1-midpoint route (`L = 83.24 mm`, `R_min = 20.40 mm`, `1` connected duct component, `0.0 mm³` exterior breakthrough, `0.0 mm³` solid obstruction).
  - Replaced the flat-bottom supply-pocket dead-end with a rounded-bowl swept elbow (`z = 54.6 -> 48.4 mm`, tangent to the `Ø12.4 mm` feed duct), raising the `468`-ray IACV floor to `6.386 mm` center / `6.309 mm` min (up from `5.986 / 5.438 mm`).
  - Added a continuous oblique bellmouth flare (`Z = 45.0 -> 38.0 mm`, `r = 6.5 -> 8.8 mm`) on the downstream `Ø13.0 mm` plenum discharge port.
  - Minimum clearance across all active structural checks is `4.800 mm` (`iacv_mounting_face = 4.800 mm`, `main_air_to_feed = 4.881 mm`, `iacv_bolts_and_outlet = 5.410 mm`, `socket_clearance = 6.278 mm`, `flange_holes = 9.025 mm`).
  - Warm-idle `0.85 lb/min` (`6.43 g/s`, `Re = 34,011`) pressure drop reduced to `2.972 / 7.022 / 14.190 kPa` (`K_minor = 2 / 5 / 10`, vs `5.1 / 11.6 / 23.8 kPa` on `Ø11.1 mm`), and `1.39 lb/min` (`10.51 g/s`, `Re = 55,618`) stress flow remains sustainable across all three loss screens (`8.147 / 20.111 / 45.486 kPa`).
- **WOT 3D Plenum & Runner Balance:**
  - Flush conformal quarter-circle bellmouths (`0.0%` solid shadow blockage), `taper_cyl1_area_ratio = 0.50`, internal `rear_wall_flow_guide` (`blend_x = [48.0, 161.0] mm`, `depth = 24.0 mm`), and progressive per-cylinder entry sweep (`44 / 45 / 48 / 48 mm`, `Z = 12 / 10 / 8 / 8 mm`, axial angles `0° / 2° / 5° / 11.5°`).
  - **3D FVM (`dx = 4.0 mm`, `46,038` cells, `209` iters):** `ΔP = 1.6333 kPa` (`0.2369 psi`), cylinder maldistribution spread = `3.952%` (down from `6.79%` in Codex `iacv_flat_face/refined`), shares `[25.423, 24.991, 25.150, 24.435]%`, `0.0%` mass conservation error, `0.0 cm³` STL wall overlap.
  - **1D Network (`7,000 RPM / 18 psig`):** `VE spread = 0.90%` (`720°CA = 0.73%`), `ΔP_total = 2.179 kPa` (`0.316 psi`), `C_d = 0.9056`, plenum volume `1.859 L`.
- **Internal Geometry Fixes:**
  - **Zero TB-to-Plenum Seam Ridge:** Ended `rear_wall_flow_guide` blend at `X = 161.0 mm` and tapered `neck_in_rings[0]` at `X = 162.0 mm`; verified smooth `+Y` inner wall across `X = 154–172 mm` (`46.60–47.71 mm`).
  - **Zero Cyl 4 Crescent Gouge:** Restored `neg_u_boost = 2.4` with `entry_wall = 7.5 mm` and Cyl 4 `48.0 mm / Z = 8.0 mm / 11.5°`; permanent CAD assertion confirms `0.0 mm³` runner-bore leak on all 4 cylinders and `7.165 mm` pressure-side root wall (`3.237 mm` min all-ray span on Cyl 4).

## 3-Grid Convergence Index (GCI) & Provenance

Provenance `case_id`: `stage2v2_726bc939_13bb121c` (`stl/airflow_verification.json`).

| Grid `dx` | Fluid Cells | Outer Iters | `ΔP` (kPa) | 3D Spread (%) | Shares (Cyl 1 / 2 / 3 / 4 %) | Status |
|---|---|---|---|---|---|---|
| `4.0 mm` | `46,038` | `209` | `1.6333` | `3.952` | `25.423 / 24.991 / 25.150 / 24.435` | `CONVERGED` |
| `3.0 mm` | `108,990` | `207` | `1.4745` | `4.368` | `25.720 / 24.784 / 24.868 / 24.628` | `CONVERGED` |
| `2.5 mm` | `188,683` | `375` | `1.3812` | `5.462` | `25.611 / 25.198 / 24.946 / 24.245` | `CONVERGED` |

- Richardson extrapolated `ΔP`: `0.4037 ± 1.2219 kPa` (`p = 0.5`, monotonic).
- Richardson extrapolated 3D spread: `7.3566 ± 2.3682%` (`p = 2.5`, monotonic).
- `2.0 mm` aligned (`367,514` cells) and half-shifted (`368,225` cells) boundary checks pass with symmetric `[362]` / `[360]` outlet face counts.

## Generated STLs (Centauri Carbon 2 `256 mm³` Bed Fit)

All 10 STLs in `stl/` are watertight single-body volumes (`body_count = 1`):

- `svt_intake_manifold_v2_1piece_full.stl` (`449.71 × 200.5 × 143.0 mm`, `1413.03 cm³`, reference only)
- `svt_intake_manifold_v2_split_left_cyl1_2.stl` (`195.98 × 216.75 × 159.59 mm`, `615.71 cm³`, CC2=True)
- `svt_intake_manifold_v2_split_right_cyl3_4_tb.stl` (`253.73 × 216.75 × 159.59 mm`, `1011.18 cm³`, CC2=True)
- `svt_intake_manifold_v2_split_left_print_oriented.stl` (`159.59 × 216.75 × 195.98 mm`, `615.71 cm³`, CC2=True)
- `svt_intake_manifold_v2_split_right_print_oriented.stl` (`159.59 × 216.75 × 253.73 mm`, `1011.18 cm³`, CC2=True)
- `svt_v2_runner_boot_fit_gauge.stl` (`56.8 × 56.8 × 44.0 mm`, `29.29 cm³`, CC2=True)
- `svt_v2_tb_flange_fit_gauge.stl` (`96.0 × 100.0 × 4.0 mm`, `24.30 cm³`, CC2=True)
- `svt_v2_iacv_flange_fit_gauge.stl` (`48.0 × 68.0 × 4.0 mm`, `11.52 cm³`, CC2=True)
- `svt_v2_alignment_dowel_pins.stl` (`20.0 × 41.8 × 5.5 mm`, `2.05 cm³`, CC2=True)
- `svt_v2_flat_face_iacv_fit_coupon.stl` (`96.0 × 100.0 × 4.0 mm`, `23.31 cm³`, CC2=True)

## Manufacturing & Physical Qualification Requirements

CFD and CAD verification alone do **not** qualify a 3D-printed composite manifold for `18–25 psig` underhood boost service. Before engine installation:

1. **Print & Post-Cure:** Print the split halves in `PPA-CF` or `PAHT-CF` (`100%` wall/perimeter density, dry filament), then oven-anneal per filament manufacturer schedule to maximize HDT and interlaminar bond strength.
2. **Epoxy Seal & Bond:** Bond the split joint with alignment dowels and coat internal/external pressure boundaries with high-temp automotive epoxy (e.g., `Loctite E-120HP` / `3M DP420` or equivalent) to eliminate micro-porosity.
3. **Physical Fit-Coupon Check:** Print `svt_v2_flat_face_iacv_fit_coupon.stl` and verify BBK/OEM `65 mm` TB bolt pattern, bore alignment, IACV kidney seal land, and rear `M6` socket clearance before committing full halves.
4. **Bench Pressure Test:** Cap runner spigots and TB/IACV ports and soap-bubble / pressure-decay test the assembled manifold at `20–25 psi` (`1.38–1.72 bar`) for at least `15–30 minutes` with zero leaks or joint creep.
