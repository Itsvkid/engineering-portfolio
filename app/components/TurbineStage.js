"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { useMemo, useRef, useSyncExternalStore } from "react";
import {
  BufferGeometry,
  CylinderGeometry,
  EdgesGeometry,
  ExtrudeGeometry,
  Float32BufferAttribute,
  LatheGeometry,
  Matrix4,
  Shape,
  Vector2,
  Vector3,
} from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { getEffectiveTheme, subscribeToTheme } from "../lib/theme";

/**
 * The heavy half of the site's background — three.js + R3F land in this
 * chunk, code-split via next/dynamic in TurbineBackground so the main bundle
 * stays lean. Loads eagerly rather than behind an IntersectionObserver (the
 * hero is above the fold by definition, and TurbineBackground is now fixed
 * behind the whole page, not scoped to the hero).
 *
 * A complete twin-spool turbofan core, drawn as line art and viewed from an
 * isometric-ish 3/4 angle — not a single fan face. Two independent spools:
 * LP (low-pressure compressor + spinner + low-pressure turbine) and HP
 * (high-pressure compressor + high-pressure turbine), each its own rotating
 * group at its own speed, exactly like a real twin-spool engine — the HP
 * spool visibly spins faster than the LP spool. Every part is a real solid
 * (extrude/lathe/cylinder), reduced to its silhouette + crease edges via
 * EdgesGeometry and drawn unlit, the same move a manufacturer's cutaway
 * diagram makes. Each stage's ring of blades is instanced by baking a
 * transform into a cloned edge geometry per blade and merging the whole ring
 * into one BufferGeometry (mergeGeometries) — one draw call per stage rather
 * than one per blade, which matters for a canvas that never stops rendering.
 */

const MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeToMotion(onChange) {
  const query = window.matchMedia(MOTION_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

// Matches Tailwind's `md` breakpoint (768px) — the same width TurbineBackground
// and the rest of the site already treat as "mobile" (nav collapses, CadOverlay
// hides below it). The engine's long axis runs horizontally by design (a real
// engine's own proportions), which is exactly wrong for a narrow, tall
// viewport — it either overflows the sides or shrinks to a sliver. Rolling
// the whole rendered scene 90° in screen space on mobile, rather than
// re-deriving the inner 3/4-elevation tilt for a second aspect ratio, reuses
// every already-tuned framing decision (camera zoom, the casing/nacelle
// silhouette, the combustor bulge) exactly as-is — just spun.
const MOBILE_QUERY = "(max-width: 767px)";

function subscribeToViewport(onChange) {
  const query = window.matchMedia(MOBILE_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

const EDGE_ANGLE = 18; // degrees — below this, adjacent faces merge into one line

// Materials are drawn on a canvas, which can't recolour itself under a CSS
// media query — this is the same swap globals.css does for figures, done in
// JS. The HP spool is drawn a shade warmer than the LP spool — a real
// technical diagram's way of telling two mechanically independent shafts
// apart at a glance, and it doubles as a second, more restrained accent tying
// into the site's orange.
// `structure` is a distinct third tier, not just "faint at higher opacity" —
// the casing/nacelle/combustor outlines are the shapes that make this read
// as a gas turbine at a glance, and they were getting lost in the same
// low-contrast tone as background texture (flanges, injectors, stator
// combs). Sits between `faint` and `lp` in contrast, so the hierarchy reads:
// structure (primary silhouette) > lp/hp (rotating hardware) > faint (detail
// texture), instead of everything competing at one value.
// `combustor` was first tried as a reuse of `hp` — the combustor sits
// mechanically downstream of the HP compressor, so it seemed like a natural
// fit. It wasn't: the HP compressor and turbine blade rings that surround
// the combustor in screen space are *already* drawn in `hp`, so colouring
// the combustor the same tone made it disappear into that cluster rather
// than stand out from it. A rust/terracotta distinct from both `hp`'s
// amber and `structure`'s grey-beige — confirmed by isolating just the
// casing and combustor in the canvas and inspecting the render, not by
// eyeballing hex values against each other.
const PALETTE = {
  dark: { lp: "#a89f8f", hp: "#c39a63", faint: "#5f594c", structure: "#948a74", combustor: "#b56a45" },
  light: { lp: "#7d7460", hp: "#96703a", faint: "#a89f8c", structure: "#7c7259", combustor: "#9c5330" },
};

// Compressor blades: long, thin, swept — root at x=0, tip at x=1.
function compressorBladeShape() {
  const s = new Shape();
  s.moveTo(0, -0.06);
  s.quadraticCurveTo(0.4, -0.11, 0.84, -0.05);
  s.quadraticCurveTo(0.96, -0.02, 1, 0);
  s.quadraticCurveTo(0.96, 0.025, 0.84, 0.06);
  s.quadraticCurveTo(0.4, 0.13, 0, 0.07);
  s.closePath();
  return s;
}

// Stator vanes: short, straight, static — the stationary row a real
// compressor alternates with every rotor row. Blueprints show this
// alternation as a dense "comb" pattern; a rotor-only engine never gets it.
function statorBladeShape() {
  const s = new Shape();
  s.moveTo(0, -0.045);
  s.lineTo(0.55, -0.06);
  s.lineTo(0.62, 0);
  s.lineTo(0.55, 0.06);
  s.lineTo(0, 0.045);
  s.closePath();
  return s;
}

// Turbine blades: short and wide-chorded — a distinct silhouette so a
// turbine stage never reads as "just another compressor row".
function turbineBladeShape() {
  const s = new Shape();
  s.moveTo(0, -0.1);
  s.quadraticCurveTo(0.26, -0.17, 0.56, -0.09);
  s.quadraticCurveTo(0.68, -0.04, 0.72, 0.02);
  s.quadraticCurveTo(0.6, 0.1, 0.38, 0.16);
  s.quadraticCurveTo(0.15, 0.2, 0, 0.1);
  s.closePath();
  return s;
}

const EXTRUDE_COMPRESSOR = { depth: 0.09, bevelEnabled: false, curveSegments: 6 };
const EXTRUDE_STATOR = { depth: 0.06, bevelEnabled: false, curveSegments: 4 };
const EXTRUDE_TURBINE = { depth: 0.14, bevelEnabled: false, curveSegments: 6 };

// A lathed bullet-shaped spinner nose and a tapered tail cone — rounded
// solids of revolution, not flat-ended cylinders.
const SPINNER_PROFILE = [
  [0, 0.62],
  [0.1, 0.52],
  [0.22, 0.34],
  [0.3, 0.12],
  [0.34, 0],
];
const TAILCONE_PROFILE = [
  [0.34, 0],
  [0.3, -0.14],
  [0.2, -0.34],
  [0.08, -0.5],
  [0, -0.58],
];

// Compressor stages are drum-built: one continuous tapered rotor that
// several blade rows mount to, rather than a disc per stage. These profiles
// are [radius, z] pairs in absolute engine-Z (no extra position offset is
// applied to the drum groups), stepping through each stage's hub radius so
// the drum reads as the thing the blade rings are actually attached to.
const LP_DRUM_FRONT_PROFILE = [
  [0.58, 1.22],
  [0.62, 1.05],
  [0.6, 0.94],
  [0.56, 0.84],
  [0.5, 0.72],
];
const LP_DRUM_REAR_PROFILE = [
  [0.4, -0.54],
  [0.48, -0.68],
  [0.52, -0.82],
  [0.56, -0.96],
  [0.5, -1.1],
];
const HP_DRUM_PROFILE = [
  [0.5, 0.66],
  [0.46, 0.56],
  [0.44, 0.46],
  [0.41, 0.36],
  [0.39, 0.27],
  [0.37, 0.18],
  [0.35, 0.1],
];

// The combustor sits in the gap between the last HPC stage and the HPT — a
// barrel-shaped can, static (real combustors don't rotate). Tracks the new
// bulge in CASING_PROFILE above (same z-range, radius kept ~0.1 inside it),
// so the can now reads as the thing the casing is visibly flaring to clear,
// not just another line buried in the hub cluster.
const COMBUSTOR_PROFILE = [
  [0.35, 0.14],
  [0.58, 0.0],
  [0.64, -0.12],
  [0.56, -0.26],
  [0.46, -0.36],
];

// The flame-tube liner nested just inside the combustor's outer case — real
// combustors are double-walled, and a single outline read as a hollow can
// rather than a hot section. Traces the same shape, pulled in and shortened.
const COMBUSTOR_LINER_PROFILE = [
  [0.29, 0.09],
  [0.48, -0.02],
  [0.53, -0.13],
  [0.46, -0.24],
  [0.37, -0.32],
];

// Fuel injector/igniter stubs on the combustor dome — the ring of nozzles
// every real annular combustor mounts at its forward face, poking into the
// airflow rather than the dome just being a bare cap.
const INJECTORS = { id: "injectors", z: 0.16, radius: 0.35, count: 18 };

// Two-stage LP compressor (front, larger/longer blades), three-stage HP
// compressor (smaller, more numerous blades — the annulus tapers as the gas
// compresses), then across the combustor gap: one HP turbine stage (wide,
// short blades) and two LP turbine stages (growing again as gas expands).
// `radius` is where each blade's root sits (the hub surface); `scale` is the
// blade's length as a fraction of that radius, so the tip lands at roughly
// radius * (1 + scale) — every earlier draft left this out and let the
// (much longer) unscaled blade shape overshoot into neighbouring stages,
// which is what turned the whole engine into a tangle.
const STAGES = [
  { id: "lpc1", z: 1.05, radius: 0.62, scale: 0.34, count: 20, stagger: 0.5, kind: "compressor", spool: "lp" },
  { id: "lpc2", z: 0.84, radius: 0.56, scale: 0.3, count: 22, stagger: 0.46, kind: "compressor", spool: "lp" },
  { id: "hpc1", z: 0.56, radius: 0.46, scale: 0.24, count: 24, stagger: 0.44, kind: "compressor", spool: "hp" },
  { id: "hpc2", z: 0.36, radius: 0.41, scale: 0.21, count: 26, stagger: 0.42, kind: "compressor", spool: "hp" },
  { id: "hpc3", z: 0.18, radius: 0.37, scale: 0.19, count: 28, stagger: 0.4, kind: "compressor", spool: "hp" },
  { id: "hpt1", z: -0.4, radius: 0.4, scale: 0.26, count: 16, stagger: 0.48, kind: "turbine", spool: "hp" },
  { id: "lpt1", z: -0.68, radius: 0.48, scale: 0.3, count: 14, stagger: 0.46, kind: "turbine", spool: "lp" },
  { id: "lpt2", z: -0.96, radius: 0.56, scale: 0.34, count: 14, stagger: 0.44, kind: "turbine", spool: "lp" },
];

// Static (non-rotating) stator/guide-vane rows sitting between rotor stages
// — the alternating rotor-stator pattern is what makes a real compressor
// section read as a compressor rather than a stack of identical fans. `igv`
// is the inlet guide vane row ahead of LPC1 — every real fan/compressor inlet
// has one, and without it the nose looked like it fed straight into a rotor.
const STATORS = [
  { id: "igv", z: 1.16, radius: 0.61, scale: 0.2, count: 20 },
  { id: "s1", z: 0.945, radius: 0.59, scale: 0.24, count: 22 },
  { id: "s2", z: 0.46, radius: 0.435, scale: 0.18, count: 25 },
  { id: "s3", z: 0.27, radius: 0.39, scale: 0.16, count: 27 },
];

// Bolted flange joints — where a real engine casing splits into
// manufacturable/removable sections, cutaways show a ring of fastener heads.
// `radius`/`z` are picked to sit right on the CASING_PROFILE line at that
// station. Drawn as short radial ticks poking past the casing, not a solid
// ring, so they read as fasteners rather than another hoop line.
const FLANGES = [
  { id: "f1", z: 1.05, radius: 0.9, count: 44 },
  { id: "f2", z: -0.16, radius: 0.74, count: 36 },
  { id: "f3", z: -0.96, radius: 0.85, count: 40 },
];

// Exhaust mixer lobes — the scalloped, alternating-radius trailing edge a
// real turbofan nozzle has where the core exhaust mixes with bypass air,
// instead of the tail cone just tapering to a bare point.
const NOZZLE_LOBE_COUNT = 12;

// The nacelle/fan cowl — the outer skin every installed turbofan actually
// wears, standing well clear of the core casing so the gap between the two
// reads as the bypass duct it is. A real fan cowl is short relative to the
// whole core: it wraps the fan and the compressor section, then ends well
// ahead of the combustor, leaving the core casing, combustor bulge, turbines
// and nozzle exposed downstream — exactly the "installed nacelle over a
// visible core" cutaway this profile traces, closest to the owner's own
// nacelle-installation-aerodynamics research of anything on this canvas.
// Offset ~0.3–0.35 above the casing's own radius at each matching station —
// a first pass kept this to ~0.15–0.2, worried a wider ring would repeat the
// pylon's mistake below (projecting as a shape disconnected from the core
// under this canvas's steep rotation). It didn't: the pylon's problem was a
// short feature parked at a z-station well outside the core's own footprint,
// not radius by itself. A profile that still tracks the casing's z-range
// stays anchored regardless of offset, and a tight ~0.15–0.2 gap read as no
// gap at all once drawn at real screen size — indistinguishable from the
// casing it was meant to stand apart from. Widened here so the duct between
// the two lines is actually visible.
const NACELLE_PROFILE = [
  [1.23, 1.95],
  [1.34, 1.72],
  [1.32, 1.45],
  [1.23, 1.1],
  [1.12, 0.75],
  [1.0, 0.4],
  [0.92, 0.05],
];
// Marks the inlet opening itself (the smaller inner-lip radius at the very
// front face), not the cowl's max diameter a little further aft.
const NACELLE_LIP_RADIUS = 1.23;
const NACELLE_LIP_Z = 1.95;
// Bypass exit annulus — the ring of bypass air discharging between the fan
// cowl's trailing edge and the core casing, at the same station the cowl
// closes. Sits roughly midway between the two walls, not on either of them,
// since it marks an airflow boundary rather than a piece of hardware.
const BYPASS_EXIT_RADIUS = 0.74;
const BYPASS_EXIT_Z = 0.05;

// The pylon that hangs the engine off the wing — a real cutaway is never
// just a bare cylinder floating in space. A wide z-span first draft (base
// and tip nearly a full radius apart in both z and radius) projected, under
// this canvas's steep rotation, as a long diagonal streak floating clear of
// the core rather than a strut riding it — the same lesson the nacelle's own
// radius took. Kept to a narrow z-window at the fan cowl's widest point and
// a modest radial rise instead, matching the scale every other static
// add-on (flanges, lip ring) already reads correctly at.
const PYLON_POINTS = [
  new Vector3(0, 1.32, 1.75),
  new Vector3(0, 1.5, 1.78),
  new Vector3(0, 1.54, 1.78),
  new Vector3(0, 1.54, 1.55),
  new Vector3(0, 1.4, 1.48),
  new Vector3(0, 1.28, 1.55),
];

// The outer casing/nacelle — one continuous static envelope, not a plain
// cylinder, tracing just outside every stage's blade-tip radius with an
// intake bell at the front and an exhaust flare at the rear. This smooth
// hub-to-casing flowpath envelope is the single most recognisable shape in
// a real engine cutaway; a straight cylinder never reads as one.
// The dip-then-bulge around z 0.16 to -0.44 is deliberate, not filler
// points — a real engine case actually flares outward around the combustor
// to clear it, and that flare is the single most legible way to say "there
// is a combustor here" from the outer silhouette alone. A flatter first
// draft left the combustor's own lines to do all the work nested deep in
// the busiest, most cluttered part of the whole drawing, where they read as
// texture rather than a distinct can.
const CASING_PROFILE = [
  [0.95, 1.55],
  [0.9, 1.05],
  [0.8, 0.84],
  [0.66, 0.56],
  [0.56, 0.34],
  [0.5, 0.16],
  [0.62, -0.02],
  [0.74, -0.16],
  [0.64, -0.32],
  [0.58, -0.44],
  [0.7, -0.68],
  [0.85, -0.96],
  [0.75, -1.3],
];

function circlePoints(radius, segments = 96) {
  return Array.from({ length: segments + 1 }, (_, i) => {
    const t = (i / segments) * Math.PI * 2;
    return new Vector3(Math.cos(t) * radius, Math.sin(t) * radius, 0);
  });
}

// A ring of short radial line segments (not a closed loop) — the geometry
// behind both the flange bolt rings and, at a coarser count with a longer
// tick, the nozzle mixer-lobe scallop.
function radialTicksGeometry(radius, count, tickLength) {
  const positions = new Float32Array(count * 6);
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    const idx = i * 6;
    positions[idx] = cos * radius;
    positions[idx + 1] = sin * radius;
    positions[idx + 2] = 0;
    positions[idx + 3] = cos * (radius + tickLength);
    positions[idx + 4] = sin * (radius + tickLength);
    positions[idx + 5] = 0;
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new Float32BufferAttribute(positions, 3));
  return geometry;
}

// A ring of short radial ticks — flange fasteners at a casing joint,
// injector stubs on a combustor dome, the same primitive either way.
function TickRing({ z, radius, count, tickLength = 0.028, color, opacity = 0.55 }) {
  const geometry = useMemo(() => radialTicksGeometry(radius, count, tickLength), [radius, count, tickLength]);
  return (
    <group position={[0, 0, z]}>
      <lineSegments geometry={geometry}>
        <lineBasicMaterial color={color} transparent opacity={opacity} />
      </lineSegments>
    </group>
  );
}

// Alternating long/short points around the nozzle exit — a scalloped ring
// rather than a flat circle, tracing a real mixer lobe's silhouette.
function nozzleLobePoints(radius, count, depth) {
  const segmentsPerLobe = 6;
  const points = [];
  const total = count * segmentsPerLobe;
  for (let i = 0; i <= total; i++) {
    const t = (i / total) * Math.PI * 2;
    const wobble = Math.cos(t * count) * depth;
    points.push(new Vector3(Math.cos(t) * (radius + wobble), Math.sin(t) * (radius + wobble), 0));
  }
  return points;
}

// Bakes each blade's transform (spread angle around the shaft, radial
// offset, stagger/pitch) into a cloned copy of the blade's edge geometry,
// then merges the whole ring into one buffer — one draw call per stage
// instead of one per blade.
function buildRingGeometry(baseGeometry, count, radius, stagger, scale) {
  const edgesBase = new EdgesGeometry(baseGeometry, EDGE_ANGLE);
  const instances = [];
  const bladeLength = radius * scale;
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2;
    const clone = edgesBase.clone();
    const m = new Matrix4()
      .makeRotationZ(angle)
      .multiply(new Matrix4().makeTranslation(radius, 0, 0))
      .multiply(new Matrix4().makeRotationX(stagger))
      .multiply(new Matrix4().makeScale(bladeLength, bladeLength, bladeLength));
    clone.applyMatrix4(m);
    instances.push(clone);
  }
  const merged = mergeGeometries(instances, false);
  instances.forEach((g) => g.dispose());
  edgesBase.dispose();
  return merged;
}

function EdgeLines({ geometry, color, opacity = 0.85 }) {
  const edges = useMemo(() => new EdgesGeometry(geometry, EDGE_ANGLE), [geometry]);
  return (
    <lineSegments geometry={edges}>
      <lineBasicMaterial color={color} transparent opacity={opacity} />
    </lineSegments>
  );
}

function StageRing({ z, geometry, color, opacity = 0.85 }) {
  return (
    <group position={[0, 0, z]}>
      <lineSegments geometry={geometry}>
        <lineBasicMaterial color={color} transparent opacity={opacity} />
      </lineSegments>
    </group>
  );
}

function Engine({ reduced, light, mobile }) {
  const palette = light ? PALETTE.light : PALETTE.dark;
  const lpSpin = useRef(null);
  const hpSpin = useRef(null);

  const compressorGeo = useMemo(
    () => new ExtrudeGeometry(compressorBladeShape(), EXTRUDE_COMPRESSOR),
    []
  );
  const statorGeo = useMemo(() => new ExtrudeGeometry(statorBladeShape(), EXTRUDE_STATOR), []);
  const turbineGeo = useMemo(() => new ExtrudeGeometry(turbineBladeShape(), EXTRUDE_TURBINE), []);

  // One merged ring geometry per stage — built once, reused across renders.
  const rings = useMemo(() => {
    return STAGES.map((stage) => ({
      ...stage,
      geometry: buildRingGeometry(
        stage.kind === "turbine" ? turbineGeo : compressorGeo,
        stage.count,
        stage.radius,
        stage.stagger,
        stage.scale
      ),
    }));
  }, [compressorGeo, turbineGeo]);

  const statorRings = useMemo(() => {
    return STATORS.map((row) => ({
      ...row,
      geometry: buildRingGeometry(statorGeo, row.count, row.radius, 0, row.scale),
    }));
  }, [statorGeo]);

  const lathe = (profile) => new LatheGeometry(profile.map(([x, y]) => new Vector2(x, y)), 24);
  const spinnerGeo = useMemo(() => lathe(SPINNER_PROFILE), []);
  const tailconeGeo = useMemo(() => lathe(TAILCONE_PROFILE), []);
  const lpDrumFrontGeo = useMemo(() => lathe(LP_DRUM_FRONT_PROFILE), []);
  const lpDrumRearGeo = useMemo(() => lathe(LP_DRUM_REAR_PROFILE), []);
  const hpDrumGeo = useMemo(() => lathe(HP_DRUM_PROFILE), []);
  const combustorGeo = useMemo(() => lathe(COMBUSTOR_PROFILE), []);
  const combustorLinerGeo = useMemo(() => lathe(COMBUSTOR_LINER_PROFILE), []);
  const lpShaftGeo = useMemo(() => new CylinderGeometry(0.08, 0.08, 2.5, 12, 1, true), []);
  const hpShaftGeo = useMemo(() => new CylinderGeometry(0.14, 0.14, 1.35, 12, 1, true), []);
  const casingGeo = useMemo(() => lathe(CASING_PROFILE), []);
  const nacelleGeo = useMemo(() => lathe(NACELLE_PROFILE), []);

  // A turbine stage is disc-built (one flat rotor per stage), unlike the
  // compressor's continuous drum — a real construction difference, and a
  // simple way to give each turbine ring something visible to mount on.
  const discGeo = useMemo(() => new CylinderGeometry(1, 1, 0.09, 28), []);

  const accentPoints = useMemo(() => circlePoints(0.68), []);
  const stationPointsA = useMemo(() => circlePoints(0.75), []);
  const stationPointsB = useMemo(() => circlePoints(0.6), []);
  const nozzlePoints = useMemo(() => nozzleLobePoints(0.095, NOZZLE_LOBE_COUNT, 0.03), []);
  const nacelleLipPoints = useMemo(() => circlePoints(NACELLE_LIP_RADIUS), []);
  const bypassExitPoints = useMemo(() => circlePoints(BYPASS_EXIT_RADIUS), []);

  useFrame((_, delta) => {
    if (reduced) return;
    if (lpSpin.current) lpSpin.current.rotation.z -= delta * 0.11;
    if (hpSpin.current) hpSpin.current.rotation.z -= delta * 0.24;
  });

  const lpRings = rings.filter((r) => r.spool === "lp");
  const hpRings = rings.filter((r) => r.spool === "hp");

  return (
    // World-space roll, applied outside the inner group's own tilt — on
    // mobile this spins the entire already-framed drawing 90° in screen
    // space rather than composing with the inner Euler rotation, which
    // would fight the carefully-tuned [0.14, 1.4, 0.03] elevation instead
    // of just rotating its result.
    <group rotation={[0, 0, mobile ? Math.PI / 2 : 0]}>
    <group rotation={[0.14, 1.4, 0.03]} scale={2.2}>
      {/* Outer casing — one continuous static envelope the length of the
          core (the flowpath silhouette every real cutaway shows), plus the
          combustor can and the static stator rows, none of which rotate.
          Drawn in `structure`, not `faint` — the silhouette that makes this
          read as a turbine belongs a tier above the background texture. */}
      <group rotation={[Math.PI / 2, 0, 0]}>
        <EdgeLines geometry={casingGeo} color={palette.structure} opacity={0.85} />
      </group>
      {/* The combustor is drawn in its own `combustor` tone — casing,
          nacelle, lip/bypass rings and pylon all share `structure`, and the
          HP compressor/turbine blade rings that physically surround the
          combustor in screen space are already `hp`. Colouring the
          combustor `hp` (a first attempt, on the logic that it's downstream
          of the HP compressor) made it disappear into that existing amber
          blade cluster instead of standing apart from it — confirmed by
          isolating just the casing and combustor in the canvas, which is
          the only way this was actually visible against the full drawing's
          clutter. A genuinely unused hue was the fix, not more opacity. */}
      <group rotation={[Math.PI / 2, 0, 0]}>
        <EdgeLines geometry={combustorGeo} color={palette.combustor} opacity={0.95} />
      </group>
      {/* Combustor liner, nested just inside the outer can — the double
          wall a real annular combustor is built from, not a hollow shell —
          plus a dome ring of fuel-injector stubs. */}
      <group rotation={[Math.PI / 2, 0, 0]}>
        <EdgeLines geometry={combustorLinerGeo} color={palette.combustor} opacity={0.7} />
      </group>
      <TickRing
        z={INJECTORS.z}
        radius={INJECTORS.radius}
        count={INJECTORS.count}
        tickLength={0.045}
        color={palette.combustor}
        opacity={0.6}
      />
      {/* Stators, flanges and the station rings are texture, not silhouette
          — dialled down (0.65/0.55 → 0.35–0.4) so they read as fine detail
          sitting behind the structural lines above, instead of competing
          with them at the same weight and burying the shapes that actually
          say "this is a turbine". */}
      {statorRings.map((row) => (
        <StageRing key={row.id} z={row.z} geometry={row.geometry} color={palette.faint} opacity={0.4} />
      ))}
      <Line points={stationPointsA} color={palette.faint} lineWidth={1} transparent opacity={0.3} position={[0, 0, 0.7]} />
      <Line points={stationPointsB} color={palette.faint} lineWidth={1} transparent opacity={0.3} position={[0, 0, -0.9]} />

      {/* Bolted casing-split flanges — the fastener rings a real cutaway
          shows wherever the case is manufactured/removed in sections. */}
      {FLANGES.map((flange) => (
        <TickRing
          key={flange.id}
          z={flange.z}
          radius={flange.radius}
          count={flange.count}
          color={palette.faint}
          opacity={0.35}
        />
      ))}

      {/* The nacelle/fan cowl — stood clear of the core casing so the gap
          between the two reads as the bypass duct, with an inlet-lip ring
          at the front face and a bypass-exit annulus where the cowl closes
          ahead of the combustor. The one bit of "installation" context this
          canvas draws, closest to the owner's own research subject. Drawn in
          `structure` at the same weight as the casing — the two silhouettes
          only read as "an installed nacelle over a core" if both are legible
          at a glance, not just present in the geometry. */}
      <group rotation={[Math.PI / 2, 0, 0]}>
        <EdgeLines geometry={nacelleGeo} color={palette.structure} opacity={0.85} />
      </group>
      <Line points={nacelleLipPoints} color={palette.structure} lineWidth={1.25} transparent opacity={0.8} position={[0, 0, NACELLE_LIP_Z]} />
      <Line points={bypassExitPoints} color={palette.structure} lineWidth={1} transparent opacity={0.55} position={[0, 0, BYPASS_EXIT_Z]} />

      {/* The wing pylon — every real engine cutaway hangs off one; without
          it the core reads as floating hardware rather than an installed
          engine. Static, drawn once, outside both spool groups. */}
      <Line points={PYLON_POINTS} color={palette.structure} lineWidth={1.25} transparent opacity={0.75} />

      {/* LP spool — spinner, LPC drum, LPT discs, tail cone. Slower of the
          two. Compressor stages share one continuous tapered drum (what the
          blade rows are actually mounted to); each turbine stage gets its
          own disc, matching how the two are really built. */}
      <group ref={lpSpin}>
        <group position={[0, 0, 1.35]} rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={spinnerGeo} color={palette.lp} />
        </group>
        <group position={[0, 0, -1.15]} rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={tailconeGeo} color={palette.lp} opacity={0.7} />
        </group>
        {/* Nozzle mixer lobes — a scalloped exit ring, not a bare taper. */}
        <Line points={nozzlePoints} color={palette.lp} lineWidth={1} transparent opacity={0.6} position={[0, 0, -1.6]} />
        <group rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={lpShaftGeo} color={palette.lp} opacity={0.55} />
        </group>
        <group rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={lpDrumFrontGeo} color={palette.lp} opacity={0.7} />
        </group>
        <group rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={lpDrumRearGeo} color={palette.lp} opacity={0.7} />
        </group>
        {lpRings.map((stage) => (
          <group key={stage.id}>
            {stage.kind === "turbine" ? (
              <group position={[0, 0, stage.z]} rotation={[Math.PI / 2, 0, 0]} scale={stage.radius * 0.92}>
                <EdgeLines geometry={discGeo} color={palette.lp} opacity={0.75} />
              </group>
            ) : null}
            <StageRing z={stage.z} geometry={stage.geometry} color={palette.lp} />
          </group>
        ))}
      </group>

      {/* HP spool — HPC drum, HPT disc. Faster; visibly out of sync with the
          LP spool because the two groups rotate at different rates. */}
      <group ref={hpSpin}>
        <group rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={hpShaftGeo} color={palette.hp} opacity={0.6} />
        </group>
        <group rotation={[Math.PI / 2, 0, 0]}>
          <EdgeLines geometry={hpDrumGeo} color={palette.hp} opacity={0.7} />
        </group>
        {hpRings.map((stage) => (
          <group key={stage.id}>
            {stage.kind === "turbine" ? (
              <group position={[0, 0, stage.z]} rotation={[Math.PI / 2, 0, 0]} scale={stage.radius * 0.92}>
                <EdgeLines geometry={discGeo} color={palette.hp} opacity={0.75} />
              </group>
            ) : null}
            <StageRing z={stage.z} geometry={stage.geometry} color={palette.hp} />
          </group>
        ))}
      </group>

      {/* The one deliberate colour hit — an accent ring at the LP compressor
          inlet, same role it played on the single-stage version. */}
      <Line points={accentPoints} color="#ff6d3b" lineWidth={1.25} transparent opacity={0.6} position={[0, 0, 1.15]} />
    </group>
    </group>
  );
}

export default function TurbineStage() {
  // matchMedia is an external store, so read it as one — this also picks up
  // a visitor changing the OS setting while the page is open.
  const reduced = useSyncExternalStore(
    subscribeToMotion,
    () => window.matchMedia(MOTION_QUERY).matches,
    () => false
  );
  // Reads the same theme (system query + ThemeToggle's manual override) that
  // drives the CSS palette, so the canvas never disagrees with the page.
  const light = useSyncExternalStore(
    subscribeToTheme,
    () => getEffectiveTheme() === "light",
    () => false
  );
  // Same pattern as `reduced`/`light` — an external store so a resize across
  // the 768px breakpoint (rotating a tablet, a resized browser window) is
  // picked up live, not just on first paint.
  const mobile = useSyncExternalStore(
    subscribeToViewport,
    () => window.matchMedia(MOBILE_QUERY).matches,
    () => false
  );

  return (
    <Canvas
      orthographic
      // Orthographic rather than perspective — no vanishing-point distortion,
      // which is what makes a technical blueprint read as a blueprint rather
      // than a product render. `zoom` replaces `fov` as the framing control.
      // Zoomed OUT on mobile (105 → 80), not in — the engine's girth (its
      // blade-radius spread, originally the short dimension matching
      // desktop's ~950px canvas height) becomes the *width* dimension once
      // rolled 90°, and a phone's width (~390px) is under half that. 120
      // (an earlier value, reasoned from "fill the taller frame" rather than
      // from the width constraint) left the widest arcs overflowing the
      // sides — the drawing read as stretched/oversized rather than fitted.
      camera={{ position: [2, 0.5, 6], zoom: mobile ? 80 : 105, near: 0.1, far: 20 }}
      dpr={[1, 1.5]}
      frameloop={reduced ? "demand" : "always"}
      gl={{ antialias: true, alpha: true }}
    >
      <Engine reduced={reduced} light={light} mobile={mobile} />
    </Canvas>
  );
}
