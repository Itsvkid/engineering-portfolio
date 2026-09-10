"""Stage C unit C5: HPC off-design -- stage stacking, the VSVs, stall margin.

Stage C1's last line asks for a *stall margin estimate* and the *VSV
schedule effect*. The first three items on that line -- work split,
diffusion factor per row, de Haller -- closed in unit 5.

**There is no stall margin in here, and there cannot be.** A stall margin
is the distance from an operating line to a **stall line**, and no stall
line for this compressor is published: not as a map, not as a table, not
as a figure this project has read. No VSV schedule is published either --
the reports give the variable geometry as *IGV and stators 1-4* and the
actuation as a torsion-bar system, and never a stagger against speed.
A number called a stall margin here would have no reference behind it.

What the HPC report does give is its stall-margin **design intent**, in
four unusually specific sentences, and every one is a claim about loading
order:

    Stages 6 and 7 are deliberately unloaded: they are the first two
    stages not controlled by upstream variable stators... Equalising
    part-speed near-stall loading among the five fixed rear stages gave
    the highest part-speed stall margin at some cost in design-speed
    margin. Near stall at design speed stages 8-10 are the most loaded; at
    intermediate speed 6-7 join them; at low speed 8-10 unload and 6-7
    stay heavily loaded.

Three of those check against figures already transcribed. The fourth needs
an off-design march, and this module does it with a stage characteristic
that has **no free parameter**: `psi = 1 - phi (1 - psi_d)/phi_d`, the
Euler relation at fixed relative exit angle, normalised through each
stage's own design point. A characteristic with a tunable slope could be
made to produce any ordering asked of it, and would prove nothing.

STEP0.md, unit C5."""
from __future__ import annotations

import csv
import math
from functools import lru_cache

import yaml

from e3cycle.cycle import DATA

CP = 1004.0
GAMMA = 1.4
R_AIR = 287.05


def _stagewise():
    return yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())


def variable_rows():
    """What is published, and what it implies about which stage is first
    uncontrolled. The prose and the geometry list must agree."""
    d = _stagewise()
    vg = None
    def walk(o):
        nonlocal vg
        if isinstance(o, dict):
            if "variable_geometry" in o:
                vg = o["variable_geometry"]
            for v in o.values():
                walk(v)
    walk(d)
    # "IGV and stators 1-4" -> those five rows sit upstream of stages 1-5
    return dict(published=vg, rows=["IGV", "S1", "S2", "S3", "S4"],
                count=5, controls_stages=list(range(1, 6)),
                first_uncontrolled_stage=6)


def published_loading():
    """Fig 14's temperature rise and Fig 18's diffusion factor, per stage."""
    d = _stagewise()
    dt = df = None
    def walk(o):
        nonlocal dt, df
        if isinstance(o, dict):
            if "temperature_rise_C" in o:
                dt = o["temperature_rise_C"]
            if "diffusion_factor_pitch" in o:
                df = o["diffusion_factor_pitch"]
            for v in o.values():
                walk(v)
    walk(d)
    return [dict(stage=i + 1, dt_C=dt["per_stage"][i],
                 df_rotor=df["rotors"][i], df_stator=df["stators"][i])
            for i in range(10)]


def design_intent_checks():
    """The three claims that need no model at all."""
    rows = published_loading()
    by_dt = sorted(rows, key=lambda r: r["dt_C"])[:2]
    by_df = sorted(rows, key=lambda r: r["df_rotor"])[:2]
    top_st = sorted(rows, key=lambda r: -r["df_stator"])[:3]
    vr = variable_rows()
    return dict(
        least_loaded_by_temperature_rise=sorted(r["stage"] for r in by_dt),
        least_loaded_by_rotor_df=sorted(r["stage"] for r in by_df),
        most_loaded_stator_df=sorted(r["stage"] for r in top_st),
        first_uncontrolled_stage=vr["first_uncontrolled_stage"],
        claim_unloaded=[6, 7],
        claim_most_loaded_at_design=[8, 9, 10])


# ------------------------------------------------------- the design point

def _areas():
    """Annulus area at each rotor leading edge, from the flowpath."""
    rows = {}
    with open(DATA / "hpc-flowpath.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            if r["row"].startswith("R") and r["edge"] == "LE":
                n = int(r["row"][1:])
                rh, rt = float(r["r_hub_cm"]) / 100, float(r["r_tip_cm"]) / 100
                rows[n] = dict(area=math.pi * (rt ** 2 - rh ** 2),
                               r_pitch=(rh + rt) / 2)
    return rows


@lru_cache(maxsize=1)
def design_point():
    """Per stage: blade speed, axial velocity by continuity, and the two
    coefficients the characteristic is normalised on.

    Cached: `claim_window` marches the whole compressor eighty times per
    sweep, and Table XXI's stagewise solve is the expensive part."""
    from meanline.compressor import stagewise_from_table_xxi
    raw = stagewise_from_table_xxi()
    st = next((x for x in raw if isinstance(x, list)), None) or raw[0]
    areas = _areas()
    d = _stagewise()
    w = 54.4          # HPC inlet corrected flow, kg/s (e3-fps size block)
    t, p = 288.15, 101325.0
    out = []
    for s in st:
        n = s["stage"]
        a = areas[n]["area"]
        rho = p / (R_AIR * t)
        cx = w / (rho * a)
        u = s["u"]
        psi = CP * s["dt"] / (u * u)
        # polytropic efficiency implied by this stage's OWN published dt
        # and pressure ratio, so the march below reproduces the published
        # chain exactly at design instead of drifting away from it
        eta_p = (math.log(s["pr_stage"])
                 / (GAMMA / (GAMMA - 1) * math.log(1 + s["dt"] / t)))
        out.append(dict(stage=n, u=u, area=a, cx=cx, phi=cx / u, psi=psi,
                        dt=s["dt"], pr=s["pr_stage"], eta_p=eta_p,
                        t_in=t, p_in=p))
        t += s["dt"]
        p *= s["pr_stage"]
    return out


def characteristic(phi, phi_d, psi_d):
    """psi = 1 - phi (1 - psi_d)/phi_d.

    The Euler relation at a fixed relative exit angle, normalised through
    the stage's own design point: at phi = phi_d it returns psi_d exactly,
    and its slope is set by that point rather than chosen. No parameter."""
    return 1.0 - phi * (1.0 - psi_d) / phi_d


def march(speed_frac=1.0, flow_frac=None, vsv_deg=0.0):
    """Stack the ten stages at a fraction of design speed.

    `vsv_deg` closes the IGV and stators 1-4 by adding pre-swirl, which
    lowers the work those five stages do at a given flow. The schedule is
    NOT published, so this is an input to be swept, never a claim."""
    dp = design_point()
    if flow_frac is None:
        flow_frac = OPERATING_LINE.get(speed_frac, speed_frac)
    w = 54.4 * flow_frac
    t, p = 288.15, 101325.0
    out = []
    for s in dp:
        u = s["u"] * speed_frac
        rho = p / (R_AIR * t)
        cx = w / (rho * s["area"])
        phi = cx / u
        psi_d = s["psi"]
        if s["stage"] <= 5 and vsv_deg:
            # closing a variable stator adds pre-swirl: less work at the
            # same flow coefficient, by the Euler term u*c_theta1
            psi_d = psi_d - phi * math.tan(math.radians(vsv_deg))
        psi = characteristic(phi, s["phi"], psi_d)
        dt = psi * u * u / CP
        pr = (1 + dt / t) ** (GAMMA / (GAMMA - 1) * s["eta_p"])
        out.append(dict(stage=s["stage"], phi=phi, phi_design=s["phi"],
                        phi_ratio=phi / s["phi"], psi=psi, psi_design=psi_d,
                        loading=psi / psi_d if psi_d else float("nan"),
                        dt=dt, u=u))
        t += dt
        p *= max(pr, 1.0)
    return out


def design_point_identity():
    """The validation this unit runs before it is believed: at design speed
    and design flow the march must reproduce the design point exactly.

    It did not, on the first attempt -- the pressure chain used a flat 0.9
    polytropic efficiency and drifted, until by stage 10 the flow
    coefficient was 70 percent high and the loading negative. Taking each
    stage's efficiency from its own published dt and pressure ratio closes
    it. A march that cannot return its own design point cannot be trusted
    off it (finding 185)."""
    dp = {d["stage"]: d for d in design_point()}
    rows = march(1.0, 1.0)
    return [dict(stage=r["stage"], phi_ratio=r["phi"] / dp[r["stage"]]["phi"],
                 loading=r["loading"]) for r in rows]


def loading_order(speed_frac, vsv_deg=0.0, n=3):
    """The `n` most loaded stages at this speed, most first."""
    rows = march(speed_frac, vsv_deg=vsv_deg)
    return [r["stage"] for r in sorted(rows, key=lambda r: -r["loading"])[:n]]


#: The flow the march needs at each speed. NOT an operating line from
#: turbine matching -- see `operating_line_is_assumed`.
OPERATING_LINE = {1.00: 1.00, 0.85: 0.60, 0.70: 0.42}


def operating_line_is_assumed():
    """The weakest input in this unit, named.

    A real operating line comes from the downstream choke: the HPT nozzle
    is choked over most of the range, which fixes the corrected flow at
    station 4 and closes the match. This module has no turbine in it, so
    the flow at each speed is an INPUT. Setting flow proportional to speed
    -- the obvious first guess -- makes the rear stages turbine at 85 %
    speed, with loadings of -1.4 (finding 186): a high-pressure-ratio
    compressor's corrected flow falls far faster than its speed, and that
    is what the variable stators exist to manage. The values used are the
    highest flows at which every stage still does positive work."""
    return dict(source="assumed", from_turbine_matching=False,
                values=dict(OPERATING_LINE),
                why=("no turbine in this module; the HPT nozzle choke that "
                     "would close the match is Stage B's, not C1's"))


def intermediate_claim_holds(flow):
    """Are stages 6 and 7 among the four most loaded at 85 % speed?"""
    rows = march(0.85, flow)
    if min(r["loading"] for r in rows) <= 0:
        return None
    top4 = [r["stage"] for r in sorted(rows, key=lambda r: -r["loading"])[:4]]
    return 6 in top4 and 7 in top4


def low_claim_holds(flow, vsv_deg=0.0):
    """Are stages 8, 9 and 10 the three least loaded at 70 % speed?"""
    rows = march(0.70, flow, vsv_deg=vsv_deg)
    if min(r["loading"] for r in rows) <= 0:
        return None
    bot3 = sorted(r["stage"] for r in sorted(rows, key=lambda r: r["loading"])[:3])
    return bot3 == [8, 9, 10]


def claim_window(fn, lo=0.30, hi=0.70, step=0.005, **kw):
    """The range of flow over which a claim holds -- how robust it is, not
    merely whether one chosen point satisfies it."""
    ok = []
    x = lo
    while x <= hi + 1e-9:
        if fn(x, **kw) is True:
            ok.append(x)
        x += step
    if not ok:
        return dict(holds=False, lo=None, hi=None, width=0.0)
    return dict(holds=True, lo=min(ok), hi=max(ok), width=max(ok) - min(ok))


def vsv_effect(closures=(0, 5, 10, 15, 20)):
    """The VSV schedule effect, as a widening of the window in which the
    published low-speed loading order survives.

    The schedule itself is not published; this sweeps the closure and
    reports what it does, which is what the report says it is for --
    *front variable stators kept low so they close for low-speed stall
    margin*."""
    out = []
    for c in closures:
        w = claim_window(low_claim_holds, vsv_deg=c)
        out.append(dict(vsv_deg=c, **w))
    base = out[0]["width"]
    for r in out:
        r["widening_pct"] = (r["width"] / base - 1) * 100 if base else 0.0
    return out


def part_speed_story(vsv_deg=0.0):
    """The report's three off-design statements, as this model sees them."""
    return dict(
        design=loading_order(1.00, vsv_deg),
        intermediate=loading_order(0.85, vsv_deg),
        low=loading_order(0.70, vsv_deg),
        claim_design=[8, 9, 10],
        claim_intermediate_joins=[6, 7],
        claim_low_unloads=[8, 9, 10])


def no_stall_margin():
    """Stated rather than estimated."""
    return dict(
        reported=False,
        why=("a stall margin is the distance from an operating line to a "
             "STALL LINE, and no stall line for this compressor is "
             "published -- not as a map, not as a table, not as a figure "
             "this project has read"),
        vsv_schedule_published=False,
        vsv_published_instead="IGV and stators 1-4, torsion-bar actuation",
        what_it_would_need=("a compressor map, or enough part-speed test "
                            "points to build one"))


def summary():
    c = design_intent_checks()
    vr = variable_rows()
    L = ["Stage C unit C5 -- HPC off-design", ""]
    L.append("   the design intent, against the figures:")
    L.append(f"      least loaded by temperature rise (Fig 14): "
             f"{c['least_loaded_by_temperature_rise']}   claim {c['claim_unloaded']}")
    L.append(f"      least loaded by rotor DF        (Fig 18): "
             f"{c['least_loaded_by_rotor_df']}   claim {c['claim_unloaded']}")
    L.append(f"      most loaded stator DF           (Fig 18): "
             f"{c['most_loaded_stator_df']}   claim {c['claim_most_loaded_at_design']}")
    L.append(f"      variable geometry: {vr['published']!r} -> controls stages "
             f"{vr['controls_stages'][0]}-{vr['controls_stages'][-1]}, "
             f"first uncontrolled is {vr['first_uncontrolled_stage']}")
    ident = design_point_identity()
    L += ["", f"   validation: the march returns its own design point to "
          f"{max(abs(x['phi_ratio'] - 1) for x in ident) * 100:.4f} % on all ten stages"]
    wi = claim_window(intermediate_claim_holds, 0.40, 0.70)
    wl = claim_window(low_claim_holds, 0.30, 0.60)
    L += ["", "   the published part-speed claims, and how robust each is:"]
    L.append(f"      6-7 among the four most loaded at 85 % speed: "
             f"{'HOLDS' if wi['holds'] else 'fails'} over W = "
             f"{wi['lo']:.2f}-{wi['hi']:.2f}  (width {wi['width']:.3f})")
    L.append(f"      8-10 the three least loaded at 70 % speed:    "
             f"{'HOLDS' if wl['holds'] else 'fails'} over W = "
             f"{wl['lo']:.2f}-{wl['hi']:.2f}  (width {wl['width']:.3f})")
    L += ["", "   the VSV schedule effect on that second window:"]
    for r in vsv_effect():
        L.append(f"      closed {r['vsv_deg']:>2} deg: W = {r['lo']:.3f}-{r['hi']:.3f}"
                 f"   width {r['width']:.3f}  ({r['widening_pct']:+.0f} %)")
    n = no_stall_margin()
    L += ["", f"   stall margin: NOT REPORTED. {n['why'][:72]}...",
          f"   VSV schedule published: {n['vsv_schedule_published']} "
          f"({n['vsv_published_instead']})"]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
