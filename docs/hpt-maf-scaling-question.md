# UJAHAS3 MAF scaling question — draft, not sent

Subject: Black Oak UJAHAS3 ECM12163 MAF table units versus Scanner airflow

I am working with a2004FocusSVT, BlackOak1472KPWM, UJAHAS3, using VCM Suite
5.3.1332Beta. Before changing its MAF transfer, please clarify the definition
and conversion for ECM12163 MAF Airflow vs.Voltage and Scanner2300/2302.

The saved tune shows0.60V ->4.9 with Editor unitslb/h. Changing display units
tolb/min yieldsapproximately0.082; reopening the unchanged file retains that
conversion. Editor's own description states the lookup supplies airflow(g/sec).
The native Scanner CSV reports MassAirflow inlb/min and rawMAF voltage inV.
At warm idle, voltage is0.517–0.639V and flow about0.58lb/min. Across that interval,
loggedlb/h divided by the interpolated Editor number has median7.58, near the
g/s-to-lb/h factor7.94, with timing/temperature corrections not fully isolated.

Please confirm:

1. What are the actual raw/engineering units and conversion for ECM12163 on
   this exact strategy? Is the display conversion correct in this build?
2. Are Scanner2300 flow and2302 voltage the appropriate signals for validating
   that lookup, or are either scaled/filtered differently on this PCM?
3. Is there a strategy-specific global scaling factor affecting MAF, injector
   slopes and inferred load that must be retained? What identifies it?
4. Which validated Editor values should represent a manufacturer reference of
   3.81660676g/s (=30.29103935lb/h) at0.60V without applying a conversion twice?

Hardware: owner-confirmed plain PMASHPX in a PMAS3-inch blow-through housing,
LMR1996–2004Mustang kit (listing LRS-MH30HPXS), installed after turbo near throttle.
Manufacturer's PMAS3ProTubeII reference remains subject to housing revision/
serial confirmation. The current concern is definition/scaling, not a request
to approve an unverified generic MAF curve.

Prepared evidence: exactv018HPT/hash, nativev018Stage2AHPL/CSV and actualchannel
XML, read-only Editor observations, PMAS workbook URL/hash and reference math.
Review privacy and attach relevant files/vehicle-connected InfoLog before any
submission. No support request or external message has been sent.
