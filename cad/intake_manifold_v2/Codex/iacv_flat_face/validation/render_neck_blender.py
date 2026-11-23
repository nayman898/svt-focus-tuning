"""Render the actual manifold STL from the throttle and runner sides."""

from pathlib import Path
import sys

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent


def render(stl, label):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.wm.stl_import(filepath=str(stl))
    model = bpy.context.selected_objects[0]
    blue = bpy.data.materials.new("Intake shell")
    blue.diffuse_color = (0.17, 0.40, 0.55, 1)
    red = bpy.data.materials.new("Downward faces")
    red.diffuse_color = (0.75, 0.22, 0.13, 1)
    model.data.materials.append(blue)
    model.data.materials.append(red)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1220
    scene.render.resolution_y = 920
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.background_type = "WORLD"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.world.color = (0.74, 0.78, 0.82)
    scene.display.render_aa = "8"
    scene.view_settings.view_transform = "Standard"
    camera = bpy.data.objects.new("Neck orthographic", bpy.data.cameras.new("Neck camera"))
    scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 205
    camera.data.clip_end = 2000
    scene.camera = camera
    for view, direction, target, use_overhang in (
        ("throttle", (0.48, -1, 1.5), (193, -31, 43), False),
        ("flange_back", (0.66, -0.68, 0.09), (220, -37, 33), False),
        ("build_underside", (-0.48, -1, 0.30), (178, -30, 48), True),
    ):
        camera.data.ortho_scale = 162 if view == "flange_back" else 205
        center = Vector(target)
        camera.location = center + 360 * Vector(direction).normalized()
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        if use_overhang:
            for polygon in model.data.polygons:
                polygon.material_index = int(polygon.normal.x < -0.707107)
        scene.render.filepath = str(HERE / f"{label}_{view}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    path, label = sys.argv[sys.argv.index("--") + 1:]
    render(Path(path).resolve(), label)
