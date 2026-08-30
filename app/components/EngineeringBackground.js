"use client";

import { useEffect, useRef } from "react";
import TurbineBackground from "./TurbineBackground";
import DraftingMotion from "./DraftingMotion";

const MOTION_QUERY = "(prefers-reduced-motion: reduce)";

// One target framing per section — the same drawing pans/zooms toward a
// different part of itself as the reader scrolls, rather than swapping in a
// unique illustration per section. Kept deliberately modest (≤ 6% scale
// change): a first pass went up to 12%, which was enough to drag the
// drafting cluster back toward the text column it's positioned clear of at
// rest (confirmed with a real screenshot, not just by reading the numbers).
// `null` is the hero's own resting state.
const SECTION_FRAMES = {
  projects: { scale: 1.04, x: -2, y: 1 },
  cad: { scale: 1.03, x: -3, y: -1 },
  experience: { scale: 1.02, x: -1, y: 1 },
  education: { scale: 1, x: 0, y: 0 },
  toolchain: { scale: 1.03, x: -2, y: 0 },
  contact: { scale: 0.96, x: 2, y: 2 },
};
const HERO_FRAME = { scale: 1, x: 0, y: 0 };
const SECTION_IDS = Object.keys(SECTION_FRAMES);

/**
 * Owns the two effects layered on top of TurbineStage's tuned 3D wireframe:
 *
 * - Scroll-linked framing: an IntersectionObserver (the same pattern Nav
 *   already uses for its active-section marker) picks the current section
 *   and eases the whole stage toward that section's target scale/pan via a
 *   CSS transition — a deliberate, section-triggered re-frame rather than a
 *   continuous per-pixel scroll-scrub, which stays cheap and never fights
 *   the browser's own scroll performance.
 * - Mouse parallax: a rAF-throttled pointermove listener writes normalized
 *   (-1..1) offsets to `--dm-mx`/`--dm-my`, consumed by DraftingMotion's own
 *   layers at different multipliers for depth. Skipped entirely on touch
 *   (no `hover: hover`) and under reduced motion.
 *
 * Both write straight to the DOM via refs, matching ReadProgress/Reveal's
 * existing no-React-state pattern — neither scrolling nor pointer movement
 * triggers a re-render here.
 */
export default function EngineeringBackground() {
  const stageRef = useRef(null);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    if (window.matchMedia(MOTION_QUERY).matches) return;

    const sections = SECTION_IDS.map((id) => document.getElementById(id)).filter(
      Boolean
    );
    if (!sections.length || typeof IntersectionObserver === "undefined") return;

    function applyFrame(id) {
      const frame = (id && SECTION_FRAMES[id]) || HERO_FRAME;
      stage.style.setProperty("--eb-scale", frame.scale);
      stage.style.setProperty("--eb-x", `${frame.x}%`);
      stage.style.setProperty("--eb-y", `${frame.y}%`);
      // The dense annotation cluster (construction circles, dimensions,
      // station labels) is hand-placed to clear the hero's own text and
      // portrait — verified with a screenshot. Every other section lays out
      // its content differently, and the background is genuinely fixed, so
      // there's no single placement guaranteed clear of all of them. Fading
      // the cluster down once any section is active (confirmed on Contact,
      // where a station label sat on the email field's label row) is more
      // robust than chasing per-section coordinates.
      stage.style.setProperty("--dm-detail", id ? "0.3" : "1");
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const hit = entries.find((entry) => entry.isIntersecting);
        if (hit) applyFrame(hit.target.id);
      },
      { rootMargin: "-40% 0px -40% 0px", threshold: 0 }
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    if (window.matchMedia(MOTION_QUERY).matches) return;
    if (!window.matchMedia("(hover: hover)").matches) return;

    let frame = 0;
    let lastX = 0;
    let lastY = 0;

    function update() {
      frame = 0;
      stage.style.setProperty("--dm-mx", lastX.toFixed(3));
      stage.style.setProperty("--dm-my", lastY.toFixed(3));
    }

    function onPointerMove(e) {
      lastX = (e.clientX / window.innerWidth) * 2 - 1;
      lastY = (e.clientY / window.innerHeight) * 2 - 1;
      if (!frame) frame = requestAnimationFrame(update);
    }

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onPointerMove);
    };
  }, []);

  return (
    <div ref={stageRef} className="eb-stage">
      <TurbineBackground />
      <DraftingMotion />
    </div>
  );
}
