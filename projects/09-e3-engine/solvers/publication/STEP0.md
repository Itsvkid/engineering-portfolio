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
