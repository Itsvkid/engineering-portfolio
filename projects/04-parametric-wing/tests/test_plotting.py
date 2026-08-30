"""Smoke tests for the figures.

No test can check that a drawing reads well. These check it is produced, in
both themes, so a refactor that breaks figure generation fails here rather
than silently the next time the drawings are rebuilt.
"""

import matplotlib.pyplot as plt
import pytest

from src import plotting
from src.wing import Wing

REF = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, sweep_deg=25.0,
           dihedral_deg=5.0, twist_deg=3.0)


def test_generates_both_themes(tmp_path):
    light = plotting.generate_all(REF, tmp_path, theme="light")
    dark = plotting.generate_all(REF, tmp_path, theme="dark", suffix="-dark")
    assert len(light) == len(dark) == 2
    for path in light + dark:
        assert path.exists() and path.stat().st_size > 10_000
    assert {p.name for p in light}.isdisjoint({p.name for p in dark})


def test_dark_theme_is_selected_not_flipped():
    assert plotting.THEMES["light"]["series"] != plotting.THEMES["dark"]["series"]
    assert plotting.THEMES["light"]["surface"] != plotting.THEMES["dark"]["surface"]


def test_unknown_theme_raises():
    with pytest.raises(ValueError, match="unknown theme"):
        plotting.use_theme("blueprint")


def test_each_figure_builds_without_a_path():
    for fn in (plotting.planform, plotting.sections):
        fig = fn(REF)
        assert fig is not None
        plt.close(fig)
