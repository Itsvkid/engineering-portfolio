"""Generate the reference wing and export it.

Run inside the pyOCC environment:

    conda run -n pyocc_env python build.py
"""

from src.airfoil import NACA4
from src.drawing import general_arrangement
from src.export import to_glb, to_iges, to_step
from src.plotting import generate_all
from src.wing import Wing

REFERENCE = Wing(
    span=10.0,
    root_chord=1.6,
    taper_ratio=0.45,
    sweep_deg=25.0,
    dihedral_deg=5.0,
    twist_deg=3.0,
    section=NACA4.from_code("2412"),
)


def main() -> None:
    w = REFERENCE
    print(f"{'span':<22}{w.span:.3f} m")
    print(f"{'root / tip chord':<22}{w.root_chord:.3f} / {w.tip_chord:.3f} m")
    print(f"{'taper ratio':<22}{w.taper_ratio:.3f}")
    print(f"{'sweep (quarter-chord)':<22}{w.sweep_deg:.1f} deg")
    print(f"{'dihedral':<22}{w.dihedral_deg:.1f} deg")
    print(f"{'washout at tip':<22}{w.twist_deg:.1f} deg")
    print(f"{'planform area':<22}{w.area:.4f} m^2")
    print(f"{'aspect ratio':<22}{w.aspect_ratio:.4f}")
    print(f"{'MAC':<22}{w.mac:.4f} m at y = {w.mac_spanwise_station:.4f} m")

    shape = w.build()
    print(f"\n{'volume (kernel)':<22}{w.measured_volume():.6f} m^3")
    print(f"{'volume (predicted)':<22}{w.predicted_volume():.6f} m^3")

    print("\nwrote", to_step(shape, "exports/wing.step"))
    print("wrote", to_iges(shape, "exports/wing.iges"))
    print("wrote", to_glb(shape, "exports/wing.glb"), "— web viewer mesh")

    for theme, suffix in (("light", ""), ("dark", "-dark")):
        for figure in generate_all(w, "figures", theme=theme, suffix=suffix):
            print("wrote", figure)

    general_arrangement(w, "drawings/wing-ga.png")
    print("wrote drawings/wing-ga.png")


if __name__ == "__main__":
    main()
