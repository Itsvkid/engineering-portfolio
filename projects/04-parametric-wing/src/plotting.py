"""Figures for the wing: planform and sections.

Same two selected palettes as the flight performance project — the dark steps
are re-stepped for a dark ground and validated against it, not an inversion of
the light set. The dark surface, ink and grid are the portfolio site's tokens,
so a figure sits flush on that page.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .wing import Wing  # noqa: E402

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink_muted": "#52514e",
              "grid": "#e4e3df", "series": ("#2a78d6", "#eb6834", "#1baf7a"),
              "fill_alpha": 0.10},
    "dark": {"surface": "#101316", "ink": "#edeef0", "ink_muted": "#788087",
             "grid": "#23282e", "series": ("#3987e5", "#d95926", "#199e70"),
             "fill_alpha": 0.16},
}
_ACTIVE = THEMES["light"]
LINE_W, DPI = 2.0, 160


def use_theme(name: str) -> None:
    global _ACTIVE
    if name not in THEMES:
        raise ValueError(f"unknown theme {name!r}")
    _ACTIVE = THEMES[name]


def _c(role):
    return _ACTIVE[role]


def _axes(title, xlabel, ylabel, size=(8.0, 5.0), title_pad=14):
    fig, ax = plt.subplots(figsize=size, dpi=DPI)
    fig.patch.set_facecolor(_c("surface"))
    ax.set_facecolor(_c("surface"))
    ax.set_title(title, color=_c("ink"), fontsize=12, fontweight="600",
                 loc="left", pad=title_pad)
    ax.set_xlabel(xlabel, color=_c("ink_muted"), fontsize=10)
    ax.set_ylabel(ylabel, color=_c("ink_muted"), fontsize=10)
    ax.grid(True, color=_c("grid"), linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_c("grid"))
    ax.tick_params(colors=_c("ink_muted"), labelsize=9, length=0)
    return fig, ax


def _save(fig, path):
    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, facecolor=_c("surface"), bbox_inches="tight")
    return fig


def planform(wing: Wing, path=None):
    """Top view with the quarter-chord line and the MAC marked.

    Drawn from the same parameters that build the solid, so the drawing cannot
    describe a different wing from the one exported.
    """
    semi = wing.span / 2.0
    sweep = math.tan(math.radians(wing.sweep_deg))

    def edges(eta):
        y = eta * semi
        chord = wing.chord_at(eta)
        quarter = 0.25 * wing.root_chord + y * sweep
        return quarter - 0.25 * chord, quarter + 0.75 * chord, quarter

    etas = [i / 200 for i in range(201)]
    ys = [e * semi for e in etas]
    le = [edges(e)[0] for e in etas]
    te = [edges(e)[1] for e in etas]
    qc = [edges(e)[2] for e in etas]

    fig, ax = _axes(
        f"Planform — {wing.span:.1f} m span, taper {wing.taper_ratio:.2f}, "
        f"{wing.sweep_deg:.0f}° sweep",
        "Spanwise station y (m)", "Chordwise x (m), aft positive",
    )

    for sign in (1, -1):
        yy = [sign * v for v in ys]
        ax.plot(yy, le, color=_c("series")[0], linewidth=LINE_W, zorder=3)
        ax.plot(yy, te, color=_c("series")[0], linewidth=LINE_W, zorder=3)
        ax.fill_between(yy, le, te, color=_c("series")[0],
                        alpha=_c("fill_alpha"), zorder=1)
        ax.plot(yy, qc, color=_c("series")[1], linewidth=1.2,
                linestyle=(0, (5, 3)), zorder=4)

    y_mac = wing.mac_spanwise_station
    eta_mac = y_mac / semi
    mac_le, mac_te, _ = edges(eta_mac)
    ax.plot([y_mac, y_mac], [mac_le, mac_te], color=_c("series")[2],
            linewidth=2.5, zorder=5)
    ax.annotate(f"MAC {wing.mac:.3f} m\nat y = {y_mac:.3f} m",
                xy=(y_mac, mac_te), xytext=(10, 8),
                textcoords="offset points", color=_c("ink"), fontsize=9)
    # Port side: the MAC callout owns the starboard half, and two labels in
    # the same corner is how a drawing stops being readable.
    ax.annotate("Quarter-chord line", xy=(-semi * 0.6, edges(0.6)[2]),
                xytext=(-18, -34), textcoords="offset points",
                color=_c("ink"), fontsize=9, fontweight="600", ha="center")

    ax.invert_yaxis()          # aft downward, as a drawing would show it
    ax.set_aspect("equal")
    return _save(fig, path)


def sections(wing: Wing, path=None):
    """Root and tip sections at true relative scale, washout included.

    Worth drawing because a wing this slender — 51:1 span to thickness on the
    reference geometry — renders as a flat plate in any 3D view. The section is
    the part a reviewer actually needs to see.
    """
    upper, lower = wing.section.surfaces()
    fig, ax = _axes(
        f"Sections — NACA {int(wing.section.max_camber*100)}"
        f"{int(wing.section.camber_position*10)}"
        f"{int(wing.section.thickness*100):02d}, "
        f"{wing.twist_deg:.0f}° washout at tip",
        "x (m)", "z (m)", size=(8.0, 3.8), title_pad=30,
    )

    for label, chord, twist_deg, colour in (
        (f"Root, c = {wing.root_chord:.3f} m", wing.root_chord, 0.0,
         _c("series")[0]),
        (f"Tip, c = {wing.tip_chord:.3f} m", wing.tip_chord, wing.twist_deg,
         _c("series")[1]),
    ):
        twist = math.radians(-twist_deg)
        xs, zs = [], []
        for xc, zc in upper + list(reversed(lower)):
            x = (xc - 0.25) * chord
            z = zc * chord
            xs.append(0.25 * chord + x * math.cos(twist) - z * math.sin(twist))
            zs.append(x * math.sin(twist) + z * math.cos(twist))
        ax.plot(xs, zs, color=colour, linewidth=LINE_W, zorder=3, label=label)
        ax.fill(xs, zs, color=colour, alpha=_c("fill_alpha"), zorder=1)

    # Above the axes. Below it collided with the x-axis tick labels, and the
    # equal-aspect box is too shallow to hold a legend inside without sitting
    # on the aerofoil.
    ax.legend(frameon=False, labelcolor=_c("ink_muted"), fontsize=9, ncol=2,
              loc="lower center", bbox_to_anchor=(0.5, 1.02))
    ax.set_aspect("equal")
    return _save(fig, path)


def generate_all(wing: Wing, directory="figures", theme="light", suffix=""):
    use_theme(theme)
    directory = Path(directory)
    written = []
    for name, fn in ((f"wing-planform{suffix}.png", planform),
                     (f"wing-sections{suffix}.png", sections)):
        target = directory / name
        fig = fn(wing, target)
        plt.close(fig)
        written.append(target)
    return written
