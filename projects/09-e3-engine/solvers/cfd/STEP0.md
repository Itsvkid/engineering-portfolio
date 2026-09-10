# Step 0 — CFD (C4): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit C4-1 — does the solver compute compressible flow correctly?

C4's own first line says *"only after the method is validated"*, and its
Rotor 37 bands have been written and tested since 2026-09-06, waiting for a
solver. **A solver arrived on 2026-09-07** — but Rotor 37 is not the first
thing to point it at. Rotor 37 is a *published* answer with experimental
scatter; before that comes a case with an **exact** one.

Every stage of this project has done this. Ainley–Mathieson was run on
R&M 2974's own worked example before the E³ LPT. The beam was checked
against closed-form eigenvalues before it saw a blade. The polygon
integrator was checked on a rectangle and an ellipse. A CFD solver gets the
same treatment, and the case is the **Sod shock tube**: a diaphragm at
x = 0 between air at 100 kPa / 348.432 K and 10 kPa / 278.746 K, both at
rest — ρ = 1.000 and 0.125 kg/m³, which is Sod's problem in SI units. Its
solution is closed form: an expansion fan, a contact discontinuity and a
shock, with no correlation and no scatter anywhere in it.

The exact solver is written out in `shocktube.py` rather than imported, so
the known answer lives in this repository: Toro's Newton iteration on
f(p) = f_L(p) + f_R(p) + (u_R − u_L), then sampling the similarity
solution. **It needs its own known answer**, and it has one — Sod's
textbook star pressure is **p*/p_L = 0.30313**.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| The exact solver's own star pressure | Sod's **0.30313** | **±0.001** | the textbook constant for this problem; if the exact solver is wrong nothing below means anything |
| Star-region pressure, CFD vs exact | closed form | **±2 %** | 100 cells over 10 m is coarse; the plateau is the least-smeared quantity there is |
| Star-region velocity | closed form | **±3 %** | velocity is the noisiest of the three primitives on a coarse grid |
| Shock position at t = 0.007 s | closed form | **±2 cells** | a shock-capturing scheme smears a discontinuity over 2–4 cells by construction |
| L2 error, pressure and density | closed form, whole domain | **±5 %** | includes the smeared fan, contact and shock, so it is dominated by discretisation |
| L2 error, velocity | closed form, whole domain | **±8 %** | wider because the contact discontinuity carries no pressure jump and is the hardest feature to hold |
| The run completes | — | exit 0 | — |

Not a band, but stated: the mesh is the tutorial's 100 cells and **no grid
refinement is done here**. This unit answers "is the solver right", not
"is this mesh converged" — the second question is METHOD.md's step 6 and
belongs to Rotor 37, where the pass bands already ask for GCI 3 %.

**Toolchain, recorded because it took finding out.** There is no Docker
Desktop on this machine; `colima` provides the daemon (`colima start`).
`opencfd/openfoam-default:2406` has a native linux/arm64 build, so
OpenFOAM v2406 runs without emulation. **SU2 is not on conda-forge, pip or
Homebrew** — the only packaged binaries are x86_64, and the macOS one runs
under Rosetta 2. Both are installed and both are verified.

---

## Unit C4-1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`./cfd/run_shocktube.sh` then `cd solvers && python -m cfd.shocktube`)

```
Sod shock tube, 100 cells over 10 m, t = 0.007 s, dx = 0.1 m
   left  rho 0.9995  p   100000  a 374.3 m/s
   right rho 0.1249  p    10000  a 334.8 m/s

   exact star state:  p* = 30313.0 Pa   u* = 293.36 m/s
   CFD plateau:       p* = 30320.2 Pa   u* = 293.75 m/s
   error:             +0.02 %              +0.13 %

   wave speeds (m/s): fan head  -374.3  fan tail  -22.2  contact  293.4  shock  554.2
   shock at t: exact x = 3.880 m, CFD x = 3.900 m   (0.20 cells)

   L2 error over the whole domain, normalised:
      pressure 0.85 %   density 1.20 %   velocity 2.82 %
```

Toolchain verification:

```
colima         running, aarch64, 4 CPU / 6 GiB / 30 GiB, docker runtime
docker server  29.5.2
OpenFOAM       v2406, linuxARM64GccDPInt32Opt  -- native, no emulation
SU2            v8.5.0, macos64 (x86_64) under Rosetta 2, ~/.local/opt/su2-v8.5.0
               NACA 0012 Euler, M 0.8, AoA 1.25 deg: 162 iterations, residual
               down 7 orders, CL 0.3285 CD 0.02148, Exit Success
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Exact solver's star pressure | **0.30313** | Sod's 0.30313 ±0.001 | pass |
| Star pressure, CFD vs exact | **+0.02 %** | ±2 % | pass |
| Star velocity | **+0.13 %** | ±3 % | pass |
| Shock position | **0.20 cells** | ±2 cells | pass |
| L2 pressure | 0.85 % | ±5 % | pass |
| L2 density | 1.20 % | ±5 % | pass |
| L2 velocity | 2.82 % | ±8 % | pass |
| Run completes | exit 0 | exit 0 | pass |

### Findings

124. **The solver is right to 0.02 % where it can be checked exactly.**
     rhoCentralFoam's star-region pressure is 30,320 Pa against an exact
     30,313, and its star velocity 293.75 against 293.36 — on a 100-cell
     mesh, which is coarse by any standard. The shock lands **within a
     fifth of a cell** of where the Riemann solution puts it. Nothing
     about this was tuned: the case is the shipped tutorial, the exact
     solution is Toro's algorithm written out here, and the two met.
125. **The nesting is what makes it worth anything.** A CFD result checked
     against a hand-written exact solver is only as good as the exact
     solver, so that got a known answer of its own: Sod's textbook star
     pressure, **p*/p_L = 0.30313**, which this implementation returns to
     five figures. Two links in the chain, each with an answer that came
     from outside it. Without the first link the second would have been a
     program agreeing with itself.
126. **The error is where discretisation puts it, which is the real
     evidence.** Pressure is 0.85 % out in L2, density 1.20 %, velocity
     **2.82 %** — and that ordering is not arbitrary. Pressure is
     continuous across the contact discontinuity and the scheme holds it
     well; density jumps there with no pressure gradient to help, and
     velocity carries the numerical dissipation of both the fan and the
     contact. A solver with a *coding* error would not put its error in
     the physically expected place, in the physically expected order.
127. **The toolchain took finding out, and two of the three assumptions
     about it were wrong.** There is no Docker Desktop on this machine —
     `colima` was already installed with a stopped profile, so the daemon
     was one command away and nobody knew. OpenFOAM was **not** installed
     at all. And **SU2 is on no package manager that runs here**: not
     conda-forge (`conda search` finds nothing on any channel), not pip,
     not Homebrew, and `su2code/su2` has no Docker manifest. Its only
     binaries are x86_64; the macOS one runs under Rosetta 2 and does, at
     29 s for 162 iterations of transonic NACA 0012. Recorded so the next
     session does not rediscover it.

---

## Unit C4-2 — Rotor 37's blade, transcribed and checked

C4 cannot go near Rotor 37 without its blade, and the blade is in TP-1337's
Appendix C: twelve sections from a 7.0000 in hub to a 9.9330 in tip, each
with leading- and trailing-edge radii, a stacking point, a stagger angle
and a table of L / HP / HS.

**The appendix is a 1978 scan carrying NASA's own "ORIGINAL PAGE IS OF POOR
QUALITY" stamp, and its OCR is unusable.** `pdftotext` returns `0 .Otis`
and `0 .$073` where numbers should be, `LESS)` for `L(sp)`, `¢AHHA` for
GAMMA. No text extraction was used; the pages were read directly and
transcribed.

That is roughly **nine hundred numbers off a bad scan**, which is exactly
the kind of transcription that should not be trusted. So the bands below
are not tolerances on a model — they are **properties the real blade must
have and a typo would break**, and none of them was used to produce a
number.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Section closure at the leading edge | HP = HS = R1 at L = 0 | **exact** | the appendix prints R1 separately from the coordinate table, so this is 12 independent constraints, not a restatement |
| Section closure at the trailing edge | HP = HS = R2 at L = L_max | **exact** | 12 more, and R2 is printed separately too |
| Suction surface outside pressure surface | thickness ≥ 0 everywhere | **≥ 0** | a blade with a negative thickness is a typo |
| Surface smoothness | second difference / max thickness | **< 0.15** anywhere | a misread digit is a kink; real MCA surfaces are smooth |
| Stagger against radius | monotonic hub to tip | **strictly increasing** | a transonic rotor's sections turn one way |
| Hub/tip radius ratio | Table I's **0.70** | **±2 %** | Table I was transcribed on 2026-09-06 from a different table, months before these pages were opened |
| **Tip speed from the transcribed tip radius** | Table I's **454.136 m/s** at 17,188.7 rpm | **±1 %** | the sharpest check available: the radius comes from Appendix C and the speed from Table I, and nothing connects them but the blade being real |

Two printed digits did not resolve and are recorded rather than guessed:
the stagger at r = 7.2000 (tens digit, taken as 38 — its neighbours at
36°32′ and 41°25′ leave no other possibility) and at r = 9.9330 (**taken as
read at 65°23′**, though the trend through 57°26′ and 60°21′ would suggest
about 63; this project does not correct printed source data).

---

## Unit C4-2 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m cfd.rotor37`)

```
NASA Rotor 37 blade, TP-1337 Appendix C: 12 sections

     rad in   chord   t_max    t/c  stagger      R1      R2  pts
     7.0000  2.1518  0.1867 0.0868   36.533  0.0099  0.0118   23
     7.4800  2.1750  0.1646 0.0757   41.417  0.0091  0.0101   23
     8.0000  2.1887  0.1422 0.0650   46.583  0.0082  0.0087   23
     8.5000  2.1899  0.1207 0.0551   51.200  0.0074  0.0075   23
     9.0000  2.1974  0.0995 0.0453   55.433  0.0065  0.0062   23
     9.6100  2.1840  0.0752 0.0344   60.350  0.0055  0.0047   23
     9.9330  2.2020  0.0566 0.0257   65.383  0.0052  0.0036   24
     (five more)

1. closure: worst leading edge 0.000000 in, worst trailing edge 0.000000 in
2. thickness: thinnest +0.0000 in (the leading edge itself);
   t/c runs 0.0868 at the hub to 0.0257 at the tip
3. smoothness: worst 0.109 (hub, hs, L = 2.00); next 0.100 (9.6100, hp, L = 1.40)
4. stagger monotonic: True
   36.5 38.5 41.4 44.2 46.6 49.1 51.2 53.3 55.4 57.4 60.4 65.4
   rate 9.7 deg/in mean, 15.6 max at the tip
5. hub/tip radius ratio  0.7047 vs Table I's 0.70          +0.67 %
   tip speed at 17,188.7 rpm  454.1 vs Table I's 454.136 m/s   -0.00 %
   aspect ratio from the LE span 1.343 vs Table I's 1.19
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Leading-edge closure, 12 sections | **0.000000 in** | exact | pass |
| Trailing-edge closure, 12 sections | **0.000000 in** | exact | pass |
| Thickness non-negative | min +0.0000 | ≥ 0 | pass |
| Smoothness | worst 0.109 | < 0.15 | pass |
| Stagger monotonic | True | strictly increasing | pass |
| Hub/tip radius ratio | +0.67 % | ±2 % | pass |
| **Tip speed** | **−0.00 %** | ±1 % | pass |
| Aspect ratio | 1.343 vs 1.19 | — | **not a match, and the reason is recorded — finding 130** |

### Findings

128. **Twenty-four closure constraints, satisfied exactly.** Each of the
     twelve sections prints its leading- and trailing-edge radius
     *separately* from its coordinate table, and every one of the
     twenty-four is reproduced by the first and last row of that table to
     the last printed digit. Those numbers sit in different places on the
     page and were read at different times. For a transcription of nine
     hundred figures off a scan stamped "OF POOR QUALITY", that is the
     evidence that matters.
129. **The tip radius and the tip speed were transcribed from different
     tables, months apart, and they agree to four figures.** Appendix C
     puts the tip section at **9.9330 in**; Table I, transcribed on
     2026-09-06 before these pages were ever opened, gives **454.136 m/s**
     at 17,188.7 rpm. The radius times the speed is **454.1 m/s** —
     **−0.00 %**. Nothing connects those two numbers except the blade
     being real and both readings being right.
130. **The printed aspect ratio does not follow from the printed geometry,
     and that is a warning rather than an error.** Table I gives the rotor
     aspect ratio as **1.19**; span over mean chord from Appendix C gives
     **1.343**. The gap is not small and it is not a typo: 1.19 implies a
     mean blade height of **2.599 in** against Appendix C's leading-edge
     span of **2.933**, an 11 % contraction — which is what a compressor
     annulus does through a rotor. So the two are consistent only if the
     aspect ratio is built on the *mean* blade height and Appendix C's
     radii are *leading-edge* radii. Anyone who takes a chord from this
     appendix and an aspect ratio from Table I and divides one by the other
     will get a blade height that does not exist.

     > **Answered 2026-09-07 by finding 135.** The missing height is what
     > the casing trims off. Mean blade height 2.5915 in over mean chord
     > 2.1838 gives 1.1867 against the published 1.19, −0.28 %.
131. **The blade thins by more than a factor of three from hub to tip, and
     that is the transonic design.** t/c runs **0.0868 at the hub to
     0.0257 at the tip** while the chord barely changes (2.152 to 2.202
     in), and the stagger opens from 36.5° to 65.4°. The tip section is
     2.6 % thick and staggered 65° — a thin, highly staggered blade to keep
     the passage shock weak at a relative Mach of about 1.48. It is the
     same design logic as the E³'s own transonic rows, which is why this
     is the case C4 chose.
132. **Two printed digits did not resolve, and they are handled
     differently on purpose.** The stagger at r = 7.2000 has an unreadable
     tens digit, but its neighbours at 36°32′ and 41°25′ admit only one
     value, so 38°30′ is a reading and not a guess. The tip's 65°23′ is
     **taken as read** even though the trend through 57°26′ and 60°21′
     would suggest about 63° — the rate to the tip is 15.6 deg/in against a
     9.7 mean, the largest step in the blade. Correcting it would be
     correcting printed source data, which this project does not do; the
     smoothness check carries it as a known outlier instead.

### Unit C4-2, continued: the annulus

The blade is not a flow domain. TP-1337's figure 1(a) prints the flow-path
coordinates — inner and outer radius against axial distance — and its
x-axis is datumed on the **rotor-blade hub leading edge**, which is what
lets it be checked against Appendix C with no model in between.

```
   inner radius at x = 0   17.780 cm = 7.0000 in   (Appendix C's hub section: 7.0000)
   outer radius at x = 0   25.400 cm = 10.0000 in
   hub rises 1.651 cm through the machine; casing falls 1.651 cm
   annulus 7.620 cm at the leading edge, 4.318 cm at the exit
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Hub radius at x = 0 vs Appendix C's hub section | **7.0000 in vs 7.0000 in** | ±0.01 in | pass |
| Casing at x = 0 | 10.0000 in exactly | — | as printed |

### Findings, continued

133. **The flow path is datumed on the blade, and it lands exactly on it.**
     Figure 1(a)'s inner radius at x = 0 is **17.780 cm, which is 7.0000
     in** — Appendix C's hub section radius, to four decimal places. Two
     tables, forty pages apart, one in centimetres and one in inches, and
     the datum they share is a physical edge of the blade. Together with
     the tip-speed check (finding 129) that is both ends of the blade tied
     to independently transcribed numbers.
134. **Appendix C's outermost section lies OUTSIDE the casing, and the
     blade is trimmed to it.**

     > **Corrected 2026-09-07, within the hour it was written.** This
     > finding first said the opposite — that Appendix C "does not reach
     > the blade tip" and the blade "must be extrapolated to the casing
     > less the clearance". ~~That was wrong, and it was wrong because the
     > comparison used the wrong axial station:~~ the casing at **x = 0**
     > is 10.0000 in and the outermost section is at 9.9330, which looks
     > like a 1.70 mm shortfall. But x = 0 is the *hub* leading edge, and
     > the tip section's own leading edge sits at **x = 0.294 in**, by
     > which point the casing has already fallen to 9.9278 — *below* the
     > section. Over its whole chord, to x = 1.215 in where the casing is
     > at 9.672, the outermost printed section is **outside the flow
     > path**. Extrapolating outward would have added blade where the
     > casing already is.

     The physical blade is machined to the casing line less the running
     clearance, which is ordinary practice, and the trim takes the outer
     **trailing** corner off because the casing falls through the rotor.
     Clipping each section where it crosses that line leaves the sections
     up to 9.6100 in untouched and removes a smoothly growing fraction
     above it — 2 % at 9.637, 45 % by 9.798, 75 % by 9.852. The trimmed
     solid is **2.9 % smaller** than the lofted one.
135. **The trim is where the published aspect ratio went, and it closes to
     0.28 %.** Finding 130 recorded that Table I's rotor aspect ratio of
     1.19 does not follow from Appendix C's chord, which gives 1.343, and
     that 1.19 implies a mean blade height of 2.599 in against a
     leading-edge span of 2.933. **That height is exactly what the casing
     leaves.** Taking the blade height as the casing minus the hub at the
     hub's own leading edge (3.000 in) and at its trailing edge (2.183 in),
     the mean is **2.5915 in**, and over the mean chord of 2.1838 that is
     an aspect ratio of **1.1867 against a published 1.19 — −0.28 %.**
     Finding 130 is answered: nothing was wrong with either number, the
     ratio is simply built on the trimmed blade and the appendix on the
     manufacturing sections. It also confirms, in one number, the axial
     datum, the flow-path transcription and the chord together.
136. **The hub rises exactly as much as the casing falls: 1.651 cm each.**
     The annulus closes from 7.620 cm at the leading edge to 4.318 at the
     exit — a 43 % area contraction — and it is split symmetrically between
     the two walls to four figures. On a stage designed in 1978 that is
     unlikely to be coincidence; it is the mean radius being held while the
     passage is squeezed.

---

## Unit C4-3 — the mesh

One blade passage of thirty-six: a 10° sector with rotationally cyclic
sides.

The background mesh is **body-fitted to the annulus**. The hub and casing
are surfaces of revolution whose radii are printed against axial distance
(TP-1337 fig. 1(a)), so a blockMesh whose radial extent follows them at
every axial station needs no snapping on those two walls at all. That
leaves snappyHexMesh one job — the blade — instead of three, which matters
in a passage where the running tip clearance is **0.356 mm against a 74 mm
span**.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Background mesh builds | blockMesh | **exit 0, checkMesh OK** | a body-fitted block mesh has no excuse for failing |
| Background non-orthogonality | — | **< 30°** | it is a structured annular sector; anything worse means the axial stations are too coarse where the annulus turns |
| Background skewness | — | **< 0.5** | same |
| Snapped mesh builds | snappyHexMesh | **exit 0** | — |
| Snapped non-orthogonality | — | **< 70°**, OpenFOAM's own default limit | past 70 the discretisation error stops being second order |
| Highly skew faces | — | **< 0.01 % of faces** | a handful is normal where a snapped surface meets a background edge; a percent is a broken mesh |
| **Mesh volume vs the analytic annulus** | π(r_c²−r_h²) integrated over x, ÷ 36, less the blade | **±5 %** | the sharpest check available on a mesh: it is the geometry, integrated two completely different ways |
| Patches | inlet, outlet, hub, casing, two periodics, blade | **all seven** | — |

---

## Unit C4-3 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07

```
blockMesh          exit 0     196,800 cells, 207,583 points
   max aspect ratio 2.97, non-orthogonality max 16.83 (avg 3.99),
   max skewness 0.181                                    Mesh OK.

snappyHexMesh      exit 0     455,606 cells, 1,486,738 faces, 4m16s
   max aspect ratio 5.49, non-orthogonality max 64.85 (avg 12.50),
   max skewness 5.60 -- 7 faces of 1,486,738 (0.0005 %)
   patches: inlet outlet hub casing periodic_m periodic_p blade

mesh volume 3.3696e-4 m3   analytic annulus sector 3.33e-4 m3   +1.2 %
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Background builds | exit 0, Mesh OK | exit 0 | pass |
| Background non-orthogonality | **16.83°** | < 30° | pass |
| Background skewness | **0.181** | < 0.5 | pass |
| Snapped builds | exit 0 | exit 0 | pass |
| Snapped non-orthogonality | 64.85° | < 70° | pass |
| Highly skew faces | 7 of 1,486,738 = **0.0005 %** | < 0.01 % | pass |
| Mesh volume vs analytic | **+1.2 %** | ±5 % | pass |
| Patches | all seven | all seven | pass |

### Findings

137. **Body-fitting the annulus turned a three-surface snap into a
     one-surface snap, and it shows in the numbers.** The hub and casing
     come out of blockMesh exactly, with a background non-orthogonality of
     **16.8° and skewness 0.18** — a structured mesh, not an approximated
     one. After snapping the blade the worst non-orthogonality is 64.8°
     and there are **7 highly skew faces in 1.49 million**. Snapping all
     three surfaces would have put the mesh's worst cells exactly where
     the tip clearance is, which is the one place this case cannot afford
     them.
138. **The mesh volume checks against the annulus integrated
     analytically, to 1.2 %.** π(r_c² − r_h²) integrated along the printed
     flow path, divided by 36 and less the blade, is 3.33 × 10⁻⁴ m³; the
     mesh reports 3.3696 × 10⁻⁴. It is the sharpest check available on a
     mesh — the same geometry arrived at two completely different ways,
     one through a transcription and a CAD kernel, the other through an
     integral — and it catches a wrong sector angle, a wrong datum or a
     dropped section at once.
139. **blockMesh said "patch → block consistency" when it meant "you
     defined an edge twice".** Thirty blocks share their circumferential
     edges with their neighbours, and emitting the arc for each block
     emitted every shared edge twice. blockMesh rejects the whole topology
     for that and reports it as a *patch* problem, which sent this unit
     through two wrong fixes — a hex handedness that was already right,
     and a face ordering that was already right — before the real cause
     turned up by deleting the arcs and watching it pass. **The handedness
     was worth checking anyway and was worth checking numerically**: the
     sector's own rotation helper puts +θ at *negative* y, so the
     right-handed vertex order is the opposite of the one the sign of the
     angle suggests.

---

## Unit C4-4 — the run. **Open, with the fault characterised but not found.**

The mesh is built and checked (C4-3), the solver is validated against an
exact answer (C4-1), the blade and annulus are transcribed and cross-checked
(C4-2). The case runs. It does not yet produce a physical answer, and this
section records exactly what it does instead, because a wrong answer that
converges is worth more to the next person than a vague one.

### What the case is

`rhoSimpleFoam`, MRF at 1799.9965 rad/s (TP-1337's 17,188.7 rpm), k-omega
SST, total-pressure inlet at standard day, one 10° passage of thirty-six
with rotationally cyclic sides. Coarse grid level, 138,201 cells.

### Three faults found and fixed

Each produced a **converged, plausible, wrong answer**. None raised an
error. The only quantity that ever exposed them was the outlet temperature,
which must exceed the inlet because a compressor compresses.

| Fault | Evidence | Fix |
|---|---|---|
| Walls `noSlip` under MRF — a stationary blade in a rotating frame | T_out **278 K** against a 288 K inlet | `rotatingWallVelocity`; `MRFnoSlip` is not in this build |
| MRF cellZone spanning the **inlet patch**, so the frame spun the incoming flow to ~400 m/s tangentially before `totalPressure` was evaluated | mass flow 11× low, still no work | zone restricted to the rotor passage, 92,441 of 138,201 cells |
| Rotating wall patch spanning the **whole duct** while the zone covered only the passage — 4 cm of stationary-frame inlet with a wall at 1800 rad/s | mass flow a quarter of design, residual 0.03 | hub split into `hub_rotating` and `hub_static` at the zone boundary |

After the third fix the rotor compresses for the first time: **T_out 416.6 K
against a 288 K inlet at iteration 236**, mass flow 21.2 kg/s.

### The fault that remains

It does not hold. Every run so far collapses onto the same stalled branch:

```
run A  whole-domain MRF zone      mdot -0.1456   T_out 286.3 K
run B  zone restricted            mdot -0.1445   T_out 298.4 K
run C  hub split + ramped p_out   mdot -0.1437   T_out 298.2 K
```

**Three different setups, three collapses to within 1.3 % of the same mass
flow, all near iteration 700.** That is one mechanism, not three. The
stalled branch is 5.17 kg/s — **26 % of design flow** — with a 10 K
temperature rise against a design 78 K, so **13 % of design work**. And it
*converges* there: the pressure residual falls to 0.024.

A ramped back pressure (95 kPa held to iteration 300, then to 150 kPa by
1200) was tried on the hypothesis that the rotor was being run far past
choke before a sensible field existed. It collapsed at iteration 709 exactly
as the unramped runs did, at the same mass flow. **The hypothesis was wrong
and the ramp is not the answer.**

### What to try next, in order

1. **Inspect the converged stalled field.** Nothing so far has looked at
   the solution — only at integrated quantities. Reconstruct it, and check
   the axial velocity profile at the inlet plane and through the passage
   for reversal, and the swirl upstream of the blade. That distinguishes
   "the rotor does no work" from "the inlet is blocked", which the
   integrated numbers cannot.
2. **Check the cyclic coupling carries flow.** Plain `cyclic` matched
   without error, so the faces align, but confirm the flux across the pair
   is non-zero and balanced. A passage walled off by non-functioning
   periodics would restrict flow exactly like this.
3. **Check y+ on the blade.** At 138k cells the first cell off the blade is
   large; if y+ is in the thousands the wall functions are outside their
   valid range and the boundary layer is being modelled as a blockage.
4. **Try `SRF`** (`SRFSimpleFoam` is incompressible, but the SRF machinery
   exists) or a whole-domain rotating frame with `rotatingTotalPressure` at
   the inlet, which is in this build. That removes the zone-boundary
   question entirely, and for a rotor-only domain the rotating frame is the
   natural one.

### Findings

140. **Three MRF faults in a row, none of which raised an error.** A
     stationary wall in a rotating frame, a frame zone spanning the inlet
     patch, and a rotating wall spanning the zone boundary. Each converged
     to a plausible answer and each masked the next. The third converged
     most convincingly of all — residual 0.03 — to a machine passing a
     quarter of its design flow. **Residuals were useless as a guide all
     night; the outlet temperature was the only thing that ever caught
     them.** Instrument a rotating-machinery case with the physical
     quantity you are validating against *before* trusting any residual.
141. **The stalled branch is an attractor, and its repeatability is the
     evidence.** Three different setups collapsed to mass flows of 0.1456,
     0.1445 and 0.1437 kg/s per sector — a spread of 1.3 % — all near
     iteration 700. Three unrelated bugs would not converge to the same
     number. Whatever is left is one mechanism, and it is upstream of
     everything that has been changed so far.
142. **A ramped back pressure was tried and did not help, which rules out
     the most likely remaining explanation.** Running a transonic rotor far
     past choke from the first iteration is a standard way to get exactly
     this collapse, and loading it gradually is the standard cure. It made
     no difference: the ramped run collapsed at iteration 709 at the same
     mass flow as the unramped ones. Recorded because a negative result on
     an obvious hypothesis saves the next attempt from repeating it.

---

## Unit C4-4, continued — 2026-09-10: the field, at last, and one hypothesis killed

STEP0's four next steps were written on 2026-09-08. Steps 1 and 2 are now
done, step 3 is attempted and inconclusive, and the run they produced
**rules out the explanation everything had been converging on.**

### Result

| | |
|---|---|
| Step 1, inspect the field | **done** — the profiles are in `data/rotor37-stalled-field.yaml` |
| Step 2, cyclic carries flux | **done** — `sum(periodic_m) of phi = 0.996` at iteration 124. The periodics work |
| Step 3, y+ on the blade | **attempted, inconclusive** — the `yPlus` field did not survive into the written time directory and `postProcess` recomputed it as zero on every wall. Not answered; not claimed either way |
| Step 4, SRF / rotating frame | not attempted |
| Tip gap, measured | **0.515 mm** against 0.356 intended — 1.45×, 0.70 % of span |
| Constant back pressure at 105 kPa | **collapses anyway**, between iterations 1000 and 1200 |

### Findings

194. **The stalled machine is neither blocked at the inlet nor doing no
     work — it is reversed at the tip.** The question step 1 existed to
     answer is settled. At the inlet plane, four centimetres upstream of
     the blade, the inner **87 % of the span flows forward at 83 to 98
     m/s** and the outer 13 % is reversed, with a minimum axial velocity of
     **−165 m/s**, swirl of **−486 m/s** and a temperature of **597 K**.
     Just ahead of the blade the reversal begins at 84 % of span and the
     swirl reaches **−608 m/s** — against a tip blade speed of about −453.
     **The tip fluid is moving faster than the blade, in the blade's own
     direction, and rotor-worked gas at 597 K is being driven back out of
     the machine along the casing and past the inlet plane.** Five runs of
     integrated quantities could not have found that; one traverse did.

195. **It collapses at constant back pressure too, which kills the
     throttling explanation.** Finding 142 recorded that a ramp did not
     help. The obvious remaining reading was that 150 kPa was simply past
     this model's stall point, so the cure was to ask for less. Held at a
     **constant 105 kPa** — inside the range where the ramped run was still
     passing 104 % of design flow — it ran healthily for a thousand
     iterations and **collapsed anyway**, between iterations 1000 and 1200.
     The collapse is not caused by the back pressure, ramped or steady.
     That is the second obvious hypothesis to die, and both deaths are
     worth more than the guesses they replace.

196. **The tip gap is 1.45× design, not 14×, and the difference was a
     station error of mine.** Measuring the blade STL's maximum radius
     against the *domain's* maximum casing radius gives a 5.02 mm gap and a
     ratio of 14 — a dramatic finding that would have been wrong. The
     domain's widest casing is at the **inlet**, four centimetres upstream
     of the blade and 4.5 mm larger in radius. Measured at the blade's own
     axial station the gap is **0.515 mm against 0.356 intended: 1.45×,
     0.70 % of span**. Real, worth fixing, and nowhere near enough to
     explain a machine passing a third of its flow. Recorded because the
     wrong number was one edit away from being published.

197. **The solution never converges at all, which reframes the problem.**
     The trace at constant back pressure is not a march to a stalled
     branch. The work swings **−3 %, +38, +8, +12, +19, +45, −2, +91 %** of
     design across 1500 iterations while the flow drifts *upward* from 95 %
     to 118 % and then crashes to 34 %. **There is no steady state
     anywhere in the run.** Unit C4-1's finding that residuals were useless
     as a guide applies again and harder: the earlier runs were described
     as *converging* to a stalled branch on the strength of a falling
     pressure residual, and the integral quantities were swinging by a
     factor of thirty the whole time. A steady solver asked to converge a
     flow with a large reversed tip region may have nothing steady to
     converge to. **The next step is therefore not a fifth variation on the
     steady setup: it is a transient solve** (`rhoPimpleFoam`), which would
     also say whether the reversal is a rotating-stall cell rather than a
     fixed separation.

### What to try next, revised

1. **`rhoPimpleFoam`, transient**, from the healthy field at iteration
   1000 of the constant-105 kPa run. If the tip reversal is unsteady, a
   steady solver was never going to work and this is the whole answer.
2. **y+ properly** — write the field, do not recompute it. Step 3 is still
   open and the tip is where it matters.
3. Close the tip gap from 0.515 to 0.356 mm and repeat, to bound how much
   of the tip reversal the 1.45× gap is responsible for.
4. Only then the rotating-frame formulation of the old step 4.

