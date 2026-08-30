# 08 — Turbofan cycle model

A twin-spool, separate-exhaust turbofan cycle: freestream to both nozzle
exits, station by station, with every turbine's pressure ratio solved
against the power its own spool actually demands rather than picked by
hand. This is the thermodynamic-performance side of the "Gas Turbine
Performance" module at Cranfield — station temperatures, pressures, thrust,
TSFC and efficiency breakdown — not CAD. Projects 06 and 07 are the
geometry this engine would be built from; this is what decides whether that
geometry is worth building at all.

**Status:** v1 — full cycle solve, closed-form ideal-cycle validation, spool
power-balance checks, a convergent-divergent core nozzle option, a
simplified single-parameter part-throttle model and 82 tests are done. No
real off-design behaviour (compressor/turbine maps, surge margins) — see
Outstanding.
**Environment:** none beyond `pip install pytest matplotlib` — no pyOCC
anywhere in this project. A cycle model is thermodynamics, not geometry, so
unlike projects 06 and 07 every single test here runs on a plain runner,
with no `pyocc_env`-only split.

```bash
python build.py         # solve the reference design point and export a figure
python -m pytest -q     # 82 tests, all of them, everywhere
```

## Why this is a different kind of validation problem

Projects 04, 06 and 07 all validate a shape: does the kernel's solid match
an independent geometric calculation. This project validates a *cycle*:
does the assembled engine match the textbook thermodynamic limit its
components approach as they get closer to ideal. The check is the same
species — an independent route to the same answer — applied to energy
balances instead of volumes.

## Two conventions for one word, "efficiency"

A compressor's pressure ratio is a design choice; efficiency says how much
*more* temperature rise (work in) an imperfect machine needs to reach it —
divide the ideal delta-T by efficiency.

A turbine in this cycle never gets to choose its pressure ratio — it has to
deliver exactly the power its spool's compressor demands. Efficiency here
says how much *more* pressure ratio an imperfect machine needs to deliver a
given amount of work — the arithmetic looks the same (divide by efficiency
again) but for the opposite physical reason. Every turbine's pressure ratio
in this model is solved from required work, in `components.expand_for_work`,
not specified as an input.

## The combustor solves for fuel, not the other way round

Turbine entry temperature (TET, station 4) is the design input. Fuel-air
ratio is solved from the energy balance

```
mdot_air*cp_cold*T3 + mdot_fuel*LHV*eta_comb = (mdot_air+mdot_fuel)*cp_hot*T4
```

and two different `GasProperties` are used either side of that equation —
air at cp 1005 J/(kg·K), gamma 1.4, going in; combustion products at cp 1244
J/(kg·K), gamma 1.333, coming out. Reusing air's properties across the
combustor is a common simplification that is quietly wrong by a percent or
two on every downstream number.

## Reference design point

Representative of a mid-size subsonic civil turbofan cruise condition —
picked to sit in a plausible range, **not reverse-engineered from a
specific real engine**:

| | |
|---|---|
| Altitude / Mach | 10,668 m (35,000 ft) / 0.78 |
| Overall pressure ratio | 35.84 (fan 1.6 × booster 1.6 × HPC 14) |
| Bypass ratio | 6.0 |
| Turbine entry temperature | 1650 K |

| Station | T, K | p, kPa |
|---|---|---|
| Fan face | 245.4 | 34.9 |
| Fan exit | 284.6 | 55.9 |
| Booster exit | 331.1 | 89.4 |
| HPC exit | 759.5 | 1251.7 |
| Combustor exit | 1650.0 | 1201.6 |
| HPT exit | 1312.9 | 428.7 |
| LPT exit | 1060.5 | 165.8 |
| Core nozzle exit | 909.1 | 88.3 — **choked**, V 613.7 m/s |
| Bypass nozzle exit | 237.2 | 28.8 — **choked**, V 308.8 m/s |

| | |
|---|---|
| Fuel-air ratio | 3.18% |
| Net thrust | 57.67 kN |
| TSFC | 22.07 g/(kN·s) |
| Thermal efficiency | 46.7% |
| Propulsive efficiency | 52.2% |
| Overall efficiency | 24.4% |
| Ideal Brayton efficiency (upper bound) | 64.0% |

The gap between 46.7% and the 64.0% ideal-cycle ceiling is real component
losses *and* a second effect worth its own section below — it is not one
number quietly absorbing both.

## Validation

- **Spool power balance** — HPT delivered power is recomputed from the
  resulting stations and checked against HPC's actual draw (divided by
  mechanical efficiency); same for LPT against fan+booster. This is the
  identity every turbine's sizing in this model depends on, not a
  downstream sanity check.
- **Combustor energy balance** — both sides of the equation above are
  recomputed from the solved fuel-air ratio and checked to agree.
- **Ideal Brayton limit, isolated from ram effects** — with every
  efficiency at 1, no pressure losses, one gas throughout, and Mach low
  enough that ram compression is negligible (ram *is* modelled correctly
  elsewhere; it just isn't part of the textbook formula being checked
  against here), thermal efficiency matches `1 - 1/OPR^((gamma-1)/gamma)`
  to within 0.01% when the core nozzle is unchoked.
- **`overall_efficiency == thermal_efficiency * propulsive_efficiency`** —
  checked as an identity on the actual computed numbers, not assumed.
- **`propulsive_efficiency <= 1`** — a physical bound, not a design target,
  checked across 12 design-point combinations. See below for why this
  needed fixing at all.
- **C-D nozzle area ratio, two independent routes** — at zero loss, mass-
  flow continuity between the (exactly sonic) throat and the computed
  supersonic exit gives one route to the exit/throat area ratio; the
  standard isentropic area-Mach relation, evaluated at the exit Mach number
  alone, gives a second, unrelated one. They agree to 1e-6 relative — see
  `test_cd_nozzle_area_ratio_matches_the_closed_form_area_mach_relation_
  at_zero_loss`.
- **Part-throttle identity and monotonicity** — `throttle=1.0` reproduces
  the reference design by object identity, not floating-point round-trip;
  every compressor's pressure ratio satisfies
  `(PR_off - 1)/(PR_design - 1) == throttle**2` exactly by construction;
  and net thrust, TSFC, thermal efficiency and overall efficiency are all
  checked to move monotonically (thrust and both efficiencies down, TSFC
  up) as throttle is reduced across the reference design's full valid
  range — a property of this specific design and scaling law, verified
  rather than assumed.

### A choked nozzle is a real thermodynamic loss, and the model finds it

Running the ideal-limit check at increasing pressure ratio surfaced
something worth keeping, not just a pass/fail:

| OPR | Core nozzle | Thermal efficiency | Ideal formula | Gap |
|---|---|---|---|---|
| 2.0 | unchoked | 17.97% | 17.97% | 0.01% |
| 3.0 | choked | 26.89% | 26.94% | 0.21% |
| 5.0 | choked | 36.07% | 36.87% | 2.16% |
| 8.0 | choked | 42.54% | 44.80% | 5.05% |

Even with **zero component losses anywhere**, a choked, convergent-only
core nozzle cannot fully expand the flow to ambient pressure — real
pressure energy is left "stranded" at the throat as pressure thrust rather
than converted to jet kinetic energy, and the gap this leaves versus the
idealised (fully-expanded) textbook formula grows monotonically with OPR,
exactly as the underlying gas dynamics predict. `test_choking_penalty_grows_
with_pressure_ratio` checks the trend is monotonic, not just that any one
point is close; `test_choked_nozzle_thermal_efficiency_never_exceeds_the_
ideal_formula` checks the bound holds at every OPR tried. The reference
design's OPR of 35.84 pushes its core nozzle to 6.95× the critical pressure
ratio — significantly underexpanded, and a real driver of that design's
24.4% overall efficiency sitting well under the 64% ceiling, alongside
ordinary component losses.

### Convergent-divergent core nozzle

`components.cd_nozzle_exit` models an ideally-expanded C-D nozzle: instead
of capping at exit Mach 1 the way a convergent-only duct physically must,
the diverging section is sized to keep expanding the flow — supersonically,
if the pressure ratio calls for it — all the way down to ambient static
pressure. `cycle.solve_cycle_with_cd_nozzle` swaps this in for the core
nozzle only (the bypass stream's pressure ratio is low enough it never
chokes, so there's nothing for a C-D bypass nozzle to recover) while
reusing every upstream station from `solve_cycle` unchanged.

On the reference design, whose convergent core nozzle sits at 6.95× the
critical pressure ratio:

| | Convergent (choked) | Convergent-divergent |
|---|---|---|
| Core nozzle exit | T 909.1 K, p 88.3 kPa, V 613.7 m/s | T 661.5 K, p 23.8 kPa, V 996.4 m/s, **M 1.90** |
| Net thrust | 57.67 kN | 59.59 kN (+3.3%) |
| TSFC | 22.07 g/(kN·s) | 21.36 g/(kN·s) (−3.2%) |
| Thermal efficiency | 46.7% | 50.1% |
| Overall efficiency | 24.4% | 25.2% |

The convergent nozzle's exit pressure (88.3 kPa) sits well above ambient
(23.8 kPa at this altitude) — that gap is exactly the pressure thrust a
convergent-only duct cannot convert into jet velocity. The C-D nozzle's
exit pressure is ambient by construction; the same enthalpy drop instead
shows up as 62% more exit velocity, closing part — not all — of the gap
between this design's 24.4% overall efficiency and the 64.0% ideal-Brayton
ceiling, alongside the ordinary component losses that account for the
rest.

### Part-throttle model

`off_design.solve_off_design` is a deliberately simplified single-parameter
throttle model, **not** compressor-map-based off-design matching — see the
module's docstring for the full list of what it does and does not capture.
The short version: every compressor's pressure ratio scales with the
square of a throttle parameter (Euler's turbomachinery work equation,
specific work ∝ blade speed², the same physics project 06's free-vortex
blade design already leans on), turbine entry temperature scales linearly
with the same throttle, and everything else — mass flow, every component
efficiency — is held at its design value. Real off-design behaviour needs
compressor/turbine maps this project does not have; see Outstanding for
what that would take.

| Throttle | Net thrust | TSFC | Thermal efficiency |
|---|---|---|---|
| 1.00 | 57.67 kN | 22.07 g/(kN·s) | 46.7% |
| 0.90 | 50.75 kN | 22.47 g/(kN·s) | 44.3% |
| 0.80 | 43.47 kN | 23.09 g/(kN·s) | 41.4% |
| 0.70 | 35.89 kN | 24.08 g/(kN·s) | 37.6% |
| 0.62 | 29.65 kN | 25.30 g/(kN·s) | 33.9% |

0.62 is not a chosen floor — it's where this specific reference design's
turbine entry temperature (1650 K × throttle) scales down to
`TurbofanDesignPoint`'s own 1000 K plausibility guard, reused rather than
duplicated with a second bound in `off_design.py`. Thrust and both
efficiencies fall monotonically, TSFC rises monotonically, across the
whole range — a real, checked property of this design and this scaling
law (see Validation), not assumed from the shape of the formula.

### Two real bugs this caught

**Propulsive efficiency above 1.** The first version of `jet_kinetic_power`
used each nozzle's raw exit velocity. On the reference design this gave a
propulsive efficiency of 1.14 — a physical impossibility, since thrust
power can never exceed the kinetic power added to the flow. The cause: a
choked nozzle's exit pressure exceeds ambient, so its gross thrust includes
a pressure term the raw exit velocity's kinetic energy doesn't account
for. Fixed by using gross-thrust-per-unit-mass-flow — an effective velocity
that folds the pressure term into an equivalent momentum-only quantity — for
the kinetic-energy accounting instead. The two are identical whenever a
nozzle is unchoked, where there is no pressure term to fold in.

**Division by zero for a pure turbojet.** `bypass_ratio=0` is a legitimate
configuration (no bypass stream at all), but `bypass_effective_velocity`
divided gross thrust by zero mass flow unguarded. `test_pure_turbojet_does_
not_crash` is the regression test.

## Figures

`figures/station-ladder.png` — stagnation temperature through the core gas
path, intake to core nozzle exit: a staircase up through compression, a
spike at the combustor, a staircase down through the turbines. The single
most legible way to show what the cycle does to the working fluid, rather
than leaving it as a table of numbers.

`figures/throttle-sweep.png` — net thrust and TSFC against throttle for
the simplified part-throttle model, both curves falling out of the same
pressure-ratio/TET scaling rather than being independently fitted.

## Outstanding

- [x] Twin-spool, separate-exhaust cycle solve — every turbine work-matched
      to its spool
- [x] Two-gas-property combustor (cold air in, hot combustion products out)
- [x] Choked/unchoked nozzle physics, both streams
- [x] Ideal-Brayton-limit validation, isolated from ram effects
- [x] Spool power-balance and combustor energy-balance identities
- [x] 82 tests, no pyOCC anywhere
- [x] **Convergent-divergent nozzle** — `components.cd_nozzle_exit` and
      `cycle.solve_cycle_with_cd_nozzle`, opt-in (the default `solve_cycle`
      is unchanged): recovers 3.3% more net thrust and 3.2% better TSFC on
      the reference design by letting the core nozzle's exit reach
      supersonic (M 1.90) instead of stranding pressure thrust a
      convergent-only duct can't fully use. See "Convergent-divergent core
      nozzle" above. Does not model off-design over/under-expansion at any
      pressure ratio other than the one the nozzle was sized for.
- [x] **Simplified part-throttle model** — `off_design.solve_off_design`,
      a single throttle parameter scaling every compressor's pressure
      ratio with throttle² (Euler's turbomachinery work equation) and TET
      linearly. See "Part-throttle model" above for the numbers and
      exactly what this does and does not capture. This is explicitly
      *not* the item below — no compressor/turbine maps, mass flow and
      every efficiency held fixed regardless of throttle.
- [ ] **Real off-design performance** — compressor and turbine
      characteristics (2D maps of pressure ratio and mass flow against
      corrected speed), corrected mass flow that actually varies with
      speed and altitude, efficiency islands, and surge margin checking —
      what the simplified throttle model above deliberately doesn't have.
      Needed to say anything trustworthy about takeoff, climb, or how far
      this specific engine sits from surge at part power — a substantially
      larger undertaking than this project's scope.
- [ ] **Cooling and bleed flows** — HPT/LPT blade cooling air bypasses the
      combustor and re-enters downstream in a real engine, which both caps
      the metal-temperature-limited TET this model treats as freely
      choosable and changes the mass-flow bookkeeping through the turbines.
- [x] Wire a station-ladder or performance-summary figure into the site —
      not the CAD gallery (this project has no geometry to show, so it
      doesn't fit that section), but the Projects section: a full entry
      with the reference design's stats (net thrust, thermal efficiency,
      test count) and the station-ladder figure, both light and dark
      variants generated to match the site's actual theme tokens rather
      than reused from another project's palette. Live on the site.
- [ ] **Simulink cross-check** — an independent MATLAB/Simulink
      implementation of `solve_cycle()`'s default (convergent-only)
      reference design, to check against this project's numbers by a
      different language and execution engine rather than a different
      formula. Physics port and Simulink model-builder are written (see
      `simulink/`), but unexecuted — I don't have MATLAB access, so
      nothing has actually run yet. Whoever has MATLAB needs to run
      `simulink/matlab/test_physics_standalone.m` first and report back
      whether the numbers match.
- [x] Fixed-design Mach/altitude sweep, as a notebook — see
      `notebooks/cycle_envelope_analysis.ipynb`. Explicitly not the
      off-design item above: pressure ratios, TET and mass flow all stay
      at the reference design's values, so it shows ram effects only, not
      how the engine would actually respond off-design (no throttle
      model, no compressor map). Verified by executing it end to end; the
      grid point nearest the reference design reproduces 57.67 kN /
      22.07 g/(kN·s) exactly.

## Log

| Date | What was done |
|---|---|
| 2026-08-20 | `gas.py` (two-gas thermodynamics, ideal Brayton reference formula), `atmosphere.py` (ISA), `components.py` (compressor/turbine/combustor/nozzle, both efficiency conventions), `cycle.py` (twin-spool assembly, work-matched turbines, choked/unchoked nozzles). Found and fixed a propulsive-efficiency-above-1 bug (pressure thrust not represented in the kinetic-energy accounting) and a pure-turbojet division-by-zero, both now regression-guarded. Validated the ideal-Brayton limit at low Mach and low OPR to 0.01%, and characterised — rather than hid — the real, monotonic efficiency penalty a choked convergent nozzle imposes even with zero component losses. 56 tests, no pyOCC. |
| 2026-08-21 | Wired the project onto the live portfolio site (this Outstanding item was checked off without a log entry at the time — added retroactively while auditing this project's actual status against the README rather than trusting the checklist). Added a dark-mode station-ladder figure (`plotting.py` gained a `dark` parameter matching the site's actual `app/globals.css` tokens — bg1/fg0/fg1/accent — rather than reusing another project's palette) alongside the existing light one, and a full Projects entry in `app/data.js` with net thrust, thermal efficiency and test count as stats. |
| 2026-08-22 | Added a convergent-divergent core nozzle (`components.cd_nozzle_exit`, `cycle.solve_cycle_with_cd_nozzle`) — additive, `solve_cycle`'s convergent-only path is untouched. Reused `expand_to_pressure`'s existing energy relation with the M=1 cap simply removed, since that cap only exists because a convergent-only duct is physically stuck at it. Added `gas.isentropic_area_mach_ratio` (the standard closed-form relation) purely to cross-check the new nozzle by an independent route — mass-flow continuity between the sonic throat and the computed supersonic exit against the closed form evaluated at the exit Mach number, agreeing to 1e-6 relative at zero loss. On the reference design the C-D nozzle reaches M 1.90 at exit and recovers 3.3% more net thrust, 3.2% better TSFC, over the convergent nozzle's choked baseline. 15 new tests (71 total). |
| 2026-08-22 | Wrote a MATLAB/Simulink port of the default (convergent-only) reference design under `simulink/`, as a cross-check by a different language and execution engine rather than a different formula — the same validation species as every other independent-route check in this project, just with a different tool standing in for the second route. Unexecuted: no MATLAB access here, so `simulink/README.md` is explicit about what's a direct, low-risk physics port versus what's Simulink-API surface I couldn't test — see Outstanding. |
| 2026-08-22 | Added `notebooks/cycle_envelope_analysis.ipynb`: a Mach/altitude sweep at the reference design's fixed pressure ratios, TET and mass flow. Unlike the Simulink entry above, this one was actually executed end to end (`jupyter nbconvert --execute`) rather than written blind, since Python tooling is available here — outputs are embedded so the plots render on GitHub without anyone re-running it. Deliberately labelled as not an off-design model: thrust barely changing with altitude at fixed Mach is the plot showing its own blind spot, since `core_mass_flow` is a fixed input here rather than derived from density and flow area the way a real engine's would be. |
| 2026-08-22 | Added a simplified single-parameter part-throttle model (`off_design.py`) — compressor pressure ratios scale with throttle² (Euler's turbomachinery work equation, the same physics project 06's free-vortex blade design uses), TET scales linearly, mass flow and every efficiency stay fixed. Explicitly not real off-design performance (no compressor/turbine maps) — split the old "Off-design performance" Outstanding item into what this covers and what it deliberately doesn't. Reused `TurbofanDesignPoint`'s own 1000 K TET floor as the throttle range's lower bound rather than inventing a second one. 11 new tests (82 total), including that throttle=1.0 returns the reference design by object identity and that thrust/TSFC/efficiency all move monotonically across the whole valid range — caught a sort-direction bug in my own first version of the thrust-monotonicity test (descending throttle needs a descending, not ascending, thrust check) before it shipped. |
