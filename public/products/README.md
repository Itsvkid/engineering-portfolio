# Product renders

Images of parts and assemblies you designed — the CAD equivalent of a figure.
Drop them here, then list them in `products` in `app/data.js`:

```js
export const products = [
  {
    src: "/products/nacelle-assembly.png",
    alt: "Rendered nacelle assembly, shaded grey, showing the fan cowl split line and pylon interface.",
    short: "Nacelle assembly",
    tool: "CATIA V5",
    caption: "Full nacelle assembly modelled in CATIA V5. The fan cowl is a single parametric surface driven by the iCST section definition, so a change to the section propagates through the whole assembly.",
  },
];
```

## The five fields

| Field | What it is for |
|---|---|
| `src` | Path from `public/`, so `/products/name.png` |
| `alt` | **Describes the part**, for screen readers and when images fail. "Rendered nacelle assembly showing the fan cowl split line" — never "render 1" |
| `short` | Tile heading, roughly three words |
| `tool` | Shown beside the heading — `CATIA V5`, `SolidWorks`, `pyOCC`. This is what a reviewer scanning for CAD experience actually looks for |
| `caption` | Full sentence in the lightbox: what it is **and what was hard about it** |

While this array and `cadModels` are both empty the section shows a placeholder
frame. Adding the first entry to either one retires it — there is no flag to
unset.

## Preparing the images

- **Format:** PNG for shaded CAD renders and drawings; JPEG only for photographs.
- **Size:** around **1600px** on the long edge. Next.js generates the responsive
  sizes; anything larger is wasted bytes.
- **Crop the CAD UI out.** Export the viewport, not a screenshot of CATIA with
  its tree and toolbars. A cropped render reads as a part; a screen grab reads
  as a tutorial.
- **Use a plain background.** The tiles sit on a near-black page — a white or
  mid-grey studio background reads best. Avoid gradients and floors.
- **Shade it, do not render it glossy.** Neutral matte grey reads as engineering
  geometry; chrome and studio reflections read as a product advert.
- **One part per image.** An exploded view is one image; a contact sheet of six
  small parts is not.

Tiles are cropped to 4:3 in the grid but the lightbox shows the full frame, so
keep nothing important right at the edge.

## No renders yet?

Screenshot the model from the Autodesk viewer — it is a legitimate source for
these tiles and needs no CAD licence. See `docs/CAD_VIEWER.md`.
