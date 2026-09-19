#!/usr/bin/env python3
"""Read HPC report Figure 30 (p.59, PDF page 68) -- "Rotor Design Features"
-- off the scan numerically rather than by eye.

The figure is the whole ten-stage HPC rotor in meridional section: ten
airfoils, ten discs with their webs and bores, the integral forward stub
shaft, the one bolt joint and the three-tooth CDP seal. **It carries no
dimension.** What makes it readable is that the annulus it is drawn
against IS published, at every row's leading and trailing edge, in
`data/hpc-flowpath.csv` (Table XXI streamlines 1 and 12). So the page is
calibrated on twenty published radii -- ten blade tips and ten blade roots
-- and the un-dimensioned quantities (the disc bore radii, the bolt-joint
radius, the CDP seal) are then read off.

Three things this file does that a ruler does not:

* it fits the calibration, so the residual against each of the twenty
  published radii is a number and not an impression;
* it carries an **x term**. A single (scale, offset) in y fits the ten tip
  radii to 0.046 cm and then misses the ten root radii by up to 1.1 cm,
  with the miss ordered by blade span. Adding one shear parameter --
  a 0.40 degree rotation of the scan -- collapses all twenty to 0.054 cm
  rms. J8 met the same page defect on CR-159584 Fig 1 and answered it with
  two independent scales; a rotation is the one-parameter form of that, and
  here it is the right one, because once it is removed the radial and axial
  scales agree to 1.6 percent (see solvers/mechanical/STEP0.md unit E11);
* every radius is read twice -- once from the fitted calibration, once as a
  depth below the *published* hub radius of its own stage, which uses the
  scale but not the intercept.

Run this to regenerate data/hpc-disc-profile.yaml.
"""
from __future__ import annotations

import csv
import pathlib
import subprocess
import tempfile

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "sources" / "e3-hp-compressor-detail-design.pdf"
PDF_PAGE = 68            # report p.59, offset +9 (DATA-INDEX)
DPI = 600
THRESH = 128

#: x-windows containing each rotor's drawn blade tip, read off a
#: topmost-dark-pixel profile taken every 10 px across the whole figure.
#: Generous: the RANSAC fit below trims them to the inliers.
TIP_WIN = {1: (1515, 1890), 2: (2225, 2405), 3: (2735, 2890), 4: (3155, 3280),
           5: (3510, 3620), 6: (3860, 3965), 7: (4150, 4250), 8: (4487, 4580),
           9: (4770, 4860), 10: (5020, 5115)}
#: the bore feet sit under their own blades; this is the y band to search
BORE_BAND = (2800, 3100)
#: the CDP seal disc is aft of stage 10 and is the rotor's last disc
CDP_WIN = (5380, 5520)
CDP_BAND = (2950, 3120)
#: the bolt-head/nut assembly of the one bolt joint
BOLT_WIN = (3430, 3650)
BOLT_BAND = (2270, 2350)

AS_PRINTED = (
    "Figure 30 carries no dimension and no centreline; the engine axis "
    "falls below the drawn area. Its NASA page stamp is ORIGINAL PAGE IS OF "
    "POOR QUALITY, but the linework is clean -- the ten tip lines fit to "
    "1.0-1.6 px rms at 600 dpi. Stage 1 has no bore foot: its disc runs "
    "forward and inward into the integral stub shaft, so only stages 2-10 "
    "and the CDP seal disc give a bore radius. The drawn line is 3-6 px "
    "thick (0.06-0.12 cm at the fitted scale) and that, not the fit, sets "
    "the floor on a read."
)


# --------------------------------------------------------------- the scan

def render(page: int = PDF_PAGE, dpi: int = DPI) -> np.ndarray:
    tmp = pathlib.Path(tempfile.mkdtemp()) / "fig30"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page),
                    "-png", str(PDF), str(tmp)], check=True)
    return np.array(Image.open(f"{tmp}-0{page}.png").convert("L"))


# ----------------------------------------------------------- line finding

def _topmost(dark, x, y0=1620, y1=2450):
    col = np.flatnonzero(dark[y0:y1, x])
    return y0 + col[0] if len(col) else None


def _ransac(pts, tol=4.0, iters=4000, seed=0):
    """A straight line through the dominant collinear set. The airfoil tip
    edge owns 250-400 of the columns in its window; a leader line crossing
    it owns tens, at a different angle."""
    rng = np.random.default_rng(seed)
    p = np.asarray(pts, float)
    best = (-1, None)
    for _ in range(iters):
        i, j = rng.integers(0, len(p), 2)
        if abs(p[i, 0] - p[j, 0]) < 20:
            continue
        m = (p[j, 1] - p[i, 1]) / (p[j, 0] - p[i, 0])
        c = p[i, 1] - m * p[i, 0]
        k = int((np.abs(p[:, 1] - (m * p[:, 0] + c)) < tol).sum())
        if k > best[0]:
            best = (k, (m, c))
    m, c = best[1]
    inl = np.abs(p[:, 1] - (m * p[:, 0] + c)) < tol
    a, b = np.polyfit(p[inl, 0], p[inl, 1], 1)
    res = p[inl, 1] - (a * p[inl, 0] + b)
    return dict(slope=float(a), intercept=float(b),
                x_lo=float(p[inl, 0].min()), x_hi=float(p[inl, 0].max()),
                n_in=int(inl.sum()), n=len(p), rms_px=float(res.std()))


def _runs(dark, x0, x1, y0, y1, frac=0.7):
    """y intervals over which at least `frac` of the columns are dark --
    a horizontal line, however short."""
    cov = dark[y0:y1, x0:x1].mean(axis=1) >= frac
    out, cur = [], None
    for i, v in enumerate(cov):
        if v and cur is None:
            cur = i
        if not v and cur is not None:
            out.append((y0 + cur, y0 + i - 1))
            cur = None
    if cur is not None:
        out.append((y0 + cur, y0 + len(cov) - 1))
    return out


def extract(a: np.ndarray) -> dict:
    dark = a < THRESH
    stages = {}
    for s, (x0, x1) in TIP_WIN.items():
        pts = [(x, _topmost(dark, x)) for x in range(x0, x1)]
        pts = [p for p in pts if p[1] is not None]
        tip = _ransac(pts)
        xm = (tip["x_lo"] + tip["x_hi"]) / 2
        y_tip = tip["slope"] * xm + tip["intercept"]
        band = (int(xm - 25), int(xm + 25))
        # the airfoil root: first strong horizontal line below the tip
        below = _runs(dark, *band, int(y_tip) + 30, 2600)
        y_root = (below[0][0] + below[0][1]) / 2 if below else None
        # the bore: the deepest strong horizontal line inside the bore band
        feet = _runs(dark, *band, *BORE_BAND)
        y_bore = (feet[0][0] + feet[0][1]) / 2 if feet else None
        stages[s] = dict(tip=tip, x_mid=float(xm), y_tip=float(y_tip),
                         y_root=None if y_root is None else float(y_root),
                         y_bore=None if y_bore is None else float(y_bore),
                         root_run=below[0] if below else None,
                         bore_run=feet[0] if feet else None)
    cdp = _runs(dark, *CDP_WIN, *CDP_BAND)
    bolt = _runs(dark, *BOLT_WIN, *BOLT_BAND, frac=0.5)
    return dict(stages=stages,
                cdp_bore=dict(x_mid=float(sum(CDP_WIN) / 2),
                              y=float(sum(cdp[0]) / 2) if cdp else None),
                bolt=dict(x_mid=float(sum(BOLT_WIN) / 2),
                          y=float(sum(bolt[0]) / 2) if bolt else None,
                          x_lo=float(BOLT_WIN[0]), x_hi=float(BOLT_WIN[1])))


# ------------------------------------------------------------ calibration

def published_annulus() -> dict:
    """mean of LE and TE tip and hub radius, and mean tip z, per rotor"""
    rows = {}
    with open(ROOT / "data" / "hpc-flowpath.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            rows[(r["row"], r["edge"])] = r
    out = {}
    for s in range(1, 11):
        le, te = rows[(f"R{s}", "LE")], rows[(f"R{s}", "TE")]
        out[s] = dict(
            r_tip=(float(le["r_tip_cm"]) + float(te["r_tip_cm"])) / 2,
            r_hub=(float(le["r_hub_cm"]) + float(te["r_hub_cm"])) / 2,
            z_tip=(float(le["z_tip_cm"]) + float(te["z_tip_cm"])) / 2)
    return out


def fit_radial(feat, pub, stages=range(1, 11), shear=True):
    """r = a + b*y (+ c*x). The x term is a rotation of the scan, not a
    second scale -- see the module docstring."""
    X, Y, R = [], [], []
    for s in stages:
        f = feat["stages"][s]
        X += [f["x_mid"], f["x_mid"]]
        Y += [f["y_tip"], f["y_root"]]
        R += [pub[s]["r_tip"], pub[s]["r_hub"]]
    X, Y, R = np.array(X), np.array(Y), np.array(R)
    A = np.c_[np.ones_like(X), Y, X] if shear else np.c_[np.ones_like(X), Y]
    coef, *_ = np.linalg.lstsq(A, R, rcond=None)
    res = R - A @ coef
    c = tuple(coef) if shear else (coef[0], coef[1], 0.0)
    return dict(a=float(c[0]), b=float(c[1]), c=float(c[2]),
                px_per_cm=float(-1 / c[1]),
                shear=float(c[2] / c[1]),
                rot_deg=float(np.degrees(np.arctan(c[2] / c[1]))),
                rms_cm=float(res.std()), max_cm=float(np.abs(res).max()),
                n=len(R))


def radius(cal, x, y):
    return cal["a"] + cal["b"] * y + cal["c"] * x


def fit_axial(feat, pub, cal):
    """z along the drawing's own x, with the rotation taken from the radial
    fit rather than fitted again -- x and y are collinear across the ten
    tip mid-chords, so a free shear here is not determined."""
    k = -cal["shear"]           # rotate back by the same angle
    u = np.array([feat["stages"][s]["x_mid"] + k * feat["stages"][s]["y_tip"]
                  for s in range(1, 11)])
    z = np.array([pub[s]["z_tip"] for s in range(1, 11)])
    m, q = np.polyfit(u, z, 1)
    res = z - (m * u + q)
    return dict(px_per_cm=float(1 / m), a=float(q), b=float(m),
                rms_cm=float(res.std()), max_cm=float(np.abs(res).max()))


def axial(feat, cal, ax, x, y):
    return ax["a"] + ax["b"] * (x - cal["shear"] * y)


# ------------------------------------------------------------------ write

def build() -> dict:
    a = render()
    feat = extract(a)
    pub = published_annulus()
    cal = fit_radial(feat, pub)
    ax = fit_axial(feat, pub, cal)

    tips, roots, bores = [], [], []
    for s in range(1, 11):
        f = feat["stages"][s]
        tips.append(dict(stage=s, y_px=f["y_tip"],
                         r_cm=round(radius(cal, f["x_mid"], f["y_tip"]), 3),
                         published_cm=round(pub[s]["r_tip"], 3),
                         residual_cm=round(radius(cal, f["x_mid"], f["y_tip"])
                                           - pub[s]["r_tip"], 3)))
        roots.append(dict(stage=s, y_px=f["y_root"],
                          r_cm=round(radius(cal, f["x_mid"], f["y_root"]), 3),
                          published_cm=round(pub[s]["r_hub"], 3),
                          residual_cm=round(radius(cal, f["x_mid"], f["y_root"])
                                            - pub[s]["r_hub"], 3)))
        if s == 1:
            continue                 # stage 1 has no bore foot -- stub shaft
        r1 = radius(cal, f["x_mid"], f["y_bore"])
        depth = (f["y_bore"] - f["y_root"]) * (-cal["b"])
        r2 = pub[s]["r_hub"] - depth
        bores.append(dict(stage=s, y_px=f["y_bore"],
                          z_cm=round(axial(feat, cal, ax, f["x_mid"], f["y_bore"]), 2),
                          r_calibrated_cm=round(r1, 3),
                          r_depth_below_published_hub_cm=round(r2, 3),
                          two_routes_differ_cm=round(r1 - r2, 3)))

    cdpf = feat["cdp_bore"]
    cdp = radius(cal, cdpf["x_mid"], cdpf["y"])
    b = feat["bolt"]
    return dict(
        meta=dict(
            source="HPC detail design report, Figure 30 p.59 (PDF page 68), "
                   "Rotor Design Features",
            method="tools/read_hpc_fig30.py",
            dpi=DPI, threshold=THRESH, as_printed=AS_PRINTED,
            calibrated_on="the twenty published radii of data/hpc-flowpath.csv "
                          "-- ten rotor blade tips and ten rotor blade roots, "
                          "each the mean of the row's LE and TE value",
            nothing_dimensioned_on_the_page=True),
        calibration=dict(
            radial=dict(
                form="r_cm = a + b*y_px + c*x_px",
                **{k: cal[k] for k in ("a", "b", "c", "px_per_cm", "shear",
                                       "rot_deg", "rms_cm", "max_cm", "n")}),
            axial=dict(form="z_cm = a + b*(x_px - shear*y_px)", **ax),
            isotropy_pct=round(100 * (ax["px_per_cm"] / cal["px_per_cm"] - 1), 2),
            note=("one scale, not two: the 8.4 percent apparent anisotropy "
                  "between a shear-free radial fit and the axial fit is the "
                  "scan rotation, and removing it leaves the two scales 1.6 "
                  "percent apart")),
        blade_tips=tips,
        blade_roots=roots,
        disc_bores=bores,
        cdp_seal_disc=dict(
            y_px=cdpf["y"], r_bore_cm=round(cdp, 3),
            note="the rotor's aft-most disc, carrying the three-tooth CDP seal"),
        bolt_joint=dict(
            y_px=b["y"], r_cm=round(radius(cal, b["x_mid"], b["y"]), 3),
            z_cm=round(axial(feat, cal, ax, b["x_mid"], b["y"]), 2),
            note=("the ONE BOLT JOINT the figure labels, drawn under the "
                  "stage-5 blade at the stage 4/5 interface -- E9 finding 189 "
                  "recorded that no position is published for it")),
        raw_px={str(s): dict(x_mid=feat["stages"][s]["x_mid"],
                             y_tip=feat["stages"][s]["y_tip"],
                             y_root=feat["stages"][s]["y_root"],
                             y_bore=feat["stages"][s]["y_bore"],
                             tip_fit_rms_px=feat["stages"][s]["tip"]["rms_px"],
                             tip_x_lo=feat["stages"][s]["tip"]["x_lo"],
                             tip_x_hi=feat["stages"][s]["tip"]["x_hi"])
               for s in range(1, 11)})


if __name__ == "__main__":
    import yaml
    d = build()
    out = ROOT / "data" / "hpc-disc-profile.yaml"
    out.write_text(
        "# Generated by tools/read_hpc_fig30.py -- do not hand-edit.\n"
        "# HPC report Figure 30 p.59: the ten-stage rotor in section,\n"
        "# calibrated on the published annulus it is drawn against.\n"
        + yaml.safe_dump(d, sort_keys=False, default_flow_style=False))
    c = d["calibration"]["radial"]
    print(f"radial {c['px_per_cm']:.3f} px/cm, rotation {c['rot_deg']:+.3f} deg, "
          f"rms {c['rms_cm']:.4f} cm on n={c['n']}")
    print(f"axial  {d['calibration']['axial']['px_per_cm']:.3f} px/cm  "
          f"(isotropy {d['calibration']['isotropy_pct']:+.2f} %)")
    for b in d["disc_bores"]:
        print(f"  disc {b['stage']:>2}  bore {b['r_calibrated_cm']:6.3f} cm   "
              f"(depth route {b['r_depth_below_published_hub_cm']:6.3f}, "
              f"differ {b['two_routes_differ_cm']:+.3f})")
    print(f"  CDP seal disc bore {d['cdp_seal_disc']['r_bore_cm']:.3f} cm")
    print(f"  bolt joint r {d['bolt_joint']['r_cm']:.3f} cm, "
          f"z {d['bolt_joint']['z_cm']:.2f} cm")
