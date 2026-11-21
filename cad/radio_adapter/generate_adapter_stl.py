#!/usr/bin/env python3
"""
generate_adapter_stl.py
Generates watertight, manifold binary STLs for:
  Vehicle: 2004 Ford Focus SVT (MK1 New Edge Dashboard)
  Radio:   JVC KW-V830BT Double-DIN

Printables Model 1216108 Baseline Adaptation:
  - Baseline Provenance:
      * Printables Model: 1216108 (Ford Focus MK1 radio frame by kstor)
      * Factory-matching MK1 Focus dash console outer interface & retention
  - Front Plane:
      * 100% flat front face (Z = 0.0) from the radio aperture to the outer perimeter (no chamfer/bevel)
      * Seamless PEI bed adhesion with crisp OEM texture across the entire visible surface
  - X-Y Profile (Printables MK1 Baseline):
      * Straight Flanks: 188.50 mm width (constant across vertical sides)
      * Height: 100.50 mm nominal / 101.50 mm peak brow arch (confirmed good fit)
      * Corner Radii: R = 10.00 mm all four corners (deep inward curve clearance for dash fillets)
      * Top brow crown: +1.00 mm upward arch matching console brow
      * Lower edge contour: +0.30 mm
      * Radio Cutout: 179.20 mm wide x 98.80 mm high (R = 2.0 mm, calibrated for JVC KW-V830BT faceplate)
  - Rear Insertion Boss (Printables MK1 Baseline):
      * 183.00 mm wide x 94.00 mm high (drops directly into Focus MK1 dash console pocket)
      * Steps down from the 188.50 x 100.50 mm flange by 2.75 mm per side and 3.25 mm top/bottom
  - Z-Axis Compound Curvature:
      * 0.80 mm horizontal Z-bow on rear seating shelf to match convex Focus dashboard:
        z_shelf(x) = -2.50 - 0.80 * (x / 94.25)^2
      * Flange is 2.50 mm thick at center, thickening to 3.30 mm at sides for a 100% gapless seal
"""

import math
import struct
import os

def generate_profile_loop_tapered(
    w_top, w_bot, height,
    r_top_x, r_top_y, r_bot,
    crown_top=0.0, crown_bot=0.0,
    k_arc=12, k_edge=12
):
    w_top2 = w_top / 2.0
    w_bot2 = w_bot / 2.0
    h2 = height / 2.0
    pts = []
    
    # 1. Top-Right Corner (Elliptical: rx = r_top_x, ry = r_top_y)
    c1_x = w_top2 - r_top_x
    c1_y = h2 - r_top_y
    for i in range(k_arc):
        a = 0.0 + (math.pi / 2.0) * (i / float(k_arc))
        pts.append((c1_x + r_top_x * math.cos(a), c1_y + r_top_y * math.sin(a)))
        
    # 2. Top Edge with upward crown
    x_start = c1_x
    x_end = -c1_x
    for i in range(k_edge):
        frac = i / float(k_edge)
        x = x_start + (x_end - x_start) * frac
        t = 1.0 - 2.0 * frac
        y = h2 + crown_top * (1.0 - t * t)
        pts.append((x, y))
        
    # 3. Top-Left Corner
    c2_x = -w_top2 + r_top_x
    c2_y = h2 - r_top_y
    for i in range(k_arc):
        a = (math.pi / 2.0) + (math.pi / 2.0) * (i / float(k_arc))
        pts.append((c2_x + r_top_x * math.cos(a), c2_y + r_top_y * math.sin(a)))
        
    # 4. Left Edge (Straight line tapering from top to bottom)
    y_start = c2_y
    y_end = -h2 + r_bot
    for i in range(k_edge):
        frac = i / float(k_edge)
        y = y_start + (y_end - y_start) * frac
        x = -(w_top2 * (1.0 - frac) + w_bot2 * frac)
        pts.append((x, y))
        
    # 5. Bottom-Left Corner
    c3_x = -w_bot2 + r_bot
    c3_y = -h2 + r_bot
    for i in range(k_arc):
        a = math.pi + (math.pi / 2.0) * (i / float(k_arc))
        pts.append((c3_x + r_bot * math.cos(a), c3_y + r_bot * math.sin(a)))
        
    # 6. Bottom Edge with contour
    x_start = c3_x
    x_end = -c3_x
    for i in range(k_edge):
        frac = i / float(k_edge)
        x = x_start + (x_end - x_start) * frac
        t = 1.0 - 2.0 * frac
        y = -h2 - crown_bot * (1.0 - t * t)
        pts.append((x, y))
        
    # 7. Bottom-Right Corner
    c4_x = w_bot2 - r_bot
    c4_y = -h2 + r_bot
    for i in range(k_arc):
        a = (3.0 * math.pi / 2.0) + (math.pi / 2.0) * (i / float(k_arc))
        pts.append((c4_x + r_bot * math.cos(a), c4_y + r_bot * math.sin(a)))
        
    # 8. Right Edge (Straight line tapering from bottom to top)
    y_start = -h2 + r_bot
    y_end = c1_y
    for i in range(k_edge):
        frac = i / float(k_edge)
        y = y_start + (y_end - y_start) * frac
        x = w_bot2 * (1.0 - frac) + w_top2 * frac
        pts.append((x, y))
        
    return pts

def generate_rect_loop(width, height, radius, k_arc=12, k_edge=12):
    w2 = width / 2.0
    h2 = height / 2.0
    r = min(radius, w2, h2)
    pts = []
    
    corners = [
        (w2 - r, h2 - r, 0.0, math.pi / 2.0),
        (-w2 + r, h2 - r, math.pi / 2.0, math.pi),
        (-w2 + r, -h2 + r, math.pi, 3.0 * math.pi / 2.0),
        (w2 - r, -h2 + r, 3.0 * math.pi / 2.0, 2.0 * math.pi)
    ]
    
    for c_idx, (cx, cy, start_a, end_a) in enumerate(corners):
        for i in range(k_arc):
            a = start_a + (end_a - start_a) * (i / float(k_arc))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        if c_idx == 0:  # Top edge
            for i in range(k_edge):
                pts.append(((w2 - r) - 2 * (w2 - r) * (i / float(k_edge)), h2))
        elif c_idx == 1:  # Left edge
            for i in range(k_edge):
                pts.append((-w2, (h2 - r) - 2 * (h2 - r) * (i / float(k_edge))))
        elif c_idx == 2:  # Bottom edge
            for i in range(k_edge):
                pts.append((-(w2 - r) + 2 * (w2 - r) * (i / float(k_edge)), -h2))
        elif c_idx == 3:  # Right edge
            for i in range(k_edge):
                pts.append((w2, -(h2 - r) + 2 * (h2 - r) * (i / float(k_edge))))
                
    return pts

def z_shelf(x, base_thick=2.50, z_bow=0.80, w2=95.10):
    frac = min(1.0, abs(x) / w2)
    return -base_thick - z_bow * (frac * frac)

def calc_normal(p1, p2, p3):
    u = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    v = (p3[0]-p1[0], p3[1]-p1[1], p3[2]-p1[2])
    nx = u[1]*v[2] - u[2]*v[1]
    ny = u[2]*v[0] - u[0]*v[2]
    nz = u[0]*v[1] - u[1]*v[0]
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 1e-12:
        return (nx/length, ny/length, nz/length)
    return (0.0, 0.0, 0.0)

def write_binary_stl(triangles, filepath, header_title=b'2004 Ford Focus SVT - JVC KW-V830BT Bezel'):
    with open(filepath, 'wb') as f:
        header = header_title.ljust(80, b'\0')
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for p1, p2, p3 in triangles:
            norm = calc_normal(p1, p2, p3)
            f.write(struct.pack('<3f', *norm))
            f.write(struct.pack('<3f', *p1))
            f.write(struct.pack('<3f', *p2))
            f.write(struct.pack('<3f', *p3))
            f.write(struct.pack('<H', 0))

def create_bezel_mesh():
    # Primary dimensions (mm)
    cutout_w = 179.20  # Shrunk in width only by 1.80 mm (zero-slop fit)
    cutout_h = 98.80   # Calibrated to JVC KW-V830BT 98.43 mm motorized faceplate
    
    # Outer Flange Geometry (Printables 1216108 Baseline)
    flange_w_top = 188.50  # Straight flanks matching Printables baseline width
    flange_w_bot = 188.50  # Constant 188.50 mm width across vertical flanks
    flange_h     = 100.50  # Nominal height (101.50 mm peak brow arch)
    flange_thick = 2.50
    z_bow        = 0.80    # 0.80 mm Z-curve matching convex dash
    
    # Corners & Crown (Printables 1216108 Baseline)
    r_top_x = 10.00    # Printables baseline R=10 corner radius (deep corner clearance)
    r_top_y = 10.00
    r_bot   = 10.00    # Printables baseline R=10 lower corner radius
    crown_top = 1.00   # Proven top brow upward arch
    crown_bot = 0.30   # Lower edge contour
    
    # Rear Insertion Boss Geometry (Printables 1216108 Baseline)
    boss_w_top = 183.00 # Exact Printables rear insert body width
    boss_w_bot = 183.00
    boss_h     = 94.00  # Exact Printables rear insert body height
    boss_r_top = 4.00
    boss_r_bot = 4.00
    
    k_arc = 12
    k_edge = 12
    
    loop_inner = generate_rect_loop(cutout_w, cutout_h, radius=2.0, k_arc=k_arc, k_edge=k_edge)
    loop_boss = generate_profile_loop_tapered(boss_w_top, boss_w_bot, boss_h, boss_r_top, boss_r_top, boss_r_bot, k_arc=k_arc, k_edge=k_edge)
    loop_flange_outer = generate_profile_loop_tapered(flange_w_top, flange_w_bot, flange_h, r_top_x, r_top_y, r_bot, crown_top, crown_bot, k_arc=k_arc, k_edge=k_edge)
    
    N = len(loop_inner)
    z_front = 0.0
    z_rear = -12.50
    w2 = flange_w_bot / 2.0
    
    triangles = []
    
    # 1. 100% Flat Front Annular Face (Z = 0.0, zero chamfer/bevel)
    for i in range(N):
        nxt = (i + 1) % N
        out_cur = (loop_flange_outer[i][0], loop_flange_outer[i][1], z_front)
        out_nxt = (loop_flange_outer[nxt][0], loop_flange_outer[nxt][1], z_front)
        in_cur = (loop_inner[i][0], loop_inner[i][1], z_front)
        in_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], z_front)
        triangles.append((out_cur, out_nxt, in_nxt))
        triangles.append((out_cur, in_nxt, in_cur))
        
    # 2. Outer Flange Straight Rim (from flat Z = 0.0 down to z_shelf(x))
    for i in range(N):
        nxt = (i + 1) % N
        zf_cur = z_shelf(loop_flange_outer[i][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        zf_nxt = z_shelf(loop_flange_outer[nxt][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        
        f_cur = (loop_flange_outer[i][0], loop_flange_outer[i][1], z_front)
        f_nxt = (loop_flange_outer[nxt][0], loop_flange_outer[nxt][1], z_front)
        s_cur = (loop_flange_outer[i][0], loop_flange_outer[i][1], zf_cur)
        s_nxt = (loop_flange_outer[nxt][0], loop_flange_outer[nxt][1], zf_nxt)
        triangles.append((f_cur, s_cur, s_nxt))
        triangles.append((f_cur, s_nxt, f_nxt))
        
    # 3. Stepped Shelf (between loop_flange_outer and loop_boss at z_shelf)
    for i in range(N):
        nxt = (i + 1) % N
        zf_cur = z_shelf(loop_flange_outer[i][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        zf_nxt = z_shelf(loop_flange_outer[nxt][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        zb_cur = z_shelf(loop_boss[i][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        zb_nxt = z_shelf(loop_boss[nxt][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        
        flg_cur = (loop_flange_outer[i][0], loop_flange_outer[i][1], zf_cur)
        flg_nxt = (loop_flange_outer[nxt][0], loop_flange_outer[nxt][1], zf_nxt)
        bss_cur = (loop_boss[i][0], loop_boss[i][1], zb_cur)
        bss_nxt = (loop_boss[nxt][0], loop_boss[nxt][1], zb_nxt)
        triangles.append((flg_cur, bss_nxt, flg_nxt))
        triangles.append((flg_cur, bss_cur, bss_nxt))
        
    # 4. Outer Boss Walls (from z_shelf down to z_rear)
    for i in range(N):
        nxt = (i + 1) % N
        zb_cur = z_shelf(loop_boss[i][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        zb_nxt = z_shelf(loop_boss[nxt][0], base_thick=flange_thick, z_bow=z_bow, w2=w2)
        
        b_cur = (loop_boss[i][0], loop_boss[i][1], zb_cur)
        b_nxt = (loop_boss[nxt][0], loop_boss[nxt][1], zb_nxt)
        r_cur = (loop_boss[i][0], loop_boss[i][1], z_rear)
        r_nxt = (loop_boss[nxt][0], loop_boss[nxt][1], z_rear)
        triangles.append((b_cur, r_cur, r_nxt))
        triangles.append((b_cur, r_nxt, b_nxt))
        
    # 5. Rear Annular Face (Z = z_rear)
    for i in range(N):
        nxt = (i + 1) % N
        bss_cur = (loop_boss[i][0], loop_boss[i][1], z_rear)
        bss_nxt = (loop_boss[nxt][0], loop_boss[nxt][1], z_rear)
        in_cur = (loop_inner[i][0], loop_inner[i][1], z_rear)
        in_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], z_rear)
        triangles.append((bss_cur, in_nxt, bss_nxt))
        triangles.append((bss_cur, in_cur, in_nxt))
        
    # 6. Inner Tunnel Wall (z_front to z_rear)
    for i in range(N):
        nxt = (i + 1) % N
        f_cur = (loop_inner[i][0], loop_inner[i][1], z_front)
        f_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], z_front)
        r_cur = (loop_inner[i][0], loop_inner[i][1], z_rear)
        r_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], z_rear)
        triangles.append((f_cur, f_nxt, r_nxt))
        triangles.append((f_cur, r_nxt, r_cur))
        
    return triangles

def create_gauge_mesh(base_thick=1.20, z_bow=0.80):
    """Generates a quick-print test gauge with flat front and 0.8 mm Z-contoured back."""
    cutout_w = 179.20
    cutout_h = 98.80
    flange_w_top = 188.50
    flange_w_bot = 188.50
    flange_h     = 100.50
    r_top_x = 10.00
    r_top_y = 10.00
    r_bot   = 10.00
    crown_top = 1.00
    crown_bot = 0.30
    
    k_arc, k_edge = 12, 12
    loop_inner = generate_rect_loop(cutout_w, cutout_h, radius=2.0, k_arc=k_arc, k_edge=k_edge)
    loop_outer = generate_profile_loop_tapered(flange_w_top, flange_w_bot, flange_h, r_top_x, r_top_y, r_bot, crown_top, crown_bot, k_arc=k_arc, k_edge=k_edge)
    
    N = len(loop_inner)
    w2 = flange_w_bot / 2.0
    triangles = []
    
    # 1. Front face (Z = 0.0, 100% flat on PEI bed)
    for i in range(N):
        nxt = (i + 1) % N
        out_cur = (loop_outer[i][0], loop_outer[i][1], 0.0)
        out_nxt = (loop_outer[nxt][0], loop_outer[nxt][1], 0.0)
        in_cur = (loop_inner[i][0], loop_inner[i][1], 0.0)
        in_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], 0.0)
        triangles.append((out_cur, out_nxt, in_nxt))
        triangles.append((out_cur, in_nxt, in_cur))
        
    # 2. Back face (Z = z_shelf(x)) -Z normal
    for i in range(N):
        nxt = (i + 1) % N
        z_out_cur = -base_thick - z_bow * ((abs(loop_outer[i][0]) / w2)**2)
        z_out_nxt = -base_thick - z_bow * ((abs(loop_outer[nxt][0]) / w2)**2)
        z_in_cur = -base_thick - z_bow * ((abs(loop_inner[i][0]) / w2)**2)
        z_in_nxt = -base_thick - z_bow * ((abs(loop_inner[nxt][0]) / w2)**2)
        
        out_cur = (loop_outer[i][0], loop_outer[i][1], z_out_cur)
        out_nxt = (loop_outer[nxt][0], loop_outer[nxt][1], z_out_nxt)
        in_cur = (loop_inner[i][0], loop_inner[i][1], z_in_cur)
        in_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], z_in_nxt)
        triangles.append((out_cur, in_nxt, out_nxt))
        triangles.append((out_cur, in_cur, in_nxt))
        
    # 3. Outer rim (Z = 0 down to z_shelf(x)) outward normal
    for i in range(N):
        nxt = (i + 1) % N
        z_out_cur = -base_thick - z_bow * ((abs(loop_outer[i][0]) / w2)**2)
        z_out_nxt = -base_thick - z_bow * ((abs(loop_outer[nxt][0]) / w2)**2)
        
        f_cur = (loop_outer[i][0], loop_outer[i][1], 0.0)
        f_nxt = (loop_outer[nxt][0], loop_outer[nxt][1], 0.0)
        s_cur = (loop_outer[i][0], loop_outer[i][1], z_out_cur)
        s_nxt = (loop_outer[nxt][0], loop_outer[nxt][1], z_out_nxt)
        triangles.append((f_cur, s_cur, s_nxt))
        triangles.append((f_cur, s_nxt, f_nxt))
        
    # 4. Inner rim (Z = 0 down to z_shelf(x)) inward normal
    for i in range(N):
        nxt = (i + 1) % N
        z_in_cur = -base_thick - z_bow * ((abs(loop_inner[i][0]) / w2)**2)
        z_in_nxt = -base_thick - z_bow * ((abs(loop_inner[nxt][0]) / w2)**2)
        
        f_cur = (loop_inner[i][0], loop_inner[i][1], 0.0)
        f_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], 0.0)
        r_cur = (loop_inner[i][0], loop_inner[i][1], z_in_cur)
        r_nxt = (loop_inner[nxt][0], loop_inner[nxt][1], z_in_nxt)
        triangles.append((f_cur, f_nxt, r_nxt))
        triangles.append((f_cur, r_nxt, r_cur))
        
    return triangles

if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_bezel = os.path.join(out_dir, "focus_svt_jvc_kw_v830bt_bezel.stl")
    out_gauge_parent = os.path.join(out_dir, "focus_svt_jvc_profile_gauge.stl")
    out_gauge_codex = os.path.join(out_dir, "codex_bezel_concept", "focus_svt_jvc_profile_gauge.stl")
    
    # 1. Generate Production Bezel STL (Flat Front Face, Printables Baseline)
    triangles_bezel = create_bezel_mesh()
    write_binary_stl(triangles_bezel, out_bezel, b'2004 Focus SVT - JVC KW-V830BT Bezel (Printables 1216108 Baseline)')
    print(f"Generated Calibrated Bezel STL ({len(triangles_bezel)} triangles) at: {out_bezel}")
    
    # 2. Generate Z-Bow Test Gauge STL
    triangles_gauge = create_gauge_mesh()
    write_binary_stl(triangles_gauge, out_gauge_parent, b'2004 Focus SVT - JVC Test Gauge (Printables 1216108 Baseline)')
    print(f"Generated Calibrated Gauge STL ({len(triangles_gauge)} triangles) at: {out_gauge_parent}")
    
    if os.path.exists(os.path.dirname(out_gauge_codex)):
        write_binary_stl(triangles_gauge, out_gauge_codex, b'2004 Focus SVT - JVC Test Gauge (Printables 1216108 Baseline)')
        print(f"Updated Codex Gauge STL at: {out_gauge_codex}")
