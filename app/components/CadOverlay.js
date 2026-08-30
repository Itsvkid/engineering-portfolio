/**
 * A drafting-sheet frame for the page's empty margins — the turbine canvas
 * sits right-of-centre (see TurbineBackground's mask), which leaves the left
 * margin and the sheet corners bare. This adds the furniture a real
 * engineering drawing carries around its subject: corner crop marks, a ruler
 * edge, one reference dimension, an axis glyph, and a title block. Static
 * markup, no canvas, no JS — it sits behind TurbineStage in the DOM so the
 * engine's linework stays the foreground layer. Hidden below `lg`: on a
 * narrow viewport there is no margin left to furnish, and the hero content
 * needs all of it.
 *
 * `absolute`/`h-screen` anchored to the top of the page, not `fixed` —
 * TurbineBackground stays pinned for the whole scroll by design (it's the
 * page's actual backdrop), but this is framing for the hero specifically. A
 * `fixed` first draft kept the title block glued to the viewport's bottom
 * corner for the entire page, which put it right on top of the footer's own
 * colophon line the moment a visitor scrolled that far — this scrolls away
 * with the hero instead, the same way the rest of the page's content does.
 */
export default function CadOverlay() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-x-0 top-0 -z-10 hidden h-screen overflow-hidden lg:block"
    >
      <CornerMark className="left-5 top-20 border-t border-l" />
      <CornerMark className="right-5 top-20 border-t border-r" />
      <CornerMark className="left-5 bottom-5 border-b border-l" />
      <CornerMark className="right-5 bottom-5 border-b border-r" />

      {/* Ruler edge — major tick every 80px, minor every 16px. Left margin
          only; the right margin already carries the engine. Kept inside the
          leftmost ~36px so it never reaches the hero text column, which
          starts at the 40px section gutter the moment this layer turns on
          (`lg`, 1024px) — verified against the narrowest width this shows at,
          not just wide desktop. */}
      <div
        className="absolute inset-y-0 left-0 w-3 opacity-40"
        style={{
          backgroundImage:
            "repeating-linear-gradient(to bottom, var(--line) 0 1px, transparent 1px 16px), repeating-linear-gradient(to bottom, var(--line) 0 1.5px, transparent 1.5px 80px)",
          backgroundSize: "60% 16px, 100% 80px",
          backgroundPosition: "left top",
          backgroundRepeat: "repeat-y",
        }}
      />

      {/* One reference dimension, called out in the empty left margin — the
          kind of stray callout a cutaway sheet always carries near its
          subject, even where it isn't load-bearing information. Label runs
          sideways along the line rather than out to the right, so its
          footprint stays a couple of characters wide, not a couple of words. */}
      <div className="absolute top-1/2 left-3 h-[34vh] w-px -translate-y-1/2 bg-line/70">
        <Tick className="-top-px" />
        <Tick className="-bottom-px" />
        <span className="t-label absolute top-1/2 left-2 origin-left -translate-y-1/2 -rotate-90 whitespace-nowrap text-fg2">
          FIG. 04 — CORE, NTS
        </span>
      </div>

      {/* Axis / orientation glyph, bottom-left. */}
      <div className="absolute bottom-9 left-9 text-fg2">
        <svg width="34" height="34" viewBox="0 0 34 34" fill="none" className="opacity-70">
          <path d="M2 32V2H32" stroke="currentColor" strokeWidth="1" />
          <path d="M2 32L2 25M2 32L9 32" stroke="currentColor" strokeWidth="1" />
        </svg>
        <span className="t-label absolute top-0.5 -left-0.5 text-[9px]">Z</span>
        <span className="t-label absolute bottom-0.5 left-[38px] text-[9px]">R</span>
      </div>

      {/* Title block, bottom-right — the one place a drawing sheet always
          signs itself. */}
      <div className="absolute right-5 bottom-5 border border-line/70 px-3 py-2 font-mono text-[10px] leading-[1.7] tracking-[0.08em] text-fg2 uppercase">
        <p>DWG — VK·TF001 · REV 01</p>
        <p>TWIN-SPOOL TURBOFAN, CORE SECTION</p>
        <p>SCALE NTS · 3RD ANGLE PROJ.</p>
      </div>
    </div>
  );
}

function CornerMark({ className = "" }) {
  return (
    <span
      className={`absolute block h-4 w-4 border-line/70 ${className}`}
    />
  );
}

function Tick({ className = "" }) {
  return (
    <span
      className={`absolute left-1/2 block h-px w-2.5 -translate-x-1/2 bg-line/70 ${className}`}
    />
  );
}
