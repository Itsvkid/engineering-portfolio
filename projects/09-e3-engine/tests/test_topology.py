"""The engine's topology, asserted rather than assumed.

A turbofan's gas path is a straight line and its shafts cross it. Both facts
are easy to state and easy to get wrong in a way that still produces a
plausible-looking model: pair the HPC with the LP turbine and every work
split is wrong, but nothing looks odd until the stage counts come out absurd.

So the topology lives in `data/e3-fps-published.yaml` as data, and these
tests hold it to three things:

  1. the gas path is in flow order, by station number;
  2. every component on a spool is on the gas path, and each spool's turbine
     sits downstream of the compressors it drives;
  3. the ordering agrees with `Stations` in projects/08-cycle-model, which is
     the other place in this portfolio that encodes the same architecture.

Runs on a plain interpreter -- yaml only, no pyOCC, no CadQuery.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data" / "e3-fps-published.yaml"
CYCLE_SRC = (
    pathlib.Path(__file__).resolve().parents[2]
    / "08-cycle-model" / "src" / "cycle.py"
)


@pytest.fixture(scope="module")
def published():
    return yaml.safe_load(DATA.read_text())


@pytest.fixture(scope="module")
def topology(published):
    return published["topology"]


def station_order(station: int) -> float:
    """Aero-engine station numbers are hierarchical, not linear.

    A multi-digit station is a SUB-station of its first digit: 21 and 25 sit
    between 2 and 3, and 45 sits between 4 and 5. So the sequence
    2, 21, 25, 3, 4, 45, 5, 8 is in flow order even though it is not
    numerically ascending -- read it as 2, 2.1, 2.5, 3, 4, 4.5, 5, 8.

    This function was written because the first version of the test below
    sorted the raw integers and failed on correct data. The convention was
    the thing that was wrong, not the engine.
    """
    text = str(station)
    return float(text[0]) if len(text) == 1 else float(f"{text[0]}.{text[1:]}")


def test_station_order_reads_substations_correctly():
    """Guard the guard: the helper above is the assumption everything else
    in this file rests on."""
    assert station_order(2) == 2.0
    assert station_order(21) == 2.1
    assert station_order(25) == 2.5
    assert station_order(45) == 4.5
    assert station_order(2) < station_order(21) < station_order(25) < station_order(3)
    assert station_order(4) < station_order(45) < station_order(5)


def test_the_core_gas_path_is_in_flow_order(topology):
    """Stations advance along the core. A pair that goes backwards means two
    components have been transposed."""
    stations = [step["station"] for step in topology["gas_path"]]
    keys = [station_order(s) for s in stations]
    assert keys == sorted(keys), (
        f"core gas path is out of order: {stations} reads as {keys}. "
        "Components are transposed somewhere in topology.gas_path."
    )


def test_the_core_runs_compressors_then_combustor_then_turbines(topology):
    """The ordering the question always comes down to: LPC, HPC, combustor,
    HPT, LPT."""
    order = [step["component"] for step in topology["gas_path"]]
    for earlier, later in [
        ("fan", "booster"),
        ("booster", "hpc"),
        ("hpc", "combustor"),
        ("combustor", "hpt"),
        ("hpt", "lpt"),
        ("lpt", "nozzle"),
    ]:
        assert order.index(earlier) < order.index(later), (
            f"{earlier!r} must come before {later!r} in the gas path, "
            f"got {order}"
        )


def test_the_bypass_stream_leaves_the_fan_and_rejoins_at_the_mixer(topology):
    """E3 is mixed-flow, so the bypass path must start at the fan and end
    where the core ends, not at a nozzle of its own."""
    bypass = [step["component"] for step in topology["bypass_path"]]
    assert bypass[0] == "fan", f"bypass must start at the fan, got {bypass}"
    assert bypass[-1] == "mixer", (
        f"E3 mixes core and bypass; the bypass path must end at the mixer, "
        f"got {bypass}"
    )


def test_the_spools_are_crossed_the_way_a_twin_spool_actually_is(topology):
    """The LP spool takes the FIRST compressors and the LAST turbine; the HP
    spool takes the ones in the middle. Reversing this is the error these
    tests exist to catch."""
    spools = topology["spools"]
    assert spools["lp"]["driven_by"] == "lpt"
    assert spools["hp"]["driven_by"] == "hpt"
    assert set(spools["lp"]["drives"]) == {"fan", "booster"}
    assert set(spools["hp"]["drives"]) == {"hpc"}

    # And no component may sit on both shafts.
    lp, hp = set(spools["lp"]["drives"]), set(spools["hp"]["drives"])
    assert not (lp & hp), f"component on both spools: {lp & hp}"


def test_each_turbine_sits_downstream_of_what_it_drives(topology):
    """A turbine extracts work downstream of the compressor it powers. True
    of both spools, and it is what makes the crossed arrangement physical."""
    order = [step["component"] for step in topology["gas_path"]]
    for spool in topology["spools"].values():
        turbine = spool["driven_by"]
        for compressor in spool["drives"]:
            assert order.index(compressor) < order.index(turbine), (
                f"{turbine!r} drives {compressor!r} but does not sit "
                f"downstream of it in {order}"
            )


def test_every_spool_component_is_on_the_gas_path(topology):
    on_path = {step["component"] for step in topology["gas_path"]}
    for name, spool in topology["spools"].items():
        for component in [*spool["drives"], spool["driven_by"]]:
            assert component in on_path, (
                f"{component!r} is on the {name.upper()} spool but appears "
                f"nowhere in the gas path"
            )


def test_the_power_balance_pairs_match_the_spools(topology):
    """The power-balance block is a second, independent statement of the same
    pairing. If the two disagree, one was edited and the other was not."""
    from_spools = {
        spool["driven_by"]: set(spool["drives"])
        for spool in topology["spools"].values()
    }
    for pair in topology["power_balance"]:
        driven = pair["compressor"]
        driven = {driven} if isinstance(driven, str) else set(driven)
        assert from_spools[pair["turbine"]] == driven, (
            f"power_balance says {pair['turbine']!r} drives {driven}, "
            f"spools say {from_spools[pair['turbine']]}"
        )


def test_the_ordering_agrees_with_the_cycle_model(topology):
    """PF-08 encodes the same architecture in its `Stations` dataclass. These
    are two independent statements of one fact, which is the only reason
    checking them against each other is worth anything."""
    source = CYCLE_SRC.read_text()
    body = source.split("class Stations:", 1)[1].split("@dataclass", 1)[0]

    # Field order as declared, e.g. "    booster_exit: Station"
    fields = [
        line.split(":", 1)[0].strip()
        for line in body.splitlines()
        if line.startswith("    ") and ":" in line and not line.strip().startswith("#")
    ]
    core = [f for f in fields if f in {
        "fan_face", "booster_exit", "hpc_exit",
        "combustor_exit", "hpt_exit", "lpt_exit",
    }]
    assert core == [
        "fan_face", "booster_exit", "hpc_exit",
        "combustor_exit", "hpt_exit", "lpt_exit",
    ], f"PF-08's station order has changed: {core}"

    ours = [s["component"] for s in topology["gas_path"]]
    assert ours.index("booster") < ours.index("hpc") < ours.index("combustor")
    assert ours.index("combustor") < ours.index("hpt") < ours.index("lpt")


def test_the_booster_is_not_quietly_missing(published):
    """The booster was omitted from the first draft of the architecture block.
    It is a real component on the LP spool: leave it out and the LP power
    balance is wrong and the HPC inlet lands at the wrong radius.

    Its stage count is not yet established, so this asserts the gap is
    RECORDED rather than that it is filled.
    """
    booster = published["architecture"]["booster_lpc_stages"]
    assert "settle_at" in booster, (
        "booster stage count is unknown; the entry must say where to settle it"
    )
    if booster["value"] is None:
        assert booster["verified"] is False
    else:
        assert booster["value"] > 0


def test_unverified_values_are_labelled_not_guessed(published):
    """Anything not yet read in the source must say so and say where to look."""
    for name, value in published["architecture"].items():
        if isinstance(value, dict) and value.get("verified") is False:
            assert value.get("settle_at"), (
                f"{name!r} is unverified but does not say where to settle it"
            )
