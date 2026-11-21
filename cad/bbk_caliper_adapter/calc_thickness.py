import math

tau_y = 213.6 # MPa
f_bolt = 7171.1 # N (1,612 lbs)

for t, name in [(9.525, "3/8 inch (9.525 mm)"), (10.0, "10.0 mm"), (12.7, "1/2 inch (12.70 mm)")]:
    a_m = 2.0 * 12.0 * t
    a_s = 2.0 * 10.0 * t
    a_th = 0.75 * math.pi * 12.0 * t
    pullout = a_th * tau_y * 0.224809
    wt_lbs = 67.6 * (t / 12.7) * 7.87 * 0.00220462
    fos_m = tau_y / (f_bolt / a_m)
    fos_s = tau_y / (f_bolt / a_s)
    fos_th = tau_y / (f_bolt / a_th)
    print(f"{name}:")
    print(f"  Mustang Ear Shear FOS: {fos_m:.2f}x")
    print(f"  SVT Ear Shear FOS:     {fos_s:.2f}x")
    print(f"  Thread Stripping FOS:  {fos_th:.2f}x ({pullout:,.0f} lbs capacity)")
    print(f"  Weight:                {wt_lbs:.2f} lbs ({wt_lbs/0.00220462:.0f} g)")
