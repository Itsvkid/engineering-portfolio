"""Stage E4: shafts, criticals, bolted joints and blade-out.

The work plan's E4 closure has two halves: *no rotor critical inside the
operating band without a damper, and the thrust-bearing load stays inside
capacity in both directions.*

**The second half is gated.** CR-168219 sec 5.7 names all five bearings,
their types, their roles and their sumps, but prints **no bearing load and
no bearing capacity**, and Stage D's thrust balance is not done. Written
down, not worked around.

The first half can be settled, and more than settled: HPT report Table
XXII prints four critical speeds with the report's own definition of the
margin, so the arithmetic can be checked rather than trusted, and Fig. 88
prints enough of one disc's travelling-wave diagram to ask whether the
critical it names is the one the physics gives.

What else is here is what the published data actually supports:

  * **Shaft torque from the cycle**, at each rating, with the spool speed
    taken from the reports' own N/sqrt(T) cycle-match parameters -- which
    is itself a check, because those two numbers have to reproduce the
    published physical speeds.
  * **The bolted joint that carries that torque.** The HPT rotor bolts
    are specified to transmit torque *through flange friction only, with
    no slip*, and Figs 90-91 print the clamp load both new and after
    9,000 h of creep relaxation. So the margin can be quoted at both.
  * **Blade-out.** The load a released blade throws into the mounts is
    its own centrifugal load, and for the fan that is the sizing case for
    the whole mount system.

STEP0.md, unit E4."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle import cycle as cyc
from e3cycle.cycle import DATA

RPS_TO_RPM = 60.0
MU_STEEL = 0.15          # metal-on-metal flange friction; handbook, stated


def _hpt():
    return yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())


def _pub():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


# ------------------------------------------------- criticals, from Table XXII

def critical_speed_margins():
    """Table XXII prints the critical speed AND the margin, and sec 5.2.1.11
    prints the definition -- (critical - maximum)/maximum. Three printed
    quantities and one definition: the table checks itself."""
    rd = _hpt()["rotor_dynamics"]
    t, n_max = rd["table_xxii"], rd["max_engine_speed_rps"]
    out = []
    for i, name in enumerate(t["component"]):
        crit = t["critical_speed_rps"][i]
        margin = (crit - n_max) / n_max
        out.append(dict(component=name, nodes=t["critical_nodes_N"][i], crit_rps=crit,
                        margin=margin, printed=t["safety_margin"][i],
                        diff=margin - t["safety_margin"][i],
                        inside_band=crit <= n_max))
    return out, n_max


def travelling_wave(nodes=None, f0_cps=None, crit_rps=None):
    """A disc mode with N nodal diameters splits into a forward and a
    backward travelling wave. In the stationary frame the backward wave is
    f(Omega) - N*Omega, and the critical is where that reaches zero:

        sqrt(f0^2 + S Omega^2) = N Omega   ->   S = N^2 - (f0/Omega_crit)^2

    Fig 88 prints f0, N and the critical, so S -- how much the disc mode
    stiffens with speed -- is an OUTPUT, not an input."""
    d = _hpt()["rotor_dynamics"]["aft_seal_disk"]
    n = nodes or d["N"]
    f0 = f0_cps or d["zero_speed_frequency_cps"]
    om = crit_rps or d["backward_wave_zero_rps"]
    s = n ** 2 - (f0 / om) ** 2
    f_disc = math.sqrt(f0 ** 2 + s * om ** 2)
    # the other point Fig 88 prints, on the forward wave
    om2 = 440.0
    f_disc2 = math.sqrt(f0 ** 2 + s * om2 ** 2)
    return dict(nodes=n, f0_cps=f0, crit_rps=om, southwell=s,
                f_disc_at_crit=f_disc, check_n_omega=n * om,
                rigid_critical_rps=f0 / n,
                fwd_at_440_model=f_disc2 + n * om2,
                bwd_at_440_model=f_disc2 - n * om2,
                fwd_at_440_printed=d["forward_wave_at_440_rps_cps"],
                implied_nodes_at_440=(d["forward_wave_at_440_rps_cps"] - f_disc2) / om2)


# ------------------------------------------------------- shafts and the joint

@dataclass
class SpoolTorque:
    rating: str
    hp_power_MW: float
    lp_power_MW: float
    hp_rpm: float
    lp_rpm: float
    hp_torque_kNm: float
    lp_torque_kNm: float


def spool_torques():
    """Power from the cycle, speed from the reports' own cycle-match
    N/sqrt(T) parameters. That the second reproduces the published
    physical speeds is a check in itself."""
    pub = _pub()
    k_hp = pub["hpt"]["cycle_match"]["speed_N_over_sqrtT_rad_s_sqrtK"]
    k_lp = pub["lpt"]["cycle_match"]["speed_N_over_sqrtT_rad_s_sqrtK"]
    out = []
    for r in cyc.run_all():
        st = r.stations
        hp_power = st["hpt_dh_per_kg"] * st["w41"]
        lp_power = st["lpt_dh_per_kg"] * st["w45"]
        w_hp = k_hp * math.sqrt(st["t41"])
        w_lp = k_lp * math.sqrt(st["t45"])
        out.append(SpoolTorque(r.rating, hp_power / 1e6, lp_power / 1e6,
                               w_hp * 60 / (2 * math.pi), w_lp * 60 / (2 * math.pi),
                               hp_power / w_hp / 1e3, lp_power / w_lp / 1e3))
    return out


def bolted_joint_margin(mu=MU_STEEL):
    """The HPT rotor bolts must carry torque through flange friction alone,
    with no slip (sec 5.2.1.12's first criterion). Fig 90's inducer-disk
    joint is the one the report says is *governed by torque transfer*, and
    it prints the clamp load new and after 9,000 h of creep relaxation.
    The bolt-circle radius is not printed, so it is inverted: what radius
    does the joint need to hold the worst shaft torque?"""
    b = _hpt()["rotor_bolts"]["inducer_disk_bolt"]
    worst = max(spool_torques(), key=lambda s: s.hp_torque_kNm)
    n, f_new = b["bolts"]["count"], b["initial_clamp_kN"] * 1e3
    f_old = b["after_9000h_kN"] * 1e3
    t = worst.hp_torque_kNm * 1e3
    return dict(rating=worst.rating, torque_kNm=worst.hp_torque_kNm, bolts=n, mu=mu,
                clamp_new_kN=f_new / 1e3, clamp_relaxed_kN=f_old / 1e3,
                r_required_new_cm=t / (mu * n * f_new) * 100,
                r_required_relaxed_cm=t / (mu * n * f_old) * 100,
                relaxation_pct=(1 - f_old / f_new) * 100)


# ----------------------------------------------------------------- blade-out

def blade_masses():
    """Airfoil mass by integrating the reconstructed section areas, against
    Table VI's printed per-blade weights. The printed weight is the WHOLE
    blade -- airfoil, platform, dovetail, and on the fan the part-span
    shroud -- so the airfoil must come out a sensible fraction below it."""
    from mechanical.blade_frequency import booster_rotor, fan_rotor
    import numpy as np
    w = yaml.safe_load((DATA / "fan-design.yaml").read_text())["fps_weight"]["items_kg"]
    fan, _ = fan_rotor()
    out = []
    for m, printed_total, count in ((fan, w["fan_blades"], 32),
                                    (booster_rotor(), w["booster_blades"], 56)):
        x = np.asarray(m.x)
        a = np.asarray(m.area)
        mass = m.rho * float(np.trapezoid(a, x))
        r_cg = m.hub_radius_m + float(np.trapezoid(a * x, x)) / float(np.trapezoid(a, x))
        out.append(dict(name=m.name, airfoil_kg=mass, printed_kg=printed_total / count,
                        fraction=mass / (printed_total / count), r_cg_m=r_cg,
                        length_m=m.length_m, hub_m=m.hub_radius_m, count=count))
    return out


def blade_out():
    """The load a released blade throws into the mounts is its own
    centrifugal load, m omega^2 r_cg. For the fan that is the case the
    whole mount system is sized by (33.94 / CS-E 810)."""
    fan_c = yaml.safe_load((DATA / "fan-design.yaml").read_text())["fan_rotor_mechanical"]["campbell"]
    rpm = fan_c["max_speed_rpm"]
    om = rpm * 2 * math.pi / 60
    out = []
    for b in blade_masses():
        for label, m in (("airfoil only", b["airfoil_kg"]), ("whole blade (Table VI)", b["printed_kg"])):
            out.append(dict(blade=b["name"], basis=label, rpm=rpm, mass_kg=m,
                            r_cg_m=b["r_cg_m"], load_kN=m * om ** 2 * b["r_cg_m"] / 1e3,
                            tonnes=m * om ** 2 * b["r_cg_m"] / 9.80665 / 1e3))
    # and the HPT stage-1 blade, whose mass follows from its printed
    # dovetail load instead of from geometry
    hm = _hpt()
    dt = hm["stage1_blade"]["dovetail"]
    from mechanical.disc import stage1_radii
    r_tip, r_hub, om_h = stage1_radii()
    r_cg = 0.5 * (r_tip + r_hub)
    m = dt["load_per_blade_kN"] * 1e3 / (om_h ** 2 * r_cg)
    out.append(dict(blade="HPT stage 1", basis="mass from the printed dovetail load",
                    rpm=dt["condition"]["rpm"], mass_kg=m, r_cg_m=r_cg,
                    load_kN=dt["load_per_blade_kN"],
                    tonnes=dt["load_per_blade_kN"] * 1e3 / 9.80665 / 1e3))
    return out


if __name__ == "__main__":
    rows, n_max = critical_speed_margins()
    print(f"1. Rotor criticals against Table XXII (max engine speed {n_max} rps"
          f" = {n_max * 60:,.0f} rpm)\n")
    print(f"   {'component':<20}{'N':>3}{'crit rps':>10}{'margin':>9}{'printed':>9}{'diff':>8}")
    for r in rows:
        print(f"   {r['component']:<20}{r['nodes']:>3}{r['crit_rps']:>10}"
              f"{r['margin']:>9.3f}{r['printed']:>9.2f}{r['diff']:>+8.3f}")
    print(f"   -> criticals inside the operating band: "
          f"{sum(r['inside_band'] for r in rows)} of {len(rows)}")

    tw = travelling_wave()
    print(f"\n2. The aft seal disc's travelling wave (Fig 88)")
    print(f"   {tw['nodes']} nodal diameters, {tw['f0_cps']} cps at rest, "
          f"backward wave zero at {tw['crit_rps']} rps")
    print(f"   a RIGID disc would cross at f0/N = {tw['rigid_critical_rps']:.0f} rps")
    print(f"   so the disc must stiffen: implied S = {tw['southwell']:.2f}"
          f"  (f_disc there {tw['f_disc_at_crit']:.0f} = N x Omega = {tw['check_n_omega']:.0f})")
    print(f"   the other printed point, the forward wave at 440 rps:")
    print(f"      model {tw['fwd_at_440_model']:.0f} cps   printed "
          f"{tw['fwd_at_440_printed']:.0f} cps"
          f"   -> implies N = {tw['implied_nodes_at_440']:.2f}, not {tw['nodes']}")

    print(f"\n3. Shaft torque, power from the cycle and speed from N/sqrt(T)")
    print(f"\n   {'rating':<10}{'HP MW':>8}{'HP rpm':>9}{'HP kNm':>9}"
          f"{'LP MW':>8}{'LP rpm':>9}{'LP kNm':>9}")
    for s in spool_torques():
        print(f"   {s.rating:<10}{s.hp_power_MW:>8.2f}{s.hp_rpm:>9,.0f}{s.hp_torque_kNm:>9.1f}"
              f"{s.lp_power_MW:>8.2f}{s.lp_rpm:>9,.0f}{s.lp_torque_kNm:>9.1f}")

    j = bolted_joint_margin()
    print(f"\n4. The joint that carries it: 34 inducer-disc studs, friction only")
    print(f"   worst HP torque {j['torque_kNm']:.1f} kNm at {j['rating']}")
    print(f"   clamp {j['clamp_new_kN']:.0f} kN new, {j['clamp_relaxed_kN']:.1f} kN after"
          f" 9,000 h ({j['relaxation_pct']:.0f} % relaxation)")
    print(f"   bolt-circle radius needed at mu = {j['mu']}:"
          f" {j['r_required_new_cm']:.2f} cm new, {j['r_required_relaxed_cm']:.2f} cm relaxed")

    print(f"\n5. Blade mass audit against Table VI")
    print(f"   {'blade':<15}{'airfoil kg':>12}{'printed kg':>12}{'airfoil %':>11}{'r_cg cm':>10}")
    for b in blade_masses():
        print(f"   {b['name']:<15}{b['airfoil_kg']:>12.3f}{b['printed_kg']:>12.3f}"
              f"{b['fraction'] * 100:>11.0f}{b['r_cg_m'] * 100:>10.1f}")

    print(f"\n6. Blade-out: the load a released blade throws into the mounts")
    print(f"   {'blade':<13}{'basis':<32}{'rpm':>7}{'kg':>8}{'kN':>9}{'tonnes':>9}")
    for b in blade_out():
        print(f"   {b['blade']:<13}{b['basis']:<32}{b['rpm']:>7,}{b['mass_kg']:>8.3f}"
              f"{b['load_kN']:>9.0f}{b['tonnes']:>9.0f}")
