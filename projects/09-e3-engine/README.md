# 09 — The Energy Efficient Engine, rebuilt from its design reports

A complete twin-spool turbofan — nacelle, fan, booster, compressor,
combustor, both turbines, shafts, sumps, bearings and casings — designed
discipline by discipline to the fidelity the published data can check, then
assembled and sectioned as a rotating cutaway. **Every number is traceable
to a public-domain NASA report; every analysis method is validated on a NASA
test case before it touches the engine; every result is compared with what
NASA measured, and the gap is published.**

**Status:** foundation. Sources on disk, the architecture and the
stage-level data transcribed and held by 37 tests. Work plan in
[WORK-PLAN.md](WORK-PLAN.md) — ten stages, ~510 hours — sources in
[REFERENCES.md](REFERENCES.md), what is transcribed in
[DATA-INDEX.md](DATA-INDEX.md), the data itself in
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
against NASA's published annulus radius**, then **ten Campbell diagrams
against NASA's ten**, then the render.

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
python -m pytest tests/     # 37 tests, plain interpreter
```

`build.py` arrives with Stage B.

---

*Primary source: NASA CR-168219, "Energy Efficient Engine Flight Propulsion
System Final Analysis and Design Report", General Electric Company for NASA
Lewis Research Center, contract NAS3-20643. US Government work, public use
permitted. Thirteen further E³ reports and twenty-four method, validation,
materials and regulatory sources are listed in REFERENCES.md.*
