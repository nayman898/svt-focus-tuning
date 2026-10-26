# Device baseline

Captured 2026-10-26 using Windows Plug and Play information and VCM Editor's
**Help > VCM Suite Information > Gather VCM Suite Information**.

| Item | Observed value |
| --- | --- |
| USB-reported product | MPVI4 |
| Connection method | USB |
| USB vendor / product | 31DE / 1870 |
| Windows status | OK |
| USB serial interface | COM7; this does not establish a generic OBD serial API |
| VCM Editor | 5.3.1332 Beta |
| Hardware | 4.2.0 |
| Firmware | 1.33.1 Release |
| Primary application | MPVI4.Kernel 0.1.380 Release |
| Bluetooth component | 0.2.2 |
| Licensed features | Pro Feature Set |
| Credits purchased / used / available | 2 / 2 / 0 |
| Existing controller license | Ford Oak 1472K PWM; calibration identifier UJAHAS3 |
| Vehicle power | Not detected |

The existing controller license is stored in the interface. It is not a live
identification of a connected ECU. Match it against the Focus when connected.
The full report, including device ID and licensed VIN, is stored only in
`.local/vcm-suite-info-2026-10-26.txt` and excluded from Git.

The device responds to VCM Editor; no driver repair is currently indicated.
Firmware update availability and vehicle compatibility have not been checked.
