"""Blend the firewall-side inner plenum wall toward cylinder 4 without moving the skin."""

import numpy as np


def attach(generator):
    build = generator.build_plenum_loft

    def build_plenum(params, is_inner):
        solid = build(params, is_inner)
        cfg = params["plenum"].get("rear_wall_flow_guide")
        if not is_inner or cfg is None:
            return solid
        mesh = generator.manifold_to_trimesh(solid)
        xyz = mesh.vertices.copy()
        start, end = cfg["blend_x_mm"]
        axial = np.clip((xyz[:, 0] - start) / (end - start), 0, 1)
        firewall = np.clip((xyz[:, 1] + 6) / 54, 0, 1)
        weight = np.sin(np.pi * axial)**2 * firewall**2 * (3 - 2 * firewall)
        xyz[:, 1] -= cfg["depth_mm"] * weight
        mesh.vertices = xyz
        return generator.trimesh_to_manifold(mesh)

    generator.build_plenum_loft = build_plenum
