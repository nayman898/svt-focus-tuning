"""Reproduce CAD, 1D, sweep and factory-comparison findings without editing source outputs."""

from copy import deepcopy
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import inspect
import json
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import textwrap
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import numpy as np
from shapely.geometry import Polygon
import compare_factory_manifold as factory
import generate_intake_manifold as cad
import verify_airflow as va


def section(solid, origin, axis):
    u = np.cross([0, 0, 1], axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    rotation = np.stack((u, v, axis))
    transform = np.column_stack((rotation, -rotation @ origin))
    polygons = solid.transform(transform).slice(0).to_polygons()
    return va._polygon_area_perimeter([np.asarray(p) for p in polygons])


def cad_checks(params, fluid, audit):
    sys.path.insert(0, str(HERE.parent))
    from check_geometry import iacv_floor, indexed_stl, root_witnesses

    mesh = indexed_stl(ROOT/'stl'/'svt_intake_manifold_1piece_full.stl')[1]
    rows = []
    for xc, bore in zip(params['runners']['center_x_mm'], fluid['runner_bores']):
        _, axis, p0, *_ = cad.runner_bezier_points(xc, params)
        # The flare is closed out at this station and the curved taper has yet to begin.
        area, perimeter = section(bore, p0 - axis * 1.1, axis)
        rows.append({'x_mm': xc, 'area_mm2': area, 'perimeter_mm': perimeter,
                     'hydraulic_diameter_mm': 4 * area / perimeter})
    reference = HERE.parent/'reference'
    old_params = json.loads((reference/'intake_manifold_parameters.json').read_text(encoding='utf-8'))
    spec = spec_from_file_location('archived_manifold_generator', reference/'generate_intake_manifold.py')
    old_cad = module_from_spec(spec)
    spec.loader.exec_module(old_cad)
    scope = {**vars(va), 'gen': old_cad}
    name = va.extract_fluid_cavity.__name__
    exec(textwrap.dedent(inspect.getsource(va.extract_fluid_cavity)), scope)
    old_fluid = scope[name](old_params)
    old = old_fluid['fluid_solid']
    new = fluid['fluid_solid']
    end_ratio = params['plenum']['taper_cyl1_area_ratio']
    return {
        'main_cavity_current_vs_previous_symmetric_difference_mm3': abs((old-new).volume()) + abs((new-old).volume()),
        'main_cavity_current_minus_previous_mm3': (new-old).volume(),
        'main_cavity_previous_minus_current_mm3': (old-new).volume(),
        'plenum_liters_current': fluid['pl_inner'].volume() * 1e-6,
        'plenum_liters_previous_cad': old_fluid['pl_inner'].volume() * 1e-6,
        'current_stl_thin_internal_lip_crossings': root_witnesses(mesh, params),
        'current_stl_iacv_floor': iacv_floor(mesh, params),
        'cad_throat_sections': rows,
        'network_input_throat_area_mm2': audit['runner_throat_area_mm2'],
        'network_input_throat_perimeter_mm': 2 * (46 - 2 * 19.2) + 2 * (40 - 2 * 19.2) + 2 * math.pi * 19.2,
        'analytic_cyl1_taper_end_ratio': end_ratio,
    }


def baseline_projection(fluid, params, dx):
    # manifold3d's -90 degree Y rotation maps world coordinates to (-Z, Y, X).
    bare = fluid['pl_inner'].rotate([0, -90, 0])
    intr = fluid['bm_intrusion'].rotate([0, -90, 0])
    result = []
    empty = Polygon()
    for x in params['runners']['center_x_mm']:
        projection = empty
        for station in np.arange(x-30, x+30+dx/2, dx):
            cross = empty
            for loop in intr.slice(station).to_polygons():
                poly = Polygon(loop)
                if poly.is_valid:
                    cross = cross.symmetric_difference(poly)
            projection = projection.union(cross)
        bare_slice = Polygon(bare.slice(x).to_polygons()[0])
        result.append(float(projection.intersection(bare_slice).area / bare_slice.area * 100))
    return result


def network_check(params, audit, rpm=7000.0, n_ca=720, cycles=3):
    observed = {'branch_history': [], 'cycle_history': []}
    source = textwrap.dedent(inspect.getsource(va.solve_1d_compressible_and_pulsating))
    substitutions = {
        '    n_ca = 720\n': f'    n_ca = {n_ca}\n',
        '    for cyc in range(3):': f'    for cyc in range({cycles}):',
        '            if cyc == 2:': f'            if cyc == {cycles - 1}:',
        '        for _ in range(55):': "        lower_flow = float(np.sum(branch_sum(lo)))\n"
                                     "        upper_flow = float(np.sum(branch_sum(hi)))\n"
                                     "        observed['branch_history'].append([lower_flow, mdot_total_ref, upper_flow])\n"
                                     '        for _ in range(55):',
        '        for s_idx, th_g in enumerate(ca_deg):': '        cycle_net_tb = 0.0\n'
                                                       '        p_start = p_pl_inst\n'
                                                       '        cycle_net_valves = np.zeros(4)\n'
                                                       '        for s_idx, th_g in enumerate(ca_deg):',
        '            dm_pl = mdot_tb - float(np.sum(mdot_valves))': '            cycle_net_tb += mdot_tb * dt\n'
                                                                     '            cycle_net_valves += mdot_valves * dt\n'
                                                                     '            dm_pl = mdot_tb - float(np.sum(mdot_valves))',
        '    mdot_peak_runner =': "        observed['cycle_history'].append({\n"
                                  "            'net_tb_kg_per_cycle': cycle_net_tb,\n"
                                  "            'net_cylinders_kg_per_cycle': cycle_net_valves.tolist(),\n"
                                  "            'plenum_pressure_change_pa': p_pl_inst - p_start,\n"
                                  '        })\n'
                                  '    mdot_peak_runner =',
    }
    for old, new in substitutions.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    scope = {**vars(va), 'observed': observed}
    exec(source, scope)
    result = scope[va.solve_1d_compressible_and_pulsating.__name__](params, audit, rpm=rpm)
    observed['branch_all_bracketed'] = all(lo >= target >= hi for lo, target, hi in observed['branch_history'])
    observed['steady_cylinder_sum_from_report_kgs'] = sum(result['cyl_mass_flow_kgs'])
    measured = np.asarray(observed['cycle_history'][-1]['net_cylinders_kg_per_cycle'])
    observed['last_cycle_net_valve_mass_kgs'] = float(measured.sum() * rpm/120)
    observed['last_cycle_raw_admitted_mass_ref_density_ve'] = float(np.mean(measured) / (va.RHO0 * va.ENGINE_DISP_L * 1e-3 / 4))
    observed['model'] = {k:v for k,v in result.items() if not k.startswith('_')}
    return observed


def factory_checks(archived):
    curve = archived['rpm_curves']
    def at(mode, rpm):
        return next(v for v in curve[mode] if v['rpm'] == rpm)

    rpm = 7000
    custom = at('custom', rpm)
    oem = at('oem_short', rpm)
    official = factory.estimate_boosted_airflow_lbmin(rpm, custom, 'custom')
    same_acoustic = factory.estimate_boosted_airflow_lbmin(rpm, custom, 'oem_short')
    oem_flow = factory.estimate_boosted_airflow_lbmin(rpm, oem, 'oem_short')
    ve = np.asarray(custom['cyl_ve'])
    checks = {
        'custom_full_lbmin_7000': official,
        'custom_with_oem_short_acoustic_factor_lbmin_7000': same_acoustic,
        'oem_short_lbmin_7000': oem_flow,
        'predicted_oem_short_anchor_lbmin_at_6397': factory.estimate_boosted_airflow_lbmin(6397, factory.simulate_oem_dsi_point('short', 6397), 'oem_short'),
        'published_equal_fuel_afr_from_inverse_ve': (11 * np.mean(ve) / ve).tolist(),
        'correct_equal_fuel_afr_from_direct_ve': (11 * ve / np.mean(ve)).tolist(),
    }
    with TemporaryDirectory(dir=HERE) as temporary:
        folder = Path(temporary)
        factory.OUT_JSON = folder/'factory.json'
        factory.OUT_PNG = folder/'factory.png'
        try:
            factory.main()
        except Exception:
            checks['driver_traceback'] = traceback.format_exc()
        else:
            checks['driver_artifacts_written'] = factory.OUT_JSON.exists() and factory.OUT_PNG.exists()
    return checks


def main():
    inputs = (va.PARAMS_PATH, Path(va.__file__), Path(cad.__file__), Path(factory.__file__), factory.MANIFEST_PATH,
              factory.VERIF_PATH, factory.OUT_JSON, ROOT/'stl'/'svt_intake_manifold_1piece_full.stl')
    report = {'sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    params = json.loads(va.PARAMS_PATH.read_text(encoding='utf-8'))
    fluid = va.extract_fluid_cavity(params)
    audit = va.audit_cad_flow_geometry(fluid, params)
    print('CAD and model perturbations', flush=True)
    report['cad'] = cad_checks(params, fluid, audit)
    baseline = va.make_baseline_params(params)
    base_fluid = va.extract_fluid_cavity(baseline)
    base_audit = va.audit_cad_flow_geometry(base_fluid, baseline)
    report['cad']['baseline_projected_sleeve_shadow_pct'] = {
        'published_sampling': base_audit['cyl_peak_blockage_pct'],
        'point_union_0p5mm_actual_slice_coords': baseline_projection(base_fluid, baseline, 0.5),
    }
    report['network'] = {}
    variants = ((3000, 720, 3), (7000, 720, 3), (7500, 720, 3), (7000, 1440, 3), (7000, 2880, 6))
    for rpm, n_ca, cycles in variants:
        report['network'][f'{rpm}rpm_{n_ca}steps_{cycles}cycles'] = network_check(params, audit, rpm=float(rpm), n_ca=n_ca, cycles=cycles)

    report['taper'] = {}
    for ratio in (0.54, 0.60, 0.78, 0.94):
        trial = deepcopy(params)
        trial['plenum']['taper_cyl1_area_ratio'] = ratio
        fresh = va.audit_cad_flow_geometry(va.extract_fluid_cavity(trial), trial)
        stale = va.solve_1d_compressible_and_pulsating(trial, audit)
        actual = va.solve_1d_compressible_and_pulsating(trial, fresh)
        report['taper'][str(ratio)] = {
            'stale_volume_l': audit['bare_plenum_volume_liters'], 'actual_volume_l': fresh['bare_plenum_volume_liters'],
            'stale_helmholtz_hz': stale['helmholtz_freq_hz'], 'actual_helmholtz_hz': actual['helmholtz_freq_hz'],
            'stale_steady_spread_pct': stale['ve_maldistribution_spread_pct'],
            'with_fresh_cad_steady_spread_pct': actual['ve_maldistribution_spread_pct'],
            'stale_pulsating_spread_pct': stale['ve_maldistribution_720ca_pct'],
            'with_fresh_cad_pulsating_spread_pct': actual['ve_maldistribution_720ca_pct'],
            'actual_section_scale_at_split_x0': cad.plenum_area_scale(0.0, trial),
        }
    file = HERE/'model_evidence.json'
    file.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Factory comparison entry point', flush=True)
    archived = json.loads(factory.OUT_JSON.read_text(encoding='utf-8'))
    report['factory'] = factory_checks(archived)
    file.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['factory'], flush=True)


if __name__ == '__main__':
    main()
