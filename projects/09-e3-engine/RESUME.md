# Where the work stands — resume here

Last updated 2026-09-10. Written so a new session can pick up cold.
The two files that carry the real state are [WORK-PLAN.md](WORK-PLAN.md)
(what is ticked and what its status note says) and each solver's
`STEP0.md` (the band stated before every run, and the findings after it).
This page is only a pointer.


## Session log — 2026-09-09/10

**State now: 41 closures (25 met, 12 half, 4 gated), 194 findings,
1,020 test functions, 53 unticked plan items.** Suite green at 1117
passed / 44 xfailed.

**Stage J is complete** — seven units, J1 to J7. Also closed this session:
E7, E8, E9 (mechanical), C5 (HPC off-design), G2 (the swept OGV), I4 (the
digitising register), D6 (thrust balance, gated), and C4-4 moved
substantially.

The units, and the one thing worth remembering about each:

| Unit | What it is | The thing to remember |
|---|---|---|
| J1 | meridional plot | An assumption in use had **no home in `data/`**, so a second consumer made its own — two pictures of one engine 128 cm apart (**159**) |
| J2 | Campbell match | **11 of E3's 24 comparisons cannot resolve a 5 % band at all** — the closure was measuring two things at once (**160**) |
| J3 | glTF, 2,890 blades | Instancing: 32 meshes, not 2,890. Tip caps stand 3 mm proud of their own sections (**163**) |
| J4 | generated README | It claimed **"37 tests"** for months. Numbers in prose need a generator and a staleness test (**168**) |
| J5 | drawing pack | **4 of 10 gas-path stations can be placed**; three of six sheets exist to say something cannot be drawn (**166–167**) |
| J6 | the post | A **true sentence aged out** — "twenty of twenty-one" was right at 98 comparisons, wrong at 100 (**169**) |
| J7 | site cutaway | three.js does not surface `asset.extras`; the page would have spun at plausible speeds while ignoring the file (**172**) |
| E7 | flutter screen | A test built to be **blind to a known bias** — the constancy check survives E3's frequency error (**175**) |
| E8 | gas bending | **Euler's identity caught a counter-swirl sign.** Check a convention against a conservation law before trusting it (**176**) |
| E9 | HPC rotor | The rotor has **two kinds of joint**; the open material question is worth **1.67×** in joint torque (**188, 190**) |
| C5 | HPC off-design | **No stall margin is reported** — none is published. The design intent is confirmed by two figures that do not know about each other (**184**) |
| G2 | swept inner OGV | The plan line **conflated two rows**; a trapezoidal integral is the wrong reference for a curved stack (**180, 181**) |
| I4 | digitising register | Stage A3's last line is **14 % done**, measured rather than described (**178**) |
| D6 | thrust balance | **Gated on the disc bore** — the same A3 figure as E2 and F2, and the term it needs is 3.2–6.4× the one that closes (**193**) |
| C4-4 | Rotor 37 | **The solution never converges at all.** Next step is transient, not another steady variation (**194–197**) |

### Two hazards this session hit

1. **Another session was committing to this repo throughout.** Its commits
   are interleaved in the log above — the CI fixes, the atlas and site
   work, and `52d884e`, which found CR-159584 Table I and corrected two
   offsets my J1 had assumed 61 cm too long. Nothing was lost, but the
   README count raced twice and had to be regenerated. **If you are
   resuming, `git fetch` and check the log before assuming the working
   tree is yours.**
2. **Numbers in prose churn.** `POST.md` states closure and finding counts,
   and every new unit moves them; `tests/test_post.py` catches it, but it
   is an edit per unit. Test counts and findings are stated as **floors**
   for that reason (**170**); closure counts are still exact.

## Handing over — read this first if you are a new session

**Everything needed to continue is in this repository.** Nothing depends
on a Claude account, a saved conversation, or a particular machine. If you
have the repo and the machine's toolchain, you have the project.

| Question | Where the answer lives |
|---|---|
| What is done, what is not, and to what tolerance | `WORK-PLAN.md` — the item list, each stage's *Closes when*, and the Progress table (▣ met, ◧ half, ⬜ not started) |
| Every closure as a machine-readable number | `data/closures.yaml`, checked by `tests/test_cross_discipline.py` |
| Why a number is what it is | the `STEP0.md` in each `solvers/*/` directory: the band stated **before** each run, then the result and the findings |
| Every dataset and where it came from | `DATA-INDEX.md` |
| How to run everything | `README.md`, and `python build.py` |
| How to reproduce the CFD | `cfd/README.md` — including a table of every toolchain trap hit so far |
| The engineering standards this follows | `METHOD.md` |
| The design engineer's accumulated knowledge | `../../.claude/agents/gas-turbine-designer.md` (in this repo, version-controlled, **not** in any user account) |

There are 139 numbered findings across the `STEP0.md` files. They are the
real output of the project; the code exists to produce and check them.

### The rules that matter

1. **State the band before the run.** METHOD.md step 0. A `STEP0.md`
   step-0 section is never edited after its run; results and findings are
   appended below it.
2. **Never "correct" printed source data.** Record it as read, with an
   `as_printed` note. Reading errors in OCR are a different thing and may
   be repaired — say which you are doing.
3. **A miss is a finding, not a bug to tune away.** Several closures are
   half-met on purpose, with the missing half named.
4. **Commit per unit of work**, and update
   `.claude/agents/gas-turbine-designer.md` in the same commit as any
   engine work. A change that leaves the agent stale is incomplete.
5. `./sync-public.sh --push` mirrors publicly; it excludes `.claude/`,
   `CLAUDE.md`, the vault, `resume/` and `cv/`.

### What is left, triaged

Fifty-six plan items are unticked. They are not fifty-six pieces of work
waiting on effort — the great majority are waiting on something that is
not effort, and the split is worth knowing before planning anything.

| | Items | What they need |
|---|---|---|
| **Hand CAD** (all of Stage H) | 13 | **A person at a GUI.** Nothing here can be done by writing code |
| **Un-digitised figures** (A3 and everything it gates) | ~16 | Someone to measure figures: disc profiles, HPT Fig 78, Figs 46–56, 61, 63, the combustor, the mixer and nozzle. Each is marked **GATED** in the plan with what it blocks |
| **Elevated-temperature properties** | 4 | MIL-HDBK-5J prints them as figures, not tables. Blocks creep, LCF, and the Goodman HCF margin — a Goodman diagram at room temperature for a 655 °C blade is not a result |
| **CFD** | 5 | C4-4's Rotor 37 solve, which is characterised and unsolved, plus four cases downstream of it |
| **FEA** | 3 | CalculiX is not installed. Meaningful FEA also needs meshing, boundary conditions and a convergence study — a stage, not a task |
| **Genuinely open to code, now** | ~5 | see below |
| **Deferred by design** | 1 | B's component maps, deferred to Stage C in the plan itself |

**The five that were open to code are now done** (2026-09-09/10):

1. ~~Booster and inner-OGV sweep and lean~~ — **G2**. The sweep and lean
   turned out to be the OGV's alone; the booster's radial stack was
   already right (finding 180).
2. ~~HPC stall margin and the VSV schedule effect~~ — **C5**. No stall
   margin is reported, because no stall line is published; the design
   intent is confirmed against three figures and the VSV effect measured.
3. ~~The bolted-joint and inertia-weld rotor structure of the HPC~~ —
   **E9**. Two kinds of joint, neither positioned, so the answer is a
   torque curve.
4. ~~D's thrust balance~~ — **D6**. Gated after all, but on the disc bore
   radius, which is the same A3 figure that gates E2 and F2 — and the
   disc-face term it needs is 3.2–6.4× the one that closes.
5. ~~Emissions against Tables XVI–XVII~~ — not attempted; the combustor
   volume it needs is undimensioned.

**C4-4 has also moved**: the Rotor 37 field is inspected, two hypotheses
are dead, and the next step is a transient solve. See item 1 below.

**The honest summary:** the modelling this project set out to do is done.
What remains is transcription, a CAD seat, two toolchains, and one
unsolved CFD case.

### The next three things to do

Written 2026-09-10, after Stage J closed and the last five code-reachable
plan items were done. **All three of these are picking up threads that are
already characterised — none is a fresh start.**

1. **C4-4, the Rotor 37 solve — go transient.** The fault is now
   *localised*, not merely characterised (findings 194–197). The machine is
   **reversed at the tip**: the inner 87 % of span flows forward, the outer
   13 % carries 597 K rotor-worked gas back past the inlet plane at swirl
   exceeding blade speed. The periodics carry flux, so that is closed. A
   **constant** back pressure collapses too, so throttling is not the
   cause. And the solution **never reaches a steady state at all** — work
   swings −3 % to +91 % of design across 1500 iterations.

   **Do this:** `rhoPimpleFoam` from the healthy field at iteration 1000 of
   the constant-105 kPa run. If the tip reversal is unsteady, a steady
   solver was never going to work and that is the whole answer. The revised
   four-step list is at the end of `solvers/cfd/STEP0.md`. Two smaller
   things are still open there: y+ on the blade (attempted, inconclusive —
   write the field, do not recompute it) and closing the tip gap from
   0.515 mm to the intended 0.356.

2. **Digitise the HPC disc profiles.** This is now the highest-value
   transcription in the project by some distance: it gates **four**
   closures, not three. E2's peak stress, E2's 120 % burst margin, F2's
   disc masses — and, since unit D6, the whole HP thrust balance, whose
   deciding term is `(p3 − p25)·π(r_hub² − r_bore²)` and is **3.2 to 6.4
   times** the term that does close (finding 193). One figure, four
   closures.

3. **Stage H, or say it will not happen.** Thirteen plan items, all hand
   CAD, all needing a person at a GUI. Fusion 360 is installed and
   verified. Nothing here can be done by writing code, and it is the only
   stage untouched. It is worth an explicit decision rather than sitting in
   the backlog as though it were queued work.

**What is NOT worth picking up:** the remaining ~16 un-digitised figures
other than the disc profiles, the elevated-temperature properties (four
closures wait on figures MIL-HDBK-5J prints rather than tabulates), and the
FEA items (CalculiX is not installed, and meaningful FEA is a stage rather
than a task). All are in the triage table above with what each waits on.

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
2. **C4 — the gate is lifted (2026-09-07) and unit C4-1 is closed.**
    OpenFOAM v2406 runs natively on arm64 via `colima` +
    `opencfd/openfoam-default:2406`; SU2 v8.5.0 runs under Rosetta 2 from
    `~/.local/opt/su2-v8.5.0`. **The solver was validated on an exact
    answer before anything published**: the Sod shock tube, where
    OpenFOAM's star pressure is +0.02 % of closed form and the shock lands
    within a fifth of a cell. Rotor 37 is next — its bands have been
    written since 2026-09-06.
   *(superseded note below, kept for the gate's history)*
   **C4 — was GATED on a CFD solver.** The Rotor 37 validation case and its
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
    `STEP0.md`, findings 73–103. **Unit E1 met E1's closure**: all ten HPC
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
    **Unit E4 met E4's first closure half**: no rotor critical sits inside
    the operating band (worst margin 1.61×), Table XXII checks itself to
    0.008, and the aft seal disc's published critical implies a mode
    stiffening of S = 8.20 from three printed numbers. Shaft torque came
    out of the cycle with the spool speed from each report's own N/√T —
    **takeoff LP speed closes at −0.5 % across three independent
    documents** — and the LP shaft turns out to carry 2.4× the HP shaft's
    torque. Fan blade-out is 746 kN, 76 tonnes. The thrust-bearing half is
    **gated**: no bearing load or capacity is printed anywhere.
    **Unit E5 closed E5 substantially**: the weak-link order holds
    everywhere it can be checked, every attachment with a printed
    allowable has margin, and the printed numbers were made to check each
    other — the HPT tang stresses track the neck widths to 0.47 % (fixing
    the load split at 57/43), LPT Fig. 70's printed Kt reproduces from its
    own stresses to 0.6 % on the blade sections and on neither disc
    section, and a hand tension calculation reads a dovetail **6.4× low**.
    The HPC dovetails are gated: nothing from §3.2.3 was transcribed.
    Next: gas bending and the root stress, HPT blade creep by
    Larson–Miller against the published rupture life, the flutter screen
    and the Goodman HCF margin.
5. **Stage F (materials and mass) — started.** `solvers/materials/`, its
    own `STEP0.md`, findings 104 onward. **Unit F1 substantially closed
    F1** and, more importantly, **corrected E1**: Table X's airfoil weight
    and root area make the density of every HPC blade a measurement, and
    it disagrees with Table X's own material column at stages 5 and 6,
    where the printed weight exceeds the heaviest possible titanium blade
    of that root section. E1's finding 74 is struck in two of its three
    parts (the crossover stands; the "no per-stage material is printed"
    and "it lands on the inertia weld" claims are withdrawn).
    MIL-HDBK-5J's room-temperature allowables are transcribed; its
    **elevated-temperature data is figure-status and gated**.
    **Unit F2** put the C3 blading reconstruction against Table X's twenty
    printed airfoil areas for the first time — **−7.4 % mean and negative
    20 times out of 20**, a one-sided bias that is the missing edge radii
    — and cross-checked five module weights between a component report and
    Table XXVI to 3.2 %. F2's stated closure is **gated**: the disc
    profiles, the casings and frames, and the 320 kg of sumps and drives
    are all un-drawn, so a basic-engine total would pass its band by
    arithmetic rather than by evidence.
    Next in F: creep data per hot-section alloy and Larson–Miller
    constants, which is also what E1's remaining rupture-life item needs.
6. **Stage G (geometry) — started.** `solvers/geometry/`, its own
    `STEP0.md`, findings 113–117. **Unit G1 generates all 32 bladed rows
    as valid solids** and the CAD volume matches Stage F2's integral of the
    same sections to **0.94 %** — PF-06 extended with the conformal
    cylindrical wrap, because PF-06's own validity condition fails at
    chord/radius 0.49. Zero blade-to-blade interference on all 32.
    `python build.py` runs all 29 solver modules in 90 s and writes each
    one's table to `build/`; `--export` adds the STEP set. Discs, casings
    and the nacelle are **gated on transcription, not on method**
    (finding 117).
7. **Stage I (verification) — I1 closed.** `solvers/verification/`, its
    own `STEP0.md`, findings 118–123. Eight stages of independent reading
    now have to agree, as tests: **T41 0.01 %** between the cycle and the
    HPT report's cycle-match line, **cooling flows 0.00 %**, masses F2 vs
    G1 0.94 %, and spool speeds from four documents to 1.6 % with the
    ratio at 3.57 against the plan's 3.6. `data/closures.yaml` carries all
    20 closures with their bands: **14 of 15 numeric ones inside**, one
    pinned miss, and no closure open without a reason attached.
    Next: I2 (sensitivity) and I3 (`FINDINGS.md` — the deliverable).
8. Then H (hand CAD,
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

- **HPC blade and dovetail data (§3.2.3, Table XIV) un-transcribed.**
  `hpc-mechanical.yaml` has no blade block at all. Blocks E5's first item.
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
