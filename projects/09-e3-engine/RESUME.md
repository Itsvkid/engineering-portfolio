# Where the work stands — resume here

Last updated 2026-09-07. Written so a new session can pick up cold.
The two files that carry the real state are [WORK-PLAN.md](WORK-PLAN.md)
(what is ticked and what its status note says) and each solver's
`STEP0.md` (the band stated before every run, and the findings after it).
This page is only a pointer.

## Done

| Stage | State |
|---|---|
| **A** Foundation | complete — every source transcribed or classified; flowpaths derived from tables, not figures; 30 LPT airfoil sections |
| **B** Thermodynamic design | complete — `solvers/e3cycle/`. sfc +0.46 / +0.56 / +1.91 % at climb / cruise / takeoff against ±1.5 %; annulus by continuity closes at every dimensioned HPT station |
| **C1** Mean-line | **complete** — seven units, see below |

## C1, unit by unit — **closed 2026-09-06**

| Unit | What | Result |
|---|---|---|
| 1 | LPT mean-line kinematics, `meanline/lpt.py` | 28 of 50 Table II pitch quantities in band; 4 findings |
| 2 | Ainley–Mathieson loss model, `meanline/losses.py` | reproduces R&M 2974's own worked example; reads the E³ LPT 8 points low |
| 2b | SP-290 end-wall method | **LPT closes: 0.911 against 0.917** |
| 3 | HPT mean-line, `meanline/hpt.py` | **closes: 0.921 against 0.9155 / 0.925 / 0.927**; Table V transcribed |
| 4 | Compressor deviation, `meanline/compressor.py` | Carter vs 240 printed points: bias −0.39°, rms 2.58° |
| 4b | Compressor loss roll-up | **HPC closes: 0.8455 against 0.847**, two routes agreeing to 0.03 % |
| 5 | HPC stagewise | Figs 11, 17, 18 reproduced from Table XXI; Fig 14 is the span average |
| 6 | Fan and booster, `meanline/fan.py` | tip M_rel **1.405 against 1.41** from the specific flow and tip speed |
| 7 | Stage counts, `meanline/stage_counts.py` | HPC 10, HPT 2, booster 1 **exact** from the cycle alone |

Twenty-nine findings are recorded in `solvers/meanline/STEP0.md`. One
correction to the plan itself: its 0.5-point turbine tolerance cannot be
met by a mean-line method that claims ±2 points for itself, so closing
to 0.5 point is recorded as a C4 (CFD) claim.

## C2 — through-flow, **complete 2026-09-06**

`solvers/throughflow/`, its own `STEP0.md`. Findings 30–41.

| Unit | What | Result |
|---|---|---|
| 8 | Radial-equilibrium audit of Table XXI | balances to 0.243 of the largest term; 0.172 with curvature restored |
| 9 | Predict the spanwise distributions | **stator-10 exit: 0.02° swirl, 0.002 Mach against the plan's ±2° / ±0.02** |
| 10 | The vortex law | LPT "controlled vortex" is **n ≈ −0.5**; the HPC has no single law |
| 11 | HPT Fig 5c, extracted by script | stage-1 work **+0.4 %**; neither free vortex nor solid body |

## C3 — blade sections, in progress

`solvers/blading/`, its own `STEP0.md`. Findings 42–54.

| Unit | What | Result |
|---|---|---|
| 12 | HPC sections rebuilt from Table XXII; throats | **throat margin 4.0 % vs a stated 6 %** on the transonic rotors; stators circular-arc, rotors aft-loaded |
| 13 | LPT throats and Zweifel from the coordinates | **outlet angle to 1.4° rms** of Table II; Zweifel to 0.083 of Table III |
| 14 | HPT throats from Table IV's aspect ratio | **outlet angle to 1.8° rms** of the unit-3 mean-line, with no coordinates |
| 15 | Fan blade — **designed, not transcribed** | **throat margin 11–17 % vs a published 5–8.8 %**; camber 35° → 1°, tip solidity 1.43 vs 1.40 |

## Next, in order

1. **C3's remaining items** — the booster rows and inner OGV (published
    sweep 60°, lean 0–20°) and section stacking with the published
    pretwist and tilt. The LPT's Figs 9–18 surface Mach needs a
    blade-to-blade solver and is really C4.
2. **C4 — GATED on a CFD solver.** The Rotor 37 validation case and its
    pass bands are written and tested
    (`data/methods/rotor37-validation-case.yaml`), so the target is ready.
    But no solver is installed: no OpenFOAM, no SU2, no Homebrew formula,
    Docker present with its daemon stopped. Installing a multi-gigabyte
    image is the user's call. Until then every C4 item waits.
3. **Stage D (thermal) — started.** `solvers/thermal/`, its own
    `STEP0.md`, findings 58–72. **D3 (secondary air) and D4 (clearance control) are closed; D2's exit profile is done.** Unit D1 put all four cooled rows on one
    effectiveness curve; **unit D2 met D1's ±25 K closure at two points of
    three** and located the third's deficit as the leading-edge film.
    Next: film superposition and the cooling transient, the remaining
    rim-seal cavities and the thrust balance, and the combustor's liner
    cooling and its pressure drop from geometry — the last needs the
    liner hole areas, which Stage A did not transcribe.
4. **Stage E (mechanical) — started.** `solvers/mechanical/`, its own
    `STEP0.md`, findings 73–88. **Unit E1 met E1's closure**: all ten HPC
    blade root stresses within 6.5 % of Table X from geometry alone, and
    the blade material crossover fell out of the data at the inertia weld.
    **Unit E2 met half of E2's closure**: the bore doubling for a small
    hole is exact (2.0000 in the limit), and the rim load is 5,882 kN —
    600 tonnes on one disc. The other half, Fig. 64's peak effective
    stress, is **gated on digitising the disc cross-sections**, which
    Stage A never did; that is recorded as finding 81, not skipped. E2
    also rejected the assumption behind the stage: **not one of nineteen
    published rotor stresses scales as N²** — the rotor is thermal at its
    limiting times, bores peaking at 875 s and gas-washed parts at 40 s.
    **Unit E3 built and validated a beam** (`mechanical/beam.py`, exact to
    0.0001 % on three closed-form boundary conditions) and ran it on the
    four blades whose Campbell diagrams are transcribed: the unshrouded
    booster closes at **−2.7 %**, the fan and both HPC vanes bracket
    correctly, and two misses are recorded — the pinned-tip LPT blade
    45 % high, and centrifugal stiffening 30–41 % low on both free blades.
    E3's stated closure is **gated on HPC Figs 33–42**, which
    `hpc-mechanical.yaml` marks figure-status; the ten predictions are
    recorded so the gate is a comparison, not a rebuild.
    Next: gas bending and the root stress, HPT blade creep by
    Larson–Miller against the published rupture life, the flutter screen
    and the Goodman HCF margin, then E4 (rotordynamics), E5 (attachments).
5. Then F (materials and mass), G (geometry generation), H (hand CAD,
    gated on a working install), I (verification), J (publication).

Carried, unresolved, and worth picking up in C3 or later: the LPT's rotor
inlet relative angle 3–7° low at pitch (C1 unit 1 finding 4), the HPT
stage-2 reaction and turning (C1 unit 3 finding 10), the fan's
non-uniform inlet axial profile (C1 unit 6 finding 22), and the
compressor's radial redistribution (C1 unit 4b finding 17).

## Standing rules

- Commit per unit of work. **Push and sync the public mirror only when
  the user says so** (`./sync-public.sh --push`).
- Never "correct" printed source data. Record it as read, with a named
  allowance or `as_printed` note.
- Every solver follows [METHOD.md](METHOD.md): the tolerance and the
  validation case go into `STEP0.md` *before* the run, and are not edited
  after it. Results and findings are appended below them.
- `set -o pipefail` before chaining a commit on a test run.

## Open items carried

- **HPC rotor Campbell diagrams (Figs 33–42) un-digitised.** This is the
  only thing standing between unit E3's ten predictions and E3's stated
  closure. Second-highest-value item in the A3 backlog.
- **Disc cross-sections un-digitised.** This now blocks E2's Fig. 64
  peak-stress comparison and its 120 % burst margin, and will block F2's
  disc masses. Highest-value item in the A3 backlog.
- Mixer level to Stage H (needs Fig 39/40's mixing-plane area).
- Takeoff sfc day effect to Stage C (needs component maps).
- Dunham–Came 1970 and Kacker–Okapuu 1982 papers not on disk; both are
  labelled `src: assumption` where used. Fetch before the HPT clearance
  debit is leaned on (unit 3 finding 9).
- Two AGARD sources still failing in `./fetch-sources.sh` (DTIC).
- A3 backlog: combustor liner geometry, mixer and nozzle drawings, the
  two whole-engine stitching offsets (Stage H), per-figure digitising
  uncertainty.
