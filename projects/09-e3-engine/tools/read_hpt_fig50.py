#!/usr/bin/env python3
"""Calibrate CR-167955 Figure 50 p.87 -- "E3 HPT Major Design Features" --
against the published HPT flowpath, and then put it against Figure 112.

WHY THIS FIGURE.  Unit E12 ended by naming its own unattempted band C3:
*calibrate Figure 50 the same way and compare -- the only test that puts
two independent drawings of the same engine against each other.*  Figure 50
also draws **both disc bores in the same view as the flowpath**, so it is a
one-link read where Figure 63 is a two-link chain.

WHAT IT COSTS.  Figure 50 has to fit the casing, the CDP air pipe and ten
numbered call-outs into the page height that Figure 112 gives to the rotor
alone, so it is drawn smaller -- and the line weight does not shrink with
it.  One line width is about 14 px on both pages, 0.16 cm at Figure 112's
86.7 px/cm and about 0.23 cm here.  Two of the four anchors are crossed by
leader lines.  Both were said in step 0 before the fit.

THE ANCHORS are the same four as Figure 112's, deliberately, so that the
two calibrations are comparable feature by feature: both blade tips and
both blade platforms, from e3-fps-published.yaml hpt.flowpath (HPT report
Fig 3, dimensioned).

THE TIP IS FOUND FROM BELOW.  Figure 112 draws the rotor alone, so the
topmost dark pixel above an aerofoil is the blade tip.  Figure 50 draws the
casing too, so above each aerofoil there is a stack of three lines -- the
shroud support, the shroud body and the tip.  Taking the topmost would read
the shroud.  The rule used here is the one that means the same thing on
both pages: start inside the aerofoil, walk up to the first dark pixel, and
take the top of that run.

THE ROTATION is measured on the caption type, as unit E12 did, and is an
input the anchors never see.

THE CROSS-CHECK (`cross_check`) measures, on BOTH pages, five radii that
neither calibration was fitted on and that no source publishes: the two
bolt-joint centrelines and the three near-cylindrical surfaces at the
bottom of the rotor.  Agreement is a statement about the reading method,
not about the engine -- both drawings descend from one design -- and that
is exactly what needs testing before either is extrapolated below its
anchors.

Run this to regenerate data/hpt-fig50-calibration.yaml.
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
DPI = 600
THRESH = 128

PAGE50 = 96             # report p.87, offset +9 (DATA-INDEX)
PAGE112 = 189           # report p.180
XREF50 = 3385           # px; the stage-1 blade, so the rotation pivots there
XREF112 = 2750          # as read_hpt_fig112.py

#: the caption band, located by row density and pinned.  x starts at 2400 so
#: the rotated page number "87" at x 609-668 is not in the fit.
CAPTION50 = dict(y0=4391, y1=4528, x0=2487, x1=4495)

#: per blade on Figure 50: the columns that lie inside the aerofoil (for the
#: walk-up tip read) and the window over which the platform's top surface is
#: drawn clear of the leader lines.
BLADES50 = {
    1: dict(air_win=(3320, 3460), air_seed=2200,
            plat_win=(3285, 3465), plat_band=(2300, 2400), plat_floor=2300,
            stations=("stage1_vane_exit", "stage1_blade_exit")),
    2: dict(air_win=(4020, 4140), air_seed=2200,
            plat_win=(4085, 4165), plat_band=(2415, 2450), plat_floor=2415,
            stations=("stage2_vane_exit", "stage2_blade_exit")),
}

#: the five common features, per page.  `centreline` windows sit on a clean
#: stretch of the dash-dot line clear of the head and the nut; `joint_x` is
#: the flange plane and is recorded only so the two pages can be shown to be
#: talking about the same joint.
COMMON = {
    "interstage_bolt_centreline": dict(
        f50=dict(x=(3900, 3970), y=(3060, 3092), joint_x=3720),
        f112=dict(x=(3040, 3140), y=(2165, 2205), joint_x=3100),
        what="the dash-dot axis of the bolted joint between the stage-1 disc "
             "aft arm and the interstage seal disc"),
    "aft_bolt_centreline": dict(
        f50=dict(x=(4650, 4720), y=(3270, 3300), joint_x=4500),
        f112=dict(x=(4190, 4290), y=(2505, 2545), joint_x=4230),
        what="the dash-dot axis of the bolted joint aft of the stage-2 disc"),
}

#: the three stacked near-cylindrical surfaces at the bottom of the rotor.
#: Columns are kept only where exactly three runs appear in the band, each no
#: longer than a line width and the whole stack no deeper than 50 px -- which
#: rejects the columns where a disc web or a bolt crosses.
INNER = dict(
    f50=dict(x=(3150, 4300), band=(3820, 3895)),
    f112=dict(x=(2600, 3900), band=(3260, 3400)),
    max_run_px=16, max_span_px=50,
    what="the three stacked surfaces drawn at the bottom of the rotor -- the "
         "inner tube and the member under it; neither is published and "
         "neither calibration is fitted on them")

#: Figure 112 only: under each blade there is exactly ONE line between the
#: platform and the disc body, unbroken across the blade.  It is the bottom
#: of the dovetail, which is the live disc's rim -- the radius at which the
#: blade and post dead load is applied.  E2 needs it, D6 needs it, and no
#: source prints it.  Figure 112 is used rather than Figure 50 because it is
#: the larger drawing and E12 measured this region to 1.0 % of r there.
RIM112 = {
    1: dict(x=(2600, 2700), band=(1180, 1400)),
    2: dict(x=(3600, 3760), band=(1450, 1700)),
}
RIM_WHAT = ("the bottom of the dovetail, i.e. the live-disc rim: the only "
            "line drawn between the blade platform and the disc body, "
            "unbroken across the blade")

AS_PRINTED = (
    "Figure 50 carries no dimension, no centreline and no scale bar. Its "
    "NASA page stamp is ORIGINAL PAGE IS OF POOR QUALITY and the sheet is a "
    "landscape page scanned askew -- the caption type sits 0.54 degrees off "
    "horizontal, a quarter of Figure 112's 2.07, so the tilt is a fact about "
    "how each sheet was laid on the platen. The drawing is 0.69 times "
    "Figure 112's scale at the same 12-17 px line weight, so one line width "
    "is 0.23 cm here against 0.16 cm there. Ten numbered call-out leaders "
    "cross the rotor; two of them cross the blade platforms."
)


# --------------------------------------------------------------- the scan

def render(page: int, dpi: int = DPI) -> np.ndarray:
    tmp = pathlib.Path(tempfile.mkdtemp()) / "pg"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page),
                    "-png", str(PDF), str(tmp)], check=True)
    # pdftoppm zero-pads the page number to the width of the page count
    (png,) = sorted(tmp.parent.glob("pg-*.png"))
    return np.array(Image.open(png).convert("L")) < THRESH


# ------------------------------------------------- the rotation, externally

def _text_line(dark, y0, y1, x0, x1, which):
    xs, ys = [], []
    for x in range(x0, x1 + 1):
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
    c = CAPTION50
    base = _text_line(dark, c["y0"], c["y1"], c["x0"], c["x1"], "baseline")
    cap = _text_line(dark, c["y0"], c["y1"], c["x0"], c["x1"], "capheight")
    return dict(baseline=base, cap_height=cap,
                deg=float((base["deg"] + cap["deg"]) / 2),
                spread_deg=float(abs(base["deg"] - cap["deg"])),
                measured_on="the figure caption, two independent lines",
                note="an EXTERNAL measurement -- the anchors never see it")


# ----------------------------------------------------------- line finding

def _tip_from_below(dark, x0, x1, seed):
    """Walk UP from inside the aerofoil to the first dark pixel and take the
    top of that run. On Figure 50 the casing is drawn, so the topmost dark
    pixel above an aerofoil is the shroud support and not the blade."""
    ys = []
    for x in range(x0, x1):
        y = seed
        while y > 0 and not dark[y, x]:
            y -= 1
        if y == 0:
            continue
        while y > 0 and dark[y - 1, x]:
            y -= 1
        ys.append(y)
    ys = np.array(ys, float)
    keep = np.abs(ys - np.median(ys)) < 10
    return float(ys[keep].mean()), int(keep.sum()), float(ys[keep].std())


def _surface(dark, x0, x1, y0, y1, floor, x_at):
    """A drawn surface that slopes: topmost dark pixel per column at or below
    `floor`, line fit, trimmed. The slope is returned because the platform's
    fall across the blade is itself published."""
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


def published_anchors():
    pub = yaml.safe_load((ROOT / "data" / "e3-fps-published.yaml").read_text())
    fp = {r["location"]: r for r in pub["hpt"]["flowpath"]["stations"]}
    out = {}
    for s, b in BLADES50.items():
        a, c = (fp[k] for k in b["stations"])
        out[s] = dict(r_tip=(a["r_tip_cm"] + c["r_tip_cm"]) / 2,
                      r_hub=(a["r_hub_cm"] + c["r_hub_cm"]) / 2,
                      drop_cm=a["r_hub_cm"] - c["r_hub_cm"])
    return out


def features50(dark) -> dict:
    pub = published_anchors()
    out = {}
    for s, b in BLADES50.items():
        xm = float(sum(b["air_win"]) / 2)
        ty, tn, ts = _tip_from_below(dark, *b["air_win"], b["air_seed"])
        pl = _surface(dark, *b["plat_win"], *b["plat_band"], b["plat_floor"], xm)
        out[s] = dict(
            tip=dict(y_px=ty, x_px=xm, n=tn, scatter_px=ts,
                     r_published_cm=pub[s]["r_tip"]),
            platform=dict(x_px=xm, r_published_cm=pub[s]["r_hub"], **pl))
    return out


# ------------------------------------------------------------ calibration

def fit(feat, theta_deg, xref):
    t = np.tan(np.radians(theta_deg))
    Y, R = [], []
    for s in sorted(feat):
        for k in ("tip", "platform"):
            f = feat[s][k]
            Y.append(f["y_px"] - t * (f["x_px"] - xref))
            R.append(f["r_published_cm"])
    Y, R = np.array(Y), np.array(R)
    A = np.c_[np.ones_like(Y), Y]
    coef, *_ = np.linalg.lstsq(A, R, rcond=None)
    res = R - A @ coef
    return dict(a=float(coef[0]), b=float(coef[1]),
                px_per_cm=float(-1 / coef[1]), rot_deg=float(theta_deg),
                xref=xref,
                rms_cm=float(res.std()), max_cm=float(np.abs(res).max()),
                labels=[f"stage{s} {k}" for s in sorted(feat)
                        for k in ("tip", "platform")],
                residuals_cm=[round(float(v), 4) for v in res], n=len(R))


def free_rotation(feat, xref):
    g = np.linspace(-6, 6, 4801)
    best = min(g, key=lambda th: fit(feat, th, xref)["rms_cm"])
    return fit(feat, float(best), xref)


def radius(cal, x, y):
    t = np.tan(np.radians(cal["rot_deg"]))
    return float(cal["a"] + cal["b"] * (y - t * (x - cal["xref"])))


# ------------------------------------------------------- the cross-check

def _thin_line(dark, x0, x1, y0, y1, runmax=16):
    """centroid of the thin horizontal runs in a window -- the dash-dot axis,
    with the long runs of a flange or a head rejected by run length"""
    xs, ys = [], []
    for x in range(x0, x1):
        col = dark[y0:y1, x]
        i, n = 0, len(col)
        while i < n:
            if col[i]:
                j = i
                while j < n and col[j]:
                    j += 1
                if j - i <= runmax:
                    xs.append(x)
                    ys.append(y0 + (i + j - 1) / 2)
                i = j
            else:
                i += 1
    xs, ys = np.array(xs, float), np.array(ys, float)
    return dict(x_px=float(xs.mean()), y_px=float(ys.mean()),
                n=len(xs), scatter_px=float(ys.std()))


def _inner_surfaces(dark, x0, x1, y0, y1, max_run, max_span):
    """the three stacked surfaces at the bottom of the rotor. A column counts
    only if it shows exactly three runs, each within a line width and the
    stack within max_span -- which is what rejects a crossing web or bolt."""
    cols = {0: [], 1: [], 2: []}
    xs = []
    for x in range(x0, x1):
        col = dark[y0:y1, x]
        runs, i, n = [], 0, len(col)
        while i < n:
            if col[i]:
                j = i
                while j < n and col[j]:
                    j += 1
                runs.append((i, j - 1))
                i = j
            else:
                i += 1
        if len(runs) != 3:
            continue
        if any(b - a + 1 > max_run for a, b in runs):
            continue
        if runs[-1][1] - runs[0][0] > max_span:
            continue
        xs.append(x)
        for k in range(3):
            cols[k].append(y0 + runs[k][0])
    out = []
    xs = np.array(xs, float)
    for k in range(3):
        ys = np.array(cols[k], float)
        m, q = np.polyfit(xs, ys, 1)
        for _ in range(8):
            r = ys - (m * xs + q)
            keep = np.abs(r) < max(2.0, 2.0 * r.std())
            m, q = np.polyfit(xs[keep], ys[keep], 1)
        xm = float(xs.mean())
        out.append(dict(x_px=xm, y_px=float(m * xm + q), slope_px_px=float(m),
                        n=len(xs), n_in=int(keep.sum()),
                        rms_px=float((ys[keep] - (m * xs[keep] + q)).std())))
    return out, int(len(xs))


def cross_check(d50, d112, cal50, cal112) -> dict:
    out = {}
    for name, spec in COMMON.items():
        m50 = _thin_line(d50, *spec["f50"]["x"], *spec["f50"]["y"])
        m112 = _thin_line(d112, *spec["f112"]["x"], *spec["f112"]["y"])
        r50 = radius(cal50, m50["x_px"], m50["y_px"])
        r112 = radius(cal112, m112["x_px"], m112["y_px"])
        out[name] = dict(what=spec["what"],
                         fig50=dict(r_cm=round(r50, 4), **m50),
                         fig112=dict(r_cm=round(r112, 4), **m112),
                         difference_cm=round(r50 - r112, 4),
                         difference_pct=round(100 * (r50 - r112) / r112, 3))

    s50, n50 = _inner_surfaces(d50, *INNER["f50"]["x"], *INNER["f50"]["band"],
                               INNER["max_run_px"], INNER["max_span_px"])
    s112, n112 = _inner_surfaces(d112, *INNER["f112"]["x"],
                                 *INNER["f112"]["band"],
                                 INNER["max_run_px"], INNER["max_span_px"])
    for k in range(3):
        r50 = radius(cal50, s50[k]["x_px"], s50[k]["y_px"])
        r112 = radius(cal112, s112[k]["x_px"], s112[k]["y_px"])
        out[f"inner_surface_{k + 1}"] = dict(
            what=INNER["what"],
            fig50=dict(r_cm=round(r50, 4), columns_used=n50, **s50[k]),
            fig112=dict(r_cm=round(r112, 4), columns_used=n112, **s112[k]),
            difference_cm=round(r50 - r112, 4),
            difference_pct=round(100 * (r50 - r112) / r112, 3))

    d = [v["difference_cm"] for v in out.values()]
    p = [v["difference_pct"] for v in out.values()]
    out["summary"] = dict(
        n=len(d), worst_cm=round(max(abs(x) for x in d), 4),
        worst_pct=round(max(abs(x) for x in p), 3),
        mean_cm=round(float(np.mean(d)), 4),
        spread_about_mean_cm=round(float(np.std(d)), 4),
        note="a common OFFSET is the two calibrations disagreeing about "
             "where the origin is; the SPREAD about it is what the two "
             "readings disagree about feature by feature")
    return out


# ----------------------------------------------- the one thing E2 needs

def live_rim(d112, cal112) -> dict:
    pub = published_anchors()
    out = dict(what=RIM_WHAT,
               measured_on="CR-167955 Figure 112 p.180, the larger drawing")
    for s, w in RIM112.items():
        xm = float(sum(w["x"]) / 2)
        f = _surface(d112, *w["x"], *w["band"], w["band"][0], xm)
        r = radius(cal112, xm, f["y_px"])
        out[f"stage{s}"] = dict(
            r_cm=round(r, 4), x_px=xm,
            platform_r_cm=round(pub[s]["r_hub"], 4),
            shank_plus_dovetail_depth_cm=round(pub[s]["r_hub"] - r, 4), **f)
    return out


# ------------------------------------------------------------------ write

def build() -> dict:
    d50 = render(PAGE50)
    d112 = render(PAGE112)

    rot = caption_rotation(d50)
    feat = features50(d50)
    cal = fit(feat, rot["deg"], XREF50)
    cal_none = fit(feat, 0.0, XREF50)
    cal_free = free_rotation(feat, XREF50)

    cal112 = yaml.safe_load(
        (ROOT / "data" / "hpt-rotor-calibration.yaml").read_text())["calibration"]
    cal112 = dict(cal112, xref=XREF112)

    pub = published_anchors()
    per_blade = {}
    for s, b in BLADES50.items():
        dy = feat[s]["platform"]["y_px"] - feat[s]["tip"]["y_px"]
        span = pub[s]["r_tip"] - pub[s]["r_hub"]
        per_blade[f"stage{s}"] = dict(span_px=round(float(dy), 2),
                                      span_cm=round(span, 3),
                                      px_per_cm=round(float(dy / span), 3))
    ks = [v["px_per_cm"] for v in per_blade.values()]

    slopes = {}
    for s, b in BLADES50.items():
        m = feat[s]["platform"]["slope_px_px"] - np.tan(np.radians(rot["deg"]))
        dx = b["plat_win"][1] - b["plat_win"][0]
        window_cm = dx / cal["px_per_cm"]
        slopes[f"stage{s}"] = dict(
            window_px=dx, window_cm=round(float(window_cm), 3),
            blade_axial_cm=round(float(_blade_axial(s)), 3),
            drop_over_window_cm=round(float(m * dx / cal["px_per_cm"]), 4),
            published_drop_over_window_cm=round(
                float(pub[s]["drop_cm"] * window_cm / _blade_axial(s)), 4),
            published_drop_across_blade_cm=round(pub[s]["drop_cm"], 4),
            note="the published hub fall is quoted across the whole blade; "
                 "the drawn window is shorter, so the published value is "
                 "pro-rated to the window before they are compared")

    return dict(
        meta=dict(
            source="CR-167955 Figure 50 p.87 (PDF page 96), "
                   "E3 HPT Major Design Features",
            method="tools/read_hpt_fig50.py", dpi=DPI, threshold=THRESH,
            as_printed=AS_PRINTED,
            calibrated_on="the same four published HPT flowpath radii as "
                          "Figure 112 -- both blade tips and both blade "
                          "platforms, e3-fps-published.yaml hpt.flowpath",
            why_this_figure=(
                "unit E12's band C3, stated there and not attempted: the only "
                "test that puts two independent drawings of the same engine "
                "against each other. Figure 50 also draws both disc bores in "
                "the same view as the flowpath."),
            nothing_dimensioned_on_the_page=True),
        page_rotation=rot,
        calibration=dict(
            form="r_cm = a + b*(y_px - tan(rot_deg)*(x_px - %d))" % XREF50,
            **cal,
            drawing_scale_one_to=round(DPI / 2.54 / cal["px_per_cm"], 3)),
        calibration_without_rotation=cal_none,
        calibration_free_rotation=dict(
            **cal_free,
            agreement_with_caption_deg=round(
                float(cal_free["rot_deg"] - rot["deg"]), 4),
            note="3 parameters on 4 points, recorded and not used"),
        scale_relative_to_figure_112=dict(
            fig50_px_per_cm=round(cal["px_per_cm"], 3),
            fig112_px_per_cm=round(cal112["px_per_cm"], 3),
            ratio=round(cal["px_per_cm"] / cal112["px_per_cm"], 4),
            line_width_px=14,
            line_width_cm_fig50=round(14 / cal["px_per_cm"], 4),
            line_width_cm_fig112=round(14 / cal112["px_per_cm"], 4)),
        scale_per_blade=dict(**per_blade,
                             spread_pct=round(float(100 * (max(ks) - min(ks))
                                                    / np.mean(ks)), 2)),
        platform_slope_check=slopes,
        cross_check=cross_check(d50, d112, cal, cal112),
        live_disc_rim=live_rim(d112, cal112),
        features={f"stage{s}": v for s, v in feat.items()},
    )


def _blade_axial(stage):
    """axial length over which the published hub drop is quoted, from the
    same flowpath table's x column (read off Fig 3's scale, +-0.3 cm)"""
    pub = yaml.safe_load((ROOT / "data" / "e3-fps-published.yaml").read_text())
    fp = {r["location"]: r for r in pub["hpt"]["flowpath"]["stations"]}
    b = BLADES50[stage]["stations"]
    return fp[b[1]]["x_cm"] - fp[b[0]]["x_cm"]


if __name__ == "__main__":
    d = build()
    out = ROOT / "data" / "hpt-fig50-calibration.yaml"
    out.write_text(
        "# Generated by tools/read_hpt_fig50.py -- do not hand-edit.\n"
        "# CR-167955 Figure 50 p.87: the whole HP turbine in section,\n"
        "# calibrated on the published flowpath it is drawn against, and\n"
        "# cross-checked feature by feature against Figure 112 p.180.\n"
        + yaml.safe_dump(d, sort_keys=False, default_flow_style=False))

    r, c, n = d["page_rotation"], d["calibration"], d["calibration_without_rotation"]
    f, s = d["calibration_free_rotation"], d["scale_per_blade"]
    print(f"caption rotation {r['deg']:+.3f} deg  (baseline {r['baseline']['deg']:+.3f}, "
          f"cap {r['cap_height']['deg']:+.3f}, spread {r['spread_deg']:.3f})")
    print(f"free  rotation   {f['rot_deg']:+.3f} deg  "
          f"(caption {f['agreement_with_caption_deg']:+.3f} away)")
    print(f"with rotation    {c['px_per_cm']:.3f} px/cm  rms {c['rms_cm']:.4f} cm  "
          f"max {c['max_cm']:.4f}  drawing 1:{c['drawing_scale_one_to']:.2f}")
    print(f"without rotation {n['px_per_cm']:.3f} px/cm  rms {n['rms_cm']:.4f} cm")
    for lab, e in zip(c["labels"], c["residuals_cm"]):
        print(f"    {lab:18s} {e:+.4f} cm")
    q = d["scale_relative_to_figure_112"]
    print(f"scale ratio      {q['ratio']:.4f} of Figure 112; one line width is "
          f"{q['line_width_cm_fig50']:.3f} cm here, {q['line_width_cm_fig112']:.3f} there")
    print(f"per-blade scale  spread {s['spread_pct']:.2f} %")
    for k, v in d["platform_slope_check"].items():
        print(f"platform slope   {k}: drawn {v['drop_over_window_cm']:+.3f} cm "
              f"over its window against a published "
              f"{v['published_drop_over_window_cm']:+.3f}")
    print("\nCROSS-CHECK -- five radii neither calibration was fitted on")
    for k, v in d["cross_check"].items():
        if k == "summary":
            continue
        print(f"  {k:28s} fig50 {v['fig50']['r_cm']:7.3f}  fig112 "
              f"{v['fig112']['r_cm']:7.3f}  {v['difference_cm']:+.3f} cm "
              f"({v['difference_pct']:+.2f} %)")
    sm = d["cross_check"]["summary"]
    print(f"  worst {sm['worst_cm']:.3f} cm / {sm['worst_pct']:.2f} %; "
          f"mean offset {sm['mean_cm']:+.3f} cm, spread about it "
          f"{sm['spread_about_mean_cm']:.3f} cm")
    lr = d["live_disc_rim"]
    for k in ("stage1", "stage2"):
        v = lr[k]
        print(f"\nlive-disc rim (Fig 112) {k}: r = {v['r_cm']:.3f} cm, "
              f"{v['shank_plus_dovetail_depth_cm']:.3f} cm below the platform, "
              f"{v['n_in']} of {v['n']} columns, {v['rms_px']:.2f} px rms")
