# 07 — Parametric nacelle

An axisymmetric engine-nacelle external cowl — and, as of the internal duct
below, a complete hollow nacelle shell — generated from Class-Shape
Transformation (CST) curves: the technique named in the live nacelle
installation-aerodynamics thesis this repository's owner is working on at
Cranfield, built here as a self-contained, testable piece rather than left
as a claim on a CV.

**Status:** v1 — CST curve, profile integration, revolved solid, an internal
duct completing the shell into a hollow nacelle, STEP/glTF export, a
CST-fit-recovery demo, an OpenFOAM validation case fitted to real NASA
wind-tunnel data (geometry/data pipeline run and verified, the CFD case
itself written but not executed — see `openfoam/README.md`) and 71 tests
are done.
**Environment:** `conda activate pyocc_env` (Python 3.10, pythonocc-core
7.9.0 — the same environment projects 04 and 06 use)

```bash
conda run -n pyocc_env python build.py          # generate and export
conda run -n pyocc_env python -m pytest -q      # 71 tests
```

54 of those 71 tests need no pyOCC at all — `tests/test_cst.py`,
`tests/test_profile.py`, `tests/test_fit.py` and
`tests/test_openfoam_reference.py` run in any Python with pytest, numpy
and scipy, which is what CI runs (see `.github/workflows/nacelle-ci.yml`);
the OpenCASCADE-dependent tests
(`test_nacelle.py`, `test_export.py`) only run locally, in `pyocc_env`.

## Why CST, and why not just reuse the wing's NACA sections

A NACA camberline is one specific curve family — good for a wing, wrong
shape for a nacelle. **CST** (Kulfan & Bussoletti, 2006) is not a curve, it
is a *parametrization method*: a class function fixes the general family
(rounded, pointed, blunt), and a Bernstein-polynomial shape function is free
to bend that class into whatever specific curve is wanted, controlled by a
handful of weights rather than a point cloud. It is the standard technique
behind "iCST parametric geometry" as used in real nacelle and fuselage
design tools, which is why the thesis project uses it and why this one does
too — this is the reusable piece of that technique, exercised on a problem
simple enough to fully validate.

A standard airfoil CST curve pins both ends to zero. A nacelle generatrix
cannot: the highlight (inlet lip) and the fan-cowl trailing edge both sit at
a real, nonzero radius. `src/cst.py`'s `CSTCurve` adds a linear term
carrying the curve between two arbitrary end values — the ordinary fix for
this in practice, not a one-off invention here.

## Design parameters

| Parameter | Symbol | Effect |
|---|---|---|
| Length | L | Highlight to trailing edge, axial |
| Highlight radius | r0 | Inlet lip radius — curve value at psi=0 |
| Trailing radius | r1 | Fan-cowl trailing-edge radius — curve value at psi=1 |
| Weights | A_0..A_n | Bernstein coefficients; the actual design variables — max radius and its station are *measured off the result*, the same relationship NACA4.max_thickness_station has to the wing project |
| Class exponents | N1, N2 | 0.5/0.5: rounded at both ends, the family an external cowl belongs to |

## Reference design

Representative of a mid-size turbofan external cowl — picked to sit in a
plausible range, **not reverse-engineered from a specific real engine**:

| | |
|---|---|
| Length | 3.000 m |
| Highlight radius | 0.850 m |
| Trailing radius | 0.600 m |
| Max radius (measured) | **1.108 m at 36.3% of length** |
| Predicted volume (integration) | 9.4212 m³ |
| Predicted total surface (integration) | 23.0206 m² |
| Measured volume (kernel) | 9.4232 m³ — **+0.022%** vs predicted |
| Measured total surface (kernel) | 23.0330 m² — **+0.054%** vs predicted |

The max-radius station (36% of length) is a plausible position for this
class of nacelle, not a targeted one — weights were chosen once and the
station read back off the result, the point being that this parametrization
finds a realistic answer rather than being steered to one.

### Internal duct

An independent CST curve for the duct wall — not derived from the external
one, and not required to follow its shape. `r0`/`r1` sit inside the external
curve's by 0.10 m at each end (lip and trailing-edge wall thickness):

| | |
|---|---|
| Highlight (inner lip) radius | 0.750 m |
| Trailing radius | 0.500 m |
| Max radius (measured) | 0.9422 m at 30.8% of length |
| Predicted material volume (integration) | 2.6119 m³ |
| Predicted total surface (integration) | 36.9561 m² |
| Measured material volume (kernel) | 2.6117 m³ — **−0.010%** vs predicted |
| Measured total surface (kernel) | 36.9819 m² — **+0.070%** vs predicted |
| Material fraction of the solid cowl | 27.7% |

"Material volume" is the external swept volume minus the internal swept
volume — the actual solid a real nacelle skin occupies, not the volume of
air passing through it. The 27.7% figure is a sanity check with physical
meaning, not just numerical self-consistency: hollowing the cowl into a
shell has to reduce its material, and by a plausible fraction for a thin
shell, not by a value near 0% or 100% that would suggest the two curves
were nearly coincident or the internal one had collapsed to the axis.

## Validation — what this does and does not claim

This project's validation is **entirely self-consistent**: closed-form
limiting cases and independent-route agreement, the same standard projects
04 and 06 hold themselves to. It does **not** claim agreement with a real
wind-tunnel dataset or a specific commercial-CAD export — doing that
honestly needs data this project does not have access to, and inventing a
comparison number would be worse than not having one.

- **Cylinder limiting case** — zero weights and equal end radii collapses
  the profile to a perfect cylinder, whose volume (`pi*R^2*L`) and lateral
  area (`2*pi*R*L`) are exact closed forms. Checked on both routes: the
  Simpson integration in `profile.py` and the revolved solid's kernel
  measurement in `nacelle.py`. This is what caught a real bug — see below.
- **Kernel vs. integration** — the revolved solid's measured volume and
  surface area are checked against `profile.py`'s independent numerical
  integration, sharing no code with the kernel. Agreement to 0.02–0.05% on
  the reference design.
- **Hollow shell — the same two checks, on `CompleteNacelle`** — the
  concentric-cylinders limiting case (an annulus of constant cross-section,
  `pi*(R_ext^2 - R_int^2)*L`, exact) and kernel-vs-integration agreement on
  the reference design (−0.010% / +0.070%, at least as tight as the solid
  cowl's own). Plus one check the solid cowl has no equivalent of: a curve
  can satisfy `r0_int < r0_ext` and `r1_int < r1_ext` at both ends while
  still crossing the external curve somewhere in between, since each is an
  independent CST curve free to bulge on its own — `internal_clearance_ok`
  checks every sampled station, not just the two ends, and a test confirms
  it actually catches a mid-span crossing that an endpoints-only check
  would call valid.
- **CST-fit recovery** — the actual mechanism behind "benchmarked against
  commercial CAD output for dimensional accuracy": in practice a CAD export
  gives a point cloud, not weights, and a CST curve is fitted to it by
  linear least squares (the shape function is linear in the weights, so
  this is not an optimizer). `build.py` samples the reference profile as if
  it were such an export, fits a fresh curve back to it, and reports the RMS
  residual — 4×10⁻¹³ mm on a noiseless sample, which demonstrates the fitting
  pipeline works, not that it would still work against real, noisy CAD
  export data.
- **Bernstein partition of unity** — equal weights must make the shape
  function exactly constant everywhere, a property of the Bernstein basis
  checked directly rather than trusted.

### A real bug this caught

The first version of `_simpson`'s panel-count handling computed the step
size `h` by dividing the *full* domain span by an *adjusted* panel count —
correct only when no adjustment was needed. Whenever `n_points` didn't give
an odd station count (the default, 400, doesn't), `h` was quietly wrong, and
the cylinder limiting-case test caught it immediately: 0.25% off a volume
that has an exact answer. Fixed by computing `h` from the actual uniform
grid spacing instead of re-deriving it from the span. This is exactly why
the limiting-case tests exist rather than only testing the general case —
a general case has no exact answer to be caught being wrong against.

## Exports

STEP in millimetres, glTF in metres — same reasoning as projects 04 and 06.
`exports/nacelle.step` is the external cowl as a single revolved solid.
`exports/nacelle-complete.step` is the hollow shell — external cowl plus
internal duct, with the interior left empty as the space air actually
flows through. Both are kept: the external-only solid is already in use
(the site's CAD gallery), and the two answer different questions —
"what's the outer aerodynamic shape" versus "what's the actual part."

## Figures

`figures/meridian-profile.png` — the generatrix and its mirror, the max-
radius station marked where the geometry actually put it.

`figures/complete-nacelle.png` — external cowl and internal duct together,
upper half only (mirroring both would draw the duct wall twice and read as
two nested outlines rather than a hollow shell), with the material between
them filled in — what a real cutaway would show as solid.

`figures/fit-recovery.png` — target profile against the CST curve fitted
back to it, with the residual plotted underneath rather than left as a
single number a reader has to trust.

`openfoam/figures/cst-fit-to-naca-1-85-100.png` — the same "don't just
report a residual number" treatment, applied to the real NASA TM 110300
ordinates rather than this project's own synthetic fit-recovery target;
see `openfoam/README.md`.

## Outstanding

- [x] CST curve with nonzero end values, tested without pyOCC
- [x] Profile integration (volume, lateral area, max radius), tested
      without pyOCC
- [x] Linear least-squares CST fitting, tested without pyOCC
- [x] Revolved solid on the OpenCASCADE kernel
- [x] STEP + glTF export
- [x] Kernel-vs-integration and cylinder-limiting-case validation
- [x] 71 tests, CI on the pyOCC-free half
- [x] **Internal duct / inlet surface** — `CompleteNacelle` in `nacelle.py`
      closes a loop between the external curve and a second, independent
      CST curve for the duct wall (never touching the axis, unlike
      `NacelleSolid`'s), revolving into a proper hollow shell rather than a
      solid lump. `NacelleSolid` and `exports/nacelle.step` are untouched —
      "external cowl only" was always a legitimate v1 scope, and the site's
      CAD gallery already depends on that exact solid. See Validation below
      for the new checks this added, and `exports/nacelle-complete.step` /
      `figures/complete-nacelle.png` for the result.
- [ ] **Real dimensional benchmark against a CATIA export** — the fit-
      recovery demo proves the fitting mechanism works; doing this for real
      needs an actual CAD-exported point cloud, not a synthetic sample of
      this project's own curve.
- [ ] **Installation aerodynamics** — a pylon and a wing-mounted position
      are the entire point of the thesis this project borrows its technique
      from; an isolated axisymmetric cowl on its own says nothing about
      interference effects.
- [x] **OpenFOAM validation against published data, in the style of
      project 05** — see `openfoam/`. **Re, R. J. and Abeyounis, W. K.,
      "A Wind Tunnel Investigation of Three NACA 1-Series Inlets at Mach
      Numbers Up to 0.92," NASA TM 110300, November 1996** (free, public,
      NTRS) is the dataset: real, cited, transcribed external-cowl
      pressure coefficients (`openfoam/reference_data.py`) for the NACA
      1-85-100 inlet at M=0.79, mfr=0.71, α=0°. A CST curve fitted to the
      real ordinates (not this project's own arbitrary reference design)
      reproduces them to 0.019% RMS of max radius — `openfoam/
      fit_reference_geometry.py`, run and verified. The CFD surface
      geometry is built and exported (`openfoam/generate_stl.py`, run in
      `pyocc_env`): captured mass flow is represented as a prescribed
      velocity on a flat capture-plane disc at the highlight, not real
      internal duct geometry — `NacelleSolid`/`CompleteNacelle` both close
      the profile into fully solid/closed geometry with no flow-through
      opening, so neither fits this case; see `openfoam/README.md` for
      why a custom open-shell revolve was built instead, and for the
      mass-flow derivation. **The OpenFOAM case now actually runs**:
      meshed (`blockMesh` + `snappyHexMesh`, 108,904 cells, quality-checked),
      solved (`rhoSimpleFoam`, converges in 555 iterations after finding
      and fixing four real bugs plus a missing `fvOptions` stability
      safeguard — see `openfoam/README.md`, "Getting the solve to
      converge," for the full debugging story), and compared against the
      real NASA Cp data (`openfoam/README.md`, "Results"). The comparison
      is honest, not flattering: RMS Cp error 0.65 over 17 matched
      stations, with the model missing NASA's leading-edge suction peak
      entirely (likely mesh resolution / capture-plane fidelity right at
      the highlight) while tracking reasonably over the mid-to-aft body.
      Closing that gap is future work, not done here.
      A second, more directly relevant paper — Robinson, M., MacManus,
      D. G. and Sheaf, C., "Aspects of aero-engine nacelle drag," *Proc.
      IMechE Part G*, 2019, from Cranfield's own Propulsion Engineering
      Centre (the same research tradition as the thesis this project
      borrows CST from) — validates CFD against isolated-nacelle ARA
      wind-tunnel data at a closely matching Mach/Reynolds/MFCR range,
      but its underlying data is Rolls-Royce/ARA proprietary and the
      paper itself is paywalled: useful as methodology and lineage
      context, not as a usable data source.

## Log

| Date | What was done |
|---|---|
| 2026-08-20 | `cst.py` (CST curve with nonzero end values), `profile.py` (integration, limiting cases), `fit.py` (linear least-squares weight fitting) — all pure Python, no pyOCC. `nacelle.py` (revolved solid) and `export.py`. Caught and fixed a 0.25% Simpson-integration bug via the cylinder limiting-case test before it reached the kernel comparison. Full build verified end to end in `pyocc_env`: kernel vs. integration agreement to 0.02–0.05%, 33 tests passing. First working draft, scoped deliberately to self-consistent validation only — see Outstanding. |
| 2026-08-21 | Internal duct / inlet surface. `CompleteNacelle` in `nacelle.py` closes a loop between the external curve and a second, independent CST curve for the duct wall — never touching the axis, so it revolves into a hollow shell rather than a solid lump. Added `internal_clearance_ok`, `material_volume` and `material_surface_area` to `profile.py`, all pyOCC-free: the clearance check samples every station rather than just the two endpoints, since a curve can satisfy both endpoint inequalities while still crossing the external curve in between — proven with a deliberately-constructed crossing case (equal CST weights collapse the shape function to a constant via the Bernstein partition-of-unity property already used elsewhere in this project, pushing the mid-span radius well past the external curve while both endpoints stay clear) rather than just asserted. Validated the hollow kernel the same two ways `NacelleSolid` already was: concentric-cylinder limiting case (exact, `pi*(R_ext^2-R_int^2)*L`) and kernel-vs-integration agreement on the reference design (−0.010% / +0.070%). `NacelleSolid` and the existing `exports/nacelle.step` are unchanged — this is additive, not a replacement, and the site's CAD gallery still points at the solid it already validated. 12 new tests, 45 total, all passing first try. |
| 2026-08-22 | Literature search for the OpenFOAM-validation Outstanding item: found and cited a real, free, publicly-hosted dataset — Re & Abeyounis, NASA TM 110300 (1996), an isolated axisymmetric NACA 1-series cowl tested at Mach 0.60–0.92 with tabulated external-cowl pressure coefficients, the same isolated-cowl scope `NacelleSolid` has. No CFD case built yet — see Outstanding for the full citation and what's still needed (a prescribed mass-flow exit condition, which the internal duct added the day before now makes representable). |
| 2026-08-22 | Started the OpenFOAM case (`openfoam/`). Transcribed the report's Table II (external ordinates) and Table V(a) (Cp at M=0.79, mfr=0.71, α=0°) by rendering its PDF pages as images — plain text extraction garbles the report's tables completely. Fitted a CST curve to the real ordinates (0.019% RMS residual), backed out freestream static pressure from the report's stated Reynolds number per foot, and built the actual CFD surface geometry in `pyocc_env` — a custom open-shell revolve (not `NacelleSolid`/`CompleteNacelle`, both of which close the profile with no flow-through opening) plus a flat capture-plane disc at the highlight carrying a prescribed velocity (`V_capture = mfr * V_inf`) to represent captured mass flow without modelling the real internal duct. All of that — data, fit, freestream conditions, STL export — was actually run and verified, including catching a real transcription error (a hand-computed Sutherland `As` coefficient, wrong until cross-checked numerically against the same module's own `dynamic_viscosity()` before being written into `thermophysicalProperties`). The OpenFOAM case itself (mesh, boundary conditions, solver settings) is written but not executed — no OpenFOAM or working Docker daemon available; `openfoam/README.md` is explicit about exactly which half is which. 26 new tests (71 total): 24 on the geometry/data/fit pipeline (all genuinely exercised), plus 2 for the new `src.export.to_stl` function this needed. |
| 2026-08-23 | Got the OpenFOAM case actually running, via Colima + Docker (`opencfd/openfoam-default:2406`) after Docker Desktop's cask install proved uninstallable in this environment. `blockMesh`/`snappyHexMesh`/`checkMesh` all succeeded first try, validating the meshing work done blind the day before. The solve itself did not: found and fixed four real bugs (a wrong `fvSchemes` divergence-term name, a missing `div(phi,h)` scheme entry for the actual solved energy field, a `waveTransmissive` pressure BC incompatible with steady-state solvers, a SIMPLEC/relaxation mismatch), then hit a severe first-iteration pressure blowup that survived three independently-tested and *ruled out* hypotheses (the `highlightInlet` capture BC's type, mesh conditioning, a natively-ramped capture mass flow) before running OpenFOAM's own `aerofoilNACA0012` tutorial as a control — which converged cleanly, exposing a missing `fvOptions` `limitTemperature` safeguard as the actual fix. Converges in 555 iterations. Ran the real Cp comparison against NASA TM 110300 (fixing one more bug this exposed: `compare_to_reference.py`'s raw-surface filename and "top meridian" assumptions, both wrong against the real mesh's ~27-faces-around resolution — replaced with a circumferential average, physically justified by this case's axisymmetry). Result, reported honestly: RMS Cp error 0.65 over 17 matched stations, missing NASA's leading-edge suction peak but tracking reasonably over the mid-to-aft body — a converged, real, imperfect result, not a fabricated match. `openfoam/README.md`'s "Getting the solve to converge" and "Results" sections have the full story. Full test suite (including the 2 `compare_to_reference` tests rewritten for the new averaging logic) still passing. |
