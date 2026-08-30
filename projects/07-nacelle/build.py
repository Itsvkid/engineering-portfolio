"""Generate the reference nacelle, run the fit-recovery demo, and export.

Dimensions below are representative of a mid-size turbofan external cowl —
chosen to sit in a plausible range, not reverse-engineered from any specific
real engine. See the README for what "validated" means here: closed-form
limiting cases and kernel-vs-integration agreement, not a comparison against
a real wind-tunnel or CAD dataset this project does not have access to.

Run inside the pyOCC environment:

    conda run -n pyocc_env python build.py
"""

from src.cst import CSTCurve
from src.export import to_glb, to_step
from src.fit import fit_residual, fit_weights
from src.nacelle import CompleteNacelle, NacelleSolid
from src.plotting import complete_nacelle_figure, fit_demo_figure, meridian_figure
from src.profile import NacelleProfile

REFERENCE = NacelleProfile(
    length=3.0,
    curve=CSTCurve(r0=0.85, r1=0.60, weights=(0.6, 0.9, 0.5), n1=0.5, n2=0.5),
)

# Internal duct wall — the highlight-inward surface named in the README's
# Outstanding list. r0/r1 sit inside the external curve's by the lip and
# trailing-edge wall thickness (0.10 m each); weights chosen independently
# of the external curve's own shape (a real inlet duct's internal line
# doesn't have to track the external bulge) and checked, not assumed, to
# stay clear of it at every station — see internal_clearance_ok. Runs over
# the same length as the external cowl: this project does not model a
# separately-positioned fan face, so the duct is only defined as far as the
# cowl it sits inside.
INTERNAL_DUCT = NacelleProfile(
    length=REFERENCE.length,
    curve=CSTCurve(r0=0.75, r1=0.50, weights=(0.55, 0.65, 0.45), n1=0.5, n2=0.5),
)


def main() -> None:
    p = REFERENCE
    x_max, r_max = p.max_radius()
    print(f"{'length':<24}{p.length:.3f} m")
    print(f"{'highlight radius':<24}{p.highlight_radius:.3f} m")
    print(f"{'trailing radius':<24}{p.trailing_radius:.3f} m")
    print(f"{'max radius':<24}{r_max:.4f} m at x={x_max:.3f} m "
          f"({100*x_max/p.length:.1f}% of length)")
    print(f"{'predicted volume':<24}{p.predicted_volume():.4f} m^3")
    print(f"{'predicted total area':<24}{p.predicted_total_surface_area():.4f} m^2")

    solid = NacelleSolid(p)
    measured_v = solid.measured_volume()
    measured_s = solid.measured_surface_area()
    print(f"\n{'measured volume':<24}{measured_v:.4f} m^3  "
          f"({100*(measured_v/p.predicted_volume()-1):+.3f}% vs predicted)")
    print(f"{'measured total area':<24}{measured_s:.4f} m^2  "
          f"({100*(measured_s/p.predicted_total_surface_area()-1):+.3f}% vs predicted)")

    print("\nwrote", to_step(solid.build(), "exports/nacelle.step"))
    print("wrote", to_glb(solid.build(), "exports/nacelle.glb"), "— web viewer mesh")

    # Complete nacelle: external cowl + internal duct as one hollow solid —
    # the "internal duct / inlet surface" outstanding item. A separate
    # export from the external-only solid above, not a replacement: that
    # one is already in use (the site's CAD gallery), and "external cowl
    # only" was always a legitimate v1 scope, not a bug.
    complete = CompleteNacelle(external=p, internal=INTERNAL_DUCT)
    x_max_int, r_max_int = INTERNAL_DUCT.max_radius()
    predicted_mv = complete.predicted_material_volume()
    measured_mv = complete.measured_volume()
    predicted_ms = complete.predicted_total_surface_area()
    measured_ms = complete.measured_surface_area()
    print(f"\n{'internal duct max radius':<26}{r_max_int:.4f} m at "
          f"{100*x_max_int/INTERNAL_DUCT.length:.1f}% of length")
    print(f"{'predicted material volume':<26}{predicted_mv:.4f} m^3")
    print(f"{'measured material volume':<26}{measured_mv:.4f} m^3  "
          f"({100*(measured_mv/predicted_mv-1):+.3f}% vs predicted)")
    print(f"{'predicted total surface':<26}{predicted_ms:.4f} m^2")
    print(f"{'measured total surface':<26}{measured_ms:.4f} m^2  "
          f"({100*(measured_ms/predicted_ms-1):+.3f}% vs predicted)")
    print(f"{'material fraction of solid cowl':<26} "
          f"{100*measured_mv/measured_v:.1f}%")

    print("wrote", to_step(complete.build(), "exports/nacelle-complete.step"))
    print("wrote", to_glb(complete.build(), "exports/nacelle-complete.glb"), "— web viewer mesh")

    # Fit-recovery demo: sample the reference profile as if it were a point
    # cloud exported from CAD, then fit a fresh CST curve back to it and
    # report the residual — the actual mechanic behind "benchmarked against
    # commercial CAD output for dimensional accuracy" (see fit.py).
    target = [(psi, p.curve(psi)) for psi in [i / 60 for i in range(61)]]
    fitted_weights = fit_weights(target, r0=p.highlight_radius,
                                  r1=p.trailing_radius, order=3)
    fitted = CSTCurve(r0=p.highlight_radius, r1=p.trailing_radius,
                       weights=fitted_weights)
    residual = fit_residual(target, fitted)
    print(f"\n{'CST fit residual (RMS)':<24}{residual * 1000:.6f} mm "
          f"against a {len(target)}-point sampled profile")

    print()
    for theme, suffix in (("light", ""), ("dark", "-dark")):
        print("wrote", meridian_figure(p, f"figures/meridian-profile{suffix}.png", theme=theme))
        print("wrote", complete_nacelle_figure(
            p, INTERNAL_DUCT, f"figures/complete-nacelle{suffix}.png", theme=theme
        ))
    print("wrote", fit_demo_figure(p, fitted, "figures/fit-recovery.png"))


if __name__ == "__main__":
    main()
