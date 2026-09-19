"""Stage E unit E11: HPC Figure 30 calibrated, and the bore radius unit D6
is gated on.

Unit D6 closes the gas-path annulus term on the HP rotor and then stops,
because the term that decides the answer is the one the annulus control
volume excludes: high pressure behind the compressor drum and low pressure
in front of it, acting on the disc faces from the bore out to the hub line.
Finding 193 priced that gate -- `+342 to +672 kN forward over bores of 8 to
20 cm, 3.2 to 6.4 times the annulus term` -- and named the missing number
as the HPC disc **bore radius**.

`tools/read_hpc_fig30.py` reads it off HPC report Figure 30 p.59, which
draws the whole ten-stage rotor over an annulus this project has published
since Stage A. This module does three things with it:

* **validates the calibration on data it was not fitted to** -- five stages
  held out of a fit made on the other five;
* **carries the bore into D6 as a band, not a point**, by bootstrapping the
  calibration;
* **re-forms the disc-face term disc by disc**, which the measurement now
  allows and the single telescoped form did not.

It does not close D6, and says why: see `still_missing()`.

Sign convention, as in `thermal/thrust_balance.py`: **positive is forward**.

STEP0.md, unit E11."""
from __future__ import annotations

import math
import pathlib

import numpy as np
import yaml

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
GAMMA = 1.4
#: Table XXI column order, from the file's own `columns.rotor_station`
COL = dict(radius_cm=2, pt_ratio=4, m_abs=6)


def profile() -> dict:
    return yaml.safe_load((DATA / "hpc-disc-profile.yaml").read_text())


# ------------------------------------------------- the calibration itself

def _design(p, stages):
    """the (x, y) pixels and the published radii of one set of stages"""
    tips = {t["stage"]: t for t in p["blade_tips"]}
    roots = {t["stage"]: t for t in p["blade_roots"]}
    X, Y, R = [], [], []
    for s in stages:
        x = p["raw_px"][str(s)]["x_mid"]
        X += [x, x]
        Y += [tips[s]["y_px"], roots[s]["y_px"]]
        R += [tips[s]["published_cm"], roots[s]["published_cm"]]
    return np.array(X), np.array(Y), np.array(R)


def _fit(X, Y, R):
    A = np.c_[np.ones_like(X), Y, X]
    coef, *_ = np.linalg.lstsq(A, R, rcond=None)
    return dict(a=coef[0], b=coef[1], c=coef[2],
                px_per_cm=-1 / coef[1], shear=coef[2] / coef[1],
                rot_deg=math.degrees(math.atan(coef[2] / coef[1])))


def _r(cal, x, y):
    return cal["a"] + cal["b"] * y + cal["c"] * x


def holdout(p=None):
    """Band 1 and band 2. Fit on the odd stages, predict the even ones, and
    the other way round -- ten points fitted, ten predicted, each way.

    A three-parameter fit to twenty points that has never seen half of them
    is the only thing that separates a calibration from a curve fit."""
    p = p or profile()
    out = {}
    for name, fit_s, pred_s in (("odd->even", range(1, 11, 2), range(2, 11, 2)),
                                ("even->odd", range(2, 11, 2), range(1, 11, 2))):
        cal = _fit(*_design(p, fit_s))
        X, Y, R = _design(p, pred_s)
        res = _r(cal, X, Y) - R
        out[name] = dict(rot_deg=cal["rot_deg"], px_per_cm=cal["px_per_cm"],
                         rms_cm=float(res.std()), max_cm=float(np.abs(res).max()),
                         n=len(R))
    out["rotation_spread_deg"] = abs(out["odd->even"]["rot_deg"]
                                     - out["even->odd"]["rot_deg"])
    out["worst_rms_cm"] = max(out[k]["rms_cm"] for k in ("odd->even", "even->odd"))
    out["worst_max_cm"] = max(out[k]["max_cm"] for k in ("odd->even", "even->odd"))
    return out


def _shear_free(p, stages, which=("tip", "root")):
    tips = {t["stage"]: t for t in p["blade_tips"]}
    roots = {t["stage"]: t for t in p["blade_roots"]}
    Y, R = [], []
    for s in stages:
        if "tip" in which:
            Y.append(tips[s]["y_px"]); R.append(tips[s]["published_cm"])
        if "root" in which:
            Y.append(roots[s]["y_px"]); R.append(roots[s]["published_cm"])
    Y, R = np.array(Y), np.array(R)
    m, c = np.polyfit(Y, R, 1)
    res = R - (m * Y + c)
    return dict(px_per_cm=float(-1 / m), rms_cm=float(res.std()),
                max_cm=float(np.abs(res).max()), n=len(R))


def isotropy(p=None):
    """Band 3. One scale or two?

    A calibration built on the ten blade **tips** alone -- the only family a
    reader who had not thought about the roots would use -- gives 53.0 px/cm
    and fits its own ten points to 0.046 cm. Against the axial scale that is
    a 7.7 % anisotropy, which is what J8 met on CR-159584 Fig 1 and answered
    with two scales. It is the scan rotation. Forcing a shear-free fit onto
    all twenty points instead splits the difference at 49.5 px/cm and fits
    three times worse; allowing the rotation gives 49.6 px/cm at the tips'
    own rms, and the axial scale then agrees to 1.4 %."""
    p = p or profile()
    tip_only = _shear_free(p, range(1, 11), which=("tip",))
    root_only = _shear_free(p, range(1, 11), which=("root",))
    all20 = _shear_free(p, range(1, 11))
    rad = p["calibration"]["radial"]
    ax = p["calibration"]["axial"]
    return dict(
        tip_only_shear_free=tip_only, root_only_shear_free=root_only,
        all20_shear_free=all20,
        radial_px_per_cm=rad["px_per_cm"], radial_rms_cm=rad["rms_cm"],
        axial_px_per_cm=ax["px_per_cm"],
        apparent_anisotropy_pct=100 * (ax["px_per_cm"] / tip_only["px_per_cm"] - 1),
        isotropy_pct=100 * (ax["px_per_cm"] / rad["px_per_cm"] - 1),
        shear_free_costs_rms_x=all20["rms_cm"] / rad["rms_cm"],
        rot_deg=rad["rot_deg"])


def bootstrap_bore(stage=10, n=2000, seed=0, p=None):
    """Band 4. Resample the ten calibration stages with replacement, refit,
    and re-read one bore. This carries the calibration's own uncertainty; the
    line thickness is added on top by `bore_band`."""
    p = p or profile()
    rng = np.random.default_rng(seed)
    bores = {b["stage"]: b for b in p["disc_bores"]}
    x = p["raw_px"][str(stage)]["x_mid"]
    y = bores[stage]["y_px"]
    vals = []
    for _ in range(n):
        s = rng.integers(1, 11, 10)
        cal = _fit(*_design(p, s))
        vals.append(_r(cal, x, y))
    v = np.array(vals)
    lo, hi = np.percentile(v, [2.5, 97.5])
    return dict(stage=stage, mean_cm=float(v.mean()), sd_cm=float(v.std()),
                ci95_cm=(float(lo), float(hi)), width_cm=float(hi - lo))


def bootstrap_bore_depth_route(stage=10, n=2000, seed=0, p=None):
    """The same bootstrap on the *second* route -- the bore as a depth below
    the published hub radius of its own stage.

    This route uses the calibration's SCALE and not its intercept, so it was
    expected to be materially tighter than route one -- which asks the fitted
    line for a radius 10 cm below its lowest anchor. **It is not**: 0.38 cm
    against 0.40 on the 95 % width, because the scale itself carries 0.6 %
    and is then applied over an 18 cm depth. The hypothesis was stated during
    the run and is recorded as wrong (finding 258). What the second route is
    good for is *agreeing* with the first to 0.08 cm worst on all nine discs,
    an order better than either's own interval -- which is what bounds the
    systematic that neither resampling can see."""
    p = p or profile()
    rng = np.random.default_rng(seed)
    b = {x["stage"]: x for x in p["disc_bores"]}[stage]
    root = {t["stage"]: t for t in p["blade_roots"]}[stage]
    depth_px = b["y_px"] - root["y_px"]
    vals = []
    for _ in range(n):
        cal = _fit(*_design(p, rng.integers(1, 11, 10)))
        vals.append(root["published_cm"] - depth_px / cal["px_per_cm"])
    v = np.array(vals)
    lo, hi = np.percentile(v, [2.5, 97.5])
    return dict(stage=stage, mean_cm=float(v.mean()), sd_cm=float(v.std()),
                ci95_cm=(float(lo), float(hi)), width_cm=float(hi - lo))


def extrapolation_lever(p=None):
    """How far below the calibration the bore sits. 64 % beyond the fitted
    span is why every estimator exceeds step 0's band -- though, per finding
    258, not why they differ from each other by a factor of 2.4."""
    p = p or profile()
    rs = [t["published_cm"] for t in p["blade_tips"] + p["blade_roots"]]
    bore = min(b["r_calibrated_cm"] for b in p["disc_bores"])
    return dict(calibrated_from_cm=min(rs), calibrated_to_cm=max(rs),
                lowest_bore_cm=bore, below_lowest_anchor_cm=min(rs) - bore,
                as_fraction_of_span=(min(rs) - bore) / (max(rs) - min(rs)))


def analytic_sd(stage=10, p=None):
    """The textbook prediction standard error of the fitted calibration at
    the bore point: sigma^2 * v' (A'A)^-1 v. Cheap, and it is the estimator
    a bootstrap of ten stages is trying to approximate."""
    p = p or profile()
    X, Y, R = _design(p, range(1, 11))
    A = np.c_[np.ones_like(X), Y, X]
    coef, *_ = np.linalg.lstsq(A, R, rcond=None)
    res = R - A @ coef
    s2 = float((res ** 2).sum() / (len(R) - 3))
    C = s2 * np.linalg.inv(A.T @ A)
    b = {x["stage"]: x for x in p["disc_bores"]}[stage]
    v = np.array([1.0, b["y_px"], p["raw_px"][str(stage)]["x_mid"]])
    return dict(sd_cm=float(np.sqrt(v @ C @ v)), sigma_cm=float(np.sqrt(s2)),
                width95_cm=float(3.92 * np.sqrt(v @ C @ v)))


def jackknife_bore(stage=10, p=None):
    """Leave one stage out, ten times. Every refit is well conditioned,
    which a ten-stage bootstrap draw is not always."""
    p = p or profile()
    b = {x["stage"]: x for x in p["disc_bores"]}[stage]
    x = p["raw_px"][str(stage)]["x_mid"]
    v = [ _r(_fit(*_design(p, [k for k in range(1, 11) if k != s])), x, b["y_px"])
          for s in range(1, 11) ]
    v = np.array(v)
    sd = float(np.sqrt(9 / 10 * ((v - v.mean()) ** 2).sum()))
    return dict(sd_cm=sd, width95_cm=3.92 * sd, mean_cm=float(v.mean()))


def bore_band(stage=10, p=None):
    """The bore radius with everything on it, and the **widest** of the three
    uncertainty estimators carried rather than the friendliest.

    A disc-face term that swung 342-672 kN on the bore (finding 193) cannot
    honestly take a point value, so this is the band D6 is given. The three
    estimators disagree by a factor of two -- analytic 0.27 cm, bootstrap
    0.40, jackknife 0.61 on the 95 % width -- because the bore sits 10 cm
    below the lowest radius the calibration was fitted on."""
    p = p or profile()
    b = {x["stage"]: x for x in p["disc_bores"]}[stage]
    est = dict(bootstrap=bootstrap_bore(stage, p=p)["width_cm"],
               bootstrap_depth_route=bootstrap_bore_depth_route(stage, p=p)["width_cm"],
               analytic=analytic_sd(stage, p)["width95_cm"],
               jackknife=jackknife_bore(stage, p)["width95_cm"])
    widest = max(est.values())
    routes = abs(b["two_routes_differ_cm"])
    line = 3.0 / p["calibration"]["radial"]["px_per_cm"]   # half a 6 px line
    half = math.sqrt((widest / 2) ** 2 + routes ** 2 + line ** 2)
    r = b["r_calibrated_cm"]
    return dict(stage=stage, r_cm=r, half_width_cm=half,
                lo_cm=r - half, hi_cm=r + half,
                estimators_width95_cm=est, widest_width95_cm=widest,
                from_two_routes_cm=routes, from_line_thickness_cm=line)


# ------------------------------------------------ what it means for D6

def _cycle():
    from e3cycle import cycle as cyc
    return max(cyc.run_all(), key=lambda r: r.stations["p3"])


def _hub_static_after_each_rotor():
    """Inter-disc cavity pressure, taken as the rotor-exit hub static of the
    stage forward of the cavity. Table XXI prints the total-pressure ratio
    and the Mach number on twelve streamlines; streamline 12 is the hub."""
    rating = _cycle()
    p25 = rating.stations["p25"]
    xxi = yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())
    out = {}
    for row in xxi["rows"]:
        if row.get("row") != "rotor":
            continue
        hub = row["exit"][-1]
        pt = p25 * hub[COL["pt_ratio"]]
        m = hub[COL["m_abs"]]
        out[row["stage"]] = pt / (1 + (GAMMA - 1) / 2 * m ** 2) ** (GAMMA / (GAMMA - 1))
    return out


def disc_face_per_disc(p=None, r_bore_shift_cm=0.0):
    """Band 5. The forward force on the drum, summed over the discs that
    have a drawn bore, instead of telescoped into one area.

    The cavity forward of disc i is at stage i-1's pressure and the one aft
    of it at stage i's, so each disc carries `(p_i - p_{i-1}) * pi (r_hub_i^2
    - r_bore_i^2)` forward. Telescoping that to `(p3 - p25) * A` is exact
    only if every disc has the same face area -- and Figure 30 shows two
    families, 10.7 cm bores forward of the bolt joint and 9.1 cm aft."""
    p = p or profile()
    bores = {b["stage"]: b["r_calibrated_cm"] + r_bore_shift_cm
             for b in p["disc_bores"]}
    hubs = {t["stage"]: t["published_cm"] for t in p["blade_roots"]}
    ps = _hub_static_after_each_rotor()
    p25 = _cycle().stations["p25"]
    rows = []
    for s in sorted(bores):
        area = math.pi * ((hubs[s] / 100) ** 2 - (bores[s] / 100) ** 2)
        dp = ps[s] - (ps[s - 1] if s - 1 in ps else p25)
        rows.append(dict(stage=s, r_bore_cm=bores[s], r_hub_cm=hubs[s],
                         area_m2=area, dp_Pa=dp, forward_N=dp * area))
    return rows


def telescoped(p=None, r_bore_shift_cm=0.0):
    """The single-area form unit D6 already uses, now with a measured bore."""
    p = p or profile()
    b = {x["stage"]: x for x in p["disc_bores"]}[10]["r_calibrated_cm"] + r_bore_shift_cm
    hub = {t["stage"]: t["published_cm"] for t in p["blade_roots"]}[10]
    r = _cycle().stations
    area = math.pi * ((hub / 100) ** 2 - (b / 100) ** 2)
    return dict(r_bore_cm=b, r_hub_cm=hub, area_m2=area,
                dp_Pa=r["p3"] - r["p25"],
                forward_N=(r["p3"] - r["p25"]) * area)


def d6_verdict(p=None):
    """Band 6, and the number D6 has been waiting for.

    The bore is carried as a band: the per-disc sum and the telescoped form
    are each evaluated at the low, central and high bore."""
    p = p or profile()
    band = bore_band(10, p)
    from thermal.thrust_balance import net_hp_gas_load
    ann = net_hp_gas_load()
    out = {}
    for tag, shift in (("lo", -band["half_width_cm"]), ("mid", 0.0),
                       ("hi", band["half_width_cm"])):
        # a LARGER bore is a SMALLER face, so lo/hi on r is hi/lo on force
        per = sum(r["forward_N"] for r in disc_face_per_disc(p, shift))
        tel = telescoped(p, shift)["forward_N"]
        out[tag] = dict(r_bore_cm=band["r_cm"] + shift,
                        per_disc_N=per, telescoped_N=tel,
                        per_over_telescoped=per / tel,
                        times_annulus=per / abs(ann["hpc_forward_N"]))
    out["bore_band_cm"] = (band["lo_cm"], band["hi_cm"])
    out["annulus_hpc_N"] = ann["hpc_forward_N"]
    out["disc_face_forward_N"] = (min(out[t]["per_disc_N"] for t in ("lo", "mid", "hi")),
                                  max(out[t]["per_disc_N"] for t in ("lo", "mid", "hi")))
    out["swing_from_bore_pct"] = 100 * (out["disc_face_forward_N"][1]
                                        / out["disc_face_forward_N"][0] - 1)
    return out


def where_the_thrust_is_made(p=None):
    """Which discs actually carry the drum's forward push."""
    rows = disc_face_per_disc(p)
    tot = sum(r["forward_N"] for r in rows)
    back3 = sum(r["forward_N"] for r in rows if r["stage"] >= 8)
    return dict(total_N=tot, rear_three_N=back3, rear_three_pct=100 * back3 / tot,
                forward_family_pct=100 * sum(r["forward_N"] for r in rows
                                             if r["stage"] <= 4) / tot)


def still_missing():
    """Why D6 does not close even now, with the bore measured.

    Everything here is a statement about what the reports on disk do not
    print, not about what has not been attempted."""
    return dict(
        hpc_drum_disc_face="CLOSED by this unit -- Figure 30 gives every bore",
        hpc_stage1_forward_face=(
            "stage 1 has no bore foot: its disc runs forward and inward into "
            "the integral stub shaft, so the drum's FORWARD face is a cone of "
            "un-dimensioned inner radius. Figure 30 draws it"),
        hpt_rotor_disc_faces=(
            "the HPT rotor's two discs carry the same kind of term with the "
            "opposite sign, across roughly p3 down to the HPT exit. CR-167955 "
            "Fig 63 p.114 draws the stage-1 disc profile and dimensions "
            "nothing; it is the same kind of digitisation as this one and is "
            "not done"),
        balance_piston=(
            "finding 191: HPT report Figs 95-96 give the piston-balance seal "
            "as HARDWARE and never as a load -- no thrust, no piston area, no "
            "piston radius, no cavity pressure"),
        bearing_capacity=(
            "unit E4's gate: CR-168219 sec 5.7 names all five bearings and "
            "prints no load and no capacity"),
        consequence=(
            "the HP rotor's net axial load cannot be formed, so D6 stays "
            "gated -- but the gate is no longer the bore radius"))


def summary():
    p = profile()
    cal = p["calibration"]["radial"]
    h, iso, v = holdout(p), isotropy(p), d6_verdict(p)
    band = bore_band(10, p)
    L = ["Stage E unit E11 -- HPC Figure 30, and the bore D6 is gated on", ""]
    L.append(f"   calibration on 20 published radii: {cal['px_per_cm']:.3f} px/cm, "
             f"scan rotation {cal['rot_deg']:+.3f} deg, rms {cal['rms_cm']:.4f} cm")
    L.append(f"   held out five stages of ten: rms {h['worst_rms_cm']:.4f} cm, "
             f"max {h['worst_max_cm']:.4f} cm; rotation stable to "
             f"{h['rotation_spread_deg']:.3f} deg")
    L.append(f"   tip-only shear-free {iso['tip_only_shear_free']['px_per_cm']:.2f} "
             f"(its own rms {iso['tip_only_shear_free']['rms_cm']:.3f} cm) vs axial "
             f"{iso['axial_px_per_cm']:.2f} px/cm = "
             f"{iso['apparent_anisotropy_pct']:+.1f} % -- with the rotation "
             f"removed, {iso['isotropy_pct']:+.2f} %; a shear-free fit on all "
             f"twenty costs {iso['shear_free_costs_rms_x']:.1f}x in rms")
    L += ["", "   the bores, as drawn:"]
    for b in p["disc_bores"]:
        L.append(f"      disc {b['stage']:>2}   {b['r_calibrated_cm']:6.3f} cm"
                 f"   (second route {b['r_depth_below_published_hub_cm']:6.3f}, "
                 f"differ {b['two_routes_differ_cm']:+.3f})")
    L.append(f"      CDP seal disc {p['cdp_seal_disc']['r_bore_cm']:6.3f} cm")
    L.append(f"   stage 10 bore {band['r_cm']:.3f} +/- {band['half_width_cm']:.3f} cm "
             f"(95 % widths: " + ", ".join(
                 f"{k} {v:.3f}" for k, v in band['estimators_width95_cm'].items())
             + f"; routes {band['from_two_routes_cm']:.3f}, "
               f"line {band['from_line_thickness_cm']:.3f})")
    L += ["", "   what it does to D6:"]
    L.append(f"      annulus term            {v['annulus_hpc_N']/1e3:9.1f} kN")
    for t in ("lo", "mid", "hi"):
        d = v[t]
        L.append(f"      bore {d['r_bore_cm']:5.3f} cm  per-disc "
                 f"{d['per_disc_N']/1e3:8.1f} kN   telescoped "
                 f"{d['telescoped_N']/1e3:8.1f}   ratio {d['per_over_telescoped']:.3f}"
                 f"   x annulus {d['times_annulus']:.2f}")
    L.append(f"      the bore band is worth {v['swing_from_bore_pct']:.1f} % of the term")
    w = where_the_thrust_is_made(p)
    L.append(f"      discs 8-10 carry {w['rear_three_pct']:.0f} % of it; "
             f"discs 2-4 carry {w['forward_family_pct']:.0f} %")
    L += ["", "   STILL GATED, and no longer on the bore:"]
    for k, val in still_missing().items():
        if k in ("consequence", "hpc_drum_disc_face"):
            continue
        L.append(f"      {k}: {val[:72]}...")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
