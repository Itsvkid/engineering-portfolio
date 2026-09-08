"""Stage J unit J2: the Campbell match.

Second in the plan's Stage J order. What this plots is a **failure**:
Stage E3's closure asked for the first three modes of every HPC rotor
stage within 5 % of the published Campbell diagrams (HPC report Figs
33-42) and got 1 of 24. J2 does not move that closure. Its job is to make
the miss legible, and to show the one thing the closure's single number
hides -- that on nearly half the comparisons **the 5 % band is finer than
the transcription can read**, so no model could have been judged against
it either way (finding 160).

Two figures:

  campbell-stages.png   ten Campbell diagrams, one per rotor stage:
                        published mode lines drawn flat as they were read,
                        predicted lines carrying the Southwell stiffening
                        the model does have, per-rev rays, and the HP
                        operating range shaded.
  campbell-match.png    the match itself: 24 comparisons on a linear axis
                        with the 5 % closure band drawn to scale and each
                        point's reading uncertainty as an error bar.

STEP0.md unit J2."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from e3cycle.cycle import DATA

FIGDIR = Path(__file__).resolve().parent / "figures"

#: Half a minor division on each of the four frequency axes the ten
#: diagrams use, in Hz. Straight from `hpc-rotor-campbell.yaml`'s
#: `meta.reading_uncertainty` -- not a guess made here.
READING_UNCERTAINTY_HZ = {6: 50.0, 12: 100.0, 22: 250.0, 26: 250.0}

#: HP spool, from `e3-fps-published.yaml`
RPM_100PCT = 12303.0
RPM_MAX_CLIMB = 12645.0
RPM_DETERIORATED = 13948.0
RPM_MAX_PLOT = 14500.0

CLOSURE_BAND_PCT = 5.0


def published():
    return yaml.safe_load((DATA / "hpc-rotor-campbell.yaml").read_text())


def reading_uncertainty_hz(stage_block):
    """The uncertainty of READING the diagram, per stage. It is a property
    of the axis the mode line was drawn against, not of the model."""
    return READING_UNCERTAINTY_HZ[stage_block["axis_max_kHz"]]


def comparisons():
    """The 24 comparisons E3's closure is made of, each carrying the
    uncertainty of the number it is compared against."""
    from mechanical.blade_frequency import hpc_campbell_comparison
    by = {s["stage"]: s for s in published()["stages"]}
    out = []
    for r in hpc_campbell_comparison():
        blk = by[r["stage"]]
        u = reading_uncertainty_hz(blk)
        for m in r["modes"]:
            if m["published"] is None or m["err_pct"] is None:
                continue
            unc_pct = 100.0 * u / m["published"]
            out.append(dict(
                stage=r["stage"], figure=blk["figure"], mode=m["mode"],
                material=r["material"], axis_max_kHz=blk["axis_max_kHz"],
                predicted=m["predicted"], publishedHz=m["published"],
                err_pct=m["err_pct"], unc_hz=u, unc_pct=unc_pct,
                # can a 5 % band even be resolved against this reading?
                resolvable=unc_pct <= CLOSURE_BAND_PCT,
                # is the model inside the reading uncertainty of the figure?
                within_reading=abs(m["err_pct"]) <= unc_pct,
            ))
    return out


def resolvability():
    """finding 160. The closure band is 5 %. On eleven of the twenty-four
    comparisons the transcription cannot resolve 5 %, and on every single
    first-flex mode it cannot -- reading a 350 Hz line off a 0-6 kHz axis
    to half a minor division is +-14 %."""
    c = comparisons()
    res = [r for r in c if r["resolvable"]]
    unres = [r for r in c if not r["resolvable"]]
    return dict(
        total=len(c), resolvable=len(res), unresolvable=len(unres),
        first_flex_resolvable=sum(1 for r in res if r["mode"] == "1F"),
        first_flex_total=sum(1 for r in c if r["mode"] == "1F"),
        passes_overall=sum(1 for r in c if abs(r["err_pct"]) <= CLOSURE_BAND_PCT),
        passes_among_resolvable=sum(1 for r in res
                                    if abs(r["err_pct"]) <= CLOSURE_BAND_PCT),
        within_reading=sum(1 for r in c if r["within_reading"]),
        worst_unc_pct=max(r["unc_pct"] for r in c),
    )


def mode_number_trend():
    """Does the over-prediction grow with mode number? Reported on the four
    stages that publish all three flexural modes, because the 3F sample is
    only the four longest blades and comparing it against a 1F sample of
    ten would confound mode number with blade length."""
    import statistics as st
    c = comparisons()
    stages = {r["stage"] for r in c if r["mode"] == "3F"}
    out = {}
    for mode in ("1F", "2F", "3F"):
        e = [r["err_pct"] for r in c if r["mode"] == mode and r["stage"] in stages]
        all_e = [r["err_pct"] for r in c if r["mode"] == mode]
        out[mode] = dict(n_matched=len(e), median_matched=st.median(e),
                         n_all=len(all_e), mean_all=st.mean(all_e))
    out["matched_stages"] = sorted(stages)
    out["monotone"] = (out["1F"]["median_matched"] < out["2F"]["median_matched"]
                       < out["3F"]["median_matched"])
    return out


def crossings(rpm_lo=RPM_100PCT, rpm_hi=RPM_DETERIORATED):
    """Where each mode line crosses an engine order INSIDE the operating
    range -- which is the only question a Campbell diagram exists to
    answer.

    Counted twice: once against the published lines as they are drawn
    (flat), once against the model's own lines (rising with speed). The
    two disagree, and that disagreement is a consequence of the flatness,
    not a separate finding."""
    pub = published()
    out = []
    for blk in pub["stages"]:
        stage = blk["stage"]
        for i, key in enumerate(("first_flex", "second_flex", "third_flex")):
            f0 = blk["modes"].get(key)
            if f0 is None:
                continue
            curve = predicted_curve(stage, i, [rpm_lo, rpm_hi])
            for n in blk["per_rev_lines"]:
                order_lo, order_hi = n * rpm_lo / 60, n * rpm_hi / 60
                # published line is flat at f0
                pub_hit = order_lo <= f0 <= order_hi
                mdl_hit = ((curve[0] - order_lo) * (curve[1] - order_hi)) <= 0 \
                    if curve else None
                if pub_hit or mdl_hit:
                    out.append(dict(stage=stage, mode=("1F", "2F", "3F")[i], order=n,
                                    published_crosses=bool(pub_hit),
                                    model_crosses=bool(mdl_hit),
                                    agree=bool(pub_hit) == bool(mdl_hit)))
    return out


def crossing_summary():
    c = crossings()
    return dict(total=len(c),
                published_only=sum(1 for r in c if r["published_crosses"]
                                   and not r["model_crosses"]),
                model_only=sum(1 for r in c if r["model_crosses"]
                               and not r["published_crosses"]),
                both=sum(1 for r in c if r["agree"]))


@lru_cache(maxsize=None)
def predicted_curves(stage, rpms):
    """All three flexural mode lines for one stage, across speed.

    Solved three-at-a-time per speed rather than once per mode: the figure
    wants nine speeds x three modes, and asking for them separately triples
    the eigensolves for no new information.

    `stiff=False` is the WEAK axis -- the same quantity E3's closure
    compares. `stiff=True` selects the root-axis inertia and returns a
    frequency 2.3x higher; plotting that would have illustrated the closure
    with a number the closure does not use (finding 161).

    The model comes from `blade_frequency.hpc_rotor_model`, the same call
    the closure itself uses, so the figure cannot drift from it."""
    from mechanical.blade_frequency import hpc_rotor_model
    m = hpc_rotor_model(stage)
    if m is None:
        return None
    per_speed = [m.modes(False, rpm, 3) for rpm in rpms]
    return tuple(tuple(sp[i] for sp in per_speed) for i in range(3))


def predicted_curve(stage, mode_index, rpms):
    """One mode line across speed. See `predicted_curves`."""
    c = predicted_curves(stage, tuple(rpms))
    return None if c is None else list(c[mode_index])


def plot_match(path=None):
    """The match. Linear axis, the 5 % band to scale, every point's reading
    uncertainty shown, and the eleven points where 5 % is unresolvable
    marked as such."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    c = sorted(comparisons(), key=lambda r: (r["mode"], r["stage"]))
    R = resolvability()
    fig, ax = plt.subplots(figsize=(13.5, 6.4))

    ax.axhspan(-CLOSURE_BAND_PCT, CLOSURE_BAND_PCT, color="#cfe8d6", alpha=0.75,
               zorder=0, label=f"E3's closure band, ±{CLOSURE_BAND_PCT:.0f} %")
    ax.axhline(0, color="0.35", lw=0.9, zorder=1)

    xs = range(len(c))
    COL = {"1F": "#1f4e79", "2F": "#a8600f", "3F": "#8c2f39"}
    for x, r in zip(xs, c):
        ax.errorbar(x, r["err_pct"], yerr=r["unc_pct"], fmt="none",
                    ecolor="0.62", elinewidth=1.1, capsize=3, zorder=2)
        ax.plot([x], [r["err_pct"]], marker="o" if r["resolvable"] else "D",
                ms=7 if r["resolvable"] else 6.5,
                mfc=COL[r["mode"]] if r["resolvable"] else "white",
                mec=COL[r["mode"]], mew=1.6, zorder=3)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{r['mode']}\n{r['stage']}" for r in c], fontsize=7.4)
    ax.set_xlabel("mode / HPC rotor stage", labelpad=2)
    ax.set_ylabel("predicted − published, % of published")

    from matplotlib.lines import Line2D
    handles = [
        Line2D([], [], marker="o", ls="", mfc=COL["1F"], mec=COL["1F"], ms=7,
               label="5 % is resolvable against the reading"),
        Line2D([], [], marker="D", ls="", mfc="white", mec="0.3", mew=1.6, ms=6.5,
               label="5 % is FINER than the reading uncertainty — unfalsifiable"),
        Line2D([], [], color="0.62", lw=1.1,
               label="reading uncertainty, half a minor division of that stage's axis"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.95)

    ax.set_title(
        "E$^3$ Stage E3 closure: HPC rotor blade frequencies against Figs 33–42\n"
        f"{R['passes_overall']} of {R['total']} inside ±5 %. "
        f"But on {R['unresolvable']} of {R['total']} — including every one of the "
        f"{R['first_flex_total']} first-flex modes — the transcription "
        "cannot resolve 5 % at all.", fontsize=10.5)
    ax.grid(axis="y", alpha=0.25, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    path = Path(path or (FIGDIR / "campbell-match.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_stages(path=None, n_rpm=9):
    """Ten Campbell diagrams. Published lines flat as read; predicted lines
    carrying the stiffening the model has and the diagrams do not."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pub = published()
    by = {s["stage"]: s for s in pub["stages"]}
    rpms = [RPM_MAX_PLOT * i / (n_rpm - 1) for i in range(n_rpm)]
    fig, axes = plt.subplots(2, 5, figsize=(19, 7.4), sharex=True)
    COL = {0: "#1f4e79", 1: "#a8600f", 2: "#8c2f39"}
    LBL = {0: "1F", 1: "2F", 2: "3F"}

    for ax, stage in zip(axes.ravel(), sorted(by)):
        blk = by[stage]
        top = blk["axis_max_kHz"]
        ax.axvspan(RPM_100PCT / 1000, RPM_DETERIORATED / 1000, color="#f2e6cf",
                   alpha=0.85, zorder=0)

        for n in blk["per_rev_lines"]:
            ax.plot([0, RPM_MAX_PLOT / 1000], [0, n * RPM_MAX_PLOT / 60 / 1000],
                    color="0.82", lw=0.7, zorder=1)
            y = n * RPM_MAX_PLOT / 60 / 1000
            if y <= top:
                ax.text(RPM_MAX_PLOT / 1000, y, f" {n}E", fontsize=5.5,
                        color="0.55", va="center")

        # published: drawn flat, as the diagrams draw them
        for name, f in blk["modes"].items():
            if f / 1000 > top:
                continue
            ax.plot([0, RPM_MAX_PLOT / 1000], [f / 1000] * 2, color="0.25",
                    lw=1.3, zorder=3)
        # predicted: the model's own speed dependence, weak axis
        for i in range(3):
            curve = predicted_curve(stage, i, rpms)
            if curve is None:
                continue
            ax.plot([r / 1000 for r in rpms], [f / 1000 for f in curve],
                    color=COL[i], lw=1.6, ls=(0, (5, 2)), zorder=4,
                    label=LBL[i] if stage == 1 else None)
            # a predicted line above this stage's published axis is still a
            # prediction; say where it went rather than clip it away
            if min(curve) / 1000 > top:
                ax.annotate(f"{LBL[i]} predicted {curve[0] / 1000:.1f} kHz ↑",
                            xy=(0.5, 0.97 - 0.075 * i), xycoords="axes fraction",
                            ha="center", va="top", fontsize=6.6, color=COL[i])

        ax.set_title(f"rotor {stage} — Fig {blk['figure']}", fontsize=9)
        ax.set_ylim(0, top)
        ax.set_xlim(0, RPM_MAX_PLOT / 1000)
        ax.grid(alpha=0.2, lw=0.4)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=7.5)

    for ax in axes[1]:
        ax.set_xlabel("HP rotor speed, 1000 rpm", fontsize=8.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("frequency, kHz", fontsize=8.5)
    axes[0][0].legend(fontsize=7.5, loc="upper left", title="predicted",
                      title_fontsize=7.5)
    fig.suptitle(
        "E$^3$ HPC rotor Campbell diagrams — solid grey: published mode lines "
        "(Figs 33–42), drawn flat as they are printed.  Dashed: this project's "
        "beam model, carrying the centrifugal stiffening the published lines do not "
        "show.  Shaded: HP operating range, 12,303–13,948 rpm.", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    path = Path(path or (FIGDIR / "campbell-stages.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def summary():
    R, T = resolvability(), mode_number_trend()
    L = ["Stage J unit J2 -- the Campbell match", ""]
    L.append(f"   {R['passes_overall']} of {R['total']} comparisons inside E3's "
             f"±{CLOSURE_BAND_PCT:.0f} % closure band")
    L.append(f"   {R['unresolvable']} of {R['total']} cannot resolve 5 % at all -- "
             f"the reading uncertainty is coarser than the band")
    L.append(f"   first flex: {R['first_flex_resolvable']} of "
             f"{R['first_flex_total']} resolvable  (worst reading "
             f"±{R['worst_unc_pct']:.0f} %)")
    L.append(f"   among the {R['resolvable']} that CAN be judged: "
             f"{R['passes_among_resolvable']} pass")
    L.append(f"   inside the figure's own reading uncertainty: "
             f"{R['within_reading']} of {R['total']}")
    L += ["", "   over-prediction vs mode number, on the "
          f"{len(T['matched_stages'])} stages publishing all three "
          f"(stages {', '.join(str(s) for s in T['matched_stages'])}):"]
    for m in ("1F", "2F", "3F"):
        L.append(f"      {m}  median {T[m]['median_matched']:+6.1f} %   "
                 f"(all stages: mean {T[m]['mean_all']:+6.1f} %, n={T[m]['n_all']})")
    L.append(f"   monotone with mode number: {T['monotone']}")
    X = crossing_summary()
    L += ["", f"   resonance crossings inside the HP operating range "
          f"({RPM_100PCT:.0f}-{RPM_DETERIORATED:.0f} rpm): {X['total']}"]
    L.append(f"      both agree        {X['both']}")
    L.append(f"      published only    {X['published_only']}")
    L.append(f"      this model only   {X['model_only']}")
    L.append("   -- the flat published lines and the rising predicted ones do "
             "not pick the same resonances")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
    root = Path(__file__).resolve().parents[2]
    for p in (plot_match(), plot_stages()):
        print(f"\n   wrote {p.relative_to(root)}")
