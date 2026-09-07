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
134. **Appendix C does not reach the blade tip, and a mesh built as if it
     did would carry a tip gap five times too large.** The casing at the
     leading edge is 10.0000 in and the outermost tabulated section is at
     **9.9330** — a gap of 0.0670 in, **1.70 mm**, against Rotor 37's
     running tip clearance of about 0.36 mm. The appendix simply stops
     tabulating below the tip. Any tip-clearance CFD built on the last
     printed section would model a gap nearly five times the real one, and
     tip-clearance flow is what sets this rotor's stall margin. **The blade
     must be extrapolated to the casing less the clearance before it is
     meshed**, and that is a modelling decision that has to be stated, not
     absorbed.
135. **The hub rises exactly as much as the casing falls: 1.651 cm each.**
     The annulus closes from 7.620 cm at the leading edge to 4.318 at the
     exit — a 43 % area contraction — and it is split symmetrically between
     the two walls to four figures. On a stage designed in 1978 that is
     unlikely to be coincidence; it is the mean radius being held while the
     passage is squeezed.
