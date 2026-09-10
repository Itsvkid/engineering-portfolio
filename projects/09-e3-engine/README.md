# 09 — The Energy Efficient Engine, rebuilt from its design reports

A complete twin-spool turbofan — nacelle, fan, booster, compressor,
combustor, both turbines, shafts, sumps, bearings and casings — designed
discipline by discipline to the fidelity the published data can check, then
assembled and sectioned as a rotating cutaway. **Every number is traceable
to a public-domain NASA report; every analysis method is validated on a NASA
test case before it touches the engine; every result is compared with what
NASA measured, and the gap is published.**

<!-- BEGIN GENERATED: tools/build_readme.py -->

**Status:** nine of ten stages built. **1020 test functions**, **194 numbered findings**, **41 closures** — 25 met, 12 half, 4 gated. Stage H needs a human at a CAD GUI; Stage J is in progress.

| Stage | | State |
|---|---|---|
| **A** | sources and transcription — data/*.yaml, every value with a src: | transcribed; four figure gaps remain |
| **B** | cycle — three Table XII ratings, the mixer, the station table | 1 met, 2 half |
| **C** | aero — mean-line, through-flow, blading, CFD validation | 7 met, **1 gated** |
| **D** | thermal — cooling, secondary air, clearance, combustor | 1 met, 1 half, **1 gated** |
| **E** | mechanical — blade and disc stress, frequencies, rotordynamics, attachments | 3 met, 6 half |
| **F** | materials and mass — allowables, the module roll-up | 1 half, **1 gated** |
| **G** | geometry — 32 blade rows lofted to STEP | 1 met, 2 half |
| **H** | assembly — hand CAD -- needs a human at the GUI | **not started** — needs a human at the GUI |
| **I** | verification — cross-discipline consistency, sensitivity, FINDINGS.md | 3 met |
| **J** | publication — meridional plot, Campbell match, glTF | 9 met |

### Validation

Every solver states its tolerance in a `STEP0.md` **before** the run, and the tolerance is never edited afterwards. `data/closures.yaml` holds all of them with today's number, so the scoreboard below is read from the code rather than remembered.

| Closure | Achieved vs band | |
|---|---|---|
| **B1** — the mixer reproduces Table XXIII's sfc improvement | — | half |
| **B3** — sfc at three ratings against Table XII | 1.91 vs 1.5 percent | half |
| **B4** — annulus by continuity at every dimensioned HPT station | — | met |
| **C1** — LPT mean-line efficiency against 0.917 | 0.6 vs 2.0 points | met |
| **C1** — HPT mean-line efficiency against 0.9155 / 0.925 / 0.927 | 0.55 vs 2.0 points | met |
| **C1** — HPC efficiency against 0.847 | 0.15 vs 2.0 points | met |
| **C2** — stator-10 exit swirl | 0.02 vs 2.0 degrees | met |
| **C4-1** — the solver against an exact answer (Sod shock tube, star pressure) | 0.02 vs 2.0 percent | met |
| **C4-2** — Rotor 37 blade geometry, 24 section-closure constraints | 0.0 vs 0.0 inches of closure error | met |
| **C4-3** — CFD against the Rotor 37 validation case | — | **gated** |
| **D3** — total secondary air against Table XI's 16.1 % of W25 | 0.04 vs 0.5 percent of W25 | half |
| **D4** — cruise clearance, two independent routes | 0.04 vs 0.2 percent of span | met |
| **E1** — Table X centrifugal stresses, all ten HPC stages | 6.5 vs 10.0 percent | half |
| **E2** — the bore doubling for a small hole | 0.0 vs 0.5 percent | half |
| **E3** — blade first flex, the unshrouded booster | 2.7 vs 15.0 percent | met |
| **E3** — first three modes of every HPC stage against Figs 33-42 | 21.4 vs 5.0 percent, mean over 24 comparisons | half |
| **E4** — no rotor critical inside the operating band | 0.0 vs 0.0 count inside the band | half |
| **E5** — every attachment with a printed allowable has margin | 0.0 vs 0.0 percent by which any attachment exceeds its allowable | half |
| **F1** — every Stage E stress with a printed allowable, tabulated against it | 0.0 vs 0.0 percent by which any stress exceeds its allowable | half |
| **F2** — basic engine mass within 10 % of 3,473 kg | — | **gated** |
| **G1** — generated blade volume against Stage F2's integral | 0.94 vs 2.0 percent | half |
| **G1** — blade-to-blade interference, all 32 rows | 0.0 vs 0.0 cubic metres of overlap | met |
| **H** — zero clashes through rotation, every bearing with its load | — | **gated** |
| **I3** — FINDINGS.md written -- every disagreement ranked, with a cause or unresolved | 0.0 vs 0.0 sections of the closure not written | met |
| **I2** — one-at-a-time sensitivity of sfc, metal temperature and disc stress | 0.017 vs 0.02 worst departure from an exact analytic elasticity | met |
| **J1** — the meridional plot draws every module at true scale, with the known join measured and both unknown joins visible as gaps | — | met |
| **J2** — the Campbell match renders every one of E3's 24 comparisons with its reading uncertainty, on a linear axis, published lines as read | — | met |
| **J3** — the glTF carries all 32 rows and 2890 blades, each row's mesh within 1 percent of its solid by volume, placed on J1's axis | 0.374 vs 1.0 percent of row volume | met |
| **J4** — the README's numbers are generated from the code and a test fails if they drift | — | met |
| **J5** — the drawing pack renders a GA and one sheet per module, every assumed dimension parenthesised, no station drawn at an unpublished position | — | met |
| **J6** — every headline claim in the post is bound to the value the code produces | — | met |
| **J7** — the site cutaway turns both spools at the ratio the glTF carries, taking every row's spool and both speeds from the file | 1.35 vs 2.0 percent of row volume, web variant | met |
| **J8** — the two assumed axial stitching offsets close the published turbomachinery length | 0.0 vs 4.0 percent of the 318.0 cm fan-flange-to-LPT-exit length | met |
| **J9** — the mixed-flow nozzle exit area from continuity on the published cycle matches the printed diameter | 0.3 vs 3.0 percent of exit diameter | met |
| **E7** — the five LPT flutter safety factors imply one allowable index, and the five agree | 24.4 vs 15.0 percent departure from the mean implied allowable | half |
| **E8** — uncorrected root gas bending on all five LPT stages, from the C1 mean-line loads and the transcribed root sections | 17.7 vs 25.0 percent | met |
| **I4** — every recorded reading uncertainty is in the register with the closures it governs and a resolvability verdict, and the unstated ones are counted | — | met |
| **G2** — the inner OGV builds with its sections on planes normal to a 60-degree swept, 20-to-0-degree leaned stacking axis | 2.09 vs 2.0 percent of vane volume | half |
| **C5** — the HPC's published stall-margin design intent is reproduced -- stages 6-7 least loaded at design, 6-7 loading up at intermediate speed, 8-10 unloading at low speed | — | met |
| **E9** — the HPC rotor's joint torque as a function of position, bounded by the HP spool torque and by the HPT joint | — | met |
| **D6** — thrust balance on the HP rotor -- the net axial load and what the balance piston must trim | — | **gated** |

### Figures

- [`blading-meridional.png`](solvers/publication/figures/blading-meridional.png)
- [`campbell-match.png`](solvers/publication/figures/campbell-match.png)
- [`campbell-stages.png`](solvers/publication/figures/campbell-stages.png)
- [`meridional.png`](solvers/publication/figures/meridional.png)

### Outstanding

16 closures are not met. None is open without a reason attached:

- **B1** (half) — the mixer reproduces Table XXIII's sfc improvement. open on the LEVEL. Table XXIII's column-to-column differences reproduce to 0.25 point, but the level is 0.7 point high because mass-weighted total pressure is the ideal upper bound. Needs Fi
- **B3** (half) — sfc at three ratings against Table XII. two of three inside the band. Takeoff reads +1.91 % and is a strict xfail with its size pinned; the cause is recorded -- Table XII is a mixed-day table, T41 on the flat-rating day and sfc on
- **C4-3** (gated) — CFD against the Rotor 37 validation case. The mesh is built and checked (C4-3) and the case runs, but it collapses onto a stalled branch at 26 % of design flow and 13 % of design work, repeatably, near iteration 700. Three MRF fault
- **D3** (half) — total secondary air against Table XI's 16.1 % of W25. the closure also asks that every cavity keeps hot gas out; the stage-1 nozzle's two are done and no others
- **E1** (half) — Table X centrifugal stresses, all ten HPC stages. the closure also asks HPT blade rupture life within a factor of 2; no creep data or Larson-Miller constants are sourced
- **E2** (half) — the bore doubling for a small hole. the closure also asks HPT disc peak effective stress within 10 % of Fig 64; the disc cross-sections were never digitised
- **E3** (half) — first three modes of every HPC stage against Figs 33-42. Figs 33-42 were transcribed on 2026-09-08 and the closure is now EVALUATED rather than gated -- and it fails: 1 of 24 comparisons inside the band, mean +21.4 %, first flex +15.8 % and over-p
- **E4** (half) — no rotor critical inside the operating band. the closure also asks the thrust-bearing load against capacity; no bearing load or capacity is printed anywhere, and D's thrust balance is not done
- **E5** (half) — every attachment with a printed allowable has margin. HPC dovetails per sec 3.2.3; hpc-mechanical.yaml has no blade or dovetail block at all
- **F1** (half) — every Stage E stress with a printed allowable, tabulated against it. allowables AT temperature; MIL-HDBK-5J prints elevated-temperature strength as figures, not tables
- **F2** (gated) — basic engine mass within 10 % of 3,473 kg. disc profiles un-digitised, casings and frames figure-status, and the 320 kg of sumps and drives has no printed geometry
- **G1** (half) — generated blade volume against Stage F2's integral. the closure also asks the generated engine mass to match F2, whose own total is gated
- **H** (gated) — zero clashes through rotation, every bearing with its load. no hand-CAD tool installed and verified; the plan records Fusion's install as corrupt
- **E7** (half) — the five LPT flutter safety factors imply one allowable index, and the five agree. NOT MET on the definition STEP0 named before the run (rotor relative exit velocity): the five implied allowables spread 1.61x, worst 24.4 percent. The departure is MONOTONE, 39.7 to 63.8 fro
- **G2** (half) — the inner OGV builds with its sections on planes normal to a 60-degree swept, 20-to-0-degree leaned stacking axis. Three of four checks pass: the sections are normal to the axis by construction, the solid is valid, and 64 vanes have zero overlap. The volume misses by 0.09 of a point -- and finding 181 sh
- **D6** (gated) — thrust balance on the HP rotor -- the net axial load and what the balance piston must trim. GATED on the HPC disc BORE RADIUS, the un-digitised disc profile -- the same figure that gates E2's peak stress, E2's burst margin and F2's disc masses (finding 193). The gas-path annulus te

The four gaps that are **transcription, not modelling**: the HPT disc profile has no absolute radial scale (blocks E2's peak stress and burst margin, and F2's disc masses); the HPC §3.2.3 dovetails (E5); the casing, liner and dome flowpaths (G); and the combustor liner hole areas (D2). None is a hard problem — they are figures nobody has digitised.

<!-- END GENERATED -->

Work plan in [WORK-PLAN.md](WORK-PLAN.md) — ten stages — sources in
[REFERENCES.md](REFERENCES.md), what is transcribed in
[DATA-INDEX.md](DATA-INDEX.md), how every solver is built in
[METHOD.md](METHOD.md), the data itself in
[`data/e3-fps-published.yaml`](data/e3-fps-published.yaml).

```
gas path   fan -> booster (1/4-stage) -> HPC (10) -> combustor -> HPT (2) -> LPT (5) -> mixer -> nozzle
stations    2          21                  25          3           4          45        5         8
LP spool   [--]       [--]                                                   [--]     bearings 1, 2, 5
HP spool                                  [--]                    [--]                bearings 3, 4
```

---

## The engine

The **NASA/GE Energy Efficient Engine (E³) Flight Propulsion System** — a
mixed-flow, twin-spool, high-bypass turbofan designed by General Electric
under NASA contract NAS3-20643, and the technology programme behind the
big-fan engines GE built afterwards.

It is chosen over a GE90 or a Trent for one reason that decides everything:

> **Its entire design is public domain, and it contains the numbers.**

Fourteen NASA contractor reports cover it — cycle at three rating points,
every component efficiency and cooling flow, per-stage compressor blading
down to section angles, a dimensioned turbine flowpath, blade counts,
metal temperatures, disc stresses, Campbell diagrams for every compressor
stage, running clearances, the bearing arrangement, module masses, and the
engine's measured performance as tested. A modern engine's geometry is
proprietary; this one's is published.

That is the difference between a model that *looks* like an engine and a
design that can be **checked against one**.

## What "no compromise" means, precisely

| Level | Meaning | This project |
|---|---|---|
| L1 Geometric | looks like the component | the reference model; not acceptable here |
| L2 Parametric | stage-level numbers right, from the source | the floor, everywhere |
| **L3 Physical** | a **validated** method reproduces the **published** performance to a **stated** tolerance | **the commitment, wherever NASA published a result to check** |

Ten stages: foundation, thermodynamic, aerodynamic, thermal, mechanical,
materials and mass, geometry, hand CAD, whole-engine verification,
publication. Each discipline validates its method on a NASA test case
(Rotor 37, NACA 65-series cascades, Ainley–Mathieson, TP-2232 cooling data)
before applying it to the E³, then compares with the E³'s own published
result. Stages A–F need no CAD licence — 370 of the 510 hours.

## What this project claims, and how each claim is checked

| Claim | Checked against | Tolerance |
|---|---|---|
| The cycle is right at three ratings | Table XII: sfc, OPR, BPR, FPRs, HPC PR, T41 | stated before the run, same at all three points |
| The compressor is right | Table XIV η 0.860; Table X angles and stresses; Table XXI vector diagrams; Figs. 33–42 Campbell, all ten stages | 1.0 pt η · 10 % stress · 2° swirl · 5 % frequency |
| The turbines are right | HPT Table III, Fig. 5; LPT Table I | 0.5 pt η |
| The cooling is right | HPT report Figs. 27, 33, 35 metal temperatures, with the published flows | 25 K |
| The structure is an engine | five bearings, two sumps, thrust balance across the mission | load path traced to a casing for every rotor |
| The mass is right | Table XXVI, module by module | 10 % total, 20 % any module |
| The methods are trustworthy | Rotor 37 CFD, TN 3916 cascades, TP-2232 correlations | within published experimental scatter |

The last row is the one the others rest on.

## Why it is not another CAD render

Searching for turbofan models returns hundreds sharing three properties:
untwisted blades, no bearings, proportions from a photograph. The
[work plan](WORK-PLAN.md) lists every flaw in the reference model and the
phase that designs it out.

This one starts from the thermodynamics and lets the geometry fall out of
it. The headline figure is not the cutaway. It is **computed annulus radius
against NASA's published annulus radius** — the first version is
[`solvers/e3cycle/figures/annulus.png`](solvers/e3cycle/figures/annulus.png),
continuity at each report's design Mach against the transcribed walls with
the pass band drawn — then **ten Campbell diagrams against NASA's ten**,
then the render.

## What it builds on

| Project | Contributes | State |
|---|---|---|
| [08 — Turbofan cycle model](../08-cycle-model/) | station-by-station solve, to be extended with a mixer and validated | v1, 82 tests |
| [06 — Parametric blade row](../06-blade-row/) | twist, blade rings, annulus, STEP; extended to arbitrary section stacks | v1, 96 tests |
| [07 — Parametric nacelle](../07-nacelle/) | CST cowl | v1, 71 tests |
| [05 — OpenFOAM airfoil](../05-openfoam-airfoil/) | the CFD discipline: GCI, convergence | complete |
| [01 — Airfoil analysis](../01-airfoil-analysis/) | camber-line + thickness section construction | complete |
| [CAD-05 — Sheet metal bracket](https://github.com/Itsvkid/CAD-Projects) | FEA discipline: converge, then disbelieve the peak | complete |
| [CAD-06 — HP turbine blade](https://github.com/Itsvkid/CAD-Projects) | hot-section blade detail | brief |

Seven projects become one engine.

## Consistency rules

1. One source of numbers — `data/*.yaml`, every value with a `src:`.
2. Two routes to every number the reports give two ways, and a test.
3. Tolerance stated before the result.
4. Validate the method before applying it.
5. A quantity two disciplines share is asserted equal by a test.
6. Assumptions labelled `src: assumption` — the fan sections are the known one.
7. Everything regenerated by `build.py`; nothing hand-edited.
8. `FINDINGS.md` grows; it is never trimmed.

## Honesty rules

1. **It is the E³, not a GE90.** Named, cited, NASA credited.
2. **Inputs fixed before the run.** Efficiencies and cooling flows are
   NASA's; they are not tuned to match.
3. **Digitised geometry carries an uncertainty.** Stated per figure.
4. **The disagreement gets published.**
5. **Unverified numbers are labelled**, with where to settle them.
6. **Designed, not transcribed, is said so.** The fan blade sections are
   not published; they are designed by the SP-36 method and labelled.

## Running it

```bash
./fetch-sources.sh          # 41 documents, all public domain, ~720 MB
./fetch-sources.sh --check  # what is present
python -m pytest tests/     # the full suite; two files skip without cadquery
./cfd/run_shocktube.sh      # Stage C4: the OpenFOAM validation case (needs colima + docker)
python build.py             # every stage's tables and figures, into build/
python build.py --export    # ...and unit G1's 32 blade rows as STEP  (5 min)
python build.py --list      # what would run, without running it
python tools/build_findings.py   # regenerate FINDINGS.md, the deliverable
python tools/build_readme.py     # regenerate this README's status block

python solvers/e3cycle/run.py   # Stage B: the three Table XII ratings, the mixer, sensitivities
(cd solvers && python -m e3cycle.stations)   # B4: station table, annulus checks, the two figures
```

`build.py` writes each solver module's output to `build/<module>.txt`, so a
run can be diffed against the numbers quoted in the `STEP0.md` files. It
deliberately produces no gated quantity — there is no basic-engine mass and
no CFD in it, because both are blocked on transcription that has not been
done.

**[FINDINGS.md](FINDINGS.md) is the deliverable** — every disagreement with a
published number, ranked, with a cause or "unresolved". Regenerate it with
`python tools/build_findings.py`.

Where the work stands, and what comes next, is in
[RESUME.md](RESUME.md).

Every solver directory carries a `STEP0.md` that states its tolerance and
its validation case **before** the run, and records the misses and findings
after it. Those files are the project: `solvers/*/STEP0.md`.

---

*Primary source: NASA CR-168219, "Energy Efficient Engine Flight Propulsion
System Final Analysis and Design Report", General Electric Company for NASA
Lewis Research Center, contract NAS3-20643. US Government work, public use
permitted. Thirteen further E³ reports and twenty-four method, validation,
materials and regulatory sources are listed in REFERENCES.md.*
