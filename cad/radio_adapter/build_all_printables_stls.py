import bpy
import bmesh
import math
import os


def make_trapezoidal_rounded_rect_pts(
    w_top, w_bot, h, r_top, r_bot, y_offset=0.0, corner_segs=12, edge_segs=24
):
    """
    Generate a densely subdivided 2D loop of (x, y) points for a trapezoidal rounded rectangle,
    allowing independent top width `w_top` and flared bottom width `w_bot` (e.g. wider rear
    base flaring from 196.00 mm top to 197.50 mm bottom to cover console corner gaps cleanly).
    Includes `edge_segs` intermediate vertices along all 4 edges so 3D Z-axis contours curve smoothly.
    """
    hw_top = w_top / 2.0
    hw_bot = w_bot / 2.0
    hh = h / 2.0
    r_top = min(r_top, hw_top - 0.01, hh - 0.01)
    r_bot = min(r_bot, hw_bot - 0.01, hh - 0.01)

    pts = []

    # 1. Top-Right Corner (0 to pi/2)
    cx, cy = hw_top - r_top, y_offset + hh - r_top
    for i in range(corner_segs):
        a = 0.0 + (math.pi / 2.0) * (i / float(corner_segs))
        pts.append((cx + r_top * math.cos(a), cy + r_top * math.sin(a)))

    # 2. Top Straight Edge (x from +(hw_top-r_top) to -(hw_top-r_top), y = y_offset + hh)
    for i in range(edge_segs):
        frac = i / float(edge_segs)
        x = (hw_top - r_top) * (1.0 - 2.0 * frac)
        pts.append((x, y_offset + hh))

    # 3. Top-Left Corner (pi/2 to pi)
    cx, cy = -hw_top + r_top, y_offset + hh - r_top
    for i in range(corner_segs):
        a = (math.pi / 2.0) + (math.pi / 2.0) * (i / float(corner_segs))
        pts.append((cx + r_top * math.cos(a), cy + r_top * math.sin(a)))

    # 4. Left Edge (tapering linearly from -hw_top to -hw_bot)
    y_start = y_offset + hh - r_top
    y_end = y_offset - hh + r_bot
    for i in range(edge_segs):
        frac = i / float(edge_segs)
        y = y_start + (y_end - y_start) * frac
        hw = hw_top * (1.0 - frac) + hw_bot * frac
        pts.append((-hw, y))

    # 5. Bottom-Left Corner (pi to 3*pi/2)
    cx, cy = -hw_bot + r_bot, y_offset - hh + r_bot
    for i in range(corner_segs):
        a = math.pi + (math.pi / 2.0) * (i / float(corner_segs))
        pts.append((cx + r_bot * math.cos(a), cy + r_bot * math.sin(a)))

    # 6. Bottom Straight Edge (x from -(hw_bot-r_bot) to +(hw_bot-r_bot), y = y_offset - hh)
    for i in range(edge_segs):
        frac = i / float(edge_segs)
        x = -(hw_bot - r_bot) * (1.0 - 2.0 * frac)
        pts.append((x, y_offset - hh))

    # 7. Bottom-Right Corner (3*pi/2 to 2*pi)
    cx, cy = hw_bot - r_bot, y_offset - hh + r_bot
    for i in range(corner_segs):
        a = (3.0 * math.pi / 2.0) + (math.pi / 2.0) * (i / float(corner_segs))
        pts.append((cx + r_bot * math.cos(a), cy + r_bot * math.sin(a)))

    # 8. Right Edge (tapering linearly from +hw_bot to +hw_top)
    for i in range(edge_segs):
        frac = i / float(edge_segs)
        y = y_end + (y_start - y_end) * frac
        hw = hw_bot * (1.0 - frac) + hw_top * frac
        pts.append((hw, y))

    return pts


def make_rounded_rect_pts(w, h, r, y_offset=0.0, corner_segs=12, edge_segs=24):
    """Symmetric wrapper calling make_trapezoidal_rounded_rect_pts with w_top = w_bot = w."""
    return make_trapezoidal_rounded_rect_pts(
        w, w, h, r, r, y_offset=y_offset, corner_segs=corner_segs, edge_segs=edge_segs
    )


def z_console_offset(
    x, y,
    z_bow_top=7.60,
    z_bow_bottom=5.00,
    z_bow_x=5.50,
    ref_hw_top=98.00,
    ref_hw_bot=98.75,
    ref_y_top=53.60,
    ref_y_bot=55.40,
):
    """
    Calibrated 3D biquadratic console contour from physical ruler + caliper measurements & test print photos:
      - Top Edge (y = +53.60, x from 0 to +-98.00): corners drop 7.60 mm from top-center (+2.0 mm deeper hug to close upper corner gaps).
      - Bottom Edge (y = -55.40, x from 0 to +-98.75): corners drop 5.00 mm from bottom-center.
      - Left & Right Sides:
        * Top corners drop 7.60 mm relative to top-center.
        * Bottom corners drop 4.20 mm from side-center.
      - Bottom-Right Corner (+X, -Y): curves an additional 3.00 mm closer to the console (total ~7.5 mm drop)
        to eliminate the daylight gap visible in the physical fitment photos!
    """
    if y >= 0.0:
        fy2 = min(1.2, (y / ref_y_top) ** 2)
        fx2 = min(1.2, (x / ref_hw_top) ** 2)
        return -(0.30 * fx2 + 0.20 * fy2 + (z_bow_top - 0.30) * fx2 * fy2)
    else:
        fy2 = min(1.2, ((-y) / ref_y_bot) ** 2)
        frac_bot = min(1.0, (-y) / ref_y_bot)
        hw_y = ref_hw_top + (ref_hw_bot - ref_hw_top) * frac_bot
        fx2 = min(1.2, (x / hw_y) ** 2)
        base = -(0.30 * fx2 - 0.50 * fy2 + (z_bow_bottom - 0.30) * fx2 * fy2)
        if x > 0.0:
            # Smooth C1-continuous extra curve towards the console in the bottom-right corner (+X, -Y)
            u = min(1.0, x / hw_y)
            v = min(1.0, (-y) / ref_y_bot)
            extra_br = -3.00 * (u ** 2) * (v ** 2)
            return base + extra_br
        return base


def make_sloped_contoured_pod(
    name,
    z_depth,
    z_bow_top=7.60,
    z_bow_bottom=5.00,
    z_bow_x=5.50,
    corner_segs=12,
    edge_segs=24,
    n_steps=14,
):
    """
    Build the sloped pod from Z = 0.0 (100% flat front face for PEI printing)
    to the 3D Z-contoured rear console seating surface Z = -z_depth + z_console_offset(x, y).
    - Widened Top Base Edge: 196.00 mm (X = +-98.00 mm, Y = +53.60 mm, +2.25 mm/side wider) with tighter 5.0 mm corner radius to hide upper corner notches.
    - Widened Bottom Base Edge: 197.50 mm (X = +-98.75 mm, Y = -55.40 mm, +1.00 mm/side wider) with 6.5 mm corner radius, seamlessly clearing the ashtray/HVAC bezels.
    - Total height remains identical at 109.00 mm (Y = -55.40 to +53.60 mm).
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    w_front_top, w_front_bot = 185.20, 187.20
    h_front = 104.20
    r_front_top, r_front_bot = 3.00, 3.50
    y_off_front = -0.40

    w_back_top, w_back_bot = 196.00, 197.50  # Widened rear base skirt (+4.5 mm top / +2.0 mm bottom) to hide console cutout corner gaps!
    h_back = 109.00
    r_back_top, r_back_bot = 5.00, 6.50
    y_off_back = -0.90

    vert_rings = []
    for step in range(n_steps + 1):
        t = step / float(n_steps)
        ease = math.sin(t * (math.pi / 2.0)) ** 0.75
        w_top = w_front_top + (w_back_top - w_front_top) * ease
        w_bot = w_front_bot + (w_back_bot - w_front_bot) * ease
        h = h_front + (h_back - h_front) * ease
        r_top = r_front_top + (r_back_top - r_front_top) * ease
        r_bot = r_front_bot + (r_back_bot - r_front_bot) * ease
        y_off = y_off_front + (y_off_back - y_off_front) * ease

        pts = make_trapezoidal_rounded_rect_pts(
            w_top, w_bot, h, r_top, r_bot, y_offset=y_off, corner_segs=corner_segs, edge_segs=edge_segs
        )
        ring = []
        for x, y in pts:
            z = -t * z_depth + (t ** 1.05) * z_console_offset(
                x, y, z_bow_top=z_bow_top, z_bow_bottom=z_bow_bottom, z_bow_x=z_bow_x
            )
            ring.append(bm.verts.new((x, y, z)))
        vert_rings.append(ring)

    n_pts = len(vert_rings[0])
    for l_idx in range(len(vert_rings) - 1):
        r_a = vert_rings[l_idx]
        r_b = vert_rings[l_idx + 1]
        for i in range(n_pts):
            nxt = (i + 1) % n_pts
            bm.faces.new([r_a[i], r_a[nxt], r_b[nxt], r_b[i]])

    # Cap flat front face at Z = 0.0 (normal +Z)
    bm.faces.new(list(reversed(vert_rings[0])))

    # Cap contoured rear face using an inner ring (inside the 169.70 x 97.30 front inlay cutter)
    pts_inner_cap = make_trapezoidal_rounded_rect_pts(
        164.00, 164.00, 92.00, 1.00, 1.00, y_offset=-0.50, corner_segs=corner_segs, edge_segs=edge_segs
    )
    pts_outer_back = make_trapezoidal_rounded_rect_pts(
        w_back_top, w_back_bot, h_back, r_back_top, r_back_bot, y_offset=y_off_back, corner_segs=corner_segs, edge_segs=edge_segs
    )
    r_inner_back = []
    for (xi, yi), (xo, yo) in zip(pts_inner_cap, pts_outer_back):
        z_back = -z_depth + z_console_offset(
            xo, yo, z_bow_top=z_bow_top, z_bow_bottom=z_bow_bottom, z_bow_x=z_bow_x
        )
        r_inner_back.append(bm.verts.new((xi, yi, z_back)))

    r_last = vert_rings[-1]
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        bm.faces.new([r_last[i], r_last[nxt], r_inner_back[nxt], r_inner_back[i]])

    v_center = bm.verts.new((0.0, 0.0, -z_depth))
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        bm.faces.new([r_inner_back[i], r_inner_back[nxt], v_center])

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return obj
    bm.to_mesh(mesh)
    bm.free()
    return obj


def make_loft_solid(name, levels):
    """Create a watertight 2-manifold prism/loft from planar Z levels."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    vert_rings = []
    for pts, z in levels:
        ring = [bm.verts.new((x, y, z)) for x, y in pts]
        vert_rings.append(ring)

    n_pts = len(levels[0][0])
    for l_idx in range(len(levels) - 1):
        r_a = vert_rings[l_idx]
        r_b = vert_rings[l_idx + 1]
        for i in range(n_pts):
            nxt = (i + 1) % n_pts
            bm.faces.new([r_a[i], r_a[nxt], r_b[nxt], r_b[i]])

    bm.faces.new(list(reversed(vert_rings[0])))
    bm.faces.new(vert_rings[-1])

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return obj


def build_contoured_tab_solid(
    name, x_inner, x_outer_fn, y_span, chamfer, z_front_fn, z_back_fn, n_y=36, n_z=8
):
    """
    Build a 100% manifold, zero-ngon quad-grid solid for left and right contoured tabs,
    supporting a 3D contoured outer X profile `x_outer_fn(y, t_z)` so integrated
    pressure-fit console retention clips/ribs can be molded directly into the side tabs!
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    y_vals = [-y_span + (2.0 * y_span) * (i / float(n_y)) for i in range(n_y + 1)]

    for side in [-1, 1]:
        # Build a grid of (n_y + 1) x (n_z + 1) vertices on inner wall and outer wall
        v_in = []
        v_out = []
        for y in y_vals:
            zf = z_front_fn(y, side)
            dist_end = y_span - abs(y)
            chamf = max(0.0, chamfer - dist_end)
            zb = z_back_fn(y, side) + chamf

            row_in = []
            row_out = []
            for k in range(n_z + 1):
                tz = k / float(n_z)  # tz=0 is front (overlap into bezel), tz=1 is rear edge
                z = zf + (zb - zf) * tz
                xo = x_outer_fn(y, tz)
                if side == -1:
                    x_a = -xo
                    x_b = -x_inner
                else:
                    x_a = x_inner
                    x_b = xo
                row_in.append(bm.verts.new((x_a, y, z)))
                row_out.append(bm.verts.new((x_b, y, z)))
            v_in.append(row_in)
            v_out.append(row_out)

        # 1. Left (-X of solid) and Right (+X of solid) walls across (i, k)
        for i in range(n_y):
            for k in range(n_z):
                # x_a face (normal -X)
                bm.faces.new([v_in[i][k], v_in[i + 1][k], v_in[i + 1][k + 1], v_in[i][k + 1]])
                # x_b face (normal +X)
                bm.faces.new([v_out[i][k + 1], v_out[i + 1][k + 1], v_out[i + 1][k], v_out[i][k]])

        # 2. Front Z wall (k = 0, normal +Z) and Rear Z wall (k = n_z, normal -Z)
        for i in range(n_y):
            bm.faces.new([v_out[i][0], v_out[i + 1][0], v_in[i + 1][0], v_in[i][0]])
            bm.faces.new([v_in[i][n_z], v_in[i + 1][n_z], v_out[i + 1][n_z], v_out[i][n_z]])

        # 3. Bottom Y cap (i = 0, normal -Y) and Top Y cap (i = n_y, normal +Y)
        for k in range(n_z):
            bm.faces.new([v_in[0][k], v_in[0][k + 1], v_out[0][k + 1], v_out[0][k]])
            bm.faces.new([v_out[n_y][k], v_out[n_y][k + 1], v_in[n_y][k + 1], v_in[n_y][k]])

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    clean_object_mesh(obj)
    return obj


def make_contoured_two_step_locators_obj(
    name,
    z_depth=10.0,
    z_bow_top=5.60,
    z_bow_bottom=5.00,
    z_bow_x=5.50,
    recess_depth=14.0,
    boss_depth=4.0,
    n_y=40,
):
    """
    2-step rear side locator tabs with calibrated front-to-back depth taper:
      - Step 1 (Extended 14.0 mm Deep Console Shelf):
        Tapers linearly from 187.40 mm (X = +-93.70 mm) at the collar down to 184.00 mm
        (X = +-92.00 mm) at the rear (+1.00 mm wider than 186.40 mm for snug anti-tilt friction lock!),
        sliding into the console opening effortlessly and wedging firmly to prevent forward sagging!
      - Step 2 (Inner Lead-In Boss): 178.50 mm outer width (X = +-89.25 mm) at the very
        rear (14.0 to 18.0 mm behind the collar) with smooth lead-in chamfers.
    """
    x_inner_recess = 87.20
    x_inner_boss = 88.10
    x_recess_collar = 93.70   # 187.40 mm at collar (front, +1.00 mm total / +0.50 mm per side over 186.40 mm for tight anti-tilt lock!)
    x_recess_rear = 92.00     # 184.00 mm at rear of 14mm shelf (slides in freely, maintains anti-tilt friction depth!)
    x_boss_outer = 89.25      # 178.50 mm inner lead-in guide tab

    def z_surf_at_y(y, side=1):
        x = side * x_recess_collar
        return -z_depth + z_console_offset(
            x, y, z_bow_top=z_bow_top, z_bow_bottom=z_bow_bottom, z_bow_x=z_bow_x
        )

    def x_shelf_tapered(y, tz):
        """
        Front-to-back depth tapered shelf:
        - tz in [0.0, 0.90]: tapers from 187.40 mm (X = +-93.70 mm) down to 184.00 mm (X = +-92.00 mm)
        - tz > 0.90: smooth lead-in chamfer tapering down to 183.00 mm
        """
        xo = x_recess_collar + (x_recess_rear - x_recess_collar) * tz
        if tz > 0.90:
            xo -= 0.50 * ((tz - 0.90) / 0.10)
        return xo

    # 1. Step 1: 187.40 mm -> 184.00 mm Tapered Console Opening Shelf
    obj1 = build_contoured_tab_solid(
        name + "_recess",
        x_inner=x_inner_recess,
        x_outer_fn=x_shelf_tapered,
        y_span=41.50,
        chamfer=3.50,
        z_front_fn=lambda y, s=1: z_surf_at_y(y, s) + 2.50,
        z_back_fn=lambda y, s=1: z_surf_at_y(y, s) - recess_depth,
        n_y=n_y,
        n_z=16,
    )

    # 2. Step 2: 178.50 mm Inner Lead-In Boss (X = +-89.25 mm)
    obj2 = build_contoured_tab_solid(
        name + "_boss",
        x_inner=x_inner_boss,
        x_outer_fn=lambda y, tz: x_boss_outer,
        y_span=39.00,
        chamfer=4.00,
        z_front_fn=lambda y, s=1: z_surf_at_y(y, s) - recess_depth + 2.50,
        z_back_fn=lambda y, s=1: z_surf_at_y(y, s) - recess_depth - boss_depth,
        n_y=n_y,
        n_z=4,
    )

    mod_u = obj1.modifiers.new(name="UnionBoss", type='BOOLEAN')
    mod_u.operation = 'UNION'
    mod_u.object = obj2
    mod_u.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj1
    bpy.ops.object.modifier_apply(modifier="UnionBoss")
    bpy.data.objects.remove(obj2, do_unlink=True)
    clean_object_mesh(obj1)
    return obj1


def clean_object_mesh(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def make_top_label_cutter(name, z_depth, deboss_depth=0.50):
    """
    Build a deboss cutter object for '▲ TOP ▲' on the rear seating rim at top-center.
    Positioned at X=0, Y=51.6 mm, debossed 0.5 mm deep into the rear surface.
    Hidden when installed against the console, but immediately visible when holding the part!
    """
    z_rear = -z_depth + z_console_offset(0.0, 51.60)
    z_min = z_rear - 0.40  # overlaps slightly past the rear face into the dash cavity
    z_max = z_rear + deboss_depth  # cuts deboss_depth deep into the plastic

    c = bpy.data.curves.new(name + "_curve", 'FONT')
    c.body = 'TOP'
    c.size = 2.40
    c.extrude = (z_max - z_min) / 2.0
    t_obj = bpy.data.objects.new(name + "_text", c)
    bpy.context.collection.objects.link(t_obj)
    t_obj.select_set(True)
    bpy.context.view_layer.objects.active = t_obj
    bpy.ops.object.convert(target='MESH')
    clean_object_mesh(t_obj)

    bb = [t_obj.matrix_world @ v.co for v in t_obj.data.vertices]
    cx = 0.5 * (min(v.x for v in bb) + max(v.x for v in bb))
    cy = 0.5 * (min(v.y for v in bb) + max(v.y for v in bb))
    t_obj.location = (-cx, 51.60 - cy, z_min)

    def make_arrow_mesh(arr_name, x_center, y_bot, y_top, width):
        m = bpy.data.meshes.new(arr_name)
        o = bpy.data.objects.new(arr_name, m)
        bpy.context.collection.objects.link(o)
        bm_a = bmesh.new()
        hw = width / 2.0
        pts_xy = [(x_center - hw, y_bot), (x_center + hw, y_bot), (x_center, y_top)]
        v_b = [bm_a.verts.new((x, y, z_min)) for x, y in pts_xy]
        v_t = [bm_a.verts.new((x, y, z_max)) for x, y in pts_xy]
        for i in range(3):
            nxt = (i + 1) % 3
            bm_a.faces.new([v_b[i], v_b[nxt], v_t[nxt], v_t[i]])
        bm_a.faces.new(list(reversed(v_b)))
        bm_a.faces.new(v_t)
        bmesh.ops.triangulate(bm_a, faces=bm_a.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        bm_a.normal_update()
        bm_a.to_mesh(m)
        bm_a.free()
        clean_object_mesh(o)
        return o

    arr1 = make_arrow_mesh(name + "_arr1", -4.80, 50.60, 52.60, 2.00)
    arr2 = make_arrow_mesh(name + "_arr2",  4.80, 50.60, 52.60, 2.00)

    for arr in [arr1, arr2]:
        mod = t_obj.modifiers.new("UnionArr", 'BOOLEAN')
        mod.operation = 'UNION'
        mod.object = arr
        mod.solver = 'EXACT'
        bpy.context.view_layer.objects.active = t_obj
        bpy.ops.object.modifier_apply(modifier="UnionArr")
        bpy.data.objects.remove(arr, do_unlink=True)

    clean_object_mesh(t_obj)
    return t_obj


def run_generation():
    out_dir = r"c:\Users\nlm89\source\repos\svt-focus-tuning\cad\radio_adapter"
    bpy.ops.wm.read_factory_settings(use_empty=True)

    corner_segs = 12
    edge_segs = 24
    # Calibrated JVC KW-V830BT front faceplate pocket (179.70 x 99.30 mm, R=1.20 mm)
    cutout_w = 179.70
    cutout_h = 99.30
    cutout_r = 1.20

    # Front 1.00 mm thick inlay lip (Z = 0.00 to Z = -1.00 mm):
    # Symmetric on both sides (5.00 mm left & right -> width = 169.70 mm, X = +-84.85 mm)
    # and symmetric on top & bottom (1.00 mm top & 1.00 mm bottom -> height = 97.30 mm,
    # Y = -48.65 to +48.65 mm, y_offset = 0.00 mm) so top and bottom match each other!
    inlay_w = cutout_w - 2.0 * 5.00  # 169.70 mm (5.00 mm inlay on left & right)
    inlay_h = cutout_h - 2.0 * 1.00  # 97.30 mm  (1.00 mm inlay on top & bottom)
    inlay_y_off = 0.00               # Symmetric top & bottom (Y = -48.65 to +48.65 mm)
    inlay_thick = 1.00               # 1.00 mm thick (Z = 0.00 to -1.00 mm)

    pts_inlay_window = make_rounded_rect_pts(
        inlay_w, inlay_h, cutout_r, y_offset=inlay_y_off, corner_segs=corner_segs, edge_segs=edge_segs
    )
    pts_cutter_front = make_rounded_rect_pts(
        cutout_w, cutout_h, cutout_r, y_offset=0.0, corner_segs=corner_segs, edge_segs=edge_segs
    )
    # Behind Z = -15.5 mm (where the JVC metal chassis sits), the JVC chassis is 178.00 mm wide!
    # Stepping the cutter width down to 178.30 mm (X = +-89.15 mm) behind Z = -17.5 mm lets the
    # side mounting arms hug the 178.00 mm JVC metal chassis tightly!
    pts_cutter_chassis = make_rounded_rect_pts(
        178.30, cutout_h, cutout_r, y_offset=0.0, corner_segs=corner_segs, edge_segs=edge_segs
    )

    # Through-cutter for the 169.70 x 98.30 mm front screen inlay opening
    cutter_obj = make_loft_solid("jvc_inlay_cutter", [
        (pts_inlay_window,   5.0),
        (pts_inlay_window, -95.0),
    ])
    clean_object_mesh(cutter_obj)

    # Rear pocket cutter starting at Z = -1.00 mm (behind the 1.00 mm front inlay lip)
    pocket_cutter_obj = make_loft_solid("jvc_pocket_cutter", [
        (pts_cutter_front,   -inlay_thick),
        (pts_cutter_front,  -15.5),
        (pts_cutter_chassis, -17.5),
        (pts_cutter_chassis, -95.0),
    ])
    clean_object_mesh(pocket_cutter_obj)

    mod_u_cut = cutter_obj.modifiers.new(name="UnionPocketCutter", type='BOOLEAN')
    mod_u_cut.operation = 'UNION'
    mod_u_cut.object = pocket_cutter_obj
    mod_u_cut.solver = 'EXACT'
    bpy.context.view_layer.objects.active = cutter_obj
    bpy.ops.object.modifier_apply(modifier="UnionPocketCutter")
    bpy.data.objects.remove(pocket_cutter_obj, do_unlink=True)
    clean_object_mesh(cutter_obj)

    z_bow_top = 7.60
    z_bow_bottom = 5.00
    z_bow_x = 5.50

    # -------------------------------------------------------------------------
    # 1. Extended Bezel with 3D Console Contour + Pressure-Fit Side Clips
    # -------------------------------------------------------------------------
    base_bezel = make_sloped_contoured_pod(
        "extended_bezel",
        z_depth=10.0,
        z_bow_top=z_bow_top,
        z_bow_bottom=z_bow_bottom,
        z_bow_x=z_bow_x,
        corner_segs=corner_segs,
        edge_segs=edge_segs,
        n_steps=14,
    )
    clean_object_mesh(base_bezel)

    locators = make_contoured_two_step_locators_obj(
        "console_locators",
        z_depth=10.0,
        z_bow_top=z_bow_top,
        z_bow_bottom=z_bow_bottom,
        z_bow_x=z_bow_x,
        recess_depth=14.0,
        boss_depth=4.0,
    )

    mod_loc = base_bezel.modifiers.new(name="UnionLocators", type='BOOLEAN')
    mod_loc.operation = 'UNION'
    mod_loc.object = locators
    mod_loc.solver = 'EXACT'
    bpy.context.view_layer.objects.active = base_bezel
    bpy.ops.object.modifier_apply(modifier="UnionLocators")
    bpy.data.objects.remove(locators, do_unlink=True)

    mod_cut = base_bezel.modifiers.new(name="JVC_Cutout", type='BOOLEAN')
    mod_cut.operation = 'DIFFERENCE'
    mod_cut.object = cutter_obj
    mod_cut.solver = 'EXACT'
    bpy.context.view_layer.objects.active = base_bezel
    bpy.ops.object.modifier_apply(modifier="JVC_Cutout")
    clean_object_mesh(base_bezel)

    label_bezel = make_top_label_cutter("bezel_top_label", z_depth=10.0, deboss_depth=0.50)
    mod_blab = base_bezel.modifiers.new(name="DebossTopLabel", type='BOOLEAN')
    mod_blab.operation = 'DIFFERENCE'
    mod_blab.object = label_bezel
    mod_blab.solver = 'EXACT'
    bpy.context.view_layer.objects.active = base_bezel
    bpy.ops.object.modifier_apply(modifier="DebossTopLabel")
    bpy.data.objects.remove(label_bezel, do_unlink=True)
    clean_object_mesh(base_bezel)

    out_bezel = os.path.join(out_dir, "focus_svt_jvc_kw_v830bt_bezel.stl")
    out_curved = os.path.join(out_dir, "focus_svt_jvc_from_printables_curved.stl")
    bpy.ops.object.select_all(action='DESELECT')
    base_bezel.select_set(True)
    bpy.ops.wm.stl_export(filepath=out_bezel, export_selected_objects=True)
    bpy.ops.wm.stl_export(filepath=out_curved, export_selected_objects=True)
    print("Exported Sleek Contoured Bezel STL to:", out_bezel)

    # -------------------------------------------------------------------------
    # 2. Quick Test Profile Gauge (Full 3D Console Contour + Pressure-Fit Clips)
    # -------------------------------------------------------------------------
    gauge_obj = make_sloped_contoured_pod(
        "profile_gauge",
        z_depth=6.0,
        z_bow_top=z_bow_top,
        z_bow_bottom=z_bow_bottom,
        z_bow_x=z_bow_x,
        corner_segs=corner_segs,
        edge_segs=edge_segs,
        n_steps=10,
    )
    clean_object_mesh(gauge_obj)

    gauge_loc = make_contoured_two_step_locators_obj(
        "gauge_locators",
        z_depth=6.0,
        z_bow_top=z_bow_top,
        z_bow_bottom=z_bow_bottom,
        z_bow_x=z_bow_x,
        recess_depth=10.5,
        boss_depth=3.5,
    )
    mod_gloc = gauge_obj.modifiers.new(name="UnionGaugeLoc", type='BOOLEAN')
    mod_gloc.operation = 'UNION'
    mod_gloc.object = gauge_loc
    mod_gloc.solver = 'EXACT'
    bpy.context.view_layer.objects.active = gauge_obj
    bpy.ops.object.modifier_apply(modifier="UnionGaugeLoc")
    bpy.data.objects.remove(gauge_loc, do_unlink=True)

    mod_gcut = gauge_obj.modifiers.new(name="GaugeCut", type='BOOLEAN')
    mod_gcut.operation = 'DIFFERENCE'
    mod_gcut.object = cutter_obj
    mod_gcut.solver = 'EXACT'
    bpy.context.view_layer.objects.active = gauge_obj
    bpy.ops.object.modifier_apply(modifier="GaugeCut")
    clean_object_mesh(gauge_obj)

    label_gauge = make_top_label_cutter("gauge_top_label", z_depth=6.0, deboss_depth=0.50)
    mod_glab = gauge_obj.modifiers.new(name="DebossGaugeLabel", type='BOOLEAN')
    mod_glab.operation = 'DIFFERENCE'
    mod_glab.object = label_gauge
    mod_glab.solver = 'EXACT'
    bpy.context.view_layer.objects.active = gauge_obj
    bpy.ops.object.modifier_apply(modifier="DebossGaugeLabel")
    bpy.data.objects.remove(label_gauge, do_unlink=True)
    clean_object_mesh(gauge_obj)

    out_gauge = os.path.join(out_dir, "focus_svt_jvc_profile_gauge.stl")
    out_gauge_codex = os.path.join(out_dir, "codex_bezel_concept", "focus_svt_jvc_profile_gauge.stl")
    bpy.ops.object.select_all(action='DESELECT')
    gauge_obj.select_set(True)
    bpy.ops.wm.stl_export(filepath=out_gauge, export_selected_objects=True)
    if os.path.exists(os.path.dirname(out_gauge_codex)):
        bpy.ops.wm.stl_export(filepath=out_gauge_codex, export_selected_objects=True)
    print("Exported Contoured Profile Gauge STL to:", out_gauge)
    bpy.data.objects.remove(gauge_obj, do_unlink=True)

    # -------------------------------------------------------------------------
    # 3. Full Unibody Cage:
    #    - 2-Step Console Shelf with Integrated Pressure-Fit Clips
    #    - Stepped-In Side Arms (178.30 mm inner width) Hugging the 178.00 mm JVC Chassis
    #    - Multi-Row (Upper Y=+22mm, Center Y=0mm, Lower Y=-22mm) ISO M5 Screw Slots
    # -------------------------------------------------------------------------
    cage_obj = make_sloped_contoured_pod(
        "cage_bezel",
        z_depth=10.0,
        z_bow_top=z_bow_top,
        z_bow_bottom=z_bow_bottom,
        z_bow_x=z_bow_x,
        corner_segs=corner_segs,
        edge_segs=edge_segs,
        n_steps=14,
    )
    clean_object_mesh(cage_obj)

    cage_locators = make_contoured_two_step_locators_obj(
        "cage_locators",
        z_depth=10.0,
        z_bow_top=z_bow_top,
        z_bow_bottom=z_bow_bottom,
        z_bow_x=z_bow_x,
        recess_depth=14.0,
        boss_depth=4.0,
    )
    mod_cloc = cage_obj.modifiers.new(name="UnionCageLoc", type='BOOLEAN')
    mod_cloc.operation = 'UNION'
    mod_cloc.object = cage_locators
    mod_cloc.solver = 'EXACT'
    bpy.context.view_layer.objects.active = cage_obj
    bpy.ops.object.modifier_apply(modifier="UnionCageLoc")
    bpy.data.objects.remove(cage_locators, do_unlink=True)

    # Side mounting brackets: 78.0 mm tall (Y = -39.0 to +39.0 mm) with front-to-back depth taper:
    # 187.40 mm (X = +-93.70 mm) at collar down to 181.00 mm (X = +-90.50 mm) at the rear!
    # Hugs the 178.00 mm JVC chassis (X = +-89.15 mm) while locking firmly against dash walls!
    b_depth = 65.0
    b_height = 78.0
    z_start = -15.0
    z_end = z_start - b_depth  # -80.0 mm
    x_inner_overlap = 86.50    # Trimmed to X = +-89.15 mm (178.30 mm) behind Z = -17.5 mm by cutter_obj!
    lead_in = 8.0

    bracket_mesh = bpy.data.meshes.new("side_brackets")
    bracket_obj = bpy.data.objects.new("side_brackets", bracket_mesh)
    bpy.context.collection.objects.link(bracket_obj)

    bm_b = bmesh.new()
    for side in [-1, 1]:
        ya = -b_height / 2.0
        yb = b_height / 2.0
        za = z_end
        zb = z_start + 7.0  # -8.0 mm (ensures solid 5+ mm overlap into bezel pod across curved contour)

        def x_outer_arm_at_z(z_coord):
            t_depth = (z_coord - zb) / (za - zb)
            t_depth = max(0.0, min(1.0, t_depth))
            # Linear taper: 93.70 mm (187.40 mm) at collar (zb) down to 90.50 mm (181.00 mm) at rear (za)
            return 93.70 + (90.50 - 93.70) * t_depth

        poly_yz = [
            (ya + lead_in, za),
            (yb - lead_in, za),
            (yb, za + lead_in),
            (yb, zb),
            (ya, zb),
            (ya, za + lead_in),
        ]
        v_xa = []
        v_xb = []
        for y, z in poly_yz:
            xo = x_outer_arm_at_z(z)
            xa = min(side * x_inner_overlap, side * xo)
            xb = max(side * x_inner_overlap, side * xo)
            v_xa.append(bm_b.verts.new((xa, y, z)))
            v_xb.append(bm_b.verts.new((xb, y, z)))

        k = len(poly_yz)
        for i in range(k):
            nxt = (i + 1) % k
            bm_b.faces.new([v_xa[i], v_xa[nxt], v_xb[nxt], v_xb[i]])
        bm_b.faces.new(list(reversed(v_xa)))
        bm_b.faces.new(v_xb)

    bmesh.ops.triangulate(bm_b, faces=bm_b.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_b.normal_update()
    bm_b.to_mesh(bracket_mesh)
    bm_b.free()
    clean_object_mesh(bracket_obj)

    # Multi-Row Continuous ISO M5 Slot Array:
    # Continuous 54.0 mm slots spanning Z = -19.0 mm to Z = -73.0 mm.
    # Eliminates any dividing bridge so 45 mm spacing, 4-hole grids, diagonal pairs,
    # or any forward/rear depth positioning bolt straight through with zero obstruction!
    # - Lower Row: centered at Y = -26.00 mm (6.50 mm tall slot: covers ~20-27 mm from bottom)
    # - Upper Row: centered at Y = +19.00 mm (6.50 mm tall slot: exactly 45.0 mm above lower row!)
    # - Center Row: centered at Y = -3.50 mm (5.50 mm tall slot: for middle/single-row mounting)
    slot_cutter_mesh = bpy.data.meshes.new("slot_cutter")
    slot_cutter_obj = bpy.data.objects.new("slot_cutter", slot_cutter_mesh)
    bpy.context.collection.objects.link(slot_cutter_obj)

    bm_s = bmesh.new()
    y_rows = [
        ( 19.00, 3.25),  # Upper row (45.0 mm center-to-center above lower row)
        ( -3.50, 2.75),  # Middle row
        (-26.00, 3.25),  # Lower row (~22-26 mm up from bottom)
    ]
    z_s_min = -73.0
    z_s_max = -19.0
    for y_center, y_half in y_rows:
        y_s_min = y_center - y_half
        y_s_max = y_center + y_half
        v_c = [
            bm_s.verts.new((-105.0, y_s_min, z_s_min)),
            bm_s.verts.new(( 105.0, y_s_min, z_s_min)),
            bm_s.verts.new(( 105.0, y_s_max, z_s_min)),
            bm_s.verts.new((-105.0, y_s_max, z_s_min)),
            bm_s.verts.new((-105.0, y_s_min, z_s_max)),
            bm_s.verts.new(( 105.0, y_s_min, z_s_max)),
            bm_s.verts.new(( 105.0, y_s_max, z_s_max)),
            bm_s.verts.new((-105.0, y_s_max, z_s_max)),
        ]
        bm_s.faces.new([v_c[0], v_c[1], v_c[2], v_c[3]])
        bm_s.faces.new([v_c[4], v_c[7], v_c[6], v_c[5]])
        bm_s.faces.new([v_c[0], v_c[4], v_c[5], v_c[1]])
        bm_s.faces.new([v_c[2], v_c[6], v_c[7], v_c[3]])
        bm_s.faces.new([v_c[0], v_c[3], v_c[7], v_c[4]])
        bm_s.faces.new([v_c[1], v_c[5], v_c[6], v_c[2]])

    bmesh.ops.triangulate(bm_s, faces=bm_s.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_s.normal_update()
    bm_s.to_mesh(slot_cutter_mesh)
    bm_s.free()
    clean_object_mesh(slot_cutter_obj)

    mod_ub = cage_obj.modifiers.new(name="UnionBrackets", type='BOOLEAN')
    mod_ub.operation = 'UNION'
    mod_ub.object = bracket_obj
    mod_ub.solver = 'EXACT'
    bpy.context.view_layer.objects.active = cage_obj
    bpy.ops.object.modifier_apply(modifier="UnionBrackets")
    bpy.data.objects.remove(bracket_obj, do_unlink=True)
    clean_object_mesh(cage_obj)

    mod_slot = cage_obj.modifiers.new(name="SlotCut", type='BOOLEAN')
    mod_slot.operation = 'DIFFERENCE'
    mod_slot.object = slot_cutter_obj
    mod_slot.solver = 'EXACT'
    bpy.context.view_layer.objects.active = cage_obj
    bpy.ops.object.modifier_apply(modifier="SlotCut")
    bpy.data.objects.remove(slot_cutter_obj, do_unlink=True)
    clean_object_mesh(cage_obj)

    mod_ccut = cage_obj.modifiers.new(name="CageCut", type='BOOLEAN')
    mod_ccut.operation = 'DIFFERENCE'
    mod_ccut.object = cutter_obj
    mod_ccut.solver = 'EXACT'
    bpy.context.view_layer.objects.active = cage_obj
    bpy.ops.object.modifier_apply(modifier="CageCut")
    clean_object_mesh(cage_obj)

    label_cage = make_top_label_cutter("cage_top_label", z_depth=10.0, deboss_depth=0.50)
    mod_clab = cage_obj.modifiers.new(name="DebossCageLabel", type='BOOLEAN')
    mod_clab.operation = 'DIFFERENCE'
    mod_clab.object = label_cage
    mod_clab.solver = 'EXACT'
    bpy.context.view_layer.objects.active = cage_obj
    bpy.ops.object.modifier_apply(modifier="DebossCageLabel")
    bpy.data.objects.remove(label_cage, do_unlink=True)
    clean_object_mesh(cage_obj)

    out_cage = os.path.join(out_dir, "focus_svt_jvc_kw_v830bt_unibody_cage.stl")
    bpy.ops.object.select_all(action='DESELECT')
    cage_obj.select_set(True)
    bpy.ops.wm.stl_export(filepath=out_cage, export_selected_objects=True)
    print("Exported Sleek Contoured Unibody Cage STL to:", out_cage)

    bpy.data.objects.remove(cutter_obj, do_unlink=True)

    # -------------------------------------------------------------------------
    # 4. Rapid Cage Arm Depth Taper Test Slip (20-25 min print):
    #    Tests the exact 187.40 mm -> 181.00 mm taper & friction fit in the car
    # -------------------------------------------------------------------------
    h_arm = 24.0
    y_min, y_max = -h_arm / 2.0, h_arm / 2.0
    z_front = 0.0
    z_collar = -8.0
    z_rear = -80.0
    lead_in = 6.0
    x_flange = 97.75      # 195.50 mm outer stop flange
    x_collar = 93.70      # 187.40 mm at collar
    x_tip = 90.50         # 181.00 mm at rear tip
    x_inner = 89.15       # 178.30 mm inner cavity (rigid radio simulation)

    def x_slip_outer(z):
        if z >= z_collar:
            return x_flange
        t = (z - z_collar) / (z_rear - z_collar)
        t = max(0.0, min(1.0, t))
        xo = x_collar + (x_tip - x_collar) * t
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            xo -= 1.20 * c_frac
        return xo

    slip_mesh = bpy.data.meshes.new("cage_test_slip")
    slip_obj = bpy.data.objects.new("cage_test_slip", slip_mesh)
    bpy.context.collection.objects.link(slip_obj)

    bm_slip = bmesh.new()
    z_slices = [
        z_front,
        z_collar + 0.01,
        z_collar,
        -18.0, -28.0, -38.0, -48.0, -58.0, -68.0,
        z_rear + lead_in,
        z_rear,
    ]
    rings = []
    for z in z_slices:
        xo = x_slip_outer(z)
        yo_max = y_max
        yo_min = y_min
        if z < (z_rear + lead_in):
            c_frac = (z_rear + lead_in - z) / lead_in
            yo_max -= 1.00 * c_frac
            yo_min += 1.00 * c_frac
        v0 = bm_slip.verts.new((-xo, yo_min, z))
        v1 = bm_slip.verts.new(( xo, yo_min, z))
        v2 = bm_slip.verts.new(( xo, yo_max, z))
        v3 = bm_slip.verts.new((-xo, yo_max, z))
        rings.append([v0, v1, v2, v3])

    for i in range(len(rings) - 1):
        r1, r2 = rings[i], rings[i + 1]
        for j in range(4):
            nxt = (j + 1) % 4
            bm_slip.faces.new([r1[j], r1[nxt], r2[nxt], r2[j]])
    bm_slip.faces.new(list(reversed(rings[0])))
    bm_slip.faces.new(rings[-1])

    bmesh.ops.triangulate(bm_slip, faces=bm_slip.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_slip.normal_update()
    bm_slip.to_mesh(slip_mesh)
    bm_slip.free()
    clean_object_mesh(slip_obj)

    # Cut hollow center (leaving front bridge and rear tie-bar)
    cut_mesh = bpy.data.meshes.new("slip_cutter")
    cut_obj = bpy.data.objects.new("slip_cutter", cut_mesh)
    bpy.context.collection.objects.link(cut_obj)
    bm_sc = bmesh.new()
    zc_front = z_collar - 0.01
    zc_rear = z_rear + 8.00
    yc_min = y_min - 2.0
    yc_max = y_max + 2.0
    vc = [
        bm_sc.verts.new((-x_inner, yc_min, zc_rear)),
        bm_sc.verts.new(( x_inner, yc_min, zc_rear)),
        bm_sc.verts.new(( x_inner, yc_max, zc_rear)),
        bm_sc.verts.new((-x_inner, yc_max, zc_rear)),
        bm_sc.verts.new((-x_inner, yc_min, zc_front)),
        bm_sc.verts.new(( x_inner, yc_min, zc_front)),
        bm_sc.verts.new(( x_inner, yc_max, zc_front)),
        bm_sc.verts.new((-x_inner, yc_max, zc_front)),
    ]
    bm_sc.faces.new([vc[0], vc[1], vc[2], vc[3]])
    bm_sc.faces.new([vc[4], vc[7], vc[6], vc[5]])
    bm_sc.faces.new([vc[0], vc[4], vc[5], vc[1]])
    bm_sc.faces.new([vc[2], vc[6], vc[7], vc[3]])
    bm_sc.faces.new([vc[0], vc[3], vc[7], vc[4]])
    bm_sc.faces.new([vc[1], vc[5], vc[6], vc[2]])
    bmesh.ops.triangulate(bm_sc, faces=bm_sc.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_sc.normal_update()
    bm_sc.to_mesh(cut_mesh)
    bm_sc.free()
    clean_object_mesh(cut_obj)

    mod_scut = slip_obj.modifiers.new(name="SlipCut", type='BOOLEAN')
    mod_scut.operation = 'DIFFERENCE'
    mod_scut.object = cut_obj
    mod_scut.solver = 'EXACT'
    bpy.context.view_layer.objects.active = slip_obj
    bpy.ops.object.modifier_apply(modifier="SlipCut")
    bpy.data.objects.remove(cut_obj, do_unlink=True)
    clean_object_mesh(slip_obj)

    # Deboss depth tick marks on top rim (every 10mm from collar)
    notch_mesh = bpy.data.meshes.new("slip_notches")
    notch_obj = bpy.data.objects.new("slip_notches", notch_mesh)
    bpy.context.collection.objects.link(notch_obj)
    bm_sn = bmesh.new()
    for d in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]:
        z_mark = z_collar - d
        for side in [-1, 1]:
            x_m = side * (x_slip_outer(z_mark) + 1.0)
            x_in = side * (x_inner - 1.0)
            xa = min(x_m, x_in)
            xb = max(x_m, x_in)
            w_z = 0.80
            d_y = 0.60
            vn = [
                bm_sn.verts.new((xa, y_max - d_y, z_mark - w_z / 2)),
                bm_sn.verts.new((xb, y_max - d_y, z_mark - w_z / 2)),
                bm_sn.verts.new((xb, y_max + 1.0, z_mark - w_z / 2)),
                bm_sn.verts.new((xa, y_max + 1.0, z_mark - w_z / 2)),
                bm_sn.verts.new((xa, y_max - d_y, z_mark + w_z / 2)),
                bm_sn.verts.new((xb, y_max - d_y, z_mark + w_z / 2)),
                bm_sn.verts.new((xb, y_max + 1.0, z_mark + w_z / 2)),
                bm_sn.verts.new((xa, y_max + 1.0, z_mark + w_z / 2)),
            ]
            bm_sn.faces.new([vn[0], vn[1], vn[2], vn[3]])
            bm_sn.faces.new([vn[4], vn[7], vn[6], vn[5]])
            bm_sn.faces.new([vn[0], vn[4], vn[5], vn[1]])
            bm_sn.faces.new([vn[2], vn[6], vn[7], vn[3]])
            bm_sn.faces.new([vn[0], vn[3], vn[7], vn[4]])
            bm_sn.faces.new([vn[1], vn[5], vn[6], vn[2]])
    bmesh.ops.triangulate(bm_sn, faces=bm_sn.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm_sn.normal_update()
    bm_sn.to_mesh(notch_mesh)
    bm_sn.free()
    clean_object_mesh(notch_obj)

    mod_snotches = slip_obj.modifiers.new(name="SlipNotches", type='BOOLEAN')
    mod_snotches.operation = 'DIFFERENCE'
    mod_snotches.object = notch_obj
    mod_snotches.solver = 'EXACT'
    bpy.context.view_layer.objects.active = slip_obj
    bpy.ops.object.modifier_apply(modifier="SlipNotches")
    bpy.data.objects.remove(notch_obj, do_unlink=True)
    clean_object_mesh(slip_obj)

    # Deboss front label '▲ TOP · 187.4mm SLIP ▲'
    font_curve = bpy.data.curves.new(type="FONT", name="label_slip_curve")
    font_curve.body = "▲ TOP · 187.4mm SLIP ▲"
    font_curve.size = 5.2
    font_curve.extrude = 0.60
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'
    label_slip = bpy.data.objects.new("label_slip_obj", font_curve)
    bpy.context.collection.objects.link(label_slip)
    label_slip.location = (0.0, 0.0, -0.30)
    bpy.ops.object.select_all(action='DESELECT')
    label_slip.select_set(True)
    bpy.context.view_layer.objects.active = label_slip
    bpy.ops.object.convert(target='MESH')
    clean_object_mesh(label_slip)

    mod_slab = slip_obj.modifiers.new(name="DebossSlipLabel", type='BOOLEAN')
    mod_slab.operation = 'DIFFERENCE'
    mod_slab.object = label_slip
    mod_slab.solver = 'EXACT'
    bpy.context.view_layer.objects.active = slip_obj
    bpy.ops.object.modifier_apply(modifier="DebossSlipLabel")
    bpy.data.objects.remove(label_slip, do_unlink=True)
    clean_object_mesh(slip_obj)

    out_slip = os.path.join(out_dir, "focus_svt_cage_arm_test_slip.stl")
    bpy.ops.object.select_all(action='DESELECT')
    slip_obj.select_set(True)
    bpy.ops.wm.stl_export(filepath=out_slip, export_selected_objects=True)
    print("Exported Cage Arm Depth Taper Test Slip STL to:", out_slip)

    # Pre-oriented Flat on Bed (24 mm tall, 85 layers, ~18 min print time):
    out_slip_flat = os.path.join(out_dir, "focus_svt_cage_arm_test_slip_flat.stl")
    slip_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    slip_obj.location = (0.0, -80.0, 12.0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    bpy.ops.wm.stl_export(filepath=out_slip_flat, export_selected_objects=True)
    print("Exported Pre-Oriented Flat Test Slip STL to:", out_slip_flat)

    print("\nALL SLEEK CONTOURED EXTENDED BEZEL STLS GENERATED SUCCESSFULLY!")


if __name__ == "__main__":
    run_generation()
