# Figures

CFD contours, mesh screenshots, shadowgraph validation pairs — the evidence
behind each project. Drop images here and list them in `app/data.js`:

```js
figures: [
  {
    src: "/figures/jet-mach08-contour.png",
    alt: "Mach number contour of the controlled jet at Mach 0.8, showing the potential core ending at 4.2 nozzle diameters.",
    short: "Mach contour, M 0.8",
    caption: "Mach contour at M 0.8 with the Delta Tandem Tab fitted. The potential core closes at 4.2 D against 11.6 D for the uncontrolled baseline — the 64% reduction quoted above.",
  },
]
```

## The four fields

| Field | What it is for |
|---|---|
| `src` | Path from `public/`, so `/figures/name.png` |
| `alt` | **Describes the result**, for screen readers and for anyone whose images fail. "Mach contour showing the core closing at 4.2 D" — never "CFD plot" or "figure 1" |
| `short` | Grid label under the thumbnail, roughly four words |
| `caption` | Full sentence in the lightbox: what it shows *and what it proves* |

## Preparing the images

- **Format:** PNG for contour plots and line graphs (sharp edges, flat colour);
  JPEG only for photographs.
- **Size:** export around **1600px** on the long edge. Next.js generates the
  responsive sizes; anything larger is wasted bytes.
- **Crop the solver UI out.** Export the viewport, not a screenshot of Fluent
  with its ribbon and tree visible. A cropped plot reads as a result; a screen
  grab reads as a tutorial.
- **Keep the colour bar** — a contour plot without its scale proves nothing.
- **Label the axes** if the source plot has them.

Thumbnails are cropped to 16:10 in the grid but the lightbox shows the full
frame, so nothing important should sit right at the edge.
