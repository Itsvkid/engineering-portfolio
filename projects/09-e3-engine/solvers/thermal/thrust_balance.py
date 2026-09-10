"""Stage D unit D6: thrust balance on the HP rotor -- the part that closes.

Stage D asks for a *thrust balance on each rotor across the mission;
balance-piston cavities per HPT report Figs. 95-96; net load into bearings
1 and 3.*

**Figures 95 and 96 are transcribed, and they are not what that item
assumed.** They give the inducer and piston-balance seal as *structure* --
62 tangential holes at 30 degrees, 64 Inco 718 bypass tubes, an Inco 903A
seal against the rotating balance-piston seal disk, 64 Waspaloy OGV bolts
-- and eleven stress-temperature-LCF points at a 40-second hot-day
takeoff. Neither gives a thrust, a piston area, a piston radius or a
cavity pressure. **The balance piston is described as hardware and never
as a load**, so the balance cannot be closed and this module does not
pretend to close it.

What closes is the **gas-path axial load on the rotating blade rows**.
Table XXI gives every HPC rotor its own inlet and exit stations, twelve
streamlines each, with radius, axial velocity, total pressure ratio and
Mach, so the rotor-only control volume needs no cavity information at all.
The HPT's two rotors close the same way from the C1 mean-line and Fig 3's
dimensioned annulus.

That is a **component** of the thrust balance and not the balance: the
disc faces and the piston act on areas nothing published dimensions. What
it gives is the sign and scale of what the piston must trim, and one
number worth inverting -- the piston area that would be needed at the
pressure difference the engine actually has.

Sign convention: **positive is forward**, towards the inlet.

STEP0.md, unit D6."""
from __future__ import annotations

import math

import yaml

from e3cycle.cycle import DATA

GAMMA = 1.4
R_AIR = 287.05
#: Table XXI column order, from the file's own `columns.rotor_station`
COL = dict(sl=0, pct_imm=1, radius_cm=2, z_cm=3, pt_ratio=4, tt_ratio=5,
           m_abs=6, m_rel=7, u=8, cz=9, beta=10, phi=11)


def _xxi():
    return yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())


def figs_95_96_contain():
    """What the two figures the plan named actually give."""
    h = yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())
    b = None

    def walk(o):
        nonlocal b
        if isinstance(o, dict):
            if "inducer_and_piston_balance_seal" in o:
                b = o["inducer_and_piston_balance_seal"]
            for v in o.values():
                walk(v)
    walk(h)
    return dict(
        src=b["src"], structure_given=True,
        tangential_holes=b["tangential_holes"]["count"],
        bypass_tubes=b["bypass_tubes"]["count"],
        seal_material=b["seal_material"],
        stress_points=len(b["stresses"]["points"]),
        thrust_given=False, piston_area_given=False,
        piston_radius_given=False, cavity_pressure_given=False,
        consequence="the balance piston is described as hardware, never as a load")


# --------------------------------------------------- the HPC rotor rows

def _station(row, which):
    """Area-weighted axial velocity and static pressure at one station of
    one rotor row, plus the annulus area, from Table XXI's streamlines."""
    data = row[which]
    r_tip = data[0][COL["radius_cm"]] / 100
    r_hub = data[-1][COL["radius_cm"]] / 100
    area = math.pi * (r_tip ** 2 - r_hub ** 2)
    # area-weight by the annulus each streamline stands for
    tot_w = cz = pt = mach = 0.0
    for i, sl in enumerate(data):
        r = sl[COL["radius_cm"]] / 100
        lo = (r + data[min(i + 1, len(data) - 1)][COL["radius_cm"]] / 100) / 2
        hi = (r + data[max(i - 1, 0)][COL["radius_cm"]] / 100) / 2
        w = max(math.pi * (hi ** 2 - lo ** 2), 0.0)
        tot_w += w
        cz += w * sl[COL["cz"]]
        pt += w * sl[COL["pt_ratio"]]
        mach += w * sl[COL["m_abs"]]
    if tot_w <= 0:
        tot_w = 1.0
    return dict(area=area, cz=cz / tot_w, pt_ratio=pt / tot_w,
                mach=mach / tot_w, r_tip=r_tip, r_hub=r_hub)


def _static(pt_abs, mach):
    return pt_abs / (1 + (GAMMA - 1) / 2 * mach ** 2) ** (GAMMA / (GAMMA - 1))


def hpc_rotor_loads(p_ref=None, w=None):
    """Axial gas load on each HPC rotor row, forward positive.

    F = m(cz_in - cz_out) + (ps_in A_in - ps_out A_out). The pressure term
    dominates and is negative-signed in the sense that a compressor's
    rising static pressure pushes the rotor UPSTREAM."""
    from e3cycle import cycle as cyc
    rating = max(cyc.run_all(), key=lambda r: r.stations["p3"])
    p_ref = p_ref if p_ref is not None else rating.stations["p25"]
    w = w if w is not None else rating.stations["w41"]

    out = []
    for row in _xxi()["rows"]:
        if row.get("row") != "rotor":
            continue
        a, b = _station(row, "inlet"), _station(row, "exit")
        ps_in = _static(p_ref * a["pt_ratio"], a["mach"])
        ps_out = _static(p_ref * b["pt_ratio"], b["mach"])
        mom = w * (a["cz"] - b["cz"])
        pres = ps_in * a["area"] - ps_out * b["area"]
        out.append(dict(stage=row["stage"], blades=row.get("blade_count"),
                        area_in=a["area"], area_out=b["area"],
                        cz_in=a["cz"], cz_out=b["cz"],
                        ps_in=ps_in, ps_out=ps_out,
                        momentum_N=mom, pressure_N=pres,
                        forward_N=mom + pres))
    return out


def hpc_continuity_check(p_ref=None, w=None):
    """Does the mass flow implied by each rotor station agree with the
    cycle's? A check on the streamline areas and the pressure chain, not on
    the loads -- but if it fails, the loads are meaningless."""
    from e3cycle import cycle as cyc
    rating = max(cyc.run_all(), key=lambda r: r.stations["p3"])
    p_ref = p_ref if p_ref is not None else rating.stations["p25"]
    w = w if w is not None else rating.stations["w41"]
    t_ref = rating.stations["t25"]
    out = []
    for row in _xxi()["rows"]:
        if row.get("row") != "rotor":
            continue
        a = _station(row, "inlet")
        tt = t_ref * row["inlet"][0][COL["tt_ratio"]]
        ts = tt / (1 + (GAMMA - 1) / 2 * a["mach"] ** 2)
        ps = _static(p_ref * a["pt_ratio"], a["mach"])
        rho = ps / (R_AIR * ts)
        out.append(dict(stage=row["stage"], w_implied=rho * a["cz"] * a["area"],
                        w_cycle=w))
    return out


# ------------------------------------------------------- the HPT rotors

def hpt_rotor_loads():
    """The two HPT rotors, from the C1 mean-line and Fig 3's annulus.

    A turbine's static pressure falls through the rotor, so the pressure
    force pushes it AFT -- the opposite sign to every HPC row."""
    from meanline.hpt import solve
    from e3cycle import cycle as cyc
    res = solve()
    stages = next((x for x in res if isinstance(x, list)), None) if isinstance(res, tuple) else res
    rating = max(cyc.run_all(), key=lambda r: r.stations["p3"])
    w = rating.stations["w41"]
    fp = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())[
        "hpt"]["flowpath"]["stations"]

    def area_at(x):
        near = min(fp, key=lambda s: abs(s["x_cm"] - x))
        return math.pi * ((near["r_tip_cm"] / 100) ** 2 - (near["r_hub_cm"] / 100) ** 2)

    out = []
    for i, s in enumerate(stages):
        a_in, a_out = area_at(3.5 + i * 7), area_at(8.5 + i * 7)
        ps_in = _static(s.p01, s.m2)
        ps_out = _static(s.p03, s.m3)
        # axial velocity from the absolute Mach and the exit angle
        a_snd_in = math.sqrt(GAMMA * R_AIR * s.t01 / (1 + (GAMMA - 1) / 2 * s.m2 ** 2))
        a_snd_out = math.sqrt(GAMMA * R_AIR * s.t03 / (1 + (GAMMA - 1) / 2 * s.m3 ** 2))
        cz_in = s.m2 * a_snd_in * math.cos(math.radians(s.alpha2))
        cz_out = s.m3 * a_snd_out * math.cos(math.radians(s.alpha3))
        mom = w * (cz_in - cz_out)
        pres = ps_in * a_in - ps_out * a_out
        out.append(dict(stage=s.n, area_in=a_in, area_out=a_out,
                        cz_in=cz_in, cz_out=cz_out, ps_in=ps_in, ps_out=ps_out,
                        momentum_N=mom, pressure_N=pres, forward_N=mom + pres))
    return out


def net_hp_gas_load():
    """The HPC and HPT gas-path loads, and what is left for the piston."""
    hpc = sum(r["forward_N"] for r in hpc_rotor_loads())
    hpt = sum(r["forward_N"] for r in hpt_rotor_loads())
    net = hpc + hpt
    return dict(hpc_forward_N=hpc, hpt_forward_N=hpt, net_forward_N=net,
                hpc_pushes_forward=hpc > 0, hpt_pushes_aft=hpt < 0,
                cancellation_pct=100 * (1 - abs(net) / max(abs(hpc), abs(hpt))),
                hpt_over_hpc=abs(hpt) / abs(hpc) if hpc else float("nan"))


def disc_face_force(r_bore_m):
    """The forward force on the HPC drum's disc faces, for an assumed bore.

    This is the term the annulus control volume above EXCLUDES, and it is
    the one that dominates. High pressure behind the drum and low in front
    push it forward across the annulus from the bore out to the hub line:
    `(p3 - p25) x pi (r_hub_aft^2 - r_bore^2)`.

    **The bore radius is not published.** It is the disc profile -- the
    same un-digitised figure that gates unit E2's peak stress and burst
    margin and unit F2's disc masses. So this returns a curve, and the
    thrust balance stays gated on it (finding 193)."""
    import csv
    from e3cycle import cycle as cyc
    rating = max(cyc.run_all(), key=lambda r: r.stations["p3"])
    p25, p3 = rating.stations["p25"], rating.stations["p3"]
    hub = {}
    with open(DATA / "hpc-flowpath.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            hub[(r["row"], r["edge"])] = float(r["r_hub_cm"]) / 100
    r_hub_aft = hub[("S10", "TE")]
    area = math.pi * (r_hub_aft ** 2 - r_bore_m ** 2)
    return dict(r_bore_m=r_bore_m, r_hub_aft_m=r_hub_aft, area_m2=area,
                dp_Pa=p3 - p25, forward_N=(p3 - p25) * area)


def disc_face_curve(bores_cm=(8, 10, 12, 15, 18, 20)):
    """The curve, and how it compares with the annulus term."""
    ann = abs(net_hp_gas_load()["hpc_forward_N"])
    out = []
    for b in bores_cm:
        d = disc_face_force(b / 100)
        out.append(dict(r_bore_cm=b, forward_N=d["forward_N"],
                        area_m2=d["area_m2"],
                        times_annulus=d["forward_N"] / ann))
    return out


def why_gated():
    """The thrust balance is gated, and this says on what, with a number.

    STEP0 predicted the HPC rotors would push forward. On the ANNULUS
    control volume they do not -- they push aft, 106 kN of it (finding
    192). The forward push is the disc-face term, and it is 3.2 to 6.4
    times the annulus term over any plausible bore radius. That radius is
    the un-digitised disc profile, so the balance is gated on exactly what
    E2's peak stress and F2's disc masses are gated on."""
    c = disc_face_curve()
    ann = net_hp_gas_load()
    return dict(
        annulus_hpc_N=ann["hpc_forward_N"],
        annulus_is_aft=ann["hpc_forward_N"] < 0,
        disc_face_range_N=(min(r["forward_N"] for r in c),
                           max(r["forward_N"] for r in c)),
        times_annulus_range=(min(r["times_annulus"] for r in c),
                             max(r["times_annulus"] for r in c)),
        gated_on="the HPC disc bore radius -- the un-digitised disc profile",
        same_gate_as=["E2 peak stress", "E2 burst margin", "F2 disc masses"])


def what_is_not_published():
    return dict(
        piston_area=False, piston_radius=False, cavity_pressures=False,
        disc_face_areas=False, bearing_1_load=False, bearing_3_load=False,
        bearing_capacity=False, mission_sweep=False,
        consequence=("the balance itself is not closed; bearing loads need "
                     "the disc-face pressures and the mission sweep needs a "
                     "balance to sweep"))


def summary():
    f = figs_95_96_contain()
    n = net_hp_gas_load()
    g = why_gated()
    L = ["Stage D unit D6 -- thrust balance on the HP rotor", ""]
    L.append(f"   Figs 95-96 ({f['src']}) give:")
    L.append(f"      structure yes -- {f['tangential_holes']} tangential holes, "
             f"{f['bypass_tubes']} bypass tubes, {f['stress_points']} stress points")
    L.append(f"      thrust {f['thrust_given']}, piston area {f['piston_area_given']}, "
             f"cavity pressure {f['cavity_pressure_given']}")
    L += ["", "   gas-path axial load on the rotating rows, forward positive:"]
    for r in hpc_rotor_loads():
        L.append(f"      HPC rotor {r['stage']:>2}: {r['forward_N']/1e3:9.2f} kN"
                 f"   (momentum {r['momentum_N']/1e3:7.2f}, "
                 f"pressure {r['pressure_N']/1e3:8.2f})")
    for r in hpt_rotor_loads():
        L.append(f"      HPT rotor {r['stage']:>2}: {r['forward_N']/1e3:9.2f} kN"
                 f"   (momentum {r['momentum_N']/1e3:7.2f}, "
                 f"pressure {r['pressure_N']/1e3:8.2f})")
    L += ["", f"   HPC total {n['hpc_forward_N']/1e3:9.2f} kN forward",
          f"   HPT total {n['hpt_forward_N']/1e3:9.2f} kN forward",
          f"   net       {n['net_forward_N']/1e3:9.2f} kN "
          f"({n['cancellation_pct']:.0f} % cancelled)"]
    L += ["", "   the term the annulus control volume EXCLUDES, and which dominates:"]
    L.append(f"      {'r_bore cm':>10}{'force kN':>11}{'x annulus':>12}")
    for r in disc_face_curve():
        L.append(f"      {r['r_bore_cm']:>10}{r['forward_N']/1e3:>11.1f}"
                 f"{r['times_annulus']:>11.2f}x")
    L += ["", f"   GATED on {g['gated_on']},",
          f"   which is the same gate as {', '.join(g['same_gate_as'])}."]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
