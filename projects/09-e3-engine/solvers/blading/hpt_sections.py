"""C3 unit 14: the HPT's blading geometry, without a single coordinate.

CR-167955 Table IV prints, for each of the four rows, the count, the
axial solidity AW/t, a Zweifel number, the trailing-edge blockage, the
aspect ratio h/d0 and the unguided turn. Fig 6 -- the actual airfoil
shapes -- is a figure and was not transcribed.

But **h/d0 is height over throat**, and Fig 3 gives the annulus heights.
So the throat follows from two printed numbers, the pitch from the count
and the radius, and then cos^-1(o/s) gives the outlet angle by the same
R&M 2974 rule unit 13 used on the LPT. None of that touches the vector
diagrams, which say what the answer should be. STEP0.md, unit 14."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA
from meanline.losses import AM, _interp

CM = 0.01
ROWS = ["stage1_vane", "stage2_vane", "stage1_blade", "stage2_blade"]
# which Fig 3 station bounds each row's exit annulus
EXIT_STATION = {"stage1_vane": "stage1_vane_exit", "stage1_blade": "stage1_blade_exit",
                "stage2_vane": "stage2_vane_exit", "stage2_blade": "stage2_blade_exit"}


def load():
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    return pub["hpt"]


@dataclass
class HptRow:
    row: str
    count: int
    height_m: float
    r_pitch_m: float
    pitch_m: float
    aspect_ratio: float
    throat_m: float
    o_over_s: float
    acos_deg: float
    alpha2_rule: float
    solidity: float
    axial_width_m: float
    zweifel: float
    zweifel_printed: float
    te_blockage_pct: float
    unguided_turn_deg: float


def analyse(mean_line_angles=None):
    """mean_line_angles: {row: (alpha_in, alpha_out)} in degrees, magnitudes.
    Defaults to the unit-3 HPT mean-line result."""
    hpt = load()
    bg = hpt["blading_geometry"]
    st = {x["location"]: x for x in hpt["flowpath"]["stations"]}
    ta = hpt["stage_aerodynamics"]
    if mean_line_angles is None:
        from meanline.hpt import solve
        _, _, stages, _ = solve()
        mean_line_angles = {
            "stage1_vane": (0.0, stages[0].alpha2),
            "stage1_blade": (stages[0].beta2, stages[0].beta3),
            "stage2_vane": (stages[0].alpha3, stages[1].alpha2),
            "stage2_blade": (stages[1].beta2, stages[1].beta3),
        }
    out = []
    for i, name in enumerate(ROWS):
        s = st[EXIT_STATION[name]]
        h = (s["r_tip_cm"] - s["r_hub_cm"]) * CM
        r = 0.5 * (s["r_tip_cm"] + s["r_hub_cm"]) * CM
        n = bg["count"][i]
        pitch = 2 * math.pi * r / n
        ar = bg["aspect_ratio_h_d0"][i]
        throat = h / ar
        o_s = throat / pitch
        acos = math.degrees(math.acos(min(o_s, 1.0)))
        f5 = AM["fig5_outlet_angle"]
        rule = _interp(acos, f5["acos_o_over_s_deg"], f5["alpha2_star_deg"])
        sol = bg["solidity_AW_over_t"][i]
        bx = sol * pitch
        a1, a2 = mean_line_angles[name]
        zw = 2 * (pitch / bx) * math.cos(math.radians(a2)) ** 2 * (
            math.tan(math.radians(a1)) + math.tan(math.radians(a2)))
        out.append(HptRow(name, n, h, r, pitch, ar, throat, o_s, acos, rule, sol, bx,
                          zw, bg["zweifel"][i], bg["te_blockage_pct"][i], bg["unguided_turn_deg"][i]))
    return out, mean_line_angles


if __name__ == "__main__":
    import statistics
    res, angles = analyse()
    print("throat recovered from Table IV's aspect ratio and Fig 3's annulus heights")
    print(f"{'row':<14}{'N':>4}{'h cm':>7}{'r cm':>7}{'s cm':>7}{'h/d0':>6}{'d0 cm':>7}"
          f"{'o/s':>7}{'acos':>8}{'a2 rule':>9}{'a2 mean-line':>14}{'diff':>7}")
    for r in res:
        a2 = angles[r.row][1]
        print(f"{r.row:<14}{r.count:>4}{r.height_m*100:>7.2f}{r.r_pitch_m*100:>7.2f}{r.pitch_m*100:>7.3f}"
              f"{r.aspect_ratio:>6.1f}{r.throat_m*100:>7.3f}{r.o_over_s:>7.3f}{r.acos_deg:>8.2f}"
              f"{r.alpha2_rule:>9.2f}{a2:>14.2f}{r.alpha2_rule - a2:>7.2f}")
    d = [r.alpha2_rule - angles[r.row][1] for r in res]
    print(f"\noutlet angle vs the unit-3 mean-line: mean {statistics.mean(d):+.2f} deg, "
          f"rms {math.sqrt(sum(x*x for x in d)/len(d)):.2f}, worst {max(abs(x) for x in d):.2f}")
    print(f"\n{'row':<14}{'sigma':>8}{'bx cm':>8}{'s/bx':>7}{'Zweifel':>9}{'Table IV':>10}{'diff':>8}")
    for r in res:
        print(f"{r.row:<14}{r.solidity:>8.2f}{r.axial_width_m*100:>8.3f}{r.pitch_m/r.axial_width_m:>7.3f}"
              f"{r.zweifel:>9.3f}{r.zweifel_printed:>10.2f}{r.zweifel - r.zweifel_printed:>8.3f}")
    dz = [r.zweifel - r.zweifel_printed for r in res]
    print(f"\nZweifel vs Table IV: mean {statistics.mean(dz):+.3f}, rms {math.sqrt(sum(x*x for x in dz)/len(dz)):.3f}")
