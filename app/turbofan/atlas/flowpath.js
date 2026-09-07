/**
 * The E³ flowpath in metres, stitched into one axial coordinate.
 *
 * Every radius and every within-component axial station here is transcribed
 * from the NASA/GE Energy Efficient Engine reports via
 * projects/09-e3-engine/data/engine-flowpath.yaml and the two flowpath CSVs
 * it points to. The reports dimension each component in its own datum; the
 * two offsets between datums that no transcribed table gives (fan stacking
 * axis to HPC inlet, and HPC exit to HPT inlet across the diffuser and
 * combustor) are ASSUMED here and flagged `assumed: true` so the page can
 * say so. They are placed by the bearing spans and frame positions of the
 * whole-engine cross-section, and are the only two numbers in this file
 * that are not from a table.
 *
 * Axial coordinate y: positive downstream, fan rotor stacking axis at 0.
 */

// ── Datum offsets ─────────────────────────────────────────────────────────
// HPC report's z (rotor-1 LE hub = 0) sits at y = HPC0 (assumed).
export const HPC0 = 1.42;
// HPT report's x (stage-1 vane inlet = 0) sits at y = HPT0 (assumed: HPC OGV
// trailing edge at HPC0 + 0.782 = 2.202, plus a 0.43 m diffuser + combustor).
export const HPT0 = 2.63;
// LPT datum is the HPT stage-2 blade exit (HPT Fig 3, x = 20 cm).
export const LPT0 = HPT0 + 0.2;

export const ASSUMED_OFFSETS = [
  { name: "fan stacking axis → HPC rotor-1 LE", value_m: HPC0 },
  { name: "HPC OGV TE → HPT vane-1 inlet (diffuser + combustor)", value_m: +(HPT0 - (HPC0 + 0.782)).toFixed(3) },
];

// ── Fan and booster (CR-165148 Table IV, Fig 2, Fig 15) ───────────────────
export const FAN = {
  rTip: 1.054,
  rHub: 0.3605,
  blades: 32,
  // The 50 % span shroud the E³ fan carries (CR-168219 sec 5.1.2 p.45).
  shroudSpan: 0.5,
  chordRoot: 0.30,
  chordTip: 0.42,
};
export const BOOSTER = {
  rTip: 0.669,
  rHub: 0.523,
  blades: 56,
  islandVanes: 60,
  innerOgv: 64,
  bypassOgv: 34,
  splitFraction: 0.223,
};
// Axial stations for the fan module (fan-report datum is the stacking axis).
export const FAN_STATIONS = {
  spinnerNose: -0.62,
  fanLE: -0.19,
  fanTE: 0.17,
  splitterLE: 0.26,
  islandVane: 0.34,
  boosterRotor: 0.48,
  innerOgv: 0.62,
  bypassOgv: 0.86, // 1.8 tip chords behind the rotor (CR-165148)
  fanFrame: 0.98,
};

// ── HPC (HPC report Table XXI streamlines, Table X) ───────────────────────
// [row, edge, z_hub_cm, r_hub_cm, z_tip_cm, r_tip_cm] from hpc-flowpath.csv.
const HPC_CSV = `IGV,LE,-6.543,17.337,-7.658,36.211
IGV,TE,-2.464,17.288,-1.458,35.540
R1,LE,0.000,17.795,2.085,35.070
R1,TE,9.254,20.343,6.891,34.379
S1,LE,10.307,20.641,9.655,34.103
S1,TE,13.984,21.693,13.630,33.804
R2,LE,15.464,22.100,16.418,33.589
R2,TE,21.168,23.623,19.865,33.317
S2,LE,22.325,23.902,21.974,33.171
S2,TE,25.044,24.536,25.008,32.971
R3,LE,26.380,24.805,26.886,32.833
R3,TE,30.372,25.505,29.629,32.601
S3,LE,31.474,25.681,31.219,32.466
S3,TE,33.702,26.029,33.637,32.262
R4,LE,34.908,26.173,35.279,32.123
R4,TE,38.112,26.471,37.512,31.934
S4,LE,39.129,26.576,38.946,31.813
S4,TE,41.054,26.775,41.001,31.639
R5,LE,42.157,26.840,42.479,31.514
R5,TE,44.857,26.919,44.386,31.352
S5,LE,45.727,26.955,45.647,31.246
S5,TE,47.485,27.031,47.505,31.088
R6,LE,49.346,27.098,49.563,30.849
R6,TE,51.527,27.163,51.201,30.732
S6,LE,52.448,27.180,52.369,30.649
S6,TE,54.134,27.252,54.158,30.521
R7,LE,55.288,27.286,55.498,30.425
R7,TE,57.481,27.327,57.164,30.306
S7,LE,58.418,27.326,58.370,30.219
S7,TE,60.276,27.317,60.255,30.084
R8,LE,62.186,27.323,62.353,29.957
R8,TE,64.226,27.368,63.974,29.885
S8,LE,65.002,27.367,64.995,29.840
S8,TE,67.053,27.353,67.158,29.745
R9,LE,67.961,27.357,68.113,29.703
R9,TE,69.804,27.377,69.571,29.639
S9,LE,70.603,27.374,70.612,29.593
S9,TE,72.443,27.359,72.473,29.511
R10,LE,73.432,27.361,73.552,29.463
R10,TE,75.025,27.375,74.843,29.406
S10,LE,76.036,27.370,75.974,29.358
S10,TE,78.207,27.357,78.207,29.342`;

export const HPC_ROTOR_BLADES = [28, 38, 50, 60, 70, 80, 82, 84, 86, 94]; // Table X p.65
export const HPC_STATOR_VANES = { IGV: 32, S1: 50, S2: 68, S3: 82, S4: 92, S5: 110, S6: 120, S7: 112, S8: 104, S9: 118, S10: 140 }; // Table XXII
export const HPC_VARIABLE_ROWS = ["IGV", "S1", "S2", "S3", "S4", "S5"]; // FPS product: IGV + stators 1–5

function parseRows(csv, datum, scale = 0.01) {
  const rows = {};
  for (const line of csv.trim().split("\n")) {
    const [row, edge, zh, rh, zt, rt] = line.split(",");
    rows[row] ??= {};
    rows[row][edge] = {
      yHub: datum + Number(zh) * scale,
      rHub: Number(rh) * scale,
      yTip: datum + Number(zt) * scale,
      rTip: Number(rt) * scale,
    };
  }
  return rows;
}

export const HPC_ROWS = parseRows(HPC_CSV, HPC0);

// ── HPT (HPT report Fig 3, dimensioned) ───────────────────────────────────
export const HPT_STATIONS = {
  vane1Inlet: { y: HPT0 + 0.0, rHub: 0.315, rTip: 0.372 },
  vane1Exit: { y: HPT0 + 0.035, rHub: 0.3258, rTip: 0.3658 },
  blade1Exit: { y: HPT0 + 0.085, rHub: 0.3233, rTip: 0.366 },
  vane2Exit: { y: HPT0 + 0.155, rHub: 0.3122, rTip: 0.3805 },
  blade2Exit: { y: HPT0 + 0.2, rHub: 0.3112, rTip: 0.381 },
};
export const HPT_VANES = [46, 48];
export const HPT_BLADES = [76, 70];

// ── LPT (from the 30 airfoil sections, lpt-flowpath.csv) ─────────────────
// [row, edge, z_hub_cm, r_hub_cm, z_tip_cm, r_tip_cm]
const LPT_CSV = `S1,LE,6.845,32.324,6.846,40.777
S1,TE,12.116,33.416,12.133,43.901
R1,LE,13.897,33.729,13.933,44.845
R1,TE,16.834,34.283,16.653,46.162
S2,LE,18.722,34.593,18.412,47.095
S2,TE,22.477,35.172,22.478,48.888
R2,LE,23.840,35.436,23.880,49.580
R2,TE,26.797,35.955,26.614,50.898
S3,LE,28.376,36.182,28.167,51.720
S3,TE,32.569,36.866,32.570,53.632
R3,LE,33.938,37.141,33.991,54.284
R3,TE,37.122,37.547,36.874,55.587
S4,LE,39.302,37.533,38.499,56.330
S4,TE,42.889,37.535,42.889,57.828
R4,LE,44.731,37.536,44.886,58.448
R4,TE,47.589,37.543,47.150,59.095
S5,LE,49.938,37.384,49.024,59.540
S5,TE,53.549,36.916,53.551,60.020
R5,LE,55.147,36.787,55.123,60.084
R5,TE,58.646,36.787,58.647,60.127`;

export const LPT_ROWS = parseRows(LPT_CSV, LPT0);
export const LPT_BLADES = [120, 122, 122, 156, 110]; // LPT report Fig 52
export const LPT_VANES = [72, 102, 96, 114, 120]; // LPT report Fig 6

// ── Combustor (combustor-design.yaml) ─────────────────────────────────────
export const COMBUSTOR = {
  // Shingle arc widths give the liner radii: outer 37.4 cm, inner 29.2 cm.
  rLinerOuter: 0.374,
  rLinerInner: 0.292,
  fuelNozzles: 30,
  swirlCups: 60, // double annular: two rows of 30
  yDome: HPT0 - 0.30,
  yExit: HPT0,
  yDiffuserInlet: HPC0 + 0.782,
};

// ── Exhaust (CR-168219 sec 5.8, undimensioned) ────────────────────────────
export const EXHAUST = {
  mixerLobes: 18,
  yMixerStart: LPT0 + 0.62,
  yMixerEnd: LPT0 + 1.05,
  yNozzleExit: LPT0 + 1.72,
};

// ── Downstream stations used by the casings and cowls ─────────────────────
export const STATIONS = {
  hpcIgvLE: HPC_ROWS.IGV.LE.yTip,
  hpcOgvTE: HPC_ROWS.S10.TE.yTip,
  hptIn: HPT0,
  hptOut: HPT0 + 0.2,
  lptIn: LPT_ROWS.S1.LE.yTip,
  lptOut: LPT_ROWS.R5.TE.yTip,
  trf: LPT0 + 0.66, // turbine rear frame centre
};

// The whole engine, for framing the camera and the explode reference.
export const ENGINE_LENGTH = EXHAUST.yNozzleExit - FAN_STATIONS.spinnerNose;
export const ENGINE_CENTRE = (EXHAUST.yNozzleExit + FAN_STATIONS.spinnerNose) / 2;
