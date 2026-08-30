# 04 — Parametric wing

A wing whose geometry is generated from parameters, not drawn. Changing taper
ratio or sweep regenerates the solid; nothing is positioned by hand.

**Status:** Complete — generator, exports, figures, drawing and tests done
**Environment:** `conda activate pyocc_env` (Python 3.10 + pythonocc-core 7.9.0)

```bash
conda run -n pyocc_env python build.py          # generate and export
conda run -n pyocc_env python -m pytest -q      # 31 tests
```

## Why pyOCC rather than the FreeCAD GUI

The brief said FreeCAD, and FreeCAD is installed. But **parametric is the whole
point**, and a wing clicked into existence in a GUI is not reproducible,
testable, or reviewable in a diff.

pythonocc-core is a Python binding onto Open CASCADE — the same geometry kernel
FreeCAD is built on — so this is the same kernel driven from code. It is also
the toolchain the portfolio claims, which makes this project evidence for that
claim rather than a separate skill.

FreeCAD still earns its place downstream: open `exports/wing.step` there for the
dimensioned drawing and the renders.

## Design parameters

| Parameter | Symbol | Effect |
|---|---|---|
| Span | b | Overall size; sets aspect ratio with area |
| Root chord | c_root | Scale |
| Taper ratio | λ = c_tip/c_root | Spanwise load distribution, induced drag |
| Sweep | Λ | Quarter-chord angle; delays transonic shock formation |
| Dihedral | Γ | Lateral (roll) stability |
| Washout | ε | Tip pitch-down; prevents tip stall, keeps aileron authority |

Sweep is applied to the **quarter-chord line**, not the leading edge. Sweeping
the leading edge instead is an easy slip that puts the quarter-chord at the
wrong angle for every taper ratio except 1 — there is a test pinning it down.

## Reference wing

| | |
|---|---|
| Span | 10.000 m |
| Root / tip chord | 1.600 / 0.720 m |
| Taper ratio | 0.45 |
| Sweep (quarter-chord) | 25° |
| Dihedral | 5° |
| Washout at tip | 3° |
| Section | NACA 2412 |
| **Planform area** | **11.6000 m²** |
| **Aspect ratio** | **8.6207** |
| **MAC** | **1.2156 m at y = 2.1839 m** |

## Validation

The kernel and the algebra are independent routes to the same wing, so they can
be checked against each other. 31 tests:

- **Volume** from the B-rep against the section area integrated along the span
  — two routes sharing no code, agreeing to 0.016%
- **MAC** closed form against numerical integration of c² over the semi-span
- **Sweep** — measured tip trailing-edge position against
  `0.25·c_root + (b/2)·tan Λ + 0.75·c_tip`
- **Dihedral** — measured tip height against `(b/2)·tan Γ` plus the section crown
- **Limiting case** — an untapered wing must give MAC = chord
- **Solid validity** — `BRepCheck_Analyzer` before export, because a
  non-manifold body meshes badly in CFD and is far harder to diagnose there
- **STEP round-trip** — re-read the export and confirm the volume matches
- **Export units** — a 10 m wing must re-read as 10 000 mm, not 10
- NACA sections against their published definition: 12% thickness at 30% chord

## Exports are in millimetres

The model is in metres, which is natural for an aircraft. The STEP and IGES
exports convert to millimetres, and that default was earned rather than chosen:
writing metres and declaring `SI_UNIT(.METRE.)` is correct by the standard, and
FreeCAD still opened the result at **1/1000 scale** — it read the raw numbers as
millimetres and ignored the declaration.

Most mechanical CAD assumes millimetres whatever the file says. The
interoperable choice is to meet that assumption rather than to be right and
unreadable. `to_step(..., unit="M")` still writes metres for a tool known to
honour the declaration.

## Two bugs worth recording

### The bounding box was 1.1% too big

`measured_bounds` originally used OpenCASCADE's default `Bnd_Box` via
`brepbndlib.Add`. That bounds a B-spline surface by its **control polygon**,
which lies outside the surface it defines — it over-reported the wing's height
by **1.1%**.

The tell was that the error stayed at exactly 0.008642 m whether the sections
were sampled at 60 points or 900. A sampling error shrinks with sampling; a
constant one is structural. `AddOptimal` computes a tight box and brings the
agreement to 0.004%.

A measurement function feeding a dimensioned drawing cannot carry a 1% error,
and nothing about the number looked wrong on its own.

### The export opened at 1/1000 scale

Covered above. Worth noting how it surfaced: not from a test, but from opening
the file in the tool it was meant for and reading the coordinate in the status
bar. Both bugs produced internally consistent numbers, and neither was visible
without an outside reference — the same pattern as project 03.

## The drawing

`drawings/wing-ga.png` — A4 landscape, third angle, millimetres. Plan and front
views at 1:50 with span, chords, quarter-chord sweep, dihedral, tip rise and
the MAC marked where it actually sits, plus a root section detail at 1:20 and a
title block carrying area, aspect ratio, taper and washout.

Generated from the same `Wing` object that builds the solid, so the drawing
cannot document a different wing from the one exported — which is the usual way
a drawing and a model come apart.

It is also **deterministic**: no date is stamped unless one is passed, so
regenerating an unchanged design produces a byte-identical file. A sheet that
changes without the design changing is not worth committing. Two tests hold
that: one asserting the bytes match across regenerations, and one asserting a
date *does* change them, so the determinism comes from omitting the timestamp
rather than from ignoring the argument.

The section detail earns its place on the sheet. At 51:1 span to thickness
neither the plan nor the front view shows the aerofoil at all — at 1:20 it is
legible, and a detail at its own scale is normal practice for exactly that
reason.

## Outstanding

- [x] Dimensioned general arrangement drawing — `drawings/wing-ga.png`
- [x] Planform and section figures, light and dark
- [x] Shaded 3D render for the site's product gallery — `figures/wing-3d-render.png`.
      Rendered standalone (three.js, not the live site) from the same
      `public/models/wing.glb` the site's own interactive viewer uses, so
      the lighting/shading matches exactly rather than being a separate
      pipeline. Not wired into `app/data.js`'s `products` array yet — that's
      a visible change to the live site, worth confirming before adding.
- [ ] Upload the STEP to viewer.autodesk.com for the CAD viewer — blocked on
      an Autodesk account and browser session, the same category of thing
      project 02's SimScale run is blocked on. `exports/wing.step` is
      already validated and upload-ready (see project 02's log for the
      `BRepCheck_Analyzer` check — same file).

## Log

| Date | What was done |
|---|---|
| 2026-08-19 | General arrangement drawing: plan and front at 1:50, root section detail at 1:20, title block, dimensioned throughout. First attempt was unusable — matplotlib sizes arrowheads in points scaled by font size, which drew 10 mm heads on an A4 sheet, and the two views overlapped. Rebuilt the dimension primitives as polygons in sheet coordinates. 49 tests. |
| 2026-08-19 | Planform and section figures. The 3D view reads as a flat plate because the wing is 51:1 span to thickness — true, but it hides the aerofoil, so the section drawing carries what a reviewer actually needs to see. Confirmed the section is a real cambered NACA 2412 with the tip rotated by its washout. 40 tests. |
| 2026-08-21 | Shaded 3D render, standalone three.js against the live site's own `wing.glb` and lighting setup. First framing attempts used the site's default `ModelStage` camera angle and orbited via synthetic mouse drag — the orbit never registered (Playwright's mouse events landed on the wrong `<canvas>` entirely: the page has two, and the site's fixed background engine mounts first, so an unscoped selector grabbed that one, not the model viewer's). Switched to a standalone render with an explicit camera position instead of fighting the interaction, which also surfaced that the exported glTF keeps the STEP file's native axis convention (X = chord, Y = span, Z = thickness/up) rather than converting to glTF's usual Y-up — confirmed by logging the actual bounding box rather than assuming it, since the first camera formula silently assumed Y was vertical and produced an edge-on, unusable view. Also validated `exports/wing.step` with pyOCC's `BRepCheck_Analyzer` (1 solid, 1 shell, 6 faces, no gaps) as prep for the Autodesk upload, which is a browser/account task outside what an agent can complete. |
| 2026-08-19 | Export units fixed. FreeCAD opened the metre-declared STEP at 1/1000 scale — it reads raw numbers as mm and ignores the SI_UNIT declaration. Exports now convert to mm by default, verified by re-reading a 10 m wing as 10 000 units. 36 tests. |
| 2026-08-19 | `airfoil.py` (NACA 4-digit, cosine spacing, closed TE) and `wing.py` (parametric loft on OCCT). STEP + IGES export, round-trip verified. Chose pyOCC over the FreeCAD GUI so the wing regenerates from parameters and can be tested. Found and fixed a 1.1% height over-report from the default bounding box bounding control points rather than the surface. 31 tests. |
