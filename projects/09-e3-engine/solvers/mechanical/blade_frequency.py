"""Stage E3: blade natural frequency, on the three blades whose boundary
condition the E3 reports themselves name.

METHOD.md's step 0 for this stage says "LPT Fig. 62; **a cantilever beam
first**", and that is the order this follows: the beam is validated
against closed-form eigenvalues in `beam.py` before it sees a blade.

**E3's stated closure is gated, and that is recorded rather than worked
around.** The work plan closes E3 on *the first three modes of every HPC
stage within 5 % of the published Campbell lines* — HPC report Figs 33-42.
`hpc-mechanical.yaml` marks those ten diagrams, and Figs 43-54 with them,
as *"remain figure-status (A3)"*: they were never transcribed. There is
nothing to compare an HPC rotor against. What Stage A **did** transcribe
is three rotor-blade Campbell diagrams, each with a different and
explicitly named tip condition:

  * **LPT stage 1** — CR-168289 Fig. 62, titled *"pinned-tip resonant
    frequency analysis"*. Cast Rene 77 with an integral tip shroud whose
    interlock the report's own model treats as a pin. First flex 2,050 Hz
    at zero speed. And the LPT is the one row whose real airfoil
    coordinates were transcribed, so its section properties come out of
    Green's theorem with **no shape factor at all**.
  * **Booster rotor** — CR-165148 Fig. 55. Unshrouded, stubby, low aspect
    ratio: a plain cantilever, first flex 250 Hz at zero speed rising to
    330 Hz at 3,653 rpm.
  * **Fan rotor** — CR-165148 Fig. 45. A **part-span shroud at 55 %
    height**, so it is neither a free cantilever nor a pinned one. First
    flex 80 Hz at zero speed. The honest prediction is a bracket.

Sections for the fan and the booster are built by the same double-circular-
arc camber line and quarter-sine thickness distribution the C3 blading
work uses (`blading/sections.py`), from Fig. 41's and Fig. 52's chord,
camber, stagger and thickness against height. Twist enters as a bracket
too: a section bends most easily about its **own** weak axis, and least
easily if the whole blade is forced to bend about the root's -- the real
twisted blade is between.

STEP0.md, unit E3."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import yaml

from blading.sections import implied_max_camber, section
from e3cycle.cycle import DATA
from mechanical.beam import Beam, closed_airfoil, polygon_properties
from meanline.losses import _interp
from meanline.sections import load_section

CM, IN = 0.01, 0.0254

# Handbook elastic properties -- NOT from the E3 reports, which print none.
E_TI_6AL_4V, RHO_TI_6AL_4V = 114.0e9, 4430.0      # fan and booster blades
E_RENE77, RHO_RENE77 = 207.0e9, 8220.0            # LPT rotor blades, room temperature


def _fan():
    return yaml.safe_load((DATA / "fan-design.yaml").read_text())


def _lpt():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


# ------------------------------------------------------- section properties

def _props_from_polygon(pts):
    p = polygon_properties(pts)
    return p


def _resolve(p, phi):
    """second moment about an axis at angle phi to x, from the tensor"""
    return ((p["ixx"] + p["iyy"]) / 2 + (p["ixx"] - p["iyy"]) / 2 * math.cos(2 * phi)
            - p["ixy"] * math.sin(2 * phi))


def _weak_axis_angle(p):
    """direction of the axis about which I is smallest"""
    lo, hi = 0.0, math.pi
    xs = np.linspace(lo, hi, 721)
    vals = [_resolve(p, x) for x in xs]
    return float(xs[int(np.argmin(vals))])


@dataclass
class BladeModel:
    name: str
    src: str
    length_m: float
    hub_radius_m: float
    e_pa: float
    rho: float
    published_f1_Hz: float
    published_f1_at_speed: tuple = None      # (rpm, Hz)
    pinned_at: float = None                  # fraction of span, None = free
    x: list = field(default_factory=list)    # station, m from the root
    area: list = field(default_factory=list)
    i_weak: list = field(default_factory=list)
    i_root_axis: list = field(default_factory=list)

    def beam(self, stiff=False, elements=60):
        inertia = self.i_root_axis if stiff else self.i_weak
        return Beam(self.length_m,
                    lambda s: self.e_pa * _interp(s, self.x, inertia),
                    lambda s: self.rho * _interp(s, self.x, self.area),
                    self.hub_radius_m, elements)

    def modes(self, stiff=False, rpm=0.0, n=3, tip_clamped=False):
        omega = rpm * 2 * math.pi / 60
        return self.beam(stiff).frequencies(n, omega, self.pinned_at, tip_clamped)

    def bracket(self, rpm=0.0, n=3):
        return self.modes(False, rpm, n), self.modes(True, rpm, n)


def _fill(model, sections):
    """sections: list of (x_from_root_m, closed polygon in metres)"""
    root = _props_from_polygon(sections[0][1])
    phi_root = _weak_axis_angle(root)
    for x, poly in sections:
        p = _props_from_polygon(poly)
        model.x.append(x)
        model.area.append(p["area"])
        model.i_weak.append(p["i_min"])
        model.i_root_axis.append(_resolve(p, phi_root))
    return model


# ---------------------------------------------------------- the three blades

def lpt_stage1():
    """from the transcribed coordinates -- no shape factor anywhere"""
    return lpt_rotor(1)


@lru_cache(maxsize=None)
def lpt_rotor(stage):
    """Any of the five LPT rotors, from its own transcribed sections.

    Generalised out of `lpt_stage1` for unit E7's flutter screen, which
    needs a first-flex frequency for every stage and not only the one the
    report plots. Stage 1 keeps its published Campbell frequencies; the
    other four have none printed, so they carry NaN and the caller must
    not compare them against a number that does not exist."""
    d = _lpt()
    rb = d["rotor_blades"]
    i = stage - 1
    length = rb["blade_length_cm"][i] * CM
    cam = (d["stage1_blade_campbell"]["natural_frequencies_Hz"]["first_flex"]
           if stage == 1 else None)

    spans, radii, polys = [10, 50, 90], [], []
    for sp in spans:
        pts = load_section(f"R{stage}", sp)
        poly = [(z * IN, t * IN) for z, t in closed_airfoil(pts)]
        rs = []
        with open(DATA / "lpt-airfoils" / f"R{stage}_{sp}.csv") as f:
            for line in f:
                if line.startswith(("#", "surface")):
                    continue
                rs.append(float(line.split(",")[2]))
        radii.append(sum(rs) / len(rs) * IN)
        polys.append(poly)

    # the three sections sit at 10/50/90 % of the span; extrapolate the
    # radius linearly to get the hub, which is where the beam is clamped
    slope = (radii[2] - radii[0]) / 0.8
    hub = radii[0] - 0.1 * slope
    m = BladeModel(f"LPT stage {stage}",
                   "CR-168289 Fig 62 (pinned tip), appendix coordinates"
                   if stage == 1 else "CR-168289 appendix coordinates",
                   length, hub, E_RENE77, RHO_RENE77,
                   cam["at_0_rpm"] if cam else float("nan"),
                   (4000, cam["at_4000_rpm"]) if cam else None,
                   pinned_at=1.0)
    return _fill(m, [(f * length, poly) for f, poly in zip((0.10, 0.50, 0.90), polys)])


def _built_sections(chord_cm, beta1_deg, beta2_deg, stagger_deg, tm_c_pct,
                    edge_c_pct, pct_c_tm_list):
    """double-circular-arc camber, quarter-sine thickness -- the E3's own
    documented construction (CR-165148 sec II.A), as C3 unit 12 uses it.

    **The metal angles are the PRINTED ones** (unit G5). Appendices B and D
    give beta*_LE and beta*_TE in their own columns, and
    `blading.sections.section` solves the double-arc join so that the
    section reproduces both of them AND the printed stagger -- which puts
    the maximum camber where the blade actually has it instead of at
    mid-chord.

    Until 2026-09-18 this function took `camber` and split it symmetrically,
    `b1 = stg + cam/2, b2 = stg - cam/2`, which forces max camber to
    mid-chord on every section. That is the single-circular-arc case, and
    the fan is not one: the appendix's own `stagger - (b1+b2)/2` runs
    -1.57 deg at the hub to +1.82 deg at the tip, 1.85 deg rms, changing
    sign. The booster very nearly is one, 0.61 deg rms, which is why it is
    the control for this change.

    Returns None if any section's join falls outside the arc family, rather
    than silently dropping a station -- a short blade is not a blade."""
    out = []
    for c, b1, b2, stg, tmc, ec, a in zip(chord_cm, beta1_deg, beta2_deg,
                                          stagger_deg, tm_c_pct, edge_c_pct,
                                          pct_c_tm_list):
        sec = section(c * CM, b1, b2, stg, tmc / 100, a, ec / 100)
        if sec is None:
            return None
        out.append(closed_airfoil(sec))
    return out


def max_camber_positions(kind):
    """`f`, the chordwise position of maximum camber, for every printed
    station of the fan or booster.

    An output of the printed angles, not a choice. This is unit G5's
    headline: a symmetric split can only ever return 0.5, and the fan does
    not sit there."""
    f = _fan()
    a = (f["fan_rotor_airfoil"]["appendix_b"] if kind == "fan"
         else f["booster_rotor_airfoil"]["appendix_d"])
    return [(a["percent_blade_height"][i],
             implied_max_camber(a["beta_le_star_deg"][i],
                                a["beta_te_star_deg"][i],
                                a["stagger_deg"][i]))
            for i in range(a["stations"])]


def _at_pct(x, xs, ys):
    """linear in x, clamped at both ends -- the appendix tables run from
    -9 % to 102.5 % of blade height and the read-off they replace runs 0 to
    100, so the two end stations extrapolate and are held flat rather than
    run off the end of a printed trend."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def appendix_sections(kind):
    """The fan or booster rotor built from its PRINTED section table.

    CR-165148 **Appendix B p.134** prints 23 stations for the fan rotor and
    **Appendix D p.136** prints 14 for the booster: percent blade height,
    section height, chord, stagger, camber, tm/c and the two metal angles.
    Unit 15b transcribed both. The seven- and five-station read-offs of
    Fig 41 and Fig 52 that this project built its blades from until now are
    superseded by them, and the data file says so in its own
    `superseded_by:` -- the read-off is wrong by **+5.82 deg of stagger at
    the hub**, up to +4.25 deg of camber, and 1.2-2.8 % of chord, and it is
    radially short at both ends because it spans the stacking-axis box
    rather than the annulus.

    **Radius comes from the table, not from a span fraction.** The first and
    last rows are deliberately off the linear percent-height line because
    they are the flowpath itself: 36.067 cm against a published inlet hub of
    36.047, and 105.410 against a published tip of 105.4. Reading the height
    column rather than the percent column is unit 15b's own instruction.

    **One quantity is not in the appendices and is carried across**: the
    edge thickness ratio, which Fig 41 and Fig 52 print and the tables do
    not. It is interpolated from the superseded block onto the new stations
    by percent blade height. It enters the section shape only near the edges
    and the appendix supplies everything that sets the section's area.

    Returns (radii in metres, closed polygons in metres).
    """
    f = _fan()
    if kind == "fan":
        a = f["fan_rotor_airfoil"]["appendix_b"]
        old = f["fan_rotor_mechanical"]["blade_geometry"]
        edge_pct, h_old = old["tle_c_pct"], old["height_pct"]
        # printed at the hub (42 % chord) and the tip (59 %), linear between
        loc = f["fan_rotor_airfoil"]["max_thickness_location_pct_chord"]
        ats = [loc["hub"] + (loc["tip"] - loc["hub"]) * h / 100
               for h in a["percent_blade_height"]]
    elif kind == "booster":
        a = f["booster_rotor_airfoil"]["appendix_d"]
        old = f["booster_blade_mechanical"]["geometry"]
        edge_pct, h_old = old["te_c_pct"], old["height_pct"]
        # CR-165148 prints the thickness law but not where the maximum sits;
        # 50 % chord, stated as an assumption, as unit 12 states it
        ats = [50.0] * a["stations"]
    else:
        raise ValueError(kind)

    edges = [_at_pct(h, h_old, edge_pct) for h in a["percent_blade_height"]]
    polys = _built_sections(a["chord_cm"], a["beta_le_star_deg"],
                            a["beta_te_star_deg"], a["stagger_deg"],
                            [t * 100 for t in a["tm_over_c"]], edges, ats)
    if polys is None:
        raise RuntimeError(
            f"a printed {kind} section's double-arc join falls outside the "
            "family; it must be reported, not skipped")
    return [r * CM for r in a["radius_cm"]], polys


def fan_rotor():
    f = _fan()
    cam = f["fan_rotor_mechanical"]["campbell"]
    radii, polys = appendix_sections("fan")
    hub, tip = radii[0], radii[-1]
    length = tip - hub
    m = BladeModel("fan rotor",
                   "CR-165148 Appendix B p.134 (geometry), Fig 45 (Campbell)",
                   length, hub, E_TI_6AL_4V, RHO_TI_6AL_4V,
                   cam["modes_Hz"]["first_flex"]["at_0"],
                   (cam["max_speed_rpm"], cam["modes_Hz"]["first_flex"]["at_3653_lowest_in_phase"]),
                   pinned_at=None)
    m.shroud_span = f["fan_rotor_mechanical"]["shroud"]["span_pct"] / 100
    return _fill(m, [(r - hub, p) for r, p in zip(radii, polys)]), tip


def booster_rotor():
    f = _fan()
    cam = f["booster_blade_mechanical"]["campbell"]
    radii, polys = appendix_sections("booster")
    hub, tip = radii[0], radii[-1]
    length = tip - hub
    m = BladeModel("booster rotor",
                   "CR-165148 Appendix D p.136 (geometry), Fig 55 (Campbell)",
                   length, hub, E_TI_6AL_4V, RHO_TI_6AL_4V,
                   cam["modes_Hz"]["first_flex"]["at_0"],
                   (cam["max_speed_rpm"], cam["modes_Hz"]["first_flex"]["at_3653"]),
                   pinned_at=None)
    return _fill(m, [(r - hub, p) for r, p in zip(radii, polys)])


E_NICKEL = 200.0e9                                 # rear HPC stages, handbook
RHO_NICKEL = 8190.0


def hpc_rotor_predictions():
    """E3's stated closure -- the first three modes of every HPC stage
    within 5 % of Figs 33-42 -- cannot be evaluated: those ten diagrams
    were never transcribed. The prediction can still be MADE, from the
    same Table XXII sections E1 used and with E1's own material split
    (titanium stages 1-4, nickel 5-10, which fell out of the stress data
    at the inertia weld). Recorded so that digitising Figs 33-42 is a
    one-line test rather than a fresh piece of work."""
    out = []
    for stage in hpc_rotor_stages():
        m = hpc_rotor_model(stage)
        if m is None:
            continue
        out.append(dict(stage=stage, material="Ti-6Al-4V" if stage <= 4 else "nickel",
                        length_cm=m.length_m * 100,
                        hub_over_length=m.hub_radius_m / m.length_m,
                        modes=m.modes(False, 0.0, 3), stiff=m.modes(True, 0.0, 3)[0]))
    return out


def hpc_rotor_stages():
    from blading.sections import all_sections
    return sorted({s.stage for s in all_sections() if s.kind == "rotor"})


@lru_cache(maxsize=None)
def hpc_rotor_model(stage):
    """Build the beam model for one HPC rotor stage.

    Cached: unit J2 evaluates every stage across nine speeds and three
    modes, and rebuilding the sections each time made the figure take
    minutes. The model is a pure function of the stage number.

    Factored out of `hpc_rotor_predictions` so that unit J2's Campbell
    figure evaluates the SAME model across speed rather than keeping its
    own copy of the material split and the section assembly. Two copies of
    a rule are two chances for it to drift -- see unit J1 finding 159.

    Returns None if any section fails to build."""
    from blading.sections import all_sections
    secs = sorted([s for s in all_sections()
                   if s.kind == "rotor" and s.stage == stage],
                  key=lambda s: s.radius_m)
    if not secs:
        return None
    hub, tip = secs[0].radius_m, secs[-1].radius_m
    ti = stage <= 4                       # E1's split, at the inertia weld
    m = BladeModel(f"HPC rotor {stage}", "Table XXII sections; E1's material split",
                   tip - hub, hub, E_TI_6AL_4V if ti else E_NICKEL,
                   RHO_TI_6AL_4V if ti else RHO_NICKEL,
                   published_f1_Hz=float("nan"), pinned_at=None)
    polys = []
    for sc in secs:
        built = section(sc.chord_m, sc.beta1, sc.beta2, sc.stagger,
                        *_xxii_thickness(sc))
        if built is None:
            return None
        polys.append((sc.radius_m - hub, closed_airfoil(built)))
    _fill(m, polys)
    return m


def _xxii_thickness(sc):
    """Table XXII's tm/c, max-thickness location and trailing-edge thickness
    for one section, looked up again because RowSection does not carry them"""
    import yaml as _y
    from blading.sections import load as _load
    global _XXII
    try:
        _XXII
    except NameError:
        xxii, _ = _load()
        _XXII = xxii
    cols = _XXII["columns"]
    blocks = _XXII["rotors"] if sc.kind == "rotor" else _XXII["stators"]
    blk = next(b for b in blocks if b["stage"] == sc.stage)
    for raw in blk["sections"]:
        r = dict(zip(cols, raw))
        if abs(r["sect_ht_cm"] * CM - sc.radius_m) < 1e-9:
            return r["tm_c"], r["pct_c_tm"], r["tte_c"]
    raise KeyError(sc)


def hpc_vane_check():
    """The ONE HPC frequency Stage A did transcribe: Figs 55-56 of the
    10A-rig report give the stage-9 and stage-10 vane Campbell diagrams,
    first flex 18.3 and 28.5 kHz at zero speed. Table XXII has those
    vanes' sections. A vane is not a cantilever -- it is banded at the
    inner end as well as bolted at the outer -- so the honest prediction
    is the bracket between a cantilever and a beam built in at both
    ends, whose first eigenvalue is 6.36 times the cantilever's."""
    from blading.sections import all_sections
    pub = yaml.safe_load((DATA / "hpc-mechanical.yaml").read_text())["vane_campbell_10A"]
    rows = {}
    for sec in all_sections():
        if sec.kind == "stator":
            rows.setdefault(sec.stage, []).append(sec)
    out = []
    for stage, key in ((9, "stage9_vane"), (10, "stage10_vane")):
        if stage not in rows:
            continue
        secs = sorted(rows[stage], key=lambda s: s.radius_m)
        hub, tip = secs[0].radius_m, secs[-1].radius_m
        m = BladeModel(f"HPC stage-{stage} vane", "Table XXII sections; Figs 55-56",
                       tip - hub, hub, E_NICKEL, RHO_NICKEL,
                       pub[key]["first_flex_kHz"]["at_0"] * 1000.0)
        polys = []
        for sc in secs:
            built = section(sc.chord_m, sc.beta1, sc.beta2, sc.stagger, *_xxii_thickness(sc))
            if built is None:
                polys = None
                break
            polys.append((sc.radius_m - hub, closed_airfoil(built)))
        if not polys:
            continue
        _fill(m, polys)
        free = m.modes(False, 0.0, 1)[0], m.modes(True, 0.0, 1)[0]
        both = m.modes(False, 0.0, 1, tip_clamped=True)[0], \
            m.modes(True, 0.0, 1, tip_clamped=True)[0]
        out.append(dict(stage=stage, length_cm=m.length_m * 100, published=m.published_f1_Hz,
                        cantilever=free, built_in=both,
                        inside=free[0] < m.published_f1_Hz < both[1]))
    return out


def blades():
    fan, _ = fan_rotor()
    return [lpt_stage1(), booster_rotor(), fan]


def fan_shroud_bracket():
    """the fan blade is neither free nor pinned: its part-span shroud at
    55 % height is a partial restraint. Compute both ends."""
    fan, _ = fan_rotor()
    free = fan.modes(False, 0.0, 1)[0], fan.modes(True, 0.0, 1)[0]
    fan.pinned_at = fan.shroud_span
    pinned = fan.modes(False, 0.0, 1)[0], fan.modes(True, 0.0, 1)[0]
    fan.pinned_at = None
    return dict(free=free, pinned=pinned, published=fan.published_f1_Hz,
                shroud_span=fan.shroud_span)


def southwell_table():
    """f_N^2 = f_0^2 + S (N/60)^2. S is a property of the mode shape and of
    the hub radius, so it can be tested even where the absolute frequency
    cannot -- the fan's shroud changes f_0 and f_N together."""
    out = []
    for b in blades():
        rpm, f_pub = b.published_f1_at_speed
        omega = rpm * 2 * math.pi / 60
        s_model, f0m, fnm = b.beam().southwell(omega, b.pinned_at)
        s_pub = (f_pub ** 2 - b.published_f1_Hz ** 2) / (rpm / 60) ** 2
        out.append(dict(name=b.name, rpm=rpm, hub_over_length=b.hub_radius_m / b.length_m,
                        s_model=s_model, s_published=s_pub,
                        f0_model=f0m, fN_model=fnm,
                        f0_pub=b.published_f1_Hz, fN_pub=f_pub,
                        err_pct=(s_model / s_pub - 1) * 100))
    return out


if __name__ == "__main__":
    print("Stage E3 -- blade natural frequency from a validated beam\n")
    print("1. First flex at zero speed, each blade with the tip condition its")
    print("   own report names\n")
    print(f"   {'blade':<15}{'BC':>13}{'L cm':>7}{'R/L':>6}{'weak':>9}{'root-axis':>11}"
          f"{'published':>11}{'weak %':>9}{'stiff %':>9}")
    for b in blades():
        soft, stiff = b.bracket(0.0, 1)
        bc = "pinned tip" if b.pinned_at else "free"
        print(f"   {b.name:<15}{bc:>13}{b.length_m * 100:>7.2f}"
              f"{b.hub_radius_m / b.length_m:>6.2f}{soft[0]:>9.0f}{stiff[0]:>11.0f}"
              f"{b.published_f1_Hz:>11.0f}{(soft[0] / b.published_f1_Hz - 1) * 100:>9.1f}"
              f"{(stiff[0] / b.published_f1_Hz - 1) * 100:>9.1f}")
    print("\n   weak      = every section bends about its own weak axis (softest)")
    print("   root-axis = the whole blade forced to bend about the root's weak axis")
    print("   the real twisted blade is between the two")

    fb = fan_shroud_bracket()
    print(f"\n2. The fan blade is not a cantilever: a part-span shroud at "
          f"{fb['shroud_span'] * 100:.0f} % height")
    print(f"   free at the tip        {fb['free'][0]:>7.0f} - {fb['free'][1]:>4.0f} Hz")
    print(f"   pinned at the shroud   {fb['pinned'][0]:>7.0f} - {fb['pinned'][1]:>4.0f} Hz")
    print(f"   published (Fig 45)     {fb['published']:>7.0f} Hz")
    inside = fb['free'][0] < fb['published'] < fb['pinned'][1]
    print(f"   -> published sits {'INSIDE' if inside else 'OUTSIDE'} the bracket")

    print(f"\n3. Centrifugal stiffening: f_N^2 = f_0^2 + S (N/60)^2")
    print(f"   {'blade':<15}{'rpm':>7}{'R/L':>7}{'S model':>10}{'S published':>13}{'err %':>9}")
    for r in southwell_table():
        print(f"   {r['name']:<15}{r['rpm']:>7}{r['hub_over_length']:>7.2f}"
              f"{r['s_model']:>10.2f}{r['s_published']:>13.2f}{r['err_pct']:>9.1f}")
    print(f"\n4. The ten HPC rotors -- PREDICTED, not validated: Figs 33-42 were")
    print(f"   never transcribed, so E3's stated closure cannot be evaluated")
    print(f"\n   {'stage':>6}{'material':>11}{'L cm':>7}{'R/L':>6}"
          f"{'1F Hz':>9}{'2F Hz':>9}{'3F Hz':>9}{'1F stiff':>10}")
    for r in hpc_rotor_predictions():
        m = r["modes"]
        print(f"   {r['stage']:>6}{r['material']:>11}{r['length_cm']:>7.2f}"
              f"{r['hub_over_length']:>6.2f}{m[0]:>9.0f}{m[1]:>9.0f}{m[2]:>9.0f}"
              f"{r['stiff']:>10.0f}")

    print(f"\n4b. E3's stated closure, no longer gated: the first three flexural")
    print(f"    modes of every HPC stage against Figs 33-42\n")
    print(f"   {'st':>3}{'fig':>5}{'1F pred':>9}{'1F pub':>8}{'err %':>8}"
          f"{'2F pred':>9}{'2F pub':>8}{'err %':>8}{'3F pred':>9}{'3F pub':>8}{'err %':>8}")
    for r in hpc_campbell_comparison():
        cells = []
        for m in r["modes"]:
            cells += [f"{m['predicted']:>9.0f}",
                      f"{m['published']:>8.0f}" if m["published"] else f"{'-':>8}",
                      f"{m['err_pct']:>8.1f}" if m["err_pct"] is not None else f"{'-':>8}"]
        print(f"   {r['stage']:>3}{r['figure']:>5}" + "".join(cells))
    cs = hpc_campbell_summary()
    print(f"\n   {cs['within_5pct']} of {cs['comparisons']} comparisons within E3's 5 % band")
    print(f"   mean error {cs['mean']:+.1f} %, worst {cs['worst']:+.1f} %")
    print(f"   first flex alone: mean {cs['first_flex_mean']:+.1f} %, worst"
          f" {cs['first_flex_worst']:+.1f} %, all over-predicted: {cs['all_positive']}")

    print(f"\n5. The one HPC frequency that WAS transcribed: the stage-9 and")
    print(f"   stage-10 vanes (Figs 55-56 of the 10A rig report)")
    print(f"\n   {'vane':>6}{'L cm':>7}{'cantilever kHz':>20}{'built-in kHz':>18}"
          f"{'published kHz':>15}{'inside?':>9}")
    for r in hpc_vane_check():
        print(f"   {r['stage']:>6}{r['length_cm']:>7.2f}"
              f"{r['cantilever'][0] / 1e3:>11.1f} -{r['cantilever'][1] / 1e3:>7.1f}"
              f"{r['built_in'][0] / 1e3:>10.1f} -{r['built_in'][1] / 1e3:>6.1f}"
              f"{r['published'] / 1e3:>15.1f}{'yes' if r['inside'] else 'NO':>9}")

    print("\n   S is a mode-shape and hub-radius property, not a material one.")
    print("   The model reproduces S = 1.193 for a uniform cantilever at zero hub")
    print("   radius and S = 1.193 + 1.571 (R/L) as the hub grows, so a stubby")
    print("   blade on a big drum stiffens several times more than the textbook")
    print("   case -- see beam.py's validation.")


# ------------------------------------------- E3's closure, no longer gated

def hpc_campbell_comparison():
    """Stage E3's stated closure: the first three modes of every HPC stage
    within 5 % of the published Campbell lines.

    Those ten diagrams (HPC report Figs 33-42) were figure-status until
    2026-09-08 and are now transcribed in `data/hpc-rotor-campbell.yaml`.
    This is the comparison the closure asks for -- run for the first time,
    against predictions that were made and recorded before the diagrams
    were read (finding 88)."""
    pub = yaml.safe_load((DATA / "hpc-rotor-campbell.yaml").read_text())
    by_stage = {s["stage"]: s for s in pub["stages"]}
    out = []
    for r in hpc_rotor_predictions():
        m = by_stage[r["stage"]]["modes"]
        # the beam gives flexural modes only; compare like with like
        want = [m.get("first_flex"), m.get("second_flex"), m.get("third_flex")]
        got = r["modes"]
        rows = []
        for i, (g, w) in enumerate(zip(got, want), start=1):
            rows.append(dict(mode=f"{i}F", predicted=g, published=w,
                             err_pct=None if w is None else (g / w - 1) * 100))
        out.append(dict(stage=r["stage"], material=r["material"],
                        figure=by_stage[r["stage"]]["figure"], modes=rows,
                        first_torsion_published=m.get("first_torsion")))
    return out


def hpc_campbell_summary():
    rows = hpc_campbell_comparison()
    errs = [m["err_pct"] for r in rows for m in r["modes"] if m["err_pct"] is not None]
    first = [m["err_pct"] for r in rows for m in r["modes"]
             if m["mode"] == "1F" and m["err_pct"] is not None]
    return dict(comparisons=len(errs), within_5pct=sum(1 for e in errs if abs(e) <= 5),
                mean=sum(errs) / len(errs), worst=max(errs, key=abs),
                first_flex_mean=sum(first) / len(first),
                first_flex_worst=max(first, key=abs),
                all_positive=all(e > 0 for e in first))
