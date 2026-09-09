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
