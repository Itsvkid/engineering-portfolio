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
| LPT hardware | +13 | `e3-lp-turbine-hardware.pdf` |
| Fan hardware CR-165148 | +10 | `e3-fan-hardware-design-CR-165148.pdf` |
| Combustor CR-168301 | +15 (design sections); +37 in the test section from about p.380 (plates) | `e3-combustor-hardware-design.pdf` |
| ICLS CR-168211 | +25 | `e3-icls-design-and-performance-CR-168211.pdf` |
| HPT cooling model CR-165374 (P&W) | +5 | `e3-hp-turbine-cooling-model.pdf` |

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
| **Cycle solved** — `solvers/e3cycle/`: the three Table XII ratings from Table XI's components and the four secondary-air streams, real gas. What the reports do not print and the solver gives: the booster-to-HPC transition loss the printed OPR implies, 2.22 / 1.84 / 1.41 % (climb / cruise / takeoff); takeoff fan corrected flow 580 kg/s at 173.5 kN; T3 796 / 784 / 877 K; combustor exit 1573 / 1540 / 1695 K behind T41 1517 / 1485 / 1638; HPT PR 4.99 / 5.00 / 4.98; LPT PR 4.55 / 4.45 / 4.12; T5 749 / 734 / 840 K; core at 0.95–0.96 of bypass pressure at the mixing plane. sfc +0.46 / +0.56 / +1.91 % against Table XII | **D** | derived; B1–B3, `tests/test_e3cycle.py`, findings in `solvers/e3cycle/STEP0.md` |

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
| LPT blades 1–5 | 120 122 122 156 110 | **T** | LPT report Fig. 52 p.83; §4.1.2 p.78 |
| LPT vanes 1–5 | 72 102 96 114 120 | **T** | LPT report Fig. 6 p.12; §4.2.1 p.84 |
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
| LPT vane and blade shapes per stage, Block II — peak Mach and axial extents transcribed; coordinates in the appendix | **T/D** | LPT report Figs. 9–18 pp.18–27 |
| **LPT final vector diagrams (Table II: Δh, PR, loading, φ, reaction, angles, Mach at hub/pitch/tip × 5 stages); blading solidity, Zweifel, TE blockage, aspect ratios (Table III, 10 rows); transition-duct Mach and separation; Block I lessons and Block II rig results (92.0 % five-stage, 91.4 % status)** — `data/lpt-aero.yaml` | **T** | LPT report §2.4–2.8, Tables II–III, Figs. 2–19, pp.6–29 |
| **HPT active clearance control — Table X payoff (1.533 % η, −1.22 % sfc), Figs 44–47 transients and capability, Tables XI–XII short-start pinch, Table XIII out-of-round, Table XIV blade-tip/shroud clearance bookkeeping, casing rings, manifold** — `data/hpt-clearance.yaml` | **T** | CR-167955 §4, pp.68–85 |
| **ICLS as tested (CR-168211): 64 h 50 min to 15 June 1983; SLS sfc 0.0332 kg/h·N as tested, 0.0327 with test faults corrected, 0.0316 fully corrected; takeoff thrust 2.5 % over design; max-cruise projection 0.0561 uninstalled = 12.1 % better than CF6-50C, 13.2 % installed against a 12 % objective; Table XII sfc stack-up (six items summing to the 2.5 %); component efficiencies (fan 0.886 / 0.901, HPC 0.856, HPT 0.925, LPT −0.7 vs goal and 1–1.5 below rig, unexplained); EPR, BPR, core-speed, sfc, pumping and compressor curves read off** — `data/icls-tested.yaml` | **T** (measured) | CR-168211 pp.1–8, 240–247, 279–286, 620–623 |
| **Combustor (CR-168301): goals (Tables I–III), requirements (Table IV), radial profile (Fig 5), cycle comparison (Table V), Fig 8 airflow distribution (24 labels summing to 100.0 % Wc), diffuser, fuel nozzle and staging, swirl cup (Fig 21), starting studies (Tables VI–X, Figs 12–16), emissions (Tables XI–XIII, Figs 17–20), mechanical requirements (Table XV), materials (Figs 29–30), shingle liner (Table XVI, Figs 33–35), casing and support pins (Figs 37–40), dome, centrebody, fuel delivery, heat transfer (Tables XVII–XVIII, Figs 56–63), fuel-nozzle thermal (Fig 64), mission mix (Fig 65), shingle stress and life (Figs 67–71, Table XIX), support-liner buckling (Figs 72–76), casing (Fig 77), centrebody life (Fig 78), nozzle vibration (Fig 82, Table XX), development-test summaries (Tables LVII–LXII, Mod VI EGT)** — `data/combustor-design.yaml` | **T** | CR-168301 pp.1–129, 388–393, 410–415 |
| HP turbine cooling model report (NASA CR-165374) — **Pratt & Whitney's** E³ HPT blade cooling-passage flow-visualisation tests, not GE's engine; reviewed, kept as design-practice reference only | ref | CR-165374, 31 pp. |
| **Fan and booster (CR-165148): Tables I–II requirements at three ratings (FPS and growth), Fig 2 flowpath labels, Table III cycle points, Table IV aero parameters, Table V materials, Appendix A per-row summaries (flows, PR, TR, η, counts) — the island flow split closes to 0.1 kg/s and every row's η recomputes from PR and TR; fan rotor airfoil design (throat margins, shroud, Fig 15 chord/solidity, Fig 16 tm/c), stator 1, booster and inner-OGV airfoils, bypass vane-frame; fan blade mechanical (Figs 41–51: stresses, untwist, Campbell 14.6 % over 2/rev, shroud, dovetail/post, Goodman, bird strike, retention), booster blade (Figs 52–57), rotor structure (Figs 58–61), Table VI weight 496.2 kg** — `data/fan-design.yaml` | **T** | CR-165148 pp.1–74, 118–127 |
| **HPC mechanical and 10A rig: stator aeromechanical response (Table XV), clearance elements (Table XVI), casing temperatures analysis vs test (Fig 59), rig bleeds (Fig 60), FPS and rig clearances per stage (Figs 61–62), casing bolting (Table XVII: 60/32/28 × 3/8 in), VSV bushing materials and temperatures (Table XVIII) and endurance (Table XIX), vane 9–10 Campbells (Figs 55–56)** — `data/hpc-mechanical.yaml` | **T** | HPC report §3, pp.92–103 |
| **HPC stagewise design (Figs 10–20): aspect ratio, pitch solidity, meridional Mach, stator exit swirl at tip/pitch/hub, stage temperature rise (493.5 °C total, stage 6 unloaded by design), pitch loss and diffusion factor, inlet Mach extremes; stator-6 radial swirl (Fig 16) and stage-5 radial DF (Fig 19); CAFD design inputs — 25:1 design point, η 0.847, blockage 0.97→0.90, bleed sizing, hub tilt, transonic throat margin** — `data/hpc-stagewise.yaml`; every curve checked against Table XXI's streamlines and Table X | **T** | HPC report §2.2–2.3.1, pp.20–39 |
| **HPT ceramic shrouds (Figs 106–109: zirconia/Y₂O₃ on René 77, 0.102 cm minimum, bond coat < 982 °C), maintainability modules, Table XXIII FPS turbine weight (414 kg: rotor 282, stator 132)** — `data/hpt-mechanical.yaml`. **CR-167955 is now fully transcribed** across `hpt-cooling.yaml` (§3), `hpt-clearance.yaml` (§4), `hpt-mechanical.yaml` (§5) and the published file (§1–2) | **T** | CR-167955 §5.2.3–5.4, pp.167–186 |
| **HPT blades and stator — stage-1 blade transient LCF (Figs 77–79, 414 MPa range, 26,000 cycles), Campbell (Fig 80: 46/23/48/24/30/72 per rev), platform damper, dovetail (Fig 81); stage-2 blade mission (Table XXI), rupture map (Fig 84), Campbell (Fig 85), damper, three-tang dovetail (Fig 87); rotor dynamics (Table XXII, Fig 88); bolts (Figs 89–91); casing LCF map (Fig 93), nozzle support (Fig 94), inducer seal (Figs 95–96), stage-1 nozzle (Figs 97–101), stage-2 nozzle (Figs 102–105)** — `data/hpt-mechanical.yaml` | **T** | CR-167955 §5.2.1.9–5.2.2, pp.130–170 |
| **HPT mechanical — configuration (Fig 50), Table XV lives, materials (Figs 51–52, Table XVI), Table XVII methods, Table XVIII flight times, Fig 54 rotor temperatures (17 locations × 3 times), Fig 55 CLASS/MASS stresses (19 × 3), forward shaft, inducer disk, impeller (Fig 60), stage-1 disk (Figs 61–64), interstage seal disk (Fig 65), retainers (Figs 66–68), stage-2 disk (Figs 69–71), aft shaft (Fig 72), stage-1 blade mission (Tables XIX–XX, Fig 74)** — `data/hpt-mechanical.yaml` | **T** | CR-167955 §5.1–5.2.1.9, pp.86–130 |
| **LPT clearances and weights: out-of-round stage 1 (Table XVIII, 3 conditions × 4 clock positions), combined clearance (Table XIX), summary (Table XX: 0.010 cm new, goal 0.038), Fig 92 relative diameters, manifold tube sizes; Table XXI weights (rotor 254.4, stator 250.4, total 504.8 kg)** — `data/lpt-design.yaml` | **T** | LPT report §4.4.4–4.5, pp.136–142 |
| **Flowpaths derived from the tables** — `data/lpt-flowpath.csv` (hub/tip at every row's LE and TE from the airfoil sections, z from the HPT exit plane), `data/hpc-flowpath.csv` (Table XXI streamlines 1 and 12 at every row's inlet and exit), both rebuilt by `tools/build_flowpaths.py`; `data/engine-flowpath.yaml` maps every component's datum, its radii and the two stitching offsets no source gives | **D→T** | derived; A3 |
| **LPT airfoil coordinates** — all ten rows at 10/50/90 % span, suction and pressure surfaces, 48 points each, (Z, R, Rθ) in inches: 30 sections, 2,879 triples in `data/lpt-airfoils/*.csv` (one illegible row omitted and noted; one ambiguous digit noted). Every section checked by `tools/lpt_airfoil_check.py` (monotonic Z after the nose, one-way R, quadratic smoothness of R and Rθ in Z, shared leading edge, closing trailing edge) and by `tests/test_lpt_airfoils.py` against Fig 52's chords, Table VII's radii, gas-path order and stagger sense | **T** | LPT report appendix pp.144–173 |
| **LPT mean-line at pitch** — `solvers/meanline/lpt.py`, `figures/lpt-vector-diagrams.png`: five stages from the max-climb state at 3,539 rpm, Δh and α₂ from Table II, radii from the sections; Mach numbers, exit angles and loading on Table II, 28 of 50 quantities in band. Findings: Table II's stator-exit column is at the stator TE (annulus 5–10 % under the rotor LE); its φ and reaction columns are not the kinematics of its own angles (1.43 / 0.52 vs 1.25 / 0.305 on stage 1); its stage PRs multiply to the pre-rematch 4.21, not the final 4.55; β₂ 3–7° low on every stage | **D** | derived; C1 unit 1, `tests/test_lpt_meanline.py` |
| **Ainley–Mathieson loss method, digitised** — `data/methods/ainley-mathieson-rm2974.yaml`: Figs 4–9 of R&M 2974 read at 300 dpi with stated uncertainties, equations 1–6, and the report's worked example (row coefficients, incidence table, Fig 15 stage characteristic) as the validation case; `solvers/meanline/losses.py` reproduces the example to its chart-read bands. Applied to the E³ LPT (`lpt_losses.py`, `figures/lpt-losses.png`): 0.837 as printed, 0.869 with a Dunham–Came c/h term (labelled assumption), against 0.917 — the 1951 method's missing aspect-ratio term and profile-loss level, recorded | **T** / **D** | R&M 2974 pp.1–19, 24–30; C1 unit 2, `tests/test_ainley_mathieson.py`, `tests/test_lpt_losses.py` |
| **SP-290 boundary-layer end-wall method** — `data/methods/sp290-boundary-layer-losses.yaml`: chapter 7's equations 7-45 to 7-47 (end-wall loss as an area ratio, 1 + (s/h)·cos stagger), the Reynolds rule of R&M 2974 §8 ((1−η) ∝ Re^−1/5 at a 2×10⁵ basis, Re the mean of first vane and last rotor) and R&M 2974's own stated accuracy (±2 % efficiency, ±15 % on the loss rules). **This route closes the E³ LPT: 0.911 against a published 0.917** where the pure 1951 correlation gave 0.837 | **T** / **D** | SP-290 pp.193–223; R&M 2974 §8–9; C1 unit 2b |
| **HPT efficiency audit, Table V** — `e3-fps-published.yaml` `hpt.efficiency_estimate`: a tight-clearance uncooled base of 92.65 % and seven corrections (loading +0.27, aspect ratio −1.04, tip clearance −1.50, overlap +0.30, edge blockage +0.37, aerodynamics +0.20, **cooling +0.30**) summing exactly to the printed 91.55 %, plus the efficiency chronology (ICLS goal 91.9, FPS goal 92.4, warm-air rig 92.5, Table XI 92.7, ICLS as tested 92.5). The mean-line model reaches 92.1 % and prices the clearance debit at 0.95 point against the printed 1.50 | **T** | HPT report CR-167955 Table V p.13, §2.3.2; C1 unit 3, `tests/test_hpt_meanline.py` |
| **SP-36 compressor correlations** — `data/methods/sp36-compressor-correlations.yaml`: Carter's deviation rule (eq 270) with Fig 160's m-factor digitised for both circular- and parabolic-arc meanlines, the diffusion-factor definition and its 0.62 separation limit, and the loss-parameter form. Checked against Table XXI's 240 printed deviations: mean bias −0.39°, rms 2.58°, with a structural pattern by row type (C1 unit 4) | **T** / **D** | SP-36 pp.204–211; `tests/test_compressor_deviation.py` |
| **HPC efficiency, rolled up two ways** — `solvers/meanline/compressor.py --4b`: real-gas adiabatic efficiency per streamline from Table XXI's printed ratios (reproduces its own `cum_eff` column to <0.01, area-weights to **0.8455 against the 0.847 design intent**), and the same pressure ratio rebuilt from the printed element loss coefficients alone through 21 rows with rothalpy (+0.03 % mean, rms 0.72 %), which also rebuilds the temperature ratio independently. Span-wise efficiency 0.778 hub / 0.869 mid / 0.811 tip at a nearly uniform pressure ratio | **D** | derived; C1 unit 4b, `tests/test_compressor_rollup.py` |
| **HPC stagewise, recomputed from the through-flow** — `solvers/meanline/compressor.py --unit5`: diffusion factor, loss coefficient and solidity per stage from Table XXI against the read-offs of Figs 18, 17 and 11 (≤0.004, ≤0.0008, ≤0.03 — two independent Stage-A transcriptions agreeing); Fig 14's average temperature rise confirmed as the **span average**, area-weighted 492.6 K vs a printed 493.5 while the pitch line reads 477.3; de Haller added (rotors 0.668–0.723, stators 0.616–0.734), which the report never plots | **D** | derived; C1 unit 5, `tests/test_hpc_stagewise_meanline.py` |
| **Fan and booster mean-line** — `solvers/meanline/fan.py`: axial Mach 0.630 from the specific flow, tip relative Mach **1.405 against a printed 1.41**, shroud and hub sections at −0.064 / +0.063 (the radial-equilibrium signature); both tip speeds implying 3727.7 corrected rpm to half an rpm; the island split closing to 0.00 kg/s at 22.3 % under and 42.7 % returned, BPR 6.813 vs 6.8; loading ψ 0.67 fan / 0.25 booster | **D** | derived; C1 unit 6, `tests/test_fan_meanline.py` |
| **Stage counts derived** — `solvers/meanline/stage_counts.py`: from Stage B's work, the two shaft speeds and the flowpath radii, with generic loading limits (never E³ values), the HPC's 10 stages, the HPT's 2 and the booster's 1 fall out exactly, and the single-stage HPT that CR-167955 Table II evaluated and rejected is rejected again (ψ 1.38 vs 0.85). The fan (1 where the limit asks 2, ψ 0.74) and the LPT (5 where loading asks 4, ψ 1.25) are the two informative misses | **D** | derived; C1 unit 7, `tests/test_stage_counts.py` |
| **Radial equilibrium audit of Table XXI** — `solvers/throughflow/radial_equilibrium.py`: the printed through-flow satisfies simple radial equilibrium to 0.243 of its largest term over 400 interior points, and to **0.172** once the streamline-curvature term is restored (36 of 40 stations improve). The printed φ column reproduces atan(dr/dz) from the table's own z and r to **0.23°** over 480 points — two separately transcribed columns describing one set of streamlines | **D** | derived; C2 unit 8, `tests/test_radial_equilibrium.py` |
| **Spanwise distributions predicted** — `solvers/throughflow/predict.py`: radial equilibrium integrated for c_z from the vortex law, work and loss, with continuity setting the level; Mach and flow angle are outputs. **Stator-10 exit: swirl rms 0.02°, Mach rms 0.002** against the plan's ±2° / ±0.02. All 42 stations predicted — rear half inside 0.2°, transonic front rows up to 5.2° | **D** | derived; C2 unit 9, `tests/test_throughflow_predict.py` |
| **Vortex law, LPT and HPC** — `solvers/throughflow/lpt_vortex.py`: c_θ ∝ r^n fitted across the span. The LPT's "controlled vortex" (LPT report §2.6, no number published) is **n = −0.31 → −0.69, mean −0.51**, against −1.00 for a free vortex, drifting toward free vortex rearward as the radius ratio opens 0.76 → 0.61. The HPC's nine swirling stators give +0.54 to −0.76 with no order — a swirl schedule, not a vortex law; the OGV is degenerate at 2.4° mean swirl | **D** | derived; C2 unit 10, `tests/test_lpt_vortex.py` |
| **HPT spanwise energy extraction** — `data/hpt-fig5.yaml`, extracted from CR-167955 Fig 5c at 300 dpi by `tools/read_hpt_fig5.py` (numerically, not by eye; the page carries NASA's own poor-quality stamp), ±5 kJ/kg, with the stage-2 axis gridline inconsistency recorded `as_printed`. Area-weights to the report's **own** pre-rematch design point: stage 1 +0.4 %, stage 2 +4.5 %, split 0.555 vs 0.565. Neither free vortex (uniform) nor solid body (monotonic) — peaks at 50–55 % and unloads both end walls | **T** / **D** | CR-167955 Fig 5c p.13; C2 unit 11, `tests/test_hpt_spanwise.py` |
| **HPC sections reconstructed, and their throats** — `solvers/blading/sections.py`: a double-circular-arc camber line whose join is solved to reproduce β₁*, β₂* and the printed stagger, plus the quarter-sine thickness CR-165148 documents. Outputs: max camber at **49 % of chord on stators, 55 % on rotors**; and a **throat margin of 4.0 % on the transonic rotors against a stated 6 %**, rising 2.2 % → 28.0 % from rotor 1 to rotor 10. The IGV does not fit the family (98–100 %, recorded as a limit of the method) | **D** | derived; C3 unit 12, `tests/test_hpc_blade_sections_geometry.py` |
| **LPT throats and Zweifel from the coordinates** — `solvers/blading/lpt_sections.py`: throat-to-pitch 0.413–0.647 from the 30 transcribed sections; **R&M 2974's outlet-angle rule reproduces Table II's exit angles to 1.4° rms** (bias −0.71° from Fig 5 alone, +0.27° with equation (1)'s −4(s/e), *e* fitted to the suction surface); s/e 0.141–0.386 against 0.279/0.355 in R&M's worked example; **Zweifel to 0.083 rms** of Table III at pitch | **D** | derived; C3 unit 13, `tests/test_lpt_blade_sections_geometry.py` |
| **HPT throats from the aspect ratio** — `solvers/blading/hpt_sections.py`: Table IV's h/d₀ with Fig 3's annulus heights gives throats 1.12–1.55 cm and o/s 0.257–0.488 with no coordinates at all; R&M 2974's Fig 5 then gives outlet angles within **1.8° rms** of the independent unit-3 mean-line, with the same −1.7° bias the LPT showed before its −4(s/e) term was added. Zweifel matches Table IV on three of four rows to 0.03 | **D** | derived; C3 unit 14, `tests/test_hpt_blade_sections_geometry.py` |
| **LPT stator and casing: inner seal supports (Figs 78–79); stages 2–5 nozzles — segments (Fig 80: 18/17/16/19/20), airfoil loads and margins (Fig 81), stage-2 hooks (Fig 82), tangential load stops (Table XVII); casing construction, bolts (132/120), end-flange stresses (Fig 87), containment (Fig 88); ACC manifold (§4.4.3)** — `data/lpt-design.yaml` | **T** | LPT report §4.3.1–4.4.3, pp.120–135 |
| **LPT rotor structure: Table X blade LCF; Table XI flutter; tip shrouds (Figs 64–66); angel wings; retainers (Figs 68–69); stage-1 dovetail stress map (Fig 70) and Table XII life; disks — spacer arms (Fig 71), stage-1 disk stress and temperature (Fig 72), Table XIII bolts, Table XIV bolt selection, Table XV disk LCF; stator stage-1 nozzle assembly, Table XVI airfoil, hooks (Fig 77), support (Fig 75)** — `data/lpt-design.yaml` | **T** | LPT report §4.2.1–4.3.1, pp.96–119 |
| **LPT blades: chords, lengths, aspect ratios, edge diameters; takeoff stresses per stage (CF, LE resultant, gas bending); rupture mission (7 points, 18,000 h); rupture and HCF results; stage-1 Campbell; materials; life basis; design cycle points and speeds; ACC payoff; start-transient temperatures** — `data/lpt-design.yaml` | **T** | LPT report §3.10, §4.1–4.2.1, Tables V–IX, Figs. 47–62, pp.72–95 |
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
| **Annulus by continuity at max climb** — `solvers/e3cycle/stations.py`, `figures/annulus.png`: HPT stage exits −3.6 / +0.2 % against Fig 3; HPC −5.5 / −10.2 % geometric, −2.5 / −0.2 % with Table XXI's blockage 0.97 / 0.90; LPT stage exits at pitch Mach a uniform 3.4–5.5 % under the sections (an unprinted 4–5 % blockage); vane-1 LE Mach 0.32 by continuity against Fig 7's 0.40; fan-face Mach 0.63. Turbine cycle-match tables by two routes: HPT W41√T/P +0.8 %, Δh/T +0.7 %; T49 +0.25 %; LPT W49√T/P −0.5 %, Δh/T +2.8 % | **D** | derived; B4, `tests/test_e3stations.py`, findings in `solvers/e3cycle/STEP0.md` |

## Discs, shafts, bearings, structure

| Quantity | Status | Source |
|---|---|---|
| **Bearing arrangement** — 5 bearings, 2 sumps, which shaft each supports, thrust vs. roller, intershaft No. 4 | **T** | CR-168219 §5.7.1–5.7.3 pp.96–99; Figs. 37, 38 |
| **Turbine (rear) frame** — 12 radial struts, Inco 718 polygonal casing, spring rate 1.75×10⁶ N/cm bearing-to-strut-plane, No.5 bearing housing/mixer/centerbody support, 3 mount lugs; **struts explicitly cambered to remove residual LPT exit swirl** (Fig.36 caption) | **T** | CR-168219 §5.6 pp.90–95; Figs. 34–36; `data/e3-fps-published.yaml` `turbine_rear_frame` |
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
| **Preliminary (Task III) mixer design, one program phase before the FPS's 18-lobe geometry** — 24 lobes sized against an empirical PL/D_h² = 7.3 correlation (perimeter × mixing length / hydraulic diameter², from GE scale/full-scale data plus T.H. Frost's published correlation) for a 65 % effectiveness target; mixing-plane Mach 0.56 in a 0.50–0.60 design band; Table 68 pressure-loss breakdown gives mixer-chute friction+pressure as two explicit line items (0.11 % fan duct, 0.47 % core duct) kept separate from a thermodynamic-mixing loss GE computed independently in the cycle deck via a momentum/energy/continuity balance — `exhaust.mixer_preliminary_design_task3` | **T** | CR-135444 pp.246–249, "f. Mixer Design" / "g. Pressure Losses" / Table 68 |

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
