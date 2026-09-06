"""Stage D3: the secondary-air network — does it add up, and does every
cavity have the pressure to keep hot gas out?

The work plan's D3 closure: *total secondary air lands at Table XI's
16.1 % of W25 and every cavity has a pressure that keeps hot gas out.*

Both halves are checkable from printed numbers. CR-167955 Table VII gives
the detailed-design flow budget item by item; CR-168219 Table XI gives the
final four streams. And Fig 13 gives the stage-1 nozzle's cavity static
pressures, the gas pressure they seal against, and the report's own
**backflow margin**, with its definition printed beside it:

    backflow margin = 100 (Ps_coolant − Pt_gas) / Pt_gas

so it can be recomputed rather than believed. STEP0.md, unit D3."""
from __future__ import annotations

from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA


def load():
    hpt = yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    return hpt, pub


@dataclass
class Stream:
    name: str
    pct_w25: float
    source: str
    charge: str


def detailed_budget():
    """CR-167955 Table VII, the detailed design: eight items"""
    hpt, _ = load()
    f = hpt["flows"]
    return [Stream(i["name"], i["pct"], i["source"], i["charge"]) for i in f["items"]], f["total_pct"]


def final_budget():
    """CR-168219 Table XI, the final FPS: four streams by source"""
    _, pub = load()
    c = pub["cooling_flows"]
    return {
        "CPD nonchargeable": c["cpd_nonchargeable"] * 100,
        "CPD chargeable": c["cpd_chargeable"] * 100,
        "stage 7": c["stage_7_cooling_and_purge"] * 100,
        "stage 5": c["stage_5_cooling_and_purge"] * 100,
    }


@dataclass
class Cavity:
    name: str
    coolant_static_MPa: float
    gas_total_MPa: float
    gas_static_MPa: float
    printed_margin_pct: float

    def margin_vs(self, gas_pressure):
        return 100.0 * (self.coolant_static_MPa - gas_pressure) / gas_pressure

    @property
    def margin_vs_total(self):
        return self.margin_vs(self.gas_total_MPa)

    @property
    def margin_vs_static(self):
        return self.margin_vs(self.gas_static_MPa)


def stage1_nozzle_cavities():
    hpt, _ = load()
    n = hpt["stage1_nozzle"]
    gas = n["supply_conditions"]["gas_at_vane"]
    cp = n["cavity_pressures"]
    return [
        Cavity("forward cavity", cp["forward_cavity"]["static_MPa"], gas["pt_MPa"],
               gas["ps_MPa"], cp["forward_cavity"]["backflow_margin_pct"]),
        Cavity("aft cavity", cp["aft_cavity"]["static_MPa"], gas["pt_MPa"],
               gas["ps_MPa"], cp["aft_cavity"]["backflow_margin_pct"]),
    ], cp["backflow_margin_definition"]


def supply_chain():
    """each cooled row's source, and why the report chose it"""
    hpt, _ = load()
    return hpt["supply_system"]


if __name__ == "__main__":
    items, total = detailed_budget()
    final = final_budget()
    print("1. Does the secondary air add up?")
    print(f"{'stream':<48}{'% W25':>8}{'source':>14}{'charge':>16}")
    for s in items:
        print(f"{s.name:<48}{s.pct_w25:>8.2f}{s.source:>14}{s.charge:>16}")
    print(f"{'detailed-design total (Table VII)':<48}{sum(s.pct_w25 for s in items):>8.2f}   printed {total}")
    print()
    for k, v in final.items():
        print(f"{'final FPS, ' + k:<48}{v:>8.2f}")
    print(f"{'final FPS total (Table XI)':<48}{sum(final.values()):>8.2f}   work plan D3 target 16.1")

    print("\n2. Does every cavity keep the hot gas out?")
    cavs, defn = stage1_nozzle_cavities()
    print(f"   definition as printed: {defn}")
    print(f"{'cavity':<18}{'Ps cool':>10}{'Pt gas':>9}{'Ps gas':>9}"
          f"{'vs Pt':>9}{'vs Ps':>9}{'printed':>9}{'matches':>10}")
    for c in cavs:
        which = "Pt" if abs(c.margin_vs_total - c.printed_margin_pct) < 0.1 else (
            "Ps" if abs(c.margin_vs_static - c.printed_margin_pct) < 0.1 else "neither")
        print(f"{c.name:<18}{c.coolant_static_MPa:>10.3f}{c.gas_total_MPa:>9.3f}{c.gas_static_MPa:>9.3f}"
              f"{c.margin_vs_total:>9.2f}{c.margin_vs_static:>9.2f}{c.printed_margin_pct:>9.2f}{which:>10}")

    print("\n3. Where each row's coolant comes from, and why")
    for row, d in supply_chain().items():
        if isinstance(d, dict) and "source" in d:
            why = d.get("why", "")
            print(f"   {row:<16} {d['source']}")
            if why:
                print(f"   {'':<16} why: {why[:110]}")
