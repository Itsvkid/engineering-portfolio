"""C3 unit 12: reconstruct every HPC blade section from Table XXII, and
check that its throat passes the flow Table XXI puts through it.

Table XXII prints, for each of 252 sections: chord, camber, stagger, the
metal angles beta1* and beta2*, the maximum thickness and where it sits,
and the trailing-edge thickness. It does not print the camber-line family
or the throat.

The camber line is built as a double circular arc -- two arcs meeting
where the tangent is parallel to the chord -- with the join position
solved so that the section reproduces beta1*, beta2* AND the printed
stagger exactly. The thickness is the quarter-sine distribution the fan
report documents for this engine (CR-165148 sec II.A), scaled to the
printed maximum and trailing-edge thicknesses. STEP0.md, unit 12."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA

CM = 0.01


def load():
    xxii = yaml.safe_load((DATA / "hpc-blade-sections.yaml").read_text())
    xxi = yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())
    return xxii, xxi


def implied_max_camber(beta1, beta2, stagger):
    """where the double-circular-arc camber line's tangent is parallel to
    the chord, from the printed stagger:  f tan(t1/2) = (1-f) tan(t2/2)"""
    a = math.tan(math.radians((beta1 - stagger) / 2))
    b = math.tan(math.radians((stagger - beta2) / 2))
    if abs(a + b) < 1e-12:
        return None
    return b / (a + b)


def camber_line(beta1, beta2, stagger, n=400):
    """(x, y) along the chord, chord from (0,0) to (1,0)"""
    f = implied_max_camber(beta1, beta2, stagger)
    if f is None or not (0.02 < f < 0.98):
        return None, f
    t1 = math.radians(beta1 - stagger)
    t2 = math.radians(stagger - beta2)
    pts = []
    for i in range(n + 1):
        x = i / n
        if x <= f:
            # arc from (0,0), tangent angle t1, turning to 0 at x = f
            frac = x / f if f else 0.0
            ang = t1 * (1 - frac)
            # chord of the partial arc makes angle (t1 + ang)/2
            y = x * math.tan((t1 + ang) / 2)
        else:
            frac = (x - f) / (1 - f)
            ang = -t2 * frac
            y_f = f * math.tan(t1 / 2)
            y = y_f + (x - f) * math.tan((0 + ang) / 2)
        pts.append((x, y))
    return pts, f


def thickness(x, tm_c, a, te_c):
    """quarter-sine to the maximum, reversed to the trailing edge
    (CR-165148 sec II.A, the E3's own documented distribution)"""
    if x <= a:
        return tm_c * math.sin(0.5 * math.pi * (x / a if a else 0.0))
    return te_c + (tm_c - te_c) * math.sin(0.5 * math.pi * (1 - x) / (1 - a))


def section(chord_m, beta1, beta2, stagger, tm_c, pct_c_tm, te_c, n=400):
    """suction and pressure surfaces in blade-row coordinates (axial x,
    tangential y), scaled to the real chord"""
    cl, f = camber_line(beta1, beta2, stagger, n)
    if cl is None:
        return None
    a = pct_c_tm / 100.0
    g = math.radians(stagger)
    suc, pre, cam = [], [], []
    for i, (x, y) in enumerate(cl):
        # camber-line tangent
        if i == 0:
            dx, dy = cl[1][0] - x, cl[1][1] - y
        elif i == len(cl) - 1:
            dx, dy = x - cl[-2][0], y - cl[-2][1]
        else:
            dx, dy = cl[i + 1][0] - cl[i - 1][0], cl[i + 1][1] - cl[i - 1][1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        t = 0.5 * thickness(x, tm_c, a, te_c)
        for lst, s in ((suc, +1), (pre, -1)):
            xi, yi = x + s * t * nx, y + s * t * ny
            # rotate the chord line to the stagger angle, scale to the chord
            lst.append((chord_m * (xi * math.cos(g) - yi * math.sin(g)),
                        chord_m * (xi * math.sin(g) + yi * math.cos(g))))
        cam.append((chord_m * (x * math.cos(g) - y * math.sin(g)),
                    chord_m * (x * math.sin(g) + y * math.cos(g))))
    return dict(suction=suc, pressure=pre, camber=cam, f=f)


def throat(sec, pitch):
    """minimum distance from the suction surface of one blade to the
    pressure surface of the next, which sits one pitch away in y"""
    suc, pre = sec["suction"], sec["pressure"]
    nxt = [(x, y + pitch) for x, y in pre]
    best, at = float("inf"), None
    # a compressor passage is diffusing, so its throat sits near the INLET,
    # not near the trailing edge as in a turbine. Scan the whole surface.
    for i in range(len(suc)):
        px, py = suc[i]
        for qx, qy in nxt:
            dsq = (px - qx) ** 2 + (py - qy) ** 2
            if dsq < best:
                best, at = dsq, i / (len(suc) - 1)
    return math.sqrt(best), at


@dataclass
class RowSection:
    kind: str
    stage: int
    sl: int
    radius_m: float
    chord_m: float
    beta1: float
    beta2: float
    stagger: float
    camber: float
    count: int
    pitch_m: float
    o_over_s: float
    cos_beta1: float
    f: float
    at_chord: float


def all_sections(step=1):
    xxii, xxi = load()
    cols = xxii["columns"]
    counts = {}
    for row in xxi["rows"]:
        if row["row"] == "igv":
            counts[("igv", 0)] = row.get("vane_count")
        else:
            counts[(row["row"], row["stage"])] = row.get("blade_count") or row.get("vane_count")
    out = []
    for key, blocks in (("rotor", xxii["rotors"]), ("stator", xxii["stators"])):
        for blk in blocks:
            n = counts.get((key, blk["stage"]))
            if not n:
                continue
            for i, raw in enumerate(blk["sections"][::step]):
                r = dict(zip(cols, raw))
                sl = i * step + 1
                radius = r["sect_ht_cm"] * CM
                pitch = 2 * math.pi * radius / n
                sec = section(r["chord_cm"] * CM, r["beta1"], r["beta2"], r["stagger"],
                              r["tm_c"], r["pct_c_tm"], r["tte_c"])
                if sec is None:
                    continue
                o, at = throat(sec, pitch)
                out.append(RowSection(key, blk["stage"], sl, radius, r["chord_cm"] * CM,
                                      r["beta1"], r["beta2"], r["stagger"], r["camber"], n, pitch,
                                      o / pitch, math.cos(math.radians(r["beta1"])), sec["f"], at))
    return out


if __name__ == "__main__":
    import statistics
    secs = all_sections(step=3)
    print(f"{'row':<9}{'sl':>3}{'r cm':>7}{'chord':>7}{'pitch':>7}{'s/c':>6}"
          f"{'b2':>7}{'camber':>8}{'f %':>6}{'o/s':>7}{'cos b1':>8}{'diff':>7}{'at %c':>7}")
    for s in secs:
        print(f"{s.kind[0].upper()}{s.stage:<8}{s.sl:>3}{s.radius_m*100:>7.1f}{s.chord_m*100:>7.2f}"
              f"{s.pitch_m*100:>7.2f}{s.pitch_m/s.chord_m:>6.2f}{s.beta2:>7.2f}{s.camber:>8.2f}"
              f"{s.f*100:>6.0f}{s.o_over_s:>7.3f}{s.cos_beta1:>8.3f}{s.o_over_s-s.cos_beta1:>7.3f}{s.at_chord*100:>7.0f}")
    d = [s.o_over_s - s.cos_beta1 for s in secs]
    print(f"\n{len(secs)} sections: o/s - cos(beta1*) mean {statistics.mean(d):+.3f}, "
          f"rms {math.sqrt(sum(x*x for x in d)/len(d)):.3f}")


# ---------------------------------------------------------------------------
# Does the throat pass the flow? The HPC report states the answer for its
# transonic rows: "throat area 6 percent above critical, with one normal
# shock at the inlet Mach assumed ahead of the throat" (hpc-stagewise.yaml).
# ---------------------------------------------------------------------------
GAMMA = 1.40


def area_ratio(mach, g=GAMMA):
    """A/A* for isentropic flow"""
    return (1.0 / mach) * ((2.0 / (g + 1)) * (1 + 0.5 * (g - 1) * mach ** 2)) ** ((g + 1) / (2 * (g - 1)))


def normal_shock(mach, g=GAMMA):
    """downstream Mach and total-pressure ratio across a normal shock"""
    m2 = math.sqrt((1 + 0.5 * (g - 1) * mach ** 2) / (g * mach ** 2 - 0.5 * (g - 1)))
    p0 = (((g + 1) * mach ** 2 / (2 + (g - 1) * mach ** 2)) ** (g / (g - 1))
          * ((g + 1) / (2 * g * mach ** 2 - (g - 1))) ** (1 / (g - 1)))
    return m2, p0


def throat_margin(o_over_s, beta1_deg, mach_rel):
    """how far the throat sits above the area that would just choke it.

    The capture area of one passage is s*cos(beta1) per unit span, and the
    throat is o. For the throat to pass the flow it must exceed A*, and for
    a supersonic inlet the report's rule puts one normal shock ahead of the
    throat, which lowers the total pressure and so raises A*."""
    capture = math.cos(math.radians(beta1_deg))
    if mach_rel <= 1.0:
        a_min = capture / area_ratio(mach_rel)
        return o_over_s / a_min - 1.0, 1.0
    _, p0_ratio = normal_shock(mach_rel)
    a_min = capture / area_ratio(mach_rel) / p0_ratio
    return o_over_s / a_min - 1.0, p0_ratio


def rotor_throat_margins(step=1):
    """every rotor section's throat margin, with Table XXI's inlet relative
    Mach at the same streamline"""
    xxii, xxi = load()
    cols = xxii["columns"]
    mrel, counts = {}, {}
    for row in xxi["rows"]:
        if row["row"] != "rotor":
            continue
        counts[row["stage"]] = row["blade_count"]
        c = xxi["columns"]["rotor_station"]
        for raw in row["inlet"]:
            r = dict(zip(c, raw))
            mrel[(row["stage"], r["sl"])] = r["m_rel"]
    out = []
    for blk in xxii["rotors"]:
        n = counts.get(blk["stage"])
        for i, raw in enumerate(blk["sections"][::step]):
            r = dict(zip(cols, raw))
            sl = i * step + 1
            m = mrel.get((blk["stage"], sl))
            if m is None:
                continue
            radius = r["sect_ht_cm"] * CM
            pitch = 2 * math.pi * radius / n
            sec = section(r["chord_cm"] * CM, r["beta1"], r["beta2"], r["stagger"],
                          r["tm_c"], r["pct_c_tm"], r["tte_c"])
            if sec is None:
                continue
            o, at = throat(sec, pitch)
            margin, p0 = throat_margin(o / pitch, r["beta1"], m)
            out.append(dict(stage=blk["stage"], sl=sl, m_rel=m, o_over_s=o / pitch,
                            beta1=r["beta1"], margin=margin, shock_p0=p0,
                            transonic=blk["stage"] <= 4, at=at))
    return out
