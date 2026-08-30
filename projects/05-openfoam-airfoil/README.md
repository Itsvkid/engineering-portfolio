# 05 — NACA 0012 in OpenFOAM

**Moved to its own repository:**
<https://github.com/Itsvkid/naca0012-openfoam>

The mesh generator, case, study drivers and validation figures live there with
their full history. Split out once complete, for the same reason as project 03:
a reviewer sent to a repository should land on the project, not on a Next.js
site.

## What it is

A structured C-grid generated from parameters, a grid convergence study with a
Grid Convergence Index, and a ten-angle polar. 53 tests, none needing Docker.

| | |
|---|---|
| Observed order of convergence | 2.24 |
| Richardson extrapolation, h→0 | Cd = 0.008645 |
| GCI on the finest grid | 6.4% |
| Lift-curve slope | 0.10710/deg — 97.7% of 2π |
| Zero-lift angle | +0.0001° (symmetry requires 0) |
| Best L/D | 46.9 at +8° |
| Lift vs experiment | mean \|ΔCl\| = 0.0092 |
| Grid-converged drag vs experiment | −3.4%, inside the 6.4% GCI band |

## Validated against Ladson, NASA TM 4074

Table VII — M 0.15, transition fixed with grit, Re 6×10⁶. The tripped case,
because the computation is fully turbulent with no transition model. Lift agrees
to better than 0.007 in Cl everywhere below +12°, and the grid-converged drag
lands within the numerical uncertainty of the measurement.

## Two findings worth quoting

`cellLimited Gauss linear 1` — the gradient limiter every tutorial reaches for —
reported **Cl = 0.049 for a symmetric section at zero incidence**, where symmetry
requires exactly zero, and inflated drag by 69%. It converged cleanly, residuals
fell, forces were flat from iteration 500. Nothing looked wrong. The only thing
that exposed it was a physical identity the answer had to satisfy.

**A reference constant carried from memory was wrong.** The repository held
`PUBLISHED_CD = 0.0080` — a figure belonging to a *smooth* aerofoil with free
transition, while the computation is fully turbulent and must be compared
against the tripped case, 0.00895. Against the bad constant the extrapolated
drag looked 8.1% high; against the real source it is 3.4% low. It made the model
look worse than it is and pointed the error the wrong way. The analysis now
reads the digitised reference instead of holding a constant at all.

## For the website

Figures are in the repository under `validation/`. To use them, copy into
`public/figures/` and add entries to a project's `figures` array in
`app/data.js` — see `public/figures/README.md` for the field format, and note
that figures carry a light and a dark render.
