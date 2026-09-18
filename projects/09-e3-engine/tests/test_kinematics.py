"""Unit H4 -- the assembly's kinematics.

Bands written into solvers/geometry/STEP0.md before the module existed.
The geometry half needs the CAD kernel and declares it; the engine-order
half does not and runs everywhere.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from geometry import kinematics as K      # noqa: E402


# --- bands 3 and 4 need no geometry -----------------------------------------

def test_band3_one_lp_hp_ratio_everywhere():
    r = K.ratio_routes()
    assert abs(r["gltf"] / r["four_route"] - 1.0) < 0.005


def test_band4_every_rotor_carries_its_downstream_stator_order():
    rows = K.hpc_campbell_orders()
    assert len(rows) == 10
    assert all(x["downstream_present"] for x in rows)


def test_band4_every_rotor_but_the_first_carries_its_upstream_order():
    rows = K.hpc_campbell_orders()
    assert sum(x["upstream_present"] for x in rows) == 9
    missing = [x["stage"] for x in rows if not x["upstream_present"]]
    assert missing == [1]                      # and it is the IGV
    assert rows[0]["upstream"] == 32


def test_band4_the_hpt_blade_campbell_carries_the_lpt_vane_count():
    L = K.lpt_order_on_the_hpt_blade()
    assert L["equal"] and L["lpt_assembly"] == 72


# --- bands 1, 2 and 5 need the assembly -------------------------------------

@pytest.fixture(scope="module")
def _cq():
    pytest.importorskip("cadquery")


def test_band1_no_pair_of_rows_overlaps_axially(_cq):
    """the closure, as a proof rather than a sample: two rows that share no
    axial interval cannot touch at ANY relative angular position"""
    assert K.overlapping_pairs() == []


def test_band2_the_sweep_finds_the_same_gap_at_every_angle(_cq):
    s = K.sweep_is_redundant(steps=360)
    assert s["spread_mm"] == 0.0
    assert s["min_gap_mm"] > 0.0


def test_band5_every_placed_row_has_a_blade_passing_frequency(_cq):
    b = K.blade_passing()
    assert len(b) == 32
    assert all(x["bpf_hz"] > 0 for x in b if x["spool"] in ("lp", "hp"))
