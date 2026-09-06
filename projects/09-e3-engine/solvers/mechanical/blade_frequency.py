"""Stage E3: blade natural frequency — the cantilever beam METHOD.md
names as the validation case before any Campbell diagram.

The work plan's E3 closure is *the first three modes of every HPC stage
within 5 % of the published Campbell lines* — and those ten diagrams
(HPC report Figs 33–42) are figure-status and were **not** transcribed in
Stage A. So that closure is gated on transcription and is not claimed.

What can be done now is METHOD.md's own prescription for this stage:
"E3 | vibration | LPT Fig. 62; **a cantilever beam first**". Two blades
have their zero-speed first-flex frequency published — the fan rotor and
the booster rotor, both in CR-165148 — and both have their chord and
thickness distributions published too. So the beam can be validated
against a real blade before it is trusted on one whose answer is unknown.

    uniform cantilever:  f1 = (1.875^2 / 2 pi) sqrt(EI / (rho A L^4))

and for a tapered blade the same by Rayleigh's quotient, integrating the
real c(r) and t(r). STEP0.md, unit E3."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA
from meanline.losses import _interp

CM, IN = 0.01, 0.0254
BETA1_SQ = 1.875 ** 2          # first cantilever eigenvalue, squared
AREA_SHAPE = 0.70              # airfoil area / (chord x max thickness); stated, not fitted
E_TITANIUM = 114.0e9           # Pa, Ti-6Al-4V
RHO_TITANIUM = 4430.0


def load():
    return yaml.safe_load((DATA / "fan-design.yaml").read_text())


@dataclass
class BladeBeam:
    name: str
    length_m: float
    radii_m: list
    chord_m: list
    t_over_c: list
    published_f1_Hz: float
    src: str

    def section(self, r):
        c = _interp(r, self.radii_m, self.chord_m)
        return c, c * _interp(r, self.radii_m, self.t_over_c)

    def uniform_frequency(self, E=E_TITANIUM, rho=RHO_TITANIUM):
        """the textbook cantilever, at the ROOT section"""
        c, t = self.section(self.radii_m[0])
        inertia = c * t ** 3 / 12
        area = AREA_SHAPE * c * t
        return BETA1_SQ / (2 * math.pi) * math.sqrt(E * inertia / (rho * area * self.length_m ** 4))

    def rayleigh_frequency(self, E=E_TITANIUM, rho=RHO_TITANIUM, n=400):
        """Rayleigh quotient with the real taper, on the uniform-cantilever
        mode shape. phi(x) = cosh(kx) - cos(kx) - s (sinh(kx) - sin(kx))"""
        k = 1.875 / self.length_m
        s = ((math.cosh(1.875) + math.cos(1.875)) / (math.sinh(1.875) + math.sin(1.875)))

        def phi(x):
            kx = k * x
            return (math.cosh(kx) - math.cos(kx)) - s * (math.sinh(kx) - math.sin(kx))

        def d2phi(x):
            kx = k * x
            return k ** 2 * ((math.cosh(kx) + math.cos(kx)) - s * (math.sinh(kx) + math.sin(kx)))

        num = den = 0.0
        r0 = self.radii_m[0]
        for i in range(n):
            x0, x1 = self.length_m * i / n, self.length_m * (i + 1) / n
            for x in (0.5 * (x0 + x1),):
                c, t = self.section(r0 + x)
                inertia = c * t ** 3 / 12
                area = AREA_SHAPE * c * t
                num += E * inertia * d2phi(x) ** 2 * (x1 - x0)
                den += rho * area * phi(x) ** 2 * (x1 - x0)
        return math.sqrt(num / den) / (2 * math.pi)


def fan_blade():
    f = load()
    a = f["fan_rotor_airfoil"]
    fig15, fig16 = a["fig15"], a["fig16_tm_over_c"]
    radii = [x * CM for x in fig16["radius_cm"]]
    chords = [_interp(x * CM, [y * CM for y in fig15["radius_cm"]],
                      [y * CM for y in fig15["chord_cm"]]) for x in fig16["radius_cm"]]
    length = fig15["blade_height_in"] * IN
    return BladeBeam("fan rotor", length, radii, chords, fig16["tm_c"],
                     a["campbell"]["modes_Hz"]["first_flex"]["at_0"],
                     "CR-165148 Fig 15 (chord), Fig 16 (t/c), campbell first_flex at 0 rpm")


def booster_blade():
    f = load()
    b = f["booster_rotor_airfoil"]
    a = f["aero_parameters"]
    r_tip = a["tip_diameter_cm"][1] / 200
    r_hub = r_tip * a["radius_ratio_inlet"][1]
    return BladeBeam("booster rotor", r_tip - r_hub, [r_hub, r_tip],
                     [b["chord_cm"]["hub"] * CM, b["chord_cm"]["tip"] * CM],
                     [b["tm_c"]["hub"], b["tm_c"]["tip"]],
                     b["campbell"]["modes_Hz"]["first_flex"]["at_0"],
                     "CR-165148 sec II.C chord and t/c, campbell first_flex at 0 rpm")


def blades():
    return [fan_blade(), booster_blade()]


if __name__ == "__main__":
    print("Blade first-flex frequency at zero speed: a cantilever beam, validated")
    print("on the two E3 blades whose answer is published (METHOD.md's E3 step 0)\n")
    print(f"{'blade':<16}{'L cm':>7}{'c root':>9}{'t root':>9}{'uniform':>10}"
          f"{'Rayleigh':>10}{'published':>11}{'unif %':>9}{'Rayl %':>9}")
    for b in blades():
        c, t = b.section(b.radii_m[0])
        u, ray = b.uniform_frequency(), b.rayleigh_frequency()
        print(f"{b.name:<16}{b.length_m * 100:>7.1f}{c * 100:>9.2f}{t * 100:>9.3f}"
              f"{u:>10.1f}{ray:>10.1f}{b.published_f1_Hz:>11.0f}"
              f"{(u / b.published_f1_Hz - 1) * 100:>9.1f}{(ray / b.published_f1_Hz - 1) * 100:>9.1f}")
    print("\n   uniform = the textbook cantilever at the root section")
    print("   Rayleigh = the same mode shape with the real chord and thickness taper")
