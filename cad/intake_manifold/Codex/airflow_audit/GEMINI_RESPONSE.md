# Gemini response to the airflow audit

Gemini 4 Argon (High), conversation 0da738ff-999f-4a73-851e-656640f5ed99

The wall thicknesses and numerical tolerances below are proposals from Gemini. The audit establishes sampled geometry and solver failures. The structural acceptance criteria and benchmark tolerances still need an engineering basis.

# Engineering Handoff & Assessment: Stage-2 Intake Manifold Airflow Suite Audit

**Receipt Confirmed.** The Codex engineering audit (`Codex/airflow_audit/GEMINI_REVIEW.md`) has been reviewed and cross-checked directly against [`generate_intake_manifold.py`](../../generate_intake_manifold.py), [`verify_airflow.py`](../../verify_airflow.py), [`compare_factory_manifold.py`](../../compare_factory_manifold.py), and [`intake_manifold_parameters.json`](../../intake_manifold_parameters.json). **The active working model and all repository files have been preserved untouched during this review.**

---

## Scope Distinction: Current Stage-2 vs. Separate WRC Design

| Attribute | Current Stage-2 Design (`cad/intake_manifold`) | Separate WRC Design (`cad/intake_manifold_wrc`) |
| :--- | :--- | :--- |
| **Role in This Update** | **Active fit & geometric baseline** for this engineering update | Separate side-feed/WRC-style architecture; out of scope for Stage-2 CAD edits |
| **Current Geometry** | 65 mm TB (`7°` forward cant), `2.038 L` bare tapered plenum (`0.60` Cyl-1 / `0.889` split area ratio), wall-flush `+7 mm` bellmouths (`[0°, 2.5°, 4.0°, 11.5°]` scoop angles), `Ø50.8 / Ø42.8 mm` (`2"`) round boot spigots ending at `Y = -146.0 mm` | Distinct plenum/runner package evaluated by its own `verify_wrc_airflow.py` driver |
| **Shared Solver Defect** | Uses center-point voxel cutoff `py <= tip_y + dx_mm * 0.95` ([`verify_airflow.py#L411`](../../verify_airflow.py#L411)) | Shares the identical `0.95 * dx` outlet selection vulnerability (`verify_wrc_airflow.py#L280`) and must receive the backported geometric boundary patch & diagnostics |

---

## Independent Assessment of Highest-Impact Findings

Every major defect identified in the Codex review is confirmed in the current source code:

### 1. 3D FVM Boundary Selection Failure at 2 mm & Silent CG Termination (Critical)
* **Root Cause Confirmed:** [`extract_fluid_cavity`](../../verify_airflow.py#L108-L110) clips the runner bores at `tip_y = -146.0 mm`. In [`voxelize_fluid_solid`](../../verify_airflow.py#L287), `ys` steps from `floor(bmin[1]/dx)*dx`. At `dx = 2.0 mm`, `Y = -146.0 mm` lies on the clipped boundary cap (excluded by `contains_points`), placing the first fluid cell centers at `Y = -144.0 mm`. The predicate `py <= tip_y + dx_mm * 0.95` ([`verify_airflow.py#L411`](../../verify_airflow.py#L411)) evaluates `-144.0 <= -144.1` (`False`), yielding **0 outlet faces** across 365,581 fluid cells while injecting mass into 1,184 inlet cells.
* **Silent Solver Failure Confirmed:** [`_jacobi_cg`](../../verify_airflow.py#L315-L319) and [`_jacobi_bicgstab`](../../verify_airflow.py#L322-L327) discard SciPy's convergence `info` code (`x, _ = spla.cg(...)`). With no Dirichlet anchor (`all_outlet_mask` empty), `L_p0` and `L_p` are singular all-Neumann matrices with an incompatible non-zero RHS, hitting the 700/600 iteration caps and producing unphysical velocities (`Mach ~ 5,301`). Even when the cutoff is relaxed to `1.01 * dx` (restoring 362 faces/runner), Jacobi-PCG hits its 600-iteration cap at 2 mm while global outlet mass error rounds to `0.00%`, proving that global mass error is merely a projection identity on the last step's `p_corr` and not a measure of outer or linear convergence.

### 2. Single-Runner `-1` Indexing Bug, Momentum Flux Inconsistency & Pressure Sampling (Critical)
* **Inactive-Runner Flux Bug Confirmed:** In [`solve_3d_navier_stokes_fvm`](../../verify_airflow.py#L585-L606), `om_lookup` is initialized to `-1` and populated only for active outlets (`om_idx = np.flatnonzero(all_outlet_mask)`). The reporting loop (lines 596–605) iterates over all four `outlet_masks[idx]` without intersecting `all_outlet_mask`. For any closed runner, `loc_idx = om_lookup[om_i]` is `-1`, indexing the **last element of `v_out_divfree`** and attributing active runner flow to closed runners (`~300.5%` false mass imbalance). Clipping `np.maximum(v_out_divfree, 0.0)`, defaulting zero-flow shares to `25.0%` (line 614), and clamping `max(p0_in_mean - p0_out_manifold, 0.0)` (line 610) hide backflow and failed solves.
* **Momentum/Continuity Discrepancy Confirmed:** In the Picard loop ([`verify_airflow.py#L499-L510`](../../verify_airflow.py#L499-L510)), the momentum matrix `M_vel` computes upwind face transport from raw cell-center averages `0.5 * (comp[r] + comp[c]) * sgn` rather than carrying the Rhie–Chow + `p_corr` mass-conserving face flux (`u_f`) forward. As a result, cell velocities remain non-solenoidal (`1.55x` summed local cell imbalance at 40 iterations) and the 4 mm cylinder flow spread drifts from **0.35% at 40 iterations to 1.41% at 80 iterations**.
* **Total-Pressure Loss Definition Confirmed:** `tb_to_plenum_dp_kpa` (lines 591–618) compares the volumetric mean of `p + 0.5 * rho * speed^2` inside the momentum source cells (`inlet_cell`) against a volume slab (`tip_y + 25..38 mm`) immediately upstream of the `24 mm`, `K = 14` porous spigot zone. It must be replaced by mass-flux-weighted total-pressure integrals across defined planar stations outside the volumetric source and porous sink zones.

### 3. Provenance Drift & Cylinder 3/4 Internal Sharp Lips (High)
* **Mixed-Revision Artifacts Confirmed:** Current [`intake_manifold_parameters.json`](../../intake_manifold_parameters.json) and [`generate_intake_manifold.py`](../../generate_intake_manifold.py) produce a `2.038 L` bare plenum (`45,486` cells at 4 mm) with an improved IACV pocket floor (`5.55 mm` center / `4.63 mm` minimum vertical ray thickness vs. the earlier `3.41 mm`). However, `stl/airflow_verification.json` holds an older `2.024 L` (`45,540`-cell) run, and [`compare_factory_manifold.py#L298-L325`](../../compare_factory_manifold.py#L298-L325) mixes the current parameter file and manifest with the stale verification JSON without hash checks.
* **Best-Supported CAD Defect Confirmed:** Section checks on the current Stage-2 STL show thin, sharp internal material webs (**0.67 mm and 0.75 mm spans** between internal air spaces) at the **Cylinder 3 and Cylinder 4** runner-entry / flush-bellmouth lips (where `4.0°` and `11.5°` axial scoop angles intersect the tapered plenum wall).

### 4. 1D Network, 720° Crank-Cycle Dynamics & Taper-Sweep Audit Bugs (High)
* **720° Crank-Cycle Momentum Equation & VE Scaling Confirmed:** In [`verify_airflow.py#L902-L911`](../../verify_airflow.py#L902-L911) (and [`compare_factory_manifold.py#L232-L238`](../../compare_factory_manifold.py#L232-L238)), `p_port_c = p_pl_local - loss_pa`, so `dmdt = (p_pl_local - p_port_c) / inertance` simplifies to `+loss_pa / inertance`. Instead of accelerating flow by the net pressure gradient across the runner `(p_pl_local - p_port_c - loss_pa)`, the resistive loss term drives `+dmdt` and is algebraically blended (`0.75 * mdot_valves + 0.25 * (m_run_inst + dmdt * dt)`). Furthermore, the integrated cycle flow (`0.24164 kg/s`, or `85.26%` raw VE) is rescaled to `VE_REF = 0.98` (line 933).
* **Taper Sweep Stale Audit & Non-Monotonic Split Confirmed:** [`verify_airflow.py#L1217-L1225`](../../verify_airflow.py#L1217-L1225) sweeps `taper_cyl1_area_ratio` up to `0.94` while passing the static `0.60`-taper `opt_res["cad_audit"]` (`2.038 L`) into every call, and when `r_cyl1 = 0.94 > split_x_area_ratio = 0.88869`, [`plenum_area_scale`](../../generate_intake_manifold.py#L255-L264) falls back to a non-monotonic piecewise linear pinch at `X = 0`. Acoustic length also conflicts between `275 mm` (`verify_airflow.py#L941`) and `243 mm` (`compare_factory_manifold.py#L323`).

### 5. Inverted AFR Formula & Assumed Acoustic Gain in Factory Comparison (High)
* **Inverted AFR Math Confirmed:** [`compare_factory_manifold.py#L335-L336`](../../compare_factory_manifold.py#L335-L336) computes `lean_afr = 11.0 * (mean_ve / min(ve_arr))` and `rich_afr = 11.0 * (mean_ve / max(ve_arr))`. Under equal injected fuel per cylinder, `AFR_i = 11.0 * (VE_i / mean_ve)`—a cylinder with higher airflow is **leaner**, not richer.
* **Encoded Acoustic Gain & Mixed IAT Confirmed:** In [`estimate_boosted_airflow_lbmin`](../../compare_factory_manifold.py#L270-L294), `+0.77 lb/min` (`71%`) of the reported `+1.08 lb/min` (`+11.6 bhp`) advantage over OEM Short-Runner at 7,000 RPM comes from the hardcoded `+2.0%` high-RPM acoustic multiplier (line 288), while mixing `52 °C` pressure-loss simulation with `72 °F` v037 density scaling.

---

## Prioritized Solver & CAD Update Plan

### Phase 1: Solver & Verification Suite Repair (Before Any CAD Parameter Change)
1. **Geometric Cap Boundary Tagging & Pre-Solve Gate (`verify_airflow.py` & `verify_wrc_airflow.py`):**
   * Tag inlet and 4 individual runner outlet boundary faces by geometric intersection/projection against the CAD throttle-body cap plane and the 4 spigot exit caps (`Y = tip_y_mm`), independent of cell-center phase (`0.95 * dx` cutoff removed).
   * Enforce a pre-solve gate verifying non-empty, disjoint outlet face sets, expected discrete areas, outward normals, and graph connectivity from inlet to all active outlets. Fail fast with diagnostic output if any active outlet has 0 faces.
2. **Inactive-Runner Masking, Consistent Face Fluxes & Convergence Tracking (`verify_airflow.py`):**
   * Intersect `outlet_masks[idx]` with `all_outlet_mask` before indexing `om_lookup`; report closed runners as `None`/`0.0` (masked), record signed net flow and reverse flow separately, remove nonnegative `ΔP` and `25%` fallback clipping, and disable 4-cylinder spread metrics when `< 4` outlets are active.
   * Carry Rhie–Chow + pressure-corrected face fluxes `u_f` directly into the next Picard step's momentum convection assembly so cell velocities and face fluxes converge to a single divergence-free state.
   * Capture `spla.cg` / `spla.bicgstab` exit codes (`info`), relative residual norms, and outer iteration histories for momentum, continuity, `ΔP`, and cylinder flow shares. Switch to AMG/ILU or tightened tolerances if Jacobi-PCG saturates on fine grids.
   * Compute mass-flux-weighted total pressure on fixed cross-sectional planes upstream of the porous spigot resistance zone and downstream of the inlet source plug.
3. **1D/720° Model & Audit Hygiene (`verify_airflow.py` & `compare_factory_manifold.py`):**
   * Fix the 720° runner momentum ODE so `dm_run/dt = ((p_pl_local - p_port_c) - loss_pa) / inertance` integrates genuinely rather than being driven by `+loss_pa`, and report raw unscaled `net_admitted_mass_kgs` / `raw_ve` separately from normalized distribution share.
   * Re-extract or update `cad_audit` per taper point in the taper sweep, constrain or flag cases where `taper_cyl1_area_ratio >= split_x_area_ratio`, and unify the physical runner vs. total acoustic length definitions (`108 mm` upper runner vs. `243 mm` / `275 mm` total tract).
   * Fix the cylinder AFR calculation to `AFR_i = afr_target * (ve_i / mean_ve)`. Separate pure `ΔP`-driven airflow differences from acoustic scenario multipliers, align reference temperatures (`52 °C` vs. `72 °F`), remove unsupported headline bhp claims, and embed SHA-256 provenance hashes (CAD script, parameter JSON, exported STLs, solver script) with a strict hash match gate in `compare_factory_manifold.py`.

### Phase 2: Three-Grid Rebaselining of Current Stage-2 CAD
* Run the repaired 3D FVM solver on the **current unmodified Stage-2 CAD** across **three valid grid resolutions** (e.g., `4.0 mm`, `2.8 mm`, `2.0 mm`) until outer residuals, `ΔP`, and cylinder shares plateau.
* Quantify grid-convergence uncertainty (GCI) on `ΔP` and cylinder maldistribution spread across all-open (`[1, 2, 3, 4]`) and single-runner (`[1]`, `[2]`, `[3]`, `[4]`) cases.

### Phase 3: Targeted Stage-2 CAD Update (`generate_intake_manifold.py`)
* **Keep Fixed (Fit Baseline):** Preserve the current `2.038 L` plenum taper (`0.60 / 0.889`), `65 mm` TB flange and `7°` cant, `Ø50.8 / Ø42.8 mm` spigot bores/tips, center split flange, tie bars, vacuum pads, and the improved `>= 4.63 mm` IACV pocket floor.
* **Single Local Geometric Change:** Smooth the sharp internal entry lips at **Cylinders 3 and 4** (where the `4.0°` and `11.5°` scooped flush bellmouths meet the tapered plenum wall and currently leave `0.67 mm` and `0.75 mm` solid spans) by introducing a controlled internal blend / minimum lip radius (`>= 2.0–2.5 mm` solid web thickness across the full bellmouth-to-plenum transition) paired with a local exterior root wall check so minimum pressure-wall thickness remains `>= 4.5 mm` everywhere.
* Re-export the 1-piece and split STLs, verify manifold watertightness and minimum wall thickness, and evaluate the exact single-feature delta against the Phase-2 Stage-2 baseline.

---

## First Verification Case

Before running the Stage-2 manifold geometry, the **first verification case** is a **Deterministic Boundary & Symmetry Suite (`test_airflow_suite.py`)** consisting of two fast analytical/geometric gates plus the single-runner Stage-2 isolation probe:

1. **Case 1A — Straight Rectangular/Circular Duct Benchmark (Mesh Phase & Refinement Invariance):**
   * **Setup:** Straight duct matching the `65 mm` TB / runner hydraulic diameter with imposed mass inflow at one cap and Dirichlet pressure outlet at the opposite cap, tested across 3 grid spacings (`4.0 mm`, `2.5 mm`, `2.0 mm`) and sub-cell grid coordinate offsets (`0.0`, `+0.35*dx`, `+0.50*dx` along the outlet axis).
   * **Pass Criteria:**
     * Non-empty outlet face detection on every grid spacing and offset (`0` empty-boundary failures).
     * Linear solvers return `info == 0` on all steps.
     * Signed inlet-to-outlet mass conservation error `< 1e-6` (unrounded) and interior cell velocity divergence residual `< 1e-4`.
     * Flux-weighted total pressure drop matches analytical Darcy–Weisbach + porous-zone `ΔP` within `< 3%` across all three grid densities.
2. **Case 1B — Symmetric 4-Outlet Manifold & Single-Runner Masking Gate:**
   * **Setup:** Symmetric 4-branch manifold (and Stage-2 geometry) tested with `active_cyls = [1, 2, 3, 4]`, `[1]`, `[2]`, `[3]`, `[4]`, and `[]` (empty outlet rejection test).
   * **Pass Criteria:**
     * `active_cyls = []` raises an immediate pre-solve boundary validation error.
     * Single-runner cases (`[2]`, etc.) report **exact `0.0 kg/s` (masked)** on inactive cylinders `1, 3, 4` (eliminating the `-1` index bug) and conserve `100.00% ± 0.01%` of inflow through the sole active runner at both `4 mm` and `2 mm`.
     * Symmetric 4-branch geometry yields `< 0.05%` left-to-right symmetry error across cylinders `(1, 4)` and `(2, 3)`.

---

## What Evidence Would Warrant Choosing a Different CAD Change

We will hold to the **local Cylinder 3 & 4 internal lip blend** as the sole CAD modification **unless** the repaired, grid-converged (`4 mm / 2.8 mm / 2.0 mm`) Stage-2 baseline produces one of the following four specific pieces of evidence:

1. **Plenum Axial Maldistribution Exceeds 1.5% With Grid-Converged Monotonic Bias:**
   * *Evidence:* If the converged 3D FVM baseline shows cylinder-to-cylinder flow share spread `> 1.5%` with a monotonic axial gradient (e.g., Cylinder 1 consistently starving or over-charging relative to Cylinder 4 by more than `2x` the grid uncertainty band `GCI`), and the local Cyl 3/4 lip blend changes spread by `< 0.2%`.
   * *Alternative CAD Change:* Adjust `taper_cyl1_area_ratio` (currently `0.60`) and `split_x_area_ratio` (currently `0.889`) in a single-variable sweep while holding bellmouths and spigots fixed.
2. **Persistent Cylinder 4 Jet-Overshoot / Entry Separation at `7°` TB Cant:**
   * *Evidence:* If the converged 3D velocity and flux-weighted total-pressure planes at the runner throats show Cylinder 4 suffering a localized total-pressure loss `> 25%` higher than Cylinders 1–3 due to high-velocity TB neck jet detachment overshooting the Cylinder 4 entry even after the Cyl 3/4 lip blend.
   * *Alternative CAD Change:* Revise the Cylinder 4 axial scoop angle (`axial_entry_angles_deg[3]`, currently `11.5°`) or lengthen/re-index the TB-neck-to-plenum transition (`cyl4_end_x_mm` / `forward_cant_deg`) rather than altering plenum volume.
3. **True Geometric Runner-Throat Pinch Identified by Centerline-Normal Slicing:**
   * *Evidence:* If centerline-orthogonal cross-sectional slicing along the full runner sweep (`p_bm_tip` to `tip_y`) reveals an unintended minimum cross-sectional area below the `Ø42.8 mm` spigot exit area (`< 1,438.7 mm²`) caused by the Bezier loft transition.
   * *Alternative CAD Change:* Increase `plenum_entry_diameter_mm` or re-schedule the runner loft profile interpolation (`build_single_runner_components`) to enforce a strictly monotonic area contraction from bellmouth lip to spigot exit.
4. **Structural Wall Thinning Below `4.0 mm` Under Internal Blend:**
   * *Evidence:* If ray-cast wall-thickness auditing around the Cyl 3/4 runner root and adjacent center-split flange / IACV boss shows that blending the internal lip reduces minimum solid wall thickness below `4.0 mm`.
   * *Alternative CAD Change:* Expand the exterior runner-to-plenum root fillet (`exterior_fillet_x_mm` / `exterior_fillet_z_mm`) concurrently with the internal lip radius to preserve the full structural pressure shell.

