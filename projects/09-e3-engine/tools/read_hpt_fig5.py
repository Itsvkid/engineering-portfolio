#!/usr/bin/env python3
"""Read HPT report Fig 5c (stage energy extraction against annulus height)
off the scan numerically rather than by eye.

CR-167955 p.13 is stamped "ORIGINAL PAGE IS OF POOR QUALITY" by NASA
itself, so the curve is extracted by finding, on each scan line, the
rightmost thin dark run inside the plot box that is not a gridline and
not the box edge. Run this to regenerate data/hpt-fig5.yaml."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

PDF = pathlib.Path(__file__).resolve().parents[1] / "sources" / "e3-hp-turbine-hardware-CR-167955.pdf"
PDF_PAGE = 22          # report p.13, offset +8 (DATA-INDEX)
# Plot geometry at 300 dpi. The x scale is calibrated by least squares on
# the labelled gridlines rather than by assuming the right-hand box edge is
# a round number -- on the stage-2 panel it is not (see AS_PRINTED below).
Y100, Y0 = 2171, 2846
PANELS = {
    "stage1": dict(x0=611, x1=1480, grid=[611, 897.5, 1191, 1480], grid_val=[200.0, 250.0, 300.0, 350.0]),
    "stage2": dict(x0=1675, x1=2249, grid=[1675.5, 1979], grid_val=[200.0, 250.0]),
}
AS_PRINTED = (
    "The stage-1 panel's four labelled gridlines are evenly spaced to under a "
    "pixel (289.7 px per 50 kJ/kg), so its box spans exactly 200-350. The "
    "stage-2 panel's single interior gridline sits 303.5 px from its left "
    "edge; at the stage-1 scale that is 252.4, not the 250 it is labelled, "
    "and its right-hand box edge falls at about 295-299 rather than the 300 "
    "the axis suggests. Calibrating on the two labelled gridlines gives a "
    "scale 5.6 percent finer than assuming 300 at the edge. Recorded, not "
    "corrected: the panel is hand-drawn and the page carries NASA's own "
    "poor-quality stamp."
)


def render(page=PDF_PAGE, dpi=300):
    tmp = pathlib.Path(tempfile.mkdtemp()) / "fig5"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png",
                    str(PDF), str(tmp)], check=True)
    return np.array(Image.open(f"{tmp}-0{page}.png").convert("L"))


def _calibrate(grid, grid_val):
    """least-squares px -> value on the labelled gridlines"""
    n = len(grid)
    mx, mv = sum(grid) / n, sum(grid_val) / n
    num = sum((g - mx) * (v - mv) for g, v in zip(grid, grid_val))
    den = sum((g - mx) ** 2 for g in grid)
    slope = num / den
    return slope, mv - slope * mx


def extract(a, x0, x1, grid, grid_val, step=5):
    slope, intercept = _calibrate(grid, grid_val)
    v0 = intercept + slope * x0
    v1 = intercept + slope * x1
    pts = []
    for pct in range(0, 101, step):
        y = int(round(Y0 + (Y100 - Y0) * pct / 100))
        band = a[max(y - 1, 0):y + 2, x0 + 6:x1 - 5]
        col = (band < 120).sum(axis=0)
        keep = [x0 + 6 + i for i, v in enumerate(col)
                if v >= 2 and all(abs(x0 + 6 + i - g) > 8 for g in grid)]
        if not keep:
            continue
        runs, cur = [], [keep[0]]
        for g in keep[1:]:
            if g - cur[-1] <= 5:
                cur.append(g)
            else:
                runs.append(cur)
                cur = [g]
        runs.append(cur)
        runs = [r for r in runs if 2 <= len(r) <= 30]
        if not runs:
            continue
        xc = sum(runs[-1]) / len(runs[-1])
        val = intercept + slope * xc
        if val > v1 - 4 or val < v0 + 4:      # the box edge, not the curve
            continue
        pts.append((pct, val))
    # one pass of smoothness rejection against the local neighbours
    out = []
    for pct, val in pts:
        nb = [w for q, w in pts if q != pct and abs(q - pct) <= 10]
        if nb and abs(val - sum(nb) / len(nb)) > 8:
            continue
        out.append((pct, round(val, 1)))
    return out


def _wrap(text, width=68):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return lines


def main():
    a = render()
    res = {name: extract(a, **cfg) for name, cfg in PANELS.items()}
    lines = ['# HPT report CR-167955 Figure 5c, "Blading Parameters" -- stage energy',
             '# extraction against annulus height, read off the 300 dpi scan by',
             '# tools/read_hpt_fig5.py (not by eye). The page carries NASA\'s own',
             '# "ORIGINAL PAGE IS OF POOR QUALITY" stamp; see the uncertainty below.',
             '',
             'meta:',
             '  src: "CR-167955 Fig.5c p.13 (PDF page 22); extracted by tools/read_hpt_fig5.py"',
             '  transcribed: 2026-09-06',
             '  method: rightmost thin dark run per scan line inside the plot box, excluding gridlines and box edges',
             '  read_off_uncertainty_kJ_kg: 5',
             '  axis: {y: annulus height percent, x: stage energy extraction kJ/kg}',
             '  as_printed: >',
             *[f'    {l}' for l in _wrap(AS_PRINTED)],
             '']
    for name, pts in res.items():
        lines.append(f"{name}:")
        lines.append("  pct_height: [" + ", ".join(str(p) for p, _ in pts) + "]")
        lines.append("  dh_kJ_kg:   [" + ", ".join(f"{v:.1f}" for _, v in pts) + "]")
    (pathlib.Path(__file__).resolve().parents[1] / "data" / "hpt-fig5.yaml").write_text("\n".join(lines) + "\n")
    for name, pts in res.items():
        print(f"{name}: {len(pts)} points, {min(v for _, v in pts):.0f}-{max(v for _, v in pts):.0f} kJ/kg")


if __name__ == "__main__":
    sys.exit(main())
