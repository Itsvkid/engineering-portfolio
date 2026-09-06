# Where the work stands — resume here

Last updated 2026-09-06. Written so a new session can pick up cold.
The two files that carry the real state are [WORK-PLAN.md](WORK-PLAN.md)
(what is ticked and what its status note says) and each solver's
`STEP0.md` (the band stated before every run, and the findings after it).
This page is only a pointer.

## Done

| Stage | State |
|---|---|
| **A** Foundation | complete — every source transcribed or classified; flowpaths derived from tables, not figures; 30 LPT airfoil sections |
| **B** Thermodynamic design | complete — `solvers/e3cycle/`. sfc +0.46 / +0.56 / +1.91 % at climb / cruise / takeoff against ±1.5 %; annulus by continuity closes at every dimensioned HPT station |
| **C1** Mean-line | units 1–4 done, see below |

## C1, unit by unit

| Unit | What | Result |
|---|---|---|
| 1 | LPT mean-line kinematics, `meanline/lpt.py` | 28 of 50 Table II pitch quantities in band; 4 findings |
| 2 | Ainley–Mathieson loss model, `meanline/losses.py` | reproduces R&M 2974's own worked example; reads the E³ LPT 8 points low |
| 2b | SP-290 end-wall method | **LPT closes: 0.911 against 0.917** |
| 3 | HPT mean-line, `meanline/hpt.py` | **closes: 0.921 against 0.9155 / 0.925 / 0.927**; Table V transcribed |
| 4 | Compressor deviation, `meanline/compressor.py` | Carter's rule vs 240 printed points: bias −0.39°, rms 2.58° |

## Next, in order

1. **C1 unit 4b — compressor loss.** Table XXI prints a loss for each of
   the same 240 streamline points. Roll those into stage and overall
   efficiency, compare with its own cumulative-efficiency column (0.872
   at the OGV pitch streamline) and with the published 0.847 design
   intent / 0.861 Table XI / 0.856 ICLS as tested. Then end-wall and
   tip-clearance loss and the incidence range. SP-36 Fig 148 (wake
   momentum thickness vs diffusion factor, p.204) is the chart to
   digitise if a *predicted* loss is wanted.
2. **C1 remaining** — stage-by-stage HPC against Figs 14, 17, 18, 27;
   fan and quarter-stage with the island split; derive the stage counts
   from loading limits and compare with 1 / ¼ / 10 / 2 / 5.
3. **C2** through-flow, **C3** blade sections, **C4** CFD.

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

- Mixer level to Stage H (needs Fig 39/40's mixing-plane area).
- Takeoff sfc day effect to Stage C (needs component maps).
- Dunham–Came 1970 and Kacker–Okapuu 1982 papers not on disk; both are
  labelled `src: assumption` where used. Fetch before the HPT clearance
  debit is leaned on (unit 3 finding 9).
- Two AGARD sources still failing in `./fetch-sources.sh` (DTIC).
- A3 backlog: combustor liner geometry, mixer and nozzle drawings, the
  two whole-engine stitching offsets (Stage H), per-figure digitising
  uncertainty.
