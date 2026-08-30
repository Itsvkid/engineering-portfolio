"use client";

import { useEffect, useState } from "react";
import ReadProgress from "./ReadProgress";
import ThemeToggle from "./ThemeToggle";

/**
 * Tracks which section is currently under the nav. The observer's rootMargin
 * turns the viewport into a thin band just below the 4rem header, so exactly
 * one section is "current" at a time and the marker never flickers between two.
 */
function useActiveSection(items) {
  const [active, setActive] = useState(null);

  useEffect(() => {
    const sections = items
      .map((item) => document.getElementById(item.href.slice(1)))
      .filter(Boolean);
    if (!sections.length || typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        const hit = entries.find((entry) => entry.isIntersecting);
        if (hit) setActive(`#${hit.target.id}`);
      },
      // rootMargin takes absolute lengths and percentages only — `rem` is
      // rejected outright by WebKit, so this must stay in px. 64px is the
      // h-16 header.
      { rootMargin: "-64px 0px -70% 0px", threshold: 0 }
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [items]);

  return active;
}

export default function Nav({ items, cvHref, wordmark }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const active = useActiveSection(items);

  useEffect(() => {
    if (!menuOpen) return;
    function onKeyDown(e) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="border-b border-line bg-bg0/94 backdrop-blur-sm">
        <nav
          aria-label="Primary"
          className="mx-auto flex h-16 max-w-[70rem] items-center justify-between px-6 md:px-10"
        >
          <a
            href="#top"
            className="t-label text-fg0 tracking-[0.08em] text-[0.75rem]"
          >
            {wordmark}
          </a>

          <div className="hidden items-center gap-8 md:flex">
            {items.map((item) => {
              const current = active === item.href;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  aria-current={current ? "true" : undefined}
                  className={`t-body-sm relative transition-colors duration-[var(--dur-fast)] hover:text-fg0 ${
                    current ? "text-fg0" : "text-fg1"
                  }`}
                >
                  {item.label}
                  {/* Underline grows from the centre as the section becomes
                      current — the one place the nav moves at all. */}
                  <span
                    aria-hidden="true"
                    className={`absolute -bottom-1.5 left-0 h-px w-full origin-center bg-accent transition-transform duration-[var(--dur-base)] ${
                      current ? "scale-x-100" : "scale-x-0"
                    }`}
                  />
                </a>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />

            <a
              href={cvHref}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-sm bg-accent px-4 py-2 font-mono text-[0.75rem] font-medium uppercase tracking-[0.06em] text-bg0 transition-colors duration-[var(--dur-fast)] hover:bg-accent-hover active:bg-accent-active"
            >
              <span className="hidden md:inline">CV — PDF</span>
              <span className="md:hidden">CV</span>
            </a>

            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-expanded={menuOpen}
              aria-controls="mobile-menu"
              className="t-label py-4 text-[0.75rem] text-fg1 transition-colors duration-[var(--dur-fast)] hover:text-fg0 md:hidden"
            >
              {menuOpen ? "Close" : "Menu"}
            </button>
          </div>
        </nav>

        <ReadProgress />
      </div>

      {/* always rendered so aria-controls never dangles */}
      <div
        id="mobile-menu"
        hidden={!menuOpen}
        className="border-b border-line bg-bg0 md:hidden"
      >
        {items.map((item) => (
          <a
            key={item.href}
            href={item.href}
            onClick={() => setMenuOpen(false)}
            aria-current={active === item.href ? "true" : undefined}
            className="flex h-14 items-center border-b border-line px-6 text-base text-fg0 last:border-b-0 aria-[current]:text-accent"
          >
            {item.label}
          </a>
        ))}
      </div>
    </header>
  );
}
