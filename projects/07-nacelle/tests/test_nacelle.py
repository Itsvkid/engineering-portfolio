"""NacelleSolid: kernel geometry checked against profile.py's independent
integration. Needs pyOCC — run inside pyocc_env."""

from __future__ import annotations

import math

import pytest
from OCC.Core.BRepCheck import BRepCheck_Analyzer

from src.cst import CSTCurve
from src.nacelle import CompleteNacelle, NacelleSolid
from src.profile import NacelleProfile


def make_solid(**overrides) -> NacelleSolid:
    curve_kwargs = dict(r0=0.85, r1=0.60, weights=(0.6, 0.9, 0.5))
    curve_kwargs.update(overrides.pop("curve", {}))
    profile_kwargs = dict(length=3.0)
    profile_kwargs.update(overrides)
    return NacelleSolid(NacelleProfile(curve=CSTCurve(**curve_kwargs), **profile_kwargs))


def make_complete_nacelle(length=3.0) -> CompleteNacelle:
    external = NacelleProfile(length=length, curve=CSTCurve(r0=0.85, r1=0.60, weights=(0.6, 0.9, 0.5)))
    internal = NacelleProfile(length=length, curve=CSTCurve(r0=0.75, r1=0.50, weights=(0.55, 0.65, 0.45)))
    return CompleteNacelle(external=external, internal=internal)


def test_build_produces_a_valid_solid():
    solid = make_solid()
    assert BRepCheck_Analyzer(solid.build()).IsValid()


def test_measured_volume_matches_predicted_volume():
    """The independent-route check this whole project exists to run: the
    kernel's revolved solid and profile.py's disk-integration share no
    code, so agreement here means the geometry is actually what the
    parameters describe."""
    solid = make_solid()
    measured = solid.measured_volume()
    predicted = solid.profile.predicted_volume()
    assert measured == pytest.approx(predicted, rel=1e-3)


def test_measured_surface_area_matches_predicted_total():
    solid = make_solid()
    measured = solid.measured_surface_area()
    predicted = solid.profile.predicted_total_surface_area()
    assert measured == pytest.approx(predicted, rel=1e-2)


def test_cylinder_limiting_case_kernel_volume_matches_closed_form():
    """Same limiting case test_profile.py runs on the integration route,
    run here on the kernel — a cylinder is exact by construction, so the
    revolved solid's volume has to match pi*R^2*L too, not just agree with
    the (potentially also-wrong) prediction."""
    R, L = 0.9, 3.0
    solid = make_solid(curve={"r0": R, "r1": R, "weights": (0.0, 0.0, 0.0)},
                        length=L)
    assert solid.measured_volume() == pytest.approx(math.pi * R**2 * L, rel=1e-3)


def test_volume_is_repeatable():
    solid = make_solid()
    v1 = solid.measured_volume()
    v2 = solid.measured_volume()
    assert v1 == pytest.approx(v2)


def test_more_bulge_gives_more_measured_volume():
    small = make_solid(curve={"r0": 0.8, "r1": 0.6, "weights": (0.2, 0.2, 0.2)})
    big = make_solid(curve={"r0": 0.8, "r1": 0.6, "weights": (1.0, 1.0, 1.0)})
    assert big.measured_volume() > small.measured_volume()


# ── CompleteNacelle: external cowl + internal duct as a hollow solid ─────


def test_complete_nacelle_rejects_a_self_intersecting_pair():
    """The same crossing test_profile.py's internal_clearance_ok test runs
    on the arithmetic, run here on the class that actually has to build a
    solid from it — the constructor should refuse before ever reaching
    BRepPrimAPI_MakeRevol, not produce a shape that IsValid() then has to
    catch."""
    external = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.7, r1=0.7, weights=(0.0,)))
    internal = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.5, r1=0.4, weights=(2.0, 2.0, 2.0)))
    with pytest.raises(ValueError):
        CompleteNacelle(external=external, internal=internal)


def test_complete_nacelle_build_produces_a_valid_solid():
    nacelle = make_complete_nacelle()
    assert BRepCheck_Analyzer(nacelle.build()).IsValid()


def test_complete_nacelle_measured_volume_matches_predicted_material_volume():
    """The independent-route check this class exists to run, same as
    NacelleSolid's: the kernel's revolved hollow solid and profile.py's
    external-minus-internal integration share no code."""
    nacelle = make_complete_nacelle()
    assert nacelle.measured_volume() == pytest.approx(
        nacelle.predicted_material_volume(), rel=1e-3
    )


def test_complete_nacelle_measured_surface_matches_predicted_total():
    nacelle = make_complete_nacelle()
    assert nacelle.measured_surface_area() == pytest.approx(
        nacelle.predicted_total_surface_area(), rel=1e-2
    )


def test_complete_nacelle_concentric_cylinders_kernel_volume_matches_closed_form():
    """Same limiting case as NacelleSolid's cylinder test, run on the
    hollow-shell kernel: two concentric cylindrical tubes revolve into a
    perfect annular cylinder, volume pi*(R_ext^2 - R_int^2)*L exactly."""
    R_ext, R_int, L = 0.9, 0.6, 3.0
    external = NacelleProfile(length=L, curve=CSTCurve(r0=R_ext, r1=R_ext, weights=(0.0,)))
    internal = NacelleProfile(length=L, curve=CSTCurve(r0=R_int, r1=R_int, weights=(0.0,)))
    nacelle = CompleteNacelle(external=external, internal=internal)
    expected = math.pi * (R_ext**2 - R_int**2) * L
    assert nacelle.measured_volume() == pytest.approx(expected, rel=1e-3)


def test_complete_nacelle_volume_less_than_solid_cowl_volume():
    """Sanity check with real physical meaning, not just numerical
    self-consistency: hollowing out the cowl to add a duct must reduce the
    amount of material, not increase it."""
    solid = make_solid()
    hollow = make_complete_nacelle()
    assert hollow.measured_volume() < solid.measured_volume()
