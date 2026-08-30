"use client";

import { useSyncExternalStore } from "react";
import { applyTheme, getEffectiveTheme, subscribeToTheme } from "../lib/theme";

// The dark default the page already renders before any client JS runs
// (bare `:root` in globals.css) — matching it here means the first client
// render agrees with the server-rendered HTML, so there is no hydration
// flash to see, just the same one-frame correction TurbineStage already
// accepts for reduced-motion/scheme detection.
function getServerSnapshot() {
  return "dark";
}

function SunIcon() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="3.25" stroke="currentColor" strokeWidth="1.3" />
      <path
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        d="M8 .75v2M8 13.25v2M15.25 8h-2M2.75 8h-2M13.07 2.93 11.66 4.34M4.34 11.66l-1.41 1.41M13.07 13.07l-1.41-1.41M4.34 4.34 2.93 2.93"
      />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" fill="none" aria-hidden="true">
      <path
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
        d="M13.5 9.65A6 6 0 0 1 6.35 2.5a6 6 0 1 0 7.15 7.15Z"
      />
    </svg>
  );
}

/**
 * A manual override on top of the site's prefers-color-scheme default (see
 * DESIGN_SPEC.md §10) — persisted to localStorage and applied via a
 * `data-theme` attribute on <html>, which every scheme-aware rule in
 * globals.css and TurbineStage's palette checks alongside the media query.
 * The icon shown is the mode a click switches *to*, matching the aria-label.
 */
export default function ThemeToggle() {
  const theme = useSyncExternalStore(subscribeToTheme, getEffectiveTheme, getServerSnapshot);
  const isLight = theme === "light";

  return (
    <button
      type="button"
      onClick={() => applyTheme(isLight ? "dark" : "light")}
      aria-label={isLight ? "Switch to dark mode" : "Switch to light mode"}
      className="grid size-8 shrink-0 cursor-pointer place-items-center rounded-sm text-fg1 transition-colors duration-[var(--dur-fast)] hover:text-accent"
    >
      {isLight ? <MoonIcon /> : <SunIcon />}
    </button>
  );
}
