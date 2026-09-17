"""Stage L figures — the shaft-speed conflict, drawn.

One chart, because the study has one result. Bypass ratio 10 does not fail
on the fan and it does not fail on blade stress; it fails because the fan
and the LP turbine want the shaft at different speeds, and everything else
in the study is a way of paying that difference.

A table of rpm cannot show divergence. Two lines pulling apart can, and the
whole argument — gearbox or stages — is the vertical gap between them at
the right-hand edge.

Colours are the site's own figure convention (`app/globals.css`, and the
same pairs `projects/08-cycle-model/src/plotting.py` uses), stepped for the
dark surface rather than flipped, and both pairs were run through the
categorical palette checks before use: lightness band, chroma floor,
colour-vision separation, normal-vision separation and contrast. The dark
pair as published elsewhere on the site failed two of those — both hues sat
above the dark band at L 0.70, and the blue fell under the chroma floor at
0.097, which is the value at which a hue starts reading as grey — so the
dark steps here are darker and more saturated than the light ones rather
than the same hex on a different ground.

Identity never rests on colour: each line carries a direct label at its own
end, so the chart survives being printed, photocopied, or read by someone
who cannot separate the two hues.
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .tf001 import Excursion, N_E3_RPM  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")

# Validated categorical pairs. Light: surface #FFFFFF. Dark: surface #101316.
LIGHT = dict(bg="#FFFFFF", fg0="#17191C", fg1="#4A5057", rule="#E3E3DF",
             fan="#c0392b", lpt="#2874a6", band="#8a8f96")
DARK = dict(bg="#101316", fg0="#EDEEF0", fg1="#A8AFB8", rule="#23282E",
            fan="#E0561F", lpt="#3B87C9", band="#6d757e")


def series():
    """The two speeds, and the gap between them, across the sweep."""
    ex = Excursion()
    out = []
    for p in ex.sweep():
        c = ex.shaft_speed_conflict(p)
        out.append(dict(bpr=p.bpr, fan=c["n_fan_rpm"], lpt=c["n_lpt_rpm"],
                        ratio=c["gear_ratio"]))
    return out


def shaft_speed_figure(path=None, dark=False):
    """The fan and the LP turbine, pulling apart."""
    c = DARK if dark else LIGHT
    pts = series()
    x = [p["bpr"] for p in pts]
    fan = [p["fan"] for p in pts]
    lpt = [p["lpt"] for p in pts]

    fig, ax = plt.subplots(figsize=(8.6, 4.5), dpi=150)
    fig.patch.set_facecolor(c["bg"])
    ax.set_facecolor(c["bg"])

    # The gap is the subject, so it is drawn rather than left to be inferred.
    ax.fill_between(x, fan, lpt, color=c["band"], alpha=0.16 if dark else 0.12,
                    zorder=1, linewidth=0)

    ax.plot(x, lpt, "-o", color=c["lpt"], linewidth=2, markersize=5,
            zorder=3, solid_capstyle="round")
    ax.plot(x, fan, "-o", color=c["fan"], linewidth=2, markersize=5,
            zorder=3, solid_capstyle="round")

    # Direct labels, placed inside the axes and away from both the title and
    # each other. Identity never rests on hue: each line is named at its own
    # height, so the chart survives print, photocopy and colour-blindness.
    ax.annotate("the LP turbine wants this\n(5 stages at the E³'s own loading)",
                xy=(x[4], lpt[4]), xytext=(0, 16), textcoords="offset points",
                ha="center", va="bottom", fontsize=9, color=c["lpt"], linespacing=1.35)
    ax.annotate("the fan wants this\n(its own tip loading)",
                xy=(x[3], fan[3]), xytext=(0, -16), textcoords="offset points",
                ha="center", va="top", fontsize=9, color=c["fan"], linespacing=1.35)

    # The headline, written where it is measured.
    ax.annotate("", xy=(x[-1] - 0.05, fan[-1]), xytext=(x[-1] - 0.05, lpt[-1]),
                arrowprops=dict(arrowstyle="<->", color=c["fg1"], linewidth=1.2))
    ax.annotate(f"{(pts[-1]['ratio'] - 1) * 100:.0f} % apart\n"
                f"= {pts[-1]['ratio']:.2f} : 1 of gearbox,\nor three more LPT stages",
                xy=(x[-1] - 0.14, (fan[-1] + lpt[-1]) / 2), ha="right", va="center",
                fontsize=9.5, color=c["fg0"], linespacing=1.4)

    # Where they agree, which is why the real engine is a direct drive.
    # Placed ABOVE the convergence, not beside or below it. Any position level
    # with the crossing point puts the text on the fan line, and any position
    # below it makes the leader cross the fan line instead. Above, the leader
    # has a clear vertical run down to the point it names.
    ax.annotate(f"here they agree to {abs(pts[0]['ratio'] - 1) * 100:.1f} %,\n"
                f"which is why the E³ is a direct drive",
                xy=(x[0], (fan[0] + lpt[0]) / 2), xycoords="data",
                xytext=(0.03, 0.90), textcoords="axes fraction",
                ha="left", va="top", fontsize=9, color=c["fg1"],
                linespacing=1.4,
                arrowprops=dict(arrowstyle="-", color=c["fg1"], linewidth=0.9,
                                shrinkA=2, shrinkB=4,
                                connectionstyle="angle3,angleA=-90,angleB=0"))

    ax.set_xlabel("Bypass ratio, max climb", color=c["fg1"], fontsize=10)
    ax.set_ylabel("LP shaft speed, rpm", color=c["fg1"], fontsize=10)
    ax.set_title("What the fan wants and what the turbine wants — "
                 "ME TF0.01 on the E³ core",
                 color=c["fg0"], fontsize=11.5, pad=12)
    ax.tick_params(colors=c["fg1"], labelsize=9)
    ax.grid(True, color=c["rule"], linewidth=0.8, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(c["rule"])
    ax.set_xlim(x[0] - 0.14, x[-1] + 0.14)
    # Headroom so the direct labels sit inside the axes rather than colliding
    # with the title above or falling out under the x-axis label below.
    span = max(lpt) - min(fan)
    ax.set_ylim(min(fan) - 0.16 * span, max(lpt) + 0.20 * span)

    fig.tight_layout()
    if path is None:
        os.makedirs(FIGDIR, exist_ok=True)
        path = os.path.join(FIGDIR, "shaft-speed-conflict-dark.png" if dark
                            else "shaft-speed-conflict.png")
    fig.savefig(path, dpi=150, facecolor=c["bg"])
    plt.close(fig)
    return path


def main():
    for dark in (False, True):
        print("wrote", shaft_speed_figure(dark=dark))


if __name__ == "__main__":
    main()
