"""Instrument the existing FVM in memory. Saves diagnostic traces beside this script."""

from collections import Counter
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import textwrap

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import numpy as np
from scipy import ndimage
import verify_airflow as va


PROJECTION_DIAGNOSTICS = '''
        pressure_defect = (L_p @ p_corr - rhs_p) / RHO0
        corrected_flux_sum = float(np.sum(v_out_divfree) * RHO0 * face_area)
        positive_flux_sum = float(np.maximum(v_out_divfree, 0).sum() * RHO0 * face_area)
        center_face_div = -q_in_div.copy()
        for _, _, _, key, _, sign in dirs:
            comp = u if key.endswith('x') else v if key.endswith('y') else w
            valid, nb = nbrs[key]
            idx = np.flatnonzero(valid)
            center_face_div[idx] += 0.5 * (comp[idx] + comp[nb[valid]]) * sign / dx_m
        center_face_div[om_idx] -= v[om_idx] / dx_m
        audit['trace'].append({
            'iteration': _it + 1,
            'max_mach': float(np.max(np.sqrt(u*u + v*v + w*w)) / A0_SOUND),
            'projection_linear_relative_l2': float(np.linalg.norm(L_p @ p_corr - rhs_p) / max(np.linalg.norm(rhs_p), 1e-30)),
            'projected_local_continuity_abs_l1_over_inlet': float(np.abs(pressure_defect).sum() * dx_m**3 / q_target),
            'reconstructed_center_face_continuity_abs_l1_over_inlet': float(np.abs(center_face_div).sum() * dx_m**3 / q_target),
            'signed_outlet_kgs': corrected_flux_sum,
            'positive_only_outlet_kgs': positive_flux_sum,
            'signed_cylinder_kgs': [float(np.sum(v_out_divfree[m[om_idx]]) * RHO0 * face_area) for m in outlet_masks],
        })
        if audit['trace'][-1]['max_mach'] > 1:
            break
'''


def instrument(grid, params, fluid, mdot, n_picard, active, outlet_row_trial=False):
    audit = {'trace': []}
    solver_stats = {'cg': [], 'bicgstab': []}

    def track(method, name):
        def call(*args, **kwargs):
            value, info = method(*args, **kwargs)
            solver_stats[name].append(int(info))
            return value, info
        return call

    source = textwrap.dedent(inspect.getsource(va.solve_3d_navier_stokes_fvm))
    if outlet_row_trial:
        # Isolate the missing row to demonstrate the cause. Production needs face tagging.
        original = 'py <= tip_y + dx_mm * 0.95'
        assert source.count(original) == 1
        source = source.replace(original, 'py <= tip_y + dx_mm * 1.01')
    marker = '        p = p + alpha_p * p_corr\n'
    assert source.count(marker) == 1
    source = source.replace(marker, marker + PROJECTION_DIAGNOSTICS)
    anchor = '    wall_face_count[inlet_cell] ='
    assert source.count(anchor) == 1
    source = source.replace(anchor, "    audit['inlet_cells'] = int(inlet_cell.sum())\n"
                            "    audit['outlet_faces_by_cylinder'] = [int(m.sum()) for m in outlet_masks]\n"
                            "    audit['active_outlet_faces'] = int(all_outlet_mask.sum())\n" + anchor)

    # Use a fresh module mapping so the repository implementation and SciPy are untouched.
    from types import SimpleNamespace
    scope = {**vars(va), 'audit': audit,
             'spla': SimpleNamespace(cg=track(va.spla.cg, 'cg'), bicgstab=track(va.spla.bicgstab, 'bicgstab'))}
    for helper in ('_jacobi_cg', '_jacobi_bicgstab'):
        exec(textwrap.dedent(inspect.getsource(getattr(va, helper))), scope)
    exec(source, scope)
    results = scope[va.solve_3d_navier_stokes_fvm.__name__](grid, params, fluid, mdot, active_cyls=active, n_picard=n_picard)
    audit['linear_solver_exit_codes'] = {name: dict(Counter(codes)) for name, codes in solver_stats.items()}
    audit['reported_metrics'] = {k: v for k, v in results.items() if not k.startswith('slice_')}
    return audit


def main():
    params = json.loads(va.PARAMS_PATH.read_text(encoding='utf-8'))
    fluid = va.extract_fluid_cavity(params)
    cad = va.audit_cad_flow_geometry(fluid, params)
    mdot = va.solve_1d_compressible_and_pulsating(params, cad)['total_mass_flow_kgs']
    source_hash = hashlib.sha256(Path(va.__file__).read_bytes()).hexdigest()
    dx = float(sys.argv[1])
    outlet_row_trial = '--outlet-row-trial' in sys.argv[2:]
    grid = va.voxelize_fluid_solid(fluid['fluid_solid'], dx)
    labels, _ = ndimage.label(grid['inside'])
    _, counts = np.unique(labels[labels != 0], return_counts=True)
    around_first = abs(grid['xs_mm'] - params['runners']['center_x_mm'][0]) <= 30
    y_counts = grid['inside'][around_first].sum(axis=(0, 2))
    early_rows = [[float(y), int(n)] for y, n in zip(grid['ys_mm'][:3], y_counts[:3])]
    result = {'source_sha256': source_hash, 'dx_mm': dx, 'cell_components': sorted(counts.tolist(), reverse=True),
              'cylinder_one_first_rows_y_mm_and_cell_count': early_rows,
              'outlet_row_trial': outlet_row_trial,
              'geometry_volume_mm3': fluid['fluid_solid'].volume(), 'mass_flow_input_kgs': mdot, 'cases': {}}
    for name, maxit, active in (('all_cylinders', 80, [1, 2, 3, 4]), ('single_cylinder', 1, [2])):
        if dx != 4 and name == 'single_cylinder':
            continue
        print(f'{dx:g} mm, {name}', flush=True)
        result['cases'][name] = instrument(grid, params, fluid, mdot, 4 if outlet_row_trial else maxit, active, outlet_row_trial)
        suffix = '_outlet_row_trial' if outlet_row_trial else ''
        (HERE / f'fvm_{dx:g}mm{suffix}.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        audit = result['cases'][name]
        print(audit['linear_solver_exit_codes'], audit['reported_metrics'], flush=True)


if __name__ == '__main__':
    main()
