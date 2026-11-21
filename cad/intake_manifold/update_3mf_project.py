#!/usr/bin/env python3
"""
Update the ElegooSlicer .3mf project in cad/intake_manifold to use the
PLA Pro demo process and filament presets (and build-plate-only tree supports
for the manifold halves while keeping fitment gauges support-free).
"""

from __future__ import annotations

import copy
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET_3MF = ROOT / "svt_intake_manifold_PLAPro_Demo_CC2.3mf"
PROCESS_JSON = ROOT / "profiles" / "process" / "PLAPro_0.4_0.24_SVTManifold_Demo_TreeSupport_CC2.json"
FILAMENT_JSON = ROOT / "profiles" / "filament" / "PLAPro_SVTManifold_Demo_CC2.json"


def update_3mf() -> None:
    proc = json.loads(PROCESS_JSON.read_text(encoding="utf-8"))
    fil = json.loads(FILAMENT_JSON.read_text(encoding="utf-8"))

    with zipfile.ZipFile(TARGET_3MF, "r") as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}

    # 1) Update Metadata/project_settings.config
    ps = json.loads(entries["Metadata/project_settings.config"].decode("utf-8"))

    # Clone slot 2 (clean PLA base) across all 4 filament slots so slot 1 has zero leftover ASA settings
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

    # 2) Update Metadata/model_settings.config: unify all parts onto extruder 2 (PLA Pro)
    #    and disable supports/brim + set 0.20mm layer height on fitment gauges.
    cfg = ET.fromstring(entries["Metadata/model_settings.config"])
    gauge_names = {"svt_runner_boot_fit_gauge.stl", "svt_tb_flange_fit_gauge.stl"}

    def set_meta(elem: ET.Element, key: str, value: str) -> None:
        for m in elem.findall("metadata"):
            if m.attrib.get("key") == key:
                m.attrib["value"] = str(value)
                return
        ET.SubElement(elem, "metadata", key=key, value=str(value))

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

    # Write updated copy back in-place to the canonical PLA Pro demo .3mf
    tmp_3mf = ROOT / "_tmp_updated.3mf"
    with zipfile.ZipFile(tmp_3mf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    shutil.move(str(tmp_3mf), str(TARGET_3MF))
    print(f"Updated {TARGET_3MF.name}")


if __name__ == "__main__":
    update_3mf()
