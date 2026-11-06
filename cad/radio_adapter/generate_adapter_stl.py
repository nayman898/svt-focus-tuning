#!/usr/bin/env python3
"""
generate_adapter_stl.py
Generates a watertight, manifold binary STL radio adapter bezel for:
  Vehicle: 2004 Ford Focus SVT
  Radio:   JVC KW-V830BT Double-DIN
"""

import math
import struct
import os

def rounded_rect_points(width, height, radius, num_arc_pts=8):
    """
    Returns an ordered list of (x, y) coordinates for a rounded rectangle
    centered at (0, 0) with a given corner radius.
    """
    w2 = width / 2.0
    h2 = height / 2.0
    r = min(radius, w2, h2)
    
    pts = []
    # 4 corners:
    # 1. Top-Right: center at (w2 - r, h2 - r), angles 0 to pi/2
    # 2. Top-Left: center at (-w2 + r, h2 - r), angles pi/2 to pi
    # 3. Bottom-Left: center at (-w2 + r, -h2 + r), angles pi to 3pi/2
    # 4. Bottom-Right: center at (w2 - r, -h2 + r), angles 3pi/2 to 2pi
    
    corners = [
        (w2 - r, h2 - r, 0.0, math.pi / 2.0),
        (-w2 + r, h2 - r, math.pi / 2.0, math.pi),
        (-w2 + r, -h2 + r, math.pi, 3.0 * math.pi / 2.0),
        (w2 - r, -h2 + r, 3.0 * math.pi / 2.0, 2.0 * math.pi)
    ]
    
    for cx, cy, start_a, end_a in corners:
        for i in range(num_arc_pts):
            theta = start_a + (end_a - start_a) * (i / float(num_arc_pts))
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            pts.append((x, y))
            
    return pts

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

def write_binary_stl(triangles, filepath):
    with open(filepath, 'wb') as f:
        # 80-byte header
        header = b'2004 Ford Focus SVT - JVC KW-V830BT Radio Adapter Bezel'.ljust(80, b'\0')
        f.write(header)
        # uint32 count
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
    jvc_w = 179.39
    jvc_h = 98.43
    dash_w = 190.50
    dash_h = 101.60
    
    # Tolerances
    cutout_w = 181.00  # +0.8 mm clearance per side
    cutout_h = 100.00  # +0.78 mm clearance top/bottom
    
    flange_overlap = 3.0
    flange_w = dash_w + (2.0 * flange_overlap)  # 196.50 mm
    flange_h = dash_h + (2.0 * flange_overlap)  # 107.60 mm
    flange_thick = 2.50
    
    boss_w = dash_w - 1.00  # 189.50 mm (-0.5 mm per side insertion clearance)
    boss_h = dash_h - 0.80  # 100.80 mm (-0.4 mm top/bottom insertion clearance)
    boss_depth = 9.50
    
    num_pts = 10  # per corner -> 40 points per loop
    
    loop_inner = rounded_rect_points(cutout_w, cutout_h, radius=2.0, num_arc_pts=num_pts)
    loop_flange = rounded_rect_points(flange_w, flange_h, radius=5.0, num_arc_pts=num_pts)
    loop_boss = rounded_rect_points(boss_w, boss_h, radius=3.5, num_arc_pts=num_pts)
    
    N = len(loop_inner)
    
    # Levels along Z:
    # Z = 0: Front face of flange
    # Z = -flange_thick (-2.5): Step shelf where flange meets boss
    # Z = -(flange_thick + boss_depth) (-12.0): Rear edge of boss
    z_front = 0.0
    z_step = -flange_thick
    z_rear = -(flange_thick + boss_depth)
    
    triangles = []
    
    # 1. Front Annular Face (Z = z_front)
    # Normal points +Z
    for i in range(N):
        next_i = (i + 1) % N
        out_cur = (loop_flange[i][0], loop_flange[i][1], z_front)
        out_nxt = (loop_flange[next_i][0], loop_flange[next_i][1], z_front)
        in_cur = (loop_inner[i][0], loop_inner[i][1], z_front)
        in_nxt = (loop_inner[next_i][0], loop_inner[next_i][1], z_front)
        
        # CCW for +Z normal: out_cur -> out_nxt -> in_nxt, out_cur -> in_nxt -> in_cur
        triangles.append((out_cur, out_nxt, in_nxt))
        triangles.append((out_cur, in_nxt, in_cur))
        
    # 2. Outer Flange Rim (Z from z_front to z_step)
    # Normal points outward
    for i in range(N):
        next_i = (i + 1) % N
        f_cur = (loop_flange[i][0], loop_flange[i][1], z_front)
        f_nxt = (loop_flange[next_i][0], loop_flange[next_i][1], z_front)
        s_cur = (loop_flange[i][0], loop_flange[i][1], z_step)
        s_nxt = (loop_flange[next_i][0], loop_flange[next_i][1], z_step)
        
        triangles.append((f_cur, s_cur, s_nxt))
        triangles.append((f_cur, s_nxt, f_nxt))
        
    # 3. Stepped Shelf (Z = z_step, between loop_flange and loop_boss)
    # Normal points -Z (rearward)
    for i in range(N):
        next_i = (i + 1) % N
        flg_cur = (loop_flange[i][0], loop_flange[i][1], z_step)
        flg_nxt = (loop_flange[next_i][0], loop_flange[next_i][1], z_step)
        bss_cur = (loop_boss[i][0], loop_boss[i][1], z_step)
        bss_nxt = (loop_boss[next_i][0], loop_boss[next_i][1], z_step)
        
        # CW from front (CCW from -Z):
        triangles.append((flg_cur, bss_nxt, flg_nxt))
        triangles.append((flg_cur, bss_cur, bss_nxt))
        
    # 4. Outer Boss Walls (Z from z_step to z_rear)
    # Normal points outward
    for i in range(N):
        next_i = (i + 1) % N
        b_cur = (loop_boss[i][0], loop_boss[i][1], z_step)
        b_nxt = (loop_boss[next_i][0], loop_boss[next_i][1], z_step)
        r_cur = (loop_boss[i][0], loop_boss[i][1], z_rear)
        r_nxt = (loop_boss[next_i][0], loop_boss[next_i][1], z_rear)
        
        triangles.append((b_cur, r_cur, r_nxt))
        triangles.append((b_cur, r_nxt, b_nxt))
        
    # 5. Rear Annular Face (Z = z_rear, between loop_boss and loop_inner)
    # Normal points -Z
    for i in range(N):
        next_i = (i + 1) % N
        bss_cur = (loop_boss[i][0], loop_boss[i][1], z_rear)
        bss_nxt = (loop_boss[next_i][0], loop_boss[next_i][1], z_rear)
        in_cur = (loop_inner[i][0], loop_inner[i][1], z_rear)
        in_nxt = (loop_inner[next_i][0], loop_inner[next_i][1], z_rear)
        
        triangles.append((bss_cur, in_nxt, bss_nxt))
        triangles.append((bss_cur, in_cur, in_nxt))
        
    # 6. Inner Tunnel Wall (Z from z_front to z_rear)
    # Normal points inward (towards center)
    for i in range(N):
        next_i = (i + 1) % N
        f_cur = (loop_inner[i][0], loop_inner[i][1], z_front)
        f_nxt = (loop_inner[next_i][0], loop_inner[next_i][1], z_front)
        r_cur = (loop_inner[i][0], loop_inner[i][1], z_rear)
        r_nxt = (loop_inner[next_i][0], loop_inner[next_i][1], z_rear)
        
        triangles.append((f_cur, f_nxt, r_nxt))
        triangles.append((f_cur, r_nxt, r_cur))
        
    return triangles

if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_stl = os.path.join(out_dir, "focus_svt_jvc_kw_v830bt_bezel.stl")
    
    triangles = create_bezel_mesh()
    write_binary_stl(triangles, out_stl)
    print(f"Generated binary STL with {len(triangles)} triangles at: {out_stl}")
    print(f"File size: {os.path.getsize(out_stl)} bytes")

