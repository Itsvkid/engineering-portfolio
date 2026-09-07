import { blob, doorRing, drum, hoop, lathe, merge, pipe, probeRing, ring, shell, unit } from "./geometry";
import { COMBUSTOR, EXHAUST, FAN_STATIONS as FS, HPC0, HPC_ROWS, HPT0, HPT_STATIONS as HT, LPT0, LPT_ROWS, STATIONS } from "./flowpath";

/**
 * The externals: eleven of the twelve systems, drawn as the line-replaceable
 * units, pipes, wires, valves and probes a mechanic sees with the cowls open.
 *
 * Positions are [axial y, radius r, clock] in the engine frame, clock seen
 * from the front with the pylon at 12. Where an E³ report places a unit
 * (the oil tank on the outer fan case, the gearbox in the core compartment,
 * igniters at 120° and 240°) it is placed there and tagged `e3`; where the
 * reports are silent (anti-ice ducting, fire loops, the flight exciter) the
 * layout is generic large-turbofan practice and tagged `schematic`.
 */

const E3 = "e3";
const SCH = "schematic";
const TB = "textbook";
const f = (k, v, src, tag = E3) => ({ k, v, src, tag });

// Frequently used stations.
const R_FANCASE = 1.12; // outside of the fan containment case
const R_CORE_OUT = 0.5; // a typical radius for a pipe run along the core casings
const Y_S5 = HPC0 + 0.475; // stage-5 bleed port (z ≈ 47.5 cm)
const Y_S7 = HPC0 + 0.603; // stage-7 bleed port (z ≈ 60.3 cm)
const Y_AGB = FS.fanFrame + 0.35; // accessory gearbox centre, core compartment
const R_AGB = 0.42;
const Y_DOME = COMBUSTOR.yDome;

// ── Accessory drive (shared by fuel, oil, control) ────────────────────────

const drives = [
  {
    id: "agb",
    name: "Accessory gearbox",
    system: "oil",
    y: Y_AGB,
    r: R_AGB + 0.1,
    clock: 180,
    build: () =>
      merge([
        unit(Y_AGB, R_AGB, 180, [0.16, 0.7, 0.9]),
        // Drive pads along the aft face.
        drum(Y_AGB + 0.4, R_AGB + 0.02, 160, 0.06, 0.1),
        drum(Y_AGB + 0.4, R_AGB + 0.02, 200, 0.06, 0.1),
      ]),
    text: "The gearbox under the core, driven by a radial shaft from the HP spool, that turns the fuel pump, the oil pumps, the control alternator, the hydraulic pumps and the aircraft generator, and that the air starter turns to spin the core for a start. The E³ put it in the core compartment rather than on the fan case because it weighed nothing extra there.",
    facts: [
      f("Location", "core-compartment mounted, chosen over fan-case (+34 kg) and pylon (+22.7 kg)", "CR-168219 sec 5.9.3 p.114, Tables XXIV–XXV pp.115–116"),
      f("Drive", "radial drive of two splined shafts with a mid-span bearing from the PTO on the HP stub shaft", "CR-168219 sec 5.9.3 p.114"),
      f("Pads", "lube & scavenge pump, air starter(s), control alternator, VSCF generator, hydraulic pumps, fuel pump & control", "CR-168219 Fig.46 p.117"),
      f("ICLS accessory power", "53.69 kW; max starter torque 1,084.6 N·m", "CR-168211 p.132"),
    ],
  },
  {
    id: "radial-drive",
    name: "Radial drive shaft",
    system: "oil",
    y: FS.fanFrame,
    r: 0.3,
    clock: 180,
    build: () =>
      merge([
        pipe([[FS.fanFrame, 0.19, 180], [FS.fanFrame, 0.36, 180], [FS.fanFrame + 0.02, 0.56, 180], [Y_AGB - 0.1, R_AGB, 180]], 0.03, 16),
        drum(FS.fanFrame + 0.03, 0.56, 180, 0.05, 0.08),
      ]),
    text: "The shaft that brings power out of the engine. A bevel gear on the HP stub shaft in the forward sump drives it, and it runs radially down through the thick 6 o'clock strut of the fan frame to the gearbox. When the starter turns, power flows the other way.",
    facts: [
      f("Path", "PTO from the compressor stub shaft, radially out through the bottom front-frame strut", "CR-168219 sec 5.7.2 p.96"),
      f("Construction", "two splined shafts with a mid-span bearing", "CR-168219 sec 5.9.3 p.114"),
    ],
  },
  {
    id: "starter",
    name: "Air turbine starter",
    system: "control",
    y: Y_AGB + 0.45,
    r: R_AGB + 0.02,
    clock: 200,
    build: () => merge([drum(Y_AGB + 0.5, R_AGB + 0.02, 205, 0.09, 0.22), pipe([[Y_AGB + 0.62, R_AGB + 0.12, 205], [Y_AGB + 0.8, 0.56, 215], [2.6, 0.57, 215]], 0.03, 24)]),
    text: "A small air turbine on the gearbox, fed with bleed air from the APU or another engine through the starter valve, that spins the HP spool up to light-off speed. The E³ was designed with two of the biggest starters available for a 60-second start; testing showed one was enough.",
    facts: [
      f("Unit", "Hamilton Standard PS600-3, two fitted for a 60-s start; the second deleted from the FPS", "CR-168017 sec 5.2 p.37; CR-168219 sec 4.6 p.36, sec 3.1 p.10"),
      f("As tested", "ICLS start in 44 s with no start bleed", "CR-168211 p.1"),
    ],
  },
];

// ── Fuel system ───────────────────────────────────────────────────────────

const fuel = [
  {
    id: "fuel-pump",
    name: "Main fuel pump and filter",
    system: "fuel",
    y: Y_AGB - 0.1,
    r: R_AGB + 0.16,
    clock: 150,
    build: () => merge([drum(Y_AGB - 0.15, R_AGB + 0.16, 150, 0.08, 0.26), drum(Y_AGB + 0.12, R_AGB + 0.2, 145, 0.045, 0.14)]),
    text: "The engine-driven pump on the gearbox: a centrifugal boost stage so the vane element never cavitates, then a positive-displacement vane element that delivers far more than the engine burns. The surplus is what powers every fuel-operated actuator and is then bypassed back to the inlet.",
    facts: [
      f("Type", "positive-displacement vane element with integral centrifugal boost; pump-mounted filter", "CR-168219 sec 5.10.2 p.125, Fig.46 p.117; CR-168017 sec 5.1 p.12"),
      f("Fuel flow", "≈2,600 kg/h at takeoff, ≈300 kg/h at idle", "CR-168301 Fig.27 p.51 (read off)"),
      f("Inlet limit", "408 K for coking", "CR-168301 sec 5.4.1.4 p.104"),
    ],
  },
  {
    id: "fuel-control",
    name: "Fuel control (metering unit)",
    system: "fuel",
    y: Y_AGB + 0.2,
    r: R_AGB + 0.16,
    clock: 150,
    build: () => unit(Y_AGB + 0.22, R_AGB + 0.12, 152, [0.2, 0.3, 0.26]),
    text: "Bolted to the end of the pump: the metering valve that the FADEC positions, the bypass valve that returns the pump's surplus, a mechanical overspeed governor that can cut fuel with no electronics at all, the shutoff valve and the pressurising valve. On the demonstrator a hydromechanical backup computer could take over from the FADEC.",
    facts: [
      f("Contents", "metering valve, bypass valve, core-overspeed governor, shutoff, pressurising valve; RVPT position feedback", "CR-168219 sec 5.10.2 p.125, Fig.52 p.127; CR-168017 sec 11.4.2 p.103"),
      f("Backup", "transfer valves switch fuel and stator control to a hydromechanical computer", "CR-168017 sec 4 p.11, sec 10.1 p.68"),
    ],
  },
  {
    id: "fuel-oil-cooler",
    name: "Fuel/oil heat exchanger",
    system: "fuel",
    y: Y_AGB + 0.55,
    r: 0.58,
    clock: 135,
    build: () => merge([drum(Y_AGB + 0.55, 0.52, 135, 0.07, 0.3, true), pipe([[Y_AGB + 0.4, R_AGB + 0.2, 150], [Y_AGB + 0.5, 0.55, 140]], 0.02, 12)]),
    text: "Oil on one side, fuel on the other. It cools the oil, which is the point, and warms the fuel, which is a bonus that keeps ice out of the fuel filter. Every drop of fuel burned passes through it on its way to the combustor.",
    facts: [f("Location", "in the fuel line downstream of the shutoff valve, outside the fan duct", "CR-168219 Fig.52 p.127; CR-168017 Fig.5 p.13")],
  },
  {
    id: "fuel-supply-line",
    name: "Fuel supply line",
    system: "fuel",
    y: 2.0,
    r: 0.5,
    clock: 130,
    build: () =>
      merge([
        // From the pylon interface down to the pump, then aft along the core.
        pipe([[FS.fanFrame + 0.3, 1.2, 0], [FS.fanFrame + 0.3, 0.9, 60], [Y_AGB - 0.25, 0.62, 120], [Y_AGB - 0.25, R_AGB + 0.16, 150]], 0.022, 40),
        pipe([[Y_AGB + 0.7, 0.55, 135], [2.05, 0.5, 130], [Y_DOME - 0.02, 0.5, 130]], 0.022, 40),
      ]),
    text: "Fuel arrives from the wing tank through the pylon at low pressure, drops to the pump, and after metering and the heat exchanger runs aft along the core to the manifolds at the combustor. Double-walled and shrouded on a real installation, so a leak drains overboard rather than into the fire zone.",
    facts: [f("Routing", "generic; the E³ reports give the circuit, not the pipe runs", "CR-168017 Fig.5 p.13", SCH)],
  },
  {
    id: "fuel-split-valves",
    name: "Main-zone shutoff and pilot reset valves",
    system: "fuel",
    y: 2.1,
    r: 0.52,
    clock: 120,
    build: () => merge([unit(2.1, 0.5, 118, [0.09, 0.14, 0.1]), unit(2.28, 0.5, 125, [0.08, 0.12, 0.09])]),
    text: "The valves that make a double-annular combustor work: the main-zone shutoff valve keeps the inner dome dry at start and idle, and opens it at about 80 % core speed; the pilot reset valve trims the pilot's share. Servo-operated, positioned by the FADEC.",
    facts: [
      f("MZSOV / PZRV", "servo-operated; MZSOV inside the fan duct on the core, PZRV outside", "CR-168219 sec 5.10.2 p.128; CR-168017 Fig.5 p.13"),
      f("Split", "pilot ≈40 % of fuel at high power; pilot only below ~80 % N2", "CR-168301 Fig.27 p.51; CR-168219 sec 5.10.2"),
    ],
  },
  {
    id: "fuel-manifolds",
    name: "Fuel manifolds (pilot and main)",
    system: "fuel",
    y: Y_DOME,
    r: 0.52,
    build: () => merge([hoop(0.505, 0.014, Y_DOME - 0.02), hoop(0.505, 0.014, Y_DOME + 0.03)]),
    text: "Two stainless rings around the combustor casing, one for each dome, with a pigtail to every nozzle. Two manifolds rather than one is the price of staged combustion; the reward is a combustor that is clean at idle and clean at takeoff.",
    facts: [f("Arrangement", "two independent manifolds, pilot and main, with pigtails; stainless steel", "CR-168301 sec 5.3.2 pp.74–80")],
  },
  {
    id: "fuel-nozzles",
    name: "Fuel nozzles (30)",
    system: "fuel",
    y: Y_DOME,
    r: 0.44,
    build: () =>
      merge([
        probeRing(30, 0.49, COMBUSTOR.rLinerInner + 0.03, Y_DOME + 0.005, 0.014, 6),
        // Pigtails from each manifold to each stem.
        ...Array.from({ length: 30 }, (_, i) => {
          const c = (i / 30) * 360 + 6;
          return merge([pipe([[Y_DOME - 0.02, 0.505, c], [Y_DOME - 0.01, 0.5, c + 2], [Y_DOME, 0.49, c]], 0.007, 6), pipe([[Y_DOME + 0.03, 0.505, c], [Y_DOME + 0.015, 0.5, c - 2], [Y_DOME, 0.49, c]], 0.007, 6)]);
        }),
      ]),
    text: "Thirty stems through the casing, each with two tips, one for the pilot cup and one for the main cup behind it, each tip a duplex nozzle with primary and secondary orifices. The stem is stainless, the tips Hastelloy X, and the valves above the flange are cooled by fan air so the fuel inside never cokes.",
    facts: [
      f("Count and type", "30 single-stem dual-tip duplex nozzles", "CR-168219 sec 5.3.2 p.61; CR-168301 sec 4.2.3 pp.21–23"),
      f("Materials", "347 SS body, 321 SS tubes, Hastelloy X tips", "CR-168301 Fig.29"),
      f("Limits", "first flex 750 Hz; max ΔP 3,102 kPa", "CR-168301 Table XX p.129"),
    ],
  },
  {
    id: "fuel-heater",
    name: "Fuel heater (aircraft interface)",
    system: "fuel",
    y: FS.fanFrame + 0.4,
    r: 1.22,
    clock: 0,
    build: () => unit(FS.fanFrame + 0.45, 1.22, 12, [0.1, 0.2, 0.16]),
    text: "On the E³ the fuel is warmed at the pylon by heat taken from the aircraft's environmental-control bleed air through a water-glycol loop, with a bypass valve the FADEC controls. It is there to keep ice out of the fuel, not to help combustion.",
    facts: [f("Arrangement", "ECS-air to fuel via a water/antifreeze loop; bypass valve from the FADEC", "CR-168219 sec 5.10.5 p.133, Fig.55 p.134")],
  },
];

// ── Control system ────────────────────────────────────────────────────────

const control = [
  {
    id: "fadec",
    name: "FADEC (engine control unit)",
    system: "control",
    y: 0.45,
    r: R_FANCASE,
    clock: 60,
    build: () => merge([unit(0.45, R_FANCASE + 0.01, 60, [0.09, 0.44, 0.34]), unit(0.45, R_FANCASE + 0.1, 60, [0.03, 0.44, 0.34])]),
    text: "The full-authority digital engine control: one of the first on a large transport engine. A microprocessor reads every sensor about a hundred times a second, sets fuel to hold the corrected fan speed the thrust lever asks for, and drives the stators, the bleed and the three clearance-control loops. Powered by its own alternator, cooled by fuel through its chassis plate, and backed by a second unit.",
    facts: [
      f("Hardware", "single time-shared microprocessor, 3.5 MHz clock, ≈10 ms cycle; alumina/tungsten ceramic boards on a fuel-cooled aluminium plate", "CR-168219 sec 5.10.1 pp.118–124, Fig.50 p.124"),
      f("Redundancy", "primary + active standby; control alternator power, 28 V DC aircraft backup", "CR-168219 sec 5.10.1 p.120, sec 5.10.6 p.135"),
      f("Thrust setting", "corrected fan speed, best of 14 candidate parameters", "CR-168219 sec 5.10.1"),
      f("Sensor accommodation", "FICA: engine model + extended Kalman filter substitutes for failed sensors", "CR-168219 sec 5.10.1 p.120"),
      f("Location", "on the fan case on the ICLS (65 h, no problems); FPS not stated", "CR-168219 sec 5.10.6"),
      f("As tested", "stators tracked ±0.5° in fast transients; flight idle to 90 % thrust in ≈5.5 s", "CR-168219 sec 5.10.6 pp.133–135"),
    ],
  },
  {
    id: "control-alternator",
    name: "Control alternator",
    system: "control",
    y: Y_AGB - 0.2,
    r: R_AGB + 0.16,
    clock: 215,
    build: () => drum(Y_AGB - 0.2, R_AGB + 0.16, 215, 0.06, 0.16),
    text: "A small permanent-magnet generator on the gearbox that powers the FADEC as long as the core is turning, so the control never depends on the aircraft's electrical system. Its frequency is also the N2 speed signal.",
    facts: [f("Role", "primary FADEC power; N2 read from its frequency", "CR-168219 sec 5.10.1 p.120, Fig.46 p.117")],
  },
  {
    id: "harness",
    name: "Electrical harness",
    system: "control",
    y: 1.6,
    r: 0.55,
    clock: 60,
    build: () =>
      merge([
        // Fan case run: FADEC to the pylon connector and forward to T12.
        pipe([[0.45, R_FANCASE + 0.02, 60], [0.7, R_FANCASE + 0.02, 30], [FS.fanFrame + 0.2, 1.2, 8]], 0.014, 24),
        pipe([[0.45, R_FANCASE + 0.02, 60], [0.0, R_FANCASE + 0.02, 62], [-0.45, 1.16, 65]], 0.012, 20),
        // Down the fan frame strut to the core, then aft along the core at ~2 o'clock.
        pipe([[0.55, R_FANCASE + 0.02, 60], [FS.bypassOgv, 1.0, 62], [FS.bypassOgv, 0.7, 62], [FS.fanFrame + 0.3, 0.6, 60], [2.0, 0.53, 60], [HPT0 + 0.1, 0.5, 60], [LPT0 + 0.5, 0.62, 60]], 0.014, 64),
        // Branch to the gearbox side.
        pipe([[FS.fanFrame + 0.3, 0.6, 60], [FS.fanFrame + 0.35, 0.6, 120], [Y_AGB, R_AGB + 0.2, 150]], 0.012, 24),
      ]),
    text: "The wiring: every sensor and every servovalve on the engine talks to the FADEC through it. Shielded, twisted, run in two separate looms for the two control channels so that one damaged loom leaves the other channel whole, and clipped every few centimetres so vibration cannot chafe it.",
    facts: [f("Layout", "generic; the reports give the signal list, not the loom", "CR-168219 Fig.48 p.121", SCH)],
  },
  {
    id: "t12-probe",
    name: "T12 inlet temperature sensor",
    system: "control",
    y: -0.45,
    r: 1.0,
    clock: 65,
    build: () => merge([probeRing(1, 1.07, 0.93, -0.45, 0.012, 65), blob(-0.45, 1.09, 65, 0.03)]),
    text: "A resistance thermometer in the inlet ahead of the fan. Every corrected speed and every limit the FADEC applies is corrected by this one temperature, which is why it is heated against icing and why the FADEC can synthesise it if it fails.",
    facts: [f("Type", "RTD in the inlet duct, an F101 part", "CR-168219 sec 5.10.1 p.120, Fig.48 p.121")],
  },
  {
    id: "n1-sensor",
    name: "N1 speed sensor",
    system: "control",
    y: 0.9,
    r: 0.2,
    clock: 200,
    build: () => merge([probeRing(1, 0.3, 0.13, 0.9, 0.012, 200), ring(0.1, 0.13, 0.885, 0.915, 6)]),
    text: "A magnetic pickup reading a six-tooth wheel on the fan shaft just ahead of the No. 2 bearing. Fan speed is the thrust-setting parameter on this engine, and it is also what the vibration monitor uses to track the fan's once-per-rev.",
    facts: [f("Type", "magnetic pickup on a 6-tooth wheel; cogged wheel on the No.2 housing", "CR-168219 sec 5.7.2 p.98, sec 5.10.1 p.120")],
  },
  {
    id: "t25-p25",
    name: "T25 / P25 core inlet sensors",
    system: "control",
    y: HPC0 - 0.12,
    r: 0.36,
    clock: 60,
    build: () => merge([probeRing(2, HPC_ROWS.IGV.LE.rTip + 0.05, HPC_ROWS.IGV.LE.rTip - 0.12, HPC0 - 0.14, 0.012, 50)]),
    text: "Temperature and pressure at the entry to the HP compressor. Corrected core speed, the parameter the stator schedule and the bleed schedule run on, is corrected by T25.",
    facts: [f("Type", "T25 RTD in the core inlet duct; PT0 for pressure", "CR-168219 Fig.48 p.121; CR-168017 sec 11.5–11.10")],
  },
  {
    id: "ps3-t3",
    name: "PS3 tap and T3 thermocouple",
    system: "control",
    y: Y_DOME - 0.08,
    r: 0.5,
    clock: 45,
    build: () => merge([probeRing(1, 0.52, 0.47, Y_DOME - 0.1, 0.01, 40), probeRing(1, 0.52, 0.47, Y_DOME - 0.06, 0.01, 50), pipe([[Y_DOME - 0.1, 0.53, 40], [1.6, 0.55, 45], [0.5, 1.13, 58]], 0.01, 32)]),
    text: "Compressor delivery pressure and temperature, tapped through the combustor casing. PS3 is the FADEC's measure of how much air the engine is actually pumping, and the fuel-to-air limits that protect the compressor from stall and the turbine from over-temperature are all ratios to PS3.",
    facts: [f("Type", "chromel-alumel thermocouple on the outer combustor case; PS3 static tap", "CR-168219 sec 5.10.1 p.120")],
  },
  {
    id: "t42-rakes",
    name: "T42 thermocouple rakes (EGT)",
    system: "control",
    y: HPT0 + 0.25,
    r: 0.42,
    build: () => probeRing(8, HT.blade2Exit.rTip + 0.075, HT.blade2Exit.rHub + 0.02, HPT0 + 0.25, 0.011, 20),
    text: "Eight rakes of thermocouples in the gas behind the HP turbine. T41 itself cannot be measured, so the FADEC watches T42 and holds a limit on it; the crew see it as exhaust gas temperature, the number that tells them how much life the hot section has left.",
    facts: [f("Type", "thermocouples in rakes behind the HPT", "CR-168219 Fig.48 p.121"), f("Rake count", "8", "", "assumed")],
  },
  {
    id: "skin-thermocouples",
    name: "Casing skin thermocouples",
    system: "control",
    y: HPT0 + 0.1,
    r: 0.44,
    clock: 100,
    build: () => merge([blob(HPC0 + 0.65, 0.33, 100, 0.018), blob(HPT0 + 0.1, 0.44, 100, 0.018), blob(LPT0 + 0.3, 0.6, 100, 0.018), pipe([[HPC0 + 0.65, 0.34, 100], [HPT0 + 0.1, 0.45, 100], [LPT0 + 0.3, 0.61, 100]], 0.008, 24)]),
    text: "Thermocouples on the outside of the HPC rear, HPT and LPT casings. They are the feedback for the three clearance-control loops: the FADEC modulates the cooling air until each casing sits at the temperature that gives the clearance it wants.",
    facts: [f("Purpose", "three independent clearance-control loops on measured casing temperature", "CR-168219 sec 5.10.1, sec 5.10.4 p.131")],
  },
];

// ── Air system ────────────────────────────────────────────────────────────

const air = [
  {
    id: "bleed-s5",
    name: "Stage-5 bleed manifold and customer bleed",
    system: "air",
    y: Y_S5,
    r: 0.4,
    build: () =>
      merge([
        hoop(HPC_ROWS.S5.TE.rTip + 0.06, 0.03, Y_S5),
        // Customer bleed duct up to the pylon.
        pipe([[Y_S5, HPC_ROWS.S5.TE.rTip + 0.08, 20], [Y_S5 + 0.05, 0.55, 12], [Y_S5 + 0.1, 0.9, 4], [Y_S5 + 0.15, 1.15, 0]], 0.045, 24),
        unit(Y_S5 + 0.05, 0.56, 12, [0.1, 0.12, 0.12]),
      ]),
    text: "Air taken after the fifth stage, the lowest pressure that will do the job. It supplies the aircraft's cabin and wing anti-ice as customer bleed, and on the engine it cools the rear compressor casing for clearance control, cools the first LPT vanes, and purges the HPT stage-2 disc cavity.",
    facts: [
      f("Users", "customer bleed up to 9 %; aft-HPC ACC 1.3–1.4 %; LPT vane cooling; HPT stage-2 aft purge", "CR-168219 sec 5.2.1 p.52, sec 5.7.4 p.100; HPC report sec 2.3.1 p.28"),
      f("Station", "after stator 5, z ≈ 47.5 cm", "CR-168219 sec 5.2.1 p.52"),
    ],
  },
  {
    id: "bleed-s7",
    name: "Stage-7 bleed and HPT cooling pipes",
    system: "air",
    y: Y_S7 + 0.3,
    r: 0.42,
    build: () =>
      merge([
        hoop(HPC_ROWS.S7.TE.rTip + 0.06, 0.025, Y_S7),
        ...[30, 120, 210, 300].map((c) => pipe([[Y_S7, HPC_ROWS.S7.TE.rTip + 0.08, c], [Y_S7 + 0.2, 0.47, c], [HPT0 - 0.05, 0.5, c], [HPT0 + 0.11, 0.455, c + 10]], 0.026, 24)),
        ...[30, 120, 210, 300].flatMap((c) => [blob(HPT0 + 0.11, 0.45, c + 10, 0.022), blob(HPT0 + 0.11, 0.45, c - 10, 0.022)]),
      ]),
    text: "Air from after stage 7, piped around the combustor casing in four pipes to eight ports on the HPT casing, to cool the second-stage nozzle vanes. Also the port the 30 % start bleed used on the demonstrator, until testing showed the engine started without it.",
    facts: [
      f("Users", "HPT stage-2 nozzle, 1.95–2.35 % of core flow; four pipes into eight HPT casing inlet ports", "CR-167955 sec 3.2.4 p.49; CR-168219 sec 5.2.1 p.52"),
      f("Start bleed", "up to 30 % through this port on the demonstrator; deleted from the FPS", "CR-168219 sec 4.6 p.36"),
    ],
  },
  {
    id: "cdp-bleed",
    name: "CDP bleed ports and HPT rotor coolant path",
    system: "air",
    y: Y_DOME + 0.1,
    r: 0.48,
    build: () => merge([probeRing(8, 0.5, 0.46, Y_DOME + 0.12, 0.022, 22), ring(0.19, 0.2, HPT0 - 0.03, HPT0 + 0.03), lathe([[0.2, HPT0 - 0.03], [0.26, HPT0 + 0.02], [0.3, HPT0 + 0.03], [0.3, HPT0 + 0.045], [0.2, HPT0 + 0.02]])]),
    text: "Compressor-delivery-pressure air: some bypasses the liner to cool the first nozzle, and the rotor's share is taken at mid-span of the diffuser through 28 of its struts and fed to an 80-vane inducer ahead of the first disc. The inducer swirls the air up to wheel speed so it enters the blade roots with no relative velocity, which raises its supply pressure and lowers its relative temperature.",
    facts: [
      f("Ports", "8 CDP bleed ports on the combustor case", "CR-168301 sec 5.3.2"),
      f("Split", "diffuser mid-span bleed: 80 % to the inducer/expander, 20 % CDP-seal blockage", "CR-167955 sec 3.1.3 p.23, sec 3.2.2 p.37"),
      f("Inducer", "80 vanes, plus 64 CDP-leakage bypass tubes", "CR-167955 Fig.95 p.158"),
      f("Total secondary air", "16.1 % of core flow: 7.46 % nonchargeable + 5.33 % chargeable CDP + 1.95 % stage 7 + 1.40 % stage 5", "CR-168219 Table XI p.34"),
    ],
  },
  {
    id: "acc-hpc",
    name: "HPC active clearance control valve and manifold",
    system: "air",
    y: HPC0 + 0.68,
    r: 0.36,
    build: () => merge([shell([[HPC_ROWS.R6.LE.rTip + 0.05, HPC_ROWS.R6.LE.yTip], [HPC_ROWS.S10.TE.rTip + 0.06, HPC_ROWS.S10.TE.yTip]], 0.006), unit(Y_S5 + 0.1, 0.4, 330, [0.08, 0.1, 0.1]), pipe([[Y_S5, HPC_ROWS.S5.TE.rTip + 0.08, 330], [Y_S5 + 0.1, 0.42, 330], [HPC0 + 0.55, 0.38, 330]], 0.024, 12)]),
    text: "A fuel-operated valve passes stage-5 air into a jacket over the rear casing, stages 6 to 10, keeping the casing isolated from the hot gas path and bathed in cooler air. Blade tips there are two centimetres tall; a half-millimetre of clearance is worth a point of efficiency.",
    facts: [f("Arrangement", "valve with position feedback; stage-5 air over the aft casing, casing isolated from flowpath gas", "CR-168219 sec 5.10.4 p.131, sec 5.2.2 p.55, Fig.54 p.132")],
  },
  {
    id: "acc-scoop",
    name: "Turbine ACC fan-air scoop, valves and duct",
    system: "air",
    y: 2.4,
    r: 0.72,
    clock: 0,
    build: () =>
      merge([
        unit(2.0, 1.05, 0, [0.06, 0.28, 0.18]),
        pipe([[2.05, 1.05, 0], [2.2, 0.9, 0], [2.4, 0.7, 0]], 0.05, 16),
        unit(2.28, 0.86, 0, [0.1, 0.1, 0.12]),
        unit(2.28, 0.86, 350, [0.1, 0.1, 0.06]),
        // The 270° duct in the core cowl.
        (() => {
          const g = hoop(0.585, 0.028, 2.5, 8, 96);
          return g;
        })(),
      ]),
    text: "Fan air enters a split scoop on the pylon skirt in the bypass duct, slows in a diffuser, passes two fuel-operated butterfly valves in the pylon, one for the HPT and one for the LPT, and runs round a 270° duct inside the core cowl to the impingement manifolds. The FADEC modulates the valves on casing temperature. Only a third of a percent of core flow, and it was worth more than a percent of fuel burn.",
    facts: [
      f("Arrangement", "split scoop on the pylon skirt, 2:1 diffuser, two butterfly valves, 270° duct in the core cowl", "CR-167955 sec 4.1–4.3 pp.69–83; CR-168219 sec 5.10.4 p.131"),
      f("Worth", "HPT ACC −1.22 % sfc for 0.15 % of core flow; LPT ACC −0.33 %", "CR-167955 Table X p.73; LPT report Fig.48 p.73"),
      f("Max flow", "0.3 % of core flow", "CR-168219 sec 5.10.4"),
    ],
  },
  {
    id: "acc-hpt",
    name: "HPT clearance-control impingement manifolds",
    system: "air",
    y: HPT0 + 0.1,
    r: 0.46,
    build: () => merge([hoop(0.452, 0.016, HPT0 + 0.03), hoop(0.455, 0.016, HPT0 + 0.1), hoop(0.46, 0.016, HPT0 + 0.17), ...[45, 135, 225, 315].map((c) => pipe([[2.5, 0.585, c], [HPT0 - 0.06, 0.52, c], [HPT0 + 0.03, 0.47, c]], 0.02, 16))]),
    text: "Rings of perforated tube around the HPT casing, four 90° manifolds per stage fed by four pipes, blowing fan air straight onto the single-wall casing so it shrinks toward the blade tips at cruise. Left off through takeoff on purpose: the casing must be big while the discs are still growing.",
    facts: [
      f("Arrangement", "four feed pipes to four 90° impingement manifolds per stage; 321 stainless", "CR-167955 sec 4.1–4.3; Fig.52 p.92"),
      f("Schedule", "casing left uncooled through takeoff; clearance 0.41 mm wanted at cruise, 0.64 mm at takeoff", "CR-167955 sec 4.1 p.69, sec 4.2 p.73"),
      f("Casing heating", "0.3 % of core flow of CDP air impinged for 200 s after idle to avoid a takeoff rub", "CR-167955 sec 4.1 p.71; CR-168017 sec 4 p.11"),
    ],
  },
  {
    id: "acc-lpt",
    name: "LPT clearance-control manifold",
    system: "air",
    y: LPT0 + 0.32,
    r: 0.6,
    build: () => merge([...[1, 2, 3, 4, 5].map((k) => { const r = LPT_ROWS[`R${k}`]; return hoop(r.LE.rTip + 0.05, 0.012, (r.LE.yTip + r.TE.yTip) / 2); }), ...[45, 135, 225, 315].map((c) => pipe([[2.5, 0.585, c], [LPT0 + 0.1, 0.5, c], [LPT0 + 0.55, 0.65, c]], 0.016, 16))]),
    text: "The LPT's version: a four-sector backbone with a rib over each rotor stage, in stainless tube, blowing fan air on the LPT casing. Less to gain than on the HPT, because the LPT blades are tall and shrouded, but a third of a percent of fuel is still worth a few kilograms of tube.",
    facts: [f("Arrangement", "4-sector backbone and rib manifold of 321 SS tubes; fan bleed from pylon scoops", "LPT report sec 4.4 pp.128–135")],
  },
  {
    id: "bulkhead",
    name: "Pressure bulkhead (fire safety wall)",
    system: "air",
    y: HPT0 - 0.02,
    r: 0.55,
    // A thin conical wall, not a slab: sheet metal in six sectors.
    build: () => merge([shell([[0.485, HPT0 - 0.07], [0.55, HPT0 - 0.04], [0.598, HPT0 - 0.02]], 0.006), struts(6, 0.49, 0.595, HPT0 - 0.045, 0.05, 0.008, 30)]),
    text: "A six-sector curved sheet-metal wall between the core casings and the core cowl at the HPT. It makes the turbine compartment a low-pressure sink so spent clearance-control air can leave through the rear-frame struts and the centre vent, and it is also the fire wall between the front and back of the core compartment. Its reinforcement was one of three named causes of an HPT casing going out of round on test.",
    facts: [
      f("Design", "six sectors; 389 °C radial gradient and 48 kPa; metal bellows at pipe penetrations", "CR-168219 sec 5.7.4 p.100, sec 5.4.3 p.73"),
      f("Finding", "bulkhead reinforcement next to the HPT stage-1 forward flange contributed to ICLS casing eccentricity", "CR-168211 p.375"),
    ],
  },
  {
    id: "sump-pressurisation",
    name: "Sump pressurisation and bore cooling air",
    system: "air",
    y: 0.7,
    r: 0.3,
    clock: 300,
    build: () => merge([pipe([[FS.innerOgv, 0.62, 300], [0.75, 0.5, 300], [0.85, 0.3, 300], [0.9, 0.22, 300]], 0.02, 16), ring(0.2, 0.215, 0.35, 1.3), ring(0.21, 0.222, HPT0 + 0.25, LPT0 + 0.6)]),
    text: "Fan discharge air fed to the labyrinth seals of both sumps so the pressure outside the seal is always higher than inside: oil stays in, hot air stays out. The same fan air cools the HPC rotor bore on its way aft, and surrounds the aft sump in sealed cavities as a thermal blanket.",
    facts: [
      f("Sealing", "labyrinths pressurised by fan discharge air, both sumps; flows aft through the vent-shaft/LP-shaft annulus", "CR-168219 sec 5.7.2–5.7.3 pp.96–98"),
      f("Bore cooling", "fan discharge air through the HPC rotor bore", "CR-168219 sec 5.2.2 p.52"),
      f("Rear-frame hub heating", "0.147 % + 0.05 % of core flow bled inward between LPT stage 5 and the frame hub", "CR-168219 sec 5.6 pp.90–95"),
    ],
  },
];

// ── Oil system ────────────────────────────────────────────────────────────

const oil = [
  {
    id: "oil-tank",
    name: "Oil tank",
    system: "oil",
    y: 0.05,
    r: R_FANCASE + 0.08,
    clock: 100,
    build: () => merge([drum(0.05, R_FANCASE + 0.005, 100, 0.11, 0.5), blob(0.28, R_FANCASE + 0.13, 100, 0.03)]),
    text: "On the outside of the fan case, where a mechanic can read the sight glass and top it up from the ground without opening the core cowls. Pressurised, de-aerated, and sized so the engine can run a whole flight if the scavenge stops returning oil.",
    facts: [f("Location", "on the outer fan case, for quick inspection", "CR-168219 sec 3.2 p.12"), f("Quantity", "not printed in the transcribed data", "", SCH)],
  },
  {
    id: "oil-pumps",
    name: "Lube and scavenge pump pack",
    system: "oil",
    y: Y_AGB,
    r: R_AGB + 0.16,
    clock: 235,
    build: () => merge([unit(Y_AGB - 0.05, R_AGB + 0.1, 235, [0.16, 0.36, 0.22]), drum(Y_AGB + 0.25, R_AGB + 0.14, 240, 0.045, 0.14)]),
    text: "One pressure element feeds the whole engine; separate scavenge elements, one per sump and one for the gearbox, suck the oil back out. Scavenge always out-pumps supply, so the sumps run nearly dry and the returning oil carries the bearing heat with it.",
    facts: [
      f("Arrangement", "single supply element, separate scavenge elements per sump and gearbox; lube pump filter", "CR-168219 sec 5.7.5 p.100, Fig.46 p.117"),
      f("Features", "filters on supply and scavenge, scavenge inlet screen, supply check valves against sump flooding at shutdown", "CR-168219 sec 5.7.5 p.100"),
    ],
  },
  {
    id: "oil-filter",
    name: "Oil filter and chip detectors",
    system: "oil",
    y: Y_AGB + 0.5,
    r: R_AGB + 0.16,
    clock: 250,
    build: () => merge([drum(Y_AGB + 0.5, R_AGB + 0.12, 250, 0.055, 0.2), blob(Y_AGB + 0.65, R_AGB + 0.16, 262, 0.025), blob(Y_AGB + 0.65, R_AGB + 0.16, 238, 0.025)]),
    text: "The scavenge filter with a bypass indicator, and magnetic chip detectors in each scavenge line that catch the ferrous debris a failing bearing sheds before it fails. Checking the chip detectors is the first thing done after a shift of flying.",
    facts: [f("Maintainability features", "chip detectors, oil sampling, filter-bypass indication", "CR-168219 Fig.5 p.15")],
  },
  {
    id: "forward-sump",
    name: "Forward sump (bearings 1, 2, 3)",
    system: "oil",
    y: 0.85,
    r: 0.19,
    build: () => merge([shell([[0.17, 0.32], [0.19, 0.55], [0.2, 0.9], [0.22, 1.15], [0.2, 1.32]], 0.006), ring(0.16, 0.17, 0.32, 0.36), ring(0.16, 0.2, 1.32, 1.35)]),
    text: "The sealed housing in the fan-frame hub holding the LP thrust bearing, the LP support bearing and the HP thrust bearing, and the PTO bevel gears. Oil jets and under-race feeds come off one manifold; the No. 3 damper has its own. Vented forward through the LP shaft.",
    facts: [
      f("Contents", "No.1, No.2, No.3 and the PTO bearings; jet or under-race lube from a common manifold, the No.3 damper from its own", "CR-168219 sec 5.7.2 p.96"),
      f("Vent", "through the LP fan shaft to the centre vent tube", "CR-168219 sec 5.7.2"),
    ],
  },
  {
    id: "aft-sump",
    name: "Aft sump (bearings 4, 5)",
    system: "oil",
    y: LPT0 + 0.5,
    r: 0.17,
    build: () => merge([shell([[0.15, HPT0 + 0.28], [0.16, LPT0 + 0.3], [0.17, STATIONS.trf + 0.02]], 0.006), ring(0.12, 0.15, HPT0 + 0.27, HPT0 + 0.3)]),
    text: "The hot end: the intershaft bearing and the No. 5 bearing under the turbine rear frame, cooled under-race by a jet on the No. 5 housing. Surrounded by cooling air in sealed cavities, and vented through an air/oil separator on the end of the LP shaft into the centre vent tube.",
    facts: [
      f("Contents", "No.4 intershaft and No.5; under-race cooling from a jet on the No.5 housing; air/oil separator on the LP shaft end", "CR-168219 sec 5.7.3 p.98, Fig.38 p.99"),
      f("Lines", "lube and scavenge cross the gas path inside the rear-frame struts", "CR-168219 sec 5.6 p.90, sec 5.7.5 p.100"),
    ],
  },
  {
    id: "oil-lines",
    name: "Oil supply and scavenge lines",
    system: "oil",
    y: 2.2,
    r: 0.5,
    clock: 240,
    build: () =>
      merge([
        pipe([[0.3, R_FANCASE + 0.05, 100], [0.7, R_FANCASE + 0.02, 130], [FS.bypassOgv, 1.0, 170], [FS.bypassOgv, 0.7, 176], [Y_AGB - 0.2, R_AGB + 0.2, 220]], 0.018, 40),
        pipe([[Y_AGB + 0.1, R_AGB + 0.2, 240], [Y_AGB + 0.1, 0.56, 240], [FS.fanFrame + 0.05, 0.56, 240], [FS.fanFrame + 0.05, 0.36, 210], [FS.fanFrame + 0.05, 0.23, 210]], 0.016, 32),
        pipe([[Y_AGB + 0.3, R_AGB + 0.2, 245], [Y_AGB + 0.4, 0.55, 245], [2.2, 0.53, 245], [HPT0 + 0.1, 0.5, 245], [STATIONS.trf, 0.62, 250], [STATIONS.trf, 0.3, 250], [STATIONS.trf, 0.2, 250]], 0.016, 64),
        pipe([[Y_AGB + 0.3, R_AGB + 0.2, 232], [Y_AGB + 0.4, 0.55, 232], [2.2, 0.53, 232], [HPT0 + 0.1, 0.5, 232], [STATIONS.trf, 0.62, 236], [STATIONS.trf, 0.3, 236], [STATIONS.trf, 0.2, 236]], 0.016, 64),
      ]),
    text: "From the tank down to the pump, and from the pump forward to the front sump and aft along the core to the rear sump, with a scavenge line beside each supply. The aft lines cross the exhaust gas inside the rear-frame struts, which is why those struts are hollow and insulated.",
    facts: [f("Routing", "generic between the printed endpoints", "CR-168219 sec 5.7.5", SCH)],
  },
  {
    id: "vent-tube",
    name: "Centre vent tube (vent stinger)",
    system: "oil",
    y: STATIONS.trf + 0.6,
    r: 0.03,
    build: () => merge([ring(0.02, 0.03, STATIONS.trf - 0.02, EXHAUST.yNozzleExit + 0.1), ring(0.03, 0.05, EXHAUST.yNozzleExit + 0.02, EXHAUST.yNozzleExit + 0.1)]),
    text: "The tube down the centreline and out through the tail cone that carries the breather air from both sumps and the gearbox, and the spent clearance-control air, out past the nozzle exit plane. Everything that leaks past a seal leaves the engine here, as a faint blue haze on a cold morning.",
    facts: [f("Vents", "both sumps, the gearbox, rear-frame cavities and spent ACC air, through the nozzle exit plane", "CR-168219 sec 5.8 p.102, sec 5.7.5 p.100; CR-167955 sec 4.1 p.72")],
  },
];

// ── Ignition ──────────────────────────────────────────────────────────────

const ignition = [
  ...[120, 240].map((c, i) => ({
    id: `igniter-${i + 1}`,
    name: `Igniter plug ${i + 1} (${c}°)`,
    system: "ignition",
    y: Y_DOME + 0.06,
    r: 0.45,
    clock: c,
    build: () => merge([probeRing(1, 0.5, COMBUSTOR.rLinerOuter - 0.005, Y_DOME + 0.06, 0.016, c), drum(Y_DOME + 0.06, 0.49, c, 0.028, 0.04, false)]),
    text: "A surface-discharge plug through the combustor casing, its tip flush with the outer liner wall in the pilot dome. It fires a few joules a couple of times a second during a start; once the dome is lit it is switched off and does nothing for the rest of the flight unless the crew select continuous ignition.",
    facts: [
      f("Location", `combustor casing at ${c}°, in the outer (pilot) liner, panel 1, flush with the wall`, "CR-168301 Fig.38 p.67, Fig.39 p.68; sec 6 p.275"),
      f("Energy", "rig system: 2 J delivered, 2 sparks/s (flight exciter not printed)", "CR-168301 p.275"),
    ],
  })),
  {
    id: "exciters",
    name: "Ignition exciters and leads",
    system: "ignition",
    y: 1.9,
    r: 0.55,
    clock: 140,
    build: () =>
      merge([
        unit(1.85, 0.5, 140, [0.08, 0.16, 0.14]),
        unit(1.85, 0.5, 220, [0.08, 0.16, 0.14]),
        pipe([[1.93, 0.55, 140], [2.1, 0.55, 130], [Y_DOME + 0.06, 0.53, 122]], 0.01, 20),
        pipe([[1.93, 0.55, 220], [2.1, 0.55, 230], [Y_DOME + 0.06, 0.53, 238]], 0.01, 20),
      ]),
    text: "Two independent exciter boxes in the core compartment, each charging a capacitor from the aircraft bus and dumping it down a shielded high-tension lead to its own plug. Two, so that a failed exciter never means a failed relight at altitude.",
    facts: [
      f("Location", "core compartment, under the core cowl; the cowl is purged by ≈478 K fan air and soak-back after shutdown was analysed to 616 K against a 700 K PTFE lead limit", "CR-168301 sec 5.4.1.5 pp.105–106"),
      f("Relight", "altitude relight requirement 9.1 km", "CR-168301 Table II p.5"),
    ],
  },
  {
    id: "crossfire-tubes",
    name: "Crossfire tubes",
    system: "ignition",
    y: Y_DOME + 0.05,
    r: 0.333,
    build: () => merge(...[[120, 240].map((c) => drum(Y_DOME + 0.05, 0.322, c, 0.012, 0.03, false))]),
    text: "Two short tubes through the centrebody between the two domes, in line with the igniters. Only the outer pilot dome has igniters; when the main-zone valve opens at about 80 % core speed, flame crosses through these tubes to light the inner dome.",
    facts: [f("Count", "2, through the centrebody, in line with the igniters", "CR-168301 sec 5.3.2 p.73")],
  },
];

// ── Variable geometry ─────────────────────────────────────────────────────

const vg = [
  {
    id: "vsv-rings",
    name: "VSV unison rings and levers",
    system: "variable-geometry",
    y: HPC0 + 0.2,
    r: 0.4,
    build: () =>
      merge(
        ["IGV", "S1", "S2", "S3", "S4", "S5"].map((n) => {
          const row = HPC_ROWS[n];
          const y = (row.LE.yTip + row.TE.yTip) / 2;
          return hoop(row.LE.rTip + 0.062, 0.012, y, 8, 96);
        })
      ),
    text: "One ring around the casing for each variable row. Every vane has a spindle through the casing with a lever on it, and every lever pins to the ring, so turning the ring a few degrees turns all the vanes together. A torsion bar links the rings so one pair of actuators drives all six rows on one schedule.",
    facts: [
      f("Rows", "IGV + stators 1–5 (FPS product); IGV + 1–4 in the HPC design report", "HPC report sec 2.3.1 p.28, sec 3.3 p.64"),
      f("Bushings", "ZX / Fabroid XV composite to 546 K (IGV–S3), PBH-20 carbon beyond", "HPC report Table XVIII p.102"),
    ],
  },
  {
    id: "vsv-actuators",
    name: "VSV actuators (fuel-driven rams)",
    system: "variable-geometry",
    y: HPC0 + 0.2,
    r: 0.44,
    clock: 90,
    build: () => merge([drum(HPC0 + 0.18, 0.4, 90, 0.035, 0.32), drum(HPC0 + 0.18, 0.4, 270, 0.035, 0.32), pipe([[HPC0 + 0.02, 0.43, 90], [HPC0 - 0.02, 0.43, 95], [HPC0 - 0.03, 0.42, 100]], 0.014, 8), pipe([[HPC0 + 0.02, 0.43, 270], [HPC0 - 0.02, 0.43, 265], [HPC0 - 0.03, 0.42, 260]], 0.014, 8)]),
    text: "A pair of hydraulic rams, one each side of the casing, working on fuel from the pump's surplus through one electrohydraulic servovalve. A position transducer tells the FADEC where the vanes actually are, and the demonstrator tracked its schedule to half a degree even in slam accelerations.",
    facts: [
      f("Arrangement", "pair of fuel-driven ram actuators, levers, unison rings, one servovalve, LVPT feedback, torsion-bar linkage", "CR-168219 sec 5.10.3 p.128, Fig.53 p.129; HPC report p.99"),
      f("Schedule", "against corrected core speed with rain, stall, reverser, deterioration and bleed biases", "CR-168219 sec 5.10.1"),
      f("As tested", "stator tracking ±0.5° in fast transients", "CR-168219 sec 5.10.6"),
    ],
  },
  {
    id: "vbv-doors",
    name: "Variable bleed valve doors",
    system: "variable-geometry",
    kind: "vbv",
    y: 0.8,
    r: 0.67,
    vbv: { count: 12, r: 0.585, y: 0.9, width: 0.13, length: 0.14 },
    build: () => doorRing(12, 0.585, 0.9, 0.13, 0.14, 0),
    text: "Doors in the wall between the booster exit and the bypass duct. At idle the booster pumps more air than the slow-turning core can swallow and would stall; the doors open and dump the surplus into the bypass. They also throw hail and water out of the core stream. Move the slider to open them.",
    facts: [f("Arrangement", "generic; the E³ reports treat the start bleed and the booster match, not a VBV door count", "", SCH)],
  },
  {
    id: "start-bleed-valve",
    name: "Start bleed valve (stage 7)",
    system: "variable-geometry",
    y: Y_S7,
    r: 0.44,
    clock: 40,
    build: () => merge([unit(Y_S7, 0.38, 40, [0.1, 0.12, 0.14]), pipe([[Y_S7 + 0.08, 0.45, 40], [Y_S7 + 0.3, 0.55, 40], [2.5, 0.58, 40]], 0.03, 16)]),
    text: "A fuel-actuated valve on the stage-7 port sized to dump up to 30 % of the core flow during a start so the rear stages are not choked while the front stages are stalled. The demonstrator started fine with it shut, so the production design deleted it.",
    facts: [f("Status", "up to 30 % stage-7 start bleed; never needed on test, deleted from the FPS", "CR-168219 sec 4.6 p.36, sec 3.1 p.10")],
  },
  {
    id: "reverser",
    name: "Thrust reverser (cascade)",
    system: "variable-geometry",
    y: 1.7,
    r: 1.1,
    build: () => merge([shell([[1.09, 1.35], [1.09, 2.1]], 0.02), ...Array.from({ length: 24 }, (_, i) => { const g = ring(1.075, 1.1, 1.4 + i * 0.028, 1.4 + i * 0.028 + 0.012); return g; })]),
    text: "In the bypass duct wall aft of the fan frame: a translating sleeve that slides back to uncover cascade vanes, while blocker doors swing into the duct so the bypass air goes out through the cascades, forward. Only the fan stream is reversed; the core keeps going aft. The E³'s was FADEC-controlled and split in two halves hinged from the pylon.",
    facts: [f("Design", "fixed cascades, translating sleeve, blocker doors on a floating unison ring; two halves hinged at the pylon, latched at 6 o'clock; FADEC-controlled", "CR-168219 sec 5.9.1 pp.105–110, Figs.41–42"), f("Mass", "379 kg", "CR-168219 Table XXVI p.140")],
  },
];

// ── Anti-icing ────────────────────────────────────────────────────────────

const antiIce = [
  {
    id: "lip-d-duct",
    name: "Inlet lip anti-ice duct (D-duct)",
    system: "anti-ice",
    y: -0.78,
    r: 1.15,
    build: () => merge([hoop(1.14, 0.045, -0.79, 10, 128), hoop(1.14, 0.012, -0.79, 6, 128)]),
    text: "The hollow D-shaped chamber inside the inlet lip. Hot bleed air swirls round it and out through small holes, keeping the lip skin above freezing so ice cannot form and then shed into the fan. The one place on the nacelle that has to be anti-iced, because the lip is the one place ice would grow.",
    facts: [f("Design", "generic; the E³ reports describe no inlet anti-ice hardware", "CR-168017 sec 5.2 p.16 lists anti-ice bleed as a control-study input only", SCH)],
  },
  {
    id: "anti-ice-valve",
    name: "Anti-ice pressure-regulating shutoff valve",
    system: "anti-ice",
    y: 0.6,
    r: R_FANCASE + 0.02,
    clock: 20,
    build: () => merge([unit(0.6, R_FANCASE + 0.01, 20, [0.1, 0.18, 0.12]), blob(0.6, R_FANCASE + 0.14, 20, 0.03)]),
    text: "A valve on the fan case, opened by the crew or the FADEC when icing conditions are declared, that regulates the bleed pressure down to what the lip duct can take. Position is reported to the flight deck; a stuck-closed valve is an icing restriction, a stuck-open one is a lip overheat.",
    facts: [f("Design", "generic", "Rolls-Royce, The Jet Engine, ch. 11", TB)],
  },
  {
    id: "anti-ice-duct",
    name: "Anti-ice supply duct",
    system: "anti-ice",
    y: 0.2,
    r: 1.16,
    clock: 20,
    build: () => merge([pipe([[Y_S5, HPC_ROWS.S5.TE.rTip + 0.08, 15], [Y_S5 - 0.1, 0.55, 18], [FS.bypassOgv + 0.05, 0.66, 20], [FS.bypassOgv, 1.0, 20], [FS.bypassOgv - 0.1, R_FANCASE + 0.03, 20], [0.7, R_FANCASE + 0.03, 20]], 0.035, 40), pipe([[0.5, R_FANCASE + 0.03, 20], [0.0, R_FANCASE + 0.03, 20], [-0.5, 1.17, 20], [-0.75, 1.16, 20]], 0.035, 32)]),
    text: "Bleed air from the stage-5 port, up through a fan-frame strut and forward along the fan case to the lip. Insulated, because it runs through the fan compartment at several hundred degrees, and fitted with a bellows to take the growth.",
    facts: [f("Source", "HPC stage-5 or stage-7 bleed on this engine", "", SCH)],
  },
  {
    id: "spinner-anti-ice",
    name: "Spinner and probe heating",
    system: "anti-ice",
    y: -0.5,
    r: 0.15,
    build: () => merge([lathe([[0.0, -0.61], [0.09, -0.5], [0.19, -0.37], [0.2, -0.36], [0.1, -0.49], [0.0, -0.6]]), blob(-0.45, 1.09, 65, 0.035)]),
    text: "The spinner is not heated: its 32° cone and the flex of the blades shed ice before it can build, and any that does shed goes into the bypass, not the core. The T12 probe is electrically heated, because a frozen probe would feed the FADEC a wrong temperature and every corrected parameter would be wrong with it.",
    facts: [
      f("Spinner", "composite, 32° half-angle; no anti-ice", "CR-165148 p.3; CR-168219 sec 5.1.2 p.45"),
      f("Probe heating", "generic", "Rolls-Royce, The Jet Engine, ch. 11", TB),
    ],
  },
];

// ── Fire detection ────────────────────────────────────────────────────────

const fire = [
  {
    id: "fire-loop-fan",
    name: "Fan zone fire detector loops",
    system: "fire",
    y: 0.6,
    r: 1.18,
    build: () => merge([hoop(1.18, 0.006, 0.15, 6, 128), hoop(1.19, 0.006, 0.85, 6, 128), pipe([[0.15, 1.18, 350], [0.85, 1.19, 350]], 0.006, 8)]),
    text: "Two continuous-element sensing loops run round the fan compartment, between the fan case and the cowl. Each is a thin tube whose electrical resistance falls as it heats; the control unit declares a fire only when both loops agree, so a chafed loop gives a fault, not a false alarm.",
    facts: [f("Design", "two loops, AND logic; the E³ ran undercowl fire-detection thermocouples on the test stand", "CR-168211 Table VI p.163; CS-E 530 / Part 33.17", SCH)],
  },
  {
    id: "fire-loop-core",
    name: "Core zone fire detector loops",
    system: "fire",
    y: 2.2,
    r: 0.57,
    build: () => merge([hoop(0.565, 0.006, 1.6, 6, 128), hoop(0.565, 0.006, 2.3, 6, 128), hoop(0.575, 0.006, 3.1, 6, 128), pipe([[1.6, 0.565, 350], [2.3, 0.565, 350], [3.1, 0.575, 350]], 0.006, 12)]),
    text: "The same in the core compartment, where the fuel manifolds, the exciters and the hot casings all are. The pressure bulkhead at the HPT splits this zone in two, so a loop runs on each side of it.",
    facts: [f("Zones", "fan compartment and core compartment; the six-sector bulkhead splits the core zone at the HPT", "CR-168219 sec 5.7.4 p.100", E3)],
  },
  {
    id: "fire-bottles",
    name: "Fire extinguisher bottles and discharge lines",
    system: "fire",
    y: 1.9,
    r: 1.35,
    clock: 0,
    build: () => merge([drum(1.7, 1.4, 6, 0.09, 0.26, true), drum(2.05, 1.4, 354, 0.09, 0.26, true), pipe([[1.85, 1.4, 6], [2.0, 1.2, 8], [2.2, 0.7, 12], [2.4, 0.58, 20]], 0.014, 24), pipe([[2.2, 1.4, 354], [2.3, 1.2, 352], [2.5, 0.7, 348], [2.7, 0.58, 340]], 0.014, 24), pipe([[2.0, 1.2, 8], [1.2, 1.2, 10], [0.9, 1.17, 30]], 0.014, 16)]),
    text: "Two bottles of extinguishing agent in the pylon, each with a squib-fired discharge head, piped down to spray bars in the core and fan zones. The fire drill closes fuel, hydraulics and bleed at the pylon first, then fires bottle one, then bottle two if the warning stays on.",
    facts: [f("Design", "generic; aircraft-side equipment, not described in the E³ reports", "Rolls-Royce, The Jet Engine, ch. 14", SCH)],
  },
  {
    id: "fire-detection-unit",
    name: "Fire detection control unit",
    system: "fire",
    y: 2.6,
    r: 1.36,
    clock: 0,
    build: () => unit(2.6, 1.36, 0, [0.06, 0.16, 0.14]),
    text: "In the pylon: the electronics that read both loops in each zone, compare them, test their continuity, and drive the fire warning and the master caution. It is aircraft equipment, but it decides whether the engine is on fire.",
    facts: [f("Design", "generic, aircraft-side", "", SCH)],
  },
  {
    id: "drain-mast",
    name: "Drain mast",
    system: "fire",
    y: 1.3,
    r: 1.25,
    clock: 180,
    build: () => unit(1.3, 1.24, 180, [0.14, 0.12, 0.05]),
    text: "The little fin under the nacelle that every seal leak, every fuel manifold drain and every overfill from the tank drains through, overboard and clear of the airframe. Fuel that cannot pool inside the cowls cannot feed a fire; the drain mast is part of the fire protection as much as the bottles are.",
    facts: [f("Design", "generic", "", SCH)],
  },
];

// ── Vibration monitoring ──────────────────────────────────────────────────

const vibration = [
  {
    id: "accel-no3",
    name: "No. 3 bearing accelerometer",
    system: "vibration",
    y: HPC0 - 0.19,
    r: 0.22,
    clock: 350,
    build: () => merge([blob(HPC0 - 0.19, 0.2, 350, 0.025), blob(HPC0 - 0.19, 0.2, 80, 0.025)]),
    text: "The FPS's reference vibration point: an accelerometer on the soft, rotor side of the No. 3 bearing's squirrel cage, where the HP rotor's motion is felt most directly. Every published vibration level for this engine is quoted here.",
    facts: [
      f("Design levels", "0.104 mm double amplitude at 1/core at 12,420 N2; 0.127 mm at 1/fan at 2,600 N1", "CR-168219 sec 5.11.2 p.137"),
      f("Result", "no speed-avoidance zones; core response flat and highly damped", "CR-168219 sec 5.11.2 p.137"),
    ],
  },
  {
    id: "accel-fan-frame",
    name: "Fan frame accelerometers",
    system: "vibration",
    y: FS.bypassOgv,
    r: 1.1,
    clock: 30,
    build: () => merge([blob(FS.bypassOgv, 1.1, 0, 0.028), blob(FS.bypassOgv, 1.1, 90, 0.028), pipe([[FS.bypassOgv, 1.11, 0], [FS.bypassOgv - 0.2, R_FANCASE + 0.03, 40], [0.45, R_FANCASE + 0.03, 55]], 0.008, 16)]),
    text: "Vertical and horizontal pickups on the fan frame, the stiffest place close to the fan. Fan imbalance, a lost blade tip, a bird, shows up here first, tracked at once-per-rev of N1.",
    facts: [f("ICLS set", "fan frame vertical + horizontal, forward fan case, and eleven more stations", "CR-168211 Table XXIX p.546")],
  },
  {
    id: "accel-trf",
    name: "Turbine rear frame accelerometer",
    system: "vibration",
    y: STATIONS.trf,
    r: 0.66,
    clock: 355,
    build: () => merge([blob(STATIONS.trf, 0.665, 355, 0.028), pipe([[STATIONS.trf, 0.68, 355], [LPT0 + 0.5, 0.63, 60]], 0.008, 8)]),
    text: "The aft pickup, on the rear frame at 355°. Turbine imbalance and LPT blade problems show here rather than at the front, and the monitor tells LP from HP by whether the vibration follows N1 or N2.",
    facts: [f("ICLS station", "turbine frame, vertical, 355°", "CR-168211 Table XXIX p.546")],
  },
  {
    id: "avm",
    name: "Airborne vibration monitor",
    system: "vibration",
    y: 0.9,
    r: R_FANCASE + 0.01,
    clock: 120,
    build: () => unit(0.9, R_FANCASE + 0.01, 120, [0.08, 0.22, 0.18]),
    text: "The unit that conditions the accelerometer charge signals, filters them at once-per-rev of N1 and N2, shows the crew a vibration number per engine, and stores the phase so a trim-balance weight can be computed after the flight without a test run.",
    facts: [
      f("Design", "generic production arrangement: two accelerometers into an AVM with 1/rev tracking", "", SCH),
      f("Residual unbalance design values", "HP 381 g·cm, LP 1,270 g·cm; 3 mils of vibration carried in every clearance stack", "HPC report Table XVI p.96; CR-167955 Table XIII p.84"),
    ],
  },
  {
    id: "balance-weights",
    name: "Fan trim balance weights",
    system: "vibration",
    y: FS.fanLE - 0.02,
    r: 0.36,
    build: () => merge(...[Array.from({ length: 16 }, (_, i) => blob(FS.fanLE - 0.03, 0.352, i * 22.5, 0.012))]),
    text: "Screw-in weights around the spinner flange. The vibration monitor's phase reading says where to put them; a few grams here cancels an imbalance that would otherwise be felt in the cabin.",
    facts: [f("Design", "generic", "", SCH)],
  },
];

export const SYSTEM_PARTS = [...drives, ...fuel, ...control, ...air, ...oil, ...ignition, ...vg, ...antiIce, ...fire, ...vibration];
