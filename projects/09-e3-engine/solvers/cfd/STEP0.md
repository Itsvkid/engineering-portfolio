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
