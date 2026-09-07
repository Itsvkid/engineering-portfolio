"use client";

import { useEffect, useRef, useState } from "react";
import { ASSUMED_OFFSETS } from "./flowpath";
import { PARTS_BY_SYSTEM, PART_BY_ID, provenanceOf, searchParts } from "./parts";
import { PRESETS, SYSTEMS, SYSTEM_BY_ID, TAGS } from "./systems";
import { TOURS, TOUR_BY_ID } from "./tours";

/** The studio's panels: chips, systems, inspector, controls, tour, search, about. */

function Tag({ tag }) {
  const t = TAGS[tag] ?? TAGS.schematic;
  return (
    <span className={`atlas-tag tag-${tag}`} title={t.title}>
      {t.label}
    </span>
  );
}

// ── System chips (always visible in the dock bar) ─────────────────────────

export function SystemChips({ state, dispatch, palette }) {
  return (
    <div className="atlas-chips" role="group" aria-label="System layers">
      {SYSTEMS.map((s) => {
        const on = state.visibleSystems.includes(s.id);
        return (
          <button
            key={s.id}
            type="button"
            className="atlas-chip"
            aria-pressed={on}
            style={{ "--swatch": palette[s.id] }}
            title={`${s.name}: click to show or hide, double-click to show only this`}
            onClick={() => dispatch({ type: "toggleSystem", id: s.id })}
            onDoubleClick={() => dispatch({ type: "soloSystem", id: s.id })}
          >
            <span className="atlas-swatch" />
            <span className="atlas-chip-name">{s.name}</span>
          </button>
        );
      })}
    </div>
  );
}

// ── Systems drawer ────────────────────────────────────────────────────────

export function SystemsPanel({ state, dispatch, palette }) {
  return (
    <div className="atlas-drawer-grid">
      <div className="atlas-col">
        <div className="atlas-kicker mb-2">Presets</div>
        <div className="flex flex-wrap gap-1">
          {PRESETS.map((p) => (
            <button key={p.id} type="button" className="atlas-btn" onClick={() => dispatch({ type: "preset", systems: p.systems })}>
              {p.name}
            </button>
          ))}
        </div>
        <p className="mt-3 text-[0.8125rem] text-fg2">
          Click a system to read about it and list its parts. The checkbox shows or hides its layer; the chips in the bar below do the same.
        </p>
      </div>
      <div className="atlas-col atlas-systems-list">
        {SYSTEMS.map((s) => {
          const on = state.visibleSystems.includes(s.id);
          const current = state.selectedSystem === s.id;
          return (
            <div key={s.id} className="flex items-center">
              <button type="button" className="atlas-row" aria-pressed={on} aria-current={current ? "true" : undefined} onClick={() => dispatch({ type: "focusSystem", id: s.id })}>
                <span className="atlas-num">{String(s.n).padStart(2, "0")}</span>
                <span className="atlas-swatch" style={{ "--swatch": palette[s.id] }} />
                <span className="flex-1 truncate">{s.name}</span>
                <span className="atlas-num w-auto text-right">{PARTS_BY_SYSTEM[s.id].length}</span>
              </button>
              <input type="checkbox" aria-label={`Show ${s.name}`} checked={on} onChange={() => dispatch({ type: "toggleSystem", id: s.id })} className="mr-2 accent-[var(--accent)]" />
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Inspector drawer ──────────────────────────────────────────────────────

const HEADLINE = [
  ["Engine", "NASA/GE E³ Flight Propulsion System, 1983"],
  ["Takeoff thrust", "173.5 kN"],
  ["Bypass ratio", "6.7 (max climb), 7.0 (takeoff)"],
  ["Overall pressure ratio", "38.4 (max climb)"],
  ["Fan diameter", "2.108 m, 32 blades"],
  ["Spools", "LP 3,539 rpm · HP 12,645 rpm at max climb"],
  ["Stages", "fan + 1 booster · 10 HPC · 2 HPT · 5 LPT"],
  ["Count", "1,536 blades · 1,750 vanes · 5 bearings · 2 frames · 2 sumps"],
  ["Basic engine mass", "3,473 kg (4,465 kg installed)"],
];

export function Inspector({ state, dispatch, part, palette }) {
  if (part) return <PartInspector part={part} state={state} dispatch={dispatch} palette={palette} />;
  if (state.selectedSystem) return <SystemInspector id={state.selectedSystem} state={state} dispatch={dispatch} palette={palette} />;
  return (
    <div className="atlas-drawer-grid">
      <div className="atlas-col">
        <span className="atlas-kicker">Turbofan anatomy</span>
        <h1 className="mt-1 text-base font-semibold text-fg0">A high-bypass turbofan, part by part</h1>
        <p className="mt-2 text-[0.8125rem] leading-relaxed">
          Click any part to read what it is and what it does. Every number carries its source: an E³ report page, or a note that the
          geometry is schematic. Or let a tour walk you through.
        </p>
        <div className="mt-3 flex flex-wrap gap-1">
          {TOURS.map((t) => (
            <button key={t.id} type="button" className="atlas-btn" onClick={() => dispatch({ type: "tourStart", id: t.id, playing: false })}>
              {t.name}
            </button>
          ))}
        </div>
      </div>
      <div className="atlas-col">
        <table className="atlas-facts">
          <tbody>
            {HEADLINE.map(([k, v]) => (
              <tr key={k}>
                <th>{k}</th>
                <td>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="atlas-src mt-2">CR-168219 Tables IV, XII, XXVI; LPT report Table VI; HPC report Table X.</p>
      </div>
    </div>
  );
}

function SystemInspector({ id, dispatch, palette }) {
  const sys = SYSTEM_BY_ID[id];
  const parts = PARTS_BY_SYSTEM[id];
  return (
    <div className="atlas-drawer-grid">
      <div className="atlas-col">
        <div className="flex items-center gap-2">
          <span className="atlas-swatch" style={{ "--swatch": palette[id] }} />
          <span className="atlas-kicker">
            System {String(sys.n).padStart(2, "0")} · {sys.short}
          </span>
        </div>
        <h2 className="mt-1 text-base font-semibold text-fg0">{sys.name}</h2>
        <p className="mt-2 text-[0.8125rem] leading-relaxed">{sys.blurb}</p>
        <div className="mt-3 flex flex-wrap gap-1">
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "preset", systems: [id] })}>
            Show only this
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "preset", systems: SYSTEMS.map((s) => s.id) })}>
            Show all
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "focusSystem", id: null })}>
            Close
          </button>
        </div>
      </div>
      <div className="atlas-col atlas-systems-list">
        <div className="atlas-kicker px-2 pb-1">{parts.length} parts</div>
        {parts.map((p) => (
          <button key={p.id} type="button" className="atlas-row" onClick={() => dispatch({ type: "select", id: p.id })}>
            <span className="flex-1 truncate">{p.name}</span>
            <Tag tag={provenanceOf(p)} />
          </button>
        ))}
      </div>
    </div>
  );
}

function PartInspector({ part, state, dispatch, palette }) {
  const sys = SYSTEM_BY_ID[part.system];
  const isolated = state.isolated === part.id;
  return (
    <div className="atlas-drawer-grid">
      <div className="atlas-col">
        <button type="button" className="flex items-center gap-2 text-left" onClick={() => dispatch({ type: "focusSystem", id: sys.id })}>
          <span className="atlas-swatch" style={{ "--swatch": palette[sys.id] }} />
          <span className="atlas-kicker hover:text-fg0">
            {String(sys.n).padStart(2, "0")} · {sys.name}
          </span>
        </button>
        <div className="mt-1 flex items-start justify-between gap-2">
          <h2 className="text-base font-semibold leading-snug text-fg0">{part.name}</h2>
          <Tag tag={provenanceOf(part)} />
        </div>
        {part.spool && <p className="atlas-kicker mt-1">Rotates with the {part.spool === "lp" ? "LP" : "HP"} spool</p>}
        <p className="mt-2 text-[0.8125rem] leading-relaxed text-fg1">{part.text}</p>
        <div className="mt-3 flex flex-wrap gap-1">
          <button type="button" className="atlas-btn" aria-pressed={isolated} onClick={() => dispatch({ type: "isolate", id: isolated ? null : part.id })}>
            {isolated ? "Show all" : "Isolate"}
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "frame", part })}>
            Frame
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "preset", systems: [sys.id] })}>
            Only this system
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "select", id: null })}>
            Close
          </button>
        </div>
      </div>
      <div className="atlas-col">
        <table className="atlas-facts">
          <tbody>
            {part.facts.map((x, i) => (
              <tr key={i}>
                <th>{x.k}</th>
                <td>
                  {x.v}
                  <span className="atlas-src">
                    <Tag tag={x.tag} /> {x.src}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Controls drawer ───────────────────────────────────────────────────────

function Slider({ label, value, min = 0, max = 1, step = 0.01, format, onChange }) {
  return (
    <label className="atlas-slider">
      <span className="atlas-kicker">{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} />
      <output>{format ? format(value) : `${Math.round(value * 100)} %`}</output>
    </label>
  );
}

export function Controls({ state, dispatch, reducedMotion }) {
  const set = (key) => (value) => dispatch({ type: "set", key, value });
  return (
    <div className="atlas-controls">
      <div className="flex flex-wrap items-center gap-1">
        <span className="atlas-kicker mr-1">View</span>
        {["iso", "front", "side", "top", "aft"].map((id) => (
          <button key={id} type="button" className="atlas-btn" aria-pressed={state.cameraPreset.id === id} onClick={() => dispatch({ type: "camera", id })}>
            {id}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-line" aria-hidden="true" />
        <button type="button" className="atlas-btn" aria-pressed={state.cutaway} onClick={() => dispatch({ type: "set", key: "cutaway", value: !state.cutaway })} title="C">
          Cutaway
        </button>
        <button
          type="button"
          className="atlas-btn"
          aria-pressed={state.motion}
          disabled={reducedMotion}
          title={reducedMotion ? "Off: your system prefers reduced motion" : "M"}
          onClick={() => dispatch({ type: "set", key: "motion", value: !state.motion })}
        >
          Rotate
        </button>
        <button type="button" className="atlas-btn" aria-pressed={state.labels} onClick={() => dispatch({ type: "set", key: "labels", value: !state.labels })}>
          Label
        </button>
        <span className="mx-1 h-4 w-px bg-line" aria-hidden="true" />
        <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "reset", reducedMotion })}>
          Reset
        </button>
      </div>
      <div className="atlas-sliders">
        <Slider label="Throttle" value={state.throttle} onChange={set("throttle")} format={(v) => `${Math.round(3539 * v).toLocaleString()} N1`} />
        <Slider label="Separate" value={state.separation} onChange={set("separation")} />
        <Slider label="Casings" value={state.shellOpacity} min={0.1} onChange={set("shellOpacity")} />
        <Slider label="VSV" value={state.vsv} onChange={set("vsv")} format={(v) => (v < 0.02 ? "closed" : v > 0.98 ? "open" : `${Math.round(v * 100)} %`)} />
        <Slider label="VBV doors" value={state.vbv} onChange={set("vbv")} format={(v) => (v < 0.02 ? "shut" : v > 0.98 ? "open" : `${Math.round(v * 100)} %`)} />
      </div>
    </div>
  );
}

// ── Tour drawer ───────────────────────────────────────────────────────────

export function TourPanel({ state, dispatch, part }) {
  if (!state.tour) {
    return (
      <div className="atlas-drawer-grid">
        <div className="atlas-col">
          <span className="atlas-kicker">Guided tours</span>
          <h2 className="mt-1 text-base font-semibold text-fg0">Let the engine explain itself</h2>
          <p className="mt-2 text-[0.8125rem] leading-relaxed">
            Each tour steps through the parts in order, flying the camera to each. Press play to let it run, or use the arrow keys.
          </p>
        </div>
        <div className="atlas-col">
          {TOURS.map((t) => (
            <button key={t.id} type="button" className="atlas-row items-start" onClick={() => dispatch({ type: "tourStart", id: t.id, playing: true })}>
              <span className="flex-1">
                <span className="block text-fg0">{t.name}</span>
                <span className="block text-[0.8125rem] text-fg2">
                  {t.blurb} · {t.steps.length} stops
                </span>
              </span>
            </button>
          ))}
        </div>
      </div>
    );
  }
  const tour = TOUR_BY_ID[state.tour.id];
  const step = tour.steps[state.tour.step];
  const stepPart = PART_BY_ID[step.part];
  const last = state.tour.step === tour.steps.length - 1;
  return (
    <div className="atlas-drawer-grid">
      <div className="atlas-col">
        <span className="atlas-kicker">
          {tour.name} · {state.tour.step + 1} / {tour.steps.length}
        </span>
        <h2 className="mt-1 text-base font-semibold text-fg0">{stepPart.name}</h2>
        <p className="mt-2 text-[0.9375rem] leading-relaxed text-fg1">{step.text}</p>
      </div>
      <div className="atlas-col atlas-tour-controls">
        <div className="flex flex-wrap gap-1">
          <button type="button" className="atlas-btn" disabled={state.tour.step === 0} onClick={() => dispatch({ type: "tourStep", delta: -1 })}>
            ← Back
          </button>
          <button type="button" className="atlas-btn" aria-pressed={state.tour.playing} onClick={() => dispatch({ type: "tourPlay", playing: !state.tour.playing })}>
            {state.tour.playing ? "Pause" : "Play"}
          </button>
          <button type="button" className="atlas-btn" disabled={last} onClick={() => dispatch({ type: "tourStep", delta: 1 })}>
            Next →
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "drawer", id: "part" })} disabled={!part}>
            Read the part
          </button>
          <button type="button" className="atlas-btn" onClick={() => dispatch({ type: "tourStop" })}>
            End tour
          </button>
        </div>
        <div className="atlas-tour-track" aria-hidden="true">
          {tour.steps.map((s, i) => (
            <button key={i} type="button" className="atlas-tour-dot" aria-current={i === state.tour.step ? "true" : undefined} title={PART_BY_ID[s.part].name} onClick={() => dispatch({ type: "tourStep", index: i })} />
          ))}
        </div>
        <p className="text-[0.75rem] text-fg2">
          {state.tour.playing ? "Advancing every nine seconds." : "Paused."} Arrow keys step, space plays, Esc ends.
        </p>
      </div>
    </div>
  );
}

// ── Search ────────────────────────────────────────────────────────────────

export function SearchBox({ dispatch, inputRef }) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const results = q ? searchParts(q) : [];
  const box = useRef(null);
  useEffect(() => {
    function onDown(e) {
      if (box.current && !box.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("pointerdown", onDown);
    return () => document.removeEventListener("pointerdown", onDown);
  }, []);
  return (
    <div ref={box} className="relative w-full max-w-md">
      <input
        ref={inputRef}
        type="search"
        className="atlas-search"
        placeholder="Search parts, systems, numbers…  /"
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && results[0]) {
            dispatch({ type: "select", id: results[0].id });
            setOpen(false);
            e.currentTarget.blur();
          }
          if (e.key === "Escape") {
            setOpen(false);
            e.currentTarget.blur();
          }
        }}
        aria-label="Search parts"
      />
      {open && q && (
        <div className="atlas-panel top-full left-0 right-0 mt-1 max-h-80 z-30">
          <div className="atlas-scroll p-1">
            {results.length === 0 && <p className="px-3 py-2 text-fg2">No part matches “{q}”.</p>}
            {results.map((p) => (
              <button
                key={p.id}
                type="button"
                className="atlas-row"
                onClick={() => {
                  dispatch({ type: "select", id: p.id });
                  setOpen(false);
                }}
              >
                <span className="atlas-num">{String(SYSTEM_BY_ID[p.system].n).padStart(2, "0")}</span>
                <span className="flex-1 truncate">{p.name}</span>
                <span className="atlas-kicker truncate">{SYSTEM_BY_ID[p.system].short}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── About ─────────────────────────────────────────────────────────────────

export function AboutDialog({ onClose }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="atlas-dialog" onClick={onClose} role="presentation">
      <div className="atlas-dialog-card" role="dialog" aria-modal="true" aria-labelledby="atlas-about-title" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4">
          <h2 id="atlas-about-title">About this atlas</h2>
          <button type="button" className="atlas-btn" onClick={onClose}>
            Close
          </button>
        </div>
        <p>
          An interactive anatomy of a high-bypass turbofan, built the way the human-anatomy explorers{" "}
          <a href="https://github.com/ashemag/human-atlas" target="_blank" rel="noopener noreferrer">
            Human Atlas
          </a>{" "}
          and{" "}
          <a href="https://github.com/choxos/OMFAtlas" target="_blank" rel="noopener noreferrer">
            OMF Atlas
          </a>{" "}
          are built: the model first, every part selectable, layers you can switch off, a separation control that lays the assembly
          out as a parts inventory, and an honest line between what is measured and what is drawn.
        </p>
        <h3>Where the geometry comes from</h3>
        <p>
          There is no public segmented dataset of a turbofan the way BodyParts3D exists for a human. So every mesh here is procedural,
          fitted to the dimensions the NASA/GE Energy Efficient Engine (E³) programme published in 1978–83: 42 hub and tip stations
          of the HPC, five dimensioned HPT stations, the LPT walls from thirty transcribed airfoil sections, and the blade and vane
          count of every row. What the reports do not dimension is drawn as teaching geometry and tagged{" "}
          <span className="atlas-tag">schematic</span>; numbers that this model had to choose are tagged{" "}
          <span className="atlas-tag tag-assumed">assumed</span>.
        </p>
        <h3>What this model does not show</h3>
        <ul>
          <li>It is the E³, not a modern production engine. Modern internals are proprietary; this stays inside the public-domain reports and says so.</li>
          <li>
            Two axial gaps are not published and are set here: {ASSUMED_OFFSETS.map((o) => `${o.name} = ${o.value_m} m`).join("; ")}. No overall
            engine length is printed.
          </li>
          <li>
            Blade rows: the ten HPC rotors and eleven stators are lofted from all twelve printed sections per row of Table XXII
            (chord, camber, stagger and thickness at each radius); the ten LPT rows from the printed surface coordinates of the LPT
            report at three spans, hub and tip extrapolated. The HPT airfoils are inferred from throat and aspect ratio, and the fan is designed,
            not transcribed: the E³ never published its fan sections.
          </li>
          <li>Disc profiles are generic web-and-bore shapes at the published rim and bore radii.</li>
          <li>
            Anti-icing, fire detection and extinguishing, and the airborne vibration monitor are schematic: the E³ was a ground-test
            demonstrator. The reports describe the fire safety wall, under-cowl fire thermocouples and the No. 3 bearing accelerometer,
            and nothing more.
          </li>
          <li>The final FPS hot-section materials differ from the hardware reports (René N4 and thermal barrier coatings replaced René 150); both are printed where they differ.</li>
          <li>The model turns; it does not run. Rotation is kinematic at LP : HP ≈ 1 : 3.6. Nothing on the page is a simulation.</li>
          <li>Cooling passages, film holes, seal teeth and bolt patterns are simplified to what reads at screen scale.</li>
        </ul>
        <h3>Sources</h3>
        <p>
          NASA CR-168219 (FPS final design), CR-165148 (fan), NTRS 19850002690 (HPC), CR-167955 (HPT), NTRS 19850002686 (LPT), CR-168301
          (combustor), CR-168017 (controls), CR-168211 (ICLS test). All US Government work, all on NTRS. The transcription, the
          cross-checks and the two-route closures behind the numbers are in the E³ rebuild project on this site.
        </p>
        <h3>Keys</h3>
        <p>
          <kbd>/</kbd> search · <kbd>Esc</kbd> deselect · <kbd>C</kbd> cutaway · <kbd>M</kbd> rotate · <kbd>I</kbd> isolate ·{" "}
          <kbd>1</kbd>–<kbd>5</kbd> camera · <kbd>←</kbd> <kbd>→</kbd> tour steps · <kbd>space</kbd> play · drag to orbit · wheel to zoom ·
          right-drag to pan
        </p>
      </div>
    </div>
  );
}
