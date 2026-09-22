"""Stage E unit E7: the flutter screen.

The plan asks for *reduced frequency per row; flexural and torsional
stability plots vs HPC Figs. 43-44*. Those two figures are not
transcribed. What is transcribed is a better check: **LPT report Table XI**
prints a flutter safety factor for each of the five LPT rotor stages, in
both modes, and states the index behind it --

    index = relative flow velocity / (half blade chord x natural frequency)

-- the safety factor being *maximum allowable index / calculated index*,
required to be at least 1.

**The allowable is not printed**, so the index cannot be checked against a
number directly. It can be checked across stages: if one allowable judges
all five, then `SF_published x I_computed` is that allowable, five times
over, and the five must agree. The value they agree on is an allowable
this project **recovers** rather than reads.

That test survives unit E3's frequency bias. A frequency wrong by a
constant factor k makes every index wrong by 1/k and every product
`allowable/k` -- still constant. **The check is blind to a uniform bias
and sensitive to a stage-to-stage one**, which is the part of the model it
can honestly examine. It cannot recover the allowable's absolute value,
and `recovered_allowable` says so in its own name.

Torsion is **not modelled**. The beam gives flexural modes only; a
torsional index needs GJ and a polar inertia this project has not built.
Table XI's torsional column is carried here as published data and compared
with nothing.

STEP0.md, unit E7."""
from __future__ import annotations

import math
import statistics

import yaml

from e3cycle.cycle import DATA

#: the band stated in STEP0 before the run
BAND_PCT = 15.0


def _lpt():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


def published_safety_factors():
    """Table XI as printed, both modes, all five stages."""
    f = _lpt()["flutter"]
    return [dict(stage=s, torsion=t, flex=x)
            for s, t, x in zip(f["stage"], f["torsion"], f["flex"])]


def half_chords_m():
    """Table XI's own definition. The aspect-ratio note says the report
    works at the pitch, so root and tip are averaged."""
    rb = _lpt()["rotor_blades"]
    return [(r + t) / 2 / 100 / 2
            for r, t in zip(rb["root_chord_cm"], rb["tip_chord_cm"])]


def _stages():
    from meanline.lpt import run
    return [x for x in run() if isinstance(x, list)][0]


def relative_velocities_m_s(where="exit"):
    """Rotor relative velocity, straight off the C1 velocity triangle. No
    thermodynamics in the path, so nothing here depends on a
    static-temperature model.

    Table XI says "relative flow velocity" and does not say at which
    station. STEP0 chose the **exit**, w3 = cx3/cos(beta3), as the natural
    reading for a turbine rotor and as the larger of the two. The inlet
    reading is available here because the ambiguity is in the source, and
    it is reported alongside rather than substituted -- see
    `alternative_inlet_definition` and finding 173."""
    return [(s.cx2 if where == "inlet" else s.cx3)
            / math.cos(math.radians(s.beta2 if where == "inlet" else s.beta3))
            for s in _stages()]


def flexural_frequencies_hz(rpm=0.0):
    """First flex of each LPT rotor, from the transcribed sections. The
    blades carry integral tip shrouds, so the beam is pinned at the tip --
    which is also how the report's own Fig 62 is labelled."""
    from mechanical.blade_frequency import lpt_rotor
    return [lpt_rotor(n).modes(False, rpm, 1)[0] for n in range(1, 6)]


def screen(rpm=0.0, where="exit"):
    """The five stages, each with its computed index and the allowable that
    the published safety factor then implies."""
    sf = published_safety_factors()
    b = half_chords_m()
    w = relative_velocities_m_s(where)
    f = flexural_frequencies_hz(rpm)
    out = []
    for i, row in enumerate(sf):
        index = w[i] / (b[i] * f[i])
        out.append(dict(
            stage=row["stage"], w_rel_m_s=w[i], half_chord_m=b[i],
            f_flex_hz=f[i], index=index,
            sf_flex_published=row["flex"], sf_torsion_published=row["torsion"],
            implied_allowable=row["flex"] * index))
    return out


def alternative_inlet_definition(rpm=0.0):
    """Finding 173. Table XI's "relative flow velocity" does not name a
    station. On the **inlet** reading the four front stages agree to 4.2 %
    -- comfortably inside the band STEP0 stated -- and stage 5 stands out
    at +33 %.

    This is reported, not adopted. STEP0 named the exit velocity before the
    run and the closure is evaluated on that; swapping the definition
    afterwards because the other one fits better is the exact move this
    project exists not to make. What the two readings together say is that
    the index is reproducible on four of five stages under one plausible
    reading of an ambiguous sentence, and that stage 5 is the odd one under
    both."""
    rows = screen(rpm, where="inlet")
    a = [r["implied_allowable"] for r in rows]
    front = statistics.mean(a[:4])
    return dict(
        implied=a, front_four_mean=front,
        front_four_worst_pct=max(abs(x / front - 1) * 100 for x in a[:4]),
        stage5_departure_pct=(a[4] / front - 1) * 100,
        adopted=False,
        why_not=("STEP0 named the exit velocity before the run; the closure "
                 "is evaluated on that definition"))


def recovered_allowable(rpm=0.0):
    """What the five stages agree the allowable index is -- carrying, and
    saying, the beam model's bias in its absolute value."""
    rows = screen(rpm)
    a = [r["implied_allowable"] for r in rows]
    mean = statistics.mean(a)
    spread = [(x / mean - 1) * 100 for x in a]
    return dict(
        rows=rows, mean=mean, median=statistics.median(a),
        worst_pct=max(abs(x) for x in spread), band_pct=BAND_PCT,
        inside=max(abs(x) for x in spread) <= BAND_PCT,
        spread_ratio=max(a) / min(a),
        caveat=("absolute value carries unit E3's frequency bias; the "
                "stage-to-stage agreement does not"))


def torsion_is_not_modelled():
    """Stated rather than approximated. Table XI's torsional column is
    published data this project compares with nothing."""
    return dict(
        published=[r["torsion"] for r in published_safety_factors()],
        modelled=False,
        why=("the beam model gives flexural modes only; a torsional index "
             "needs GJ and a polar second moment this project has not built"),
        note=("Table XI's own note: stage 4, the 156-blade acoustic stage "
              "with the smallest chord and highest aspect ratio, sits "
              "exactly on the torsional limit at 1.0"))


def summary():
    r = recovered_allowable()
    L = ["Stage E unit E7 -- the flutter screen (LPT, flexural)", ""]
    L.append(f"   {'stg':>3}{'w_rel':>9}{'b cm':>8}{'f_1F Hz':>10}"
             f"{'index':>9}{'SF pub':>9}{'implied allowable':>19}")
    for x in r["rows"]:
        L.append(f"   {x['stage']:>3}{x['w_rel_m_s']:>9.1f}"
                 f"{x['half_chord_m']*100:>8.2f}{x['f_flex_hz']:>10.1f}"
                 f"{x['index']:>9.2f}{x['sf_flex_published']:>9.1f}"
                 f"{x['implied_allowable']:>19.2f}")
    L += ["", f"   recovered allowable index  {r['mean']:.2f} "
          f"(median {r['median']:.2f})",
          f"   worst departure            {r['worst_pct']:.1f} % "
          f"against a {r['band_pct']:.0f} % band -- "
          f"{'INSIDE' if r['inside'] else 'OUTSIDE'}",
          f"   spread across five stages  {r['spread_ratio']:.2f}x"]
    alt = alternative_inlet_definition()
    L += ["", "   Table XI does not say at which station the relative "
          "velocity is taken.",
          "   STEP0 chose the exit before the run, and the closure above is "
          "that choice.",
          f"   On the INLET reading: stages 1-4 agree to "
          f"{alt['front_four_worst_pct']:.1f} % about "
          f"{alt['front_four_mean']:.2f}, and stage 5 departs "
          f"{alt['stage5_departure_pct']:+.1f} %.",
          "   Reported, not adopted (finding 173)."]
    t = torsion_is_not_modelled()
    L += ["", f"   torsion: NOT MODELLED. {t['why']}",
          f"      published torsional safety factors {t['published']}"]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())


# =========================================================================
# Unit E7b -- pricing the variable the gate names, before opening a figure
# =========================================================================
#
# E7's gate named the **tip-shroud mass** as the missing term and LPT Figs
# 64-66 pp.99-101 as the work needed to supply it. Finding 291's rule says
# write the elasticity of the answer to the thing the gate names first.
# Everything below is that pricing. The closure above is untouched.

RHO_RENE77 = 8220.0                        # as blade_frequency.py, handbook
E_RENE77 = 207.0e9

#: the three shroud sizes priced, smallest to largest
SHROUD_MODES = ("printed_overhang", "full_platform", "generous")


def _rotor(stage):
    from mechanical.blade_frequency import lpt_rotor
    return lpt_rotor(stage)


def _pitch_m(stage):
    """circumferential pitch at the blade tip -- the width of one shroud"""
    m = _rotor(stage)
    n = _lpt()["rotor_blades"]["blade_count"][stage - 1]
    return 2 * math.pi * (m.hub_radius_m + m.length_m) / n


def airfoil_mass_kg(stage):
    """the beam's own rho*A distribution, integrated -- so the shroud is
    priced against the same blade the frequency comes from"""
    import numpy as np
    from meanline.losses import _interp
    m = _rotor(stage)
    xs = np.linspace(0.0, m.length_m, 400)
    ra = np.array([_interp(x, m.x, m.area) for x in xs])
    return float(np.trapezoid(ra, xs)) * m.rho


def shroud_axial_extent_m(stage):
    """How long the shroud is, axially. Two readings, and which one is used
    is the whole span of the pricing.

    `tip_shrouds.overhang_l_cm` is PRINTED for stages 1-3 (0.767, 1.010,
    0.988 cm) and null for 4-5. It is the interlock overhang, not the whole
    shroud: a shroud that seals has to cover the blade's axial chord. So the
    small reading is the printed overhang and the large one is the tip
    chord, and stages 4-5 scale the printed mean by their own tip chord."""
    d = _lpt()
    ov = d["tip_shrouds"]["overhang_l_cm"][stage - 1]
    tc = d["rotor_blades"]["tip_chord_cm"]
    printed = ov is not None
    if not printed:
        known = [x for x in d["tip_shrouds"]["overhang_l_cm"] if x]
        ov = (sum(known) / len(known)) * tc[stage - 1] / (sum(tc[:3]) / 3)
    return dict(overhang_m=ov / 100, chord_m=tc[stage - 1] / 100,
                overhang_is_printed=printed)


def shroud_mass_kg(stage, mode="full_platform"):
    """Shroud mass per blade, from printed geometry. Nothing is digitised.

    Thickness is the one printed number: `tip_shrouds.stage1_analysis`
    gives 0.27 and 0.292 cm from Fig 66 for the stage-1 shroud, and 0.27 cm
    is carried across the five stages because no other stage prints one.

    * `printed_overhang` -- overhang x thickness x pitch, the smallest
      defensible shroud
    * `full_platform` -- tip chord x thickness x pitch, plus two seal teeth
      2.0 mm tall and 1.0 mm thick
    * `generous` -- 1.5x the full platform on taller, thicker teeth
    """
    g = shroud_axial_extent_m(stage)
    w, t = _pitch_m(stage), 0.27e-2
    if mode == "printed_overhang":
        v = g["overhang_m"] * t * w
    elif mode == "full_platform":
        v = g["chord_m"] * t * w + 2 * 0.20e-2 * 0.10e-2 * w
    elif mode == "generous":
        v = 1.5 * (g["chord_m"] * t * w + 2 * 0.30e-2 * 0.15e-2 * w)
    else:
        raise ValueError(mode)
    return v * RHO_RENE77


def _worst(a):
    mu = statistics.mean(a)
    return max(abs(x / mu - 1) * 100 for x in a)


def _allowables(freqs):
    """the five implied allowables for a given set of frequencies, with the
    published safety factors, half chords and exit velocities held"""
    sf = [r["flex"] for r in published_safety_factors()]
    b, w = half_chords_m(), relative_velocities_m_s("exit")
    return [sf[i] * w[i] / (b[i] * freqs[i]) for i in range(5)]


def _freqs(**tip):
    """first flex of all five LPT rotors.

    `rpm` is popped OUTSIDE the comprehension on purpose: popping it inside
    consumed it on stage 1 and silently ran stages 2-5 at zero speed, which
    made the centrifugal row of the P3 table read +0.07 pp where the answer
    is -3.68. A dict mutated inside a comprehension is a bug that returns a
    plausible number."""
    from mechanical.blade_frequency import lpt_rotor
    rpm = tip.pop("rpm", 0.0)
    return [lpt_rotor(n).modes(False, rpm, 1, **tip)[0] for n in range(1, 6)]


def price_shroud_mass():
    """**P1 and P2, the two bands E7b stated before the run.**

    P1, the gate test: the full plausible shroud mass on the beam at the
    PINNED tip the model actually uses. A lumped mass at a pinned node has
    zero displacement, so zero kinetic energy, so zero effect on any
    eigenvalue -- the only channel left is the shroud's rotary inertia
    about the pin, taken as a plate of its own axial extent.

    P2, the bound: the same mass on a FREE tip, the softest interlock
    physically possible and therefore the most the mass could EVER be
    worth at any interlock stiffness.
    """
    base = _worst(_allowables(_freqs()))
    out = []
    for mode in SHROUD_MODES:
        ms = [shroud_mass_kg(n, mode) for n in range(1, 6)]
        js = [ms[n - 1] * shroud_axial_extent_m(n)["chord_m"] ** 2 / 12
              for n in range(1, 6)]
        row = dict(mode=mode, mass_g=[x * 1000 for x in ms],
                   frac_of_airfoil_pct=[ms[n - 1] / airfoil_mass_kg(n) * 100
                                        for n in range(1, 6)])
        for name, spring in (("pinned", None), ("free", 0.0)):
            f0 = _freqs(tip_spring=spring)
            f1 = [_rotor(n).modes(False, 0.0, 1, tip_mass=ms[n - 1],
                                  tip_rotary_inertia=js[n - 1],
                                  tip_spring=spring)[0] for n in range(1, 6)]
            row[name] = dict(
                df1_pct=[(f1[i] / f0[i] - 1) * 100 for i in range(5)],
                worst_pct=_worst(_allowables(f1)),
                moved_pp=_worst(_allowables(f1)) - base)
        out.append(row)
    free_no_mass = _worst(_allowables(_freqs(tip_spring=0.0)))
    return dict(baseline_worst_pct=base, rows=out,
                p1_moved_pp=max(abs(r["pinned"]["moved_pp"]) for r in out),
                p2_worst_pct=min(r["free"]["worst_pct"] for r in out),
                free_tip_zero_mass_worst_pct=free_no_mass,
                mass_moves_it_the_wrong_way_on_a_free_tip=all(
                    r["free"]["worst_pct"] > free_no_mass for r in out),
                p1_band_pp=1.5, p2_band_pct=BAND_PCT)


def price_candidates():
    """**P3.** Every candidate variable priced on the same footing: how many
    percentage points of the 24.4 does a plausible change in it move?

    The modulus row uses a linear E(T) for a nickel superalloy between the
    handbook 207 GPa at room temperature and about 150 GPa at 900 C, on the
    stage-1 bulk metal temperature the report prints (855-905 C) falling
    through the turbine. It is an estimate and is labelled one.
    """
    d = _lpt()
    rb = d["rotor_blades"]
    base = _worst(_allowables(_freqs()))
    f_pin = _freqs()
    sf = [r["flex"] for r in published_safety_factors()]
    b0, w0 = half_chords_m(), relative_velocities_m_s("exit")

    def w_(a):
        return _worst(a) - base

    rows = []

    # the thing the gate names
    p = price_shroud_mass()
    heavy = [r for r in p["rows"] if r["mode"] == "generous"][0]
    rows.append(("shroud mass, pinned tip (as modelled)", heavy["pinned"]["moved_pp"],
                 "the gate's own variable"))
    rows.append(("shroud mass, free tip (upper bound)", heavy["free"]["moved_pp"],
                 "the most it could be worth at any interlock stiffness"))

    # the station Table XI does not name
    wi = relative_velocities_m_s("inlet")
    rows.append(("velocity station: inlet, all five stages",
                 w_([sf[i] * wi[i] / (b0[i] * f_pin[i]) for i in range(5)]),
                 "finding 173's 4.2 % is four stages of five"))

    # the chord Table XI does not define
    for nm, bb in (("pitch", [rb["blade_length_cm"][i] / rb["aspect_ratio"][i] / 200
                              for i in range(5)]),
                   ("root", [rb["root_chord_cm"][i] / 200 for i in range(5)]),
                   ("tip", [rb["tip_chord_cm"][i] / 200 for i in range(5)])):
        rows.append((f"half chord = {nm} rather than root/tip mean",
                     w_([sf[i] * w0[i] / (bb[i] * f_pin[i]) for i in range(5)]),
                     "Table XI says 'half blade chord' and no station"))

    # the mode
    f2 = [_rotor(n).modes(False, 0.0, 2)[1] for n in range(1, 6)]
    rows.append(("second flexural mode rather than first",
                 w_(_allowables(f2)), "Table XI says 'blade natural frequency'"))

    # speed and temperature, the two right-signed physical terms
    RPM = 3707.0
    f_n = _freqs(rpm=RPM)
    rows.append((f"centrifugal stiffening at {RPM:.0f} rpm",
                 w_(_allowables(f_n)),
                 "right-signed: S grows with hub/length, so the rear stiffens most"))
    tt = [880, 800, 730, 660, 600]
    efac = [(207 - (207 - 150) * (t - 20) / 880) / 207 for t in tt]
    f_t = [f_pin[i] * efac[i] ** 0.5 for i in range(5)]
    rows.append(("modulus at bulk metal temperature (estimated E(T))",
                 w_(_allowables(f_t)),
                 "right-signed: the front stages run hottest"))
    f_b = [f_n[i] * efac[i] ** 0.5 for i in range(5)]
    rows.append(("both of the above together", w_(_allowables(f_b)),
                 "the two physically right-signed terms, combined"))

    # the interlock, as a stiffness rather than a mass
    s = interlock_stiffness_sweep()
    rows.append(("elastic interlock stiffness, one value for all five",
                 s["best_worst_pct"] - base,
                 "FITTED -- one parameter swept and chosen for this closure"))
    rows.append(("interlock stiffness PREDICTED from the printed overhang",
                 s["predicted_worst_pct"] - base,
                 "nothing fitted; 3EI/L^3 on the printed overhang"))
    return dict(baseline_worst_pct=base,
                rows=[dict(variable=a, moved_pp=b, note=c) for a, b, c in rows],
                threshold_pp=10.0)


def interlock_stiffness_sweep():
    """The interlock as a STIFFNESS rather than a mass -- finding 228's
    result on the fan's part-span shroud, transferred to a full tip shroud
    where finding 228 said it would not transfer.

    `best_*` is a **fit**: one parameter swept over three decades and the
    value chosen that minimises the very departure it is being asked to
    close, on five comparisons. It is reported as a diagnosis of which
    variable matters and never as a closure.

    `predicted_*` is the honest version: the overhang treated as a
    cantilever plate, k = 3EI/L^3, from the printed overhang length, the
    printed 0.27 cm thickness and the pitch. Nothing fitted.
    """
    import numpy as np
    base = _worst(_allowables(_freqs()))
    ks = np.logspace(5.5, 8.0, 26)
    sweep = [(float(k), _worst(_allowables(_freqs(tip_spring=float(k)))))
             for k in ks]
    best = min(sweep, key=lambda x: x[1])
    inside = [k for k, v in sweep if v <= BAND_PCT]

    kp = []
    for n in range(1, 6):
        g = shroud_axial_extent_m(n)
        w, t, L = _pitch_m(n), 0.27e-2, g["overhang_m"]
        kp.append(3 * E_RENE77 * (w * t ** 3 / 12) / L ** 3)
    fp = [_rotor(n).modes(False, 0.0, 1, tip_spring=kp[n - 1])[0]
          for n in range(1, 6)]
    return dict(
        baseline_worst_pct=base, sweep=sweep,
        best_k_N_m=best[0], best_worst_pct=best[1], best_is_a_fit=True,
        inside_band_k_range=(min(inside), max(inside)) if inside else None,
        inside_band_width=(max(inside) / min(inside)) if inside else None,
        predicted_k_N_m=kp, predicted_worst_pct=_worst(_allowables(fp)),
        predicted_over_fitted=statistics.mean(kp) / best[0])


def interlock_stiffness_published_routes():
    """Two routes to the stage-1 shroud's own stiffness, both from printed
    numbers, neither fitted to anything -- so they can judge the fit.

    A. the overhang as a cantilever plate, k = 3EI/L^3, on the printed
       0.767 cm overhang and 0.27 cm thickness
    B. the shroud's OWN printed section frequency. Fig 66 prints four,
       10,490 to 15,800 Hz, against a 102/rev vane-passing excitation; the
       lowest with the shroud's mass gives k = (2 pi f)^2 m.
    """
    g = shroud_axial_extent_m(1)
    w, t, L = _pitch_m(1), 0.27e-2, g["overhang_m"]
    k_a = 3 * E_RENE77 * (w * t ** 3 / 12) / L ** 3
    f = min(_lpt()["tip_shrouds"]["stage1_analysis"]["frequency_Hz"])
    m = shroud_mass_kg(1, "full_platform")
    k_b = (2 * math.pi * f) ** 2 * m
    fit = interlock_stiffness_sweep()["best_k_N_m"]
    return dict(route_a_overhang_cantilever_N_m=k_a,
                route_b_fig66_section_frequency_N_m=k_b,
                fig66_lowest_Hz=f, shroud_mass_kg=m,
                ratio_b_over_a=k_b / k_a,
                fitted_k_N_m=fit,
                a_over_fitted=k_a / fit, b_over_fitted=k_b / fit,
                verdict=("two independent published routes agree to a factor "
                         "of 1.4 and are both an order of magnitude STIFFER "
                         "than the value the closure wants, so the record "
                         "argues against the soft interlock the fit prefers"))


def collinearity():
    """Why no correlation on this data can name a mechanism: with five
    stages, every candidate is monotone in stage number."""
    import numpy as np
    d = _lpt()["rotor_blades"]
    a = [r["implied_allowable"] for r in screen()]
    v = dict(stage=[1, 2, 3, 4, 5], blade_length_cm=d["blade_length_cm"],
             f_first_flex=_freqs())
    from meanline.lpt import run
    st = [x for x in run() if isinstance(x, list)][0]
    v["loading_psi"] = [s.psi for s in st]
    v["inlet_rel_mach"] = [s.m2rel for s in st]
    return dict(
        against_implied_allowable={k: float(np.corrcoef(x, a)[0, 1])
                                   for k, x in v.items()},
        pairwise_stage_vs_length=float(np.corrcoef(v["stage"],
                                                  v["blade_length_cm"])[0, 1]),
        note=("every candidate correlates with the implied allowable at "
              "|r| >= 0.96 because every one of them is monotone in stage "
              "number; the interlock stiffness is nominated on a measured "
              "elasticity and a named physical channel, not on a fit"))


def e7b_summary():
    p = price_shroud_mass()
    c = price_candidates()
    s = interlock_stiffness_sweep()
    r = interlock_stiffness_published_routes()
    L = ["", "Unit E7b -- pricing the variable the gate names", "",
         f"   baseline worst departure {p['baseline_worst_pct']:.2f} % "
         f"against a {BAND_PCT:.0f} % band", ""]
    L.append("   P1/P2  shroud mass, three sizes, two tip conditions")
    L.append(f"   {'size':<18}{'mass g':>28}{'% airfoil':>12}"
             f"{'pinned':>10}{'free':>10}")
    for row in p["rows"]:
        L.append(f"   {row['mode']:<18}"
                 f"{str([round(x, 1) for x in row['mass_g']]):>28}"
                 f"{min(row['frac_of_airfoil_pct']):>6.1f}-"
                 f"{max(row['frac_of_airfoil_pct']):<5.1f}"
                 f"{row['pinned']['moved_pp']:>+10.2f}"
                 f"{row['free']['moved_pp']:>+10.2f}")
    L += ["      (percentage points moved on the 24.4)", "",
          f"   P1  worst move at the pinned tip  {p['p1_moved_pp']:+.2f} pp "
          f"against a {p['p1_band_pp']:.1f} pp band -- "
          f"{'MISNAMED' if p['p1_moved_pp'] < p['p1_band_pp'] else 'the gate holds'}",
          f"   P2  best free-tip departure       {p['p2_worst_pct']:.2f} % "
          f"against the {BAND_PCT:.0f} % band -- the shroud mass cannot "
          f"close E7 at any interlock stiffness", ""]
    L.append("   P3  every candidate, on the same footing")
    for row in c["rows"]:
        L.append(f"      {row['variable']:<52}{row['moved_pp']:>+8.2f} pp")
    L += ["", f"   the interlock as a STIFFNESS: best single k "
          f"{s['best_k_N_m']:.2e} N/m -> {s['best_worst_pct']:.2f} % "
          f"(inside the band over a factor of {s['inside_band_width']:.1f} in k)",
          "      FITTED. Not adopted, and E7 stays at "
          f"{p['baseline_worst_pct']:.2f} %.",
          f"   predicted from the printed overhang: "
          f"{min(s['predicted_k_N_m']):.1e}-{max(s['predicted_k_N_m']):.1e} N/m "
          f"-> {s['predicted_worst_pct']:.2f} %, "
          f"{s['predicted_over_fitted']:.0f}x the fitted value", "",
          f"   two published routes to the stage-1 interlock stiffness: "
          f"{r['route_a_overhang_cantilever_N_m']:.2e} (overhang cantilever) "
          f"and {r['route_b_fig66_section_frequency_N_m']:.2e} "
          f"(Fig 66's own {r['fig66_lowest_Hz']} Hz section), agreeing to "
          f"{r['ratio_b_over_a']:.2f}x",
          f"   both are {r['a_over_fitted']:.0f}x and {r['b_over_fitted']:.0f}x "
          f"the fitted value -- the record argues against the soft interlock"]
    return "\n".join(L)
