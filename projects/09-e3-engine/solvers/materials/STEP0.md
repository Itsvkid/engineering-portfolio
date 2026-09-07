# Step 0 — materials and mass (F): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit F1 — materials with allowables

The work plan's F1 closure: *every stress in Stage E is compared with an
allowable at its metal temperature, and the margin is tabulated.*

**"At its metal temperature" is partly gated, and the gate is in the
handbook, not in the E³ reports.** MIL-HDBK-5J prints room-temperature
design allowables as *tables* — now transcribed into
`data/methods/mil-hdbk-5j-allowables.yaml` for the three alloys the E³
names for rotating parts — but prints *elevated*-temperature strength as
**figures**, percentage of the room-temperature value against temperature,
which were not digitised. Its wrought-alloy scope also excludes René 77,
René 95, René 150 and AF115 entirely, and **no substitute is nominated**:
naming one would put an unsourced allowable into the project under a
handbook's authority. So a margin at temperature is quoted only where an
E³ report prints an allowable; elsewhere the room-temperature margin is
quoted together with **how much of the allowable the metal would have to
lose before the margin is gone**, which is a bound rather than a fudge.

F1's *first* bullet — *alloy per component from the reports* — turns out to
be the interesting one. HPC report Table X prints a material for each of
the ten rotor stages. It also prints, in the same table, each stage's
**airfoil weight** and **root area**, and Table XXII prints the section
shapes. Those three make the density of every blade a **measurement**:

    rho = m_airfoil / (A_root × ∫ A(r)/A_root dr)

Stage E unit E1 inferred a material crossover from the *stress* column and
recorded it as finding 74. This unit measures the same thing from an
independent column, and E1's finding is re-examined against it.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Handbook transcription | Ti-6-4, Ti-8-1-1, Inco 718 room-temperature allowables | exact, as printed in ksi and lb/in³ | MIL-HDBK-5J Tables 5.4.1.0(f), 5.3.2.0(c), 6.3.5.0(c); SI computed, not read |
| Measured blade density, every stage | must land on **one of the two** handbook densities | **±15 %** | the reconstruction's own area accuracy; a 2:1 gap between the candidates makes ±15 % decisive |
| Centrifugal stress recomputed with the measured density | Table X's own column | **±15 %** | if the density measurement is right this must close; it uses a different combination of the same table |
| Table X's material column | printed | must agree with the measurement | **if it does not, one of Table X's columns is wrong and the unit must say which** |
| Ti → Ni switch | Table X's own metal temperatures | the last titanium stage must run **below** ~500 °C, titanium's practical limit | F1's fourth bullet: the switch as a design check, not a fact |
| Every Stage E stress with a *printed* allowable | the report's own limit | **margin ≥ 1.00** | F1's closure, on the parts where an allowable exists |

The 500 °C titanium limit is a handbook generality, stated as such: it is
where titanium's strength and its oxidation and fire behaviour stop it
being used in a compressor, not a number from any E³ report.

---

## Unit F1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m materials.allowables`)

```
handbook densities: Ti-8-1-1 4373,  Inco 718 8221 kg/m3

 st  Table X says  T metal     m g     rho   /Ti   /Ni    nearer  m/max Ti  sig calc  sig pub   err %
  1      Ti-8-1-1      113  284.00    4302  0.98  0.52  titanium      0.60     21.80     21.1     3.3
  2      Ti-8-1-1      178   78.60    4614  1.06  0.56  titanium      0.65     17.64     16.5     6.9
  3      Ti-8-1-1      235   35.60    4333  0.99  0.53  titanium      0.66     13.01     13.1    -0.7
  4      Ti-8-1-1      249   18.00    4605  1.05  0.56  titanium      0.79     12.18     11.0    10.7
  5      Ti-8-1-1      361   19.80    9177  2.10  1.12    nickel      1.49     18.32     17.2     6.5
  6      Ti-8-1-1      423   12.20    8511  1.95  1.04    nickel      1.57     15.42     14.5     6.3
  7       Inco718      480    9.40    8225  1.88  1.00    nickel      1.30     10.57     11.0    -3.9
  8       Inco718      540    6.60    8926  2.04  1.09    nickel      1.40      9.59      9.0     6.6
  9       Inco718      599    4.50    8274  1.89  1.01    nickel      1.30      7.92      8.3    -4.5
 10       Inco718      655    4.00    8486  1.94  1.03    nickel      1.41      7.71      7.6     1.4

measured switch to nickel at stage 5; Table X prints it at stage 7
disputed stages: [5, 6]
printed weight exceeds the heaviest possible TITANIUM blade of its own
root section and span at stages: [5, 6]

airfoil length cross-check, Table X against Table XXII: agree to 1.6 %

Stage E stresses against an allowable
   part                           stress   T C  allowable  margin  may lose
   HPC rotor 1 root, max             365   113        827    2.27       56 %
   HPC rotor 4 root, max             207   249        827    4.00       75 %
   HPC rotor 10 root, max            296   655       1034    3.49       71 %
   fan blade dovetail corner         393     -        503    1.28       22 %
   fan disk post corner              319     -        469    1.47       32 %
   fan disk, max                     393     -        678    1.72       42 %
   LPT blade retainer 1              620   649        634    1.02        2 %
   LPT blade retainer 3              634   649        634    1.00        0 %
   HPT stage-1 disk dovetail        1000     -       1000    1.00        0 %
   (seventeen rows in all)
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Measured density lands on a handbook value | worst 12 %, mean 3 % | ±15 % | pass |
| Stress recomputed with the measured density | worst **10.7 %** | ±15 % | pass |
| Table X's material column agrees | **stages 5 and 6 do not** | must agree | **fail — finding 104** |
| Ti → Ni switch below the titanium limit | last Ti stage 423 °C, first Ni 480 °C | < ~500 °C | pass on the *printed* column, and it is the printed column that makes design sense |
| Every Stage E stress with a printed allowable | worst margin **1.00** | ≥ 1.00 | pass, three of them exactly on |
| **Allowables at temperature** | **only where a report prints one** | — | **gated: MIL-HDBK-5J's elevated-temperature data is figure-status** |

### Findings

104. **Table X contradicts itself, and it takes three of its own columns to
     show it.** The table prints, for every HPC rotor stage, a material, an
     airfoil weight, a root area and a centrifugal stress. Weight over
     (root area × the section shape's integral) is a density, and it comes
     out within 12 % of a handbook value at every stage: **4,302–4,605
     kg/m³ at stages 1–4 (titanium, 4,373) and 8,225–9,177 at stages 5–10
     (Inco 718, 8,221)**. Table X's material column puts the change at
     stage 7. For stages 5 and 6 the two readings are not merely different
     — the printed weight is **1.49× and 1.57× the heaviest a titanium
     blade of that root section and span could possibly be**, which is a
     constant-area one. Table X's own airfoil length agrees with Table
     XXII's to 1.6 %, so the span is not the escape. And recomputing the
     centrifugal stress with the *measured* density reproduces Table X's
     own stress column to 10.7 % at every stage. **Two of Table X's
     columns agree with each other and with Table XXII, and the material
     column disagrees with all three.** Flagged for a re-read of Table X
     p.65 and p.66 — the table already carries one known metric/US print
     inconsistency, in the stage-10 airfoil length.
105. **Correction to finding 74, in three parts.** E1 wrote that (a) "the
     reports never state a blade material stage by stage", (b) the
     crossover falls at stages 4/5, and (c) it "lands exactly on the
     inertia weld CR-168219 describes".
     **(a) is wrong**: HPC report Table X prints a material for every
     stage, in the same table E1 took its stresses from. It was not
     looked for.
     **(b) stands, and is now much better evidenced**: the crossover at
     4/5 no longer rests on the stress column alone. The weight column
     gives it independently, and gives it as a measured density rather
     than as a choice between two trial values.
     **(c) is unsupported and is withdrawn**: CR-168219 says the rotor is
     "inertia-welded forward and aft sections joined by a single bolt
     joint" and **never says where the weld is**. E1 inferred the weld's
     position from its own crossover and then presented the agreement as
     corroboration. That is circular, and it is struck.
106. **The material switch that Table X prints is a temperature decision,
     and the one it implies is not.** Titanium is not used much above
     ~500 °C. Table X's printed switch is at stage 7, where the metal goes
     **423 °C → 480 °C** — right up against the limit, which is exactly
     where a designer would change material and not one stage earlier.
     The measured switch at stage 5 sits at **361 °C**, where there is no
     thermal reason to leave titanium and a real weight penalty for doing
     so. So the two readings are not equally plausible as *design*: the
     material column is the one that makes engineering sense, and the
     weight and stress columns are the ones that are arithmetically
     self-consistent. That is what makes this worth flagging rather than
     resolving — F1's fourth bullet asked for the Ti→Ni switch "as a
     design check, not a fact", and the check passes on the column the
     arithmetic rejects.
107. **Three parts sit exactly on their allowable, and they are the parts
     whose allowable is printed.** LPT blade retainer 3 at 634.3 MPa
     against a 634.3 MPa yield at 649 °C; the HPT stage-1 disc dovetail at
     1,000 MPa "on the limit exactly"; and retainers 1 and 2 within 2 %.
     Every other Stage E stress with a printed allowable clears it by
     1.3–1.7×. The pattern is not an accident of transcription: where GE
     printed an allowable it printed it because the part was *at* it.
108. **The compressor blades have room, and the number that says how much
     is not a margin but a knockdown.** Against MIL-HDBK-5J's
     room-temperature yield, the ten HPC blade roots carry margins of
     2.3–4.2. Since the elevated-temperature allowable is figure-status,
     the useful statement is the other way round: **the metal would have to
     lose 56 % of its room-temperature yield before the worst of them
     (stage 1, at 113 °C) reached it**, and 66 % before stage 6 at 423 °C
     did. Neither titanium nor Inco 718 loses anything like that at those
     temperatures, so the conclusion survives the gate even though the
     number behind it does not.

---

## Unit F2 — mass

The work plan's F2 closure: *basic engine mass within **10 %** of 3,473 kg,
and no module more than 20 % off.*

**That closure is gated, and by the same A3 gaps Stage E hit.** Building
3,473 kg from geometry needs the disc profiles (un-digitised, E2's finding
81), the casings and frames (figure-status), and the **320 kg of sumps,
drives and seals** that Table XXVI itself calls out — 9.2 % of the basic
engine, more than twice the combustor, casing and diffuser together — for
which no bearing or sump geometry is printed anywhere (E4's gate). A total
assembled without those would be an invented engine, not a reconstructed
one, and it would pass a ±10 % band by arithmetic rather than by evidence.

What can be done splits in two, and the first half is something the
project has never done before.

**The C3 blading reconstruction has been checked on angles and on throats.
It has never been checked on *area*.** HPC report Table X prints a root
area and a tip area for every one of the ten rotor stages, plus an airfoil
weight and a whole-blade weight. The sections C3 unit 12 built from
camber, stagger and thickness can be integrated and put against all of
them.

**And the published masses can be checked against each other.** Four
separate component reports print a module weight that CR-168219's Table
XXVI prints again. Nothing in the project has ever had to make those
agree.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Built section area vs Table X | 20 printed areas | **±20 %** | a double-circular-arc camber line with a quarter-sine thickness law omits the leading- and trailing-edge radii, so a bias is *expected*; the band is wide because this is a first calibration |
| The sign of that error | — | if there is a bias it should be **one-sided** | a thickness law that under-fills does so everywhere; a scattered error would mean noise, a one-sided one means a correctable model |
| Built airfoil mass vs Table X's airfoil weight | 10 printed weights | **±20 %** | the area error carries straight into it |
| Airfoil as a fraction of the whole blade | printed for all ten HPC stages | must be **< 1** everywhere, and the trend is an output | the remainder is platform, shank, dovetail and shroud |
| Module weight, component report vs Table XXVI | five modules | **±5 %** | two independent documents printing the same module; nothing in either was derived from the other |
| **Basic engine total** | 3,473 kg | ±10 % | **gated — not attempted** |

---

## Unit F2 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m materials.mass`)

```
1. Twenty printed airfoil areas against the sections C3 built
    st  root built   root X   err %   tip built   tip X   err %
     1       6.686    6.915    -3.3       1.743   1.897    -8.1
     2       2.465    2.596    -5.0       0.867   0.944    -8.1
     3       1.565    1.634    -4.2       0.449   0.537   -16.5
     4       0.813    0.908   -10.5       0.366   0.417   -12.1
     5       0.615    0.665    -7.4       0.274   0.313   -12.5
     6       0.416    0.485   -14.2       0.209   0.238   -12.1
     7       0.527    0.542    -2.8       0.215   0.216    -0.5
     8       0.396    0.418    -5.3       0.192   0.204    -6.0
     9       0.328    0.344    -4.6       0.172   0.183    -6.3
    10       0.302    0.313    -3.4       0.154   0.163    -5.4
   twenty comparisons: mean -7.4 %, worst -16.5 %, 20 of 20 negative

2. And what those sections weigh
    st  material   built g  printed g   err %  whole blade g  airfoil %
     1  titanium    271.31     284.00    -4.5         550.00         52
     2  titanium     70.16      78.60   -10.7         183.30         43
     3  titanium     34.13      35.60    -4.1          82.40         43
     4  titanium     15.22      18.00   -15.5          47.70         38
     5    nickel     16.38      19.80   -17.3          62.80         32
     6    nickel     10.02      12.20   -17.9          44.50         27
     7    nickel      9.10       9.40    -3.2          43.30         22
     8    nickel      5.76       6.60   -12.7          29.50         22
     9    nickel      4.27       4.50    -5.1          20.10         22
    10    nickel      3.73       4.00    -6.7          15.50         26

3. How much of a blade is airfoil
   fan rotor      66 %      HPC 1   52 %      LPT stage 1   41 %
   booster        48 %      HPC 4   38 %      HPC 7-9       22 %

4. Five module weights, printed twice in two different reports
   fan + booster rotor    496.2 vs 481    +3.2 %
   HPT rotor              282.0 vs 283    -0.4 %
   HPT stator             132.0 vs 132    +0.0 %
   LPT rotor              254.4 vs 260    -2.2 %
   LPT stator             250.4 vs 257    -2.6 %

5. What fraction of a rotor module is blades
   HPC rotor               46.5 of 214 kg   22 %   (167.5 kg is disc and joint)
   LPT rotor              135.0 of 260 kg   52 %
   fan + booster rotor    248.6 of 481 kg   52 %
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Built area vs 20 printed areas | mean −7.4 %, worst −16.5 % | ±20 % | pass |
| One-sided bias | **20 of 20 negative** | must be one-sided if present | pass — finding 109 |
| Built airfoil mass vs 10 printed weights | mean −9.8 %, worst −17.9 % | ±20 % | pass |
| Airfoil fraction | 22–66 %, always < 1 | must be < 1 | pass |
| Module weight across two reports | worst **+3.2 %**, one exact | ±5 % | pass — finding 111 |
| **Basic engine total** | **not attempted** | ±10 % | **gated — finding 112** |

### Findings

109. **The blading reconstruction is 7 % thin, and all twenty comparisons
     agree on the sign.** Against Table X's printed root and tip areas the
     sections C3 built from camber, stagger and thickness come out
     **−7.4 % on average, worst −16.5 %, and negative every single time**.
     A one-sided error is a model, not noise: the double-circular-arc
     camber line with a quarter-sine thickness distribution has no
     leading- or trailing-edge radius, and a section that ends in a point
     at both ends is lighter than one that ends in a circle. The airfoil
     masses inherit it almost exactly — mean −9.8 %. **This is the first
     time in the project that the reconstruction's *area* has met a
     published number**; angles and throats were checked in C3 units 12–15
     and area never was. The bias is recorded, not applied: correcting it
     would need the edge radii, which Table X prints as t/c ratios that
     the section builder already consumes.
110. **The smaller the blade, the less of it is blade.** Airfoil as a
     fraction of whole-blade weight runs **66 % on the fan**, 52 % on HPC
     stage 1, 48 % on the booster, 41 % on LPT stage 1, and falls to
     **22 % by HPC stages 7–9**. A dovetail does not shrink with the
     airfoil it holds — it is sized by the load and by the disc rim it has
     to fit into — so a 2 cm rear-stage compressor blade is three-quarters
     attachment. That is the mass argument against small blades, and it
     runs the opposite way to the aerodynamic argument for them.
111. **Five module weights, two documents each, and they agree to 3.2 %.**
     CR-165148's Table VI, CR-167955's Table XXIII and CR-168289's Table
     XXI each print a module weight that CR-168219's Table XXVI prints
     again, and none was derived from another. The HPT stator matches
     **exactly**, the HPT rotor to 0.4 %, the LPT rotor and stator to
     2.2 % and 2.6 %, and the fan-plus-booster rotor to 3.2 % — the last
     being the biggest and the one whose component table includes a shaft
     the whole-engine table may group elsewhere. For a project that has
     spent four stages finding places where two published numbers do not
     agree, it is worth recording a place where five do.
112. **F2's closure is gated on the same three things Stage E was, and
     the biggest of them is the one nobody draws.** The basic engine is
     3,473 kg. Sumps, drives and seals are **320 kg of it — 9.2 %, more
     than twice the combustor, casing and diffuser at 137 kg** — and not
     one bearing load, span or capacity is printed anywhere in the E³
     reports. Add the un-digitised disc profiles (which are 167.5 kg of a
     214 kg HPC rotor module, and 48 % of the fan and LPT rotors) and the
     figure-status casings and frames, and what remains buildable is 22–52
     % of three modules out of eight. A ±10 % total assembled over those
     gaps would pass by arithmetic and not by evidence, so it is not
     attempted.
