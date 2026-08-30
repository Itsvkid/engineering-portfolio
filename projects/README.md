# Portfolio projects

Five self-contained aerospace projects, each free to run and each ending in
something a reviewer can look at. They exist to put evidence behind the claim
the site makes: engine and aircraft geometry designed and analysed in code.

Environment setup and versions: [SETUP.md](SETUP.md).

## Status

| # | Project | Tool | Output that proves it | Status |
|---|---|---|---|---|
| 01 | [Airfoil analysis](01-airfoil-analysis/) | Python (Hess-Smith panel method + Thwaites/Michel boundary layer) | Cl/Cd polars, Cp distributions, symmetric vs. cambered comparison, cross-check against XFLR5/XFoil, 38 tests | **Complete** |
| 02 | [External CFD](02-simscale-cfd/) | SimScale | Surface pressure, streamlines, wingtip vortex, Cl/Cd | Not started |
| 03 | [Flight performance calculator](03-flight-performance-python/) → [own repo](https://github.com/Itsvkid/flight-performance-calculator) | Python | Installable package, plots, tests, validation report | **Complete** |
| 04 | [Parametric wing](04-parametric-wing/) | pyOCC + FreeCAD | STEP/IGES geometry + dimensioned drawing | **Complete** |
| 05 | [OpenFOAM airfoil](05-openfoam-airfoil/) → [own repo](https://github.com/Itsvkid/naca0012-openfoam) | OpenFOAM | C-grid generator, GCI 6.4%, ten-angle polar | **Complete** |

Update the status column as each moves through `Not started → In progress →
Complete`. Each project's own README carries its work log.

## Suggested order

**03 → 01 → 04 → 05 → 02.** (Historical — 01, 03, 04 and 05 are now done; 02
is what's left.)

Start with **03 (Python)** because it needs no external tool, produces a real
GitHub repository on day one, and is the project that most directly backs the
site's positioning — engineering done by writing code.

**01** ended up following the same logic rather than XFLR5: a panel method is
light enough that there's no equivalent of 02's hardware argument for staying
in a GUI, so it became a second from-scratch Python solver (Hess-Smith panel
method + Thwaites/Michel boundary layer) instead — see its README for why.

Then **04 (FreeCAD)** to produce geometry, and **05 (OpenFOAM)** to analyse
that geometry — 04 and 05 chain together, which reads as one substantial
piece of work rather than two small ones. **02 (SimScale)** last: it overlaps
with 05, so it is the most skippable if time runs short — and per
`SETUP.md`, it's not skippable *to* a local alternative: this machine's 8 GB
RAM can't do 3D CFD locally, which is why 02 is scoped to SimScale's cloud
compute specifically, not just a tool preference.

## What connects to what

04 exports STEP → feeds 02 and 05.
01 gives the 2D baseline that 05's results should be checked against.

Chained projects are worth more than isolated ones. Say so explicitly in each
README and on LinkedIn.

## Where the output goes

Each finished project produces three things:

**GitHub** — the code and case files. Projects 03 and 05 are split out to
<https://github.com/Itsvkid/flight-performance-calculator> and
<https://github.com/Itsvkid/naca0012-openfoam>. The rest can live here.

Split a project out only once it is finished. Doing it early means maintaining
two histories while the work is still moving.

**The website** — figures go in `public/figures/`, CAD renders in
`public/products/`, and native CAD gets uploaded to viewer.autodesk.com and
referenced from `cadModels` in `app/data.js`. See `docs/CAD_VIEWER.md` and the
READMEs in those two folders for the field formats.

**LinkedIn** — one or two figures plus what the result actually shows. A number
with a comparison beats a screenshot of a contour plot.

## A rule worth keeping

A result without a reference is a picture. Every project below has a validation
or comparison step for that reason — against published data, against a second
airfoil, against an analytical result. That step is what separates a portfolio
piece from a tutorial you followed.

## Repository hygiene

Simulation output gets large fast. `.gitignore` at the repo root excludes VTK
files, ParaView state, OpenFOAM time directories and mesh binaries. Commit the
*inputs* (case dictionaries, scripts, geometry) and the *figures*; regenerate
everything in between. If a file is over ~10 MB and a script can recreate it,
it does not belong in git.
