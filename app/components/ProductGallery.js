"use client";

import { useState } from "react";
import Chevron from "./Chevron";
import FigureImage from "./FigureImage";
import Lightbox from "./Lightbox";

/**
 * Designed parts and the drawings of them. Distinct from FigureGallery, which
 * carries a project's CFD evidence: these are the products themselves, and each
 * carries the tool it was built in — a reviewer scanning for CATIA or pyOCC
 * experience should find it without opening anything, which is why the tool
 * badge sits on the always-visible header rather than behind the toggle.
 *
 * Each entry's heading is a disclosure toggle; only the first opens by
 * default, since stacking every full-width drawing at once was the reader's
 * complaint this fixes. Bordered on the page background, never carded, per
 * DESIGN_SPEC §1.3 — rules do the separating here too.
 */
export default function ProductGallery({ products, label = "Selected parts" }) {
  const [openAt, setOpenAt] = useState(null); // lightbox index
  const [expanded, setExpanded] = useState(
    () => new Set(products?.length ? [0] : [])
  );

  if (!products?.length) return null;

  function toggle(i) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  return (
    <div>
      <p className="t-label text-fg2">{label}</p>

      <ul className="mt-4 flex flex-col">
        {products.map((product, i) => {
          const open = expanded.has(i);
          const contentId = `product-${i}-content`;

          return (
            <li
              key={product.src}
              className="border-b border-line py-4 first:pt-0 last:border-b-0"
            >
              <button
                type="button"
                onClick={() => toggle(i)}
                aria-expanded={open}
                aria-controls={contentId}
                className="group flex w-full cursor-pointer items-baseline justify-between gap-4 text-left"
              >
                <span className="t-h4 text-fg0 transition-colors duration-[var(--dur-fast)] group-hover:text-accent">
                  {product.short ?? product.alt}
                </span>
                <span className="flex items-center gap-3">
                  {product.tool ? (
                    <span className="t-meta uppercase text-fg2">
                      {product.tool}
                    </span>
                  ) : null}
                  <Chevron
                    open={open}
                    className="text-fg2 transition-colors duration-[var(--dur-fast)] group-hover:text-accent"
                  />
                </span>
              </button>

              <div
                id={contentId}
                className={`grid transition-[grid-template-rows] duration-[var(--dur-base)] ${
                  open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                }`}
              >
                <div className="overflow-hidden" inert={!open}>
                  <button
                    type="button"
                    onClick={() => setOpenAt(i)}
                    aria-haspopup="dialog"
                    className="group/img mt-3 block w-full cursor-pointer text-left"
                  >
                    <span
                      className="relative block w-full overflow-hidden rounded-md border border-line bg-bg1 transition-colors duration-[var(--dur-fast)] group-hover/img:border-accent group-focus-visible/img:border-accent"
                      style={{
                        aspectRatio:
                          product.width && product.height
                            ? `${product.width} / ${product.height}`
                            : "4 / 3",
                      }}
                    >
                      <FigureImage
                        figure={product}
                        sizes="(min-width: 64rem) 44rem, 92vw"
                        className="object-contain"
                      />
                    </span>
                  </button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {openAt !== null ? (
        <Lightbox
          figures={products}
          index={openAt}
          onClose={() => setOpenAt(null)}
          onStep={setOpenAt}
        />
      ) : null}
    </div>
  );
}
