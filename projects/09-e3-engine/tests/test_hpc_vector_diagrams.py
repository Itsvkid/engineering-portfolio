"""HPC Table XXI -- the through-flow data -- checked five ways.

Every row is twelve streamlines at inlet and exit plus twelve blade-element
lines, read off a 1985 scan. What makes it checkable is that almost nothing
in it is independent:

  1. R-BAR is the stacking-axis radius of each streamline, and Table XXII
     prints the same radii as its section heights. Two tables, two pages,
     one number.
  2. U = omega * r on every rotor streamline. One omega for the whole
     compressor, and it is the HP spool speed the published data file
     carries from Table X's footnote.
  3. Exit PT/PT1 and TT/TT1 of a row are the inlet PT/PT1 and TT/TT1 of the
     next row IN THE GAS PATH (which is not the print order).
  4. Solidity is chord / pitch: the page's own original-design chord times
     the blade count over 2 pi R-BAR.
  5. The diffusion factor is a formula in the printed velocities, angles
     and solidity, so it can be recomputed from the same line.

Lines that fail a check AS PRINTED, or could not be read, are in
`inconsistent_as_printed` and allowed by name. Plain interpreter -- yaml only.
"""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def xxi():
    return yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())


@pytest.fixture(scope="module")
def xxii():
    return yaml.safe_load((DATA / "hpc-blade-sections.yaml").read_text())


@pytest.fixture(scope="module")
def published():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def cols(xxi, row, block):
    if block == "sl_data":
        return xxi["columns"]["sl_data_igv" if row["row"] == "igv" else "sl_data"]
    return xxi["columns"]["rotor_station" if row["row"] == "rotor" else "stator_station"]


def c(xxi, row, block, name):
    return cols(xxi, row, block).index(name)


def label(row):
    return row["row"] if row["row"] == "igv" else f"{row['row']} {row['stage']}"


def key(row):
    return (row["row"], row.get("stage"))


def gas_path(xxi):
    """Rows in the order the air sees them, whatever order the pages are in."""
    by_key = {key(r): r for r in xxi["rows"]}
    order = [("igv", None)]
    n = max(r.get("stage", 0) for r in xxi["rows"])
    for s in range(1, n + 1):
        order += [("rotor", s), ("stator", s)]
    return [by_key[k] for k in order if k in by_key]


def allowed(xxi, row, block, sl, check):
    return any(a["row"] == label(row) and a["block"] == block and a["sl"] == sl and a["check"] == check
               for a in xxi.get("inconsistent_as_printed", []))


# ── shape ───────────────────────────────────────────────────────────────

def test_every_row_has_twelve_streamlines_in_every_block(xxi):
    for row in xxi["rows"]:
        for block in ("inlet", "exit", "sl_data"):
            n = len(cols(xxi, row, block))
            assert len(row[block]) == 12, f"{label(row)} {block}: {len(row[block])} lines"
            for i, line in enumerate(row[block], 1):
                assert len(line) == n, f"{label(row)} {block} SL {i}: {len(line)} values, expected {n}"
                assert line[0] == i, f"{label(row)} {block}: SL numbering at line {i}"
        assert len(row["chord_original_cm"]) == 12, f"{label(row)}: chord_original_cm"


def test_all_twenty_one_rows_are_present(xxi):
    present = {key(r) for r in xxi["rows"]}
    expect = {("igv", None)} | {(k, s) for s in range(1, 11) for k in ("rotor", "stator")}
    assert present == expect, f"missing {expect - present}, extra {present - expect}"


def test_overall_pressure_ratio_of_the_original_design(xxi):
    """Stator 10 exit PT/PT1 is the compressor's original-design pressure
    ratio at the aero design point. The FPS match point (Table XIV) is 23.0
    at 98.4 % speed; the original design at 100 % speed sits a little
    above it."""
    s10 = next(r for r in xxi["rows"] if key(r) == ("stator", 10))
    pt = [l[c(xxi, s10, "exit", "pt_ratio")] for l in s10["exit"]]
    assert 24.5 < min(pt) and max(pt) < 25.2, pt


def test_no_gaps_in_the_gas_path_so_far(xxi):
    """Rows may arrive in batches, but never with a hole: if stator N is
    present, rotor N and every earlier row must be too."""
    present = {key(r) for r in xxi["rows"]}
    assert ("igv", None) in present
    stages = sorted(s for k, s in present if s is not None)
    for s in range(1, max(stages) + 1):
        assert ("rotor", s) in present, f"rotor {s} missing"
        if ("stator", s) not in present:
            assert s == max(stages), f"stator {s} missing but later rows present"


def test_immersion_runs_tip_to_hub_and_radius_falls(xxi):
    for row in xxi["rows"]:
        for block in ("inlet", "exit", "sl_data"):
            imm = [l[c(xxi, row, block, "pct_imm")] for l in row[block]]
            r_name = "r_bar_cm" if block == "sl_data" else "radius_cm"
            rad = [l[c(xxi, row, block, r_name)] for l in row[block]]
            assert imm[0] == 0.0 and imm[-1] == 100.0, f"{label(row)} {block}: {imm}"
            assert imm == sorted(imm), f"{label(row)} {block} immersion not monotonic"
            assert rad == sorted(rad, reverse=True), f"{label(row)} {block} radius not monotonic"


def test_streamline_slope_is_tip_negative_hub_positive_and_monotonic(xxi):
    """PHI signs on faint lines were set from this trend, so the trend must
    hold -- otherwise the sign was set wrongly."""
    for row in xxi["rows"]:
        if key(row) == ("stator", 10):
            # The last row runs into the exit diffuser: streamlines converge
            # and the slope changes sign across the span. No trend to hold,
            # and every PHI on that page is legible.
            continue
        for block in ("inlet", "exit"):
            phi = [l[c(xxi, row, block, "phi_deg")] for l in row[block]]
            assert phi[0] <= 0.0, f"{label(row)} {block}: tip PHI {phi[0]} not <= 0"
            if row["row"] != "igv":
                # Rear stages run nearly cylindrical: the hub slope can stay
                # slightly negative. What must hold is hub >= tip and a
                # monotonic rise below the tip line.
                assert phi[-1] >= phi[0], f"{label(row)} {block}: hub PHI {phi[-1]} below tip {phi[0]}"
                rises = sum(b >= a for a, b in zip(phi[1:], phi[2:]))
                assert rises >= 9, f"{label(row)} {block}: PHI not monotonic below the tip: {phi}"


# ── 1 · R-BAR is Table XXII's section radius ────────────────────────────

def test_r_bar_equals_table_xxii_section_radius(xxi, xxii):
    sections = {("igv", None): xxii["igv"]["sections"]}
    sections.update({("rotor", r["stage"]): r["sections"] for r in xxii["rotors"]})
    sections.update({("stator", s["stage"]): s["sections"] for s in xxii["stators"]})
    for row in xxi["rows"]:
        want = [s[0] for s in sections[key(row)]]
        got = [l[c(xxi, row, "sl_data", "r_bar_cm")] for l in row["sl_data"]]
        for sl, (g, w) in enumerate(zip(got, want), 1):
            if allowed(xxi, row, "sl_data", sl, "r_bar"):
                # A recorded disagreement between the two tables. It must be
                # the one XXII already flags as inconsistent with its own
                # inch column -- three prints, and XXI sides with the inches.
                sec = sections[key(row)][sl - 1]
                inch_cm = sec[1] * 2.54
                assert abs(g - inch_cm) < 0.0015, f"{label(row)} SL {sl}: XXI {g} does not match XXII's inches {inch_cm:.4f}"
                assert abs(w - inch_cm) > 0.003, f"{label(row)} SL {sl}: XXII cm agrees with its inches; allowance is stale"
                continue
            assert abs(g - w) < 0.0015, f"{label(row)} SL {sl}: R-BAR {g}, Table XXII {w}"


# ── 2 · U = omega r, one omega, and it is the HP spool speed ────────────

def test_wheel_speed_over_radius_is_one_angular_velocity(xxi, published):
    omegas = []
    for row in xxi["rows"]:
        if row["row"] != "rotor":
            continue
        for block in ("inlet", "exit"):
            for l in row[block]:
                u, r = l[c(xxi, row, block, "u_m_s")], l[c(xxi, row, block, "radius_cm")] / 100
                omegas.append((label(row), block, l[0], u / r))
    values = [o[3] for o in omegas]
    mean = sum(values) / len(values)
    for lab, block, sl, w in omegas:
        assert abs(w - mean) / mean < 0.002, f"{lab} {block} SL {sl}: omega {w:.2f} vs mean {mean:.2f}"
    rpm = mean * 60 / (2 * math.pi)
    xnhr = published["hpc"]["spool_speed_rpm"]["xnhr_100pct"]
    assert abs(rpm - xnhr) / xnhr < 0.002, f"omega gives {rpm:.0f} rpm; Table X footnote says {xnhr}"


# ── 3 · exit of each row chains into inlet of the next, in gas-path order ─

def test_total_pressure_and_temperature_chain_along_the_gas_path(xxi):
    rows = gas_path(xxi)
    for a, b in zip(rows, rows[1:]):
        for sl in range(12):
            if allowed(xxi, a, "exit", sl + 1, "chain"):
                continue  # a recorded break -- misprint, or a bleed port
            for q, tol in (("pt_ratio", 0.0012), ("tt_ratio", 0.0004)):
                out = a["exit"][sl][c(xxi, a, "exit", q)]
                inn = b["inlet"][sl][c(xxi, b, "inlet", q)]
                assert abs(out - inn) <= tol, (
                    f"{label(a)} exit -> {label(b)} inlet, SL {sl+1}, {q}: {out} vs {inn}")


@pytest.mark.parametrize("stage, purpose", [
    (5, "customer bleed and active clearance control"),
    (7, "HPT cooling air"),
])
def test_the_bleed_ports_show_up_where_the_report_says_they_are(xxi, stage, purpose):
    """CR-168219 sec 5.2.1 p.52 puts casing bleed ports at the stator-5 exit
    and the stage-7 exit. If both rows around a port are transcribed, the
    tip streamline -- and only the tip streamline -- must change total
    pressure AND temperature between that stator's exit and the next rotor's
    inlet, because the outermost stream tube has left the compressor and
    the tip line is redrawn. Every other streamline must chain as usual.

    A bleed you can see in the data is the transcription agreeing with the
    prose, from two different documents."""
    by = {key(r): r for r in xxi["rows"]}
    if ("stator", stage) not in by or ("rotor", stage + 1) not in by:
        pytest.skip(f"stator {stage} / rotor {stage + 1} not yet transcribed")
    s, r = by[("stator", stage)], by[("rotor", stage + 1)]
    pt_o, pt_i = c(xxi, s, "exit", "pt_ratio"), c(xxi, r, "inlet", "pt_ratio")
    tt_o, tt_i = c(xxi, s, "exit", "tt_ratio"), c(xxi, r, "inlet", "tt_ratio")
    d_pt = [abs(s["exit"][i][pt_o] - r["inlet"][i][pt_i]) for i in range(12)]
    d_tt = [abs(s["exit"][i][tt_o] - r["inlet"][i][tt_i]) for i in range(12)]
    assert d_pt[0] > 0.004 and d_tt[0] > 0.008, f"{purpose}: tip streamline unchanged: {d_pt[0]}, {d_tt[0]}"
    assert all(d < 0.0002 for d in d_pt[1:]), d_pt
    assert all(d < 0.0002 for d in d_tt[1:]), d_tt
    assert any(a["row"] == f"stator {stage}" and a["check"] == "chain" and a.get("physical")
               for a in xxi["inconsistent_as_printed"]), "the bleed break must be on the record as physical"


def test_no_other_streamline_break_is_marked_physical(xxi):
    """Only the two documented bleed ports may be excused as physics.
    Anything else that breaks the chain is a print or read error and must
    say so."""
    physical = [a["row"] for a in xxi["inconsistent_as_printed"]
                if a["check"] == "chain" and a.get("physical")]
    assert set(physical) <= {"stator 5", "stator 7"}, physical


def test_total_temperature_is_constant_across_stators_and_rises_across_rotors(xxi):
    for row in xxi["rows"]:
        for sl in range(12):
            t_in = row["inlet"][sl][c(xxi, row, "inlet", "tt_ratio")]
            t_out = row["exit"][sl][c(xxi, row, "exit", "tt_ratio")]
            if row["row"] == "rotor":
                assert t_out > t_in + 0.05, f"{label(row)} SL {sl+1}: rotor adds no work"
            else:
                assert abs(t_out - t_in) < 0.0002, f"{label(row)} SL {sl+1}: TT changes across a stator"


def test_total_pressure_falls_across_stators_and_rises_across_rotors(xxi):
    for row in xxi["rows"]:
        for sl in range(12):
            p_in = row["inlet"][sl][c(xxi, row, "inlet", "pt_ratio")]
            p_out = row["exit"][sl][c(xxi, row, "exit", "pt_ratio")]
            if row["row"] == "rotor":
                # Front stages run 1.4-1.7; the rear stages of a 23:1 ten-stage
                # machine settle near 1.25 mid-span (rotor 10 SL 6: 1.249).
                assert p_out > p_in * 1.20, f"{label(row)} SL {sl+1}: rotor PR {p_out/p_in:.3f}"
            else:
                assert p_out < p_in and p_out > 0.9 * p_in, f"{label(row)} SL {sl+1}: stator PT {p_in} -> {p_out}"


# ── 4 · solidity = chord * N / (2 pi r) ─────────────────────────────────

def original_count(row):
    """The blade count the page was computed with. Two rotors were re-bladed
    between the original and final designs; their pages carry the original."""
    return row.get("blade_count_original", row.get("blade_count", row.get("vane_count")))


def test_solidity_equals_original_chord_over_pitch(xxi):
    """sigma = c N / (2 pi r), with the page's own chord and blade count.
    0.5 % covers print rounding of a four-figure solidity; a wrong blade
    count moves it by 2 % or more, which is how the rotor 9 and 10 originals
    were established."""
    for row in xxi["rows"]:
        n = original_count(row)
        for sl, l in enumerate(row["sl_data"]):
            r = l[c(xxi, row, "sl_data", "r_bar_cm")]
            sigma = row["chord_original_cm"][sl] * n / (2 * math.pi * r)
            got = l[c(xxi, row, "sl_data", "solidity")]
            if allowed(xxi, row, "sl_data", sl + 1, "solidity"):
                # Recorded: the hub-trim lines, where the report's solidity
                # was computed on the untrimmed chord. Printed must sit ABOVE
                # computed, by less than 2.5 %, or the allowance is wrong.
                assert 0.005 < (got - sigma) / got < 0.025, (
                    f"{label(row)} SL {sl+1}: allowance covers offset {(got-sigma)/got:+.4f} -- revisit")
                continue
            assert abs(sigma - got) / got < 0.005, (
                f"{label(row)} SL {sl+1}: solidity {got}, chord*N/(2 pi r) = {sigma:.4f} with N={n}")
    hub = xxi["design_change_original_to_final"]["hub_solidity"]
    listed = {(a["row"], a["sl"]) for a in xxi["inconsistent_as_printed"] if a["check"] == "solidity"}
    assert {r for r, _ in listed} == set(hub["rows"]), (listed, hub["rows"])
    assert all(sl >= 10 for _, sl in listed), "solidity allowances must be hub-end lines only"


def test_rebladed_rotors_are_recorded_and_their_counts_are_forced_by_solidity(xxi):
    """A rotor may carry blade_count_original only if the solidity on its
    page cannot be reproduced with the final count -- otherwise the note is
    unjustified."""
    changes = xxi["design_change_original_to_final"]["blade_counts"]
    for row in xxi["rows"]:
        if "blade_count_original" not in row:
            continue
        rec = changes[f"rotor_{row['stage']}"]
        assert rec == {"original": row["blade_count_original"], "final": row["blade_count"]}, rec
        l = row["sl_data"][0]
        r = l[c(xxi, row, "sl_data", "r_bar_cm")]
        got = l[c(xxi, row, "sl_data", "solidity")]
        with_final = row["chord_original_cm"][0] * row["blade_count"] / (2 * math.pi * r)
        assert abs(with_final - got) / got > 0.02, (
            f"{label(row)}: the final count {row['blade_count']} reproduces the page's solidity; "
            "no re-blading to record")


def test_final_design_chord_change_matches_the_recorded_findings(xxi, xxii):
    """Table XXII is the final design; the chord on the XXI page is the
    original. Where they moved, the YAML says so; this pins those findings
    and insists every other row stayed within 1 %."""
    final = {("igv", None): [s[xxii["igv"]["columns"].index("chord_cm")] for s in xxii["igv"]["sections"]]}
    ci = xxii["columns"].index("chord_cm")
    final.update({("rotor", r["stage"]): [s[ci] for s in r["sections"]] for r in xxii["rotors"]})
    final.update({("stator", s["stage"]): [s[ci] for s in s["sections"]] for s in xxii["stators"]})
    worst = {}
    for row in xxi["rows"]:
        for orig, fin in zip(row["chord_original_cm"], final[key(row)]):
            worst[label(row)] = max(worst.get(label(row), 0), abs(fin - orig) / orig)
    recorded = {"rotor 3": (0.030, 0.045), "rotor 4": (0.020, 0.032),
                "stator 8": (0.06, 0.09), "stator 9": (0.045, 0.065)}
    for lab, w in worst.items():
        if lab in recorded:
            lo, hi = recorded[lab]
            assert lo < w < hi, f"{lab}: chord change {w:.3f} outside the recorded range {recorded[lab]}"
        else:
            assert w < 0.012, f"{lab}: chord moved {w:.3f} between original and final -- record it"


# ── 5 · diffusion factor recomputed from the printed line ───────────────

def test_diffusion_factor_recomputes_from_velocities_and_solidity(xxi):
    """DF = 1 - W2/W1 + (W_theta1 - W_theta2) / (2 sigma W1), with W the
    velocity in the blade's own frame: relative for rotors (BETA, CZ),
    absolute for stators (ALPHA, CZ). The IGV's DF is negative (it
    accelerates) and the same formula applies.

    Inlet and exit lines sit at slightly different radii from R-BAR, so
    this is a check to a few hundredths, not to print precision -- but a
    mis-read angle or CZ moves it by far more than that."""
    for row in xxi["rows"]:
        ang = "beta_deg" if row["row"] == "rotor" else "alpha_deg"
        for sl in range(12):
            li, lo, ls = row["inlet"][sl], row["exit"][sl], row["sl_data"][sl]
            a1, a2 = math.radians(li[c(xxi, row, "inlet", ang)]), math.radians(lo[c(xxi, row, "exit", ang)])
            cz1, cz2 = li[c(xxi, row, "inlet", "cz_m_s")], lo[c(xxi, row, "exit", "cz_m_s")]
            w1, w2 = cz1 / math.cos(a1), cz2 / math.cos(a2)
            wt1, wt2 = cz1 * math.tan(a1), cz2 * math.tan(a2)
            sigma = ls[c(xxi, row, "sl_data", "solidity")]
            df = 1 - w2 / w1 + (wt1 - wt2) / (2 * sigma * w1)
            got = ls[c(xxi, row, "sl_data", "df")]
            if not allowed(xxi, row, "sl_data", sl + 1, "df"):
                assert abs(df - got) < 0.045, f"{label(row)} SL {sl+1}: DF printed {got}, recomputed {df:.4f}"


def test_loss_and_efficiency_are_physical(xxi):
    for row in xxi["rows"]:
        for l in row["sl_data"]:
            loss = l[c(xxi, row, "sl_data", "loss")]
            assert 0.0 < loss < 0.30, f"{label(row)} SL {l[0]}: loss {loss}"
            if row["row"] != "igv":
                eff = l[c(xxi, row, "sl_data", "cum_eff")]
                assert 0.6 < eff < 1.0, f"{label(row)} SL {l[0]}: cum eff {eff}"


def test_stator_inlet_angle_is_the_rotor_exit_absolute_angle(xxi):
    """A rotor prints BETA (relative); the following stator prints ALPHA
    (absolute) at the same streamline one plane downstream. The rotor's
    absolute exit angle is atan((U - CZ tan BETA) / CZ). Different axial
    planes and radii, so a few degrees."""
    rows = gas_path(xxi)
    for a, b in zip(rows, rows[1:]):
        if a["row"] != "rotor" or b["row"] != "stator":
            continue
        for sl in range(12):
            lo = a["exit"][sl]
            u = lo[c(xxi, a, "exit", "u_m_s")]
            cz = lo[c(xxi, a, "exit", "cz_m_s")]
            beta = math.radians(lo[c(xxi, a, "exit", "beta_deg")])
            alpha_abs = math.degrees(math.atan((u - cz * math.tan(beta)) / cz))
            alpha_stator = b["inlet"][sl][c(xxi, b, "inlet", "alpha_deg")]
            assert abs(alpha_abs - alpha_stator) < 4.0, (
                f"{label(a)} exit SL {sl+1}: absolute angle {alpha_abs:.2f}, "
                f"{label(b)} inlet prints {alpha_stator}")


def test_blade_and_vane_counts_match_the_section_file(xxi, xxii):
    counts = {("igv", None): xxii["igv"]["vane_count"]}
    counts.update({("rotor", r["stage"]): r["blade_count"] for r in xxii["rotors"]})
    counts.update({("stator", s["stage"]): s["vane_count"] for s in xxii["stators"]})
    for row in xxi["rows"]:
        n = row.get("blade_count", row.get("vane_count"))
        assert n == counts[key(row)], f"{label(row)}: {n}"


def test_every_allowance_names_a_row_that_exists_and_a_gap_that_is_real(xxi):
    rows = {label(r): r for r in xxi["rows"]}
    path = gas_path(xxi)
    nxt = {label(a): b for a, b in zip(path, path[1:])}
    for a in xxi.get("inconsistent_as_printed", []):
        assert a["row"] in rows, a
        row = rows[a["row"]]
        if a["check"] == "chain":
            b = nxt[a["row"]]
            out = row["exit"][a["sl"] - 1][c(xxi, row, "exit", "pt_ratio")]
            inn = b["inlet"][a["sl"] - 1][c(xxi, b, "inlet", "pt_ratio")]
            assert 0.0012 < abs(out - inn) < 0.02, f"{a}: gap {abs(out-inn):.4f} -- revisit"
            assert "physical" in a, f"{a}: say whether the break is physical or a print error"
        elif a["check"] == "illegible":
            col_ = c(xxi, row, a["block"], a["column"])
            assert row[a["block"]][a["sl"] - 1][col_] == a["stated"], a
        elif a["check"] not in ("df", "r_bar", "solidity"):
            raise AssertionError(f"unknown check kind: {a}")
