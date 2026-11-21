# Focus SVT to 2010 Mustang GT Big Brake Kit (BBK) Reversible Caliper Adapter (V2.1 Exact G1-Tangent)

3D B-rep STEP solids, print-ready binary STLs, 1:1 analytical CNC DXF drawings, and finite-element screening reports for adapting a **2010 Ford Mustang GT front caliper & carrier ($316 \times 30\text{ mm}$ rotor)** onto a **2002–2004 Ford Focus SVT (MK1 Focus)** front steering knuckle using **3/8" ($9.525\text{ mm}$) 1018 Steel** and **M12 $\times$ 1.75 Class 10.9 hardware**.

---

## 1. Current Disposition & V2.1 Verification ([`independent_review_v2_1_2026-11-07/REVIEW.md`](independent_review_v2_1_2026-11-07/REVIEW.md))

**Disposition:** **Candidate requiring V2.1 physical fit check and complete assembly validation.**  
**Verified V2.1 STEP SHA-256:** `6f57097922f5a15efb3da27714a69521b6ecd68713ded26432cea28f97e3d3f5`

All geometric findings from the prior reviews are closed in **V2.1**, and all documentation/provenance items from [`independent_review_v2_1_2026-11-07/REVIEW.md`](independent_review_v2_1_2026-11-07/REVIEW.md) have been reconciled:

1. **Closed Geometry & Export Findings:**
   * **Exact $0.000000^\circ$ $G^1$ Tangency at All 8 Perimeter Junctions:** [`generate_step_file.py`](generate_step_file.py) uses `theta_n = theta_c - 0.5 * math.pi - alpha`. Direct OpenCASCADE derivative checks on [`focus_svt_mustang_bbk_steel_bracket.step`](focus_svt_mustang_bbk_steel_bracket.step) (`6f570979...`) confirm **$0.000000^\circ$ tangent discontinuity** at all 8 joins.
   * **Exact Ligaments:** **$11.000\text{ mm}$ inner** (SVT) and **$12.000\text{ mm}$ outer** (Mustang) minimum ligaments around the four $\varnothing 13.00\text{ mm}$ through-clearance holes.
   * **Exact STEP / DXF / STL Agreement:** DXF arcs/lines match the STEP outline within $0.000018\text{ mm}$, and the STL (`tolerance=0.001, angular_tolerance=0.01`) matches the STEP outline within $0.00466\text{ mm}$ ($67,674.59\text{ mm}^3$ STEP vs. $67,679.09\text{ mm}^3$ STL, $0.00665\%$ volume difference).
2. **Reconciled M12 $\times$ 1.75 Coarse-Thread Nut Standards & FEA Provenance:**
   * **M12 $\times$ 1.75 Coarse-Thread Class 10 Nuts:** Corrected the coarse-thread all-metal prevailing-torque flange nut reference to **ISO 7044 (or DIN 6927)** *(ISO 12126 applies only to fine pitch)* alongside **ISO 4032** (full-height hex nut) and **ISO 7042** (all-metal prevailing-torque hex high nut), paired with **ISO 7089 Property Class 300 HV** hardened flat washers ($\text{OD} = 24.0\text{ mm}$).
   * **Fresh V2.1 FEA Screening Provenance:** [`STRUCTURAL_ANALYSIS_1018_STEEL.md`](STRUCTURAL_ANALYSIS_1018_STEEL.md) and [`bbk_adapter_parameters.json`](bbk_adapter_parameters.json) report the fresh V2.1 FEA solves on STEP `6f570979...` (`equal_X` $2\text{ mm}$ fixed-bore peak $= \mathbf{242.4\text{ MPa}}$, web $= \mathbf{226.0\text{ MPa}}$, disp $= \mathbf{0.0901\text{ mm}}$; $3\text{ mm}$ back-face patch peak $= \mathbf{368.8\text{ MPa}}$; 75/25 `split75_X` $= \mathbf{363.8\text{ MPa}}$ bore / $\mathbf{486.5\text{ MPa}}$ face), with earlier V2 (`225.7 MPa`) and V1 (`685.8 MPa`) values explicitly labeled as historical.
3. **Full-Thickness Physical Fit Check (`PENDING_V2_1_FIT_CHECK`):**
   * Use the full-thickness $9.525\text{ mm}$ print ([`focus_svt_mustang_bbk_steel_bracket.stl`](focus_svt_mustang_bbk_steel_bracket.stl))—or compensate the $5.525\text{ mm}$ thickness difference of the $4.00\text{ mm}$ gauge ([`focus_svt_mustang_bbk_steel_gauge.stl`](focus_svt_mustang_bbk_steel_gauge.stl))—to verify caliper centering, outer carrier bolt thread depth, and inner nut/washer/socket clearance on the vehicle before machining steel.

---

## 2. Deliverables Catalog

All files are in [`cad/bbk_caliper_adapter/`](file:///c:/Users/nlm89/source/repos/svt-focus-tuning/cad/bbk_caliper_adapter/):

| File | Format | Description |
| :--- | :---: | :--- |
| [**`focus_svt_mustang_bbk_steel_bracket.step`**](focus_svt_mustang_bbk_steel_bracket.step) | **Solid STEP (AP214)** | **Verified V2.1 3/8" ($9.525\text{ mm}$) 1018 Steel Bracket Solid B-rep** (`6f570979...`). Exact $0.000000^\circ$ $G^1$-tangent arcs/lines and 4x $\varnothing 13.00\text{ mm}$ cylindrical through-holes. |
| [**`focus_svt_mustang_bbk_4mm_spacer.step`**](focus_svt_mustang_bbk_4mm_spacer.step) | **Solid STEP (AP214)** | **4.00 mm Steel Caliper Centering Spacer Solid B-rep** ($\text{OD}=26.0\text{ mm}, \text{ID}=13.0\text{ mm}$). |
| [**`focus_svt_mustang_bbk_steel_bracket.dxf`**](focus_svt_mustang_bbk_steel_bracket.dxf) | **2D CAD (R12 DXF)** | **1:1 CNC CAD Drawing.** True analytical `ARC`, `LINE`, `CIRCLE`, and `POINT` entities matching the V2.1 STEP within $0.000018\text{ mm}$. |
| [**`focus_svt_mustang_bbk_steel_bracket.stl`**](focus_svt_mustang_bbk_steel_bracket.stl) | **Binary STL** | **V2.1 Full-Thickness ($9.525\text{ mm}$) 3D Print Fit-Check Model** ($67.68\text{ cm}^3$, $532.6\text{ g}$, 100% watertight). |
| [**`focus_svt_mustang_bbk_steel_gauge.stl`**](focus_svt_mustang_bbk_steel_gauge.stl) | **Binary STL** | **Rapid 4.00 mm 2D Outline / Hole-Alignment Gauge** ($5.525\text{ mm}$ thinner than final plate). |
| [**`focus_svt_mustang_bbk_4mm_spacer_pair.stl`**](focus_svt_mustang_bbk_4mm_spacer_pair.stl) | **Binary STL** | **Pair of two 4.00 mm spacers** placed between adapter and Mustang GT carrier. |
| [**`MACHINING_SPECIFICATION.md`**](MACHINING_SPECIFICATION.md) | **Markdown** | **CNC milling & M12 $\times$ 1.75 hardware specification sheet** (reconciled coordinates, hole tolerances, and ISO 4032 / 7042 / 7044 nut specs). |
| [**`STRUCTURAL_ANALYSIS_1018_STEEL.md`**](STRUCTURAL_ANALYSIS_1018_STEEL.md) | **Markdown** | **Structural & bolted-joint screening summary** reporting the fresh V2.1 FEA solves on STEP `6f570979...`. |
| [**`independent_review_v2_1_2026-11-07/REVIEW.md`**](independent_review_v2_1_2026-11-07/REVIEW.md) | **Markdown** | **Independent V2.1 correction review** and [`FEA_RESULTS.md`](independent_review_v2_1_2026-11-07/FEA_RESULTS.md). |
