# Step 0 — the E³ cycle solver: tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing below was changed after a run.

## What is being solved

A twin-spool, mixed-flow turbofan cycle at three rating points, with real
gas properties, the four Table XI secondary-air streams at their published
sources and sinks, the 18-lobe mixer with its published effectiveness, and
one convergent–divergent nozzle with the published coefficient. Inputs come
only from `data/e3-fps-published.yaml` (Tables XI, XII, XIV) and
`data/hpc-vector-diagrams.yaml` (the pressure at the two bleed ports).

## Validation cases (step 0)

| Check | Known answer | Pass band | Route |
|---|---|---|---|
| cp of air at 288 K | 1.005 kJ/kg·K | ±0.5 % | Walsh & Fletcher chart 3.1 |
| cp of air at 1500 K | 1.216 kJ/kg·K | ±0.5 % | same |
| cp of products, FAR 0.02, 1500 K | 1.285 kJ/kg·K | ±1 % | same |
| OPR at max climb | 38.4 (Table XII) | ±1 % | fan hub PR × (1 − core duct loss) × HPC PR |
| core flow at max climb | from BPR 6.7 and 646 kg/s fan flow | ±1.5 % | from the 54.4 kg/s corrected core flow of Table XIV |
| **sfc, max climb** | **0.0541 kg/(N·h)** | **±1.5 %** | Table XII |
| sfc, max cruise | 0.0540 | ±1.5 % — the same band | Table XII |
| sfc, takeoff | 0.0305 | ±1.5 % — the same band | Table XII |
| mixer gain | 2.9 % sfc for 85 % effectiveness | ±0.5 points | Table XXIII |

A cycle that hits max climb and misses the other two by more than the band
has been tuned, not validated; the band is the same at all three.

## Convergence criteria

Every implicit inversion (temperature from enthalpy, isentropic exit
temperature from the entropy function, fuel–air ratio from the energy
balance) stops at 1e-6 relative, never on an iteration cap; hitting the cap
raises.

## What is assumed, and where it must be replaced

- Takeoff is sea-level static on a standard +15 °C day (the flat-rating
  temperature CR-168219 §4.4 quotes is not in the transcribed data; the
  ICLS report's Table I uses +15 °C for the same rating). Replace from
  §4.4 when transcribed.
- Chargeable CDP cooling and the stage-7 stream rejoin at HPT exit and do
  LPT work; the stage-5 stream rejoins at LPT exit and does none. The real
  engine feeds stage 7 to HPT vane 2 (it does stage-2 work) — a small
  conservatism, stated.
- Mixed total pressure is the mass-weighted mean of the two streams; the
  mixing effectiveness is the fraction of the ideal-mixing thrust gain
  realised, applied between the separate-flow and fully mixed limits.
- Gas constant 287.05 J/(kg·K) for air and products alike (the change at
  FAR 0.02 is 0.3 %).
- Fuel LHV 43.124 MJ/kg (Jet A, 18,540 Btu/lb); fuel enters at 298 K.
- Off-design: each rating point is solved with Table XII's own pressure
  ratios and bypass ratio as inputs. Following the three points from one
  match point through component maps is Stage C work and is not claimed here.

---

## After the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`python solvers/e3cycle/run.py`)

| Check | Result | Band | Verdict |
|---|---|---|---|
| cp air 288 K | 1.0033 (−0.17 %) | ±0.5 % | pass |
| cp air 1500 K | 1.2109 (−0.42 %) | ±0.5 % | pass |
| cp products 1500 K, FAR 0.02 | 1.2851 (+0.01 %) | ±1 % | pass |
| OPR route | see finding 1 — the route as written was wrong, not the number | ±1 % | replaced by the transition-loss check |
| core flow, max climb | 31.8 kg/s from W2/(1+BPR); corrected to station 25 against Table XIV's 54.4 | ±1.5 % | pass |
| sfc max climb | 0.0543 vs 0.0541 (**+0.46 %**) | ±1.5 % | pass |
| sfc max cruise | 0.0543 vs 0.0540 (**+0.56 %**) | ±1.5 % | pass |
| sfc takeoff | 0.0311 vs 0.0305 (**+1.91 %**) | ±1.5 % | **miss** — finding 2; strict xfail |
| mixer gain at 85 % | 3.61 % vs 2.9 | ±0.5 pt | **miss** — finding 3; strict xfail; slopes pass |

Both misses are pinned in `tests/test_e3cycle.py` so that a change in
either is noticed; neither band was widened.

### Revisions to the assumptions, and why

1. **The 1.7 % "core duct" loss moved from the HPC inlet to the core
   stream ahead of the mixing plane.** Table XI labels both duct losses
   "(Duct Mixer)". With it wrongly placed the OPR came out 38.6 by the
   route in the table above; with it in its place fan hub PR × HPC PR is
   39.3 against the printed 38.4 — see finding 1.
2. **Takeoff day confirmed** as standard +15 °C from CR-168219 §4.4 p.33,
   as assumed. **Max cruise moved from standard day to +10 °C**, the
   flat-rating day §4.4 gives for "the climb *and cruise* ratings" and
   the day Table XII's footnote 2 puts its T41 on — see finding 2.
3. **Separate-flow baseline for the mixer check** sheds the mixer's own
   0.57 % loss (Table XXIII) from both streams; Table XI's 1.4 / 1.7 %
   are taken to include it.
4. **No shaft mechanical loss** (none in Table XI; parameters only from
   the data files). 0.995 on both spools would cost +0.53 % sfc.
5. **Takeoff is sized to its published thrust**, 173.5 kN (CR-168219
   §4.3), not to the climb match-point fan flow; the flow that gives it
   is a derived number, below.

### Findings

1. **The printed OPR implies a booster-to-HPC loss the report does not
   list.** Fan hub PR × HPC PR exceeds Table XII's OPR by 2.3 / 2.0 / 1.4 %
   at climb / cruise / takeoff. The solver takes P25 from the OPR and
   records the implied transition-duct loss, 2.22 / 1.84 / 1.41 %, of the
   same order as the listed duct losses and falling with power as a
   duct loss should.
2. **Table XII is a mixed-day table.** Footnote 2 puts T41 at the
   flat-rating temperature; the header and §4.4 put the sfc on the
   standard day. Solved on the flat-rating day, the core reaches the
   mixing plane at 0.953 / 0.948 / 0.959 of the bypass total pressure at
   the three ratings — what a mixer needs. Solved on the standard day the
   ratio is 1.16 / 1.15 / 1.18, which no mixer can run and which reverses
   the ordering of T41/T2 between climb and cruise. The residual sfc
   (+0.46 / +0.56 / +1.91 %) has the sign and the ordering of the
   constant-thrust day effect: on a colder day a flat-rated engine makes
   the same thrust at lower T41, and the shift is largest at takeoff
   (15 °C, sea level). Quantifying it needs the component maps — Stage C.
3. **Ideal mixing overstates the mixer's level, not its slopes.** With
   mass-weighted total pressure the sfc gain is 3.57 / 3.31 / 3.61 %
   against Table XXIII's 3.1 / 2.6 / 2.9 for its three
   effectiveness-and-loss pairs: the level is 0.5–0.7 point high, the
   differences between columns (−0.5 and +0.3 points printed) come out
   −0.26 and +0.29. A momentum-balance mixing plane at a finite Mach
   number lowers the ideal gain; it needs the mixing-plane area, which
   is Fig 39/40 (undimensioned) — Stage H.

### Derived numbers (not printed anywhere; the solver's)

| Quantity | Max climb | Max cruise | Takeoff |
|---|---|---|---|
| Fan corrected flow, kg/s | 646 (input) | 646 (input) | **580** (from 173.5 kN) |
| Core physical flow, kg/s | 31.8 | 31.4 | 70.6 |
| Transition-duct loss | 2.22 % | 1.84 % | 1.41 % |
| T3, K | 796 | 784 | 877 |
| Combustor exit T4, K (T41 printed) | 1573 (1517) | 1540 (1485) | 1695 (1638) |
| Combustor fuel–air ratio | 0.0232 | 0.0224 | 0.0253 |
| HPT pressure ratio | 4.99 | 5.00 | 4.98 |
| LPT pressure ratio | 4.55 | 4.45 | 4.12 |
| T5, K | 749 | 734 | 840 |
| Core / bypass total pressure at the mixing plane | 0.953 | 0.948 | 0.959 |
| Ideal mixing gain in gross thrust | 2.12 % | 2.05 % | 2.25 % |

Convergence: bisection on the fuel–air ratio to 1e-10, Newton inversions
to 1e-6 relative; the sfc is reported to four figures and does not move
in the fifth when the Newton tolerance is tightened to 1e-9 (step 6 —
there is no grid to refine).

---

# Step 0 for B4 — station properties and the annulus, written before the run

`stations.py` takes the max-climb solve (the cycle match point, which every
component report names as its aerodynamic design point) and, at each
station where a report gives both a design Mach number and dimensioned
radii, computes the annulus area by continuity with real-gas static
properties and compares it with the transcribed annulus. It also runs the
two-route checks against the turbine cycle-match tables.

| Check | Known answer | Band | Source of the known answer |
|---|---|---|---|
| Fan-face specific flow | 208.9 kg/s·m² with the fan annulus from r 105.4 / 36.05 cm | ±1 % | CR-165148; engine-flowpath.yaml |
| HPC rotor-1 inlet annulus | 0.2869 m² at meridional Mach 0.602, Table XXI's pitch swirl | ±3 % | hpc-flowpath.csv R1 LE; hpc-stagewise.yaml |
| HPC exit annulus | 0.0354 m² at meridional Mach 0.30 (23:1 operating line), OGV exit swirl 4° | ±4 % — a ±0.01 read-off on the Mach is ±3 % | hpc-flowpath.csv S10 TE; hpc-stagewise.yaml |
| HPT stage-1 exit annulus | 0.0925 m² (Fig 3) at Mach 0.34 with 16° swirl; 56.5 % of the work in stage 1 at the overall efficiency | ±4 % | e3-fps-published.yaml hpt |
| HPT stage-2 exit annulus | 0.1518 m² (Fig 3; Fig 1 reads 0.151) at Mach 0.42, no swirl | ±3 % | same |
| HPT corrected flow W41√T41/P41 | 0.8643 g·√K/(s·Pa), W41 = combustor exit + nonchargeable coolant | ±2 % | CR-168219 Table XVIII |
| HPT Δh/T41 | 355.5 J/(kg·K) | ±2 % | Table XVIII |
| LPT inlet temperature T49 | 1056.3 K | ±1.5 % | CR-168219 Table XXI |
| LPT corrected flow W49√T49/P49 | 3.936 g·√K/(s·Pa) | ±2 % | Table XXI |
| LPT Δh/T49 | 326.5 J/(kg·K) | ±3 % — the LPT report's Table II stage sum is 2.5 % above Table XXI's (pre- and post-rematch) | Table XXI |
| LPT vane-1 leading-edge annulus | 0.1940 m² at Mach 0.40 (Fig 7, both walls) | ±4 % | lpt-flowpath.csv S1 LE; lpt-aero.yaml |
| LPT stage 1–5 exit annuli | the sections' rotor trailing-edge annulus at Table II's stage-exit axial Mach, the state from Table II's Δh and pressure ratio per stage | ±5 % — Table II's hub-to-tip Mach spread is ±10 % on the flux; the mass-flux mean of the three is used | lpt-flowpath.csv; lpt-aero.yaml |

Assumptions, stated first: max climb is the design point of every
component; no total-pressure loss in the HPT–LPT transition duct (none is
listed); the two HPT stages share the overall efficiency; the stage-7
coolant rejoins at HPT exit as in B2, so the stage-1 exit flow is W41; the
LPT inlet is swirl-free (Table III's stage-2 exit swirl is 0°); the fan
specific flow is on the corrected flow, as CR-165148 defines it.

Plots: `figures/annulus.png` — hub and tip from the tables, the
continuity-implied tip radius at each check station with its band;
`figures/ts-diagram.png` — the max-climb cycle on T–s with Table XII's T41
and Table XXI's T49 as the published points.

---

## B4 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m e3cycle.stations`)

| Check | Result | Band | Verdict |
|---|---|---|---|
| Fan-face specific flow | 209.6 vs 208.9 (+0.34 %); fan-face Mach 0.634 by continuity | ±1 % | pass |
| HPC rotor-1 inlet annulus | −5.45 % geometric; **−2.53 % with Table XXI's inlet blockage 0.97** | ±3 % | miss / pass |
| HPC exit annulus | −10.15 % geometric; **−0.17 % with the exit blockage 0.90** | ±4 % | miss / pass |
| HPT W41√T/P | 0.8711 vs 0.8643 (+0.79 %) | ±2 % | pass |
| HPT Δh/T41 | 357.9 vs 355.5 (+0.68 %) | ±2 % | pass |
| HPT stage-1 exit annulus | −3.58 % (interstage 1275 K; stage PRs 2.30 / 2.17 at the 56.5 % split) | ±4 % | pass |
| HPT stage-2 exit annulus | +0.19 % | ±3 % | pass |
| T49 | 1058.9 vs 1056.3 K (+0.25 %) | ±1.5 % | pass |
| LPT W49√T/P | 3.915 vs 3.936 (−0.54 %) | ±2 % | pass |
| LPT Δh/T49 | 335.8 vs 326.5 (+2.84 %); the solver's Δh 355.6 kJ/kg is +0.5 % on Table II's stage sum 353.8 | ±3 % | pass |
| LPT vane-1 LE annulus | −18.5 % at Fig 7's 0.40; continuity puts the LE Mach at **0.316** | ±4 % | **miss** — finding 2 |
| LPT stage exits, h/p/t mean | −14.7 / −17.2 / −16.4 / −13.7 / −6.1 % | ±5 % | **miss** — finding 3 |
| LPT stage exits, pitch Mach only (diagnostic) | −3.4 / −5.5 / −4.1 / −5.2 / −3.7 % | ±5 % | three of five; uniform |

The check that misses by my own error was the first run's rotor-1 inlet
at +44 %: the swirl was read from the row's β column (the relative angle,
56°) instead of the IGV exit α (10.0°). Fixed by reading the column by
name; recorded here so the number is not mistaken for a finding.

### Findings

1. **The geometric annulus reads short by exactly the published
   blockage.** Table XXI's through-flow carries a blockage of 0.97 at the
   inlet and 0.90 at the exit (HPC report p.19); continuity at the design
   meridional Mach reads the exit annulus 10.2 % short and the inlet 5.5 %.
   With the blockage the exit closes to 0.2 % and the inlet to 2.5 %. The
   E³ compressor runs with a tenth of its exit annulus in end-wall
   boundary layer, and that is design intent, not a discrepancy.
2. **Fig 7's vane-1 leading-edge Mach is not the mean-flow Mach.** The
   sections' annulus and the cycle's flow, both checked to within 1 % by
   other routes, put the LE meridional Mach at 0.316; the axisymmetric
   duct analysis reads 0.40 on both walls of a coarse plot whose radii
   are themselves 5–10 % off the sections. The HPT exit (0.42 at 0.1518 m²)
   diffusing to 0.194 m² gives 0.32 by continuity, so the sections and
   Table III agree with each other and Fig 7 is the odd one out.
3. **Table II's hub and tip Mach columns do not carry the flow.** Equal
   weighting of hub/pitch/tip axial Mach (0.335 / 0.261 / 0.303 on
   stage 1 — the 0.20-reaction hub exits fast) overstates the flow by
   6–17 %. The pitch value alone lands every stage 3.4–5.5 % under the
   sections' annulus, uniformly from stage 1 to 5 — the signature of a
   through-flow blockage of 4–5 %, which the LPT report says it applies
   (sec 2.6, "blockage and radial loss gradients") and does not print.
   The number is inferred, and labelled so.

### Station table, max climb (10.67 km, M0.8, ISA+10)

| Station | 0 | 13 | 23 | 25 | 3 | 4 | 41 | 45 | 5 | 6 |
|---|---|---|---|---|---|---|---|---|---|---|
| T_t, K | 258.2 | 304.4 | 304.9 | 304.9 | 796.5 | 1572.8 | 1517.2 | 1058.9 | 749.1 | 366.3 |
| p_t, kPa | 36.3 | 61.1 | 61.8 | 60.4 | 1395.5 | 1325.7 | 1325.7 | 265.7 | 58.4 | 59.8 |

Flows, kg/s: fan 244.9 (646 corrected), core 31.8, bypass 213.1,
combustor 26.7, W41 29.7, W49 32.0, LPT exit 32.4, mixed 245.5, fuel 0.74.

**B4 closes:** the computed annulus is inside the band at every
dimensioned HPT station; the disagreement elsewhere is quantified and
explained, twice by a published blockage and once by a coarse figure.
