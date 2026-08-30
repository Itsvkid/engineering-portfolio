"use client";

import { useCallback, useEffect, useRef } from "react";
import FigureImage from "./FigureImage";

/**
 * Full-bleed figure viewer. Deliberately plain: a dimmed page, the figure at
 * its natural aspect, its caption, and a counter. No zoom, no pan, no captions
 * that animate — the figure is the content.
 *
 * Focus is trapped while open and returned to the thumbnail on close, so
 * keyboard and screen-reader users are never dropped back at the top of the page.
 */
export default function Lightbox({ figures, index, onClose, onStep }) {
  const dialogRef = useRef(null);
  const closeRef = useRef(null);
  const restoreRef = useRef(null);

  const figure = figures[index];

  const step = useCallback(
    (delta) => {
      onStep((index + delta + figures.length) % figures.length);
    },
    [figures.length, index, onStep]
  );

  // Remember what had focus, move focus into the dialog, restore on unmount.
  useEffect(() => {
    restoreRef.current = document.activeElement;
    closeRef.current?.focus();
    const { body } = document;
    const previousOverflow = body.style.overflow;
    body.style.overflow = "hidden";

    return () => {
      body.style.overflow = previousOverflow;
      if (restoreRef.current instanceof HTMLElement) restoreRef.current.focus();
    };
  }, []);

  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key === "ArrowRight" && figures.length > 1) {
        step(1);
        return;
      }
      if (e.key === "ArrowLeft" && figures.length > 1) {
        step(-1);
        return;
      }
      if (e.key !== "Tab") return;

      // Focus trap: cycle within the dialog's tabbable controls.
      const focusables = dialogRef.current?.querySelectorAll(
        "button, [href], [tabindex]:not([tabindex='-1'])"
      );
      if (!focusables?.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [figures.length, onClose, step]);

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-label={figure.alt}
      className="fixed inset-0 z-60 flex flex-col bg-bg0/97 backdrop-blur-sm"
    >
      <div className="flex shrink-0 items-center justify-between border-b border-line px-6 py-4 md:px-10">
        <p className="t-label text-fg2">
          {figures.length > 1
            ? `Figure ${index + 1} / ${figures.length}`
            : "Figure"}
        </p>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          className="t-label cursor-pointer px-2 py-3 text-fg1 transition-colors duration-[var(--dur-fast)] hover:text-accent"
        >
          Close (Esc)
        </button>
      </div>

      {/* Clicking the backdrop closes; the figure itself does not. */}
      <div
        className="flex min-h-0 flex-1 items-center justify-center p-6 md:p-10"
        onClick={onClose}
      >
        <div
          className="relative h-full w-full max-w-5xl overflow-hidden rounded-md"
          onClick={(e) => e.stopPropagation()}
        >
          <FigureImage
            figure={figure}
            sizes="(min-width: 64rem) 64rem, 100vw"
            className="object-contain"
            priority
          />
        </div>
      </div>

      <div className="shrink-0 border-t border-line px-6 py-4 md:px-10">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 sm:flex-row sm:items-baseline sm:justify-between">
          <p className="t-body-sm max-w-2xl text-fg1">{figure.caption}</p>

          {figures.length > 1 ? (
            <div className="flex shrink-0 items-center gap-6">
              <button
                type="button"
                onClick={() => step(-1)}
                className="t-label cursor-pointer py-3 text-fg1 transition-colors duration-[var(--dur-fast)] hover:text-accent"
              >
                ← Prev
              </button>
              <button
                type="button"
                onClick={() => step(1)}
                className="t-label cursor-pointer py-3 text-fg1 transition-colors duration-[var(--dur-fast)] hover:text-accent"
              >
                Next →
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
