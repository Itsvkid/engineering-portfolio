"""Stage E unit E8: gas bending, and the tilt that cancels it.

The plan asks for gas bending from the C1 loads compared against Table X's
`max_root_stress`. Table X gives a maximum and a centrifugal part and
nothing between them. **LPT Table VIII is the better target**: it prints
the whole decomposition per stage -- centrifugal at pitch and root, the
**uncorrected gas bending at the root**, and the leading-edge **resultant**
-- and its own note says why the first exceeds the third:

> "Uncorrected" gas bending is before the stacking tilt that cancels it
> against centrifugal bending.

That sentence is the design idea in one line, and it is checkable.

The load comes from the mean-line and nowhere else: tangential force from
the change in swirl, axial force from the change in axial velocity plus
the static pressure drop over the annulus, both applied at mid-span, and
the root moment resolved onto the **principal axes of the root section**
computed from the transcribed coordinates.

What this does not do is reproduce the tilt angle. Table X's own
transcription note records tilt as *omitted -- stages 8-10 print as
percentage LMI rather than radians*, and the LPT table does not print it.
The cancellation is checked as an inequality instead: the published
resultant must be below the published uncorrected bending, on every stage.

STEP0.md, unit E8."""
from __future__ import annotations

import math

import yaml

from e3cycle.cycle import DATA

CM = 0.01
#: the band stated in STEP0 before the run
BAND_PCT = 25.0


def _lpt():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


def published():
    """LPT Table VIII, as printed."""
    t = _lpt()["airfoil_stress_takeoff"]
    return [dict(stage=s, centrifugal_root=cr, centrifugal_pitch=cp,
                 resultant_root=rr, resultant_pitch=rp, gas_bending_root=gb)
            for s, cr, cp, rr, rp, gb in zip(
                t["stage"], t["centrifugal_root_MPa"], t["centrifugal_pitch_MPa"],
                t["leading_edge_resultant_root_MPa"],
                t["leading_edge_resultant_pitch_MPa"],
                t["uncorrected_gas_bending_root_MPa"])]


def _stages():
    from meanline.lpt import run
    return [x for x in run() if isinstance(x, list)][0]


def _core_flow():
    """LPT inlet flow, station 45, from the same cycle the mean-line ran."""
    from meanline.lpt import run
    for x in run():
        st = getattr(x, "stations", None) or (x if isinstance(x, dict) else None)
        if isinstance(st, dict) and "w45" in st:
            return st["w45"]
        if isinstance(st, dict) and "stations" in st:
            return st["stations"]["w45"]
    raise KeyError("w45 not found in the mean-line result")


def root_section_properties(stage):
    """Principal second moments and extreme-fibre distances of the root
    section, from the transcribed coordinates. The 10 % section is the
    lowest published; it stands for the root, and that is a stated
    approximation rather than a hidden one."""
    from meanline.sections import load_section
    from mechanical.beam import closed_airfoil, polygon_properties
    IN = 0.0254
    pts = [(z * IN, t * IN) for z, t in closed_airfoil(load_section(f"R{stage}", 10))]
    p = polygon_properties(pts)
    th = math.radians(p["principal_angle_deg"])
    c, s = math.cos(th), math.sin(th)
    # extreme fibre distance along each principal axis
    u = [(x - p["cx"]) * c + (y - p["cy"]) * s for x, y in pts]
    v = [-(x - p["cx"]) * s + (y - p["cy"]) * c for x, y in pts]
    return dict(area=p["area"], i_min=p["i_min"], i_max=p["i_max"],
                principal_angle_deg=p["principal_angle_deg"],
                c_min=max(abs(min(v)), abs(max(v))),
                c_max=max(abs(min(u)), abs(max(u))))


def gas_loads():
    """Per-blade tangential and axial force at the mean line."""
    rb = _lpt()["rotor_blades"]
    w = _core_flow()
    out = []
    for i, s in enumerate(_stages()):
        n = rb["blade_count"][i]
        m_blade = w / n
        ct2 = s.cx2 * math.tan(math.radians(s.alpha2))
        ct3 = s.cx3 * math.tan(math.radians(s.alpha3))
        # The mean-line stores alpha3 as a MAGNITUDE and the stage exit is
        # counter-swirled, so the swirl CHANGE across the rotor is the sum
        # and not the difference. Checked against Euler work rather than
        # asserted: dh/U agrees with ct2 + ct3 to 4 % on all five stages
        # and with ct2 - ct3 by a factor of 1.4 to 3.8 (finding 176).
        f_theta = m_blade * (ct2 + ct3)
        # annulus area at the rotor exit, from the mean radius and the span
        length = rb["blade_length_cm"][i] * CM
        a_ann = 2 * math.pi * s.r3 * length
        f_axial = m_blade * (s.cx2 - s.cx3) + (s.ps2 - s.ps3) * a_ann / n
        out.append(dict(stage=s.n, blades=n, m_blade=m_blade, length=length,
                        f_theta=f_theta, f_axial=f_axial,
                        ct2=ct2, ct3=ct3))
    return out


def euler_check(cp=1150.0):
    """The guard that caught finding 176. Euler's dh = U x delta_c_theta is
    an identity, so the swirl change taken from the stored angles must
    reproduce the enthalpy drop the mean-line already solved for. If a sign
    convention is misread, this is where it shows."""
    out = []
    for s in _stages():
        dh = cp * (s.t01 - s.t03)
        u = (s.u2 + s.u3) / 2
        ct2 = s.cx2 * math.tan(math.radians(s.alpha2))
        ct3 = s.cx3 * math.tan(math.radians(s.alpha3))
        out.append(dict(stage=s.n, dct_from_work=dh / u, sum_convention=ct2 + ct3,
                        difference_convention=ct2 - ct3,
                        err_pct=((ct2 + ct3) / (dh / u) - 1) * 100))
    return out


def bending():
    """Root bending stress from the mid-span resultant, resolved onto the
    root section's principal axes."""
    out = []
    for load in gas_loads():
        p = root_section_properties(load["stage"])
        # moment at the root from a resultant at mid-span
        m_theta = load["f_theta"] * load["length"] / 2
        m_axial = load["f_axial"] * load["length"] / 2
        th = math.radians(p["principal_angle_deg"])
        # the tangential force bends about the axis perpendicular to it;
        # resolve both moments onto the principal pair
        m_u = m_theta * math.cos(th) + m_axial * math.sin(th)
        m_v = -m_theta * math.sin(th) + m_axial * math.cos(th)
        sigma = (abs(m_v) * p["c_min"] / p["i_min"]
                 + abs(m_u) * p["c_max"] / p["i_max"]) / 1e6
        out.append(dict(stage=load["stage"], f_theta=load["f_theta"],
                        f_axial=load["f_axial"], m_theta=m_theta,
                        m_axial=m_axial, sigma_MPa=sigma,
                        i_min=p["i_min"], i_max=p["i_max"]))
    return out


def comparison():
    pub = {p["stage"]: p for p in published()}
    out = []
    for b in bending():
        p = pub[b["stage"]]
        out.append(dict(
            stage=b["stage"], predicted_MPa=b["sigma_MPa"],
            published_MPa=p["gas_bending_root"],
            err_pct=(b["sigma_MPa"] / p["gas_bending_root"] - 1) * 100,
            resultant_MPa=p["resultant_root"],
            centrifugal_MPa=p["centrifugal_root"]))
    return out


def the_tilt_cancels():
    """The report's own sentence, as an inequality: if the stacking tilt
    cancels gas bending against centrifugal bending, the resultant must sit
    below the uncorrected value. Not a tolerance -- a sign check."""
    rows = []
    for p in published():
        rows.append(dict(stage=p["stage"], uncorrected=p["gas_bending_root"],
                         resultant=p["resultant_root"],
                         cancelled_pct=(1 - p["resultant_root"]
                                        / p["gas_bending_root"]) * 100,
                         holds=p["resultant_root"] < p["gas_bending_root"]))
    return dict(rows=rows, all_hold=all(r["holds"] for r in rows),
                mean_cancelled_pct=sum(r["cancelled_pct"] for r in rows) / len(rows))


def summary():
    c = comparison()
    t = the_tilt_cancels()
    worst = max(abs(r["err_pct"]) for r in c)
    L = ["Stage E unit E8 -- gas bending at the LPT blade root", ""]
    L.append(f"   {'stg':>3}{'F_theta N':>11}{'F_axial N':>11}"
             f"{'predicted':>11}{'published':>11}{'err %':>9}")
    for r, ld in zip(c, bending()):
        L.append(f"   {r['stage']:>3}{ld['f_theta']:>11.1f}{ld['f_axial']:>11.1f}"
                 f"{r['predicted_MPa']:>11.1f}{r['published_MPa']:>11.1f}"
                 f"{r['err_pct']:>9.1f}")
    L += ["", f"   worst {worst:.1f} % against a {BAND_PCT:.0f} % band -- "
          f"{'INSIDE' if worst <= BAND_PCT else 'OUTSIDE'}"]
    L += ["", "   the tilt cancels (the report's own sentence, as an inequality):"]
    for r in t["rows"]:
        L.append(f"      stage {r['stage']}: uncorrected {r['uncorrected']:6.1f} "
                 f"-> resultant {r['resultant']:6.1f} MPa, "
                 f"{r['cancelled_pct']:5.1f} % cancelled  "
                 f"{'ok' if r['holds'] else 'FAILS'}")
    L.append(f"   holds on all five: {t['all_hold']}; "
             f"mean cancellation {t['mean_cancelled_pct']:.0f} %")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
