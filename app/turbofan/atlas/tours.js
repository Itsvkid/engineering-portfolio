/**
 * Guided tours: a sequence of parts the page steps through, with the camera
 * flying to each and a line of narration. Each step names a part id from
 * parts.js; the reducer selects it, applies any layer/cutaway overrides,
 * and asks the scene to frame it. `camera` may name a preset instead of
 * framing the part. Text is written to be read aloud in about ten seconds.
 */
export const TOURS = [
  {
    id: "air",
    name: "Follow the air",
    blurb: "From the inlet lip to the nozzle: what happens to a kilogram of air on its way through.",
    steps: [
      { part: "inlet-cowl", camera: "front", text: "Air arrives through a thick, rounded lip that keeps the flow attached at high incidence, contracts to a throat, then diffuses gently to the fan face." },
      { part: "fan-blades", text: "Thirty-two titanium blades, tips supersonic, do four fifths of the thrust. Six sevenths of the air goes round the core, not through it." },
      { part: "core-inlet-duct", text: "The splitter lip divides the flow. The core stream turns inward from 0.67 m radius to 0.36 m on its way to the HP compressor." },
      { part: "booster-blades", text: "One booster stage on the LP spool supercharges the core. At idle it pumps more than the core can swallow, so the bleed doors behind it open." },
      { part: "vbv-doors", text: "The variable bleed valves: at low speed they dump surplus booster air into the bypass duct, and throw hail and water out with it." },
      { part: "hpc-igv", text: "The HP compressor's inlet guide vanes, and the five stators behind them, re-stagger with speed so the transonic front stages never stall." },
      { part: "hpc-r1", text: "Rotor 1: the biggest single step, a pressure ratio near 1.6, with a blade set at 23° at the root and 65° at the tip straight from the report's Table X." },
      { part: "hpc-r10", text: "Ten stages later the blades are two centimetres tall and the pressure is 23 times what it was at the core inlet." },
      { part: "diffuser", text: "The diffuser slows the air from Mach 0.30 to 0.16 before the combustor. Its thirty struts also carry the rotor's cooling air." },
      { part: "combustor-liner", text: "Two rings of thirty swirl cups on one dome. The pilot ring alone burns at idle; both burn at power. T41 leaves at 1,517 K at climb." },
      { part: "hpt-v1", text: "Forty-six vanes take the first hit, cooled by compressor-delivery air that bypasses the liner, and turn the gas seventy degrees onto the rotor." },
      { part: "hpt-b1", text: "Seventy-six blades pulling 77 kN each at 13,948 rpm, in gas above their own melting point. The two HPT stages drive the whole ten-stage compressor." },
      { part: "lpt-s1", text: "The transition duct flares the flow outward and the five-stage LPT takes over, turning at a third of the HP speed and driving the fan." },
      { part: "lpt-r5", text: "The last and tallest blades, 23 cm, shrouded at the tip. Whatever swirl leaves here the rear frame's cambered struts must remove." },
      { part: "mixer", text: "Eighteen lobes fold the hot core stream into the cold bypass stream. The mixed jet is slower and cooler: more thrust per kilogram of fuel, and quieter." },
      { part: "nozzle", camera: "aft", text: "One convergent-divergent nozzle for both streams, velocity coefficient 0.996. The air has gone from 288 K to 1,500 K and back down, and pushed the aircraft with the difference." },
    ],
  },
  {
    id: "fuel",
    name: "Follow the fuel",
    blurb: "Tank to flame: the pump, the control, the two manifolds, the thirty nozzles and the plugs that light them.",
    steps: [
      { part: "fuel-heater", text: "Fuel arrives from the wing through the pylon and is warmed against the aircraft's bleed air so ice never reaches the filter." },
      { part: "fuel-supply-line", text: "Down to the gearbox, then aft along the core: on a flight engine this line is double-walled so a leak drains overboard, not into the fire zone." },
      { part: "fuel-pump", text: "A centrifugal boost stage then a vane element on the gearbox. It pumps far more than the engine burns; the surplus is the engine's hydraulic supply." },
      { part: "fuel-control", text: "The FADEC positions this metering valve to hold corrected fan speed. A mechanical overspeed governor beside it can cut fuel with no electronics at all." },
      { part: "fadec", text: "The control itself lives on the fan case: a 3.5 MHz microprocessor on a fuel-cooled plate, reading every sensor on the engine about a hundred times a second." },
      { part: "fuel-oil-cooler", text: "Oil on one side, fuel on the other. Every drop burned passes through here and takes the bearing heat with it." },
      { part: "vsv-actuators", text: "Before it is burned, fuel is also the muscle: these rams re-stagger the front compressor stators on the pump's surplus pressure." },
      { part: "fuel-split-valves", text: "The main-zone shutoff valve keeps the inner dome dry at idle and opens it at about 80 % core speed. Staging is what makes the combustor clean at both ends." },
      { part: "fuel-manifolds", text: "Two stainless rings, pilot and main, each with a pigtail to every nozzle." },
      { part: "fuel-nozzles", text: "Thirty stems, each with two duplex tips, one per dome. Hastelloy X tips, and valves cooled by fan air so the fuel inside never cokes." },
      { part: "igniter-1", text: "Two surface-discharge plugs at 120° and 240° light the pilot dome at a couple of sparks a second, then switch off for the rest of the flight." },
      { part: "crossfire-tubes", text: "When the main zone opens, flame crosses through two tubes in the centrebody to light the inner dome. Nobody sparks it." },
      { part: "combustor-liner", text: "And here it burns: 2,600 kg of fuel an hour at takeoff, in shingled walls of X-40 cobalt alloy, at a pressure loss of about five percent." },
    ],
  },
  {
    id: "structure",
    name: "What holds it together",
    blurb: "The load path: two frames, the casings between them, five bearings, and where 173 kN of thrust goes into the wing.",
    steps: [
      { part: "fan-case", text: "The ring around the fan tips. Certification asks it to hold a blade released at full speed: 746 kN, about 76 tonnes, into Kevlar over an aluminium liner." },
      { part: "fan-frame", text: "The main frame, graphite composite with an aluminium hub. Its thirty-four bypass vanes are its struts, and every bit of rotor thrust arrives here." },
      { part: "bearing-1", text: "The LP thrust bearing in the frame's hub: a ball bearing that takes the fan's forward push. The whole engine hangs off what this frame can carry." },
      { part: "bearing-3", text: "The HP thrust bearing, in a squirrel cage with a squeeze-film damper, 1.27 mm of oil film that keeps the core's critical speed out of the running range." },
      { part: "thrust-links", text: "Four links on the frame's aft face. Two at ±45° carry the thrust through a whiffle tree, reacting it at two points 90° apart so the fan case stays round." },
      { part: "hpc-front-case", text: "From the frame aft, the casings are the backbone. This one is drilled for hundreds of stator spindles and split so blades can be changed with the rotor in place." },
      { part: "combustor-case", text: "The pressure vessel: forty atmospheres at a few hundred degrees, with ports for thirty nozzles, two igniters, eight bleeds and the borescope." },
      { part: "bulkhead", text: "Between the casings and the cowl at the HPT, a six-sector bulkhead: the fire wall, and a pressure sink for spent cooling air." },
      { part: "lpt-case", text: "Two forgings, one electron-beam weld, 132 bolts forward sized to hold the LPT rotor axially if its shaft ever breaks." },
      { part: "trf", text: "The rear frame: twelve cambered struts through the exhaust carrying the No. 5 bearing, the mixer, the centrebody and the aft mount." },
      { part: "aft-mount", text: "Three links, vertical and roll only. On this engine the aft mount takes no thrust." },
      { part: "pylon", camera: "top", text: "The pylon carries all of it, plus fuel, bleed, power, the clearance-control scoop and the fire bottles, into the wing spar." },
    ],
  },
];

export const TOUR_BY_ID = Object.fromEntries(TOURS.map((t) => [t.id, t]));
