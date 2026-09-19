#!/usr/bin/env python3
"""Calibrate CR-167955 Figure 112 p.180 -- "HP Turbine Rotor Module
Assembly" -- against the published HPT flowpath, and say how good the
calibration is.

WHY THIS FIGURE AND NOT FIGURE 63.  Unit E2's peak-stress closure and
D6's gate item 2 both name **Figure 63 p.114, "Stage 1 Disk
Finite-Element Model"**.  Figure 63 carries no dimension, no flowpath, no
centreline and no published length: its top edge is the *dovetail seat*,
which sits below the flowpath hub by a platform-and-shank height nobody
prints.  There is nothing on that page to calibrate against.  D6's gate
says Fig 63 is drawn "over a published HPT annulus"; it is not.

The figures that ARE drawn over the published annulus are **Figure 50
p.87** (the whole turbine) and **Figure 112 p.180** (the rotor module).
Figure 112 is taken here because it is the larger drawing of the two --
Figure 50 has to fit the casing and the CDP air pipe into the same page
height -- and because its four flowpath features are clean closed lines
rather than lines crossed by leaders and labels.

WHAT IS PUBLISHED TO CALIBRATE ON.  e3-fps-published.yaml hpt.flowpath
(HPT report Fig 3, dimensioned) gives hub and tip radius at five
stations.  Four of them are features Figure 112 actually draws:

    stage-1 blade tip       36.58 / 36.60 cm   -> 36.59
    stage-1 blade platform  32.58 / 32.33 cm   -> 32.45
    stage-2 blade tip       38.05 / 38.10 cm   -> 38.07
    stage-2 blade platform  31.22 / 31.12 cm   -> 31.17

Four anchors at four radii spanning 6.9 cm, against Figure 30's twenty
spanning 15.6 cm.  That is the whole budget and it is stated here rather
than discovered later.

THE ROTATION IS MEASURED, NOT FITTED.  Unit E11 found Figure 30 needed
one rotation rather than two scales, and *fitted* the angle to the
anchors.  This page is a landscape sheet scanned sideways and is rotated
about five times as far, so the angle is taken from the CAPTION TEXT --
an external measurement the anchors never see -- on two independent
lines, the baseline and the top of the capitals.  The angle the four
anchors would choose for themselves is computed too, and reported beside
it, so the two can be compared rather than conflated.

Run this to regenerate data/hpt-rotor-calibration.yaml.
"""
from __future__ import annotations

import pathlib
import subprocess
import tempfile

import numpy as np
import yaml
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "sources" / "e3-hp-turbine-hardware-CR-167955.pdf"
PDF_PAGE = 189           # report p.180, offset +9 (DATA-INDEX)
DPI = 600
THRESH = 128
XREF = 2750              # px; the stage-1 blade, so the rotation pivots there

#: caption band, located once by row density and pinned so the read is fixed
CAPTION = dict(y0=3674, y1=3805)

#: per blade: the airfoil window carrying the tip line, and the window over
#: which the platform's TOP SURFACE -- the flowpath hub -- is drawn.  The
#: platform is wider than the aerofoil, so its top edge is visible clear of
#: the aerofoil on both sides; `plat_floor` rejects the columns where the
#: topmost dark pixel is the aerofoil itself rather than the platform.
BLADES = {
    1: dict(tip_win=(2620, 2860), tip_band=(700, 900),
            plat_win=(2490, 2815), plat_band=(1000, 1260), plat_floor=1060,
            stations=("stage1_vane_exit", "stage1_blade_exit")),
    2: dict(tip_win=(3560, 3830), tip_band=(600, 800),
            plat_win=(3545, 3800), plat_band=(1150, 1400), plat_floor=1230,
            stations=("stage2_vane_exit", "stage2_blade_exit")),
}


def published_anchors():
    """the anchor radii are NOT written here: they are the mean of the two
    published flowpath stations that bound each blade"""
    pub = yaml.safe_load((ROOT / "data" / "e3-fps-published.yaml").read_text())
    fp = {r["location"]: r for r in pub["hpt"]["flowpath"]["stations"]}
    out = {}
    for s, b in BLADES.items():
        a, c = (fp[k] for k in b["stations"])
        out[s] = dict(r_tip=(a["r_tip_cm"] + c["r_tip_cm"]) / 2,
                      r_hub=(a["r_hub_cm"] + c["r_hub_cm"]) / 2,
                      drop_cm=a["r_hub_cm"] - c["r_hub_cm"])
    return out

#: the interstage flange stud, 52 off, printed 0.953 cm.  The ONE published
#: length anywhere near the radius the disc lives at.  Attempted, and see
#: `bolt_scale` for why it cannot be read.
BOLT = dict(x=(2880, 3350), y=(2040, 2300), gap=(3112, 3142),
            published_cm=0.953, joint="interstage", count=52)

AS_PRINTED = (
    "Figure 112 carries no dimension and no centreline. Its NASA page "
    "stamp is ORIGINAL PAGE IS OF POOR QUALITY and the sheet is a "
    "landscape page scanned askew -- the caption text sits 2.07 degrees "
    "off horizontal, five times Figure 30's 0.416. The linework is "
    "hand-traced and 3-6 px thick at 600 dpi, 0.03-0.07 cm at the fitted "
    "scale. Both blade tips are drawn as closed lines, not broken off."
)


# --------------------------------------------------------------- the scan

def render(page: int = PDF_PAGE, dpi: int = DPI) -> np.ndarray:
    tmp = pathlib.Path(tempfile.mkdtemp()) / "f112"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page),
                    "-png", str(PDF), str(tmp)], check=True)
    return np.array(Image.open(f"{tmp}-{page}.png").convert("L")) < THRESH


# ------------------------------------------------- the rotation, externally

def _text_line(dark, y0, y1, which):
    """robust straight line through the bottom (baseline) or the top (cap
    height) of a line of type"""
    cols = np.flatnonzero(dark[y0:y1 + 1].sum(axis=0) > 0)
    xs, ys = [], []
    for x in range(int(cols.min()), int(cols.max()) + 1):
        c = np.flatnonzero(dark[y0:y1 + 1, x])
        if len(c):
            xs.append(x)
            ys.append(y0 + (c[-1] if which == "baseline" else c[0]))
    xs, ys = np.array(xs, float), np.array(ys, float)
    m, q = np.polyfit(xs, ys, 1)
    for _ in range(12):
        r = ys - (m * xs + q)
        keep = np.abs(r) < max(4.0, 0.7 * r.std())
        m, q = np.polyfit(xs[keep], ys[keep], 1)
    return dict(deg=float(np.degrees(np.arctan(m))), n_in=int(keep.sum()),
                n=len(xs), rms_px=float((ys[keep] - (m * xs[keep] + q)).std()))


def caption_rotation(dark) -> dict:
    base = _text_line(dark, CAPTION["y0"], CAPTION["y1"], "baseline")
    cap = _text_line(dark, CAPTION["y0"], CAPTION["y1"], "capheight")
    return dict(baseline=base, cap_height=cap,
                deg=float((base["deg"] + cap["deg"]) / 2),
                spread_deg=float(abs(base["deg"] - cap["deg"])))


# ----------------------------------------------------------- line finding

def _topmost(dark, x0, x1, y0, y1):
    """mean y of the topmost dark pixel, trimmed to the flat majority"""
    ys = []
    for x in range(x0, x1):
        c = np.flatnonzero(dark[y0:y1, x])
        ys.append(y0 + c[0] if len(c) else np.nan)
    ys = np.array(ys, float)
    keep = np.abs(ys - np.nanmedian(ys)) < 10
    return float(np.nanmean(ys[keep])), int(np.nansum(keep)), \
        float(np.nanstd(ys[keep]))


def _surface(dark, x0, x1, y0, y1, floor, x_at):
    """A drawn surface that SLOPES.  Take the topmost dark pixel per column,
    drop the columns where that is the aerofoil (above `floor`), fit a line,
    trim, and return its value at `x_at`.  The fitted slope is returned too,
    because the platform's slope is itself a published quantity -- the hub
    radius falls across the blade -- and so is a check."""
    xs, ys = [], []
    for x in range(x0, x1):
        c = np.flatnonzero(dark[y0:y1, x])
        if len(c) and y0 + c[0] >= floor:
            xs.append(x)
            ys.append(y0 + c[0])
    xs, ys = np.array(xs, float), np.array(ys, float)
    m, q = np.polyfit(xs, ys, 1)
    for _ in range(10):
        r = ys - (m * xs + q)
        keep = np.abs(r) < max(3.0, 1.5 * r.std())
        m, q = np.polyfit(xs[keep], ys[keep], 1)
    return dict(y_px=float(m * x_at + q), slope_px_px=float(m),
                n_in=int(keep.sum()), n=len(xs),
                rms_px=float((ys[keep] - (m * xs[keep] + q)).std()))


def features(dark) -> dict:
    pub = published_anchors()
    out = {}
    for s, b in BLADES.items():
        xm = float(sum(b["tip_win"]) / 2)
        ty, tn, ts = _topmost(dark, *b["tip_win"], *b["tip_band"])
        pl = _surface(dark, *b["plat_win"], *b["plat_band"], b["plat_floor"], xm)
        out[s] = dict(
            tip=dict(y_px=ty, x_px=xm, n=tn, scatter_px=ts,
                     r_published_cm=pub[s]["r_tip"]),
            platform=dict(x_px=xm, r_published_cm=pub[s]["r_hub"], **pl))
    return out


# ------------------------------------------------------------ calibration

def fit(feat, theta_deg):
    """r = a + b*(y - tan(theta)*(x - XREF)).  One scale, one offset, and a
    rotation that is an INPUT."""
    t = np.tan(np.radians(theta_deg))
    Y, R = [], []
    for s in sorted(feat):
        for k in ("tip", "platform"):
            f = feat[s][k]
            Y.append(f["y_px"] - t * (f["x_px"] - XREF))
            R.append(f["r_published_cm"])
    Y, R = np.array(Y), np.array(R)
    A = np.c_[np.ones_like(Y), Y]
    coef, *_ = np.linalg.lstsq(A, R, rcond=None)
    res = R - A @ coef
    return dict(a=float(coef[0]), b=float(coef[1]),
                px_per_cm=float(-1 / coef[1]), rot_deg=float(theta_deg),
                rms_cm=float(res.std()), max_cm=float(np.abs(res).max()),
                labels=[f"stage{s} {k}" for s in sorted(feat)
                        for k in ("tip", "platform")],
                residuals_cm=[round(float(v), 4) for v in res], n=len(R))


def free_rotation(feat):
    """what the four anchors WANT the angle to be -- 3 parameters on 4
    points, so it is recorded beside the caption's angle and not used"""
    g = np.linspace(-6, 6, 4801)
    best = min(g, key=lambda th: fit(feat, th)["rms_cm"])
    return fit(feat, float(best))


def radius(cal, x, y):
    t = np.tan(np.radians(cal["rot_deg"]))
    return cal["a"] + cal["b"] * (y - t * (x - XREF))


# ------------------------------------------- an independent scale, at depth

def bolt_scale(dark) -> dict:
    """The interstage stud is printed at 0.953 cm and sits at r ~ 20 cm,
    well below every flowpath anchor -- exactly where a scale extrapolated
    from the flowpath would need checking.  It cannot be used: the drawing
    shows the head and the nut and hides the shank inside the two flanges,
    so between them there is nothing on the page but the dashed centreline.
    The evidence is the column heights across the gap."""
    x0, x1 = BOLT["gap"]
    hs = []
    for x in range(x0, x1):
        c = np.flatnonzero(dark[BOLT["y"][0]:BOLT["y"][1], x])
        hs.append(int(c[-1] - c[0]) if len(c) else 0)
    med = float(np.median(hs))
    return dict(
        measurable=False,
        published_cm=BOLT["published_cm"], joint=BOLT["joint"],
        count=BOLT["count"],
        gap_px=[x0, x1],
        median_dark_run_in_gap_px=round(med, 1),
        max_dark_run_in_gap_px=int(max(hs)),
        expected_shank_px_if_drawn=round(BOLT["published_cm"] * 86.7, 1),
        why=("between the bolt head and the nut the drawing carries only the "
             "dashed centreline: the median dark run across the gap is %.1f px "
             "against the %.0f a 0.953 cm shank would need, and the few tall "
             "columns are the disc web crossing behind. The shank is hidden "
             "in the two flanges. So the one published length at the radius "
             "the disc occupies gives no independent check of the scale, and "
             "the extrapolation below the flowpath stays unverified."
             % (med, round(BOLT["published_cm"] * 86.7))))


# ------------------------------------------------------------------ write

def build() -> dict:
    dark = render()
    rot = caption_rotation(dark)
    feat = features(dark)
    cal_none = fit(feat, 0.0)
    cal = fit(feat, rot["deg"])
    cal_free = free_rotation(feat)

    # what each blade says about the SCALE on its own -- immune to any
    # relative radial misplacement of the two blades by the draughtsman
    pub = published_anchors()
    per_blade = {}
    for s, b in BLADES.items():
        dy = feat[s]["platform"]["y_px"] - feat[s]["tip"]["y_px"]
        span = pub[s]["r_tip"] - pub[s]["r_hub"]
        per_blade[s] = dict(span_px=round(float(dy), 2), span_cm=round(span, 3),
                            px_per_cm=round(float(dy / span), 3))
    ks = [v["px_per_cm"] for v in per_blade.values()]
    spread = 100 * (max(ks) - min(ks)) / float(np.mean(ks))

    # the platform slope is itself published: the hub falls across the blade
    slopes = {}
    for s, b in BLADES.items():
        m = feat[s]["platform"]["slope_px_px"] - np.tan(np.radians(rot["deg"]))
        dx = b["plat_win"][1] - b["plat_win"][0]
        slopes[f"stage{s}"] = dict(
            drop_over_window_cm=round(float(m * dx / cal["px_per_cm"]), 4),
            published_drop_cm=round(pub[s]["drop_cm"], 4),
            note="de-rotated slope of the drawn platform against the "
                 "published fall of the hub radius across the blade")

    return dict(
        meta=dict(
            source="CR-167955 Figure 112 p.180 (PDF page 189), "
                   "HP Turbine Rotor Module Assembly",
            method="tools/read_hpt_fig112.py", dpi=DPI, threshold=THRESH,
            as_printed=AS_PRINTED,
            calibrated_on="four published HPT flowpath radii -- both blade "
                          "tips and both blade platforms, e3-fps-published.yaml "
                          "hpt.flowpath (HPT report Fig 3, dimensioned)",
            why_not_figure_63=(
                "Figure 63 p.114 carries no flowpath, no dimension and no "
                "published length. Its top edge is the dovetail seat, which "
                "sits below the flowpath hub by an unpublished platform and "
                "shank height. D6's gate calls it 'drawn over a published "
                "HPT annulus'; it is not."),
            nothing_dimensioned_on_the_page=True),
        page_rotation=dict(
            measured_on="the figure caption, two independent lines",
            baseline=rot["baseline"], cap_height=rot["cap_height"],
            deg=rot["deg"], spread_deg=rot["spread_deg"],
            note="an EXTERNAL measurement -- the anchors never see it, "
                 "unlike Figure 30 where unit E11 fitted the angle to the "
                 "anchors themselves"),
        calibration=dict(
            form="r_cm = a + b*(y_px - tan(rot_deg)*(x_px - %d))" % XREF,
            **cal,
            drawing_scale_one_to=round(DPI / 2.54 / cal["px_per_cm"], 3)),
        calibration_without_rotation=cal_none,
        calibration_free_rotation=dict(
            **cal_free,
            agreement_with_caption_deg=round(
                float(cal_free["rot_deg"] - rot["deg"]), 4),
            note="3 parameters on 4 points, so it is recorded and not used. "
                 "What matters is that it lands within a tenth of a degree "
                 "of an angle measured off the caption text, which the "
                 "anchors never saw."),
        scale_per_blade=dict(
            **{f"stage{s}": v for s, v in per_blade.items()},
            spread_pct=round(float(spread), 2),
            note="each blade's own tip-to-platform span is immune to any "
                 "relative radial misplacement of the two blades, so this "
                 "is the estimate of the scale that does not depend on the "
                 "draughtsman having stacked the two stages correctly"),
        platform_slope_check=slopes,
        independent_scale_check=bolt_scale(dark),
        features={f"stage{s}": v for s, v in feat.items()},
    )


if __name__ == "__main__":
    d = build()
    out = ROOT / "data" / "hpt-rotor-calibration.yaml"
    out.write_text(
        "# Generated by tools/read_hpt_fig112.py -- do not hand-edit.\n"
        "# CR-167955 Figure 112 p.180: the HPT rotor module in section,\n"
        "# calibrated on the published flowpath it is drawn against.\n"
        + yaml.safe_dump(d, sort_keys=False, default_flow_style=False))
    r, c, n = d["page_rotation"], d["calibration"], d["calibration_without_rotation"]
    f, s = d["calibration_free_rotation"], d["scale_per_blade"]
    print(f"caption rotation {r['deg']:+.3f} deg  (baseline {r['baseline']['deg']:+.3f}, "
          f"cap {r['cap_height']['deg']:+.3f}, spread {r['spread_deg']:.3f})")
    print(f"free  rotation   {f['rot_deg']:+.3f} deg  "
          f"(agrees with the caption to {f['agreement_with_caption_deg']:+.3f} deg)")
    print(f"with rotation    {c['px_per_cm']:.3f} px/cm  rms {c['rms_cm']:.4f} cm  "
          f"max {c['max_cm']:.4f}  drawing 1:{c['drawing_scale_one_to']:.2f}")
    print(f"without rotation {n['px_per_cm']:.3f} px/cm  rms {n['rms_cm']:.4f} cm  "
          f"max {n['max_cm']:.4f}")
    for lab, e in zip(c["labels"], c["residuals_cm"]):
        print(f"    {lab:18s} {e:+.4f} cm")
    print(f"per-blade scale  stage1 {s['stage1']['px_per_cm']:.2f}, "
          f"stage2 {s['stage2']['px_per_cm']:.2f} px/cm, spread {s['spread_pct']:.2f} %")
    for k, v in d["platform_slope_check"].items():
        print(f"platform slope   {k}: drawn {v['drop_over_window_cm']:+.3f} cm "
              f"against a published {v['published_drop_cm']:.3f}")
    b = d["independent_scale_check"]
    print(f"bolt check       NOT MEASURABLE -- median {b['median_dark_run_in_gap_px']} px "
          f"of dark across the gap against {b['expected_shank_px_if_drawn']} needed")
