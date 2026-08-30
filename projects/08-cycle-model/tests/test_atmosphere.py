"""ISA atmosphere. No pyOCC — runs anywhere."""

from __future__ import annotations

import pytest

from src.atmosphere import P0, T0, TROPOPAUSE, at


def test_sea_level_matches_iso_2533():
    state = at(0.0)
    assert state.temperature == pytest.approx(T0)
    assert state.pressure == pytest.approx(P0)


def test_rejects_negative_altitude():
    with pytest.raises(ValueError):
        at(-100.0)


def test_temperature_falls_linearly_through_the_troposphere():
    lo, hi = at(0.0), at(5000.0)
    expected_drop = 0.0065 * 5000.0
    assert lo.temperature - hi.temperature == pytest.approx(expected_drop)


def test_temperature_is_constant_above_the_tropopause():
    a, b = at(TROPOPAUSE + 1000.0), at(TROPOPAUSE + 8000.0)
    assert a.temperature == pytest.approx(b.temperature)


def test_pressure_is_continuous_across_the_tropopause():
    """The two branches of at() must agree at the boundary — a jump there
    would mean the troposphere and stratosphere formulas were stitched
    together with mismatched constants. The offset is 1 mm, not 1 m: at a
    1 m gap, real pressure change over that altitude difference (roughly
    12 Pa) is the same order of magnitude as the tolerance and swamps the
    thing being tested; at 1 mm it's negligible."""
    just_below = at(TROPOPAUSE - 0.001)
    just_above = at(TROPOPAUSE + 0.001)
    assert just_below.pressure == pytest.approx(just_above.pressure, rel=1e-4)


def test_pressure_decreases_monotonically_with_altitude():
    altitudes = [0, 3000, 6000, TROPOPAUSE, 15000, 20000]
    pressures = [at(a).pressure for a in altitudes]
    assert pressures == sorted(pressures, reverse=True)


def test_sound_speed_matches_hand_calculation_at_sea_level():
    import math
    state = at(0.0)
    expected = math.sqrt(1.4 * 287.05287 * T0)
    assert state.sound_speed == pytest.approx(expected)


def test_cruise_altitude_matches_known_iso_values():
    """35,000 ft (10,668 m) is the reference cruise altitude the reference
    design point in build.py uses — pinned against published ISA tables
    (approx 218.8 K, approx 23,840 Pa) rather than only checked against its
    own formula."""
    state = at(10668.0)
    assert state.temperature == pytest.approx(218.8, abs=0.2)
    assert state.pressure == pytest.approx(23840.0, rel=0.01)
