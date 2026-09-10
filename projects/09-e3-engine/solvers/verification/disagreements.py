"""Stage I3: every disagreement with a published number, ranked.

I3's first bullet: *every disagreement with a published number, ranked by
size, with a cause or "unresolved".*

The point of generating this rather than writing it by hand is that a
hand-written list contains the disagreements someone remembered. This one
contains all of them, including the ones nobody wants to look at, and it
re-ranks itself every time the solvers change. If a later stage quietly
makes an earlier comparison worse, this is where it shows up.

Each record carries what was predicted, what was published, where the
published number came from, and a **cause** — or the word `unresolved`,
which is a legitimate entry and is counted separately.

STEP0.md, unit I3."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Disagreement:
    quantity: str
    stage: str
    predicted: float
    published: float
    source: str
    cause: str = "unresolved"
    units: str = "%"
    finding: int | None = None

    @property
    def err_pct(self):
        if self.published == 0:
            return 0.0 if self.predicted == 0 else float("inf")
        return (self.predicted / self.published - 1) * 100

    @property
    def resolved(self):
        return self.cause != "unresolved"


def _hpc_blade_stress():
    from mechanical.blade_stress import all_stages
    from materials.allowables import measured_blade_density
    mat = {r["stage"]: r["nearer"] for r in measured_blade_density()}
    out = []
    for s in all_stages():
        got = s.sigma_titanium_kN_cm2 if mat[s.stage] == "titanium" else s.sigma_nickel_kN_cm2
        out.append(Disagreement(
            f"HPC rotor {s.stage} root centrifugal stress", "E1", got, s.printed_kN_cm2,
            "HPC Table X", "area distribution from Table XXII; material from the F1 density "
            "measurement, not from Table X's material column", finding=74))
    return out


def _hpc_density():
    from materials.allowables import alloys, measured_blade_density
    a = alloys()
    rho = {"titanium": a["ti_8al_1mo_1v_forging"]["density"],
           "nickel": a["inconel_718_bar_forging"]["density"]}
    return [Disagreement(
        f"HPC rotor {r['stage']} blade density", "F1", r["rho"], rho[r["nearer"]],
        "MIL-HDBK-5J handbook density",
        "the reconstruction's own area accuracy; the two candidates are a factor of "
        "two apart so the identification is never in doubt", finding=104)
        for r in measured_blade_density()]


def _hpc_areas_and_masses():
    from materials.mass import hpc_airfoil_areas, hpc_airfoil_masses
    out = [Disagreement(
        f"HPC rotor {a['stage']} {a['where']} section area", "F2",
        a["built_cm2"], a["printed_cm2"], "HPC Table X",
        "the double-circular-arc and quarter-sine construction has no leading- or "
        "trailing-edge radius, so a built section is thinner than the real one; "
        "20 of 20 comparisons are negative", finding=109)
        for a in hpc_airfoil_areas()]
    out += [Disagreement(
        f"HPC rotor {m['stage']} airfoil mass", "F2",
        m["built_kg"], m["printed_airfoil_kg"], "HPC Table X",
        "inherits the section-area bias of finding 109 almost exactly", finding=109)
        for m in hpc_airfoil_masses()]
    return out


def _hpc_campbell():
    from mechanical.blade_frequency import hpc_campbell_comparison
    out = []
    for r in hpc_campbell_comparison():
        for m in r["modes"]:
            if m["published"] is None:
                continue
            out.append(Disagreement(
                f"HPC rotor {r['stage']} {m['mode']} frequency", "E3",
                m["predicted"], m["published"], f"HPC Fig {r['figure']}",
                "a clamped beam is the stiffest root a blade can have and a dovetail in a "
                "slot is not a clamp; the bias grows with mode number, which is what a soft "
                "root does", finding=143))
    return out


def _blade_frequencies():
    from mechanical.blade_frequency import blades, southwell_table
    out = []
    for b in blades():
        got = b.modes(False, 0.0, 1)[0]
        cause = {"booster rotor": "none needed -- an unshrouded blade really is a beam",
                 "fan rotor": "the part-span shroud; the published mode is the lowest "
                              "in-phase one, where the shroud ring travels with the blades",
                 "LPT stage 1": "a rigidly clamped root against a two-tang dovetail, plus "
                                "hot modulus; the modulus alone accounts for about half"}
        out.append(Disagreement(f"{b.name} first flex", "E3", got, b.published_f1_Hz,
                                b.src.split(",")[0], cause.get(b.name, "unresolved"),
                                finding=82 if b.name == "booster rotor" else 84))
    for r in southwell_table():
        if r["s_published"] < 0:
            continue
        out.append(Disagreement(
            f"{r['name']} Southwell coefficient", "E3", r["s_model"], r["s_published"],
            "the published Campbell pair",
            "outboard shroud and platform mass not modelled, and the flap-lag coupling of "
            "a staggered blade; S goes as f squared so a 7 % read error is 25 % here",
            finding=85))
    return out


def _rotor_criticals():
    from mechanical.rotordynamics import critical_speed_margins
    from verification.consistency import spool_speeds_four_routes
    out = [Disagreement(f"{r['component']} critical-speed margin", "E4",
                        r["margin"], r["printed"], "HPT Table XXII",
                        "the report rounds the same 1.618 two ways", finding=91)
           for r in critical_speed_margins()[0]]
    s = spool_speeds_four_routes()
    out.append(Disagreement("LP spool speed at max climb", "E4", s["lp"][0].value,
                            s["lp"][1].value, "LPT report N/sqrt(T) and the cycle's T45",
                            "two independent documents; nothing needed", finding=121))
    out.append(Disagreement("HP spool speed at max climb", "E4", s["hp"][1].value,
                            s["hp"][0].value, "HPC Table X aero design point",
                            "two independent documents; nothing needed", finding=121))
    return out


def _geometry():
    from materials.mass import module_audit
    return [Disagreement(f"{r['module']} mass", "F2", r["component_report"], r["table_xxvi"],
                         r["src"].split(" vs ")[-1],
                         "the fan+booster component table includes a shaft the whole-engine "
                         "table may group elsewhere" if "fan" in r["module"]
                         else "two documents agreeing; nothing needed", finding=111)
            for r in module_audit()]


def _cycle():
    from e3cycle import cycle as cyc
    return [Disagreement(f"sfc at {r.rating}", "B3", r.sfc_kg_N_h, r.sfc_published,
                         "Table XII",
                         "Table XII is a mixed-day table: T41 on the flat-rating day, sfc on "
                         "the standard day. Takeoff is a pinned xfail"
                         if r.rating == "takeoff" else "within band; nothing needed")
            for r in cyc.run_all()]


def _open_questions():
    """Disagreements with no cause yet. `unresolved` is a legitimate entry
    and this project would rather carry four of them than pretend every
    number has been explained."""
    import yaml
    from e3cycle.cycle import DATA
    h = yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())
    l = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    out = []

    # Fig 64 (detailed FE) against Fig 55 (CLASS/MASS), same disc, same instant
    out.append(Disagreement(
        "HPT stage-1 disc bore stress, Fig 64 vs Fig 55", "E2",
        h["stage1_disk_stress_fig64"]["whole_disk"]["bore"],
        h["rotor_effective_stress"]["locations_MPa"]["stage1_disk_bore"][0],
        "CR-167955 Figs 55 and 64", "unresolved"))

    # Fig 70's printed Kt reproduces on the blade sections and not the disc
    d = l["dovetails"]["stage1_stress_distribution"]
    for key, kt in (("disk_C_MPa", "disk_C"), ("disk_D_MPa", "disk_D")):
        out.append(Disagreement(
            f"LPT Fig 70 {kt} stress concentration", "E5",
            d[key][1] / d[key][0], d["kt"][kt], "LPT Fig 70", "unresolved", finding=100))

    # the published Campbell lines do not rise with speed
    out.append(Disagreement(
        "HPC stage-1 first flex at 14,000 rpm", "E3", 539.0, 350.0,
        "HPC Fig 33, read flat across the speed range", "unresolved", finding=145))

    # Rotor 37 will not hold a physical solution
    out.append(Disagreement(
        "Rotor 37 mass flow, converged solve", "C4", 5.17, 20.188,
        "TP-1337 Table I design flow",
        "the solve never reaches a steady state at all -- work swings from "
        "-3 to +91 % of design across 1500 iterations while a reversed tip "
        "region carries 597 K gas back past the inlet plane. Not a stalled "
        "branch; an unsteady flow given to a steady solver (findings 194-197)",
        finding=197))

    # the published Campbell lines do not rise with speed; the model says
    # stage-1 first flex gains 54 % across the range (unit J2, finding 162)
    from publication.campbell import predicted_curve, RPM_DETERIORATED
    lo, hi = predicted_curve(1, 0, [0.0, RPM_DETERIORATED])
    out.append(Disagreement(
        "HPC stage-1 1F rise, rest to max speed", "J2", hi / lo, 1.0,
        "HPC Figs 33-42, mode lines drawn flat across the speed range",
        "unresolved", units="ratio", finding=162))

    # the five LPT flutter safety factors do not imply one allowable (E7)
    from mechanical.flutter import recovered_allowable
    r = recovered_allowable()
    out.append(Disagreement(
        "LPT flutter allowable, stage 5 vs stage 1", "E7",
        r["rows"][4]["implied_allowable"], r["rows"][0]["implied_allowable"],
        "LPT Table XI safety factors, which should imply one allowable",
        "unresolved", units="index", finding=174))

    # two published lengths for the same duct, 10 % apart (unit J1)
    td = yaml.safe_load((DATA / "engine-flowpath.yaml").read_text())["transition_duct"]
    out.append(Disagreement(
        "HPT-to-LPT transition duct length", "J1",
        td["from_sections_cm"], td["axial_length_cm"],
        "CR-168219 sec 5.5 printed length vs the LPT section coordinates",
        "unresolved", units="cm", finding=157))
    return out


HARVESTERS = (_open_questions, _cycle, _hpc_blade_stress, _hpc_density, _hpc_areas_and_masses,
              _hpc_campbell, _blade_frequencies, _rotor_criticals, _geometry)


def collect():
    out = []
    for h in HARVESTERS:
        out.extend(h())
    return sorted(out, key=lambda d: -abs(d.err_pct))


def summary(rows=None):
    rows = rows if rows is not None else collect()
    unresolved = [r for r in rows if not r.resolved]
    return dict(total=len(rows),
                within_1=sum(1 for r in rows if abs(r.err_pct) <= 1),
                within_5=sum(1 for r in rows if abs(r.err_pct) <= 5),
                within_10=sum(1 for r in rows if abs(r.err_pct) <= 10),
                over_20=sum(1 for r in rows if abs(r.err_pct) > 20),
                unresolved=len(unresolved),
                worst=rows[0], median=sorted(abs(r.err_pct) for r in rows)[len(rows) // 2],
                by_stage={s: sum(1 for r in rows if r.stage == s)
                          for s in sorted({r.stage for r in rows})})


if __name__ == "__main__":
    rows = collect()
    s = summary(rows)
    print(f"Stage I3: every disagreement with a published number, ranked\n")
    print(f"   {s['total']} comparisons across {len(s['by_stage'])} stages")
    print(f"   within 1 %: {s['within_1']}   within 5 %: {s['within_5']}   "
          f"within 10 %: {s['within_10']}   over 20 %: {s['over_20']}")
    print(f"   median |error| {s['median']:.2f} %   unresolved: {s['unresolved']}\n")
    print(f"   {'err %':>8}  {'stage':<5} {'quantity':<44} {'source':<26} cause")
    for r in rows[:20]:
        print(f"   {r.err_pct:>+8.1f}  {r.stage:<5} {r.quantity[:44]:<44} "
              f"{r.source[:26]:<26} {'' if r.resolved else 'UNRESOLVED'}")
    print(f"\n   ... {len(rows) - 20} more, all in FINDINGS.md")
