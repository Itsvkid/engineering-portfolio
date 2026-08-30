"use client";

import { useState } from "react";
import Chevron from "./Chevron";
import FigureGallery from "./FigureGallery";
import ModelViewer from "./ModelViewer";

/**
 * The title row doubles as a disclosure toggle: period, title, context and
 * stats stay visible for scanning, while the write-up, figures and model
 * viewer — the part that costs the most reading time — collapse behind it.
 * Collapse is a CSS grid-rows transition (no JS height measurement, no
 * layout thrash), and `inert` keeps collapsed content out of tab order and
 * assistive tech while it's hidden.
 */
export default function ProjectEntry({ project, index, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const ongoing = project.period.toLowerCase().includes("ongoing");
  const contentId = `${project.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")}-content`;

  return (
    <article>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <span className="t-label text-fg2">{index}</span>
        <span className="t-meta flex items-center gap-2 uppercase text-fg2">
          {project.period}
          {ongoing ? (
            <span
              aria-hidden="true"
              className="inline-block size-1.5 shrink-0 rounded-full bg-accent"
            />
          ) : null}
        </span>
      </div>

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={contentId}
        className="group mt-2 flex w-full cursor-pointer items-start justify-between gap-4 text-left"
      >
        <span>
          <h3 className="t-h3 text-fg0 transition-colors duration-[var(--dur-fast)] group-hover:text-accent">
            {project.title}
          </h3>
          <span className="t-meta mt-1 block text-fg2">{project.context}</span>
        </span>
        <Chevron
          open={open}
          className="mt-2 text-fg2 transition-colors duration-[var(--dur-fast)] group-hover:text-accent"
        />
      </button>

      {project.stats ? (
        <dl className="stagger mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-x-10 sm:gap-y-6">
          {/* column-reverse so each figure sits above its label without
              breaking the required dt-then-dd source order */}
          {project.stats.map((stat) => (
            <div key={stat.label} className="flex flex-col-reverse gap-1">
              <dt className="t-label text-fg2">{stat.label}</dt>
              <dd className="text-[1.0625rem] font-semibold text-fg0">
                {stat.value}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}

      <div
        id={contentId}
        className={`grid transition-[grid-template-rows] duration-[var(--dur-base)] ${
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="overflow-hidden" inert={!open}>
          <div className="mt-6 space-y-3">
            {project.points.map((point) => (
              <p key={point} className="t-body text-fg1">
                {point}
              </p>
            ))}
          </div>

          {project.model ? (
            <ModelViewer
              src={project.model.src}
              title={project.model.title}
              description={project.model.description}
              autoRotate={project.model.autoRotate}
            />
          ) : null}

          <FigureGallery figures={project.figures} />

          <p className="t-meta mt-6 uppercase text-fg2">
            {project.tech.join(" · ")}
          </p>

          {project.link ? (
            <a
              href={project.link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="cta t-label mt-4 inline-block text-accent transition-colors duration-[var(--dur-fast)] hover:text-accent-hover"
            >
              {project.link.label}{" "}
              <span aria-hidden="true" className="arrow">
                →
              </span>
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}
