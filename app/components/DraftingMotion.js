"use client";

/**
 * The animated half of the background's drafting language — a flat SVG
 * layer composited over TurbineStage's 3D wireframe (which stays the
 * "primary geometry": real twin-spool rotation, already tuned). This layer
 * never re-draws the engine itself; it adds the marks a reviewer actually
 * annotates a cutaway with — a centreline, construction circles, dimension
 * lines, station callouts, an airflow indicator, a sparse grid and a slow
 * inspection scan — each easing in on its own delay so the drawing reads as
 * being built up rather than dropped in at once. See globals.css §Drafting
 * motion background for the keyframes and the `.js` + prefers-reduced-motion
 * contract: without either, every element below renders at its settled,
 * fully-drawn opacity — static, not broken mid-reveal.
 *
 * Coordinates are a tight cluster around (78%, 38%) of the viewBox — the
 * same anchor TurbineBackground's own mask already centres on — not spread
 * across the full width. A first pass used the viewBox's arithmetic centre
 * (300 of 600, i.e. 50%) by mistake and let the station cluster span nearly
 * the whole width; both put labels directly under the hero tagline. Verified
 * against a real screenshot (Playwright), not just by inspecting the numbers
 * — this stuff doesn't reveal itself from source.
 *
 * `dm-parallax-near`/`dm-parallax-far` read `--dm-mx`/`--dm-my`, written by
 * EngineeringBackground's pointermove listener onto a shared ancestor —
 * this component itself holds no mouse-tracking state.
 *
 * Station names and numbers are the reference design's real ones (see
 * projects/08-cycle-model), not filler — the twin-spool cycle model this
 * portfolio already documents.
 */

const VB_W = 640;
const VB_H = 600;
const ANCHOR_X = 0.78 * VB_W; // 499 — matches the mask's own anchor
const ANCHOR_Y = 0.38 * VB_H; // 228

// Four, not the full six — the middle two would sit almost exactly behind
// the hero portrait at this anchor (confirmed with a screenshot: the row's
// horizontal centre lands within a few px of the photo's own centre). The
// portrait is opaque and legitimately occludes background content by
// design (see TurbineBackground's own comment on that), but two orphaned
// label fragments peeking out from behind a photo read as broken, not
// deliberate — cutting to the pair that already falls clear of it, in the
// margins either side, keeps every visible label actually legible.
const STATIONS = [
  { dx: -90, label: "STA 0", sub: "FAN" },
  { dx: -30, label: "STA 25", sub: "HPC" },
  { dx: 30, label: "STA 41", sub: "HPT" },
  { dx: 90, label: "STA 50", sub: "NOZ" },
];

const CENTER_X = ANCHOR_X;
const CENTER_Y = ANCHOR_Y;
const TICK_TOP = CENTER_Y + 20;
const TICK_BOTTOM = CENTER_Y + 45;
const LABEL_Y = CENTER_Y + 60;

export default function DraftingMotion() {
  return (
    <div
      aria-hidden="true"
      className="dm-layer pointer-events-none absolute inset-0 overflow-hidden [mask-image:radial-gradient(85%_130%_at_50%_40%,black_55%,transparent_100%)] md:[mask-image:radial-gradient(120%_100%_at_78%_38%,black_55%,transparent_100%)]"
    >
      {/* Sparse dot grid — the one element visible from `md`, everything
          else waits for `lg` where there is room to read it. */}
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="xMidYMid slice"
        className="dm-parallax-far absolute inset-0 hidden h-full w-full opacity-[0.045] md:block"
      >
        <defs>
          <pattern id="dm-grid-dots" width="42" height="42" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="var(--fg2)" />
          </pattern>
        </defs>
        <rect width={VB_W} height={VB_H} fill="url(#dm-grid-dots)" className="dm-grid" />
      </svg>

      {/* Centreline, construction geometry, dimensions and station
          annotations — the desktop-only detail tier, kept as a tight
          cluster around the mask's own anchor rather than spanning the
          full viewBox width. */}
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="xMidYMid slice"
        className="dm-detail absolute inset-0 hidden h-full w-full lg:block"
      >
        <defs>
          <marker
            id="dm-arrow"
            viewBox="0 0 10 10"
            refX="7"
            refY="5"
            markerWidth="4.5"
            markerHeight="4.5"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 Z" fill="var(--fg2)" />
          </marker>
        </defs>

        {/* Centreline — the long-short-long GD&T dash convention, fading
            in first so everything after reads as annotating it. */}
        <line
          x1={CENTER_X - 150}
          y1={CENTER_Y}
          x2={CENTER_X + 138}
          y2={CENTER_Y}
          strokeDasharray="26 6 4 6"
          className="dm-appear dm-parallax-far [stroke:var(--fg2)]"
          style={{ "--dm-delay": "0ms" }}
          strokeWidth="1"
          opacity="0.14"
        />
        <text
          x={CENTER_X - 144}
          y={CENTER_Y - 8}
          className="dm-appear [fill:var(--fg2)]"
          style={{ "--dm-delay": "150ms", font: "500 9px var(--font-mono)", letterSpacing: "0.1em" }}
          opacity="0.28"
        >
          CL
        </text>

        {/* Construction geometry — two small reference circles at roughly
            the compressor and turbine stations, each with a short
            schematic rotation arc rather than a spinning render. */}
        <g className="dm-appear dm-parallax-near" style={{ "--dm-delay": "500ms" }} opacity="0.1">
          <circle cx={CENTER_X - 40} cy={CENTER_Y} r="20" fill="none" className="[stroke:var(--fg2)]" strokeWidth="1" />
          <circle cx={CENTER_X + 60} cy={CENTER_Y} r="15" fill="none" className="[stroke:var(--fg2)]" strokeWidth="1" />
        </g>
        <path
          d={`M ${CENTER_X - 40} ${CENTER_Y - 18} A 18 18 0 0 1 ${CENTER_X - 22} ${CENTER_Y - 2}`}
          fill="none"
          className="dm-rotation [stroke:var(--fg2)]"
          style={{ "--dm-delay": "900ms", transformOrigin: `${CENTER_X - 40}px ${CENTER_Y}px` }}
          strokeWidth="1"
          opacity="0.18"
          markerEnd="url(#dm-arrow)"
        />
        <path
          d={`M ${CENTER_X + 60} ${CENTER_Y - 13} A 13 13 0 0 1 ${CENTER_X + 73} ${CENTER_Y - 1}`}
          fill="none"
          className="dm-rotation [stroke:var(--fg2)]"
          style={{ "--dm-delay": "1000ms", transformOrigin: `${CENTER_X + 60}px ${CENTER_Y}px` }}
          strokeWidth="1"
          opacity="0.18"
          markerEnd="url(#dm-arrow)"
        />

        {/* Dimension lines — two short spans with arrowheads, periodically
            pulsing rather than sitting at one flat opacity forever. */}
        <g
          className="dm-dim"
          style={{ "--dm-delay": "1300ms", "--dm-cycle": "11s", "--dm-pulse-delay": "3s", "--dm-base": 0.08, "--dm-peak": 0.18 }}
        >
          <line
            x1={CENTER_X - 70}
            y1={CENTER_Y + 64}
            x2={CENTER_X - 10}
            y2={CENTER_Y + 64}
            className="[stroke:var(--fg2)]"
            strokeWidth="1"
            markerStart="url(#dm-arrow)"
            markerEnd="url(#dm-arrow)"
          />
          <line x1={CENTER_X - 70} y1={CENTER_Y + 58} x2={CENTER_X - 70} y2={CENTER_Y + 70} className="[stroke:var(--fg2)]" strokeWidth="1" />
          <line x1={CENTER_X - 10} y1={CENTER_Y + 58} x2={CENTER_X - 10} y2={CENTER_Y + 70} className="[stroke:var(--fg2)]" strokeWidth="1" />
        </g>
        <g
          className="dm-dim"
          style={{ "--dm-delay": "1450ms", "--dm-cycle": "13s", "--dm-pulse-delay": "7s", "--dm-base": 0.08, "--dm-peak": 0.16 }}
        >
          <line
            x1={CENTER_X + 20}
            y1={CENTER_Y + 64}
            x2={CENTER_X + 80}
            y2={CENTER_Y + 64}
            className="[stroke:var(--fg2)]"
            strokeWidth="1"
            markerStart="url(#dm-arrow)"
            markerEnd="url(#dm-arrow)"
          />
          <line x1={CENTER_X + 20} y1={CENTER_Y + 58} x2={CENTER_X + 20} y2={CENTER_Y + 70} className="[stroke:var(--fg2)]" strokeWidth="1" />
          <line x1={CENTER_X + 80} y1={CENTER_Y + 58} x2={CENTER_X + 80} y2={CENTER_Y + 70} className="[stroke:var(--fg2)]" strokeWidth="1" />
        </g>

        {/* Airflow — a dashed line along the centreline whose dash offset
            loops continuously once it appears, reading as slow left-to-
            right flow rather than a static dashed rule. */}
        <line
          x1={CENTER_X - 130}
          y1={CENTER_Y}
          x2={CENTER_X + 128}
          y2={CENTER_Y}
          strokeDasharray="3 9"
          className="dm-airflow dm-parallax-near [stroke:var(--accent)]"
          style={{ "--dm-delay": "1900ms" }}
          strokeWidth="1"
          opacity="0.16"
          markerEnd="url(#dm-arrow)"
        />

        {/* Station callouts — the only part of this layer that responds to
            the pointer: hovering a label brings its own leader tick and
            text up from background texture to legible. */}
        {STATIONS.map((s, i) => (
          <g
            key={s.label}
            className="dm-region dm-appear dm-parallax-near"
            style={{ "--dm-delay": `${2200 + i * 90}ms` }}
          >
            <line
              x1={CENTER_X + s.dx}
              y1={TICK_TOP}
              x2={CENTER_X + s.dx}
              y2={TICK_BOTTOM}
              className="dm-region-tick [stroke:var(--fg2)]"
              strokeWidth="1"
              opacity="0.16"
            />
            <text
              x={CENTER_X + s.dx}
              y={LABEL_Y}
              textAnchor="middle"
              className="dm-region-text [fill:var(--fg2)]"
              style={{ font: "500 7.5px var(--font-mono)", letterSpacing: "0.05em" }}
              opacity="0.22"
            >
              {s.label} · {s.sub}
            </text>
          </g>
        ))}
      </svg>

      {/* Inspection scan — a soft translucent band drifting slowly across
          the drawing, the way a reviewer's eye (or a plotter's pen) tracks
          a sheet left to right. Loops on a long, unhurried cycle. */}
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="xMidYMid slice"
        className="absolute inset-0 hidden h-full w-full lg:block"
      >
        <defs>
          <linearGradient id="dm-scan-gradient" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="var(--fg2)" stopOpacity="0" />
            <stop offset="50%" stopColor="var(--fg2)" stopOpacity="0.05" />
            <stop offset="100%" stopColor="var(--fg2)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect x="-80" y="0" width="140" height={VB_H} fill="url(#dm-scan-gradient)" className="dm-scan" />
      </svg>

      {/* Mobile — a small vertical variant of the same drafting language,
          matching TurbineStage's own 90° roll on narrow viewports. Only
          non-textual marks live here: this whole layer is viewport-fixed
          (via .eb-stage), not scoped to the hero, so a "bottom-40px" offset
          means 40px above whatever the CURRENT viewport's bottom edge is —
          fine for a line or a dot grid crossing behind content at low
          opacity (the engine itself already does exactly that on mobile),
          but confirmed broken for readable text: on a short viewport
          (360×640) the station notation landed squarely on the status
          line, because the hero's actual rendered height and "40px from
          whatever the current window's bottom happens to be" are two
          different numbers. The DWG number and station notation moved into
          Hero.js itself instead, in normal document flow, where the
          browser's own layout — not a guessed pixel offset — keeps them
          correctly positioned at any viewport height. `dm-detail` fades
          this down once scrolled past the hero, same as the desktop tier. */}
      <div className="dm-detail pointer-events-none absolute inset-0 overflow-hidden md:hidden">
        <div
          className="dm-appear absolute inset-y-0 left-1/2 w-px -translate-x-1/2 opacity-[0.12]"
          style={{
            "--dm-delay": "0ms",
            backgroundImage:
              "repeating-linear-gradient(to bottom, var(--fg2) 0 22px, transparent 22px 28px, var(--fg2) 28px 32px, transparent 32px 54px)",
          }}
        />
        <span
          className="dm-appear absolute top-16 left-1/2 -translate-x-1/2 text-fg2 opacity-40"
          style={{ "--dm-delay": "150ms", font: "500 9px var(--font-mono)", letterSpacing: "0.1em" }}
        >
          CL
        </span>
        <div
          className="dm-grid absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage: "radial-gradient(var(--fg2) 1px, transparent 1px)",
            backgroundSize: "34px 34px",
          }}
        />
      </div>
    </div>
  );
}
