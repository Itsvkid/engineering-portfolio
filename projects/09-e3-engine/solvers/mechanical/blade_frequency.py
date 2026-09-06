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

import numpy as np
import yaml

from blading.sections import section
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
    d = _lpt()
    rb = d["rotor_blades"]
    length = rb["blade_length_cm"][0] * CM
    cam = d["stage1_blade_campbell"]["natural_frequencies_Hz"]["first_flex"]

    spans, radii, polys = [10, 50, 90], [], []
    for sp in spans:
        pts = load_section("R1", sp)
        poly = [(z * IN, t * IN) for z, t in closed_airfoil(pts)]
        rs = []
        with open(DATA / "lpt-airfoils" / f"R1_{sp}.csv") as f:
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
    m = BladeModel("LPT stage 1", "CR-168289 Fig 62 (pinned tip), appendix coordinates",
                   length, hub, E_RENE77, RHO_RENE77,
                   cam["at_0_rpm"], (4000, cam["at_4000_rpm"]), pinned_at=1.0)
    return _fill(m, [(f * length, poly) for f, poly in zip((0.10, 0.50, 0.90), polys)])


def _built_sections(chord_cm, camber_deg, stagger_deg, tm_c_pct, edge_c_pct, pct_c_tm_list):
    """double-circular-arc camber, quarter-sine thickness -- the E3's own
    documented construction (CR-165148 sec II.A), as C3 unit 12 uses it.
    Camber is split symmetrically about the stagger, which is the circular-
    arc case; only the section SHAPE enters a second moment, not the
    absolute angles."""
    out = []
    for c, cam, stg, tmc, ec, a in zip(chord_cm, camber_deg, stagger_deg,
                                       tm_c_pct, edge_c_pct, pct_c_tm_list):
        b1, b2 = stg + cam / 2, stg - cam / 2
        sec = section(c * CM, b1, b2, stg, tmc / 100, a, ec / 100)
        if sec is None:
            return None
        out.append(closed_airfoil(sec))
    return out


def fan_rotor():
    f = _fan()
    g = f["fan_rotor_mechanical"]["blade_geometry"]
    a = f["fan_rotor_airfoil"]
    fig15 = a["fig15"]
    hub, tip = fig15["r_sa_id_in"] * IN, fig15["r_sa_od_in"] * IN
    length = fig15["blade_height_in"] * IN
    cam = f["fan_rotor_mechanical"]["campbell"]

    # the maximum-thickness location is printed at the hub (42 % chord) and
    # at the tip (59 %); taken linearly between. The shroud-region values
    # (55, 58) are printed too and are recorded, not used.
    loc = a["max_thickness_location_pct_chord"]
    ats = [loc["hub"] + (loc["tip"] - loc["hub"]) * h / 100 for h in g["height_pct"]]
    polys = _built_sections([c * IN / CM for c in g["chord_in"]], g["camber_deg"],
                            g["stagger_deg"], g["tm_c_pct"], g["tle_c_pct"], ats)
    m = BladeModel("fan rotor", "CR-165148 Fig 41 (geometry), Fig 45 (Campbell)",
                   length, hub, E_TI_6AL_4V, RHO_TI_6AL_4V,
                   cam["modes_Hz"]["first_flex"]["at_0"],
                   (cam["max_speed_rpm"], cam["modes_Hz"]["first_flex"]["at_3653_lowest_in_phase"]),
                   pinned_at=None)
    m.shroud_span = f["fan_rotor_mechanical"]["shroud"]["span_pct"] / 100
    return _fill(m, [(h / 100 * length, p) for h, p in zip(g["height_pct"], polys)]), tip


def booster_rotor():
    f = _fan()
    g = f["booster_blade_mechanical"]["geometry"]
    b = f["booster_rotor_airfoil"]
    ap = f["aero_parameters"]
    tip = ap["tip_diameter_cm"][1] / 200
    hub = tip * ap["radius_ratio_inlet"][1]
    length = tip - hub
    cam = f["booster_blade_mechanical"]["campbell"]

    # CR-165148 prints the booster's thickness law ("quarter-sine to
    # maximum then 65-series") but not where the maximum sits; 50 % chord,
    # stated as an assumption.
    polys = _built_sections([c * IN / CM for c in g["chord_in"]], g["camber_deg"],
                            g["stagger_deg"], g["tm_c_pct"], g["te_c_pct"],
                            [50.0] * len(g["height_pct"]))
    m = BladeModel("booster rotor", "CR-165148 Fig 52 (geometry), Fig 55 (Campbell)",
                   length, hub, E_TI_6AL_4V, RHO_TI_6AL_4V,
                   cam["modes_Hz"]["first_flex"]["at_0"],
                   (cam["max_speed_rpm"], cam["modes_Hz"]["first_flex"]["at_3653"]),
                   pinned_at=None)
    return _fill(m, [(h / 100 * length, p) for h, p in zip(g["height_pct"], polys)])


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
    from blading.sections import all_sections
    rows = {}
    for sec in all_sections():
        if sec.kind != "rotor":
            continue
        rows.setdefault(sec.stage, []).append(sec)
    out = []
    for stage in sorted(rows):
        secs = sorted(rows[stage], key=lambda s: s.radius_m)
        hub, tip = secs[0].radius_m, secs[-1].radius_m
        length = tip - hub
        ti = stage <= 4
        m = BladeModel(f"HPC rotor {stage}", "Table XXII sections; E1's material split",
                       length, hub, E_TI_6AL_4V if ti else E_NICKEL,
                       RHO_TI_6AL_4V if ti else RHO_NICKEL,
                       published_f1_Hz=float("nan"), pinned_at=None)
        polys = []
        for sc in secs:
            built = section(sc.chord_m, sc.beta1, sc.beta2, sc.stagger,
                            *_xxii_thickness(sc))
            if built is None:
                polys = None
                break
            polys.append((sc.radius_m - hub, closed_airfoil(built)))
        if not polys:
            continue
        _fill(m, polys)
        out.append(dict(stage=stage, material="Ti-6Al-4V" if ti else "nickel",
                        length_cm=length * 100, hub_over_length=hub / length,
                        modes=m.modes(False, 0.0, 3), stiff=m.modes(True, 0.0, 3)[0]))
    return out


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
