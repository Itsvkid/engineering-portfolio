# 03 — Aircraft flight performance calculator

**Moved to its own repository:**
<https://github.com/Itsvkid/flight-performance-calculator>

The code, figures and validation report live there with their full history. It
was split out once complete because five focused repositories read better on a
GitHub profile than one folder inside a website repo — and because a reviewer
sent to a repository should land on the project, not on a Next.js site.

## What it is

Classical flight-performance metrics from first principles: ISO 2533 atmosphere,
parabolic drag polar, thrust lapse with altitude and Mach, climb, ceilings,
Breguet range and payload-range. 52 tests. Validated against published data for
the 737-800, A320-200 and 777-300ER.

## Results worth quoting

- **Service ceiling within 8%** across a 4.5× mass range
- **(L/D)max 17-18**, the right band for a jet transport
- **Maximum speed is not usable above Mach 0.8** — the polar has no wave-drag
  term, so the model predicts M 0.98-1.09 for aircraft that cruise at 0.78-0.84

That last one is the most valuable finding, and it belongs in the write-up
rather than hidden: it was invisible to every unit test, because the number was
self-consistent and simply not physical.

## For the website

Figures are in the repository under `figures/`. To use them on the site, copy
into `public/figures/` and add entries to a project's `figures` array in
`app/data.js` — see `public/figures/README.md` for the field format.
