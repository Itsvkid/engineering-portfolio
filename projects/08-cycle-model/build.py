"""Solve the reference turbofan cycle and print/plot the result.

Dimensions and design parameters are representative of a mid-size subsonic
civil turbofan design point — chosen to sit in a plausible range, not
reverse-engineered from any specific real engine. See the README for what
"validated" means here.

Run:
    python build.py
"""

import math

from src.cycle import TurbofanDesignPoint, solve_cycle, solve_cycle_with_cd_nozzle
from src.gas import ideal_brayton_efficiency
from src.off_design import solve_off_design
from src.plotting import station_ladder_figure, throttle_sweep_figure

REFERENCE = TurbofanDesignPoint(
    altitude=10668.0,          # 35,000 ft
    mach=0.78,
    core_mass_flow=40.0,       # kg/s
    bypass_ratio=6.0,
    fan_pressure_ratio=1.6,
    booster_pressure_ratio=1.6,
    hpc_pressure_ratio=14.0,
    turbine_entry_temperature=1650.0,  # K
)


def main() -> None:
    d = REFERENCE
    c = solve_cycle(d)
    s = c.stations

    print(f"{'altitude':<26}{d.altitude:.0f} m   mach {d.mach:.2f}")
    print(f"{'overall pressure ratio':<26}{d.overall_pressure_ratio:.2f}")
    print(f"{'bypass ratio':<26}{d.bypass_ratio:.1f}")
    print(f"{'turbine entry temperature':<26}{d.turbine_entry_temperature:.0f} K")
    print()
    print(f"{'station':<22}{'T, K':>10}{'p, kPa':>12}")
    for name, st in (
        ("fan face", s.fan_face), ("fan exit", s.fan_exit),
        ("booster exit", s.booster_exit), ("HPC exit", s.hpc_exit),
        ("combustor exit", s.combustor_exit), ("HPT exit", s.hpt_exit),
        ("LPT exit", s.lpt_exit),
    ):
        print(f"{name:<22}{st.t:>10.1f}{st.p/1000:>12.1f}")
    print(f"{'core nozzle exit':<22}{s.core_nozzle.t:>10.1f}{s.core_nozzle.p/1000:>12.1f}"
          f"   V={s.core_nozzle.velocity:.1f} m/s"
          f"   {'choked' if s.core_nozzle.choked else 'unchoked'}")
    print(f"{'bypass nozzle exit':<22}{s.bypass_nozzle.t:>10.1f}{s.bypass_nozzle.p/1000:>12.1f}"
          f"   V={s.bypass_nozzle.velocity:.1f} m/s"
          f"   {'choked' if s.bypass_nozzle.choked else 'unchoked'}")

    core_pr_available = s.lpt_exit.p / c.ambient_pressure
    print(f"\n{'core nozzle PR available':<26}{core_pr_available:.2f}  "
          f"(underexpanded — see README)" if s.core_nozzle.choked else "")

    print(f"\n{'fuel-air ratio':<26}{c.fuel_air_ratio:.4f}")
    print(f"{'net thrust':<26}{c.net_thrust/1000:.2f} kN")
    print(f"{'TSFC':<26}{c.tsfc_g_per_kns:.2f} g/(kN.s)")
    print(f"{'thermal efficiency':<26}{c.thermal_efficiency*100:.1f} %")
    print(f"{'propulsive efficiency':<26}{c.propulsive_efficiency*100:.1f} %")
    print(f"{'overall efficiency':<26}{c.overall_efficiency*100:.1f} %")
    print(f"{'ideal Brayton efficiency':<26}{ideal_brayton_efficiency(d.overall_pressure_ratio)*100:.1f} %  "
          f"(no losses, no ram, fully-expanded nozzle — an upper bound, not a target)")

    print("\nwrote", station_ladder_figure(c, "figures/station-ladder.png"))
    print("wrote", station_ladder_figure(c, "figures/station-ladder-dark.png", dark=True))

    # Convergent-divergent core nozzle — opt-in, see README "Convergent-
    # divergent core nozzle". Everything upstream of the core nozzle is
    # identical to the convergent solve above; only the final expansion
    # differs.
    cd = solve_cycle_with_cd_nozzle(d)
    cn = cd.stations.core_nozzle
    print(f"\n{'C-D core nozzle exit':<26}{cn.t:>10.1f} K{cn.p/1000:>10.1f} kPa"
          f"   V={cn.velocity:.1f} m/s   M={cn.mach:.2f}"
          f"   {'supersonic' if cn.supersonic else 'subsonic'}")
    print(f"{'C-D net thrust':<26}{cd.net_thrust/1000:.2f} kN"
          f"  ({(cd.net_thrust/c.net_thrust - 1)*100:+.1f}% vs. convergent)")
    print(f"{'C-D TSFC':<26}{cd.tsfc_g_per_kns:.2f} g/(kN.s)"
          f"  ({(cd.tsfc_g_per_kns/c.tsfc_g_per_kns - 1)*100:+.1f}% vs. convergent)")

    # Part-throttle sweep — simplified single-parameter model, see
    # src/off_design.py for exactly what it does and does not capture.
    # 0.62 is not an arbitrary floor: it is where this specific reference
    # design's turbine entry temperature scales down to
    # TurbofanDesignPoint's own 1000 K plausibility guard.
    throttles = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.62]
    off_design_cycles = [solve_off_design(d, t) for t in throttles]
    print(f"\n{'throttle':<10}{'thrust, kN':>12}{'TSFC':>10}{'thermal eff':>13}")
    for t, oc in zip(throttles, off_design_cycles):
        print(f"{t:<10.2f}{oc.net_thrust/1000:>12.2f}{oc.tsfc_g_per_kns:>10.2f}"
              f"{oc.thermal_efficiency*100:>12.1f}%")

    for suffix, dark in (("", False), ("-dark", True)):
        print("wrote", throttle_sweep_figure(
            throttles, [oc.net_thrust / 1000 for oc in off_design_cycles],
            [oc.tsfc_g_per_kns for oc in off_design_cycles],
            f"figures/throttle-sweep{suffix}.png", dark=dark,
        ))


if __name__ == "__main__":
    main()
