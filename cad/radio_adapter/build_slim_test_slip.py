"""
build_slim_test_slip.py
Generates focus_svt_cage_arm_test_slip_slim.stl:
Ultra-fast (12-15 min, ~14 grams) rigid test slip for verifying the 187.40 -> 181.00 mm
taper and friction fit of the unibody cage side arms in the Ford Focus SVT dash.
"""

import bpy
import bmesh
import math
import os

def clean_object_mesh(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def build_slim_slip():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out_dir = r"c:\Users\nlm89\source\repos\svt-focus-tuning\cad\radio_adapter"
    out_path = os.path.join(out_dir, "focus_svt_cage_arm_test_slip_slim.stl")

    # Dimensions
    # Height of slip: 16.0 mm (in CAD Y, which becomes Z on bed: 16.0 mm = 57 layers at 0.28mm!)
    h_slip = 16.0
    y_min, y_max = -h_slip / 2.0, h_slip / 2.0

    z_front = 0.0
    z_collar = -4.0       # 4.0 mm front flange stop
    z_rear = -75.0        # Insertion depth: 75.0 mm
    lead_in = 6.0

    x_flange = 96.00      # 192.00 mm outer stop lip
    x_collar = 93.70      # 187.40 mm at collar
    x_tip = 90.50         # 181.00 mm at rear tip
    x_inner = 89.15       # 178.30 mm inner clearance (radio width)

    # 1. Build Outer Shell
    def x_outer(z):
        if z >= z_collar:
            return x_flange
        t = (z - z_collar) / (z_rear - z_collar)
        t = max(0.0, min(1.0, t))
        xo = x_collar + (x_tip - x_collar) * t
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            xo -= 1.20 * c_frac
        return xo

    mesh = bpy.data.meshes.new("slim_slip")
    obj = bpy.data.objects.new("slim_slip", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    z_slices = [
        z_front,
        z_collar + 0.01,
        z_collar,
        -14.0, -24.0, -34.0, -44.0, -54.0, -64.0,
        z_rear + lead_in,
        z_rear,
    ]
    rings = []
    for z in z_slices:
        xo = x_outer(z)
        yo_max = y_max
        yo_min = y_min
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            yo_max -= 1.00 * c_frac
            yo_min += 1.00 * c_frac
        v0 = bm.verts.new((-xo, yo_min, z))
        v1 = bm.verts.new(( xo, yo_min, z))
        v2 = bm.verts.new(( xo, yo_max, z))
        v3 = bm.verts.new((-xo, yo_max, z))
        rings.append([v0, v1, v2, v3])

    for i in range(len(rings) - 1):
        r1, r2 = rings[i], rings[i + 1]
        for j in range(4):
            nxt = (j + 1) % 4
            bm.faces.new([r1[j], r1[nxt], r2[nxt], r2[j]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    clean_object_mesh(obj)

    # 2. Hollow Pocket Cutter (removes 80% of volume! Leaves 2.8mm front bridge and 3mm rear tie bar)
    cut_mesh = bpy.data.meshes.new("hollow_cut")
    cut_obj = bpy.data.objects.new("hollow_cut", cut_mesh)
    bpy.context.collection.objects.link(cut_obj)
    bm_c = bmesh.new()

    zc_front = z_collar - 2.80   # 2.8 mm thick front bridge
    zc_rear = z_rear + 3.50      # 3.5 mm thick rear tie bar
    yc_min = y_min - 2.0
    yc_max = y_max + 2.0

    vc = [
        bm_c.verts.new((-x_inner, yc_min, zc_rear)),
        bm_c.verts.new(( x_inner, yc_min, zc_rear)),
        bm_c.verts.new(( x_inner, yc_max, zc_rear)),
        bm_c.verts.new((-x_inner, yc_max, zc_rear)),
        bm_c.verts.new((-x_inner, yc_min, zc_front)),
        bm_c.verts.new(( x_inner, yc_min, zc_front)),
        bm_c.verts.new(( x_inner, yc_max, zc_front)),
        bm_c.verts.new((-x_inner, yc_max, zc_front)),
    ]
    bm_c.faces.new([vc[0], vc[1], vc[2], vc[3]])
    bm_c.faces.new([vc[4], vc[7], vc[6], vc[5]])
    bm_c.faces.new([vc[0], vc[4], vc[5], vc[1]])
    bm_c.faces.new([vc[2], vc[6], vc[7], vc[3]])
    bm_c.faces.new([vc[0], vc[3], vc[7], vc[4]])
    bm_c.faces.new([vc[1], vc[5], vc[6], vc[2]])
    bmesh.ops.triangulate(bm_c, faces=bm_c.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_c.normal_update()
    bm_c.to_mesh(cut_mesh)
    bm_c.free()
    clean_object_mesh(cut_obj)

    mod_c = obj.modifiers.new(name="Hollow", type='BOOLEAN')
    mod_c.operation = 'DIFFERENCE'
    mod_c.object = cut_obj
    mod_c.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Hollow")
    bpy.data.objects.remove(cut_obj, do_unlink=True)
    clean_object_mesh(obj)

    # 3. Deboss Front Label '▲ TOP · 187.4mm ▲'
    font_curve = bpy.data.curves.new(type="FONT", name="label_curve")
    font_curve.body = "▲ TOP · 187.4mm ▲"
    font_curve.size = 4.2
    font_curve.extrude = 0.50
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'
    lab_obj = bpy.data.objects.new("lab_obj", font_curve)
    bpy.context.collection.objects.link(lab_obj)
    lab_obj.location = (0.0, 0.0, -0.25)
    bpy.ops.object.select_all(action='DESELECT')
    lab_obj.select_set(True)
    bpy.context.view_layer.objects.active = lab_obj
    bpy.ops.object.convert(target='MESH')
    clean_object_mesh(lab_obj)

    mod_l = obj.modifiers.new(name="Deboss", type='BOOLEAN')
    mod_l.operation = 'DIFFERENCE'
    mod_l.object = lab_obj
    mod_l.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Deboss")
    bpy.data.objects.remove(lab_obj, do_unlink=True)
    clean_object_mesh(obj)

    # Pre-rotate flat on build plate (Z height = 16.0 mm = 57 layers at 0.28mm!)
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    obj.location = (0.0, -75.0, 8.0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=out_path, export_selected_objects=True)
    print("Exported Slim Test Slip to:", out_path)

if __name__ == "__main__":
    build_slim_slip()
