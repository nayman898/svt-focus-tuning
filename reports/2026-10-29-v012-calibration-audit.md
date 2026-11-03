# v012 calibration audit: idle instability and inherited assumptions

**Reference update:** SCT BEF backup has now been received and preserved; see
[intake and format limitation](2026-10-29-sct-backup-intake.md). No decoded
factory comparison has yet been obtained. The other-laptop availability notes
below describe the earlier audit state, not a remaining file-transfer request.

Read-only inspection in VCM Editor,2026-10-29. File:
[v012](../tunes/v012-idle-spark-gain-1p0.hpt). All13 cataloged binaries passed
SHA-256/size checks before inspection. No tune value was intentionally edited,
no file saved and no ECU read/write performed. This is a focused idle/air/fuel/
cam audit, not validation of every table, DTC or operating condition.

**There are concrete settings worth investigating before another spark-gain
change. None is established as the sole cause of the random stalls.** Owner
confirms v010 also stalled, while reduced gain improved steadiness between
stumbles. Keep onset and recovery-handoff questions separate.

## Ranked findings

| Priority | Verified finding | Why it matters | Decision |
| --- | --- | --- | --- |
| 1 | ECM6950 Manifold Vacuum Multiplier0.484; installed Editor help explicitly gives zero for a return-style conversion | Owner has1:1 manifold-referenced return regulation; current vacuum/pressure assumptions need checking together | Audit the coupled fuel-pressure/injector model; do not flip this scalar alone |
| 2 | Warm idle-air multiplier declines from1.30 at165s to about1.02 at200s at188F | A substantial time-dependent pre-correction airflow change could interact with learned air and recovery | Log real engine runtime and compare original calibration; not proven to explain every random dip |
| 3 | VCT enabled, intake-only; angle-table values at1000RPM/load0.2–0.3 are-22/-25degrees | Nonzero low-speed cam targets and actual phaser behavior can affect idle air/combustion; no requested/actual angle trace exists | Prioritize stock-reference and actual cam-tracking evidence; no blind phasing edits |
| 4 | Cylinder-airmass filtering and extra idle coefficient enabled; coefficient0.11; anticipation and MAF air-charge-delay compensation disabled | Estimated cylinder aircharge has filtering/lag assumptions relevant to transients | Compare original settings and response; coefficient alone does not prove excessive filtering |
| 5 | Idle source eligibility200/30RPM,3mph;2s in-gear-to-P/N delay | State-dependent entry/exit can affect recovery, but scalar names do not reconstruct arbitration | Preserve until controller semantics and state evidence are established |

These appear inherited from the modified baseline rather than introduced by
the recent gain experiments. That statement uses the preserved comparison
chain: v009 versus v001 listed Notes, targets and OL TPS threshold; v010 versus
v009 and v012 versus v010 listed gain and Notes. This is not a new factory-stock
comparison. v001 itself was a modified ECU read, not a proven factory image.

## 1. Return-system model: the clearest configuration concern

Direct Editor reading:

- ECM6950 **0.484**. Its matching help describes vacuum scaling/compensation
  and says: “Set to 0 if going to a return style.”
- Injector Pressure Drop Reference **40.00psi**, pressure compensation
  **Enabled** (ECM32047), rechecked in the current file.
- Previously verified inherited ECM7596 sensor transfer is flat40psi across
  its inputs. It is not dynamic pressure evidence; see the
  [existing pressure audit](../docs/fuel-pressure-feedback-review.md).
- Injector low/high slopes **0.017500000/0.016700000lb/s**, numerically63.00/
  60.12lb/hr; minimum pulse width0.00050000s; breakpoint0.00003360lb. Those are
  tune values, not validated characterization of the actual injectors.
- Physical hardware: owner-confirmed1:1 Aeromotive return regulator, latest
  owner setting43psi engine-off, digital gauge sender at regulator; OEM ECU
  pressure sensor still awaiting installation.

This warrants checking whether manifold-vacuum compensation, assumed pressure
and injector characterization describe the same physical differential-pressure
system. The observed pressure video does not validate the software model. It
only lacks a large displayed pressure collapse in one later recovered dip.

Do not independently set6950to0, change40to43, disable compensation, restore an
unknown sensor transfer, or rescale the MAF/injectors from trim averages. Exact
Black Oak implementation, injector part/reference data and pump arrangement
remain unresolved. Other tables may already compensate for an inherited model
assumption; that is a hypothesis to investigate, not evidence to stack changes.
Pressure affects flow and offset as documented in the
[HP Tuners injector reference](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_fuel_general.htm).

## 2. Runtime-dependent airflow is a real, separate timer path

ECM44242 P/N and44239 Drive base-air tables both show0.41lb/min at900RPM,
0.46at1000,0.60at1250,0.74at1500. The slope is not a sudden cliff around900.

ECM44243 P/N and44240 Drive ECT/runtime multiplier matrices are identical in
this inspection. Selected warm columns:

| Engine runtime axis s |120F column |200F column |
| ---: | ---: | ---: |
| 2 |1.80 |1.60 |
| 30 |1.60 |1.50 |
| 72 |1.50 |1.40 |
| 120 |1.40 |1.40 |
| 165 |1.30 |1.30 |
| 200 |1.15 |1.00 |

At188F, linear interpolation gives about1.30 at165s and1.0225 at200s. Applied
only to the0.41 base contribution, that is approximately0.533 to0.419lb/min:
about21% reduction over35s. **This is not total commanded or measured airflow.**
Other corrections, controller state, adaptation and valve behavior still apply.
Actual engine runtime is not established merely by recording elapsed time.

This is a plausible contributor to after-start settling or learned-air mismatch,
including warm restarts, and deserves comparison with the SCT reference. It
does not explain all events by itself: the drive's later dips occurred after
different restart/load histories, including before200s since its restart. Do not
flatten the table merely to remove a timer. General purpose is documented in
[Ford idle airflow controls](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_idle.htm).

A separate [16-channel runtime trial](../profiles/2004%20Focus%20SVT%20-%20Target%20Idle%20Runtime%20Trial.Channels.xml)
is prepared offline, not loaded/tested. It preserves all15 Target Idle Air
definitions and adds the existing Scanner-saved Engine Run Time2131 request
at1s. That PID previously capped at255s; useful for this early interval, not an
unbounded clock. First validate acquisition; no new engine run was started.

## 3. VCT: a missing measurement, not a proven bad table

ECM44401 enabled; ECM44420 Intake Only. ECM44412's lowest RPM column is1000.
Displayed values there are-10degrees at load0.10,-22at0.20,-25at0.30,-26at0.40
and-28at0.50. Warm ECT multiplier44414 is1.00 and IAT multiplier44413 is1.00
at the inspected breakpoints. Startup-delay44403 gives2s at160F/254F.

These are calibration values, **not proof of the final requested/actual phase**
at900RPM. Selection, limits, sign/reference convention and hardware matter.
The logs have no verified commanded/actual VCT, tracking error or solenoid duty
to correlate with the stumbles. IMRC switch2019 and position-sensor44397 are
Disabled; hardware correspondence remains unverified. Do not enable IMRC or
disable/zero VCT just to see what happens, especially with uncertain cam hardware.

The original matching calibration would help distinguish factory phasing from
earlier tuner changes. Independently verify actual cam tracking before blaming
phasing or selecting a replacement angle. See the
[Ford VCT parameter definitions](https://www.hptuners.eu/help/vcm_editor_parameters_ford_eng_airflow_general.htm).

## 4. Aircharge filtering and spark/startup context

Verified: Cylair Filter44323 Enabled; Anticipation44324 Disabled; Use Idle
Filter44325 Enabled; coefficient12002=0.11; MAF ACDC45258 Disabled. WOT and
maximum cylinder-airmass multipliers12001/12004 are2.00/0.90, upper-bound model
coefficients, not instructions to double fueling. Without original calibration
and algorithm/sample-period knowledge, do not derive a time constant or call
0.11 intrinsically wrong. Some captured UI help is cached for unrelated fields;
only matching label/description pairs were used for parameter identification.

P/N idle spark44579 is12degrees at its displayed breakpoints, gain47996=1.000,
idle spark floor44582=-6degrees. Actual timing can differ because of feedback,
limits and corrections. Global spark floor12908=-30 and ceiling42279=55 are
bounds, not observed commands. Tip-in control RPM minimum44607=775 is a **tip-in
gate**, not an established explanation for parked MBT entry near that speed.

Maximum-cold-start spark44568 has strongly varying negative displayed values
over ECT/runtime. It is retained as an audit item because Cold Start Emissions
Reduction is reported during warm restarts/moving off. Do not equate raw table
values directly with observed absolute timing without the specific controller's
offset, limiter and eligibility logic. It is not yet a selected correction.

The fixed startup RPM adder12255 and its maximum time44221 are both0 in this
file. That does not disable the separate ECT/runtime airflow or spark paths.
Fan High Speed Idle44224 is Enabled; its effect does not establish fan operation.

## 5. Eligibility and inspection limits

Fresh readings: ECM44213 enable error200RPM;12262 disable error30RPM;44214
minimum VSS3mph;12267 in-gear-to-P/N delay2.00s. Descriptions alone do not
resolve the state machine or Spark Source selection. The captured first MBT
entry at139RPM error and later Idle Feedback beyond200RPM error cannot be
reduced to one instantaneous200RPM switch, given asynchronous data and unknown
internal states. No threshold change selected.

Idle integrator timing/learning-limit controls were not found in the inspected
idle pages or Navigator searches for Integrator/Learn/Adaptive. Advanced view
was requested and the Idle search repeated without exposing them. No numerical
integrator timing, learning bounds or complete arbitration map is claimed.
Their presence in generic Ford documentation is not proof this definition exposes
them. This pass did not comprehensively audit diagnostic reporting or every
injector compensation/MAF cell, torque model or protection table.

## SCT backup: what to provide

Owner confirms it is the device's original/stock backup on a different laptop;
it is not yet available here. Copy the original file unchanged, keeping its
extension and any accompanying calibration/strategy information private. There
is no need to return the car to stock to supply a file. Do not flash the stock
calibration onto the turbo/injector setup as a comparison test.

Before using it, verify controller/strategy identity, provenance, readable
format and axes/units. Device-original is a useful reference, but we still need
to establish what it actually contains. Do not assume a proprietary SCT backup
can be directly opened or converted by VCM Editor; determine supported handling
after seeing its format. SCT documents backup retrieval through
[Device Updater](https://derivepower.freshdesk.com/support/solutions/articles/72000576848-retrieving-the-stock-file-from-your-device).

Compare control structure and relevant settings first:6950, pressure/injector
assumptions, idle-air matrices, VCT, filtering, startup and eligibility. Do not
copy factory injector/MAF settings into the modified engine. If the format cannot
be decoded with supported tools, report that limitation rather than infer binary
table differences or alter the ECU to obtain a comparison.

## Next action

1. Obtain the SCT backup as a reference while continuing engine-off checks.
2. Resolve the return-system pressure/injector assumptions as one documented
   model, retaining exact calibration/physical references.
3. Establish real engine-runtime and requested/actual VCT acquisition using
   verified controller definitions; inspect actual air-path/IAC operation.
4. Select a single supported diagnostic change only after that evidence separates
   a calibration mismatch from actuator/load/combustion disturbance.

No v013 or new numerical adjustment selected. Engine operation not started.
Private `.local/audit-v012-*.json` captures retain the inspected labels, values,
help and table cells; these are read-only observations, not a complete tune dump.
