"""Stage E unit E9: the HPC rotor -- the inertia welds and the one bolt joint.

Two neighbouring units are already done and are not this one. E5's
`casing_bolting` checks Table XVII's three *casing* flanges against their
printed criterion; E4's `bolted_joint_margin` inverts the *HPT*
inducer-disk joint. Neither touches the HPC rotor.

The FPS report gives the rotor one line:

    inertia-welded forward and aft sections joined by a single bolt joint;
    bore cooled by fan discharge air

which describes **two kinds of joint in different places**: inertia welds,
plural and internal -- individual stage discs friction-welded into a drum
-- and **one** bolt joint, where the forward drum meets the aft one.
Conflating them has cost this project once already: unit E1's finding 74
read a material crossover as the weld position and was withdrawn as
circular. A material change happens at a **weld**, disc to disc; the
sentence gives no position for either kind of joint.

**What can be computed is a curve, not a number.** The HPT drives the
rotor from the aft end and each stage takes its share going forward, so a
joint after stage *n* transmits only the torque the stages ahead of it
absorb. Figure 14's per-stage temperature rise is that split, printed. The
torque through the joint therefore follows from the position -- and the
position is the unknown.

STEP0.md, unit E9."""
from __future__ import annotations

import yaml

from e3cycle.cycle import DATA


def published_construction():
    """The one published sentence, and what it does and does not fix."""
    d = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    line = d["hpc"]["rotor_construction"]
    return dict(
        line=line,
        inertia_welds=dict(count="plural, unstated",
                           what="stage discs friction-welded into a drum",
                           position_published=False),
        bolt_joints=dict(count=1, what="forward drum to aft drum",
                         position_published=False),
        bore_cooling="fan discharge air",
        why_two_kinds=("a material change happens at a WELD, disc to disc; "
                       "the single bolt joint is a different feature in a "
                       "different place. Unit E1 finding 74 conflated them"))


def work_split():
    """Figure 14's per-stage temperature rise as a cumulative work fraction.

    Cumulative from the FRONT, because torque enters at the aft end and is
    consumed going forward: a joint after stage n carries what stages 1..n
    take."""
    d = yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())
    dt = None

    def walk(o):
        nonlocal dt
        if isinstance(o, dict):
            if "temperature_rise_C" in o:
                dt = o["temperature_rise_C"]
            for v in o.values():
                walk(v)
    walk(d)
    per, total = dt["per_stage"], dt["total"]
    run = 0.0
    out = []
    for i, x in enumerate(per, start=1):
        run += x
        out.append(dict(stage=i, dt_C=x, cumulative_C=run,
                        fraction_forward=run / total))
    return dict(rows=out, printed_total_C=total, summed_C=run,
                closes_to_C=abs(run - total))


def hp_torque_kNm(rating="takeoff"):
    from mechanical.rotordynamics import spool_torques
    return next(s for s in spool_torques() if s.rating == rating).hp_torque_kNm


def torque_through_joint(after_stage, rating="takeoff"):
    """The torque a joint carries if it sits immediately aft of `after_stage`.

    `after_stage = 10` is the joint at the very back, which carries the
    whole HP torque; `after_stage = 1` carries only stage 1's share."""
    ws = work_split()
    f = next(r["fraction_forward"] for r in ws["rows"] if r["stage"] == after_stage)
    t = hp_torque_kNm(rating)
    return dict(after_stage=after_stage, fraction=f, torque_kNm=f * t,
                hp_torque_kNm=t, rating=rating)


def joint_demand_curve(rating="takeoff"):
    """The whole curve, because the position is what is unknown."""
    return [torque_through_joint(n, rating) for n in range(1, 11)]


def versus_hpt_joint(rating="takeoff"):
    """Every HPC joint position against the HPT joint, which carries the
    whole HP torque. The comparison is dimensionless, so it needs neither
    the HPC joint's bolt count nor its radius -- none of which is
    published."""
    from mechanical.rotordynamics import bolted_joint_margin
    hpt = bolted_joint_margin()
    out = []
    for r in joint_demand_curve(rating):
        out.append(dict(after_stage=r["after_stage"],
                        torque_kNm=r["torque_kNm"],
                        fraction_of_hpt_joint=r["torque_kNm"] / hpt["torque_kNm"]))
    return dict(hpt_joint_torque_kNm=hpt["torque_kNm"], rows=out,
                all_below_one=all(x["fraction_of_hpt_joint"] < 1.0
                                  for x in out[:-1]))


def candidate_positions():
    """The two stations the project has evidence for a MATERIAL change at,
    and the joint torque each would imply.

    Neither is a weld position. Unit F1 measured a titanium-to-nickel
    density crossover between stages 4 and 5 from Table X's own weight
    column; Table X's material column prints the change at stage 7. The
    two disagree and F1 flagged it rather than resolving it. Listing the
    torque at each is not an argument for either -- it is the range the
    joint demand sits in while the question is open."""
    out = []
    for stage, why in ((4, "unit F1's measured density crossover, stages 4/5"),
                       (7, "Table X's printed material column")):
        r = torque_through_joint(stage)
        out.append(dict(after_stage=stage, why=why, fraction=r["fraction"],
                        torque_kNm=r["torque_kNm"]))
    return dict(rows=out, is_an_argument_for_neither=True,
                note=("a material change happens at an inertia weld, and no "
                      "weld position is published; see finding 74"))


def what_is_not_published():
    return dict(
        weld_positions=False, weld_count=False, bolt_count=False,
        bolt_size=False, bolt_circle_radius=False, axial_load=False,
        consequence=("the unit reports joint torque as a function of "
                     "position rather than inventing a position to report "
                     "a number at"))


def summary():
    ws = work_split()
    pc = published_construction()
    v = versus_hpt_joint()
    L = ["Stage E unit E9 -- the HPC rotor structure", ""]
    L.append(f"   published: {pc['line']}")
    L.append(f"      -> inertia welds: {pc['inertia_welds']['count']}, "
             f"position published: {pc['inertia_welds']['position_published']}")
    L.append(f"      -> bolt joints:   {pc['bolt_joints']['count']}, "
             f"position published: {pc['bolt_joints']['position_published']}")
    L += ["", f"   work split closes to {ws['closes_to_C']:.3f} C against "
          f"Fig 14's printed {ws['printed_total_C']} C", ""]
    L.append(f"   torque through a joint sitting aft of each stage, at "
             f"takeoff (HP {v['hpt_joint_torque_kNm']:.1f} kNm):")
    L.append(f"      {'aft of':>7}{'work fwd':>10}{'torque kNm':>12}"
             f"{'of HPT joint':>14}")
    for r in v["rows"]:
        L.append(f"      {r['after_stage']:>7}"
                 f"{next(x['fraction'] for x in joint_demand_curve() if x['after_stage']==r['after_stage']):>10.3f}"
                 f"{r['torque_kNm']:>12.2f}{r['fraction_of_hpt_joint']:>14.3f}")
    cp = candidate_positions()
    L += ["", "   the two stations with material-change evidence "
          "(an argument for neither):"]
    for r in cp["rows"]:
        L.append(f"      aft of stage {r['after_stage']}: {r['torque_kNm']:5.2f} kNm "
                 f"({r['fraction']*100:.0f} % of HP torque) -- {r['why']}")
    n = what_is_not_published()
    L += ["", "   not published: weld positions, weld count, bolt count, "
          "bolt size, bolt-circle radius, axial load"]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
