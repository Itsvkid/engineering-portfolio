#!/usr/bin/env python3
"""Print the three-rating table against Table XII, and the mixer check."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from e3cycle.cycle import run_all, load_inputs, solve, solve_rating

def table(results, title):
    print(title)
    print(f"{'rating':<11}{'sfc':>8}{'XII':>8}{'diff%':>7}{'Fn kN':>7}{'W2c':>7}{'Wcore':>7}{'FAR':>8}{'trans%':>7}{'p6c/p6b':>8}{'HPT':>6}{'LPT':>6}{'T3':>6}{'T4':>6}{'T5':>6}{'ideal mix%':>11}")
    for r in results:
        s = r.stations
        print(f"{r.rating:<11}{r.sfc_kg_N_h:>8.4f}{r.sfc_published:>8.4f}{(r.sfc_kg_N_h/r.sfc_published-1)*100:>7.2f}{r.fn_N/1000:>7.1f}{r.w2_corrected_kg_s:>7.0f}{r.w_core_kg_s:>7.1f}{r.far_combustor:>8.4f}{r.transition_loss*100:>7.2f}{r.p5_over_p13:>8.3f}{r.hpt_pr:>6.2f}{r.lpt_pr:>6.2f}{s['t3']:>6.0f}{s['t4']:>6.0f}{s['t5']:>6.0f}{r.ideal_mixing_gain_pct:>11.2f}")

if __name__ == "__main__":
    inp = load_inputs()
    table(run_all(inp), "E3 FPS ratings, Table XI components, Table XII ratios")
    mc = inp.ratings[1]
    loss = 0.0057   # Table XXIII mixer pressure loss, removed for the separate-flow engine
    sep = solve(mc, inp, mixed=False, extra_loss=-loss)
    sep_same = solve(mc, inp, mixed=False)
    for eff in (0.75, 0.79, 0.838, 0.85):
        m = solve(mc, inp, mixer_eff=eff)
        print(f"mixer {eff*100:4.1f} %: sfc {m.sfc_kg_N_h:.5f}; gain vs separate-flow without the mixer loss {(1-m.sfc_kg_N_h/sep.sfc_kg_N_h)*100:.2f} %, vs same ducts {(1-m.sfc_kg_N_h/sep_same.sfc_kg_N_h)*100:.2f} %")
    print("Table XXIII: 75 % -> 3.1, 79 % -> 2.6, 85 % -> 2.9 (with 0.20/0.57/0.57 % loss)")
    print(f"bleed ports, fraction of HPC exit total pressure: stage 5 {inp.bleed_port_fraction[5]:.3f}, stage 7 {inp.bleed_port_fraction[7]:.3f}")
    print("\nsensitivities at max cruise (sfc % change):")
    base = solve_rating(mc, inp).sfc_kg_N_h
    for label, kw in (("shaft efficiency 0.995", dict(eta_mech=0.995)), ("mixer loss +0.57 % on both streams", dict(extra_loss=0.0057)), ("separate flow, same ducts", dict(mixed=False))):
        print(f"  {label:<36}{(solve_rating(mc, inp, **kw).sfc_kg_N_h/base-1)*100:+.2f}")
