"""The general arrangement drawing.

No test can say a drawing reads well — that needs eyes on the sheet. These
check it is produced, that it is deterministic, and that the values it quotes
come from the wing rather than from constants typed into the drawing code.
"""

import matplotlib.pyplot as plt
import pytest

from src.drawing import general_arrangement, section_label
from src.airfoil import NACA4
from src.wing import Wing

REF = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, sweep_deg=25.0,
           dihedral_deg=5.0, twist_deg=3.0)


def test_produces_a_sheet(tmp_path):
    path = tmp_path / "ga.png"
    plt.close(general_arrangement(REF, path))
    assert path.exists() and path.stat().st_size > 50_000


def test_is_deterministic(tmp_path):
    """Regenerating an unchanged design must produce an identical file.

    A timestamp in the sheet would make every rebuild a diff, and a drawing
    that changes without the design changing stops being worth committing.
    """
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(REF, a))
    plt.close(general_arrangement(REF, b))
    assert a.read_bytes() == b.read_bytes()


def test_a_date_changes_the_sheet(tmp_path):
    """The determinism above must come from omitting the date, not ignoring it."""
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(REF, a))
    plt.close(general_arrangement(REF, b, date="2026-08-19"))
    assert a.read_bytes() != b.read_bytes()


def test_a_different_wing_gives_a_different_sheet(tmp_path):
    """Guards against a drawing that ignores its input."""
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(REF, a))
    plt.close(general_arrangement(
        Wing(span=12.0, root_chord=1.6, taper_ratio=0.45, sweep_deg=25.0), b))
    assert a.read_bytes() != b.read_bytes()


@pytest.mark.parametrize("code", ["0012", "2412", "4415", "0024"])
def test_section_label_round_trips_the_code(code):
    """The title block designation is rebuilt from the section, not stored."""
    wing = Wing(span=10.0, root_chord=1.6, taper_ratio=0.5,
                section=NACA4.from_code(code))
    assert section_label(wing) == f"NACA {code}"


def test_scale_is_honoured(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(REF, a, scale_denominator=50))
    plt.close(general_arrangement(REF, b, scale_denominator=75))
    assert a.read_bytes() != b.read_bytes()
