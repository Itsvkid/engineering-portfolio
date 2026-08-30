# Engineering portfolio — Vinaykumar Venkateshkumar

Design and analysis work in aerospace propulsion, written as code so that
every result can be regenerated and every claim can be checked.

**Live site:** <https://vinaykumar.is-a.dev>

## What is here

Eight self-contained projects. Each ends in something a reviewer can look
at, and each carries a validation step — a comparison against published
data, an independent solver, or a closed-form result. A number without a
reference is a picture.

| # | Project | Tool | Validated against |
|---|---|---|---|
| 01 | [Airfoil analysis](projects/01-airfoil-analysis/) | Python — Hess-Smith panel method + Thwaites/Michel | XFoil: lift to 0.047 RMS, drag at 0.41× |
| 02 | [External CFD](projects/02-simscale-cfd/) | SimScale | *not started — needs a browser session* |
| 03 | [Flight performance](https://github.com/Itsvkid/flight-performance-calculator) | Python | Three aircraft, ceiling within 8% |
| 04 | [Parametric wing](projects/04-parametric-wing/) | pyOCC / OpenCASCADE | Kernel volume vs. closed-form integration |
| 05 | [OpenFOAM airfoil](https://github.com/Itsvkid/naca0012-openfoam) | OpenFOAM | Grid convergence index 6.4% |
| 06 | [Blade row](projects/06-blade-row/) | pyOCC | Free-vortex triangles, Carter's-rule deviation |
| 07 | [Nacelle](projects/07-nacelle/) | pyOCC + OpenFOAM | NASA TM 110300 wind-tunnel pressures |
| 08 | [Turbofan cycle model](projects/08-cycle-model/) | Python | Ideal-Brayton limit to 0.01% |

Mechanical design work — parametric CAD generators, toleranced drawing
packs with GD&T, sheet-metal flat patterns and a design-for-manufacture
checker — lives in a separate repository:
**[CAD-Projects](https://github.com/Itsvkid/CAD-Projects)**.

## The site

Next.js 16 App Router, statically prerendered, deployed on Vercel. All
content lives in `app/data.js` as plain exported objects; the components
map over it. Visual rules are in [`docs/DESIGN_SPEC.md`](docs/DESIGN_SPEC.md).

```bash
npm install
npm run dev
npm run build
```

## The CV

`cv/cv.tex` is the source; the PDF the site serves is built from it.

```bash
brew install tectonic
cd cv && tectonic -X compile cv.tex --outdir .
cp cv.pdf ../public/Vinaykumar_Venkateshkumar_CV.pdf
```

## Running the project tests

Projects 01, 03 and 08 need only NumPy, SciPy and Matplotlib. Projects 04,
06 and 07 need `pythonocc-core`, which lives in its own conda environment —
see [`projects/SETUP.md`](projects/SETUP.md).

```bash
cd projects/08-cycle-model && python -m pytest -q     # 82 tests
cd projects/01-airfoil-analysis && python -m pytest -q # 38 tests
```

## A note on what "validated" means here

Every project states what it was checked against and where it falls short.
The airfoil solver recovers only 41% of XFoil's drag, and says so. The
nacelle CFD misses the leading-edge suction peak, and says so. Reporting
the gap is the point — a portfolio where everything agreed perfectly would
mean the checks were not sharp enough to disagree.
