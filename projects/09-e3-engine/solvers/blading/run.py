#!/usr/bin/env python3
"""C3 unit 12: the HPC sections reconstructed, and their throats."""
import math
import statistics
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from blading.sections import all_sections, implied_max_camber, load, rotor_throat_margins


def main():
    xxii, _ = load()
    cols = xxii["columns"]
    rows = []
    for kind, blocks in (("rotor", xxii["rotors"]), ("stator", xxii["stators"])):
        for blk in blocks:
            for raw in blk["sections"]:
                r = dict(zip(cols, raw))
                rows.append((kind, blk["stage"], r))
    igv = [("igv", 0, dict(zip(cols, raw))) for raw in xxii["igv"]["sections"]]

    print("1. Is the camber line a circular arc?  (stagger - (beta1*+beta2*)/2)")
    print(f"{'family':<9}{'n':>5}{'mean':>9}{'rms':>8}{'implied max camber, % chord':>32}")
    for kind, group in (("rotor", [r for k, _, r in rows if k == "rotor"]),
                        ("stator", [r for k, _, r in rows if k == "stator"]),
                        ("IGV", [r for _, _, r in igv])):
        d = [r["stagger"] - 0.5 * (r["beta1"] + r["beta2"]) for r in group]
        f = [implied_max_camber(r["beta1"], r["beta2"], r["stagger"]) for r in group]
        f = [x * 100 for x in f if x is not None]
        rms = math.sqrt(sum(x * x for x in d) / len(d))
        span = f"median {statistics.median(f):.0f}, range {min(f):.0f}-{max(f):.0f}" if f else "-"
        print(f"{kind:<9}{len(group):>5}{statistics.mean(d):>9.2f}{rms:>8.2f}{span:>32}")

    print("\n2. Do the throats pass the flow?  (throat area above the choking area)")
    tm = rotor_throat_margins()
    print(f"{'stage':>6}{'n':>4}{'M_rel range':>16}{'o/s':>8}{'margin %':>11}")
    for st in range(1, 11):
        sub = [r for r in tm if r["stage"] == st]
        if not sub:
            continue
        ms = [r["m_rel"] for r in sub]
        print(f"{st:>6}{len(sub):>4}{f'{min(ms):.2f}-{max(ms):.2f}':>16}"
              f"{statistics.median([r['o_over_s'] for r in sub]):>8.3f}"
              f"{statistics.median([r['margin'] for r in sub]) * 100:>11.1f}")
    tr = [r["margin"] * 100 for r in tm if r["transonic"]]
    sup = [r["margin"] * 100 for r in tm if r["m_rel"] > 1.0]
    sub = [r["margin"] * 100 for r in tm if not r["transonic"]]
    print(f"\ntransonic rotors 1-4: median {statistics.median(tr):.1f} %   (HPC report: 6 %)")
    print(f"supersonic sections:  median {statistics.median(sup):.1f} %   n={len(sup)}")
    print(f"subsonic rotors 5-10: median {statistics.median(sub):.1f} %")

    print("\n3. Throat position along the chord")
    at = [r["at"] * 100 for r in tm]
    print(f"  median {statistics.median(at):.0f} % of chord, range {min(at):.0f}-{max(at):.0f}")


if __name__ == "__main__":
    main()
