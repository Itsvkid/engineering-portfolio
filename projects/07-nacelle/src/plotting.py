"""Figures. Matplotlib only — no pyOCC dependency."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .cst import CSTCurve
from .profile import NacelleProfile

# Site tokens (see the portfolio's app/globals.css :root / [data-theme="light"]
# blocks) — same THEMES pattern project 06 uses, so a figure dropped into
# public/products/ sits flush on the page rather than carrying a plot's
# default palette.
THEMES = {
    "light": {"surface": "#f2eee6", "ink": "#221e18", "ink_muted": "#6e6558",
              "grid": "#d9d0c0", "fill": "#b23d0e", "marker": "#221e18"},
    "dark": {"surface": "#1b1815", "ink": "#f1ece4", "ink_muted": "#8c8377",
             "grid": "#39332b", "fill": "#ff6d3b", "marker": "#f1ece4"},
}


def meridian_figure(profile: NacelleProfile, path, theme: str = "light") -> Path:
    """The generatrix itself, plus its mirror — what the revolution
    actually sweeps, since the meridian alone reads as a plot, not a
    nacelle. theme picks the site's dark or light tokens so this can drop
    straight into public/products/, the same convention project 06's
    hub-tip-sections figure uses."""
    t = THEMES[theme]
    points = profile.meridian_points()
    xs = [x for x, _ in points]
    rs = [r for _, r in points]
    x_max, r_max = profile.max_radius()

    fig, ax = plt.subplots(figsize=(8.0, 4.0), dpi=220)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    ax.plot(xs, rs, color=t["fill"], linewidth=2.4, zorder=3)
    ax.plot(xs, [-r for r in rs], color=t["fill"], linewidth=2.4, alpha=0.4, zorder=3)
    ax.fill_between(xs, rs, [-r for r in rs], color=t["fill"], alpha=0.14, zorder=1)
    ax.axhline(0, color=t["grid"], linewidth=0.8, linestyle="--", zorder=2)
    ax.plot([x_max], [r_max], "o", color=t["marker"], zorder=5)
    ax.annotate(f"max r={r_max:.3f} m at {100*x_max/profile.length:.0f}% length",
                xy=(x_max, r_max), xytext=(14, -22), textcoords="offset points",
                color=t["ink"])
    ax.set_xlabel("Axial station, m", color=t["ink_muted"])
    ax.set_ylabel("Radius, m", color=t["ink_muted"])
    ax.set_aspect("equal")
    ax.tick_params(colors=t["ink_muted"])
    for spine in ax.spines.values():
        spine.set_color(t["grid"])
    ax.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("Nacelle meridian profile (CST)", color=t["ink"],
                 loc="left", fontweight="600", pad=14)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight")
    plt.close(fig)
    return path


def complete_nacelle_figure(external: NacelleProfile, internal: NacelleProfile,
                             path, theme: str = "light") -> Path:
    """External cowl and internal duct together, upper half only — showing
    both curves mirrored like meridian_figure does would draw the duct wall
    twice at the same radius on each side and read as two nested outlines
    rather than a hollow shell in cross-section. The filled band between
    the two curves is the material a real cutaway would show as solid."""
    t = THEMES[theme]
    ext_points = external.meridian_points()
    int_points = internal.meridian_points()
    ext_xs, ext_rs = [x for x, _ in ext_points], [r for _, r in ext_points]
    int_xs, int_rs = [x for x, _ in int_points], [r for _, r in int_points]

    fig, ax = plt.subplots(figsize=(8.0, 4.0), dpi=220)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    ax.plot(ext_xs, ext_rs, color=t["fill"], linewidth=2.4, zorder=3, label="External cowl")
    ax.plot(int_xs, int_rs, color=t["ink_muted"], linewidth=2.0, linestyle="--",
             zorder=3, label="Internal duct")
    ax.fill_between(ext_xs, ext_rs, int_rs, color=t["fill"], alpha=0.14, zorder=1)
    ax.axhline(0, color=t["grid"], linewidth=0.8, linestyle=":", zorder=2)

    ax.set_xlabel("Axial station, m", color=t["ink_muted"])
    ax.set_ylabel("Radius, m", color=t["ink_muted"])
    ax.set_aspect("equal")
    ax.tick_params(colors=t["ink_muted"])
    for spine in ax.spines.values():
        spine.set_color(t["grid"])
    ax.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    legend = ax.legend(frameon=False, loc="upper right")
    for text in legend.get_texts():
        text.set_color(t["ink"])
    ax.set_title("Nacelle cross-section — cowl and duct wall", color=t["ink"],
                 loc="left", fontweight="600", pad=14)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight")
    plt.close(fig)
    return path


def fit_demo_figure(target_profile: NacelleProfile, fitted: CSTCurve, path) -> Path:
    """Target profile against the CST curve fitted back to it — the
    benchmarking demo made visible rather than left as a single RMS number.
    """
    points = target_profile.meridian_points(80)
    xs = [x for x, _ in points]
    psis = [x / target_profile.length for x in xs]
    target_rs = [r for _, r in points]
    fitted_rs = [fitted(psi) for psi in psis]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 5.2), dpi=150,
                                    sharex=True, height_ratios=(3, 1))
    ax1.plot(xs, target_rs, color="#888888", linewidth=4.0, alpha=0.4,
              label="Target (sampled)")
    ax1.plot(xs, fitted_rs, color="#c0392b", linewidth=1.4, linestyle="--",
              label="Fitted CST curve")
    ax1.set_ylabel("Radius, m")
    ax1.legend(frameon=False)
    ax1.set_title("CST fit recovery")

    residual_mm = [1000 * (f - t) for f, t in zip(fitted_rs, target_rs)]
    ax2.plot(xs, residual_mm, color="#2874a6", linewidth=1.2)
    ax2.axhline(0, color="#888888", linewidth=0.8)
    ax2.set_xlabel("Axial station, m")
    ax2.set_ylabel("Error, mm")
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path
