"use client";

import dynamic from "next/dynamic";

const TurbineStage = dynamic(() => import("./TurbineStage"), { ssr: false });

/**
 * Decorative compressor-inlet animation, behind the entire page — it keeps
 * spinning while the page scrolls rather than scrolling away with the hero.
 * `absolute inset-0`, not `fixed`: EngineeringBackground's `.eb-stage`
 * wrapper is the actual fixed, viewport-sized box (its own scroll-linked
 * transform would otherwise break `fixed` positioning on a child — see the
 * comment on `.eb-stage` in globals.css), and this fills that. Purely
 * ambient: aria-hidden, no pointer events, with a soft radial fade so it
 * never reads as a hard-edged panel. Every section's own content (the
 * carded project/experience/education entries) sits on an opaque `bg1`
 * fill, so it naturally occludes the canvas wherever legibility actually
 * matters.
 *
 * The mask and opacity are both responsive, not just the canvas:
 * TurbineStage rolls the whole drawing 90° below the `md` breakpoint so its
 * long axis runs vertically instead of overflowing a narrow phone screen
 * sideways, and a mask tuned for that horizontal desktop spread (anchored
 * right-of-centre, wide and short) would crop the rotated engine's top and
 * bottom on mobile instead of its now-unused left and right margins. The
 * base (mobile) mask is narrow and tall, centred, to match. Opacity drops
 * too (55% → 40%): desktop's right-of-centre anchor keeps the drawing mostly
 * in the page's margin, but a phone has no margin to put it in — centred and
 * full-width, the same 55% read as competing with the text on top of it
 * rather than sitting behind it.
 */
export default function TurbineBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden opacity-40 md:opacity-55 [mask-image:radial-gradient(85%_130%_at_50%_40%,black_55%,transparent_100%)] md:[mask-image:radial-gradient(120%_100%_at_78%_38%,black_55%,transparent_100%)]"
    >
      <TurbineStage />
    </div>
  );
}
