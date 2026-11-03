# v009 off-idle fuel-control inspection

The owner confirms exact v009 installed without additional edits for the
[latest stationary900 run](2026-10-27-900-load-capture.md). Hold this idle target
while checking return-to-idle and fuel-control transitions. This inspection
does not establish a road-ready calibration or select replacement table values.

All10 cataloged binaries match their SHA-256 hashes and lengths. Editor's main
file is v009, with v008 loaded as comparison. Main-file Open Loop / Base controls
and the named parameter-table windows were inspected without editing or saving.
Private UI snapshots and grid-cell exports are preserved under `.local/`.

## Verified controls

- ECM32731 Open Loop Fuel TPS Thresh vs.RPM retains200 at0/1500RPM and0
  at2000/2500/5500/6500/16384RPM. The stationary experiment's transition remains.
- ECM32725 Open Loop Delay vs.RPM vs.Gear shows0.00s in all50 visible data
  cells: gears1–5 and RPM750/1500/2000/2500/3000/3500/4000/4500/5000/6000.
- Main-page OL Delay Ramp0.00, OL Delay Blend Ramp0.10 and OL Delay Maximum2.50s
  were read from the controls grouped with those exact labels. Ramp units and
  exact strategy semantics are not inferred beyond the generic documentation.
- ECM44511 Fuel Base vs.RPM vs.TPS is populated. Its2500RPM column includes
  displayed lambda1.07 and1.14 in the first two TPS rows, alongside much richer
  values elsewhere. Axis interpretation and the strategy's active table,
  corrections and commanded-mixture channel meaning need verification before
  treating those cells as actual delivered lambda or choosing edits.

HP Tuners describes the
[TPS threshold, open-loop delays and lambda base tables](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_loop.htm).
This generic documentation does not establish the exact absolute/relative TPS
comparator for this controller. Zero in the delay table does not prove immediate
open-loop entry under every condition; other gates and state logic remain.

## Decision

The inherited change is not confined to idle. Reverting the whole table blindly
would also discard the change that enabled stationary closed-loop operation;
extending200 across the RPM range would introduce another unvalidated experiment.
Neither action is selected. Keep the current file unchanged while validating
TPS scaling, loop/fuel-source transitions and commanded-versus-measured mixture.

A separate paired hot-restart capture is the next stationary measurement.
Off-idle exercises and road testing require their own defined scope after the
fuel-control review; this report does not authorize a throttle sweep or boost
test. Water/meth remains completely disabled by owner instruction. Its reported
enabled activation is7psi, while calibration dependency under boost is unknown.
