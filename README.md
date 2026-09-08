# Engineering portfolio — Vinaykumar Venkateshkumar

Design and analysis work in aerospace propulsion, written as code so that
every result can be regenerated and every claim can be checked.

**Live site:** <https://vinaykumar.is-a.dev>

## Mechanical design

Parametric CAD generators, toleranced drawing packs with GD&T to ISO 1101
and limits and fits to ISO 286, sheet-metal flat patterns, an FEA load case
taken from failure through a hand-screened trade study to a fix, and a
design-for-manufacture checker that reads a STEP file it did not create.
That work lives in its own repository:
**[CAD-Projects](https://github.com/Itsvkid/CAD-Projects)**.

## Analysis and propulsion

Nine self-contained projects. Each ends in something a reviewer can look at,
and each carries a validation step — a comparison against published data, an
independent solver, or a closed-form result. A number without a reference is
a picture.

| # | Project | Tool | Validated against |
|---|---|---|---|
| 01 | [Airfoil analysis](projects/01-airfoil-analysis/) | Python — Hess-Smith panel method + Thwaites/Michel | XFoil: lift to 0.047 RMS, drag at 0.41× |
| 02 | [External CFD](projects/02-simscale-cfd/) | SimScale | geometry validated; the 3D run needs a browser session |
| 03 | [Flight performance](https://github.com/Itsvkid/flight-performance-calculator) | Python | Three aircraft, ceiling within 8% |
| 04 | [Parametric wing](projects/04-parametric-wing/) | pyOCC / OpenCASCADE | Kernel volume vs. closed-form integration |
| 05 | [OpenFOAM airfoil](https://github.com/Itsvkid/naca0012-openfoam) | OpenFOAM | Grid convergence index 6.4% |
| 06 | [Blade row](projects/06-blade-row/) | pyOCC | Free-vortex triangles, Carter's-rule deviation |
| 07 | [Nacelle](projects/07-nacelle/) | pyOCC + OpenFOAM | NASA TM 110300 wind-tunnel pressures |
| 08 | [Turbofan cycle model](projects/08-cycle-model/) | Python | Ideal-Brayton limit to 0.01% |
| 09 | [E³ engine reconstruction](projects/09-e3-engine/) | Python — mean-line, through-flow, thermal, mechanical | The engine's own published tables: HPC efficiency 0.8455 against a printed 0.847, LPT 0.911 against 0.917, stage counts exact from the cycle alone |

Project 09 rebuilds the NASA/GE Energy Efficient Engine from its design
reports. Every transcribed value carries a report page, independent routes to
the same number are made to agree, and each place where a model and a
published figure disagree is written down rather than quietly reconciled.

## Turbofan Atlas

An interactive 3D anatomy of that engine, at
**[vinaykumar.is-a.dev/turbofan](https://vinaykumar.is-a.dev/turbofan)**.
Source in [`app/turbofan/`](app/turbofan/), which carries
[its own README](app/turbofan/README.md).

The flowpath is drawn to the dimensions the reports publish: 42 compressor
stations, five turbine stations, and the low-pressure turbine walls from
thirty transcribed aerofoil sections. The compressor and turbine blades are
lofted from the printed section tables rather than drawn by eye. All twelve
systems are there — gas generator, fuel, control, air, oil, ignition,
variable geometry, anti-icing, fire detection, vibration monitoring, exhaust
and structure — across 144 selectable parts.

Every number on the page is tagged: a report page, or `schematic` for generic
practice, or `assumed` for a value the model had to choose. The engine is
NASA's. Reading it accurately is the work.

## The site

Next.js 16 App Router, statically prerendered, deployed on Vercel. All
content lives in `app/data.js` as plain exported objects; the components map
over it. Visual rules are in [`docs/DESIGN_SPEC.md`](docs/DESIGN_SPEC.md).

```bash
npm install
npm run dev
npm run build
```

## The CV

`cv/cv.tex` is the source; the PDF the site serves is built from it. One
source, not two — an earlier split let a corrected version and a stale one
drift apart, and the stale one was the one being published.

```bash
brew install tectonic
cd cv && tectonic -X compile cv.tex --outdir .
cp cv.pdf ../public/Vinaykumar_Venkateshkumar_CV.pdf
```

## Running the project tests

Projects 01, 03, 08 and 09 need only NumPy, SciPy and Matplotlib. Projects
04, 06 and 07 need `pythonocc-core`, which lives in its own conda environment
— see [`projects/SETUP.md`](projects/SETUP.md).

```bash
cd projects/08-cycle-model && python -m pytest -q      # 82 tests
cd projects/01-airfoil-analysis && python -m pytest -q # 38 tests
cd projects/09-e3-engine && python -m pytest -q        # transcription and solver suites
```

The atlas carries its own geometry check, which builds all 144 parts in Node
and reports any that fail:

```bash
cd app/turbofan/tools && node --import "data:text/javascript,import { register } from 'node:module'; register('file://$PWD/node-resolve-hooks.mjs');" smoke.mjs
```

## A note on what "validated" means here

Every project states what it was checked against and where it falls short.
The airfoil solver recovers only 41% of XFoil's drag, and says so. The
nacelle CFD misses the leading-edge suction peak, and says so. The E³
reconstruction records where its own models disagree with the printed
numbers, including the ones still open. Reporting the gap is the point — a
portfolio where everything agreed perfectly would mean the checks were not
sharp enough to disagree.
