# Method — how every solver in PF-09 is built

Seven steps. The middle five are the ordinary numerical-method skeleton
— parameters, domain, matrix, solve, plot. The first and last are what
turn a plot into a result that can be checked by someone else. No solver
in this project skips step 0, and no plot is published without step 6.

This is the structure the E³ team used for their own through-flow
(LPT report §2.6: the radial-equilibrium equations on the axisymmetric
mesh of Fig. 8, solved for the vector diagrams of Table II). We follow it
because it is auditable, not because it is elegant.

```
 0  Tolerance and validation case — written BEFORE any run
 1  Parameters      every value with a src:, from the data files
 2  Domain          stations · meridional grid · mesh
 3  Matrix          assemble; for nonlinear problems, linearise
 4  Solve           direct / iterative; loop 3→4 until converged
 5  Plot            the quantity, the published value, the band
 6  Grid independence and record — halve the mesh, then write it down
```

## Step 0 — tolerance and validation case first

Before the first run, three things are written in the solver's header:

1. **The known answer it must reproduce.** A published number from the
   data files, or an analytic solution. Every solver has one; if it does
   not, it is not ready to touch the E³ (the validation ladder in
   [WORK-PLAN.md](WORK-PLAN.md#the-validation-ladder)).
2. **The pass band.** Set from the method's own scatter, not from what
   the run produces. Mean-line ±2 % on efficiency; through-flow ±3° on
   angles, ±0.03 on reaction; 1-D stress ±10 %; frequencies ±5 %.
3. **The convergence criterion** for anything iterative — residual, or
   change per pass — as a number.

A band widened after seeing the output is a finding, recorded as such
(`FINDINGS.md`), never a silent edit.

## Step 1 — parameters

Every input comes from `data/*.yaml` with its `src:`. A solver never
carries a literal that is not in the data files; if a number is needed
that is not there, it goes into the data file first, with its source or
with `status: assumed` and the reason. Units are SI internally. Where
a source prints both units, the test that transcribed it already checked
they agree.

## Step 2 — domain

- **Cycle**: the station list of the topology file (2, 21, 25, 3, 4,
  45, 5, 8) — hierarchical order, never numeric sort.
- **Through-flow**: a meridional grid — streamlines × calculation
  stations, one station at each row's leading and trailing edge plus the
  duct stations, as Fig. 8 of the LPT report.
- **Blade / disc**: 1-D beam along span, or 2-D axisymmetric mesh; the
  boundary conditions named (fixed root, free tip, shroud pinned).
- The domain's extent and count are printed in the run header so step 6
  can halve it.

## Step 3 — matrix

Assemble the discrete operator. Two cautions:

- **Nonlinear problems.** Radial equilibrium is nonlinear — the
  streamline positions depend on the solution. Step 3 becomes
  *linearise about the current streamlines*, and steps 3–4 loop until
  the streamlines stop moving (criterion from step 0). This is the
  streamline-curvature method; it is what the E³ used.
- **Conditioning.** Print the condition number or the residual history.
  A solve that "converges" in one pass on a poorly conditioned system has
  not converged.

## Step 4 — solve

Direct for small systems (tridiagonal through-flow stations, beam
stiffness), iterative with a printed residual for the rest. The solver
stops on the step-0 criterion, never on an iteration cap alone; if the
cap is hit, the run fails and says so.

## Step 5 — plot

Every plot shows three things: the computed curve, the published points
it is validated against, and the pass band as a shaded region. A plot
without the published points is not a result.

Standard plots by solver:

| Solver | Plot | Published points from |
|---|---|---|
| Cycle | T–s diagram; station table | Table XII (cycle), XI (components) |
| Through-flow | reaction, angles, Mach vs span per stage | LPT Table II; HPC Table XXI |
| Blade sections | surface Mach vs chord | LPT Figs 9–18 peak Mach |
| Blade stress | CF, bending vs span | LPT Table VIII, Fig. 55; HPT §4 |
| Disc | radial/hoop stress vs radius; burst margin | HPT §5.2.1; LPT §4.2.3 |
| Vibration | Campbell diagram | LPT Fig. 62; HPT Campbell |
| Cooling | metal temperature per node | HPT Tables IX–XIV node maps |

## Step 6 — grid independence and record

1. **Halve the mesh** (or double it). The answer must move by less than
   the step-0 band. Print both.
2. **Two routes.** Where a second, independent route to the number
   exists — a different table, a different equation — run it. Cross-
   checks that have already earned their place: Δh sum vs Δh/T × T49;
   loading from Δh and geometry vs the printed loading; ρω²A/2π vs the
   printed root stress; h/AW ÷ h/c as a stagger.
3. **Record.** The result, the validation case, the band, the mesh, and
   the date go into the data file (`derived:` block with `method:` and
   `validated_against:`) and, when it changes what the designer should
   expect, into the agent's §5 or §12.

## What this rules out

- A solver run "to see what happens" before step 0 is written.
- A literal in a solver that is not in a data file.
- A plot with no published points on it.
- A tolerance chosen after the run.
- A result recorded without its mesh and validation case.

## Where it applies

| Phase | Solver | Validation case (step 0) |
|---|---|---|
| B1–B4 | cycle | Table XII to 0.5 % on every station; ICLS as-tested |
| C1 | mean-line | Table I / Table XXI stage loadings; HPC Table XIV |
| C2 | through-flow | LPT Table II at hub/pitch/tip; HPC Table XXI |
| C3 | blade sections | peak Mach of Figs 9–18; NACA TN 3916 cascades |
| D1 | cooling network | HPT Table VII flows; node temperatures |
| E1 | blade stress | LPT Table VIII; ρω²A/2π first |
| E2 | disc | HPT / LPT disc data; Lamé thin-disc first |
| E3 | vibration | LPT Fig. 62; a cantilever beam first |
| E4 | rotordynamics | Jeffcott rotor first; bearing spans from CR-168219 |
