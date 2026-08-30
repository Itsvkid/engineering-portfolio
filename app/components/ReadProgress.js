"use client";

import { useEffect, useRef } from "react";

/**
 * A 2px accent bar under the nav showing how far through the page the reader is.
 * Written straight to a CSS custom property inside rAF — no React state, so
 * scrolling never triggers a re-render, and the bar animates on transform only.
 */
export default function ReadProgress() {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let frame = 0;

    function update() {
      frame = 0;
      const scrollable =
        document.documentElement.scrollHeight - window.innerHeight;
      const ratio = scrollable > 0 ? window.scrollY / scrollable : 0;
      el.style.setProperty("--progress", Math.min(Math.max(ratio, 0), 1));
    }

    function onScroll() {
      if (!frame) frame = requestAnimationFrame(update);
    }

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return (
    <div
      // Decorative: the scrollbar already conveys this to assistive tech.
      aria-hidden="true"
      className="h-0.5 w-full overflow-hidden bg-transparent"
    >
      <div ref={ref} className="progress h-full w-full bg-accent" />
    </div>
  );
}
