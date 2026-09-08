"""Stage G unit G1: solid blade geometry
(solvers/geometry/STEP0.md unit G1).

Building all 32 rows takes three minutes, which is `python build.py`'s job,
not the test suite's. These take a representative four: the two highest
chord-to-radius rows, the row whose section counts exposed finding 114, and
one with only three transcribed sections."""
import math
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))
cq = pytest.importorskip("cadquery")

from geometry.blades import (  # noqa: E402
    _arc_resample, _decimate, all_rows, fan_rows, hpc_rows, interference_check,
    loft_capped, lpt_rows, volume_check, wrapped_wire,
)
from OCP.BRepCheck import BRepCheck_Analyzer  # noqa: E402

SAMPLE_NAMES = {"hpc-rotor-1", "fan-rotor", "lpt-stator-5", "lpt-rotor-1"}
ROWS = all_rows()          # built once: the section data, not the solids


@pytest.fixture(scope="module")
def sample():
    return [r for r in ROWS if r.name in SAMPLE_NAMES]


@pytest.fixture(scope="module")
def checked(sample):
    return {v["row"]: v for v in volume_check(sample)}


# --- the row inventory -----------------------------------------------------

def test_every_bladed_row_with_sections_is_generated():
    rows = ROWS
    assert len(rows) == 32
    assert len(fan_rows()) == 2 and len(hpc_rows()) == 20 and len(lpt_rows()) == 10
    assert {r.spool for r in rows} == {"lp", "hp", "static"}
    assert all(r.count > 0 for r in rows)
    assert len(SAMPLE_NAMES - {r.name for r in rows}) == 0


def test_pf06s_stated_validity_condition_fails_on_this_engine():
    """which is why unit G1 wraps conformally instead of stacking planar
    sections -- PF-06 says the planar offset is 'valid because chord is
    small next to radius'"""
    by = {r.name: r.chord_over_radius for r in ROWS}
    assert by["hpc-rotor-1"] > 0.45
    assert by["fan-rotor"] > 0.40
    assert max(by.values()) > 0.45


# --- resampling: finding 114 ----------------------------------------------

def test_arc_resample_is_uniform_along_a_straight_line():
    pts = _arc_resample([(0.0, 0.0), (1.0, 0.0)], 5)
    assert len(pts) == 5
    for i, (x, _) in enumerate(pts):
        assert x == pytest.approx(i / 4)


def test_every_section_of_every_row_resamples_to_the_same_point_count():
    """finding 114 -- 92 edges against 93 was enough to stop a loft"""
    for row in ROWS:
        counts = {len(_decimate(s)) for s in row.sections}
        assert len(counts) == 1, f"{row.name} gave {counts}"


def test_duplicate_coordinates_in_the_appendix_are_dropped_at_the_geometry():
    """finding 114 -- the transcription still says what the report says"""
    from meanline.sections import load_section
    from mechanical.beam import closed_airfoil
    raw = closed_airfoil(load_section("R1", 10))
    dup = sum(1 for a, b in zip(raw, raw[1:]) if math.dist(a, b) < 1e-12)
    assert dup > 0                                   # the report really does repeat one
    out = _decimate([(x * 0.0254, y * 0.0254) for x, y in raw])
    assert all(math.dist(a, b) > 1e-6 for a, b in zip(out, out[1:]))


# --- the cap: finding 113 --------------------------------------------------

def test_an_uncapped_wrapped_loft_reports_two_thirds_of_its_volume():
    """finding 113 -- a flat rectangle wrapped through 1.5 degrees. OCC
    returns something that calls itself a Solid and whose volume is wrong,
    and nothing raises."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
    dx, dy, r0, r1 = 0.0929, 0.005, 0.1907, 0.2049

    def rect(r, n=40):
        pts = ([(dx * i / n, 0.0) for i in range(n)]
               + [(dx, dy * i / n) for i in range(n)]
               + [(dx * (1 - i / n), dy) for i in range(n)]
               + [(0.0, dy * (1 - i / n)) for i in range(n)])
        return cq.Workplane().polyline(
            [(x, r * math.sin(y / r), r * math.cos(y / r)) for x, y in pts]).close().wire().val()

    exact = dx * dy * (r1 - r0)
    lo = BRepOffsetAPI_ThruSections(True, True)
    for w in (rect(r0), rect(r1)):
        lo.AddWire(w.wrapped)
    lo.Build()
    open_solid = cq.Shape.cast(lo.Shape())
    assert open_solid.Volume() / exact == pytest.approx(2 / 3, abs=0.01)
    assert not BRepCheck_Analyzer(open_solid.wrapped).IsValid()
    assert not open_solid.Shells()[0].wrapped.Closed()

    capped = loft_capped([rect(r0), rect(r1)])
    assert capped.Volume() == pytest.approx(exact, rel=1e-4)
    assert BRepCheck_Analyzer(capped.wrapped).IsValid()


# --- the rows themselves ---------------------------------------------------

def test_the_sampled_rows_build_as_valid_solids(checked):
    assert set(checked) == SAMPLE_NAMES
    assert all(v["valid"] for v in checked.values())


def test_the_cad_volume_matches_stage_f2s_integral(checked):
    """finding 115 -- the wrap is exactly volume-preserving in arc-length
    coordinates, so this tests the CAD and not the aerodynamics"""
    assert max(abs(v["err_pct"]) for v in checked.values()) < 2.0


def test_the_residual_is_the_polyhedral_approximation_it_should_be(checked):
    """twelve sections at low chord/radius do better than three sections
    or a 0.49 chord/radius"""
    assert abs(checked["hpc-rotor-1"]["err_pct"]) > abs(checked["lpt-rotor-1"]["err_pct"]) / 3
    assert all(v["err_pct"] < 0.5 for v in checked.values())


def test_no_blade_touches_its_neighbour(sample):
    """finding 116 -- Stage G's sixth bullet, on the sampled rows"""
    for i in interference_check(sample):
        assert i["overlap_m3"] == 0.0
        assert 2.0 < i["pitch_deg"] < 15.0


def test_a_wrapped_wire_lies_on_its_own_cylinder():
    row = next(r for r in ROWS if r.name == "hpc-rotor-1")
    r0 = row.radii[0]
    w = wrapped_wire(r0, row.sections[0])
    for v in w.Vertices():
        assert math.hypot(v.Y, v.Z) == pytest.approx(r0, rel=1e-9)


# --- build.py --------------------------------------------------------------

def test_build_py_lists_every_stage_and_every_runnable_module():
    p = subprocess.run([sys.executable, "build.py", "--list"], cwd=ROOT,
                       capture_output=True, text=True)
    assert p.returncode == 0
    assert "35 modules" in p.stdout
    for stage in ("B  cycle", "C1 mean-line", "D  thermal", "F  materials",
                  "G  geometry", "I  verification", "J  publication"):
        assert stage in p.stdout


def test_build_py_produces_no_gated_number():
    """there is no basic-engine mass and no CFD here; a build script that
    filled those in would be manufacturing agreement"""
    text = (ROOT / "build.py").read_text()
    assert "3473" not in text and "3,473" not in text
    assert "gated" in text
