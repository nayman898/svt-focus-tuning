# Extended-neck flat-face V2 validation

The checks cover the CAD and reloaded STLs, the new IACV passage, the build orientation, and steady wide-open-throttle flow. The load and flow screens use modeled boundary conditions. The installed throttle body, molded seal and IAC valve still need to be checked as an assembly.

## IACV air supply

The v024 warm-idle review reported 0.587 lb/min of total engine airflow. The v029 drive review shows 0.70–0.85 lb/min at idle. The duct calculation assigns the entire 0.85 lb/min or 6.43 g/s to the bypass, which gives a conservative warm-idle case. The separate 1.39 lb/min case uses a part-throttle hold as a stress input. It gives no direct measurement of cold-start IACV airflow. [v024 log review](../../../../../reports/2026-11-03-v024-cold-cleanup-review.md) · [v029 log review](../../../../../reports/2026-11-03-v029-drive-review.md)

The analysis slices the inlet transition and the round duct normal to its centerline. It uses the smallest sampled area and hydraulic diameter, 101.325 kPa inlet absolute pressure, 320 K air, 0.15 mm assumed wall roughness and a minor-loss coefficient sweep of 2, 5 and 10. The combined coefficient covers the entrance, turns and junction as a sensitivity range. No valve flow curve or actual printed roughness is available. The ideal choked flow is an upper bound for the duct. [Pressure and flow calculations](idle_and_pressure_results.json) · [NASA mass-flow equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/mass-flow-rate-equations/) · [Ford idle air control description](https://www.fordservicecontent.dealerconnection.com/pubs/content/~WVX2/~MUS~LEN/15/VX21026.HTM)

The face opening is about 256 mm². The lowest of 105 sampled duct sections is **96.58 mm²**, with an 11.08 mm hydraulic diameter. The bend radius increased from approximately 5.8 mm to **9.24 mm** and the duct length fell from 120.9 mm to **117.5 mm**. The reloaded full STL has less than 0.001 mm³ of solid intrusion into the capped feed. The feed is separated from the main air passage by at least 5.06 mm and from the cable pilot cavities by at least 10.51 mm.

| Demand sent through the duct | Modeled duct loss, low / mid / high assumed restriction |
|---|---:|
| 0.587 lb/min (4.44 g/s) | 2.4 / 5.4 / 10.6 kPa |
| 0.85 lb/min (6.43 g/s) | 5.1 / 11.6 / 23.8 kPa |
| 1.39 lb/min (10.51 g/s), stress case | 14.2 / 35.5 kPa / model cannot sustain this flow |

The v024 return-to-idle log recorded about 50 kPa of manifold vacuum relative to atmospheric. At the 6.43 g/s warm-idle case, the duct leaves pressure head for the valve across the modeled range. The 10.51 g/s stress case is sensitive to bend and valve losses. Bench-check actual cold-start and loaded-idle operation with the printed duct, throttle body and IACV together.

## Structural and print checks

The refined part has a **5.44 mm** minimum sampled IACV floor, **6.26 mm** sampled runner-root pressure walls, and clear CAD probes for all four flange sockets. The nominal tube-only hoop-stress screen gives 0.219 MPa at 18 psig and 0.304 MPa at 25 psig. Both halves fit the nominal build box in their exported orientations. The tall right half measures 159.59 × 216.75 × 253.73 mm, leaving **2.27 mm** of nominal Z room.

The outside of the duct now slopes into the right-half print orientation. In the neck inspection box, downward area past 55° fell from 7,687 to 7,528 mm², and area past 65° fell from 3,197 to 3,097 mm². Area past 45° stayed about 10,829 mm². The underside view shows steep regions on the runner and flange. [Final throttle-side view](refined_throttle.png) · [Overhang view](refined_build_underside.png) · [Before](baseline_overhang.json) · [After](refined_overhang.json) · [CAD checks](../refined/geometry_validation.json)

OrcaSlicer generated toolpaths for both halves with the CC2 0.4 mm profile, 0.20 mm layers and normal supports from the build plate. The right and left runs reported 1,271 and 983 layer markers respectively. This used the PLA preset for an offline geometry check. The actual manifold material, layer bonding and support removal still need verification with the chosen print process. [Right-half toolpath check](slicer_result.json) · [Left-half toolpath check](slicer_result_left.json)

The generator measures the runner-root walls, IACV floor, cable-pilot wall and flange access. The pressure screen computes the nominal round duct's hoop stress and the forces acting on the flange, feed and plenum split from 18 and 25 psig differential. Fastener preload, thermal creep, material and interlayer properties, and bracket loads require part-specific validation. The CAD check of the gasket traces the factory photo and measures the support land. An actual gasket and installed leak test are needed to establish sealing.

The mesh overhang check measures downward-facing triangles in a fixed box around the neck in the right-half print orientation. It includes inner and outer surfaces, so it measures changes in slope and area directly. A slicer determines actual supports and bridging from the material and process profile. The CC2 bounds check uses the 256 mm cubed envelope and the exclusion region in Orca's 0.4 mm profile. [ELEGOO build volume](https://wiki.elegoo.com/en/faq/centauri-carbon-2-combo) · [Orca machine definition](https://github.com/OrcaSlicer/OrcaSlicer/blob/main/resources/profiles/Elegoo/machine/ECC2/Elegoo%20Centauri%20Carbon%202%200.4%20nozzle.json)

## Wide-open-throttle airflow

The frozen 3D solver uses 0.2777 kg/s at 7,000 RPM, 18 psig and 52 °C. The IACV and vacuum branches are sealed in this calculation. The imposed flow and downstream loss model are common across revisions. The 1D sweep reports lumped flow and acoustic predictions from 3,000 to 7,500 RPM. Solver convergence, grid agreement and validation against physical test data are separate checks. [Frozen solver](../../reference/verify_airflow_v2.py) · [NASA grid convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)

| 3D grid spacing and offset | Pressure loss | Cylinder flow spread |
|---|---:|---:|
| [4.0 mm, aligned](wot_dx4_offset0_rpm7000.json) | 1.356 kPa | 6.79% |
| [4.0 mm, 2.0 mm shifted](wot_dx4_offset2_rpm7000.json) | 1.228 kPa | 6.34% |
| [3.0 mm, aligned](polished_wot_dx3_offset0_rpm7000.json) | 1.223 kPa | 6.21% |
| [2.5 mm, aligned](polished_wot_dx2.5_offset0_rpm7000.json) | 1.235 kPa | 6.31% |
| [Extended neck before the IACV face, 4.0 mm shifted](extended_neck_wot_dx4_offset2_rpm7000.json) | 1.228 kPa | 6.34% |
| [V1 at 4.0 mm, 2.0 mm shifted](../../airflow_regression/cases/v1_dx4_shift2_rpm7000.json) | 1.190 kPa | 1.11% |

All four flat-face solutions met the solver's iteration and projected face-mass closure criteria. The cell-velocity continuity diagnostic remained high, and pressure and spread shifted non-monotonically with spacing. The two 2 mm boundary checks kept all four outlets in one connected region with 362 or 360 tagged faces per cylinder. The final 2.5 mm solve assigned C4 23.98% of total flow. V2 has greater modeled cylinder imbalance than V1. The separate lumped model predicts 0.96% steady spread at 7,000 RPM and has its own loss and valve assumptions. The final refined model has zero measured symmetric volume difference against both flat-face CSG cavities used in the 3D runs, with the IACV branch sealed. [2 mm boundary checks](polished_wot_boundary_only.json) · [Lumped RPM sweep](polished_wot_lumped_rpm_sweep.json) · [4 mm cavity comparison](wot_domain_equivalence_refined_verified.json) · [Finer-case cavity comparison](wot_domain_equivalence.json)
