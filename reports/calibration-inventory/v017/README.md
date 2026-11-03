# v017 calibration inventory

Source: `v017-o2-readiness-600.hpt`. SHA-256: `9597BAB2DB9DEB063298C7814F8B9930C530DBDB3FE114D80F8EE44B6463E7CE`.

Captured 342/342 exposed parameter entries: 96 tables, 246 scalar/switch entries; 4692 table cells including axes/headers.

This is the saved file in Advanced view, not an ECU readback. Values retain Editor display precision. Hidden firmware controls and raw numerical precision are not inferred. Matching descriptions are included only when their parameter identity was verified. Unmatched help text in raw controls is UI evidence, not an attributed parameter description.

[Searchable index](index.csv) · [All table cells](table-cells.csv) · [Combined JSON](inventory.json) · [Coverage manifest](manifest.json)

The v016 parent differs only in ECM12115 (520 F rather than600 F) and Notes. This relationship was verified through the saved-file Editor comparison.

Raw tables preserve row/column coordinates, including axis/header cells. Axis units are not universally exposed by UI Automation; use verified descriptions where available. Missing metadata is listed in the manifest. A/B and unnamed checkboxes in raw controls may be UI selectors and must not be interpreted as calibration switches.

| ID | Parameter path | Value / grid | Capture |
| --- | --- | --- | --- |
| 20250 | Engine / General / Engine / Number Of Cylinders | 4 | [JSON](000.json) |
| 44205 | Engine / General / Engine / Standard Air Charge | 0.00136 | [JSON](001.json) |
| 44213 | Engine / Idle / General / General / Idle Control Enable RPM Error | 200 | [JSON](002.json) |
| 12262 | Engine / Idle / General / General / Idle Control Disable RPM Error | 30 | [JSON](003.json) |
| 44214 | Engine / Idle / General / General / Idle Minimum VSS | 3 | [JSON](004.json) |
| 12267 | Engine / Idle / General / General / Idle In Gear to P/N Delay | 2.00 | [JSON](005.json) |
| 44215 | Engine / Idle / General / General / Idle AC Delay Initial vs. RPM | 7 x 2 (including axis/header cells) | [JSON](006.json) |
| 32937 | Engine / Idle / General / General / Idle AC Delay Cycling vs. RPM | 7 x 2 (including axis/header cells) | [JSON](007.json) |
| 44218 | Engine / Idle / RPM / Transmission Based Setpoint / Target Idle Speed Park/Neutral  | 950 | [JSON](008.json) |
| 44217 | Engine / Idle / RPM / Transmission Based Setpoint / Target Idle Speed Drive | 950 | [JSON](009.json) |
| 44224 | Engine / Idle / RPM / Idle Adders / Fan High Speed Idle | Enabled | [JSON](010.json) |
| 32955 | Engine / Idle / RPM / Idle Adders / Idle RPM Adder vs. ECT | 9 x 2 (including axis/header cells) | [JSON](011.json) |
| 32957 | Engine / Idle / RPM / Idle Adders / Idle RPM Adder vs. IAT | 8 x 2 (including axis/header cells) | [JSON](012.json) |
| 32959 | Engine / Idle / RPM / Idle Adders / Idle RPM Adder vs. Startup ECT | 8 x 2 (including axis/header cells) | [JSON](013.json) |
| 32961 | Engine / Idle / RPM / Idle Adders / Idle RPM Adder vs. Startup IAT | 8 x 2 (including axis/header cells) | [JSON](014.json) |
| 44221 | Engine / Idle / RPM / Startup / Startup Idle Adder Time Max | 0.0 | [JSON](015.json) |
| 12255 | Engine / Idle / RPM / Startup / Startup Idle Speed Adder | 0 | [JSON](016.json) |
| 44924 | Engine / Idle / RPM / Climate Control Setpoint / Holding Delay Time After AC Disengagement (Air Conditioning) | 0.0 | [JSON](017.json) |
| 44239 | Engine / Idle / Airflow / Idle Airflow / Idle Airflow (Drive) vs. Desired Idle RPM | 11 x 2 (including axis/header cells) | [JSON](018.json) |
| 44240 | Engine / Idle / Airflow / Idle Airflow / Idle Airflow Mult (Drive) vs. ECT vs. ERT | 7 x 8 (including axis/header cells) | [JSON](019.json) |
| 44242 | Engine / Idle / Airflow / Idle Airflow / Idle Airflow (P/N) vs. Desired Idle RPM | 11 x 2 (including axis/header cells) | [JSON](020.json) |
| 44243 | Engine / Idle / Airflow / Idle Airflow / Idle Airflow Mult (P/N) vs. ECT vs. ERT | 7 x 8 (including axis/header cells) | [JSON](021.json) |
| 44247 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot Low Limit to Enable | 0.07 | [JSON](022.json) |
| 44248 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot Minimum VSS to Enable | 4 | [JSON](023.json) |
| 44249 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot VSS Hysteresis | 2 | [JSON](024.json) |
| 44252 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot Neutral Clip Modifier | 1.00 | [JSON](025.json) |
| 32984 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot Decay vs. Dashpot Airflow | 8 x 2 (including axis/header cells) | [JSON](026.json) |
| 32986 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot Minimum vs. Desired Idle RPM | 6 x 2 (including axis/header cells) | [JSON](027.json) |
| 32988 | Engine / Idle / Airflow / Dashpot Airflow / Idle Dashpot Pre-Position vs. RPM | 7 x 2 (including axis/header cells) | [JSON](028.json) |
| 32945 | Engine / Idle / Airflow / Dashpot Clip / Idle Dashpot Max Clip vs. VSS | 7 x 2 (including axis/header cells) | [JSON](029.json) |
| 6950 | Engine / Airflow / General / General / Manifold Vacuum Multiplier | 0.000 | [JSON](030.json) |
| 35184 | Engine / Airflow / General / MAP / Estimated Airflow Leakage | 0.03 | [JSON](031.json) |
| 19006 | Engine / Airflow / General / Barometric Pressure / Barometric Pressure Min | 15.00 | [JSON](032.json) |
| 19005 | Engine / Airflow / General / Barometric Pressure / Barometric Pressure Max | 31.88 | [JSON](033.json) |
| 12163 | Engine / Airflow / General / MAF Calibration / MAF Airflow vs. Voltage | 2 x 31 (including axis/header cells) | [JSON](034.json) |
| 44318 | Engine / Airflow / General / MAF Calibration / MAF Temp Compensation vs. Airflow vs. IAT | 10 x 11 (including axis/header cells) | [JSON](035.json) |
| 45258 | Engine / Airflow / General / MAF Calibration / MAF Air Charge Delay Compensation Switch | Disabled | [JSON](036.json) |
| 44319 | Engine / Airflow / General / MAF Calibration / Load With Failed MAF vs. RPM vs. TPS | 11 x 11 (including axis/header cells) | [JSON](037.json) |
| 44320 | Engine / Airflow / General / MAF Calibration / Load with failed MAF (IMRC Open) vs. RPM vs. TPS | 11 x 11 (including axis/header cells) | [JSON](038.json) |
| 44321 | Engine / Airflow / General / MAF Calibration / MAF Backflow Entry TPS vs. RPM | 9 x 2 (including axis/header cells) | [JSON](039.json) |
| 44322 | Engine / Airflow / General / MAF Calibration / MAF Backflow Entry TPS (low throttle) vs. RPM | 9 x 2 (including axis/header cells) | [JSON](040.json) |
| 2006 | Engine / Airflow / General / MAF Calibration / MAF Backflow Low Throttle Enable | Disabled | [JSON](041.json) |
| 2005 | Engine / Airflow / General / MAF Calibration / MAF Adaption | Disabled | [JSON](042.json) |
| 12000 | Engine / Airflow / General / MAF Calibration / Default Baro | 27.00 | [JSON](043.json) |
| 44323 | Engine / Airflow / General / MAF Calibration / Cylair Filter | Enabled | [JSON](044.json) |
| 44324 | Engine / Airflow / General / MAF Calibration / Cylair Anticipation Logic | Disabled | [JSON](045.json) |
| 44325 | Engine / Airflow / General / MAF Calibration / Cylair Use Idle Filter Coeff | Enabled | [JSON](046.json) |
| 12002 | Engine / Airflow / General / MAF Calibration / Cylair Idle Filter Coeff | 0.11 | [JSON](047.json) |
| 12001 | Engine / Airflow / General / MAF Calibration / Cylair WOT Multiplier | 2.00 | [JSON](048.json) |
| 12004 | Engine / Airflow / General / MAF Calibration / Cylair Max Multiplier | 0.90 | [JSON](049.json) |
| 13419 | Engine / Airflow / General / MAF Calibration / Percent Load Switch | MAF Corrected | [JSON](050.json) |
| 32042 | Engine / Airflow / Speed Density / General / VE Correction (Density) vs. ACT | 8 x 2 (including axis/header cells) | [JSON](051.json) |
| 32044 | Engine / Airflow / Speed Density / General / VE Correction vs. ACT vs. ECT | 9 x 9 (including axis/header cells) | [JSON](052.json) |
| 44344 | Engine / Airflow / Speed Density / General / Airmass TPS Failed vs. RPM | 9 x 2 (including axis/header cells) | [JSON](053.json) |
| 12003 | Engine / Airflow / Speed Density / Dynamic Airflow / Intake Manifold Volume | 5.40 | [JSON](054.json) |
| 18224 | Engine / Airflow / Speed Density / Aircharge / Peak Load at WOT (Sea Level) | 13 x 2 (including axis/header cells) | [JSON](055.json) |
| 2042 | Engine / Airflow / Electronic Throttle / General / Electronic Throttle Control Enable | Not Fitted | [JSON](056.json) |
| 2019 | Engine / Airflow / IMRC / General / IMRC Switch | Disabled | [JSON](057.json) |
| 44397 | Engine / Airflow / IMRC / General / IMRC Sensor | Disabled | [JSON](058.json) |
| 25253 | Engine / Airflow / IMRC / General / IMRC Type | Electric | [JSON](059.json) |
| 25262 | Engine / Airflow / IMRC / General / IMRC Opening RPM vs TPS | 8 x 2 (including axis/header cells) | [JSON](060.json) |
| 44401 | Engine / Airflow / Variable Camshaft / General / Variable Camshaft | Enabled | [JSON](061.json) |
| 44420 | Engine / Airflow / Variable Camshaft / General / VCT Mode | Intake Only | [JSON](062.json) |
| 44403 | Engine / Airflow / Variable Camshaft / Configuration / VCT Startup Delay vs. Temp | 10 x 2 (including axis/header cells) | [JSON](063.json) |
| 44404 | Engine / Airflow / Variable Camshaft / Configuration / VCT Low Speed Slope | 0.00072 | [JSON](064.json) |
| 44405 | Engine / Airflow / Variable Camshaft / Configuration / VCT High Speed Slope | 0.00049 | [JSON](065.json) |
| 12502 | Engine / Airflow / Variable Camshaft / Configuration / VCT Low Speed Offset | -0.62250 | [JSON](066.json) |
| 44406 | Engine / Airflow / Variable Camshaft / Configuration / VCT High Speed Offset | 0.25000 | [JSON](067.json) |
| 44407 | Engine / Airflow / Variable Camshaft / Configuration / VCT High/Low Speed Breakpoint | 2,900.00 | [JSON](068.json) |
| 44412 | Engine / Airflow / Variable Camshaft / Configuration / VCT Angle vs. RPM vs. Load | 10 x 12 (including axis/header cells) | [JSON](069.json) |
| 44413 | Engine / Airflow / Variable Camshaft / Configuration / VCT Angle Mult vs. IAT | 8 x 2 (including axis/header cells) | [JSON](070.json) |
| 44414 | Engine / Airflow / Variable Camshaft / Configuration / VCT Angle Mult vs. ECT | 8 x 2 (including axis/header cells) | [JSON](071.json) |
| 44557 | Engine / Exhaust / Temperature / Exhaust Gas Temperature / Exhaust Flange Temperature | 7 x 7 (including axis/header cells) | [JSON](072.json) |
| 44430 | Engine / Fuel / General / General / Part Throttle TPS Enable | 8.00 | [JSON](073.json) |
| 44431 | Engine / Fuel / General / General / Wide Open Throttle TPS Enable | 7 x 2 (including axis/header cells) | [JSON](074.json) |
| 2300 | Engine / Fuel / General / Stoichiometry / Stoichiometric Air Fuel Ratio | 14.64 | [JSON](075.json) |
| 12016 | Engine / Fuel / General / Injector Control / Injector Pressure Drop Reference | 40.00 | [JSON](076.json) |
| 12010 | Engine / Fuel / General / Injector Control / Injector Flow Rate Low | 0.017500000 | [JSON](077.json) |
| 32062 | Engine / Fuel / General / Injector Control / Injector Flow Rate Low Mult vs. Pressure | 7 x 2 (including axis/header cells) | [JSON](078.json) |
| 12011 | Engine / Fuel / General / Injector Control / Injector Flow Rate High | 0.016700000 | [JSON](079.json) |
| 32060 | Engine / Fuel / General / Injector Control / Injector Flow Rate High Mult vs. Pressure | 7 x 2 (including axis/header cells) | [JSON](080.json) |
| 12012 | Engine / Fuel / General / Injector Control / Injector Breakpoint | 0.00003360 | [JSON](081.json) |
| 32064 | Engine / Fuel / General / Injector Control / Injector Breakpoint Mult vs. Pressure | 7 x 2 (including axis/header cells) | [JSON](082.json) |
| 32047 | Engine / Fuel / General / Injector Control / Injector Pressure Compensation | Enabled | [JSON](083.json) |
| 12015 | Engine / Fuel / General / Injector Control / Injector PW Minimum | 0.00050000 | [JSON](084.json) |
| 32050 | Engine / Fuel / General / Injector Control / Injector Offset vs IGNV | 13 x 2 (including axis/header cells) | [JSON](085.json) |
| 32052 | Engine / Fuel / General / Injector Control / Injector Offset Mult vs. Pressure | 8 x 2 (including axis/header cells) | [JSON](086.json) |
| 32085 | Engine / Fuel / General / Injector Control / Injector Timing vs. ECT | 7 x 2 (including axis/header cells) | [JSON](087.json) |
| 12019 | Engine / Fuel / General / Injector Control / Injector Spray Delay | 0.00 | [JSON](088.json) |
| 12018 | Engine / Fuel / General / Injector Control / Injector Intake Valve Open | 373.00 | [JSON](089.json) |
| 44519 | Engine / Fuel / General / Cranking Fuel / Fuel Cranking vs. ECT | 13 x 2 (including axis/header cells) | [JSON](090.json) |
| 1165 | Engine / Fuel / Oxygen Sensors / General / Fore/Aft Oxygen Sensor Control | Disabled | [JSON](091.json) |
| 12115 | Engine / Fuel / Oxygen Sensors / Feedback / Closed Loop O2 Sensor Temp | 600.00 | [JSON](092.json) |
| 45358 | Engine / Fuel / Oxygen Sensors / Feedback / Closed Loop Delay - ECT Cold | 254 | [JSON](093.json) |
| 45359 | Engine / Fuel / Oxygen Sensors / Feedback / Closed Loop Delay - ECT Warm | 254 | [JSON](094.json) |
| 45360 | Engine / Fuel / Oxygen Sensors / Feedback / Closed Loop Delay - ECT Hot | 254 | [JSON](095.json) |
| 12462 | Engine / Fuel / Oxygen Sensors / Feedback / Closed Loop Enable Delay | 10 x 2 (including axis/header cells) | [JSON](096.json) |
| 230 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Enable | Disabled | [JSON](097.json) |
| 2502 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Min ECT | 160 | [JSON](098.json) |
| 2503 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Max ECT | 230 | [JSON](099.json) |
| 2530 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Max Limit | 0.75 | [JSON](100.json) |
| 2531 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Min Limit | 0.25 | [JSON](101.json) |
| 14682 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Table Select | vs. Airflow | [JSON](102.json) |
| 14683 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning vs. Load | 10 x 11 (including axis/header cells) | [JSON](103.json) |
| 12134 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Min IAT | -20.00 | [JSON](104.json) |
| 44507 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Max IAT | 190.00 | [JSON](105.json) |
| 44508 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Min Load | 0.1600 | [JSON](106.json) |
| 44509 | Engine / Fuel / Oxygen Sensors / Feedback / LTFT Learning Max TPS | 1,023.00 | [JSON](107.json) |
| 32916 | Engine / Fuel / Oxygen Sensors / Heaters / O2S1 Heater Duty Cycle | 8 x 2 (including axis/header cells) | [JSON](108.json) |
| 44211 | Engine / Fuel / Oxygen Sensors / Heaters / O2 Heater Tip Temperature vs. EGT vs. Duty Cycle | 9 x 9 (including axis/header cells) | [JSON](109.json) |
| 12170 | Engine / Fuel / Oxygen Sensors / Sensor Bias / O2 Closed Loop Bias Min | -0.030 | [JSON](110.json) |
| 32905 | Engine / Fuel / Oxygen Sensors / Sensor Bias / O2 Closed Loop Bias Bank 1 | 6 x 6 (including axis/header cells) | [JSON](111.json) |
| 32908 | Engine / Fuel / Oxygen Sensors / Sensor Bias / O2 Closed Loop Bias Bank 2 | 6 x 6 (including axis/header cells) | [JSON](112.json) |
| 44521 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - Load Min | 0.15 | [JSON](113.json) |
| 44522 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - Load Max | 0.90 | [JSON](114.json) |
| 44523 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - RPM Min | 1,000.00 | [JSON](115.json) |
| 44524 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - RPM Max | 4,000.00 | [JSON](116.json) |
| 44525 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - Sec Min | 0.10 | [JSON](117.json) |
| 44526 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - Sec Max | 2.00 | [JSON](118.json) |
| 44527 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - Time Min | -1.00 | [JSON](119.json) |
| 44528 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - Time Max | 1.00 | [JSON](120.json) |
| 44529 | Engine / Fuel / Oxygen Sensors / Transport Delay / O2 Transport Delay Learn - ECT Min | 160.00 | [JSON](121.json) |
| 44502 | Engine / Fuel / Open Loop / Base / General / Open/Closed Loop Hot Start ECT | 150.00 | [JSON](122.json) |
| 12111 | Engine / Fuel / Open Loop / Base / General / Open/Closed Loop Cold Start ECT | 56.00 | [JSON](123.json) |
| 32725 | Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Delay vs. RPM vs. Gear | 6 x 11 (including axis/header cells) | [JSON](124.json) |
| 44503 | Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Delay Ramp | 0.00 | [JSON](125.json) |
| 44504 | Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Delay Blending Ramp | 0.10 | [JSON](126.json) |
| 44505 | Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Delay Maximum | 2.50 | [JSON](127.json) |
| 32720 | Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Decel Load vs. RPM | 8 x 2 (including axis/header cells) | [JSON](128.json) |
| 32731 | Engine / Fuel / Open Loop / Base / Open Loop / Open Loop Fuel TPS Thresh vs. RPM | 8 x 2 (including axis/header cells) | [JSON](129.json) |
| 44506 | Engine / Fuel / Open Loop / Base / Open Loop / Fuel Adaptive WOT Switch | Disabled | [JSON](130.json) |
| 44515 | Engine / Fuel / Open Loop / Base / Base Fuel / Fuel Base Enable Time | 10.00 | [JSON](131.json) |
| 44511 | Engine / Fuel / Open Loop / Base / Base Fuel / Fuel Base vs. RPM vs. TPS | 9 x 11 (including axis/header cells) | [JSON](132.json) |
| 44168 | Engine / Fuel / Open Loop / Base / Base Fuel / Cylinder Cutoff Lambda Limit (Catalyst Protection) | 1.30 | [JSON](133.json) |
| 44169 | Engine / Fuel / Open Loop / Base / Base Fuel / Cylinder Cutoff Lambda To Achieve Desired Torque Reduction | 2 x 8 (including axis/header cells) | [JSON](134.json) |
| 12140 | Engine / Fuel / Open Loop / Base / Base Fuel / Manual Fuel Override | Disabled | [JSON](135.json) |
| 12141 | Engine / Fuel / Open Loop / Base / Base Fuel / Manual Fuel Override Target Lambda | 1.00 | [JSON](136.json) |
| 44513 | Engine / Fuel / Open Loop / Base / Cold/Warmup / Fuel Base Enable ECT | 158.00 | [JSON](137.json) |
| 44514 | Engine / Fuel / Open Loop / Base / Cold/Warmup / Fuel Base Disable ECT | 90.00 | [JSON](138.json) |
| 44512 | Engine / Fuel / Open Loop / Base / Cold/Warmup / Fuel Base Cold vs. ECT vs. Load | 9 x 13 (including axis/header cells) | [JSON](139.json) |
| 44516 | Engine / Fuel / Open Loop / Base / Cold/Warmup / Fuel Base Cold Enrich Decay vs. ECT vs. ERT | 9 x 13 (including axis/header cells) | [JSON](140.json) |
| 32748 | Engine / Fuel / Open Loop / Base / Cold/Warmup / Fuel Base Startup Enleanment for Exhaust Warm Up | 9 x 13 (including axis/header cells) | [JSON](141.json) |
| 32740 | Engine / Fuel / Open Loop / Base / Lost Fuel / Fuel Base Open Loop Lost Fuel vs. ECT. vs. Load | 9 x 13 (including axis/header cells) | [JSON](142.json) |
| 32742 | Engine / Fuel / Open Loop / Base / Lost Fuel / Fuel Base Startup Open Loop Lost Fuel vs. ECT vs. ERT | 9 x 13 (including axis/header cells) | [JSON](143.json) |
| 44550 | Engine / Fuel / Temperature Control / Exhaust Manifold Protection / Flange Temp Control | Enabled | [JSON](144.json) |
| 44551 | Engine / Fuel / Temperature Control / Exhaust Manifold Protection / Flange OT Enable Temp | 1,560 | [JSON](145.json) |
| 23055 | Engine / Fuel / Temperature Control / Exhaust Manifold Protection / Flange OT Disable Temp | 1,540 | [JSON](146.json) |
| 44546 | Engine / Fuel / Temperature Control / Catalyst Protection / Catalyst Temperature Control | Enabled | [JSON](147.json) |
| 44547 | Engine / Fuel / Temperature Control / Catalyst Protection / COT Stage 1 Temp | 1,650 | [JSON](148.json) |
| 23057 | Engine / Fuel / Temperature Control / Catalyst Protection / COT OT Temp Disable | 1,600 | [JSON](149.json) |
| 44549 | Engine / Fuel / Temperature Control / Catalyst Protection / Cat Temp Control Max Enrichment | 0.83 | [JSON](150.json) |
| 49895 | Engine / Fuel / Temperature Control / Catalyst Protection / Cat Temp Control Base Enrichment | 0.95 | [JSON](151.json) |
| 44554 | Engine / Fuel / Temperature Control / Component Protection / O2 Temp Control | Enabled | [JSON](152.json) |
| 44555 | Engine / Fuel / Temperature Control / Component Protection / O2 Sens OT Enable Temp | 1,700 | [JSON](153.json) |
| 23056 | Engine / Fuel / Temperature Control / Component Protection / O2 Sens OT Disable Temp | 1,645 | [JSON](154.json) |
| 2070 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM Limit Cutoff | 7,400 | [JSON](155.json) |
| 44473 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM Limit Neutral Cutoff | 7,400 | [JSON](156.json) |
| 47997 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM to Enable Torque Ratio Based Limiting | 7,400 | [JSON](157.json) |
| 47998 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM to Disable Torque Ratio Based Limiting | 7,100 | [JSON](158.json) |
| 43881 | Engine / Fuel / Cutoff, DFCO / RPM Limits / Torque Ratio Limiting | 8 x 2 (including axis/header cells) | [JSON](159.json) |
| 44475 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM Limit Neutral Exit Speed | 5 | [JSON](160.json) |
| 12215 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM Limit Neutral Min Load | 1.99 | [JSON](161.json) |
| 12216 | Engine / Fuel / Cutoff, DFCO / RPM Limits / RPM Limit Neutral Max Load | 0.00 | [JSON](162.json) |
| 2251 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Minimum ECT to Allow DFCO | 165 | [JSON](163.json) |
| 2290 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Minimum RPM to Allow DFCO | 1,200 | [JSON](164.json) |
| 2291 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Maximum RPM to Disable DFCO | 750 | [JSON](165.json) |
| 44491 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Minimum VSS to Allow DFCO | 35.00 | [JSON](166.json) |
| 44492 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Maximum VSS to Disable DFCO | 12.00 | [JSON](167.json) |
| 12156 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Maximum Load to Disable DFCO | 1.00 | [JSON](168.json) |
| 44493 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / Maximum N/V Ratio to Disable DFCO | 140.00 | [JSON](169.json) |
| 44494 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / DFCO Torque Ramp On Rate | 0.75 | [JSON](170.json) |
| 44495 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / DFCO Torque Ramp Off Rate | 1.00 | [JSON](171.json) |
| 44496 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / DFCO Closed Throttle Delay | 3.00 | [JSON](172.json) |
| 44497 | Engine / Fuel / Cutoff, DFCO / Deceleration Fuel Cutoff / DFCO Closed Throttle Delay Extended | 20.00 | [JSON](173.json) |
| 33262 | Engine / Fuel / Transient / Accelerator Pump / Accelerator Pump Threshold for Tip In | 0.002 | [JSON](174.json) |
| 33263 | Engine / Fuel / Transient / Accelerator Pump / Accelerator Pump Tip In Filter | 1.000 | [JSON](175.json) |
| 33264 | Engine / Fuel / Transient / Accelerator Pump / Accelerator Pump Tip In Multiplier | 0.000 | [JSON](176.json) |
| 33265 | Engine / Fuel / Transient / Accelerator Pump / Accelerator Pump Threshold for Tip out | -0.002 | [JSON](177.json) |
| 33266 | Engine / Fuel / Transient / Accelerator Pump / Accelerator Pump Tip Out Filter | 1.000 | [JSON](178.json) |
| 33267 | Engine / Fuel / Transient / Accelerator Pump / Accelerator Pump Tip Out Multiplier | 0.000 | [JSON](179.json) |
| 44569 | Engine / Spark / Advance / Base / Spark Maximum Cold Start Adder vs. RPM vs. Load | 6 x 7 (including axis/header cells) | [JSON](180.json) |
| 11545 | Engine / Spark / Advance / Base / Spark Emissions Reduction Adder (Driver Demand vs. Catalyst Temperature) | 7 x 7 (including axis/header cells) | [JSON](181.json) |
| 44600 | Engine / Spark / Advance / Base Corrections / Spark Emissions Retard vs. RPM vs. Load | 6 x 7 (including axis/header cells) | [JSON](182.json) |
| 44599 | Engine / Spark / Advance / Base Corrections / Spark Combustion Noise Retard vs. RPM vs. Load | 10 x 12 (including axis/header cells) | [JSON](183.json) |
| 44583 | Engine / Spark / Advance / Borderline / Spark Borderline Knock vs. RPM vs. Load | 10 x 12 (including axis/header cells) | [JSON](184.json) |
| 32295 | Engine / Spark / Advance / Borderline Corrections / Spark VID Octane Adjust vs. RPM vs. Load | 6 x 7 (including axis/header cells) | [JSON](185.json) |
| 44585 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline Lambda Correction vs. RPM vs. Lambda | 9 x 11 (including axis/header cells) | [JSON](186.json) |
| 44587 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline IAT Correction Base | 8 x 2 (including axis/header cells) | [JSON](187.json) |
| 44588 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline IAT Correction Mult vs. RPM vs. Load | 6 x 7 (including axis/header cells) | [JSON](188.json) |
| 44589 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline ECT Correction vs. ECT | 8 x 2 (including axis/header cells) | [JSON](189.json) |
| 44590 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline Correction ECT Multiplier | 6 x 7 (including axis/header cells) | [JSON](190.json) |
| 48000 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline EGR Adder | 7 x 2 (including axis/header cells) | [JSON](191.json) |
| 44593 | Engine / Spark / Advance / Borderline Corrections / Spark Borderline VCT Correction vs. RPM vs. Load | 10 x 12 (including axis/header cells) | [JSON](192.json) |
| 32265 | Engine / Spark / Advance / MBT / Spark MBT vs. RPM vs. Load | 10 x 12 (including axis/header cells) | [JSON](193.json) |
| 44586 | Engine / Spark / Advance / MBT Corrections / MBT Spark Lambda Correction | 8 x 2 (including axis/header cells) | [JSON](194.json) |
| 44594 | Engine / Spark / Advance / MBT Corrections / MBT Spark VCT Correction vs. RPM vs. Load | 10 x 12 (including axis/header cells) | [JSON](195.json) |
| 44578 | Engine / Spark / Advance / Idle Spark Advance / Spark Idle In Gear vs. ECT | 6 x 2 (including axis/header cells) | [JSON](196.json) |
| 44579 | Engine / Spark / Advance / Idle Spark Advance / Spark Idle P/N vs. ECT | 6 x 2 (including axis/header cells) | [JSON](197.json) |
| 32360 | Engine / Spark / Advance / Idle Spark Advance / Spark Idle Drive during A/C Dis-engagement | 6 x 7 (including axis/header cells) | [JSON](198.json) |
| 44582 | Engine / Spark / Advance / Idle Spark Advance / Spark Idle Control Minimum | -6.00 | [JSON](199.json) |
| 47996 | Engine / Spark / Advance / Idle Spark Advance / Idle Spark Proportional Gain | 1.000 | [JSON](200.json) |
| 44565 | Engine / Spark / Advance / Startup / Spark Cranking vs. ACT vs. ECT | 6 x 6 (including axis/header cells) | [JSON](201.json) |
| 12908 | Engine / Spark / Advance / Minimum Spark / Minimum Spark Advance | -30 | [JSON](202.json) |
| 42279 | Engine / Spark / Advance / Maximum Spark / Maximum Final Spark Advance | 55.0 | [JSON](203.json) |
| 44568 | Engine / Spark / Advance / Maximum Spark / Spark Maximum Cold Start vs. ECT vs. ERT | 7 x 8 (including axis/header cells) | [JSON](204.json) |
| 44603 | Engine / Spark / Advance / Maximum Spark / Spark Low Load Maximum vs. Time | 8 x 2 (including axis/header cells) | [JSON](205.json) |
| 44606 | Engine / Spark / Advance / Transient / Spark Tip-In Torque Control RPM Max | 7,400 | [JSON](206.json) |
| 44607 | Engine / Spark / Advance / Transient / Spark Tip-In Torque Control RPM Min | 775 | [JSON](207.json) |
| 44608 | Engine / Spark / Advance / Transient / Spark Tip-In Torque Control Airmass Enable | 0.0000599 | [JSON](208.json) |
| 44609 | Engine / Spark / Advance / Transient / Spark Tip-In Torque Control Airmass Disable | 0.0000300 | [JSON](209.json) |
| 20886 | Engine / Spark / Advance / Transient / Spark Tip-In Retard for Detonation Control | 7 x 7 (including axis/header cells) | [JSON](210.json) |
| 20887 | Engine / Spark / Advance / Transient / Spark Tip-In Retard Multiplier | 5 x 2 (including axis/header cells) | [JSON](211.json) |
| 20888 | Engine / Spark / Advance / Transient / Spark Tip-In Retard Maximum | 9 x 2 (including axis/header cells) | [JSON](212.json) |
| 44605 | Engine / Spark / Advance / Transient / Spark Decel vs. RPM vs. ECT | 6 x 8 (including axis/header cells) | [JSON](213.json) |
| 44617 | Engine / Spark / Advance / Global Spark / Spark Global Adder | 0.00 | [JSON](214.json) |
| 44618 | Engine / Spark / Advance / Global Spark / Spark Global Multiplier | 1.00 | [JSON](215.json) |
| 6832 | Engine / Spark / Advance / Global Spark / Spark Global Adder by Cylinder | 11 x 2 (including axis/header cells) | [JSON](216.json) |
| 44602 | Engine / Spark / Advance / Misc / Spark Firing Order vs. Cylinder # | 2 x 13 (including axis/header cells) | [JSON](217.json) |
| 2558 | Engine / Spark / Dwell / Spark Dwell / RPM Max for Coil Test | 4,500 | [JSON](218.json) |
| 20227 | Engine / Spark / Knock Sensors / General / Knock Sensors Fitted | 1 | [JSON](219.json) |
| 44779 | Engine / Torque Model / General / Indicated Torque / Engine Inertia Torque | 0.0150 | [JSON](220.json) |
| 6497 | Engine / Torque Model / General / Fuel Effects / Lambda Efficiency | 2 x 8 (including axis/header cells) | [JSON](221.json) |
| 21343 | Engine / Torque Model / General / Fuel Effects / Ethanol Efficiency | 2 x 9 (including axis/header cells) | [JSON](222.json) |
| 44770 | Engine / Torque Management / General / General / Torque Module | Enabled | [JSON](223.json) |
| 44771 | Engine / Torque Management / General / General / Torque Oscillation Module | Enabled | [JSON](224.json) |
| 44774 | Engine / Torque Management / General / General / Torque Check | Enabled | [JSON](225.json) |
| 44801 | Engine / Torque Management / General / Traction Control System / Traction Control Disable | 135 | [JSON](226.json) |
| 33458 | Engine / Torque Management / General / Torque Ratio / Spark Only Torque Ratio vs. Requestor | 18 x 2 (including axis/header cells) | [JSON](227.json) |
| 44776 | Engine / Torque Management / General / Torque Ratio / Spark Torque Ratio Limit vs. Requestor | 18 x 2 (including axis/header cells) | [JSON](228.json) |
| 19017 | Engine Diagnostics / General / Variable Cam Timing / VCT Test Angle for P0340 | 50 | [JSON](229.json) |
| 19018 | Engine Diagnostics / General / Variable Cam Timing / VCT Test ECT Min | 150.00 | [JSON](230.json) |
| 7277 | Engine Diagnostics / General / Crank Position Sensor / Crank Position Sensor Max Speed | 4,500 | [JSON](231.json) |
| 2018 | Engine Diagnostics / General / Temperature Sensors / ECT Sensor | Enabled | [JSON](232.json) |
| 45631 | Engine Diagnostics / Airflow / Mass Airflow Sensor / MAF Fail RPM | 5,500 | [JSON](233.json) |
| 45634 | Engine Diagnostics / Airflow / Manifold Absolute Pressure Sensor / MAP Intermittent | Disabled | [JSON](234.json) |
| 19030 | Engine Diagnostics / Airflow / Manifold Absolute Pressure Sensor / MAP Intermittent Max | 3 | [JSON](235.json) |
| 19012 | Engine Diagnostics / Misfire / Detection / Misfire Test ECT Max | 250.00 | [JSON](236.json) |
| 19013 | Engine Diagnostics / Misfire / Detection / Misfire Test ECT Min | 20.00 | [JSON](237.json) |
| 19014 | Engine Diagnostics / Misfire / Detection / Misfire Test RPM Min | 100 | [JSON](238.json) |
| 19015 | Engine Diagnostics / Misfire / Detection / Misfire Test Background RPM Max | 7,100 | [JSON](239.json) |
| 19016 | Engine Diagnostics / Misfire / Detection / Misfire Test Background RPM Min | 500 | [JSON](240.json) |
| 39205 | Engine Diagnostics / Misfire / Detection / Misfire Negative Torque Disable Line | 9 x 11 (including axis/header cells) | [JSON](241.json) |
| 39206 | Engine Diagnostics / Misfire / Detection / Misfire Torque Level | 9 x 11 (including axis/header cells) | [JSON](242.json) |
| 19009 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Voltage Max | 1.50 | [JSON](243.json) |
| 9309 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Max RPM | 4,000 | [JSON](244.json) |
| 9310 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Min RPM | 2,000 | [JSON](245.json) |
| 9308 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Delta RPM | 150 | [JSON](246.json) |
| 9306 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Load Max | 0.45 | [JSON](247.json) |
| 9307 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Load Min | 0.20 | [JSON](248.json) |
| 9305 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Delta Load | 0.10 | [JSON](249.json) |
| 9311 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Lambda Max | 1.10 | [JSON](250.json) |
| 9312 | Engine Diagnostics / Exhaust / Oxygen Sensors / O2 Monitor Lambda Min | 0.90 | [JSON](251.json) |
| 19040 | Engine Diagnostics / Exhaust / Rich/Lean DTC / LTFT P0172/P0175 Rich Thresh | 0.7900 | [JSON](252.json) |
| 19041 | Engine Diagnostics / Exhaust / Rich/Lean DTC / LTFT P0171/P0174 Lean Thresh | 1.2000 | [JSON](253.json) |
| 19080 | Engine Diagnostics / Exhaust / Catalyst / Catalyst Monitor Failure Ratio - Bank 1 | 0.700 | [JSON](254.json) |
| 19081 | Engine Diagnostics / Exhaust / Catalyst / Catalyst Monitor Failure Ratio - Bank 2 | 0.700 | [JSON](255.json) |
| 50 | Engine Diagnostics / DTCs / List / Master DTC List | 164 x 3 (including axis/header cells) | [JSON](256.json) |
| 45820 | Transmission / General / General / Trans Automatic Switch | Disabled | [JSON](257.json) |
| 45822 | Transmission / General / General / 4WD Low Switch | Disabled | [JSON](258.json) |
| 45823 | Transmission / General / General / Trans Load Switch | 2 | [JSON](259.json) |
| 45824 | Transmission / General / General / Trans Infer Neutral | Enabled | [JSON](260.json) |
| 45825 | Transmission / General / General / Trans Force Neutral | Disabled | [JSON](261.json) |
| 20088 | Transmission / General / Limits / Output Shaft Speed Limit | 8,000 | [JSON](262.json) |
| 20000 | Transmission / General / Gear Ratios / Trans Chain Ratio | 1.00 | [JSON](263.json) |
| 20010 | Transmission / Manual / Gear Ratios / Trans (Manual) 1st Gear Ratio | 4.45 | [JSON](264.json) |
| 20011 | Transmission / Manual / Gear Ratios / Trans (Manual) 2nd Gear Ratio | 2.71 | [JSON](265.json) |
| 20012 | Transmission / Manual / Gear Ratios / Trans (Manual) 3rd Gear Ratio | 1.97 | [JSON](266.json) |
| 20013 | Transmission / Manual / Gear Ratios / Trans (Manual) 4th Gear Ratio | 1.61 | [JSON](267.json) |
| 20014 | Transmission / Manual / Gear Ratios / Trans (Manual) 5th Gear Ratio | 1.33 | [JSON](268.json) |
| 20015 | Transmission / Manual / Gear Ratios / Trans (Manual) 6th Gear Ratio | 1.09 | [JSON](269.json) |
| 20016 | Transmission / Manual / Gear Ratios / Trans (Manual) Reverse Gear Ratio | 4.16 | [JSON](270.json) |
| 46630 | Transmission / Torque Converter / General / TCC Test / Trans Test TCC Lock | Disabled | [JSON](271.json) |
| 7596 | Fuel System / General / Fuel Pressure Sensor / Fuel Pressure Sensor Transfer Function | 8 x 2 (including axis/header cells) | [JSON](272.json) |
| 45691 | Fuel System / General / EVAP / EVAP Canister Purge Switch | Enabled | [JSON](273.json) |
| 45692 | Fuel System / General / EVAP / EVAP Canister Purge Switch A | Enabled | [JSON](274.json) |
| 43010 | Fuel System / General / Fuel Rail / Ambient Rail Temp Time Constant vs. Fuel Flow | 9 x 2 (including axis/header cells) | [JSON](275.json) |
| 43000 | Fuel System / Fuel Pressure / Desired Fuel Pressure / Desired Fuel Pressure Over Injector | 8 x 2 (including axis/header cells) | [JSON](276.json) |
| 43005 | Fuel System / Fuel Pressure / Desired Fuel Pressure / Desired Fuel Pressure Over Injector AAT Adder | 9 x 2 (including axis/header cells) | [JSON](277.json) |
| 6002 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Secondary Monitor | Enabled | [JSON](278.json) |
| 23005 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Minimum On Time | 8.00 | [JSON](279.json) |
| 43002 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Desired Voltage | 6 x 10 (including axis/header cells) | [JSON](280.json) |
| 6961 | Fuel System / Fuel Pump / Fuel Pump / Minimum Fuel Pump Duty Cycle | 10.00 | [JSON](281.json) |
| 6960 | Fuel System / Fuel Pump / Fuel Pump / Maximum Fuel Pump Duty Cycle | 48.00 | [JSON](282.json) |
| 45694 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Adaptive Voltage | Enabled | [JSON](283.json) |
| 23033 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Update Time | 2.0000 | [JSON](284.json) |
| 23034 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Time Constant | 0.0156 | [JSON](285.json) |
| 23030 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Voltage Deadband | 0.2500 | [JSON](286.json) |
| 23031 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Low Limit Mult | 0.7500 | [JSON](287.json) |
| 23032 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump High Limit Mult | 1.2500 | [JSON](288.json) |
| 23002 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Gain - Proportional | 0.0600 | [JSON](289.json) |
| 23001 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Gain - Integral | 0.0996 | [JSON](290.json) |
| 23000 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Gain - Derivative | 0.0000 | [JSON](291.json) |
| 45693 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Fixed Duty Cycle Mode | Disabled | [JSON](292.json) |
| 23003 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Fixed Duty Cycle | 60.00 | [JSON](293.json) |
| 23035 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Off Duty Cycle | 75.00 | [JSON](294.json) |
| 6982 | Fuel System / Fuel Pump / Fuel Pump / Fuel Pump Command Frequency | 150.0 | [JSON](295.json) |
| 23040 | Fuel System / Diagnostics / Fuel Pressure / Fuel Pressure Test Fail Time | 8.00 | [JSON](296.json) |
| 23041 | Fuel System / Diagnostics / Fuel Pressure / Fuel Pressure Test Fail Delta | 2.40 | [JSON](297.json) |
| 23042 | Fuel System / Diagnostics / Fuel Pressure / Fuel Pressure Test Error Buffer | 14.30 | [JSON](298.json) |
| 23043 | Fuel System / Diagnostics / Fuel Pressure / Fuel Pressure Test Low | 6.00 | [JSON](299.json) |
| 23044 | Fuel System / Diagnostics / Fuel Pressure / Fuel Pressure Test Drop | 4.00 | [JSON](300.json) |
| 4233 | Fuel System / Diagnostics / FPDM / FPDM KOEO Test Switch | Enabled | [JSON](301.json) |
| 4234 | Fuel System / Diagnostics / FPDM / FPDM KOER Test Switch | Enabled | [JSON](302.json) |
| 45794 | System / General / Security / PATS Alternate Switch | Enabled | [JSON](303.json) |
| 45797 | System / General / Power Steering / Power Steering Pressure Switch | Enabled | [JSON](304.json) |
| 23010 | System / General / Ambient Air Temperature / Ambient IAT Delta - Ambient Update | 0.00 | [JSON](305.json) |
| 23011 | System / General / Ambient Air Temperature / Ambient IAT Delta | 0.00 | [JSON](306.json) |
| 23012 | System / General / Ambient Air Temperature / Ambient Update - ECT Min | 0.00 | [JSON](307.json) |
| 23013 | System / General / Ambient Air Temperature / Ambient Update - VSS Min | 0 | [JSON](308.json) |
| 23015 | System / General / Ambient Air Temperature / Ambient Inferred Time Constant | 0 | [JSON](309.json) |
| 23016 | System / General / Ambient Air Temperature / Ambient Adder (AC On) | 0 | [JSON](310.json) |
| 23017 | System / General / Ambient Air Temperature / Ambient IAT/ECT Factor During Soak | 1 | [JSON](311.json) |
| 45789 | System / Braking / General / Brake Input | Enabled | [JSON](312.json) |
| 45804 | System / Fans / Hardware / Electric Fan Enabled | Enabled | [JSON](313.json) |
| 24020 | System / Fans / Control By ECT / Fan Low Speed Enable ECT | 195.0 | [JSON](314.json) |
| 24021 | System / Fans / Control By ECT / Fan Low Speed Disable ECT | 190.0 | [JSON](315.json) |
| 24022 | System / Fans / Control By ECT / Fan Low Speed Enable VSS | 48.0 | [JSON](316.json) |
| 24023 | System / Fans / Control By ECT / Fan Low Speed Disable VSS | 53.0 | [JSON](317.json) |
| 24030 | System / Fans / Control By ECT / Fan High Speed Enable ECT | 225.0 | [JSON](318.json) |
| 24031 | System / Fans / Control By ECT / Fan High Speed Disable ECT | 215.0 | [JSON](319.json) |
| 24032 | System / Fans / Control By ECT / Fan High Speed High Load Enable RPM | 2,240 | [JSON](320.json) |
| 24033 | System / Fans / Control By ECT / Fan High Speed High Load Enable Load | 0.6000 | [JSON](321.json) |
| 24034 | System / Fans / Control By ECT / Fan High Speed High Load Enable VSS | 35.0 | [JSON](322.json) |
| 24035 | System / Fans / Control By ECT / Fan High Speed High Load Enable ECT | 235.0 | [JSON](323.json) |
| 45810 | System / A/C / Hardware / A/C Master Switch | Enabled | [JSON](324.json) |
| 45811 | System / A/C / Hardware / A/C Pressure Switch | Disabled | [JSON](325.json) |
| 24001 | System / A/C / Disable Conditions / A/C WOT Disable TPS | 450.0000 | [JSON](326.json) |
| 24000 | System / A/C / Disable Conditions / A/C WOT Disable Time | 15.0 | [JSON](327.json) |
| 8002 | Speedometer / Calibration / Hardware / Final Drive/Tire use VID | Disabled | [JSON](328.json) |
| 45782 | Speedometer / Calibration / Hardware / VSS out via SCP | Disabled | [JSON](329.json) |
| 45783 | Speedometer / Calibration / Hardware / VSS out via PCM | Enabled | [JSON](330.json) |
| 5001 | Speedometer / Calibration / Hardware / VSS Pulses Per Rev - Trans | 89.0000 | [JSON](331.json) |
| 9050 | Speedometer / Calibration / Gear Ratio & Tire Size / Final Drive Ratio | 1.00 | [JSON](332.json) |
| 845 | Speedometer / Calibration / Gear Ratio & Tire Size / Axle Ratio Max | 1.00 | [JSON](333.json) |
| 846 | Speedometer / Calibration / Gear Ratio & Tire Size / Axle Ratio Min | 1.00 | [JSON](334.json) |
| 9003 | Speedometer / Calibration / Sensor Calibration / VSS Tire Revs per Distance | 839.00 | [JSON](335.json) |
| 25110 | Speedometer / Calibration / Speed by Engine RPM / N/V Base | 13.9800 | [JSON](336.json) |
| 4219 | Speedometer / Limiter / Limits / Torque Ratio vs. Output Shaft Speed | 8 x 2 (including axis/header cells) | [JSON](337.json) |
| 16712 | Speedometer / Limiter / Limits / Speed Limiter ECM On | 105 | [JSON](338.json) |
| 16713 | Speedometer / Limiter / Limits / Speed Limiter ECM Off | 102 | [JSON](339.json) |
| 4227 | Speedometer / Limiter / Limits / OSS Limiter On | 16,380 | [JSON](340.json) |
| 4228 | Speedometer / Limiter / Limits / OSS Limiter Off | 0 | [JSON](341.json) |

## Coverage notes

Missing entries: 0. Metadata/coverage issues: 94. See manifest for exact entries. No calibration changes were made during capture.
