"""Re-run the documented CAD and flow cases, and check numerical sensitivity."""

import hashlib
import json
import os
from pathlib import Path
import sys

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'reference'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import verify_airflow as airflow


def run_case(params, dx, iterations):
    fluid = airflow.extract_fluid_cavity(params)
    audit = airflow.audit_cad_flow_geometry(fluid, params)
    network = airflow.solve_1d_compressible_and_pulsating(params, audit, rpm=7000)
    grid = airflow.voxelize_fluid_solid(fluid['fluid_solid'], dx=dx)
    result = airflow.solve_3d_navier_stokes_fvm(
        grid, params, fluid, network['total_mass_flow_kgs'], n_picard=iterations
    )
    failed = result['mass_conservation_error_pct'] > 1 or result['max_mach_3d'] >= 1
    return {
        'cell_mm': dx,
        'picard_iterations': iterations,
        'numerical_screen': 'failed' if failed else 'completed, convergence unresolved',
        'cad_audit': audit,
        'sim_1d_7000rpm': {k: v for k, v in network.items() if not k.startswith('_')},
        'cfd_3d': {k: v for k, v in result.items() if not k.startswith('slice_')},
    }


def main():
    parameters = ROOT / 'intake_manifold_parameters.json'
    archive = ROOT / 'airflow_verification.json'
    params = json.loads(parameters.read_text(encoding='utf-8'))
    saved = json.loads(archive.read_text(encoding='utf-8'))
    report = {
        'operating_point': saved['operating_point'],
        'source_sha256': {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (parameters, archive, ROOT / 'verify_airflow.py', ROOT / 'generate_intake_manifold.py')
        },
        'cases': {},
    }
    for key, inputs, dx, iterations in (
        ('boost_optimized', params, 4.0, 40),
        ('baseline', airflow.make_baseline_params(params), 4.0, 40),
        ('boost_optimized_more_iterations', params, 4.0, 80),
        ('boost_optimized_finer_grid', params, 2.0, 80),
    ):
        print(f'Running {key}', flush=True)
        result = run_case(inputs, dx, iterations)
        if key in saved:
            result['matches_saved_by_field'] = {
                field: {name: bool(value == reference) for name, reference in saved[key][field].items()
                        if (value := result[field].get(name)) is not None}
                for field in ('cad_audit', 'sim_1d_7000rpm', 'cfd_3d')
            }
        report['cases'][key] = result
        (HERE / 'airflow_reproduction.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(result['cfd_3d'], flush=True)


if __name__ == '__main__':
    main()
