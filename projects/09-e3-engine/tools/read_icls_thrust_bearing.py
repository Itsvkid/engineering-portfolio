#!/usr/bin/env python3
"""ICLS report Figs 340 and 341 -- the measured thrust-bearing axial loads.

CR-168211 pp.527-528 print the "on line" calculation of the HP (No. 3) and
LP (No. 1) thrust-bearing axial load against corrected speed, each with a
pounds axis AND a kN axis.  Unit E4 recorded in 2026-09-07 that "no bearing
load and no bearing capacity" is printed; that was true of CR-168219 sec
5.7 and false of the source list (finding 269).

What this script measures, and what it does NOT
-----------------------------------------------
It locates the plot grid numerically and measures the two *crossings* --
the speed at which each curve reaches the edge of its box -- because a
box edge is a sharp, unambiguous feature.  It then closes the printed
pounds axis against the printed kN axis, which is arithmetic on the axis
labels and needs no reading at all.

A per-column trace of the curve was attempted and abandoned: both figures
overplot dense clusters of individual test symbols ON the drawn curve, in
the same ink weight, and over most of the width the curve is horizontal,
so the rightmost-thin-dark-run method that works on HPT Fig 5c's steep
curves picks symbols instead (finding 272).  Values between the crossings
are therefore read by eye against these gridlines and carry half a minor
division, recorded in data/icls-thrust-bearing.yaml.
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "sources" / "e3-icls-design-and-performance-CR-168211.pdf"

LBF_PER_UNIT = 100.0                # both axes read "Thrust - Pounds x 10^2"
N_PER_LBF = 4.4482216

# report pp.527, 528; ICLS offset +25 (DATA-INDEX). Grid rows/cols at 300 dpi.
FIGS = {
    "fig340_hp_no3": dict(
        page=552, x_zero=619.0, px_per_pct=9.87,
        ygrid=[1005, 1190, 1379, 1566, 1755, 1934],
        yval=[100.0, 80.0, 60.0, 40.0, 20.0, 0.0],
        printed_kn=[44.5, 35.6, 26.7, 17.8, 8.9, 0.0],
        edge_row=1002, edge_val=100.0, search=(1300, 1600)),
    "fig341_lp_no1": dict(
        page=553, x_zero=764.0, px_per_pct=9.94,
        ygrid=[983, 1172, 1367, 1560, 1753],
        yval=[-10.0, -50.0, -90.0, -130.0, -170.0],
        printed_kn=[-4.4, -22.2, -40.0, -57.8, -75.6],
        edge_row=1830, edge_val=None, search=(1600, 1756)),
}


def render(page, dpi=300):
    tmp = pathlib.Path(tempfile.mkdtemp()) / "icls"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page),
                    "-png", str(PDF), str(tmp)], check=True)
    return np.array(Image.open(f"{tmp}-{page}.png").convert("L"))


def calibrate(spec):
    """least squares px row -> axis units, on the LABELLED gridlines"""
    a, b = np.polyfit(spec["ygrid"], spec["yval"], 1)
    rms = float(np.sqrt(np.mean(
        (np.polyval([a, b], spec["ygrid"]) - np.array(spec["yval"])) ** 2)))
    return a, b, rms


def axis_closure(spec):
    """the printed kN axis against the printed pound axis -- pure arithmetic"""
    kn = np.array(spec["yval"]) * LBF_PER_UNIT * N_PER_LBF / 1000.0
    return float(np.abs(kn - np.array(spec["printed_kn"])).max())


def edge_crossing(img, spec, thresh=128):
    """the speed at which the curve reaches the given box edge row"""
    lo, hi = spec["search"]
    row = np.where(img[spec["edge_row"], lo:hi] < thresh)[0] + lo
    runs, cur = [], [row[0]]
    for c in row[1:]:
        if c - cur[-1] <= 3:
            cur.append(c)
        else:
            runs.append(cur)
            cur = [c]
    runs.append(cur)
    # the vertical gridlines sit on exact 10 % marks; the curve does not
    cand = [r for r in runs if len(r) < 25]
    cand = [r for r in cand
            if min(abs((np.mean(r) - spec["x_zero"]) / spec["px_per_pct"] - 10 * k)
                   for k in range(11)) > 1.5]
    # the drawn curve is the heaviest mark on the line; stray symbols are thinner
    best = max(cand, key=len)
    a, b, _ = calibrate(spec)
    return ((np.mean(best) - spec["x_zero"]) / spec["px_per_pct"],
            float(np.polyval([a, b], spec["edge_row"])))


def read():
    out = {}
    for name, spec in FIGS.items():
        img = render(spec["page"])
        a, b, rms = calibrate(spec)
        pct, val = edge_crossing(img, spec)
        out[name] = dict(
            calibration_rms_units=rms,
            px_per_unit=abs(1.0 / a),
            axis_closure_kN=axis_closure(spec),
            edge_pct=pct,
            edge_lbf=val * LBF_PER_UNIT,
            edge_kN=val * LBF_PER_UNIT * N_PER_LBF / 1000.0)
    return out


if __name__ == "__main__":
    for name, r in read().items():
        print(f"\n{name}")
        print(f"  grid calibration rms     {r['calibration_rms_units']:.3f} axis units"
              f"  ({r['px_per_unit']:.2f} px per unit)")
        print(f"  lb axis vs kN axis       {r['axis_closure_kN']:.3f} kN worst")
        print(f"  curve reaches box edge   {r['edge_kN']:+.1f} kN "
              f"({r['edge_lbf']:+.0f} lbf) at {r['edge_pct']:.1f} % corrected speed")
