"""HPC Table XXII, checked against itself and against Table X.

Twelve sections per row, ~260 rows, eleven numbers each, read off a 1985
scan. The only defence against a mis-read digit is that the table gives
almost every number twice:

  * camber is printed AND beta1* - beta2* is printed -- they must agree;
  * every length is printed in cm AND in inches -- they must agree;
  * the tip and root sections must match Table X's tip and root columns,
    which were transcribed separately, from a different page.

Rows where the PRINTED values disagree are listed in the YAML under
`inconsistent_as_printed` and allowed here by name, so an allowance is a
decision on the record rather than a loosened tolerance.

Plain interpreter -- yaml only.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def xxii():
    return yaml.safe_load((DATA / "hpc-blade-sections.yaml").read_text())


@pytest.fixture(scope="module")
def table_x():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())["hpc"]["rotor_stages"]


def col(xxii, name):
    return xxii["columns"].index(name)


def bladed_rows(xxii):
    """Rotors and stators -- every row that has metal angles."""
    return [("rotor", r) for r in xxii["rotors"]] + [("stator", s) for s in xxii["stators"]]


def allowed(xxii, kind, stage, section, check, column=None):
    """An allowance names the row, the section, the check it fails and --
    for a length check -- which column. Nothing broader."""
    return any(a["row"] == kind and a["stage"] == stage and a["section"] == section
               and a["check"] == check and (column is None or a.get("column") == column)
               for a in xxii.get("inconsistent_as_printed", []))


# ── shape ───────────────────────────────────────────────────────────────

def test_every_bladed_row_has_twelve_sections_of_eleven_values(xxii):
    n = len(xxii["columns"])
    for kind, row in bladed_rows(xxii):
        assert len(row["sections"]) == 12, f"{kind} {row['stage']}: {len(row['sections'])} sections"
        for i, s in enumerate(row["sections"], 1):
            assert len(s) == n, f"{kind} {row['stage']} section {i}: {len(s)} values, expected {n}"


def test_igv_has_twelve_sections_of_its_own_column_count(xxii):
    igv = xxii["igv"]
    assert len(igv["sections"]) == 12
    for s in igv["sections"]:
        assert len(s) == len(igv["columns"])


def test_rotor_stages_run_one_to_ten(xxii):
    assert [r["stage"] for r in xxii["rotors"]] == list(range(1, 11))


# ── two routes to every number ──────────────────────────────────────────

def test_camber_equals_beta1_minus_beta2(xxii):
    c, b1, b2 = col(xxii, "camber"), col(xxii, "beta1"), col(xxii, "beta2")
    bad = []
    for kind, row in bladed_rows(xxii):
        for i, s in enumerate(row["sections"], 1):
            gap = abs((s[b1] - s[b2]) - s[c])
            if gap > 0.06 and not allowed(xxii, kind, row["stage"], i, "camber"):
                bad.append(f"{kind} {row['stage']} section {i}: camber {s[c]}, beta1-beta2 {s[b1]-s[b2]:.2f}")
    assert not bad, "\n".join(bad)


def test_every_allowance_covers_a_real_and_small_disagreement(xxii):
    """An allowance must correspond to an actual disagreement in the data as
    transcribed, and a small one. If a later re-read fixes the row, this
    test says the allowance is stale and should go; if the gap is large, the
    row was mis-read and an allowance is the wrong response."""
    rows = {("rotor", r["stage"]): r for r in xxii["rotors"]}
    rows.update({("stator", s["stage"]): s for s in xxii["stators"]})
    for a in xxii.get("inconsistent_as_printed", []):
        s = rows[(a["row"], a["stage"])]["sections"][a["section"] - 1]
        if a["check"] == "camber":
            gap = abs((s[col(xxii, "beta1")] - s[col(xxii, "beta2")]) - s[col(xxii, "camber")])
            assert 0.06 < gap < 1.0, f"{a}: camber gap {gap:.2f} — revisit"
        elif a["check"] == "length":
            cm, inch = f"{a['column']}_cm", f"{a['column']}_in"
            gap = abs(s[col(xxii, cm)] - s[col(xxii, inch)] * 2.54)
            assert 0.004 < gap < 0.05, f"{a}: length gap {gap:.4f} cm — revisit"
        else:
            raise AssertionError(f"unknown check kind in allowance: {a}")


def test_centimetres_equal_inches_times_2_54(xxii):
    pairs = [("sect_ht_cm", "sect_ht_in"), ("chord_cm", "chord_in")]
    bad = []
    for kind, row in bladed_rows(xxii):
        for i, s in enumerate(row["sections"], 1):
            for cm, inch in pairs:
                got, want = s[col(xxii, cm)], s[col(xxii, inch)] * 2.54
                # inches are printed to 3 dp -> +-0.0005 in = +-0.0013 cm
                if abs(got - want) > 0.004 and not allowed(xxii, kind, row["stage"], i, "length", cm[:-3]):
                    bad.append(f"{kind} {row['stage']} section {i} {cm}: {got} vs {want:.4f}")
    igv = xxii["igv"]
    for i, s in enumerate(igv["sections"], 1):
        for cm, inch in pairs:
            got = s[igv["columns"].index(cm)]
            want = s[igv["columns"].index(inch)] * 2.54
            if abs(got - want) > 0.004:
                bad.append(f"igv section {i} {cm}: {got} vs {want:.4f}")
    assert not bad, "\n".join(bad)


def test_sections_run_tip_to_hub(xxii):
    r = col(xxii, "sect_ht_cm")
    for kind, row in bladed_rows(xxii):
        radii = [s[r] for s in row["sections"]]
        assert radii == sorted(radii, reverse=True), f"{kind} {row['stage']}: {radii}"


def test_thickness_ratios_are_physical(xxii):
    tm, te = col(xxii, "tm_c"), col(xxii, "tte_c")
    for kind, row in bladed_rows(xxii):
        for i, s in enumerate(row["sections"], 1):
            assert 0.02 <= s[tm] <= 0.12, f"{kind} {row['stage']} s{i} tm/c {s[tm]}"
            assert 0.003 <= s[te] <= 0.02, f"{kind} {row['stage']} s{i} te/c {s[te]}"
            assert s[te] < s[tm]


# ── against Table X, transcribed separately ─────────────────────────────

def test_rotor_blade_counts_match_table_x(xxii, table_x):
    assert [r["blade_count"] for r in xxii["rotors"]] == table_x["blade_count"]


def test_rotor_root_section_sits_at_table_x_root_radius(xxii, table_x):
    r = col(xxii, "sect_ht_cm")
    for rotor, root in zip(xxii["rotors"], table_x["radius_root_cm"]):
        got = rotor["sections"][-1][r]
        assert abs(got - root) < 0.05, f"rotor {rotor['stage']}: last section at {got}, Table X root {root}"


def test_rotor_tip_section_lies_inside_table_x_tip_radius(xxii, table_x):
    r = col(xxii, "sect_ht_cm")
    for rotor, tip_le, root in zip(xxii["rotors"], table_x["radius_tip_le_cm"], table_x["radius_root_cm"]):
        got = rotor["sections"][0][r]
        assert root < got <= tip_le + 0.01, f"rotor {rotor['stage']}: first section {got} not within ({root}, {tip_le}]"
        assert tip_le - got < 0.8, f"rotor {rotor['stage']}: first section {got} is far below the LE tip {tip_le}"


def _end_check(xxii, table_x, quantity, xxii_col, tip_or_root, tol, rel=False):
    idx = 0 if tip_or_root == "tip" else -1
    key = f"{quantity}_{tip_or_root}" + ("_cm" if quantity == "chord" else "_deg" if quantity in ("camber",) else "")
    # Table X names: chord_tip_cm, camber_tip_deg, orient_angle_tip_deg, tm_over_c_tip, te_over_c_tip
    names = {
        ("chord", "tip"): "chord_tip_cm", ("chord", "root"): "chord_root_cm",
        ("camber", "tip"): "camber_tip_deg", ("camber", "root"): "camber_root_deg",
        ("stagger", "tip"): "orient_angle_tip_deg", ("stagger", "root"): "orient_angle_root_deg",
        ("tm_c", "tip"): "tm_over_c_tip", ("tm_c", "root"): "tm_over_c_root",
    }
    xcol = col(xxii, xxii_col)
    bad = []
    # Recorded disagreements are keyed by quantity name; strip the unit
    # suffix so `chord_root_cm` and `camber_tip` both match their check.
    strip = lambda q: q.replace("_cm", "").replace("_deg", "")
    known = {(d["stage"], strip(d["quantity"])) for d in xxii.get("disagrees_with_table_x", [])}
    for rotor, ref in zip(xxii["rotors"], table_x[names[(quantity, tip_or_root)]]):
        got = rotor["sections"][idx][xcol]
        gap = abs(got - ref) / ref if rel else abs(got - ref)
        if gap > tol and (rotor["stage"], f"{quantity}_{tip_or_root}") not in known \
           and (rotor["stage"], "orient_angle_root_and_camber_root") not in known:
            bad.append(f"rotor {rotor['stage']} {quantity} {tip_or_root}: XXII {got}, Table X {ref}")
    return bad


def test_rotor_tip_and_root_chord_match_table_x(xxii, table_x):
    bad = _end_check(xxii, table_x, "chord", "chord_cm", "tip", 0.01, rel=True)
    bad += _end_check(xxii, table_x, "chord", "chord_cm", "root", 0.01, rel=True)
    assert not bad, "\n".join(bad)


def test_rotor_tip_and_root_stagger_match_table_x(xxii, table_x):
    bad = _end_check(xxii, table_x, "stagger", "stagger", "tip", 1.2)
    bad += _end_check(xxii, table_x, "stagger", "stagger", "root", 1.0)
    assert not bad, "\n".join(bad)


def test_rotor_tip_and_root_camber_match_table_x(xxii, table_x):
    bad = _end_check(xxii, table_x, "camber", "camber", "tip", 0.6)
    bad += _end_check(xxii, table_x, "camber", "camber", "root", 0.8)
    assert not bad, "\n".join(bad)


def test_rotor_tip_thickness_ratio_matches_table_x(xxii, table_x):
    bad = _end_check(xxii, table_x, "tm_c", "tm_c", "tip", 0.06, rel=True)
    assert not bad, "\n".join(bad)


def test_every_recorded_disagreement_with_table_x_is_real(xxii, table_x):
    """Each entry in `disagrees_with_table_x` must describe a gap that
    actually exists between the two transcriptions -- otherwise it is a
    stale note."""
    names = {
        "camber_root": ("camber_root_deg", -1, "camber"),
        "camber_tip": ("camber_tip_deg", 0, "camber"),
        "chord_root_cm": ("chord_root_cm", -1, "chord_cm"),
    }
    rotors = {r["stage"]: r for r in xxii["rotors"]}
    for d in xxii["disagrees_with_table_x"]:
        if d["quantity"] not in names:
            continue  # the stage-7 duplication is described in prose
        xname, idx, xcol = names[d["quantity"]]
        got = rotors[d["stage"]]["sections"][idx][col(xxii, xcol)]
        ref = table_x[xname][d["stage"] - 1]
        assert abs(got - ref) > 0.5 or abs(got - ref) / ref > 0.01, f"stale note: {d}"
        assert abs(got - d["table_xxii_section_12" if idx == -1 else "table_xxii_section_1"]) < 1e-9
        assert abs(ref - d["table_x"]) < 1e-9


# ── stators ─────────────────────────────────────────────────────────────

def test_stator_vane_counts_are_all_ten_plus_the_igv(xxii):
    assert [s["stage"] for s in xxii["stators"]] == list(range(1, 11))
    counts = [s["vane_count"] for s in xxii["stators"]]
    assert counts == [50, 68, 82, 92, 110, 120, 112, 104, 118, 140]
    assert xxii["igv"]["vane_count"] == 32


def test_stator_10_vane_count_and_tip_section_match_table_xxi(xxii):
    """Table XXI (p.153, the original-design blading) printed 'STATOR 10 -
    140 VANES' and a first plane section of chord 0.9984 in, camber 73.54,
    stagger 28.45, beta1 64.47, beta2 -9.07. Table XXII's final-design
    stator 10 must agree -- an independent page, transcribed separately."""
    s10 = next(s for s in xxii["stators"] if s["stage"] == 10)
    assert s10["vane_count"] == 140
    tip = s10["sections"][0]
    assert abs(tip[col(xxii, "chord_in")] - 0.9984) < 0.001
    assert tip[col(xxii, "camber")] == 73.54
    assert tip[col(xxii, "stagger")] == 28.45
    assert tip[col(xxii, "beta1")] == 64.47
    assert tip[col(xxii, "beta2")] == -9.07


def test_stator_and_rotor_counts_agree_with_the_published_data_file(xxii):
    """The published-data YAML now carries the vane counts too; the two
    files must not drift."""
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())["hpc"]
    assert pub["stator_vane_counts"]["igv"] == xxii["igv"]["vane_count"]
    for s in xxii["stators"]:
        assert pub["stator_vane_counts"][f"s{s['stage']}"] == s["vane_count"]
