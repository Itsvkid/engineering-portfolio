# Data index — what exists, where it is, what has been transcribed

The question this file answers: *for each quantity a gas turbine design
needs, is it published, where, and has it been pulled into
`data/e3-fps-published.yaml` yet?*

Status key — **T** transcribed into the YAML with a `src:` · **L** located
(report, table/figure, page) but not yet transcribed · **D** must be
digitised off a figure, not a table · **—** not published in the E³ reports.

All seven source documents are on disk under `sources/` via
`./fetch-sources.sh`. Report page numbers are the printed ones; add the
front-matter offset (given per report below) to get the PDF page.

| Report | PDF offset | On disk as |
|---|---|---|
| CR-168219 FPS final design | +14 | `e3-fps-final-design-CR-168219.pdf` |
| HPC detail design | +9 | `e3-hp-compressor-detail-design.pdf` |
| HPT hardware CR-167955 | +8 | `e3-hp-turbine-hardware-CR-167955.pdf` |
| LPT hardware | +8 | `e3-lp-turbine-hardware.pdf` |

---

## Architecture and topology

| Quantity | Status | Source |
|---|---|---|
| Gas path order, station numbers | **T** | CR-168219 throughout; `topology` block |
| Spool arrangement (what drives what) | **T** | CR-168219 §5.7.1 p.96 — five-bearing, two-sump; `topology.spools` |
| Stage counts: fan 1 · booster ¼-stage · HPC 10 · HPT 2 · LPT 5 | **T** | CR-168219 §5.1 p.37, §5.2 p.45, §5.4 p.65, §5.5 p.82 |
| Exhaust type: mixed-flow, 18-lobe mixer, single C-D nozzle | **T** | CR-168219 §5.8 pp.101–102 |
| Combustor type: **double-annular** (not cannular) | **T** | CR-168219 §5.3 p.57 |

> **On "cannular".** The E³ is not cannular and neither is any GE engine of
> its generation. It is a short-length **double-annular** combustor — two
> concentric annular domes, pilot outer and main inner, sharing one liner.
> This is the design that became the GE90's DAC. Cannular (can-annular)
> combustors are individual flame tubes inside a common annular casing —
> a 1950s–70s architecture still found on some industrial GTs. Worth having
> the distinction straight before an interview.

## Cycle — compression, expansion, temperature, flow

| Quantity | Status | Source |
|---|---|---|
| OPR, BPR, fan bypass/hub PR, HPC PR, T41, sfc — 3 rating points | **T** | CR-168219 Table XII p.35 |
| Component efficiencies and pressure losses | **T** | CR-168219 Table XI p.34 |
| Cooling flows, chargeable / nonchargeable, 5th and 7th stage | **T** | CR-168219 Table XI p.34; bleed locations §5.2.1 p.52 |
| **HPT cooling design, as designed** — 18.87 % flow budget by component and source; supply system; per-row film and impingement geometry; cavity pressures and backflow margins; pitch-section metal-temperature maps for stage-1 vane (14 nodes), stage-1 blade (43), stage-2 vane (58 at two spans), stage-2 blade (23), shroud (15), casing (22); transients; FOD and tip-cap-loss analyses; rotor-structure and casing fixes — **`data/hpt-cooling.yaml`**, every C/F pair checked | **T** | HPT report §3 pp.17–67, Tables VI–IX, Figs. 9–40 |
| Fan corrected flow, PRs at aero DP and cycle match | **T** | CR-168219 §5.1.1 p.41 |
| Core corrected flow 54.4 kg/s, T25, P25, HPC PR at max climb | **T** | CR-168219 Table XIV p.51 |
| HPT T41, Δh/T, N/√T, corrected flow | **T** | CR-168219 Table XVIII p.70; HPT report Table I p.4 (3 rating points) |
| LPT T49, Δh/T, N/√T, corrected flow, loading | **T** | CR-168219 Table XXI p.86; LPT report Table I p.5 (3 rating points) |
| Takeoff thrust | **T** | CR-168219 §4.3 p.32 |
| Mixer effectiveness, ΔP/P, sfc gain | **T** | CR-168219 Table XXIII p.104 |
| Fan duct Mach 0.40–0.45 | **T** | CR-168219 §5.8 p.101 |

## Blade speed and spool speed

| Quantity | Status | Source |
|---|---|---|
| Fan corrected tip speed 411.5 m/s; tip rel. Mach 1.4 | **T** | CR-168219 §5.1.1 pp.41, 43 |
| HPC corrected tip speed 456 m/s | **T** | CR-168219 §5.2.1 p.48 |
| **HP spool rpm** — 12,303 (100 % XNHR), 12,645 (XNH, max climb), 13,948 (deteriorated) | **T** | HPC report Table X footnotes p.65 |
| HPT tip speed at takeoff, stage 1 / 2: 513.9 / 535.2 m/s | **T** | HPT report Table III p.10 |
| LP spool rpm | **derived** | from LPT N/√T × √T49 — see `tests/test_published_data.py` |

## Blade counts per stage

| Row | Count | Status | Source |
|---|---|---|---|
| Fan blades | 32 | **T** | CR-168219 §5.1.2 p.45; Fig. 13 p.38 |
| Fan OGV | 34 | **T** | Fig. 13 p.38 annotation |
| Booster stage-1 vane / booster blade | 60 / 56 | **T** (assignment inferred from figure position) | Fig. 13 p.38 |
| Inner OGV (core duct) | 64 | **T** | CR-168219 §5.1.1 p.43 |
| HPC rotors 1–10 | 28 38 50 60 70 80 82 84 86 94 | **T** | HPC report Table X p.65 |
| HPC IGV, stators 1–10 | 32 · 50 68 82 92 110 120 112 104 118 140 | **T** | HPC report Table XXII pp.157–159 |
| HPT vanes 1 / 2 | 46 / 48 | **T** | HPT report Table III p.10, Table IV p.12 |
| HPT blades 1 / 2 | 76 / 70 | **T** | same |
| LPT vanes and blades 1–5 | — | **L** | LPT report §4.2.1 pp.82–101, Fig. 52 p.83 |
| Combustor swirl cups / fuel nozzles | 60 / 30 | **T** | CR-168219 §5.3.2 p.61 |

## Blade geometry — angles, chord, airfoil shape

| Quantity | Status | Source |
|---|---|---|
| **HPC rotors 1–10: per-stage summary** — airfoil length, root/tip radius (LE and stacking axis), orientation angle, camber, chord, aspect ratio, radius ratio, tm/c, te/c, solidity, tilt, pretwist, airfoil family, weight, material, metal temperature, root stress | **T** | HPC report Table X pp.65–66 |
| **HPC rotors 1–10 and IGV + stators 1–10: section-by-section** — 12 spanwise sections per row with radius, chord, camber, stagger, β1*, β2*, tm/c, %c of max thickness, te/c (IGV: stagger and CL0) — **252 sections, `data/hpc-blade-sections.yaml`**, every row checked camber = β1*−β2* and cm = in × 2.54, ends checked against Table X | **T** | HPC report Table XXII pp.154–159 |
| **HPC through-flow, every row** — inlet and exit on 12 streamlines: radius, z, PT/PT1, TT/TT1, Mach (abs and rel), U, Cz, flow angle, slope; blade-element solidity, DF, loss, cumulative efficiency, incidence, deviation; original-design chord — **21 rows, 756 station lines, `data/hpc-vector-diagrams.yaml`**. Checked: R-BAR = XXII radii; U/r = one ω = 12,303 rpm; PT/TT chain along the gas path; σ = cN/2πr; DF recomputed. Both bleed ports visible in the data; rotor 9 and 10 re-bladed between original and final | **T** | HPC report Table XXI pp.112–132 (SI) |
| Fan blade airfoil sections | **—** in tables; described only | CR-168219 §5.1.1 p.43: transonic sections on 12 streamsurfaces, GE Streamsurface program |
| Inner OGV: sweep 60°, lean 0°→20° hub | **T** | CR-168219 §5.1.1 p.43, Fig. 17 p.44 |
| HPT blading aero geometry — solidity, Zweifel, TE blockage, aspect ratio, unguided turn, 4 rows | **T** | HPT report Table IV p.12 |
| HPT stage parameters — PR, loading, reaction, exit Mach, swirl, radius ratio, tip clearance | **T** | HPT report Table III p.10 |
| HPT airfoil shapes at hub/pitch/tip, all 4 rows, with surface velocity | **D** | HPT report Fig. 6 p.14 — 0.508 cm grid, digitisable |
| HPT flow angles, Mach, energy extraction vs. span | **D** | HPT report Fig. 5 p.13 |
| LPT vane and blade shapes per stage, Block II | **D** | LPT report Figs. 9–18 pp.18–27 |
| LPT vector diagrams | **L** | LPT report §2.6 p.13 |

## Flowpath radii and axial stations

| Region | Status | Source |
|---|---|---|
| **HPT** — hub and tip radius at every row LE/TE, axial length 20 cm | **T** | HPT report Fig. 3 p.9 — dimensioned, not just drawn |
| **HPC** — root and tip radius per stage at LE and stacking axis | **T** | HPC report Table X p.65 |
| HPC flowpath drawing | **D** | HPC report Fig. 15 p.27 (CAFD flowpath); CR-168219 Fig. 18 p.47 |
| Fan and booster | **D** | CR-168219 Fig. 13 p.38 — scale from 2.11 m tip diameter |
| Fan inlet radius ratio 0.342; specific flow 208.9 kg/s·m² | **T** | CR-168219 §5.1.1 p.41 |
| Combustor | **D** | CR-168219 Fig. 22 p.59 |
| LPT — 25° outer wall slope, 7.62 cm transition duct | **T** / **D** | CR-168219 §5.5 p.82; Fig. 32 p.83; LPT report Fig. 6 p.12 |
| HPT stage exit annulus areas | **T** | HPT report Fig. 1 p.7 (design points ≈ 0.0895 / 0.151 m²) |
| Whole engine | **D** | CR-168219 Fig. 1 p.4 |
| Nacelle GA, inlet, exhaust | **D** | CR-168219 Fig. 40 p.106 |

## Discs, shafts, bearings, structure

| Quantity | Status | Source |
|---|---|---|
| **Bearing arrangement** — 5 bearings, 2 sumps, which shaft each supports, thrust vs. roller, intershaft No. 4 | **T** | CR-168219 §5.7.1–5.7.3 pp.96–99; Figs. 37, 38 |
| PTO gearbox location and drive | **T** | CR-168219 §5.7.2 p.96 |
| Sump sealing and venting | **T** | CR-168219 §5.7.2–5.7.3 pp.96–98 |
| HPC rotor construction — inertia-welded, single bolt joint, bore-cooled | **T** | CR-168219 §5.2.2 p.52 |
| HPT rotor components — forward HP shaft, inducer disk, stage 1 and 2 disks, interstage seal disk, aft shaft/seal disk, retainers, bolts — stress, concentration, LCF | **L** | HPT report §5.2.1 pp.105–149 |
| HPT disk finite-element models and stress/life | **L** | HPT report Figs. 61–72 pp.111–124 |
| LPT rotor — blades, dovetails, disks, seals | **L** | LPT report §4.2 pp.82–108 |
| LPT — bolted disc flanges, single bearing cone, tip shrouds | **T** | CR-168219 §5.5 p.82 |
| Blade tip and interstage seal clearances | **L** | CR-168219 Figs. 29–31 pp.77–79; HPT report Figs. 44–46 pp.74–76 |
| HPC clearances and casing bolting | **L** | HPC report Table XVI p.96, Table XVII p.102, Figs. 61–62 |
| Materials — combustor, fan, compressor rotor by stage | **T** | CR-168219 §5.3 p.57, §5.1.2 p.45; HPC Table X |
| Materials — HPT rotor and static | **L** | HPT report Figs. 51–52 pp.91–92 |
| **Module masses** | **T** | CR-168219 Table XXVI p.140 |
| HPT assembly weight | **L** | HPT report §5.4 p.179 |

## Combustor sizing

| Quantity | Status | Source |
|---|---|---|
| Type, zones, staging, prediffuser split 48/52 | **T** | CR-168219 §5.3.1 p.57 |
| 60 swirl cups, 30 dual-tip nozzles, 30 support pins | **T** | §5.3.2 p.61 |
| Liner construction — double-wall, 3 shingle rows, impingement + film | **T** | §5.3.2 pp.61–62 |
| Materials and TBC | **T** | §5.3 p.57 |
| Pressure drop 5.0 %, set by HPT vane cooling circuit | **T** | Table XI p.34; §5.3.3 p.62 |
| Geometry — dome height, liner length, annulus radii | **D** | Fig. 22 p.59 |
| Emissions goals and results | **L** | Tables XVI, XVII pp.63–64 |

## Intake and exhaust sizing

| Quantity | Status | Source |
|---|---|---|
| Fan tip diameter 2.11 m; inlet radius ratio 0.342 → hub 0.361 m | **T** | CR-168219 §4.3 p.32, §5.1.1 p.41 |
| Fan face specific flow → capture area | **T** | §5.1.1 p.41 |
| Exhaust — full-length duct, 18-lobe mixer, C-D nozzle, low area ratio | **T** | §5.8 pp.101–102 |
| Nozzle dimensions | **D** | Fig. 1 p.4, Fig. 39 p.103, Fig. 40 p.106 |
| Nozzle coefficient 0.996; nozzle duct loss 0.21 % | **T** | Table XI p.34 |

---

## What is genuinely not in the reports

Be straight about this in the write-up:

- **Fan blade section coordinates.** Described (transonic, 12 streamsurfaces,
  proprietary GE program) but not tabulated. Generate from the published
  radius ratio, tip speed, and pressure ratios using PF-06's free-vortex
  machinery, and say so.
- **Full 3-D airfoil coordinate files.** Table X names GE "coordinate tape
  numbers" per stage — those tapes are not public. Table XXII gives enough
  per section (chord, camber, stagger, β angles, thickness distribution
  parameters) to *reconstruct* a section from a camber line and a thickness
  law, which is exactly what `projects/01-airfoil-analysis/src/geometry.py`
  already does one dimension down.
- **Disc profiles as coordinates.** Cross-sections only; digitise.

## The highest-value transcription still to do

In order of what it unlocks:

1. **HPC Table XXII** (5 pages) — section-by-section rotor geometry. Turns
   "blades with free-vortex twist" into "blades with *NASA's* twist".
2. **HPC Table XXI** stator rows — completes the compressor.
3. **HPT Fig. 6** — digitise the four airfoil shapes at three spans.
4. **LPT blade counts** — the one row of the blade-count table still empty.
5. **Fan/booster Fig. 13** — the only flowpath region with no dimensioned
   drawing anywhere.
