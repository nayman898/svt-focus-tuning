# Machining & Assembly Specification (V2.1 Exact G1-Tangent Release)
## Focus SVT Front Knuckle to 2010 Mustang GT (S197) Caliper Adapter Bracket

**Document Version:** 3.2 (V2.1 Exact $G^1$-Tangent 3/8" Steel & All-$\varnothing 13.00\text{ mm}$ Through-Bolted Candidate)  
**Part Name:** `focus_svt_mustang_bbk_steel_bracket`  
**Verified STEP SHA-256:** `6f57097922f5a15efb3da27714a69521b6ecd68713ded26432cea28f97e3d3f5`  
**Application:** 2002–2004 Ford Focus SVT Front Knuckle $\to$ 2010 Mustang GT Front Caliper & Carrier ($316 \times 30\text{ mm}$ Rotor)  
**Primary 3D Solid (CAM):** [`focus_svt_mustang_bbk_steel_bracket.step`](focus_svt_mustang_bbk_steel_bracket.step) (ISO 10303-21 STEP Solid B-rep)  
**Spacer 3D Solid (CAM):** [`focus_svt_mustang_bbk_4mm_spacer.step`](focus_svt_mustang_bbk_4mm_spacer.step) (ISO 10303-21 STEP Solid B-rep)  
**2D CAD / CAM DXF:** [`focus_svt_mustang_bbk_steel_bracket.dxf`](focus_svt_mustang_bbk_steel_bracket.dxf) (AutoCAD R12 DXF with true analytical `ARC`, `LINE`, `CIRCLE`, and `POINT` entities)  
**3D Print Fit-Check Models:** [`focus_svt_mustang_bbk_steel_bracket.stl`](focus_svt_mustang_bbk_steel_bracket.stl) (full $9.525\text{ mm}$ thickness for full stack/engagement fit checks) / [`focus_svt_mustang_bbk_steel_gauge.stl`](focus_svt_mustang_bbk_steel_gauge.stl) ($4.00\text{ mm}$ outline/hole gauge only—$5.525\text{ mm}$ thinner than final plate; use STEP/DXF for CNC toolpaths)

---

## 1. Raw Stock & Material Specification

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Material** | **AISI 1018 Cold-Rolled Steel Flat Bar (ASTM A108)** | Screening assumptions use $S_y = 370\text{ MPa}, S_u = 440\text{ MPa}, E = 205\text{ GPa}$. Obtain and verify the actual mill test report (MTR) for the bar stock prior to machining. |
| **Bar Stock Size** | **3/8" Thick ($9.525\text{ mm}$) $\times$ 2-1/2" Wide ($63.5\text{ mm}$) $\times$ 24" Long** | Finished part envelope is $187.20\text{ mm} \times 50.70\text{ mm} \times 9.525\text{ mm}$ ($7.370'' \times 1.996'' \times 0.375''$), leaving $0.504''$ ($12.80\text{ mm}$) of bar width for vise clamping. |
| **Finished Bracket Volume & Mass** | **$67,674.59\text{ mm}^3$ ($67.67\text{ cm}^3$) / $532.6\text{ g}$ ($1.17\text{ lbs}$)** | Verified directly from OpenCASCADE STEP solid (`6f570979...`) at $\rho = 7.87\text{ g/cm}^3$. |
| **Caliper Centering Spacers** | **4x Steel Spacers: $\text{OD} = 26.00\text{ mm}, \text{ID} = 13.00\text{ mm}, \text{Thickness} = 4.00 \pm 0.05\text{ mm}$** | Placed between the adapter plate and the Mustang GT caliper carrier (2 per side, 4 total). Faces must be flat and parallel within $0.03\text{ mm}$. |

---

## 2. Exact $G^1$-Tangent Contour & Hole Coordinates

All dimensions are in **millimeters**. Origin $(0, 0)$ is on the vertical symmetry axis ($X = 0$). All 8 curve-to-curve junctions on the outer perimeter have **$0.000000^\circ$ tangent discontinuity** (verified directly on the STEP solid in OpenCASCADE):

* **Mustang Outer Boss Arcs (2x):** True $\varnothing 37.00\text{ mm}$ ($R = 18.5000\text{ mm}$) centered at $(\pm 75.1000, 29.7000) \implies$ **exact $12.0000\text{ mm}$ minimum ligament** around $\varnothing 13.00\text{ mm}$ holes.
* **SVT Inner Boss Arcs (2x):** True $\varnothing 35.00\text{ mm}$ ($R = 17.5000\text{ mm}$) centered at $(\pm 45.5000, 15.0000) \implies$ **exact $11.0000\text{ mm}$ minimum ligament** around $\varnothing 13.00\text{ mm}$ holes (and $5.5000\text{ mm}$ radial margin outside a centered $\varnothing 24.0\text{ mm}$ washer).
* **Upper Bridge Tangent Arch (1x):** $R = \mathbf{1,641.1765\text{ mm}}$ centered at $(0.0000, 1,687.6765)$, passing through $(0.0000, 46.5000)$ and meeting the Mustang bosses tangentially at $(\mathbf{\pm 74.2629, 48.1811})$.
* **Lower Hub-Relief Tangent Arch (1x):** $R = \mathbf{86.3333\text{ mm}}$ centered at $(0.0000, -78.3333)$, peaking at $(0.0000, 8.0000)$ and meeting the SVT bosses tangentially at $(\mathbf{\pm 37.8315, -0.7303})$.
* **Lower External Tangent Lines (2x):** Straight lines connecting $(\mathbf{\pm 52.8060, -0.9019})$ on the SVT bosses to $(\mathbf{\pm 82.8235, 12.8894})$ on the Mustang bosses ($\mathbf{n} \cdot (\mathbf{C}_{\text{outer}} - \mathbf{C}_{\text{inner}}) = -1.0000\text{ mm}$).

### Hole Table (All 4 Holes Identical $\varnothing 13.00\text{ mm}$ Through-Clearance)

| Hole Feature | Quantity | Center Coordinates $(X, Y)$ | Finished Diameter | Machining Tolerance | Tooling / Operation Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **SVT Knuckle Mounts** | 2 | $(\pm 45.50, 15.00)$ | **$\varnothing 13.00\text{ mm}$** ($0.512''$) | Center: $\pm 0.05\text{ mm}$<br>Dia: $+0.15 / -0.05\text{ mm}$<br>($12.95\text{–}13.15\text{ mm}$) | **Unthreaded through-clearance hole.** Machine to finished tolerance via $\varnothing 13.0\text{ mm}$ metric drill/reamer, $33/64''$ ($13.10\text{ mm}$) drill, or CNC helical bore. *(Do not finish at $1/2'' / 12.70\text{ mm}$, which is below $12.95\text{ mm}$).* Chamfer $0.5\text{ mm} \times 45^\circ$ both sides. |
| **Mustang Carrier Mounts** | 2 | $(\pm 75.10, 29.70)$ | **$\varnothing 13.00\text{ mm}$** ($0.512''$) | Center: $\pm 0.05\text{ mm}$<br>Dia: $+0.15 / -0.05\text{ mm}$<br>($12.95\text{–}13.15\text{ mm}$) | **Unthreaded through-clearance hole.** Same $\varnothing 13.00\ (+0.15/-0.05)\text{ mm}$ finished bore and $0.5\text{ mm} \times 45^\circ$ chamfers both sides. |

---

## 3. Pre-Machining V2.1 Fit Check & M12 $\times$ 1.75 Hardware Specification

### 3.1 Physical Fit-Check Requirement (Before Cutting Steel)
Because V2.1 enlarges the SVT inner bosses to $\varnothing 35.0\text{ mm}$ (extending down to $Y = -2.50\text{ mm}$), fills in the upper bridge ($Y = 46.50\text{ mm}$ at $X = 0$), and adds a nut/washer stack on the inner SVT mounts, verify the V2.1 print on the vehicle prior to CNC milling:
* **Use Full Thickness ($9.525\text{ mm}$) for Stack Checks:** The $4.00\text{ mm}$ gauge ([`focus_svt_mustang_bbk_steel_gauge.stl`](focus_svt_mustang_bbk_steel_gauge.stl)) only checks the 2D outline and hole alignment because it is $5.525\text{ mm}$ thinner than the $9.525\text{ mm}$ plate. Use the full-thickness model ([`focus_svt_mustang_bbk_steel_bracket.stl`](focus_svt_mustang_bbk_steel_bracket.stl)) or compensate the $5.525\text{ mm}$ thickness difference when checking caliper centering, usable bolt thread engagement, and inner nut/washer/socket clearance.

### 3.2 Fastener & Hardware Specification (M12 $\times$ 1.75 Coarse Thread)
* **Inner SVT Knuckle Joint (Through-Bolted M12 $\times$ 1.75):**
  * **Bolt:** **M12 $\times$ 1.75 Property Class 10.9** (ISO 898-1 proof stress $= 830\text{ MPa}$, proof load $= 69.97\text{ kN}$ on $A_s = 84.3\text{ mm}^2$). Select grip/thread length so at least 2–3 full threads protrude past the nut face after tightening without thread runout binding inside the plate.
  * **Hardened Bearing Washers:** **ISO 7089 (DIN 125) Property Class 300 HV Hardened Flat Washers** ($\text{ID} = 13.0\text{ mm}, \text{OD} = 24.0\text{ mm}, \text{Thickness} = 2.5\text{ mm}$).
  * **Nut (Select one specific M12 $\times$ 1.75 coarse-thread Property Class 10 product):**
    1. **ISO 4032 Property Class 10** full-height hex nut (M12 $\times$ 1.75 coarse, $m = 10.8\text{ mm}$ nominal) used with the ISO 7089 300 HV hardened washer and medium threadlocker (Loctite 243 per Henkel TDS instructions), **OR**
    2. **ISO 7042 Property Class 10** all-metal prevailing-torque **hex high nut** (M12 $\times$ 1.75 coarse, $m_{\text{max}} = 12.3\text{ mm}$, used with the ISO 7089 300 HV hardened washer), **OR**
    3. **ISO 7044 (or DIN 6927) Property Class 10** all-metal prevailing-torque **hex flange nut** for M12 $\times$ 1.75 coarse pitch *(note: ISO 7044 is the coarse-thread flange locknut standard; ISO 12126 applies only to fine pitch)*.
    * *Proof Load Note:* Per ISO 898-2 / Bossard tables, an M12 $\times$ 1.75 Property Class 10 nut has a nominal proof stress of **$1,050\text{ MPa}$** (**$88.5\text{ kN}$** proof load).
* **Outer Mustang GT Carrier Joint (Tapped Carrier + 4.00 mm Spacer):**
  * **Bolt:** **M12 $\times$ 1.75 Property Class 10.9** flanged hex bolt (or hex bolt + ISO 7089 300 HV hardened washer).
  * **Spacer:** **4.00 mm steel spacer** ($\text{OD} = 26.00\text{ mm}, \text{ID} = 13.00\text{ mm}$) between the adapter plate and the Mustang GT caliper carrier.
* **Tightening Torque & Friction Validation Note:**
  * Do not apply a generic dry torque figure blindly across lubricated or prevailing-torque hardware. Using $T = K F d$, a torque of $111\text{ N}\cdot\text{m}$ ($82\text{ ft-lbs}$) corresponds to $51.4\text{ kN}$ at $K = 0.18$, $37.0\text{ kN}$ at $K = 0.25$, and $77.1\text{ kN}$ at $K = 0.12$ (which exceeds the $70.0\text{ kN}$ Class 10.9 bolt proof load).
  * Select the installation torque from the fastener manufacturer's VDI 2230 / Bossard table matched to the actual bolt/nut coating, washer friction ($\mu_{\text{thread}}, \mu_{\text{head}}$), and locking method (adding measured prevailing torque if using an ISO 7042 / ISO 7044 locknut), and physically verify outer carrier thread engagement depth and absence of bolt bottoming before final tightening.
