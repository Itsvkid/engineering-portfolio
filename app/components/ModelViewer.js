"use client";

import dynamic from "next/dynamic";
import { Component, useEffect, useRef, useState } from "react";

/**
 * The light half of the model viewer. three.js, R3F and drei add roughly
 * 600 KB gzipped, so ModelStage is code-split behind `next/dynamic` AND behind
 * an IntersectionObserver: a visitor who never scrolls to the geometry never
 * downloads it. `ssr: false` because there is no WebGL context on the server.
 */
const ModelStage = dynamic(() => import("./ModelStage"), {
  ssr: false,
  loading: () => <Notice>Loading geometry…</Notice>,
});

function Notice({ children }) {
  return (
    <div className="absolute inset-0 grid place-items-center px-6 text-center">
      <p className="t-label text-fg2">{children}</p>
    </div>
  );
}

/**
 * A missing or malformed .glb throws inside Suspense, where a plain fallback
 * cannot catch it. Without this the whole page would blank out — so the viewer
 * degrades to a caption instead, and the rest of the project entry survives.
 */
class StageBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <Notice>Geometry unavailable — see figures below.</Notice>;
    }
    return this.props.children;
  }
}

export default function ModelViewer({ src, title, description, autoRotate = false }) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    // IntersectionObserver is baseline in every browser since 2019. If it were
    // somehow absent the frame keeps its title and the figures below still
    // carry the evidence — nothing breaks, the canvas just never mounts.
    if (!el || typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setInView(true);
          observer.disconnect();
        }
      },
      // Start fetching a screen early so the canvas is ready on arrival.
      { rootMargin: "0px 0px 25% 0px", threshold: 0 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <figure className="mt-8">
      <div
        ref={ref}
        className="relative aspect-16/10 w-full overflow-hidden rounded-md border border-line bg-bg1"
      >
        {inView ? (
          <StageBoundary>
            <ModelStage src={src} autoRotate={autoRotate} />
          </StageBoundary>
        ) : (
          <Notice>{title}</Notice>
        )}
      </div>

      {/* The canvas is not reachable by keyboard, so the geometry is also
          described in text — this is the accessible equivalent, not a caption
          duplicating what is already on screen. */}
      <figcaption className="t-body-sm mt-3 text-fg2">
        {description}{" "}
        <span className="text-fg2">Drag to orbit, scroll to zoom.</span>
      </figcaption>
    </figure>
  );
}
