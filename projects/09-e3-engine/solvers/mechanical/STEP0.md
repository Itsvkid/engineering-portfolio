# Step 0 — mechanical solvers (E): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit E1 — centrifugal stress at every HPC blade root

The work plan's E1 closure: *Table X centrifugal stresses reproduced
within **10 %** all ten stages.*

A rotating blade's root stress is

    sigma_root = (rho·omega²/A_root) ∫_root^tip A(r)·r·dr

and everything on the right except the density is already transcribed.
Table XXII gives the chord and the maximum thickness ratio at twelve
sections of every rotor, so the area distribution follows as
A(r) ∝ c(r)²·(t/c)(r) — and because only the **ratio** A(r)/A_root enters,
the airfoil shape constant cancels and nothing about the section's shape
needs assuming.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Root centrifugal stress, all ten stages | Table X | **±10 %** | the work plan's own E1 criterion |
| Rotational speed | 13,948 rpm | — | Table X's own footnote: the stress case is the *deteriorated engine*, not the 12,303 rpm aero design point |
| Blade density | not published per stage | — | the rotor is "inertia-welded forward and aft sections"; **both titanium and a nickel alloy are carried, and which stages take which is an output, not an input** |

---

## Unit E1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m mechanical.blade_stress`)

```
HPC blade root centrifugal stress at the Table X stress case: 13948 rpm
(Table X's footnote: Nc deteriorated, the max-pressure/max-temperature case)

 stage   r_root   r_tip   taper   Ti kN/cm2   Ni kN/cm2   printed  Ti diff %  Ni diff %
     1    19.07   34.73   0.564       22.45       41.51      21.1        6.4       96.7
     2    22.86   33.45   0.601       16.94       31.32      16.5        2.7       89.8
     3    25.16   32.72   0.643       13.30       24.60      13.1        1.6       87.7
     4    26.32   32.03   0.745       11.72       21.66      11.0        6.5       96.9
     5    26.88   31.43   0.705        8.84       16.35      17.2      -48.6       -5.0
     6    27.12   30.79   0.799        8.03       14.84      14.5      -44.7        2.3
     7    27.31   30.36   0.683        5.69       10.52      11.0      -48.2       -4.3
     8    27.35   29.92   0.683        4.76        8.80       9.0      -47.1       -2.2
     9    27.37   29.67   0.683        4.24        7.84       8.3      -48.9       -5.5
    10    27.37   29.43   0.725        4.02        7.44       7.6      -47.1       -2.1

within 10 % on titanium: stages [1, 2, 3, 4]
within 10 % on nickel:   stages [5, 6, 7, 8, 9, 10]
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Stages 1–4, titanium | +6.4, +2.7, +1.6, +6.5 % | ±10 % | pass |
| Stages 5–10, nickel | −5.0, +2.3, −4.3, −2.2, −5.5, −2.1 % | ±10 % | pass |
| **All ten stages** | **worst 6.5 %** | ±10 % | **E1's closure met** |

### Findings

73. **All ten root stresses reproduce within 6.5 %, from geometry
    alone.** The chord and thickness at twelve sections per rotor, the
    root and tip radii, one rotational speed and one density — nothing
    else. The work plan asked for 10 % and the worst stage is 6.5.
74. **The material crossover falls out of the stress data, and it lands
    exactly on the weld.** Stages 1–4 match a titanium density to within
    6.5 %; stages 5–10 match a nickel-alloy density to within 5.5 %; and
    neither works for the other group — titanium reads the rear stages
    **47 % low** and nickel reads the front stages **90 % high**. The E³
    reports never state a blade material stage by stage. But CR-168219
    describes the HPC rotor as "**inertia-welded forward and aft
    sections** joined by a single bolt joint", and the crossover this
    calculation finds — between stage 4 and stage 5 — is where that weld
    is. A published stress table and a one-line construction note,
    neither referring to the other, locate the same joint.
75. **Table X's stresses are at the deteriorated-engine speed, and its
    own footnote is the only place that says so.** 13,948 rpm, not the
    12,303 of the max-climb aero design point. That is a factor of 1.29
    in stress: computing at the design speed would have read **every
    stage 22 % low** and looked like a systematic modelling error rather
    than a misread condition. Blade stress is quoted at the worst case a
    designer must survive, not at the point the aerodynamics was drawn
    for — and the two differ by 13 % in speed on this engine.
76. **The taper factor runs 0.56 to 0.80 and it is the whole point of
    tapering a blade.** A constant-area stage-1 blade would carry 40
    kN/cm²; the real tapered one carries 22. Every stage's factor is
    recorded, and the front stages — longest blades, most to gain — are
    tapered hardest.
