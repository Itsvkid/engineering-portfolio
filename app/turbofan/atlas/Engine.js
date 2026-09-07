"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import { memo, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { BufferGeometry, Color, DoubleSide, Matrix4, Mesh, Plane, Quaternion, Vector3 } from "three";
import { acceleratedRaycast, computeBoundsTree, disposeBoundsTree } from "three-mesh-bvh";
import { ENGINE_CENTRE } from "./flowpath";
import { bladeGeometry, bladeRingMatrices, cyl, doorRing } from "./geometry";
import { PARTS } from "./parts";
import { SYSTEM_BY_ID } from "./systems";

/**
 * The scene. One mesh per part (a blade row is one merged mesh), two
 * rotating groups for the two spools, a fixed wedge cutaway made of two
 * clipping planes, and a separation offset per part. Picking goes through
 * three-mesh-bvh so hovering a million-triangle engine costs nothing.
 *
 * Human Atlas batches everything into a few draw calls with per-structure
 * textures; at ~150 parts this engine does not need that, and a mesh per
 * part keeps selection, isolation and the cutaway trivially correct.
 */

BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
BufferGeometry.prototype.disposeBoundsTree = disposeBoundsTree;
Mesh.prototype.raycast = acceleratedRaycast;

// The wedge removed by the cutaway: world +Y and +Z (the upper quadrant
// nearest the default camera). clipIntersection makes a material vanish
// only where BOTH planes clip, i.e. inside the wedge rather than in either
// half-space.
const CUT_PLANES = [new Plane(new Vector3(0, -1, 0), 0), new Plane(new Vector3(0, 0, -1), 0)];

// Visual spool speeds. Real speeds alias to a blur at 60 fps; these are
// slow enough to read while keeping the published ratio between the shafts.
const LP_VIS_RPS = 0.45; // at full throttle
const HP_OVER_LP = 12645 / 3539; // max climb, CR-168219 / LPT Table VI

export const CAMERA_PRESETS = {
  iso: { position: [-2.2, 2.3, 5.4], target: [1.9, 0, 0] },
  front: { position: [-5.6, 0.5, 0.01], target: [0.8, 0, 0] },
  side: { position: [1.9, 0.6, 10.5], target: [1.9, 0, 0] },
  top: { position: [1.9, 10, 0.01], target: [1.9, 0, 0] },
  aft: { position: [11, 0.9, 0.01], target: [2.2, 0, 0] },
};

function separationOffset(part, t) {
  if (t <= 0) return null;
  const axial = (part.y - ENGINE_CENTRE) * 0.9 * t;
  let radial = 0;
  if (part.clock !== undefined && !part.spool) radial = 0.55 * t;
  if (radial === 0) return new Vector3(0, axial, 0);
  const dir = cyl(0, 1, part.clock);
  return new Vector3(dir.x * radial, axial, dir.z * radial);
}

/**
 * Builds every part's geometry once, synchronously, in the state initialiser
 * (about a quarter of a second for the whole engine, measured in Node), then
 * the bounds trees for picking in an idle loop. Until a part has its tree,
 * three-mesh-bvh falls back to the plain raycast, so hovering is correct
 * throughout, only slower for a moment. Building a few parts per animation
 * frame was tried first and made the engine appear one part at a time on a
 * slow GPU, because each frame had to render before the next batch began.
 */
function useBuiltGeometries() {
  const [built] = useState(() => {
    const map = new Map();
    for (const part of PARTS) {
      try {
        map.set(part.id, part.build());
      } catch (err) {
        // A malformed profile must not take the whole engine down.
        console.error(`turbofan atlas: could not build ${part.id}`, err);
      }
    }
    return map;
  });
  useEffect(() => {
    let cancelled = false;
    const order = [...built.keys()];
    let j = 0;
    const idle = typeof requestIdleCallback === "function" ? requestIdleCallback : (fn) => setTimeout(fn, 16);
    function trees() {
      if (cancelled) return;
      const start = performance.now();
      while (j < order.length && performance.now() - start < 12) {
        built.get(order[j++]).computeBoundsTree();
      }
      if (j < order.length) idle(trees);
    }
    idle(trees);
    return () => {
      cancelled = true;
      built.forEach((g) => {
        g.disposeBoundsTree?.();
        g.dispose();
      });
    };
  }, [built]);
  return built;
}

const PartMesh = memo(function PartMesh({ part, geometry, color, state, dispatch, cut }) {
  const selected = state.selected === part.id;
  const hovered = state.hovered === part.id;
  const sys = SYSTEM_BY_ID[part.system];
  const isShell = part.system === "structure" || part.system === "exhaust";
  const opacity = isShell ? state.shellOpacity : 1;
  const offset = useMemo(() => separationOffset(part, state.separation), [part, state.separation]);

  const emissive = selected ? "#ff6d3b" : hovered ? color : "#000000";
  const emissiveIntensity = selected ? 0.55 : hovered ? 0.25 : 0;

  return (
    <mesh
      geometry={geometry}
      position={offset ?? undefined}
      userData={{ partId: part.id, systemId: sys.id }}
      onClick={(e) => {
        if (e.delta > 4) return; // a drag, not a click
        e.stopPropagation();
        dispatch({ type: "select", id: selected ? null : part.id });
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        dispatch({ type: "hover", id: part.id });
      }}
      onPointerOut={() => dispatch({ type: "hover", id: null })}
    >
      <meshStandardMaterial
        color={color}
        emissive={emissive}
        emissiveIntensity={emissiveIntensity}
        metalness={0.45}
        roughness={0.55}
        side={DoubleSide}
        transparent={opacity < 1}
        opacity={opacity}
        depthWrite={opacity >= 0.5}
        clippingPlanes={cut ? CUT_PLANES : null}
        clipIntersection
      />
    </mesh>
  );
});

/** A variable stator row: instanced so each vane turns on its spindle. */
const VsvRow = memo(function VsvRow({ part, color, state, dispatch, cut }) {
  const ref = useRef();
  const { count, rHub, y, spec, closedDeg } = part.vsv;
  const geometry = useMemo(() => {
    const g = bladeGeometry(spec);
    g.computeBoundsTree();
    return g;
  }, [spec]);
  const ringMatrices = useMemo(() => bladeRingMatrices(count, rHub, y, 0.5), [count, rHub, y]);
  const selected = state.selected === part.id;
  const hovered = state.hovered === part.id;
  const offset = useMemo(() => separationOffset(part, state.separation), [part, state.separation]);

  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const spindle = new Matrix4().makeRotationX(((closedDeg * (1 - state.vsv)) * Math.PI) / 180);
    const m = new Matrix4();
    for (let i = 0; i < count; i++) {
      m.copy(ringMatrices[i]).multiply(spindle);
      mesh.setMatrixAt(i, m);
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
  }, [state.vsv, ringMatrices, count, closedDeg]);

  return (
    <instancedMesh
      ref={ref}
      args={[geometry, undefined, count]}
      position={offset ?? undefined}
      userData={{ partId: part.id }}
      onClick={(e) => {
        if (e.delta > 4) return;
        e.stopPropagation();
        dispatch({ type: "select", id: selected ? null : part.id });
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        dispatch({ type: "hover", id: part.id });
      }}
      onPointerOut={() => dispatch({ type: "hover", id: null })}
    >
      <meshStandardMaterial
        color={color}
        emissive={selected ? "#ff6d3b" : hovered ? color : "#000000"}
        emissiveIntensity={selected ? 0.55 : hovered ? 0.25 : 0}
        metalness={0.45}
        roughness={0.55}
        side={DoubleSide}
        clippingPlanes={cut ? CUT_PLANES : null}
        clipIntersection
      />
    </instancedMesh>
  );
});

/** The bleed doors, rebuilt at the slider's angle (twelve boxes: cheap). */
const VbvDoors = memo(function VbvDoors({ part, color, state, dispatch, cut }) {
  const { count, r, y, width, length } = part.vbv;
  const open = Math.round(state.vbv * 40);
  const geometry = useMemo(() => {
    const g = doorRing(count, r, y, width, length, open);
    g.computeBoundsTree();
    return g;
  }, [count, r, y, width, length, open]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <PartMesh part={part} geometry={geometry} color={color} state={state} dispatch={dispatch} cut={cut} />;
});

function Spool({ speed, children }) {
  const ref = useRef();
  useFrame((_, dt) => {
    if (ref.current && speed > 0) ref.current.rotation.y += speed * Math.PI * 2 * Math.min(dt, 0.05);
  });
  return <group ref={ref}>{children}</group>;
}

function Label({ part, theme }) {
  const p = cyl(part.y, part.r + 0.05, part.clock ?? 20);
  const sys = SYSTEM_BY_ID[part.system];
  return (
    <Html position={[p.x, p.y, p.z]} zIndexRange={[15, 0]} style={{ pointerEvents: "none" }}>
      <div
        className="atlas-label"
        style={{
          "--label-color": sys.color[theme],
        }}
      >
        <span className="atlas-label-dot" />
        {part.name}
      </div>
    </Html>
  );
}

/**
 * Drives the camera to a preset or to frame a part, tweening over ~0.7 s.
 * A preset and a frame request are both "goals"; whichever changed last
 * wins. The frame goal is the part's bounding sphere, rotated into world,
 * seen from the camera's current direction so the fly-to feels continuous.
 */
function CameraDriver({ preset, frameRequest, built, controlsRef, reduced }) {
  const { camera, invalidate, size } = useThree();
  const portrait = size.width < size.height;
  const tween = useRef(null);
  // -1 so the first preset is applied on mount (a portrait viewport needs its lift).
  const seen = useRef({ preset: -1, frame: frameRequest?.n ?? -1 });

  const start = (position, target) => {
    const controls = controlsRef.current;
    if (!controls) return;
    if (reduced) {
      camera.position.copy(position);
      controls.target.copy(target);
      controls.update();
      invalidate();
      return;
    }
    tween.current = {
      t: 0,
      p0: camera.position.clone(),
      t0: controls.target.clone(),
      p1: position,
      t1: target,
    };
    invalidate();
  };

  useEffect(() => {
    if (!preset || preset.n === seen.current.preset) return;
    seen.current.preset = preset.n;
    const c = CAMERA_PRESETS[preset.id] ?? CAMERA_PRESETS.iso;
    const target = new Vector3(...c.target);
    if (portrait) target.y -= 1.6; // keep the engine above the phone's drawer
    start(new Vector3(...c.position), target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset]);

  useEffect(() => {
    if (!frameRequest || frameRequest.n === seen.current.frame) return;
    seen.current.frame = frameRequest.n;
    const part = frameRequest.part;
    const controls = controlsRef.current;
    if (!controls) return;
    const q = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), -Math.PI / 2);
    const g = built.get(part.id);
    let centre;
    let radius;
    if (g) {
      if (!g.boundingSphere) g.computeBoundingSphere();
      centre = g.boundingSphere.center.clone().applyQuaternion(q);
      radius = g.boundingSphere.radius;
    } else {
      centre = cyl(part.y, part.clock !== undefined ? part.r : 0, part.clock ?? 0).applyQuaternion(q);
      radius = Math.max(0.3, part.r);
    }
    // Axisymmetric parts have their centre on the axis; look at the part's
    // labelled side instead so the camera does not stare down the bore.
    // Axisymmetric parts sit on the axis and are mostly hidden inside the
    // casings; look at their upper-near quadrant, the one the cutaway
    // opens, from the default three-quarter direction and from far enough
    // back that the neighbouring rows give the part its context.
    const axisymmetric = part.clock === undefined;
    if (axisymmetric) centre.add(cyl(0, Math.min(part.r, radius) * 0.6, 40).applyQuaternion(q));
    // Inside the nacelle everything is within a metre of the camera, so an
    // internal part is framed from outside the skin, where the cutaway's
    // edge gives it context; an external unit can be approached closely.
    const dist = Math.max(axisymmetric ? 3.6 : 1.4, radius * (axisymmetric ? 4.0 : 2.6) + 0.6);
    const dir = axisymmetric
      ? new Vector3(-0.45, 0.55, 0.7).normalize()
      : new Vector3().subVectors(camera.position, controls.target).normalize();
    if (dir.lengthSq() < 0.5) dir.set(-0.4, 0.5, 0.75).normalize();
    start(centre.clone().addScaledVector(dir, dist), centre);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [frameRequest]);

  useFrame((_, dt) => {
    const tw = tween.current;
    if (!tw) return;
    const controls = controlsRef.current;
    tw.t = Math.min(1, tw.t + dt / 0.7);
    const e = 1 - Math.pow(1 - tw.t, 3); // ease-out cubic
    camera.position.lerpVectors(tw.p0, tw.p1, e);
    if (controls) {
      controls.target.lerpVectors(tw.t0, tw.t1, e);
      controls.update();
    }
    if (tw.t >= 1) tween.current = null;
    else invalidate();
  });
  return null;
}

/** A portrait viewport gets a wider lens so the long engine still fits across it. */
function Lens() {
  const size = useThree((s) => s.size);
  const set = useThree((s) => s.set);
  const get = useThree((s) => s.get);
  useEffect(() => {
    const fov = size.width < size.height ? 50 : 32;
    const cam = get().camera;
    if (cam.fov === fov) return;
    // Replace rather than mutate: the store hands out a fresh camera object
    // and R3F re-renders with it.
    const next = cam.clone();
    next.fov = fov;
    next.updateProjectionMatrix();
    set({ camera: next });
    get().invalidate();
  }, [size, set, get]);
  return null;
}

function Scene({ state, dispatch, theme, palette }) {
  const built = useBuiltGeometries();
  const controlsRef = useRef();
  const visible = state.visibleSystems;
  const cut = state.cutaway;
  const lpSpeed = state.motion ? state.throttle * LP_VIS_RPS : 0;

  const groups = useMemo(() => {
    const lp = [];
    const hp = [];
    const fixed = [];
    for (const part of PARTS) {
      if (!visible.includes(part.system)) continue;
      if (state.isolated && state.isolated !== part.id) continue;
      (part.spool === "lp" ? lp : part.spool === "hp" ? hp : fixed).push(part);
    }
    return { lp, hp, fixed };
  }, [visible, state.isolated]);

  const render = (part) => {
    const color = palette[part.tint] ?? palette[part.system];
    if (part.kind === "vsvRow") return <VsvRow key={part.id} part={part} color={color} state={state} dispatch={dispatch} cut={cut} />;
    if (part.kind === "vbv") return <VbvDoors key={part.id} part={part} color={color} state={state} dispatch={dispatch} cut={cut} />;
    const g = built.get(part.id);
    if (!g) return null;
    return <PartMesh key={part.id} part={part} geometry={g} color={color} state={state} dispatch={dispatch} cut={cut} />;
  };

  const selectedPart = state.selected ? PARTS.find((p) => p.id === state.selected) : null;

  return (
    <>
      <color attach="background" args={[palette.background]} />
      <hemisphereLight args={[palette.skyLight, palette.groundLight, 0.9]} />
      <directionalLight position={[4, 8, 6]} intensity={1.6} />
      <directionalLight position={[-6, 3, -5]} intensity={0.6} />
      <directionalLight position={[2, -5, 2]} intensity={0.35} />

      <group rotation={[0, 0, -Math.PI / 2]} onPointerMissed={() => dispatch({ type: "select", id: null })}>
        <Spool speed={lpSpeed}>{groups.lp.map(render)}</Spool>
        <Spool speed={lpSpeed * HP_OVER_LP}>{groups.hp.map(render)}</Spool>
        <group>{groups.fixed.map(render)}</group>
        {state.labels && selectedPart && <Label part={selectedPart} theme={theme} />}
      </group>

      <OrbitControls
        ref={controlsRef}
        makeDefault
        enableDamping={false}
        minDistance={0.6}
        maxDistance={16}
        target={CAMERA_PRESETS.iso.target}
      />
      <Lens />
      <CameraDriver preset={state.cameraPreset} frameRequest={state.frameRequest} built={built} controlsRef={controlsRef} reduced={!state.motion} />
    </>
  );
}

export default function Engine({ state, dispatch, theme, palette }) {
  const live = state.motion && state.throttle > 0;
  return (
    <Canvas
      camera={{ position: CAMERA_PRESETS.iso.position, fov: 32, near: 0.05, far: 60 }}
      dpr={[1, 1.75]}
      frameloop={live ? "always" : "demand"}
      gl={{ antialias: true, localClippingEnabled: true, powerPreference: "high-performance" }}
      onCreated={({ gl }) => {
        gl.localClippingEnabled = true;
        gl.setClearColor(new Color(palette.background));
      }}
      style={{ touchAction: "none" }}
    >
      <Scene state={state} dispatch={dispatch} theme={theme} palette={palette} />
    </Canvas>
  );
}
