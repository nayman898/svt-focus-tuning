# v024 cold-start, clutch A/B, off-idle hold and fan-cycle review

Source: `paired-20261103-093505-f70dae31-v024`, preserved in
`logs/2026-11-03-v024-cold-cleanup-01/` with native HPL (`35F23CD4...`), VCM CSV
(`A4B64A83...`), SCG CSV (`EC355662...`), verified SQLite backup (`FB00407A...`,
source `6A98B630...`, `PRAGMA integrity_check = ok`) and manifest (`E8E8EED2...`).
Owner confirms the new upstream O2 sensor was installed before this run and
[v024](../tunes/v024-fuel-cleanup-diagnostics.md) was flashed. Water/meth remained
OFF. No agent ECU write, readback, DTC clear or adaptation reset occurred.

**Decision:** Provisionally adopt **v024** as the new working parent for covered
stationary conditions (zero stalls, zero CKP sync dropouts, calmer warm idle than
v021, clean fan-on and initial fan-off survival), and prepare
[v025](../tunes/v025-maf-idle-offidle-smooth.md) from exact **v024** to resolve
the single root cause unifying all remaining idle/warmup/off-idle mixture errors:
the `0.500–1.000 V` `ECM12163` MAF curve kink and rich bulge.

---

## 1. Capture quality and alignment

- **VCM coverage:** `38,438` rows from `1.290` to `906.631 s` (`15.11 min`). All
  **18 requested channels are 100.0% populated** across every row, including
  `Idle Desired RPM` and `Throttle Position ADC (Absolute)`. Three sample gaps
  exceed `0.30 s`: `412.937–417.817 s` (`4.880 s`), `595.025–599.965 s` (`4.940 s`),
  and `745.695–747.602 s` (`1.907 s`, near the end of `clutch_down`). None
  overlaps startup, `Open Loop FMEM` entry/exit, the two throttle holds, or the
  warm fan cycle; time-weighted intervals exclude `dt > 0.30 s`.
- **Manifest status note:** `session.json` recorded `status: "partial"` because
  `vcm_csv_audited` encountered a transient Windows file-share lock (`Errno 13`)
  `208 ms` after `vcm_export` acknowledged. The exported `vcm.csv` (`7,019,820 B`)
  completed cleanly; original manifest status is preserved unaltered.
- **SCG coverage and alignment:** `11,058` total samples (`10,670` `valid`, `365`
  `warmup` across `VCM 4.82–34.64 s`, `21` `sensor_error` at `3.06–4.70 s`, `1`
  `gap`, `1` `stopped`). Provisional metadata alignment is
  `SCG elapsed = VCM offset + 3.150 s` (`+1.513 s` from `vcm_start.invoked_utc`).
  Mixture statistics use `valid` SCG samples only.

---

## 2. Cold start (`60.0 F`), new O2 closed-loop entry and mid-warmup `FMEM`

| VCM offset | ECT | Event / behavior |
| --- | ---: | --- |
| `1.290–4.114 s` | `60.0 F` | KOEO (`125` rows): `TPS_Abs = 180.82`, `FRP = 2.921 V` (`~42.4 psi`), `Vbatt = 10.79 V`, `O2 = 0.001 V`, `Desired RPM = 1,648`. Below the `64.00 F` `ECM44519` cranking step (`0.930` lambda region). |
| `4.137–6.980 s` | `60.0 F` | Cranking begins at `4.137 s` (`Vbatt = 8.69 V`), `RPM > 400` at `5.424 s`, clean flare to `2,123.2 RPM` at `6.980 s`, post-flare minimum `1,533.8 RPM` at `8.310 s`. **Zero post-start rows `< 500 RPM` across the entire `15.11 min` log.** |
| `64.435–65.616 s` | `84.0 F` | New upstream O2 crosses `0.10 V` (`0.117 V`) at `+59.0 s` runtime and `0.45 V` (`0.460 V`) at `+60.2 s`. `Closed Loop Active = Yes` at `65.431 s` (`STFT` mean `-2.83%`, `SCG Lambda = 0.974` over `+30 s`; no `+25%` false-lean excursion). |
| `120.0–177.50 s` | `110–128 F` | At `1,200–1,300 RPM` (`MAF_V = 0.84–0.93 V`), base fueling is ~22–24% rich. Closed Loop pulls `STFT` to **`-23.92%`** to maintain `SCG Lambda ≈ 0.985`, keeping `O2 B1S1` rich (`0.87–0.92 V`) without crossing `0.45 V`. |
| `177.548 s` | `128.0 F` | **`Open Loop FMEM` trips to `Yes`** (`Closed Loop Active = No`, `Fuel Source = Cold Eng. / Startup`). Removing `-23.9%` `STFT` immediately drops `SCG Lambda` to **`0.783`** while `O2 B1S1` reads **`0.996 V`**, proving the O2 sensor remained live and accurate (`0` of `9,063` FMEM rows had `O2 < 0.05 V`). |
| `358.882 s` | `158.0 F` | Reaching `ECM44513 = 158.0 F` switches `Fuel Source` from `Cold Eng. / Startup` to `Power Demand Enrich`. |
| `389.959 s` | `162.0 F` | Once `Desired RPM` reaches `944 RPM` and `MAF_V` settles onto the `0.605 V` idle region, mixture leans near stoich (`Lambda = 0.97–1.005`), `O2 B1S1` dips to `0.323 V` (`< 0.45 V`), and **`Open Loop FMEM` clears to `No`** (`Closed Loop Active = Yes` continuously through `906.6 s`, save intentional OL throttle hold). |

---

## 3. Warm idle vs. v021 and Stage A2 clutch-pedal chatter A/B (`12:00–12:30`)

Owner markers: `clutch_down` at `12:00` (`720 s`), `clutch_up` at `12:30` (`750 s`).

| Window | Mean / SD (`RPM`) | Min / Max (`Span`) | `P05–P95` (`RPM`) | Time outside `944 +/- 50` | Time `< 844 RPM` | Sub-`900` groups (`/min`) | `Base/MBT` rows (`max deg`) | `MAF_V` (`% < 0.600 V`) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **v021 baseline** (`238.9–506.0 s`, `180–188 F`) | `950.72 / 27.94` | `829.5 / 1017.0` (`187.5`) | — | — | — | `72` (`16.18`) | `4` (`29.5`) | — |
| **v024 warm pre-clutch** (`540–720 s`, `180–184 F`) | **`950.28 / 22.23`** | `816.5 / 1001.0` (`184.5`) | `909.5–980.3` | `3.05%` (`5.34 s`) | `0.144 s` | `34` (**`11.66`**) | `2` (`29.5`) | `0.607 V` (`36.7%`) |
| **Pre-clutch UP #1** (`690–720 s`, `184 F`) | `950.38 / 25.25` | `816.5 / 1001.0` (`184.5`) | `904.5–982.6` | `4.47%` (`1.34 s`) | `0.144 s` | `7` (`14.02`) | `2` (`29.5`) | `0.603 V` (`47.5%`) |
| **CLUTCH DOWN** (`720–750 s`, `184–186 F`) | **`950.23 / 24.29`** | **`849.5 / 1002.5` (`153.0`)** | `904.0–980.7` | **`4.03%`** (`1.13 s`) | **`0.000 s`** | `5` (**`10.68`**) | **`0` (`20.5`)** | `0.602 V` (`48.1%`) |
| **CLUTCH DOWN pre-gap** (`722–745.5 s`) | `951.17 / 23.94` | `849.5 / 1002.5` (`153.0`) | `906.5–981.3` | `3.79%` (`0.89 s`) | `0.000 s` | `4` (`10.23`) | `0` (`20.5`) | `0.602 V` (`48.5%`) |
| **Post-clutch UP #2** (`750–779 s`, `186 F`) | `950.59 / 26.46` | `826.8 / 1000.5` (`173.8`) | `902.1–984.4` | `4.49%` (`1.30 s`) | `0.074 s` | `9` (`18.63`) | `4` (`29.3`) | `0.603 V` (`47.3%`) |

1. **Mechanical gearbox contribution (trough depth):** Decoupling the Getrag MT285
   dual-layshaft input gears (`clutch_down`) raised minimum RPM by **`+23` to `+33 RPM`**
   (`849.5` vs `816.5`/`826.8 RPM`), reduced peak-to-peak span from `173.8–184.5` to
   `153.0 RPM`, and eliminated all `< 844 RPM` undershoots and `Base / MBT` spark
   rescue hits (`0` vs `2` and `4`).
2. **Calibration contribution (continuous oscillation):** With the clutch held to the
   floor, `RPM SD` (`24.29`), central `90%` width (`76.7 RPM`), and step-to-step
   `|dRPM|` (`4.21` mean, `14.25` P95 vs `4.00`/`4.27` clutch-up) persisted nearly
   unchanged as `MAF_V` (`0.602 V`) oscillated across the `0.600 V` `ECM12163` slope
   discontinuity (`48.1%` of samples `< 0.600 V`).
3. **Trigger integrity:** Across all `15.11 min`, closed-throttle (`TPS_Abs <= 182.0`)
   step changes exceeding `55 RPM` (`dt <= 0.10 s`) occurred `0` times during steady
   idle (only `3` normal downward deceleration steps during pedal release from the
   `1.6k`/`2.2k` holds). Warm `FRP` held `3.063 V` (`3.042–3.086 V`, `~44.9 psi`),
   matching v021 (`STFT = -2.78%`, `SCG Lambda = 1.0116`, `IAC = 39.44%`,
   `STIT = -0.1189`, `LTIT = -0.0687`). *(Because the new upstream O2 was installed
   simultaneously with v024, improved cold entry and slightly calmer warm SD are
   properties of the v024 + new-O2 baseline together, not attributed to v024 edits alone.)*

---

## 4. Stage B stationary holds (`13:00` & `13:45`) and empirical MAF scaling proof

| Segment | Mean RPM (`Range`) | `TPS_Abs` (`Rel`) | Loop / `Fuel Source` | `MAF` (`MAF_V`) | `STFT` (`Range`) | `SCG Lambda` (`Range`) | `SCG Boost` |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| **Hold #1 (`787.0–797.5 s`)** | `1,621.5` (`1523–1764`) | `204.6` (`+23.8`) | `CL = Yes` / `Stoich` | `1.165 lb/min` (`0.848 V`) | **`-15.54%`** (`-21.91..-6.35%`) | `0.9964` (`0.904–1.087`) | `-8.12 psi` |
| **Return #1 (`799.0–825.0 s`)** | `970.4` (`min 854.8`) | `181.2` (`+0.4`) | `CL = Yes` / `Stoich` | `0.615 lb/min` (`0.627 V`) | `-5.69%` (`-18.20..+0.12%`) | `1.0493` (`0.957–1.260`) | `-7.29 psi` |
| **Hold #2 (`832.0–843.5 s`)** | `2,181.0` (`2048–2269`) | `224.7` (`+43.8`) | `CL = No` / `Power Demand Enrich` | `1.390 lb/min` (`0.972 V`) | `+0.00%` (`0.00..0.00%`) | **`0.7345` (`0.712–0.760`)** | `-8.53 psi` |
| **Return #2 (`845.5–859.0 s`)** | `1,058.3` (`min 872.8`) | `182.3` (`+1.5`) | `No -> Yes` / `PDE -> Stoich` | `0.684 lb/min` (`0.662 V`) | `-3.04%` (`-6.56..0.00%`) | `0.9876` (`0.806–1.048`) | `-7.12 psi` |

1. **Exact ECU-to-Editor `ECM12163` proportionality established:** Across every
   steady operating window from `0.607 V` to `0.974 V`, logged `Mass Airflow`
   (`lb/min`) divided by `(60 * Editor_ECM12163_lb_min * 0.132277)` is constant to
   **`0.9527 +/- 0.0008`** (`7.562x` raw Editor `lb/min` display). The PCM applies
   `ECM12163` linearly with no hidden nonlinear table transform.
2. **Why Hold #2 ran `0.7345` lambda despite `ECM44511 = 1.000`:** At `192 F` and
   `ERT > 830 s`, `ECM44511` (`1.000`), `ECM44512 - ECM44516` (`1.03 - 0.03 = 1.00`),
   and `ECM32740` (`0.000`) yield a net open-loop command of **`1.000` lambda**.
   Moreover, fuel mass per intake event at `2,181 RPM` (`1.393 lb/min / 4,362 strokes`)
   equals `950 RPM` warm idle (`0.587 lb/min / 1,900 strokes`) within **`3%`**,
   canceling injector offset/deadtime and `3.064 V` pressure effects. Yet `ECM32731 = 0`
   at `>= 2,000 RPM` forced Open Loop (`STFT = 0%`, `LTFT` disabled), exposing an
   uncompensated **`+26%` `ECM12163` airflow bulge** across `0.699–1.000 V` (where
   the PMAS 2.8" Pro-Tube II reference is likewise `0.729x` of v024 at `0.699–0.898 V`).
   In Closed Loop at `1,622 RPM` (`0.848 V`), that same bulge forced `STFT` to
   `-19.1%`, causing a transient `1.260` lean overshoot upon throttle release back
   to `0.603 V` idle. *(The `2,500 RPM` hold was appropriately omitted once the `2.18k`
   hold crossed the `< 0.80` lambda review trigger for `11.5 s`.)*

---

## 5. Warm fan cycle (`14:19` on, `14:49` off)

- **Fan ON (`859.0–888.5 s`, `196 -> 190 F`):** **Most stable idle of the entire
  session** — `RPM = 951.3 +/- 18.13` (`888.5–1,002.2`, span `113.8`), only
  **`0.39%`** time outside `944 +/- 50 RPM`, and `4.1` sub-900 groups/min
  (`SCG Lambda = 1.014`, `STFT = -1.65%`). Electrical fan load opened `IAC` to
  `41.37%` and shifted `MAF_V` from `0.602 V` to **`0.626 V`**, lifting operation
  above the `0.600 V` `ECM12163` slope kink.
- **Fan OFF (`889.0–906.6 s`, `188 -> 186 F`, `17.6 s` captured):** Unlike v023
  (which stalled after `188 F` fan-off with `10 deg` nominal idle spark), v024
  (`12 deg` nominal spark) transitioned cleanly (`min RPM = 871.2`, `mean = 951.9`,
  `SD = 31.54`, `IAC` `41.4% -> 37.4%`, `Lambda = 1.005`). Because recording stopped
  `17.6 s` after fan-off (vs. `60 s` target), extended post-fan-off remains partial
  coverage to verify fully in the v025 run.

---

## 6. Next bounded intervention — v025 (`ECM12163` `0.500–1.000 V` smoothing)

Prepare [v025](../tunes/v025-maf-idle-offidle-smooth.md) from exact **v024**,
modifying **only** `ECM12163` (`MAF Airflow vs. Voltage`) across the **8 contiguous
idle and off-idle columns `6–13` (`0.500–1.000 V`)** using a smooth convex quadratic
anchored to untouched `0.479 V` (`3.5145` g/s-eq), warm-idle `0.600 V` (`4.5600`
g/s-eq, `-2.74%`), and untouched `1.100 V` (`12.3970` g/s-eq):

- Eliminates both the `5.6x` `0.600 V` idle shelf and `12.0x` `0.649 V` jump
  (segment slopes progress smoothly `7.5 -> 8.1 -> 8.5 -> 9.3 -> 10.6 -> 11.7 -> 14.5 -> 17.9 -> 20.2`).
- Preserves warm idle mixture (`0.607 V`: `-1.59%`, predicted `STFT ~ -1.0%`) and
  fan-on idle (`0.626 V`: `+1.49%`, predicted `STFT ~ -3.1%`).
- Reduces the `0.84–0.90 V` warmup/off-idle bulge by **`-15.4%` to `-15.8%`**
  (bringing warmup `STFT` from `-23.9%` FMEM clip to `~ -8%..-10%` and `1.6k` CL
  hold `STFT` from `-19%` to `~ -1%..-4%`) and reduces `0.974 V` by **`-10.3%`**
  (lifting `2.18k` OL hold from `0.735` to a conservative `~0.82` lambda without
  risking open-loop lean excursion).
- Leaves all `0.000–0.479 V` and **`1.100–4.800 V` (`17` cruise/load/boost cells)**
  100% unchanged.
