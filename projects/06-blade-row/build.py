"""Generate the reference blade row, stator and stage, and export them.

Run inside the pyOCC environment:

    conda run -n pyocc_env python build.py
"""

import math

from src.annulus import axial_extent, full_assembly
from src.blade import BladeRow
from src.deviation import DeviationCorrectedDesign
from src.drawing import general_arrangement
from src.export import to_glb, to_step
from src.meridional import annulus_area, converging_annulus_exit
from src.plotting import (
    deviation_comparison_figure,
    meridional_flowpath_figure,
    section_comparison_figure,
    velocity_triangle_figure,
)
from src.stage import converging_stage_assembly, stage_assembly, stator_offset
from src.velocity_triangles import RotorDesignPoint, StatorDesignPoint

# How much the annulus narrows across the stage, exit area / inlet area — a
# chosen input sitting in a plausible single-stage subsonic range (typically
# 0.85-0.95), not derived from an actual compression calculation: see
# meridional.converging_annulus_exit's docstring for why that would need a
# stage thermodynamic model this project does not have.
CONVERGING_AREA_RATIO = 0.90

# A first-stage-like rotor: hub-to-tip ratio 0.57, 8000 rpm, stage loading
# psi = dW/U_mean^2 ~ 0.35 — an unexceptional subsonic design point, chosen
# to sit in typical ranges rather than to flatter any one number.
ROTOR_DESIGN = RotorDesignPoint(
    axial_velocity=150.0,
    omega=8000.0 * 2 * math.pi / 60.0,
    mean_radius=0.275,
    exit_swirl_mean=80.0,
)

ROTOR = BladeRow(
    hub_radius=0.20,
    tip_radius=0.35,
    n_blades=32,
    root_chord=0.062,
    tip_chord=0.052,
    thickness=0.06,
    design=ROTOR_DESIGN,
)

# The stator's inlet swirl is the rotor's exit swirl by definition of a
# stage — same number, not a separately chosen one. 45 blades against the
# rotor's 32 share no common factor, the usual way to avoid a resonant
# blade-passing excitation between the two rows.
STATOR_DESIGN = StatorDesignPoint(
    axial_velocity=ROTOR_DESIGN.axial_velocity,
    mean_radius=ROTOR_DESIGN.mean_radius,
    inlet_swirl_mean=ROTOR_DESIGN.exit_swirl_mean,
)

STATOR = BladeRow(
    hub_radius=0.20,
    tip_radius=0.35,
    n_blades=45,
    root_chord=0.050,
    tip_chord=0.045,
    thickness=0.08,
    design=STATOR_DESIGN,
)


def _print_row(name: str, row: BladeRow) -> None:
    d = row.design
    print(f"\n{name}")
    print(f"{'  n_blades':<24}{row.n_blades}")
    print(f"{'  root / tip chord':<24}{row.root_chord:.4f} / {row.tip_chord:.4f} m")
    for r in (row.hub_radius, row.mean_radius, row.tip_radius):
        print(f"    r={r:.3f}  stagger={math.degrees(d.stagger_angle(r)):5.1f} deg  "
              f"camber={math.degrees(d.camber_angle(r)):5.1f} deg  "
              f"solidity={row.solidity_at(r):.3f}")


def main() -> None:
    print(f"{'hub / tip radius':<24}{ROTOR.hub_radius:.3f} / {ROTOR.tip_radius:.3f} m")
    print(f"{'axial velocity Ca':<24}{ROTOR_DESIGN.axial_velocity:.1f} m/s")
    print(f"{'rotor speed':<24}{ROTOR_DESIGN.omega * 60 / (2 * math.pi):.0f} rpm")
    print(f"{'specific work dW':<24}"
          f"{ROTOR_DESIGN.specific_work(ROTOR.mean_radius):.1f} J/kg "
          f"(constant across span, by design)")
    print(f"{'stage loading psi':<24}"
          f"{ROTOR_DESIGN.specific_work(ROTOR.mean_radius) / ROTOR_DESIGN.blade_speed(ROTOR.mean_radius)**2:.3f}")

    _print_row("Rotor", ROTOR)
    _print_row("Stator", STATOR)

    rotor_volume = ROTOR.measured_volume()
    stator_volume = STATOR.measured_volume()
    print(f"\n{'single rotor-blade volume':<28}{rotor_volume * 1e6:.2f} cm^3")
    print(f"{'single stator-blade volume':<28}{stator_volume * 1e6:.2f} cm^3")

    rotor_assembly = full_assembly(ROTOR)
    print("\nwrote", to_step(rotor_assembly, "exports/blade_row.step"))
    print("wrote", to_glb(rotor_assembly, "exports/blade_row.glb"), "— web viewer mesh")

    stage = stage_assembly(ROTOR, STATOR)
    print("wrote", to_step(stage, "exports/stage.step"))
    print("wrote", to_glb(stage, "exports/stage.glb"), "— web viewer mesh")

    # Converging annulus: the stator sits in a smaller-area annulus than
    # the rotor, holding mean radius constant (see meridional.py), so its
    # own free-vortex design point keeps the rotor's mean_radius unchanged
    # — only the span it's swept across shrinks. Separate export from the
    # constant-annulus stage above, not a replacement: exports/stage.step
    # is already in use (the site's CAD gallery) and a constant annulus is
    # still a legitimate (if simplified) v1 scope.
    converged_hub, converged_tip = converging_annulus_exit(
        ROTOR.hub_radius, ROTOR.tip_radius, CONVERGING_AREA_RATIO
    )
    converging_stator_design = StatorDesignPoint(
        axial_velocity=ROTOR_DESIGN.axial_velocity,
        mean_radius=ROTOR_DESIGN.mean_radius,
        inlet_swirl_mean=ROTOR_DESIGN.exit_swirl_mean,
    )
    converging_stator = BladeRow(
        hub_radius=converged_hub,
        tip_radius=converged_tip,
        n_blades=45,
        root_chord=0.050,
        tip_chord=0.045,
        thickness=0.08,
        design=converging_stator_design,
    )
    print(f"\n{'converging annulus, area ratio':<32}{CONVERGING_AREA_RATIO:.2f}")
    print(f"{'rotor hub / tip':<32}{ROTOR.hub_radius:.4f} / {ROTOR.tip_radius:.4f} m  "
          f"(area {annulus_area(ROTOR.hub_radius, ROTOR.tip_radius):.5f} m^2)")
    print(f"{'stator hub / tip':<32}{converged_hub:.4f} / {converged_tip:.4f} m  "
          f"(area {annulus_area(converged_hub, converged_tip):.5f} m^2)")
    _print_row("Converging stator", converging_stator)

    converging_stage = converging_stage_assembly(ROTOR, converging_stator)
    print("\nwrote", to_step(converging_stage, "exports/stage-converging.step"))
    print("wrote", to_glb(converging_stage, "exports/stage-converging.glb"), "— web viewer mesh")

    rotor_x0, rotor_x1 = axial_extent(ROTOR)
    stator_x0, stator_x1 = axial_extent(converging_stator)
    dx = stator_offset(ROTOR, converging_stator)

    print("\nwrote", velocity_triangle_figure(ROTOR, "figures/velocity-triangles.png"))
    for theme, suffix in (("light", ""), ("dark", "-dark")):
        print("wrote", section_comparison_figure(
            ROTOR, f"figures/hub-tip-sections{suffix}.png", theme=theme))
        print("wrote", meridional_flowpath_figure(
            ROTOR.hub_radius, ROTOR.tip_radius,
            converging_stator.hub_radius, converging_stator.tip_radius,
            rotor_x0, rotor_x1, stator_x0 + dx, stator_x1 + dx,
            f"figures/meridional-flowpath{suffix}.png", theme=theme,
        ))

    # Deviation correction (Carter's rule) — opt-in via a wrapper around
    # ROTOR_DESIGN, not a change to it: DeviationCorrectedDesign duck-types
    # velocity_triangles.py's stagger_angle/camber_angle interface, so
    # ROTOR itself (and exports/blade_row.step, already on the site) is
    # untouched, and DEVIATION_ROTOR is a genuinely separate blade row
    # built from corrected angles. space_chord_ratio reuses ROTOR's own
    # solidity_at — chord and blade count are geometry, not part of what
    # deviation correction changes.
    deviation_design = DeviationCorrectedDesign(
        base=ROTOR_DESIGN, space_chord_ratio=lambda r: 1.0 / ROTOR.solidity_at(r)
    )
    DEVIATION_ROTOR = BladeRow(
        hub_radius=ROTOR.hub_radius,
        tip_radius=ROTOR.tip_radius,
        n_blades=ROTOR.n_blades,
        root_chord=ROTOR.root_chord,
        tip_chord=ROTOR.tip_chord,
        thickness=ROTOR.thickness,
        design=deviation_design,
    )
    print(f"\n{'deviation angle, hub/mean/tip':<32}", end="")
    print(", ".join(
        f"{math.degrees(deviation_design.deviation_angle(r)):.2f} deg"
        for r in (ROTOR.hub_radius, ROTOR.mean_radius, ROTOR.tip_radius)
    ))
    _print_row("Deviation-corrected rotor", DEVIATION_ROTOR)

    deviation_assembly = full_assembly(DEVIATION_ROTOR)
    print("\nwrote", to_step(deviation_assembly, "exports/blade_row-deviation-corrected.step"))
    print("wrote", to_glb(deviation_assembly, "exports/blade_row-deviation-corrected.glb"),
          "— web viewer mesh")

    for theme, suffix in (("light", ""), ("dark", "-dark")):
        print("wrote", deviation_comparison_figure(
            ROTOR, DEVIATION_ROTOR, f"figures/deviation-comparison{suffix}.png", theme=theme))

    # Dimensioned general arrangement drawing, in the style of project 04's
    # — the reference (uncorrected) ROTOR, not the deviation-corrected
    # variant, since it is what exports/blade_row.step and the site's CAD
    # gallery already show.
    general_arrangement(ROTOR, "drawings/blade-row-ga.png", drawing_no="BR-001",
                        row_name="ROTOR")
    print("\nwrote drawings/blade-row-ga.png")


if __name__ == "__main__":
    main()
