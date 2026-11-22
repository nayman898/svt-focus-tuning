#!/usr/bin/env python3
"""
Update the ElegooSlicer .3mf project in cad/intake_manifold to:
  1. Refresh embedded STL meshes (split halves + fit gauges, including IACV gauge).
  2. Configure PLA Pro demo process and filament presets across all 4 AMS slots.
  3. Apply build-plate-only tree supports to the split manifold halves while
     keeping the 3 fitment gauges support-free at 0.20 mm layer height.
"""

from __future__ import annotations

import copy
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parent
STL_DIR = ROOT / "stl"
TARGET_3MF = ROOT / "svt_intake_manifold_PLAPro_Demo_CC2.3mf"
PROCESS_JSON = ROOT / "profiles" / "process" / "PLAPro_0.4_0.24_SVTManifold_Demo_TreeSupport_CC2.json"
FILAMENT_JSON = ROOT / "profiles" / "filament" / "PLAPro_SVTManifold_Demo_CC2.json"


def build_object_model_xml(obj_id: int, uuid_str: str, stl_path: Path) -> bytes:
    """Create a 3MF sub-object .model XML centered at (0, 0, 0) matching ElegooSlicer layout."""
    mesh = trimesh.load(stl_path, process=False)
    # Center mesh about its bounding-box midpoint so build transform z = height/2 sits at Z=0
    center = 0.5 * (mesh.bounds[0] + mesh.bounds[1])
    mesh.apply_translation(-center)

    verts_xml = "\n".join(
        f'     <vertex x="{v[0]:.7f}" y="{v[1]:.7f}" z="{v[2]:.7f}"/>' for v in mesh.vertices
    )
    tris_xml = "\n".join(
        f'     <triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in mesh.faces
    )
    xml_text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
        'requiredextensions="p">\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        ' <resources>\n'
        f'  <object id="{obj_id}" p:UUID="{uuid_str}" type="model">\n'
        '   <mesh>\n'
        '    <vertices>\n'
        f'{verts_xml}\n'
        '    </vertices>\n'
        '    <triangles>\n'
        f'{tris_xml}\n'
        '    </triangles>\n'
        '   </mesh>\n'
        '  </object>\n'
        ' </resources>\n'
        '</model>\n'
    )
    return xml_text.encode("utf-8")


def update_3mf() -> None:
    proc = json.loads(PROCESS_JSON.read_text(encoding="utf-8"))
    fil = json.loads(FILAMENT_JSON.read_text(encoding="utf-8"))

    with zipfile.ZipFile(TARGET_3MF, "r") as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}

    # 1) Refresh split manifold STL meshes inside 3D/Objects/ (sub-object IDs match 3dmodel.model components)
    entries["3D/Objects/svt_intake_manifold_split_left_print_oriented.stl_8.model"] = build_object_model_xml(
        1, "00080000-81cb-4c03-9d28-80fed5dfa1dc", STL_DIR / "svt_intake_manifold_split_left_print_oriented.stl"
    )
    entries["3D/Objects/svt_intake_manifold_split_right_print_oriented.stl_9.model"] = build_object_model_xml(
        5, "00090000-81cb-4c03-9d28-80fed5dfa1dc", STL_DIR / "svt_intake_manifold_split_right_print_oriented.stl"
    )
    entries["3D/Objects/svt_runner_boot_fit_gauge.stl_10.model"] = build_object_model_xml(
        9, "000a0000-81cb-4c03-9d28-80fed5dfa1dc", STL_DIR / "svt_runner_boot_fit_gauge.stl"
    )
    entries["3D/Objects/svt_tb_flange_fit_gauge.stl_11.model"] = build_object_model_xml(
        7, "000b0000-81cb-4c03-9d28-80fed5dfa1dc", STL_DIR / "svt_tb_flange_fit_gauge.stl"
    )

    # Add IACV fit gauge (obj 18 / sub 17) and alignment dowel pins (obj 20 / sub 19) to Plate 3
    extra_plate3_parts = [
        {
            "obj_id": "18",
            "sub_id": "17",
            "stl_name": "svt_iacv_flange_fit_gauge.stl",
            "model_path": "3D/Objects/svt_iacv_flange_fit_gauge.stl_12.model",
            "uuid_base": "0018",
            "x": "824",
            "y": "128",
            "z": "2",
            "identify_id": "560",
        },
        {
            "obj_id": "20",
            "sub_id": "19",
            "stl_name": "svt_alignment_dowel_pins.stl",
            "model_path": "3D/Objects/svt_alignment_dowel_pins.stl_14.model",
            "uuid_base": "0020",
            "x": "660",
            "y": "128",
            "z": "2.75",
            "identify_id": "561",
        },
    ]

    for part_spec in extra_plate3_parts:
        entries[part_spec["model_path"]] = build_object_model_xml(
            int(part_spec["sub_id"]),
            f"{part_spec['uuid_base']}0000-81cb-4c03-9d28-80fed5dfa1dc",
            STL_DIR / part_spec["stl_name"],
        )

    ns_core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ns_p = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
    ns_b = "http://schemas.bambulab.com/package/2021"
    ET.register_namespace("", ns_core)
    ET.register_namespace("p", ns_p)
    ET.register_namespace("BambuStudio", ns_b)
    model_root = ET.fromstring(entries["3D/3dmodel.model"])
    res_el = model_root.find(f"{{{ns_core}}}resources")
    build_el = model_root.find(f"{{{ns_core}}}build")
    extra_ids = {p["obj_id"] for p in extra_plate3_parts}
    for el in list(res_el.findall(f"{{{ns_core}}}object")):
        if el.attrib.get("id") in extra_ids:
            res_el.remove(el)
    for el in list(build_el.findall(f"{{{ns_core}}}item")):
        if el.attrib.get("objectid") in extra_ids:
            build_el.remove(el)
    for part_spec in extra_plate3_parts:
        oid = part_spec["obj_id"]
        ub = part_spec["uuid_base"]
        obj_el = ET.SubElement(
            res_el,
            f"{{{ns_core}}}object",
            {"id": oid, f"{{{ns_p}}}UUID": f"0000{ub}-61cb-4c03-9d28-80fed5dfa1dc", "type": "model"},
        )
        comps = ET.SubElement(obj_el, f"{{{ns_core}}}components")
        ET.SubElement(
            comps,
            f"{{{ns_core}}}component",
            {
                f"{{{ns_p}}}path": f"/{part_spec['model_path']}",
                "objectid": part_spec["sub_id"],
                f"{{{ns_p}}}UUID": f"{ub}0000-b206-40ff-9872-83e8017abed1",
                "transform": "1 0 0 0 1 0 0 0 1 0 0 0",
            },
        )
        ET.SubElement(
            build_el,
            f"{{{ns_core}}}item",
            {
                "objectid": oid,
                f"{{{ns_p}}}UUID": f"0000{ub}-b1ec-4553-aec9-835e5b724bb4",
                "transform": f"1 0 0 0 1 0 0 0 1 {part_spec['x']} {part_spec['y']} {part_spec['z']}",
                "printable": "1",
                "auto_drop": "1",
            },
        )
    entries["3D/3dmodel.model"] = ET.tostring(model_root, encoding="utf-8", xml_declaration=True)

    # Register added external .model files in 3D/_rels/3dmodel.model.rels (required by 3MF Production spec)
    ns_rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    ET.register_namespace("", ns_rel)
    rels_root = ET.fromstring(entries["3D/_rels/3dmodel.model.rels"])
    existing_targets = {r.attrib.get("Target") for r in rels_root.findall(f"{{{ns_rel}}}Relationship")}
    rel_idx = len(list(rels_root)) + 1
    for part_spec in extra_plate3_parts:
        target_path = f"/{part_spec['model_path']}"
        if target_path not in existing_targets:
            ET.SubElement(
                rels_root,
                f"{{{ns_rel}}}Relationship",
                {
                    "Target": target_path,
                    "Id": f"rel-{rel_idx}",
                    "Type": "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel",
                },
            )
            rel_idx += 1
    entries["3D/_rels/3dmodel.model.rels"] = ET.tostring(rels_root, encoding="utf-8", xml_declaration=True)

    # 2) Update Metadata/project_settings.config
    ps = json.loads(entries["Metadata/project_settings.config"].decode("utf-8"))
    non_filament_4lists = {
        "bed_exclude_area",
        "bed_texture_area",
        "printable_area",
        "print_compatible_printers",
        "compatible_printers",
    }
    for k, v in list(ps.items()):
        if isinstance(v, list) and len(v) == 4 and k not in non_filament_4lists:
            ps[k] = [copy.deepcopy(v[1]) for _ in range(4)]

    proc_skip = {"from", "inherits", "is_custom_defined", "name", "version"}
    proc_diff_keys = []
    for k, v in proc.items():
        if k in proc_skip:
            continue
        ps[k] = v
        if k != "print_settings_id":
            proc_diff_keys.append(k)

    fil_skip = {"from", "inherits", "is_custom_defined", "name", "version", "compatible_printers"}
    fil_diff_keys = []
    for k, v in fil.items():
        if k in fil_skip:
            continue
        if isinstance(v, list):
            if len(v) == 1:
                ps[k] = [copy.deepcopy(v[0]) for _ in range(4)]
            elif len(v) == 4:
                ps[k] = copy.deepcopy(v)
        if k != "filament_settings_id":
            fil_diff_keys.append(k)

    ps["filament_settings_id"] = [fil["name"]] * 4
    ps["filament_ids"] = ["EPLAB00"] * 4
    ps["filament_notes"] = [
        "PLA Pro (Slot 1)",
        "PLA Pro (Slot 2 - Active)",
        "PLA Pro (Slot 3)",
        "PLA Pro (Slot 4)",
    ]
    ps["filament_colour"] = ["#000000"] * 4
    ps["filament_multi_colors"] = ["#000000"] * 4
    ps["flush_volumes_matrix"] = ["0"] * 16
    ps["curr_bed_type"] = "Textured PEI Plate"
    ps["inherits_group"] = [
        proc["inherits"],
        fil["inherits"],
        fil["inherits"],
        fil["inherits"],
        fil["inherits"],
        ps.get("inherits_group", ["", "", "", "", "", "Elegoo Centauri Carbon 2 0.4 nozzle"])[5],
    ]
    fil_diff_str = ";".join(sorted(set(fil_diff_keys)))
    mach_diff_str = ps.get("different_settings_to_system", ["", "", "", "", "", ""])[5]
    ps["different_settings_to_system"] = [
        ";".join(sorted(set(proc_diff_keys))),
        fil_diff_str,
        fil_diff_str,
        fil_diff_str,
        fil_diff_str,
        mach_diff_str,
    ]
    entries["Metadata/project_settings.config"] = (json.dumps(ps, indent=4) + "\n").encode("utf-8")

    # 3) Update Metadata/model_settings.config: unify all parts onto extruder 2 (PLA Pro),
    #    ensure IACV fit gauge is on Plate 3, and apply support-free 0.20 mm overrides on gauges.
    cfg = ET.fromstring(entries["Metadata/model_settings.config"])
    gauge_names = {
        "svt_runner_boot_fit_gauge.stl",
        "svt_tb_flange_fit_gauge.stl",
        "svt_iacv_flange_fit_gauge.stl",
        "svt_alignment_dowel_pins.stl",
    }

    def set_meta(elem: ET.Element, key: str, value: str) -> None:
        for m in elem.findall("metadata"):
            if m.attrib.get("key") == key:
                m.attrib["value"] = str(value)
                return
        ET.SubElement(elem, "metadata", key=key, value=str(value))

    for o in list(cfg.findall("object")):
        if o.attrib.get("id") in extra_ids:
            cfg.remove(o)
    for plate in cfg.findall("plate"):
        for mi in list(plate.findall("model_instance")):
            if any(m.attrib.get("key") == "object_id" and m.attrib.get("value") in extra_ids for m in mi.findall("metadata")):
                plate.remove(mi)
    asm = cfg.find("assemble")
    if asm is not None:
        for ai in list(asm.findall("assemble_item")):
            if ai.attrib.get("object_id") in extra_ids:
                asm.remove(ai)

    for part_spec in extra_plate3_parts:
        oid = part_spec["obj_id"]
        obj_cfg = ET.SubElement(cfg, "object", id=oid)
        set_meta(obj_cfg, "name", part_spec["stl_name"])
        set_meta(obj_cfg, "extruder", "2")
        sub_part = ET.SubElement(obj_cfg, "part", id=part_spec["sub_id"], subtype="normal_part")
        set_meta(sub_part, "name", part_spec["stl_name"])
        set_meta(sub_part, "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
        set_meta(sub_part, "source_file", part_spec["stl_name"])
        set_meta(sub_part, "source_object_id", "0")
        set_meta(sub_part, "source_volume_id", "0")
        set_meta(sub_part, "source_offset_x", "0")
        set_meta(sub_part, "source_offset_y", "0")
        set_meta(sub_part, "source_offset_z", part_spec["z"])

        for plate in cfg.findall("plate"):
            pid = next((m.attrib.get("value") for m in plate.findall("metadata") if m.attrib.get("key") == "plater_id"), None)
            if pid == "3":
                mi = ET.SubElement(plate, "model_instance")
                set_meta(mi, "object_id", oid)
                set_meta(mi, "instance_id", "0")
                set_meta(mi, "identify_id", part_spec["identify_id"])

        asm = cfg.find("assemble")
        if asm is not None:
            ET.SubElement(
                asm,
                "assemble_item",
                {"object_id": oid, "instance_id": "0", "transform": f"1 0 0 0 1 0 0 0 1 0 0 {part_spec['z']}", "offset": "0 0 0"},
            )

    for obj in cfg.findall("object"):
        obj_name = ""
        for m in obj.findall("metadata"):
            if m.attrib.get("key") == "name":
                obj_name = m.attrib.get("value", "")
        set_meta(obj, "extruder", "2")
        for part in obj.findall("part"):
            set_meta(part, "extruder", "2")
        if obj_name in gauge_names:
            set_meta(obj, "enable_support", "0")
            set_meta(obj, "brim_type", "no_brim")
            set_meta(obj, "brim_width", "0")
            set_meta(obj, "layer_height", "0.20")

    entries["Metadata/model_settings.config"] = ET.tostring(
        cfg, encoding="utf-8", xml_declaration=True
    )

    tmp_3mf = ROOT / "_tmp_updated.3mf"
    with zipfile.ZipFile(tmp_3mf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    shutil.move(str(tmp_3mf), str(TARGET_3MF))
    print(f"Updated {TARGET_3MF.name} with latest STLs and PLA Pro presets")


if __name__ == "__main__":
    update_3mf()
