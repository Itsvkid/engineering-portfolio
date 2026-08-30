# 02 — External aerodynamic CFD (SimScale)

3D external flow over the project 04 wing, run in the browser.

**Status:** Geometry validated and ready to upload. The run itself needs a
human at SimScale's browser UI — an agent can prep everything up to that
point but can't hold your SimScale login, and shouldn't.
**Tool:** SimScale — <https://www.simscale.com> (free community plan; public
projects, limited core-hours)
**Why SimScale and not local OpenFOAM:** not a tooling preference — see
`../SETUP.md`. This machine's 8 GB RAM can't mesh a 3D wing with inflation
layers without thrashing swap; 2D (project 05) is fine locally, 3D isn't.

## Objective

A 3D result that shows something a 2D analysis cannot: spanwise loading, tip
vortex formation, and the induced drag that comes with them — checked against
project 01's 2D panel-method polar for the same section, which is what makes
this a validated comparison rather than an isolated number. That chain (04 →
02, checked against 01) is worth more than an unconnected CFD run.

## Core concepts

- Computational domain sizing (virtual wind tunnel)
- Near-wall treatment: y+ estimation and inflation layers
- RANS turbulence modelling with k-omega SST

## Geometry — checked, ready to upload

`../04-parametric-wing/exports/wing.step` (43 KB), checked with
`BRepCheck_Analyzer` (pyOCC): 1 solid, 1 shell, 6 faces, topologically valid
— no gaps, no open shells, nothing that would block meshing. STEP length
unit is millimetres; **set the import unit to mm** on upload, not the default
some tools assume, or the wing imports at 1/1000 or 1000× true scale.

Real geometry, from `build.py`'s own parameters — use these, not round
numbers, for domain sizing and force-coefficient normalisation:

| | |
|---|---|
| Span | 10.000 m |
| Root / tip chord | 1.600 / 0.720 m |
| Sweep (quarter-chord) | 25.0° |
| Dihedral | 5.0° |
| Washout at tip | 3.0° |
| **Planform area S** | **11.60 m²** |
| **MAC** | **1.2156 m**, at y = 2.1839 m |
| Section | NACA 2412 (constant across span) |

**The STEP file is the full 10 m span** (y from −5 m to +5 m), not a
half-model. Trimming it at y = 0 (root) in FreeCAD, and running a half-model
with a symmetry plane there, roughly halves the mesh cell count for the same
resolution — worth doing before upload given the free tier's core-hour
budget, not required for the case to be physically correct.

## Domain — sized off the real geometry above, not a rule of thumb

Half-model (symmetry plane at y = 0), MAC = 1.2156 m for streamwise/vertical
sizing, half-span = 5 m for spanwise:

| | |
|---|---|
| Upstream (wing root LE) | 12 m (≈10× MAC) |
| Downstream (wing root TE) | 24 m (≈20× MAC — wake needs more room than the approach flow) |
| Spanwise, beyond the tip (y = 5 m) | out to y = 10 m (one full span of clearance, so the wingtip vortex doesn't feel the wall) |
| Height, above and below | ±12 m |
| Symmetry BC | y = 0 face |

Full-model (no symmetry cut): same upstream/downstream/height, spanwise
domain y = [−10, 10] m instead — roughly double the cell count for the same
resolution, only worth it if the free tier's core-hour budget absorbs it.

## Mesh

- Hex-dominant, refined at the leading edge, trailing edge and wingtip —
  those are the three regions where a coarse mesh quietly eats the drag
  number without eating the lift number, which is why lift converges long
  before drag does.
- **First inflation-layer height ≈ 5–7 μm**, targeting y+ ≈ 1 — from
  Cf ≈ 0.058·Re⁻⁰·² (Schlichting, the same correlation project 01's
  boundary-layer module uses) at Re ≈ 5.5×10⁶ (MAC-based, see below), giving
  u_τ ≈ 2.45 m/s and y₁ = y⁺·ν/u_τ. Treat this as a starting point, not a
  guarantee — check the *actual* y+ SimScale reports after the first run and
  refine the first layer if it's off, the same iterative loop project 05
  used to get its own y+ into the 0.45–0.93 range.
- 15–20 inflation layers, growth rate ≈ 1.2.
- Start coarse (1–2M cells) to confirm the whole pipeline runs end to end
  before committing core-hours to a fine mesh — this is what "start project
  02" should actually mean on the first pass, not going straight for a
  publication-quality mesh.

## Physics

- k-omega SST, matching project 05's turbulence model — the same choice for
  the same reason, comparable near-wall behaviour.
- **Velocity inlet, not a fixed 30 m/s** — 68 m/s (Mach ≈ 0.2 at sea level,
  matching the original brief's flow condition and project 01's Reynolds
  range). Angle of attack is imposed by rotating the *velocity vector*, not
  the geometry — the wing in the STEP file is level:

  | α | Vx (m/s) | Vz (m/s) |
  |---|---|---|
  | 0° | 68.00 | 0.00 |
  | 5° | 67.74 | 5.93 |
  | 8° | 67.34 | 9.46 |

  Three angles, not one — 5° sits mid-linear-range, 8° is where project 01's
  2D panel method on the same NACA 2412 section starts flagging separation
  (see below), which is exactly the case worth having a 3D result for.
- Reynolds number (MAC-based): **Re ≈ 5.51×10⁶**.
- Outlet: 0 Pa gauge. Model surface: no-slip. Domain far-field/outer faces:
  velocity-inlet or a dedicated far-field BC if SimScale offers one for this
  case type — not a wall (that would block the flow instead of letting it
  pass through).

## 2D baseline to validate against

Project 01's Hess-Smith panel method + Thwaites/Michel boundary layer, same
NACA 2412 section, same Re ≈ 5.51×10⁶:

| α | Cl (2D) | Cd (2D) |
|---|---|---|
| 0° | 0.260 | 0.00211 |
| 5° | 0.863 | 0.00167 |
| 8° | 1.222 | 0.00141 (upper *and* lower flagged separated) |

Expect the 3D Cl to sit **below** these — a finite wing loses lift near the
tip that an infinite 2D section doesn't have to (tip relief), and picks up
induced drag the 2D result has no mechanism to predict at all (a 2D section
literally cannot show induced drag; it's the entire reason project 02 exists
rather than stopping at project 01). A 3D Cl within roughly 10–15% under the
2D number, plus a nonzero Cdi (induced drag) that 2D can't provide, is the
comparison this project is actually for — not an exact match, which would
mean one of the two methods is wrong.

## Post-processing

Residuals below 1e-4 for velocity, pressure and k before trusting any force
number. **Normalise Cl/Cd by S = 11.60 m² and the MAC = 1.2156 m** in
SimScale's force/moment post-processing setup — its defaults won't know
these, and force coefficients normalised by the wrong reference area are a
wrong number that looks like a right one. Export surface pressure contours,
3D streamlines, and the tip vortex — the actual reason this project exists
over stopping at project 01.

Check y+ against what the turbulence model expects before trusting any drag
number. Lift is forgiving of a coarse near-wall mesh; drag is not.

## Deliverables

- [ ] Mesh independence: three refinements, Cl and Cd tabulated against cell
      count
- [ ] Surface pressure contours
- [ ] Streamlines showing separation, if any
- [ ] Wingtip vortex visualisation
- [ ] Case study written up for LinkedIn or the site

## Folders

```
geometry/   STEP/IGES input
results/    exported data, force coefficients
figures/    contours, streamlines, vortex images
report/     the write-up
```

## Log

| Date | What was done |
|---|---|
| 2026-08-21 | Prep work only — the actual SimScale run needs a human at the browser, not something an agent can do without holding your login. Checked `wing.step` with pyOCC's `BRepCheck_Analyzer`: 1 solid, 1 shell, 6 faces, topologically valid, no gaps. Pulled the wing's real parameters from `build.py` (S = 11.60 m², MAC = 1.2156 m, NACA 2412) instead of using round numbers, sized the domain and mesh off them, and ran project 01's panel method on the same section at the same Reynolds number to give this project an actual 2D baseline to check the CFD result against, rather than an isolated number. |
