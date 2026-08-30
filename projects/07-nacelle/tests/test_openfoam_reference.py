"""The real, transcribed NASA TM 110300 data (openfoam/reference_data.py)
and the CST fit against it (openfoam/fit_reference_geometry.py). No pyOCC —
this only exercises cst.py and fit.py, both already pyOCC-free."""

from __future__ import annotations

import pytest

from openfoam.fit_reference_geometry import (
    CST_ORDER,
    fit_target_curve,
    length_m,
    target_points_m,
)
from openfoam.reference_data import (
    EXTERNAL_ORDINATES_PERCENT,
    FOREBODY_CP_TOP,
    L_INCHES,
    RMAX_INCHES,
    REYNOLDS_PER_FOOT_RANGE,
)


def test_external_ordinates_start_at_the_highlight():
    """X/L=0, R/RMAX=85.36% is the highlight (lip) — the report's own
    starting point, not an assumption of this project's."""
    x_l, r_rmax = EXTERNAL_ORDINATES_PERCENT[0]
    assert x_l == 0.0
    assert r_rmax == pytest.approx(85.36)


def test_external_ordinates_end_at_the_max_radius_station():
    x_l, r_rmax = EXTERNAL_ORDINATES_PERCENT[-1]
    assert x_l == pytest.approx(100.0)
    assert r_rmax == pytest.approx(100.0)


def test_external_ordinates_are_monotonically_increasing():
    """Both X/L and R/RMAX only increase along the table — the defining
    shape of an external cowl generatrix from lip to max-diameter station,
    checked directly on the transcribed data rather than assumed true of
    it."""
    x_values = [x for x, _ in EXTERNAL_ORDINATES_PERCENT]
    r_values = [r for _, r in EXTERNAL_ORDINATES_PERCENT]
    assert x_values == sorted(x_values)
    assert r_values == sorted(r_values)


def test_reynolds_per_foot_range_is_physically_ordered():
    lo, hi = REYNOLDS_PER_FOOT_RANGE
    assert 0 < lo < hi


def test_forebody_cp_stagnation_region_is_near_one():
    """Cp approaches 1.0 near a stagnation point — the physical identity
    every Cp table has to satisfy near the highlight, at low mass-flow
    ratio the stagnation point sits just inside the highlight (still
    visible in this forebody trace) rather than exactly on it."""
    near_stagnation = [cp for x_l, cp in FOREBODY_CP_TOP if -1.0 <= x_l <= 0.0]
    assert max(near_stagnation) > 0.85


def test_forebody_cp_suction_peak_is_negative_and_pronounced():
    """The classic external-cowl suction peak just aft of the highlight —
    a real, physical feature of this flow, not a transcription artifact:
    it appears at the same stations in every mfr block on the source
    page, growing more negative as mfr (and therefore local acceleration
    around the lip) increases."""
    peak = min(cp for _, cp in FOREBODY_CP_TOP)
    assert peak < -1.0


# ── CST fit to the real target geometry ─────────────────────────────────


def test_target_points_convert_units_correctly():
    """psi=0 -> r0, psi=1 -> r1, in metres, matching L_INCHES/RMAX_INCHES
    converted by the standard inch-to-metre factor — checked as an
    independent unit conversion, not just trusted from the fit."""
    points = target_points_m()
    assert points[0][0] == pytest.approx(0.0)
    assert points[-1][0] == pytest.approx(1.0)
    assert points[0][1] == pytest.approx(0.8536 * RMAX_INCHES * 0.0254, rel=1e-6)
    assert points[-1][1] == pytest.approx(RMAX_INCHES * 0.0254, rel=1e-6)


def test_length_matches_the_report():
    assert length_m() == pytest.approx(L_INCHES * 0.0254)


def test_fitted_curve_endpoints_match_the_target_exactly():
    """CSTCurve's class function vanishes at psi=0 and psi=1 by
    construction, so the fitted curve's endpoints have to equal the
    target's exactly regardless of fit quality in between — checked
    directly, not assumed from CSTCurve's docstring."""
    points = target_points_m()
    curve = fit_target_curve()
    assert curve(0.0) == pytest.approx(points[0][1])
    assert curve(1.0) == pytest.approx(points[-1][1])


def test_fitted_curve_reproduces_the_target_to_a_fraction_of_a_percent():
    """The actual accuracy number this benchmarking exercise exists to
    report — order 8 recovers this real external cowl shape to well
    under 0.1% of the max radius, not just 'close enough to look right'
    on a plot."""
    from src.fit import fit_residual

    points = target_points_m()
    curve = fit_target_curve()
    residual = fit_residual(points, curve)
    assert residual / curve.r1 < 0.001


def test_fit_order_is_high_enough_to_actually_be_tested():
    assert CST_ORDER >= 6


# ── Freestream conditions, back-solved to match the report's stated Re ──


def test_freestream_state_reproduces_the_target_reynolds_number():
    """The actual point of freestream_conditions.py: whatever static
    pressure it solves for has to give back exactly the Reynolds number
    per foot it was solved to match — checked directly by recomputing
    Re/ft from the solved state via the independent reynolds_per_foot
    function, not just trusted from the root-finder converging."""
    from openfoam.freestream_conditions import freestream_state, reynolds_per_foot

    state = freestream_state(mach=0.79, target_reynolds_per_foot=3.7e6)
    recomputed = reynolds_per_foot(state["pressure_pa"], state["temperature_k"], state["mach"])
    assert recomputed == pytest.approx(3.7e6, rel=1e-6)


def test_freestream_velocity_matches_mach_times_sound_speed():
    from openfoam.freestream_conditions import freestream_state

    state = freestream_state(mach=0.79, target_reynolds_per_foot=3.7e6)
    assert state["velocity_m_s"] == pytest.approx(
        state["mach"] * state["sound_speed_m_s"]
    )


def test_higher_target_reynolds_number_needs_higher_pressure():
    """Re scales linearly with density at fixed T and M, and density with
    pressure at fixed T — so a higher target Re/ft must be solved by a
    higher pressure, not a coincidence of the root-finder."""
    from openfoam.freestream_conditions import static_pressure_for_target_reynolds

    lo = static_pressure_for_target_reynolds(3.2e6, mach=0.79)
    hi = static_pressure_for_target_reynolds(4.2e6, mach=0.79)
    assert hi > lo


def test_dynamic_viscosity_matches_a_known_air_value_near_room_temperature():
    """Sutherland's law at 288.15 K should land close to the textbook
    figure for air's dynamic viscosity at that temperature, ~1.79e-5 Pa*s
    — an independent sanity check on the Sutherland constants used, not
    just that the formula runs."""
    from openfoam.freestream_conditions import dynamic_viscosity

    assert dynamic_viscosity(288.15) == pytest.approx(1.79e-5, rel=0.02)


# ── CFD surface geometry (pyOCC-free parts only) ────────────────────────


def test_open_shell_points_extend_the_cowl_with_a_cylindrical_afterbody():
    """Every afterbody point sits at exactly the trailing radius (a
    cylinder, constant radius) and strictly beyond the cowl's own length
    — the geometric claim the module docstring makes about matching NASA
    TM 110300's real test article, checked directly."""
    from openfoam.generate_stl import _open_shell_points, build_external_profile

    profile = build_external_profile()
    points = _open_shell_points(profile)
    cowl_points = [p for p in points if p[0] <= profile.length]
    afterbody_points = [p for p in points if p[0] > profile.length]

    assert len(cowl_points) == len(profile.meridian_points())
    assert len(afterbody_points) > 0
    assert all(r == pytest.approx(profile.trailing_radius) for _, r in afterbody_points)
    assert all(x > profile.length for x, _ in afterbody_points)


def test_open_shell_points_reach_past_the_furthest_comparison_station():
    """reference_data.FOREBODY_CP_TOP's furthest station is X/L=139% —
    the geometry has to extend past that with margin, or the comparison
    script would have nothing to sample at the last few stations."""
    from openfoam.generate_stl import _open_shell_points, build_external_profile

    profile = build_external_profile()
    points = _open_shell_points(profile)
    furthest_x_over_l_pct = (points[-1][0] / profile.length) * 100.0
    furthest_target_pct = max(x_l for x_l, _ in FOREBODY_CP_TOP)
    assert furthest_x_over_l_pct > furthest_target_pct


def test_axial_pressure_trace_averages_all_circumferential_faces_per_station():
    """Synthetic rows standing in for a real raw-surface sample. Superseded
    an earlier top-meridian-only filter (kept only faces near y=0, z>0)
    after a real solve showed cowlAndAfterbody has only ~27 faces around
    the circumference -- a tight y~0 band matched 1 face out of 1252.
    This case is axisymmetric at alpha=0 deg, so averaging over ALL
    circumferential faces at each axial station is both more robust to that
    coarse resolution and physically justified (Cp should be circumferentially
    uniform there) -- see axial_pressure_trace's docstring."""
    from openfoam.compare_to_reference import axial_pressure_trace

    rows = [
        (0.10, 0.0, 0.05, 1000.0),   # station ~0.10, one face
        (0.20, 0.001, 0.06, 1000.0),  # station ~0.20, face A
        (0.20, 0.0, -0.05, 1020.0),  # station ~0.20, face B (opposite side)
        (0.40, 0.05, 0.02, 1030.0),  # station ~0.40, one face
    ]
    trace = axial_pressure_trace(rows)
    assert trace == [
        (0.10, 1000.0),
        (0.20, 1010.0),  # average of the two faces at this station
        (0.40, 1030.0),
    ]


def test_axial_pressure_trace_is_sorted_by_x():
    from openfoam.compare_to_reference import axial_pressure_trace

    rows = [(0.30, 0.0, 0.05, 3.0), (0.10, 0.0, 0.05, 1.0), (0.20, 0.0, 0.05, 2.0)]
    trace = axial_pressure_trace(rows)
    assert [x for x, _ in trace] == [0.10, 0.20, 0.30]


def test_to_cp_matches_the_definition_directly():
    from openfoam.compare_to_reference import to_cp

    p_inf, rho_inf, v_inf = 66829.5, 0.80796, 268.83
    q_inf = 0.5 * rho_inf * v_inf ** 2
    pressures = [(0.0, p_inf + q_inf), (1.0, p_inf - q_inf)]
    cp = to_cp(pressures, p_inf, rho_inf, v_inf)
    assert cp[0] == (0.0, pytest.approx(1.0))
    assert cp[1] == (1.0, pytest.approx(-1.0))


def test_interpolate_matches_a_hand_worked_linear_case():
    from openfoam.compare_to_reference import interpolate

    trace = [(0.0, 0.0), (10.0, 100.0)]
    assert interpolate(trace, 2.5) == pytest.approx(25.0)


def test_interpolate_returns_none_outside_the_trace_range():
    """Extrapolating silently would make a missing region of the solved
    surface look like agreement or disagreement with the reference by
    accident -- returning None and letting the caller print '--' is the
    honest behaviour."""
    from openfoam.compare_to_reference import interpolate

    trace = [(0.0, 0.0), (10.0, 100.0)]
    assert interpolate(trace, -1.0) is None
    assert interpolate(trace, 11.0) is None


def test_compare_reports_zero_error_when_model_exactly_matches_reference():
    """A model trace built by walking reference_data.FOREBODY_CP_TOP's own
    stations exactly has to compare against itself with zero error at
    every station -- the identity check on compare()'s own arithmetic."""
    from openfoam.compare_to_reference import compare

    l_m = L_INCHES * 0.0254
    exact_trace = [((x_l / 100.0) * l_m, cp) for x_l, cp in FOREBODY_CP_TOP]
    result = compare(exact_trace)
    for row in result["stations"]:
        assert row["cp_model"] is not None
        assert row["error"] == pytest.approx(0.0, abs=1e-9)


def test_disc_stl_is_well_formed_ascii_stl():
    """write_disc_stl needs no pyOCC — checked here that its output is
    valid enough for a mesher to read: matching solid/endsolid names, one
    vertex triple per facet, and every vertex sitting at exactly x and
    radius `radius` from the axis (not just approximately circular)."""
    import math
    import tempfile
    from pathlib import Path

    from openfoam.generate_stl import write_disc_stl

    with tempfile.TemporaryDirectory() as tmp:
        path = write_disc_stl(Path(tmp) / "disc.stl", x=0.5, radius=0.2, n=16)
        text = path.read_text()

    assert text.startswith("solid highlightInlet")
    assert text.strip().endswith("endsolid highlightInlet")
    assert text.count("facet normal 1 0 0") == 16
    assert text.count("vertex") == 16 * 3

    for line in text.splitlines():
        if not line.strip().startswith("vertex"):
            continue
        _, x, y, z = line.split()
        x, y, z = float(x), float(y), float(z)
        assert x == pytest.approx(0.5)
        distance_from_axis = math.hypot(y, z)
        assert distance_from_axis == pytest.approx(0.0, abs=1e-6) or \
            distance_from_axis == pytest.approx(0.2, rel=1e-6)
