# References

Every source this project builds on, what it gives, and its licence status.

**The rule this project runs on:** a number that appears in the model must be
traceable to a row in this file. If it cannot be cited, it is an assumption,
and assumptions get labelled as such in `data/e3-fps-published.yaml`.

---

## Primary — the design report this project rebuilds

### [1] NASA CR-168219 — E³ Flight Propulsion System, Final Analysis and Design

General Electric Company, for NASA Lewis Research Center under contract
**NAS3-20643**, Aircraft Energy Efficiency (ACEE) Program, Energy Efficient
Engine (E³) Project. 175 pp.

<https://ntrs.nasa.gov/api/citations/19900019242/downloads/19900019242.pdf>

**Licence: US Government work, public use permitted.** This is the reason
the project is possible at all.

This single document is a complete engineering data package for a whole
turbofan. Verified contents, with report page numbers:

| Item | Where | What it gives this project |
|---|---|---|
| **Table XII — FPS Cycle Definition** | p. 35 | OPR, BPR, fan and compressor pressure ratios, HPT rotor inlet temperature and sfc, at three rating points. **The cycle validation target** |
| **Table XI — Component Performance, Max Cruise** | p. 34 | Every component efficiency, every pressure loss, and all four cooling/purge flows as % W₂₅. **The inputs that make the validation fair** |
| **Table XXVI — FPS Weight Summary** | p. 140 | Mass broken down by module and by rotor/stator. **Module-level mass validation, not just a total** |
| Fig. 1 — FPS Design | p. 4 | Full engine cross-section — the master flowpath drawing |
| Fig. 13 — Fan Cross Section | p. 38 | Fan and booster flowpath |
| Fig. 18 — Compressor Cross Section | p. 47 | 10-stage HPC flowpath |
| Fig. 22 — Combustor Cross Section | p. 59 | Liner, dome, diffuser |
| Fig. 24 — HPT Cross Section | p. 66 | 2-stage HPT flowpath |
| Fig. 32 — LPT Cross Section | p. 83 | 5-stage LPT flowpath |
| Fig. 35, 36 — Turbine Frame | pp. 93, 94 | Rear structure, both views |
| Fig. 37, 38 — Forward and Aft Sump Design | pp. 97, 99 | **Bearing locations and support structure** — the thing every student model omits |
| Fig. 29, 30, 31 — Blade-tip and interstage seal clearances | pp. 77–79 | Real running clearance numbers |
| Fig. 40 — Nacelle General Arrangement | p. 106 | Cowl, reverser, mount |
| Fig. 44, 45 — Mount links and brackets | pp. 112, 113 | How the engine hangs off the pylon |
| §5.7 — Sumps, Drives, Configuration, Lube | pp. 96–100 | Bearing system narrative |
| §4.3 — Final Cycle Refinement | p. 32 | Fan tip diameter, core corrected flow, thrust |

**Sections read and verified in preparing this project:** Foreword, Tables of
Contents / Illustrations / Tables, Fig. 1, §4.3, §4.4, Tables XI, XII, XIII,
XIV, XV, XVIII, XXI, XXIII, XXVI; §5.1 (fan, incl. Figs. 13–17), §5.2
(compressor, incl. Fig. 18), §5.3 (combustor, incl. Figs. 22–23), §5.4
(HPT, incl. Figs. 24–27), §5.5 (LPT, incl. Figs. 32–33), §5.7 (sumps and
bearings, incl. Figs. 37–38), §5.8 (exhaust, incl. Fig. 39), §5.9 opening.
What each gave is in [DATA-INDEX.md](DATA-INDEX.md).

### [2] Sister E³ component design reports

Same programme, same licence, all on NTRS. Each is the depth behind one
module of [1]. Open these when a component needs more than [1] gives.

| Report | NTRS ID | Gives — verified contents |
|---|---|---|
| E³ High Pressure Compressor, detail design (170 pp.) | `19850002690` | **Table X pp. 65–66: per-stage rotor summary** — blade count, radii, angles, chord, solidity, material, temperature, stress, HP spool rpm. **Table XXI pp. 112–153: stator vector diagrams and geometry. Table XXII pp. 154–158: rotor airfoil section geometry.** Campbell diagrams per stage, clearances, casing bolting |
| E³ HPT test hardware, detailed design, CR-167955 (195 pp.) | `19850002687` | **Fig. 3 p. 9: dimensioned flowpath. Table III p. 10: stage aero, blade counts 46/48/76/70, tip speeds, clearances. Table IV p. 12: solidity, Zweifel, aspect ratio. Fig. 6 p. 14: airfoil shapes hub/pitch/tip.** §5.2.1: every disc, shaft and retainer with stress and LCF |
| E³ LPT test hardware, detailed design (188 pp.) | `19850002686` | **Table I p. 5: three-point operating data.** §2.5–2.7 final flowpath and vector diagrams; Figs. 9–18 vane and blade shapes per stage; §4.2 blades, dovetails, discs, seals |
| E³ Preliminary Design, CR-135444 (402 pp.) | `19780023165` | The trade studies behind the configuration — not yet opened |
| E³ Core design and performance (538 pp.) | `19900019243` | Core as tested — not yet opened |

### [2b] NASA SP-36 — *Aerodynamic Design of Axial-Flow Compressors*

Johnsen & Bullock (eds.), Lewis Research Center, 1965. NTRS `19650013744`.
**Public use permitted.** Consolidates the declassified 1956 research
memoranda into the compressor design method: Lieblein diffusion factor,
cascade loss and deviation correlations, radial equilibrium, stall. The
reference every later compressor text is measured against, and the method
behind the E³ HPC. Fetched by `fetch-sources.sh`.

Fetch pattern: `https://ntrs.nasa.gov/api/citations/<ID>/downloads/<ID>.pdf`

> **These are scanned documents.** Text extraction fails; they must be read
> as page images. Budget for that — it is why digitising the flowpath is its
> own phase rather than an afternoon.

---

## Secondary — the GE90, for the "what did this become" framing

The E³ is the technology programme behind GE's subsequent big fans. The GE90
is the recognisable name; its actual geometry is proprietary, so it is used
here **only for context and top-level comparison**, never as a geometry source.

### [3] CAA New Zealand, Type Acceptance Report TAR 11/21B/7 — GE90-100 Series

Rev. 0, 21 October 2010, validating FAA Type Certificate **E00049EN**.

<https://www.aviation.govt.nz/assets/aircraft/type-acceptance-reports/Gen_Electric_GE90-100_Series.pdf>

Verified directly from the document:

- GE90 baseline architecture: **10-stage HPC** driven by a **2-stage HPT**;
  a **6-stage LPT** drives a **single-stage fan and 3-stage LPC**.
- GE90-100 growth changes: increased fan diameter and pressure ratio using
  **swept blade technology**; **booster gains a 4th stage**; **new 9-stage HPC
  with a stage-1 blisk**; combustor scaled from the **DAC II** design; new HP
  and LP turbine blades and vanes with lower solidity and improved cooling;
  fan-blade-out load reduction features; FADEC 3.
- Certification basis FAR Part 33 through Amdt 33-20, plus Special Condition
  **SC-33-ANE-08-NE** for the composite fan blades.
- Blade-out test agreed at the **inner annulus flowpath line rather than the
  dovetail** — a detail worth knowing if the blade root ever comes up.
- Emissions compliance quoted with **28 P02 and 2 P01 fuel nozzles**.

### [4] EASA TCDS IM.E.002 — GE90 series

<https://www.easa.europa.eu/en/downloads/7799/en> — **not yet opened.**
Use it to confirm dimensions and ratings independently of [3].

---

## Verified 3 September — the architecture block is closed

Everything that was on the "to verify" list has now been read in the source.
What each turned out to be, since two of them were not what was assumed:

| Claim | Settled as | Where |
|---|---|---|
| E³ fan blade count | **32**, solid titanium, 50 % span shrouds — *not* wide-chord unshrouded | [1] §5.1.2 p. 45; Fig. 13 p. 38 |
| E³ booster | **A single quarter-stage** under an untrapped island — *not* a multi-stage LPC. Rows 60 / 56 / 64 | [1] §5.1 p. 37, §5.1.1 p. 43; Fig. 13 |
| E³ HPC | 10 stages, **23.0** on the operating line at the max-climb match ([2]'s abstract quotes 22.6 as the design value), 0.860 adiabatic, 0.906 polytropic | [1] §5.2 p. 45, Table XIV p. 51 |
| E³ LPT stage count | **5** | [1] §5.5 p. 82, §5.5.1 p. 85 |
| E³ combustor | **Double annular**, 60 cups, 30 nozzles | [1] §5.3 pp. 57–62 |

## Still to verify before quoting

| Claim | Current status | Where to settle it |
|---|---|---|
| GE90-115B fan diameter 128 in / 3.25 m | Sources seen disagree (10.5 ft vs 128 in) | [4], or GE's own published data |
| GE90-115B dry weight | Not sourced | [4] or manufacturer data |
| Booster rows 60 / 56 — which is the vane and which the blade | Assigned by upstream/downstream position in Fig. 13; 64 is confirmed in text as the inner OGV | [1] §5.1.1 pp. 41–45, read again with the figure |
| HPC variable-stator row count | [1] says IGV + stators 1–4 (pp. 45, 52); [2] says IGV + five rows for the product engine (p. 64) | Use [2] for the FPS product; note both |
| LPT blade counts per stage | Not yet transcribed | LPT report §4.2.1 pp. 82–101, Fig. 52 p. 83 |

Full inventory of what is transcribed, located, or must be digitised:
[DATA-INDEX.md](DATA-INDEX.md).

---

## Own prior work this project consumes

Not external, but it is where most of the engineering already lives.

| Project | Path | What this project takes |
|---|---|---|
| PF-08 turbofan cycle | `projects/08-cycle-model` | `Stations`, `gas.py`, `components.py` — the solver to validate and then drive geometry from |
| PF-06 blade row | `projects/06-blade-row` | `velocity_triangles.py`, `annulus.py`, `blade.py`, free-vortex twist, STEP export |
| PF-07 nacelle | `projects/07-nacelle` | CST cowl and hollow shell, STEP export |
| CAD-05 bracket | `CAD-Projects/05-Sheet-Metal-Bracket` | The verification pattern: converge it, then disbelieve the peak |
| CAD-06 turbine blade | `CAD-Projects/06-Turbine-Blade` | The hot-section blade detail, when Stage 1 of that brief is done |

## Domain notes backing the physics

In the private vault, not the public mirror:
`Job-Search-2026/Job_Search-2026/GT-Design/` — nine subjects, nine worked
problem sets. Subjects 01 (aero), 02 (integrity), 04 (cooling) and 05
(secondary air) all carry directly into this project.

---

## Citation style for the write-up

State the report, the table or figure, and the page. Not "NASA data" —
**"NASA CR-168219, Table XII, p. 35."** The specificity *is* the credibility,
and it takes four extra words.
