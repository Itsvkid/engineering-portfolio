"use client";

import { useEffect, useRef } from "react";

/**
 * Fade-up on first viewport entry, once. The hidden initial state lives in CSS
 * behind `.js` (set before paint in layout.js), so this component renders its
 * children in normal flow on the server and for no-JS visitors.
 *
 * Visibility is toggled by writing the class straight to the node rather than
 * through state: this is a one-way sync out to the DOM, it costs no re-render,
 * and it keeps the effect free of the cascading-render pattern React warns about.
 *
 * Reduced motion needs no branch here — the media query in globals.css pins
 * every revealed element to its final state regardless of this class.
 *
 * Anything inside marked `.stagger` has its direct children cascade in; a `.rule`
 * inside draws itself left-to-right. Both key off the class set below.
 */
export default function Reveal({ children, delay = 0, className = "" }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Browsers without IntersectionObserver would otherwise never reveal.
    if (typeof IntersectionObserver === "undefined") {
      el.classList.add("is-visible");
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          el.classList.add("is-visible");
          observer.disconnect();
        }
      },
      // Fires once the element's top clears the lower 15% of the viewport.
      // A plain `threshold: 0.15` would never fire for a block taller than
      // ~6.6 viewports, leaving it permanently hidden on short screens.
      { rootMargin: "0px 0px -15% 0px", threshold: 0 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`reveal${className ? ` ${className}` : ""}`}
      style={delay ? { "--reveal-delay": `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
