export const profile = {
  name: "Vinaykumar Venkateshkumar",
  // `role` was removed: nothing rendered it, and it had drifted into an
  // exact duplicate of the kicker the hero actually shows.
  kicker: "Design Engineer — Aerospace & Propulsion Hardware",
  tagline:
    "Design engineer with an aerospace propulsion background. Detail and GA drawings with GD&T to ISO 1101, limits and fits to ISO 286, tolerance stack-up, sheet-metal flat patterns and DFM \u2014 from parametric CAD built in CATIA V5, CadQuery and pyOCC, with the geometry verified rather than assumed. Open to freelance parametric-CAD and simulation work alongside full-time design roles.",
  location: "United Kingdom",
  workAuth: "Sponsorship required",
  availability: "Available Sep 2026",
  seeking: "Entry-level design engineering \u2014 aerospace / propulsion hardware",
  email: "kumarvsvinay@gmail.com",
  phone: "+44 7742 914241",
  linkedin: "https://linkedin.com/in/vinaykumar-venkateshkumar",
  github: "https://github.com/Itsvkid",
  cv: "/Vinaykumar_Venkateshkumar_CV.pdf",
};

export const skills = [
  {
    group: "Programming & Geometry",
    items: [
      "Python",
      "Parametric geometry (iCST)",
      "Geometry benchmarking vs. commercial CAD",
      "Automated test suites (pytest)",
      "MATLAB",
    ],
  },
  {
    group: "Mechanical Design",
    items: [
      "GD&T (ISO 1101)",
      "Limits and fits (ISO 286)",
      "Tolerance stack-up (worst-case / RSS)",
      "Design for manufacture",
      "Sheet-metal forming and flat patterns",
      "Detail and GA drawings",
    ],
  },
  {
    group: "CAD",
    items: [
      "CATIA V5",
      "CadQuery",
      "pyOCC / OpenCASCADE",
      "ANSYS DesignModeler",
      "STEP / DXF interchange",
    ],
  },
  {
    group: "Aircraft Engines",
    items: [
      "Gas turbine performance",
      "Turbomachinery aerodynamics",
      "Combustion",
      "Engine design",
    ],
  },
  {
    group: "Simulation",
    items: [
      "ANSYS Fluent",
      "ANSYS ICEM CFD / Meshing",
      "k-ε / k-ω turbulence modelling",
      "OpenFOAM",
      "Grid-independence studies",
    ],
  },
  {
    group: "Aerospace",
    items: ["Aircraft structures", "Non-destructive testing"],
  },
];

export const projects = [
  {
    title: "Installation Aerodynamics of Aero-Engine Nacelles",
    context: "Individual Research Project",
    period: "Ongoing — expected Sep 2026",
    stats: [
      { value: "0.019%", label: "Geometry fit RMS error" },
      { value: "555", label: "Solver iterations to converge" },
      { value: "0.65", label: "RMS Cp error vs. NASA data" },
    ],
    points: [
      "Fitted a Class-Shape Transformation (CST) curve directly to real, published wind-tunnel geometry — NASA TM 110300's NACA 1-85-100 cowl ordinates — reproducing them to 0.019% RMS of the maximum radius, not a synthetic self-check against the project's own reference curve.",
      "Built and converged a compressible RANS OpenFOAM case (rhoSimpleFoam, k-ω SST) around the fitted cowl at Mach 0.79, meshed with snappyHexMesh (108,904 cells) and debugged to convergence after four real solver bugs plus a missing stability safeguard, confirmed against OpenFOAM's own reference tutorial run as a control.",
      "Compared the converged solve's surface pressure against NASA TM 110300's own wind-tunnel data — RMS Cp error 0.65 over 17 matched stations, reported honestly including where the model misses the real leading-edge suction peak.",
    ],
    tech: ["pyOCC", "OpenCASCADE", "Python", "iCST", "OpenFOAM"],
    figures: [
      {
        src: "/figures/cst-fit-to-naca-1-85-100.png",
        alt: "CST-fitted meridian curve overlaid on NASA TM 110300's real external cowl ordinates for the NACA 1-85-100 inlet, the fitted curve passing directly through the measured points.",
        short: "CST fit to real NASA ordinates",
        caption: "A Class-Shape Transformation curve fitted directly to NASA TM 110300's own published cowl ordinates (Table II), not a synthetic sample of this project's own reference design. RMS residual 0.043 mm — 0.019% of the maximum radius.",
      },
    ],
  },
  {
    title: "Twin-Spool Turbofan Cycle Model",
    context: "Personal project — thermodynamic cycle modeling",
    period: "Aug 2026",
    stats: [
      { value: "57.67 kN", label: "Net thrust" },
      { value: "46.7%", label: "Thermal efficiency" },
      { value: "82", label: "Tests" },
    ],
    points: [
      "Built a twin-spool, separate-exhaust turbofan cycle solver station by station from freestream to both nozzle exits, with every turbine's pressure ratio solved against the power its own spool actually demands rather than picked by hand.",
      "Modelled the combustor as an energy balance that solves for fuel-air ratio rather than assuming it, using two distinct gas properties either side of combustion — air at cp 1005 J/(kg·K) going in, combustion products at cp 1244 J/(kg·K) coming out.",
      "Validated against the closed-form ideal-Brayton limit (agrees to within 0.01% when the core nozzle is unchoked) and spool power-balance / combustor energy-balance identities, then characterised — rather than hid — the real, monotonic efficiency penalty a choked convergent nozzle imposes even with zero component losses: at the reference design's OPR of 35.84 the core nozzle runs 6.95× the critical pressure ratio, well underexpanded.",
    ],
    tech: ["Python", "Matplotlib", "pytest"],
    figures: [
      {
        src: "/figures/station-ladder-dark.png",
        srcLight: "/figures/station-ladder.png",
        alt: "Stagnation temperature through the core gas path from fan face to core nozzle exit: a staircase up through compression, a spike at the combustor to 1650 K, then a staircase down through the HPT and LPT to 909 K.",
        short: "Station-ladder diagram",
        caption: "Stagnation temperature through the core gas path — compression as a staircase up, combustion as a spike, expansion as a staircase down. The single most legible way to show what the cycle does to the working fluid, rather than leaving it as a table of numbers.",
      },
    ],
  },
  {
    title: "Aircraft Flight Performance Calculator",
    context: "Personal project — open source",
    period: "Aug 2026",
    stats: [
      { value: "within 8%", label: "Ceiling vs. published" },
      { value: "3", label: "Aircraft validated" },
      { value: "63", label: "Tests" },
    ],
    points: [
      "Built a tested Python package computing flight performance from first principles — ISO 2533 atmosphere, parabolic drag polar, Mach-dependent thrust lapse, climb rate, ceilings, Breguet range and payload-range.",
      "Validated against published data for the 737-800, A320-200 and 777-300ER across a 4.5\u00d7 mass range. Service ceiling agrees within 8%; because manufacturers do not publish CD0 or Oswald efficiency, every result carries a band swept across the plausible range of both.",
      "Added a compressibility (wave) drag term and documented what it did and didn't fix rather than tuning it to look complete: predicted max speed improved from Mach 0.98\u20131.09 to 0.91\u20130.98, but still sits above each aircraft's published MMO \u2014 a real, un-hidden gap in a simplified empirical correlation.",
    ],
    tech: ["Python", "NumPy", "SciPy", "Matplotlib", "pytest"],
    link: {
      href: "https://github.com/Itsvkid/flight-performance-calculator",
      label: "View on GitHub",
    },
    figures: [
      {
        src: "/figures/flight-envelope-dark.png",
        srcLight: "/figures/flight-envelope.png",
        alt: "Flight envelope: altitude against true airspeed, bounded left by a low-speed limit and right by a thrust limit, the two closing on each other and meeting at 13.5 km.",
        short: "Flight envelope",
        caption: "Where level flight is possible. The left boundary is stall speed down low, but above about 12 km it becomes thrust-limited \u2014 the aircraft runs out of thrust before it runs out of wing. Both boundaries meet at the absolute ceiling.",
      },
      {
        src: "/figures/thrust-curves-dark.png",
        srcLight: "/figures/thrust-curves.png",
        alt: "Thrust required and thrust available against true airspeed at 10 km, crossing at 273 m/s, with minimum drag at 197 m/s.",
        short: "Thrust curves, 10 km",
        caption: "Thrust required and available at 10 km. Their crossing sets maximum level speed; the minimum of the required curve is the minimum-drag speed, where induced and parasite drag are equal and L/D peaks at 17.2.",
      },
      {
        src: "/figures/payload-range-dark.png",
        srcLight: "/figures/payload-range.png",
        alt: "Payload-range diagram: flat at 18 tonnes of payload out to 3717 km, then sloping to zero payload at 7519 km.",
        short: "Payload-range",
        caption: "Flat while the tanks still have room, then sloped once fuel is the binding constraint and every extra kilometre is bought by offloading payload.",
      },
    ],
  },
  {
    title: "Airfoil Panel Method, Validated Against XFoil",
    context: "Personal project — from-scratch aerodynamic solver",
    period: "Aug 2026",
    stats: [
      { value: "0.047", label: "Cl RMS vs. XFoil" },
      { value: "0.41\u00d7", label: "Drag recovered vs. XFoil" },
      { value: "38", label: "Tests" },
    ],
    points: [
      "Wrote a Hess-Smith panel method from scratch \u2014 constant-strength source panels for thickness plus a shared vortex distribution for the Kutta condition \u2014 coupled to a Thwaites/Michel/Squire-Young boundary layer for profile drag. Built in code rather than driven through XFLR5's GUI, on the same reasoning as the parametric CAD: a result clicked into existence in a GUI is not reproducible, testable, or reviewable in a diff.",
      "Validated four ways before ever comparing against another code: a panel's self-induced velocity against its closed-form value, two independent routes to Cl (Kutta-Joukowski circulation and direct Cp integration) that share no code path after the linear solve, the Blasius flat-plate solution, and exact zero lift at zero incidence on a symmetric section. Two real bugs fell out of this \u2014 a sign-convention error in the panel rotation and a Kutta-Joukowski circulation sign error.",
      "Then cross-checked the whole thing against XFLR5/XFoil, which couples the inviscid solve and the boundary layer where this does not \u2014 both codes fed identical geometry so no disagreement is attributable to a different body. Lift agrees to 0.047 RMS on NACA 0012, and the lift slopes bracket 2\u03c0 in the direction the physics demands. Drag came out at 0.41\u00d7 XFoil's, nearly flat in incidence against XFoil's tripling: an uncoupled boundary layer recovers skin friction and almost none of the pressure-drag rise. Reported as the headline result rather than buried, and pinned by a test so it cannot drift silently.",
    ],
    tech: ["Python", "NumPy", "SciPy", "Matplotlib", "pytest", "XFLR5"],
    figures: [
      {
        src: "/figures/xflr5-validation-dark.png",
        srcLight: "/figures/xflr5-validation.png",
        alt: "Two panels comparing this project's panel method against XFLR5. Left, lift against angle of attack: the two solvers' curves nearly overlap for NACA 0012 and diverge above 8 degrees for NACA 4412. Right, drag on a logarithmic axis: this project's curves sit roughly a factor of 2.5 below XFLR5's and stay nearly flat while XFLR5's triple.",
        short: "Panel method vs. XFoil",
        caption: "Lift and drag against an independent solver, identical geometry into both. Lift agrees to 0.047 RMS on the symmetric section. Drag is plotted on a log axis on purpose \u2014 the gap is a factor of about 2.5, and on a linear axis two curves 0.007 apart would look like agreement.",
      },
    ],
  },
  {
    title: "Parametric CAD Generators and Drawing Pack",
    context: "Personal project — programmatic mechanical design",
    period: "Aug 2026",
    stats: [
      { value: "5", label: "CAD projects, complete" },
      { value: "0.25%", label: "Flat-pattern volume error" },
      { value: "231", label: "Tests" },
    ],
    points: [
      "Wrote two CadQuery generators that size a design before they draw it: a flight-control actuator family across four aircraft classes, and an engine accessory gearbox family across five power ratings. Changing one input \u2014 bore, or shaft power \u2014 propagates through gear sizing, bearing selection, housing geometry and the bill of materials, whose masses come from the generated solids' own volumes rather than a separate estimate.",
      "Sized the gearbox from the Lewis bending equation solved for module, then snapped that module up to a standard cutter size \u2014 so the safety factor is a consequence of the preferred-number list rather than a figure anyone chose. Tooth flanks are true involutes of the base circle; bearings are real SKF 60xx-series parts picked on shaft torque.",
      "Took the actuator from geometry to a releasable drawing pack: four A4 sheets carrying ISO 286 limits and fits (\u2300\u200935\u2009H8 bore, \u2300\u200921\u2009f7 rod), ISO 1101 geometric tolerances on the features that decide function \u2014 cylindricity on the bore rather than roundness, total runout rather than concentricity, position at maximum material condition on clearance holes \u2014 a chosen datum scheme, surface finishes, and a five-contributor tolerance stack on installed length reported both worst-case and RSS. The tolerances are derived from the model, not typed onto it, and a test asserts the stack's nominal equals where the assembly actually puts the clevis.",
      "Added a formed sheet-metal bracket, because a folded part is a different discipline from a machined one: the blank a shop cuts is shorter than the finished part's legs added together, by one bend deduction per fold. Bend allowance from a K-factor neutral axis, five design-for-manufacture rules \u2014 minimum bend radius, flange length, hole-to-bend distance, fastener edge distance \u2014 and a material trade with a real answer: 2024-T3 is twice as strong as 5052-H32 and cannot make the fold, because its minimum bend radius is 4T against 1T. Validated by conservation of volume: forming moves metal without creating it, so the blank and the formed solid agree to 0.25%, against 5.12% for a naively summed blank.",
      "Then loaded that bracket and found it fails — 2 kg of avionics at a 9g crash factor, solved with CalculiX through FreeCAD headlessly. The result worth having was not the stress but the mesh study: refining from 173k to 333k nodes, deflection converged to 0.06% and bulk stress to 0.28%, while the peak stress climbed 12% and never settled. Its location says why — every peak node sat at z = 0.00 exactly, on the bore edge of a constrained hole, hopping between the two holes run to run. A fixed constraint is singular at its own boundary, so that 545 MPa peak is a boundary condition rather than a stress, and refining further would only make it larger. The converged answer is 196.7 MPa against a 193 MPa yield: the part is marginal, not catastrophic, and the difference between those two verdicts is the whole reason to refine a mesh more than once.",
      "Backed that solver result with closed-form beam theory sharing none of its code, which put the nominal at 235 MPa — also past yield, from a different direction — and surfaced what a single-cantilever idealisation misses: most of the tip movement is the base rotating, not the upright bending, because the base reacts the moment back to the bolts through the same 1.6 mm of material. A test pins the non-convergence itself, so if anyone later rounds that edge and the peak starts converging, the suite fails and the claim gets rewritten.",
      "Sized a bleed-air duct from station 3 of my own turbofan cycle model \u2014 759.5 K at 12.5 bar \u2014 and routed it in pyOCC as a solid swept along a 3D spline, then measured true minimum distance to the structure around it. Two findings the arithmetic gave up rather than the drawing: the wall is governed by surviving a 2\u00d7 diameter bend, not by hoop stress, because bending thins the outside by 20%; and the clearance requirement is 10.5 mm because stainless at 760 K grows 7.6 mm over a metre before anything vibrates. The obvious short route fouled the casing outright, and it is kept in the repository beside the one that works.",
      "Wrote a design-for-manufacture checker that reads a STEP file it did not create \u2014 wall thickness by firing rays through the solid, draft from face normals, hole aspect and internal corner radius from the cylinders that are holes rather than fillets. Run across every part in the repository it found seventeen failures on the gearbox housing as a casting, which that project's own README lists as a known omission: the checker recovered it from the geometry, having never read the README. Its ray-cast wall thickness also returns 3.00 mm on the actuator, exactly the wall_thickness constant its generator sets, by a path that shares no code.",
      "Wrote 78 tests for the gearbox generator \u2014 the last of the five with none, and the one with the most defects already found, which is not a coincidence. They found another: both tooth profiles are drawn with a tooth centred on their own +X axis, so with an even gear the two solids overlapped by 424 mm\u00b3, 2.1% of the pinion, in every exported assembly. Every member of the family has an even gear. Fixed by phasing the gear half a tooth pitch, and the parity matters \u2014 an odd gear already presents a gap, so rotating it causes exactly the clash it avoids. Both directions are pinned by tests and the STEP files are regenerated.",
      "Checked those tests by reintroducing the original involute sign error to confirm the suite goes red. It does, but through only one test of the three that look like they should catch it. Tooth thickness at the pitch circle is still correct with the sign mirrored, which is why the bug survived its first review; and BRepCheck_Analyzer validity still passes too, because at every tooth count this project ships the mirrored flanks stay inside their own sector and the solid is genuinely well-formed. Only checking that the tooth narrows from root to tip finds it. Verifying geometry is well-formed is a different question from verifying it is right.",
      "Checked the geometry rather than assuming it, which is what found the interesting problems: the involute half-angle carried the wrong sign, giving hourglass teeth whose flanks crossed and a solid that failed BRepCheck_Analyzer and would not triangulate; the housing footprint was driven by bearing-boss diameter, so the 50 kW gear hung 84 mm outside its own casing; the actuator assembly stacked every part at the origin, sealing the rod and its rod-end inside the barrel; the clevis was too small to carry its own bolt holes clear of its pin bore; and every BOM mass was a hand-rolled formula, one of them wrong by 5.3\u00d7. All fixed, all covered by tests.",
    ],
    tech: ["Python", "CadQuery", "pyOCC", "GD&T", "ISO 286", "ISO 1101", "Sheet metal", "DFM", "FEA", "CalculiX", "STEP"],
    figures: [
      {
        src: "/products/gearbox-assembly-dark.png",
        srcLight: "/products/gearbox-assembly.png",
        alt: "Shaded render of a single-stage accessory gearbox: a 90-tooth gear meshing with a 20-tooth pinion, both seated on bearing bosses that stand on a flanged aluminium housing with four corner mounting pads.",
        short: "20 kW gearbox assembly",
        caption: "The 20 kW narrow-body design \u2014 90 teeth against 20, a 4.5:1 reduction on a 110 mm centre distance. Rendered straight from the kernel's own tessellation of the exported solid, so what is drawn here is the geometry that ships in the STEP file, not a separate illustration of it.",
      },
      {
        src: "/products/bracket-fea-convergence-dark.png",
        srcLight: "/products/bracket-fea-convergence.png",
        alt: "Two panels against node count on a log axis. Left, peak von Mises stress rising from 457 to 545 MPa and still climbing, with a flat 99th-percentile line at 197 MPa just above a dotted yield line at 193 MPa. Right, tip deflection flat at 4.83 mm against a dashed hand-calculation reference at 6.8 mm.",
        short: "Bracket mesh convergence",
        caption: "Two quantities from the same five solves. The 99th percentile settles to 0.28% and the deflection to 0.06%; the peak node climbs 12% and does not converge, because it sits on the edge of a fixed constraint, which is singular. Hollow markers are meshes too coarse to put two elements through a 1.6 mm wall \u2014 reported, and excluded from every conclusion.",
      },
    ],
  },
  {
    title: "NACA 0012 in OpenFOAM",
    context: "Personal project — open source",
    period: "Aug 2026",
    stats: [
      { value: "\u22123.4%", label: "Drag vs. wind tunnel" },
      { value: "6.4%", label: "Grid convergence index" },
      { value: "53", label: "Tests" },
    ],
    points: [
      "Wrote a generator for a six-block structured C-grid, solving the geometric series for the radial grading so the first cell lands at a target y+ \u2014 the run reports 0.45 to 0.93, so the boundary layer is resolved rather than modelled by wall functions.",
      "Ran a four-level mesh independence study refining every direction including the near-wall spacing, giving an observed order of convergence of 2.24 and a Richardson extrapolation with a 6.4% grid convergence index.",
      "Validated against Ladson, NASA TM 4074, at matching Reynolds number and tripped transition: lift within 0.007 in Cl below 12\u00b0, and grid-converged drag 3.4% from the measurement \u2014 inside the numerical uncertainty band.",
    ],
    tech: ["OpenFOAM", "k-\u03c9 SST", "Python", "Docker", "ParaView"],
    link: {
      href: "https://github.com/Itsvkid/naca0012-openfoam",
      label: "View on GitHub",
    },
    figures: [
      {
        src: "/figures/vs-experiment-dark.png",
        srcLight: "/figures/vs-experiment.png",
        alt: "Computed lift curve overlaid on wind tunnel measurements from NASA TM 4074, the two coinciding from minus 4 to plus 12 degrees before the computation over-predicts approaching stall.",
        short: "Lift vs. wind tunnel",
        caption: "Computed lift against Ladson, NASA TM 4074, Table VII \u2014 matching Reynolds number of 6\u00d710\u2076 and transition fixed with grit, which is the right comparison for a fully turbulent computation. Mean absolute error in Cl is 0.0092, and better than 0.007 everywhere below 12\u00b0. The last point departs because the computation does not stall: steady RANS cannot resolve the separated flow, and the measurement stalls between 14.0\u00b0 and 15.1\u00b0.",
      },
      {
        src: "/figures/grid-convergence-dark.png",
        srcLight: "/figures/grid-convergence.png",
        alt: "Drag coefficient against representative cell size across four meshes from 7,520 to 85,050 cells, converging toward a Richardson extrapolation that sits just above the measured value.",
        short: "Grid convergence",
        caption: "Four meshes, 7,520 to 85,050 cells, refining every direction including the near-wall spacing so Richardson extrapolation applies. Observed order of convergence 2.24, extrapolated Cd 0.008645 against a measured 0.00895 \u2014 3.4% low, inside the 6.4% grid convergence index. The three coarsest levels alone gave an order of 1.31 and extrapolated to the opposite side of the measurement, which is why the order is computed rather than assumed.",
      },
      {
        src: "/figures/drag-polar-dark.png",
        srcLight: "/figures/drag-polar.png",
        alt: "Drag polar showing the classic parabolic bucket, symmetric about zero lift with minimum drag at zero lift.",
        short: "Drag polar",
        caption: "The parabolic bucket, minimum drag at zero lift where a symmetric section must have it. The polar is symmetric about Cl = 0 to five decimals in Cd \u2014 the section is symmetric, so the sweep carries its own check and passes it under real loading on both sides, not only at the trivial point.",
      },
    ],
  },
  {
    title: "Investigation of Controlled Jets for Enhanced Mixing Rates",
    context: "BEng Final Year Project — team of 3",
    period: "Mar 2025",
    stats: [
      { value: "64–76%", label: "Core-length reduction" },
      { value: "M 0.6–1.0", label: "Validated range" },
      { value: "3.4M+", label: "Mesh nodes" },
    ],
    points: [
      "Investigated passive flow-control tab geometries (Delta Tandem Tab, M Delta Tandem Tab) to enhance nozzle jet mixing.",
      "Ran ANSYS Fluent CFD simulations across Mach 0.6–1.0 with grid-independence studies to 3.4M+ nodes, validated against experimental shadowgraph imaging.",
      "Achieved 64–76% potential core-length reduction versus an uncontrolled jet baseline at Mach 0.8, with no significant thrust penalty.",
    ],
    tech: ["ANSYS Fluent", "ANSYS DesignModeler", "ANSYS ICEM CFD"],
    figures: [],
  },
];

/**
 * Section 02 — the CAD gallery. The section is always on the page; while both
 * arrays are empty it shows a placeholder frame, and the first entry added to
 * either one retires that placeholder automatically.
 *
 * `products` are renders of parts you designed. Drop images in
 * `public/products/` and describe them here — see public/products/README.md.
 *
 *   {
 *     src: "/products/nacelle-assembly.png",
 *     alt: "Rendered nacelle assembly …",   // describe the part, not "render 1"
 *     short: "Nacelle assembly",            // tile heading, ~3 words
 *     tool: "CATIA V5",                     // shown beside the heading
 *     caption: "Full sentence for the lightbox: what it is and what it shows.",
 *   }
 *
 * `cadModels` are self-hosted .glb meshes rendered in-page by three.js. See
 * public/models/README.md for getting from CAD to .glb.
 *
 *   {
 *     title: "Parametric wing",             // label in the model switcher
 *     src: "/models/wing.glb",              // tessellated mesh, keep it small
 *     format: "STEP · generated in pyOCC",  // shown under the frame
 *     href: "https://autode.sk/…",          // optional: native CAD, opens out
 *     description: "One sentence on what the model is.",
 *   }
 *
 * Autodesk Viewer cannot be embedded: it sends X-Frame-Options: DENY and
 * frame-ancestors 'self' *.autodesk.com, so browsers refuse to frame it off
 * their own domain. It is linked rather than embedded for that reason.
 */
export const products = [
  {
    src: "/products/wing-planform-dark.png",
    srcLight: "/products/wing-planform.png",
    width: 1095,
    height: 466,
    alt: "Planform drawing of a 10 m span wing: taper ratio 0.45, 25 degree quarter-chord sweep, with the quarter-chord line and the mean aerodynamic chord of 1.216 m marked at y = 2.184 m.",
    short: "Wing planform",
    tool: "pyOCC / OpenCASCADE",
    caption: "General arrangement of the parametric wing \u2014 10 m span, taper ratio 0.45, 25\u00b0 quarter-chord sweep. The dashed line is the quarter-chord, which is what sweep is measured on; the marked chord is the MAC at 1.216 m, sitting at y = 2.184 m. Drawn from the same parameters that build the solid, so the drawing cannot describe a different wing from the one exported.",
  },
  {
    src: "/products/wing-sections-dark.png",
    srcLight: "/products/wing-sections.png",
    width: 1095,
    height: 262,
    alt: "Root and tip aerofoil sections at true relative scale: NACA 2412 at 1.600 m root chord and 0.720 m tip chord, the tip rotated 3 degrees nose-down.",
    short: "Root and tip sections",
    tool: "pyOCC / OpenCASCADE",
    caption: "Root and tip sections at true relative scale, NACA 2412 throughout. The tip is rotated 3\u00b0 nose-down \u2014 washout, which makes the root stall first and keeps the ailerons working. Drawn because the wing is 51:1 span to thickness, so a 3D view renders it as a flat plate and hides the only thing worth looking at.",
  },
  {
    src: "/products/wing-3d-render-dark.png",
    srcLight: "/products/wing-3d-render.png",
    width: 1600,
    height: 1000,
    alt: "Shaded 3D render of the parametric wing from a 3/4 view, showing the swept, tapered planform and the aerofoil section visible at the root end.",
    short: "Wing, shaded 3D",
    tool: "pyOCC / OpenCASCADE",
    caption: "The same solid as the planform and section drawings above, shaded from a 3/4 view rather than drawn orthographically \u2014 the sweep and taper read as a single continuous surface here, the way they don't in a flat plan view. Rendered from the exact glTF the interactive CAD model below uses, not a separate render pipeline, so the shading matches what dragging that model shows.",
  },
  {
    src: "/products/blade-sections-dark.png",
    srcLight: "/products/blade-sections.png",
    width: 1481,
    height: 1144,
    alt: "Hub and tip sections of a compressor rotor blade at true relative scale, the hub section noticeably more cambered and less staggered than the tip.",
    short: "Rotor blade, hub vs. tip",
    tool: "pyOCC / OpenCASCADE",
    caption: "Hub and tip sections of a free-vortex-designed rotor blade, true relative scale and stagger. The hub carries 27\u00b0 of camber against 6\u00b0 at the tip \u2014 not a styling choice, but what the velocity triangle requires at each radius once blade speed is folded in.",
  },
  {
    src: "/products/deviation-comparison-dark.png",
    srcLight: "/products/deviation-comparison.png",
    width: 945,
    height: 645,
    alt: "Blade camber angle from a plain tangent-mean rule against Carter's-rule-corrected camber across the rotor span, the corrected curve running consistently higher, from 33 to 8 degrees against 27 to 6 degrees at the hub and tip.",
    short: "Deviation correction",
    tool: "pyOCC / OpenCASCADE",
    caption: "How much more camber a real cascade needs once Carter's rule deviation correction is applied, against the plain tangent-mean design this project started with. 5.9°/3.7°/2.4° of deviation at hub/mean/tip — a single-pass correction, the standard preliminary-design approximation, not an iterative solve.",
  },
  {
    src: "/products/blade-row-ga.png",
    width: 2338,
    height: 1653,
    alt: "Dimensioned general arrangement drawing of the axial compressor rotor blade row: meridional view with hub and tip radii, a hub-section cascade detail at 36.9 degrees stagger, and a blade angle schedule table across three radial stations.",
    short: "Blade row general arrangement",
    tool: "pyOCC / OpenCASCADE",
    caption: "A dimensioned general-arrangement drawing in third-angle projection — meridional view, a hub-section cascade detail, and a blade-angle schedule table for the spanwise twist a single 2D section can't show on its own.",
  },
  {
    src: "/products/dfm-findings-dark.png",
    srcLight: "/products/dfm-findings.png",
    width: 1414,
    height: 890,
    alt: "Shaded render of a cast gearbox housing with seventeen orange spheres marking the positions where a design-for-manufacture check found faces with no draft angle, plus one grey marker for an advisory finding.",
    short: "DFM findings, in place",
    tool: "Python / pyOCC",
    caption: "Seventeen failures on the gearbox housing, judged as a sand casting, each marked at the coordinate the check returned rather than annotated by hand. Project 02's own README lists casting draft as something it deliberately does not model \u2014 the checker found that from the geometry, having never read it.",
  },
  {
    src: "/products/dfm-matrix-dark.png",
    srcLight: "/products/dfm-matrix.png",
    width: 924,
    height: 651,
    alt: "Grid of six parts against four manufacturing processes, showing failure counts. Every part is clean when machined or formed as tube, and every part accumulates failures when judged as an investment or sand casting.",
    short: "Process sensitivity",
    tool: "Python / pyOCC",
    caption: "The same six solids under four sets of rules. A part is not manufacturable in the abstract \u2014 it is manufacturable by a process, and the geometry moves from clean to unbuildable depending only on which one you name. The bleed duct's single failure under machining is the honest one: you cannot machine a 0.6 mm wall from solid.",
  },
  {
    src: "/products/duct-clearance-dark.png",
    srcLight: "/products/duct-clearance.png",
    width: 1151,
    height: 1239,
    alt: "Shaded render of a bleed air duct routed past an engine core casing. Two routes are shown: the accepted one standing clear of the casing, and a rejected earlier route in orange that is buried in the casing surface.",
    short: "Duct clearance study",
    tool: "Python / pyOCC",
    caption: "Two routes for the same duct. The orange one is the obvious answer \u2014 hug the core, keep the run short \u2014 and it fouls the casing outright. Clearance is measured as true minimum distance between the B-rep solids, and the requirement is 10.5 mm because a stainless duct at 760 K grows 7.6 mm before anything has vibrated.",
  },
  {
    src: "/products/duct-constraints-dark.png",
    srcLight: "/products/duct-constraints.png",
    width: 748,
    height: 473,
    alt: "Bar chart of the three constraints on duct wall thickness: hoop stress at 0.447 mm, minimum handling gauge at 0.500 mm, and surviving a 2D bend at 0.558 mm, which is highlighted as governing. A dashed line marks the 0.60 mm standard gauge selected.",
    short: "What sets the wall",
    tool: "Python / pyOCC",
    caption: "Everyone assumes a pressure vessel is sized by pressure. Hoop stress at 12.5 bar asks for 0.447 mm; what actually governs is surviving a 2D bend, which thins the outside wall by 20% and so demands 0.558 mm before bending. The wall goes to the next standard gauge at 0.60 mm.",
  },
  {
    src: "/products/sheet-metal-bracket.png",
    width: 2338,
    height: 1653,
    alt: "A4 detail drawing of a formed sheet-metal angle bracket: side and plan views of the folded part, a flat pattern with the bend zone and bend line marked in orange, a bend table listing angle, direction, radius, allowance and deduction, and nine manufacturing notes.",
    short: "Sheet-metal bracket",
    tool: "Python / CadQuery",
    caption: "The formed part and the blank it is cut from, side by side \u2014 101.52 mm against 105.00 mm summed outside legs. A blank cut to the summed legs makes every part in the batch 3.5 mm long in the same direction, which is the classic sheet-metal error. The bend table carries the allowance so the shop does not have to re-derive it.",
  },
  {
    src: "/products/actuator-assembly-ga.png",
    width: 2338,
    height: 1653,
    alt: "A4 general arrangement drawing of a hydraulic actuator assembly in section: ballooned cylinder body, piston rod and clevis end, with a parts list, an installed-length tolerance stack-up table, and a title block.",
    short: "Actuator assembly GA",
    tool: "Python / CadQuery",
    caption: "The assembly in section, ballooned to a parts list whose masses come from each solid's real volume. The overall length carries its stack-up rather than a bare nominal \u2014 390 mm, worst case \u00b10.90, RSS \u00b10.44 \u2014 because on an assembly the useful number is not where the pin bore is meant to be but how far from there it might land.",
  },
  {
    src: "/products/actuator-clevis-detail.png",
    width: 2338,
    height: 1653,
    alt: "A4 detail drawing of an actuator clevis end: front and side views with a pin bore and two bolt holes, three feature control frames for perpendicularity, position at maximum material condition and parallelism, three datum symbols, and a numbered note block.",
    short: "Clevis detail, GD&T",
    tool: "Python / CadQuery",
    caption: "ISO 286 limits and ISO 1101 geometric tolerances on the features that decide whether the part works. The bolt holes carry position at maximum material condition, so a hole drilled larger than minimum earns bonus tolerance \u2014 withholding that rejects parts that assemble perfectly well. Every callout is derived from the model, not typed onto it.",
  },
  {
    src: "/products/actuator-family-dark.png",
    srcLight: "/products/actuator-family.png",
    width: 828,
    height: 898,
    alt: "Four hydraulic flight-control actuators shaded and lined up at true relative scale, from a 16 mm-bore Cessna-class unit to a 50 mm-bore B777-class one, each showing its cylinder body, extended piston rod and clevis rod-end.",
    short: "Actuator family, to scale",
    tool: "Python / CadQuery",
    caption: "One script, four aircraft classes, drawn at true relative scale \u2014 16 mm bore up to 50 mm. Posed extended rather than at the origin: build every part where it is defined and the rod and its rod-end sit entirely inside a barrel that is 50 mm longer than the stroke, which is what this assembly used to export.",
  },
  {
    src: "/products/actuator-scaling-dark.png",
    srcLight: "/products/actuator-scaling.png",
    width: 1320,
    height: 860,
    alt: "Output force and force per unit mass plotted against bore diameter for four actuator sizes: force rises from 4 to 41 kN while force per unit mass rises from about 10 to 15 kN per kilogram.",
    short: "Actuator force and mass",
    tool: "Python / CadQuery",
    caption: "Force against mass would be a straight line \u2014 both go as bore squared. The ratio is the interesting one: specific force climbs from 9.8 to 15.1 kN/kg across the family because the wall stays 3 mm however big the bore gets, falling from 27% of the cylinder diameter to 11%. A property of this model's sizing rule, not a law.",
  },
  {
    src: "/products/gearbox-assembly-dark.png",
    srcLight: "/products/gearbox-assembly.png",
    width: 1536,
    height: 1022,
    alt: "Shaded render of a single-stage accessory gearbox: a 90-tooth gear meshing with a 20-tooth pinion, both seated on bearing bosses that stand on a flanged aluminium housing with four corner mounting pads.",
    short: "Accessory gearbox, 20 kW",
    tool: "Python / CadQuery",
    caption: "A 4.5:1 accessory drive on a 110 mm centre distance, teeth generated as true involutes of the base circle. Both gears sit on top of the bearing bosses rather than inside them \u2014 a 47 mm boss will not pass through a 25 mm bore, which is what the original layout asked it to do.",
  },
  {
    src: "/products/gearbox-sizing-dark.png",
    srcLight: "/products/gearbox-sizing.png",
    width: 1320,
    height: 860,
    alt: "Standard module and tooth bending stress plotted against power rating from 5 to 50 kW: module rises as a staircase through 1.5, 2.0 and 2.5 mm while bending stress sawtooths downward at each step, staying below the 150 MPa allowable line.",
    short: "Lewis module sizing",
    tool: "Python / CadQuery",
    caption: "Module is a staircase, not a curve: Lewis gives a required module and the next preferred cutter size is what actually gets used. Every step up drops the stress well clear of the allowable, so the safety factor sawtooths \u2014 it falls out of the standard-module list rather than being chosen.",
  },
  {
    src: "/products/nacelle-meridian-dark.png",
    srcLight: "/products/nacelle-meridian.png",
    width: 1061,
    height: 857,
    alt: "Meridian profile of an axisymmetric nacelle cowl generated from a CST curve, marked at its measured maximum radius of 1.108 m at 36% of the length.",
    short: "Nacelle meridian profile",
    tool: "pyOCC / OpenCASCADE",
    caption: "The generatrix a nacelle's external cowl is revolved from, parametrized by a Class-Shape Transformation (CST) curve rather than a point cloud. Max radius and its station are measured off the result, not dialled in directly \u2014 the weights are the actual design variables.",
  },
];

export const cadModels = [
  {
    title: "Parametric wing",
    src: "/models/wing.glb",
    format: "Generated in pyOCC / OpenCASCADE, exported STEP and tessellated to glTF",
    href: "https://autode.sk/4xSGusM",
    description:
      // ModelViewer appends "Drag to orbit, scroll to zoom." itself — do not
      // repeat it here.
      "The wing from the drawings above, generated from six parameters: span, root chord, taper ratio, quarter-chord sweep, dihedral and washout.",
  },
  {
    title: "Compressor stage",
    src: "/models/stage.glb",
    format: "Generated in pyOCC / OpenCASCADE, exported STEP and tessellated to glTF",
    description:
      "A 32-blade rotor and 45-blade stator sharing one hub and casing. The stator removes the swirl the rotor adds — both rows' stagger and camber come from free-vortex velocity triangles, not a shape parameter, and the blade in the sections above is one radial slice of the rotor.",
  },
  {
    title: "Parametric nacelle",
    src: "/models/nacelle.glb",
    format: "Generated in pyOCC / OpenCASCADE, exported STEP and tessellated to glTF",
    description:
      "An axisymmetric external cowl revolved from the CST meridian profile above. Validated by closed-form limiting cases and kernel-vs-integration agreement rather than a claimed match to a real engine — see the project README for exactly what that does and does not cover.",
  },
];

export const experience = [
  {
    org: "AI Engineering Services Limited (AIESL)",
    sub: "Boeing 737 MRO Base — Air India Express",
    role: "Engineering Intern, Aircraft Maintenance",
    location: "Thiruvananthapuram, India",
    period: "Mar 2025 — Apr 2025",
    points: [
      "Rotational internship across Component Overhaul, Material/Production Planning, and Stores at a 737 base-maintenance facility servicing Air India Express.",
      "Documented wheel/brake overhaul procedures (torque spec 158 lb-ft, tyre pressure 205 ± 5 psi) and Eddy Current Testing (ECT) for non-destructive flaw detection.",
      "Used AMOS and RAMCO systems to track parts issuance, stock levels, and task-card compliance.",
    ],
  },
];

export const education = [
  {
    school: "Cranfield University",
    location: "Cranfield, UK",
    degree: "Thermal Power and Propulsion — Postgraduate Coursework",
    period: "Oct 2025 — Sep 2026",
    current: true,
    modules: [
      "Gas Turbine Performance",
      "Combustion",
      "Turbomachinery Aerodynamics",
      "Propulsion System Design",
    ],
    note: "Installation aerodynamics of aero-engine nacelles (ongoing)",
  },
  {
    school: "KCG College of Technology, Anna University",
    location: "Chennai, India",
    degree: "BEng Aeronautical Engineering — CGPA 7.37/10",
    period: "2021 — 2025",
    modules: [
      "Air Breathing Propulsion",
      "Rocket Propulsion",
      "Aero Engineering Thermodynamics",
      "Aerodynamics I & II",
      "Computational Fluid Dynamics",
      "Aircraft Structures I & II",
      "Finite Element Methods",
      "Wind Tunnel Techniques",
      "Non-Destructive Testing",
      "Aircraft Design",
    ],
  },
];

export const certifications = [
  {
    title: "CATIA V5",
    detail: "CADD Centre Training Services, 80 hrs",
    year: "2024",
  },
  {
    title: "MATLAB Essential Training",
    detail: "LinkedIn Learning",
    year: "2024",
  },
  {
    title: "Machine Learning with Python; Deep Learning with TensorFlow",
    detail: "IBM / Cognitive Class",
    year: "2024",
  },
];
