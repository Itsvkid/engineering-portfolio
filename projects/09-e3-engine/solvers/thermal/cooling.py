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


# ---------------------------------------------------------------------------
# Unit D2: the chordwise metal temperature of the stage-1 blade.
#
# CR-167955 Fig 23 prints the external heat-transfer coefficient against
# surface distance from the stagnation point, and Fig 27 the metal
# temperatures. A steady balance on the wall gives, at each station,
#
#     T_m = (h_g T_aw + H_c T_c) / (h_g + H_c)
#
# with H_c = h_c (A_c/A_g) the internal conductance referred to the
# external area. Rearranged, the LOCAL effectiveness obeys
#
#     phi/(1 - phi) = H_c / h_g          (no film)
#
# so a plot against 1/h_g is a straight line THROUGH THE ORIGIN whose
# slope is H_c. That is the shape test, and it costs one parameter.
# ---------------------------------------------------------------------------

@dataclass
class ChordStation:
    name: str
    surface: str
    distance_cm: float
    h_gas: float
    t_metal_published_C: float


def _interp_pairs(x, pairs):
    pairs = sorted(pairs)
    if x <= pairs[0][0]:
        return pairs[0][1]
    if x >= pairs[-1][0]:
        return pairs[-1][1]
    for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pairs[-1][1]


def stage1_blade_stations():
    """the three chordwise points the work plan's D1 closure names, with the
    external heat-transfer coefficient read from Fig 23 at each"""
    d = load()
    b = d["stage1_blade"]
    h = b["external_heat_transfer_coefficient"]["surface_distance_from_stagnation_cm_and_h"]
    fig21 = b["fig21_metal_temperatures_C"]
    return [
        ChordStation("leading edge", "stagnation", 0.0,
                     _interp_pairs(0.0, h["suction_side"]), fig21["leading_edge"]),
        ChordStation("suction surface", "suction", 4.0,
                     _interp_pairs(4.0, h["suction_side"]), fig21["suction_surface"]),
        ChordStation("midchord", "suction", 2.0,
                     _interp_pairs(2.0, h["suction_side"]), fig21["midchord"]),
    ]


def blade_conditions():
    c = load()["stage1_blade"]["metal_temperatures"]["conditions"]
    return c["t_tb_C"], c["t_cp_C"], c["t_bulk_C"]


def local_effectiveness(t_metal, t_gas, t_cool):
    return (t_gas - t_metal) / (t_gas - t_cool)


def fit_internal_conductance(stations=None):
    """one parameter: the slope of phi/(1-phi) against 1/h_g, forced
    through the origin (least squares, no intercept)"""
    stations = stations or stage1_blade_stations()
    t_g, t_c, _ = blade_conditions()
    xs, ys = [], []
    for s in stations:
        phi = local_effectiveness(s.t_metal_published_C, t_g, t_c)
        xs.append(1.0 / s.h_gas)
        ys.append(phi / (1 - phi))
    slope = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
    implied = [y / x for x, y in zip(xs, ys)]
    return dict(H_c=slope, implied_per_station=implied,
                spread_pct=(max(implied) - min(implied)) / slope * 100)


def predict_chordwise(H_c=None, stations=None):
    stations = stations or stage1_blade_stations()
    H_c = H_c if H_c is not None else fit_internal_conductance(stations)["H_c"]
    t_g, t_c, _ = blade_conditions()
    out = []
    for s in stations:
        t_m = (s.h_gas * t_g + H_c * t_c) / (s.h_gas + H_c)
        out.append(dict(name=s.name, h_gas=s.h_gas, predicted_C=t_m,
                        published_C=s.t_metal_published_C,
                        error_K=t_m - s.t_metal_published_C))
    return out, H_c


def film_effectiveness_needed(station, H_c=None):
    """the film effectiveness that would close a station's error, i.e. the
    adiabatic wall temperature the metal implies once the internal
    conductance is fixed by the other stations"""
    t_g, t_c, _ = blade_conditions()
    H_c = H_c if H_c is not None else fit_internal_conductance()["H_c"]
    t_aw = (station.t_metal_published_C * (station.h_gas + H_c) - H_c * t_c) / station.h_gas
    return (t_g - t_aw) / (t_g - t_c)


LE_FILM_HOLES = dict(rows=3, holes_per_row=10, pct_w25=0.49, angle_deg=25, orientation="radial")
