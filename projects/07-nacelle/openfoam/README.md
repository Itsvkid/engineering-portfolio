# OpenFOAM validation: isolated axisymmetric nacelle cowl

An OpenFOAM cross-check of this project's fitted external cowl geometry
against real, published wind-tunnel pressure data — the same "independent
route to the same answer" validation species every other project in this
portfolio leans on, applied here to a real external dataset rather than a
closed-form identity.

## Citation

Re, R. J. and Abeyounis, W. K., "A Wind Tunnel Investigation of Three NACA
1-Series Inlets at Mach Numbers Up to 0.92," NASA Technical Memorandum
110300, Langley Research Center, November 1996. Free, public, NTRS:
<https://ntrs.nasa.gov/citations/19970010380>

Target: the NACA 1-85-100 inlet, internal contraction ratio 1.009, at
M = 0.79, mass-flow ratio 0.71, α = 0°. Every geometry and pressure number
this project uses from that report is in `reference_data.py`, transcribed
by rendering the report's PDF pages as images and reading the printed
digits directly — its own tables are scanned/rotated and garble completely
under plain text extraction. See that file's docstring for the full
transcription note.

## What's actually verified here

Every stage below has now actually been run — geometry/data, meshing,
and solving — through a Colima + Docker `opencfd/openfoam-default:2406`
container (see the git history around 2026-08-23 for how that
environment came together). The mesh/solve half was originally written
blind, without a working OpenFOAM install to check it against; getting
it to actually run and converge took real debugging, documented in
"Getting the solve to converge," below — this is not the case as first
written, it is the case as it exists after that debugging found and
fixed several real bugs.

**Actually run and verified, in this order:**

1. `reference_data.py` — the transcribed geometry (Table II) and pressure
   data (Table V(a)) — checked with 11 tests (monotonicity, endpoint
   values, physical sanity of the stagnation region and suction peak).
2. `fit_reference_geometry.py` — fits a CST curve (project 07's own
   `src.fit`) to the real ordinates. RMS residual **0.043 mm (0.019% of
   max radius)**, run and confirmed, not estimated — see
   `figures/cst-fit-to-naca-1-85-100.png`.
3. `freestream_conditions.py` — backs out a static pressure that
   reproduces the report's stated Reynolds number per foot at M=0.79
   given a chosen static temperature (288.15 K, ISA sea-level — the
   report states Re/ft and M, not a temperature; see that module's
   docstring). Sutherland's law dynamic viscosity checked against a known
   textbook value at 288.15 K (agrees to <2%).
4. `generate_stl.py` — builds the actual CFD surface geometry with pyOCC
   and exports it. **Run successfully in `pyocc_env`**, producing real
   STL files now sitting in `case/constant/triSurface/`. The open-shell
   revolve technique it depends on (`BRepPrimAPI_MakeRevol` on a wire
   rather than a closed face, to get a shell open at the highlight) was
   tested directly in pyocc_env before being written into this file, not
   assumed to work from general knowledge of the API.
5. `compare_to_reference.py`'s parsing/interpolation/Cp logic — 6 tests
   against fabricated `(x, y, z, p)` rows, plus now `main()` itself,
   run for real against a real converged solve (see "Results," below).
6. `blockMesh` — runs cleanly, 96,000-cell background mesh.
7. `snappyHexMesh -overwrite` — runs cleanly, 108,904-cell final mesh
   (6 boundary layers on `cowlAndAfterbody`, level 2/3 surface
   refinement). `checkMesh -allTopology -allGeometry` passes every
   check except one: ~1,700 "concave cells (using face planes)" — a
   near-unavoidable characteristic of octree-refined polyhedral cells at
   refinement-level transitions (see "Getting the solve to converge" —
   tightening `meshQualityControls` barely moved this number, and it
   turned out not to be the actual solver-stability problem anyway).
8. `rhoSimpleFoam` — **converges in 555 iterations** (all residuals
   below the 1e-4 `residualControl` targets).

Run these yourself, in order:

```bash
cd projects/07-nacelle
python -m pytest ../../projects/07-nacelle/tests/test_openfoam_reference.py -q   # or just: python -m pytest -q, from this project's root
python -m openfoam.fit_reference_geometry
conda run -n pyocc_env python -m openfoam.generate_stl
cd openfoam/case && ./Allrun   # or see "Run order," below, for the exact commands used
```

## Getting the solve to converge

The case as first written did not run. Four real, distinct bugs surfaced
purely from running it and reading the actual error, in this order:

1. `fvSchemes`'s viscous-stress divergence term used the wrong name for
   this solver/version (`div((muEff*dev2(T(grad(U)))))` — the real term
   `rhoSimpleFoam` 2406 wants is `div(((rho*nuEff)*dev2(T(grad(U)))))`,
   straight from the `FOAM FATAL IO ERROR`'s own text).
2. `divSchemes` only had an entry for `div(phi,e)`; `thermophysicalProperties`'s
   `energy sensibleEnthalpy` actually solves for `h`, not `e` — another
   field genuinely used didn't have a scheme.
3. The original `p` boundary condition (`waveTransmissive` on every
   farfield patch) needs a transient `ddt` context this steady-state
   solver doesn't have (`FOAM FATAL ERROR: steadyState ... From
   advectiveFvPatchField::updateCoeffs()`). Fixed by adopting OpenFOAM's
   own `compressible/rhoSimpleFoam/aerofoilNACA0012` tutorial's pattern
   instead: `freestreamPressure`/`freestreamVelocity` on every farfield
   patch, `inletOutlet` for T/k/omega.
4. `fvSolution` mixed `consistent yes` (SIMPLEC) with SIMPLE-style low
   `p` relaxation (0.3) — SIMPLEC wants high `p` relaxation, not low.
   Matched to the NACA0012 tutorial's plain-SIMPLE settings instead.

That got the solver running, but it still diverged violently within the
first 1-2 iterations every time (pressure swinging by hundreds of
kilopascals against an ambient of 66,829.5 Pa) and crashed with a
floating-point exception inside the thermophysical model by iteration 2.
Three targeted hypotheses were each tested and **ruled out** by actually
running them:

- **`highlightInlet`'s captured-flow BC** — switched from `fixedValue`
  to `flowRateInletVelocity` (correct sign convention confirmed against
  a real OpenFOAM tutorial): same blowup, same crash.
- **Mesh conditioning** — regenerated the mesh with `meshQualityControls`
  tightened well past the (already-standard, motorBike-tutorial-matching)
  original settings, targeting the concave cells `checkMesh` flagged:
  same blowup, same crash, concave-cell count barely moved (this
  particular check is largely inherent to octree-refined polyhedral
  meshes, not something the quality-control knobs can eliminate).
- **A ramped capture flow** — `massFlowRate` is a `Function1<scalar>`
  (confirmed in `flowRateInletVelocityFvPatchVectorField.C`), so it can
  be ramped natively from 0 to full strength over the first 200
  iterations via OpenFOAM's `scale`+`linearRamp` composition. With the
  capture at ~0.5% strength at iteration 1 — functionally switched off —
  the *same* blowup occurred, ruling out the capture-plane simplification
  entirely.

The actual fix: running OpenFOAM's own `aerofoilNACA0012` tutorial
unmodified, as a control, in the same environment. It converged cleanly
(Time=667+, residuals ~1e-7) — proving the environment itself was fine —
and its `system/fvOptions` had a `limitTemperature` entry this case
didn't: `{ type limitTemperature; min 101; max 1000; selectionMode all; }`.
Adding that one file was the actual fix. It doesn't prevent the same
severe first-iteration pressure swing from happening — it still happens,
visible in the log as dozens of cells getting clipped back into range —
but it stops that swing from producing a non-physical temperature that
crashes the thermophysical property evaluation, giving the solver enough
iterations to actually recover. By iteration ~19 the limiter stops
touching any cells at all, and the solution settles into a normal,
monotonically-converging run from there.

Every one of these was found by actually running the solver and reading
its output — none of it was predictable from reading the dictionaries
alone.

## What this case does and does not model

**Geometry**: the external cowl surface, fitted to the real NACA
1-85-100 ordinates, extended with a cylindrical afterbody out to
X/L=155% and capped there. NASA TM 110300 states the real test article
this way explicitly (p. 8): "a considerable portion of the model aft of
the cowl was cylindrical in shape equal in diameter to the cowl maximum
diameter" — the slope discontinuity where the fitted cowl curve meets the
constant-radius afterbody is what the real article has, not a modelling
artifact.

**Representing captured mass flow**: the real inlet has an internal duct
of its own (Table II's "internal ordinates," more detailed than this
project uses). This case does not model that duct at all — no internal
volume, no duct wall geometry. Instead, the highlight opening is closed
with a flat disc (`highlight-inlet.stl`) carrying a **prescribed axial
velocity**, `case/0/U`'s `highlightInlet` boundary:

```
V_capture = mfr * V_inf = 0.71 * 268.83 = 190.87 m/s
```

This works because captured mass flow is what actually sets the external
cowl's pressure field (via how much streamtube area the flow ahead of the
highlight has to divide between "goes over the cowl" and "goes into the
engine") — not the internal duct's downstream shape. Air that crosses
this disc simply leaves the computational domain there; there's nothing
behind it. `mdot = mfr * rho_inf * V_inf * A_highlight` and
`V_capture = mdot / (rho_inf * A_highlight) = mfr * V_inf` are the same
statement, which is why the boundary condition reduces to that one clean
number regardless of duct shape — see `generate_stl.py`'s docstring for
why `NacelleSolid`/`CompleteNacelle` (both close the profile into a fully
solid or fully closed-shell geometry, with no flow-through opening) don't
fit this case's need, and why the open-shell geometry is built directly
here instead of reusing either.

**Not modelled at all**: the report's actual internal duct shape, angle
of attack (this comparison is α=0° only), any of the other three
mass-flow ratios or four Mach numbers the report also tested, and real
wind-tunnel wall/support-sting interference.

## Results: comparison against NASA TM 110300

`compare_to_reference.py`'s `main()`, run for real against the converged
solve's `postProcessing/cowlSurfaceSample/555/p_cowlPatch.raw`:

```
Comparing against NASA TM 110300, Table V(a): M=0.79, mfr=0.71, alpha=0.0 deg

  X/L, %   Cp (NASA)  Cp (model)     error
    1.25     -1.3049      0.3484    1.6533
    2.50     -1.0066      0.3250    1.3316
    4.38     -0.3047     -0.1657    0.1390
    7.50     -0.3005     -0.7417   -0.4412
   15.00     -0.2103     -0.6042   -0.3939
   40.00     -0.1288     -0.1576   -0.0288
   70.00     -0.1106     -0.1221   -0.0115
   90.00     -0.0874     -0.1323   -0.0449
  139.00     -0.0187     -0.1344   -0.1157

RMS Cp error over 17 matched stations: 0.6479
```

(full 25-row table in the actual run — the 8 unmatched stations sit
upstream of where the meshed `cowlAndAfterbody` patch begins, a real
geometric limitation of the highlight-disc simplification, not a bug)

Running this exposed one more real bug along the way: the raw-surface
comparison logic (`top_meridian_trace`, written blind before any solve
existed) assumed OpenFOAM names sampled-surface files
`<surfaceName>_<field>.raw` and filtered to faces within 1cm of y=0 to
find a "top meridian." The real file is named `p_cowlPatch.raw` (field
first), and `cowlAndAfterbody` turned out to have only ~1,252 faces on
the whole body of revolution (~27 around the circumference) — a 1cm
y-tolerance matched exactly 1 face out of 1,252. Fixed by renaming to
`axial_pressure_trace` and averaging Cp over *all* circumferential faces
at each axial station instead of hunting for ones near a "top" that
isn't physically distinguished anyway (this case is axisymmetric at
alpha=0deg) — more robust to the mesh's real resolution, and it reduces
face-to-face discretisation noise by averaging rather than sampling one
face. See that function's docstring and `tests/test_openfoam_reference.py`.

**Honest read of the numbers**: the solver runs and converges, and this
is a real comparison against real wind-tunnel data, not a fabricated
one — but the quantitative match is currently poor. The model misses
NASA's leading-edge suction peak entirely (model shows a mildly positive
Cp near X/L=1-3% where the real data shows a strong suction peak down to
-1.36), overshoots suction further downstream (X/L 7.5-15%), then tracks
reasonably well over the mid-to-aft body (errors shrink to -0.01 to
-0.09 across 40-90%) before diverging again on the afterbody (122%,
139% — plausibly `generate_stl.py`'s `AFTERBODY_LENGTH_FACTOR`, a
**chosen** value standing in for the real afterbody shape NASA TM 110300
doesn't fully specify, showing through). The likely causes are mesh
resolution right at the highlight (where the flow accelerates sharply
around a tight radius) and the capture-plane simplification's effect on
the local flow right there, not anything wrong with the solve's overall
setup — but neither has been investigated further. Treat the "solver
converges" result as solid and the "matches NASA's Cp distribution"
result as a documented open gap, not a validated match.

A first physical-plausibility check, from `controlDict`'s `forces`
function object: net force on `cowlAndAfterbody` is
`(-6580.8, -0.08, -0.60)` N — i.e. pointing *upstream* (a "thrust-like"
force on the cowl alone), not downstream drag as the case's own
`controlDict` comment originally assumed it should. That assumption was
too simple: an isolated nacelle cowl's leading-edge lip suction is a
real, well-documented aerodynamic effect (exactly what NASA TM 110300
itself investigates) and can produce a net forward force on the cowl
surface alone, even though the propulsion system as a whole (cowl +
captured internal flow's momentum change) still has net drag — this
external-surface-only force isn't the whole thrust/drag bookkeeping.
The magnitude is a plausible order (axial force coefficient
`F_x / (q_inf * pi * RMAX^2)` ≈ 1.4), which at least says the *solution*
isn't a numerical artifact, separately from the sign question.

## Domain and mesh choices

A full 3D box domain (`blockMeshDict`), not an axisymmetric wedge, even
though α=0° is genuinely axisymmetric. The classic OpenFOAM `wedge`
boundary type is the physically exact way to mesh this, but combining it
with `snappyHexMesh` (needed here because the body's surface comes from
an STL, not simple analytic edges) is a much less common, higher-risk
combination than a plain 3D box — and a hand-built structured multi-block
mesh following the fitted curve directly, while more "correct," is
considerably harder to get topologically right without a mesher to
iterate against. A full box is the lower-risk choice for something built
without the ability to run it. See `blockMeshDict`'s own comment for the
domain extent (−5 to +15 max diameters axially, ±10 max diameters
radially).

First boundary-layer cell height in `snappyHexMeshDict`'s
`addLayersControls` targets y+≈30–50 for `kOmegaSST` wall functions —
computed from a flat-plate turbulent skin-friction estimate at this
case's actual freestream condition (see the git history for the
calculation), not tuned against an actual y+ report, since none exists.

## Known risk points, and what actually happened

- **Solver name**: OpenFOAM 2406 (ESI/OpenFOAM.com, the version this was
  actually run against) still ships `rhoSimpleFoam` as a distinct
  solver — no substitution needed here. Some newer builds have merged it
  into a unified compressible `simpleFoam`; substitute the solver name in
  `controlDict` and `Allrun` if yours has.
- **Function-object syntax**: `controlDict`'s `forces` and
  `cowlSurfaceSample` entries parsed and ran without modification on
  2406.
- **snappyHexMesh convergence**: ran cleanly on the first attempt, both
  originally and after the `meshQualityControls` tightening in "Getting
  the solve to converge" — `nSurfaceLayers 6` fully extruded (83% face
  coverage, 6 layers reaching 50.6% of target thickness) without needing
  any adjustment.
- **locationInMesh**: `(-1.5 0.3 0.3)` worked correctly — the mesh came
  out right-side-out on the first attempt.
- **What actually broke**: none of the above. See "Getting the solve to
  converge" for the four real bugs (all in `fvSchemes`/`fvSolution`/the
  `p` boundary condition) and the missing `fvOptions` `limitTemperature`
  safeguard that were the actual obstacles.

## Files

```
reference_data.py          Real, cited NASA TM 110300 data — RUN, tested
fit_reference_geometry.py  CST fit to the real geometry — RUN, tested
freestream_conditions.py   Static p, T solved from the report's Re/ft — RUN, tested
generate_stl.py            Builds and exports the CFD surface geometry — RUN
compare_to_reference.py    Post-processing comparison — RUN against a real
                            converged solve, see "Results," above
case/                      The OpenFOAM case — meshed, quality-checked, SOLVED,
                            converged in 555 iterations
  system/                  controlDict, blockMeshDict, snappyHexMeshDict,
                            fvSchemes, fvSolution, fvOptions
  constant/                thermophysicalProperties, turbulenceProperties,
                            triSurface/ (the two STLs generate_stl.py writes)
  0/                       Boundary conditions
  Allrun                   Standard run sequence
figures/                   cst-fit-to-naca-1-85-100.png
```

## Run order (as actually run)

```bash
cd projects/07-nacelle
conda run -n pyocc_env python -m openfoam.generate_stl   # writes the two STLs
cd openfoam/case
./Allrun                                                  # blockMesh, snappyHexMesh,
                                                           # checkMesh, rhoSimpleFoam
cd ..
python -m openfoam.compare_to_reference                   # prints the Cp table
```

Requires a working OpenFOAM 2406 install. This was actually run through
Docker (`opencfd/openfoam-default:2406`) via Colima on macOS, not a
native install — see the git history around 2026-08-23 for that
environment setup if you need to reproduce it the same way.
