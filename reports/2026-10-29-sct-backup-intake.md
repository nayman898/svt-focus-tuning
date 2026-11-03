# SCT original-backup intake

Received2026-10-29 from the owner's desktop. The owner identifies it as the
SCT device's original/stock backup from the other laptop. The source is
preserved unchanged; a byte-identical copy is retained privately as
`backups/sct-original-20261029.bef`. Source filename/path includes a device
identifier and is recorded only in ignored `.local/sct-original-provenance.json`.

- Size:7,420,760bytes.
- SHA-256:`297B7F3CA423C1AF23579E33855241D78F294F7417CC888AF2BD863F597FBCDB`.
- Format supplied: **BEF device backup**, not a decoded HPT calibration.
- No companion SUL/BIN/HPT export was found beside it on the desktop.
- No decoded strategy/OS identity or table values have been authenticated from
  this file. Owner provenance is retained; factory identity remains to be checked.

## What is established

[SCT's support instructions](https://derivepower.freshdesk.com/support/solutions/articles/72000573698-11109-program-vehicle-error)
identify BEF as a file saved by Get Stock File from Device and used with vehicle
strategy/software information for support. Thus the extension is consistent
with the owner's export. The extension alone does not reveal editable tables
or establish a verified same-strategy factory comparison.

The local installed-program inventory finds SCT Device Updater2.26.292.1 and
SCT drivers. No SCT calibration editor was identified. No verified local BEF
decoder or supported direct BEF-to-HPT conversion route has been established.
Initial signature inspection did not identify a standard ZIP/GZIP/XML wrapper;
this is not proof of a particular encryption/compression scheme. No random
decoding, binary table-location guesses or file edits were attempted.

HP Tuners documents [BIN-to-HPT Tune Translation](https://www.hptuners.com/products/tune-translation/).
That is not documented acceptance of this BEF file, and compatibility with this
Black Oak strategy is unverified. Renaming BEF to BIN/HPT would not convert it.
No file uploaded, service purchased, backup restored or ECU written.

## What is needed for an actual comparison

Obtain a supported readable stock calibration export, or a matching factory
reference in a format usable by the calibration tools. SCT support or an
appropriately equipped SCT calibration provider can be asked what supported
export/reference can be obtained from this BEF, together with the device's
Vehicle Info strategy/software identifiers. This report does not authorize
contacting them or sharing private files.

We should verify controller/strategy, provenance, axes and units before comparing
6950 vacuum compensation, pressure/injector assumptions, ECT/runtime idle-air
matrices, VCT and aircharge filtering. Do not assume absent access means those
settings are stock or modified. Do not restore the car to factory calibration
to obtain a comparison: the turbo/injector hardware differs from factory.

The [current-tune audit](2026-10-29-v012-calibration-audit.md) remains usable
independently of this format limitation. Its measured findings are unchanged;
**no stock-versus-v012 table comparison has yet been performed from the BEF**.
