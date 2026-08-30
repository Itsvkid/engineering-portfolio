# XFLR5 cross-check

An independent numerical check on this project's panel method, against
**XFLR5 v6.62** — which wraps Mark Drela's XFoil.

## Why this exists

This project already validated four ways: a panel's self-induced velocity
against its closed-form value, two internal routes to the same Cl, a
Blasius comparison for the boundary layer, and a symmetric-section
zero-lift check. Every one of those confirms the code implements the
mathematics it claims to. None of them is a *different solver* arriving at
a different answer.

That is the gap this closes. XFoil is not a second opinion from the same
family of assumptions: it solves the inviscid flow and the boundary layer
*coupled*, with an e^N transition model, where this project solves an
inviscid panel method and bolts a boundary-layer drag estimate onto the
result. So the disagreements are informative — they locate which physics
the simpler method leaves out, which is more useful than agreement would
have been.

## Same geometry, deliberately

The foils fed to XFLR5 are written by `run_analysis.py` from this
project's own `Naca4.surface()`, not from XFLR5's built-in NACA generator.
Comparing two solvers only means something if both are given the same
body, and the two generators differ — this project uses the closed
trailing-edge coefficient (−0.1036), and the point distributions are not
the same. Supplying our own coordinates removes geometry as a source of
disagreement, so what remains is solver physics.

## Conditions

| | |
|---|---|
| Sections | NACA 0012, NACA 4412 |
| Reynolds | 1×10⁶ |
| Mach | 0 |
| NCrit | 9 (standard) |
| Forced transition | none (free, xtr = 1.0 both surfaces) |
| Alpha sweep | −6° to 12°, 1° steps |
| Panels | 199 points, cosine-spaced |

## Results

Compared over −4° to 8°. Above roughly 8° XFoil's coupled boundary layer
starts shedding lift that an inviscid method has no mechanism to lose, so
statistics across the full sweep would measure the onset of stall rather
than the accuracy of the solver.

| | NACA 0012 | NACA 4412 |
|---|---|---|
| Cl, RMS difference | **0.047** | 0.101 |
| Cl, max difference | 0.068 | 0.212 |
| dCl/dα, this project | 6.92 /rad | 6.90 /rad |
| dCl/dα, XFLR5 | 6.34 /rad | 5.99 /rad |
| Cd ratio (this ÷ XFLR5) | **0.41×** | 0.38× |

**Lift holds up.** On the symmetric section the two agree to 0.047 RMS,
and both give exactly zero at α = 0. The lift slopes bracket thin-airfoil
theory in the direction the physics requires: this project sits ~10% above
2π because thickness adds slope and nothing removes it, XFLR5 sits ~1%
above on the 0012 and ~5% *below* on the 4412 because viscous decambering
takes back more than thickness gives. That ordering is the check — if the
inviscid method had come out below XFoil, something would be wrong.

**Drag is where it breaks, by about 2.5×.** This project recovers 0.41×
and 0.38× of XFoil's profile drag. More telling than the factor is the
shape: this project's Cd is nearly flat with incidence (0.0027 → 0.0059
on the 0012) while XFoil's more than triples (0.0053 → 0.019). Squire-Young
applied to an uncoupled Thwaites/flat-plate boundary layer is picking up
skin friction and almost none of the pressure-drag rise, because an
uncoupled boundary layer never feeds its displacement effect back into the
pressure distribution that drives it.

The project README already said the viscous Cd was "a real but deliberately
approximate estimate". This puts a number on that, which is the entire
point of running the comparison.

## Reproducing

The comparison itself needs nothing but this repository — the XFLR5 output
is committed under `reference/`, and `build.py` and the tests read it
directly:

```bash
python build.py                      # regenerates figures/xflr5-validation*.png
python -m pytest tests/test_xflr5_reference.py -q
```

Regenerating the reference polars needs XFLR5 installed:

```bash
python xflr5/run_analysis.py
```

**That step needs a logged-in macOS GUI session.** XFLR5 ships only Qt's
`cocoa` platform plugin — there is no `offscreen` build — so even in
`--script` mode it cannot run over SSH or in CI. That is exactly why the
polars are committed rather than regenerated on demand.

## Notes on driving XFLR5 from a script

`--script <file.xml>` runs a batch foil analysis with no GUI interaction.
The format is `xflscript` v1.0; the authoritative example is
`xflr5v6/xflscript/resources/foil_script.xml` in the XFLR5 source tree,
commented field by field. Three things that are easy to get wrong:

- `<Directories>` belongs inside `<Metadata>`, not inside `<Foil_Analysis>`.
- The alpha sweep is `<Alpha>min, max, increment</Alpha>` inside
  `<OpPoint_Range>` — not separate min/max/step elements.
- The doctype is `<!DOCTYPE flow5>`, not the root element's own name.

And one worth knowing before debugging a script: **XFLR5 responds to a
script it cannot parse by calling `abort()`**, so a malformed file surfaces
as a SIGABRT crash report rather than an error message. The parser is
`xflscriptreader.cpp` in the same directory if a message is ever ambiguous.
