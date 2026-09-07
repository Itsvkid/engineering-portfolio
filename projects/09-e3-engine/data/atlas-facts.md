# E³ turbofan anatomy — fact sheet for the interactive atlas

Data sheet for the portfolio's Three.js "turbofan anatomy" page. The engine
is the NASA/GE Energy Efficient Engine (E³) Flight Propulsion System, GE for
NASA Lewis under NAS3-20643, 1978–83. Every number carries one of three tags:

- `[E3: <report>, p.<n>/Table <n>]` — printed in an E³ report and already
  transcribed into `projects/09-e3-engine/data/*.yaml` (or read from the scan
  for this sheet; those are marked `read for this sheet`).
- `[derived]` — computed from E³ printed numbers by this project; the method is
  named.
- `[schematic]` — generic large-turbofan practice with no E³ page behind it.
- `[textbook: <author>]` — from a named text.

Report short names and PDF offsets (printed page + offset = PDF page):
CR-168219 FPS final design (+14) · HPC detail design NTRS 19850002690 (+9) ·
HPT CR-167955 (+8) · LPT NTRS 19850002686 (+13) · fan CR-165148 (+10) ·
combustor CR-168301 (+15) · ICLS CR-168211 (+25) · controls CR-168017.

Where a report prints a number two ways and they disagree, both are given
and neither is "corrected". Where nothing is printed, it says so.

---

## A. Flowpath geometry

Units: **cm** unless stated. Radii are from the engine centreline. Each
component sits in its own report's axial datum; the two offsets no source
gives are named at the end of this section.

### A1. Fan and booster (datum: fan rotor stacking axis, Z_SA)

| Station | r_hub | r_tip | axial | Provenance |
|---|---|---|---|---|
| Fan tip diameter | — | 105.4 (2.108 m dia) | — | [E3: CR-165148 Table IV p.47; CR-168219 §4.3 p.32 "211 cm (83 in)"] |
| Fan inlet (LE) hub | 36.05 | — | — | [derived: tip × inlet radius ratio 0.342, CR-165148 Table IV p.47] |
| Fan stacking-axis radii | 41.76 (16.4399 in) | 103.90 (40.9061 in) | Z_SA = 8.19 (3.2253 in) on the fan report's axis | [E3: CR-165148 Fig.15 p.21, printed box] |
| Fan blade height at SA | 62.14 (24.4662 in) | | | [E3: CR-165148 Fig.15 p.21] |
| Fan chord | 18.4 hub → 28.3 tip | | | [E3: CR-165148 Fig.15 p.21] |
| Fan stagger (from hub) | 12°, 22°, 35°, 42°, 45°, 54°, 62° at 0/20/40/55/60/80/100 % height | | | [E3: CR-165148 Fig.41 p.50, read off] |
| Fan LE/TE axial extent | hub: LE ≈ Z_SA − 11.7, TE ≈ Z_SA + 6.3; tip: LE ≈ Z_SA − 8.6, TE ≈ Z_SA + 4.7 | | | [derived: axial chord = chord·cos(stagger); stacking point at 65 % axial chord per CR-165148 Fig.46 p.56 shroud data. ±1 cm] |
| Part-span shroud | at 55 % height (CR-165148) / "50 %" (CR-168219 §5.1.2 p.45) | radius ≈ 76 | 65 % axial chord | [E3: CR-165148 p.3, Fig.16 p.22, Fig.46 p.56] |
| Spinner | half-angle 32° | | | [E3: CR-165148 p.3] |
| Booster (quarter-stage) rotor | 52.3 | 66.9 (133.8 dia) | aft of the fan, under the island | [E3: CR-165148 Table IV p.47 (tip dia, radius ratio 0.782); hub derived] |
| Island splitter LE | between 66.9 and the fan tip; splits 22.3 % of fan flow under it | | | [E3: CR-165148 p.3, Fig.2 p.5] |
| Bypass OGV (fan frame) | 43.18 long, chord 31.27 root / 27.74 tip | | 1.8 rotor tip chords (≈51 cm) aft of the fan TE at the tip; CR-168219 says 1.9 | [E3: CR-165148 Table VII p.92, p.3; CR-168219 §5.1 p.38] |
| Island stator (stage-1 vane) | 15.67 long, chord 8.10 | | | [E3: CR-165148 Table VII p.92] |
| Inner OGV (core duct entry) | 11.61 long, chord 9.25 root / 5.44 tip, swept 60°, leaned 0→20° | | | [E3: CR-165148 Table VII p.92, §II.D p.28] |

Booster-exit and core-duct radii between the inner OGV and the HPC IGV are
**not dimensioned** in any transcribed table (CR-168219 Fig.13 p.38 is a
drawing). Interpolate linearly from booster hub/tip (52.3/66.9) to HPC IGV
hub/tip (17.3/36.2) through the transition duct and tag it `[schematic]`.

### A2. High-pressure compressor (datum: z = 0 at rotor-1 LE hub, HPC report)

Every row's LE and TE at hub and tip is in `data/hpc-flowpath.csv`
(Table XXI streamlines 1 and 12). Selected stations:

| Row / edge | z_hub | r_hub | z_tip | r_tip | height | Provenance |
|---|---|---|---|---|---|---|
| IGV LE | −6.54 | 17.34 | −7.66 | 36.21 | 18.87 | [E3: HPC Table XXI pp.112–132] |
| R1 LE | 0.00 | 17.80 | 2.09 | 35.07 | 17.28 | same |
| R1 TE | 9.25 | 20.34 | 6.89 | 34.38 | 14.04 | same |
| S1 TE | 13.98 | 21.69 | 13.63 | 33.80 | 12.11 | same |
| R2 LE / TE | 15.46 / 21.17 | 22.10 / 23.62 | 16.42 / 19.87 | 33.59 / 33.32 | 11.49 / 9.69 | same |
| R3 LE / TE | 26.38 / 30.37 | 24.81 / 25.51 | 26.89 / 29.63 | 32.83 / 32.60 | 8.03 / 7.10 | same |
| R4 LE / TE | 34.91 / 38.11 | 26.17 / 26.47 | 35.28 / 37.51 | 32.12 / 31.93 | 5.95 / 5.46 | same |
| R5 LE / TE | 42.16 / 44.86 | 26.84 / 26.92 | 42.48 / 44.39 | 31.51 / 31.35 | 4.67 / 4.43 | same |
| S5 TE (stage-5 bleed port aft of here) | 47.49 | 27.03 | 47.51 | 31.09 | 4.06 | same; port location CR-168219 §5.2.1 p.52 |
| R6 LE / TE | 49.35 / 51.53 | 27.10 / 27.16 | 49.56 / 51.20 | 30.85 / 30.73 | 3.75 / 3.57 | same |
| R7 LE / TE | 55.29 / 57.48 | 27.29 / 27.33 | 55.50 / 57.16 | 30.43 / 30.31 | 3.14 / 2.98 | same |
| S7 TE (stage-7 bleed port aft of here) | 60.28 | 27.32 | 60.26 | 30.08 | 2.77 | same |
| R8 LE / TE | 62.19 / 64.23 | 27.32 / 27.37 | 62.35 / 63.97 | 29.96 / 29.89 | 2.63 / 2.52 | same |
| R9 LE / TE | 67.96 / 69.80 | 27.36 / 27.38 | 68.11 / 69.57 | 29.70 / 29.64 | 2.35 / 2.26 | same |
| R10 LE / TE | 73.43 / 75.03 | 27.36 / 27.38 | 73.55 / 74.84 | 29.46 / 29.41 | 2.10 / 2.03 | same |
| S10 (OGV) TE | 78.21 | 27.36 | 78.21 | 29.34 | 1.99 | same |

Cross-checks already held by tests: rotor-1 LE tip 35.07 vs Table X 35.08;
Table X root/tip radii per stage (`e3-fps-published.yaml hpc.rotor_stages`)
[E3: HPC Table X p.65]. Hub flowpath is tilted 2–3° per stage (inward at LE)
so tolerance stack-ups never make a forward-facing step [E3: HPC §2.3.1 p.29].
Blockage 0.97 inlet → 0.90 exit [E3: HPC §2.3.1 p.28] — the geometric annulus
is 3–10 % wider than the flow needs; draw the walls, not the streamtube.

### A3. Combustor (no dimensioned axial drawing)

| Quantity | Value | Provenance |
|---|---|---|
| Diffuser inlet Mach / passage Mach | 0.30 / 0.16 | [E3: CR-168301 §4.2.2 p.18] |
| Prediffuser struts | 30 | same |
| Split-duct flow fraction outer (pilot) / inner (main) | 0.48 / 0.52 | [E3: CR-168219 §5.3.1 p.57] |
| Outer liner radius (from shingle arc: 20 × 11.76 cm) | 37.4 | [derived: CR-168301 Table XVI p.60] |
| Inner liner radius (15 × 12.24 cm) | 29.2 | [derived: same] |
| Shingle panels axial ×3, length 4.47 outer / 4.78 inner | liner ≈ 13–15 cm of shingled length | [E3: CR-168301 Table XVI p.60] |
| Comparators: ECCP/CF6-50 double annular 32.8 cm, QCSEE 17.8 cm; E³ "shorter and more compact than QCSEE" | | [E3: CR-168301 §3.1 pp.6–9] |
| HPT vane-1 inlet radii (= combustor exit) | hub 31.5, tip 37.2 | [E3: CR-167955 Fig.3 p.9, read off, not dimensioned] |
| HPC OGV exit radii (= diffuser inlet) | hub 27.36, tip 29.34 | [E3: HPC Table XXI] |

For drawing: OGV TE → vane-1 inlet is the one core gap with **no printed
length**. `[schematic]`: 45–55 cm (diffuser + dome + liner), scaled by eye
from CR-168219 Fig.1 p.4 / Fig.22 p.59, which this project deliberately does
not treat as a source. Label it as such on the page.

### A4. High-pressure turbine (datum: x = 0 at stage-1 vane inlet)

| Station | r_hub | r_tip | x | Provenance |
|---|---|---|---|---|
| Stage-1 vane inlet | 31.5 | 37.2 | 0 | [E3: CR-167955 Fig.3 p.9 — read off; not dimensioned] |
| Stage-1 vane exit | 32.58 | 36.58 | 3.5 | [E3: CR-167955 Fig.3 p.9 — dimensioned radii; x ±0.3] |
| Stage-1 blade exit | 32.33 | 36.60 | 8.5 | same |
| Stage-2 vane exit | 31.22 | 38.05 | 15.5 | same |
| Stage-2 blade exit (= LPT datum z = 0) | 31.12 | 38.10 | 20 | same |
| Stage exit annulus areas | 0.0895 / 0.151 m² | | | [E3: CR-167955 Fig.1 p.7, read off] |
| Radius ratio Dh/Dt | 0.88 / 0.82 | | | [E3: CR-167955 Table III p.10] |
| Blade axial chords | 3.45 (stage 1), 4.83 (stage 2) | | | [E3: CR-167955 Fig.81 p.137, Fig.87 p.146] |
| Shroud segments per stage | 24 | | | [E3: CR-167955 §4.3 p.80] |

### A5. LPT transition duct and LPT (datum: z = 0 at HPT stage-2 blade exit)

| Station | r_hub | r_tip | z | Provenance |
|---|---|---|---|---|
| Duct: HPT exit | 31.12 | 38.10 | 0 | above |
| Duct: LPT S1 LE | 32.32 | 40.78 | 6.85 | [derived: `data/lpt-flowpath.csv` from the 30 airfoil sections, LPT appendix pp.143–173] |
| Duct length printed | 7.62; outer wall slope max 25° (sections give 21° mean) | | | [E3: CR-168219 §5.5 p.82] |
| S1 LE / TE | 32.32 / 33.42 | 40.78 / 43.90 | 6.85 / 12.12 | [derived, lpt-flowpath.csv] |
| R1 LE / TE | 33.73 / 34.28 | 44.85 / 46.16 | 13.90 / 16.83 | same; Table VII tip dia 89.1 → 44.55 [E3: LPT Table VII p.80] |
| S2 LE / TE | 34.59 / 35.17 | 47.10 / 48.89 | 18.72 / 22.48 | same |
| R2 LE / TE | 35.44 / 35.96 | 49.58 / 50.90 | 23.84 / 26.80 | same |
| S3 LE / TE | 36.18 / 36.87 | 51.72 / 53.63 | 28.38 / 32.57 | same |
| R3 LE / TE | 37.14 / 37.55 | 54.28 / 55.59 | 33.94 / 37.12 | same |
| S4 LE / TE | 37.53 / 37.54 | 56.33 / 57.83 | 39.30 / 42.89 | same (hub cylindrical through stage 4) |
| R4 LE / TE | 37.54 / 37.54 | 58.45 / 59.10 | 44.73 / 47.59 | same |
| S5 LE / TE | 37.38 / 36.92 | 59.54 / 60.02 | 49.94 / 53.55 | same (hub turns inward) |
| R5 LE / TE | 36.79 / 36.79 | 60.08 / 60.13 | 55.15 / 58.65 | same; Table VII tip dia 118.3 → 59.15 |
| Blade lengths (Fig.52) | 10.90, 13.74, 16.66, 20.22, 22.58 | | | [E3: LPT Fig.52 p.83] |
| Radius ratio stage 1 / 5 | 0.76 / 0.64 (sections give 0.61 at stage 5) | | | [E3: LPT Table VII p.80] |
| Overall LPT model length | 24 in (61 cm) from HPT exit | | | [E3: LPT Fig.8 p.15] |

Hub/tip are straight-line extrapolations of the 10 % and 90 % sections; the
section radii themselves are exact. Stage-5 hub reads 2.8 % low against
Table VII for that reason [derived, `data/engine-flowpath.yaml`].

### A6. Turbine rear frame, mixer, nozzle

| Quantity | Value | Provenance |
|---|---|---|
| Rear frame struts | 12, radial, cambered to remove residual LPT swirl | [E3: CR-168219 §5.6 pp.90–95, Fig.36] |
| Mixer | 18 scalloped lobes, matching centrebody corrugations | [E3: CR-168219 §5.8 p.102, Fig.39 p.103] |
| Preliminary (Task III) mixer | 24 lobes, mixing-plane perimeter 16.26 m, mixing length 0.889 m, hydraulic dia 1.404 m, mixing-plane Mach 0.56 | [E3: CR-135444 pp.246–249] |
| Nozzle | single converging–diverging, low area ratio, C_v 0.996; centre vent tube through the exit plane | [E3: CR-168219 §5.8 pp.101–102; Table XI p.34] |
| Fan duct Mach | 0.40–0.45 | [E3: CR-168219 §5.8 p.101] |
| Lobe geometry, nozzle throat radius, tailpipe length | **not dimensioned** | Figs.39–40 only |

### A7. The two open stitching offsets

1. Fan stacking axis → HPC IGV LE: not in any transcribed table. `[schematic]`
   110–150 cm (bypass OGV at 1.8–1.9 tip chords, inner OGV, transition duct,
   No.1/2/3 bearing sump under the fan frame hub).
2. HPC OGV TE → HPT vane-1 inlet: see A3, `[schematic]` 45–55 cm.

Everything else chains: fan → (offset 1) → HPC 0…78.2 → (offset 2) → HPT
0…20 → LPT 6.85…58.65 → rear frame → mixer. A published overall engine
length does not exist in the transcribed data; the nacelle GA (Fig.40 p.106)
is undimensioned.

---

## B. Blade rows

Rotor sum = 32 + 56 + 672 + 146 + 630 = **1,536 blades**, exactly CR-168219
Table IV's "Blades 1536"; vanes 1,750 in Table IV = 60 + 64 + 32 + 996 + 94 +
504 = 1,750 **only if the 34 fan-frame OGVs are counted as frame struts** —
which is what they are [derived; E3: CR-168219 Table IV p.16].

| Row | Count | Shrouded / tip | r_hub–r_tip (cm) | Material (FPS) | Variable? | Provenance |
|---|---|---|---|---|---|---|
| Fan rotor | 32 | part-span shroud 55 % (CR-165148) / 50 % (CR-168219), tungsten-carbide faces | 36.05–105.4 | Ti-6Al-4V solid | no | [E3: CR-165148 Table IV p.47, Table V p.49, Fig.46 p.56] |
| Island stator (stage-1 vane) | 60 | banded | see A1 | Ti-6-4 (FPS; 403 SS ICLS) | no | [E3: CR-165148 Table VII p.92; CR-168219 Fig.13 says aluminium] |
| Booster rotor (quarter stage) | 56 | unshrouded | 52.3–66.9 | Ti-6Al-4V | no | [E3: CR-165148 Table IV p.47, Table V p.49] |
| Inner OGV (core duct) | 64 | banded, swept 60°, leaned 0→20° | see A1 | 7075 Al | no | [E3: CR-165148 Table VII p.92; §II.D] |
| Bypass OGV / fan-frame struts | 34 (5 camber families, pylon at 0°, thick strut at 180°) | integral with composite frame | 43.18 long | composite (FPS), 17-4 PH (ICLS) | no | [E3: CR-165148 §II.E p.30, Table VII; CR-168219 Fig.13 p.38] |
| HPC IGV | 32 | banded | 17.3–36.2 | — (Ti/steel not stated; nontitanium vanes for Ti-fire prevention) | **yes** | [E3: HPC Table XXII pp.157–159; CR-168219 §5.2.2 p.55] |
| HPC R1…R10 | 28, 38, 50, 60, 70, 80, 82, 84, 86, 94 | unshrouded | Table X per stage | Ti-8-1-1 (1–6), Inco 718 (7–10) per Table X; **stress reproduces as Ti for 1–4 and Ni for 5–10** | — | [E3: HPC Table X p.65; derived, `solvers/mechanical/STEP0.md` E1] |
| HPC S1…S10 | 50, 68, 82, 92, 110, 120, 112, 104, 118, 140 | S1–S4 cantilevered variable; rear stators banded; S10 = OGV | Table XXI | not stated per row | **S1–S4 yes** (HPC report design); CR-168219 says IGV+1–4; HPC §3.3 says FPS product IGV+1–5 | [E3: HPC Table XXII; HPC §2.3.1 p.28; §3.3 p.64; CR-168219 §5.2 p.45] |
| HPT stage-1 vane | 46 (23 two-vane segments) | banded, impingement + film cooled, 6.3 % W25 | 31.5/32.58 – 37.2/36.58 | MA754 airfoils, MAR-M-509 bands (CR-167955); **TBC added in FPS** | no | [E3: CR-167955 Table III p.10, Table XVI p.93; CR-168219 §3.1 p.10] |
| HPT stage-1 blade | 76 | unshrouded, squealer tip, ceramic shroud opposite | 32.58–36.6 | DS René 150 + PVD (CR-167955); **René N4 single crystal + TBC in FPS** | no | [E3: CR-167955 Table XVI; CR-168219 §3.1 p.10] |
| HPT stage-2 vane | 48 (24 segments) | banded, convection + TE slots, stage-7 air | 32.33/31.22 – 36.6/38.05 | DS René 150 airfoils, René 80 bands (CR-167955); **René N4 + TBC in FPS** | no | [same] |
| HPT stage-2 blade | 70 | unshrouded, solid René 77 shroud opposite | 31.22–38.1 | DS René 150, serpentine cooled 0.76 % (CR-167955); **DS eutectic, uncooled, in FPS** | no | [E3: CR-167955 §3.2.5 p.54; CR-168219 §3.1 p.10] |
| LPT V1…V5 | 72, 102, 96, 114, 120 | banded, 4/6/6/6/6 per segment (18/17/16/19/20 segments); V1–V3 hollow, V4–V5 solid | A5 | René 125 (V1), René 77 (V2–V5) | no | [E3: LPT Fig.6 p.12, Fig.80 p.124, Table V p.76] |
| LPT R1…R5 | 120, 122, 122, 156, 110 | **integral tip shrouds**, interlocked, two-tooth seals | A5 | cast René 77, uncoated | no | [E3: LPT Fig.52 p.83, §4.2.1 p.82] |
| Turbine rear frame struts | 12 | — | 36.8→ ~60 | Inco 718 | no | [E3: CR-168219 §5.6 p.95] |
| Mixer lobes | 18 | — | — | Inco 718 (centrebody Inco 625) | no | [E3: CR-168219 §5.8 p.102] |

Notes for the model: LPT stage 4 has 156 blades and a 1.4-chord vane-blade gap
for acoustic cut-off [E3: CR-168219 §5.5.1 p.85]. Stage-1 LPT vane went
56 → 72 between Block I and II [E3: LPT §2.5 p.10]. HPC rotors 9/10 went
88/98 → 86/94 between original and final design [E3: HPC Table XXI headers vs
Table X]. HPC casing is split (horizontal flanges) for blade/vane replacement
[E3: CR-168219 Fig.5 p.15]; the LPT casing has no horizontal flanges [E3: LPT
§4.3.3 p.128].

---

## C. Cycle and rotor numbers

### C1. Cycle (Table XII, three ratings)

| Quantity | Max climb (match point, 10.67 km, M0.8, ISA+10) | Max cruise | Takeoff (SLS, ISA+15 flat rating) | Provenance |
|---|---|---|---|---|
| OPR | 38.4 | 36.5 | 32.4 | [E3: CR-168219 Table XII p.35] |
| BPR | 6.7 | 6.8 | 7.0 | same |
| Fan bypass / hub PR | 1.68 / 1.70 | 1.64 / 1.66 | 1.56 / 1.58 | same |
| HPC PR | 23.1 | 22.4 | 20.8 | same |
| T41 (HPT rotor inlet) | 1517 K (1244 °C) | 1485 K | 1638 K (1365 °C) | same; also CR-168219 Table III p.9 |
| Combustor exit T4 | 1573 K | 1540 K | 1695 K | [derived: cycle solver, `solvers/e3cycle/STEP0.md`; ≈55–80 K above T41 = the nonchargeable coolant] |
| sfc (std day, uninstalled) | 0.0541 kg/h·N | 0.0540 | 0.0305 | [E3: Table XII] |
| Fan corrected flow | 646.0 kg/s | 634.1 | 577.9 | [E3: CR-168219 §5.1.1 p.41; CR-165148 Table I p.4] |
| Fan physical flow | ≈245 kg/s | — | ≈578 kg/s (SLS) | [derived: corrected ÷ (δ/√θ) at P_t 36.3 kPa, T_t 258 K] |
| Core corrected flow W25 | 54.4 kg/s at T25 304.8 K, P25 60.5 kPa | | | [E3: CR-168219 Table XIV p.51] |
| Core physical flow | ≈31.6 kg/s (climb); ≈72 kg/s (SLS takeoff, from BPR 7.0) | | | [derived] |
| Combustor flow, std-day takeoff | 55.3 kg/s, f/a 0.024, T3 815 K, P3 3.03 MPa | | | [E3: CR-168301 Table XVII p.92] |
| Takeoff thrust | 173.5 kN (39,000 lbf) final; 162.4 kN (36,500) initial | | | [E3: CR-168219 §4.3 p.32]. Note: p.139 prints "175.3 kN (39,000 lbf)"; 39,000 lbf is 173.5 kN — misprint, read for this sheet |
| As tested (ICLS, 1983) | sfc 0.0332 kg/h·N SLS as tested, 0.0316 fully corrected; thrust +2.5 % over design | | | [E3: CR-168211 pp.1–2, Table XII p.284] |
| Cooling/secondary air | 7.46 % CPD nonchargeable + 5.33 % CPD chargeable + 1.95 % stage 7 + 1.40 % stage 5 = 16.1 % of W25 | | | [E3: CR-168219 Table XI p.34] |
| Component η at max cruise | fan 0.894 / hub 0.906 / HPC 0.861 / comb 0.999 (ΔP 5 %) / HPT 0.927 / LPT 0.925; mixer eff. 0.838 | | | [E3: Table XI p.34] |

### C2. Spool speeds

| Quantity | Value | Provenance |
|---|---|---|
| N1 (LP) physical, max climb (case 41) | 3,539 rpm (growth 3,939) | [E3: LPT Table VI p.80; CR-165148 Table III p.46] |
| N1 takeoff (case 72, max stress) | 3,611 rpm; overspeed 3,653 (fan, +1.2 %) / 3,707 (LPT, +2.6 %) | same |
| N1 corrected at match point | 3,727.7 rpm | [E3: CR-165148 App. A p.118] |
| N2 (HP) 100 % corrected | 12,303 rpm | [E3: HPC Table X footnote p.65] |
| N2 physical, max climb | 12,645 rpm | same |
| N2 hot-day takeoff | 13,287 (CR-167955 Table VIII p.27) / 13,414 (Fig.84 p.142) / 13,300 (Fig.53 p.100, growth) | [E3: CR-167955] |
| N2 deteriorated-engine stress case | 13,948 rpm | [E3: HPC Table X p.65] |
| ICLS as tested, SLS: takeoff / flight idle / ground idle | 3,282 / 1,215 / 891 N_F; 12,576 / 9,452 / 8,371 N_c | [E3: CR-168211 §6.18.2.3 p.545, read for this sheet] |
| Both shafts co-rotating | yes; LP : HP ≈ 1 : 3.6 | [E3: CR-168219 §3.1 p.10] |

### C3. Blade and rim speeds

| Quantity | Value | Provenance |
|---|---|---|
| Fan corrected tip speed | 411.5 m/s (climb), 399.6 (cruise), 365.2 (takeoff) | [E3: CR-165148 Table I p.4] |
| Fan physical tip speed | 390.6 m/s at 3,539 rpm; 398.5 at 3,611 | [derived: 2π·1.054·N/60] |
| Fan tip relative Mach | 1.41 (1.4 in CR-168219) | [E3: CR-165148 Fig.10; CR-168219 §5.1.1 p.43] |
| Booster tip speed | 261.1 m/s (corrected, climb) | [E3: CR-165148 Table IV p.47] |
| HPC corrected tip speed | 456 m/s; physical R1 tip ≈464 m/s at 12,645 rpm | [E3: CR-168219 §5.2.1 p.48; derived] |
| HPC front-stage rotor tip rel. Mach | 1.35 (R1), transonic R1–R4 | [E3: HPC Fig.20 p.37] |
| HPT tip speed, takeoff | 513.9 (stage 1) / 535.2 (stage 2) m/s | [E3: CR-167955 Table III p.10] — these imply 13,410 rpm at Fig.3's tip radii [derived] |
| HPT rim (hub-line) speed at 13,414 rpm | ≈454 (stage 1, r 32.3) / ≈437 (stage 2, r 31.1) m/s | [derived] |
| HPT AN² stage 2 | 2.4×10⁷ m²·rpm² (3.7×10¹⁰ in²·rpm²) at 12,645 rpm | [derived from Fig.1 area] |
| LPT tip speed at 3,611 rpm | 168.6 (stage 1) / 223.7 (stage 2, printed "23.7") m/s | [E3: LPT Table VII p.80] |
| LPT rim speed at 3,611 rpm | ≈128 (stage-1 hub r 33.7) / ≈139 (stage-5 hub r 36.8) m/s | [derived] |
| Fan blade CF per blade / disc | ≈746 kN blade-out load; 7.27 kg per blade | [derived E4; E3: CR-165148 Table VI p.74] |
| HPT stage-1 blade pull | 77.4 kN per blade at 13,948 rpm → 5,882 kN on the disc | [E3: CR-167955 Fig.81 p.137; derived] |

### C4. Bearings, sumps, shafts

| Item | E³ fact | Provenance |
|---|---|---|
| Count | 5 bearings, 2 sumps, 2 frames (CF6-50C: 7 / 4 / 4) | [E3: CR-168219 Table IV p.16; §5.7.1 p.96] |
| No.1 | ball, LP thrust, forward sump, in the fan frame hub; eccentric fan-disc contour lets it sit close to the fan centreline | [E3: CR-168219 §5.7.2 p.96, Fig.37 p.97; CR-165148 §III.E p.69] |
| No.2 | roller, LP shaft support, forward sump, just ahead of the PTO drive gear; carries the LP speed pickup (cogged wheel + magnetic pickup on the No.2 housing) | [E3: CR-168219 §5.7.2 pp.96–98] |
| No.3 | ball, HP (core) thrust, forward sump; squirrel-cage centering spring k = 52,540 kN/m (3×10⁵ lb/in); multi-film squeeze-film damper, 5 sleeves, 1.27 mm radial clearance, r 137.46 mm, length 27.94 mm, 6 × 1.6 mm oil holes with check valves, piston-ring end seals | [E3: CR-168219 §5.7.2 p.96; §5.11.1 p.135; Fig.57 p.138] |
| No.4 | intershaft roller, aft sump; outer race in a controlled-spring-rate housing (rotating squirrel cage, k = 52,540 kN/m) on the LP shaft, inner ring on the aft HP stub shaft — eliminates a hot frame | [E3: CR-168219 §5.7.3 p.98; Fig.56 p.136; §5.11.2 p.137] |
| No.5 | roller, aft sump, mounted to the turbine rear frame; supports both rotors through No.4; No.4 and No.5 underrace-cooled by a jet on the No.5 housing | [E3: CR-168219 §5.7.3 p.98, Fig.38 p.99] |
| LPT rotor support | single bearing cone from the HPT/LPT sump to the LPT spool between the stage-3 and stage-4 discs | [E3: LPT §4.1.1 p.76; CR-168219 §5.5 p.82] |
| Sump sealing | labyrinth seals pressurised by fan discharge air, both sumps; forward sump vented through the LP fan shaft; aft sump vented through an air/oil separator on the end of the LP shaft; all vent air out the aft centre vent tube | [E3: CR-168219 §5.7.2–5.7.3 pp.96–98] |
| Aft sump thermal blanket | compressor rotor cooling air and seal pressurisation air surround the aft sump in sealed cavities | [E3: CR-168219 §5.7.3 p.98] |
| Fan shaft | steel: 4340 (demonstrator), MARAGE 250 intended for FPS; disc-shaft joint 30 × 5/8-in Inco 718 bolts, 101.9 kN preload each, torque by friction | [E3: CR-165148 Table V p.49, Fig.61 p.73] |
| HP shaft (forward) and aft shaft/seal disc | Inco 718 (ICLS) → "Super" Inco 718, grain 7 (FPS) for 36,000 cycles; runs ≈538 °C at hot-day takeoff | [E3: CR-167955 §5.1.2 p.90; §3.2.2 p.37] |
| LP (LPT) shaft | material not stated in transcribed data; "steel fan shaft" forward | — |
| HPC rotor | inertia-welded forward and aft sections, one bolt joint, bore cooled by fan discharge air | [E3: CR-168219 §5.2.2 p.52] |
| HPT rotor | René 95 PM discs, AF115 inducer/impeller/seal disc/retainers, no bolt holes in live discs, boltless blade retainers | [E3: CR-167955 Fig.51 p.91, §5.1.1 p.86] |
| LPT rotor | Inco 718 discs with integral spacer arms, bolted flanges, no disc bolt holes (40/40/52/76/40 bolts per joint) | [E3: LPT Table V p.76, Table XIV p.110] |
| Rotordynamics | no speed-avoidance zones; max synchronous vibration at the No.3 accelerometer 0.104 mm-DA 1/core at 12,420 N_c, 0.127 mm-DA 1/fan at 2,600 N_F; no fan nodding mode in range | [E3: CR-168219 §5.11.2 p.137] |

---

## D. The twelve systems

Clock positions are aft-looking-forward with the pylon at 12 o'clock unless
stated. "Core compartment" = the annulus between the core casings and the
inner fan-duct wall, closed at the HPT by the pressure bulkhead.

### D1. Gas generator (thermodynamic unit)

Click targets: fan rotor · island/booster · inner OGV · HPC IGV, ten rotors,
ten stators · diffuser · combustor (domes, liners, centrebody) · HPT stage-1
vane/blade, stage-2 vane/blade · LPT five stages · rear frame · mixer ·
nozzle. All at the axial stations of §A.

Function (plain English): the fan does the propulsive work — 87 % of the air
never sees the core. The booster and ten-stage HPC raise the core stream to
38:1; the double-annular combustor adds heat at a constant ~5 % pressure loss;
the two-stage HPT drives the HPC and the five-stage LPT drives the fan and
booster; the mixer merges the hot core with the cold bypass so one nozzle can
expand both.

E³ specifics: 32-blade fan, quarter-stage booster on an untrapped island
that centrifuges debris out of the core [E3: CR-168219 §5.1 p.41]; HPC 23:1
in 10 stages [E3: Table XIV p.51]; combustor exit → T41 ≈ 80 °C of coolant
dilution [derived, Stage D5]; HPT 56.5/43.5 work split [E3: CR-167955 §2.2.4
p.6]; LPT loading 1.71 → 0.80 by stage [E3: LPT Table II p.16].

### D2. Fuel system

| Component | Where | Provenance |
|---|---|---|
| Main fuel pump: positive-displacement vane element with integral centrifugal boost; pump-mounted filter | accessory gearbox, core compartment, lower half (Fig.46: "Main Fuel Pump", "Main Fuel Pump Filter (Aft)") | [E3: CR-168219 §5.10.2 p.125, Fig.46 p.117; CR-168017 §5.1 p.12] |
| Fuel control (on the end of the pump): metering valve + bypass valve, mechanical core-overspeed governor acting on the bypass, shutoff valve, pressurising valve; RVPT metering-valve position transducer | AGB, "Main Fuel & Control (Aft)" | [E3: CR-168219 §5.10.2 p.125, Fig.52 p.127; CR-168017 §11.4.2 p.103] |
| Fuel/oil cooler (lube-oil cooler in the fuel line) | downstream of the shutoff valve, outside the fan duct | [E3: CR-168219 Fig.52 p.127; CR-168017 Fig.5 p.13] |
| Fuel heater/regenerator: ECS-air heat to fuel via a water/antifreeze loop, bypass valve from the FADEC | pylon/aircraft interface | [E3: CR-168219 §5.10.5 p.133, Fig.55 p.134] |
| Main Zone Shutoff Valve (MZSOV) and Pilot Zone Reset Valve (PZRV), servo-operated | MZSOV inside the fan duct on the core; PZRV outside | [E3: CR-168219 §5.10.2 p.128; CR-168017 Fig.5 p.13] |
| Two independent manifolds (pilot, main) and pigtails, stainless steel | around the combustor casing | [E3: CR-168301 §5.3.2 pp.74–80] |
| 30 single-stem dual-tip duplex nozzles (pilot primary/secondary + main primary/secondary), 347 SS body, Hastelloy X tips, 750 Hz first flex, max ΔP 3,102 kPa | combustor casing, 30 ports, valves above the flange cooled by fan air | [E3: CR-168219 §5.3.2 p.61; CR-168301 §4.2.3 pp.21–23, Table XX p.129] |
| Fuel-powered actuators: VSV rams, ACC modulating valves, start-bleed valve all use pump excess capacity through electrohydraulic servovalves | — | [E3: CR-168017 §4 p.11; CR-168219 §5.7.4 p.100] |

Function: fuel is metered to hold corrected fan speed, then split between
the outer (pilot) and inner (main) domes; pilot only for start, ground idle
and flight idle, both zones above (main stage on at ~80 % N2). Fuel is also
the hydraulic fluid for every actuator on the engine and the coolant for the
FADEC's chassis plate.

E³ specifics: SLTO fuel flow ≈2,600 kg/h, idle ≈300 [E3: CR-168301 Fig.27
p.51, read off]; pilot ≈40 % of total at high power [same]; fuel inlet limit
408 K for coking [E3: CR-168301 §5.4.1.4 p.104].

### D3. Control system

| Component | Where | Provenance |
|---|---|---|
| FADEC — single time-shared microprocessor, 3.5 MHz clock, ≈10 ms program cycle; hybrid ceramic multilayer boards (alumina/tungsten, Kovar leads) on a fuel-cooled aluminium plate; primary + active-standby units for initial service | ICLS: mounted on the fan case (no problems in 65 h); FPS location not stated | [E3: CR-168219 §5.10.1 pp.118–124, Fig.47 p.119, Fig.50 p.124; §5.10.6 p.135] |
| Control alternator (engine-driven, primary FADEC power; N2 read from its frequency); aircraft 28 V DC backup for checkout and starts | AGB, upper left of Fig.46 | [E3: CR-168219 §5.10.1 p.120, Fig.46 p.117] |
| Sensors: T12 (RTD, inlet duct ahead of the fan, F101 part), PT0, T25 (RTD, core inlet duct), N1 (magnetic pickup on a 6-tooth wheel on the fan shaft, F101 sensor), N2, T3 (chromel-alumel thermocouple on the outer combustor case), PS3, T42 (thermocouples in rakes behind the HPT), casing skin thermocouples on HPC/HPT/LPT, customer-bleed ΔP | see Fig.48 | [E3: CR-168219 §5.10.1 p.120, Fig.48 p.121; CR-168017 §11.5–11.10 pp.103–108] |
| Outputs: fuel flow and split (MZSOV/PZRV), core stator position, start-bleed valve, compressor clearance valve, HPT clearance valve, HPT heating valve, LPT clearance valve, reverser | Fig.49 boxes = "functions not on CF6-50C" | [E3: CR-168219 Fig.49 p.123] |
| Servovalves: multiple-coil electrohydraulic, fail-fixed or drift-safe; LVPT/RVPT position feedback | on each actuator | [E3: CR-168219 §5.10.1 p.120; CR-168017 §11.3–11.4] |
| Hydromechanical backup (ICLS/core): transfer valves switch fuel and stator control to a hydromechanical computer; other outputs go to safe positions | fuel control | [E3: CR-168017 §4 p.11, §10.1 p.68] |
| FICA — failure indication and corrective action: simplified engine model + extended Kalman filter substitutes calculated values for failed sensors | FADEC software | [E3: CR-168219 §5.10.1 p.120] |
| Starters: two Hamilton Standard PS600-3 air-turbine starters on the AGB (largest available) for a 60-s start; the second starter and the 30 % stage-7 start bleed were never needed and are deleted from the FPS | AGB "Start (Aft)" pad | [E3: CR-168017 §5.2 p.37; CR-168219 §4.6 p.36, §3.1 p.10; CR-168211 p.132] |

Function: a full-authority digital control — one of the first on a large
transport engine — replaces hydromechanical computation. It sets thrust on
corrected fan speed (best of 14 candidate parameters), applies T41/T42/PS3
limits, schedules the stators against corrected core speed with rain, stall,
reverser, deterioration and bleed biases, and modulates three independent
clearance-control loops on measured casing temperature.

E³ as tested: stator tracking ±0.5° in fast transients; flight idle to 90 %
thrust in ≈5.5 s; all FICA sensor-failure cases handled except core speed
[E3: CR-168219 §5.10.6 pp.133–135].

### D4. Air system (bleed, cooling, sump pressurisation, clearance control)

| Component | Where | Provenance |
|---|---|---|
| Stage-5 bleed port (customer bleed up to 9 %; aft-HPC ACC 1.3–1.4 %; then LPT vane cooling and HPT stage-2 disc aft purge) | HPC casing after stator 5, z ≈ 47.5 cm | [E3: CR-168219 §5.2.1 p.52, §5.7.4 p.100; HPC §2.3.1 p.28] |
| Stage-7 bleed port (HPT stage-2 nozzle 1.95–2.35 %; shares the start-bleed port sized for 30 %) | HPC casing after stator 7, z ≈ 60.3; four pipes into eight HPT casing inlet ports | [E3: CR-167955 §3.2.4 p.49; CR-168219 §5.2.1 p.52] |
| CDP: combustor-liner bypass air to HPT vane 1 (6.3 % vanes + 2.8 % bands); diffuser **mid-span** bleed through 28 struts to the inducer/expander (80 %) and CDP-seal blockage (20 %) for both HPT blades | combustor casing, 8 CDP bleed ports on the case | [E3: CR-167955 §3.1.3 p.23, §3.2.2 p.37; CR-168301 Fig.38 p.67] |
| Inducer / expander (80 vanes) and impeller: accelerate rotor coolant to wheel speed, raise stage-1 blade supply pressure; 64 CDP-leakage bypass tubes | forward of the HPT stage-1 disc | [E3: CR-167955 §3.1.3 p.23, Fig.95 p.158] |
| Compressor ACC: valve passes stage-5 air over the aft casing (stages 6–10); the casing is isolated from hot flowpath gas and bathed in bleed air | aft HPC casing, fuel-actuated valve with position feedback | [E3: CR-168219 §5.10.4 p.131, §5.2.2 p.55, Fig.54 p.132] |
| Turbine ACC: fan air via a split scoop on the pylon skirt, 2:1 diffuser, two fuel-operated butterfly valves in the pylon (HPT, LPT), a 270° duct in the core cowl, four feed pipes to four 90° impingement manifolds per stage (HPT) and a 4-sector backbone/rib manifold of 321 SS tubes (LPT); max 0.3 % of core flow | over the HPT and LPT casings | [E3: CR-167955 §4.1–4.3 pp.69–83; LPT §4.4 pp.128–135; CR-168219 §5.10.4 p.131] |
| HPT casing heating circuit: 0.3 % W25 of CDP impinged on the casing for 200 s after idle to avoid a takeoff rub; direct-acting solenoid valve | HPT casing | [E3: CR-167955 §4.1 p.71; CR-168017 §4 p.11] |
| Pressure bulkhead ("fire safety wall"): six-sector curved wall making a low-pressure sink around the turbine casings so spent ACC air can exit through the rear-frame struts and the centre vent stinger; designed for 389 °C radial gradient and 48 kPa; metal bellows at pipe penetrations | between the core casings and the inner fan duct, at the HPT | [E3: CR-168219 §5.7.4 p.100, §5.4.3 p.73] |
| Sump pressurisation: fan discharge air to the forward-sump labyrinths, flowing aft to the aft sump through the vent-shaft/LP-shaft annulus | both sumps | [E3: CR-168219 §5.7.2–5.7.3] |
| HPC bore cooling: fan discharge air through the rotor bore | HPC rotor | [E3: CR-168219 §5.2.2 p.52] |
| Rear-frame hub heating: 0.147 % + 0.05 % W25 bled radially inward between LPT stage 5 and the frame hub, vented to the centre vent | turbine rear frame | [E3: CR-168219 §5.6 pp.90–95] |
| Interstage seal disc, CDP seal (Inco 903A), balance-piston seal, honeycomb over the HPT stage-2 retainer and LPT stage-1 seal (5th-stage purge to the HPT aft cavity and LPT stages 1–3 cavity) | HPT/LPT interface | [E3: CR-167955 §5.2.2.2 p.157; LPT §4.3.1 pp.118–123] |

Function: about a sixth of the core flow never reaches the turbine as
working fluid. It cools the hot parts, keeps hot gas out of the disc cavities
(backflow margins 1.0–1.45 % on the stage-1 nozzle cavities), pressurises the
oil seals, and — new on this engine — is metered onto the casings to close
tip clearances in cruise. Every stream is taken from the lowest pressure
that will do the job.

E³ specifics: HPT ACC is worth −1.22 % sfc for 0.15 % W25 of fan air; LPT ACC
−0.33 % [E3: CR-167955 Table X p.73; LPT Fig.48 p.73]. Casing left uncooled
through takeoff by design [E3: CR-167955 §4.1 p.69]. HPT running clearance
0.041 cm desired at cruise, 0.064 cm at takeoff [E3: CR-167955 §4.2 p.73].

### D5. Oil system

| Component | Where | Provenance |
|---|---|---|
| Oil tank | on the **outer fan case**, for quick inspection | [E3: CR-168219 §3.2 p.12] |
| Lube & scavenge pump: one supply element, separate scavenge elements per sump and the gearbox; lube pump filter | AGB, core compartment (Fig.46 "Lube & Scavenge Pump", "Lube Pump Filter") | [E3: CR-168219 §5.7.5 p.100, Fig.46 p.117] |
| Filters on supply and scavenge; scavenge inlet screen; supply check valves against sump flooding at shutdown | lube lines | [E3: CR-168219 §5.7.5 p.100] |
| Fuel/oil cooler | fuel line downstream of the fuel control | [E3: CR-168219 Fig.52 p.127] |
| Forward sump (No.1, 2, 3 + PTO bearings): jet or underrace lube from a common manifold; the No.3 damper fed from its own manifold | fan frame hub | [E3: CR-168219 §5.7.2 p.96] |
| Aft sump (No.4, 5): underrace cooling from a jet on the No.5 housing; air/oil separator on the LP shaft end | turbine rear frame hub | [E3: CR-168219 §5.7.3 p.98] |
| Lube lines cross the gas path inside the rear-frame struts; sumps and gearbox centre-vented aft to the nozzle | rear frame / centre vent tube | [E3: CR-168219 §5.6 p.90, §5.7.5 p.100] |
| Chip detectors, soap (oil) sampling, filter-bypass indication | lube system maintainability features | [E3: CR-168219 Fig.5 p.15] |
| Oil quantity, pressure, temperature: not specified in the transcribed data | — | `[schematic]` per Rolls-Royce *The Jet Engine* ch. on lubrication |

Function: one pressure pump feeds five main bearings and the gearbox; scavenge
elements pull the oil back through a filter and the fuel-cooled cooler; the
sumps are held above cavity pressure by fan air so oil stays in and hot air
stays out; breather air leaves through the tail-cone vent.

### D6. Ignition

| Component | Where | Provenance |
|---|---|---|
| 2 igniter ports | combustor casing at **120° and 240°** (≈4 and 8 o'clock) | [E3: CR-168301 Fig.38 p.67, Fig.39 p.68] |
| Igniter plug in the outer (pilot) liner, panel 1, flush with the wall (rig: at 240° ALF) | outer liner | [E3: CR-168301 §6, p.275, read for this sheet] |
| Ignition exciter box, igniter lead routed under the core cowl (core cowl purged by ≈478 K fan air; soak-back after shutdown analysed to 616 K against a 700 K PTFE limit) | core compartment | [E3: CR-168301 §5.4.1.5 p.105–106] |
| 2 crossfire tubes through the centrebody, in line with the igniters, to light the main dome | centrebody | [E3: CR-168301 §5.3.2 p.73] |
| Rig ignition system (GE23 standard): 2 J delivered, 2 sparks/s | rig | [E3: CR-168301 p.275]. Flight exciter energy/rate: `[schematic]` |

Function: only the pilot dome is lit at start; the main dome ignites by
crossfire when the MZSOV opens at ~80 % N2. Start on the ICLS took 44 s with
no bleed [E3: CR-168211 p.1]. Altitude relight requirement 9.1 km
[E3: CR-168301 Table II p.5].

### D7. Variable geometry

| Component | Where | Provenance |
|---|---|---|
| Variable IGV + stators 1–4 (HPC report design; CR-168219 §5.2 says IGV + 1–4; HPC §3.3 says FPS product IGV + 1–5, development IGV + 1–6) | front HPC casing | [E3: HPC §2.3.1 p.28, §3.3 p.64; CR-168219 §5.2 p.45] |
| Actuation: a pair of fuel-driven ram actuators, levers and unison rings; one electrohydraulic servovalve; LVPT position feedback; torsion-bar linkage | HPC casing, both sides | [E3: CR-168219 §5.10.3 p.128, Fig.53 p.129; HPC p.99] |
| Vane bushings: ZX / Fabroid XV composites to 546 K (IGV–S3), PBH-20 carbon beyond | vane trunnions | [E3: HPC Table XVIII p.102] |
| Start-bleed valve (stage 7, up to 30 % — deleted from FPS) | HPC casing | [E3: CR-168219 §4.6 p.36] |
| Thrust reverser: fixed cascades, translating sleeve, blocker doors on a floating unison ring, in two halves hinged at the pylon and latched at 6 o'clock; FADEC-controlled | nacelle outer wall, aft of the fan frame | [E3: CR-168219 §5.9.1 pp.105–110, Figs.41–42] |
| ACC valves and casing-heating valve (see D4) | pylon / casings | — |
| Fuel-flow split valves (see D2) | — | — |

Function: the front stators close at part speed to keep the transonic front
stages off stall and open at design speed; the schedule is corrected core
speed with biases. The reverser is the nacelle's only moving part.

### D8. Anti-icing

**No E³ anti-ice hardware is described in the transcribed reports.** The only
mention is the controls report listing "engine bleed and power extraction as
required for anti-icing and aircraft accessories" as a control-mode-study
input [E3: CR-168017 §5.2 p.16, Table II p.17]. The ICLS ran on a static
test stand with a nonflight inlet.

`[schematic]` for the page: inlet-lip hot-air anti-ice fed from an HPC bleed
(stage 5 or 7 on this engine) through a pressure-regulating shutoff valve on
the fan case; spinner anti-ice by conduction/shape (composite spinner,
32° half-angle [E3: CR-165148 p.3]); fan-frame OGV/strut anti-ice not
required on a composite frame in GE practice [textbook: Rolls-Royce, *The Jet
Engine*, ch. 11].

### D9. Fire detection and protection

| Item | E³ fact | Provenance |
|---|---|---|
| Fire safety wall = pressure bulkhead: six-sector curved wall at the HPT isolating the turbine compartment from the rest of the core compartment | CR-168219 §5.4.3 p.73, §5.7.4 p.100 | [E3] |
| Pylon firewall in the mount beam just aft of the ACC plenum; pylon panels aft of it steel, rest aluminium | ICLS | [E3: CR-168211 pylon description p.118, read for this sheet] |
| Titanium fire prevention in the HPC: **nontitanium casings and vanes** | HPC | [E3: CR-168219 §5.2.2 p.55] |
| Combustor outer casing carries "the engine firewall" among its functions | combustor case | [E3: CR-168301 §5.2 p.52] |
| ICLS safety instrumentation: **undercowl fire-detection thermocouples**, sump pressures/temperatures, bearing thermocouples, accelerometers on bearing supports and frames, rotor speeds, fuel flows | ICLS test | [E3: CR-168211 Table VI p.163, read for this sheet] |
| Accessory package in a "thermally protected compartment", core cowl purged with fan air | core compartment | [E3: CR-168219 Fig.46 p.117; CR-168301 §5.4.1.5 p.105] |
| Finding worth showing: bulkhead reinforcement of the lower half of the fire wall next to the HPT stage-1 casing forward flange is one of three named causes of the ICLS HPT casing eccentricity that kept HPT ACC from being fully used (the others: uneven core-cowl airflow, initial assembly eccentricity) | ICLS | [E3: CR-168211 HPT section p.375, read for this sheet from the OCR layer] |

`[schematic]`: continuous-loop fire detectors (two loops, AND-logic) in the
fan-case zone and the core zone; two halon/agent bottles in the pylon
discharging into the core zone; fire zones = fan compartment, core
compartment, with the bulkhead splitting the core zone at the HPT
[textbook: Rolls-Royce, *The Jet Engine*, ch. 14; CS-E 530 / Part 33.17 for
the requirement].

### D10. Vibration monitoring

| Item | E³ fact | Provenance |
|---|---|---|
| FPS design: accelerometer at the No.3 bearing on the soft (rotor) side of the forward squirrel cage — the reference point for the published vibration levels | forward sump | [E3: CR-168219 §5.11.2 p.137] |
| ICLS monitoring set (Table XXIX): accelerometers on the AGB (vertical), No.1 (H), No.2 (V+H), No.3 rotor side (V 350°, H 80°), No.5 (H), forward fan case, fan frame (V+H), forward compressor case, forward combustor case, turbine frame (V 355°), exhaust centrebody, slip ring; proximity probes across the No.3 damper (231°, 71°); dynamic strain gauges on the No.3 and No.4 squirrel cages | engine-wide | [E3: CR-168211 Table XXIX p.546, §6.18.2.2 p.545, read for this sheet] |
| Speed pickups: N1 magnetic pickup on a cogged wheel forward of No.2; N2 from the control alternator frequency | forward sump / AGB | [E3: CR-168219 §5.7.2 p.98, §5.10.1 p.120] |
| Residual unbalance design values: HP 150 g·in (381 g·cm), LP 500 g·in (1,270 g·cm); 3 mils of vibration carried in every clearance stack | — | [E3: HPC Table XVI p.96; CR-167955 Table XIII p.84] |
| Result: no speed-avoidance zones; core response flat and highly damped | — | [E3: CR-168219 §5.11.2 p.137] |

`[schematic]` for a production engine: two accelerometers (fan frame and
turbine rear frame) into an airborne vibration monitor with 1/rev tracking
for fan trim balance.

### D11. Exhaust system

| Component | Where | Provenance |
|---|---|---|
| Turbine rear frame: 12 cambered radial struts, Inco 718 polygonal casing, heat shield, 1.75×10⁶ N/cm spring rate No.5-to-casing, 3 mount lugs; Astroquartz acoustic panels (25.63 kg/m³, 1.27 cm) under a shear cylinder perforated 30 % open with 0.158 cm holes | aft of LPT R5 | [E3: CR-168219 §5.6 pp.90–96] |
| 18-lobe scalloped mixer, Inco 718 | on the rear frame | [E3: CR-168219 §5.8 p.102, Fig.39] |
| Centrebody with matching corrugations, Inco 625, links to the mixer | inside the mixer | same |
| Centre vent tube from the tail cone through the nozzle exit plane; vents both sumps, gearbox, rear-frame cavities and spent ACC air ("vent stinger") | centreline | [E3: CR-168219 §5.8 p.102, §5.7.5 p.100; CR-167955 §4.1 p.72] |
| Long-duct mixed-flow tailpipe and single C-D nozzle, low area ratio, C_v 0.996 | nacelle | [E3: CR-168219 §5.8 pp.101–102] |
| Bulk absorber acoustic treatment in the nacelle and exhaust flowpath | — | [E3: CR-168211 p.2] |

Function: mixing 0.95–0.96 pressure-ratio core into the bypass buys ≈2.9 %
sfc at 85 % mixing effectiveness for 0.57 % pressure loss [E3: CR-168219
Table XXIII p.104]; the ICLS mixer beat its model by 5–8 % [E3: CR-168211
p.3, p.622]. The rear frame is the deswirler — there is no separate exit
guide vane row.

### D12. Structure, casings, mounts

| Component | E³ fact | Load path | Provenance |
|---|---|---|---|
| Fan frame | integral graphite-composite frame with aluminium hub; the 34 OGVs are its struts; outer portion forms the nacelle surface; carries No.1 (LP thrust), No.2 and No.3 (HP thrust) in the forward sump; PTO radially out through the bottom strut; pylon at 0°, thick strut at 180° | all rotor thrust and forward vertical/side loads → frame → forward mounts | [E3: CR-168219 §5.1.2 p.45, §5.7.2 p.96, §5.9 p.102; CR-165148 §II.E p.30] |
| Fan containment | Kevlar wrap on an aluminium liner; ICLS slave was a CF6 steel case | blade-out energy | [E3: CR-168219 §5.9 p.102, §5.1.2 p.45; CR-165148 p.3] |
| Forward mounts | four links on brackets on the **aft side of the fan frame**, under the core cowl: two for vertical+side, two thrust links at ±45° from top through a pivoting whiffle tree, so thrust reacts at two points 90° apart to minimise casing ovalisation | thrust + vertical + side | [E3: CR-168219 §5.9.2 p.110, Figs.44–45 pp.112–113] |
| Aft mounts | three links on the turbine rear frame: a short lateral link inside the pylon (roll + side) and two streamlined vertical links through the fan stream | vertical + roll | same |
| Mount links | seven total, all in uniballs | — | same |
| HPC casings | front / aft / manifold casings, 60 / 32 / 28 × 3/8-in bolts, no flange separation at 2× ICLS pressure; split casing for blade/vane replacement; nontitanium | core backbone | [E3: HPC Table XVII p.102; CR-168219 Fig.5 p.15, §5.2.2 p.55] |
| Compressor rear frame / diffuser | split-duct prediffuser with 30 struts; the diffuser and combustor casing are Inco 718; the HPT stage-1 inner nozzle support (René 41) bolts to the compressor OGV flange with 64 × 3/8-in Waspaloy bolts | core backbone | [E3: CR-168301 §4.2.2 p.18; CR-168219 §5.3 p.57; CR-167955 §5.2.2.2 p.154–157] |
| Combustor casing | Inco 718 pressure vessel, 30 support pins (3/8-in Inco 718) carrying dome and liner loads, 30 fuel-nozzle, 30 instrumentation, 2 igniter, 8 CDP-bleed, 4–6 borescope ports; axial loads 249 kN fwd flange / 222 kN aft flange at growth P3 | core backbone | [E3: CR-168301 §5.3.2 pp.63–70, Fig.77 p.122] |
| HPT casings | forward and aft outer nozzle supports = the structural link through the HPT; Direct-Age Inco 718 (10× LCF); single wall with fan-air impingement directly on it | core backbone | [E3: CR-167955 §5.2.2 p.150, §5.2.2.1 p.154] |
| LPT casing | two Inco 718 forgings, one EB weld, no horizontal flanges; 132 × 5/16-in bolts to the HPT casing (sized for axial containment of the LPT rotor on a shaft failure), 120 to the rear frame; wall insulation; containment 0.203 cm combined wall vs 2.7–5.6 kN·m single-blade energies | core backbone | [E3: LPT §4.3.3–4.3.4 pp.128–133] |
| Turbine rear frame | see D11; carries No.5, mixer, centrebody, aft mounts | LPT loads + aft engine weight → aft links | [E3: CR-168219 §5.6] |
| Pressure bulkhead / fire wall | six-sector, at the HPT | pressure boundary, not primary load | [E3: CR-168219 §5.7.4 p.100] |
| Nacelle | composite inlet and aft cowl, slim lines, core-mounted accessories; hinged reverser halves and core cowl panels swing up for access | — | [E3: CR-168219 §5.9 pp.102–105, Fig.40 p.106] |
| Accessory gearbox | core-compartment mounted (chosen over fan-case and pylon: 0 kg vs +34 / +22.7 kg, sfc 0 vs +0.65 / −0.1 %); radial drive of two splined shafts with a midspan bearing from the PTO; pads for lube & scavenge pump, air starter(s), control alternator, VSCF generator, hydraulic pumps, fuel pump & control; max starter torque 1,084.6 N·m; ICLS accessory power 53.69 kW | — | [E3: CR-168219 §5.9.3 p.114, Tables XXIV–XXV pp.115–116, Fig.46 p.117; CR-168211 p.132] |

Mass by module [E3: CR-168219 Table XXVI p.140], kg: fan & booster 1,103
(rotor 481, frame+stators 622) · core 1,001 (HPC rotor 214, stator 235,
combustor/casing/diffuser 137, HPT rotor 283, stator 132) · LPT 837 (rotor
260, stator 257, frame+mixer+centrebody 221, shaft cone 99) · misc 532
(sumps/drives/seals 320, controls & accessories 65, lube hardware 24,
configurations 123) · **basic engine 3,473** · installation 992 (inlet 162,
reverser 379, cowl/pylon/exhaust 181, buildup 270) · **installed 4,465**.

Design life [E3: CR-168219 Table V p.18]: combustor 9,000 h / 18,000 with
repair; HPT blading 9,000 / 18,000; HPT rotating structure 18,000 / 36,000;
remainder 36,000 h or cycles.

---

## E. Materials by component

| Component | Material | Why | Provenance |
|---|---|---|---|
| Fan blade, disc, booster spool and blades, anticlank spring | Ti-6Al-4V | strength/weight, FOD | [E3: CR-165148 Table V p.49] |
| Spinner and cover | 7075 aluminium (composite per CR-168219) | — | [E3: CR-165148 Table V; CR-168219 §5.1.2 p.45] |
| Fan blade retention key, disc-shaft bolts | Inco 718 | — | [E3: CR-165148 Table V] |
| Forward fan shaft | 4340 steel (demonstrator) / MARAGE 250 (FPS intent) | torsion, fatigue | [E3: CR-165148 Table V] |
| Fan frame + OGV | graphite composite, aluminium hub | weight, acoustics | [E3: CR-168219 §5.1.2 p.45] |
| Fan containment | Kevlar over aluminium liner | blade-out | [E3: CR-168219 §5.9 p.102] |
| Island stator / inner OGV | Ti-6-4 / 7075 Al (FPS) | — | [E3: CR-165148 Table VII p.92] |
| HPC rotor blades 1–6 / 7–10 | Ti-8Al-1Mo-1V / Inco 718 (Table X); stress reproduction says the Ti→Ni switch sits at the 4/5 inertia weld | Ti to ~450–500 °C, then creep; Ti-fire | [E3: HPC Table X p.65; derived E1] |
| HPC casings and vanes | nontitanium (Ti-fire prevention); alloy not named in transcribed data | Ti fire | [E3: CR-168219 §5.2.2 p.55] |
| VSV bushings | TFE-glass/polyimide (ZX, Fabroid XV); carbon PBH-20 | wear at 430–700 K | [E3: HPC Table XVIII p.102] |
| Combustor casing, diffuser, support pins | Inco 718 | pressure vessel | [E3: CR-168301 Fig.29 p.54] |
| Support liners | Inco 625 | buckling, 0.02 % yield 275 MPa at 922 K | [E3: CR-168301 §5.4.2.2 p.115] |
| Shingles | X-40 (cobalt); Mar-M-509 for growth | oxidation, thermal fatigue | [E3: CR-168301 Fig.29, Table XIX p.115] |
| Dome, splash plate, dilution eyelets | Hastelloy X | — | same |
| Centrebody | Hastelloy X + zirconate TBC, slotted tip | LCF 100 → 400,000 cycles | [E3: CR-168301 Figs.45–46 pp.76–77] |
| Fuel nozzle | 347 SS stem/body, 321 SS tubes, Hastelloy X tips | — | [E3: CR-168301 Fig.29] |
| Combustor-turbine seal | L605 | — | same |
| HPT stage-1 vane | MA754 ODS airfoils, MAR-M-509 cast bands (CR-167955); **+ TBC (FPS)** | usable >1100 °C uncoated | [E3: CR-167955 §5.1.2 pp.94–95; CR-168219 §3.1 p.10] |
| HPT stage-1 blade | DS René 150 + PVD NiCoCrAlY (CR-167955); **René N4 + TBC (FPS)** | creep at ~1100 °C metal | [E3: CR-167955 §5.1.2 p.90; CR-168219 §3.1 p.10] |
| HPT stage-2 vane | DS René 150 airfoils, René 80 bands (CR-167955); **René N4 + TBC (FPS)** | LCF, rupture | same |
| HPT stage-2 blade | DS René 150, cooled (CR-167955); **DS eutectic, uncooled (FPS)** | eliminates 0.76 % cooling | same |
| HPT discs 1 and 2, forward outer liner | René 95 PM, HIP near-net | tensile/burst to ~650 °C | [E3: CR-167955 Table XVI p.93] |
| Inducer disc, impeller, interstage seal disc, retainers | AF115 PM (first application) | creep 50 °C better than René 95 | same |
| HP shaft, aft shaft/seal disc | Inco 718 → Super Inco 718 (FPS) | LCF 36,000 cycles | same |
| HPT casings | Direct-Age Inco 718 | 10× LCF | [E3: CR-167955 §5.2.2.1 p.154] |
| HPT stage-1 shroud | plasma-sprayed zirconia 6–8 % Y₂O₃ on cast René 77 with pegs, NiCrAlY bond coat < 982 °C, ≥0.102 cm | >1370 °C capability, rub | [E3: CR-167955 §5.2.3 pp.167–176] |
| HPT stage-2 shroud | solid René 77, cobalt spray coat | cost, life | [E3: CR-167955 Table XVI] |
| Nozzle supports, inner seals | René 41; Inco 903A (low expansion) at the CDP/inducer seal | temperature, clearance matching | same |
| Interstage seals | Hastelloy X | — | same |
| ACC manifolds | 321 stainless steel | — | [E3: CR-167955 Fig.52 p.92; LPT §4.4.3] |
| LPT blades 1–5 | cast René 77, tip-shroud hard coat CM64 (1–2) / Triballoy T800 (3–5) | creep at 600–900 °C, fretting | [E3: LPT Table V p.76, §4.2.1 p.97] |
| LPT vane 1 / vanes 2–5 | René 125 / René 77 | HPT-exit hot streak on V1 | [E3: LPT Table V] |
| LPT discs, retainers, bolts | Inco 718; nuts Waspaloy | LCF 72,000 cycles | same |
| LPT casing | Inco 718 | — | same |
| Transition ducts, stage-1 nozzle outer duct | René 80 cast, 18 segments | — | [E3: LPT §4.3.1 p.108] |
| Turbine rear frame | Inco 718 | — | [E3: CR-168219 §5.6 p.95] |
| Mixer / centrebody | Inco 718 / Inco 625 | oxidation | [E3: CR-168219 §5.8 p.102] |
| Pylon (ICLS) | aluminium forward, steel aft of the firewall | mixed exhaust temperature | [E3: CR-168211 p.118] |
| FADEC electronics | alumina/tungsten multilayer boards, Kovar leads, fuel-cooled Al plate | matched expansion | [E3: CR-168219 §5.10.1 p.122, Fig.50] |

---

## F. What this model does not show

Print this with the page.

- **It is the E³, not a GE90.** The NASA/GE Energy Efficient Engine Flight
  Propulsion System (1978–83, NASA CR-168219 and thirteen companion reports,
  all US Government work). Modern engine internals are proprietary and
  export-controlled; this model stays inside the public-domain reports and
  says so.
- **Two axial gaps are not published**: fan stacking axis → HPC IGV, and
  HPC OGV → HPT vane 1 (diffuser + combustor). They are drawn to a stated
  `[schematic]` estimate. The fan-and-booster annulus between the island
  and the HPC is interpolated. No overall engine length is printed.
- **Fan blade sections are designed, not transcribed** — the E³ never
  published them. HPC sections are rebuilt from Table XXII's seven numbers
  per section; HPT airfoils are inferred from throat and aspect ratio; only
  the LPT's 30 sections are transcribed coordinates.
- **Disc profiles are not digitised**; discs are drawn as generic web-and-bore
  shapes at the published rim and bore radii.
- **The final FPS hot-section materials differ from the hardware reports**:
  CR-168219 p.10 replaces René 150 with René N4 single crystal on the HPT
  stage-1 blade and stage-2 vane, adds TBC, and makes the stage-2 blade an
  uncooled DS eutectic. The cooling maps and stresses in this project are the
  hardware-report (René 150) design; the model shows the FPS labels.
- **Anti-icing, fire detection/extinguishing and the airborne vibration
  monitor are `[schematic]`**: the E³ was a ground-test demonstrator with a
  nonflight inlet and nacelle; the reports describe the fire safety wall,
  undercowl fire-detection thermocouples and the No.3-bearing accelerometer,
  and nothing more.
- **The ignition exciter, oil quantities, fuel and oil pressures are not
  printed**; only counts and locations of the igniters and the layout of the
  lube and fuel circuits are.
- **The model turns; it does not run.** Rotation is kinematic at
  LP : HP ≈ 1 : 3.6; nothing on the page is a simulation.
- **Internal blade cooling passages, film-hole patterns, seal teeth and
  bolt patterns are simplified** to what is legible at screen scale; the
  counts in this sheet (holes, bolts, segments) are the real ones.
- **Every number on the page carries its provenance tag.** Where an E³ report
  prints a number two ways and they disagree, this sheet records both and
  the page shows the one the reports' own arithmetic supports.
