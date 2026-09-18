# Stage D · secondary air, the rotating side

---

## Unit D9 — the stage-1 blade's two printed coolant margins · step 0, 2026-09-18

Written **before** `solvers/secondary/backflow.py` first ran.

### The question

D3 is half closed. Its first half — the secondary-air budget against
Table XI's 16.1 % of W25 — closed at 0.04 %. Its second is the sentence
*"every cavity keeps hot gas out"*, and only the stage-1 **nozzle's** two
cavities have ever been checked (D3 finding 65, resolved by D7 finding
233). The two that remain are on the **blade**, and both are already
transcribed in `hpt-cooling.yaml`:

| | |
|---|---|
| design dovetail pressure ratio | **1.35** |
| minimum supply pressure ratio | 1.235 |
| tip backflow margin at design | **1.10** |
| inducer-seal damage case | dovetail ratio 1.24 → tip margin **1.09** |
| definition, as printed | **`P_sc / P_tb`, coolant supply over blade total** |
| Fig 26's own claim | *root, pitch and tip margins all rise linearly with pressure ratio* |

**The definition is not the vane's.** The vane's is
`100·(Ps_coolant − P_gas)/P_gas` and D7 established which gas pressure each
of its two cavities is referenced to. The blade's is a bare ratio of a
coolant supply to a *blade* total — a **relative** total pressure, in the
rotating frame, which is a different quantity from anything on the vane.

### Why the obvious band cannot be met, and what replaces it

The natural band is *reproduce each printed margin to 0.5 %*, which is
what D7 achieved on the vane. **It is not reachable here, and the reason
is worth stating before the run rather than after.** The chain from the
dovetail to the tip leading edge is

    P_sc,tip = P_sc,dovetail · (rotational pumping) · (1 − internal loss)

and the internal loss of a five-pass serpentine with turbulators, a tip
cap and film holes is **not published anywhere** — CR-167955 prints the
blade's *flows* (Fig 24, Fig 25) and its *metal temperatures* (Fig 27) and
never a coolant pressure inside the airfoil. Two of the three terms can be
computed from published data and the third cannot, so the honest form is
the one D7 used on the film holes: **invert the printed pair for the
missing term and test whether it is physical.** The dovetail radius is
also unpublished, so the pumping is computed over the *published* part of
the radius rise only and the implied loss is a **lower bound**.

### Bands

| # | Band | Why |
|---|---|---|
| 1 | every printed blade margin exceeds unity, including the inducer-seal damage case, and the design dovetail ratio exceeds the printed minimum supply ratio | **this is D3's closure sentence itself** — *keeps hot gas out* is an inequality, and it is answerable on printed numbers alone |
| 2 | rotational pumping from the flowpath hub to the blade tip, from the published radii, the published HP speed and the printed coolant temperature, is a gain of **5–30 %** | a 4 cm span on a 35 cm radius at 12,645 rpm. Hand estimate before the run: **+9.8 %** |
| 3 | with **no** internal loss the predicted tip margin **exceeds** the printed 1.10 | every term left out reduces it, so a forward calculation without losses must be an upper bound. If it comes out below 1.10 the model is wrong, not the report |
| 4 | the internal total-pressure loss the printed pair implies is **10–45 %** | the range a multipass cooled blade runs. Hand estimate before the run: **about 30 %** |
| 5 | Fig 26's two printed points give a line **flatter** than proportionality — slope < 1.10/1.35 = 0.815 | stated as an inequality because two points are all that is printed. A proportional line would put the damage case at 1.010, and the report prints 1.09 |
| 6 | the gas-side relative total pressure is **higher at the hub than at the tip**, so the spanwise term helps the tip | W² = c_x² + (c_θ − U)² and U falls inward faster than c_θ rises, on any vortex law. Bracketed free-vortex against solid-body rather than assumed |

### Not attempted

The pitch margin, because Fig 26's pitch line is not transcribed — only
the tip value and the two dovetail ratios are. The dovetail radius, which
is unpublished. And any forward prediction of 1.10, for the reason above.

---

## Unit D9 — after the run · 2026-09-18

`python -m secondary.backflow`. Nothing above was edited.

| # | Band | Result | Verdict |
|---|---|---|---|
| 1 | every printed blade margin over unity; design ratio over the minimum supply ratio | all four hold; **9.3 % headroom** on the dovetail ratio | **pass — D3's closure sentence** |
| 2 | pumping 5–30 % | **×1.0928** over the published 32.58 → 36.58 cm rise at 12,303 rpm and 628 °C coolant (estimate before the run: +9.8 %) | **pass** |
| 3 | lossless tip margin above the printed 1.10 | **1.457–1.569** | **pass** |
| 4 | implied internal loss 10–45 % | **24.5–29.9 %** (estimate before the run: about 30 %) | **pass** |
| 5 | Fig 26's line flatter than proportionality | slope **0.0909** against a proportional 0.8148 | **pass** |
| 6 | P_t,rel higher at the hub than at the tip on any vortex law | free vortex **1.0632**, solid body **0.9879** | **MISS — finding 250** |

### Findings

249. **The blade's backflow margin is a relative total pressure and the
     vane's is not, and that is why the vane closed to 0.015 % and the
     blade cannot.** The vane's printed definition is
     `100·(Ps_coolant − P_gas)/P_gas` and every term in it is a stationary
     pressure the report prints. The blade's is `P_sc/P_tb`, *coolant
     supply over blade total* — a pressure in the rotating frame, reached
     through a rotational pump and a five-pass serpentine whose internal
     pressure loss **CR-167955 never prints**. Two of the three terms are
     computable and the third is not, so the honest form is D7's: invert
     the printed pair for the missing term and ask whether it is physical.
     It is — **24.5 to 29.9 %** of the supply total pressure, on a bracket
     that is a vortex law rather than a fudge, and a lower bound because
     the dovetail radius is unpublished and every centimetre below the
     flowpath hub adds more pumping to be lost.
250. **On a 4 cm blade the vortex law decides the SIGN of the spanwise
     term, not its size.** Step 0 asserted that the gas relative total
     pressure must be higher at the hub *on any vortex law*, reasoning
     that U falls inward faster than c_θ rises. That is true of a free
     vortex — 1.0632 — and **false of a solid body**, which gives 0.9879,
     because on a solid body c_θ falls inward too and
     (c_θ − U) = r(c_θp/r_p − ω) grows with radius whenever c_θp/r_p
     exceeds ω, which it does here: 1,819 s⁻¹ against 1,288. The E³ HPT is
     neither law — C2 unit 11 measured its work peaking at 50–55 % span —
     so the bracket is the answer and it is worth **5.4 points** of
     implied internal loss. A band stated before the run, missed, and
     costing nothing, because both ends land inside band 4.
251. **Fig 26's tip line is nine times flatter than proportionality, and
     that is the inducer-seal failure case's whole margin.** If the tip
     supply pressure were simply the dovetail supply times a fixed factor,
     the margin would be proportional to the dovetail ratio — slope
     0.8148 — and the damage case at a dovetail ratio of 1.24 would sit at
     **1.010**, a 1 % margin. The report prints **1.09**. The two printed
     points give a slope of **0.0909**, so the blade's internal circuit is
     strongly flow-limited: the tip cavity pressure is nearly independent
     of what the dovetail is fed, and losing 11 points of supply ratio
     costs only 1 point of tip margin. That is why a damaged inducer seal
     is a survivable case on this blade rather than an immediate ingestion
     event.

### What D3's second half is now

Met as an inequality, which is what the closure sentence asks. **All four
numeric backflow margins CR-167955 prints are now checked** — the stage-1
nozzle's forward and aft cavities by D7, the stage-1 blade's tip and
dovetail here. The stage-2 nozzle's *"positive coolant backflow margin"*
is a listed design feature (§5.1.2's feature list) with **no printed
number**, and is named here so that a later reader does not record it as
an unchecked cavity. What is *not* met, and was declared unreachable
before the run, is a forward reproduction of 1.10 to 0.5 %: that needs the
blade's internal pressure loss, which is in no document on disk.
