"""Real-gas properties for the E3 cycle: cp(T) for dry air and for the
products of kerosene combustion at a fuel-air ratio, with enthalpy and
entropy functions integrated analytically from the polynomials.

Walsh & Fletcher, Gas Turbine Performance, chart 3.1 polynomials in
Tz = T/1000 (kJ/kg.K), 200-2000 K. Validated in tests/test_e3cycle.py
against the chart values at 288 K and 1500 K before the cycle was run.
"""
from __future__ import annotations

import math

A = [0.992313, 0.236688, -1.852148, 6.083152, -8.893933, 7.097112, -3.234725, 0.794571, -0.081873]
B = [-0.718874, 8.747481, -15.863157, 17.254096, -10.233795, 3.081778, -0.361112, -0.003919, 0.0555930]
R_AIR = 287.05  # J/(kg.K); used for products too (0.3 percent low at FAR 0.02)
T_REF = 298.15


def _poly(coeffs, tz):
    return sum(c * tz ** i for i, c in enumerate(coeffs))


def _poly_int(coeffs, tz):
    """integral of poly(tz) dtz from 0"""
    return sum(c * tz ** (i + 1) / (i + 1) for i, c in enumerate(coeffs))


def _poly_int_over_t(coeffs, tz):
    """integral of poly(tz)/tz dtz from 1 (so the constant term gives ln tz)"""
    return coeffs[0] * math.log(tz) + sum(c * (tz ** i - 1.0) / i for i, c in enumerate(coeffs) if i > 0)


def cp(t, far=0.0):
    """J/(kg.K) of air (far = 0) or products at fuel-air ratio far (mass basis)."""
    tz = t / 1000.0
    x = far / (1.0 + far)
    return 1000.0 * (_poly(A, tz) + x * _poly(B, tz))


def h(t, far=0.0):
    """J/kg above T_REF."""
    x = far / (1.0 + far)
    def H(tt):
        tz = tt / 1000.0
        return 1.0e6 * (_poly_int(A, tz) + x * _poly_int(B, tz))
    return H(t) - H(T_REF)


def phi(t, far=0.0):
    """entropy function integral of cp/T dT from T_REF, J/(kg.K)."""
    x = far / (1.0 + far)
    def P(tt):
        tz = tt / 1000.0
        return 1000.0 * (_poly_int_over_t(A, tz) + x * _poly_int_over_t(B, tz))
    return P(t) - P(T_REF)


def t_from_h(target, far=0.0, guess=800.0):
    """invert h(t) by Newton on cp; 1e-6 relative."""
    t = guess
    for _ in range(60):
        dt = (h(t, far) - target) / cp(t, far)
        t -= dt
        if abs(dt) < 1e-6 * t:
            return t
    raise RuntimeError("t_from_h did not converge")


def t_from_phi(target, far=0.0, guess=800.0):
    """invert phi(t): d(phi)/dT = cp/T."""
    t = guess
    for _ in range(60):
        dt = (phi(t, far) - target) / (cp(t, far) / t)
        t -= dt
        if abs(dt) < 1e-6 * t:
            return t
    raise RuntimeError("t_from_phi did not converge")


def compress(t1, p1, pr, eta, far=0.0):
    """adiabatic compression with efficiency eta; returns (t2, p2)."""
    t2s = t_from_phi(phi(t1, far) + R_AIR * math.log(pr), far, guess=t1 * pr ** 0.28)
    h2 = h(t1, far) + (h(t2s, far) - h(t1, far)) / eta
    return t_from_h(h2, far, guess=t2s), p1 * pr


def expand_for_work(t1, p1, dh, eta, far=0.0):
    """turbine delivering specific work dh (J/kg) at efficiency eta; returns (t2, p2)."""
    h2 = h(t1, far) - dh
    t2 = t_from_h(h2, far, guess=t1 - dh / cp(t1, far))
    h2s = h(t1, far) - dh / eta
    t2s = t_from_h(h2s, far, guess=t2)
    pr = math.exp((phi(t1, far) - phi(t2s, far)) / R_AIR)
    return t2, p1 / pr


def expand_to_pressure(t1, p1, p2, far=0.0):
    """isentropic expansion to p2; returns t2 static/total as the caller intends."""
    t2s = t_from_phi(phi(t1, far) - R_AIR * math.log(p1 / p2), far, guess=t1 * (p2 / p1) ** 0.28)
    return t2s
