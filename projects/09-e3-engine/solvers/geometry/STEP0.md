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

---

## Unit G5 — the camber split, the last assumption the appendix makes unnecessary

Unit G4 put the fan and booster onto their printed section tables and left
one thing behind. `mechanical.blade_frequency._built_sections` still builds
each section's metal angles from camber and stagger by **splitting the
camber symmetrically**:

    b1 = stagger + camber/2      b2 = stagger - camber/2

which forces the maximum camber to mid-chord on every section of every
blade. **Appendices B and D print β\*_LE and β\*_TE directly**, so the
split is an assumption the tables make unnecessary — and it is an
assumption the tables also *contradict*: `test_the_fan_sections_are_not_
circular_arcs_and_the_booster_nearly_is` already measures the fan's
departure at **1.85° rms, changing sign hub to tip**, against the
booster's **0.61°**.

`blading.sections.section(chord, β1, β2, stagger, …)` already does this
correctly for all 252 HPC sections: it solves the double-circular-arc join
so the section reproduces β₁\*, β₂\* **and** the printed stagger, with the
join position `f` as an output rather than a constant. The fan and booster
have been calling the same function with a fabricated pair of angles. This
unit deletes the fabrication.

**What this is not.** Unit 15b's 5.08° rms camber miss belongs to
`blading/fan_blade.py` — unit 15's *designed* fan blade, which derives
camber from the aerodynamics and never reads the appendix. This fix does
not touch that solver and must not be expected to move that number.

### The bands, before the run

| Check | Band | Basis |
|---|---|---|
| **f, the max-camber position, fan** | **forward inboard (f < 0.5), aft outboard (f > 0.5)**, crossing near mid-span | the appendix's own `stagger − (β\*_LE+β\*_TE)/2` changes sign hub to tip; a symmetric split can only ever give 0.5 |
| **f, booster** | **\|f − 0.5\| < 0.10 at every station** | 0.61° rms departure — "nearly a circular arc". **The booster is the control**: if it moves as much as the fan, the change is doing something other than what it claims |
| Every section still builds | **23 + 14, no `None`** | `camber_line` refuses `f` outside 0.02–0.98, and a transonic tip section at 6.2° of camber is where that would bite |
| Stagger, as built | **exactly unchanged** | stagger is a separate argument to `section()`; if it moves, the fix has altered something it must not |
| Fan blade volume vs F2's integral | stays inside G1's **±2 %**, and I predict the *change* is **under 2 %** | chord and the thickness law are untouched; only the camber line's arc length changes, and section area ≈ ∫t·ds |
| Booster volume | **changes by under 0.5 %** | the control |
| Published-mass bound (finding 227) | **still a lower bound**: fan < 7.27 kg, booster < 0.28 kg | an airfoil loft against a blade with a dovetail, a shank and a shroud |
| Booster first flex | **inside ±3 % of 250 Hz** | it is 250.68 now and the control should barely move |
| Fan first flex | **no band on the absolute** — finding 83's brackets overlap and resolve nothing. Required: the free bracket still contains 80 Hz | |
| G3 assembled length | **318.08 cm, unchanged to 0.01** | the fan is not in the 318.0 cm chain |
| G3 interference | **zero, all 32 rows** | chord and count are unchanged, so a change here would be the camber line alone |
| G3 row-to-row clearance | **all 31 gaps positive** | |

### What the atlas can and cannot follow

`tools/export_atlas_sections.py` emits five columns — radius, chord,
camber, stagger, tm/c — and cannot carry β\*_LE and β\*_TE, so the export
is extended here to carry them. **The atlas's own camber line is a
different family and always has been**: `geometry.js:airfoilSection` uses a
14-point *parabolic* line, `yc = tan(θ/2)·x(1−x)`, whose maximum is at
mid-chord by construction, where the solvers use a 400-point double
circular arc. That is a declared fidelity difference in a viewer, not the
two-different-tables defect unit G4 removed, and this unit does not create
it. The export is extended so the columns exist and the difference is a
recorded choice rather than a data gap.

## Unit G5 after the run — nothing above was edited

### Results, 2026-09-18 (`cd solvers && python -m geometry.assembly --export`)

| Check | Band | Result | |
|---|---|---|---|
| f, fan | forward inboard, aft outboard, crossing near mid-span | **0.479 → 0.81**, crosses 0.5 at **42.7 %** span; inboard f oscillates 0.48–0.54 rather than sitting below 0.5 | **PARTIAL** |
| f, booster | \|f − 0.5\| < 0.10 every station | **0.411 – 0.513**, worst departure **0.089** | MET |
| Every section builds | 23 + 14, no `None` | **all 37**, none outside the arc family | MET |
| Stagger as built | exactly unchanged | unchanged — it is a separate argument | MET |
| Fan volume vs F2 | inside ±2 %, change under 2 % | **−0.658 %** (was −0.325); change **0.33 points** | MET |
| Booster volume | change under 0.5 % | **−0.239 %** (was −0.226); change **0.013 points** | MET |
| Published-mass bound | fan < 7.27, booster < 0.28 | **5.561 < 7.272**, **0.135 < 0.284** | MET |
| Booster first flex | ±3 % of 250 Hz | **249.81 Hz, −0.07 %** | MET |
| Fan first flex | free bracket contains 80 Hz | **36.02 – 107.48**, contains 80 | MET |
| G3 assembled length | 318.08 cm unchanged | **318.08** | MET |
| G3 interference | zero, 32 rows | **zero** | MET |
| G3 row-to-row clearance | all 31 positive | **all positive**, tightest 7.50 mm | MET |

Engine total volume **−0.52 %** against F2 (was −0.32), worst row 0.94 %,
inside G1's ±2 %. `exports/e3-engine-assembly.step` 79.9 MB, 1 root /
37 assemblies / 2,932 instances, unchanged.

### Findings

236. **The booster went back inside its bracket, and the converse test
     written for exactly that fired on the very next change.** Unit G4 left
     the booster at 250.68 Hz against a published 250 with the published
     value 0.68 Hz *below* the twist bracket's soft end, and finding 82 was
     restated around the number rather than the bracket. The test kept the
     old claim as a **converse** — `soft > published` — so that a change
     moving it back would be visible. Building the sections from the
     printed metal angles gives **249.81 Hz, −0.07 %**, and the published
     value is strictly inside the bracket again. Finding 82's original form
     is restored at a quarter of its original error, and the mechanism that
     caught it is worth more than the number: **a withdrawn claim asserted
     as its own converse is the cheapest way to notice it coming back.**
237. **The fan is a mid-loaded section inboard and a strongly aft-loaded
     one outboard, and a symmetric split could never have said so.** The
     max-camber position runs **0.48 at the flowpath hub, 0.48–0.54 through
     the inner half, then climbs to 0.81 at 90 % span** and eases to 0.79
     at the tip. A symmetric camber split returns 0.5 everywhere by
     construction. The outboard half is the interesting part: a transonic
     section wants its shock aft, and 0.81 is further aft than the E³'s own
     HPC rotors (0.55, unit 12). **The band is recorded as PARTIAL, not
     met**: step 0 predicted f < 0.5 through the inboard half and the fan
     wanders either side of mid-chord there instead. The booster is the
     control and behaves: 0.411–0.513, never more than 0.089 from
     mid-chord, which is what "modified circular arc" should look like.
238. **The 3 mm tip-cap bulge was coarse section spacing, not the capping
     call.** Finding 163 recorded the fan's lofted tip cap standing 3.0 mm
     proud of its own tip section and attributed it to
     `makeNSidedSurface` interpolating across the boundary wire — the fan
     being the largest N-sided patch in the project. On Appendix B's 23
     sections it is **0.14 mm**, a factor of 21, with no change to the
     capping code at all: the last loft interval fell from 12.4 cm to
     1.5 cm, so the ruled surface arrives at the tip almost parallel to the
     cap and there is nothing left for the cap to interpolate across.
     Finding 163's mechanism was right and its cause was wrong, and the
     consequence is practical — **the fix for a bulging cap is sections,
     not a tolerance.** The fan's mesh tip now lands on the report's own
     published tip radius of 105.4 cm to 0.02 %, so the check that used to
     be pinned at a remembered 104.2 is now against a published number.
239. **Three bands and a pinned tuple were calibrated on a blade that was
     10 % short, and they failed on the correction rather than on an
     error.** The fan dovetail's implied flank count, the released-blade
     airfoil term, the mesh tip radius and the largest vertex count all
     moved when unit G4 gave the fan its missing root, and `POST.md`'s
     `(18, 44, 62)` failed on an *improvement* — a disagreement moved
     inside 1 %. Each is rebanded on what the comparison can actually
     support rather than widened until it passes: the crush reading keeps
     the **contrast** between fan and booster (1.79 against 0.98, a factor
     of 1.83) and drops the claim to a tenth of a flank, because only
     `r_cg` in that chain is ours and unit G4 moved it 4.4 %; the released
     blade keeps the **whole-blade** term, which is printed and has stayed
     seventy-odd tonnes across every geometry (76 → 72.75), and bands the
     **ratio** 0.70–0.80 that the release-plane argument in 33.94 / CS-E
     810 actually turns on. The two exact pins — the tuple and the 10,886
     vertex count — are finding 170's rule broken twice more in files that
     had already been fixed once, and both become floors.
240. **Whether Appendix B's two end stations are airfoil or manufacturing
     stock is worth 16 % of the fan blade, and it is not closed.** The
     0 %–100 % band spans the stacking-axis box, 41.757 → 103.901 cm; the
     printed table adds a −9 % row at 36.067 and a 102.5 % row at 105.410.
     Building only 0–100 % reproduces the superseded read-off almost
     exactly — mass 4.752 against 4.788 kg, r_cg 70.75 against 70.15 —
     while all 23 rows give **5.561 kg and 67.04 cm**. Two lines favour the
     full span: the end rows land on **published flowpath radii** (36.047
     and 105.4), and Fig 15 plots chord against radius **out to 105 cm**,
     beyond the box. One line looked like it favoured the short span and
     does not survive inspection: the printed aspect ratios reproduce from
     the 0–100 % rows almost exactly (fan 2.605 against 2.597, booster
     **2.090 against 2.09**) and not from all of them (2.899, 2.192) —
     but the reports compute aspect ratio on their own box height, so that
     agreement is **circular** and is evidence about the AR convention
     rather than about the airfoil. Recorded as the size of an open
     question, because every band rebanded in finding 239 rests on it.

---

## Unit G2b — the curved-axis reference integral · step 0, 2026-09-18

Written **before** `pappus_volume()` existed.

### The question

G2 is half closed on a 0.09 of a point. The vane's CAD came out **2.09 %**
below `trapezoid_volume()` against a 2 % band, and finding 181 already
localised it: straighten the stacking axis and the same CAD against the
same integral agrees to **−0.015 %**; restore the lean and it is −6.12 %
with no sweep and −2.09 % with 60°. **The reference is what does not
apply, not the CAD.**

∫A·ds is the volume of a prism swept along a *straight* path. On a curved
path the material on the concave side travels a shorter distance than the
material on the convex side, and the two only cancel if the path runs
through the section's **centroid**. It does not: `_section_2d` builds each
section from its leading edge, so the stacking axis carries a centroid
offset of roughly half a chord — four centimetres on a vane whose lean
bends the axis over an eleven-centimetre span.

### The restated band

Pappus's second theorem in its differential form. A point offset by **d**
from the axis in the normal plane sweeps an arc length ds·(1 − κ **d**·**N̂**),
so

    V = ∫ A(s) · (1 − c̄(s)·dT̂/ds) ds

with c̄ the section centroid taken from the axis point and dT̂/ds the
curvature vector. Where the axis is straight, dT̂/ds = 0 and this is the
old integral exactly, so **no straight-axis row changes and no band
elsewhere moves.**

| # | Band | Why |
|---|---|---|
| 1 | the Pappus integral reproduces an **exact** answer before it touches the OGV: a circular section swept round a circle with the stacking axis offset from its centroid gives 2π(R−e)A, to **1 part in 10⁶** | METHOD.md step 0 — a correction that improves an agreement is only worth what an independent exact case says it is. This is the same discipline C4-1 used on the shock tube |
| 2 | with a **straight** axis the Pappus integral equals the trapezoidal one to **1 part in 10⁹** | it must not disturb the 31 rows already checked |
| 3 | the OGV's CAD against the Pappus integral is inside the project's standing **2 %** geometry band | the same band every other row is judged against, deliberately not tightened to flatter this unit |
| 4 | the Pappus term cuts the residual by at least a **factor of 2** against the trapezoidal reference | this is the actual claim. A band of 2 % alone would be passed by a correction that did nothing useful |
| 5 | the residual's **sign** is explained: the centroid lies on the concave side, so c̄·dT̂/ds > 0 and the corrected reference is **smaller** than ∫A ds | finding 181 measured a CAD *below* the trapezoidal integral. If the sign comes out the other way the term is not what is missing |

### Estimate before computing

The centroid sits about 0.45 of a chord aft of the leading edge, so
c̄ ≈ 4 cm at the root falling to 2.4 at the tip; the lean turns the axis
about 20° over 11.6 cm, so κ ≈ 0.35 rad / 0.116 m ≈ 3 m⁻¹. The product is
of order 0.012 to 0.12 depending on how much of c̄ lies along the principal
normal — which brackets the measured 2.09 % comfortably and is the reason
to compute it rather than assert it.

### Not attempted

Re-lofting the vane, changing its sections, or changing the assumed hub
radius. Nothing about the CAD moves in this unit; only what it is compared
against.

## Unit G2b — after the run · 2026-09-18

Nothing above was edited.

| # | Band | Result | Verdict |
|---|---|---|---|
| 1 | the torus case to 1 part in 10⁶ | **2.0 × 10⁻⁶** against the exact circle at n = 721; against the exact answer for the 360-gon actually integrated it converges **first order** — 1.0e-4, 5.3e-5, 2.7e-5, 1.4e-5, **6.9e-6** at n = 5761 | **miss — finding 252** |
| 2 | straight axis, both integrals identical to 1 part in 10⁹ | **1.6 × 10⁻¹⁵** | **pass** |
| 3 | CAD against the Pappus integral inside 2 % | **+0.0064 / +0.0253 / +0.0429 %** at 9 / 13 / 21 span sections | **pass — G2 closes** |
| 4 | the term cuts the residual by at least 2× | **327× / 83× / 48×** at the same three resolutions — 2.11 % → 0.006–0.043 % | **pass** |
| 5 | the sign is explained: the corrected reference is smaller | Pappus **−2.11 %** against trapezoidal, so c̄·dT̂/ds > 0 and the centroid is on the concave side | **pass** |

**Grid independence** (METHOD.md step 6), on both sides. The Pappus
integral at n = 51 … 1601 halves its step each refinement — first order —
with a Richardson limit of **4.76075 × 10⁻⁵ m³**; the CAD at 9, 13 and 21
span sections rises 4.76166 → 4.76256 → 4.76340 × 10⁻⁵. The two converge
towards each other from opposite sides and the residual at the finest pair
is **+0.055 %** against the extrapolated integral — still forty times
inside the band, and a factor of 38 better than the trapezoidal reference
at the same resolution. The improvement factor falls from 327 to 48 as
both sides sharpen, which is the right behaviour: at coarse resolution two
discretisation errors happened to cancel.

### Findings

252. **The exact case has to be exact for the thing you actually
     integrate.** Band 1 asked the torus to reproduce 2πR·πa² to a part in
     a million and it does not: it converges first order to the 360-gon's
     answer, which sits 5.1 × 10⁻⁵ below the circle's, and the +2.0 × 10⁻⁶
     at n = 721 was those two errors cancelling. The residual is an
     artefact of the *test harness* and not of the method — the torus's
     axis is closed and the tangent differencer is written for an open
     curve, so the two end stations get one-sided tangents and contribute
     an O(1/n) error the OGV's genuinely open axis does not have. Recorded
     as a miss rather than re-based onto the polygon's own exact answer
     after the fact, which would have turned a 2× miss into a pass by
     changing the reference after seeing the number.
253. **The inner OGV's CAD was right all along and the reference was
     wrong, and the correction is a textbook theorem rather than a fitted
     term.** ∫A·ds is the volume of a prism swept along a *straight* path.
     Pappus's second theorem in differential form adds the only
     first-order term a curved path has — V = ∫A(1 − c̄·dT̂/ds)ds, the
     section centroid's offset from the axis times the curvature vector —
     and it takes the E³'s inner OGV from **−2.1056 % to +0.0064 %, a
     factor of 327**, with **not one number in the CAD changed**. The new
     reference is identical to the old one wherever the axis is straight,
     to 1.6 × 10⁻¹⁵, so none of the other 31 rows moves. The size of the
     term is the size of the mistake it corrects: `_section_2d` builds
     each section from its leading edge, so the stacking axis carries a
     centroid offset of about 0.45 of a chord — four centimetres on a vane
     whose lean bends the axis 20° over eleven — and a four-centimetre
     offset on a metre-ish radius of curvature is exactly the two per cent
     that was being reported as a CAD error for eight days.

---

## Unit H4 — the assembly's kinematics · step 0, 2026-09-18

Written **before** `solvers/geometry/kinematics.py` existed.

### Stage H is two closures wearing one name

`closures.yaml` carries a single Stage H entry — *"zero clashes through
rotation, every bearing with its load"* — gated on *"no hand-CAD tool
installed and verified"*. The two halves have nothing to do with each
other. **The clash-through-rotation half no longer needs a human**: G3
places all 32 rows at their true stations and proves row-to-row clearance
analytically, so a full-rotation sweep is a script. The bearing loads and
the static structure are a different problem and stay gated.

They are split into two closures here. **They are NOT named H1 and H2**,
because WORK-PLAN.md's Stage H already uses H1 for *Gates*, H2 for *Static
structure*, H3 for *Sumps and bearings* and H4 for *Assembly, motion,
section* — the kinematics half **is** plan item H4, and the hand-CAD half
is plan items H2 and H3. Using the plan's own numbering avoids two
different things called H1 in one repository.

### Bands

| # | Band | Why |
|---|---|---|
| 1 | across **all** row pairs, not only the 31 consecutive ones, the count whose assembled axial extents overlap is **zero** | this is the closure, and as an axial-extent statement it is **angle-independent**: two rows that do not share an axial interval cannot touch at any relative angular position, for any blade of either. A sweep samples; this proves |
| 2 | a 360-step sweep over one LP revolution changes the minimum row-to-row gap by **0.0 mm** | the numerical confirmation of band 1. If it moves, the placement is not rotationally periodic and something is wrong |
| 3 | the LP : HP ratio is **one number** wherever the project carries it — the glTF's `extras.kinematics`, unit I1's four-route reconciliation — to **0.5 %** | J1's finding 159 rule: a quantity two artefacts both carry is asserted equal by a test |
| 4 | every HPC rotor stage's printed Campbell per-rev lines contain the vane count of the stator **immediately downstream** (10 of 10) and **immediately upstream** (9 of 9, rotor 1's IGV excepted), and the HPT blade Campbell's 72/rev equals the LPT stage-1 vane count | **exact integers.** The engine orders a rotating assembly generates are its own blade counts, so this asks whether the counts the assembly is built from are the counts GE drew its Campbell diagrams against — across three separate reports |
| 5 | blade-passing frequency for every placed row at both spool speeds | an output, no band |

### Estimate before computing

Band 4 is the one that could fail and the one worth having. The HPC stator
counts are 32 / 50 / 68 / 82 / 92 / 110 / 120 / 112 / 104 / 118 / 140 and
the ten Campbell diagrams' per-rev lines run up to 140, so the numbers are
of the right size; whether each rotor's diagram carries *its own two
neighbours* rather than some other set is not obvious in advance. Rotor 1's
upstream neighbour is the variable IGV, which sits further forward than a
normal stator gap and is expected to be the exception.

### Not attempted

Bearing loads, casings, frames, sumps, flanges, mounts — all of Stage H's
hand-CAD half, which stays gated and whose gate is restated honestly in
`closures.yaml`. Nothing here is drawn; this unit only asks what the
already-built assembly implies about motion.

## Unit H4 — after the run · 2026-09-18

`python -m geometry.kinematics`. Nothing above was edited.

| # | Band | Result | Verdict |
|---|---|---|---|
| 1 | zero axially overlapping pairs across **all** pairs | **0 of 496** | **pass — the closure, as a proof** |
| 2 | 360-step sweep moves the tightest gap by 0.0 mm | tightest real pair HPC stator 4 / rotor 5 at **7.50 mm, spread 0.000 mm** | **pass** |
| 3 | one LP : HP ratio, to 0.5 % | glTF **3.5833** against I1's four-route **3.5739** — **0.26 %** | **pass** |
| 4 | each HPC rotor's Campbell lines carry its two neighbours' vane counts | **downstream 10 of 10, upstream 9 of 10** (rotor 1's IGV the exception, as step 0 predicted); HPT blade Campbell's 72/rev = the LPT stage-1 vane count | **pass** |
| 5 | blade-passing frequencies | 1,882 Hz at the fan to **19,810 Hz** at HPC rotor 10 | output |

### Findings

254. **"Zero clashes through rotation" is a proof on this assembly, not a
     sweep, and that is what took Stage H's first half off the human's
     desk.** Two rows whose assembled axial extents do not overlap cannot
     touch at any relative angular position, for any blade of either — and
     **none of the 496 row pairs overlaps**, not merely none of the 31
     consecutive ones G3 checked. The 360-step sweep was run anyway, on the
     real solids rather than on the argument, and moves the tightest gap by
     **0.000 mm**. That number is worth having for what it tests, which is
     not the engine: rotation about the engine axis cannot change an axial
     coordinate, so a spread of anything but zero would mean the placement
     transform had quietly carried a scale, a shear or an off-axis centre.
     It is unit J7's finding 171 — a spool turning about a line 5 mm off
     the axis — caught one artefact earlier.
255. **The assembly's own vane counts are the engine orders GE drew its
     Campbell diagrams against.** A rotor blade's excitation orders are the
     blade counts it passes, so the counts this project builds from ought
     to be the per-rev lines on the published diagrams — and across three
     separate reports they are. Every one of the ten HPC rotor stages
     carries the vane count of the stator **immediately downstream** among
     its printed per-rev lines, and nine of the ten carry the one
     **immediately upstream**: 50, 68, 82, 92, 110, 120, 112, 104, 118,
     140, each appearing on the two diagrams either side of it. And the
     **HPT stage-2 blade's Campbell carries 72/rev, which is the LPT
     stage-1 vane count** — an order drawn in the HPT report that only
     exists because of a number printed in the LPT report. Twenty
     integers, nineteen hits, nothing fitted.
256. **The one absence is the IGV, and it is unresolved.** Rotor 1's
     diagram does not carry 32/rev, although rotor 2's does and rotor 2 is
     further from the IGV. Rotor 1's printed lines are 2, 3, 4, 6, 8, 18,
     26, 50, and **8 and 26 match no vane count anywhere in the
     compressor**. Two readings are open and this project cannot choose
     between them: a variable row whose excitation GE judged not worth
     drawing on the one blade it is closest to, or a figure read where 32
     was taken as 26. The same row is the one `geometry.assembly` cannot
     build either, for an entirely unrelated reason — Table XXII prints its
     camber as a 65-series design lift coefficient rather than metal angles
     (finding 222). The E³'s IGV is the awkward row twice over.

### Blade passing, for the record

Fan 1,882 Hz · booster 3,294 · HPC rotor 1 5,901 rising to rotor 10
**19,810** · LPT rotors 6,470–9,175. The HPC's rear stages sit an order of
magnitude above the fan, which is why the rear-stage vanes' first flex has
to be up at 18–29 kHz (unit E3) and why a compressor's HCF problem is a
different problem from a fan's.
