import { BOOSTER_SECTIONS, FAN_SECTIONS, HPC_SECTIONS, LPT_SECTIONS } from "./data/e3-sections";
import {
  bladeRow,
  bladeRowFromCoords,
  boltRing,
  hoop,
  lathe,
  merge,
  mixer,
  pipe,
  ring,
  shell,
  struts,
  tipShroud,
  unit,
} from "./geometry";
import {
  BOOSTER,
  COMBUSTOR,
  ISLAND,
  EXHAUST,
  FAN,
  FAN_STATIONS as FS,
  HPC0,
  HPC_ROTOR_BLADES,
  HPC_ROWS,
  HPC_STATOR_VANES,
  HPC_VARIABLE_ROWS,
  HPT0,
  HPT_BLADES,
  HPT_STATIONS as HT,
  HPT_VANES,
  LPT0,
  LPT_BLADES,
  LPT_ROWS,
  LPT_VANES,
  NACELLE,
  STATIONS,
} from "./flowpath";

/**
 * The gas generator, the rotors, the structure and the exhaust: everything
 * that is not an "external". Each part is a plain object; `build` returns
 * its geometry in the engine frame (axis +Y) and is called once, lazily,
 * by the scene. `y`, `r` and `clock` locate the part for the label and for
 * the separation layout; `spool` marks what rotates with what.
 *
 * Provenance discipline, borrowed from OMF Atlas: a number tagged `e3`
 * comes from a transcribed NASA report table with the page cited; one
 * tagged `schematic` is generic practice drawn for teaching; `assumed` is a
 * value this model had to pick and says so. Text is written to be read
 * aloud in an interview.
 */

const E3 = "e3";
const SCH = "schematic";
const ASM = "assumed";

const f = (k, v, src, tag = E3) => ({ k, v, src, tag });

// HPC report Table X p.65 — per-stage rotor geometry, metric as printed.
const HPC_TABLE_X = {
  chordRoot: [10.106, 6.548, 4.633, 3.919, 3.35, 2.867, 2.845, 2.713, 2.54, 2.286],
  chordTip: [10.276, 7.034, 5.034, 4.002, 3.427, 2.919, 2.845, 2.718, 2.54, 2.286],
  staggerRoot: [23.18, 28.29, 30.88, 32.92, 32.731, 36.836, 38.282, 42.74, 45.21, 47.65],
  staggerTip: [65.21, 60.93, 58.98, 57.5, 56.318, 55.91, 54.071, 55.53, 57.95, 57.48],
  camberRoot: [64.04, 50.34, 46.59, 39.84, 36.837, 33.381, 38.282, 34.04, 33.36, 32.02],
  camberTip: [9.66, 12.96, 20.36, 22.35, 10.996, 23.178, 25.844, 27.65, 27.55, 29.22],
};

const HPC_MATERIAL = (k) =>
  k < 6 ? "Ti-8Al-1Mo-1V (Table X, stages 1–6); the root-stress reproduction says Ti only to stage 4" : "Inco 718 (Table X, stages 7–10); stress reproduces as nickel from stage 5";

/**
 * Table XXII sections for one HPC row as loft stations: x from the first
 * (hub) section's radius, chord, camber, stagger and thickness as printed.
 */
function printedSections(name) {
  const secs = HPC_SECTIONS[name];
  const r0 = secs[0][0];
  // Twelve printed stations a row, lofted as printed. The widest twist step
  // among the twenty-one rows is 8° (stator 3), so a ruled loft does facet
  // slightly here — but interpolating to even fourteen stations costs
  // 890,000 triangles across 2,890 blades that sit behind casings and read a
  // few pixels wide. The fan, which is the row anyone actually looks at,
  // needs no interpolation at all now that it lofts Appendix B's 23.
  return {
    rHub: r0,
    stations: secs.map(([r, chord, camber, stagger, tm]) => ({
      x: r - r0, chord, camber, stagger, thickness: tm,
    })),
  };
}

/**
 * The fan and booster rotors, from the plane-section appendices.
 *
 * These rows used to be lofted from seven and five points read off Figs 41
 * and 52. CR-165148 Appendices B and D print the same blades at 23 and 14
 * stations, and the read-offs carried a mean stagger error of +3.14° on the
 * fan (+5.82° at the hub) and −1.61° on the booster. Opposite signs, so
 * there was never a correction to apply — only the tables.
 *
 * The end stations stay. Appendix B's first and last are the flowpath hub
 * and tip, not overhang, and radius comes from the printed radius column
 * rather than the percent-height label, which is nominal at both ends.
 */
function appendixSections(secs) {
  const r0 = secs[0][0];
  return {
    rHub: r0,
    rTip: secs[secs.length - 1][0],
    stations: secs.map(([r, chord, camber, stagger, tm]) => ({
      x: r - r0, chord, camber, stagger, thickness: tm,
    })),
  };
}

function rowMid(row) {
  return {
    y: (row.LE.yHub + row.TE.yHub + row.LE.yTip + row.TE.yTip) / 4,
    rHub: (row.LE.rHub + row.TE.rHub) / 2,
    rTip: (row.LE.rTip + row.TE.rTip) / 2,
  };
}

// ── Fan module ────────────────────────────────────────────────────────────

const fanModule = [
  {
    id: "spinner",
    tint: "lp",
    name: "Spinner",
    system: "gas-generator",
    spool: "lp",
    y: -0.35,
    r: 0.2,
    build: () =>
      lathe([
        [0, FS.spinnerNose],
        [0.1, FS.spinnerNose + 0.12],
        [0.22, FS.spinnerNose + 0.27],
        [0.31, FS.spinnerNose + 0.4],
        [0.352, FS.spinnerNose + 0.5],
        [0.358, FS.fanLE + 0.02],
        [0.36, FS.fanLE + 0.02],
      ]),
    text: "The nose cone that rotates with the fan. It gives the hub flow a smooth entry, keeps ice from building at the centre by shape and flex, and carries the fan's forward balance plane.",
    facts: [
      f("Hub radius at the fan", "0.3605 m", "CR-165148 Table IV, tip radius × 0.342"),
      f("Anti-icing", "None: rubber tip and conical shape shed ice", "large-turbofan practice", SCH),
    ],
  },
  {
    id: "fan-blades",
    tint: "lp",
    name: "Fan blades",
    system: "gas-generator",
    spool: "lp",
    y: 0,
    r: 0.75,
    build: () =>
      merge([
        bladeRow(
          {
            // CR-165148 Fig.41: the printed sections, hub to tip. Camber
            // 68° → 8°, stagger 12° → 62°, thickness 10 % → 2.6 % of chord.
            // Appendix B's 23 printed stations, lofted as printed. No
            // resampling and no lean: the appendix prints ONE axial
            // coordinate for the whole stacking axis, which is what a
            // radial stack with no sweep and no lean looks like written
            // down. The 60° sweep in the reports is the inner OGV's.
            sections: appendixSections(FAN_SECTIONS).stations,
            points: 12,
          },
          FAN.blades,
          FAN.rHub,
          0
        ),
        // The mid-span shroud ring the E³ fan carries.
        tipShroud(FAN.rHub + (FAN.rTip - FAN.rHub) * FAN.shroudSpan, 0.0, 0.05, 0.012),
      ]),
    text: "Thirty-two solid titanium blades with a part-span shroud, doing about four fifths of the engine's thrust by themselves. The tip runs supersonic; the root is a 68°-camber subsonic section set almost axially, which is why the blade twists through fifty degrees from hub to tip. The sections here are the report's own, read off its Fig. 41.",
    facts: [
      f("Blade count", "32", "CR-168219 sec 5.1.2 p.45"),
      f("Tip radius", "1.054 m", "CR-165148 Table IV"),
      f("Corrected tip speed", "411.5 m/s at max climb; 390.6 m/s physical at 3,539 rpm", "CR-165148 Table I p.4; derived"),
      f("Part-span shroud", "55 % span (CR-165148) / 50 % (CR-168219), tungsten-carbide faces", "CR-165148 Fig.46 p.56; CR-168219 sec 5.1.2 p.45"),
      f("Tip relative Mach", "1.41 (design)", "CR-165148 Fig.10; reproduced 1.405 in PF-09 unit 6"),
      f("Material", "Ti-6Al-4V, solid; 7.27 kg per blade", "CR-165148 Table V p.49, Table VI p.74"),
      f("Sections", "camber 68 → 8°, stagger 12 → 62°, chord 18.5 → 28.7 cm, t/c 10 → 2.6 % at 0/20/40/55/60/80/100 % height", "CR-165148 Fig.41 p.50 (read off)"),
      f("Untwist at speed", "1.6° at the tip at 3,653 rpm; the blade is pre-twisted for it", "CR-165148 Fig.43 p.53"),
    ],
  },
  {
    id: "fan-disc",
    tint: "lp",
    name: "Fan disc",
    system: "gas-generator",
    spool: "lp",
    y: 0,
    r: 0.2,
    build: () =>
      lathe([
        [0.085, -0.13],
        [0.085, 0.14],
        [0.2, 0.1],
        [0.34, 0.06],
        [FAN.rHub, 0.03],
        [FAN.rHub, -0.03],
        [0.34, -0.06],
        [0.2, -0.1],
        [0.085, -0.13],
      ]),
    text: "The disc the fan blades dovetail into. It carries the blades' centrifugal load, roughly the weight of a house per blade at full speed, in hoop stress, and is the single most safety-critical part on the engine: a disc release cannot be contained.",
    facts: [
      f("Material", "Ti-6Al-4V; disc-shaft joint 30 × 5/8-in Inco 718 bolts at 101.9 kN preload", "CR-165148 Table V p.49, Fig.61 p.73"),
      f("Design driver", "LCF life of the bore at takeoff speed", "designer agent §4", SCH),
    ],
  },
  {
    id: "booster-drum",
    tint: "lp",
    name: "Fan and booster rotor drum",
    system: "gas-generator",
    spool: "lp",
    y: 0.4,
    r: 0.45,
    build: () =>
      shell(
        [
          [FAN.rHub, 0.03],
          [0.45, 0.22],
          [BOOSTER.rHub, FS.islandVane - 0.02],
          [BOOSTER.rHub, FS.boosterRotor + 0.06],
          [ISLAND.rCoreHubAtOgv, FS.innerOgv - 0.05],
          [ISLAND.rCoreHubAtOgv - 0.01, FS.innerOgv + 0.06],
          [0.3, 0.8],
          [0.1, 0.86],
        ],
        0.02
      ),
    text: "A cone off the back of the fan disc that carries the single booster stage and closes the LP rotor forward of its thrust bearing. Fan and booster turn together on the LP spool.",
    facts: [f("Booster hub radius", "0.523 m", "CR-165148 Table IV, tip × 0.782")],
  },
  {
    id: "island-vane",
    tint: "stator",
    name: "Island stator (booster inlet vane)",
    system: "gas-generator",
    y: FS.islandVane,
    r: 0.6,
    build: () =>
      merge([
        bladeRow(
          {
            span: BOOSTER.rTip - BOOSTER.rHub - 0.005,
            chordRoot: BOOSTER.islandVane.chord,
            staggerRoot: BOOSTER.islandVane.staggerRoot,
            staggerTip: BOOSTER.islandVane.staggerTip,
            camberRoot: BOOSTER.islandVane.camberRoot,
            camberTip: BOOSTER.islandVane.camberTip,
            thickness: BOOSTER.islandVane.tmRoot,
            mirror: true,
          },
          BOOSTER.islandVanes,
          BOOSTER.rHub + 0.005,
          FS.islandVane,
          0.5
        ),
        ring(BOOSTER.rHub - 0.012, BOOSTER.rHub + 0.004, FS.islandVane - 0.04, FS.islandVane + 0.04),
      ]),
    text: "Sixty vanes in the 'island' between the fan and the booster. They take the swirl the fan hub leaves in the core stream and set the flow up for the booster rotor.",
    facts: [
      f("Vane count", "60, banded; length 15.67 cm, chord 8.13 cm", "CR-165148 Table VII p.92"),
      f("Angles", "stagger 20.3 → 21.5°, camber 37.3 → 35.8°", "CR-165148 Table VII p.92"),
      f("Material", "Ti-6-4 on the FPS (CR-168219 Fig.13 says aluminium; both printed)", "CR-165148 Table VII p.92; CR-168219 Fig.13"),
    ],
  },
  {
    id: "booster-blades",
    tint: "lp",
    name: "Booster rotor",
    system: "gas-generator",
    spool: "lp",
    y: FS.boosterRotor,
    r: 0.6,
    build: () =>
      bladeRow(
        {
          // CR-165148 Fig.52: camber 33 → 8°, stagger 23 → 42°, t/c 8.2 → 5.2 %.
          // Appendix D's 14 printed stations. Its tm/c rises at the tip,
          // the only non-monotonic column in either appendix; it is printed
          // that way and is not smoothed here.
          sections: appendixSections(BOOSTER_SECTIONS).stations,
        },
        BOOSTER.blades,
        BOOSTER.rHub,
        FS.boosterRotor
      ),
    text: "The E³'s 'quarter-stage' booster: a single titanium rotor on the LP spool that supercharges the core. It raises core inlet pressure without a heavy multi-stage booster; the trade is a low-speed rotor that is close to stall at idle, which is what the bleed doors behind it are for.",
    facts: [
      f("Blade count", "56, unshrouded, Ti-6Al-4V", "CR-165148 Table IV p.47, Table V p.49"),
      f("Tip speed", "261.1 m/s corrected at climb", "CR-165148 Table IV p.47"),
      f("Flow", "22.3 % of the fan flow passes under the island through this rotor; 42 % of that returns to the bypass behind it, 82.4 kg/s enters the core", "CR-165148 Appendix A pp.118–124"),
      f("Sections", "camber 33 → 8°, stagger 23 → 42°, chord 7.1 → 6.4 cm", "CR-165148 Fig.52 p.63 (read off)"),
    ],
  },
  {
    id: "inner-ogv",
    tint: "stator",
    name: "Inner (core) OGV",
    system: "gas-generator",
    y: FS.innerOgv,
    r: 0.55,
    build: () =>
      merge([
        bladeRow(
          {
            span: BOOSTER.innerOgvRow.length - 0.004,
            chordRoot: BOOSTER.innerOgvRow.chordRoot,
            chordTip: BOOSTER.innerOgvRow.chordTip,
            staggerRoot: BOOSTER.innerOgvRow.staggerRoot,
            staggerTip: BOOSTER.innerOgvRow.staggerTip,
            camberRoot: BOOSTER.innerOgvRow.camberRoot,
            camberTip: BOOSTER.innerOgvRow.camberTip,
            thickness: BOOSTER.innerOgvRow.tmRoot,
            sweepTip: -0.3,
            mirror: true,
          },
          BOOSTER.innerOgv,
          ISLAND.rCoreHubAtOgv + 0.004,
          FS.innerOgv,
          0.5
        ),
        ring(ISLAND.rCoreHubAtOgv - 0.012, ISLAND.rCoreHubAtOgv + 0.004, FS.innerOgv - 0.05, FS.innerOgv + 0.05),
      ]),
    text: "Sixty-four swept and leaned aluminium vanes in the core duct, behind the second splitter, taking the swirl out of the 58 % of the island flow that goes on to the HPC. Their 55° to 62° of camber is the largest turning of any fan-module row; sweep and lean are there to reduce the noise the booster wake makes on them.",
    facts: [
      f("Vane count", "64, banded, swept 60°, leaned 0→20°, 7075 aluminium", "CR-165148 Table VII p.92, sec II.D"),
      f("Geometry", "length 11.61 cm, chord 9.25 → 5.44 cm, stagger 18.4 → 21.5°, camber 55.4 → 62.4°", "CR-165148 Table VII p.92"),
      f("Flow", "82.4 kg/s corrected, cumulative pressure ratio 1.668", "CR-165148 Appendix A p.122"),
    ],
  },
  {
    id: "island-exit-vanes",
    tint: "stator",
    name: "Island exit vanes (booster flow returning to the bypass)",
    system: "gas-generator",
    y: FS.islandExitVanes,
    r: 0.645,
    build: () =>
      bladeRow(
        { span: ISLAND.rUnder - ISLAND.rSplit2 - 0.016, chordRoot: 0.16, staggerRoot: 12, camberRoot: 30, thickness: 0.07, mirror: true },
        BOOSTER.islandExitVanes,
        ISLAND.rSplit2 + 0.012,
        FS.islandExitVanes,
        0.5
      ),
    text: "The quarter-stage trick: the booster pumps more air than the core wants, so behind it a second splitter sends 42 % of the boosted flow outward, past these thirty-four vanes, back into the bypass stream behind the island. The core takes the inner 58 %. That is what lets one booster stage serve both a growth core and the bypass efficiency.",
    facts: [
      f("Vane count", "34: the lower part of the 34-strut vane-frame", "CR-165148 Appendix A p.123 (S2OUT)"),
      f("Flow returned", "61.35 of 143.74 kg/s corrected, 42.7 %", "CR-165148 Appendix A p.123; summary p.3 'approximately 42'"),
      f("Passage radii", "0.611 → 0.669 m: the second splitter sits where 58 % of the island annulus area lies below it", "", ASM),
    ],
  },
  {
    id: "bypass-ogv",
    tint: "stator",
    name: "Bypass outlet guide vanes",
    system: "gas-generator",
    y: FS.bypassOgv,
    r: 0.88,
    build: () =>
      bladeRow(
        { span: 1.06 - ISLAND.rTop, chordRoot: 0.17, chordTip: 0.15, staggerRoot: 14, staggerTip: 10, camberRoot: 32, camberTip: 28, thickness: 0.06, sweepTip: 0.05, mirror: true },
        BOOSTER.bypassOgv,
        ISLAND.rTop,
        FS.bypassOgv,
        0.5
      ),
    text: "Thirty-four vanes across the bypass duct that straighten the fan's swirl into axial flow, which is what makes the bypass stream produce thrust. On the E³ they are also the struts of the composite fan frame: the vane is the structure. Spaced 1.8 tip chords behind the fan so its wakes have decayed, which is one of the biggest levers on fan noise.",
    facts: [
      f("Vane count", "34, in five camber families; pylon at 0°, thick strut at 180°", "CR-165148 sec II.E p.30; CR-168219 Fig.13 p.38"),
      f("Role", "the fan frame's struts, integral with the graphite-composite frame", "CR-168219 sec 5.1.2 p.45"),
      f("Spacing behind the fan", "1.8 rotor tip chords", "CR-165148"),
      f("Material", "composite (FPS); 17-4 PH steel on the ICLS", "CR-165148 Table VII"),
    ],
  },
];

// ── HPC ───────────────────────────────────────────────────────────────────

const hpcRows = [];
const statorNames = ["IGV", ...Array.from({ length: 10 }, (_, i) => `S${i + 1}`)];

for (let k = 0; k < 10; k++) {
  const row = HPC_ROWS[`R${k + 1}`];
  const m = rowMid(row);
  const span = m.rTip - m.rHub - 0.004;
  hpcRows.push({
    id: `hpc-r${k + 1}`,
    tint: "hp",
    name: `HPC rotor ${k + 1}`,
    system: "gas-generator",
    spool: "hp",
    y: m.y,
    r: (m.rHub + m.rTip) / 2,
    build: () => {
      const printed = printedSections(`R${k + 1}`);
      return bladeRow({ sections: printed.stations, points: 10 }, HPC_ROTOR_BLADES[k], printed.rHub, m.y);
    },
    text:
      k === 0
        ? "The first of ten HPC stages, and the biggest step: a transonic rotor doing a pressure ratio near 1.6 on its own. The blade is set at 23° at the root and 65° at the tip, straight from the report's Table X, which is why it looks twisted."
        : k < 4
          ? `Stage ${k + 1} of the ten-stage HPC, one of the four transonic front stages. Blade count and section angles are the report's; the row's job is a pressure ratio near 1.4 with an unshrouded titanium blade.`
          : k < 6
            ? `Stage ${k + 1}: a subsonic mid-compressor rotor, the last titanium stage before the temperature crosses into nickel-alloy territory at the inertia weld between the front and rear drums.`
            : `Stage ${k + 1}: a rear-stage rotor in Inconel 718, only about ${(span * 100).toFixed(1)} cm tall. Tip clearance is now a large fraction of blade height, which is why the rear case has active clearance control.`,
    facts: [
      f("Blade count", String(HPC_ROTOR_BLADES[k]), "HPC report Table X p.65"),
      f("Airfoil length", `${(span * 100).toFixed(1)} cm`, "HPC report Table XXI streamlines"),
      f("Stagger root → tip", `${HPC_TABLE_X.staggerRoot[k]}° → ${HPC_TABLE_X.staggerTip[k]}°`, "HPC report Table X p.65"),
      f("Camber root → tip", `${HPC_TABLE_X.camberRoot[k]}° → ${HPC_TABLE_X.camberTip[k]}°`, "HPC report Table X p.65"),
      f("Section geometry", "all 12 printed sections lofted: chord, camber, stagger, thickness per section", "HPC report Table XXII pp.154–159"),
      f("Material", HPC_MATERIAL(k), "HPC report Table X p.65; PF-09 unit E1"),
      ...(k < 4 ? [f("Transonic", "yes (rotors 1–4)", "CR-168219 sec 5.2.1 p.52")] : []),
    ],
  });
}

for (const name of statorNames) {
  const row = HPC_ROWS[name];
  const m = rowMid(row);
  const variable = HPC_VARIABLE_ROWS.includes(name);
  const idx = name === "IGV" ? 0 : Number(name.slice(1));
  const printed = printedSections(name);
  const chord = printed.stations[0].chord;
  const span = m.rTip - m.rHub - 0.004;
  const spec = { sections: printed.stations, points: 10, mirror: true };
  hpcRows.push({
    id: `hpc-${name.toLowerCase()}`,
    tint: variable ? undefined : "stator",
    name: name === "IGV" ? "HPC inlet guide vanes" : name === "S10" ? "HPC outlet guide vanes (stator 10)" : `HPC stator ${idx}`,
    system: variable ? "variable-geometry" : "gas-generator",
    y: m.y,
    r: (m.rHub + m.rTip) / 2,
    // Variable rows are instanced so each vane can turn on its spindle.
    kind: variable ? "vsvRow" : undefined,
    vsv: variable ? { count: HPC_STATOR_VANES[name], rHub: printed.rHub, y: m.y, spec, closedDeg: [38, 32, 26, 18, 12, 8][idx], rTip: m.rTip } : undefined,
    build: () =>
      merge([
        bladeRow(spec, HPC_STATOR_VANES[name], printed.rHub, m.y, 0.5),
        ring(m.rHub - 0.014, m.rHub + 0.002, m.y - chord / 2, m.y + chord / 2),
      ]),
    text: variable
      ? name === "IGV"
        ? "The inlet guide vanes: variable, closing by tens of degrees at low speed to reduce the swirl-free incidence onto rotor 1. Move the VSV slider to see the whole set schedule together on their unison rings."
        : `Stator ${idx}, one of the variable rows (IGV plus stators 1–5 on the product engine). Each vane turns on a spindle through the casing, driven by a lever from a unison ring, so the front stages stay matched to the rear ones as speed changes.`
      : name === "S10"
        ? "The last row: 140 vanes that remove the swirl from the compressor exit so the diffuser and combustor see axial flow. Two OGV rows in a real engine are often one; the E³ used a single high-count row."
        : `Stator ${idx}, fixed. It turns the flow leaving rotor ${idx} back toward axial, converting some of the rotor's swirl velocity into static pressure before the next rotor.`,
    facts: [
      f("Vane count", String(HPC_STATOR_VANES[name]), "HPC report Table XXII pp.157–159"),
      f("Variable", variable ? "yes (FPS product: IGV + S1–S5; CR-168219 says IGV + S1–S4)" : "no", "HPC report sec 3.3 p.64; CR-168219 sec 5.2 p.45"),
      f("Material", "non-titanium, for titanium-fire prevention", "CR-168219 sec 5.2.2 p.55"),
      f("Vane height", `${(span * 100).toFixed(1)} cm`, "HPC report Table XXI streamlines"),
      f("Section geometry", name === "IGV" ? "12 printed sections lofted; camber taken as 25 × CL0 (the table prints CL0)" : "all 12 printed sections lofted", "HPC report Table XXII pp.154–159"),
    ],
  });
}

const hpcRotorStructure = [
  {
    id: "hpc-drum",
    tint: "hp",
    name: "HPC rotor spool (drums and discs)",
    system: "gas-generator",
    spool: "hp",
    y: HPC0 + 0.38,
    r: 0.2,
    build: () => {
      const hubLine = [];
      for (let k = 1; k <= 10; k++) {
        const r = HPC_ROWS[`R${k}`];
        hubLine.push([r.LE.rHub - 0.004, r.LE.yHub], [r.TE.rHub - 0.004, r.TE.yHub]);
      }
      const drum = shell(hubLine, 0.022);
      const discs = [1, 3, 5, 7, 9].map((k) => {
        const r = HPC_ROWS[`R${k}`];
        const y = (r.LE.yHub + r.TE.yHub) / 2;
        return lathe([
          [0.1, y - 0.03],
          [0.1, y + 0.03],
          [0.16, y + 0.012],
          [r.LE.rHub - 0.01, y + 0.008],
          [r.LE.rHub - 0.01, y - 0.008],
          [0.16, y - 0.012],
          [0.1, y - 0.03],
        ]);
      });
      // Front cone to the HP thrust bearing and the aft cone to the HPT.
      const front = shell(
        [
          [HPC_ROWS.R1.LE.rHub - 0.01, HPC_ROWS.R1.LE.yHub],
          [0.15, HPC0 - 0.09],
          [0.12, HPC0 - 0.17],
        ],
        0.02
      );
      const aft = shell(
        [
          [HPC_ROWS.R10.TE.rHub - 0.01, HPC_ROWS.R10.TE.yHub],
          [0.2, HPC0 + 0.88],
          [0.165, HPC0 + 0.98],
          [0.165, HPT0 + 0.03],
        ],
        0.02
      );
      return merge([drum, ...discs, front, aft]);
    },
    text: "The HP rotor: a forward titanium drum and an aft nickel-alloy drum inertia-welded together, with a single bolted joint, carrying all ten blade rows. The bore is cooled by fan discharge air. Cones off each end reach the forward thrust bearing and the HPT.",
    facts: [
      f("Construction", "inertia-welded forward and aft sections, single bolt joint", "CR-168219 sec 5.2.2 p.52"),
      f("Bore cooling", "fan discharge air", "CR-168219 sec 5.2.2 p.52"),
      f("HP speed, 100 % corrected", "12,303 rpm", "HPC report Table X footnotes p.65"),
      f("Stress case speed", "13,948 rpm (deteriorated engine)", "HPC report Table X footnotes p.65"),
    ],
  },
  {
    id: "hpc-front-case",
    name: "HPC front casing (stages IGV–5)",
    system: "structure",
    y: HPC0 + 0.2,
    r: 0.36,
    build: () => {
      const line = [];
      for (const n of ["IGV", "R1", "S1", "R2", "S2", "R3", "S3", "R4", "S4", "R5", "S5"]) {
        const r = HPC_ROWS[n];
        line.push([r.LE.rTip + 0.018, r.LE.yTip], [r.TE.rTip + 0.018, r.TE.yTip]);
      }
      return shell(line, 0.02);
    },
    text: "The casing over the variable-geometry stages. Every VSV spindle passes through it, so it is drilled hundreds of times and carries the unison rings on its outside. Split at horizontal flanges so blades and vanes can be replaced with the rotor in place, and made of a non-titanium alloy so a rubbing blade cannot start a titanium fire.",
    facts: [
      f("Tip radii it follows", "0.362 → 0.312 m (IGV LE to S5 TE)", "HPC report Table XXI"),
      f("Construction", "split casing, horizontal flanges; front/aft/manifold casings with 60 / 32 / 28 × 3/8-in bolts", "CR-168219 Fig.5 p.15; HPC report Table XVII p.102"),
      f("Material", "non-titanium (Ti-fire prevention)", "CR-168219 sec 5.2.2 p.55"),
    ],
  },
  {
    id: "hpc-rear-case",
    name: "HPC rear casing (stages 6–10)",
    system: "structure",
    y: HPC0 + 0.62,
    r: 0.33,
    build: () => {
      const line = [];
      for (const n of ["R6", "S6", "R7", "S7", "R8", "S8", "R9", "S9", "R10", "S10"]) {
        const r = HPC_ROWS[n];
        line.push([r.LE.rTip + 0.018, r.LE.yTip], [r.TE.rTip + 0.018, r.TE.yTip]);
      }
      return shell(line, 0.02);
    },
    text: "The casing over the small rear stages, where a tip clearance of half a millimetre is a couple of percent of blade height. Its outside is wrapped by the clearance-control manifold, which blows cooler air on it to shrink it onto the blades at cruise.",
    facts: [f("Blade heights it encloses", "3.8 → 2.0 cm", "HPC report Table XXI")],
  },
];

// ── Diffuser and combustor ────────────────────────────────────────────────

const yDiff0 = STATIONS.hpcOgvTE;
const combustor = [
  {
    id: "diffuser",
    name: "Diffuser and compressor rear frame",
    system: "structure",
    y: yDiff0 + 0.06,
    r: 0.36,
    build: () =>
      merge([
        // Pre-diffuser walls.
        shell([[0.312, yDiff0], [0.33, yDiff0 + 0.05], [0.34, yDiff0 + 0.1]], 0.012),
        shell([[0.272, yDiff0], [0.262, yDiff0 + 0.05], [0.255, yDiff0 + 0.1]], 0.012),
        // The frame cone from the casing out to the combustor case.
        shell([[0.33, yDiff0 - 0.005], [0.42, yDiff0 + 0.04], [0.47, yDiff0 + 0.09]], 0.02),
        struts(30, 0.255, 0.34, yDiff0 + 0.06, 0.06, 0.012),
        // Inner hub cone toward the HP shaft.
        shell([[0.255, yDiff0 + 0.1], [0.21, yDiff0 + 0.13], [0.185, yDiff0 + 0.2]], 0.015),
      ]),
    text: "The pre-diffuser slows the compressor exit flow from Mach 0.30 to 0.16 before it reaches the combustor; the frame around it carries the aft end of the HP compressor case and the front of the combustor case, and its struts carry the thrust links' load on many engines.",
    facts: [
      f("Diffuser inlet Mach", "0.30, passage 0.16", "combustor report (combustor-design.yaml)"),
      f("Strut count", "30, split-duct prediffuser; mid-span bleed through 28 struts feeds the HPT rotor coolant", "CR-168301 sec 4.2.2 p.18; CR-167955 sec 3.2.2 p.37"),
      f("Material", "Inco 718", "CR-168301 Fig.29 p.54"),
    ],
  },
  {
    id: "combustor-case",
    name: "Combustor casing",
    system: "structure",
    y: (COMBUSTOR.yDome + COMBUSTOR.yExit) / 2,
    r: 0.47,
    build: () => shell([[0.47, yDiff0 + 0.09], [0.47, HPT0 - 0.02]], 0.022),
    text: "The pressure vessel of the engine: it sees the full compressor delivery pressure, near 40 atmospheres at takeoff, at a few hundred degrees. The fuel nozzles, both igniters, the PS3 tap and the borescope ports all pass through it.",
    facts: [
      f("Pressure inside", "P3 3.03 MPa, T3 815 K at standard-day takeoff; OPR 38.4 at max climb", "CR-168301 Table XVII p.92; CR-168219 Table XII p.35"),
      f("Ports", "30 fuel nozzle, 30 instrumentation, 2 igniter, 8 CDP bleed, 4–6 borescope; 30 support pins", "CR-168301 sec 5.3.2 pp.63–70"),
      f("Material", "Inco 718; flange loads 249 kN fwd / 222 kN aft at growth P3", "CR-168301 Fig.29, Fig.77 p.122"),
    ],
  },
  {
    id: "combustor-liner",
    tint: "combustor",
    name: "Combustor liner (double annular)",
    system: "gas-generator",
    y: (COMBUSTOR.yDome + COMBUSTOR.yExit) / 2,
    r: 0.34,
    build: () => {
      const { rLinerOuter: ro, rLinerInner: ri, yDome, yExit } = COMBUSTOR;
      const outer = shell([[ro, yDome], [ro + 0.005, yDome + 0.12], [HT.vane1Inlet.rTip + 0.004, yExit - 0.01]], 0.012);
      const inner = shell([[ri, yDome], [ri - 0.004, yDome + 0.12], [HT.vane1Inlet.rHub - 0.004, yExit - 0.01]], 0.012);
      const dome = ring(ri, ro, yDome - 0.012, yDome);
      const centrebody = shell([[(ri + ro) / 2, yDome], [(ri + ro) / 2, yDome + 0.11], [(ri + ro) / 2 + 0.01, yDome + 0.14]], 0.012);
      // Sixty swirl cups, two rows of thirty.
      const cups = [];
      for (const rc of [(ri + ro) / 2 + 0.024, (ri + ro) / 2 - 0.024]) {
        for (let i = 0; i < 30; i++) {
          const g = hoop(0.016, 0.005, yDome - 0.004, 6, 16);
          g.translate(rc, 0, 0);
          g.rotateY(((i + (rc > (ri + ro) / 2 ? 0 : 0.5)) / 30) * Math.PI * 2);
          cups.push(g);
        }
      }
      return merge([outer, inner, dome, centrebody, ...cups]);
    },
    text: "The E³'s double-annular combustor: two concentric rows of thirty swirl cups on one dome. The outer 'pilot' ring alone burns at idle for low CO and hydrocarbons; the inner 'main' ring lights at power for low NOx. The shingled liner walls are film-cooled segments, not one sheet.",
    facts: [
      f("Swirl cups", "60 (30 pilot + 30 main)", "combustor report sec 5.3.2 p.61"),
      f("Liner radii", "inner 29.2 cm, outer 37.4 cm (from shingle arc widths)", "combustor-design.yaml"),
      f("Cooling and dilution", "5.9 % bleed; pressure loss ~5 %", "combustor-design.yaml; CR-168219 Table XI p.34"),
      f("Exit / T41", "1,517 K at the HPT rotor (max climb); 1,638 K takeoff", "CR-168219 Table XII p.35"),
      f("Materials", "X-40 shingles, Hastelloy X dome, Inco 625 support liners; centrebody Hastelloy X + zirconate TBC", "CR-168301 Fig.29, Table XIX p.115"),
      f("Fuel staging", "pilot dome only at start and idle; main dome lit at ~80 % N2", "CR-168219 sec 5.10.2"),
    ],
  },
];

// ── HPT ───────────────────────────────────────────────────────────────────

const hpt = [
  {
    id: "hpt-v1",
    tint: "stator",
    name: "HPT stage-1 nozzle vanes",
    system: "gas-generator",
    y: HPT0 + 0.018,
    r: 0.344,
    build: () =>
      merge([
        bladeRow(
          { span: HT.vane1Exit.rTip - HT.vane1Exit.rHub - 0.004, chordRoot: 0.06, staggerRoot: 42, camberRoot: 72, thickness: 0.2, stations: 3, mirror: true },
          HPT_VANES[0],
          HT.vane1Inlet.rHub + 0.002,
          HPT0 + 0.018,
          0.5
        ),
        ring(HT.vane1Inlet.rHub - 0.014, HT.vane1Inlet.rHub + 0.002, HPT0 - 0.005, HPT0 + 0.04),
        ring(HT.vane1Inlet.rTip - 0.002, HT.vane1Inlet.rTip + 0.014, HPT0 - 0.005, HPT0 + 0.04),
      ]),
    text: "The hottest metal in the engine: forty-six vanes sitting straight in the combustor exit gas, cooled by impingement and film from compressor-delivery air that bypasses the liner. They accelerate and turn the gas by about seventy degrees onto the first rotor.",
    facts: [
      f("Vane count", "46, in 23 two-vane segments", "CR-167955 Table III p.10"),
      f("Gas temperature", "T41 1,517 K max climb; 1,638 K takeoff", "CR-168219 Table XII p.35"),
      f("Cooling air", "combustor-liner bypass (CDP) air: 6.3 % of core flow through the vanes + 2.8 % through the bands", "CR-167955 sec 3.1.3 p.23"),
      f("Material", "MA754 ODS airfoils, MAR-M-509 bands; TBC added on the FPS", "CR-167955 sec 5.1.2 pp.94–95; CR-168219 sec 3.1 p.10"),
    ],
  },
  {
    id: "hpt-b1",
    tint: "hp",
    name: "HPT stage-1 blades",
    system: "gas-generator",
    spool: "hp",
    y: HPT0 + 0.062,
    r: 0.345,
    build: () =>
      bladeRow(
        { span: HT.blade1Exit.rTip - HT.blade1Exit.rHub - 0.005, chordRoot: 0.04, staggerRoot: 38, camberRoot: 95, camberTip: 80, thickness: 0.17, stations: 3 },
        HPT_BLADES[0],
        HT.vane1Exit.rHub + 0.002,
        HPT0 + 0.062
      ),
    text: "Seventy-six cast nickel-superalloy blades, each internally cooled, each pulling several tonnes at the root at 13,000 rpm while sitting in gas hotter than its own melting point. The first stage extracts about half of the HP work.",
    facts: [
      f("Blade count", "76, unshrouded, squealer tip against a ceramic shroud", "CR-167955 Table III p.10, Table XVI"),
      f("Tip speed at takeoff", "513.9 m/s", "CR-167955 Table III p.10"),
      f("Pull per blade", "77.4 kN at 13,948 rpm", "CR-167955 Fig.81 p.137"),
      f("Material", "DS René 150 + PVD coating (hardware); René N4 single crystal + TBC on the FPS", "CR-167955 Table XVI; CR-168219 sec 3.1 p.10"),
      f("Coolant path", "CDP air through the diffuser struts to an 80-vane inducer that spins it up to wheel speed", "CR-167955 sec 3.1.3 p.23, Fig.95"),
    ],
  },
  {
    id: "hpt-v2",
    tint: "stator",
    name: "HPT stage-2 nozzle vanes",
    system: "gas-generator",
    y: HPT0 + 0.12,
    r: 0.348,
    build: () =>
      merge([
        bladeRow(
          { span: HT.vane2Exit.rTip - HT.vane2Exit.rHub - 0.006, chordRoot: 0.065, staggerRoot: 40, camberRoot: 68, thickness: 0.18, stations: 3, mirror: true },
          HPT_VANES[1],
          HT.blade1Exit.rHub - 0.004,
          HPT0 + 0.12,
          0.5
        ),
        ring(HT.blade1Exit.rHub - 0.02, HT.blade1Exit.rHub - 0.004, HPT0 + 0.09, HPT0 + 0.15),
      ]),
    text: "Forty-eight vanes between the two HPT rotors, still cooled, still turning the gas hard. Their inner platform carries the interstage seal that keeps hot gas out of the disc cavity.",
    facts: [
      f("Vane count", "48, in 24 segments", "CR-167955 Table III p.10"),
      f("Cooling air", "HPC stage-7 bleed, 1.95–2.35 % of core flow, four pipes into eight casing ports", "CR-167955 sec 3.2.4 p.49; CR-168219 sec 5.2.1 p.52"),
      f("Material", "DS René 150 airfoils, René 80 bands; René N4 + TBC on the FPS", "CR-167955; CR-168219 sec 3.1 p.10"),
    ],
  },
  {
    id: "hpt-b2",
    tint: "hp",
    name: "HPT stage-2 blades",
    system: "gas-generator",
    spool: "hp",
    y: HPT0 + 0.178,
    r: 0.346,
    build: () =>
      bladeRow(
        { span: HT.blade2Exit.rTip - HT.blade2Exit.rHub - 0.006, chordRoot: 0.045, staggerRoot: 36, camberRoot: 92, camberTip: 76, thickness: 0.15, stations: 3 },
        HPT_BLADES[1],
        HT.vane2Exit.rHub + 0.002,
        HPT0 + 0.178
      ),
    text: "Seventy blades, taller than the first stage because the gas has expanded. Together the two stages drive the entire ten-stage HPC through the HP shaft; there is no other load on this spool except the gearbox.",
    facts: [
      f("Blade count", "70, unshrouded", "CR-167955 Table III p.10"),
      f("Tip speed at takeoff", "535.2 m/s", "CR-167955 Table III p.10"),
      f("Cooling", "serpentine-cooled DS René 150 (hardware); uncooled DS eutectic on the FPS, saving 0.76 % of core flow", "CR-167955 sec 3.2.5 p.54; CR-168219 sec 3.1 p.10"),
      f("Two-stage HPT efficiency", "0.921–0.927 by condition", "CR-168219 Table XI; PF-09 unit 3 closes at 0.921"),
    ],
  },
  {
    id: "hpt-discs",
    tint: "hp",
    name: "HPT discs and spacer",
    system: "gas-generator",
    spool: "hp",
    y: HPT0 + 0.12,
    r: 0.22,
    build: () => {
      const disc = (y, rim) =>
        lathe([
          [0.165, y - 0.045],
          [0.165, y + 0.045],
          [0.21, y + 0.02],
          [rim, y + 0.012],
          [rim, y - 0.012],
          [0.21, y - 0.02],
          [0.165, y - 0.045],
        ]);
      return merge([
        disc(HPT0 + 0.062, HT.vane1Exit.rHub - 0.002),
        disc(HPT0 + 0.178, HT.vane2Exit.rHub - 0.002),
        ring(HT.blade1Exit.rHub - 0.03, HT.blade1Exit.rHub - 0.02, HPT0 + 0.075, HPT0 + 0.165),
        // Aft stub to the intershaft bearing.
        shell([[0.165, HPT0 + 0.2], [0.14, HPT0 + 0.25], [0.12, HPT0 + 0.32]], 0.02),
      ]);
    },
    text: "Two powder-metallurgy nickel discs bolted through a spacer. The rim load on one disc is about 5,900 kN, six hundred tonnes; the bore is the life-limiting feature and it peaks in stress not at maximum speed but some minutes into a climb, when the rim has heated and the bore has not.",
    facts: [
      f("Rim load, one disc", "5,882 kN (76 × 77.4 kN)", "CR-167955 Fig.81; PF-09 unit E2"),
      f("Material", "René 95 powder metallurgy, HIP near-net; AF115 inducer and seal disc", "CR-167955 Table XVI p.93"),
      f("Retention", "no bolt holes in the live discs; boltless blade retainers", "CR-167955 Fig.51 p.91"),
      f("Bore stress peak", "at ~875 s (max climb), thermal not centrifugal", "PF-09 unit E2 finding 81"),
      f("Stage-2 disc bore stress", "~1,000 MPa at 875 s", "HPT report Fig.64 via PF-09 E2"),
    ],
  },
  {
    id: "hpt-case",
    name: "HPT casing and shrouds",
    system: "structure",
    y: HPT0 + 0.1,
    r: 0.41,
    build: () =>
      shell(
        [
          [HT.vane1Inlet.rTip + 0.028, HPT0 - 0.02],
          [HT.blade1Exit.rTip + 0.028, HPT0 + 0.09],
          [HT.vane2Exit.rTip + 0.03, HPT0 + 0.16],
          [HT.blade2Exit.rTip + 0.03, HPT0 + 0.22],
        ],
        0.024
      ),
    text: "Carries the two nozzle rows and the blade-tip shroud segments. The shroud segments are the abradable surface the blade tips run against; the clearance between them and the tips is set by the active clearance control blowing fan air on this casing.",
    facts: [
      f("Tip radius it follows", "0.372 → 0.381 m", "HPT report Fig.3"),
      f("Material", "Direct-Age Inco 718, single wall with fan-air impingement directly on it", "CR-167955 sec 5.2.2.1 p.154"),
      f("Stage-1 shroud", "plasma-sprayed zirconia on cast René 77, ≥1 mm; stage-2 solid René 77", "CR-167955 sec 5.2.3 pp.167–176"),
      f("Running clearance", "0.41 mm wanted at cruise, 0.64 mm at takeoff", "CR-167955 sec 4.2 p.73"),
    ],
  },
];

// ── LPT ───────────────────────────────────────────────────────────────────

const lpt = [];
for (let k = 1; k <= 5; k++) {
  const s = LPT_ROWS[`S${k}`];
  const r = LPT_ROWS[`R${k}`];
  const sm = rowMid(s);
  const rm = rowMid(r);
  const rChord = (r.TE.yHub - r.LE.yHub) * 0.95;
  lpt.push({
    id: `lpt-s${k}`,
    tint: "stator",
    name: `LPT stage-${k} vanes`,
    system: "gas-generator",
    y: sm.y,
    r: (sm.rHub + sm.rTip) / 2,
    build: () =>
      merge([
        bladeRowFromCoords(
          LPT_SECTIONS[`S${k}`].map((sec) => sec.map(([r, z, rt]) => [r, LPT0 + z, rt])),
          LPT_VANES[k - 1]
        ),
        ring(sm.rHub - 0.014, sm.rHub + 0.002, s.LE.yHub, s.TE.yHub),
      ]),
    text:
      k === 1
        ? "The first LPT nozzle row, fed by the transition duct whose outer wall flares out at up to 25°. Cooled by stage-5 HPC air; downstream of it the LPT runs uncooled."
        : `Stage-${k} nozzle: ${LPT_VANES[k - 1]} vanes turning the gas onto rotor ${k}. Vane counts differ row to row on purpose, so no two rows share a forcing frequency the blades could resonate with.`,
    facts: [
      f("Vane count", String(LPT_VANES[k - 1]), "LPT report Fig.6 p.12"),
      f("Material", k === 1 ? "René 125 (takes the HPT-exit hot streak); hollow" : k <= 3 ? "René 77, hollow" : "René 77, solid", "LPT report Table V p.76, Fig.80 p.124"),
      f("Vane height", `${((sm.rTip - sm.rHub) * 100).toFixed(1)} cm`, "from the 30 airfoil sections (lpt-flowpath.csv)"),
      f("Section geometry", "lofted from the report's printed surface coordinates at 10, 50 and 90 % span", "LPT report appendix p.148"),
    ],
  });
  lpt.push({
    id: `lpt-r${k}`,
    tint: "lp",
    name: `LPT stage-${k} blades`,
    system: "gas-generator",
    spool: "lp",
    y: rm.y,
    r: (rm.rHub + rm.rTip) / 2,
    build: () =>
      merge([
        bladeRowFromCoords(
          LPT_SECTIONS[`R${k}`].map((sec) => sec.map(([r, z, rt]) => [r, LPT0 + z, rt])),
          LPT_BLADES[k - 1]
        ),
        tipShroud(rm.rTip - 0.01, rm.y, rChord * 0.9, 0.008),
      ]),
    text:
      k === 5
        ? "The last turbine stage: 110 blades, the tallest in the engine at over 23 cm, shrouded at the tip. Its exit is the LPT's design constraint on swirl, because whatever swirl leaves here the rear frame struts must remove."
        : `Rotor ${k} of the five-stage LPT: ${LPT_BLADES[k - 1]} shrouded blades. Blade count and vane-to-blade gap on stage 4 were chosen for acoustic cut-off, not aerodynamics.`,
    facts: [
      f("Blade count", String(LPT_BLADES[k - 1]), "LPT report Fig.52 p.83"),
      f("Blade height", `${((rm.rTip - rm.rHub) * 100).toFixed(1)} cm`, "from the airfoil sections"),
      f("Section geometry", "lofted from the report's printed surface coordinates at 10, 50 and 90 % span", "LPT report appendix p.148"),
      f("Tip shroud", "integral, interlocked, two-tooth seals", "LPT report sec 4.2.1 p.82"),
      f("Material", "cast René 77, uncoated", "LPT report Table V p.76"),
      ...(k === 4 ? [f("Acoustic design", "vane-to-blade gap 1.4 chords, blade count raised for cutoff", "LPT report sec 4.1.2 p.78")] : []),
    ],
  });
}
lpt.push({
  id: "lpt-rotor",
  tint: "lp",
  name: "LPT discs and cone",
  system: "gas-generator",
  spool: "lp",
  y: LPT0 + 0.35,
  r: 0.25,
  build: () => {
    const parts = [];
    let prevRim = null;
    let prevY = null;
    for (let k = 1; k <= 5; k++) {
      const r = LPT_ROWS[`R${k}`];
      const y = (r.LE.yHub + r.TE.yHub) / 2;
      const rim = r.LE.rHub - 0.008;
      parts.push(
        lathe([
          [0.2, y - 0.035],
          [0.2, y + 0.035],
          [0.24, y + 0.014],
          [rim, y + 0.01],
          [rim, y - 0.01],
          [0.24, y - 0.014],
          [0.2, y - 0.035],
        ])
      );
      if (prevRim) parts.push(ring(Math.min(prevRim, rim) - 0.03, Math.min(prevRim, rim) - 0.018, prevY + 0.01, y - 0.01));
      prevRim = rim;
      prevY = y;
    }
    // One bearing cone from the disc-3 hub aft-inward to the No.5 bearing.
    const r3 = LPT_ROWS.R3;
    parts.push(shell([[0.2, (r3.LE.yHub + r3.TE.yHub) / 2 + 0.03], [0.14, LPT0 + 0.5], [0.1, LPT0 + 0.62]], 0.02));
    return merge(parts);
  },
  text: "Five discs joined by bolted flanges placed in low-stress areas, hung from a single bearing cone that runs aft to the No. 5 bearing in the turbine rear frame. Because the LP shaft turns at only a third of the HP speed, the LPT needs five stages and large radius to do the fan's work.",
  facts: [
    f("Construction", "Inco 718 discs with integral spacer arms, bolted flanges, no disc bolt holes (40/40/52/76/40 bolts per joint)", "LPT report Table V p.76, Table XIV p.110"),
    f("Bearing cone", "single cone from the LPT spool between the stage-3 and stage-4 discs to the aft sump", "LPT report sec 4.1.1 p.76; CR-168219 sec 5.5 p.82"),
    f("Total LPT blades", "630", "LPT report Fig.52"),
    f("LP shaft torque", "2.4× the HP shaft's", "PF-09 unit E4"),
  ],
});
lpt.push({
  id: "lpt-case",
  name: "LPT casing and transition duct",
  system: "structure",
  y: LPT0 + 0.3,
  r: 0.55,
  build: () => {
    const line = [[HT.blade2Exit.rTip + 0.03, HPT0 + 0.22]];
    for (let k = 1; k <= 5; k++) {
      for (const n of [`S${k}`, `R${k}`]) {
        const r = LPT_ROWS[n];
        line.push([r.LE.rTip + 0.025, r.LE.yTip], [r.TE.rTip + 0.025, r.TE.yTip]);
      }
    }
    const inner = shell([[HT.blade2Exit.rHub, HPT0 + 0.2], [LPT_ROWS.S1.LE.rHub, LPT_ROWS.S1.LE.yHub]], 0.012);
    return merge([shell(line, 0.02), inner]);
  },
  text: "The transition duct flares the flow out from the HPT exit to the larger LPT radius, and the LPT casing follows the tip line out to 0.60 m. Also wrapped by a clearance-control manifold, fed on the E³ by fan air scooped from the pylon.",
  facts: [
    f("Transition duct length", "7.62 cm, outer wall slope up to 25°; René 80, 18 segments", "CR-168219 sec 5.5; LPT report sec 4.3.1 p.108"),
    f("LPT tip radius", "0.408 → 0.601 m", "lpt-flowpath.csv"),
    f("Construction", "two Inco 718 forgings, one EB weld, no horizontal flanges; 132 bolts to the HPT case, 120 to the rear frame", "LPT report sec 4.3.3–4.3.4 pp.128–133"),
    f("Containment", "2.03 mm combined wall against 2.7–5.6 kN·m single-blade energies", "LPT report sec 4.3.4"),
  ],
});

// ── Shafts and bearings ───────────────────────────────────────────────────

const shafts = [
  {
    id: "lp-shaft",
    tint: "lp",
    name: "LP shaft",
    system: "gas-generator",
    spool: "lp",
    y: 1.7,
    r: 0.08,
    build: () => merge([ring(0.065, 0.082, -0.1, LPT0 + 0.63), ring(0.02, 0.028, 0.6, LPT0 + 0.3)]),
    text: "One shaft the full length of the engine connecting the LPT to the fan, running inside the HP spool. It carries 2.4 times the HP shaft's torque at a third of its speed, and inside it runs the centre vent tube that breathes both sumps.",
    facts: [
      f("Bearings", "No.1 ball (thrust), No.2 roller, No.5 roller", "CR-168219 sec 5.7 pp.96–99"),
      f("LP speed", "3,539 rpm max climb; 3,611 rpm takeoff", "LPT report Table VI p.80"),
      f("Both spools", "co-rotating, LP : HP ≈ 1 : 3.6", "CR-168219 sec 3.1 p.10"),
      f("Fan shaft material", "4340 steel (demonstrator), MARAGE 250 intended for the FPS", "CR-165148 Table V p.49"),
      f("Sump vent", "through the LP fan shaft to the aft centre vent tube", "CR-168219 sec 5.7"),
    ],
  },
  ...[
    { n: 1, type: "ball", role: "LP thrust bearing", y: 0.42, r: 0.11, sump: "forward" },
    { n: 2, type: "roller", role: "LP shaft support", y: 0.95, r: 0.105, sump: "forward" },
    { n: 3, type: "ball", role: "HP (core) thrust bearing", y: HPC0 - 0.19, r: 0.14, sump: "forward" },
    { n: 4, type: "roller", role: "intershaft bearing", y: HPT0 + 0.33, r: 0.1, sump: "aft" },
    { n: 5, type: "roller", role: "aft support bearing", y: LPT0 + 0.66, r: 0.11, sump: "aft" },
  ].map((b) => ({
    id: `bearing-${b.n}`,
    name: `No. ${b.n} bearing (${b.type}, ${b.role})`,
    system: "structure",
    y: b.y,
    r: b.r,
    build: () => {
      const inner = ring(b.r - 0.02, b.r - 0.008, b.y - 0.03, b.y + 0.03);
      const outer = ring(b.r + 0.012, b.r + 0.026, b.y - 0.03, b.y + 0.03);
      const elements = [];
      const count = b.type === "ball" ? 18 : 22;
      for (let i = 0; i < count; i++) {
        const g =
          b.type === "ball"
            ? hoop(0.0001, 0.011, b.y, 8, 6)
            : (() => {
                const c = lathe([[0, b.y - 0.02], [0.009, b.y - 0.02], [0.009, b.y + 0.02], [0, b.y + 0.02]], 10);
                return c;
              })();
        g.translate(b.r + 0.002, 0, 0);
        g.rotateY((i / count) * Math.PI * 2);
        elements.push(g);
      }
      return merge([inner, outer, ...elements]);
    },
    text:
      b.n === 1
        ? "The LP thrust bearing: a ball bearing that takes the entire forward thrust of the fan and booster, minus what the LPT pulls the other way, into the fan frame. Sits in the forward sump."
        : b.n === 3
          ? "The HP thrust bearing, in a centering-spring housing with a fluid-film damper, which is what keeps the HP rotor's critical speed out of the running range without a stiff, heavy frame."
          : b.n === 4
            ? "The intershaft roller: its outer race rides in a controlled-spring-rate housing on the LP shaft and its inner ring on the aft HP stub shaft, so the HP rotor's aft end is supported by the LP shaft itself. That eliminates a hot turbine mid-frame."
            : b.n === 5
              ? "The aft roller bearing, mounted in the turbine rear frame, reacting both rotor systems through the intershaft No. 4. The frame struts were sized for a spring rate of 1.75 MN/cm from this bearing to the casing."
              : "A roller bearing supporting the LP shaft just ahead of the PTO drive gear; it carries the LP speed pickup.",
    facts: [
      f("Type and role", `${b.type}, ${b.role}`, "CR-168219 sec 5.7.1–5.7.3 pp.96–99"),
      f("Sump", b.sump, "CR-168219 Fig.37 p.97"),
      f("Sealing", "labyrinth seals pressurised by fan discharge air", "CR-168219 sec 5.7"),
      ...(b.n === 5 ? [f("Strut spring rate", "1,751,181 N/cm (1e6 lbf/in)", "CR-168219 sec 5.6")] : []),
      ...(b.n === 3 ? [f("Squirrel cage and damper", "k = 52,540 kN/m; 5-sleeve squeeze-film damper, 1.27 mm radial clearance, r 137.5 mm", "CR-168219 sec 5.11.1 p.135, Fig.57 p.138")] : []),
      ...(b.n === 4 ? [f("Squirrel cage", "rotating, k = 52,540 kN/m, on the LP shaft", "CR-168219 sec 5.7.3 p.98, sec 5.11.2 p.137")] : []),
      ...(b.n === 2 ? [f("Speed pickup", "N1 from a cogged wheel and magnetic pickup on the No.2 housing", "CR-168219 sec 5.7.2 p.98")] : []),
      f("Axial position", "placed from the whole-engine section, not a table", "", ASM),
    ],
  })),
];

// ── Structure ─────────────────────────────────────────────────────────────

const structure = [
  {
    id: "inlet-cowl",
    name: "Inlet cowl and lip",
    system: "structure",
    y: -1.05,
    r: 1.15,
    build: () =>
      merge([
        // Inner: hilite, contracting to a throat about a quarter of the way
        // aft, then a long gentle diffusion to the fan face at NACELLE.rHilite.
        shell([[NACELLE.rHilite, NACELLE.yHilite], [1.005, NACELLE.yHilite + 0.35], [1.02, NACELLE.yHilite + 0.68], [1.045, NACELLE.yHilite + 1.08], [1.064, FS.fanLE - 0.14]], 0.012),
        // Outer: hilite up to the maximum-diameter station.
        shell([[NACELLE.rHilite, NACELLE.yHilite], [1.16, NACELLE.yHilite + 0.33], [1.215, NACELLE.yHilite + 0.68], [NACELLE.rMax, NACELLE.yMaxDia]], 0.012),
      ]),
    text: "The intake: a thick, rounded lip so the flow stays attached at high incidence on rotation and in crosswinds, contracting to a throat and then diffusing gently to the fan face. The lip is a D-shaped duct inside, which is the anti-ice heat exchanger. It is long — 1.59 m of it ahead of the fan — and that length is most of what makes a high-bypass engine look the way it does.",
    facts: [
      f("Inlet length, hilite to fan face", "1.590 m, or 0.75 fan diameters", "CR-159584 Table I p.6", "e3"),
      f("Highlight diameter", "2.141 m, giving D_HL/D_max = 0.86 — slender, against 0.83 on the CF6/DC-10", "CR-159584 p.6; CR-135444 p.249", "e3"),
      f("Lip and diffuser contour", "not dimensioned; drawn to the published hilite, throat ratio and fan-face radius", "", SCH),
    ],
  },
  {
    id: "fan-case",
    name: "Fan containment case",
    system: "structure",
    y: 0.05,
    r: 1.09,
    build: () => merge([shell([[1.09, -0.33], [1.09, 0.42]], 0.05), ring(1.064, 1.15, -0.34, -0.31), ring(1.064, 1.15, 0.4, 0.43)]),
    text: "The ring around the fan blade tips. It is thick for one reason: certification demands that if a fan blade releases at full speed, the case holds it. The E³ FPS wraps Kevlar over an aluminium liner; the ground demonstrator ran a borrowed CF6 steel case.",
    facts: [
      f("Construction", "Kevlar wrap on an aluminium liner (FPS); CF6 steel case on the ICLS", "CR-168219 sec 5.9 p.102; CR-165148 p.3"),
      f("Certification case", "fan blade-out: ≈746 kN, about 76 tonnes, 7.27 kg blade", "PF-09 unit E4; CR-165148 Table VI p.74"),
      f("Rule", "CS-E 810 / FAR 33.94 blade containment", "designer agent §certification"),
    ],
  },
  {
    id: "fan-frame",
    name: "Fan frame",
    system: "structure",
    y: FS.fanFrame,
    r: 0.8,
    build: () =>
      merge([
        struts(12, 0.34, 0.55, FS.fanFrame, 0.16, 0.03, 15),
        ring(1.064, 1.1, FS.bypassOgv - 0.12, FS.bypassOgv + 0.14),
        ring(ISLAND.rTop - 0.025, ISLAND.rTop, FS.bypassOgv - 0.06, FS.fanFrame + 0.16),
        // Hub: bearing support cone and the static core inner wall.
        shell([[0.19, 0.78], [0.3, 0.9], [0.34, FS.fanFrame], [0.3, 1.2], [0.18, 1.3]], 0.025),
        shell([[0.12, 0.85], [0.2, 0.78]], 0.02),
        shell([[0.12, 1.3], [0.16, 1.3], [0.17, HPC0 - 0.08]], 0.02),
      ]),
    text: "The main structural frame, and on the E³ a graphite-composite one with an aluminium hub: the 34 bypass OGVs are its struts through the fan stream, and struts through the core stream tie them to the hub that holds bearings 1, 2 and 3. All of the rotor thrust arrives here. The forward mount links hang off its aft face, and the radial drive to the gearbox runs down the thick 6 o'clock strut.",
    facts: [
      f("Construction", "integral graphite-composite frame, aluminium hub; the 34 OGVs are the struts", "CR-168219 sec 5.1.2 p.45, sec 5.9 p.102"),
      f("Core struts", "12", "not in a transcribed table", ASM),
      f("Carries", "bearings No.1 (LP thrust), No.2, No.3 (HP thrust) in the forward sump; the forward mounts", "CR-168219 sec 5.7.2 p.96, sec 5.9.2 p.110"),
      f("PTO", "radially out through the bottom front-frame strut", "CR-168219 sec 5.7"),
      f("Module mass", "fan and booster 1,103 kg, of which frame and stators 622 kg", "CR-168219 Table XXVI p.140"),
    ],
  },
  {
    id: "island",
    name: "Island (quarter-stage splitter body)",
    system: "structure",
    y: 0.55,
    r: 0.69,
    build: () =>
      lathe([
        [ISLAND.rUnder - 0.024, ISLAND.yLE],
        [ISLAND.rTop, ISLAND.yLE + 0.14],
        [ISLAND.rTop, ISLAND.yTE - 0.05],
        [ISLAND.rTop - 0.018, ISLAND.yTE],
        [ISLAND.rUnder, ISLAND.yTE - 0.04],
        [ISLAND.rUnder, ISLAND.yLE + 0.1],
        [ISLAND.rUnder - 0.024, ISLAND.yLE],
      ]),
    text: "The ring-shaped body that gives the quarter stage its name. Its leading edge splits the fan flow at 22.3 %: the bypass stream passes over it, and the island stator and booster rotor sit under it. It also throws foreign objects outward into the bypass, which is one of the reasons the E³ chose this arrangement over a taller single fan.",
    facts: [
      f("Flow under the island", "22.3 % of fan flow, 143.7 kg/s corrected", "CR-165148 summary p.3, Appendix A p.120"),
      f("Why", "core-stream efficiency, growth path, bypass efficiency at lower fan speed, FOD separation", "CR-165148 summary p.1–3"),
      f("Growth", "the island leading edge moves out 1.0 cm for the growth engine", "CR-165148 Fig.15"),
      f("Radii", "underside 0.669 m (booster tip); top 0.705 m", "CR-165148 Table IV; top assumed", ASM),
    ],
  },
  {
    id: "core-inlet-duct",
    name: "Second splitter and core inlet duct",
    system: "structure",
    y: 0.95,
    r: 0.55,
    build: () =>
      merge([
        // Outer wall of the core stream: the second splitter's lower surface
        // then the goose-neck down to the HPC inlet.
        shell([[ISLAND.rSplit2, ISLAND.ySplit2], [ISLAND.rSplit2 - 0.004, FS.innerOgv], [0.60, 0.74], [0.585, 0.86], [0.53, 1.0], [0.45, 1.2], [HPC_ROWS.IGV.LE.rTip + 0.018, HPC_ROWS.IGV.LE.yTip]], 0.014),
        // The splitter's upper surface, becoming the core cowl behind the island.
        shell([[ISLAND.rSplit2, ISLAND.ySplit2], [0.62, 0.66], [0.628, 0.84]], 0.012),
        // Inner wall from the drum exit to the fan-frame hub.
        shell([[ISLAND.rCoreHubAtOgv - 0.012, FS.innerOgv + 0.06], [0.44, 0.78], [0.37, 0.9], [0.35, 1.0]], 0.012),
      ]),
    text: "Behind the booster a second splitter divides its flow again: the inner 58 % turns inward down this goose-neck, from 0.61 m radius to the 0.36 m of the HPC inlet, past the core OGVs; the outer 42 % goes up and out to the bypass. The bleed doors open through the goose-neck's outer wall.",
    facts: [
      f("Core flow", "82.4 kg/s corrected of the 143.7 under the island", "CR-165148 Appendix A p.122"),
      f("Second splitter radius", "0.611 m, from the 58/42 area split", "", ASM),
      f("Axial run to the HPC", "fan axis → rotor 1 = 1.034 m, inside the 1.00–1.12 the corrected sheet allows", "atlas-facts.md A7", ASM),
      f("How it is fixed", "CR-159584 Table I fixes fan flange → LPT exit at 3.180 m, capping this offset and the diffuser/combustor one at 1.287 m together; the sum is the table's, the split is read off the same report's Fig.1", "CR-159584 Table I p.6", "e3"),
    ],
  },
  {
    id: "fan-duct-outer",
    name: "Bypass duct outer wall",
    system: "structure",
    y: 2.0,
    r: 1.02,
    // Held near-parallel to y = 2.0, where the annulus is 2.37 down to
      // 2.27 m2 and the duct Mach is inside the published 0.40-0.45,
      // then accelerating to 1.98 m2 at the mixer — CR-135444 gives a
      // preliminary mixing-plane Mach of 0.56, so the duct is supposed to
      // speed up here rather than arrive parallel. Aft of the mixer the
      // same wall is the tailpipe, converging to meet the nozzle.
      build: () => shell([[1.064, 0.43], [1.07, 1.0], [1.06, 1.3], [1.04, 2.0], [1.015, 2.6], [1.005, 2.95], [0.95, 3.4], [0.90, 3.82]], 0.015),
    text: "The outer wall of the bypass duct from the fan case to the nozzle. On a long-duct mixed-flow nacelle it runs the full length of the engine; on a separate-flow nacelle it would end a metre behind the fan. The thrust reverser, if fitted, lives in this wall.",
    facts: [f("Geometry", "long-duct, mixed-flow, as the E³ FPS", "CR-168219 sec 5.8", "e3")],
  },
  {
    id: "core-cowl",
    name: "Core cowl (bypass duct inner wall)",
    system: "structure",
    y: 2.3,
    r: 0.6,
    build: () => shell([[0.628, 0.84], [0.62, 1.3], [0.6, 1.75], [0.6, 2.35], [0.62, EXHAUST.yMixerStart]], 0.012),
    text: "The fairing over the core. Everything between it and the casings, the pipes, wires, pumps and valves on this page, is the core compartment: fire zone 2, ventilated by a trickle of bypass air.",
    facts: [f("Radius", "0.60 m along the core", "", ASM)],
  },
  {
    id: "nacelle-outer",
    name: "Fan cowl and nacelle skin",
    system: "structure",
    y: 2.0,
    r: 1.24,
    // From the maximum-diameter station aft. The real mid-body is close to
    // parallel: read off CR-159584 Fig. 1 the radius falls about 2 % over
    // the 2.3 m behind the maximum, so the near-cylindrical look is not the
    // error it appears to be. The boat-tail then leaves at the published
    // 11°, which now reaches the published exit because the core no longer
    // runs long.
    build: () => shell([[NACELLE.rMax, NACELLE.yMaxDia], [NACELLE.rMax, -0.30], [1.238, 0.6], [1.228, 1.5], [1.222, 2.16], [1.03, 3.15], [0.90, 3.82]], 0.01),
    text: "The outer aerodynamic skin. Between it and the bypass duct wall is the fan compartment, fire zone 1, where the gearbox and most of the accessories live. The cowl doors hinge from the pylon and open upward for line maintenance.",
    facts: [
      f("Maximum diameter", "2.489 m, reached 0.978 m aft of the hilite (X/D_max = 0.40)", "CR-159584 Table I p.6; CR-135444 p.249", "e3"),
      f("Overall length", "6.033 m, hilite to nozzle exit", "CR-159584 Table I p.6", "e3"),
      f("Terminal boat-tail", "11°", "CR-135444 p.249", "e3"),
      f("Mid-body", "close to parallel — about 2 % of radius over the 2.3 m behind the maximum", "CR-159584 Fig.1 p.7", SCH),
    ],
  },
  {
    id: "pylon",
    name: "Pylon and upper bifurcation",
    system: "structure",
    y: 2.2,
    r: 1.3,
    build: () =>
      merge([
        // The pylon box above the nacelle and the bifurcation fairing
        // through the bypass duct at 12 o'clock.
        unit(2.3, 1.24, 0, [0.22, 2.2, 0.26]),
        unit(2.35, 0.64, 0, [0.44, 2.3, 0.09]),
      ]),
    text: "The strut that hangs the engine off the wing, and its fairing through the top of the bypass duct. It carries fuel, hydraulics, bleed air, electrical power, the clearance-control air scoop and the fire bottles' lines down to the engine, and takes the thrust from the forward mount into the wing spar.",
    facts: [
      f("Shown", "as a stub; the aircraft side is not this model's subject", "", SCH),
      f("ICLS pylon", "aluminium forward, steel aft of the firewall, for the mixed-exhaust temperature", "CR-168211 p.118"),
    ],
  },
  {
    id: "fwd-mount",
    name: "Forward engine mount",
    system: "structure",
    y: FS.fanFrame,
    r: 1.15,
    clock: 0,
    build: () => {
      const g = ring(1.1, 1.26, FS.fanFrame - 0.08, FS.fanFrame + 0.08, 3);
      g.rotateY(Math.PI / 2 + Math.PI / 3);
      return g;
    },
    text: "The forward mount beam on the pylon, over the fan frame. On the E³ it takes vertical and side loads through two links and all of the thrust through two more links at ±45° from the top, so the thrust is reacted at two points 90° apart and the fan case is not pulled into an oval.",
    facts: [
      f("Links", "four, on brackets on the aft side of the fan frame under the core cowl; all seven engine links in uniballs", "CR-168219 sec 5.9.2 p.110, Figs.44–45 pp.112–113"),
      f("Load path", "vertical + side + thrust (via the whiffle tree)", "CR-168219 sec 5.9.2 p.110"),
    ],
  },
  {
    id: "aft-mount",
    name: "Aft engine mount",
    system: "structure",
    y: STATIONS.trf,
    r: 0.72,
    clock: 0,
    build: () => {
      const g = ring(0.66, 0.8, STATIONS.trf - 0.07, STATIONS.trf + 0.07, 3);
      g.rotateY(Math.PI / 2 + Math.PI / 3);
      return g;
    },
    text: "The aft mount on the turbine rear frame: three links, a short lateral one inside the pylon for roll and side load, and two streamlined vertical links that pass through the fan stream. On this engine the aft mount takes no thrust; that is all done at the fan frame.",
    facts: [
      f("Links", "three on the rear frame's mount lugs: one lateral inside the pylon, two vertical through the fan stream", "CR-168219 sec 5.9.2 p.110"),
      f("Load path", "vertical + roll + side; no thrust", "CR-168219 sec 5.9.2 p.110"),
    ],
  },
  {
    id: "thrust-links",
    name: "Forward mount links and whiffle tree",
    system: "structure",
    y: FS.fanFrame + 0.15,
    r: 0.85,
    clock: 0,
    build: () =>
      merge([
        // Two thrust links at ±45° from the top, meeting at the whiffle tree.
        pipe([[FS.fanFrame + 0.08, 0.68, 45], [FS.fanFrame + 0.22, 1.02, 4]], 0.028, 6),
        pipe([[FS.fanFrame + 0.08, 0.68, -45], [FS.fanFrame + 0.22, 1.02, -4]], 0.028, 6),
        unit(FS.fanFrame + 0.22, 1.0, 0, [0.1, 0.12, 0.26]),
        // Two vertical/side links.
        pipe([[FS.fanFrame + 0.06, 0.68, 14], [FS.fanFrame + 0.1, 1.04, 8]], 0.022, 4),
        pipe([[FS.fanFrame + 0.06, 0.68, -14], [FS.fanFrame + 0.1, 1.04, -8]], 0.022, 4),
      ]),
    text: "Four links on the aft face of the fan frame. Two carry vertical and side load straight up to the pylon; two more at ±45° carry the engine's thrust, 173 kN at takeoff, into a pivoting whiffle tree so it is reacted at two points ninety degrees apart. Sharing the thrust between two points is what keeps the fan case round, and the fan case being round is what keeps the fan tip clearance even.",
    facts: [
      f("Thrust links", "two, at ±45° from top, through a pivoting whiffle tree", "CR-168219 sec 5.9.2 p.110, Figs.44–45"),
      f("Takeoff thrust", "173.5 kN (39,000 lbf)", "CR-168219 sec 4.3 p.32"),
    ],
  },
  {
    id: "trf",
    name: "Turbine rear frame",
    system: "structure",
    y: STATIONS.trf,
    r: 0.5,
    build: () =>
      merge([
        struts(12, 0.31, 0.63, STATIONS.trf, 0.12, 0.03, 15),
        ring(0.62, 0.66, STATIONS.trf - 0.08, STATIONS.trf + 0.08),
        shell([[0.31, STATIONS.trf - 0.08], [0.31, STATIONS.trf + 0.08]], 0.015),
        shell([[0.3, STATIONS.trf - 0.06], [0.2, STATIONS.trf - 0.02], [0.13, STATIONS.trf]], 0.02),
      ]),
    text: "The last frame: radial struts through the exhaust gas that carry the No. 5 bearing, the aft mount, the mixer and the centrebody. The struts were made radial rather than semi-tangential because that gave the required spring rate for the bearing with less length and mass.",
    facts: [
      f("Struts", "12, radial, cambered to remove the residual LPT swirl; there is no separate exit guide vane row", "CR-168219 sec 5.6 pp.90–95, Fig.36"),
      f("Spring rate", "1,751,181 N/cm from the No.5 bearing to the casing", "CR-168219 sec 5.6"),
      f("Supports", "centrebody, mixer, No.5 bearing housing, three aft mount lugs", "CR-168219 sec 5.6"),
      f("Material and mass", "Inco 718; frame + mixer + centrebody 221 kg", "CR-168219 sec 5.6 p.95, Table XXVI p.140"),
      f("Acoustic treatment", "Astroquartz panels under a 30 %-open perforated shear cylinder", "CR-168219 sec 5.6"),
    ],
  },
  // Flanges with their bolts.
  ...[
    { id: "f1", name: "Inlet cowl to fan case", y: -0.33, r: 1.15, n: 40 },
    { id: "f2", name: "Fan case to fan frame", y: 0.43, r: 1.15, n: 48 },
    { id: "f3", name: "Fan frame to HPC front case", y: HPC_ROWS.IGV.LE.yTip - 0.02, r: HPC_ROWS.IGV.LE.rTip + 0.06, n: 36 },
    { id: "f4", name: "HPC front case to rear case", y: HPC_ROWS.S5.TE.yTip + 0.01, r: HPC_ROWS.S5.TE.rTip + 0.06, n: 40 },
    { id: "f5", name: "HPC rear case to compressor rear frame", y: yDiff0 - 0.005, r: HPC_ROWS.S10.TE.rTip + 0.06, n: 40 },
    { id: "f6", name: "Combustor case to HPT case", y: HPT0 - 0.02, r: 0.5, n: 48 },
    { id: "f7", name: "HPT case to LPT case", y: HPT0 + 0.225, r: 0.455, n: 132, e3: "132 × 5/16-in bolts, sized to contain the LPT rotor axially on a shaft failure — LPT report sec 4.3.4 p.133" },
    { id: "f8", name: "LPT case to turbine rear frame", y: STATIONS.trf - 0.09, r: 0.685, n: 120, e3: "120 bolts — LPT report sec 4.3.4" },
    { id: "f9", name: "Turbine rear frame to mixer", y: STATIONS.trf + 0.09, r: 0.685, n: 40 },
  ].map((fl) => ({
    id: `flange-${fl.id}`,
    name: `Flange: ${fl.name}`,
    system: "structure",
    y: fl.y,
    r: fl.r,
    build: () => {
      const head = Math.min(0.022, ((2 * Math.PI * fl.r) / fl.n) * 0.32);
      return merge([ring(fl.r - 0.045, fl.r + 0.004, fl.y - 0.012, fl.y + 0.012), boltRing(fl.n, fl.r - 0.018, fl.y + 0.012, head, head * 0.7, 0.03)]);
    },
    text: `The bolted joint ${fl.name.toLowerCase()}. Casing flanges are where an engine is built and where it comes apart in the shop: each carries a ring of close-tolerance bolts that also locate the two casings concentrically, which is what sets the tip clearance across the joint.`,
    facts: [
      fl.e3 ? f("Bolt count", `${fl.n}`, fl.e3) : f("Bolt count", `${fl.n}`, "not in a transcribed table", ASM),
      f("Function", "pressure boundary, load path, concentricity", "Rolls-Royce, The Jet Engine", "textbook"),
    ],
  })),
];

// ── Exhaust ───────────────────────────────────────────────────────────────

const exhaust = [
  {
    id: "mixer",
    name: "Forced mixer (18 lobes)",
    system: "exhaust",
    y: (EXHAUST.yMixerStart + EXHAUST.yMixerEnd) / 2,
    r: 0.66,
    build: () => mixer(EXHAUST.mixerLobes, EXHAUST.yMixerStart, EXHAUST.yMixerEnd, 0.63, 0.7, 0.14),
    text: "The scalloped crown where the hot core stream and the cool bypass stream meet. Eighteen lobes fold the two streams into each other so they mix in a short length; the mixed jet leaves slower and cooler than the core alone, which is more thrust per fuel and less noise.",
    facts: [
      f("Lobes", "18, scalloped, Inco 718", "CR-168219 sec 5.8 p.102, Fig.39"),
      f("What it buys", "≈2.9 % sfc at 85 % mixing effectiveness for 0.57 % pressure loss", "CR-168219 Table XXIII p.104"),
      f("As tested", "the ICLS mixer beat its model by 5–8 %", "CR-168211 pp.3, 622"),
      f("Lobe shape", "undimensioned drawing; depth here is representative", "", SCH),
    ],
  },
  {
    id: "centrebody",
    name: "Exhaust centrebody (plug)",
    system: "exhaust",
    y: 3.9,
    r: 0.2,
    build: () => lathe([[0.31, STATIONS.trf + 0.08], [0.3, STATIONS.trf + 0.3], [0.24, STATIONS.trf + 0.55], [0.14, STATIONS.trf + 0.8], [0.04, STATIONS.trf + 0.95], [0, STATIONS.trf + 0.98]]),
    text: "The tail cone, with corrugations matching the mixer lobes. It closes the inner wall of the core stream smoothly to a point so the exhaust does not separate off a blunt hub. Through its tip runs the centre vent tube that breathes both sumps and the gearbox.",
    facts: [
      f("Material", "Inco 625, linked to the mixer", "CR-168219 sec 5.8 p.102"),
      f("Supported by", "the turbine rear frame", "CR-168219 sec 5.6"),
    ],
  },
  {
    id: "nozzle",
    name: "Common C-D nozzle",
    system: "exhaust",
    y: 4.2,
    r: 0.9,
    build: () =>
      merge([
        // Flow path: convergent to a throat just inside the lip, then the
        // small divergence, leaving at the published exit radius.
        shell([[0.88, 3.82], [0.80, 4.10], [0.786, 4.19], [NACELLE.rNozzleExit, EXHAUST.yNozzleExit]], 0.015),
        // Skin, carrying the boat-tail through to the exit at the same 11°.
        shell([[0.90, 3.82], [0.86, 4.03], [0.815, EXHAUST.yNozzleExit]], 0.01),
      ]),
    text: "One nozzle for both streams: convergent to a throat, then a slight divergence. At cruise the nozzle pressure ratio is high enough that the throat chokes and a C-D shape recovers some of the expansion a plain convergent nozzle would leave on the table.",
    facts: [
      f("Type", "single convergent-divergent, low area ratio, C_v 0.996", "CR-168219 sec 5.8 pp.101–102; Table XI p.34"),
      f("Exit diameter", "1.590 m — and continuity on the published cycle puts the choked throat at 1.586, which is 0.3 % from a number printed in 1979", "CR-159584 Table I p.6", "e3"),
      f("Fan duct Mach", "0.40–0.45", "CR-168219 sec 5.8 p.101"),
      f("Throat station", "not dimensioned; placed just inside the exit for the published low area ratio", "", SCH),
    ],
  },
];

export const CORE_PARTS = [
  ...fanModule,
  ...hpcRows,
  ...hpcRotorStructure,
  ...combustor,
  ...hpt,
  ...lpt,
  ...shafts,
  ...structure,
  ...exhaust,
];
