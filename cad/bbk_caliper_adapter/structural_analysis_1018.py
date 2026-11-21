#!/usr/bin/env python3
"""
structural_analysis_1018.py
Comprehensive Structural FEA-equivalent Analysis of Focus SVT to Mustang BBK Caliper Bracket
Manufactured from 1018 Cold-Rolled Steel (CRS) Plate.
"""

import math

def run_analysis():
    print("=" * 80)
    print("STRUCTURAL & MECHANICAL ANALYSIS: 1018 STEEL BBK CALIPER ADAPTER BRACKET")
    print("=" * 80)
    
    # --------------------------------------------------------------------------
    # 1. Vehicle & Dynamic Braking Conditions
    # --------------------------------------------------------------------------
    # Vehicle: 2002-2004 Ford Focus SVT
    m_curb = 1250.0  # kg (~2750 lbs)
    m_driver_fuel = 100.0 # kg
    m_total = m_curb + m_driver_fuel # 1350 kg (~2976 lbs)
    g = 9.80665 # m/s^2
    
    # Severe deceleration spike (sticky 200TW autocross/track tires, threshold braking)
    a_decel = 1.20 * g  # 1.2g deceleration
    f_total_brake = m_total * a_decel  # Total vehicle retarding force (N)
    
    # Dynamic weight transfer under 1.2g:
    # Front axle carries ~78% of total dynamic braking load
    pct_front = 0.78
    f_front_axle = f_total_brake * pct_front
    f_front_wheel = f_front_axle / 2.0  # Force per front tire contact patch
    
    # Wheel/Tire: Focus SVT standard 215/45R17
    # Nominal rolling radius = 0.3125 m (12.30 in)
    r_tire = 0.3125
    t_brake_wheel = f_front_wheel * r_tire  # Wheel braking torque in N*m
    
    # Brake Rotor & Caliper: Mustang S197 (12.4" / 316 mm or Cobra 13.0" / 330 mm)
    # Effective pad clamping radius: ~0.135 m
    r_rotor_eff = 0.135
    f_caliper_tangential = t_brake_wheel / r_rotor_eff # Tangential shear force at caliper
    f_bolt_shear = f_caliper_tangential / 2.0 # Shear load per M12 bolt
    
    print("\n[1] Dynamic Vehicle Braking Loads (1.2g Threshold Stop)")
    print(f"  - Total Vehicle Mass:           {m_total:.0f} kg ({m_total*2.20462:.0f} lbs)")
    print(f"  - Peak Deceleration:           1.20 g ({a_decel:.2f} m/s^2)")
    print(f"  - Front Axle Dynamic Share:    {pct_front*100:.0f}%")
    print(f"  - Retarding Force (Per Wheel): {f_front_wheel:.1f} N ({f_front_wheel*0.224809:.1f} lbs)")
    print(f"  - Dynamic Braking Torque:      {t_brake_wheel:.1f} N*m ({t_brake_wheel*0.737562:.1f} ft-lbs)")
    print(f"  - Caliper Tangential Shear:    {f_caliper_tangential:.1f} N ({f_caliper_tangential*0.224809:.1f} lbs)")
    print(f"  - Shear Load per M12 Bolt:     {f_bolt_shear:.1f} N ({f_bolt_shear*0.224809:.1f} lbs)")
    
    # --------------------------------------------------------------------------
    # 2. Material Specifications: 1018 Cold-Rolled Steel (ASTM A108)
    # --------------------------------------------------------------------------
    sigma_y = 370.0   # MPa (53.7 ksi) Yield Strength
    sigma_u = 440.0   # MPa (63.8 ksi) Ultimate Tensile Strength
    tau_y   = sigma_y / math.sqrt(3.0) # 213.6 MPa (von Mises Shear Yield)
    E       = 205000.0 # MPa (29.7 Mpsi) Young's Modulus
    nu      = 0.29     # Poisson's ratio
    G       = E / (2.0 * (1.0 + nu)) # 79,457 MPa Shear Modulus
    rho     = 7.87     # g/cm^3 (0.284 lb/in^3) Density
    S_e     = 0.50 * sigma_u # ~220 MPa Endurance Limit (unnotched)
    # Corrected endurance limit with surface factor (cold rolled k_a=0.85) and size factor (k_b=0.85):
    S_e_mod = S_e * 0.85 * 0.85 # ~158.9 MPa
    
    print("\n[2] Material Properties: 1018 Cold-Rolled Steel (CRS)")
    print(f"  - Tensile Yield Strength (Sy): {sigma_y:.1f} MPa ({sigma_y*0.145038:.1f} ksi)")
    print(f"  - Ultimate Strength (Su):       {sigma_u:.1f} MPa ({sigma_u*0.145038:.1f} ksi)")
    print(f"  - Shear Yield Strength (Ty):   {tau_y:.1f} MPa ({tau_y*0.145038:.1f} ksi)")
    print(f"  - Young's Modulus (E):         {E:,.0f} MPa (vs 68,900 MPa for 6061-T6 -> 3.0x stiffer!)")
    print(f"  - Endurance Limit (Se'):       {S_e_mod:.1f} MPa")
    
    # --------------------------------------------------------------------------
    # 3. Geometric Parameters (1/2" Plate)
    # --------------------------------------------------------------------------
    t_plate = 12.70 # mm (0.500 in)
    
    # Mustang Ear: 13.0 mm hole, 37.0 mm outer boss (R = 18.5 mm)
    d_m = 13.00
    r_m_boss = 18.50
    w_m_wall = r_m_boss - (d_m / 2.0) # 12.0 mm solid wall
    a_m_shear = 2.0 * w_m_wall * t_plate # 304.8 mm^2
    a_m_bearing = d_m * t_plate # 165.1 mm^2
    
    # SVT Knuckle Ear: 12.0 mm hole, 32.0 mm outer boss (R = 16.0 mm)
    d_s = 12.00
    r_s_boss = 16.00
    w_s_wall = r_s_boss - (d_s / 2.0) # 10.0 mm solid wall
    a_s_shear = 2.0 * w_s_wall * t_plate # 254.0 mm^2
    a_s_bearing = d_s * t_plate # 152.4 mm^2
    
    # M12x1.75 Internal Tapped Thread Engagement in 1018 Steel:
    # Length of thread engagement = t_plate = 12.7 mm
    # Standard formula for internal thread shear area: A_ts = 0.75 * pi * d * L
    a_thread_shear = 0.75 * math.pi * d_s * t_plate # 359.1 mm^2
    
    print("\n[3] Critical Section Properties (1/2\" / 12.70 mm Plate)")
    print(f"  - Mustang Ear Solid Radial Wall: {w_m_wall:.2f} mm")
    print(f"  - Mustang Ear Net Shear Area:    {a_m_shear:.1f} mm^2 (0.472 in^2)")
    print(f"  - Mustang Hole Projected Area:   {a_m_bearing:.1f} mm^2")
    print(f"  - SVT Ear Solid Radial Wall:     {w_s_wall:.2f} mm")
    print(f"  - SVT Ear Net Shear Area:        {a_s_shear:.1f} mm^2 (0.394 in^2)")
    print(f"  - Tapped M12x1.75 Shear Area:    {a_thread_shear:.1f} mm^2")
    
    # --------------------------------------------------------------------------
    # 4. Stress Calculations & Factors of Safety (FOS)
    # --------------------------------------------------------------------------
    # Mode 1: Shear tear-out of Mustang ear
    tau_m = f_bolt_shear / a_m_shear
    fos_m_shear = tau_y / tau_m
    
    # Mode 2: Hole bearing stress on Mustang 13mm hole
    sigma_bear_m = f_bolt_shear / a_m_bearing
    # Allowable bearing stress in steel = 0.90 * Sy (or 1.5 * Sy per AISC)
    fos_bear_m = (0.90 * sigma_y) / sigma_bear_m
    
    # Mode 3: Shear tear-out of SVT Knuckle ear
    tau_s = f_bolt_shear / a_s_shear
    fos_s_shear = tau_y / tau_s
    
    # Mode 4: Tapped M12x1.75 Thread Stripping / Pull-Out
    tau_thread = f_bolt_shear / a_thread_shear
    fos_thread = tau_y / tau_thread
    thread_strip_capacity_N = a_thread_shear * tau_y
    
    # Mode 5: Clamping Preload & Joint Friction Grip
    # Class 10.9 M12x1.75 fastener torqued to 82 ft-lbs (111 N*m)
    # Preload F_p = T / (k * d) with k = 0.18
    f_preload = 111.0 / (0.18 * 0.012) # ~51,389 N (11,550 lbs clamp per bolt!)
    # Friction grip coefficient for clean steel-on-steel: mu = 0.35
    f_friction_grip_per_bolt = 0.35 * f_preload # 17,986 N per bolt!
    f_friction_grip_joint = 2.0 * f_friction_grip_per_bolt # 35,972 N total
    fos_slip = f_friction_grip_joint / f_caliper_tangential
    
    # Mode 6: Structural Bending Deflection across the 14.7 mm vertical delta
    # Cantilever arm model: L = 14.7 mm, width ~30 mm average, thickness = 12.7 mm
    w_beam = 30.0 # mm
    i_beam = (w_beam * (t_plate**3)) / 12.0 # mm^4
    delta_bending_mm = (f_bolt_shear * (14.7**3)) / (3.0 * E * i_beam)
    # Stress in bending
    m_bend = f_bolt_shear * 14.7 # N*mm
    sigma_bend = (m_bend * (t_plate / 2.0)) / i_beam
    fos_bend = sigma_y / sigma_bend
    
    print("\n[4] Structural Stress Analysis & Factors of Safety (FOS)")
    print(f"  [+] Mode 1: Mustang Ear Direct Shear")
    print(f"      - Shear Stress:             {tau_m:.2f} MPa")
    print(f"      - Factor of Safety (FOS):   {fos_m_shear:.2f}x  (Yield Capacity: {a_m_shear*tau_y*0.224809:,.0f} lbs)")
    print(f"  [+] Mode 2: Mustang Hole Bearing Stress")
    print(f"      - Bearing Stress:           {sigma_bear_m:.2f} MPa")
    print(f"      - Factor of Safety (FOS):   {fos_bear_m:.2f}x")
    print(f"  [+] Mode 3: SVT Knuckle Ear Direct Shear")
    print(f"      - Shear Stress:             {tau_s:.2f} MPa")
    print(f"      - Factor of Safety (FOS):   {fos_s_shear:.2f}x  (Yield Capacity: {a_s_shear*tau_y*0.224809:,.0f} lbs)")
    print(f"  [+] Mode 4: Tapped M12x1.75 Thread Stripping (Full 12.7mm Engagement)")
    print(f"      - Thread Shear Stress:      {tau_thread:.2f} MPa")
    print(f"      - Thread Pull-out Capacity: {thread_strip_capacity_N:.0f} N ({thread_strip_capacity_N*0.224809:,.0f} lbs)")
    print(f"      - Factor of Safety (FOS):   {fos_thread:.2f}x  (Virtually Indestructible)")
    print(f"  [+] Mode 5: Joint Clamping Friction Grip (82 ft-lbs on Class 10.9)")
    print(f"      - Bolt Clamp Preload:       {f_preload:.0f} N ({f_preload*0.224809:,.0f} lbs per bolt)")
    print(f"      - Friction Grip Slip Load:  {f_friction_grip_joint:.0f} N ({f_friction_grip_joint*0.224809:,.0f} lbs)")
    print(f"      - Factor of Safety (Slip):  {fos_slip:.2f}x  (Joint will not slip before bolt bears)")
    print(f"  [+] Mode 6: Bracket Bending & Flex Under 1.2g Stop")
    print(f"      - Max Bending Stress:       {sigma_bend:.2f} MPa (FOS: {fos_bend:.2f}x)")
    print(f"      - Total Bracket Deflection: {delta_bending_mm*1000.0:.2f} microns ({delta_bending_mm*0.03937*1000.0:.3f} mils)")
    print(f"      - Flex comparison:          3x stiffer than 6061-T6 aluminum (aluminum would flex ~{delta_bending_mm*3*1000.0:.1f} um)")
    
    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("SUPERSEDED: These legacy 1/2-inch checks do not validate the 3/8-inch assembly.")
    print("See analysis_2026-11-07/STRUCTURAL_REVIEW.md; no structural approval is issued.")
    print("=" * 80)

if __name__ == '__main__':
    raise SystemExit("Legacy analysis withdrawn: incorrect geometry/preload assumptions. "
                     "See analysis_2026-11-07/STRUCTURAL_REVIEW.md and run_fea.py. "
                     "Original script is preserved in legacy_snapshot for audit only.")
