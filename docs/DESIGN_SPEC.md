# DESIGN_SPEC.md — Portfolio Revamp: Vinaykumar Venkateshkumar

Author: Kai Andersen (principal product designer).
Implementer: this document is complete and self-contained. Every measurement is decided. Do not substitute values. Where this spec says "delete", delete. Where it is silent, default to less.

Site: single-page portfolio at vinaykumar.is-a.dev. Stack stays: Next.js 16 App Router, Tailwind CSS 4, React 19, Vercel, Web3Forms contact backend. All real content (name, projects, experience, education, links, CV PDF, headshot, Web3Forms flow) is preserved — this is a redesign of presentation, with the specific content edits called out in §5.

---

## 1. Design direction

**Concept: "Instrument Grade."** The site should read like a flight-test instrument: dark, monochrome, typographically precise, with a single test-flight orange accent — the color painted on experimental aircraft so the important thing is unmissable. The owner's black-and-white studio portrait already belongs to this world; the design is built around it. Five principles govern every decision:

1. **One accent, spent sparingly.** Orange marks the current focus (kickers, links, live markers). Everything else is a grayscale.
2. **Typography is the layout.** Hierarchy comes from size, weight, and a mono/sans contrast — never from boxes. No cards.
3. **Rules, not containers.** Content is separated by 1px horizontal rules and whitespace, like an engineering drawing.
4. **Thin content presented as editorial, not inventory.** Two projects are two numbered chapters, full-width, generous — not two lonely cards in a grid.
5. **Motion is punctuation.** Entrances are staggered and rules draw themselves in, but nothing loops, follows the cursor, or scrubs to scroll (see §3.5).

Dark mode is the default and the primary design target. Light mode is fully specified and switched purely by `prefers-color-scheme` — there is no manual toggle (a toggle is UI about the UI; delete the idea).

---

## 2. Audit summary — what is wrong today

Concrete problems in the current implementation, by file:

- **No loaded typeface.** `app/layout.js` imports no `next/font`; the site renders in the browser default sans. Zero typographic identity for a portfolio whose whole job is credibility.
- **Card-itis.** `app/page.js` wraps every unit of content — projects, experience, education, skill groups, certifications, contact links, even the form (`app/ContactForm.js` line 80) — in `rounded-2xl border border-line` cards. The page reads as a template, and thin content (2 projects, 1 internship) looks like a sparsely stocked shelf.
- **Pill overload.** `Tag` component (`page.js` ~line 38) renders `rounded-full` pills for every skill, module, and tag — dozens of pills. Skill tag-clouds are the #1 template tell. Delete the `Tag` component entirely.
- **Graph-paper hero background.** `.grid-bg` in `app/globals.css` (lines 24–32) is a generic dev-portfolio trope. Delete the class and its usage.
- **Emoji in the hero.** `📍 {profile.location}` (`page.js` line 97). Never. Replace per §5.2.
- **Zebra sections.** Alternating `bg-wash` bands (`page.js` lines 187, 280) are a template rhythm. All sections sit on one background; rules do the separating.
- **Mixed radii and lazy hovers.** `rounded-full` buttons, `rounded-2xl` cards, `rounded-lg` inputs coexist; buttons hover via `hover:opacity-85` (opacity fades on solid fills read as cheap). `hover:shadow-sm` on project cards is motion without meaning.
- **Light-only palette** in `globals.css` `@theme`; no dark scheme despite a B/W portrait and an engineering audience that overwhelmingly browses dark.
- **Accessibility gaps:** no `:focus-visible` treatment anywhere; form inputs use `outline-none` with only a border-color change (`ContactForm.js` lines 106/123/140) — insufficient focus affordance; `scroll-behavior: smooth` is unconditional (no `prefers-reduced-motion` guard); no skip link; mobile users lose all section navigation (nav links are `hidden` below `md`, `page.js` line 55).
- **Contact section has three competing CTAs** — a 4-card link grid, a form, and a big CV button stacked with no hierarchy (`page.js` lines 336–374). `break-all` on link text wraps mid-word.
- **Metadata is minimal**: `app/layout.js` has no `metadataBase`, no OG image, no Twitter card, no canonical URL.
- **Certifications list leads with IELTS sub-scores** — visa paperwork presented as an achievement. Content edit in §5.6.

What already works and must be kept: the `app/data.js` single-source-of-content pattern; the Web3Forms form logic including the honeypot, the no-key `mailto` fallback, and the idle/sending/sent/error state machine; the mono index numbers on section headings (the one good instinct — it survives, refined); Vercel Analytics + Speed Insights; the CV PDF; the headshot.

---

## 3. Design tokens

All tokens are declared in `app/globals.css`. Pattern: raw scheme values live on `:root` custom properties that flip under `@media (prefers-color-scheme: light)`; Tailwind `@theme` maps utility names onto them so classes like `bg-bg0 text-fg1 border-line` work in both schemes automatically.

```css
@import "tailwindcss";

:root {
  color-scheme: dark;
  --bg0: #0A0C0E;      /* page background */
  --bg1: #101316;      /* raised surface: inputs, sticky nav fill */
  --line: #23282E;     /* all rules and borders */
  --fg0: #EDEEF0;      /* headings, primary text */
  --fg1: #A8AFB8;      /* body, secondary text */
  --fg2: #788087;      /* faint: meta, footer, placeholders */
  --accent: #FF6D3B;   /* test-flight orange */
  --accent-hover: #FF8A5E;
  --accent-active: #F05A26;
}

@media (prefers-color-scheme: light) {
  :root {
    color-scheme: light;
    --bg0: #FBFBFA;
    --bg1: #F3F3F1;
    --line: #E3E3DF;
    --fg0: #17191C;
    --fg1: #4A5057;
    --fg2: #686E75;
    --accent: #BC3C0A;
    --accent-hover: #9E3208;
    --accent-active: #8A2B06;
  }
}

@theme {
  --color-bg0: var(--bg0);
  --color-bg1: var(--bg1);
  --color-line: var(--line);
  --color-fg0: var(--fg0);
  --color-fg1: var(--fg1);
  --color-fg2: var(--fg2);
  --color-accent: var(--accent);
  --color-accent-hover: var(--accent-hover);
  --color-accent-active: var(--accent-active);
  --font-sans: var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif;
  --font-mono: var(--font-geist-mono), ui-monospace, "SF Mono", monospace;
}
```

### 3.1 Contrast (verified, WCAG relative luminance)

| Pair | Ratio | Use |
|---|---|---|
| `fg0` on `bg0` (dark) | 16.88:1 | headings, primary text |
| `fg1` on `bg0` (dark) | 8.85:1 | body |
| `fg1` on `bg1` (dark) | 8.42:1 | body on surface |
| `fg2` on `bg0` (dark) | 4.89:1 | meta text |
| `accent` on `bg0` (dark) | 7.00:1 | links, kickers |
| `bg0` text on `accent` fill (dark) | 7.00:1 | primary button |
| `fg0` on `bg0` (light) | 17.01:1 | headings |
| `fg1` on `bg0` (light) | 7.87:1 | body |
| `fg2` on `bg0` (light) | 4.98:1 | meta text (4.64:1 on `bg1`) |
| `accent` on `bg0` (light) | 5.35:1 | links, kickers |
| white `#FBFBFA` on `accent` fill (light) | 5.35:1 | primary button |

Every text/background pair in this spec is ≥ 4.5:1. Do not use `fg2` below 12px.

### 3.2 Typography

Families via `next/font/google`: **Geist** (sans) and **Geist Mono** — precise, engineered, current, and free. Setup in §9.3. Weights loaded: Geist 400, 500, 600; Geist Mono 400, 500. No other weights, no italics.

Type scale (rem values; letter-spacing in em):

| Token | Size / line-height | Tracking | Weight | Family | Used for |
|---|---|---|---|---|---|
| `display` | `clamp(2.5rem, 1.2rem + 5.5vw, 4.25rem)` / 1.05 | −0.035 | 600 | sans | Hero name only |
| `h2` | 1.375rem (22px) / 1.3 | −0.02 | 600 | sans | Section titles |
| `h3` | 1.75rem (28px) / 1.25 | −0.025 | 600 | sans | Project titles (projects are the stars — bigger than h2 deliberately) |
| `h4` | 1.0625rem (17px) / 1.4 | −0.01 | 600 | sans | Entry titles (org, school, credential group) |
| `body` | 1rem (16px) / 1.7 | 0 | 400 | sans | Paragraphs, bullets |
| `body-sm` | 0.875rem (14px) / 1.6 | 0 | 400 | sans | Form help, secondary rows |
| `label` | 0.6875rem (11px) / 1.2 | +0.12, uppercase | 500 | mono | Kickers, section indices, form labels, column headers |
| `meta` | 0.8125rem (13px) / 1.5 | +0.01 | 400 | mono | Dates, locations, tech lists, footer |

Color mapping: `display/h2/h3/h4` → `fg0`. `body` → `fg1`. `meta` → `fg2`. `label` → `accent` when it marks a section or state; `fg2` when it is a form/table label.

### 3.3 Layout, spacing, rhythm

- Base unit 4px. Only multiples of 4 appear anywhere.
- Content max-width: **70rem (1120px)**, centered. Gutter: 24px mobile, 40px ≥ 768px. (Class: `mx-auto max-w-[70rem] px-6 md:px-10`.)
- Section grid ≥ 1024px: 12 columns, 32px gap. Every section uses the same split — **label column (cols 1–4)** holding index + title (sticky, `top: 6rem`), **content column (cols 5–12)**. Below 1024px the label stacks above content with 32px between.
- Section vertical padding: 96px top and bottom desktop (`py-24`), 64px mobile (`py-16`). Sections are separated by a full-width 1px `line` rule (`border-t border-line` on each section except hero).
- Hero: 128px top / 112px bottom desktop; 64px / 72px mobile (below the 64px fixed-height nav).
- Vertical rhythm inside content: 8px label→title, 16px title→body, 32px between entries in a list, 48px between sub-groups.

### 3.4 Radii, borders, shadows

- Radius: **0** on everything except form inputs and buttons, which get **2px** (`rounded-[2px]`). No `rounded-full`, no `rounded-2xl`, anywhere. The headshot is a hard-edged square with a 1px `line` border.
- Borders: 1px `line` only. No 2px borders except the focus outline (§9).
- Shadows: **none**. Zero `shadow-*` classes in the codebase. Elevation is expressed by `bg1` fill + 1px border. The sticky nav uses a solid `bg0` fill at 94% opacity with `backdrop-blur-sm` and a bottom rule — that is the only translucency on the site.

### 3.5 Motion

*Revised — the original four-transition list was widened on the owner's instruction. Motion is still punctuation, not decoration: nothing loops, follows the cursor, or reacts to scroll position except the read-progress bar.*

Tokens: `--dur-fast: 120ms` (color/border/opacity), `--dur-base: 200ms` (underline, transform), `--dur-slow: 480ms` (entrances), `--dur-rule: 720ms` (rule draw). Easing is `--ease: cubic-bezier(0.3, 0, 0.4, 1)` for state changes and `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)` for entrances — decelerating, never overshooting.

The complete list of allowed animations:

1. **Link underline.** Text links transition `text-decoration-color` from `line` to `accent`, 120ms. Nav links: `fg1` → `fg0`, 120ms.
2. **Fade-up on first reveal.** Each section's content block fades from `opacity 0, translateY(12px)` to rest over 480ms on first viewport entry (IntersectionObserver, `rootMargin: 0px 0px -15% 0px`, fires **once**).
3. **Stagger.** Direct children of a `.stagger` container inside a revealed block cascade at 70ms per step, capped at 8 steps so long lists never crawl. Applied to: section content columns, project stat figures, toolchain rows.
4. **Rule draw.** Section divider rules `scaleX` from 0 to 1 from the left over 720ms as the section enters view — a line being laid down on a drawing. Transform-only, so it costs no layout.
5. **Hero rise.** Above-the-fold blocks animate on load (not on scroll — an observer would fire immediately anyway), each with its own `--rise-delay` in reading order: portrait 60ms, kicker 0ms, name 90ms, tagline 180ms, status 260ms/300ms, CTA row 340ms. `animation-fill-mode: backwards` holds the pre-animation state through the delay.
6. **Read progress.** A 2px accent bar under the nav scales on `--progress`, written inside `requestAnimationFrame` on a passive scroll listener. No React state, no layout, no paint. `aria-hidden` — the scrollbar already conveys this.
7. **Active section marker.** The current section's nav link warms to `fg0` and grows a 1px accent underline from centre, 200ms. Driven by an IntersectionObserver band just below the header, so exactly one link is current at a time.
8. **Button state.** Background-color transition 120ms between idle/hover/active fills. The hero CTA's arrow advances 2px on hover, `@media (hover: hover)` only. No scale, no bounce.
9. **Form status swap.** Sent-state panel fades in over 200ms.

**Forbidden — do not implement under any circumstances:** infinite marquees/tickers; typewriter effects; tilt/3D card hovers; scale-on-hover; gradient animation; skeleton shimmer; carousels; animated counters; blob/mesh backgrounds; glassmorphism panels; glowing/neon edges; particle effects. If `prefers-reduced-motion: reduce`, every animation on the page collapses to its instant final state (§9.2).

**§3.5a Background exception — the drafting-motion layer.** Parallax, section-triggered scroll motion, and pointer response were added as a deliberate, scoped exception to the rule above, for the fixed background only (`EngineeringBackground.js` / `DraftingMotion.js` / `TurbineStage.js`) — never for page content. The rest of §3.5's restraint still governs everything a reader actually reads or clicks. Specifics:

- **Not scroll-scrubbed.** Section framing is IntersectionObserver-triggered (the same pattern §9.7's active-section marker uses), not a continuous per-scroll-pixel computation — crossing into a section eases the background toward that section's target scale/pan over 1.4s, then holds. This stays cheap and never fights the browser's own scroll performance, which is what the original rule was actually protecting against.
- **Parallax is capped at 5–10px** (`--dm-mx`/`--dm-my`, written by a rAF-throttled `pointermove` listener) and only attaches under `(hover: hover)` — no drag on touch, nothing to feel disconnected from a finger.
- **The engine itself never overtly spins as the interaction** — TurbineStage's twin-spool rotation is real, tuned engine motion (mechanically accurate, not a decorative flourish), and the schematic rotation arcs in `DraftingMotion.js` breathe a few degrees, they don't complete revolutions.
- **All of it is JS-gated at the effect level, not just CSS-gated:** under `prefers-reduced-motion: reduce`, `EngineeringBackground`'s effects never attach, so the background sits at its identity transform permanently — not an instant snap to a moving target, no motion at all.
- Still forbidden even for the background: glow, particles, gradient animation, anything that reads as a product demo rather than an engineering drawing being reviewed.

**No-JS contract.** All hidden initial states are gated behind the `.js` class set by the inline script in `layout.js`. Without JS, every element renders visible and static — there is no flash of visible-then-hidden content, and no content is unreachable to crawlers.


### 3.6 Evidence blocks

Two optional blocks hang off a project entry, both driven from `app/data.js` and both absent by default (§9 of `public/models/README.md` and `public/figures/README.md` cover the asset workflow).

**Theme-aware figures.** A raster plot cannot recolour itself, so a figure may carry `srcLight` alongside `src`; `FigureImage` then ships both renders and CSS shows one. The swap in `globals.css` mirrors §3's scheme logic exactly — dark is the default, light is the media query — rather than using Tailwind's `dark:` variant, which keys off the opposite condition and would let a figure disagree with the palette around it. Only the visible render carries `alt`; the alternate is `aria-hidden`, so a screen reader hears the figure once. Both files download, which is the accepted cost of keeping Next's optimisation pipeline; the figures are lazy and served responsive, so the practical penalty is small.

**Project link.** A project may carry `link: {href, label}`, rendered under the tech line as an accent CTA with the shared arrow micro-interaction. Used where the work has a public repository.

**Figure gallery.** A 2-up (3-up at `sm`) grid of 16:10 thumbnails on the page background — bordered, not carded. Border warms to accent on hover/focus. Clicking opens a lightbox: dimmed page, figure at natural aspect, caption and counter, `←`/`→` to step, `Esc` to close. Focus is trapped while open and returned to the originating thumbnail on close; body scroll is locked. `alt` describes the *result*, never "figure 1".

**Model viewer.** A 16:10 WebGL frame showing a `.glb` of the geometry, orbit and zoom only — no pan, no damping, and `autoRotate` off by default (motion without meaning). Lit neutrally so the part reads as shaded CAD, not a product render; `frameloop="demand"` so an idle viewer costs no GPU. three.js/R3F/drei are code-split *and* gated behind an IntersectionObserver, so the 254 KB gzipped chunk is never fetched by a visitor who does not reach a project that has a model. A missing or malformed file degrades to a caption via an error boundary — the page never blanks. The canvas is not keyboard-operable, so the `figcaption` carries a text description as the accessible equivalent.

### 3.7 CAD gallery (section 02)

A conditional section for CAD work specifically, distinct from §3.6 — those blocks hang off a *project* and argue a result; these show the *parts themselves*. Two blocks, either of which may be empty:

**Product gallery.** A single column at each item's own aspect ratio, set from `width`/`height` in the data, with `object-contain` rather than `object-cover`. A cropped photograph of a part is still a photograph of that part; a cropped general arrangement has lost its wingtips, and a 2.35:1 drawing squeezed into a 4:3 tile spends most of the tile on nothing — the content here is wide because the parts are. Items without dimensions fall back to 4:3. Each tile carries a heading and the tool it was built in (`CATIA V5`, `pyOCC`), since a reviewer scanning for CAD experience looks for the tool name first. Bordered on the page background, warming to accent on hover/focus, opening the same `Lightbox` as the figure gallery.

**CAD viewer.** One 16:10 frame with an optional model switcher above it, rendering a self-hosted `.glb` through the same `ModelViewer` a project entry uses — code-split and gated behind an IntersectionObserver, so three.js is never fetched by a visitor who does not reach it.

This was specified as an embed of viewer.autodesk.com and **cannot be**: that host sends `X-Frame-Options: DENY` and `frame-ancestors 'self' *.autodesk.com`, so browsers refuse to frame it off Autodesk's own domain. No iframe configuration changes a policy set by the other origin. Self-hosting is better regardless — no third party, no cookies, no dependency on a share link staying alive. Where a model also lives on Autodesk, `href` links out to it: their viewer reads the native STEP and shows the exact B-rep rather than a mesh approximation, which is worth offering even though it cannot be embedded. See `docs/CAD_VIEWER.md`.

**Empty state.** Each block returns `null` when it has no data. When *both* are empty, `CadGallery` renders a placeholder in their place: one 16:10 frame reading "Models in preparation", followed by a line pointing the reader at Projects and the CV. A placeholder that only apologises wastes the slot — this one routes the reader to work that does exist. The first entry added to either array retires it automatically, with no flag to unset.

---

## 4. Page architecture

Single page. One person, one narrative, seven scroll-lengths — multiple routes would add navigation cost and dilute the CV-reviewer's 60-second pass. Order:

1. **Nav** — fixed, minimal, CV always reachable.
2. **Hero** — who, what, where, availability; portrait; two actions.
3. **01 / Projects** — the strongest evidence goes first. Two numbered, full-width entries.
4. **02 / CAD Gallery** — designed parts as renders, plus an interactive CAD model. Always present; shows a placeholder while `products` and `cadModels` in `app/data.js` are both empty. See §3.7.
5. **03 / Experience** — the AIESL internship as a single confident entry.
6. **04 / Education** — Cranfield first, then Anna University; module lists as quiet meta text.
7. **05 / Toolchain** — skills as a definition list (renamed from "Technical Skills"; includes Credentials as a sub-group).
8. **06 / Contact** — one statement, one big mailto link, the form.
9. **Footer** — links, colophon.

Section numbers are computed from position in `app/page.js`, not hardcoded, so reordering or inserting a section cannot leave a hole in the sequence.

Rationale for order: a recruiter for an entry-level CFD role needs proof of simulation work before anything else; education matters but Cranfield already appears in the hero location line, so it can sit third; skills are reference material, not narrative, so they sit late; contact is the terminal action.

---

## 5. Wireframes and section specs

Legend: `═` section rule (1px `line`), `─` internal rule, `[ ]` interactive, `◇` accent-colored, mono text shown in CAPS-ish spacing. Desktop frames ≈ 1440px viewport (content 1120px); mobile ≈ 390px.

### 5.1 Nav

Desktop:
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  VK—V6                Projects  Experience  Education  Toolchain  Contact    │
│  (wordmark)                                                    [Download CV] │
└──────────────────────────────────────────────────────────────────────────────┘  ← 1px line rule
```
(single 64px row; wordmark left, links center-right group, CV button far right)

Mobile:
```
┌──────────────────────────────┐
│ VK—V6            [CV] [Menu] │ 64px
└──────────────────────────────┘
│ (Menu open: full-width panel │
│  under bar, bg0, links       │
│  stacked, 56px rows, rules)  │
```

Annotations:
- Bar: `fixed top-0 inset-x-0 z-50`, height 64px, `bg0` at 94% opacity + `backdrop-blur-sm`, `border-b border-line`. Inner container = standard gutter/max-width.
- Wordmark: mono, 13px, weight 500, `fg0`, reading `VK—V6` is wrong — use exactly **`VINAYKUMAR V.`** in `label` style but 12px, tracking +0.08em. Links to `#top`.
- Nav links: `body-sm` 14px, `fg1`, hover `fg0` (120ms), 32px gap. Active-section highlighting is **not** built (scroll-spy is complexity without payoff at this page length).
- Download CV: the only filled button in the header. `accent` fill, text `bg0` (dark) / `#FBFBFA` (light), mono 12px tracking +0.06em uppercase "CV — PDF", padding 8px 16px, radius 2px. Hover `accent-hover`, active `accent-active`.
- Mobile (< 768px): links hidden; show CV button (compact, same style, label "CV") and a "Menu" text button (mono 12px uppercase, `fg1`) that toggles a full-width dropdown panel: `bg0`, `border-b border-line`, links stacked in 56px rows each with a bottom rule, `body` 16px `fg0`. Panel closes on link tap and on Escape. This fixes the current total loss of mobile navigation. No hamburger icon — the word "Menu"/"Close" is the control.

### 5.2 Hero

Desktop:
```
════════════════════════════════════════════════════════════════════════════════
│                                                                              │
│  ◇ PROPULSION / CFD — CRANFIELD UNIVERSITY            ┌────────────┐         │
│                                                       │            │         │
│  Vinaykumar                                           │  portrait  │ 240px   │
│  Venkateshkumar                                       │  B/W, 1px  │         │
│                                                       │  border    │         │
│  CFD and propulsion engineer working on nacelle       └────────────┘         │
│  installation aerodynamics. ANSYS Fluent, parametric  ◇ AVAILABLE SEP 2026   │
│  CAD, validated jet-mixing research.                    ENTRY-LEVEL ROLES    │
│                                                                              │
│  CRANFIELD, UK · SPONSORSHIP REQUIRED                                        │
│                                                                              │
│  [View projects →]   [kumarvsvinay@gmail.com]                                │
│                                                                              │
════════════════════════════════════════════════════════════════════════════════
```

Mobile:
```
│ ┌──────┐                     │
│ │ 80px │ portrait            │
│ └──────┘                     │
│ ◇ PROPULSION / CFD —         │
│   CRANFIELD UNIVERSITY       │
│ Vinaykumar                   │
│ Venkateshkumar   (display)   │
│ CFD and propulsion engineer  │
│ working on nacelle …         │
│ CRANFIELD, UK ·              │
│ SPONSORSHIP REQUIRED         │
│ [View projects →]            │
│ [kumarvsvinay@gmail.com]     │
```

Annotations:
- Two-column desktop: text block cols 1–8, portrait block cols 10–12 top-aligned. Mobile stacks portrait first (80px square), then text; 24px between blocks.
- Kicker: `label` style, `accent`: `PROPULSION / CFD — CRANFIELD UNIVERSITY`. 12px below it → name.
- Name: `display`, `fg0`, two lines allowed. This is the largest text on the site by design.
- Summary paragraph, 20px below name, `body` at 17px/1.6, `fg1`, `max-width: 34rem`. Copy (tightened from `data.js` tagline — update `profile.tagline` to): *"CFD and propulsion engineer working on nacelle installation aerodynamics — ANSYS Fluent simulation, parametric CAD, and a validated jet-mixing study."*
- Status line, 24px below summary: `meta` style, `fg2`: `CRANFIELD, UK · SPONSORSHIP REQUIRED`. No emoji, no pin icon. The current `📍` and the `|` divider are deleted.
- Portrait: `next/image`, `/headshot.jpg`, square, `object-cover`, 240px desktop / 80px mobile, 1px `line` border, radius 0, `priority`. Alt: `"Vinaykumar Venkateshkumar, black-and-white studio portrait"`. Add CSS `filter: grayscale(1)` so the image stays monochrome even if the asset is ever replaced with a color photo.
- Availability marker under portrait (desktop) / merged into status line (mobile): `label` style; first line `accent` with a leading 6px `accent` square glyph (`■`): `AVAILABLE SEP 2026`; second line `fg2`: `ENTRY-LEVEL PROPULSION / CFD / AIRCRAFT DESIGN`. This is `profile.seeking`, reframed as a positive signal.
- Actions row, 40px below status line: primary button "View projects" (accent fill, same recipe as nav CV button but 12px 20px padding, 14px text) with a `→` glyph; secondary is the raw email address as a mono 14px `fg0` text link with `line` underline → `accent` underline on hover. An email address as a literal link is more useful to a recruiter than a "Get in touch" pill.
- No background pattern. `bg0` only. (`.grid-bg` deleted from `globals.css`.)

### 5.3 Section shell (applies to sections 01–05)

Desktop:
```
════════════════════════════════════════════════════════════════════════════════
│  ◇ 01            │   (content column, cols 5–12)                             │
│  Projects        │                                                           │
│  (sticky top-24) │                                                           │
════════════════════════════════════════════════════════════════════════════════
```
Mobile: label block (index + title inline: `◇ 01 / Projects`) stacked above content, 32px gap.

- Index: `label`, `accent`. Title: `h2`, `fg0`, 8px below index on desktop; inline on mobile.
- The current `SectionHeading` kicker lines ("Research and simulation work in…") are deleted — they restate the content.
- Label column is `position: sticky; top: 6rem` within the section (desktop only).

### 5.4 Section 01 — Projects

Desktop content column:
```
│  01·A                                    ONGOING — SEP 2026 ◇■               │
│  Installation Aerodynamics of                                                │
│  Aero-Engine Nacelles                                        (h3)            │
│  Cranfield Individual Research Project                       (meta)          │
│                                                                              │
│  Investigating installation aerodynamics with a Python-based                 │
│  propulsion-integration tool, applying iCST parametric geometry              │
│  to model nacelle installation effects.                                      │
│  Developing and benchmarking a pyOCC / OpenCASCADE geometry-                 │
│  generation workflow against commercial CAD output.                          │
│                                                                              │
│  PYTHON · ICST · PYOCC · OPENCASCADE · OPENFOAM              (meta, fg2)     │
│  ──────────────────────────────────────────────────────────────────          │
│  01·B                                              MAR 2025                  │
│  Investigation of Controlled Jets for                                        │
│  Enhanced Mixing Rates                                                       │
│  BEng Final Year Project — team of 3                                         │
│                                                                              │
│  ▸ 64–76% core-length reduction     ▸ Mach 0.6–1.0     ▸ 3.4M+ nodes         │
│                                                                              │
│  Passive flow-control tab geometries (Delta Tandem Tab, M Delta              │
│  Tandem Tab) to enhance nozzle jet mixing. ANSYS Fluent simulations          │
│  with grid-independence studies, validated against experimental              │
│  shadowgraph imaging. No significant thrust penalty.                         │
│                                                                              │
│  ANSYS FLUENT · DESIGNMODELER · ICEM CFD                                     │
```

Mobile: identical order, single column; the stat row wraps to a stacked list.

Annotations:
- No cards, no borders around entries. Entries separated by a 1px `line` rule with 48px space above and below it.
- Entry index `01·A` / `01·B`: `label`, `fg2`. Period/date: `meta`, `fg2`, right-aligned on the same baseline row (flex `justify-between`). The ongoing project's date gets a leading 6px `accent` square — live work is literally marked in orange.
- Title `h3` `fg0`, 8px under the index row; context line `meta` `fg2`, 4px under title.
- Body: the current bullet arrays render as `body` 16px/1.7 `fg1` paragraphs (join each `points` item as its own paragraph, 12px apart). Delete the accent-dot `<li>` markers.
- **Stat row (project B only):** the measurable results are pulled out of prose into a horizontal row of three figures: value in sans 600 17px `fg0`, label beneath in `label` `fg2` (`CORE-LENGTH REDUCTION`, `MACH RANGE VALIDATED`, `MESH NODES`). 40px gap between figures; wraps on mobile. Data additions to `data.js`: add `stats: [{value:"64–76%",label:"Core-length reduction"},{value:"M 0.6–1.0",label:"Validated range"},{value:"3.4M+",label:"Mesh nodes"}]` to the jets project. This is how thin content is made to look deliberate: fewer items, richer treatment.
- Tech list: `meta`, `fg2`, uppercase, ` · ` separated, 24px below body. The `tags` pill array from `data.js` is **not rendered** (the tech list covers it); keep the data field, unused, or delete it.

### 5.5 Section 02 — Experience

Desktop content column:
```
│  AI Engineering Services Limited (AIESL)          MAR — APR 2025             │
│  Engineering Intern — Aircraft Maintenance        THIRUVANANTHAPURAM, IN     │
│  Boeing 737 MRO base servicing Air India Express  (meta, fg2)                │
│                                                                              │
│  Rotational internship across Component Overhaul, Material/Production        │
│  Planning, and Stores. Documented wheel/brake overhaul procedures            │
│  (torque spec 158 lb-ft, tyre pressure 205 ± 5 psi) and Eddy Current         │
│  Testing for non-destructive flaw detection. Tracked parts issuance          │
│  and task-card compliance in AMOS and RAMCO.                                 │
```

Mobile: org/role stack, dates+location as one `meta` line beneath, then body.

Annotations:
- Header row: org `h4` `fg0` left; date `meta` `fg2` right. Second row: role in `body-sm` 500 `fg1` left; location `meta` `fg2` right. Sub-line `meta` `fg2`.
- Bullets merge into flowing paragraphs (same rule as projects). The concrete numbers (158 lb-ft, 205 ± 5 psi) stay — specificity is the credibility.
- One entry only: no rules needed inside; the generous section shell makes a single entry read as a statement, not a shortage.

### 5.6 Section 03 — Education

Desktop content column:
```
│  Cranfield University                              OCT 2025 — SEP 2026 ◇■    │
│  Thermal Power and Propulsion — Postgraduate       CRANFIELD, UK             │
│                                                                              │
│  MODULES  Gas Turbine Performance · Combustion · Turbomachinery              │
│           Aerodynamics · Propulsion System Design                            │
│  THESIS   Installation aerodynamics of aero-engine nacelles (ongoing)        │
│  ────────────────────────────────────────────────────────────────            │
│  KCG College of Technology, Anna University        2021 — 2025               │
│  BEng Aeronautical Engineering — CGPA 7.37/10      CHENNAI, IN               │
│                                                                              │
│  MODULES  Air Breathing Propulsion · Rocket Propulsion · Aerodynamics        │
│           I & II · CFD · Aircraft Structures I & II · FEM · Wind             │
│           Tunnel Techniques · NDT · Aircraft Design · Thermodynamics         │
```

Annotations:
- Same header-row pattern as Experience (`h4` + `meta`). Cranfield's period gets the `accent` square (current).
- Modules: a two-column definition row — `label` `fg2` term ("MODULES", "THESIS") in a 88px fixed column, definition as `meta`-sized (13px) sans `fg1` text, ` · ` separated, wrapping. **No pills.** Mobile: term stacks above definition.
- Entries separated by the standard 1px rule, 40px clearance.

### 5.7 Section 04 — Toolchain

Desktop content column (definition-list rows):
```
│  CFD & SIMULATION      ANSYS Fluent · ICEM CFD / Meshing · k-ε / k-ω        │
│                        turbulence modelling · OpenFOAM · grid-               │
│                        independence studies                                  │
│  ─────────────────────────────────────────────────────────────────           │
│  CAD & GEOMETRY        CATIA V5 · ANSYS DesignModeler · pyOCC /              │
│                        OpenCASCADE · iCST parametric geometry                │
│  ─────────────────────────────────────────────────────────────────           │
│  PROGRAMMING           Python · MATLAB                                       │
│  ─────────────────────────────────────────────────────────────────           │
│  DOMAINS               Propulsion · Aerodynamics · Jet flow control ·        │
│                        Thermodynamics · Aircraft structures · NDT            │
│                                                                              │
│  CREDENTIALS           CATIA V5 — CADD Centre, 80 hrs          2024          │
│                        MATLAB Essential Training — LinkedIn     2024         │
│                        ML with Python / DL with TensorFlow —    2024         │
│                        IBM Cognitive Class                                   │
```

Mobile: term stacks above items, rows keep their rules.

Annotations:
- Semantic `<dl>`. Term (`<dt>`): `label`, `fg2`, fixed 176px column desktop. Definition (`<dd>`): `body-sm` 14px/1.7 `fg1`, ` · ` separated plain text. Rows separated by 1px rules with 20px padding-block. **No proficiency bars, no pills, no icons, no percentages — ever.**
- Skill levels are not displayed except where factual ("CATIA V5" drops "(Proficient)" from the list — the 80-hr certification line carries the proof).
- **Credentials sub-group** replaces the "Certifications & Achievements" block: same `<dl>` row, each credential on its own line with year right-aligned in `meta` `fg2`. **Content edit (deliberate): the IELTS entry is removed from the page.** Language-test sub-scores are visa admin, not engineering achievement, and publishing a 5.5 Speaking band actively works against the owner. It remains in the CV PDF; delete the object from `certifications` in `data.js` or filter it out. Everything else stays.

### 5.8 Section 05 — Contact

Desktop content column:
```
│  Hiring for propulsion, CFD, or aircraft-design work?                        │
│  I reply within a day.                          (h3, fg0, max-w 30rem)       │
│                                                                              │
│  ◇ kumarvsvinay@gmail.com        (mono 20px, accent, underlined link)        │
│                                                                              │
│  ──────────────────────────────────────────────────────────────────          │
│                                                                              │
│  NAME                          EMAIL                                         │
│  [__________________]          [__________________]                          │
│  MESSAGE                                                                     │
│  [________________________________________________]                         │
│  [__________________________________________ 5 rows]                        │
│                                                                              │
│  [Send message]        or download the [CV — PDF]                            │
```

Mobile: statement, email link, then form fields stacked full-width.

Annotations:
- The 4-card contact grid is **deleted**. Email is promoted to a single large mono link (20px, `accent`, 1px underline offset 4px, hover `accent-hover`); phone, LinkedIn, GitHub move to the footer where reference data belongs.
- Statement: `h3` sizing, `fg0`. Exact copy: *"Hiring for propulsion, CFD, or aircraft-design work? I reply within a day."*
- Form (restyled `ContactForm.js`, logic untouched — keep env-key guard, honeypot, fetch flow, state machine):
  - Labels: `label` style, `fg2`, 8px above field. Keep `htmlFor`/`id` pairs.
  - Inputs: `bg1` fill, 1px `line` border, radius 2px, padding 10px 12px, `body-sm` 14px `fg0`, placeholder `fg2`. Focus: `border-accent` **plus** the global focus outline (§8.1) — replace `outline-none` with `focus-visible` treatment.
  - Error text: `accent` (not Tailwind `red-600` — the accent doubles as the alert hue in this monochrome system; light-mode `#BC3C0A` reads as alert on white, dark-mode ratio 7.0:1 exceeds AA), `body-sm`, `role="alert"` kept, plus `aria-invalid` wiring per §8.4.
  - Submit: primary button recipe. Sending state keeps `disabled:opacity-50` but adds `cursor: default`.
  - Sent state: `bg1` panel, 1px `line` border, radius 0, left-aligned (not centered): `h4` "Message sent." + `body-sm` `fg1` line + "Send another" text link.
  - No-key fallback panel: same `bg1`/`line` recipe.
- CV link: text link beside submit, mono 13px, `fg1` underline → `accent`. The big duplicate CV button at the bottom of the current contact section is deleted (nav owns the primary CV action).

### 5.9 Footer

Desktop:
```
════════════════════════════════════════════════════════════════════════════════
│  © 2026 VINAYKUMAR VENKATESHKUMAR        GITHUB   LINKEDIN   +44 7742 914241 │
│  PROPULSION · CFD · PARAMETRIC CAD                            CV — PDF       │
════════════════════════════════════════════════════════════════════════════════
```
Mobile: two stacked groups, 16px apart.

- All footer text: `meta` 13px mono. Left block `fg2`; links right, `fg1`, underline on hover → `accent`. GitHub → `profile.github`, LinkedIn → `profile.linkedin`, phone → `tel:` link, CV → PDF. 40px padding-block, `border-t border-line`.
- Year computed as today (`new Date().getFullYear()` is fine — page is static-rendered per deploy, acceptable drift).

---

## 6. Component inventory

All under `app/components/`. Server components unless marked. Content still flows exclusively from `app/data.js` — components take data as props; no copy hardcoded in JSX except structural labels.

| File | Props | States / notes | Responsive |
|---|---|---|---|
| `Nav.js` (client) | `nav: {href,label}[]`, `cvHref` | `menuOpen` boolean (mobile panel); Escape + link-click close; `aria-expanded` on trigger | Links row ≥768px; Menu button + panel <768px |
| `Hero.js` | `profile` | none | 2-col ≥1024px; stacked below |
| `Section.js` | `index` ("01"), `title`, `id`, `children` | renders shell of §5.3; wraps children in `Reveal` | sticky label ≥1024px |
| `Reveal.js` (client) | `children`, `delay?` | IO fade-up once (§3.5.2); renders children statically when `prefers-reduced-motion` | n/a |
| `FigureImage.js` | `figure`, `sizes`, `className?`, `priority?` | renders one `<Image>`, or two with the `.fig-light`/`.fig-dark` swap when `srcLight` is set | inherits |
| `ProjectEntry.js` | `project` (incl. optional `stats`, `link`) | accent square when `period` contains "Ongoing" | stat row wraps <640px |
| `CadGallery.js` | `products`, `models`, `cvHref?` | composes the two blocks below; renders the §3.7 placeholder when both are empty | inherits from children |
| `ProductGallery.js` (client) | `products`, `label?` | `openAt` index; returns `null` when empty; per-item aspect ratio; shares `Lightbox` and `FigureImage` | single column at all widths |
| `CadViewer.js` (client) | `models`, `label?` | `active` model index; returns `null` when empty; switcher only when >1 model; delegates the canvas to `ModelViewer` | frame is fluid 16:10; switcher wraps |
| `ExperienceEntry.js` | `entry` | — | header rows stack <640px |
| `EducationEntry.js` | `entry` | accent square on current period | dl term stacks <768px |
| `ToolchainList.js` | `skills`, `certifications` | renders `<dl>` incl. Credentials rows | term column collapses <768px |
| `ContactSection.js` | `profile` | — | 1-col <768px |
| `ContactForm.js` (client, existing file restyled) | `email` | idle / sending / sent / error / no-key (all preserved) | 2-col name+email ≥640px |
| `Footer.js` | `profile` | — | stacks <640px |

`app/page.js` becomes a thin composition of these. Delete the inline `SectionHeading` and `Tag` components.

---

## 7. Responsive breakpoints

Tailwind defaults; exact behavior:

- **< 640px (base, design at 390px):** single column everywhere; gutter 24px; section padding-block 64px; hero portrait 80px above text; stat row stacks vertically (12px gaps); nav = wordmark + CV + Menu; form fields full-width stacked; footer stacked.
- **≥ 640px (`sm`):** form name/email side-by-side (16px gap); stat row horizontal; entry header rows become two-ended flex lines.
- **≥ 768px (`md`):** nav links visible, Menu button removed; gutter 40px; `<dl>` term columns activate (176px / 88px fixed).
- **≥ 1024px (`lg`):** 12-col section grid with sticky label column engages; hero goes two-column with 240px portrait; section padding-block 96px.
- **≥ 1440px:** no change — content stays capped at 1120px; whitespace grows symmetrically. No ultra-wide special casing.

No horizontal scrolling at any width ≥ 320px; the long email/URL strings are broken with `break-words` (never `break-all`) or wrapped in `overflow-wrap: anywhere` only inside the footer.

---

## 8. Accessibility requirements

1. **Focus:** global rule in `globals.css`:
   ```css
   :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }
   ```
   Remove every `outline-none`. Focus outlines must be visible on nav links, buttons, form fields, and footer links; verify against both schemes.
2. **Reduced motion:**
   ```css
   @media (prefers-reduced-motion: reduce) {
     html { scroll-behavior: auto; }
     *, *::before, *::after { animation: none !important; transition: none !important; }
   }
   ```
   `Reveal.js` must render content fully visible (no initial `opacity-0`) when the media query matches — check it in JS, don't rely on CSS alone, so content is never hidden if JS fails mid-reveal. Additionally: initial state must be applied by JS, not markup, so no-JS visitors see everything.
3. **Landmarks & semantics:** one `<header>`, one `<main id="top">`, one `<footer>`; each section is `<section aria-labelledby>` its `h2` id; skip link as first DOM element (`"Skip to content"`, visually hidden until focused, jumps to `#top`); heading order h1 → h2 → h3/h4 with no skips; the toolchain uses a real `<dl>`; document has exactly one `<h1>` (hero name).
4. **Form:** visible labels kept (never placeholder-as-label); on error set `aria-invalid="true"` on offending fields and keep `role="alert"` on the message; error text never conveyed by color alone (it is text); submit button min target 44×32px; honeypot keeps `aria-hidden` + `tabIndex={-1}`.
5. **Images:** headshot alt per §5.2; decorative accent squares are CSS pseudo-elements or `aria-hidden` spans.
6. **Color scheme:** `color-scheme` set on `:root` per scheme (form controls, scrollbars render correctly); all ratios per §3.1.
7. **Nav panel:** mobile menu trigger is a `<button>` with `aria-expanded`/`aria-controls`; panel links are plain anchors; focus stays in document flow (no trap needed — panel is in-flow, not modal).

---

## 9. Implementation notes

### 9.1 Build sequence

1. `globals.css`: replace entire file — token block from §3, focus rule, reduced-motion block, keep `scroll-padding-top: 5rem`, smooth scroll gated behind `@media (prefers-reduced-motion: no-preference)`. Delete `.grid-bg`.
2. `app/layout.js`: add fonts (§9.3), upgraded metadata (§9.4), `bg-bg0 text-fg1 font-sans` on body. Keep `<Analytics />` and `<SpeedInsights />` exactly as-is.
3. Build `Section.js` + `Reveal.js`, then components top-to-bottom: Nav, Hero, ProjectEntry, ExperienceEntry, EducationEntry, ToolchainList, ContactSection (+ restyle `ContactForm.js` — move it to `app/components/`, update the import), Footer.
4. Rewrite `app/page.js` as composition. Delete `SectionHeading`, `Tag`, the contact card grid, the bottom CV button, all `rounded-2xl`/`rounded-full`/`shadow`/`bg-wash` classes.
5. `data.js` edits (only these): tightened `tagline` (§5.2); add `stats` to the jets project (§5.4); remove the IELTS certification entry (§5.7); everything else byte-identical.
6. QA pass (§9.5).

### 9.2 Keep / delete

**Keep:** Web3Forms endpoint + `NEXT_PUBLIC_WEB3FORMS_ACCESS_KEY` guard + honeypot + status machine; `@vercel/analytics` + `@vercel/speed-insights`; `/Vinaykumar_Venkateshkumar_CV.pdf`; `/headshot.jpg`; `data.js` as single content source; single-page anchor architecture; README (update its Structure section after the move).
**Delete:** `.grid-bg`; old `@theme` colors (`ink/ink-2/muted/line/paper/wash` — fully replaced, no aliases); `Tag`; `SectionHeading`; contact card grid; emoji; kicker lines; IELTS page entry; every `shadow-*`, `rounded-2xl`, `rounded-full`, `hover:opacity-85`.

### 9.3 Fonts (`next/font`)

```js
// app/layout.js
import { Geist, Geist_Mono } from "next/font/google";
const geist = Geist({ subsets: ["latin"], weight: ["400","500","600"], variable: "--font-geist-sans", display: "swap" });
const geistMono = Geist_Mono({ subsets: ["latin"], weight: ["400","500"], variable: "--font-geist-mono", display: "swap" });
// <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
```
`@theme` maps `--font-sans`/`--font-mono` onto these variables (§3), so `font-sans`/`font-mono` utilities just work.

### 9.4 Metadata

Extend the existing object: `metadataBase: new URL("https://vinaykumar.is-a.dev")`, `alternates: { canonical: "/" }`, keep title/description, add `openGraph.url`, `openGraph.siteName`, `openGraph.images: ["/headshot.jpg"]`, and `twitter: { card: "summary", images: ["/headshot.jpg"] }`. Keep wording of title/description unchanged.

### 9.5 Final QA checklist

- [ ] `npm run build` clean; page fully statically prerendered.
- [ ] Lighthouse (mobile, production build): Performance ≥ 95, Accessibility 100, Best Practices 100, SEO 100.
- [ ] Keyboard walkthrough: Tab from load → skip link → wordmark → nav links → CV → hero actions → … → form → footer; every stop shows the 2px accent outline; mobile menu operable by keyboard; Escape closes it.
- [ ] Both color schemes checked (macOS appearance toggle): no hardcoded hex leaks, form controls match scheme.
- [ ] `prefers-reduced-motion`: no smooth scroll, no reveal animation, all content visible.
- [ ] JS disabled: all content visible (reveal initial states applied by JS only), form falls back gracefully (native validation still labels fields).
- [ ] 320px width: no horizontal scroll.
- [ ] Contact form: real submission against Web3Forms succeeds; error path (bad key locally) shows accent alert; no-key fallback renders.
- [ ] Grep the repo for `rounded-full`, `rounded-2xl`, `shadow-`, `grid-bg`, `📍` — zero hits.
- [ ] Zoom 200%: layout intact, no clipped text.

---

## 10. Addendum — 2026-08-20 revision

Everything above is the original "Instrument Grade" spec and stays the
reference for layout, type scale, section order, and content. The items below
are a deliberate, owner-requested departure from three of its rules — recorded
here so a future edit doesn't "fix" them back. Nothing else in §§1–9 changed.

**Scheme tokens.** Dark `bg0` moved off near-black to a warm charcoal; light
`bg0` moved off near-white to a soft warm greige. Both bg/line/fg tiers are
warm-shifted to match. All text/background pairs re-verified ≥ 4.5:1 (same bar
as §3.1). Current values live in `app/globals.css` `:root` and its
`prefers-color-scheme: light` block — read those directly rather than this
doc, since tokens are the kind of thing that drifts.

**Radius.** No longer flat 0. Two tokens now exist: `--radius-sm` (6px:
buttons, inputs, the nav CV pill, the skip link) and `--radius-md` (8px: image
frames, gallery tiles, the CAD viewer frame, and the project/experience/
education entries, which are lightly carded again — `bg1` fill + 1px `line`
border + `radius-md`, no shadow). Full-bleed chrome (the nav bar, the mobile
menu panel, the footer, section divider rules) stays edge-to-edge and
unrounded — rounding a corner that sits off-screen reads as broken, not soft.
Status dots (`AVAILABLE`, `ONGOING`, `current`) are `rounded-full` rather than
square. §3.4's "radius: 0 on everything" and §1's "no cards" are superseded by
this.

**Fixed background.** `layout.js` renders `TurbineBackground` once, as a
`position: fixed` layer behind the entire page (`app/lib` holds the theme
sync it needs — see below) — not scoped to the hero. It keeps rotating as the
visitor scrolls, by design: an earlier hero-only version disappeared the
moment you scrolled past it, which read as decorative rather than as the
site's actual backdrop. `TurbineStage.js` (code-split, `ssr: false`, loads
eagerly rather than behind an IntersectionObserver — it's visible from the
first frame) builds a complete twin-spool turbofan core viewed from an
isometric-ish 3/4 angle, not a single fan face: a lathed spinner and tail
cone, two LP compressor stages, three HP compressor stages, one HP turbine
stage and two LP turbine stages, a casing shell, and LP/HP shaft segments.
The two spools are independent rotating groups at different speeds (`lpSpin`
at 0.11 rad/s, `hpSpin` at 0.24 rad/s) — the same mechanical arrangement a
real twin-spool engine has, and the visible speed mismatch between them is
the point, not an accident. Compressor and turbine stages use distinct blade
silhouettes (`compressorBladeShape` — long, thin, swept; `turbineBladeShape`
— short, wide-chorded) so a turbine stage never reads as "just another
compressor row." Each stage's ring of blades is one merged `BufferGeometry`
(`buildRingGeometry`, via three.js's `mergeGeometries`) rather than one mesh
per blade — with ~170 blades across eight stages, that's the difference
between ~8 draw calls and ~170 on a canvas that never stops rendering.

The blade rings alone read as floating clusters with nothing connecting
them — a first pass shipped this way and the owner correctly called it out
as looking incomplete. Compressor stages are drum-built: `lpDrumFrontGeo` /
`lpDrumRearGeo` / `hpDrumGeo` are each one continuous lathed rotor stepping
through several stages' hub radii, matching real axial-compressor
construction (several blade rows sharing one drum) as distinct from turbine
construction, where each stage gets its own flat disc (`discGeo`, scaled per
stage) — a real mechanical difference, not just decoration. A static,
non-rotating `combustorGeo` (a barrel-shaped lathed can, bulging past the
shaft radius) fills what was previously empty space between the last HPC
stage and the HPT — combustors don't rotate in a real engine, so it sits
outside both spool groups. Shaft and casing opacity were also raised
(0.35–0.4 → 0.55–0.7) — they existed in the first draft but were too faint
to register, which was part of why the engine read as "just blades."

**Longitudinal-section convention, not an isometric flower.** The
drum/disc/combustor revision above still didn't read as an actual engine
blueprint — the owner was right to push back on it. Real turbine cutaways
(confirmed via a web search of manufacturer cutaway illustrations and
turbomachinery patent language — rotor/stator rows alternate along an axial
centerline, bounded by a hub flowpath line on the inside and a casing
flowpath line on the outside) are drawn close to a longitudinal elevation:
the shaft runs across the page, the hub/casing envelope is one continuous
smooth curve, and blade rows read as a repeating comb pattern along that
envelope rather than as full round rings splayed toward the viewer. The
previous camera angle (`rotation={[0.28, 1.15, 0.12]}`, perspective camera)
was still open enough to show each stage as a near-complete ellipse — a
"flower," not a section. Fixed by: switching `Canvas` to `orthographic`
(zero vanishing-point distortion, which matters for a *technical drawing*
feel — a perspective camera reads as a product render no matter the angle);
flattening the outer group's rotation to `[0.14, 1.4, 0.03]`, much closer to
a true side elevation; replacing the plain-cylinder `casingGeo` with one
continuous lathed `CASING_PROFILE` tracing just outside every stage's blade
tip with an intake bell and exhaust flare, instead of a straight tube; and
adding static `STATORS` rows between the compressor rotor stages so the
alternating rotor-stator pattern — the single most recognisable feature of a
real compressor section — is actually present. `zoom` on the orthographic
camera replaces `fov` as the framing control.

Rendering is line art, not a shaded render: every part is built as an actual
solid, then reduced to its silhouette + crease edges via `EdgesGeometry` and
drawn unlit (`LineBasicMaterial`) — the same move a manufacturer's turbine
cutaway diagram makes (solid geometry, technical linework over it), and the
reference the site's owner pointed at for this revision. A solid metal-shaded
first pass read as a dark, generic blob; a single-fan first draft of this
line-art idea read as a toy pinwheel. Line art of a *complete engine* does
both jobs at once — reads as an actual engineering drawing and fits "rules,
not containers" (§1) far better than shaded PBR metal ever would — so
there's no environment map or lighting rig here; unlit materials don't need
one. HP-spool elements are drawn a shade warmer than LP-spool elements
(`PALETTE.lp` / `PALETTE.hp` / `PALETTE.faint`) — a real technical diagram's
way of telling two mechanically independent shafts apart at a glance, and it
doubles as a second, more restrained accent alongside the single orange inlet
ring. Palette-swapped per color scheme so text printed over it never loses
contrast; rotation stops under `prefers-reduced-motion`. A radial mask
(anchored right-of-centre) keeps it out of the viewport's hard edges. Every
carded section (project/experience/education entries, form fields, the CAD
viewer frame) sits on an opaque `bg1` fill, so it naturally occludes the
canvas wherever legibility actually matters; the handful of sections that
don't card their text (hero, Toolchain, Contact's own heading, the footer)
stay legible on thin unlit lines alone — confirmed by direct pixel crops of
the headline, not just eyeballing a screenshot. This is a deliberate
exception to §3.5's "nothing loops" rule and to the forbidden list's
"gradient animation" entry — those still hold everywhere else on the page.

**Manual theme toggle.** §1 originally called a toggle "UI about the UI" and
deleted the idea; there is one now, at the request of the site's owner.
`ThemeToggle.js` sits in the nav next to the CV button (a sun/moon icon,
16px, showing the mode a click switches *to*) and writes a `data-theme`
attribute to `<html>`, persisted to `localStorage` via the shared
`app/lib/theme.js` module. `prefers-color-scheme` is still the default for a
first-time visitor — the toggle is an override on top of it, not a
replacement: every scheme-aware rule in `globals.css` (tokens, the figure
light/dark swap) and `TurbineStage`'s canvas palette now checks
`:root[data-theme]` alongside the media query, so a manual override can never
leave part of the page disagreeing with the rest. A blocking inline script in
`layout.js` applies a stored preference before first paint, so a returning
visitor never sees a flash of the system-default scheme.
