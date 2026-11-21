#!/usr/bin/env python3
"""
generate_4mm_spacer_stl.py
Generates watertight, manifold binary STLs for:
  Application: Mustang Caliper to Focus SVT Adapter 4.00 mm Centering Spacers
  Fastener:    M12x1.75 Caliper Bolts

Spacer Specifications:
  - Thickness:      4.00 mm (replaces the machined step to center caliper over rotor)
  - Inner Diameter: 13.00 mm (clean slip fit for M12x1.75 bolts)
  - Outer Diameter: 26.00 mm (matches the caliper mounting ear boss diameter)

Outputs:
  1. focus_svt_mustang_bbk_4mm_spacer.stl      (Single spacer)
  2. focus_svt_mustang_bbk_4mm_spacer_pair.stl (Pair of 2 spacers spaced 34mm apart on print bed)
"""

import math
import struct
import os
import sys

def calc_normal(p1, p2, p3):
    u = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    v = (p3[0]-p1[0], p3[1]-p1[1], p3[2]-p1[2])
    nx = u[1]*v[2] - u[2]*v[1]
    ny = u[2]*v[0] - u[0]*v[2]
    nz = u[0]*v[1] - u[1]*v[0]
    l = math.sqrt(nx*nx + ny*ny + nz*nz)
    if l < 1e-12:
        return (0.0, 0.0, 1.0)
    return (nx/l, ny/l, nz/l)

def write_binary_stl(triangles, filepath, header_title=b'Focus SVT to Mustang BBK 4mm Caliper Spacer'):
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

def build_single_spacer_mesh(center=(0.0, 0.0), od=26.0, id_hole=13.0, thick=4.0, n_pts=48):
    cx, cy = center
    r_out = od / 2.0
    r_in = id_hole / 2.0
    
    out_pts = [(cx + r_out * math.cos(2*math.pi*i/n_pts), cy + r_out * math.sin(2*math.pi*i/n_pts)) for i in range(n_pts)]
    in_pts = [(cx + r_in * math.cos(2*math.pi*i/n_pts), cy + r_in * math.sin(2*math.pi*i/n_pts)) for i in range(n_pts)]
    
    triangles = []
    
    # 1. Top Annular Face at Z = thick (Outward normal +Z)
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        o1 = (out_pts[i][0], out_pts[i][1], thick)
        o2 = (out_pts[nxt][0], out_pts[nxt][1], thick)
        i1 = (in_pts[i][0], in_pts[i][1], thick)
        i2 = (in_pts[nxt][0], in_pts[nxt][1], thick)
        triangles.append((o1, o2, i2))
        triangles.append((o1, i2, i1))
        
    # 2. Bottom Annular Face at Z = 0 (Outward normal -Z, reversed winding)
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        o1 = (out_pts[i][0], out_pts[i][1], 0.0)
        o2 = (out_pts[nxt][0], out_pts[nxt][1], 0.0)
        i1 = (in_pts[i][0], in_pts[i][1], 0.0)
        i2 = (in_pts[nxt][0], in_pts[nxt][1], 0.0)
        triangles.append((o1, i2, o2))
        triangles.append((o1, i1, i2))
        
    # 3. Outer Cylinder Wall (Outward normal)
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        b1 = (out_pts[i][0], out_pts[i][1], 0.0)
        b2 = (out_pts[nxt][0], out_pts[nxt][1], 0.0)
        t1 = (out_pts[i][0], out_pts[i][1], thick)
        t2 = (out_pts[nxt][0], out_pts[nxt][1], thick)
        triangles.append((b1, b2, t2))
        triangles.append((b1, t2, t1))
        
    # 4. Inner Cylinder Wall (Inward normal into center hole)
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        b1 = (in_pts[i][0], in_pts[i][1], 0.0)
        b2 = (in_pts[nxt][0], in_pts[nxt][1], 0.0)
        t1 = (in_pts[i][0], in_pts[i][1], thick)
        t2 = (in_pts[nxt][0], in_pts[nxt][1], thick)
        triangles.append((b1, t2, b2))
        triangles.append((b1, t1, t2))
        
    return triangles

def check_manifold(triangles):
    edge_counts = {}
    def quantize(pt, eps=1e-4):
        return (round(pt[0]/eps)*eps, round(pt[1]/eps)*eps, round(pt[2]/eps)*eps)
    for p1, p2, p3 in triangles:
        pts = [quantize(p1), quantize(p2), quantize(p3)]
        for i in range(3):
            e = tuple(sorted([pts[i], pts[(i+1)%3]]))
            edge_counts[e] = edge_counts.get(e, 0) + 1
    bad_edges = [edge for edge, count in edge_counts.items() if count != 2]
    vol = sum((p1[0]*(p2[1]*p3[2]-p2[2]*p3[1]) + p1[1]*(p2[2]*p3[0]-p2[0]*p3[2]) + p1[2]*(p2[0]*p3[1]-p2[1]*p3[0]))/6.0 for p1, p2, p3 in triangles)
    return len(bad_edges), vol

if __name__ == '__main__':
    output_dir = os.path.dirname(os.path.abspath(__file__))
    single_path = os.path.join(output_dir, 'focus_svt_mustang_bbk_4mm_spacer.stl')
    pair_path   = os.path.join(output_dir, 'focus_svt_mustang_bbk_4mm_spacer_pair.stl')
    
    # 1. Single Spacer
    print("Generating Single 4.00 mm Caliper Spacer (OD=26mm, ID=13mm)...")
    single_mesh = build_single_spacer_mesh(center=(0.0, 0.0))
    bad_edges, vol = check_manifold(single_mesh)
    print(f"Single Spacer: {bad_edges} bad edges (0 = Watertight), Volume = {vol/1000.0:.3f} cm3")
    if bad_edges == 0:
        write_binary_stl(single_mesh, single_path, header_title=b'BBK 4mm Caliper Spacer - Single')
        print(f"Saved: {single_path}")
    else:
        sys.exit(1)
        
    # 2. Spacer Pair (arranged side-by-side on bed, 34mm center distance)
    print("Generating Pair of 4.00 mm Caliper Spacers (Pre-arranged for print bed)...")
    pair_mesh = []
    pair_mesh.extend(build_single_spacer_mesh(center=(-17.0, 0.0)))
    pair_mesh.extend(build_single_spacer_mesh(center=( 17.0, 0.0)))
    bad_edges_p, vol_p = check_manifold(pair_mesh)
    print(f"Spacer Pair: {bad_edges_p} bad edges (0 = Watertight), Combined Volume = {vol_p/1000.0:.3f} cm3")
    if bad_edges_p == 0:
        write_binary_stl(pair_mesh, pair_path, header_title=b'BBK 4mm Caliper Spacer - Pair')
        print(f"Saved: {pair_path}")
    else:
        sys.exit(1)
        
    print("4mm Spacer Generation COMPLETE!")
