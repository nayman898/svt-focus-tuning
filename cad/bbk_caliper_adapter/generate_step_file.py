#!/usr/bin/env python3
"""
generate_step_file.py
Generates the redesigned G1-tangent ISO 10303-21 STEP (.step) and binary STL (.stl)
models and 1:1 CNC DXF (.dxf) for the Focus SVT to Mustang BBK Caliper Adapter Bracket:
  - Material: 1018 Cold-Rolled Steel, 3/8" (9.525 mm) thickness
  - Outer Contour: 8-segment G1-tangent analytic profile (zero sharp re-entrant corners)
      * Mustang bosses: Ø37.00 mm (R = 18.50 mm) at (±75.10, 29.70) -> min ligament 11.97 mm
      * SVT bosses:     Ø35.00 mm (R = 17.50 mm) at (±45.50, 15.00) -> min ligament 11.00 mm
      * Full-depth smooth upper bridge (Y = 46.50 mm at X = 0)
      * Smooth tangent lower hub-relief arch (Y = 8.00 mm at X = 0)
  - Holes: All 4 holes Ø13.00 mm (R = 6.50 mm) through-clearance for M12x1.75 Class 10.9
    bolts (SVT inner joint through-bolted with Class 10 nut + HV300 Ø24 mm hardened washer).
"""

from pathlib import Path
import math
import trimesh
from build123d import (
    BuildPart, BuildSketch, BuildLine, Circle, Line, ThreePointArc,
    make_face, Mode, Locations, extrude, export_step, export_stl
)

CAD_DIR = Path(__file__).resolve().parent


def compute_g1_contour_params(
    xm=75.10, ym=29.70, rm=18.50,
    xs=45.50, ys=15.00, rs=17.50,
    y_arch_peak=8.00,
    y_top_mid=46.50
):
    dx = xm - xs
    dy = ym - ys
    L = math.hypot(dx, dy)
    theta_c = math.atan2(dy, dx)
    alpha = math.asin((rm - rs) / L)
    # Exact external tangent outward normal: n . (C_m - C_s) = -(rm - rs) => theta_n = theta_c - pi/2 - alpha
    theta_n = theta_c - 0.5 * math.pi - alpha
    p_svt_bot_r = (xs + rs * math.cos(theta_n), ys + rs * math.sin(theta_n))
    p_mus_bot_r = (xm + rm * math.cos(theta_n), ym + rm * math.sin(theta_n))

    dy_arch = ys - y_arch_peak
    r_arch = (xs**2 + dy_arch**2 - rs**2) / (2.0 * (rs - dy_arch))
    yc_arch = y_arch_peak - r_arch
    dist_arch = r_arch + rs
    p_svt_arch_r = (
        xs * r_arch / dist_arch,
        yc_arch + (ys - yc_arch) * r_arch / dist_arch
    )

    dy_top = y_top_mid - ym
    r_top = (xm**2 + dy_top**2 - rm**2) / (2.0 * (rm - dy_top))
    yc_top = y_top_mid + r_top
    dist_top = r_top + rm
    p_mus_top_r = (
        xm * r_top / dist_top,
        yc_top + (ym - yc_top) * r_top / dist_top
    )

    return {
        "xm": xm, "ym": ym, "rm": rm,
        "xs": xs, "ys": ys, "rs": rs,
        "y_arch_peak": y_arch_peak, "r_arch": r_arch, "yc_arch": yc_arch,
        "y_top_mid": y_top_mid, "r_top": r_top, "yc_top": yc_top,
        "p_svt_bot_r": p_svt_bot_r,
        "p_mus_bot_r": p_mus_bot_r,
        "p_svt_arch_r": p_svt_arch_r,
        "p_mus_top_r": p_mus_top_r,
    }


def build_g1_bracket_part(thickness=9.525, r_mustang_hole=6.50, r_svt_hole=6.50, **kwargs):
    c = compute_g1_contour_params(**kwargs)
    xm, ym, rm = c["xm"], c["ym"], c["rm"]
    xs, ys, rs = c["xs"], c["ys"], c["rs"]

    p_arch_mid = (0.0, c["y_arch_peak"])
    p_svt_arch_r = c["p_svt_arch_r"]
    p_svt_bot_r = c["p_svt_bot_r"]
    p_mus_bot_r = c["p_mus_bot_r"]
    p_mus_outer_r = (xm + rm, ym)
    p_mus_top_r = c["p_mus_top_r"]
    p_top_mid = (0.0, c["y_top_mid"])

    ang_svt_1 = math.atan2(p_svt_arch_r[1] - ys, p_svt_arch_r[0] - xs)
    ang_svt_2 = math.atan2(p_svt_bot_r[1] - ys, p_svt_bot_r[0] - xs)
    ang_svt_mid = 0.5 * (ang_svt_1 + ang_svt_2)
    p_svt_mid_r = (xs + rs * math.cos(ang_svt_mid), ys + rs * math.sin(ang_svt_mid))

    p_svt_arch_l = (-p_svt_arch_r[0], p_svt_arch_r[1])
    p_svt_mid_l = (-p_svt_mid_r[0], p_svt_mid_r[1])
    p_svt_bot_l = (-p_svt_bot_r[0], p_svt_bot_r[1])
    p_mus_bot_l = (-p_mus_bot_r[0], p_mus_bot_r[1])
    p_mus_outer_l = (-p_mus_outer_r[0], p_mus_outer_r[1])
    p_mus_top_l = (-p_mus_top_r[0], p_mus_top_r[1])

    with BuildPart() as part:
        with BuildSketch():
            with BuildLine():
                ThreePointArc(p_svt_arch_l, p_arch_mid, p_svt_arch_r)
                ThreePointArc(p_svt_arch_r, p_svt_mid_r, p_svt_bot_r)
                Line(p_svt_bot_r, p_mus_bot_r)
                ThreePointArc(p_mus_bot_r, p_mus_outer_r, p_mus_top_r)
                ThreePointArc(p_mus_top_r, p_top_mid, p_mus_top_l)
                ThreePointArc(p_mus_top_l, p_mus_outer_l, p_mus_bot_l)
                Line(p_mus_bot_l, p_svt_bot_l)
                ThreePointArc(p_svt_bot_l, p_svt_mid_l, p_svt_arch_l)
            make_face()
            with Locations([(-xm, ym), (xm, ym)]):
                Circle(radius=r_mustang_hole, mode=Mode.SUBTRACT)
            with Locations([(-xs, ys), (xs, ys)]):
                Circle(radius=r_svt_hole, mode=Mode.SUBTRACT)
        extrude(amount=thickness)

    return part.part, c


def export_g1_dxf(dxf_path, c, r_mustang_hole=6.50, r_svt_hole=6.50):
    """Writes a true AutoCAD R12 DXF with analytical ARC, LINE, CIRCLE, and POINT entities."""
    xm, ym, rm = c["xm"], c["ym"], c["rm"]
    xs, ys, rs = c["xs"], c["ys"], c["rs"]

    p_svt_arch_r = c["p_svt_arch_r"]
    p_svt_bot_r = c["p_svt_bot_r"]
    p_mus_bot_r = c["p_mus_bot_r"]
    p_mus_top_r = c["p_mus_top_r"]

    p_svt_arch_l = (-p_svt_arch_r[0], p_svt_arch_r[1])
    p_svt_bot_l = (-p_svt_bot_r[0], p_svt_bot_r[1])
    p_mus_bot_l = (-p_mus_bot_r[0], p_mus_bot_r[1])
    p_mus_top_l = (-p_mus_top_r[0], p_mus_top_r[1])

    def deg(cx, cy, pt):
        a = math.degrees(math.atan2(pt[1] - cy, pt[0] - cx))
        return a % 360.0

    # DXF ARC is always counter-clockwise from start_angle (50) to end_angle (51)
    arcs = [
        # 1. Center bottom arch: center (0, yc_arch), radius r_arch, CCW from p_svt_arch_r to p_svt_arch_l
        (0.0, c["yc_arch"], c["r_arch"], deg(0.0, c["yc_arch"], p_svt_arch_r), deg(0.0, c["yc_arch"], p_svt_arch_l)),
        # 2. Right SVT boss arc: center (xs, ys), radius rs, CCW from p_svt_arch_r to p_svt_bot_r
        (xs, ys, rs, deg(xs, ys, p_svt_arch_r), deg(xs, ys, p_svt_bot_r)),
        # 3. Right Mustang boss arc: center (xm, ym), radius rm, CCW from p_mus_bot_r to p_mus_top_r
        (xm, ym, rm, deg(xm, ym, p_mus_bot_r), deg(xm, ym, p_mus_top_r)),
        # 4. Upper bridge arch: center (0, yc_top), radius r_top, CCW from p_mus_top_l to p_mus_top_r
        (0.0, c["yc_top"], c["r_top"], deg(0.0, c["yc_top"], p_mus_top_l), deg(0.0, c["yc_top"], p_mus_top_r)),
        # 5. Left Mustang boss arc: center (-xm, ym), radius rm, CCW from p_mus_top_l to p_mus_bot_l
        (-xm, ym, rm, deg(-xm, ym, p_mus_top_l), deg(-xm, ym, p_mus_bot_l)),
        # 6. Left SVT boss arc: center (-xs, ys), radius rs, CCW from p_svt_bot_l to p_svt_arch_l
        (-xs, ys, rs, deg(-xs, ys, p_svt_bot_l), deg(-xs, ys, p_svt_arch_l)),
    ]
    lines = [
        (p_svt_bot_r, p_mus_bot_r),
        (p_mus_bot_l, p_svt_bot_l),
    ]

    with open(dxf_path, "w") as f:
        f.write("0\nSECTION\n2\nENTITIES\n")
        for cx, cy, r, a_start, a_end in arcs:
            f.write(
                f"0\nARC\n8\nBRACKET_OUTLINE\n"
                f"10\n{cx:.6f}\n20\n{cy:.6f}\n30\n0.0\n"
                f"40\n{r:.6f}\n50\n{a_start:.6f}\n51\n{a_end:.6f}\n"
            )
        for p1, p2 in lines:
            f.write(
                f"0\nLINE\n8\nBRACKET_OUTLINE\n"
                f"10\n{p1[0]:.6f}\n20\n{p1[1]:.6f}\n30\n0.0\n"
                f"11\n{p2[0]:.6f}\n21\n{p2[1]:.6f}\n31\n0.0\n"
            )
        hole_specs = [
            (-xm, ym, r_mustang_hole, "MUSTANG_CLEARANCE_13MM"),
            ( xm, ym, r_mustang_hole, "MUSTANG_CLEARANCE_13MM"),
            (-xs, ys, r_svt_hole,     "SVT_CLEARANCE_13MM"),
            ( xs, ys, r_svt_hole,     "SVT_CLEARANCE_13MM"),
        ]
        for hcx, hcy, hr, layer in hole_specs:
            f.write(f"0\nCIRCLE\n8\n{layer}\n10\n{hcx:.4f}\n20\n{hcy:.4f}\n30\n0.0\n40\n{hr:.4f}\n")
            f.write(f"0\nPOINT\n8\nHOLE_CENTERS\n10\n{hcx:.4f}\n20\n{hcy:.4f}\n30\n0.0\n")
        f.write("0\nENDSEC\n0\nEOF\n")


def main():
    # 1. Primary 3/8" (9.525 mm) 1018 Steel Bracket (All 4 holes Ø13.00 mm clearance)
    part_3_8, c = build_g1_bracket_part(thickness=9.525, r_mustang_hole=6.50, r_svt_hole=6.50)
    step_path = CAD_DIR / "focus_svt_mustang_bbk_steel_bracket.step"
    stl_path = CAD_DIR / "focus_svt_mustang_bbk_steel_bracket.stl"
    stl_3_8_path = CAD_DIR / "focus_svt_mustang_bbk_steel_bracket_3_8in.stl"
    dxf_path = CAD_DIR / "focus_svt_mustang_bbk_steel_bracket.dxf"

    export_step(part_3_8, str(step_path))
    export_stl(part_3_8, str(stl_path), tolerance=0.001, angular_tolerance=0.01)
    export_stl(part_3_8, str(stl_3_8_path), tolerance=0.001, angular_tolerance=0.01)
    export_g1_dxf(dxf_path, c, r_mustang_hole=6.50, r_svt_hole=6.50)

    # 2. Rapid 4.00 mm Test Gauge STL (All 4 holes Ø13.00 mm clearance)
    part_gauge, _ = build_g1_bracket_part(thickness=4.00, r_mustang_hole=6.50, r_svt_hole=6.50)
    gauge_stl_path = CAD_DIR / "focus_svt_mustang_bbk_steel_gauge.stl"
    export_stl(part_gauge, str(gauge_stl_path), tolerance=0.001, angular_tolerance=0.01)

    # 3. 4.00 mm Spacer STEP (preserved)
    with BuildPart() as p_sp:
        with BuildSketch():
            Circle(radius=13.00)
            Circle(radius=6.50, mode=Mode.SUBTRACT)
        extrude(amount=4.00)
    spacer_step_path = CAD_DIR / "focus_svt_mustang_bbk_4mm_spacer.step"
    export_step(p_sp.part, str(spacer_step_path))

    # Verify STL watertightness & metrics
    m = trimesh.load_mesh(stl_path)
    vol_cm3 = float(m.volume) / 1000.0
    mass_g = vol_cm3 * 7.87
    print(f"[+] Exported Primary 3/8\" G1-Tangent STEP : {step_path}")
    print(f"[+] Exported Primary 3/8\" G1-Tangent STL  : {stl_path}")
    print(f"    - Dimensions (mm): {m.extents.round(3).tolist()}")
    print(f"    - Watertight     : {m.is_watertight} (Winding consistent: {m.is_winding_consistent})")
    print(f"    - Volume / Mass  : {vol_cm3:.2f} cm^3 | {mass_g:.1f} g ({mass_g*0.00220462:.2f} lbs)")
    print(f"[+] Exported 1:1 Analytical Arc/Circle DXF: {dxf_path}")
    print(f"[+] Exported 4.00 mm Test Gauge STL       : {gauge_stl_path}")


if __name__ == "__main__":
    main()
