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
