"use client";

import "./atlas.css";
import Link from "next/link";
import { useEffect, useMemo, useReducer, useRef, useState, useSyncExternalStore } from "react";
import ThemeToggle from "../../components/ThemeToggle";
import { getEffectiveTheme, subscribeToTheme } from "../../lib/theme";
import Engine from "./Engine";
import { AboutDialog, Controls, Inspector, SearchBox, SystemChips, SystemsPanel, TourPanel } from "./panels";
import { PART_BY_ID } from "./parts";
import { SYSTEMS } from "./systems";
import { TOUR_BY_ID } from "./tours";

/**
 * The studio: the canvas fills the viewport; everything else sits in a
 * dock along the bottom. A strip of system chips is always visible for
 * quick toggling; one drawer above it opens on the Systems, Part, Controls
 * or Tour tab and closes again so the model is never covered for long.
 * The first layout put the systems list and the inspector in side panels,
 * which took a third of the width on a laptop; the engine is long and
 * thin, so the width is the one thing it cannot spare.
 */

const ALL = SYSTEMS.map((s) => s.id);
const MOTION_QUERY = "(prefers-reduced-motion: reduce)";
const DRAWERS = ["systems", "part", "controls", "tour"];

function subscribeToMotion(onChange) {
  const q = window.matchMedia(MOTION_QUERY);
  q.addEventListener("change", onChange);
  return () => q.removeEventListener("change", onChange);
}

/**
 * Deep links: ?part=fan-blades&camera=front&cut=0&sep=0.5&systems=fuel,oil&tour=air.
 * Read once at start; the address bar is kept in step with the selection so
 * a link to a part can be shared.
 */
function fromUrl() {
  if (typeof window === "undefined") return {};
  const q = new URLSearchParams(window.location.search);
  const out = {};
  const part = q.get("part");
  if (part && PART_BY_ID[part]) {
    out.selected = part;
    out.drawer = "part";
  }
  const camera = q.get("camera");
  if (camera && ["iso", "front", "side", "top", "aft"].includes(camera)) out.cameraPreset = { id: camera, n: 1 };
  if (q.get("cut") === "0") out.cutaway = false;
  const sep = Number(q.get("sep"));
  if (q.has("sep") && sep >= 0 && sep <= 1) out.separation = sep;
  const shell = Number(q.get("shell"));
  if (q.has("shell") && shell >= 0.1 && shell <= 1) out.shellOpacity = shell;
  const systems = q.get("systems");
  if (systems) {
    const ids = systems.split(",").filter((id) => ALL.includes(id));
    if (ids.length) out.visibleSystems = ids;
  }
  if (out.selected && out.visibleSystems && !out.visibleSystems.includes(PART_BY_ID[out.selected].system)) out.visibleSystems.push(PART_BY_ID[out.selected].system);
  const tour = q.get("tour");
  if (tour && TOUR_BY_ID[tour]) out.pendingTour = tour;
  // ?ui=0 hides the chrome: for posters, screenshots and embeds.
  if (q.get("ui") === "0") {
    out.chrome = false;
    out.drawer = null;
  }
  return out;
}

function initial(reducedMotion) {
  return {
    visibleSystems: ALL,
    selected: null,
    hovered: null,
    selectedSystem: null,
    isolated: null,
    separation: 0,
    cutaway: true,
    motion: !reducedMotion,
    throttle: 0.45,
    vsv: 1,
    vbv: 0,
    shellOpacity: 1,
    labels: true,
    cameraPreset: { id: "iso", n: 0 },
    frameRequest: null,
    drawer: null,
    tour: null, // { id, step, playing }
    chrome: true,
    ...fromUrl(),
  };
}

function applyTourStep(state, id, index, playing) {
  const tour = TOUR_BY_ID[id];
  const step = tour.steps[Math.max(0, Math.min(tour.steps.length - 1, index))];
  const part = PART_BY_ID[step.part];
  const visibleSystems = step.systems ?? (state.visibleSystems.includes(part.system) ? state.visibleSystems : [...state.visibleSystems, part.system]);
  return {
    ...state,
    tour: { id, step: index, playing },
    selected: step.part,
    selectedSystem: null,
    isolated: null,
    visibleSystems,
    cutaway: step.cut ?? true,
    separation: step.sep ?? 0,
    drawer: "tour",
    cameraPreset: step.camera ? { id: step.camera, n: state.cameraPreset.n + 1 } : state.cameraPreset,
    frameRequest: step.camera ? null : { part, n: (state.frameRequest?.n ?? 0) + 1 },
  };
}

function reducer(state, action) {
  switch (action.type) {
    case "select": {
      if (!action.id) return { ...state, selected: null, isolated: null, frameRequest: null, tour: null, drawer: state.drawer === "part" || state.drawer === "tour" ? null : state.drawer };
      const part = PART_BY_ID[action.id];
      const visibleSystems = state.visibleSystems.includes(part.system) ? state.visibleSystems : [...state.visibleSystems, part.system];
      return {
        ...state,
        selected: action.id,
        selectedSystem: null,
        visibleSystems,
        isolated: state.isolated && state.isolated !== action.id ? null : state.isolated,
        tour: null,
        drawer: "part",
      };
    }
    case "hover":
      return state.hovered === action.id ? state : { ...state, hovered: action.id };
    case "focusSystem":
      return { ...state, selectedSystem: action.id, selected: null, isolated: null, tour: null, drawer: action.id ? "part" : null };
    case "toggleSystem": {
      const on = state.visibleSystems.includes(action.id);
      const visibleSystems = on ? state.visibleSystems.filter((s) => s !== action.id) : [...state.visibleSystems, action.id];
      const selected = state.selected && on && PART_BY_ID[state.selected].system === action.id ? null : state.selected;
      return { ...state, visibleSystems, selected, isolated: selected ? state.isolated : null };
    }
    case "soloSystem":
      return { ...state, visibleSystems: state.visibleSystems.length === 1 && state.visibleSystems[0] === action.id ? ALL : [action.id], isolated: null };
    case "preset":
      return { ...state, visibleSystems: action.systems, isolated: null, selected: state.selected && action.systems.includes(PART_BY_ID[state.selected].system) ? state.selected : null };
    case "isolate":
      return { ...state, isolated: action.id };
    case "frame":
      return { ...state, frameRequest: { part: action.part, n: (state.frameRequest?.n ?? 0) + 1 } };
    case "camera":
      return { ...state, cameraPreset: { id: action.id, n: state.cameraPreset.n + 1 } };
    case "set":
      return { ...state, [action.key]: action.value };
    case "drawer":
      return { ...state, drawer: state.drawer === action.id ? null : action.id };
    case "tourStart":
      return applyTourStep(state, action.id, 0, action.playing ?? true);
    case "tourStep": {
      if (!state.tour) return state;
      const tour = TOUR_BY_ID[state.tour.id];
      const next = action.index ?? state.tour.step + action.delta;
      if (next < 0 || next >= tour.steps.length) return { ...state, tour: { ...state.tour, playing: false } };
      return applyTourStep(state, state.tour.id, next, action.playing ?? state.tour.playing);
    }
    case "tourPlay":
      return state.tour ? { ...state, tour: { ...state.tour, playing: action.playing } } : state;
    case "tourStop":
      return { ...state, tour: null, selected: null, isolated: null, frameRequest: null, drawer: "tour" };
    case "reset":
      return { ...initial(action.reducedMotion), cameraPreset: { id: "iso", n: state.cameraPreset.n + 1 }, drawer: state.drawer };
    default:
      return state;
  }
}

function usePalette(theme) {
  return useMemo(() => {
    const p = Object.fromEntries(SYSTEMS.map((s) => [s.id, s.color[theme]]));
    const dark = theme === "dark";
    // Rotating hardware: the LP spool a shade cooler than the HP spool, the
    // combustor a terracotta between them, static rows neutral. Same
    // reasoning as the site's line-art turbine: two shafts should be told
    // apart at a glance, and the hot section should read as hot.
    p.lp = dark ? "#a89f8f" : "#6f6653";
    p.hp = dark ? "#c39a63" : "#8d6a34";
    p.combustor = dark ? "#b56a45" : "#8f4a2a";
    p.stator = dark ? "#8c8577" : "#5d574b";
    p.background = dark ? "#1b1815" : "#f2eee6";
    p.skyLight = dark ? "#f1ece4" : "#ffffff";
    p.groundLight = dark ? "#2a251f" : "#b9b0a2";
    return p;
  }, [theme]);
}

export default function Atlas() {
  const theme = useSyncExternalStore(subscribeToTheme, getEffectiveTheme, () => "dark");
  const reducedMotion = useSyncExternalStore(subscribeToMotion, () => window.matchMedia(MOTION_QUERY).matches, () => false);
  const [state, dispatch] = useReducer(reducer, reducedMotion, initial);
  const [about, setAbout] = useState(false);
  const searchRef = useRef(null);
  const palette = usePalette(theme);
  const part = state.selected ? PART_BY_ID[state.selected] : null;

  // Reduced motion arriving after first render (or changing) switches rotation off.
  useEffect(() => {
    if (reducedMotion && state.motion) dispatch({ type: "set", key: "motion", value: false });
  }, [reducedMotion, state.motion]);

  // A ?tour= link starts the tour once the scene exists.
  useEffect(() => {
    if (state.pendingTour) {
      const id = state.pendingTour;
      dispatch({ type: "set", key: "pendingTour", value: null });
      dispatch({ type: "tourStart", id, playing: false });
    }
  }, [state.pendingTour]);

  // Keep the address bar in step with the selection, without adding history.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    if (state.selected) q.set("part", state.selected);
    else q.delete("part");
    q.delete("tour");
    const qs = q.toString();
    window.history.replaceState(null, "", `${window.location.pathname}${qs ? `?${qs}` : ""}`);
  }, [state.selected]);

  // Tour autoplay.
  useEffect(() => {
    if (!state.tour?.playing) return;
    const t = setTimeout(() => dispatch({ type: "tourStep", delta: 1 }), 9000);
    return () => clearTimeout(t);
  }, [state.tour]);

  useEffect(() => {
    function onKey(e) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      switch (e.key) {
        case "/":
          e.preventDefault();
          searchRef.current?.focus();
          break;
        case "Escape":
          if (about) setAbout(false);
          else if (state.tour) dispatch({ type: "tourStop" });
          else if (state.selected) dispatch({ type: "select", id: null });
          else if (state.selectedSystem) dispatch({ type: "focusSystem", id: null });
          else if (state.drawer) dispatch({ type: "drawer", id: state.drawer });
          break;
        case "c":
          dispatch({ type: "set", key: "cutaway", value: !state.cutaway });
          break;
        case "m":
          if (!reducedMotion) dispatch({ type: "set", key: "motion", value: !state.motion });
          break;
        case "i":
          if (state.selected) dispatch({ type: "isolate", id: state.isolated ? null : state.selected });
          break;
        case "ArrowRight":
          if (state.tour) dispatch({ type: "tourStep", delta: 1 });
          break;
        case "ArrowLeft":
          if (state.tour) dispatch({ type: "tourStep", delta: -1 });
          break;
        case " ":
          if (state.tour) {
            e.preventDefault();
            dispatch({ type: "tourPlay", playing: !state.tour.playing });
          }
          break;
        case "1":
        case "2":
        case "3":
        case "4":
        case "5":
          dispatch({ type: "camera", id: ["iso", "front", "side", "top", "aft"][Number(e.key) - 1] });
          break;
        default:
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [about, state, reducedMotion]);

  const drawerLabel = { systems: "Systems", part: part ? "Part" : state.selectedSystem ? "System" : "Info", controls: "Controls", tour: "Tour" };

  return (
    <div className="atlas">
      <div className="atlas-canvas" style={{ cursor: state.hovered ? "pointer" : "grab" }}>
        <Engine state={state} dispatch={dispatch} theme={theme} palette={palette} />
      </div>

      {state.chrome && (
        <>
      {/* Top bar */}
      <header className="atlas-panel atlas-top flex-row items-center gap-2 px-3 py-2 sm:gap-3">
        <Link href="/" className="atlas-kicker whitespace-nowrap hover:text-fg0">
          ← Vinaykumar V.
        </Link>
        <span className="hidden text-fg0 font-medium tracking-tight sm:inline whitespace-nowrap">Turbofan Atlas</span>
        <span className="atlas-tag tag-e3 hidden lg:inline">E³ FPS · to scale where published</span>
        <div className="flex flex-1 justify-center min-w-0">
          <SearchBox dispatch={dispatch} inputRef={searchRef} />
        </div>
        <button type="button" className="atlas-btn" onClick={() => setAbout(true)}>
          About
        </button>
        <ThemeToggle />
      </header>

      {/* Bottom dock: drawer above, bar below */}
      <div className="atlas-dock">
        {state.drawer && (
          <section className="atlas-panel atlas-drawer" aria-label={drawerLabel[state.drawer]}>
            {state.drawer === "systems" && <SystemsPanel state={state} dispatch={dispatch} palette={palette} />}
            {state.drawer === "part" && <Inspector state={state} dispatch={dispatch} part={part} palette={palette} />}
            {state.drawer === "controls" && <Controls state={state} dispatch={dispatch} reducedMotion={reducedMotion} />}
            {state.drawer === "tour" && <TourPanel state={state} dispatch={dispatch} part={part} />}
          </section>
        )}
        <div className="atlas-panel atlas-dockbar">
          <nav className="atlas-tabs" aria-label="Panels">
            {DRAWERS.map((id) => (
              <button key={id} type="button" className="atlas-btn" aria-pressed={state.drawer === id} onClick={() => dispatch({ type: "drawer", id })}>
                {drawerLabel[id]}
              </button>
            ))}
          </nav>
          <SystemChips state={state} dispatch={dispatch} palette={palette} />
          <div className="atlas-quick">
            <button type="button" className="atlas-btn" aria-pressed={state.cutaway} onClick={() => dispatch({ type: "set", key: "cutaway", value: !state.cutaway })} title="C">
              Cutaway
            </button>
            <button type="button" className="atlas-btn" aria-pressed={state.motion} disabled={reducedMotion} onClick={() => dispatch({ type: "set", key: "motion", value: !state.motion })} title="M">
              Rotate
            </button>
          </div>
        </div>
      </div>

      {about && <AboutDialog onClose={() => setAbout(false)} />}
        </>
      )}
    </div>
  );
}
