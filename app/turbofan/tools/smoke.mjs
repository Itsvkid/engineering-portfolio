import { PARTS } from "../atlas/parts.js";
import { bladeGeometry } from "../atlas/geometry.js";
let tris = 0, verts = 0, fail = 0;
const t0 = performance.now();
for (const p of PARTS) {
  try {
    const g = p.kind === "vsvRow" ? bladeGeometry(p.vsv.spec) : p.build();
    const n = g.index ? g.index.count / 3 : g.attributes.position.count / 3;
    const v = g.attributes.position.count;
    tris += p.kind === "vsvRow" ? n * p.vsv.count : n; verts += v;
    if (!g.attributes.uv) console.log("no uv:", p.id);
    if (Number.isNaN(g.attributes.position.array[0])) console.log("NaN:", p.id);
  } catch (e) { fail++; console.log("FAIL", p.id, e.message.split("\n")[0]); }
}
console.log(`parts ${PARTS.length}, triangles ${tris.toLocaleString()}, vertices ${verts.toLocaleString()}, failures ${fail}, ${Math.round(performance.now()-t0)} ms`);
const ids = new Set(); for (const p of PARTS) { if (ids.has(p.id)) console.log("DUP id", p.id); ids.add(p.id); }
