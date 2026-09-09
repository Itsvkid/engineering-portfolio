# Step 0 — publication (J): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit J1 — the meridional plot

The plan's Stage J line is explicit about order: *Meridional plot **first**;
Campbell match second; render third.* It comes first because it is the one
figure that can contradict eight stages of solvers at a glance. If a wall
crosses itself, if a row sits outside its annulus, if a module is a
different size from the one the mass roll-up weighed — the plot shows it and
no test had to be written to ask.

**A disclosure about this unit's step 0.** It was not written before the
first run. A draft was rendered, three faults were found in it by looking
at the image, and the band below was written afterwards. That is a
departure from METHOD.md step 0 and it is recorded here rather than tidied
away; the three faults are findings 155–157 and they are the reason the
band exists in the form it does. A figure is the one artefact whose first
failure mode is visual, and the honest account is that the eye found these
before any test did.

### What this figure must not do

The band for a drawing is not a percentage. It is a list of things that
would make the figure a lie, each one a test:

| Check | Requirement | Why this one |
|---|---|---|
| Radial extent | every station drawn inside the axes, fan tip **105.4 cm** visible | the draft set `ylim` to 46 cm from the core and put the entire fan off the page |
| Aspect | `set_aspect("equal")`, no radial stretch | a stretched meridional plot misstates every wall angle on it; the core being small is the *result* of a bypass ratio of 6.8 |
| Fan module | radii only, **no wall contour drawn** | the fan report gives three dimensioned radial stations and one axial position. A casing line through them would be a scaled cutaway wearing a different coat |
| Known join | the transition duct drawn at its **measured** length | `lpt-flowpath.csv`'s header says *z from the HPT exit plane*. Re-zeroing that column deletes a real 6.85 cm duct |
| Unknown joins | ~~drawn as hatched bands, width declared in code as a **drawing** width~~ → **drawn at the offsets `engine-flowpath.yaml` records as assumed, each labelled ASSUMED with the range it is allowed** | two offsets were never printed. The first band was written before I knew the Turbofan Atlas already carried both as sourced assumptions — see finding 159 |
| Provenance | every radius traceable to a table or a dimensioned drawing | `engine-flowpath.yaml`'s own rule, and the reason CR-168219 Fig 1 is not digitised anywhere in this project |

**Closes when** the figure renders every module inside the axes at true
aspect, the one known join is at its measured length, and both unpublished
joins are visible and labelled as assumptions carrying their allowable
range — as tests, not by inspection.

## Unit J2 — the Campbell match

Second in the plan's Stage J order. This figure has a harder job than J1,
because **the thing it plots is a failure**: Stage E3's closure asked for
the first three modes of every HPC rotor stage within 5 % of Figs 33–42,
and got 1 of 24. A figure of a miss is easy to draw dishonestly in either
direction — flatter it with a log axis, or dramatise it with a truncated
one — so the band below is mostly about not doing either.

**Step 0 is written before this unit's figures exist.** Unit J1's was not,
and said so. One piece of analysis does precede this section: the reading
uncertainty of the transcription against the closure band, computed while
deciding what the figure should show. It is finding 160 and it is the
reason there are two figures here rather than one.

### What the figures must show

| Check | Requirement | Why |
|---|---|---|
| The miss is not softened | linear frequency axis on the match plot; the 5 % closure band drawn to scale | a log axis would make +78 % look like a near miss |
| The miss is not dramatised | every one of the 24 comparisons plotted, including the four negative ones and the one that passes | showing only the worst is the same lie in the other direction |
| Reading uncertainty is on the figure | per-point error bars from `meta.reading_uncertainty` (±0.05 kHz on a 0–6 axis, ±0.1 on 0–12, ±0.25 on 0–22 and 0–26) | **finding 160**: the transcription cannot resolve 5 % on 11 of the 24 points, so on those the closure is unfalsifiable and the figure must not imply otherwise |
| Published lines drawn as read | flat across the speed range, not rising | the diagrams draw them flat or drooping; that is recorded as an E3 finding and the figure must not silently "fix" it |
| Predicted lines carry their speed dependence | Southwell, evaluated across 0 → 14,500 rpm | the model *does* stiffen with speed even though the published lines do not, and the gap between those two behaviours is the point |
| Operating speed shown | the HP range 12,303 rpm (100 %) to 13,948 (deteriorated) shaded | a Campbell diagram without the operating line is a frequency table |
| Per-rev rays | drawn from each stage's own `per_rev_lines` | the crossings are what a Campbell diagram is for |

**Closes when** both figures render every one of the 24 comparisons with
its reading uncertainty, on a linear axis, with the published lines drawn
as they were read — as tests, not by inspection. **It does not close on
the model agreeing**; that closure is E3's, it is recorded as a miss, and
J2's job is to make the miss legible rather than to move it.

## Unit J3 — the render

Third in the plan's Stage J order: *a rotating cutaway on the site via the
`TurbineStage` spool pattern; static glTF to the Autodesk viewer.*

This unit builds the **glTF**. The 32 blade rows Stage G1 lofted from the
validated sections are real solids with real blade counts; nothing in this
project has yet shown them as one object, and the meridional plot (J1)
shows the annulus without a single blade in it.

**Two things make this harder than an export call.**

First, **size**. One row of 53 blades exports to 27.6 MB, and the
tessellation is dominated by the lofted surface's own face structure, not
by the deflection tolerance — coarsening from 0.5 mm to 8 mm saves 14 %.
All 2,890 blades at that rate is about 1.4 GB, which is not a deliverable.
The fix is **instancing**: glTF nodes may reference one mesh through many
transforms, so the file carries 32 meshes and 2,890 nodes rather than
2,890 meshes. `cadquery`'s own assembly exporter writes a mesh per solid,
so this unit writes the GLB container itself — a JSON chunk and a binary
chunk, no new dependency.

Second, **placement**. The LPT rows already carry their axial stations
(the CSV's z runs from the HPT exit plane); the fan, booster and HPC rows
each sit at their own local zero. Placing them means using J1's engine
axis — including the two offsets that are *assumed*, not published. This
unit must read them from `engine-flowpath.yaml` through J1's `layout()`
and must not acquire its own copy (unit J1 finding 159).

### What the render must satisfy

| Check | Band | Why this one |
|---|---|---|
| The mesh is the solid | tessellated volume within **1 %** of `Solid.Volume()`, every row | G1 checks its CAD against F2's integral to 2 %; the tessellation that feeds a viewer should be tighter than the geometry check it inherits, or the picture is not the part |
| Every row, every blade | 32 rows, **2,890** blades, counts equal to `Row.count` | a render that quietly drops a row is a different engine |
| One mesh per row | meshes = 32, nodes ≈ blades | the whole reason the file is deliverable |
| Cutaway removes blades, never clips them | no blade partially present | a clipped blade draws a shape the engine does not have |
| Axial placement is J1's | positions read through `publication.meridional.layout()` | the assumed offsets must not be copied into a second file |
| The assumption travels with the file | the two assumed offsets and their ranges named in the glTF asset extras | a 3D file outlives the page that explains it |

**Closes when** the GLB carries all 32 rows and all 2,890 blades, every
row's mesh within 1 % of its solid by volume, placed on J1's axis, with
the assumed offsets recorded inside the file — as tests, not by
inspection.

**Explicitly not in this unit:** the rotating cutaway *on the site*.
`app/turbofan/` already renders the E³ procedurally and is under active
edit in another session; adding a second three.js E³ page from this side
would duplicate it and collide. The glTF is the half that belongs to
PF-09, and it is the half the Autodesk viewer needs.

---

## Unit J4 — the README, generated where it carries numbers

The plan's first Stage J bullet: *README to the house pattern; `build.py`;
full suite in the root runner.*

The README claimed **"37 tests"** and *"`build.py`, the discipline loop,
arrives with Stage C"* long after there were nine stages and eight hundred
test functions. That is not a typo to correct once — it is the failure mode
a hand-maintained count has, and this project's whole argument is that
claims get checked. So the status, the closure scoreboard, the figure list
and the outstanding work are **generated** from `data/closures.yaml` and
the tree by `tools/build_readme.py`, between two markers, and
`tests/test_readme.py` fails if the block has drifted. The prose stays
hand-written.

**Closes when** the generated block reproduces exactly on a regenerate,
every closure appears with its state, every gated one says why, and no
test count survives in the hand-written half — as tests, not by
inspection.

## Unit J5 — the drawing pack

*Drawing pack: GA with stations; one detail per module.*

A general arrangement is not a plot with a border round it. What makes it a
drawing is that **every dimension on it is answerable**: it comes from a
table or a dimensioned figure, or it is marked as not.

| Check | Requirement | Why |
|---|---|---|
| Every dimension has a source | each callout traceable to `data/*.yaml` | the project's rule 1, applied to a sheet |
| Assumed dimensions look assumed | drawn in the drafting convention for a reference dimension — **parenthesised** — and listed in the title block | a reader must not measure an assumption off a drawing and quote it |
| Stations are placed, not decorative | the nine gas-path stations at their axial positions on J1's axis, or absent | a station number floating above a flowpath is a label, not a datum |
| A station whose position is unknown is absent | not guessed to make the sheet look complete | stations 1, 2, 13 and 8 have no published axial position |
| One sheet per module | fan and booster, HPC, combustor, HPT, LPT | the plan's own bullet |
| A module with no geometry gets a sheet saying so | the combustor | an empty sheet with the reason is a result; a missing sheet is a silence |
| Title block | source, datum, units, the assumed offsets, the date | a sheet leaves the repository and must carry its own provenance |

**Closes when** the pack renders a GA and one sheet per module, every
assumed dimension parenthesised and listed, and no station drawn at a
position no report gives — as tests, not by inspection.

---

## Unit J6 — the post

*The post: validation-led, NASA credited, the gap stated.* The plan's last
Stage J bullet, and the most public thing this project produces.

A post is also the least likely artefact to be re-checked. Unit J4 found a
README that had carried "37 tests" for months (finding 168); a post
carrying a stale number is the same failure with a wider audience and no
way to correct it after the fact.

| Check | Requirement | Why |
|---|---|---|
| Every headline number is bound to the code | each claim asserted as a substring of `POST.md` against the value the solvers produce | a number in prose has no test unless one is written |
| Validation leads | the agreements appear before the pictures | the plan's own word, *validation-led* |
| The misses are in the post, not only the repo | takeoff sfc, the Campbell closure, the unresolved seven | a post that reports only agreements is advertising |
| NASA is credited by report and contract | CR-168219, NAS3-20643, NASA Lewis, General Electric, TP-1337 | it is their engine and their data |
| Non-affiliation is stated, errors owned | in the footer | |
| The gap is stated | what the public record does not contain, and the unfinished work | the plan's own words |

**Closes when** every headline claim in the post is asserted against the
value the code produces, and the post names its misses and its unfinished
work — as tests, not by inspection.

---

---

## Result — J1

Rendered. `solvers/publication/figures/meridional.png`, from
`solvers/publication/meridional.py`, regenerated by `build.py`.

One engine axis, y = 0 at the fan rotor stacking axis — the datum
`app/turbofan/atlas/flowpath.js` uses.

| Module | Content | Datum | Placed at | How |
|---|---|---|---|---|
| fan | 3 radial stations, 1 with an axial position | fan stacking axis | **0 cm** | the datum |
| HPC | 21 rows, two walls, 85.9 cm | HPC report | 142 cm | **assumed**, allowable 110–150 |
| HPT | 5 stations, 20.0 cm | HPT Fig 3 | 268.2 cm | **assumed**, allowable 45–55 across the diffuser and combustor |
| LPT | 10 rows, two walls | HPT exit plane | 288.2 cm | **measured** |

Joins measured: 1 (the 6.85 cm transition duct). Joins assumed: 2, drawn
at their assumed value and labelled with the range each is allowed.

## Result — J2

Two figures, from `solvers/publication/campbell.py`, regenerated by
`build.py`:

- `figures/campbell-match.png` — the 24 comparisons on a linear axis, the
  ±5 % closure band to scale, each point's reading uncertainty as an error
  bar, and the eleven unfalsifiable points marked hollow.
- `figures/campbell-stages.png` — ten Campbell diagrams, published lines
  drawn flat as printed, predicted lines carrying their speed dependence,
  per-rev rays and the HP operating range shaded.

| | |
|---|---|
| Inside E3's ±5 % band | **1 of 24** |
| Cannot resolve 5 % at all | **11 of 24**, including **all 10** first-flex modes |
| Pass rate where it can be judged | 1 of 13 |
| Inside the figure's own reading uncertainty | 2 of 24 |
| Over-prediction, matched stages 1/2/3/5 | 1F **+19.5 %** → 2F **+25.8 %** → 3F **+37.8 %** |
| Resonance crossings in the operating range | 4, of which **only 1** is picked by both |

---

## Result — J3

`exports/e3-blading.glb`, **4.7 MB**, from `solvers/publication/render.py`.
Preview at `figures/blading-meridional.png`.

`exports/` is gitignored — it holds 35 STEP files as well and they are
regenerable output, not source. `python build.py` rebuilds the GLB from
the sections in about three minutes; the preview figure is committed
because it is the readable half.

| | |
|---|---|
| Rows | **32**, all of Stage G1 |
| Blades | **2,890** modelled, **2,275** drawn after a 75° cutaway |
| Meshes / nodes | **32 meshes, 2,307 nodes** — 127,060 triangles stored, 9.0 M drawn |
| Mesh fidelity | worst **0.374 %** by volume, median 0.094 %, band 1 % — **32 of 32** |
| HPC rows inside the published annulus | **20 of 20**, worst 0.8 mm |
| Axial span | 8.19 → 346.88 cm on J1's axis |
| Assumed offsets | written into `asset.extras` with their allowable ranges |

Instancing is what makes it a deliverable: `cadquery`'s assembly exporter
writes one mesh per solid and produced **27.6 MB for a single row**, which
is about 1.4 GB for the engine. One mesh per row referenced by 2,275 nodes
is 4.7 MB — a factor of 300.

---

## Result — J4 and J5

**J4.** `tools/build_readme.py` regenerates the README's status block —
status line, stage table, the full closure scoreboard, the figure list and
the outstanding work — from `data/closures.yaml` and the tree.
`tests/test_readme.py` fails if it has drifted. The CI workflow
`.github/workflows/e3-engine-ci.yml` runs **the whole suite**, not a
hand-picked list: the only two files needing the geometry kernel declare it
with `pytest.importorskip("cadquery")` and skip themselves on a plain
runner.

**J5.** `figures/e3-drawing-pack.pdf`, six A3 sheets: GA, fan and booster,
HPC, combustor, HPT, LPT.

| | |
|---|---|
| Dimensions | 9, each with a source — 5 published, 2 derived, **2 assumed** |
| Assumed dimensions | parenthesised on the sheet and listed in every title block |
| Stations placed | **4 of 10** |
| Stations not drawn | 6, each with the reason printed on the GA |
| Sheets that state a gap | 3 — combustor, HPT, fan |

---

### Findings

155. **The first render put the entire fan off the page.** `ylim` was set
     to 46 cm, sized to the core annulus, while the fan tip is at 105.4 cm. The
     fan appeared as two horizontal lines clipped at the frame and read as a
     duct that ended in mid-air. Nothing raised an error: matplotlib clips
     silently and the figure looked finished. Fixed by taking the limits from
     the data and setting an equal aspect, which is also what makes the wall
     angles meaningful.

156. **The first render deleted the transition duct.** The LPT flowpath
     CSV carries `z` measured *from the HPT exit plane* — stated in its own
     header, and the one inter-module offset this project actually knows. The
     draft re-zeroed that column to the first row's `z` before plotting, the
     way it correctly does for the HPC, which subtracted 6.85 cm and butted the
     LPT vane straight onto the HPT exit. **The one join that is known was the
     one thrown away.** A convention applied twice without checking whether it
     was true twice.

157. **Two published lengths for the transition duct disagree by 10 %.**
     CR-168219 §5.5 prints an axial length of **7.62 cm**; the LPT section
     coordinates put the stage-1 vane leading edge at **6.85 cm** from the HPT
     exit plane. Difference 0.77 cm, 10 % of the duct. The sections are used
     here, because the LPT flowpath is drawn on that datum and mixing the two
     would place every LPT row 0.77 cm downstream of where its own coordinates
     say it is. Recorded, both kept, neither corrected. Unresolved: no source
     read so far says which plane the 7.62 cm is measured between.

158. **The fan module has no publishable meridional contour.** Three
     dimensioned radial stations exist — the rotor stacking axis (Fig 15,
     r 41.8–103.9 cm, the only one with an axial position), the fan inlet
     (Table IV, 210.8 cm tip, 0.342 radius ratio) and the booster inlet
     (Table IV, 133.8 cm tip, 0.782). No hub or casing line was ever printed
     against an axial coordinate. The figure draws the three bars and says so
     on its face, solid for the station whose axial position is published and
     dashed for the two placed only indicatively. This is a **source gap, not
     a modelling gap**: it goes to the A3 backlog and it is the same gap that
     leaves the fan→HPC offset unknown.

159. **The plot nearly published a second, contradictory axial layout of
     the same engine.** The first two drafts placed each module on its own
     datum and drew an arbitrary 14 cm hatched band at each unpublished
     join, on the reasoning that an invented offset is worse than a visible
     gap. That reasoning was sound and the conclusion was still wrong,
     because **the two offsets were not un-invented — they were already
     assumed elsewhere**. `app/turbofan/atlas/flowpath.js` has carried
     `HPC0 = 1.42 m` and `HPT0 = 2.68 m` since 2026-09-07, placed from the
     bearing spans and frame positions of CR-168219's whole-engine
     cross-section, with allowable ranges of 110–150 cm and 45–55 cm from
     `atlas-facts.md` A7. Two artefacts of one engine would have shipped
     with axial layouts 128 cm apart.

     The fault was not the gap. It was that **an assumption in use had no
     home in `data/`**, so a second consumer could not find it and made its
     own. Fixed by recording both offsets in
     `engine-flowpath.yaml → whole_engine_stitching.assumed_offsets` with
     their ranges, their source and a `consumers:` list, and by testing that
     the figure and `flowpath.js` place the engine identically. The figure
     now draws the whole engine on one axis at true scale, y = 0 at the fan
     rotor stacking axis, with each assumed offset dimensioned, labelled
     ASSUMED, and shown against the range it is allowed. Consistency rule 1
     — *one source of numbers* — applies to assumptions and not only to
     transcriptions, which is the part this project had not written down.

160. **On eleven of the twenty-four comparisons, E3's closure band is
     finer than the transcription can read — and on every first-flex mode
     it is.** `hpc-rotor-campbell.yaml`'s own `meta.reading_uncertainty`
     states the precision of reading these diagrams: half a minor division,
     ±0.05 kHz on a 0–6 kHz axis, ±0.1 on 0–12, ±0.25 on 0–22 and 0–26.
     Applied per point, that is ±14.3 % on stage 1's 350 Hz first flex,
     ±16.7 % on stage 3's 600 Hz, and better than ±3 % on the higher modes
     of the same diagrams. The closure asks for ±5 %. **So on 11 of 24
     points the comparison cannot come out either way**, and all ten
     first-flex modes are in that group: a perfect model and a 20 % wrong
     one would both read as "outside 5 %" or "inside" depending on where
     the pencil landed. This does not rescue the closure — among the 13
     points where 5 % *is* resolvable, 1 passes — but it does mean the
     headline "1 of 24" is measuring two different things at once. The
     figure marks the two groups differently for that reason.

161. **The figure was briefly plotting a quantity the closure does not
     use.** `BladeModel.modes(stiff, rpm, n)` takes `stiff` as a *beam
     axis* selector — `True` uses `i_root_axis`, `False` the weak axis —
     and it is the `rpm` argument, not `stiff`, that carries centrifugal
     stiffening. The first draft of `predicted_curve` read `stiff=True` as
     "with stiffening" and plotted the root-axis modes: 929 Hz against the
     405 Hz the closure compares on stage 1, a factor of 2.3. It rendered
     without complaint and looked like a Campbell diagram. Caught by
     reading the panel against the known numbers, not by a test. The fix
     is `stiff=False`, and a test now pins the plotted curve to the same
     value the comparison table holds.

162. **The published lines are drawn flat, and that is not a cosmetic
     disagreement — it changes which resonances the engine has.** The
     diagrams draw every mode line flat or gently drooping across the
     whole speed range; this project's model says stage 1's first flex
     rises from **405 Hz at rest to 624 Hz at 13,948 rpm, +54 %**.
     Counting engine-order crossings inside the HP operating range
     (12,303–13,948 rpm) against each: **4 crossings, and only 1 is picked
     by both.** The model finds a 3E crossing on stage 2's first flex and
     a 32E on stage 3's third flex that the flat lines do not; the flat
     lines put a 10E crossing on stage 7's first flex that the model does
     not. Three of the four resonances a designer would work from depend on
     which representation is right. Recorded as read; **this project does
     not know why the published lines are flat**, and the candidate
     explanations — that they are static frequencies plotted without
     stiffening, that the blades are shrouded or platform-damped in a way
     the beam model does not carry, or that the drooping is a thermal
     effect — are not distinguishable from the figures alone. Unresolved.

163. **The lofted tip caps stand proud of their own sections, worst on the
     fan at 3.01 mm.** G1 closes each blade with
     `Face.makeNSidedSurface`, which interpolates a surface across the
     boundary wire and is under no obligation to stay inside it. Measured
     across all 32 rows: the fan rotor's mesh reaches **104.20 cm against
     a 103.90 cm tip section**, HPC rotor 2 is 0.67 mm proud, most rows
     are under 0.2 mm, and **every LPT row is exact to 0.00 mm**. The
     bulge scales with the cap — the fan's tip section is a 28 cm chord on
     a 104 cm radius, the largest N-sided patch in the project, and the
     LPT tips are small and nearly flat. It is 0.29 % of the fan tip
     radius and it stays inside the 1 % volume band, so it never showed up
     in G1's own checks. It is still real geometry: **the render's
     outermost radius is not the aerodynamic tip radius**, and the file
     should not be measured for one. Recorded rather than trimmed away,
     because trimming the cap would change the volume that F2's mass
     roll-up was checked against.

164. **The render has no tip clearance, and the amount by which it misses
     is the same size as the clearance.** All 20 HPC rows sit on the
     published annulus walls to within 0.8 mm, which is the headline
     agreement between G1's solids and J1's flowpath — but Table XXII's
     sections are defined *on* those aerodynamic walls, so the blades
     touch the casing by construction. Stage D's clearance work gives a
     desired running clearance of **0.041 cm — 0.41 mm** on the HPT, the
     same order as the 0.0–0.8 mm residual here. So the sub-millimetre
     agreement is not evidence that the clearance is modelled; it is
     evidence that the geometry is the cold aerodynamic definition, with
     the clearance not yet applied. A viewer must not read tip clearance
     off this file.

165. **The render has an HPT with walls and no blades.** J1 draws the HPT
     annulus from Fig 3's five dimensioned stations, and Stage G1 has no
     HPT rows to put in it, because the HPT airfoil coordinates were never
     published — the reports give throat dimensions and aspect ratio and
     nothing to loft. The gap is left visible and labelled on the preview
     rather than filled with a plausible aerofoil, which is the same rule
     that leaves the combustor blank: its axial coordinates are
     undimensioned in Figs 1, 22 and 79. **Two of the engine's five
     bladed modules cannot be drawn from the public record**, and the
     picture says so.

166. **Four of the engine's ten gas-path stations can be placed; six
     cannot.** Building the general arrangement forced the question nothing
     else had: *where, in centimetres from a datum, is station 2?* Stations
     25 and 3 fall out of the HPC flowpath and are published. Stations 4
     and 45 are placeable only because unit J1 assumed the HPC-to-HPT
     offset, so they are drawn parenthesised — **a station number can
     inherit an assumption, and on this drawing two of the four do.** The
     other six have no published axial position at all: 1 and 2 are
     upstream of the fan stacking axis by an unstated amount, 13 is a
     stream rather than a plane, 21's booster station was never printed,
     and 5 and 8 sit aft of an 18-lobe mixer that is nowhere dimensioned.
     They are left off the sheet. A station drawn at a guessed position is
     worse than a station missing, because the number beside it looks
     measured.

167. **Three of the six sheets exist to say that something cannot be
     drawn.** The combustor sheet is deliberately empty — double annular,
     60 cups, 30 nozzles are published, and not one axial coordinate. The
     HPT sheet has five dimensioned stations and no airfoil, because the
     blade and vane coordinates were never printed. The fan sheet has three
     radial bars and no wall, for the reason in finding 158. Half the
     drawing pack is a record of what the public domain does not contain,
     and that is the honest proportion rather than a failure of the pack.

168. **A README claimed "37 tests" for months, and no test could fail.**
     The count was written when it was true and then rotted through nine
     stages and eight hundred test functions; the same paragraph said
     `build.py` "arrives with Stage C" long after it ran ten stages. The
     project asserts every published number against its source, and had
     never once done so for the numbers in its own front page. Fixed by
     generating the block that carries numbers and testing it for
     staleness — `tools/build_readme.py`, the same arrangement
     `tools/build_findings.py` has with `FINDINGS.md`. The test that now
     forbids a bare test count in the hand-written prose is the one that
     would have caught it.

169. **The post drafted a claim that had been true and had stopped being
     true.** It said the beam-model bias accounts for *"twenty of the
     project's twenty-one worst numbers"* — copied from unit I3, where it
     was correct against 98 ranked comparisons on 2026-09-08. By the time
     the post was written the ranking held 100 comparisons and the figure
     was **sixteen of twenty-one**: units J1 and J2 had each contributed an
     entry, and the Rotor 37 flow, an LPT stress concentration and the HPT
     bore disagreement had risen into that band. Nothing was wrong when it
     was written and nothing broke; a true sentence simply aged out from
     underneath. Caught by `tests/test_post.py`, which was written for
     exactly this and found it on its first run. The claim is corrected and
     the test now pins the number.

170. **A post that states its own test count cannot be tested without
     changing it.** The first draft printed an exact figure, and adding the
     tests that check the post moved it. The count is a side effect of
     writing tests, not a claim anyone reasons from, so the post states a
     **floor** — "over 850 test functions" — and the test asserts the floor
     holds. The findings count is kept exact by contrast, because findings
     are appended one at a time and deliberately: that number *is* a claim.
     The general rule this settles for the project: a number that moves as
     a side effect of routine work belongs in a generated block or as a
     bound, never as an exact figure in prose.
