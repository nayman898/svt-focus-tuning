"""Render and measure the STL at the throttle/IACV junction."""

import argparse
import json
import os
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh


HERE = Path(__file__).resolve().parent
NECK = (np.array([132, -94, -15]), np.array([254, 45, 97]))
VIEWS = {"top_radiator": (0.48, -1, 1.5), "underside_radiator": (0.51, -1, -0.4)}


def unit(vector):
    return np.asarray(vector) / np.linalg.norm(vector)


def neck_faces(mesh):
    return np.all((mesh.triangles_center >= NECK[0]) & (mesh.triangles_center <= NECK[1]), axis=1)


def shot(mesh, mask, camera, shade_overhang, label):
    width, height = 1080, 740
    view = unit(camera)
    right = unit(np.cross([0, 0, 1], view))
    up = np.cross(view, right)
    vertices = mesh.vertices - [193, -25, 43]
    camera_points = np.stack((vertices @ right, vertices @ up), axis=1)
    pixels = camera_points * [5, -5] + [width / 2, height / 2]
    faces = mesh.faces[mask]
    depth = ((mesh.triangles_center[mask] - [193, -25, 43]) @ view)
    normals = mesh.face_normals[mask]
    color = np.tile([108, 155, 184], (len(faces), 1))
    if shade_overhang:
        color[normals[:, 0] < -np.sqrt(0.5)] = (224, 106, 76)
    light = unit(view + 0.65 * up - 0.22 * right)
    color = np.clip(color * (0.42 + 0.58 * np.maximum(normals @ light, 0))[:, None], 0, 255).astype(int)

    canvas = Image.new("RGB", (width, height), "#eef2f5")
    draw = ImageDraw.Draw(canvas)
    for index in np.argsort(depth):
        draw.polygon([tuple(pixels[j]) for j in faces[index]], fill=tuple(color[index]))
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((29, 24), label, fill="#21313e", font=font)
    if shade_overhang:
        draw.text((29, height - 38), "Orange faces exceed 45° from vertical in the right-half print orientation.",
                  fill="#572d25", font=ImageFont.truetype("arial.ttf", 17))
    return canvas


def analyze(model, label):
    mesh = trimesh.load_mesh(model)
    mask = neck_faces(mesh)
    normals = mesh.face_normals
    areas = mesh.area_faces
    neck_areas = {}
    for angle in (45, 55, 65, 80):
        off = normals[:, 0] < -np.sin(np.deg2rad(angle))
        neck_areas[str(angle)] = round(float(sum(areas[mask & off])), 2)
    result = {"neck_roi_mm": [i.tolist() for i in NECK],
              "build_axis_in_assembly_coordinates": [1, 0, 0],
              "neck_total_surface_area_mm2": round(float(sum(areas[mask])), 2),
              "neck_downward_face_area_by_angle_from_vertical_mm2": neck_areas,
              "contains_interior_and_exterior_surfaces": True}
    for key, vector in VIEWS.items():
        shade_overhang = key == "underside_radiator"
        shot(mesh, mask, vector, shade_overhang, f"{label} | {key.replace('_', ' ')}").save(HERE / f"{label}_{key}.png")
    (HERE / f"{label}_overhang.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("model", type=Path)
    cli.add_argument("label")
    args = cli.parse_args()
    analyze(args.model, args.label)
