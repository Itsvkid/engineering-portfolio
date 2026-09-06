"""Stage D1, unit D1: the overall cooling effectiveness of the E3's four
cooled turbine rows.

Before any cooling network is built, there is a question worth asking of
the published data alone: do the four cooled rows -- two vanes and two
blades, at coolant flows spanning 0.76 % to 6.30 % of W25 -- lie on one
curve?

The overall (or bulk) cooling effectiveness is

    phi = (T_gas - T_metal) / (T_gas - T_coolant)

and CR-167955 prints all three temperatures, and the coolant flow, for
every cooled row at the same condition: hot-day steady-state takeoff.
STEP0.md, unit D1.

Numbering note: units 16 and 17 are another session's (C3 booster and
stacking), so Stage D's findings start at 58."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA


@dataclass
class CooledRow:
    name: str
    kind: str
    t_gas_C: float
    t_coolant_C: float
    t_metal_C: float
    wc_pct_w25: float
    src: str

    @property
    def phi(self):
        return (self.t_gas_C - self.t_metal_C) / (self.t_gas_C - self.t_coolant_C)

    @property
    def ratio(self):
        """phi / (1 - phi) -- the form in which a convective balance is linear
        in the internal heat-capacity rate"""
        return self.phi / (1 - self.phi)


def load():
    return yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())


def rows():
    """the four cooled rows, all at hot-day steady-state takeoff"""
    d = load()
    s1n = d["stage1_nozzle"]["metal_temperatures"]
    s1b = d["stage1_blade"]["metal_temperatures"]["conditions"]
    s2n = d["stage2_nozzle"]["temperatures"]["conditions_95pct_span"]
    s2b = d["stage2_rotor"]["metal_temperatures"]["conditions"]
    vane_flow = d["stage1_nozzle"]["vane_flow_split"]
    return [
        CooledRow("stage-1 vane", "vane", 1739.0, 610.0, s1n["pitch_line_bulk_C"],
                  vane_flow["forward_insert_pct_w25"] + vane_flow["aft_insert_pct_w25"],
                  "sec 3.2.1 p.31, Fig 16 p.33 (hot streak); flows Fig 13(b)"),
        CooledRow("stage-1 blade", "blade", s1b["t_tb_C"], s1b["t_cp_C"], s1b["t_bulk_C"],
                  s1b["w_coolant_pct_w25"], "Fig 27 p.47, sec 3.2.2 p.45"),
        # The stage-2 vane is printed at 95 % SPAN, not at the pitch line
        # like the other three: that is where gas bending makes it
        # life-limiting, not where it is hottest. Fig 33 also gives the
        # 65 % span bulk, and the gas profile gives the temperature there,
        # so a like-for-like point is available -- see finding 60.
        CooledRow("stage-2 vane", "vane", s2n["t_gas_C"], s2n["t_coolant_C"], s2n["t_bulk_C"],
                  d["stage2_nozzle"]["flows_pct_w25"]["vane_cooling"],
                  "Fig 33 pp.55-56 at 95 % span; flows sec 3.2.4 p.49"),
        CooledRow("stage-2 blade", "blade", s2b["t_tb_C"], s2b["t_cp_C"], s2b["t_bulk_C"],
                  s2b["w_c_pct_w25"], "Fig 35 p.58, sec 3.2.5 p.54"),
    ]


def fit(rs=None):
    """least squares on log(phi/(1-phi)) against log(Wc)"""
    rs = rs or rows()
    xs = [math.log(r.wc_pct_w25) for r in rs]
    ys = [math.log(r.ratio) for r in rs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    n = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    c = math.exp(my - n * mx)
    pred = [c * r.wc_pct_w25 ** n for r in rs]
    obs = [r.ratio for r in rs]
    mean_obs = statistics.mean(obs)
    ss_res = sum((o - p) ** 2 for o, p in zip(obs, pred))
    ss_tot = sum((o - mean_obs) ** 2 for o in obs)
    return dict(coefficient=c, exponent=n, r2=1 - ss_res / ss_tot,
                predicted=pred, observed=obs,
                residual_pct=[(p / o - 1) * 100 for o, p in zip(obs, pred)])


def stage2_vane_at_65pct_span():
    """the same vane at the span comparable to the other three rows'
    pitch sections. Fig 33 prints the 65 % bulk and the gas profile gives
    the local peak; the coolant temperature is the vane's."""
    d = load()
    n = d["stage2_nozzle"]
    return CooledRow("stage-2 vane @65%", "vane",
                     n["gas_temperature_profile"]["peak_C"]["at_65pct_span"],
                     n["temperatures"]["conditions_95pct_span"]["t_coolant_C"],
                     n["temperatures"]["bulk_by_span_C"]["pct_65"],
                     n["flows_pct_w25"]["vane_cooling"],
                     "Fig 33 bulk_by_span_C 65 %; gas profile sec 3.2.4 p.54")


DITTUS_BOELTER_EXPONENT = 0.8


if __name__ == "__main__":
    rs = rows()
    f = fit(rs)
    print("E3 HPT cooled rows, hot-day steady-state takeoff (CR-167955 sec 3.2)")
    print(f"{'row':<16}{'T_gas C':>9}{'T_cool C':>10}{'T_metal C':>11}{'Wc % W25':>10}"
          f"{'phi':>8}{'phi/(1-phi)':>13}")
    for r in rs:
        print(f"{r.name:<16}{r.t_gas_C:>9.0f}{r.t_coolant_C:>10.0f}{r.t_metal_C:>11.0f}"
              f"{r.wc_pct_w25:>10.2f}{r.phi:>8.3f}{r.ratio:>13.3f}")
    print(f"\nfit:  phi/(1-phi) = {f['coefficient']:.4f} x Wc^{f['exponent']:.3f}"
          f"      R^2 = {f['r2']:.4f}  over {len(rs)} rows")
    print(f"{'row':<16}{'observed':>10}{'fitted':>9}{'residual':>10}")
    for r, o, p, d in zip(rs, f["observed"], f["predicted"], f["residual_pct"]):
        print(f"{r.name:<16}{o:>10.3f}{p:>9.3f}{d:>9.1f} %")
    print(f"\nDittus-Boelter puts internal h ~ Re^0.8, so a coolant-flow exponent"
          f" near {DITTUS_BOELTER_EXPONENT} is what the physics predicts; the fit gives {f['exponent']:.2f}")
    alt = stage2_vane_at_65pct_span()
    pred = f["coefficient"] * alt.wc_pct_w25 ** f["exponent"]
    print(f"\nThe stage-2 vane is the only row printed at 95 % SPAN rather than at the pitch line,")
    print(f"because gas bending makes it life-limiting there. At 65 % span, comparable to the others:")
    print(f"  T_gas {alt.t_gas_C:.0f} C, T_metal {alt.t_metal_C:.0f} C, phi {alt.phi:.3f}, "
          f"phi/(1-phi) {alt.ratio:.3f} vs fitted {pred:.3f}  ({(pred/alt.ratio-1)*100:+.1f} %)")
    print("  -- the outlier is a station mismatch, not a cooling anomaly.")
