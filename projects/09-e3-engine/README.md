# 09 — The Energy Efficient Engine, rebuilt from its design report

A complete twin-spool turbofan — nacelle, fan, booster, compressor,
combustor, both turbines, shafts, sumps and casings — modelled and sectioned
as a cutaway. **Every dimension is traceable to a public-domain NASA design
report, and the flowpath is computed from a cycle rather than traced off a
drawing.**

**Status:** planned. Work plan in [WORK-PLAN.md](WORK-PLAN.md), sources in
[REFERENCES.md](REFERENCES.md), published data transcribed with citations in
[`data/e3-fps-published.yaml`](data/e3-fps-published.yaml).

The only thing built so far is the architecture itself: the gas path and the
spool arrangement are encoded as data and held there by
[`tests/test_topology.py`](tests/test_topology.py) — 11 tests, passing on a
plain interpreter with no CAD backend.

```
gas path   fan -> booster (LPC) -> HPC -> combustor -> HPT -> LPT -> mixer -> nozzle
stations    2        21             25        3          4      45      5        8
LP spool   [--]     [--]                                       [--]
HP spool                           [--]                 [--]
```

The shafts cross the gas path: the **LP** spool takes the first compressors
and the last turbine, the **HP** spool takes the two in the middle. Pair them
the other way and every work split is wrong while the model still looks
entirely plausible — which is why it is asserted rather than assumed.

---

## The engine

The **NASA/GE Energy Efficient Engine (E³) Flight Propulsion System** — a
mixed-flow, twin-spool, high-bypass turbofan designed by General Electric
under NASA contract NAS3-20643, and the technology programme behind the
big-fan engines GE built afterwards.

It is chosen over a GE90 or a Trent for one reason that decides everything
about this project:

> **Its entire design report is public domain, and it contains the numbers.**

NASA CR-168219 gives the cycle at three rating points, every component
efficiency, every cooling flow, a module-by-module mass breakdown, running
clearances, and cross-sections of every component including the bearing
sumps. A modern engine's geometry is proprietary; this one's is published.

That is the difference between a model that *looks* like an engine and a
model that can be **checked against one**.

## What this project claims, and how each claim is checked

| Claim | Checked against |
|---|---|
| The cycle is right | NASA's own published sfc, OPR, BPR and turbine inlet temperature — CR-168219 Table XII |
| The component assumptions are fair | Published efficiencies and cooling flows, used as inputs and not tuned — Table XI |
| The annulus is *derived*, not drawn | Computed from the cycle by continuity, overlaid on NASA's published cross-sections |
| The blades are real blades | Free-vortex twist from velocity triangles, stage counts derived from the work split |
| The structure is an engine, not a shell | Every shaft's load path traced to a casing through named, placed bearings |
| The mass is plausible | Module-by-module against NASA's weight summary — Table XXVI |

The last one deserves a note. NASA's own breakdown puts **sumps, drives and
seals at 320 kg** — more than twice the combustor, casing and diffuser
together at 137 kg. A model without a bearing system is not missing a
detail; it is missing a tenth of the engine.

## Why it is not another CAD render

Searching for turbofan models returns hundreds. Almost all of them share the
same three properties: the blades are untwisted, there are no bearings, and
the proportions came from a photograph. They are shapes of engines.

This one starts from the other end — the thermodynamics — and lets the
geometry fall out of it. The headline figure is not the cutaway. It is a
plot of **computed annulus radius against NASA's published annulus radius**,
on the same axes, with the disagreement quantified and explained.

That plot is a sentence you can say in an interview: *the geometry is
downstream of the cycle, and here is where mine and NASA's differ, and why.*

## What it builds on

Three of this portfolio's existing projects are the inputs, which is why
this is a fortnight of new work rather than a term of it:

| Project | Contributes | State |
|---|---|---|
| [08 — Turbofan cycle model](../08-cycle-model/) | Station-by-station solve; the thing being validated | v1, 82 tests |
| [06 — Parametric blade row](../06-blade-row/) | Free-vortex twist, blade rings, annulus, STEP export | v1, 96 tests |
| [07 — Parametric nacelle](../07-nacelle/) | CST cowl and hollow shell | v1, 71 tests |
| [CAD-05 — Sheet metal bracket](https://github.com/Itsvkid/CAD-Projects) | The verification pattern: converge it, then disbelieve the peak | complete |
| [CAD-06 — HP turbine blade](https://github.com/Itsvkid/CAD-Projects) | Hot-section blade detail | brief only |

Three projects that read as three separate CV lines become one engine.

## Shape of the work

Five stages, 108 hours, of which 34 need a CAD licence and **74 do not**.

| Stage | Produces | CAD? |
|---|---|---|
| A · Foundation | Verified data, a validated cycle, the computed flowpath | no |
| B · Generated geometry | Every bladed row, nacelle, ducts, exports | no |
| C · Hand CAD | Casings, flanges, sumps, bearings, assembly, cutaway | **yes** |
| D · Verification | Mass, stress, clearances, and the findings | partly |
| E · Publication | Site entry, drawing pack, the write-up | no |

**Stage A stands alone.** If the CAD tool question stays open, Stage A plus
Stage B is still a complete, publishable piece of work — and it is the half
that carries the argument.

## Honesty rules for this project

Carried over from the rest of the portfolio, and worth restating because the
temptation is stronger on a project this visual:

1. **It is the E³, not a GE90.** Named correctly, with the report cited. The
   real story is better than the borrowed one.
2. **Inputs fixed before the run.** The cycle comparison is worth nothing if
   the efficiencies were tuned until it matched.
3. **Digitised geometry carries an uncertainty.** Radii scaled off a scanned
   1980s drawing are ±something. State it.
4. **The disagreement gets published.** `FINDINGS.md` is a deliverable, not
   an appendix.
5. **Unverified numbers are labelled.** `data/e3-fps-published.yaml` marks
   every value that has not yet been read in the source with
   `verified: false` and where to settle it.

## Running it

Not yet runnable. When Stage A2 lands:

```bash
python build.py            # solve, validate against Table XII, plot
python -m pytest           # including the published-data comparison tests
```

Sources are fetched by script and gitignored, following the same convention
as the reference PDF library and the STEP exports elsewhere in this
portfolio: the script is committed, the binaries are not.

---

*Data source: NASA CR-168219, "Energy Efficient Engine Flight Propulsion
System Final Analysis and Design Report", General Electric Company for NASA
Lewis Research Center, contract NAS3-20643. US Government work, public use
permitted.*
