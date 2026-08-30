"use client";

import { useState } from "react";
import ModelViewer from "./ModelViewer";

/**
 * One frame, N models, rendered in-page from a self-hosted .glb.
 *
 * This began as an embed of viewer.autodesk.com, which cannot work: that host
 * sends `X-Frame-Options: DENY` and `frame-ancestors 'self' *.autodesk.com`,
 * so a browser refuses to frame it anywhere but Autodesk's own domain. No
 * amount of iframe configuration gets around a policy set by the other origin.
 *
 * Serving our own tessellated mesh is the better answer regardless: no third
 * party, no cookies, no dependency on someone else's share link staying alive,
 * and the geometry is code-split behind an IntersectionObserver so a visitor
 * who never scrolls to it never downloads three.js.
 *
 * `href` still points at Autodesk where one exists — their viewer reads the
 * native STEP and shows the exact B-rep rather than a mesh approximation of it,
 * which is worth offering as a link even though it cannot be embedded.
 */
export default function CadViewer({ models, label = "CAD viewer" }) {
  const [active, setActive] = useState(0);

  if (!models?.length) return null;

  const model = models[active];
  const multiple = models.length > 1;

  return (
    <div className="mt-10">
      <p className="t-label text-fg2">{label}</p>

      {multiple ? (
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
          {models.map((entry, i) => (
            <button
              key={entry.src ?? entry.title}
              type="button"
              onClick={() => setActive(i)}
              aria-pressed={i === active}
              className={`t-meta cursor-pointer py-1 transition-colors duration-[var(--dur-fast)] hover:text-accent ${
                i === active ? "text-accent" : "text-fg2"
              }`}
            >
              {entry.title}
            </button>
          ))}
        </div>
      ) : null}

      <ModelViewer
        key={model.src}
        src={model.src}
        title={model.title}
        description={model.description}
        autoRotate={false}
      />

      <p className="t-body-sm mt-2 text-fg2">
        {model.format ? `${model.format}. ` : null}
        {model.href ? (
          <a
            href={model.href}
            target="_blank"
            rel="noopener noreferrer"
            className="link text-fg1"
          >
            Open the native CAD in Autodesk Viewer
          </a>
        ) : null}
      </p>
    </div>
  );
}
