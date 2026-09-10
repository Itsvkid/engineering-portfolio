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
     sweep or lean.** Stage C3 asks for *booster rows and inner OGV with
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

