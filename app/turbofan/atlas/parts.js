import { CORE_PARTS } from "./parts-core";
import { SYSTEM_PARTS } from "./parts-systems";
import { SYSTEMS, SYSTEM_BY_ID } from "./systems";

/**
 * The full parts list, in one order, with an id → part map and a search
 * index. Everything the scene and the panels need to know about a part is
 * on the part object itself; nothing here is loaded from a server.
 */
export const PARTS = [...CORE_PARTS, ...SYSTEM_PARTS];
export const PART_BY_ID = Object.fromEntries(PARTS.map((p) => [p.id, p]));

export const PARTS_BY_SYSTEM = Object.fromEntries(
  SYSTEMS.map((s) => [s.id, PARTS.filter((p) => p.system === s.id)])
);

/** Provenance summary for a part: what fraction of its facts are E³-cited. */
export function provenanceOf(part) {
  const tags = part.facts.map((x) => x.tag);
  if (tags.every((t) => t === "e3")) return "e3";
  if (tags.some((t) => t === "e3")) return "mixed";
  return "schematic";
}

/**
 * Search: a part matches if the query's words all appear in its name, its
 * system's name, or a fact's key or value. Names that start with the query
 * rank first. Kept plain on purpose; there are ~150 parts, not 3,432.
 */
export function searchParts(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const words = q.split(/\s+/);
  const hits = [];
  for (const part of PARTS) {
    const sys = SYSTEM_BY_ID[part.system];
    const hay = [part.name, sys.name, sys.short, ...part.facts.map((x) => `${x.k} ${x.v}`)].join(" ").toLowerCase();
    if (words.every((w) => hay.includes(w))) {
      const name = part.name.toLowerCase();
      const score = name.startsWith(q) ? 0 : name.includes(q) ? 1 : 2;
      hits.push({ part, score });
    }
  }
  hits.sort((a, b) => a.score - b.score || a.part.name.localeCompare(b.part.name));
  return hits.slice(0, 20).map((h) => h.part);
}
