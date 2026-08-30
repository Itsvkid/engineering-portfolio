# 3D models

Drop `.glb` files here, then reference them from `app/data.js`:

```js
model: {
  src: "/models/nacelle.glb",
  title: "Nacelle geometry",
  description: "Parametric nacelle surface generated in pyOCC, benchmarked against CATIA.",
  autoRotate: false,
}
```

The viewer is code-split and only downloads three.js once a visitor scrolls to
it, so an unused model costs nothing.

## Getting from CAD to .glb

CATIA and OpenCASCADE both emit B-rep, which browsers cannot render — the model
has to be tessellated to a mesh first.

**From CATIA V5**
1. `File → Save As` → **STEP (.stp)**, or export **STL** directly if you do not
   need the assembly tree.
2. Open the STEP in [FreeCAD](https://www.freecad.org) (free) → select the body
   → `File → Export` → **glTF (.glb)**.

**From your pyOCC / OpenCASCADE pipeline** — you are already meshing there:

```python
from OCC.Extend.DataExchange import write_stl_file
write_stl_file(shape, "nacelle.stl", mode="binary",
               linear_deflection=0.1, angular_deflection=0.3)
```

Then convert and compress in one step:

```bash
npx gltf-pipeline -i nacelle.stl -o nacelle.glb --draco.compressionLevel 7
```

## Keep it small

Aim for **under 5 MB**. A nacelle surface at 0.1 mm linear deflection is far more
triangles than a 900px canvas can show — raise `linear_deflection` until the
silhouette stops changing, then stop. Check the result with
`ls -lh public/models/`.

If a file is missing or malformed the viewer degrades to a caption; it will not
break the page.
