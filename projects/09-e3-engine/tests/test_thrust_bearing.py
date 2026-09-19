"""Unit E4's restated second half: the published thrust-bearing axial loads.

E4's gate said "no bearing load and no bearing capacity is printed
anywhere". CR-168211 Figs 340-341 print both thrust bearings' axial load.
The capacity is still printed nowhere, and these tests assert BOTH halves
of that -- the load, and the absence of a capacity -- so that a later
reader cannot mistake one for the other.
"""
import pathlib
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from mechanical.rotordynamics import (                      # noqa: E402
    is_the_thrust_bearing_load_centrifugal, thrust_bearing_loads,
    what_the_bearing_load_says_about_d6)

D = yaml.safe_load((ROOT / "data" / "icls-thrust-bearing.yaml").read_text())
T = thrust_bearing_loads()


def test_the_printed_pound_axis_closes_on_the_printed_kN_axis():
    """The band, stated before the run: +-0.1 kN, a rounding tolerance.

    This is arithmetic on eleven printed axis labels and involves no
    reading of the curve at all, so it tests the transcription of the
    calibration rather than the digitising.
    """
    assert T["axis_closure_kN"] <= 0.1


def test_the_sign_convention_is_the_reports_own_sentence():
    """CR-168211 p.525: "Positive thrust is in the forward direction"."""
    assert "forward direction" in D["meta"]["sign_convention"]
    assert T["hp_forward"] and T["lp_aft"]


def test_the_two_bearings_are_loaded_in_opposite_directions():
    """Not a tolerance -- a fact about the engine that the figures assert
    and that any later thrust balance has to reproduce."""
    hp = D["no3_hp_thrust_bearing"]["box_edge"]["load_kN"]
    lp = D["no1_lp_thrust_bearing"]["box_edge"]["load_kN"]
    assert hp > 0 > lp
    assert 1.5 < abs(lp) / hp < 2.5


def test_the_no3_load_is_not_a_centrifugal_quantity():
    """Band stated before the run: a centrifugal load would rise as N^2,
    x1.58 between 76 and 94.4 % corrected core speed, within +-20 %.

    It rises x14.4 -- a factor of 9 out. Finding 271, and E2's finding 78
    in a different part of the engine.
    """
    c = is_the_thrust_bearing_load_centrifugal()
    assert not c["centrifugal"]
    assert c["factor_out"] > 5


def test_no_bearing_capacity_or_bore_is_published_anywhere():
    """The half of E4 that CANNOT be closed, asserted as an absence so it
    is never quietly filled in. The claim is about the whole source list:
    five documents are named as searched.
    """
    assert T["capacity_published"] is False
    assert T["bore_published"] is False
    q = D["not_published"]["quantities"]
    assert any("capacity" in x for x in q)
    assert any("bore" in x for x in q)
    assert len(D["not_published"]["searched"]) >= 5


def test_the_bearing_load_prices_what_d6_cannot_compute():
    """Finding 270. The No. 3 bearing carries the residual of the HP
    rotor's axial terms, so the published load bounds the terms D6 has no
    geometry for -- the HPT disc faces, the balance piston and the CDP
    seal cavities -- at about half a meganewton.
    """
    d = what_the_bearing_load_says_about_d6()
    assert d["known_sum_kN"] > 0
    assert d["unmodelled_kN"] > 400          # kN, and it is the missing half
    assert d["bearing_as_pct_of_known"] < 15


def test_the_measured_edge_crossing_reproduces_the_printed_axis_top():
    """The calibration is fitted to the labelled gridlines; the value it
    returns at the box edge is the printed 44.5 kN, which the fit was not
    given. 0.2 % -- a closure on the grid location, not a reading.
    """
    e = D["no3_hp_thrust_bearing"]["box_edge"]
    assert abs(e["measured_from_calibration_kN"] - e["load_kN"]) < 0.15
