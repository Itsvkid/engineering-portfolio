"""Stage G unit G3: the whole engine as one STEP assembly
(solvers/geometry/STEP0.md unit G3).

Lofting all 32 rows takes about three minutes, which is `python build.py`'s
job rather than the suite's, so the geometry tests here take a subset and
the cheap tests -- the layout, the provenance in the names, the published
length -- take all of it, because none of those needs a solid.

The failure mode this unit exists to prevent is a STEP file that imports as
thirty-two unrelated solids at the origin. The test for that is to write a
file and read it back."""
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))
pytest.importorskip("cadquery")

from geometry import assembly as A  # noqa: E402
from geometry.blades import lpt_rows  # noqa: E402
from publication.meridional import layout  # noqa: E402


# ------------------------------------------------ the layout, no geometry

def test_the_two_assumed_offsets_have_exactly_one_home():
    """The STEP assembly must not acquire a second copy of the two numbers
    that place the engine. Unit J1's finding 159 is the whole reason this
    module imports `layout()` instead of typing them."""
    src = (ROOT / "solvers" / "geometry" / "assembly.py").read_text()
    body = src.split('"""', 2)[-1]          # past the module docstring
    for literal in ("1.034", "103.4", "0.253", "25.3"):
        assert f"= {literal}" not in body, (
            f"{literal} is typed into assembly.py; it belongs to "
            "engine-flowpath.yaml and reaches here through layout()")


def test_the_offsets_agree_with_the_atlas():
    """`app/turbofan/atlas/flowpath.js` draws the same engine from the same
    two numbers. Two pictures of one engine that disagree would be worse
    than either being wrong."""
    js = (ROOT.parents[1] / "app" / "turbofan" / "atlas" / "flowpath.js").read_text()
    off = layout()["offsets"]
    for const, key in (("HPC0", "fan_sa_to_hpc_r1_le"),
                       ("DIFFUSER_COMBUSTOR", "hpc_ogv_te_to_hpt_vane1")):
        line = [l for l in js.splitlines() if f"export const {const} =" in l][0]
        val_m = float(line.split("=")[1].strip().rstrip(";"))
        assert val_m * 100 == pytest.approx(off[key]["value_cm"], abs=1e-6), const


def test_every_assumed_offset_is_inside_its_own_range():
    off = layout()["offsets"]
    for key in ("fan_sa_to_hpc_r1_le", "hpc_ogv_te_to_hpt_vane1"):
        lo, hi = off[key]["range_cm"]
        assert lo <= off[key]["value_cm"] <= hi, key


def test_the_published_length_is_the_one_in_the_data_file():
    """318.0 cm is CR-159584 Table I's, and it is asserted here against the
    closure block that derives the offsets from it -- so a change to one
    cannot quietly leave the other behind."""
    import yaml
    st = yaml.safe_load((ROOT / "data" / "engine-flowpath.yaml").read_text())
    c = st["whole_engine_stitching"]["assumed_offsets"][
        "closure_against_published_turbomachinery_length"]
    assert str(A.PUBLISHED_TURBOMACHINERY_LENGTH_CM) in c["src"]
    assert A.FAN_FRONT_FLANGE_CM == c["fan_front_flange_cm"]


# ------------------------------------------------------------ provenance

def test_every_wall_declares_whether_it_is_published_or_derived():
    walls = A.published_walls()
    assert {w[0] for w in walls} == {
        "wall-hpc-hub", "wall-hpc-casing", "wall-hpt-hub", "wall-hpt-casing",
        "wall-lpt-hub", "wall-lpt-casing"}
    for name, status, pts in walls:
        assert status in ("published", "derived"), name
        assert len(pts) >= 2
        # the LPT flowpath is derived from the transcribed airfoil
        # coordinates, not printed as a wall; saying otherwise would be the
        # one dishonest label in the file
        assert (status == "derived") == name.startswith("wall-lpt")


def test_no_fan_annulus_is_drawn():
    """Three dimensioned radial stations and one axial position is not a
    contour (unit J1, finding 158). A fan wall would be the only invented
    surface in the file."""
    assert not any(w[0].startswith("wall-fan") for w in A.published_walls())


def test_walls_are_monotone_in_x_and_physically_ordered():
    by = {w[0]: w[2] for w in A.published_walls()}
    for name, pts in by.items():
        xs = [p[0] for p in pts]
        assert xs == sorted(xs), name
        assert all(r > 0 for _, r in pts), name
    for mod in ("hpc", "hpt", "lpt"):
        hub = by[f"wall-{mod}-hub"]
        cas = by[f"wall-{mod}-casing"]
        assert max(r for _, r in hub) < min(r for _, r in cas), mod


def test_the_missing_rows_are_named_with_a_reason():
    """A file that cannot say what it is short of is a file that looks
    complete. Each entry needs a source and a reason, and the IGV's reason
    must be the real one -- its camber is printed as a 65-series design
    lift coefficient, not as metal angles."""
    miss = A.missing_rows()
    assert len(miss) >= 4
    for m in miss:
        assert m["src"] and m["why"] and m["count"] > 0
    igv = [m for m in miss if m["row"] == "hpc-igv"][0]
    assert "cl0" in igv["why"]
    import yaml
    x = yaml.safe_load((ROOT / "data" / "hpc-blade-sections.yaml").read_text())
    assert igv["count"] == x["igv"]["vane_count"]
    assert "cl0" in x["igv"]["columns"], (
        "the IGV's reason for absence is that Table XXII prints cl0 rather "
        "than beta1/beta2; if that column is gone, the reason is gone")


def test_a_row_node_name_carries_its_count_and_its_provenance():
    class R:
        name, count = "hpc-rotor-1", 28
    n = A.row_node_name(R(), "assumed")
    assert "hpc-rotor-1" in n and "n28" in n and "ASSUMED" in n


# ------------------------------------------------------- with geometry

@pytest.fixture(scope="module")
def lpt():
    return lpt_rows()


def test_the_lpt_rows_do_not_overlap_axially(lpt):
    """The ten LPT rows carry their own z from the HPT exit plane, so this
    needs no assumption at all: two rows whose axial extents do not overlap
    cannot interfere at any relative angular position."""
    gaps = A.axial_clearances(lpt)
    assert len(gaps) == 9
    for g in gaps:
        assert g["gap_m"] > 0, (g["upstream"], g["downstream"], g["gap_m"])


def test_the_assembled_length_closes_on_the_published_318_cm(lpt):
    """Measured on the LOFTED rotor-5 blade, not on the CSV the offsets
    were calibrated through. The LPT rows alone suffice: rotor 5's station
    already carries both assumed offsets."""
    L = A.assembled_length(lpt)
    assert L["met"], L
    assert abs(L["err_cm"]) <= A.LENGTH_BAND_CM


def test_the_step_reimports_as_a_tree_and_not_as_loose_solids(lpt, tmp_path):
    """The stated failure mode. `STEPCAFControl_Reader` honours the product
    structure; the plain reader flattens it, which is the difference."""
    p = A.export(path=tmp_path / "sub.step", rows=lpt[:2])
    st = A.reimport_structure(p)
    assert st["roots"] == 1
    assert st["assemblies"] >= 3          # root, module, and a row node
    names = [t[1] for t in st["tree"]]
    assert names[0].startswith("E3-engine")
    assert any(n.startswith("MODULE-lpt") for n in names)
    assert any("--n" in n and "ASSUMED" in n for n in names)
    assert any("PUBLISHED" in n for n in names)
    # full blade count, not a sector
    inst = sum(1 for n in names if "-blade-" in n)
    assert inst == lpt[0].count + lpt[1].count


def test_blade_instances_share_one_representation(lpt, tmp_path):
    """The reason full blade counts are affordable. A 120-blade row must
    not cost 120 times a 1-blade row; if it does, the writer has stopped
    instancing and every later size claim in this unit is wrong."""
    import copy
    row = lpt[1]
    row.solid()                                  # loft once, share it
    one = A.export(path=tmp_path / "one.step", rows=[row], walls=False)
    sz_full = one.stat().st_size

    solo = copy.copy(row)
    solo.count = 1
    p1 = A.export(path=tmp_path / "solo.step", rows=[solo], walls=False)
    assert sz_full < 1.5 * p1.stat().st_size, (
        f"{row.count} blades cost {sz_full} bytes against "
        f"{p1.stat().st_size} for one -- the STEP writer is copying the "
        "representation rather than instancing it")


def test_placement_is_a_rigid_motion(lpt):
    """G1's interference check re-run on the placed rows. Translation along
    X and rotation about X commute, so this must return what G1 returned --
    it is here because an assembly that quietly applied a scale would show
    up nowhere else."""
    for i in A.placed_interference(lpt[:2]):
        assert i["overlap_m3"] == 0.0, i["row"]


def test_the_front_end_assumption_is_reported_rather_than_hidden(lpt):
    """The fan and booster stations are the only ones no table gives, and
    the module has to say so with a number."""
    fe = A.front_end_placement()
    assert fe["fan_axial_extent_cm"] > 5
    assert fe["shift_if_sa_at_midchord_cm"] < 0
    assert "stacking-axis" in fe["note"] and "mid-chord" in fe["note"]
