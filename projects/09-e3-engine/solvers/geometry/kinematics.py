"""Unit H4 -- what the assembled engine implies about motion.

Stage H's closure is two closures wearing one name. The hand-CAD half --
casings, frames, sumps, bearing loads -- needs a human at a GUI and stays
gated. This is the other half: *zero clashes through rotation*, which G3's
placement turned from a sweep into a proof, plus the engine orders the
assembly's own blade counts generate.

Nothing here builds geometry that G3 has not already built, and nothing
here is drawn.
"""
from __future__ import annotations

import math
import pathlib

import yaml

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def _y(name):
    return yaml.safe_load((DATA / name).read_text())


# --- bands 1 and 2: the clash proof -----------------------------------------

def overlapping_pairs(rows=None):
    """EVERY pair of rows whose assembled axial extents overlap -- not only
    the consecutive ones G3 checked.

    Two rows that share no axial interval cannot touch at any relative
    angular position, for any blade of either, so an empty result is a
    proof of band 1 and not a sample of it. The pair is reported with its
    gap so a near miss is visible.
    """
    from geometry.assembly import row_extents
    ext = row_extents(rows)
    out = []
    for i in range(len(ext)):
        for j in range(i + 1, len(ext)):
            a, b = ext[i], ext[j]
            gap = b["x_lo"] - a["x_hi"]
            if gap < 0.0:
                out.append(dict(a=a["row"], b=b["row"], gap_mm=gap * 1000.0))
    return out


def sweep_is_redundant(rows=None, steps=360):
    """Band 2. A full-rotation sweep over one LP revolution.

    The proof in `overlapping_pairs` is an axial statement, and rotation
    about the engine axis cannot change an axial coordinate -- so the sweep
    should find the same gap at every angle. It is run anyway, on the real
    solids and not on the argument, because a proof of the right thing can
    still sit on a wrong placement: a transform that quietly carried a
    scale, a shear or an off-axis rotation centre would leave the argument
    intact and the gaps moving. Unit J7's finding 171 is exactly that
    failure mode caught one artefact earlier.

    The tightest consecutive pair carries the check, and it is the tightest
    pair that has a real gap -- not the fan/booster pair, whose 0.0 mm is
    an artefact of the booster being defined at the fan's downstream end
    (G3 finding 224).
    """
    import cadquery as cq
    from geometry.assembly import axial_clearances, placed_rows

    gaps = sorted((g for g in axial_clearances(rows) if g["gap_m"] > 1e-9),
                  key=lambda g: g["gap_m"])
    tight = gaps[0]
    placed = {e["row"].name: e for e in placed_rows(rows)}
    a, b = placed[tight["upstream"]], placed[tight["downstream"]]
    sa, sb = a["row"].solid(), b["row"].solid()
    ratio = lp_hp_ratio()

    def x_hi(solid, off, theta_deg):
        return off + solid.rotate((0, 0, 0), (1, 0, 0), theta_deg).BoundingBox().xmax

    def x_lo(solid, off, theta_deg):
        return off + solid.rotate((0, 0, 0), (1, 0, 0), theta_deg).BoundingBox().xmin

    vals = []
    for k in range(steps):
        lp = 360.0 * k / steps
        hp = lp * ratio
        ta = lp if a["row"].spool == "lp" else hp if a["row"].spool == "hp" else 0.0
        tb = lp if b["row"].spool == "lp" else hp if b["row"].spool == "hp" else 0.0
        vals.append(x_lo(sb, b["x_m"], tb) - x_hi(sa, a["x_m"], ta))
    return dict(steps=steps, pair=(tight["upstream"], tight["downstream"]),
                min_gap_mm=min(vals) * 1000.0,
                spread_mm=(max(vals) - min(vals)) * 1000.0)


# --- band 3: one ratio everywhere -------------------------------------------

def lp_hp_ratio():
    from publication.render import RPM_LP, RPM_HP
    return RPM_HP / RPM_LP


def ratio_routes():
    from verification.consistency import spool_speeds_four_routes
    return dict(gltf=lp_hp_ratio(),
                four_route=spool_speeds_four_routes()["ratio"])


# --- band 4: the engine orders the assembly generates ------------------------

def hpc_campbell_orders():
    """Does each HPC rotor's printed Campbell diagram carry the vane counts
    of the two stators it sits between?

    The per-rev lines on a rotor-blade Campbell diagram are the engine
    orders that can excite it, and the strongest of those are the vane
    counts immediately upstream and downstream. So this asks whether the
    counts THIS PROJECT builds the assembly from are the counts GE drew
    its diagrams against -- two different tables in the same report,
    compared for the first time.
    """
    counts = _y("e3-fps-published.yaml")["hpc"]["stator_vane_counts"]
    camp = _y("hpc-rotor-campbell.yaml")["stages"]
    rows = []
    for n in range(1, 11):
        st = camp[n] if isinstance(camp, dict) and n in camp else \
            next(s for s in (camp.values() if isinstance(camp, dict) else camp)
                 if s.get("stage") == n)
        lines = set(st["per_rev_lines"])
        up = counts["igv"] if n == 1 else counts[f"s{n - 1}"]
        down = counts[f"s{n}"]
        rows.append(dict(stage=n, upstream=up, downstream=down,
                         lines=sorted(lines),
                         upstream_present=up in lines,
                         downstream_present=down in lines))
    return rows


def lpt_order_on_the_hpt_blade():
    """The HPT blade Campbell's 72/rev against the LPT stage-1 vane count
    the assembly places. Two reports, one number."""
    orders = _y("hpt-mechanical.yaml")["stage2_blade"]["campbell"]["forcing_per_rev"]
    lpt = _y("e3-fps-published.yaml")["lpt"]["vane_counts_per_stage"]["value"][0]
    return dict(hpt_campbell=orders["lpt_stage1_vanes"], lpt_assembly=lpt,
                equal=orders["lpt_stage1_vanes"] == lpt)


# --- band 5: blade passing ---------------------------------------------------

def blade_passing(rows=None):
    from publication.render import RPM_LP, RPM_HP
    from geometry.assembly import row_extents
    out = []
    for r in row_extents(rows):
        rpm = RPM_LP if r["spool"] == "lp" else RPM_HP if r["spool"] == "hp" else 0.0
        out.append(dict(row=r["row"], spool=r["spool"], count=r["count"],
                        rpm=rpm, bpf_hz=r["count"] * rpm / 60.0))
    return out


def main():
    print("Unit H4 -- the assembly's kinematics\n")
    bad = overlapping_pairs()
    from geometry.assembly import row_extents
    n = len(row_extents())
    print(f"band 1  {n} rows, {n * (n - 1) // 2} pairs; axially overlapping: "
          f"{len(bad)}")
    for b in bad:
        print(f"         {b['a']} / {b['b']}  {b['gap_mm']:+.2f} mm")

    s = sweep_is_redundant()
    print(f"band 2  {s['steps']}-step sweep over one LP revolution: minimum "
          f"row-to-row gap {s['min_gap_mm']:.2f} mm, spread {s['spread_mm']:.3f} mm")

    r = ratio_routes()
    print(f"band 3  LP:HP  glTF {r['gltf']:.4f}   I1 four-route "
          f"{r['four_route']:.4f}   {abs(r['gltf']/r['four_route']-1)*100:.2f} %")

    print("\nband 4  HPC rotor Campbell per-rev lines against the stator counts")
    print(f"  {'stage':>5}{'up':>5}{'down':>6}  {'up?':>4}{'down?':>6}   lines")
    hits_up = hits_down = 0
    for x in hpc_campbell_orders():
        hits_up += x["upstream_present"]
        hits_down += x["downstream_present"]
        print(f"  {x['stage']:>5}{x['upstream']:>5}{x['downstream']:>6}  "
              f"{str(x['upstream_present']):>4}{str(x['downstream_present']):>6}   "
              f"{x['lines']}")
    print(f"  downstream present on {hits_down} of 10, upstream on {hits_up} of 10")
    L = lpt_order_on_the_hpt_blade()
    print(f"  HPT blade Campbell's LPT order {L['hpt_campbell']} vs the "
          f"assembly's LPT stage-1 vane count {L['lpt_assembly']}: {L['equal']}")

    print("\nband 5  blade passing at the design speeds")
    print(f"  {'row':<18}{'spool':>7}{'n':>5}{'rpm':>8}{'BPF Hz':>10}")
    for b in blade_passing():
        print(f"  {b['row']:<18}{b['spool']:>7}{b['count']:>5}{b['rpm']:>8.0f}"
              f"{b['bpf_hz']:>10.0f}")


if __name__ == "__main__":
    main()
