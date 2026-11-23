# Focus SVT intake manifold airflow regression

The regression was paused at the owner's request after parallel runs slowed the PC. The `cases/` and `audits/` folders contain the completed results. The launch scripts allow one airflow run, geometry audit, or candidate export at a time. Candidate trial results here are screening evidence.

The comparison uses the Stage-2 V1 CAD paired with `svt_intake_manifold_1piece_full.stl` and the Codex V2 CAD with the eccentric BBK flange and separate cable-bracket posts. The baseline STL hashes match their manifests. The CAD-to-STL overlap with the capped air passage was below 0.001 mm³ for each design. Inspection with the current mesh reader flagged the V1 STL as non-watertight after vertex welding. The V1 analytic air cavity is a closed solid and supplies the simulation geometry. [V1 geometry](audits/v1.json) · [V2 geometry](audits/v2.json)

## Comparison conditions

Both designs use the same frozen V2 finite-volume solver, with all four outlets open, 18 psig, 52 °C, and 0.2777 kg/s imposed inlet mass at 7,000 rpm. Other speed points scale the imposed mass in proportion to rpm. The model seals the vacuum and IACV passages and uses the same nominal porous-outlet coefficient of 14 in all primary runs. The outlet reference planes are 22–30 mm from each spigot tip, upstream of the porous zone. The model starts the inlet reference 14–22 mm behind the throttle face.

- Pressure loss is the arithmetic mean of the four inlet-to-runner total-pressure losses. Each inlet or runner pressure uses a velocity-weighted sample. The legacy JSON field `tb_to_plenum_dp_kpa` contains that mean.
- Cylinder spread divides the difference between the largest and smallest outlet mass shares by the ideal 25% share. A 4% spread is a 1 percentage point difference between the highest and lowest mass shares.
- The steady model prescribes airflow and uses a fixed effective viscosity and modeled outlet resistance. The companion 1D runs estimate distribution under a lumped intake model. Their valve, acoustic and loss assumptions differ from the steady 3D model and they summarize different quantities.
- Each CFD case records the lattice and outlet area, solver convergence, mass closure, pressure, and flow by cylinder. Residual convergence and agreement across grid spacings and grid phases are evaluated independently. [NASA iterative convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/iterconv.html) · [NASA spatial convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)

## Solver checks

The straight duct uses a 42.8 mm bore, 0.100 kg/s and no porous outlet. Over the modeled 156 mm measurement length, the Haaland friction estimate gives 74.9 Pa. The solver returned 83.8, 80.8 and 81.1 Pa at 4.0, 3.0 and 2.5 mm. This checks the sign and scale of the pressure calculation for a straight duct. The manifold adds angled inlet tagging, turning flow and flow division. [4.0 mm duct](audits/duct_dx4_shift0.json) · [3.0 mm duct](audits/duct_dx3_shift0.json) · [2.5 mm duct](audits/duct_dx2.5_shift0.json)

The CAD-derived lumped steady model at 7,000 rpm estimated 0.36% spread on V1 and 0.96% on V2. Its 720° cycle model estimated 0.23% and 0.77% respectively. The lumped models use geometric and empirical loss terms and miss much of the flow imbalance seen in the geometry-resolved 3D calculation. The two model families give independent numerical evidence with different assumptions. [V1 lumped sweep](audits/v1.json) · [V2 lumped sweep](audits/v2.json)

## Reproduce

Run from `airflow_regression` with Python 3.11 and the packages in the [benchmark environment record](audits/duct_dx4_shift0.json).

```powershell
python -B run_case.py v1 --dx 4 --offset 2
python -B run_case.py v2 --dx 4 --offset 2
python -B audit_case.py v1
python -B audit_case.py v2
python -B audit_case.py duct --dx 3
```

The optional `--amg` switch uses PyAMG 5.3.0 to precondition the same conjugate-gradient pressure equations. It uses the same pressure residual threshold and retains the original Jacobi solve as a fallback. The raw results identify the cases run with that preconditioner. [PyAMG documentation](https://pyamg.readthedocs.io/en/latest/generated/pyamg.multilevel.html)
