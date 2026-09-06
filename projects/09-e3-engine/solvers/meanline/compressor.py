"""C1 unit 4: compressor deviation and the HPC stage roll-up.

Deviation by Carter's rule with SP-36's Fig 160 m-factor, checked against
the deviation Table XXI prints for every streamline of every row; the
stage and overall efficiency rolled up from Table XXI's own losses and
compared with its cumulative-efficiency column and with the published
compressor efficiencies. STEP0.md, unit 4."""
from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA
from meanline.losses import _interp

SP36 = yaml.safe_load((DATA / "methods" / "sp36-compressor-correlations.yaml").read_text())


def carter_m(stagger_deg, meanline="circular_arc"):
    f = SP36["carter_deviation_rule"]["fig160"]
    return _interp(stagger_deg, f["blade_chord_angle_deg"], f[meanline])


def carter_deviation(camber_deg, stagger_deg, s_c, meanline="circular_arc"):
    """SP-36 eq (270): delta = m_c * camber * sqrt(s/c)"""
    return carter_m(stagger_deg, meanline) * camber_deg * math.sqrt(s_c)


@dataclass
class RowCheck:
    row: str
    sl: int
    pct_imm: float
    camber: float
    stagger: float
    solidity: float
    dev_printed: float
    dev_carter: float
    dev_parabolic: float
    df: float
    loss: float


def load():
    xxi = yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())
    xxii = yaml.safe_load((DATA / "hpc-blade-sections.yaml").read_text())
    stagewise = yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    return xxi, xxii, stagewise, pub


def _sections(xxii, kind, stage):
    cols = xxii["columns"]
    if kind == "igv":
        block = xxii["igv"]
    else:
        block = next(b for b in xxii["rotors" if kind == "rotor" else "stators"] if b["stage"] == stage)
    return [dict(zip(cols, r)) for r in block["sections"]]


def deviation_checks():
    xxi, xxii, _, _ = load()
    cols = xxi["columns"]
    out = []
    for row in xxi["rows"]:
        kind, stage = row["row"], row.get("stage")
        if kind == "igv" or "sl_data" not in row:
            continue
        sl = [dict(zip(cols["sl_data"], r)) for r in row["sl_data"]]
        try:
            secs = _sections(xxii, kind, stage)
        except (StopIteration, KeyError):
            continue
        if len(secs) != len(sl):
            continue
        for s, sec in zip(sl, secs):
            if s.get("dev_deg") is None or sec.get("camber") is None:
                continue
            s_c = 1.0 / s["solidity"]
            out.append(RowCheck(f"{'R' if kind == 'rotor' else 'S'}{stage}", s["sl"], s["pct_imm"],
                                sec["camber"], sec["stagger"], s["solidity"], s["dev_deg"],
                                carter_deviation(sec["camber"], sec["stagger"], s_c),
                                carter_deviation(sec["camber"], sec["stagger"], s_c, "parabolic_arc"),
                                s["df"], s["loss"]))
    return out


def efficiency_rollup():
    """mass-average Table XXI's own per-streamline losses into a row, stage
    and overall polytropic/adiabatic efficiency, and compare with its
    cumulative-efficiency column"""
    xxi, _, stagewise, pub = load()
    cols = xxi["columns"]
    rows = {}
    for row in xxi["rows"]:
        if "sl_data" not in row:
            continue
        key = f"{row['row']}{row.get('stage') or ''}"
        c = cols["sl_data_igv"] if row["row"] == "igv" else cols["sl_data"]
        rows[key] = [dict(zip(c, r)) for r in row["sl_data"]]
    # the pitch streamline's cumulative efficiency along the machine
    cum = []
    for row in xxi["rows"]:
        if "sl_data" not in row or row["row"] == "igv":
            continue
        sl = [dict(zip(cols["sl_data"], r)) for r in row["sl_data"]]
        mid = min(sl, key=lambda r: abs(r["pct_imm"] - 50))
        cum.append((f"{'R' if row['row'] == 'rotor' else 'S'}{row['stage']}", mid.get("cum_eff")))
    return rows, cum, stagewise, pub


if __name__ == "__main__":
    checks = deviation_checks()
    by_row = {}
    for c in checks:
        by_row.setdefault(c.row, []).append(c)
    print(f"{'row':<5}{'n':>3}{'camber':>8}{'stagger':>8}{'sigma':>7}{'dev pub':>9}{'Carter':>8}{'diff':>7}{'parab':>8}{'diff':>7}")
    for row, cs in by_row.items():
        n = len(cs)
        pub = sum(c.dev_printed for c in cs) / n
        car = sum(c.dev_carter for c in cs) / n
        par = sum(c.dev_parabolic for c in cs) / n
        print(f"{row:<5}{n:>3}{sum(c.camber for c in cs) / n:>8.2f}{sum(c.stagger for c in cs) / n:>8.2f}"
              f"{sum(c.solidity for c in cs) / n:>7.3f}{pub:>9.2f}{car:>8.2f}{car - pub:>7.2f}{par:>8.2f}{par - pub:>7.2f}")
    d_c = [c.dev_carter - c.dev_printed for c in checks]
    d_p = [c.dev_parabolic - c.dev_printed for c in checks]
    n = len(d_c)
    print(f"\n{n} streamline points across {len(by_row)} rows")
    for label, d in (("circular arc", d_c), ("parabolic arc", d_p)):
        mean = sum(d) / n
        rms = math.sqrt(sum(x * x for x in d) / n)
        print(f"  {label:<14} mean {mean:+.2f} deg, rms {rms:.2f}, max |{max(abs(x) for x in d):.2f}|")
    _, cum, stagewise, pub = efficiency_rollup()
    print(f"\ncumulative efficiency along the pitch streamline (Table XXI):")
    print("  " + "  ".join(f"{r}:{e:.3f}" for r, e in cum if e is not None))
    dp = stagewise["design_point"] if "design_point" in stagewise else {}
    print(f"published: design intent {dp.get('efficiency_adiabatic')} at {dp.get('pressure_ratio_design')}:1;"
          f" Table XI {pub['component_performance']['compressor_efficiency']}; ICLS as tested 0.856")


# ---------------------------------------------------------------------------
# Unit 4b: the loss roll-up. Two routes to the HPC's efficiency, both from
# Table XXI: the printed total-pressure and total-temperature ratios, and
# the printed per-element loss coefficients rebuilt into a pressure chain.
# ---------------------------------------------------------------------------
import sys as _sys

from e3cycle import gas

T_REF_INLET = 288.15   # hpc-stagewise design_point: standard-day sea-level static at the IGV inlet


def _row_key(row):
    if row["row"] == "igv":
        return "IGV"
    return f"{'R' if row['row'] == 'rotor' else 'S'}{row['stage']}"


def _stations(xxi, row, which):
    cols = xxi["columns"]["rotor_station" if row["row"] == "rotor" else "stator_station"]
    return [dict(zip(cols, r)) for r in row[which]]


def _sl(xxi, row):
    c = xxi["columns"]["sl_data_igv" if row["row"] == "igv" else "sl_data"]
    return [dict(zip(c, r)) for r in row["sl_data"]]


def efficiency_from_printed_ratios(t_inlet=T_REF_INLET):
    """route 1: adiabatic efficiency at every streamline from the printed
    total-pressure and total-temperature ratios, real gas, referred to the
    IGV inlet"""
    xxi, *_ = load()
    igv = xxi["rows"][0]
    ref = {s["sl"]: s for s in _stations(xxi, igv, "inlet")}
    out = []
    for row in xxi["rows"]:
        for st in _stations(xxi, row, "exit"):
            r = ref[st["sl"]]
            pr = st["pt_ratio"] / r["pt_ratio"]
            tr = st["tt_ratio"] / r["tt_ratio"]
            t1 = t_inlet
            t2 = t1 * tr
            t2s = gas.t_from_phi(gas.phi(t1) + gas.R_AIR * math.log(pr), guess=t2)
            eta = (gas.h(t2s) - gas.h(t1)) / (gas.h(t2) - gas.h(t1)) if tr > 1.0001 else None
            out.append(dict(row=_row_key(row), sl=st["sl"], pct_imm=st["pct_imm"], pr=pr, tr=tr, eta=eta))
    return out


def _static_from_total(t0, p0, mach, far=0.0):
    """static state at a Mach number, real gas (bisection on static T)"""
    lo, hi = 0.4 * t0, t0
    for _ in range(70):
        ts = 0.5 * (lo + hi)
        cp = gas.cp(ts, far)
        g = cp / (cp - gas.R_AIR)
        resid = 2.0 * (gas.h(t0, far) - gas.h(ts, far)) - mach ** 2 * g * gas.R_AIR * ts
        lo, hi = (ts, hi) if resid > 0 else (lo, ts)
    ts = 0.5 * (lo + hi)
    ps = p0 * math.exp(-(gas.phi(t0, far) - gas.phi(ts, far)) / gas.R_AIR)
    return ts, ps


def pressure_chain_from_losses(t_inlet=T_REF_INLET, p_inlet=101325.0):
    """route 2: rebuild the total-pressure ratio row by row from the printed
    loss coefficients alone, and compare with the printed pt_ratio.

    Rotor: omega = (P01rel_ideal - P02rel) / (P01rel - p1), where the ideal
    relative total pressure at exit is P01rel raised by the radius change
    (rothalpy). Stator: the same in the absolute frame."""
    xxi, *_ = load()
    igv = xxi["rows"][0]
    ref = {s["sl"]: s for s in _stations(xxi, igv, "inlet")}
    # start every streamline at the printed inlet state
    state = {}
    for s in _stations(xxi, igv, "inlet"):
        state[s["sl"]] = dict(p0=p_inlet, t0=t_inlet)
    out = []
    for row in xxi["rows"]:
        inlet = {s["sl"]: s for s in _stations(xxi, row, "inlet")}
        exit_ = {s["sl"]: s for s in _stations(xxi, row, "exit")}
        sl = {s["sl"]: s for s in _sl(xxi, row)}
        for k, st in state.items():
            i, e, d = inlet.get(k), exit_.get(k), sl.get(k)
            if i is None or e is None or d is None or d.get("loss") is None:
                continue
            omega = d["loss"]
            if row["row"] == "rotor":
                t1, p1 = _static_from_total(st["t0"], st["p0"], i["m_abs"])
                h01rel = gas.h(t1) + 0.5 * (i["m_rel"] * _sound(t1)) ** 2
                t01rel = gas.t_from_h(h01rel, guess=t1 + 40)
                p01rel = p1 * math.exp((gas.phi(t01rel) - gas.phi(t1)) / gas.R_AIR)
                # rothalpy: h0rel - U^2/2 constant
                h02rel = h01rel + 0.5 * (e["u_m_s"] ** 2 - i["u_m_s"] ** 2)
                t02rel = gas.t_from_h(h02rel, guess=t01rel + 30)
                p02rel_ideal = p01rel * math.exp((gas.phi(t02rel) - gas.phi(t01rel)) / gas.R_AIR)
                p02rel = p02rel_ideal - omega * (p01rel - p1)
                t2, p2 = _static_from_total(t02rel, p02rel, e["m_rel"])
                h02 = gas.h(t2) + 0.5 * (e["m_abs"] * _sound(t2)) ** 2
                t02 = gas.t_from_h(h02, guess=t2 + 40)
                p02 = p2 * math.exp((gas.phi(t02) - gas.phi(t2)) / gas.R_AIR)
            else:
                t1, p1 = _static_from_total(st["t0"], st["p0"], i["m_abs"])
                p02 = st["p0"] - omega * (st["p0"] - p1)
                t02 = st["t0"]
            state[k] = dict(p0=p02, t0=t02)
            out.append(dict(row=_row_key(row), sl=k, pct_imm=e["pct_imm"],
                            pr_model=p02 / p_inlet * ref[k]["pt_ratio"],
                            pr_printed=e["pt_ratio"], tr_model=t02 / t_inlet * ref[k]["tt_ratio"],
                            tr_printed=e["tt_ratio"]))
    return out, state


def _sound(ts, far=0.0):
    cp = gas.cp(ts, far)
    return math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)


def rollup():
    xxi, _, stagewise, pub = load()
    r1 = efficiency_from_printed_ratios()
    ogv = [x for x in r1 if x["row"] == "S10"]
    # flow-weighted by annulus area per streamline at the OGV exit
    st = {s["sl"]: s for s in _stations(xxi, xxi["rows"][-1], "exit")}
    weights = []
    radii = sorted((s["radius_cm"], s["sl"]) for s in st.values())
    for i, (r, k) in enumerate(radii):
        lo = radii[i - 1][0] if i else r
        hi = radii[i + 1][0] if i + 1 < len(radii) else r
        weights.append((k, max(hi - lo, 1e-6) * r))
    wsum = sum(w for _, w in weights)
    by_sl = {x["sl"]: x for x in ogv}
    eta_avg = sum(by_sl[k]["eta"] * w for k, w in weights) / wsum
    pr_avg = sum(by_sl[k]["pr"] * w for k, w in weights) / wsum
    chain, _ = pressure_chain_from_losses()
    ogv_chain = [x for x in chain if x["row"] == "S10"]
    return dict(eta_area_weighted=eta_avg, pr_area_weighted=pr_avg, per_sl=ogv, chain=ogv_chain,
                design_intent=stagewise["design_point"]["efficiency_adiabatic"],
                design_pr=stagewise["design_point"]["pressure_ratio_design"],
                table_xi=pub["component_performance"]["compressor_efficiency"])


def main_4b():
    xxi, *_ = load()
    r = rollup()
    print("route 1 — adiabatic efficiency from the printed pressure and temperature ratios")
    print(f"{'sl':>3}{'imm %':>7}{'PR':>8}{'TR':>7}{'eta':>8}{'cum_eff printed':>17}")
    cum = {s["sl"]: s for s in _sl(xxi, xxi["rows"][-1])}
    for x in sorted(r["per_sl"], key=lambda y: y["sl"]):
        c = cum.get(x["sl"], {}).get("cum_eff")
        print(f"{x['sl']:>3}{x['pct_imm']:>7.1f}{x['pr']:>8.3f}{x['tr']:>7.4f}{x['eta']:>8.4f}{(f'{c:.4f}' if c else '-'):>17}")
    print(f"\narea-weighted: PR {r['pr_area_weighted']:.3f}, eta {r['eta_area_weighted']:.4f}")
    print(f"published: design intent {r['design_intent']} at {r['design_pr']}:1; Table XI {r['table_xi']}; ICLS as tested 0.856")
    print("\nroute 2 — the pressure chain rebuilt from the printed loss coefficients alone")
    print(f"{'sl':>3}{'imm %':>7}{'PR model':>10}{'PR printed':>12}{'diff %':>9}")
    d = []
    for x in sorted(r["chain"], key=lambda y: y["sl"]):
        diff = (x["pr_model"] / x["pr_printed"] - 1) * 100
        d.append(diff)
        print(f"{x['sl']:>3}{x['pct_imm']:>7.1f}{x['pr_model']:>10.3f}{x['pr_printed']:>12.3f}{diff:>9.2f}")
    print(f"mean {sum(d) / len(d):+.2f} %, rms {math.sqrt(sum(y * y for y in d) / len(d)):.2f} %")


if __name__ == "__main__" and "--4b" in _sys.argv:
    main_4b()


# ---------------------------------------------------------------------------
# Unit 5: the HPC stage by stage. Every curve the HPC report plots per stage
# (Figs 11, 14, 17, 18) recomputed from Table XXI's velocity data, plus
# de Haller, which the report does not plot.
# ---------------------------------------------------------------------------

def stagewise_from_table_xxi(t_inlet=T_REF_INLET):
    """per-stage quantities at the pitch streamline, from the through-flow"""
    xxi, _, stagewise, _ = load()
    rows = {_row_key(r): r for r in xxi["rows"]}
    igv = xxi["rows"][0]
    ref = min(_stations(xxi, igv, "inlet"), key=lambda s: abs(s["pct_imm"] - 50))
    out = []
    for n in range(1, 11):
        rot, sta = rows[f"R{n}"], rows[f"S{n}"]
        ri = min(_stations(xxi, rot, "inlet"), key=lambda s: abs(s["pct_imm"] - 50))
        re_ = min(_stations(xxi, rot, "exit"), key=lambda s: abs(s["pct_imm"] - 50))
        si = min(_stations(xxi, sta, "inlet"), key=lambda s: abs(s["pct_imm"] - 50))
        se = min(_stations(xxi, sta, "exit"), key=lambda s: abs(s["pct_imm"] - 50))
        rd = min(_sl(xxi, rot), key=lambda s: abs(s["pct_imm"] - 50))
        sd = min(_sl(xxi, sta), key=lambda s: abs(s["pct_imm"] - 50))
        # temperature rise across the stage, referred to the IGV inlet
        dt = (se["tt_ratio"] - ri["tt_ratio"]) / ref["tt_ratio"] * t_inlet
        # de Haller: the relative velocity ratio across each row
        w1 = math.hypot(ri["cz_m_s"], ri["u_m_s"] - ri["cz_m_s"] * math.tan(math.radians(ri["m_abs"] * 0)))
        w_in = ri["cz_m_s"] / math.cos(math.radians(ri["beta_deg"]))
        w_out = re_["cz_m_s"] / math.cos(math.radians(re_["beta_deg"]))
        c_in = si["cz_m_s"] / math.cos(math.radians(si["alpha_deg"]))
        c_out = se["cz_m_s"] / math.cos(math.radians(se["alpha_deg"]))
        out.append(dict(stage=n, dt=dt, pr_stage=se["pt_ratio"] / ri["pt_ratio"],
                        df_rotor=rd["df"], df_stator=sd["df"],
                        loss_rotor=rd["loss"], loss_stator=sd["loss"],
                        solidity_rotor=rd["solidity"], solidity_stator=sd["solidity"],
                        de_haller_rotor=w_out / w_in, de_haller_stator=c_out / c_in,
                        m_rel_in=ri["m_rel"], u=ri["u_m_s"]))
    return out, stagewise


def overall_temperature_rise(t_inlet=T_REF_INLET):
    """the overall temperature rise at the pitch streamline and area-weighted
    across the span, for comparison with Fig 14's printed total"""
    xxi = load()[0]
    igv, ogv = xxi["rows"][0], xxi["rows"][-1]
    ref = {s["sl"]: s for s in _stations(xxi, igv, "inlet")}
    ex = {s["sl"]: s for s in _stations(xxi, ogv, "exit")}
    radii = sorted((s["radius_cm"], s["sl"]) for s in ex.values())
    w = []
    for i, (r, k) in enumerate(radii):
        lo = radii[i - 1][0] if i else r
        hi = radii[i + 1][0] if i + 1 < len(radii) else r
        w.append((k, max(hi - lo, 1e-6) * r))
    tot = sum(x for _, x in w)
    tr_aw = sum(ex[k]["tt_ratio"] / ref[k]["tt_ratio"] * x for k, x in w) / tot
    kp = min(ex, key=lambda k: abs(ex[k]["pct_imm"] - 53))
    tr_pitch = ex[kp]["tt_ratio"] / ref[kp]["tt_ratio"]
    return dict(pitch_K=(tr_pitch - 1) * t_inlet, area_weighted_K=(tr_aw - 1) * t_inlet,
                tr_pitch=tr_pitch, tr_area_weighted=tr_aw)


def main_unit5():
    st, sw = stagewise_from_table_xxi()
    g = sw["stagewise"]
    print(f"{'st':>3}{'dT K':>7}{'Fig14':>7}{'diff':>6}{'PR':>7}"
          f"{'DF_R':>7}{'Fig18':>7}{'DF_S':>7}{'Fig18':>7}"
          f"{'w_R':>7}{'Fig17':>7}{'w_S':>7}{'Fig17':>7}"
          f"{'sig_R':>7}{'Fig11':>7}{'dH_R':>7}{'dH_S':>7}{'M_rel':>7}")
    for i, s in enumerate(st):
        print(f"{s['stage']:>3}{s['dt']:>7.1f}{g['temperature_rise_C']['per_stage'][i]:>7.1f}"
              f"{s['dt'] - g['temperature_rise_C']['per_stage'][i]:>6.1f}{s['pr_stage']:>7.3f}"
              f"{s['df_rotor']:>7.3f}{g['diffusion_factor_pitch']['rotors'][i]:>7.3f}"
              f"{s['df_stator']:>7.3f}{g['diffusion_factor_pitch']['stators'][i]:>7.3f}"
              f"{s['loss_rotor']:>7.4f}{g['loss_coefficient_pitch']['rotors'][i]:>7.4f}"
              f"{s['loss_stator']:>7.4f}{g['loss_coefficient_pitch']['stators'][i]:>7.4f}"
              f"{s['solidity_rotor']:>7.3f}{g['pitch_solidity']['rotors'][i]:>7.3f}"
              f"{s['de_haller_rotor']:>7.3f}{s['de_haller_stator']:>7.3f}{s['m_rel_in']:>7.3f}")
    dt_sum = sum(s["dt"] for s in st)
    o = overall_temperature_rise()
    tot = g["temperature_rise_C"]["total"]
    print(f"\ntemperature rise, overall: pitch {o['pitch_K']:.1f} K ({(o['pitch_K'] / tot - 1) * 100:+.2f} %),"
          f" area-weighted {o['area_weighted_K']:.1f} K ({(o['area_weighted_K'] / tot - 1) * 100:+.2f} %)"
          f" vs Fig 14's printed total {tot} K  (stagewise sum at pitch {dt_sum:.1f})")
    dh = [s["de_haller_rotor"] for s in st] + [s["de_haller_stator"] for s in st]
    print(f"de Haller (not published): rotors {min(s['de_haller_rotor'] for s in st):.3f}-{max(s['de_haller_rotor'] for s in st):.3f},"
          f" stators {min(s['de_haller_stator'] for s in st):.3f}-{max(s['de_haller_stator'] for s in st):.3f}; limit 0.72, worst {min(dh):.3f}")


if __name__ == "__main__" and "--unit5" in _sys.argv:
    main_unit5()
