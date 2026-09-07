/**
 * The twelve systems a turbofan is taught as, plus the rotating hardware
 * they hang off. Order is the order the user asked for; colours are one
 * muted hue per system so a reader can tell fuel from oil from air at a
 * glance, in both themes, without any of them shouting louder than the
 * site's single orange accent, which is reserved for the selection.
 */
export const SYSTEMS = [
  {
    id: "gas-generator",
    n: 1,
    name: "Gas generator",
    short: "Thermodynamic unit",
    blurb:
      "Compressor, combustor and turbine: the core that turns fuel into shaft power. On a high-bypass turbofan the fan and booster on the LP spool, and the 10-stage HPC, combustor and 2-stage HPT on the HP spool, plus the 5-stage LPT that drives the fan. Everything else on this page exists to feed, control, cool, lubricate, light, protect or hold this.",
    color: { dark: "#e0b76e", light: "#c99a45" },
  },
  {
    id: "fuel",
    n: 2,
    name: "Fuel system",
    short: "Pump, meter, inject",
    blurb:
      "Takes fuel from the aircraft at low pressure, raises it to injection pressure, meters exactly what the control commands, and delivers it through a manifold to thirty nozzles. The same fuel is used as a coolant for the oil and as hydraulic fluid for the actuators before it is burned.",
    color: { dark: "#f2c14e", light: "#d9a52a" },
  },
  {
    id: "control",
    n: 3,
    name: "Control system",
    short: "FADEC and sensors",
    blurb:
      "The full-authority digital engine control reads pressures, temperatures and speeds around the engine, compares them with the thrust the pilot asked for, and drives the fuel metering valve, the variable stators, the bleed valves and the clearance control. Two channels, each able to run the engine alone.",
    color: { dark: "#7fc0f0", light: "#3d8ed0" },
  },
  {
    id: "air",
    n: 4,
    name: "Air system",
    short: "Bleed, cooling, seals",
    blurb:
      "Compressor air that never reaches the combustor: taken from the fan and the HPC to cool the turbine, pressurise the bearing sumps, balance the rotor thrust, control tip clearances, start the engine and supply the aircraft. On the E³ about 14 % of core flow is extracted for cooling and purge alone.",
    color: { dark: "#5fd3cb", light: "#22a49b" },
  },
  {
    id: "oil",
    n: 5,
    name: "Oil system",
    short: "Lubricate, cool, scavenge",
    blurb:
      "A closed loop that feeds oil to five bearings and the gearbox, scavenges it back out of two sumps, cools it against the fuel, filters it and watches it for metal. The sumps are sealed by labyrinths held shut with fan air, so the air system and the oil system meet at every bearing.",
    color: { dark: "#d6c24a", light: "#b09a1e" },
  },
  {
    id: "ignition",
    n: 6,
    name: "Ignition system",
    short: "Exciters and igniters",
    blurb:
      "Two independent high-energy exciters, each firing its own igniter plug through the combustor casing into the dome. Used for ground start, in-flight relight, and continuously in icing, heavy rain or turbulence. Once lit, the flame is self-sustaining and the igniters are switched off.",
    color: { dark: "#ff9d7d", light: "#e0623c" },
  },
  {
    id: "variable-geometry",
    n: 7,
    name: "Variable geometry",
    short: "VSV, VBV, clearance",
    blurb:
      "The parts of the engine that move without rotating: the variable stator vanes that re-stagger the front HPC rows so the compressor does not stall at low speed, the bleed doors that dump booster air at idle, and the actuators and unison rings that drive them.",
    color: { dark: "#bfa2f0", light: "#8a63d6" },
  },
  {
    id: "anti-ice",
    n: 8,
    name: "Anti-icing",
    short: "Hot air to the lip",
    blurb:
      "Hot HPC bleed air piped forward to the inlet lip so ice never forms where it could shed into the fan. The spinner and fan blades are self-shedding by shape and flex; the probes that the control depends on are electrically heated.",
    color: { dark: "#b6dbff", light: "#5a9bd8" },
  },
  {
    id: "fire",
    n: 9,
    name: "Fire detection",
    short: "Loops and bottles",
    blurb:
      "Two fire zones, fan and core, each watched by a pair of continuous-element detector loops. A fire is declared only when both loops agree, and is fought by closing the fuel, hydraulic and bleed shut-offs and discharging the extinguisher bottles from the pylon into the zone.",
    color: { dark: "#ff6b63", light: "#d8322b" },
  },
  {
    id: "vibration",
    n: 10,
    name: "Vibration monitoring",
    short: "Accelerometers, tracking",
    blurb:
      "Accelerometers on the fan frame and the turbine rear frame, read against the N1 and N2 speed signals so the monitoring unit can tell fan imbalance from turbine imbalance by which order the vibration follows. The same signals are used to compute the trim-balance weights.",
    color: { dark: "#bfe07a", light: "#7fb02a" },
  },
  {
    id: "exhaust",
    n: 11,
    name: "Exhaust system",
    short: "Mixer and nozzle",
    blurb:
      "The E³ is a mixed-flow turbofan: the core and bypass streams meet at an 18-lobe forced mixer inside a long-duct nacelle and leave through one convergent-divergent nozzle. Mixing raises thrust for the same fuel and lowers jet noise; the lobes trade some pressure loss for that.",
    color: { dark: "#b1a6c9", light: "#8d7fb0" },
  },
  {
    id: "structure",
    n: 12,
    name: "Structure and mounts",
    short: "Frames, casings, pylon",
    blurb:
      "Two frames carry the rotors: the fan frame at the front and the turbine rear frame at the back, joined by the casings between them. The engine hangs from the pylon at a forward mount on the fan frame and an aft mount on the rear frame, with thrust links taking the thrust into the aft mount. The fan case must also contain a released blade.",
    color: { dark: "#b4ada0", light: "#8f8879" },
  },
];

export const SYSTEM_BY_ID = Object.fromEntries(SYSTEMS.map((s) => [s.id, s]));

/**
 * Presets: which layers to show. "Gas generator" is the reader's first
 * question; "externals" is what a line mechanic sees with the cowls open.
 */
export const PRESETS = [
  { id: "all", name: "Everything", systems: SYSTEMS.map((s) => s.id) },
  { id: "core", name: "Gas generator", systems: ["gas-generator"] },
  { id: "core-structure", name: "Core and structure", systems: ["gas-generator", "structure", "exhaust"] },
  {
    id: "externals",
    name: "Externals only",
    systems: ["fuel", "control", "air", "oil", "ignition", "variable-geometry", "anti-ice", "fire", "vibration"],
  },
  { id: "fluids", name: "Fuel, oil and air", systems: ["fuel", "oil", "air"] },
];

/** Provenance tags printed next to every number. */
export const TAGS = {
  e3: { label: "E³", title: "Transcribed from a NASA/GE Energy Efficient Engine report, page cited" },
  schematic: { label: "schematic", title: "Generic large-turbofan practice drawn for teaching; not from an E³ table" },
  textbook: { label: "textbook", title: "From a named textbook" },
  assumed: { label: "assumed", title: "A number this model had to choose; stated so it can be corrected" },
};
