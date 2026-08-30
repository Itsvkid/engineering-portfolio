"use client";

import { useState } from "react";
import FigureImage from "./FigureImage";
import Lightbox from "./Lightbox";

/**
 * Evidence strip under a project: CFD contours, meshes, validation pairs.
 * Thumbnails sit on a plain 16:10 frame separated by the page background —
 * no cards, per DESIGN_SPEC §1.3. The accent appears only on hover/focus.
 */
export default function FigureGallery({ figures, label = "Figures" }) {
  const [openAt, setOpenAt] = useState(null);

  if (!figures?.length) return null;

  return (
    <div className="mt-8">
      <p className="t-label text-fg2">{label}</p>

      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3">
        {figures.map((figure, i) => (
          <li key={figure.src}>
            <button
              type="button"
              onClick={() => setOpenAt(i)}
              aria-haspopup="dialog"
              className="group block w-full cursor-pointer text-left"
            >
              <span className="relative block aspect-16/10 overflow-hidden rounded-md border border-line transition-colors duration-[var(--dur-fast)] group-hover:border-accent group-focus-visible:border-accent">
                <FigureImage
                  figure={figure}
                  sizes="(min-width: 40rem) 20rem, 45vw"
                  className="object-cover"
                />
              </span>
              <span className="t-meta mt-2 block text-fg2 transition-colors duration-[var(--dur-fast)] group-hover:text-fg1">
                {figure.short ?? figure.caption}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {openAt !== null ? (
        <Lightbox
          figures={figures}
          index={openAt}
          onClose={() => setOpenAt(null)}
          onStep={setOpenAt}
        />
      ) : null}
    </div>
  );
}
