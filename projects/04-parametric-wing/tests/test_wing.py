"""Built geometry against the closed forms it is supposed to realise.

The kernel and the algebra are independent routes to the same wing. Where they
disagree, one is wrong — that is the whole value of testing a CAD model rather
than looking at it.
"""

import math

import pytest

from src.airfoil import NACA4
from src.wing import Wing

REF = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, sweep_deg=25.0,
           dihedral_deg=5.0, twist_deg=3.0)

# Same wing with the angles removed, so a property can be attributed to one
# parameter at a time instead of to the combination.
PLAIN = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45)


# ── Planform algebra ────────────────────────────────────────────────────────

def test_planform_area_by_hand():
    """S = b*(c_root + c_tip)/2 = 10*(1.6+0.72)/2 = 11.6."""
    assert REF.area == pytest.approx(11.6, rel=1e-12)


def test_aspect_ratio_by_hand():
    """AR = b^2/S = 100/11.6."""
    assert REF.aspect_ratio == pytest.approx(100.0 / 11.6, rel=1e-12)


def test_tip_chord_follows_taper_ratio():
    assert REF.tip_chord == pytest.approx(0.72, rel=1e-12)


def test_mac_matches_numerical_integration():
    """MAC = (2/S)*int c^2 dy over the semi-span, against the closed form.

    The closed form is the one quoted on a drawing; the integral is its
    definition. Checking one against the other catches an algebra slip that
    a plausible-looking number would hide.
    """
    n = 200_001
    semi = REF.span / 2.0
    total = 0.0
    for i in range(n):
        eta = i / (n - 1)
        weight = 0.5 if i in (0, n - 1) else 1.0   # trapezoid rule
        total += weight * REF.chord_at(eta) ** 2
    integral = total * (semi / (n - 1))
    numerical = 2.0 * integral / REF.area
    assert numerical == pytest.approx(REF.mac, rel=1e-6)


def test_mac_station_matches_numerical_integration():
    n = 200_001
    semi = REF.span / 2.0
    total = 0.0
    for i in range(n):
        eta = i / (n - 1)
        weight = 0.5 if i in (0, n - 1) else 1.0
        total += weight * REF.chord_at(eta) * eta * semi
    integral = total * (semi / (n - 1))
    numerical = 2.0 * integral / REF.area
    assert numerical == pytest.approx(REF.mac_spanwise_station, rel=1e-6)


def test_untapered_wing_reduces_to_the_rectangular_case():
    """A limiting case with an answer everyone knows: MAC = chord."""
    rect = Wing(span=8.0, root_chord=1.2, taper_ratio=1.0)
    assert rect.mac == pytest.approx(1.2, rel=1e-12)
    assert rect.area == pytest.approx(9.6, rel=1e-12)
    assert rect.mac_spanwise_station == pytest.approx(2.0, rel=1e-12)


# ── Built solid ─────────────────────────────────────────────────────────────

def test_solid_span_matches_the_parameter():
    """Within the kernel's own shape tolerance, which is ~1e-7 here."""
    assert REF.measured_bounds()["span"] == pytest.approx(REF.span, abs=1e-5)


def test_kernel_volume_matches_the_span_integral():
    """Two independent routes to the volume, agreeing to 0.1%.

    The kernel integrates the B-rep; the prediction integrates the section
    area along the span. They share no code.
    """
    assert REF.measured_volume() == pytest.approx(
        REF.predicted_volume(), rel=1e-3
    )


def test_sweep_places_the_tip_trailing_edge_correctly():
    """x_max = 0.25*c_root + (b/2)*tan(sweep) + 0.75*c_tip.

    Sweep is defined on the quarter-chord line. Sweeping the leading edge
    instead — an easy slip — puts x_max somewhere else for every taper ratio
    except 1, so this pins the definition down.
    """
    w = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, sweep_deg=25.0)
    expected = (0.25 * w.root_chord
                + (w.span / 2.0) * math.tan(math.radians(25.0))
                + 0.75 * w.tip_chord)
    assert w.measured_bounds()["x"][1] == pytest.approx(expected, rel=1e-4)


def test_dihedral_raises_the_tip_by_the_right_amount():
    w = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, dihedral_deg=8.0)
    upper, _ = w.section.surfaces()
    tip_crown = max(z for _, z in upper) * w.tip_chord
    expected = (w.span / 2.0) * math.tan(math.radians(8.0)) + tip_crown
    assert w.measured_bounds()["z"][1] == pytest.approx(expected, rel=1e-3)


def test_bounding_box_is_tight_not_control_polygon():
    """Guards the AddOptimal choice in measured_bounds.

    The default Bnd_Box bounds a B-spline by its control polygon, which sits
    outside the surface. That over-reported this wing's height by 1.1% — a
    constant offset, not a sampling error, so denser sections do not fix it.
    """
    w = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, dihedral_deg=8.0)
    upper, _ = w.section.surfaces()
    crown = max(z for _, z in upper) * w.tip_chord
    expected = (w.span / 2.0) * math.tan(math.radians(8.0)) + crown
    assert w.measured_bounds()["z"][1] == pytest.approx(expected, rel=1e-4)


def test_no_sweep_leaves_the_root_trailing_edge_furthest_aft():
    assert PLAIN.measured_bounds()["x"][1] == pytest.approx(
        PLAIN.root_chord, rel=1e-4
    )


def test_twist_changes_the_solid():
    """Washout must actually do something, or the parameter is a lie.

    Checked on the underside and the volume, not on z_max: the highest point
    of an untwisted-root wing is the root crown, which washout at the tip
    leaves exactly where it was. Asserting on z_max would pass whether or not
    twist did anything at all.
    """
    straight = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45)
    twisted = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, twist_deg=8.0)

    assert straight.measured_bounds()["z"][1] == pytest.approx(
        twisted.measured_bounds()["z"][1], rel=1e-9
    )
    assert twisted.measured_bounds()["z"][0] < straight.measured_bounds()["z"][0]
    assert twisted.measured_volume() != pytest.approx(
        straight.measured_volume(), rel=1e-4
    )


def test_the_solid_is_valid():
    """build() raises on an invalid solid; reaching the assert means it passed.

    A non-manifold or self-intersecting body meshes badly in CFD, and that is
    far harder to diagnose downstream than here.
    """
    assert REF.build() is not None


def test_symmetric_section_wing_is_symmetric_about_the_chord_plane():
    w = Wing(span=10.0, root_chord=1.6, taper_ratio=1.0,
             section=NACA4.from_code("0012"))
    bounds = w.measured_bounds()
    assert bounds["z"][0] == pytest.approx(-bounds["z"][1], rel=1e-6)


# ── Parameter validation ────────────────────────────────────────────────────

def test_rejects_inverse_taper():
    with pytest.raises(ValueError, match="taper_ratio must be in"):
        Wing(span=10.0, root_chord=1.6, taper_ratio=1.5)


def test_rejects_nonpositive_dimensions():
    with pytest.raises(ValueError, match="must be positive"):
        Wing(span=0.0, root_chord=1.6, taper_ratio=0.5)


def test_rejects_absurd_angles():
    with pytest.raises(ValueError, match="under 89 degrees"):
        Wing(span=10.0, root_chord=1.6, taper_ratio=0.5, sweep_deg=90.0)
