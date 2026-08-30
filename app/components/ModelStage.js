"use client";

import { Canvas } from "@react-three/fiber";
import { Bounds, Grid, OrbitControls, useGLTF } from "@react-three/drei";
import { Suspense, useSyncExternalStore } from "react";

/**
 * The heavy half of the model viewer — three.js, R3F and drei all land in this
 * chunk, which is why nothing here is imported until ModelViewer decides the
 * viewer is actually on screen.
 *
 * Lighting is neutral and directional, matching the site's monochrome
 * treatment: the geometry reads as a shaded CAD part, not a product render.
 */

function Model({ src }) {
  const { scene } = useGLTF(src);
  return <primitive object={scene} />;
}

function Fallback({ children }) {
  return (
    <div className="absolute inset-0 grid place-items-center">
      <p className="t-label text-fg2">{children}</p>
    </div>
  );
}

const MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeToMotion(onChange) {
  const query = window.matchMedia(MOTION_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

export default function ModelStage({ src, autoRotate }) {
  // matchMedia is an external store, so read it as one — this also picks up a
  // visitor changing the OS setting while the page is open.
  const reduced = useSyncExternalStore(
    subscribeToMotion,
    () => window.matchMedia(MOTION_QUERY).matches,
    () => false
  );

  return (
    <Canvas
      camera={{ position: [3, 2, 4], fov: 40 }}
      // Cap the pixel ratio: a retina canvas at devicePixelRatio 3 renders 9x
      // the fragments for no visible gain on a part this size.
      dpr={[1, 2]}
      // Only redraw when something actually changes — an idle viewer costs
      // zero GPU, which matters on a page a visitor may leave open.
      frameloop={autoRotate && !reduced ? "always" : "demand"}
      gl={{ antialias: true }}
    >
      <color attach="background" args={["#101316"]} />

      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 8, 5]} intensity={2.2} />
      <directionalLight position={[-6, 3, -4]} intensity={0.7} />

      <Suspense fallback={null}>
        <Bounds fit clip observe margin={1.1}>
          <Model src={src} />
        </Bounds>
      </Suspense>

      <Grid
        args={[20, 20]}
        cellSize={0.25}
        cellThickness={0.5}
        cellColor="#23282e"
        sectionSize={1}
        sectionThickness={1}
        sectionColor="#2f353d"
        fadeDistance={18}
        fadeStrength={1.5}
        infiniteGrid
        position={[0, -0.001, 0]}
      />

      <OrbitControls
        makeDefault
        enablePan={false}
        // Damping needs frames after the pointer stops, which fights
        // frameloop="demand" — instant response costs nothing and never stutters.
        enableDamping={false}
        minDistance={1.5}
        maxDistance={12}
        autoRotate={autoRotate && !reduced}
        autoRotateSpeed={0.6}
      />
    </Canvas>
  );
}

export { Fallback };
