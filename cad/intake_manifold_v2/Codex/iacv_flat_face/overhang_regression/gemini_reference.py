"""Rebuild the pinned Gemini V2 splits and compare the two nominal 4 mm grid phases."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path

from full_regression import (CODEX, HERE, LEFT, MAIN_FLOW, RIGHT, digest, mesh_solid, one_job,
                             read_json, solve, solver, voxelize, write_json)
from solver_controls import load
import numpy as np
import trimesh


def audit_live_exports():
    root = CODEX.parent
    manifest = root / "stl/manifest.json"
    contents = read_json(manifest)
    rows = {}
    for side in (LEFT, RIGHT):
        record = contents["parts"][side]
        payload = (root / record["file"]).read_bytes()
        mesh = trimesh.load_mesh(BytesIO(payload), file_type="stl")
        counts = np.bincount(mesh.edges_unique_inverse)
        rows[side] = {"sha256": sha256(payload).hexdigest(), "manifest_sha256": record["sha256"],
                      "manifest_is_volume": record["is_volume"], "manifest_body_count": record["body_count"],
                      "reloaded_is_volume": mesh.is_volume, "reloaded_is_watertight": mesh.is_watertight,
                      "reloaded_body_count": mesh.body_count, "boundary_edges": int((counts == 1).sum()),
                      "edges_over_two_incident_faces": int((counts > 2).sum())}
    write_json(HERE / "live_gemini_stl_integrity.json", {
        "revision": contents.get("revision"), "manifest_sha256": digest(manifest), "parts": rows,
    })


def main():
    audit_live_exports()
    root = CODEX / "reference"
    source = root / "intake_manifold_v2_parameters.json"
    generator = root / "generate_intake_manifold_v2.py"
    solver.gen = load(generator, "gemini_v2_generator")
    params = read_json(source)
    fluid = solver.extract_fluid_cavity(params)
    analytic = fluid["fluid_solid"]
    ids = {"parameters": digest(source), "generator": digest(generator),
           "frozen_solver": digest(Path(solver.__file__))}
    splits = solver.gen.assemble_all(params)
    intrusions = []
    for side in (LEFT, RIGHT):
        solid = splits[side]
        view = solver.gen.manifold_to_trimesh(solid)
        assert view.is_volume and view.body_count == 1, side
        data = view.export(file_type="stl")
        mesh = trimesh.load_mesh(BytesIO(data), file_type="stl")
        if mesh.is_volume and mesh.body_count == 1:
            ids[side] = sha256(data).hexdigest()
            solid = mesh_solid(mesh)
        else:
            print("Using pinned CAD surface for split", side, "because the STL round trip did not qualify", flush=True)
        intrusions.append(solid ^ analytic)
    obstruction = solver.gen.m_union(intrusions)
    fluid["fluid_solid"] = analytic - obstruction
    for offset in (0, 2):
        grid = voxelize(fluid, 4, offset)
        result = solve(grid, params, fluid, MAIN_FLOW, n_picard=400)
        path = HERE / "cases" / f"gemini_dx4_shift{offset}_rpm7000.json"
        write_json(path, {"source_sha256": ids, "reference": "Pinned Gemini V2 reconstructed split halves",
                   "stl_round_trip_halves": [side for side in (LEFT, RIGHT) if side in ids],
                   "solid_in_capped_wot_mm3": obstruction.volume(),
                   "dx_mm": 4, "offset_mm": offset, "flow_kg_s": MAIN_FLOW,
                   "result": {k: v for k, v in result.items() if not k.startswith("slice_")}})
        print(path.stem, result["status"], result["tb_to_plenum_dp_kpa"],
              result["cyl_maldistribution_spread_pct"], flush=True)


if __name__ == "__main__":
    with one_job():
        main()
