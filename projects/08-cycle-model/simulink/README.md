# Simulink cross-check of project 08

An independently-implemented replica of `../src/cycle.py`'s `solve_cycle()`,
built in MATLAB/Simulink instead of Python, at the exact same reference
design point, so its numbers can be checked line-for-line against
`../README.md`. This is the same "independent route to the same answer"
validation every other project in this portfolio already leans on (kernel vs.
integration, closed form vs. numerical search) — just a different language
and execution engine standing in for the second route.

It matches project 08's **default** `solve_cycle()` — the convergent-only
nozzle path, not the convergent-divergent nozzle extension (`cd_nozzle_exit`)
project 08 also has as an opt-in. The convergent-only reference numbers are
what's documented prominently in project 08's README, so they're the right
first target for a cross-check.

## What's actually verified here

This was written and carefully reviewed, but **not executed** — I don't have
MATLAB/Simulink access, so nothing past syntax-level checking happened before
this reached you. Two very different kinds of risk follow from that, and
they deserve different amounts of trust:

- **The physics** (`compress.m`, `expand_to_pressure.m`, `expand_for_work.m`,
  `combust.m`, `nozzle_exit.m`, `isa_atmosphere.m`, `gas_properties.m`) is a
  direct, careful line-for-line port of project 08's already-tested Python
  (`src/components.py`, `src/gas.py`, `src/atmosphere.py`) — plain MATLAB
  arithmetic, nothing version-sensitive. This is the trustworthy part.
- **The Simulink block-construction API calls**
  (`build_turbofan_model.m`: `add_block`, the Stateflow `EMChart.Script`
  route for authoring MATLAB Function block code, `add_line`) are the more
  likely place for a MATLAB- or Simulink-version-specific syntax issue —
  this is the part that would benefit from a debugging pass on your end.

**Run in this order** so a problem in one is easy to isolate from the other:

```matlab
cd matlab
test_physics_standalone   % 1. pure MATLAB, no Simulink at all
build_turbofan_model      % 2. generates TurbofanCycle08.slx
run_reference_design      % 3. simulates it, prints the same comparison
```

If step 1 doesn't match `../README.md`'s reference design table, the bug is
in the physics port — fix it there first, since `build_turbofan_model` calls
these exact same functions from inside its blocks. If step 1 matches but
steps 2-3 don't (or don't run at all), the bug is almost certainly in the
Simulink-specific wiring, not the physics.

## Known risk points if step 2 or 3 doesn't run cleanly

- **`Stateflow.EMChart` / `.Script`** — the way `add_fcn_block` (a local
  helper inside `build_turbofan_model.m`) sets a MATLAB Function block's
  code from a string. This is a real, documented MathWorks API, but its
  exact form has shifted slightly across MATLAB releases. If it errors,
  search your MATLAB version's documentation for "programmatically create
  MATLAB Function block" — the fix is usually a one-line change to how the
  chart object is located.
- **`To Workspace` output format** — `run_reference_design.m` reads the
  logged signal back via `evalin('base', 'cycle_results')`, which assumes
  the block writes directly to the base workspace during `sim()`. Newer
  MATLAB defaults sometimes route this through a `Simulink.SimulationOutput`
  object instead — the comment directly above that line in the script shows
  the two-line alternative if the direct read comes back empty.
- **Port ordering** — every `connect(...)` call in `build_turbofan_model.m`
  wires by argument position in each block's `function [out1,...] = fcn(in1,...)`
  signature. If a connection looks wrong in the generated diagram, check the
  signature comment next to that block's `add_fcn_block` call against the
  port number used in `connect`.

## Block-to-function map

| Simulink block | Python equivalent (`../src/`) |
|---|---|
| `Intake` | `cycle.py`'s freestream-to-fan-face stagnation calc, `atmosphere.at()` |
| `Fan` | `components.compress` |
| `CoreCompression` | `components.compress` × 2 (booster, HPC) |
| `CombustorAndHPT` | `components.combust` + `components.expand_for_work` |
| `LPT` | `components.expand_for_work` |
| `CoreNozzle` / `BypassPath` | `components.nozzle_exit` |
| `PerformanceSummary` | `cycle.TurbofanCycle`'s thrust/TSFC/efficiency properties |

The design point is baked into each block's generated code as literal
constants at build time (see the top of `build_turbofan_model.m`), rather
than wired in as Simulink signals — this is a single point-design
comparison, not a parametric study. To try a different design point, edit
those constants and re-run `build_turbofan_model`.

## Expected numbers

From `../README.md`'s reference design (OPR 35.84, bypass ratio 6.0, TET
1650 K):

| Quantity | Value |
|---|---|
| Net thrust | 57.67 kN |
| TSFC | 22.07 g/(kN·s) |
| Thermal efficiency | 46.7% |
| Propulsive efficiency | 52.2% |
| Overall efficiency | 24.4% |
| Fuel-air ratio | 3.18% |
| Core nozzle exit | 909.1 K, 88.3 kPa, 613.7 m/s, choked |
| Bypass nozzle exit | 237.2 K, 28.8 kPa, 308.8 m/s, choked |

Both scripts print a two-column table (MATLAB/Simulink alongside Python) so
you don't have to hold these numbers in your head while comparing.
