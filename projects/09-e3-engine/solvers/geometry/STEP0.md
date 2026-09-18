# Step 0 — geometry generation (G): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit G1 — solid blade rows, and one command that rebuilds everything

Stage G's closure: *`python build.py` on a clean clone reproduces
everything, and the generated mass matches F2.*

**The second half of that is partly gated and the gate is F2's, not G's.**
There is no basic-engine mass to match: F2 recorded (finding 112) that the
disc profiles are un-digitised, the casings and frames are figure-status,
and the 320 kg of sumps and drives has no printed geometry at all. What
*can* be matched — and is the right thing to match — is the **blade
volume**, because that is the one quantity the analysis and the CAD must
share exactly.

Stage G's first bullet says *PF-06 extended to arbitrary section stacks*.
PF-06 places its sections **planar** and applies the tangential offset "as
a straight tangential distance rather than conformally wrapped around the
annulus — valid because chord is small next to radius, **and stated here
because it stops being valid if that ratio isn't small**". On the E³ that
ratio is not small: the HPC stage-1 rotor carries a 10.1 cm chord at a
19.1 cm root radius, **chord/radius = 0.49**, and the fan is 0.44. PF-06's
own stated condition fails, so this unit does the conformal wrap —

    (x_axial, y_tangential) at radius r  ->  (x, r sin(y/r), r cos(y/r))

— which is the extension the bullet asks for.

The wrap is **volume-preserving exactly** when the tangential coordinate is
arc length, because the volume element (r dθ)(dx)(dr) is (dy)(dx)(dr). So
the CAD volume and Stage F2's trapezoidal integral of the same sections
must agree, and any disagreement is the CAD's discretisation, not physics.
That makes the volume a real test rather than a restatement.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Every row builds | 32 rows: fan, booster, 10 HPC rotors, 10 HPC stators, 10 LPT rows | **all of them, no exceptions** | a row that will not loft is a row whose sections are wrong; skipping it would hide that |
| Every solid is topologically valid | `BRepCheck_Analyzer` | **all of them** | an invalid solid's volume is meaningless — see finding 113 |
| CAD volume vs F2's integral | F2's trapezoid over the same sections | **±2 %** | the wrap is exactly volume-preserving; what is left is the polyhedral approximation of a curved section, and 78 points a section should do far better than 2 % |
| Blade-to-blade interference | one blade against a copy rotated by one pitch | **exactly zero**, every row | Stage G's sixth bullet |
| `build.py` | every solver module with a `__main__` | **all run, none fails** | Stage G's last bullet |
| **Generated engine mass vs F2** | — | — | **gated on F2, which is gated on the disc profiles** |

Not attempted, and why: discs (E2's finding 81 — no profiles), casings,
liner and dome (A3 figure-status), and the nacelle (PF-07's CST needs
Fig. 40, also figure-status). Those are four of Stage G's seven bullets
and every one of them is blocked on transcription, not on method.

---

## Unit G1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m geometry.blades`)

```
Stage G1: 32 blade rows generated from the validated sections

   row                  spool    n  sect    c/r      CAD m3       F2 m3   err %  valid
   fan-rotor               lp   32     7   0.44  1.0758e-03  1.0809e-03   -0.47   True
   booster-rotor           lp   56     5   0.13  3.0449e-05  3.0575e-05   -0.41   True
   hpc-rotor-1             hp   28    12   0.49  6.1535e-05  6.2035e-05   -0.81   True
   hpc-rotor-2             hp   38    12   0.25  1.5928e-05  1.6043e-05   -0.72   True
   ... (eighteen more HPC rows, -0.21 to -0.34 %)
   hpc-stator-10       static  140    12   0.08  4.6898e-07  4.7029e-07   -0.28   True
   lpt-stator-1        static   72     3   0.16  2.2417e-05  2.2521e-05   -0.46   True
   lpt-rotor-4             lp  156     3   0.07  1.0261e-05  1.0178e-05    0.81   True
   lpt-rotor-5             lp  110     3   0.09  1.7391e-05  1.7556e-05   -0.94   True

   32 rows: worst volume error 0.94 %

   blade-to-blade interference, one pitch apart:
      32 of 32 rows clear; overlapping: none
```

```
$ python build.py --no-geometry
   ...
   29 of 29 modules ran, 90 s total

$ python build.py --export        # adds unit G1's CAD: 35 STEP files, 132 MB
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Every row builds | **32 of 32** | all | pass |
| Every solid valid | **32 of 32** | all | pass |
| CAD volume vs F2 | worst **0.94 %**, mean 0.4 % | ±2 % | pass |
| Blade-to-blade interference | **zero on all 32** | exactly zero | pass |
| `build.py` | **29 of 29** modules, 90 s | none fails | pass |
| Generated engine mass vs F2 | not attempted | — | **gated on F2** |

### Findings

113. **OpenCASCADE cannot cap a non-planar wire, and it does not say so —
     it returns a shell and lets you take its volume.** Lofting the
     wrapped sections with `ThruSections` gives a shape that reports
     itself as a `Solid` with one shell, and whose volume is **exactly
     two-thirds of the truth**. The demonstration is a *flat rectangle*
     wrapped through **1.5°**: 162 faces unwrapped and closed, 160 faces
     wrapped and open — the two end caps are simply missing, because a
     section lying on a cylinder is not planar and `ThruSections` builds
     only planar caps. `Shell.Closed()` is `False` and `Volume()` on an
     open shell is meaningless, but nothing raises. The fix is to loft as
     a shell, cap both ends with `Face.makeNSidedSurface`, sew, and check
     `Closed()` before making the solid — after which the same rectangle
     returns its exact volume to five figures. **The first attempt at this
     unit read every blade 33 % light and every solid looked fine.**
114. **Two sections out of ninety-six had one fewer point than their
     neighbours, and that is enough to stop a loft.** LPT stator 5's tip
     section decimated to 92 edges where its hub and pitch sections gave
     93, because the appendix prints 95 coordinates for that section and
     96 for the others. `ThruSections` failed with
     `NCollection_DataMap::Find` — a message that names nothing. The cure
     is not to patch that row but to resample **every** section to the
     same number of arc-length-spaced points, split at the trailing edge
     so leading and trailing edges correspond between sections. That also
     absorbs the LPT appendix's **duplicated coordinates** (R1_10 prints
     the point at 5.552902, 13.819397, 0.146528 twice), which are
     zero-length edges OCC refuses. The transcription is left saying what
     the report says; the repair happens at the geometry.
115. **Thirty-two rows, every solid valid, and the CAD agrees with the
     analysis to 0.94 %.** The conformal wrap is exactly volume-preserving
     in arc-length coordinates, so this is a test of the CAD and not of
     the aerodynamics — and the residual behaves like what it is, a
     polyhedral approximation: the HPC rows with twelve sections and low
     chord-to-radius run −0.2 to −0.3 %, while the three-section LPT rows
     and the two highest chord-to-radius rows (HPC rotor 1 at 0.49, fan at
     0.44) run three times that. **The generated blade set is the same
     geometry Stage F weighed**, which is the only sense in which "the
     generated mass matches F2" can be met while F2's own total is gated.
116. **Not one blade in the engine touches its neighbour, and the check
     costs nothing.** Every row's solid was intersected with a copy of
     itself rotated by one pitch — 12.86° on the 28-blade HPC rotor 1 down
     to 2.31° on the 156-blade LPT rotor 4 — and every intersection is
     empty. It is the cheapest possible test of a blade count against a
     section chord, and it is the one that would have caught a
     transcription slip in either.
117. **Four of Stage G's seven bullets are blocked on transcription, not
     on method.** Discs need E2's un-digitised profiles; casings, liner
     and dome need A3's figure-status flowpaths; the nacelle needs Fig. 40
     for PF-07's CST fit. The machinery to build any of them is the same
     machinery that built the blades — sections, loft, cap, sew, check —
     and it is demonstrably working. What is missing is the numbers to
     feed it, which is the same gate E2, E3, E5 and F2 each hit.

---

## Unit G2 — the swept and leaned inner OGV

Stage C3's line: *Booster rows and inner OGV with the published sweep 60° /
lean 0–20°.*

**First, a correction to that line.** The sweep and lean are published for
the **inner OGV only**. `fan-design.yaml`'s `booster_rotor_airfoil` block
carries no sweep and no lean, and nothing else in the fan report gives the
booster one. G1 already builds the booster rotor on a radial stacking line,
and that is right rather than a shortcut. This unit is the inner OGV.

### What is published

Table VII p.92 gives the row completely: 64 vanes, length 11.61 cm, chord
9.25 cm at the root falling to 5.44 at the tip, stagger 18.40° → 21.53°,
camber 55.38° → 62.38°, tm/c 0.053 → 0.062. Section II.D adds the shape of
the stacking axis:

> curved in space, swept aft 60 degrees from radial, leaned
> circumferentially from 0 at the OD to 20 degrees at the ID with the
> pressure side facing the axis

and — the sentence that decides how the sections are placed —

> sections: on planes perpendicular to the swept and leaned axis

### What is not

The vane's **radial position**. Table VII gives a length, not a hub
radius. `app/turbofan/atlas/flowpath.js` has carried `rCoreHubAtOgv =
0.49 m` as an assumption; by unit J1's finding 159 that belongs in `data/`
where both artefacts can read it, and this unit puts it there rather than
making a second copy.

| Check | Band | Basis |
|---|---|---|
| Sections lie on planes normal to the stacking axis | every section's plane normal parallel to the local tangent, to **1e-9** | the report's own sentence; this is construction, not tolerance |
| Sweep | **60°** from radial, constant | the one number the sentence gives |
| Lean | **20° at the ID falling to 0° at the OD**, linear in radius | the sentence gives the two ends and calls the axis curved; linear is the reading, and it is stated |
| Volume against a trapezoidal integral along the axis | **±2 %** | G1's own band for the same check on 32 radial rows |
| Blade-to-blade interference at 64 vanes | **zero** | G1's rule; a swept and leaned vane is the one most likely to break it |
| Table VII's aspect ratio, reproduced from its own length and chords | reported, not banded | it reproduces on stage 1 to 0.2 % and does **not** on the other two rows — a property of the table, not of this geometry |

**Closes when** the vane builds as a valid solid with its sections on
planes normal to a 60°-swept, 20°-to-0°-leaned axis, the volume holds
inside 2 % of the trapezoidal integral, and 64 of them do not touch.

### Result — G2

Built on the plain reading STEP0 named: Table VII's 11.61 cm as the radial
span, 60° sweep, lean 20° → 0°.

| | |
|---|---|
| Sections on planes normal to the axis | **exact by construction** |
| Valid solid | **yes** |
| Blade-to-blade interference, 64 vanes | **zero** |
| Volume vs the trapezoidal integral | **−2.09 %** against a ±2 % band — **narrow miss** |
| Straight-axis control (same CAD, same integral) | **−0.015 %** |

**Closure: half.** Three of the four checks pass. The volume check misses
by 0.09 of a percentage point against a reference that finding 181 shows
does not apply to a curved stacking axis.

### Findings

180. **The plan line conflated two rows: the booster has no published
     sweep or lean.** *(Confirmed 2026-09-10 from the other direction:
     CR-165148 Appendix D was transcribed and states it outright — one Z
     for the whole span, "the booster rotor is stacked on a radial line:
     no sweep, no lean". This finding was reasoned from the absence of the
     data; the appendix asserts it positively. The test that guarded it
     was rewritten at the same time, because it had been checking that the
     WORDS "sweep" and "lean" did not appear in the booster block —
     absence-of-mention standing in for absence-of-data — and that proxy
     broke the moment a note affirming the finding was added.)* Stage C3 asks for *booster rows and inner OGV with
     the published sweep 60° / lean 0–20°*. Section II.D gives those two
     angles to the **inner OGV** and to nothing else;
     `booster_rotor_airfoil` carries neither, and no other block in the fan
     report gives the booster one. G1 has been building the booster on a
     radial stacking line since Stage G, and that is **correct rather than
     a shortcut** — the work-plan note that called it a gap was wrong, and
     is corrected. One row needed building, not two.

181. **A trapezoidal `∫A·ds` is the wrong reference for a curved stacking
     axis, and the error is 6 % on this vane.** The CAD came out 2.09 %
     below the integral, just outside the ±2 % band G1 uses for its
     thirty-two radially stacked rows. Section count was not the cause —
     5 to 25 sections all land within 0.17 % of each other. The cause was
     found by straightening the axis: with **constant** sweep and no lean
     the axis is straight, and the same CAD against the same integral
     agrees to **−0.015 %**. Restore the lean and it is −6.12 % with no
     sweep, −2.09 % with 60°. The gap is entirely the axis curvature, and
     it is a Pappus term the integral omits: a section swept along a
     curved path sweeps more volume on the outside of the bend than on the
     inside. **The reference is wrong here, not the CAD** — and the band
     stands as a miss because it was stated before the run.

182. **Two independent lines say Table VII's "length" is measured along
     the swept axis, not radially.** Neither is proof, and together they
     are hard to ignore. *One:* the fan report's Appendix A prints an
     aspect ratio of **0.83** for this row where Table VII prints 1.39.
     Reading 11.61 cm as the length along a 60°-swept axis gives a radial
     span of 5.81 cm and an aspect ratio of **0.790** on the mean chord —
     within 5 % of Appendix A. *Two:* the atlas's own station spacing
     leaves about **10 cm** of core duct between the inner OGV and the
     island exit vanes. The radial-span reading builds a vane **22.6 cm**
     long axially, which does not fit; the along-axis reading builds one
     **12.6 cm** long, which nearly does. The plain reading of "length" is
     still the radial span and STEP0 named it before the run, so the unit
     is built and closed on that. `LENGTH_IS_ALONG_AXIS` builds the other.

183. **The vane overhangs the hub by 5.7 cm on either reading, so it must
     be trimmed by the endwalls.** Its sections sit on planes 60° from
     radial, and a section on such a plane reaches about `chord/2 × sin 60°`
     in radius either side of its own axis point — 4 cm at the 9.25 cm
     root chord. The lofted vane spans **43.3 to 60.6 cm** in radius
     against an assumed annulus of 49.0 to 60.6. This is not an error in
     the loft; it is what a steeply swept vane with normal-plane sections
     does, and the real part is cut by the hub and casing. **Unit C4-2
     found exactly this on Rotor 37** — finding 134, where the blade is
     trimmed by the casing rather than stopping short of it. Trimming here
     needs the core-duct walls, and those are assumed rather than
     published, so it is left undone and stated.


---

## Unit G3 — the whole engine as one STEP assembly

Unit G1 wrote **36 STEP files**: one per blade row, plus a compound per
spool. That is a parts bin. Every row sits at its own local origin, so
opening all 36 in a CAD system stacks thirty-two blades on top of each
other at zero — which is exactly the failure mode this unit exists to
avoid, and the reason it is a unit at all rather than a flag on `export()`.

What is being built is the **assembly**: every row at its true axial
station on unit J1's engine axis, at full blade count, in one file with a
product structure a reader can expand, rotate and measure.

**Two things make this more than a `translate()` call.**

*One, the axial layout is not free.* Two of the three joins between module
datums are **assumed** — the fan stacking axis to HPC rotor 1, and the HPC
OGV trailing edge across the diffuser and combustor to HPT vane 1. They
were corrected on 2026-09-10 to **103.4 cm** and **25.3 cm**, whose sum is
constrained by CR-159584 Table I p.6's published turbomachinery length of
**318.0 cm**. This unit reads them through `publication.meridional.layout()`
and keeps no copy (unit J1, finding 159), and the assembled length is then
checked back against that published 318.0 cm. The offsets were calibrated
on it, so this is a closure check and not a discovery — but a closure check
that runs on the *built geometry* rather than on the CSV arithmetic, which
is the first time that has been possible.

*Two, provenance has to survive the export.* A STEP file outlives the page
that explains it, the same argument unit J3 makes for `asset.extras`. So
every node's **name carries its own status** — `PUBLISHED`, `DERIVED` or
`ASSUMED` — and the two assumed offsets are named in the module nodes that
depend on them. A reader who opens the file without this repository must
still be able to tell which surfaces NASA printed and which this project
supposed.

### The bands, before the run

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Assembled length, fan front flange to LPT rotor-5 TE | **318.0 cm**, CR-159584 Table I p.6 | **±2.0 cm** | the two offsets were calibrated on this sum, so the residual is only the difference between the CSV's R5 trailing-edge z and where the *lofted* blade's own trailing edge lands, hub against tip |
| Blade-to-blade interference, within a row, at the assembled position | zero | **exactly zero**, all 32 rows | G1's check, re-run on the placed rows — translation along X and rotation about X commute, so a change here would mean the placement is not a rigid motion |
| **Row-to-row axial clearance** | — | **strictly positive, every consecutive pair** | new to this unit and the only check the assembly enables that G1 could not make. Two rows whose axial extents do not overlap cannot interfere at any relative angular position, so a positive gap is a *proof* and not a sample. A negative gap means the layout is wrong |
| Total blade volume | sum of F2's trapezoidal integrals × blade count | **±2 %** per row, G1's band | the assembly must not change a volume; if it does, a placement is scaling something |
| Re-imported structure | one root product, module sub-assemblies, 32 row nodes | **it must re-import as a tree**, not as N solids at the origin | the stated failure mode. Checked by reading the file back with `STEPCAFControl_Reader` |

### What is deliberately left out

- **The HPT's two stages of airfoils.** The E³ never published HPT blade
  coordinates — Table IV prints an aspect ratio and a throat, which is what
  unit 14 built a mean-line from, and nothing more. The HPT *annulus* is
  published (Fig 3, five dimensioned stations) and is included, so the file
  carries a visible, labelled gap where the HP turbine's blading is.
- **The combustor.** Its axial coordinates are undimensioned in Figs 1, 22
  and 79 (unit J3, finding 165). Its *length* is published — CR-135444
  Table 65 p.239, 17.78 cm — and is already inside the 25.3 cm offset, so
  the space it occupies is right and its geometry is absent.
- **The fan annulus.** Three dimensioned radial stations and one axial
  position is not a contour (unit J1, finding 158). The fan rotor blade is
  built; no wall is drawn around it.
- **Discs, shafts, casings, frames, sumps, nacelle.** Four of Stage G's
  seven bullets, all blocked on transcription (G1's note above).
- **Tip clearance.** Table XXII's sections are defined *on* the walls, so
  the blades touch the casing by construction (unit J3, finding 164). The
  file is the cold aerodynamic definition; it does not model a running gap.

## Unit G3 after the run — nothing above was edited

### Results, 2026-09-17 (`cd solvers && python -m geometry.assembly --export`)

| Check | Band | Result | |
|---|---|---|---|
| Assembled length, fan front flange to LPT R5 TE | ±2.0 cm on 318.0 | **318.08 cm, +0.08** | MET |
| Blade-to-blade, within a row, placed | exactly zero, 32 rows | **32 of 32 clear** | MET |
| Row-to-row axial clearance | strictly positive, 31 pairs | **tightest 7.5 mm**, none negative | MET |
| Total blade volume, 2,890 blades | ±2 % per row | **−0.41 % overall, worst row 0.94 %** | MET |
| Re-imported structure | a tree, not loose solids | **1 root, 37 assemblies, 2,932 instances** | MET |

`exports/e3-engine-assembly.step`, **73.1 MB**, AP214. The file carries
**32 `MANIFOLD_SOLID_BREP` and 6 `SHELL_BASED_SURFACE_MODEL`** against
**2,932 `NEXT_ASSEMBLY_USAGE_OCCURRENCE`** — one representation per row,
instanced round the annulus, which is the only reason full blade counts
are affordable at all. 19,692 faces in the file; a system that expanded
every instance would materialise 2,890 solids and about 2.5 million faces,
so the file is small and the *import* may not be.

`figures/e3-assembly-meridional.png` draws the assembly from the solids.
Radius is invariant under rotation about the engine axis, so one instance
per row carries the whole annulus and the figure is the assembly rather
than a sample of it.

### Findings

221. **A positive axial gap is a proof and a boolean is a sample, and the
     assembly is the first artefact that could tell the difference.** Unit
     G1 could only ask whether a blade clears its own neighbour one pitch
     away, because every row sat at its own origin. Placed, the question
     becomes whether row *n* clears row *n+1*, and that one has a cheap
     exact answer: if two rows' axial extents do not overlap they cannot
     touch at **any** relative angular position, for any blade of either.
     All 31 consecutive pairs are clear, tightest **7.5 mm between HPC
     stator 4 and rotor 5**, and the HPC's front stages hold 7.5–8.3 mm
     while the LPT runs 13–18. No boolean was needed and none would have
     been as strong — a boolean at one relative angle proves nothing about
     the other 359.

222. **The compressor has 21 bladed rows and this project has built 20 —
     the IGV has never reached the section builder, and the reason is a
     column heading.** Table XXII prints every rotor and stator as
     β₁\*, β₂\*, camber and stagger, and prints the **IGV as a 65-series
     design lift coefficient** — `cl0` 0.08 at the hub to 0.80 at midspan,
     with stagger, thickness and chord but **no metal angles**.
     `blading.sections.all_sections` walks the `rotors` and `stators`
     blocks and stops, so the row has been quietly absent from unit 12's
     section reconstruction, G1's 32 rows, J3's glTF and now this
     assembly. The block itself is transcribed and correct; the gap is that
     nothing consumes it. Building it needs a `cl0`-to-camber rule —
     θ ≈ 25–27° per unit C_l0 for the 65-series — which would be the only
     **invented** camber in an engine otherwise built from printed angles,
     so it is left out and named rather than added. This is the same class
     of error as finding 220's stale sentence: the absence was true, and
     nothing was structured to ask about it.

223. **Two of the 32 rows are placed on an assumption that nothing checks,
     and it is worth 9.5 cm.** Every other row's station comes from a
     printed table — the HPC rows from `hpc-flowpath.csv`'s leading edges,
     the LPT rows from their own transcribed z. The fan is placed by
     putting its section's **x = 0, its leading edge**, on Fig 15's
     stacking-axis Z, which asserts that a fan blade stacks at its leading
     edge. It does not; it stacks near its centroid. The fan's axial extent
     is **19.07 cm**, so mid-chord stacking would move the row **9.54 cm
     forward** — and the booster, which is placed at the fan row's
     downstream end because no table gives its station at all, would move
     with it. The 318.0 cm closure does not catch this: it is measured from
     the fan **front flange**, which is its own assumption at −32.5 cm.
     So the front of the engine is the one place where the layout is
     unfalsifiable, and it is exactly where the layout looks most settled.
     Left as unit J3 placed it, because the STEP file and the glTF must not
     describe two different engines (unit J1, finding 159) — the correction
     belongs in one change across both.

224. **The tightest gap in the engine is 0.0 mm and it is the one that
     means nothing.** The fan-to-booster gap comes out exactly zero, and
     that is not a clearance result: the booster is *defined* as sitting at
     the fan row's downstream end, so the check is asking an assumption to
     confirm itself. A pass and a fail would look identical. The number to
     report is the **second** tightest, 7.5 mm, which is a real gap between
     two rows whose stations came from a table — and the rule generalises:
     in any assembly, a clearance between two parts placed by one another
     is not a measurement.

225. **The HPT has walls and no blades and the fan has a blade and no
     wall, and both gaps are the public record rather than the work.** The
     HPT annulus is dimensioned at five stations (Fig 3) and its airfoils
     were never published — Table IV gives an aspect ratio and a throat,
     which is what unit 14 built a mean-line from and is not a section. The
     fan is the reverse: 23 printed sections (Appendix B) and three
     dimensioned radial stations that are not a contour (unit J1, finding
     158). Drawing either missing half would take one plausible assumption
     and would make the file look complete. Both are left visible, and the
     meridional figure labels them, because an assembly that shows what the
     source does not contain is worth more than one that does not.


## Unit G4 — the fan and booster onto their printed sections

`blades.py` lofted the fan and the booster from the **seven- and
five-station read-offs of Fig 41 and Fig 52**, while
`tools/export_atlas_sections.py` fed the atlas on the site from
**Appendix B's 23 printed stations and Appendix D's 14**. The data file has
said `superseded_by: fan_rotor_airfoil.appendix_b` since unit 15b
transcribed them. So the project has contained **two different fan blades**:
the table's on the website, and the read-off's in G1's volumes, F2's masses,
G3's STEP assembly, J3's glTF, J7's site cutaway and E3's frequency model.
That is finding 159's failure in the form it predicted.

This unit moves every consumer onto the appendices. The read-off blocks stay
in the data file with their `superseded_by:` intact, because unit 15b's
finding is about what they cost and rests on them.

**What is expected to move, and why.** The read-off is wrong three ways, and
the third is the one nobody had counted:

1. angles — **+5.82° of stagger at the hub**, +3.14° on the mean, camber up
   to +4.25° (`read_off_error_vs_appendix_b`);
2. chord — 1.2–2.8 % low;
3. **span** — the read-off runs 41.757 → 103.901 cm, the stacking-axis box
   from Fig 15. Appendix B runs **36.067 → 105.410 cm**, which is the
   annulus: 36.067 against a published inlet hub of 36.047 and 105.410
   against a published tip of 105.4. The blade was **7.2 cm short**, 10 % of
   its own span, and all of it at the root where the sections are thickest.

### Bands, before the run

| # | Check | Band | Where it stands now |
|---|---|---|---|
| 1 | Fan blade mass, Ti-6Al-4V ρ 4430 | **7.27 kg ±15 %** (6.18–8.36), CR-165148 Table VI p.74 | **4.766 kg, −34.4 %** |
| 2 | Booster blade mass | **0.28 kg ±20 %** (0.224–0.336), same table | **0.135 kg, −51.8 %** |
| 3 | Lofted solid against the trapezoidal integral of its own sections | G1's **±2 %** per row | fan −0.47 %, booster −0.41 % |
| 4 | G3 assembled length | **318.0 ±2.0 cm**, unchanged | 318.08 |

Band 1 is the point of the unit. The published per-blade mass is an
**independent** number — it is not what the sections were transcribed from —
so it is the first check in this project able to say whether the airfoil the
CAD builds is the airfoil the engine had. A −34 % blade is not a tolerance
question; if the appendices are the right sections, most of that gap closes,
and if it does not close the section construction is wrong in a way the
angles never showed.

Bands 3 and 4 are stated because *nothing moved* is only a result if it was
a prediction first. Band 3 is a CAD check — the loft against the integral of
the same sections — so correcting the sections should leave it where it is,
or improve it, since 23 stations follow the twist inflection at 75 % span
that seven cannot carry.

Not attempted: the fan's axial placement (finding 223), which is a separate
assumption with its own range and belongs in its own unit; and the IGV
(finding 222), which has no printed metal angles.

## Unit G4 after the run — nothing above was edited

### Results, 2026-09-18 (`cd solvers && python -m geometry.assembly --export`)

| # | Check | Band | Before | After | |
|---|---|---|---|---|---|
| 1 | Fan blade mass | 7.27 kg ±15 % | 4.766 kg, −34.4 % | **5.543 kg, −23.8 %** | **MISSED** |
| 2 | Booster blade mass | 0.28 kg ±20 % | 0.135 kg, −51.8 % | **0.135 kg, −51.9 %** | **MISSED** |
| 3 | Loft against its own integral | ±2 % per row | fan −0.47, booster −0.41 | **fan −0.325, booster −0.226**; whole engine −0.32 | MET |
| 4 | Assembled length | 318.0 ±2.0 cm | 318.08 | **318.08** | MET |

`exports/e3-engine-assembly.step` rebuilt: **79.9 MB** against 73.1, 2,890
blades, re-imports as 1 root, 37 assemblies, 2,932 instances. All 31
row-to-row gaps still positive, tightest still 7.50 mm, blade-to-blade
interference still zero on 32 of 32 rows.

**Two of the four bands were missed and the model is not what was wrong.**
Band 1 moved the right way and stopped less than half way. Band 2 did not
move at all. Stating them in advance is what makes the next paragraph
available, because a mass that is 24 % light and a mass that is 52 % light,
one of which just changed and one of which did not, is a far more specific
piece of evidence than either number alone.

### Findings

226. **The read-off was radially short by 7.2 cm, and the span error was
     worth more than every angle error put together.** The three known
     defects of the seven-station read-off were angular — stagger, camber,
     chord. The one nobody had counted is that it spans **41.757 →
     103.901 cm**, which is Fig 15's *stacking-axis box*, while Appendix B
     spans **36.067 → 105.410 cm**, which is the *annulus* — and the
     appendix's own end rows prove it, landing on a published inlet hub of
     36.047 and a published tip of 105.4. The blade was missing **10 % of
     its span, all of it at the root**, where the sections are thickest and
     the chord shortest: that is where blade area is greatest per unit
     radius. Correcting the sections moved the fan's volume **+16.3 %**, and
     most of it came from the two ends rather than from the angles. A box
     printed on a figure is not the same object as the blade, and the two
     were read as if they were.

227. **A published per-blade mass cannot check an airfoil loft, and the
     booster is the control that proves it.** The fan's blade is 23.8 %
     light after the correction and the booster's is 51.9 % light — but the
     booster's geometry barely moved (its read-off spanned 52.32 → 66.90 cm
     against the appendix's 52.07 → 66.88, and its angle errors are small),
     so its deficit **cannot be the sections**, and it was the same before
     the fix and after it. What the loft does not contain is what the
     published number does: the dovetail, the shank below the flowpath, and
     on the fan the part-span shroud. Table VI's 7.27 kg is a *blade*, and
     `blades.py` builds an *airfoil*. Bands 1 and 2 were mis-specified by
     me, not failed by the model — and the mis-specification was worth
     making, because the pair of numbers localises the missing mass to the
     root far better than either one does alone: the smaller blade, whose
     root is proportionally larger, is missing proportionally more. The
     honest comparison needs either the root modelled or a published root
     allowance, and CR-165148 prints neither. Restated for whoever closes
     it: **the airfoil loft is checkable against the published blade mass
     only as a lower bound, and the bound is met — 5.543 < 7.27, 0.135 <
     0.28.**
