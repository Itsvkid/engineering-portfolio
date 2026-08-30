const STORAGE_KEY = "theme";
const THEME_EVENT = "themechange";
const SCHEME_QUERY = "(prefers-color-scheme: light)";

/**
 * Shared by ThemeToggle (writes the preference) and TurbineStage (reads it
 * to keep the canvas palette in sync with the CSS-driven page theme). Kept
 * in one place so the storage key and event name can't drift between them.
 *
 * localStorage doesn't fire `storage` in the tab that wrote it, so a write
 * also dispatches THEME_EVENT — that's what lets same-tab listeners react
 * immediately instead of only picking up changes from other tabs.
 */

function readStoredTheme() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

export function getEffectiveTheme() {
  return readStoredTheme() ?? (window.matchMedia(SCHEME_QUERY).matches ? "light" : "dark");
}

export function subscribeToTheme(onChange) {
  const query = window.matchMedia(SCHEME_QUERY);
  query.addEventListener("change", onChange);
  window.addEventListener("storage", onChange);
  window.addEventListener(THEME_EVENT, onChange);
  return () => {
    query.removeEventListener("change", onChange);
    window.removeEventListener("storage", onChange);
    window.removeEventListener(THEME_EVENT, onChange);
  };
}

export function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Storage may be unavailable (private browsing) — the attribute still
    // applies for the rest of this session.
  }
  window.dispatchEvent(new Event(THEME_EVENT));
}
