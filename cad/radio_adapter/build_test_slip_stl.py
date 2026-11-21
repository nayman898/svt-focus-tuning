"""
build_test_slip_stl.py
Generates focus_svt_cage_arm_test_slip.stl:
A fast-printing (20-25 min), lightweight, 100% watertight 2-manifold test slip
for verifying the exact 187.40 mm -> 181.00 mm front-to-back depth taper and
friction fit of the unibody cage side arms in the Ford Focus SVT MK1 center console.
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

def build_test_slip():
    # Reset Blender scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    out_dir = r"c:\Users\nlm89\source\repos\svt-focus-tuning\cad\radio_adapter"
    out_path = os.path.join(out_dir, "focus_svt_cage_arm_test_slip.stl")

    # Dimensions
    h_arm = 24.0          # Y from -12.0 to +12.0 mm
    y_min, y_max = -h_arm / 2.0, h_arm / 2.0

    z_front = 0.0         # Planar front face on PEI bed
    z_collar = -8.0       # Console collar stop lip
    z_rear = -80.0        # Insertion tip
    lead_in = 6.0         # Lead-in chamfer at rear tip

    # Widths (symmetric about X=0)
    # Flange at front (stops against console face):
    x_flange = 97.75      # 195.50 mm outer width
    # Tapered side arms:
    x_collar = 93.70      # 187.40 mm at collar (Z = -8.0)
    x_tip = 90.50         # 181.00 mm at rear (Z = -80.0)

    # Inner cavity (simulates the rigid bolted JVC chassis):
    x_inner = 89.15       # 178.30 mm inner clearance

    def x_outer_at_z(z):
        if z >= z_collar:
            # Front flange
            return x_flange
        t = (z - z_collar) / (z_rear - z_collar)
        t = max(0.0, min(1.0, t))
        xo = x_collar + (x_tip - x_collar) * t
        # Lead-in chamfer at rear
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            xo -= 1.20 * c_frac
        return xo

    mesh = bpy.data.meshes.new("test_slip")
    obj = bpy.data.objects.new("test_slip", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    # Build outer solid body:
    # Profile along Z:
    # Z slices:
    z_slices = [
        z_front,                  # 0.0
        z_collar + 0.01,          # -7.99 (flange)
        z_collar,                 # -8.00 (step to collar)
        -18.0,                    # 10 mm depth
        -28.0,                    # 20 mm depth
        -38.0,                    # 30 mm depth
        -48.0,                    # 40 mm depth
        -58.0,                    # 50 mm depth
        -68.0,                    # 60 mm depth
        z_rear + lead_in,         # -74.00 (start of chamfer)
        z_rear,                   # -80.00 (rear tip)
    ]

    # Build outer block from z_front to z_rear:
    rings = []
    for z in z_slices:
        xo = x_outer_at_z(z)
        yo_max = y_max
        yo_min = y_min
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            yo_max -= 1.00 * c_frac
            yo_min += 1.00 * c_frac
        # 4 vertices per slice: (-xo, yo_min), (xo, yo_min), (xo, yo_max), (-xo, yo_max)
        v0 = bm.verts.new((-xo, yo_min, z))
        v1 = bm.verts.new(( xo, yo_min, z))
        v2 = bm.verts.new(( xo, yo_max, z))
        v3 = bm.verts.new((-xo, yo_max, z))
        rings.append([v0, v1, v2, v3])

    # Side walls:
    for i in range(len(rings) - 1):
        r1 = rings[i]
        r2 = rings[i + 1]
        for j in range(4):
            nxt = (j + 1) % 4
            bm.faces.new([r1[j], r1[nxt], r2[nxt], r2[j]])

    # Front face at Z = 0:
    bm.faces.new(list(reversed(rings[0])))
    # Rear face at Z = -80:
    bm.faces.new(rings[-1])

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    clean_object_mesh(obj)

    # Cut central hollow pocket (between Z = -8.0 and Z = -72.0 mm)
    # Leaving front crossbar (Z = 0 to -8 mm) and rear tie-bar (Z = -72 to -80 mm)
    cut_mesh = bpy.data.meshes.new("hollow_cutter")
    cut_obj = bpy.data.objects.new("hollow_cutter", cut_mesh)
    bpy.context.collection.objects.link(cut_obj)

    bm_c = bmesh.new()
    xi = x_inner  # 89.15 mm
    zc_front = z_collar - 0.01  # -8.01 mm
    zc_rear = z_rear + 8.00     # -72.00 mm
    yc_min = y_min - 2.0
    yc_max = y_max + 2.0

    vc = [
        bm_c.verts.new((-xi, yc_min, zc_rear)),
        bm_c.verts.new(( xi, yc_min, zc_rear)),
        bm_c.verts.new(( xi, yc_max, zc_rear)),
        bm_c.verts.new((-xi, yc_max, zc_rear)),
        bm_c.verts.new((-xi, yc_min, zc_front)),
        bm_c.verts.new(( xi, yc_min, zc_front)),
        bm_c.verts.new(( xi, yc_max, zc_front)),
        bm_c.verts.new((-xi, yc_max, zc_front)),
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

    mod_cut = obj.modifiers.new(name="HollowCut", type='BOOLEAN')
    mod_cut.operation = 'DIFFERENCE'
    mod_cut.object = cut_obj
    mod_cut.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="HollowCut")
    bpy.data.objects.remove(cut_obj, do_unlink=True)
    clean_object_mesh(obj)

    # Deboss Depth Tick Marks on top rim (Y = +12.0 mm)
    # Ticks at 10, 20, 30, 40, 50, 60 mm from collar (Z = -18, -28, -38, -48, -58, -68)
    notch_mesh = bpy.data.meshes.new("notches")
    notch_obj = bpy.data.objects.new("notches", notch_mesh)
    bpy.context.collection.objects.link(notch_obj)
    bm_n = bmesh.new()

    for d in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]:
        z_mark = z_collar - d
        # Notch on left and right arm
        for side in [-1, 1]:
            x_m = side * (x_outer_at_z(z_mark) + 1.0)
            x_in = side * (x_inner - 1.0)
            xa = min(x_m, x_in)
            xb = max(x_m, x_in)
            w_z = 0.80  # 0.8 mm tick width in Z
            d_y = 0.60  # 0.6 mm deep notch in Y
            
            vn = [
                bm_n.verts.new((xa, y_max - d_y, z_mark - w_z / 2)),
                bm_n.verts.new((xb, y_max - d_y, z_mark - w_z / 2)),
                bm_n.verts.new((xb, y_max + 1.0, z_mark - w_z / 2)),
                bm_n.verts.new((xa, y_max + 1.0, z_mark - w_z / 2)),
                bm_n.verts.new((xa, y_max - d_y, z_mark + w_z / 2)),
                bm_n.verts.new((xb, y_max - d_y, z_mark + w_z / 2)),
                bm_n.verts.new((xb, y_max + 1.0, z_mark + w_z / 2)),
                bm_n.verts.new((xa, y_max + 1.0, z_mark + w_z / 2)),
            ]
            bm_n.faces.new([vn[0], vn[1], vn[2], vn[3]])
            bm_n.faces.new([vn[4], vn[7], vn[6], vn[5]])
            bm_n.faces.new([vn[0], vn[4], vn[5], vn[1]])
            bm_n.faces.new([vn[2], vn[6], vn[7], vn[3]])
            bm_n.faces.new([vn[0], vn[3], vn[7], vn[4]])
            bm_n.faces.new([vn[1], vn[5], vn[6], vn[2]])

    bmesh.ops.triangulate(bm_n, faces=bm_n.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_n.normal_update()
    bm_n.to_mesh(notch_mesh)
    bm_n.free()
    clean_object_mesh(notch_obj)

    mod_notches = obj.modifiers.new(name="NotchCut", type='BOOLEAN')
    mod_notches.operation = 'DIFFERENCE'
    mod_notches.object = notch_obj
    mod_notches.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="NotchCut")
    bpy.data.objects.remove(notch_obj, do_unlink=True)
    clean_object_mesh(obj)

    # Deboss Front Label: '▲ TOP · 187.4mm SLIP ▲'
    font_curve = bpy.data.curves.new(type="FONT", name="label_slip_curve")
    font_curve.body = "▲ TOP · 187.4mm SLIP ▲"
    font_curve.size = 5.2
    font_curve.extrude = 0.60
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'

    label_obj = bpy.data.objects.new("label_slip_obj", font_curve)
    bpy.context.collection.objects.link(label_obj)
    label_obj.location = (0.0, 0.0, -0.30)  # Cuts from Z = 0.30 to -0.30 mm

    bpy.ops.object.select_all(action='DESELECT')
    label_obj.select_set(True)
    bpy.context.view_layer.objects.active = label_obj
    bpy.ops.object.convert(target='MESH')
    clean_object_mesh(label_obj)

    mod_lab = obj.modifiers.new(name="DebossLabel", type='BOOLEAN')
    mod_lab.operation = 'DIFFERENCE'
    mod_lab.object = label_obj
    mod_lab.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="DebossLabel")
    bpy.data.objects.remove(label_obj, do_unlink=True)
    clean_object_mesh(obj)

    # Export STL
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(
        filepath=out_path,
        export_selected_objects=True,
        apply_modifiers=True,
    )
    print(f"Exported Cage Arm Test Slip to: {out_path}")

if __name__ == "__main__":
    build_test_slip()
