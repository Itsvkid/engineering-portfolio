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
      /* The mask is tighter than it was, and the reason is the light ground.
         On the old charcoal page the linework sat far enough below the body
         text's contrast that the two could overlap; on a white sheet the
         same lines compete with the paragraph they cross. The desktop mask
         now falls off before the hero's text column instead of reaching
         across it, and the whole layer is lighter. */
      /* The mask is tighter than it was, and the reason is the light ground.
         On the old charcoal page the linework sat far enough below the body
         text's contrast that the two could overlap; on a white sheet the
         same lines compete with the paragraph they cross. The desktop mask
         now falls off before the hero's text column instead of reaching
         across it.

         Mobile gets a much lower opacity rather than a cleverer mask. A
         390px column has no margin to put a drawing in — wherever it goes it
         is behind the text — so on a phone this drops to a watermark that
         reads as texture, not as linework competing with the words. */
      className="pointer-events-none absolute inset-0 overflow-hidden opacity-[0.13] md:opacity-45 [mask-image:radial-gradient(85%_130%_at_50%_40%,black_35%,transparent_92%)] md:[mask-image:radial-gradient(78%_105%_at_82%_40%,black_30%,transparent_88%)]"
    >
      <TurbineStage />
    </div>
  );
}
