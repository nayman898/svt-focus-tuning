"""
build_single_arm_gauge.py
Generates focus_svt_cage_arm_single_gauge.stl:
Ultra-fast 3-4 minute, 5-gram single side-arm gauge for verifying the 187.40 -> 181.00 mm
taper and friction feel directly against the car console wall.
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

def build_single_arm():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out_dir = r"c:\Users\nlm89\source\repos\svt-focus-tuning\cad\radio_adapter"
    out_path = os.path.join(out_dir, "focus_svt_cage_arm_single_gauge.stl")

    h_arm = 12.0
    y_min, y_max = -h_arm / 2.0, h_arm / 2.0

    z_front = 0.0
    z_collar = -3.0
    z_rear = -72.0
    lead_in = 6.0

    x_flange = 96.00
    x_collar = 93.70
    x_tip = 90.50
    x_inner = 89.15

    def x_outer(z):
        if z >= z_collar:
            return x_flange
        t = (z - z_collar) / (z_rear - z_collar)
        t = max(0.0, min(1.0, t))
        xo = x_collar + (x_tip - x_collar) * t
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            xo -= 1.00 * c_frac
        return xo

    mesh = bpy.data.meshes.new("single_arm")
    obj = bpy.data.objects.new("single_arm", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    z_slices = [
        z_front,
        z_collar + 0.01,
        z_collar,
        -15.0, -30.0, -45.0, -60.0,
        z_rear + lead_in,
        z_rear,
    ]
    rings = []
    for z in z_slices:
        xo = x_outer(z)
        xi = x_inner
        if z >= z_collar:
            xi = x_inner - 2.50  # 2.5 mm wider grip tab on the front
        yo_max = y_max
        yo_min = y_min
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            yo_max -= 0.80 * c_frac
            yo_min += 0.80 * c_frac
        # 4 vertices for right arm
        v0 = bm.verts.new((xi, yo_min, z))
        v1 = bm.verts.new((xo, yo_min, z))
        v2 = bm.verts.new((xo, yo_max, z))
        v3 = bm.verts.new((xi, yo_max, z))
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

    # Pre-rotate flat on build plate (Z height = 12.0 mm = 42 layers at 0.28mm!)
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    obj.location = (-x_inner, -72.0, 6.0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=out_path, export_selected_objects=True)
    print("Exported Single Arm Gauge to:", out_path)

if __name__ == "__main__":
    build_single_arm()
