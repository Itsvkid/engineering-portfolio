"""Stage C4 unit 2: NASA Rotor 37's blade geometry, transcribed and checked.

C4 cannot go near Rotor 37 without its blade. TP-1337's Appendix C has it —
twelve sections from a 7.0000 in hub to a 9.9330 in tip, each as leading-
and trailing-edge radii, a stacking point, a stagger angle and a table of
L / HP / HS. The appendix is a 1978 scan carrying NASA's own "ORIGINAL PAGE
IS OF POOR QUALITY" stamp, and its OCR is unusable: pdftotext returns
"0 .Otis" and "0 .$073" where numbers should be. So the pages were read
directly and transcribed into
`data/methods/rotor37-blade-coordinates.yaml`.

**Nine hundred numbers read off a bad scan is exactly the kind of
transcription that should not be trusted, so this module does not trust
it.** Every check below is a property the real blade must have and a typo
would break: the section has to close on its own printed edge radii at
both ends, the suction surface has to stay outside the pressure surface,
the surfaces have to be smooth, and the stagger has to turn one way as the
radius grows. None of them was used to *produce* a number; they are all
tests of numbers already written down.

STEP0.md, unit C4-2."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA

IN = 0.0254


@dataclass
class Section:
    radius: float                 # inches
    r1: float                     # leading-edge radius
    r2: float                     # trailing-edge radius
    l_sp: float
    h_sp: float
    gamma_deg: float              # stagger, decimal degrees
    l: list
    hp: list
    hs: list

    @property
    def chord(self):
        return self.l[-1]

    @property
    def thickness(self):
        return [s - p for s, p in zip(self.hs, self.hp)]

    @property
    def max_thickness(self):
        return max(self.thickness)

    def camber_line(self):
        return [0.5 * (p + s) for p, s in zip(self.hp, self.hs)]


def load():
    d = yaml.safe_load((DATA / "methods" / "rotor37-blade-coordinates.yaml").read_text())
    out = []
    for s in d["sections"]:
        pts = s["points"]
        out.append(Section(
            radius=s["radius"], r1=s["r1"], r2=s["r2"], l_sp=s["l_sp"], h_sp=s["h_sp"],
            gamma_deg=s["gamma_deg"] + s["gamma_min"] / 60.0,
            l=[p[0] for p in pts], hp=[p[1] for p in pts], hs=[p[2] for p in pts]))
    return out, d["meta"]


# --------------------------------------------------------------- the checks

def closure_check():
    """the section must close on its own printed edge radii at both ends"""
    out = []
    for s in load()[0]:
        out.append(dict(radius=s.radius,
                        le_hp=s.hp[0], le_hs=s.hs[0], r1=s.r1,
                        te_hp=s.hp[-1], te_hs=s.hs[-1], r2=s.r2,
                        le_err=max(abs(s.hp[0] - s.r1), abs(s.hs[0] - s.r1)),
                        te_err=max(abs(s.hp[-1] - s.r2), abs(s.hs[-1] - s.r2))))
    return out


def thickness_check():
    """suction surface outside pressure surface, everywhere"""
    out = []
    for s in load()[0]:
        t = s.thickness
        i = min(range(len(t)), key=lambda k: t[k])
        out.append(dict(radius=s.radius, min_thickness=t[i], at_l=s.l[i],
                        max_thickness=s.max_thickness,
                        tmax_over_chord=s.max_thickness / s.chord))
    return out


def smoothness_check():
    """A misread digit shows up as a kink. Second differences of a real
    blade surface are small; one bad number makes one of them large."""
    out = []
    for s in load()[0]:
        worst = dict(radius=s.radius, worst_surface=None, worst_l=None, worst=0.0)
        for name, y in (("hp", s.hp), ("hs", s.hs)):
            # interior points only: the edges close on the radii by design
            for i in range(2, len(y) - 2):
                d2 = abs(y[i - 1] - 2 * y[i] + y[i + 1])
                scale = s.max_thickness
                if d2 / scale > worst["worst"]:
                    worst.update(worst=d2 / scale, worst_surface=name, worst_l=s.l[i])
        out.append(worst)
    return out


def stagger_check():
    """stagger must turn monotonically from hub to tip on a rotor like this"""
    secs = load()[0]
    g = [s.gamma_deg for s in secs]
    steps = [(secs[i + 1].radius - secs[i].radius, g[i + 1] - g[i]) for i in range(len(g) - 1)]
    rates = [dg / dr for dr, dg in steps]
    return dict(gamma=g, monotonic=all(b > a for a, b in zip(g, g[1:])),
                rates_deg_per_in=rates,
                rate_mean=sum(rates) / len(rates),
                rate_max=max(rates), rate_max_at=secs[rates.index(max(rates)) + 1].radius)


def against_the_design_point():
    """the geometry against Table I, which was transcribed separately"""
    secs, _ = load()
    case = yaml.safe_load((DATA / "methods" / "rotor37-validation-case.yaml").read_text())
    dp = case["design_point"]
    hub, tip = secs[0].radius, secs[-1].radius
    chords = [s.chord for s in secs]
    span = tip - hub
    mean_chord = sum(chords) / len(chords)
    return dict(
        hub_in=hub, tip_in=tip,
        radius_ratio=hub / tip, radius_ratio_published=dp["hub_tip_radius_ratio"],
        radius_ratio_err_pct=(hub / tip / dp["hub_tip_radius_ratio"] - 1) * 100,
        tip_radius_m=tip * IN,
        tip_speed_m_s=tip * IN * dp["rpm"] * 2 * math.pi / 60,
        tip_speed_published=dp["tip_speed_m_s"],
        tip_speed_err_pct=(tip * IN * dp["rpm"] * 2 * math.pi / 60 / dp["tip_speed_m_s"] - 1) * 100,
        span_in=span, mean_chord_in=mean_chord,
        aspect_ratio_from_le_span=span / mean_chord,
        aspect_ratio_published=dp["rotor_aspect_ratio"],
        implied_mean_blade_height_in=dp["rotor_aspect_ratio"] * mean_chord,
        n_sections=len(secs))


if __name__ == "__main__":
    secs, meta = load()
    print(f"NASA Rotor 37 blade, TP-1337 Appendix C: {len(secs)} sections\n")
    print(f"   {'rad in':>8}{'chord':>8}{'t_max':>8}{'t/c':>7}{'stagger':>9}"
          f"{'R1':>8}{'R2':>8}{'pts':>5}")
    for s in secs:
        print(f"   {s.radius:>8.4f}{s.chord:>8.4f}{s.max_thickness:>8.4f}"
              f"{s.max_thickness / s.chord:>7.4f}{s.gamma_deg:>9.3f}"
              f"{s.r1:>8.4f}{s.r2:>8.4f}{len(s.l):>5}")

    print(f"\n1. Does each section close on its own printed edge radii?")
    cl = closure_check()
    print(f"   worst leading edge  {max(c['le_err'] for c in cl):.6f} in")
    print(f"   worst trailing edge {max(c['te_err'] for c in cl):.6f} in")

    print(f"\n2. Is the suction surface outside the pressure surface everywhere?")
    tc = thickness_check()
    w = min(tc, key=lambda r: r["min_thickness"])
    print(f"   thinnest point {w['min_thickness']:+.4f} in at L = {w['at_l']:.2f}"
          f" on the {w['radius']:.4f} in section")
    print(f"   t/c runs {min(r['tmax_over_chord'] for r in tc):.4f} at the tip to"
          f" {max(r['tmax_over_chord'] for r in tc):.4f} at the hub")

    print(f"\n3. Are the surfaces smooth? (second difference over max thickness)")
    sm = smoothness_check()
    for r in sorted(sm, key=lambda r: -r["worst"])[:4]:
        print(f"   {r['radius']:>8.4f}  worst {r['worst']:.3f}  on {r['worst_surface']}"
              f" at L = {r['worst_l']:.2f}")

    st = stagger_check()
    print(f"\n4. Does the stagger turn one way from hub to tip?")
    print(f"   monotonic: {st['monotonic']}")
    print(f"   {' '.join(f'{g:.1f}' for g in st['gamma'])}")
    print(f"   rate {st['rate_mean']:.1f} deg/in mean, {st['rate_max']:.1f} max"
          f" at r = {st['rate_max_at']:.4f}")

    d = against_the_design_point()
    print(f"\n5. Against Table I, transcribed separately")
    print(f"   hub/tip radius ratio  {d['radius_ratio']:.4f} vs published"
          f" {d['radius_ratio_published']}   {d['radius_ratio_err_pct']:+.2f} %")
    print(f"   tip speed at {17188.7:.1f} rpm  {d['tip_speed_m_s']:.1f} vs published"
          f" {d['tip_speed_published']} m/s   {d['tip_speed_err_pct']:+.2f} %")
    print(f"   aspect ratio from the LE span  {d['aspect_ratio_from_le_span']:.3f}"
          f" vs published {d['aspect_ratio_published']}")
    print(f"      -> the published ratio implies a mean blade height of"
          f" {d['implied_mean_blade_height_in']:.3f} in against an LE span of"
          f" {d['span_in']:.3f}")


# ---------------------------------------------------------- the 3-D blade

def placed_section(s: Section, n=120):
    """One section in engine coordinates, in inches.

    The appendix gives each section on its own reference line: L along the
    chord from the leading edge, H perpendicular to it, and GAMMA the angle
    that chord line makes with the axial direction. L(sp), H(sp) locate the
    stacking point, which is the one place the section touches the radial
    stacking axis -- so every section is shifted to put it at the origin
    before being staggered. Getting that wrong stacks the blade on its
    leading edge and leans the whole thing over.

        x_axial = (L - L_sp) cos g - (H - H_sp) sin g
        y_tang  = (L - L_sp) sin g + (H - H_sp) cos g
    """
    g = math.radians(s.gamma_deg)
    cg, sg = math.cos(g), math.sin(g)

    def place(ls, hs):
        out = []
        for l, h in zip(ls, hs):
            dl, dh = l - s.l_sp, h - s.h_sp
            out.append((dl * cg - dh * sg, dl * sg + dh * cg))
        return out

    suction = place(s.l, s.hs)
    pressure = place(s.l, s.hp)
    return suction + list(reversed(pressure))[1:-1]


def blade_solid(scale=IN, shifted=False, trimmed=False):
    """the lofted, capped, sewn blade -- Stage G's machinery, in metres.

    `shifted` puts the hub leading edge at x = 0, which is the flow path's
    own datum. `trimmed` then cuts the blade with the casing less the
    running clearance, which is what the geometry says actually happens:
    Appendix C tabulates sections at fixed radii for manufacture and the
    outermost of them lies outside the casing over its whole chord."""
    from geometry.blades import loft_capped, wrapped_wire
    secs, _ = load()
    dx = sections_against_the_casing()[1] if (shifted or trimmed) else 0.0
    wires = []
    for s in secs:
        pts = [((x + dx) * scale, y * scale) for x, y in placed_section(s)]
        wires.append(wrapped_wire(s.radius * scale, pts))
    solid = loft_capped(wires)
    if trimmed:
        solid = solid.intersect(casing_solid())
    return solid


def blade_report():
    from OCP.BRepCheck import BRepCheck_Analyzer
    secs, _ = load()
    solid = blade_solid()
    bb = solid.BoundingBox()
    # trapezoidal volume from the placed section areas, as Stage G checks it
    from mechanical.beam import polygon_properties
    areas = [polygon_properties([(x * IN, y * IN) for x, y in placed_section(s)])["area"]
             for s in secs]
    radii = [s.radius * IN for s in secs]
    trap = sum(0.5 * (a0 + a1) * (r1 - r0)
               for (r0, a0), (r1, a1) in zip(zip(radii, areas), zip(radii[1:], areas[1:])))
    n = 36
    pitch_tip = 2 * math.pi * secs[-1].radius / n
    pitch_hub = 2 * math.pi * secs[0].radius / n
    return dict(
        valid=BRepCheck_Analyzer(solid.wrapped).IsValid(),
        volume_m3=solid.Volume(), trapezoid_m3=trap,
        err_pct=(solid.Volume() / trap - 1) * 100,
        axial_extent_m=bb.xmax - bb.xmin,
        span_m=(secs[-1].radius - secs[0].radius) * IN,
        blades=n,
        solidity_tip=secs[-1].chord / pitch_tip, solidity_hub=secs[0].chord / pitch_hub,
        pitch_deg=360.0 / n,
        axial_chord_hub_in=secs[0].chord * math.cos(math.radians(secs[0].gamma_deg)),
        axial_chord_tip_in=secs[-1].chord * math.cos(math.radians(secs[-1].gamma_deg)))


def interference():
    """the blade against its neighbour one pitch away -- at 65 deg stagger
    and solidity 1.27 the passages overlap axially, so this is not a
    formality"""
    solid = blade_solid()
    nxt = solid.rotate((0, 0, 0), (1, 0, 0), 360.0 / 36)
    common = solid.intersect(nxt)
    vol = 0.0 if common is None or not common.Solids() else common.Volume()
    return dict(overlap_m3=vol, blade_m3=solid.Volume())


def write_stl(path=None, tol=2.0e-5):
    import cadquery as cq
    from e3cycle.cycle import DATA
    path = path or (DATA.parent / "cfd" / "rotor37" / "blade.stl")
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(cq.Workplane(obj=blade_solid()), str(path),
                        tolerance=tol, angularTolerance=0.1)
    return path


# ------------------------------------------------------------- the annulus

def flow_path():
    d = yaml.safe_load((DATA / "methods" / "rotor37-blade-coordinates.yaml").read_text())
    return d["flow_path"]


def annulus_check():
    """The flow-path table is datumed on the rotor-blade HUB leading edge,
    so it can be checked against Appendix C without any model in between."""
    fp = flow_path()
    secs, _ = load()
    inner = {round(x, 3): r for x, r in fp["inner"]}
    outer = {round(x, 3): r for x, r in fp["outer"]}
    hub_at_le, casing_at_le = inner[0.0], outer[0.0]
    tip_section = secs[-1].radius
    return dict(
        hub_at_le_cm=hub_at_le, hub_at_le_in=hub_at_le / 2.54,
        hub_section_in=secs[0].radius,
        hub_err_in=abs(hub_at_le / 2.54 - secs[0].radius),
        casing_at_le_cm=casing_at_le, casing_at_le_in=casing_at_le / 2.54,
        last_section_in=tip_section,
        gap_at_le_in=casing_at_le / 2.54 - tip_section,
        gap_at_le_mm=(casing_at_le / 2.54 - tip_section) * 25.4,
        running_clearance_mm=0.356,
        hub_rise_cm=fp["inner"][-1][1] - hub_at_le,
        casing_fall_cm=casing_at_le - fp["outer"][-1][1],
        annulus_at_le_cm=casing_at_le - hub_at_le,
        annulus_at_exit_cm=fp["outer"][-1][1] - fp["inner"][-1][1])


# ------------------------------------------------- the tip, and the domain

TIP_CLEARANCE_MM = 0.356        # Rotor 37's running clearance; the CFD
                                # validation report meshes the gap rather
                                # than modelling it


def casing_at(x_cm):
    fp = flow_path()
    pts = fp["outer"]
    if x_cm <= pts[0][0]:
        return pts[0][1]
    if x_cm >= pts[-1][0]:
        return pts[-1][1]
    for (x0, r0), (x1, r1) in zip(pts, pts[1:]):
        if x0 <= x_cm <= x1:
            return r0 + (r1 - r0) * (x_cm - x0) / (x1 - x0)


def hub_at(x_cm):
    fp = flow_path()
    pts = fp["inner"]
    if x_cm <= pts[0][0]:
        return pts[0][1]
    if x_cm >= pts[-1][0]:
        return pts[-1][1]
    for (x0, r0), (x1, r1) in zip(pts, pts[1:]):
        if x0 <= x_cm <= x1:
            return r0 + (r1 - r0) * (x_cm - x0) / (x1 - x0)


def blade_axial_range_in():
    """where the blade actually sits, from the placed sections"""
    secs, _ = load()
    xs = [x for s in secs for x, _ in placed_section(s)]
    return min(xs), max(xs)


def sections_against_the_casing():
    """Which printed sections lie outside the casing, and where.

    The flow path is datumed on the rotor-blade HUB leading edge, so the
    placed blade has to be shifted to put that point at x = 0 before the
    two can be compared at all. Once it is, only the outermost section
    exceeds the casing -- and it does so over its entire chord."""
    secs, _ = load()
    shift = -placed_section(secs[0])[0][0]
    out = []
    for sec in secs:
        xs = [pt[0] + shift for pt in placed_section(sec)]
        le, te = xs[0], max(xs)
        out.append(dict(radius=sec.radius, le_x_in=le, te_x_in=te,
                        casing_at_le_in=casing_at(le * 2.54) / 2.54,
                        casing_at_te_in=casing_at(te * 2.54) / 2.54,
                        outside_at_te=sec.radius > casing_at(te * 2.54) / 2.54,
                        outside_at_le=sec.radius > casing_at(le * 2.54) / 2.54))
    return out, shift


def casing_solid(clearance_mm=TIP_CLEARANCE_MM, pad_in=0.4):
    """everything inside the casing less the running clearance, as a solid
    of revolution about the engine axis"""
    import cadquery as cq
    x0, x1 = blade_axial_range_in()
    shift = sections_against_the_casing()[1]
    lo, hi = x0 + shift - pad_in, x1 + shift + pad_in
    dr = clearance_mm / 25.4
    xs = [lo + (hi - lo) * i / 60 for i in range(61)]
    prof = [(x * IN, (casing_at(x * 2.54) / 2.54 - dr) * IN) for x in xs]
    pts = [(prof[0][0], 0.0)] + prof + [(prof[-1][0], 0.0)]
    return (cq.Workplane("XZ").polyline(pts).close()
            .revolve(360, (0, 0, 0), (1, 0, 0)).val())


def trimmed_blade_height():
    """what the casing leaves. The published aspect ratio of 1.19 needs a
    mean blade height of 2.599 in against a leading-edge span of 2.933
    (finding 130); this is where that height comes from."""
    secs, _ = load()
    rows, shift = sections_against_the_casing()
    hub_le_x, hub_te_x = rows[0]["le_x_in"], rows[0]["te_x_in"]
    h_le = casing_at(hub_le_x * 2.54) / 2.54 - hub_at(hub_le_x * 2.54) / 2.54
    h_te = casing_at(hub_te_x * 2.54) / 2.54 - hub_at(hub_te_x * 2.54) / 2.54
    mean_chord = sum(sec.chord for sec in secs) / len(secs)
    case = yaml.safe_load((DATA / "methods" / "rotor37-validation-case.yaml").read_text())
    ar_pub = case["design_point"]["rotor_aspect_ratio"]
    return dict(height_le_in=h_le, height_te_in=h_te, mean_height_in=0.5 * (h_le + h_te),
                mean_chord_in=mean_chord,
                aspect_ratio=0.5 * (h_le + h_te) / mean_chord,
                aspect_ratio_published=ar_pub,
                err_pct=(0.5 * (h_le + h_te) / mean_chord / ar_pub - 1) * 100)


def x_max_for_radius(r_in, clearance_mm=TIP_CLEARANCE_MM):
    """the furthest downstream a section at radius r can reach before the
    casing (less the running clearance) cuts it"""
    dr = clearance_mm / 25.4
    lo, hi = -0.5, 3.0
    if casing_at(hi * 2.54) / 2.54 - dr > r_in:
        return hi
    if casing_at(lo * 2.54) / 2.54 - dr < r_in:
        return lo
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if casing_at(mid * 2.54) / 2.54 - dr > r_in:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def trimmed_sections(extra=14, clearance_mm=TIP_CLEARANCE_MM):
    """The blade as the casing leaves it.

    Appendix C tabulates sections at fixed radii for manufacture, and the
    outermost of them lies outside the casing over its whole chord. The
    physical blade is machined to the casing line less the running
    clearance, so each section is clipped where it crosses it. Because the
    casing falls through the rotor, that clip takes the outer *trailing*
    corner off -- which is where the published aspect ratio's missing blade
    height went (finding 130).

    Sections are added by interpolation above the last unclipped one, so
    the trimmed corner is resolved rather than cut in one step."""
    secs, _ = load()
    shift = sections_against_the_casing()[1]

    def interp_section(r):
        a, b = secs[-2], secs[-1]
        f = (r - a.radius) / (b.radius - a.radius)
        ls = [la + f * (lb - la) for la, lb in zip(a.l, b.l)]
        hp = [x + f * (y - x) for x, y in zip(a.hp, b.hp)]
        hs = [x + f * (y - x) for x, y in zip(a.hs, b.hs)]
        return Section(radius=r, r1=a.r1 + f * (b.r1 - a.r1), r2=a.r2 + f * (b.r2 - a.r2),
                       l_sp=a.l_sp + f * (b.l_sp - a.l_sp),
                       h_sp=a.h_sp + f * (b.h_sp - a.h_sp),
                       gamma_deg=a.gamma_deg + f * (b.gamma_deg - a.gamma_deg),
                       l=ls, hp=hp, hs=hs)

    r_top = casing_at(0.0) / 2.54 - clearance_mm / 25.4
    all_secs = list(secs[:-1])
    for i in range(1, extra + 1):
        all_secs.append(interp_section(secs[-2].radius
                                       + (r_top - secs[-2].radius) * i / extra))

    out = []
    for sec in all_secs:
        pts = [(x + shift, y) for x, y in placed_section(sec)]
        xm = x_max_for_radius(sec.radius, clearance_mm)
        kept = [p for p in pts if p[0] <= xm]
        if len(kept) < 8:
            continue
        out.append(dict(radius=sec.radius, x_max=xm, points=kept,
                        clipped=len(kept) < len(pts),
                        kept_frac=len(kept) / len(pts)))
    return out


def trimmed_solid():
    from geometry.blades import loft_capped, wrapped_wire
    rows = trimmed_sections()
    wires = [wrapped_wire(r["radius"] * IN, [(x * IN, y * IN) for x, y in r["points"]])
             for r in rows]
    return loft_capped(wires), rows
