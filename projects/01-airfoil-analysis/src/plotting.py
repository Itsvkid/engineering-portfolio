"""Figures for the NACA 0012 vs NACA 4412 comparison. Matplotlib only."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .geometry import Naca4
from .panel_method import PanelGeometry, solve
from .polar import sweep

COLORS = {"0012": "#2874a6", "4412": "#c0392b"}


def cl_alpha_figure(alphas_deg: np.ndarray, polars: dict, path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for code, pts in polars.items():
        cls = [p.cl for p in pts]
        ax.plot(alphas_deg, cls, "o-", color=COLORS[code], label=f"NACA {code}", markersize=4)
        sep_mask = [p.upper_separated or p.lower_separated for p in pts]
        ax.plot(
            np.array(alphas_deg)[sep_mask], np.array(cls)[sep_mask], "x",
            color=COLORS[code], markersize=9, markeredgewidth=2,
        )

    a = Naca4.parse("0012")
    alphas_rad = np.radians(alphas_deg)
    ax.plot(
        alphas_deg, 2 * np.pi * alphas_rad, "--", color="gray", linewidth=1,
        label="Thin airfoil theory, 2π·α",
    )

    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Angle of attack, deg")
    ax.set_ylabel("$C_l$")
    ax.set_title("Lift curve — symmetric vs. cambered\n(× marks a station where this model predicts separation)")
    ax.legend()
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def drag_polar_figure(polars: dict, path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for code, pts in polars.items():
        cls = [p.cl for p in pts]
        cds = [p.cd for p in pts]
        ax.plot(cds, cls, "o-", color=COLORS[code], label=f"NACA {code}", markersize=4)
    ax.set_xlabel("$C_d$")
    ax.set_ylabel("$C_l$")
    ax.set_title("Drag polar")
    ax.legend()
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def efficiency_figure(alphas_deg: np.ndarray, polars: dict, path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for code, pts in polars.items():
        ld = [p.cl / p.cd if p.cd else 0.0 for p in pts]
        ax.plot(alphas_deg, ld, "o-", color=COLORS[code], label=f"NACA {code}", markersize=4)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Angle of attack, deg")
    ax.set_ylabel("$C_l / C_d$")
    ax.set_title("Aerodynamic efficiency")
    ax.legend()
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def cp_distribution_figure(alpha_deg: float, path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for code in ("0012", "4412"):
        a = Naca4.parse(code)
        x, y = a.surface(160)
        geo = PanelGeometry.from_surface(x, y)
        sol = solve(geo, alpha_rad=np.radians(alpha_deg))
        ax.plot(geo.xc, sol.cp, ".", color=COLORS[code], markersize=3, label=f"NACA {code}")
    ax.invert_yaxis()  # convention: suction (negative Cp) plots upward
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("x / c")
    ax.set_ylabel("$C_p$")
    ax.set_title(f"Pressure distribution, α = {alpha_deg:.0f}°")
    ax.legend()
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


# Site tokens (see the portfolio's app/globals.css :root / [data-theme]
# blocks), so the validation figure sits flush on the page it is published
# to. The four figures above predate the site and keep their own defaults.
THEMES = {
    "light": {"surface": "#f2eee6", "ink": "#221e18", "ink_muted": "#6e6558",
              "grid": "#d9d0c0", "0012": "#2874a6", "4412": "#b23d0e"},
    "dark": {"surface": "#1b1815", "ink": "#f1ece4", "ink_muted": "#8c8377",
             "grid": "#39332b", "0012": "#5aa9e6", "4412": "#ff6d3b"},
}


def xflr5_validation_figure(project: dict, reference: dict, path,
                            theme: str = "light") -> Path:
    """This project's polars against XFLR5's, Cl and Cd side by side.

    `project` and `reference` are both {code: {alpha: PolarPoint}}. Solid
    lines are this project, dashed are XFLR5.

    The two panels are drawn on deliberately different terms. Cl is plotted
    linearly, because the two methods agree closely enough there that a
    linear axis shows the gap opening at high alpha. Cd is plotted on a log
    axis, because the disagreement is a *factor* -- roughly 2.5x -- and on a
    linear axis two curves 0.007 apart look like agreement.
    """
    t = THEMES[theme]
    fig, (ax_cl, ax_cd) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=110)
    fig.patch.set_facecolor(t["surface"])

    for ax in (ax_cl, ax_cd):
        ax.set_facecolor(t["surface"])
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(t["grid"])
        ax.tick_params(colors=t["ink_muted"], labelsize=8)
        ax.xaxis.label.set_color(t["ink"])
        ax.yaxis.label.set_color(t["ink"])
        ax.grid(True, color=t["grid"], linewidth=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        ax.set_xlabel("Angle of attack, deg")

    for code in sorted(project):
        colour = t[code]
        alphas = sorted(project[code])
        ax_cl.plot(alphas, [project[code][a].cl for a in alphas], "-",
                   color=colour, linewidth=1.8, label=f"NACA {code} — this project")
        ax_cd.semilogy(alphas, [project[code][a].cd for a in alphas], "-",
                       color=colour, linewidth=1.8)

        ref_alphas = sorted(reference[code])
        ax_cl.plot(ref_alphas, [reference[code][a].cl for a in ref_alphas], "--",
                   color=colour, linewidth=1.4, dashes=(4, 2),
                   label=f"NACA {code} — XFLR5 / XFoil")
        ax_cd.semilogy(ref_alphas, [reference[code][a].cd for a in ref_alphas],
                       "--", color=colour, linewidth=1.4, dashes=(4, 2))

    alphas_ref = np.linspace(-6, 12, 50)
    ax_cl.plot(alphas_ref, 2 * np.pi * np.radians(alphas_ref), ":",
               color=t["ink_muted"], linewidth=1.1, label="Thin airfoil, 2\u03c0\u00b7\u03b1")

    ax_cl.axhline(0, color=t["grid"], linewidth=0.8)
    ax_cl.set_ylabel("$C_l$")
    ax_cl.set_title("Lift — agrees to 0.047 RMS on the symmetric section",
                    color=t["ink"], fontsize=10, pad=8)
    legend = ax_cl.legend(fontsize=7.5, framealpha=0, loc="upper left")
    for text in legend.get_texts():
        text.set_color(t["ink_muted"])

    ax_cd.set_ylabel("$C_d$  (log scale)")
    ax_cd.set_title("Drag — this project recovers under half of XFoil's",
                    color=t["ink"], fontsize=10, pad=8)

    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=t["surface"])
    plt.close(fig)
    return path
