"""Run an offline geometry-only CC2 toolpath check using the upstream Orca presets."""

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory, gettempdir
from urllib.parse import quote
from urllib.request import urlopen
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "airflow_regression"))
from local_job import one_job


PRESETS = "https://raw.githubusercontent.com/OrcaSlicer/OrcaSlicer/main/resources/profiles/"


def fetch(path):
    with urlopen(PRESETS + quote(path), timeout=12) as response:
        return json.load(response)


def slice_check(model, label):
    exe = Path(os.environ["ProgramFiles"]) / "OrcaSlicer/orca-slicer.exe"
    index = fetch("Elegoo.json")
    catalog = {row["name"]: row["sub_path"] for group in ("machine_list", "process_list", "filament_list")
               for row in index[group]}

    def preset(name):
        data = fetch("Elegoo/" + catalog[name])
        parent = data.pop("inherits", "")
        return {**preset(parent), **data} if parent else data

    names = ("Elegoo Centauri Carbon 2 0.4 nozzle", "0.20mm Standard @Elegoo CC2 0.4 nozzle", "Elegoo PLA @ECC2")
    model = model.resolve(strict=True)
    with TemporaryDirectory(prefix="codex-orca-neck-") as work:
        folder = Path(work).resolve()
        if folder.parent != Path(gettempdir()).resolve():
            raise ValueError("Unexpected temporary directory")
        paths = []
        for index, name in enumerate(names):
            path = folder / f"preset_{index}.json"
            config = preset(name)
            if index == 1:
                config.update({"enable_support": "1", "support_on_build_plate_only": "1", "support_type": "normal(auto)"})
            path.write_text(json.dumps(config), encoding="utf-8")
            paths.append(path)
        result = folder / "offline-slice.3mf"
        cmd = [str(exe), "--load-settings", ";".join(str(p) for p in paths[:2]), "--load-filaments", str(paths[2]),
               "--arrange", "1", "--slice", "1", "--outputdir", str(folder), "--export-3mf", result.name, str(model)]
        p = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, errors="replace", timeout=150,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        payload = {"presets": names, "geometry_only": True, "support_build_plate_only": True, "support_type": "normal(auto)",
                   "return_code": p.returncode, "model_sha256": sha256(model.read_bytes()).hexdigest(),
                   "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-3000:], "sliced_gcode_members": []}
        if result.exists():
            with ZipFile(result) as archive:
                project_config = "Metadata/project_settings.config"
                if project_config in archive.namelist():
                    config = json.loads(archive.read(project_config))
                    payload["effective_slicer_settings"] = {name: config.get(name) for name in (
                        "enable_support", "support_on_build_plate_only", "support_type", "printable_height", "layer_height")}
                for member in archive.namelist():
                    if member.lower().endswith(".gcode"):
                        gcode = archive.read(member).decode("utf-8", "replace")
                        comments = Counter(line.strip() for line in gcode.splitlines()
                                           if line.startswith((";TYPE:", "; FEATURE:"))
                                           and "support" in line.lower())
                        payload["sliced_gcode_members"].append({
                            "file": member, "layer_markers": gcode.count(";LAYER:"),
                            "support_comments": dict(comments.most_common(8)),
                        })
        filename = f"slicer_result_{label}.json" if label else "slicer_result.json"
        (HERE / filename).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("model", type=Path)
    cli.add_argument("--label", help="Name suffix for the validation result")
    args = cli.parse_args()
    with one_job():
        slice_check(args.model, args.label)
