"""Stage C unit C4-4: what the stalled Rotor 37 field actually looks like.

For five runs this case was judged on integrated quantities alone -- mass
flow, outlet temperature, residuals -- and STEP0's first next step was
*inspect the converged stalled field; nothing so far has looked at the
solution.* This is that inspection, made reproducible.

It reads the radial and axial traverses `system/sampleDict` writes and
answers the one question the integrated numbers cannot: is the machine
**blocked at the inlet** or is it **doing no work**? The answer is
neither, and the profiles say so plainly -- the inner two thirds of the
span flows healthily and the outer fifth is reversed.

The sampled files live under `postProcessing/`, which is gitignored as
regenerable output, so the headline numbers are also recorded in
`data/rotor37-stalled-field.yaml` and the checks below fall back to it.

STEP0.md, unit C4-4."""
from __future__ import annotations

import math
import pathlib

import yaml

from e3cycle.cycle import DATA

CASE = pathlib.Path(__file__).resolve().parents[2] / "cfd" / "rotor37"
#: TP-1337 Table I: 20.188 kg/s over 36 blades
DESIGN_SECTOR_FLOW = 20.188 / 36
#: Rotor 37's running tip clearance, and the blade span it sits on
INTENDED_CLEARANCE_MM = 0.356
SPAN_MM = 74.0


def recorded():
    """The headline numbers, kept in `data/` so the finding survives a
    cleaned working tree."""
    return yaml.safe_load((DATA / "rotor37-stalled-field.yaml").read_text())


def _read_xy(name, time="1000"):
    p = CASE / "postProcessing" / "sampleDict" / time / name
    if not p.exists():
        return None
    rows = []
    for line in p.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        v = [float(x) for x in line.split()]
        rows.append(dict(d=v[0], T=v[1], p=v[2], ux=v[3], uy=v[4], uz=v[5]))
    return rows


def traverse(which="inlet_radial", time="1000"):
    return _read_xy(f"{which}_T_p_U.xy", time)


def reversal(which="inlet_radial", time="1000"):
    """Where the axial velocity changes sign, as a span fraction.

    This is the discriminator. A machine "blocked at the inlet" has low or
    reversed flow across the whole span; one "doing no work" has healthy
    axial flow and no temperature rise. Rotor 37's stalled branch has
    neither: it flows properly over the inner span and reverses only near
    the casing."""
    rows = traverse(which, time)
    if rows is None:
        r = recorded()[which]
        return dict(from_file=False, **r)
    span = rows[-1]["d"] - rows[0]["d"]
    first = next((x for x in rows if x["ux"] < 0), None)
    healthy = [x for x in rows if x["ux"] > 0]
    return dict(
        from_file=True,
        reverses=first is not None,
        reversal_span_fraction=(first["d"] - rows[0]["d"]) / span if first else None,
        min_ux=min(x["ux"] for x in rows),
        max_ux=max(x["ux"] for x in rows),
        peak_swirl=min(x["uy"] for x in rows),
        peak_T=max(x["T"] for x in rows),
        healthy_fraction=len(healthy) / len(rows))


def tip_gap_mm():
    """The gap between the blade tip and the casing AT THE BLADE'S OWN
    axial station.

    Measured, because the first attempt at this compared the blade tip
    against the domain's maximum casing radius -- which is at the inlet,
    four centimetres upstream, where the casing is 4.5 mm wider. That gave
    14x the intended clearance and was a unit-and-station error, not a
    finding (see finding 196)."""
    from cfd.rotor37 import casing_at
    stl = CASE / "constant" / "triSurface" / "blade.stl"
    if not stl.exists():
        return recorded()["tip_gap"]
    import struct
    with open(stl, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        rmax, xat = 0.0, 0.0
        for _ in range(n):
            d = f.read(50)
            for k in range(3):
                x, y, z = struct.unpack_from("<3f", d, 12 + 12 * k)
                r = math.hypot(y, z)
                if r > rmax:
                    rmax, xat = r, x
    tip_mm, x_cm = rmax * 1000, xat * 100
    casing_mm = casing_at(x_cm) * 10
    gap = casing_mm - tip_mm
    return dict(from_file=True, blade_tip_mm=tip_mm, blade_tip_x_cm=x_cm,
                casing_at_that_x_mm=casing_mm, gap_mm=gap,
                intended_mm=INTENDED_CLEARANCE_MM,
                ratio=gap / INTENDED_CLEARANCE_MM,
                pct_of_span=100 * gap / SPAN_MM)


def collapse_bracket():
    """The back pressures the ramp had reached when the machine still flowed
    and when it had collapsed. The ramp is linear from 95 kPa at iteration
    300 to 150 kPa at 1200."""
    def p_at(n):
        return 95000 + max(0.0, n - 300) / 900 * 55000
    r = recorded()["collapse"]
    return dict(held_iter=r["held_iter"], held_kPa=p_at(r["held_iter"]) / 1000,
                held_flow_fraction=r["held_flow"] / DESIGN_SECTOR_FLOW,
                collapsed_iter=r["collapsed_iter"],
                collapsed_kPa=p_at(r["collapsed_iter"]) / 1000,
                collapsed_flow_fraction=r["collapsed_flow"] / DESIGN_SECTOR_FLOW)


def summary():
    L = ["Stage C unit C4-4 -- the stalled field, inspected", ""]
    for which in ("inlet_radial", "preblade_radial"):
        r = reversal(which)
        L.append(f"   {which}:")
        if r.get("reverses"):
            L.append(f"      axial velocity reverses at {r['reversal_span_fraction']*100:.0f} % "
                     f"of span, min Ux {r['min_ux']:+.1f} m/s")
            L.append(f"      peak swirl {r['peak_swirl']:+.0f} m/s, "
                     f"peak T {r['peak_T']:.0f} K, "
                     f"{r['healthy_fraction']*100:.0f} % of the traverse still flows forward")
        else:
            L.append("      no reversal")
    g = tip_gap_mm()
    L += ["", f"   tip gap {g['gap_mm']:.3f} mm against an intended "
          f"{g['intended_mm']:.3f} -- {g['ratio']:.1f}x, "
          f"{g['pct_of_span']:.2f} % of span"]
    c = collapse_bracket()
    L += ["", f"   still flowing at {c['held_kPa']:.1f} kPa "
          f"({c['held_flow_fraction']*100:.0f} % of design flow)",
          f"   collapsed by     {c['collapsed_kPa']:.1f} kPa "
          f"({c['collapsed_flow_fraction']*100:.0f} %)"]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
