import {
  BoxGeometry,
  BufferGeometry,
  CatmullRomCurve3,
  CylinderGeometry,
  Float32BufferAttribute,
  LatheGeometry,
  Matrix4,
  Quaternion,
  SphereGeometry,
  TorusGeometry,
  TubeGeometry,
  Vector3,
} from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

/**
 * Procedural geometry for the turbofan atlas.
 *
 * Everything is built in one "engine frame": the engine axis is +Y, the
 * intake at low y and the exhaust at high y, radius measured in the XZ
 * plane. That is the frame three.js's LatheGeometry rotates in, so every
 * casing, disc, drum and cone is a lathe of an [r, y] profile and needs no
 * further transform. The whole engine group is rotated once at the root so
 * the axis lands on world X, horizontal on screen.
 *
 * No mesh here is a scan. OMF Atlas builds its neurovascular anatomy as
 * "schematic" geometry fitted to landmarks on the real skull; this file
 * does the same for an engine: the landmarks are the hub and tip radii and
 * axial stations transcribed from the NASA E³ reports (see flowpath.js),
 * and everything drawn between them is teaching geometry, labelled so.
 */

const TAU = Math.PI * 2;

// ── Solids of revolution ──────────────────────────────────────────────────

/**
 * A solid of revolution from an [r, y] profile. The profile is an open
 * polyline (a casing wall drawn once) or a closed one (a wall with
 * thickness, drawn outer surface then back along the inner surface).
 * Segments is high because the fan is over two metres across and a
 * faceted rim is the first thing a reader notices.
 */
export function lathe(profile, segments = 96) {
  const points = profile.map(([r, y]) => ({ x: r, y }));
  return new LatheGeometry(
    points.map((p) => new Vector3(p.x, p.y, 0)),
    segments
  );
}

/**
 * A wall of constant thickness following an [r, y] centre line — the
 * usual way to draw a casing. Offsets the line outward and inward by
 * t/2 along the local normal and closes the ends, so the cutaway shows a
 * real wall rather than a zero-thickness skin.
 */
export function shell(centreLine, thickness, segments = 96) {
  const half = thickness / 2;
  const n = centreLine.length;
  const outer = [];
  const inner = [];
  for (let i = 0; i < n; i++) {
    const [r, y] = centreLine[i];
    const [r0, y0] = centreLine[Math.max(0, i - 1)];
    const [r1, y1] = centreLine[Math.min(n - 1, i + 1)];
    // Tangent along the line, normal pointing outward (larger r).
    let tr = r1 - r0;
    let ty = y1 - y0;
    const len = Math.hypot(tr, ty) || 1;
    tr /= len;
    ty /= len;
    const nr = ty;
    const ny = -tr;
    const sign = nr >= 0 ? 1 : -1;
    outer.push([r + sign * nr * half, y + sign * ny * half]);
    inner.push([r - sign * nr * half, y - sign * ny * half]);
  }
  return lathe([...outer, ...inner.reverse(), outer[0]], segments);
}

/** A plain annular ring (a flange, a seal land) between r0 and r1, from y0 to y1. */
export function ring(r0, r1, y0, y1, segments = 96) {
  return lathe(
    [
      [r0, y0],
      [r1, y0],
      [r1, y1],
      [r0, y1],
      [r0, y0],
    ],
    segments
  );
}

/** A thin torus lying in the plane y = const, for manifolds and unison rings. */
export function hoop(radius, tube, y, radialSegments = 10, tubularSegments = 96) {
  const g = new TorusGeometry(radius, tube, radialSegments, tubularSegments);
  g.rotateX(Math.PI / 2);
  g.translate(0, y, 0);
  return g;
}

// ── Blades ────────────────────────────────────────────────────────────────

/**
 * A cambered airfoil section as a closed polygon in the (a, t) plane —
 * a along the chord, t across it. NACA-style thickness on a circular-arc
 * camber line: enough shape that a fan blade, a compressor blade and a
 * turbine blade are told apart by their sections, which is what a reader
 * who has seen a real blade expects.
 */
function airfoilSection(chord, thicknessRatio, camberDeg, points = 14) {
  const camber = (camberDeg * Math.PI) / 180;
  const upper = [];
  const lower = [];
  for (let i = 0; i <= points; i++) {
    const s = i / points;
    // Cosine spacing: more points at the leading edge, where curvature lives.
    const x = 0.5 - 0.5 * Math.cos(Math.PI * s);
    // Parabolic camber line whose leading-edge slope is half the turning
    // angle: y = tan(θ/2)·x(1−x), max camber tan(θ/2)/4. An earlier draft
    // carried a stray factor of two, which bulged every turbine section.
    const yc = Math.tan(camber / 2) * x * (1 - x);
    const yt =
      thicknessRatio *
      5 *
      (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4);
    upper.push([x * chord, (yc + yt) * chord]);
    lower.push([x * chord, (yc - yt) * chord]);
  }
  return [...upper, ...lower.reverse().slice(1, -1)];
}

/**
 * One blade as a lofted solid. Span runs along local +X (radially out from
 * the hub), the engine axis is local +Y and the tangential direction local
 * +Z. Each spanwise station is an airfoil section rotated by the local
 * stagger angle (measured from the axial direction) and shifted so the
 * section's centroid stays on the stacking axis at x = span * s. Root and
 * tip may have different chord, stagger and camber, so a fan blade twists
 * from a highly-cambered root to a flat, swept tip the way the real E³
 * blade does, and a turbine blade can be short, thick and heavily turned.
 */
/**
 * Resample printed blade sections onto a finer ladder of stations.
 *
 * The loft between two stations is RULED — straight lines joining
 * corresponding section points. That is fine where the blade changes
 * slowly and visibly wrong where it does not. The E³ fan is printed at
 * seven heights across 50° of twist, and the widest gap between two of
 * them carries 13°; ruled across that span the surface facets, and a
 * blade that is in fact strongly twisted reads as a flat plate.
 *
 * This does not invent geometry. Every printed station is kept exactly as
 * printed and lands on a station of the output; the added stations sit
 * between them with their parameters linearly interpolated, which is the
 * same assumption the ruled surface was already making — just evaluated
 * as an aerofoil rather than as a straight line between two aerofoils.
 * The result is a smooth twisted surface with correct normals.
 */
export function resampleSections(sections, target = 25) {
  if (sections.length < 2 || target <= sections.length) return sections;
  const keys = Object.keys(sections[0]).filter((k) => typeof sections[0][k] === "number");
  const x0 = sections[0].x;
  const x1 = sections[sections.length - 1].x;
  const out = [];
  const stations = new Set(sections.map((s) => s.x));
  for (let i = 0; i <= target; i++) stations.add(x0 + ((x1 - x0) * i) / target);
  for (const x of [...stations].sort((a, b) => a - b)) {
    let j = 1;
    while (j < sections.length - 1 && sections[j].x < x) j += 1;
    const a = sections[j - 1];
    const b = sections[j];
    const t = b.x === a.x ? 0 : (x - a.x) / (b.x - a.x);
    const st = { ...a };
    for (const k of keys) st[k] = a[k] + (b[k] - a[k]) * t;
    st.x = x;
    out.push(st);
  }
  return out;
}

export function bladeGeometry({
  span,
  chordRoot,
  chordTip = chordRoot,
  staggerRoot,
  staggerTip = staggerRoot,
  camberRoot = 20,
  camberTip = camberRoot,
  thickness = 0.08,
  stations = 3,
  points = 10, // per surface; a 18-vertex section shades smoothly at screen scale
  sweepTip = 0, // axial lean of the tip relative to the root, in span units
  // A stator is a rotor's mirror image in the tangential direction: it
  // takes the swirl out that the rotor put in. Mirroring the section (and
  // the stagger with it) is what makes the alternating rows read as a
  // compressor rather than as rotors that happen not to turn.
  mirror = false,
  // Optional per-station geometry, hub first: [{ x, chord, stagger, camber,
  // thickness }], x measured from the root. When given, the root/tip
  // interpolation above is ignored and each printed section is lofted as
  // printed — this is how the HPC rows carry NASA's own Table XXII.
  sections: given,
}) {
  const positions = [];
  const uvs = [];
  const index = [];
  const sections = [];
  const stationList = given
    ? given
    : Array.from({ length: stations + 1 }, (_, k) => {
        const s = k / stations;
        return {
          x: span * s,
          chord: chordRoot + (chordTip - chordRoot) * s,
          stagger: staggerRoot + (staggerTip - staggerRoot) * s,
          camber: camberRoot + (camberTip - camberRoot) * s,
          thickness,
          lean: sweepTip * span * s * s,
        };
      });
  const sign = mirror ? -1 : 1;
  for (const st of stationList) {
    const section = airfoilSection(st.chord, st.thickness ?? thickness, st.camber, points);
    const stagger = (sign * st.stagger * Math.PI) / 180;
    const cos = Math.cos(stagger);
    const sin = Math.sin(stagger);
    const lean = st.lean ?? 0;
    sections.push(
      section.map(([a, t0]) => {
        const t = sign * t0;
        const ac = a - st.chord * 0.4; // stack about 40 % chord
        return [st.x, ac * cos - t * sin + lean, ac * sin + t * cos];
      })
    );
  }
  stations = sections.length - 1;
  const m = sections[0].length;
  // Indexed skin: one vertex per section point per station, shared between
  // the quads either side, so normals are smooth and memory is a fraction
  // of a triangle soup. A row of 156 blades stays under 100 KB.
  for (let k = 0; k <= stations; k++) {
    for (let i = 0; i < m; i++) {
      positions.push(...sections[k][i]);
      uvs.push(k / stations, i / m);
    }
  }
  for (let k = 0; k < stations; k++) {
    for (let i = 0; i < m; i++) {
      const j = (i + 1) % m;
      const a = k * m + i;
      const b = (k + 1) * m + i;
      const c = (k + 1) * m + j;
      const d = k * m + j;
      index.push(a, b, c, a, c, d);
    }
  }
  // Root and tip caps: a fan from the leading-edge vertex of that section.
  const base = (k) => k * m;
  for (let i = 1; i < m - 1; i++) {
    index.push(base(0), base(0) + i + 1, base(0) + i);
    index.push(base(stations), base(stations) + i, base(stations) + i + 1);
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(positions, 3));
  g.setAttribute("uv", new Float32BufferAttribute(uvs, 2));
  g.setIndex(index);
  g.computeVertexNormals();
  return g;
}

/**
 * A blade lofted from transcribed section coordinates, already in engine
 * space: each section is a closed polygon of [r, y, rtheta] points (radius,
 * axial station, tangential arc length), hub first. Used for the E³ LPT,
 * whose thirty airfoil sections are printed in the report and transcribed
 * in the project; nothing about these blades is drawn by hand. The
 * geometry sits at its true radius and station, so a row is made by
 * rotating copies about the axis rather than translating them.
 */
export function bladeFromCoords(sections) {
  const positions = [];
  const uvs = [];
  const index = [];
  const m = sections[0].length;
  const n = sections.length;
  sections.forEach((sec, k) => {
    sec.forEach(([r, y, rt], i) => {
      const phi = rt / r;
      positions.push(Math.cos(phi) * r, y, -Math.sin(phi) * r);
      uvs.push(k / (n - 1), i / m);
    });
  });
  for (let k = 0; k < n - 1; k++) {
    for (let i = 0; i < m; i++) {
      const j = (i + 1) % m;
      const a = k * m + i;
      const b = (k + 1) * m + i;
      const c = (k + 1) * m + j;
      const d = k * m + j;
      index.push(a, b, c, a, c, d);
    }
  }
  const base = (k) => k * m;
  for (let i = 1; i < m - 1; i++) {
    index.push(base(0), base(0) + i + 1, base(0) + i);
    index.push(base(n - 1), base(n - 1) + i, base(n - 1) + i + 1);
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(positions, 3));
  g.setAttribute("uv", new Float32BufferAttribute(uvs, 2));
  g.setIndex(index);
  g.computeVertexNormals();
  return g;
}

/** A row of coordinate blades: rotated copies about the axis, merged. */
export function bladeRowFromCoords(sections, count) {
  const blade = bladeFromCoords(sections);
  const parts = [];
  for (let i = 0; i < count; i++) {
    const g = blade.clone();
    g.rotateY((i / count) * TAU);
    parts.push(g);
  }
  const merged = mergeGeometries(parts, false);
  blade.dispose();
  parts.forEach((p) => p.dispose());
  return merged;
}

/**
 * Instance matrices for a ring of `count` blades whose roots sit on radius
 * rHub at axial station y. `offsetTurn` lets a stator row be clocked
 * half a pitch from its neighbours so the alternating rows do not line up.
 */
export function bladeRingMatrices(count, rHub, y, offsetTurn = 0) {
  const out = [];
  const m = new Matrix4();
  const q = new Quaternion();
  const axis = new Vector3(0, 1, 0);
  const pos = new Vector3();
  for (let i = 0; i < count; i++) {
    const theta = ((i + offsetTurn) / count) * TAU;
    q.setFromAxisAngle(axis, theta);
    pos.set(Math.cos(theta) * rHub, y, -Math.sin(theta) * rHub);
    m.compose(pos, q, new Vector3(1, 1, 1));
    out.push(m.clone());
  }
  return out;
}

/**
 * A single blade merged `count` times into one BufferGeometry — one draw
 * call per row and a normal mesh (not instanced), so a clipping plane,
 * a hover highlight and the separation offset all behave exactly as they
 * do for every other part. At 630 LPT blades this is still only a few
 * hundred thousand triangles across the whole engine.
 */
export function bladeRow(bladeSpec, count, rHub, y, offsetTurn = 0) {
  const blade = bladeGeometry(bladeSpec);
  const parts = bladeRingMatrices(count, rHub, y, offsetTurn).map((m) =>
    blade.clone().applyMatrix4(m)
  );
  const merged = mergeGeometries(parts, false);
  blade.dispose();
  parts.forEach((p) => p.dispose());
  return merged;
}

/**
 * A tip shroud: the ring of interlocking platforms a shrouded turbine row
 * carries at its tips (the E³ LPT is shrouded; its HPT and HPC are not).
 */
export function tipShroud(rTip, y, width, thickness = 0.008) {
  return ring(rTip, rTip + thickness, y - width / 2, y + width / 2);
}

// ── Struts, bolts, probes ─────────────────────────────────────────────────

/**
 * Radial struts between rInner and rOuter at station y — a frame. Built as
 * thin airfoil-ish boxes and merged. `clockOffsetDeg` rotates the set so a
 * strut can sit at the 6 o'clock position where the radial drive runs.
 */
export function struts(count, rInner, rOuter, y, chord, thickness, clockOffsetDeg = 0) {
  const parts = [];
  const len = rOuter - rInner;
  for (let i = 0; i < count; i++) {
    const g = new BoxGeometry(len, chord, thickness);
    g.translate(rInner + len / 2, 0, 0);
    const theta = ((i / count) * TAU) + (clockOffsetDeg * Math.PI) / 180;
    g.rotateY(theta);
    g.translate(0, y, 0);
    parts.push(g);
  }
  return mergeGeometries(parts, false);
}

/**
 * A ring of hexagon-headed bolts around a flange: heads sit proud of the
 * flange face at radius r, axis parallel to the engine axis. Merged into
 * one geometry per flange.
 */
export function boltRing(count, r, y, headSize = 0.022, headHeight = 0.014, shank = 0.03) {
  const parts = [];
  for (let i = 0; i < count; i++) {
    const theta = (i / count) * TAU;
    const head = new CylinderGeometry(headSize, headSize, headHeight, 6);
    head.translate(r, y + headHeight / 2, 0);
    head.rotateY(theta);
    const body = new CylinderGeometry(headSize * 0.5, headSize * 0.5, shank, 8);
    body.translate(r, y - shank / 2, 0);
    body.rotateY(theta);
    parts.push(head, body);
  }
  return mergeGeometries(parts, false);
}

/** A set of radial probes (thermocouples, pressure rakes) around a casing. */
export function probeRing(count, rOuter, rInner, y, radius = 0.012, clockOffsetDeg = 0) {
  const parts = [];
  const len = rOuter - rInner;
  for (let i = 0; i < count; i++) {
    const g = new CylinderGeometry(radius, radius * 0.8, len, 8);
    g.rotateZ(Math.PI / 2);
    g.translate(rInner + len / 2, 0, 0);
    // A boss at the casing end so the probe reads as bolted-on hardware.
    const boss = new CylinderGeometry(radius * 2.2, radius * 2.2, len * 0.12, 12);
    boss.rotateZ(Math.PI / 2);
    boss.translate(rOuter - len * 0.06, 0, 0);
    const theta = (i / count) * TAU + (clockOffsetDeg * Math.PI) / 180;
    g.rotateY(theta);
    boss.rotateY(theta);
    g.translate(0, y, 0);
    boss.translate(0, y, 0);
    parts.push(g, boss);
  }
  return mergeGeometries(parts, false);
}

/**
 * A ring of doors in a cowl (the variable bleed valves): flat plates on
 * radius r at station y, hinged open by `openDeg` at the aft edge.
 */
export function doorRing(count, r, y, width, length, openDeg = 0) {
  const parts = [];
  const t = 0.012;
  for (let i = 0; i < count; i++) {
    const g = new BoxGeometry(t, length, width);
    g.translate(0, -length / 2, 0); // hinge at the aft edge (+y end)
    g.rotateZ((openDeg * Math.PI) / 180);
    g.translate(r, y + length / 2, 0);
    g.rotateY((i / count) * TAU);
    parts.push(g);
  }
  return mergeGeometries(parts, false);
}

// ── Pipes, wires, boxes ───────────────────────────────────────────────────

/**
 * World position from engine-frame cylindrical coordinates: axial station
 * y (metres), radius r, and clock position in degrees seen from the front
 * with 12 o'clock at the top (+X in the engine frame maps to the top once
 * the root group is rotated; see Engine.js).
 */
export function cyl(y, r, clockDeg) {
  // The root group rotates the engine frame by −90° about Z, which sends
  // engine +Y to world +X (flow left to right) and engine +X to world −Y.
  // So 12 o'clock is engine −X. Clock runs aft-looking-forward, the
  // convention the E³ reports use, which puts 3 o'clock at engine −Z.
  const a = (clockDeg * Math.PI) / 180;
  return new Vector3(-Math.cos(a) * r, y, -Math.sin(a) * r);
}

/** The rotateY angle that carries a point placed at engine +X to a clock position. */
function clockTurn(clockDeg) {
  return ((180 - clockDeg) * Math.PI) / 180;
}

/** A pipe or wire along a smooth curve through engine-frame [y, r, clock] points. */
export function pipe(points, radius = 0.02, segments = 64) {
  const curve = new CatmullRomCurve3(points.map(([y, r, c]) => cyl(y, r, c)), false, "catmullrom", 0.4);
  return new TubeGeometry(curve, segments, radius, 10, false);
}

/**
 * A box-shaped line replaceable unit (a pump, a control, an exciter) sitting
 * tangent to the engine at [y, r, clock], with its long side along the axis.
 * The box is rotated so its "down" face points at the engine axis.
 */
export function unit(y, r, clockDeg, size, corner = 0) {
  const [sx, sy, sz] = size; // sx radial, sy axial, sz tangential
  const g = corner > 0 ? new BoxGeometry(sx, sy, sz, 2, 2, 2) : new BoxGeometry(sx, sy, sz);
  g.translate(r + sx / 2, 0, 0);
  g.rotateY(clockTurn(clockDeg));
  g.translate(0, y, 0);
  return g;
}

/** A cylinder-shaped unit (a bottle, a filter, an accumulator) with the same placement. */
export function drum(y, r, clockDeg, radius, length, axial = true) {
  const g = new CylinderGeometry(radius, radius, length, 24);
  if (!axial) g.rotateZ(Math.PI / 2);
  g.translate(r + radius, 0, 0);
  g.rotateY(clockTurn(clockDeg));
  g.translate(0, y, 0);
  return g;
}

/** A small sphere: a sensor head, a chip detector, a bearing ball. */
export function blob(y, r, clockDeg, radius) {
  const g = new SphereGeometry(radius, 16, 12);
  const p = cyl(y, r, clockDeg);
  g.translate(p.x, p.y, p.z);
  return g;
}

// ── Mixer ─────────────────────────────────────────────────────────────────

/**
 * A lobed forced mixer: the wall radius is r0(y) plus a sinusoidal lobe
 * whose amplitude grows from zero at the front to `depth` at the trailing
 * edge, so the front matches the round core duct and the back is the
 * scalloped crown seen on every mixed-flow turbofan. Lobes = 18 on the E³.
 */
export function mixer(lobes, y0, y1, rFront, rBack, depth, thetaSegments = 288, axialSegments = 24) {
  const positions = [];
  const uvs = [];
  const idx = [];
  for (let j = 0; j <= axialSegments; j++) {
    const s = j / axialSegments;
    const y = y0 + (y1 - y0) * s;
    const r0 = rFront + (rBack - rFront) * s;
    const amp = depth * s * s;
    for (let i = 0; i <= thetaSegments; i++) {
      const theta = (i / thetaSegments) * TAU;
      const r = r0 + amp * Math.cos(lobes * theta);
      positions.push(Math.cos(theta) * r, y, -Math.sin(theta) * r);
      uvs.push(i / thetaSegments, s);
    }
  }
  const w = thetaSegments + 1;
  for (let j = 0; j < axialSegments; j++) {
    for (let i = 0; i < thetaSegments; i++) {
      const a = j * w + i;
      const b = a + 1;
      const c = a + w;
      const d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(positions, 3));
  g.setAttribute("uv", new Float32BufferAttribute(uvs, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** Merge helper for parts built from several primitives. */
export function merge(geometries) {
  return mergeGeometries(geometries, false);
}
