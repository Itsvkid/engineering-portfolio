# Turbofan Atlas — `/turbofan`

An interactive 3D anatomy of a high-bypass turbofan, built the way the
human-anatomy explorers [Human Atlas](https://github.com/ashemag/human-atlas)
and [OMF Atlas](https://github.com/choxos/OMFAtlas) are built: the model
first, every part selectable, systems as layers, a separation control, guided
tours, and an honest line between what is transcribed, what is designed, and
what is schematic. The engine is the NASA/GE E³ Flight Propulsion System
(1978–83), the only large turbofan whose design reports are public.

This file is the working state of the page. It lives in the repository on
purpose, so anyone opening this folder can continue without any account-level
memory. The repo-wide pointer is
`Job-Search-2026/Job_Search-2026/GT-Design/Running.md`; this file is the
atlas-specific detail it points to.

## Layout of the code

| File | What it is |
|---|---|
| `page.js`, `TurbofanAtlas.js` | route, metadata (social card), client-only dynamic import |
| `atlas/Atlas.js` | the studio shell: reducer, deep links, keyboard, bottom dock |
| `atlas/panels.js` | chips, Systems / Part / Controls / Tour drawers, search, About |
| `atlas/Engine.js` | the R3F scene: wedge cutaway (two clipping planes), spool rotation, VSV instancing, camera driver, BVH picking, environment |
| `atlas/geometry.js` | procedural builders: lathe, shell, blade loft (parametric sections or printed coordinates), struts, bolts, pipes, mixer |
| `atlas/flowpath.js` | the E³ stations in metres; the two **assumed** stitching offsets (`HPC0`, `HPT0`) and the island radii |
| `atlas/parts-core.js` | gas generator, rotors, structure, exhaust: 80-odd parts with geometry recipes, text and tagged facts |
| `atlas/parts-systems.js` | the eleven external systems: fuel, control, air, oil, ignition, variable geometry, anti-ice, fire, vibration |
| `atlas/systems.js`, `atlas/tours.js` | the twelve systems with colours; the three tours |
| `atlas/data/e3-sections.js` | **generated** by `projects/09-e3-engine/tools/export_atlas_sections.py`: HPC Table XXII sections and LPT printed coordinates |
| `tools/` | headless render driver (`cdp.mjs`), geometry smoke test (`smoke.mjs`), poster script |

## Where the numbers come from

Every fact on the page carries a tag: `e3` (a report page, transcribed in
`projects/09-e3-engine/data/`), `schematic` (generic practice), `assumed`
(a value this model chose). The fact sheet is
`projects/09-e3-engine/data/atlas-facts.md`. **Change the sheet first, then
the page.** Engine claims go through `.claude/agents/gas-turbine-designer.md`
(see `CLAUDE.md`).

Geometry provenance, as of 2026-09-07:

- **Transcribed:** HPC hub/tip at 42 stations and all 21 rows' sections
  (Table XXI/XXII); HPT five stations (Fig. 3); LPT walls and all ten rows
  from the thirty printed sections; fan sections (CR-165148 Fig. 41),
  booster sections (Fig. 52), island stator and core OGV angles (Table VII);
  every blade and vane count; bearings, mounts, frames, mixer lobes.
- **Assumed, but no longer free:** fan axis → HPC rotor 1 = 1.034 m and
  HPC OGV → HPT vane 1 = 0.253 m. CR-159584 Table I p.6 gives the fan front
  flange → LPT exit as 3.180 m, which with the published HPC, HPT and LPT
  lengths caps the two together at 1.287 m. The sum is the table's; the
  split is the ratio read off that report's Fig. 1. They used to carry 1.42
  and 0.48, so the core was drawn 0.61 m long. Second splitter
  radius 0.611 m (58/42 area split); island top 0.705 m; nacelle and cowl
  lines; disc profiles; bolt counts on five of nine flanges.
- **Schematic:** HPT airfoil shapes (throat and aspect ratio only);
  anti-icing, fire loops and bottles, airborne vibration monitor, VBV doors,
  pipe and harness runs.

## Working on it

```sh
npm run dev                      # http://localhost:3000/turbofan
npx eslint app/turbofan
cd app/turbofan/tools && node --import "data:text/javascript,import { register } from 'node:module'; register('file://$PWD/node-resolve-hooks.mjs');" smoke.mjs
```

The smoke test builds every part's geometry in Node and reports triangle
counts and failures; run it after any change to `parts-*.js` or
`geometry.js`. Regenerate `atlas/data/e3-sections.js` with the exporter
after any change to `hpc-blade-sections.yaml` or `lpt-airfoils/*.csv`.

Headless renders (posters, social card, visual checks) use Microsoft Edge on
this machine through `tools/cdp.mjs`; see `tools/posters.sh`. Lessons that
cost time, all learned the hard way:

- Run renders **one at a time**. Parallel headless instances blank the
  canvas and can kill `next dev`.
- **Kill the browser after every render, and never retry in a loop.** A
  failed render leaves its Edge instance alive; a three-attempt retry loop
  once left 32 of them fighting over the software GPU, after which every
  render timed out and the script hung for four hours having produced two
  files out of nine. `posters.sh` now kills Edge after each render and
  reports a failure rather than retrying — rerun it for the ones that fail.
- Render from `next start`, not `next dev`.
- Pass the theme as `?theme=dark|light` rather than storing it in
  localStorage and navigating twice.
- Check the file size, not the exit code: a blank render is a valid PNG of
  about 7 KB, a real one is 150 KB and up.

Link parameters: `part=`, `camera=iso|front|side|top|aft`, `cam=x,y,z&at=x,y,z`,
`frame=1`, `cut=0`, `sep=0..1`, `shell=0.1..1`, `systems=a,b`, `tour=air|fuel|structure`,
`theme=dark|light`, `ui=0`.

## Design language

The atlas does **not** use the site's Instrument Grade treatment. That spec
suits an editorial page; on a tool it read as cramped, dim and amateur. The
chrome follows [OMF Atlas](https://omfatlas.xera.ac) instead: a light studio
stage with a soft radial falloff, white panels floating over it on a blur,
one calm accent, soft radii, generous spacing, and small sentence-case type
rather than uppercase mono.

What is taken from OMF Atlas and what is not:

- **Taken:** the light stage and its radial gradient, translucent panels on
  `backdrop-filter`, the segmented view-pill control, the vertical zoom
  stack, the live-dot stage caption, alpha borders rather than solid lines,
  and 7–11 px radii.
- **Not taken:** their layout. OMF Atlas puts a sidebar and an inspector
  either side of a head, which is roughly square. An engine is long and thin,
  so the chrome stays on the bottom edge and the stage keeps full width.
- **Kept from the portfolio:** the orange accent, so the page still belongs
  to the site it is reached from.

Mechanics worth knowing:

- The site's tokens (`--bg0`, `--fg0`, `--line`, `--accent`) are redefined
  inside `.atlas` rather than replaced, so Tailwind utilities already in the
  JSX pick up the atlas palette with no churn.
- Light is the tuned default here even though the site is dark-first. Both
  themes are supported and the toggle works.
- The canvas is **transparent**; the stage gradient is CSS behind it.
- The model palette is *deeper* in light than in dark, which is the opposite
  of the instinct: a pale metal on a light stage has no contrast and the
  engine washes out.
- The Canvas is declared `flat` (R3F re-applies filmic tone mapping on
  re-render otherwise, and the engine goes dim).
- The atlas CSS stays inside `@layer components` so Tailwind utilities win.

## Publishing

Commit, `git push` (Vercel deploys `main` to vinaykumar.is-a.dev), then
`./sync-public.sh --push` for the public mirror.

The sync publishes **HEAD**, not the working tree, so the mirror always
equals a commit. It used to copy working-tree files with `git ls-files`,
which skipped files that were not yet added while publishing the edits that
imported them; the mirror twice received source that could not compile. If
the tree is dirty the script now says so and names what it is leaving out.

Vercel's bot mitigation challenges the custom domain after a burst of
headless loads; it clears by itself.

## Future tasks, in order of value

1. **Core cowl is ~5 cm tight over the turbine.** Drawn at 0.60–0.628 m;
   CR-159584 Fig 1 reads 0.65–0.68. At y = 3.469 the cowl sits 1.6 cm off
   the LPT rotor-5 tip, which does not fit the LPT casing, its insulation
   and the four-sector LPT ACC manifold. Raising it narrows the bypass
   duct, so do it **together** with a re-check of the duct areas against
   the published 0.40–0.45 fan-duct Mach — that is why it was left out of
   the 2026-09-10 offset change rather than bundled into it.

2. **The four HPT chords are assumed, and need not be.** HPT Table IV p.12
   publishes axial-width solidity (0.71 / 0.96 / 1.07 / 1.06 for v1/b1/v2/
   b2); with the published counts and Fig 3 radii the axial widths follow
   as 3.33 / 2.75 / 4.83 / 3.30 cm. Vane 1 is currently ~34 % long. This
   is a promotion from `assumed` to derived-from-`e3`, not a guess.
3. **HPT airfoils from the report's figures** — CR-167955 Fig. 6 prints the
   four HPT airfoil shapes at three spans; digitise them (DATA-INDEX item 3)
   and loft them the way the LPT rows are, replacing the parametric guess.
4. **Disc profiles** — CR-167955 and the LPT report print disc cross-sections;
   digitise and replace the generic web-and-bore lathes (HPT discs, LPT
   discs, HPC discs, fan disc). Gives the "rotor, disc, spool" fidelity the
   owner asked for.
5. **Blade platforms and dovetails** on the fan, HPC rotor 1 and HPT blades;
   the inducer/expander (80 vanes) and CDP seal ahead of HPT disc 1; seal
   teeth on the interstage seals.

6. **Fan blade shroud** — the part-span shroud is a plain ring; the real one
   is per-blade shroud segments with tungsten-carbide faces.
7. **Mixer lobe shape** — 18 lobes of representative depth; the E³ mixer is
   a scalloped design, undimensioned. Only a drawing exists.
8. **Analytics on part selection** (Vercel event per `select`) so the
   owner learns what visitors click.

9. **Recording the tours** for the launch post: `?tour=air` with autoplay,
   30 s screen capture; the social card and posters are already rendered.
10. **Embed on the home page** — a click-to-load viewer in the feature band,
    reusing `Engine` with `ui=0`, lazy behind an IntersectionObserver.

## Done log

- **2026-09-10 — the geometry review, and two items above closed by it.**
  Started from the owner's "why does it look like a turbojet?". The
  architecture and the exhaust were right: the E³ FPS is long-duct
  mixed-flow, so the tube silhouette, the single C-D nozzle, the 18-lobe
  mixer and every turbine blade count were correct. The **inlet** was 58 %
  short. Behind that: `atlas-facts.md` said the FPS nacelle is
  undimensioned, which is true of CR-168219 and false of the programme —
  CR-159584 Table I p.6 is a full installation dimension table and had
  never been opened. That also closed the old "stitching from the
  cross-section" item from an unexpected direction: the published 318.0 cm
  turbomachinery length fixes the two offsets' *sum*, so only the split was
  ever open. Applied as 1.034 and 0.253 m against 1.42 and 0.48; the core
  had been 61 cm long and the blade envelope shortened by exactly that.
  Closures J8 and J9. The general lesson is in the designer agent's §9: a
  value marked "not published" may only mean "not in the report I read".

- **Figures are one build behind as of 2026-09-07 evening.** The four
  project figures and the social card in `public/` were rendered before the
  fan-module correction, so they still show the single-splitter island. Run
  `zsh app/turbofan/tools/posters.sh` to refresh them; nothing else depends
  on it.
- 2026-09-07 — first version: 142 parts, 12 systems, side panels. Then:
  bottom dock, three tours, home-page feature band and project entry, social
  card. Then: every blade row a printed aerofoil (Table XXII, LPT coordinates),
  bright palette, procedural environment, free-camera links. Then: fan and
  booster sections from CR-165148 Figs. 41/52, the quarter-stage second
  splitter and island exit vanes, HPT datum, thin six-sector bulkhead.
