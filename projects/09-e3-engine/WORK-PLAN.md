# Work plan — PF-09

Five stages, fourteen phases. Each phase ends in something checkable, and
**no phase starts until the previous one's check has closed.** That rule is
the only thing standing between this and a three-week render.

Tick as you go. Study progress lives in the vault; *this* is the build.

| Stage | What it produces | Hours | Needs CAD? |
|---|---|---|---|
| **A** | Published data, a validated cycle, a computed flowpath | 26 | no |
| **B** | Every bladed row and the nacelle, generated | 22 | no |
| **C** | Static structure, bearings, assembly, the cutaway | 34 | **yes** |
| **D** | Mass, stress and clearance verification | 16 | partly |
| **E** | Site entry, drawing pack, the post | 10 | no |
| | | **108** | 34 in a GUI |

At ten hours a week that is eleven weeks; at twenty, six. **Stage A alone is
a portfolio piece** and needs no CAD licence — if the tool question drags,
Stage A and B still stand on their own.

> [!important] The one rule that outranks this document
> The twenty-minute weekly job block comes first, every week, without
> exception. This project makes an interview go well. It does not produce
> one. If a week only has twenty minutes in it, they go to Chain A.

---

# STAGE A — Foundation

No CAD licence, no tool decision, nothing blocked. Start here today.

## Phase A1 · Acquire and read the primary source · 6 h

- [x] Download the reference set to `sources/`, gitignored
      (mirror the `fetch-library.sh` convention — script committed, binary not)
- [x] Write `fetch-sources.sh` so a clean clone can reproduce the reference set
      — 7 documents, 1,678 pages, 67 MB
- [ ] Read §3 Features, §4 Cycle in full
- [x] Read §5.1 Fan, §5.2 Compressor, §5.3 Combustor, §5.4 HPT, §5.5 LPT
- [x] Read §5.7 Sumps, Drives, Configuration — the bearing system
- [x] Read §5.8 Exhaust
- [x] Settle every row in REFERENCES.md → "To verify before quoting"
- [x] **Find the booster stage count** — it is a single **quarter-stage**
      under an untrapped island, not a multi-stage LPC. Rows 60 / 56 / 64
- [x] Transcribe HPC Table X (per-stage rotor summary), HPT Table III and
      IV, HPT Fig. 3 flowpath, bearing arrangement, combustor counts
- [x] `data/e3-fps-published.yaml`: every architecture entry `verified: true`
      with its page
- [x] `tests/test_published_data.py` — transcription checked against itself
      wherever the reports give two routes to one number
- [ ] Transcribe HPC Table XXII (rotor section geometry, 5 pages) and
      Table XXI (stators, 40 pages) — the blade-angle data
- [ ] Transcribe LPT blade counts per stage — LPT report §4.2.1, Fig. 52
- [ ] Settle which of rows 60 / 56 is the booster vane and which the blade

*Closes when:* no `verified: false` remains in the architecture block, and
every `settle_at` has become a `src`. **The architecture block closed on
3 September.** What remains in A1 is the blade-level geometry transcription,
which DATA-INDEX.md ranks by what it unlocks.

> [!note] Topology is already asserted, not assumed
> `data/e3-fps-published.yaml → topology` encodes the gas path
> (fan → booster → HPC → combustor → HPT → LPT → mixer → nozzle) and the
> crossed spool arrangement (LP drives fan + booster, HP drives HPC), and
> `tests/test_topology.py` holds both to it — including cross-checking
> against PF-08's own `Stations` ordering. 11 tests, passing. Nothing
> downstream can quietly put a component in the wrong place.

## Phase A2 · Validate the cycle model against published data · 8 h

The phase that turns PF-08 from "a cycle model" into "a cycle model that has
been checked against a real engine's published design point".

- [ ] Add an E³ design point to PF-08 using **only** the published component
      efficiencies and pressure ratios from Table XI — no tuning
- [ ] Solve at max climb, 10.67 km, Mach 0.8, dry air, zero bleed, 100% ram
- [ ] Compare against Table XII: OPR, BPR, sfc, HPT rotor inlet temperature
- [ ] Write the comparison as a test that asserts agreement to a **stated**
      tolerance, and states it in the failure message
- [ ] **Handle the two structural differences honestly:**
  - [ ] E³ is **mixed-flow** (mixer effectiveness 83.8%); PF-08 is
        separate-exhaust. Either add a mixer model or compare core-only —
        and say which, in the README
  - [ ] E³ quotes **separate fan bypass and hub pressure ratios** (1.68 /
        1.70); PF-08 has one fan pressure ratio. Decide and document
- [ ] Add the cooling flows as chargeable / nonchargeable and check the
      effect on turbine work

*Closes when:* sfc agrees with 0.0541 kg/N/hr within a tolerance you chose
before running it, **or** you can name which assumption accounts for the
gap. A gap you can explain is a better result than agreement you cannot.

> This is the single highest-value phase in the project. "My turbofan cycle
> model reproduces the NASA E³ design point sfc to within X%" is a sentence
> almost no graduate can say, and it costs eight hours.

## Phase A3 · Digitise the flowpath · 8 h

The report gives cross-section *figures*, not coordinate *tables*. So this
is a measurement exercise with an uncertainty attached — which is itself the
engineering.

- [ ] Extract Fig. 1, 13, 18, 22, 24, 32 as images at full resolution
- [ ] Establish scale on each from the known fan tip diameter, 2.11 m
- [ ] Digitise hub and tip radius at every blade row leading and trailing edge
- [ ] Record axial positions on a common datum (fan face = x 0)
- [ ] **State the digitising uncertainty** — ±mm, from pixel size and how
      cleanly the scanned line reads
- [ ] Write the result into `flowpath.stations` in the YAML, each with `src`
- [ ] Cross-check: does the digitised fan tip radius return 2.11 m diameter?
      Does the core inlet area give 54.4 kg/s corrected at the design point?

*Closes when:* two independent checks on the digitised geometry close, and
every station carries an uncertainty.

## Phase A4 · The computed annulus, and the disagreement · 4 h

Now the part nobody else does: **compute** the annulus from your own cycle
and compare it to the one you just measured.

- [ ] From PF-08's `Stations`, compute required annulus area at each station
      by continuity at a chosen axial Mach number
- [ ] Convert area to hub and tip radii on a stated hub-line assumption
- [ ] Plot computed radii over digitised radii, same axes
- [ ] Write up where they differ and why — axial Mach assumption, hub line,
      cooling flow bookkeeping, real-gas effects

*Closes when:* **the meridional plot exists.** Computed flowpath and NASA's
published flowpath, overlaid, with the disagreement quantified.

> [!success] This figure is the project
> It is the one image that says the geometry was derived rather than drawn,
> and it is what a gas turbine engineer will stop scrolling for. Everything
> in Stages B and C is downstream of it. Lead every write-up with it.

---

# STAGE B — Generated geometry

Reuses PF-06 and PF-07 almost unchanged. Still no CAD licence.

## Phase B1 · Blade rows from the flowpath · 10 h

- [ ] Build a `BladeRow` per row — fan, booster, 10 HPC, 2 HPT, LPT stages —
      at the Phase A3 radii
- [ ] Split each spool's total work across its stages from the cycle, and
      **derive the stage count** rather than copying it
- [ ] Compare derived stage count against the published count; explain gaps
- [ ] Free-vortex twist per row, from `velocity_triangles.py`
- [ ] Blade counts from a chosen pitch-chord ratio, cited
- [ ] Export STEP per row; glTF for the web viewer
- [ ] Tests: n-fold symmetry, throat area passes station mass flow, no
      self-intersection, hub and tip radii match the YAML

*Closes when:* every row exports clean, and the derived stage counts are
either matched or explained.

## Phase B2 · Nacelle, bypass duct and core cowl · 6 h

- [ ] Fit a CST cowl (PF-07) to the nacelle GA in Fig. 40
- [ ] Bypass duct inner and outer lines from the digitised flowpath
- [ ] Core cowl and the mixer/centrebody region
- [ ] Check: bypass area at the nozzle consistent with BPR 6.7

*Closes when:* bypass and core exit areas reproduce the cycle's flow split.

## Phase B3 · Compound assembly and export · 6 h

- [ ] Place every generated body on a common axis and datum
- [ ] One compound STEP, one glTF for `viewer.autodesk.com`
- [ ] Boolean interference check across all generated bodies — zero clashes
- [ ] `build.py` regenerates everything from the YAML in one command

*Closes when:* `python build.py` on a clean clone reproduces every export.

---

# STAGE C — Hand CAD

**Gated.** Do not start until both gates below are green. This is the stage
that moves the empty right-hand column of the skills matrix.

## Phase C0 · Gates and warm-up · 4 h

- [ ] **Gate 1 — which tool?** Read it off two live adverts from the actual
      target employers. NX/Teamcenter or CATIA. Not a generalisation
- [ ] **Gate 2 — does it run?** Fusion's install on this machine was corrupt;
      the Spotlight-exclusion fix is unverified. Confirm launch *and* STEP
      export before planning around it. If NX or CATIA via the Cranfield VDI
      is the answer, confirm the catalogue has it
- [ ] Warm-up: rebuild the hydraulic cylinder body by hand in the chosen
      tool — **113,588.21 mm³**, 7 faces, 1 solid

*Closes when:* the warm-up volume matches to within a few mm³. If it does
not, find which dimension you misread before touching this project.

## Phase C1 · Static structure · 12 h

The half your code cannot do, and the half a design office screens on.

- [ ] Fan case and containment
- [ ] Core casings, split into the report's own **module boundaries**
- [ ] **Bolted flanges at every module joint** — an engine is assembled and
      maintained in modules, and the flanges are where that happens
- [ ] Fan frame and OGVs; turbine frame from Fig. 35/36
- [ ] Combustor: outer casing, inner liner, dome, diffuser (Fig. 22)
- [ ] Struts, and the service passages through them

*Closes when:* every module boundary in Table XXVI's weight breakdown is a
real, separable joint in the model.

## Phase C2 · Rotating structure, sumps and bearings · 10 h

The single clearest differentiator against every student engine model.

- [ ] LP and HP shafts, concentric, LP passing through the HP spool with
      stated running clearance
- [ ] Forward sump and aft sump per Fig. 37 and Fig. 38
- [ ] **Every bearing placed, with its type and the load it takes** — thrust
      versus radial. Write it down per bearing
- [ ] Discs for each rotor stage; blade retention features at the rims
- [ ] Spinner and nose cone

*Closes when:* you can point at each shaft and trace its load path to a
casing through named bearings. If you cannot, the model is a shape.

## Phase C3 · Assembly, section and render · 8 h

- [ ] Assemble on the axis with real constraints, not by dragging
- [ ] **Make it turn.** A revolute joint per spool about the engine axis —
      the LP group (fan, booster, LP shaft, 5 LPT discs) and the HP group
      (10 HPC discs, HP shaft, 2 HPT discs) as two independent rotating
      bodies; everything else (casings, vanes, OGVs, frames, sumps) grounded
- [ ] Motion study at the E³ speed ratio, LP : HP ≈ 3,480 : 12,645 ≈ 1 : 3.6,
      both spools **co-rotating** as the E³ is. Nothing is simulated — no
      aero, no loads — the engine turns, it does not run. Say so on the page
- [ ] Interference check **through a full rotation**, not only at rest —
      blade tips against casing, rotating seals against static, the LP shaft
      inside the HP spool. Zero clashes, the same discipline as CAD-01's
      `test_tolerances.py`
- [ ] Blade-tip and interstage seal clearances set to the published values
      in Fig. 29–31, not eyeballed
- [ ] Section on an axial plane; style the cut faces distinctly
- [ ] Exploded view by module — nearly free once constrained, and it shows
      you understand the maintenance architecture
- [ ] Renders: cutaway, exploded, and a plain GA

*Closes when:* zero clashes, and every rotating-to-static gap is a number
you chose from the report.

---

# STAGE D — Verification

Without this stage the project is a picture. With it, it is the only one of
its kind.

## Phase D1 · Mass, module by module · 6 h

- [ ] Assign materials by module — Ti fan and forward compressor, Ni
      superalloy hot section, steel shafts, composite fan case
- [ ] Total mass per module, in Table XXVI's own categories
- [ ] Compare against the published breakdown, module by module
- [ ] **Explain the largest single discrepancy** rather than the total

*Closes when:* a comparison table exists with a written explanation of the
worst row. Expect to be light — student models always omit the fasteners,
the fluid systems and the sumps, and the sumps alone are 320 kg.

## Phase D2 · Mechanical checks · 6 h

- [ ] HPT blade centrifugal root stress by hand:
      `σ ≈ ρ·ω²·(r_tip² − r_hub²)/2`. Compare against the ~220 MPa figure
      in the recall drills
- [ ] Fan tip speed and relative tip Mach number — is it in the transonic
      band a real fan runs in? If it reads 1.8, a speed assumption is wrong
- [ ] Disc rim load from blade count × blade centrifugal load
- [ ] Creep check on the HPT blade: Larson–Miller at the metal temperature
      implied by the cooling effectiveness, against a target life.
      **An HP blade is creep-limited, not yield-limited** — sizing it against
      yield is the clearest signal of someone who has not worked in this field
- [ ] Cross-check total secondary air (≈15% of W₂₅ from Table XI) against
      the ~20% of core flow rule of thumb, and explain the difference

*Closes when:* every check has a number, a comparison, and a verdict.

## Phase D3 · The disagreement report · 4 h

- [ ] `FINDINGS.md`: every place the model, the cycle and the published data
      disagree, with the cause where you found one and "unresolved" where
      you did not
- [ ] Rank by size, not by how easy they are to explain

*Closes when:* it is written. **This is the deliverable.** Every strong
project in this portfolio produced one — teeth intersecting by 424 mm³, a
545 MPa peak stress that was a boundary condition. An honest findings file
beats a clean render, and interviewers know the difference.

---

# STAGE E — Publication

## Phase E1 · Repository · 4 h

- [ ] README to the house pattern: what it is, status, how to run, what it
      found, what is outstanding
- [ ] `build.py` reproduces every figure and export from a clean clone
- [ ] Full test suite green; add to the root runner
- [ ] STEP gitignored, regenerated by script — the existing convention

## Phase E2 · Site and viewer · 3 h

- [ ] glTF to `viewer.autodesk.com`, referenced from `cadModels` in
      `app/data.js` — static, for inspection
- [ ] **A rotating cutaway on the site.** Export the glTF with bodies grouped
      by spool (`lp`, `hp`, `static`), then reuse the per-spool `useFrame`
      rotation the site's `TurbineStage.js` already does — LP and HP groups
      at the 1 : 3.6 ratio, stopped under `prefers-reduced-motion`. The
      existing `ModelViewer` `autoRotate` is a turntable, not this; the
      spool pattern is in `TurbineStage`
- [ ] Project entry in `app/data.js` — **meridional plot first, render
      second.** Resist leading with the pretty one
- [ ] Dimensioned GA drawing with stations labelled, following PF-06's
      drawing convention
- [ ] Update `projects/README.md` status table

## Phase E3 · The post · 3 h

- [ ] LinkedIn: the render stops the scroll, the meridional plot is the post
- [ ] Lead with the validation, not the modelling:
      *"I rebuilt NASA's Energy Efficient Engine from its 1980s design
      report. My own cycle model reproduces its published design-point sfc to
      within X%, and the annulus is computed from that cycle rather than
      traced off the drawing — here is where mine and NASA's disagree."*
- [ ] Credit the source properly — NASA CR-168219, public domain. Saying
      where the data came from reads as rigour, not as a caveat

---

## What would make this weak

Written down now so it is not discovered at hour ninety.

- **Skipping Stage A and going straight to modelling.** Then it is a render
  of an engine nobody recognises, which is strictly worse than a render of a
  GE90. Stage A *is* the differentiator.
- **Tuning the cycle to match Table XII.** The comparison is only worth
  something if the inputs were fixed before the run. Publish the disagreement.
- **Claiming it is a GE90.** It is the E³ — GE's NASA-funded technology
  demonstrator, and the ancestor of the engines that followed. Say that; it
  is a more interesting story and it is true.
- **Omitting the bearings again.** It is the thing the reference model got
  wrong and the thing a mechanical designer looks for first.
- **Letting it eat the job search.** 108 hours with zero applications sent is
  a worse outcome than no engine and eight applications.

## Progress

| Stage | Phase | Done |
|---|---|---|
| A | A1 Acquire and read | ⬜ |
| A | A2 Cycle validation | ⬜ |
| A | A3 Digitise flowpath | ⬜ |
| A | A4 Computed annulus | ⬜ |
| B | B1 Blade rows | ⬜ |
| B | B2 Nacelle and ducts | ⬜ |
| B | B3 Compound and export | ⬜ |
| C | C0 Gates and warm-up | ⬜ |
| C | C1 Static structure | ⬜ |
| C | C2 Sumps and bearings | ⬜ |
| C | C3 Assembly and section | ⬜ |
| D | D1 Mass | ⬜ |
| D | D2 Mechanical checks | ⬜ |
| D | D3 Findings | ⬜ |
| E | E1 Repository | ⬜ |
| E | E2 Site and viewer | ⬜ |
| E | E3 Post | ⬜ |
