"""Stage C4 unit 1: does the solver compute compressible flow correctly?

METHOD.md's step 0 asks for a validation case with a known answer before
the real one, and every stage of this project has obeyed it — the
Ainley-Mathieson model was run on R&M 2974's own worked example before the
E3 LPT, the beam on closed-form eigenvalues before a blade, the polygon
integrator on a rectangle and an ellipse before an airfoil. A CFD solver
gets the same treatment, and it needs a case whose answer is **exact**,
not merely published.

The Sod shock tube is that case. A diaphragm at x = 0 separates air at
100 kPa, 348.432 K from air at 10 kPa, 278.746 K, both at rest — which is
rho = 1.000 and 0.125 kg/m3, Sod's problem in SI. Its solution is the
exact Riemann solution: a left-running expansion fan, a contact
discontinuity and a right-running shock, all in closed form. No
correlation, no published number, no scatter — an answer.

The exact solver here is Toro's (*Riemann Solvers and Numerical Methods
for Fluid Dynamics*, ch. 4): Newton iteration on the pressure function
f(p) = f_L(p) + f_R(p) + (u_R - u_L), then sampling the similarity
solution at each x/t. It is written out rather than imported so the known
answer is in this repository and not in a package.

The pass bands are in STEP0.md and were written before the case was run.
STEP0.md, unit C4-1."""
from __future__ import annotations

import math
import pathlib
import re
from dataclasses import dataclass

GAMMA = 1.4
R_SPECIFIC = 287.15          # OpenFOAM's shockTube thermophysicalProperties


@dataclass
class State:
    rho: float
    u: float
    p: float

    @property
    def a(self):
        return math.sqrt(GAMMA * self.p / self.rho)


# ------------------------------------------------- the exact Riemann solution

def _f(p, s: State):
    """Toro eq 4.6-4.7: the pressure function and its derivative for one side"""
    a, pk, rk = s.a, s.p, s.rho
    if p > pk:                                     # shock
        ak, bk = 2.0 / ((GAMMA + 1) * rk), (GAMMA - 1) / (GAMMA + 1) * pk
        val = (p - pk) * math.sqrt(ak / (p + bk))
        der = math.sqrt(ak / (bk + p)) * (1 - 0.5 * (p - pk) / (bk + p))
    else:                                          # rarefaction
        val = 2 * a / (GAMMA - 1) * ((p / pk) ** ((GAMMA - 1) / (2 * GAMMA)) - 1)
        der = 1.0 / (rk * a) * (p / pk) ** (-(GAMMA + 1) / (2 * GAMMA))
    return val, der


def star_state(left: State, right: State, tol=1e-12, itmax=100):
    """p* and u* by Newton iteration on f(p) = f_L + f_R + (u_R - u_L)"""
    p = 0.5 * (left.p + right.p)
    for _ in range(itmax):
        fl, dfl = _f(p, left)
        fr, dfr = _f(p, right)
        f = fl + fr + (right.u - left.u)
        dp = f / (dfl + dfr)
        p_new = max(p - dp, 1e-6)
        if abs(p_new - p) / (0.5 * (p_new + p)) < tol:
            p = p_new
            break
        p = p_new
    fl, _ = _f(p, left)
    fr, _ = _f(p, right)
    u = 0.5 * (left.u + right.u) + 0.5 * (fr - fl)
    return p, u


def sample(s_over_t, left: State, right: State, p_star, u_star):
    """the similarity solution at x/t (Toro's sampling, fig 4.14)"""
    if s_over_t <= u_star:                         # left of the contact
        if p_star > left.p:                        # left shock
            sl = left.u - left.a * math.sqrt((GAMMA + 1) / (2 * GAMMA) * p_star / left.p
                                             + (GAMMA - 1) / (2 * GAMMA))
            if s_over_t <= sl:
                return left
            r = left.rho * ((p_star / left.p + (GAMMA - 1) / (GAMMA + 1))
                            / ((GAMMA - 1) / (GAMMA + 1) * p_star / left.p + 1))
            return State(r, u_star, p_star)
        # left rarefaction
        a_star = left.a * (p_star / left.p) ** ((GAMMA - 1) / (2 * GAMMA))
        head, tail = left.u - left.a, u_star - a_star
        if s_over_t <= head:
            return left
        if s_over_t >= tail:
            return State(left.rho * (p_star / left.p) ** (1 / GAMMA), u_star, p_star)
        u = 2 / (GAMMA + 1) * (left.a + (GAMMA - 1) / 2 * left.u + s_over_t)
        a = 2 / (GAMMA + 1) * (left.a + (GAMMA - 1) / 2 * (left.u - s_over_t))
        p = left.p * (a / left.a) ** (2 * GAMMA / (GAMMA - 1))
        return State(GAMMA * p / a ** 2, u, p)
    # right of the contact
    if p_star > right.p:                           # right shock
        sr = right.u + right.a * math.sqrt((GAMMA + 1) / (2 * GAMMA) * p_star / right.p
                                           + (GAMMA - 1) / (2 * GAMMA))
        if s_over_t >= sr:
            return right
        r = right.rho * ((p_star / right.p + (GAMMA - 1) / (GAMMA + 1))
                         / ((GAMMA - 1) / (GAMMA + 1) * p_star / right.p + 1))
        return State(r, u_star, p_star)
    a_star = right.a * (p_star / right.p) ** ((GAMMA - 1) / (2 * GAMMA))
    head, tail = right.u + right.a, u_star + a_star
    if s_over_t >= head:
        return right
    if s_over_t <= tail:
        return State(right.rho * (p_star / right.p) ** (1 / GAMMA), u_star, p_star)
    u = 2 / (GAMMA + 1) * (-right.a + (GAMMA - 1) / 2 * right.u + s_over_t)
    a = 2 / (GAMMA + 1) * (right.a - (GAMMA - 1) / 2 * (right.u - s_over_t))
    p = right.p * (a / right.a) ** (2 * GAMMA / (GAMMA - 1))
    return State(GAMMA * p / a ** 2, u, p)


def wave_speeds(left, right, p_star, u_star):
    """where the three waves are, per unit time"""
    a_star_l = left.a * (p_star / left.p) ** ((GAMMA - 1) / (2 * GAMMA))
    shock = right.u + right.a * math.sqrt((GAMMA + 1) / (2 * GAMMA) * p_star / right.p
                                          + (GAMMA - 1) / (2 * GAMMA))
    return dict(fan_head=left.u - left.a, fan_tail=u_star - a_star_l,
                contact=u_star, shock=shock)


def exact_profile(xs, t, left: State, right: State, x0=0.0):
    p_star, u_star = star_state(left, right)
    out = []
    for x in xs:
        s = sample((x - x0) / t, left, right, p_star, u_star)
        out.append(s)
    return out, p_star, u_star


# ------------------------------------------------------- reading OpenFOAM out

CASE = pathlib.Path(__file__).resolve().parents[2] / "cfd" / "run" / "shockTube"


def read_field(time, name, case=None):
    """the internalField of a uniform 1-D OpenFOAM case, in cell order"""
    path = (case or CASE) / str(time) / name
    text = path.read_text()
    m = re.search(r"internalField\s+nonuniform\s+List<\w+>\s*\n(\d+)\s*\n\(", text)
    if not m:
        u = re.search(r"internalField\s+uniform\s+([-\d.eE+]+)", text)
        if u:
            return None, float(u.group(1))
        raise ValueError(f"cannot parse {path}")
    n = int(m.group(1))
    body = text[m.end():]
    vals = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith(")"):
            break
        if not line:
            continue
        if line.startswith("("):                   # a vector
            vals.append(float(line.strip("()").split()[0]))
        else:
            vals.append(float(line))
    if len(vals) != n:
        raise ValueError(f"{path}: expected {n} values, read {len(vals)}")
    return vals, None


def cell_centres(n=100, x_lo=-5.0, x_hi=5.0):
    dx = (x_hi - x_lo) / n
    return [x_lo + (i + 0.5) * dx for i in range(n)], dx


def compare(time=0.007, case=None):
    """the run against the exact answer"""
    left = State(100000.0 / (R_SPECIFIC * 348.432), 0.0, 100000.0)
    right = State(10000.0 / (R_SPECIFIC * 278.746), 0.0, 10000.0)
    p, _ = read_field(time, "p", case)
    t_field, _ = read_field(time, "T", case)
    u, _ = read_field(time, "U", case)
    xs, dx = cell_centres(len(p))
    exact, p_star, u_star = exact_profile(xs, time, left, right)
    rho = [pi / (R_SPECIFIC * ti) for pi, ti in zip(p, t_field)]

    def l2(a, b, scale):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)) / scale

    speeds = wave_speeds(left, right, p_star, u_star)
    # the star plateau: cells strictly between the fan tail and the shock
    lo, hi = speeds["fan_tail"] * time + 0.15, speeds["shock"] * time - 0.15
    plateau = [i for i, x in enumerate(xs) if lo < x < hi]
    return dict(
        time=time, n_cells=len(p), dx=dx,
        left=left, right=right, p_star=p_star, u_star=u_star, speeds=speeds,
        p_star_cfd=sum(p[i] for i in plateau) / len(plateau),
        u_star_cfd=sum(u[i] for i in plateau) / len(plateau),
        p_star_err_pct=(sum(p[i] for i in plateau) / len(plateau) / p_star - 1) * 100,
        u_star_err_pct=(sum(u[i] for i in plateau) / len(plateau) / u_star - 1) * 100,
        l2_p=l2(p, [e.p for e in exact], left.p),
        l2_rho=l2(rho, [e.rho for e in exact], left.rho),
        l2_u=l2(u, [e.u for e in exact], u_star),
        shock_x_exact=speeds["shock"] * time,
        shock_x_cfd=_shock_position(xs, p),
        xs=xs, p=p, rho=rho, u=u, exact=exact)


def _shock_position(xs, p):
    """where the pressure falls fastest on the right half"""
    best, bi = 0.0, 0
    for i in range(len(xs) // 2, len(xs) - 1):
        d = abs(p[i + 1] - p[i])
        if d > best:
            best, bi = d, i
    return 0.5 * (xs[bi] + xs[bi + 1])


if __name__ == "__main__":
    c = compare()
    print("Stage C4 unit 1: OpenFOAM rhoCentralFoam against the exact Riemann solution\n")
    print(f"   Sod shock tube, {c['n_cells']} cells over 10 m, t = {c['time']} s, dx = {c['dx']} m")
    print(f"   left  rho {c['left'].rho:.4f}  p {c['left'].p:>8.0f}  a {c['left'].a:.1f} m/s")
    print(f"   right rho {c['right'].rho:.4f}  p {c['right'].p:>8.0f}  a {c['right'].a:.1f} m/s\n")
    print(f"   exact star state:  p* = {c['p_star']:.1f} Pa   u* = {c['u_star']:.2f} m/s")
    print(f"   CFD plateau:       p* = {c['p_star_cfd']:.1f} Pa   u* = {c['u_star_cfd']:.2f} m/s")
    print(f"   error:             {c['p_star_err_pct']:+.2f} %              {c['u_star_err_pct']:+.2f} %\n")
    s = c["speeds"]
    print(f"   wave speeds (m/s): fan head {s['fan_head']:>8.1f}  fan tail {s['fan_tail']:>7.1f}"
          f"  contact {s['contact']:>6.1f}  shock {s['shock']:>6.1f}")
    print(f"   shock at t: exact x = {c['shock_x_exact']:.3f} m, CFD x = {c['shock_x_cfd']:.3f} m"
          f"  ({abs(c['shock_x_cfd'] - c['shock_x_exact']) / c['dx']:.2f} cells)\n")
    print(f"   L2 error over the whole domain, normalised:")
    print(f"      pressure {c['l2_p'] * 100:.2f} %   density {c['l2_rho'] * 100:.2f} %"
          f"   velocity {c['l2_u'] * 100:.2f} %")
