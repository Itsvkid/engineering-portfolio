"""Stage D unit D7: the stage-1 nozzle cooling flow network.

The stage-1 nozzle is the row the HPT report documents most completely,
and it documents it as a **chain**: compressor discharge, through the
combustor liner, into the bands, into the impingement inserts, across the
impingement holes, out through the film rows into the gas. Every link has
a printed number and the chain has to close on itself.

Four things are checked here and only the last is not arithmetic.

Figure 15 prints a diameter and a hole count for every film row -- 105
leading-edge holes at 0.508 mm, three suction-side rows, two
pressure-side rows, eighteen trailing-edge slots at 0.559 by 1.63 mm.
Figure 17 separately prints, per row, the local gas Mach number and the
coolant flow that row carries. Figure 13(b) separately again prints the
flow each of the two impingement inserts passes. **Three figures in three
sections, never reconciled against each other.** Inverting for the
discharge coefficient asks whether they can all be right at once.

The discharge reference is the report's own: `backflow_margin_definition`
reads 100 (Ps_coolant - Pt_gas) / Pt_gas, and 1.45 % of the printed
Pt_gas reproduces the printed forward-cavity static to four figures. So
the report sizes the leading-edge showerhead against gas *total*
pressure -- the stagnation worst case -- while every row downstream of
the stagnation point discharges to its own local static, which its own
printed Mach number gives.

STEP0.md, unit D7."""
from __future__ import annotations

import itertools
import math

import yaml

from e3cycle.cycle import DATA

R_AIR = 287.05
GAMMA_GAS = 1.333          # src: combustion products, D2's value

#: Which impingement insert feeds which film row. NOT printed -- recovered
#: in insert_split() by showing exactly one subset of Figure 17's seven
#: rows sums to Figure 13(b)'s forward-insert flow.
FORWARD_ROWS = ("leading_edge", "pressure_side_forward",
                "suction_side_leading", "suction_side_forward")
AFT_ROWS = ("suction_side_mid", "suction_side_aft",
            "pressure_side_te_slots")

#: Figure 17's row names against Figure 15's geometry groups. The suction
#: side is one group for four printed rows: see suction_side_row_mismatch().
ROW_TO_GROUP = {
    "leading_edge": "leading_edge",
    "pressure_side_forward": "pressure_side",
    "suction_side_leading": "suction_side",
    "suction_side_forward": "suction_side",
    "suction_side_mid": "suction_side",
    "suction_side_aft": "suction_side",
    "pressure_side_te_slots": "trailing_edge",
}

#: The one row that does not discharge to a local static from its own
#: printed Mach: a showerhead sits on the stagnation point. Licensed by
#: discharge_reference(), where the forward cavity's printed backflow
#: margin is shown to be quoted against gas total and the aft cavity's
#: against gas static.
DISCHARGES_AT_STAGNATION = ("leading_edge",)


def _noz():
    return yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())["stage1_nozzle"]


def pressure_chain():
    """Compressor discharge to delivered band coolant, through the printed
    liner losses. Both ends are printed; the losses are printed; so this
    is arithmetic the report has to satisfy."""
    n = _noz()
    sup, loss = n["supply_conditions"], n["pressure_losses"]
    p3 = sup["p3_MPa"]
    out = []
    for band, key in (("outer", "total_system_outer_band_pct"),
                      ("inner", "total_system_inner_band_pct")):
        pct = loss[key]
        predicted = p3 * (1 - pct / 100)
        printed = sup[f"{band}_band_coolant"]["pt_MPa"]
        out.append(dict(band=band, p3_MPa=p3, loss_pct=pct,
                        predicted_MPa=predicted, printed_MPa=printed,
                        err_pct=(predicted / printed - 1) * 100))
    return out


def impingement_ratios():
    """Insert supply over cavity static, against the printed ratio."""
    c = _noz()["cavity_pressures"]
    out = []
    for cav in ("forward_cavity", "aft_cavity"):
        v = c[cav]
        predicted = v["insert_supply_MPa"] / v["static_MPa"]
        printed = v["impingement_pressure_ratio"]
        out.append(dict(cavity=cav, insert_supply_MPa=v["insert_supply_MPa"],
                        cavity_static_MPa=v["static_MPa"],
                        predicted=predicted, printed=printed,
                        err_pct=(predicted / printed - 1) * 100))
    return out


def discharge_reference():
    """Which gas pressure each cavity's printed backflow margin is quoted
    against -- and therefore what the film holes discharge to.

    Unit D3 already found that the printed definition, 100 (Ps_coolant -
    Pt_gas) / Pt_gas, does not fit both printed margins (finding 65).
    This does not re-find it; it uses D3's own cavity model and asks the
    question D7 needs answered: *which* reference fits *which* cavity.

    The answer is clean. The forward cavity's 1.45 % reproduces its
    printed static from gas **total** to 0.015 %; the aft cavity's 1.00 %
    reproduces its static from gas **static** to 0.004 %. Swap them and
    each is out by 0.68 %. The separation is two orders of magnitude, so
    the pairing is read off the data, not assumed.

    And it is the physics. The forward cavity feeds the leading-edge
    showerhead, which sits on the stagnation point, where the gas pressure
    a hole discharges against *is* the total. Everything the aft cavity
    feeds is downstream of it and sees a static. That is what licenses
    DISCHARGES_AT_STAGNATION below -- the report's own choice of
    reference, not a modelling convenience."""
    from thermal.secondary_air import stage1_nozzle_cavities
    cavities, definition = stage1_nozzle_cavities()
    out = []
    for c in cavities:
        errs = {"pt_MPa": (c.margin_vs_total / c.printed_margin_pct - 1) * 100
                if c.printed_margin_pct else float("inf"),
                "ps_MPa": (c.margin_vs_static / c.printed_margin_pct - 1) * 100
                if c.printed_margin_pct else float("inf")}
        # state it as a pressure error, which is what the reader can check
        perr = {"pt_MPa": (c.gas_total_MPa * (1 + c.printed_margin_pct / 100)
                           / c.coolant_static_MPa - 1) * 100,
                "ps_MPa": (c.gas_static_MPa * (1 + c.printed_margin_pct / 100)
                           / c.coolant_static_MPa - 1) * 100}
        best = min(perr, key=lambda r: abs(perr[r]))
        other = "ps_MPa" if best == "pt_MPa" else "pt_MPa"
        out.append(dict(
            cavity=c.name, margin_pct=c.printed_margin_pct,
            printed_MPa=c.coolant_static_MPa,
            gas_total_MPa=c.gas_total_MPa, gas_static_MPa=c.gas_static_MPa,
            reference=best, reference_MPa=(c.gas_total_MPa if best == "pt_MPa"
                                          else c.gas_static_MPa),
            predicted_MPa=(c.gas_total_MPa if best == "pt_MPa"
                           else c.gas_static_MPa) * (1 + c.printed_margin_pct / 100),
            err_pct=perr[best], err_pct_other_reference=perr[other],
            separation=abs(perr[other]) / abs(perr[best]),
            margin_err_pct=errs[best]))
    return dict(
        rows=out, definition=definition,
        forward_reference=out[0]["reference"], aft_reference=out[1]["reference"],
        references_differ=out[0]["reference"] != out[1]["reference"],
        is_finding_65=True,
        used_for=("fixes the film-hole discharge reference: stagnation at the "
                  "showerhead, local static everywhere aft of it"),
    )


def insert_split():
    """Figure 13(b) prints what each impingement insert passes: 3.4 % of
    W25 forward, 2.9 % aft. Figure 17 prints what each of seven film rows
    passes. Nothing printed says which insert feeds which row.

    It does not have to be assumed. Take every subset of the seven rows
    and ask which sums to 3.4: exactly one does, and it is the contiguous
    group running from the leading edge back. The remaining three sum to
    2.9 without being asked to. Two independently digitised figures agree
    to the last printed digit, and the agreement recovers the feed map."""
    n = _noz()
    rows = {r["location"]: r["w_c_pct"] for r in n["film_mixing_losses"]["rows"]}
    sp = n["vane_flow_split"]
    target = sp["forward_insert_pct_w25"]
    subsets = [c for k in range(1, len(rows) + 1)
               for c in itertools.combinations(sorted(rows), k)
               if abs(sum(rows[x] for x in c) - target) < 1e-9]
    fwd = sum(rows[k] for k in FORWARD_ROWS)
    aft = sum(rows[k] for k in AFT_ROWS)
    return dict(
        forward_rows=FORWARD_ROWS, aft_rows=AFT_ROWS,
        forward_sum_pct=fwd, forward_printed_pct=target,
        aft_sum_pct=aft, aft_printed_pct=sp["aft_insert_pct_w25"],
        total_pct=fwd + aft,
        total_printed_pct=n["film_mixing_losses"]["total_w_c_pct"],
        candidate_subsets=len(subsets), unique=len(subsets) == 1,
        the_unique_subset=subsets[0] if len(subsets) == 1 else None,
        forward_exact=abs(fwd - target) < 1e-9,
        aft_exact=abs(aft - sp["aft_insert_pct_w25"]) < 1e-9,
    )


def cavity_for(row: str) -> str:
    """Which cavity a Figure 17 row discharges from, per insert_split()."""
    if row in FORWARD_ROWS:
        return "forward_cavity"
    if row in AFT_ROWS:
        return "aft_cavity"
    raise KeyError(row)


def film_hole_area_m2():
    """Film-hole area per vane, from Figure 15's own diameters and counts.

    The trailing-edge slots are included: the figure prints both slot
    dimensions, 0.559 by 1.63 mm, so the area is computable. They carry
    2.27 % of W25 -- 36 % of the vane's film flow -- and leaving them out
    while keeping their flow is what made a first pass at this return an
    unphysical discharge coefficient."""
    g = _noz()["film_cooling_geometry"]
    groups = {}
    for key, group in (("leading_edge_radial_rows_at_25deg", "leading_edge"),
                       ("suction_side_compound_angle_rows", "suction_side"),
                       ("pressure_side_diffusion_shaped_rows", "pressure_side")):
        rows = []
        for r in g[key]:
            d = r["diameter_mm"] / 1000
            rows.append(dict(diameter_mm=r["diameter_mm"], holes=r["holes"],
                             area_m2=math.pi / 4 * d * d * r["holes"]))
        groups[group] = dict(rows=rows, kind="round",
                             area_m2=sum(r["area_m2"] for r in rows),
                             holes=sum(r["holes"] for r in rows))
    te = g["trailing_edge"]
    w, h = te["slot_size_mm"]
    groups["trailing_edge"] = dict(
        rows=[dict(slot_mm=[w, h], holes=te["slots"],
                   area_m2=te["slots"] * w * h / 1e6)],
        kind="slot", area_m2=te["slots"] * w * h / 1e6, holes=te["slots"])
    return dict(
        groups=groups,
        round_hole_area_m2=sum(v["area_m2"] for k, v in groups.items()
                               if v["kind"] == "round"),
        round_hole_count=sum(v["holes"] for k, v in groups.items()
                             if v["kind"] == "round"),
        te_slot_area_m2=groups["trailing_edge"]["area_m2"],
        total_area_m2=sum(v["area_m2"] for v in groups.values()),
    )


def suction_side_row_mismatch():
    """Figure 17 names four suction-side rows; Figure 15 draws three. The
    mismatch is recorded, not resolved: the suction side is treated as one
    group, so its discharge coefficient is an area-weighted aggregate and
    no single printed row is claimed from it."""
    n = _noz()
    loss = [r["location"] for r in n["film_mixing_losses"]["rows"]
            if r["location"].startswith("suction_side")]
    geom = n["film_cooling_geometry"]["suction_side_compound_angle_rows"]
    return dict(loss_rows=loss, loss_row_count=len(loss),
                geometry_row_count=len(geom), resolved=False,
                consequence="suction side reported as one aggregate group")


def w25_kg_s():
    """The flow every percentage in this section is a percentage of.

    The cycle model has no station 2.5 -- it carries w41 and aft. So this
    comes the other way: the FPS report prints the core inlet corrected
    flow, and the cycle's own p25 and t25 convert it to physical."""
    from e3cycle import cycle as cyc
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    wc = pub["size"]["core_inlet_corrected_flow_kg_s"]
    st = max(cyc.run_all(), key=lambda x: x.stations["p3"]).stations
    delta = st["p25"] / 101325.0
    theta = st["t25"] / 288.15
    return dict(corrected_kg_s=wc, p25_Pa=st["p25"], t25_K=st["t25"],
                delta=delta, theta=theta,
                physical_kg_s=wc * delta / math.sqrt(theta))


def row_network():
    """Per row: the local static its own printed Mach implies, the drop
    from its own cavity, and the flow it carries. Everything here is
    printed except the ideal-gas expansion and the feed map."""
    n = _noz()
    pt_gas = n["supply_conditions"]["gas_at_vane"]["pt_MPa"] * 1e6
    t_c = n["design"]["t_coolant_C"] + 273.15
    g = GAMMA_GAS
    out = []
    for r in n["film_mixing_losses"]["rows"]:
        cav = cavity_for(r["location"])
        p_cav = n["cavity_pressures"][cav]["static_MPa"] * 1e6
        stag = r["location"] in DISCHARGES_AT_STAGNATION
        m = 0.0 if stag else r["m_gas"]
        p_loc = pt_gas / (1 + (g - 1) / 2 * m * m) ** (g / (g - 1))
        rho = p_cav / (R_AIR * t_c)
        out.append(dict(
            row=r["location"], cavity=cav, m_gas_printed=r["m_gas"],
            m_used=m, discharges_at_stagnation=stag,
            w_c_pct=r["w_c_pct"], p_cavity_Pa=p_cav, p_local_Pa=p_loc,
            dp_Pa=p_cav - p_loc, rho=rho,
            pressure_ratio=p_cav / p_loc,
            group=ROW_TO_GROUP[r["location"]],
            ideal_flux=math.sqrt(2 * rho * (p_cav - p_loc))))
    return out


def discharge_coefficient():
    """Invert: what Cd makes Figure 15's holes pass Figure 17's flow?

    Grouped, because Figure 15's geometry is grouped -- one area for the
    leading-edge showerhead, one for the suction side, one for the
    pressure side, one for the trailing-edge slots. Within a group with
    more than one printed flow, the ideal flux is weighted by the flows
    themselves, which is the only weighting that leaves the group's total
    flow untouched.

    Incompressible orifice throughout. The largest pressure ratio is the
    trailing-edge slot's, and it is reported so the reader can judge the
    assumption rather than take it."""
    n = _noz()
    vanes = n["vane_count"]
    w25 = w25_kg_s()["physical_kg_s"]
    area = film_hole_area_m2()["groups"]
    rows = row_network()

    groups = []
    for name, a in area.items():
        mine = [r for r in rows if r["group"] == name]
        w_pct = sum(r["w_c_pct"] for r in mine)
        flux = sum(r["w_c_pct"] * r["ideal_flux"] for r in mine) / w_pct
        w = w25 * w_pct / 100
        ideal = a["area_m2"] * vanes * flux
        groups.append(dict(
            group=name, area_per_vane_m2=a["area_m2"], holes=a["holes"],
            kind=a["kind"], rows=[r["row"] for r in mine], w_c_pct=w_pct,
            flow_kg_s=w, ideal_kg_s=ideal, cd=w / ideal,
            max_pressure_ratio=max(r["pressure_ratio"] for r in mine),
            physical=0.5 <= w / ideal <= 1.0,
            typical=0.6 <= w / ideal <= 0.85))

    w_tot = sum(g["flow_kg_s"] for g in groups)
    ideal_tot = sum(g["ideal_kg_s"] for g in groups)
    cd = w_tot / ideal_tot
    return dict(
        groups=groups, vanes=vanes, w25_kg_s=w25,
        total_area_per_vane_m2=sum(g["area_per_vane_m2"] for g in groups),
        total_w_c_pct=sum(g["w_c_pct"] for g in groups),
        coolant_kg_s=w_tot, ideal_kg_s=ideal_tot, cd=cd,
        physical=0.5 <= cd <= 1.0, typical=0.6 <= cd <= 0.85,
        groups_physical=sum(g["physical"] for g in groups),
        max_pressure_ratio=max(g["max_pressure_ratio"] for g in groups),
        incompressible_is_fair=max(g["max_pressure_ratio"]
                                   for g in groups) < 1.4)


def required_reassignment():
    """The showerhead has too much area for its flow and the suction side
    too little. Both misses would close at once if some of Figure 15's
    "leading-edge radial rows" were what Figure 17 counts as suction-side
    rows -- the two groups are adjacent, and nothing says the two figures
    draw the boundary in the same place.

    So price it instead of asserting it. This returns the area transfer
    that would equalise the two discharge coefficients, and the number of
    showerhead holes that is. Nothing is transferred; the point is the
    size of what would have to be."""
    d = discharge_coefficient()
    g = {x["group"]: x for x in d["groups"]}
    le, ss = g["leading_edge"], g["suction_side"]
    V = d["vanes"]
    f_le = le["ideal_kg_s"] / (le["area_per_vane_m2"] * V)
    f_ss = ss["ideal_kg_s"] / (ss["area_per_vane_m2"] * V)
    a_le, a_ss = le["area_per_vane_m2"], ss["area_per_vane_m2"]
    w_le, w_ss = le["flow_kg_s"], ss["flow_kg_s"]
    x = ((w_ss * f_le * a_le - w_le * f_ss * a_ss)
         / (w_ss * f_le + w_le * f_ss))
    cd = w_le / ((a_le - x) * V * f_le)
    hole = math.pi / 4 * 0.000508 ** 2
    return dict(
        transfer_m2=x, transfer_fraction_of_showerhead=x / a_le,
        transfer_holes=x / hole, showerhead_holes=le["holes"],
        common_cd=cd, common_cd_typical=0.6 <= cd <= 0.85,
        suction_area_at_cd_080_m2=w_ss / (0.80 * V * f_ss),
        suction_area_printed_m2=a_ss,
        suction_shortfall_ratio=w_ss / (0.80 * V * f_ss) / a_ss,
        credible=x / a_le < 0.25,
        verdict=("a transfer this large is not a boundary-reading error; "
                 "the two figures disagree about more than where the "
                 "leading edge stops"),
    )


def the_aggregate_hides_the_rows():
    """The honest reading of discharge_coefficient().

    The vane as a whole inverts to a discharge coefficient a cooling
    engineer would sign: 0.80, inside the 0.60-0.85 the band was set at
    before the run. Two of its four groups do too. The other two do not,
    and they miss in opposite directions, which is exactly how an
    aggregate lands in band while its parts do not. The showerhead is a
    third of the vane's film area and carries a twenty-fifth of its film
    flow; the suction side has the least area of the four and carries more
    than the showerhead and pressure side together.

    So the closure is reported as met on its stated band and the
    decomposition is reported as the finding. Nothing is tuned to close
    the two groups, and required_reassignment() prices the one change that
    would."""
    d = discharge_coefficient()
    low = [g["group"] for g in d["groups"] if g["cd"] < 0.5]
    high = [g["group"] for g in d["groups"] if g["cd"] > 1.0]
    return dict(
        aggregate_cd=d["cd"], aggregate_in_band=d["typical"],
        groups_in_band=d["groups_physical"], groups=len(d["groups"]),
        too_much_area=low, too_little_area=high,
        misses_both_ways=bool(low) and bool(high),
        area_fraction_leading_edge=next(
            g["area_per_vane_m2"] for g in d["groups"]
            if g["group"] == "leading_edge") / d["total_area_per_vane_m2"],
        flow_fraction_leading_edge=next(
            g["w_c_pct"] for g in d["groups"]
            if g["group"] == "leading_edge") / d["total_w_c_pct"],
    )


def why_the_rows_miss():
    """The likeliest cause, and what would settle it.

    Figure 17 is a *mixing-loss* figure. Its Mach number is the one the
    loss correlation needs -- the mainstream Mach where the coolant joins
    it -- and that is not the static a hole discharges into. The two
    coincide well away from the stagnation point and diverge badly at it.

    Which is the pattern in the data. The two groups that land in band,
    pressure side and trailing edge, are the two furthest aft, at the
    highest Mach, where a mixing Mach and a surface static are nearly the
    same thing. The showerhead, where they differ most, is the worst miss.

    What would settle it is the vane's own surface static distribution.
    The report prints exactly that for the stage-1 *blade* -- Figure 22,
    pitch-line Mach against surface distance, both surfaces -- and does
    not print it for the vane. So the vane check is limited by a figure
    that exists for the next row and not for this one."""
    d = discharge_coefficient()
    n = _noz()
    rows = {r["row"]: r for r in row_network()}
    in_band = [g for g in d["groups"] if g["typical"]]
    by_mach = sorted(d["groups"],
                     key=lambda g: max(rows[r]["m_gas_printed"]
                                       for r in g["rows"]))
    blade = yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())["stage1_blade"]
    return dict(
        groups_in_band=[g["group"] for g in in_band],
        in_band_are_the_two_highest_mach=(
            {g["group"] for g in in_band} == {g["group"] for g in by_mach[-2:]}),
        group_order_by_mach=[g["group"] for g in by_mach],
        vane_has_surface_distribution=(
            "pitch_line_mach_distribution" in n),
        blade_has_surface_distribution=(
            "pitch_line_mach_distribution" in blade),
        blade_figure=blade["pitch_line_mach_distribution"]["src"],
        settles_it=("the vane's own surface static distribution, printed "
                    "for the blade as Fig.22 and not printed for the vane"),
    )


def summary():
    L = ["Stage D unit D7 -- the stage-1 nozzle cooling flow network", ""]
    L.append("   1. the pressure chain, CPD to delivered band coolant:")
    for r in pressure_chain():
        L.append(f"        {r['band']:<6} {r['p3_MPa']:.3f} MPa less "
                 f"{r['loss_pct']:.2f} % -> {r['predicted_MPa']:.4f}  "
                 f"printed {r['printed_MPa']:.3f}  {r['err_pct']:+.2f} %")
    L += ["", "   2. impingement pressure ratios:"]
    for r in impingement_ratios():
        L.append(f"        {r['cavity']:<16}{r['predicted']:.5f}  "
                 f"printed {r['printed']:.4f}  {r['err_pct']:+.2f} %")
    b = discharge_reference()
    L += ["", "   3. which gas pressure each cavity is referenced to "
          "(D3's finding 65, put to work):"]
    for r in b["rows"]:
        L.append(f"        {r['cavity']:<16}gas {r['reference'][:2]} "
                 f"{r['reference_MPa']:.3f} "
                 f"+{r['margin_pct']:.2f} % -> {r['predicted_MPa']:.4f}  "
                 f"printed {r['printed_MPa']:.3f}  {r['err_pct']:+.3f} %  "
                 f"(other reference {r['err_pct_other_reference']:+.3f} %, "
                 f"{r['separation']:.0f}x worse)")
    s = insert_split()
    L += ["", "   4. which insert feeds which row, recovered not assumed:",
          f"        subsets of the 7 rows summing to the printed "
          f"{s['forward_printed_pct']} %: {s['candidate_subsets']}",
          f"        forward insert {s['forward_sum_pct']:.2f} % = printed "
          f"{s['forward_printed_pct']}   ({', '.join(s['forward_rows'])})",
          f"        aft insert     {s['aft_sum_pct']:.2f} % = printed "
          f"{s['aft_printed_pct']}   ({', '.join(s['aft_rows'])})"]
    a = film_hole_area_m2()
    w = w25_kg_s()
    L += ["", "   5. film-hole geometry, Figure 15, per vane:"]
    for name, v in a["groups"].items():
        L.append(f"        {name:<14}{v['area_m2']*1e6:7.2f} mm2   "
                 f"{v['holes']:3d} {v['kind']}s")
    L += [f"        {'TOTAL':<14}{a['total_area_m2']*1e6:7.2f} mm2",
          "",
          f"   W25 {w['corrected_kg_s']} kg/s corrected x "
          f"{w['delta']:.4f}/sqrt({w['theta']:.4f}) = "
          f"{w['physical_kg_s']:.2f} kg/s physical"]
    d = discharge_coefficient()
    L += ["", "   6. do the holes pass the flow?", "",
          f"        {'group':<14}{'A mm2':>8}{'w %':>7}{'kg/s':>8}"
          f"{'ideal':>8}{'p ratio':>9}{'Cd':>8}"]
    for g in d["groups"]:
        L.append(f"        {g['group']:<14}{g['area_per_vane_m2']*1e6:8.2f}"
                 f"{g['w_c_pct']:7.2f}{g['flow_kg_s']:8.3f}"
                 f"{g['ideal_kg_s']:8.3f}{g['max_pressure_ratio']:9.3f}"
                 f"{g['cd']:8.3f}")
    L.append(f"        {'WHOLE VANE':<14}{d['total_area_per_vane_m2']*1e6:8.2f}"
             f"{d['total_w_c_pct']:7.2f}{d['coolant_kg_s']:8.3f}"
             f"{d['ideal_kg_s']:8.3f}{d['max_pressure_ratio']:9.3f}"
             f"{d['cd']:8.3f}")
    h = the_aggregate_hides_the_rows()
    L += ["",
          f"   => WHOLE VANE Cd {d['cd']:.3f}   physical: {d['physical']}   "
          f"typical: {d['typical']}",
          f"      but only {h['groups_in_band']} of {h['groups']} groups are "
          f"in band, and the misses go both ways:",
          f"        too much area for its flow: "
          f"{', '.join(h['too_much_area']) or 'none'}",
          f"        too little area for its flow: "
          f"{', '.join(h['too_little_area']) or 'none'}",
          f"      the showerhead is {h['area_fraction_leading_edge']*100:.0f} % "
          f"of the film area and {h['flow_fraction_leading_edge']*100:.0f} % "
          f"of the film flow"]
    r = required_reassignment()
    L += ["",
          f"      closing both would take {r['transfer_m2']*1e6:.2f} mm2 moved "
          f"from the showerhead to the suction side --",
          f"      {r['transfer_holes']:.0f} of its {r['showerhead_holes']} holes, "
          f"{r['transfer_fraction_of_showerhead']*100:.0f} % of the group, for a "
          f"common Cd of {r['common_cd']:.3f}",
          f"      credible as a boundary-reading error: {r['credible']}",
          f"      (the suction side alone would need "
          f"{r['suction_area_at_cd_080_m2']*1e6:.2f} mm2 at Cd 0.80, "
          f"{r['suction_shortfall_ratio']:.2f}x what Figure 15 draws)"]
    w = why_the_rows_miss()
    m = suction_side_row_mismatch()
    L += ["", f"   Figure 17 names {m['loss_row_count']} suction-side rows, "
          f"Figure 15 draws {m['geometry_row_count']}; "
          f"{m['consequence']}",
          f"   by gas Mach: {' < '.join(w['group_order_by_mach'])}",
          f"   the two groups in band are the two highest-Mach ones: "
          f"{w['in_band_are_the_two_highest_mach']}",
          f"   -- which is what a mixing Mach standing in for a surface "
          f"static would do.",
          f"   settled by: {w['settles_it']}"]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
