"""Stage E3's tool: an Euler-Bernoulli beam, because METHOD.md says
"a cantilever beam first".

Two pieces, both textbook, both validated against closed-form answers
before either is pointed at a blade.

1. **Section properties by Green's theorem.** For a closed polygon the
   area and the second moments are exact contour sums, so a transcribed
   airfoil needs no shape factor at all:

       A     = 1/2 sum (x_i y_j - x_j y_i)
       I_xx  = 1/12 sum (y_i^2 + y_i y_j + y_j^2) (x_i y_j - x_j y_i)

   and likewise I_yy, I_xy; the principal values follow from Mohr's
   circle. A blade bends first about its **weak** principal axis, so
   I_min is the one that sets first flex.

2. **A two-node Hermite beam element**, consistent mass, plus the
   geometric stiffness that centrifugal tension adds:

       K  = EI/L^3  [12, 6L, -12, 6L; ...]
       M  = rho A L/420 [156, 22L, 54, -13L; ...]
       Kg = T/(30L) [36, 3L, -36, 3L; ...]

   with T(x) = integral_x^L rho A(xi) omega^2 (R_hub + xi) dxi, the pull
   of the blade outboard of the station. Solve (K + Kg) phi = w^2 M phi.

Boundary conditions cover the three the E3 reports themselves name: a
free cantilever (booster rotor), a **pinned tip** (LPT stage 1 -- Fig 62
is titled "pinned-tip resonant frequency analysis"), and a part-span
restraint (the fan's 55 % shroud).

Exact eigenvalues used as the known answer, f = (bL)^2/(2 pi) sqrt(EI/(rho A L^4)):

    clamped-free     bL = 1.87510, 4.69409, 7.85476
    clamped-pinned   bL = 3.92660, 7.06858, 10.21018
    clamped-clamped  bL = 4.73004, 7.85320, 10.99561

STEP0.md, unit E3."""
from __future__ import annotations

import math

import numpy as np

CLAMPED_FREE = (1.8751041, 4.6940911, 7.8547574)
CLAMPED_PINNED = (3.9266023, 7.0685827, 10.2101761)
CLAMPED_CLAMPED = (4.7300408, 7.8532046, 10.9956078)


# ------------------------------------------------------- section properties

def polygon_properties(points):
    """area, centroid and second moments of a closed polygon, exactly.
    Returns the principal second moments as well; I_min is the weak axis a
    blade bends about first."""
    x = np.asarray([p[0] for p in points], float)
    y = np.asarray([p[1] for p in points], float)
    if (x[0], y[0]) != (x[-1], y[-1]):
        x, y = np.append(x, x[0]), np.append(y, y[0])
    cross = x[:-1] * y[1:] - x[1:] * y[:-1]
    a = cross.sum() / 2
    if a < 0:                                     # force counter-clockwise
        x, y, cross, a = x[::-1], y[::-1], -cross[::-1], -a
    cx = ((x[:-1] + x[1:]) * cross).sum() / (6 * a)
    cy = ((y[:-1] + y[1:]) * cross).sum() / (6 * a)
    xr, yr = x - cx, y - cy
    cr = xr[:-1] * yr[1:] - xr[1:] * yr[:-1]
    ixx = ((yr[:-1] ** 2 + yr[:-1] * yr[1:] + yr[1:] ** 2) * cr).sum() / 12
    iyy = ((xr[:-1] ** 2 + xr[:-1] * xr[1:] + xr[1:] ** 2) * cr).sum() / 12
    ixy = ((xr[:-1] * yr[1:] + 2 * xr[:-1] * yr[:-1] + 2 * xr[1:] * yr[1:]
            + xr[1:] * yr[:-1]) * cr).sum() / 24
    avg, dif = (ixx + iyy) / 2, math.hypot((ixx - iyy) / 2, ixy)
    return dict(area=a, cx=cx, cy=cy, ixx=ixx, iyy=iyy, ixy=ixy,
                i_min=avg - dif, i_max=avg + dif,
                principal_angle_deg=math.degrees(0.5 * math.atan2(2 * ixy, ixx - iyy)))


def closed_airfoil(pts):
    """the two transcribed surfaces joined into one closed loop"""
    s, q = pts["suction"], pts["pressure"]
    return list(s) + list(reversed(q))


# ------------------------------------------------------------ the beam model

class Beam:
    """A tapered Euler-Bernoulli beam clamped at x = 0. `ei` and `rho_a`
    are callables of x; `hub_radius` is the radius of the clamp, which is
    what makes the centrifugal stiffening of a stubby blade on a big drum
    so much larger than a textbook rotating cantilever's."""

    def __init__(self, length, ei, rho_a, hub_radius=0.0, elements=60):
        self.L, self.ei, self.rho_a = length, ei, rho_a
        self.R, self.ne = hub_radius, elements
        self.xs = np.linspace(0.0, length, elements + 1)

    # --- element matrices
    @staticmethod
    def _k(ei, le):
        return ei / le ** 3 * np.array([
            [12, 6 * le, -12, 6 * le],
            [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
            [-12, -6 * le, 12, -6 * le],
            [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]], float)

    @staticmethod
    def _m(rho_a, le):
        return rho_a * le / 420 * np.array([
            [156, 22 * le, 54, -13 * le],
            [22 * le, 4 * le ** 2, 13 * le, -3 * le ** 2],
            [54, 13 * le, 156, -22 * le],
            [-13 * le, -3 * le ** 2, -22 * le, 4 * le ** 2]], float)

    @staticmethod
    def _kg(tension, le):
        return tension / (30 * le) * np.array([
            [36, 3 * le, -36, 3 * le],
            [3 * le, 4 * le ** 2, -3 * le, -le ** 2],
            [-36, -3 * le, 36, -3 * le],
            [3 * le, -le ** 2, -3 * le, 4 * le ** 2]], float)

    def tension(self, x, omega):
        """centrifugal pull of everything outboard of x"""
        if omega == 0:
            return 0.0
        n = 200
        xi = np.linspace(x, self.L, n)
        f = np.array([self.rho_a(v) * omega ** 2 * (self.R + v) for v in xi])
        return float(np.trapezoid(f, xi))

    def assemble(self, omega=0.0):
        n = self.ne + 1
        K = np.zeros((2 * n, 2 * n))
        M = np.zeros((2 * n, 2 * n))
        for e in range(self.ne):
            x0, x1 = self.xs[e], self.xs[e + 1]
            le, xm = x1 - x0, 0.5 * (x0 + x1)
            ke = self._k(self.ei(xm), le) + self._kg(self.tension(xm, omega), le)
            me = self._m(self.rho_a(xm), le)
            d = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
            K[np.ix_(d, d)] += ke
            M[np.ix_(d, d)] += me
        return K, M

    def frequencies(self, n_modes=3, omega=0.0, pinned_at=None, tip_clamped=False):
        """natural frequencies in Hz. `pinned_at` is a fraction of the
        length at which lateral motion is held (the LPT tip shroud, the
        fan part-span shroud); None is a free cantilever. `tip_clamped`
        also holds the rotation at the far end -- a vane banded at both
        ends rather than cantilevered from the casing."""
        K, M = self.assemble(omega)
        fixed = {0, 1}                                    # clamped root
        if pinned_at is not None:
            node = int(round(pinned_at * self.ne))
            fixed.add(2 * node)                           # deflection only
        if tip_clamped:
            fixed.update({2 * self.ne, 2 * self.ne + 1})
        keep = [i for i in range(K.shape[0]) if i not in fixed]
        K, M = K[np.ix_(keep, keep)], M[np.ix_(keep, keep)]
        from scipy.linalg import eigh
        w2 = eigh(K, M, eigvals_only=True)
        w2 = w2[w2 > 0]
        return [math.sqrt(v) / (2 * math.pi) for v in w2[:n_modes]]

    def southwell(self, omega, pinned_at=None):
        """S in f_N^2 = f_0^2 + S (N/60)^2, first mode -- a property of the
        mode shape and the hub radius, not of the material"""
        f0 = self.frequencies(1, 0.0, pinned_at)[0]
        fn = self.frequencies(1, omega, pinned_at)[0]
        rev_per_s = omega / (2 * math.pi)
        return (fn ** 2 - f0 ** 2) / rev_per_s ** 2, f0, fn


def uniform(length, e, i, rho, area, hub_radius=0.0, elements=60):
    return Beam(length, lambda x: e * i, lambda x: rho * area, hub_radius, elements)


def exact(bl, length, e, i, rho, area):
    return bl ** 2 / (2 * math.pi) * math.sqrt(e * i / (rho * area * length ** 4))
