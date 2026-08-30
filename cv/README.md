# CV

The CV had no source under version control. Only the compiled PDF was
committed — a binary nobody could diff, dated 19 July 2026 and listing two
projects at a point when eleven existed.

| File | What it is |
|---|---|
| `cv.tex` | The source. Stock LaTeX packages only, no custom class. |
| `cv.txt` | Plain text, for application portals that mangle PDFs. |
| `../public/Vinaykumar_Venkateshkumar_CV.pdf` | Build artefact, served by the site. |

## Compiling

```bash
brew install tectonic          # once, ~20 MB
tectonic -X compile cv.tex --outdir .
cp cv.pdf ../public/Vinaykumar_Venkateshkumar_CV.pdf
```

[Tectonic](https://tectonic-typesetting.github.io/) is a single
self-contained binary that downloads exactly the packages a document
needs and caches them, rather than installing a multi-gigabyte
distribution. MacTeX would work too and is closer to the original — the
old PDF's metadata reads `pdfTeX-1.40.27` — but it is a ~4 GB download to
typeset two pages.

The published PDF is built from this source and the two agree. **Rebuild
and re-copy after any edit**, or the site serves a stale CV; that is
exactly how the previous one drifted five weeks out of date.

### Two things that bite

Tectonic runs XeTeX, not pdfTeX, and the source is written to survive
both:

- **No literal non-ASCII in the body.** A raw `·` rendered as `û` —
  `inputenc` and `fontenc` disagreeing about byte 0xB7 under XeTeX. Use
  `\textperiodcentered`, `---` for em dashes, and macros generally.
- **`\varnothing` is not a diameter symbol.** It needs `amssymb`, and it
  means *empty set*. `\O` is the right glyph, present in every font.

## What changed, and why

Retargeted from **"propulsion/CFD graduate seeking a propulsion, CFD or
aircraft design role"** to **design engineer with propulsion as the
domain** — which keeps aerospace systems and engine suppliers in scope
while making the CAD and drawing work the headline rather than a
footnote.

- **Summary** leads with the design deliverables — GD&T, limits and fits,
  stack-up, sheet metal, DFM — because that is what a design manager
  screens for, and none of it appeared anywhere on the old CV.
- **Skills** gained a *Mechanical Design* block, which did not exist. The
  old CAD line named four tools and no standards.
- **Projects** split into *Design* and *Propulsion and Analysis*, design
  first. The old CV listed two projects; this leads with the drawing pack
  and the sheet-metal bracket, keeps the thesis and the BEng FYP, and
  points at the site for the remaining six.
- **Every project carries a number that can be checked** — 0.019% fit RMS,
  1.07% volume agreement, RMS Cp 0.65, 64–76% core-length reduction. A
  claim with a figure attached survives a phone screen; one without does
  not.

Education, experience and certifications are unchanged.

## Keeping it honest

The design projects are self-directed work, and the CV says so by placing
them under *Projects* rather than *Experience*. The one piece of
industrial experience is the AIESL internship, and it is described as what
it was — a maintenance rotation, not design work.
