# References

Every source this project runs on, what it gives, and its licence. 41
documents, all fetched by `./fetch-sources.sh`, all public domain or openly
published.

**The rule:** a number in the model must be traceable to a row in this file.
If it cannot be cited, it is an assumption, and assumptions are labelled as
such in `data/e3-fps-published.yaml`.

Fetch pattern for NTRS: `https://ntrs.nasa.gov/api/citations/<ID>/downloads/<ID>.pdf`.
Most are scanned; read as page images. PDF-page offsets per report are in
[DATA-INDEX.md](DATA-INDEX.md).

---

## 1 · The E³ programme — the engine being rebuilt

General Electric for NASA Lewis under contract NAS3-20643, Aircraft Energy
Efficiency Program. **All US Government works, public use permitted.**

| File | NTRS | Gives |
|---|---|---|
| **`e3-fps-final-design-CR-168219.pdf`** | 19900019242 | **The primary source.** Cycle at 3 ratings (Table XII p.35), component performance and cooling flows (XI p.34), fan (§5.1, XIII), compressor (§5.2, XIV, XV), combustor (§5.3), HPT (§5.4, XVIII), LPT (§5.5, XXI), turbine frame, **sumps and bearings (§5.7, Figs. 37–38)**, exhaust and mixer (§5.8, XXIII), nacelle, controls, dynamics, **weights (XXVI p.140)**, cross-sections of every component |
| `e3-fps-preliminary-analysis-CR-159584.pdf` | 19810013521 | The FPS as first laid out — what changed and why |
| `e3-preliminary-design-CR-135444.pdf` | 19780023165 | Trade studies behind the configuration (402 pp.) |
| `e3-fan-hardware-design-CR-165148.pdf` | 19830008070 | Fan and quarter-stage detailed design: blade, shroud, dovetail, containment |
| `e3-fan-quarter-stage-performance.pdf` | 19850025828 | Fan rig test results — measured against design |
| **`e3-hp-compressor-detail-design.pdf`** | 19850002690 | **Table X per-stage rotor summary; Table XXI stator vector diagrams and geometry; Table XXII rotor section geometry**; Campbell diagrams all stages; clearances; casing bolting; dovetails |
| `e3-combustor-hardware-design.pdf` | 19900019238 | Double-annular combustor design: liner, dome, nozzles, diffuser, cooling, emissions |
| **`e3-hp-turbine-hardware-CR-167955.pdf`** | 19850002687 | **Dimensioned flowpath (Fig. 3); stage aero and blade counts (III); blading geometry (IV); airfoil shapes (Fig. 6)**; cooling design (§3); ACC; every disc and shaft with stress and LCF (§5.2.1) |
| `e3-hp-turbine-cooling-model.pdf` | 19810018555 | The HPT cooling design method |
| `e3-lp-turbine-hardware.pdf` | 19850002686 | Five-stage LPT: flowpath, vector diagrams, blade shapes per stage, discs, seals, ACC |
| `e3-controls-and-accessories.pdf` | 19850021645 | FADEC, VSV actuation, ACC valves, fuel system |
| `e3-component-development-vol2-appA.pdf` | 19850002683 | Component development summary across the programme |
| `e3-core-design-and-performance.pdf` | 19900019243 | The core as tested (538 pp.) |
| `e3-icls-design-and-performance-CR-168211.pdf` | 19900019245 | **The engine as tested** — measured performance to compare the FPS *design* numbers against |

## 2 · Design methods — public-domain textbooks

| File | Source | Gives |
|---|---|---|
| **`nasa-sp36-axial-compressor-design.pdf`** | NASA SP-36, Johnsen & Bullock 1965, NTRS 19650013744 | **The compressor design method**: diffusion factor, cascade loss and deviation, radial equilibrium (ch. VIII), stall, blade-element theory. The method behind the E³ HPC |
| **`nasa-sp290-turbine-design-vol1-2-3.pdf`** | NASA SP-290, Glassman 1972–75, NTRS 19950015924 | **The turbine design method**: velocity diagrams, blade design, loss, radial equilibrium, cooling, mechanical |
| `naca-tn3916-65-series-cascade-tests.pdf` | NACA TN 3916, Herrig, Emery & Erwin 1957, NTRS 19930084843 | Systematic 65-series cascade data — the validation set for compressor loss and deviation |
| `naca-tn3806-65-series-rotor-vs-cascade.pdf` | NACA TN 3806, NTRS 19930084578 | Same sections in a rotor vs in cascade — what 3-D does to 2-D data |
| `arc-rm2974-ainley-mathieson-turbine-loss.pdf` | ARC R&M 2974, Ainley & Mathieson 1951, Cranfield AERADE | The turbine loss method: profile, secondary, tip clearance, trailing edge |
| `agard-ls167-blading-design-axial-turbomachines.pdf` | AGARD LS-167, 1989, DTIC ADA211103 | Blading design methods incl. transonic and controlled-diffusion sections |
| `mit16-50-lec29.pdf`, `mit16-50-lec31-…` | MIT OCW 16.50, CC BY-NC-SA | Cycle; compressor–turbine matching |

## 3 · Validation test cases — prove the method before applying it

| File | Source | Gives |
|---|---|---|
| `nasa-tp1337-rotor37-design-and-performance.pdf` | NASA TP-1337, Reid & Moore 1978, NTRS 19780025165 | **Rotor 37**: geometry and measured performance of the standard transonic compressor test case — 36 blades, PR 2.106, 454 m/s |
| `nasa-rotor37-cfd-code-validation.pdf` | NTRS 20100029589 | How Rotor 37 is used to validate a CFD code, and what "agreement" looks like |
| `nasa-tp2879-rotor67-laser-anemometer.pdf` | NASA TP-2879, Strazisar et al. 1989, NTRS 19900001929 | **Rotor 67**: laser-anemometer flowfield in a transonic fan rotor, tip Mach 1.38 — the fan validation case |

## 4 · Thermal — cooling and secondary air

| File | Source | Gives |
|---|---|---|
| **`nasa-tp2232-internal-cooling-heat-transfer-review.pdf`** | NASA TP-2232, Yeh & Stepka 1984, NTRS 19840013760 | **Internal-passage heat-transfer and pressure-loss correlations** — the cooling-network method, with data |
| `nasa-tmx52801-turbine-cooling-limits-and-future.pdf` | NASA TM X-52801, Esgar 1970, NTRS 19700018642 | Convection, transpiration and full-coverage film cooling compared |
| `nasa-tmx2791-internal-air-cooling.pdf` | NASA TM X-2791, NTRS 19730016202 | Internal air cooling heat transfer |
| `nasa-cooling-methods-first-principles.pdf` | NTRS 20030064309 | Cooling methods from first principles |
| `nasa-full-coverage-film-cooling-study.pdf` | NTRS 19760011294 | Full-coverage film cooling heat transfer |
| `nasa-turbomachine-sealing-secondary-flows.pdf` | NTRS 20040086723 | Seals and secondary-flow systems |

## 5 · Mechanical — vibration, life, attachments

| File | Source | Gives |
|---|---|---|
| `nasa-bladed-disk-vibration.pdf` | NTRS 19870017475 | Bladed-disc modal behaviour |
| `nasa-mistuned-bladed-disk-flutter.pdf` | NTRS 19840015855 | Mistuning and flutter |
| `nasa-hot-section-fatigue-life-prediction.pdf` | NTRS 19880005071 | Creep–fatigue life methods for hot-section parts |
| `nasa-blade-root-fretting-single-crystal.pdf` | NTRS 20000033269 | Fretting at single-crystal blade roots |
| `nato-en-avt-207-10-blade-hcf-campbell.pdf` | NATO STO EN-AVT-207-10 | Blade HCF and Campbell diagrams |

## 6 · Materials

| File | Source | Gives |
|---|---|---|
| **`mil-hdbk-5j-metallic-materials.pdf`** | MIL-HDBK-5J, DoD 2003, distribution unlimited (Internet Archive mirror) | **Design allowables at temperature**: Ti-6Al-4V, Ti-8Al-1Mo-1V, Inconel 718, steels, aluminium — tensile, fatigue, creep where listed. Superseded by MMPDS (paywalled); 5J is the last public issue |

For cast and single-crystal superalloys not in 5J, the E³ reports give the
alloy and the design stresses used (HPC Table X; HPT Figs. 51–55); state
the substitution when a 5J alloy stands in.

## 7 · Combustion

| File | Source | Gives |
|---|---|---|
| `agard-cp422-combustion-and-fuels.pdf` | AGARD CP-422, 1988, DTIC ADA202495 | Combustor design methods, emissions, fuel effects |

Lefebvre & Ballal, *Gas Turbine Combustion*, is the textbook; cite it,
do not paraphrase.

## 8 · Certification

| File | Source | Gives |
|---|---|---|
| `easa-cs-e-amendment-8.pdf` | EASA CS-E Amdt 8 | 515 critical parts · 810 blade-out · 840 rotor integrity · 800 bird · 740 endurance |
| `faa-14cfr-part33-engines.pdf` | 14 CFR Part 33, 2024 ed. | 33.27 overspeed · 33.62 stress · 33.70 life-limited parts · 33.75 safety · 33.76 bird · 33.87 endurance · 33.94 containment |

Open them for wording. Never paraphrase a regulation from memory into a
document.

## 9 · Context — the GE90

| File | Source | Gives |
|---|---|---|
| `ge90-100-type-acceptance-NZ.pdf` | CAA NZ TAR 11/21B/7, validating FAA TC E00049EN | GE90 baseline 1 / 3 / 10 / 2 / 6; -100 series 4-stage booster, 9-stage HPC with blisk, DAC II combustor; SC-33-ANE-08-NE composite fan |

**Context only.** The GE90's geometry is proprietary. Nothing from it enters
the model.

---

## Textbooks — cite, do not paraphrase into documents

Saravanamuttoo, Rogers, Cohen — *Gas Turbine Theory* · Dixon & Hall —
*Fluid Mechanics and Thermodynamics of Turbomachinery* · Walsh & Fletcher —
*Gas Turbine Performance* · Mattingly — *Elements of Propulsion* · Kerrebrock
— *Aircraft Engines and Gas Turbines* · Cumpsty — *Compressor Aerodynamics*
· Lefebvre & Ballal — *Gas Turbine Combustion* · Han, Dutta & Ekkad — *Gas
Turbine Heat Transfer and Cooling Technology* · Reed — *The Superalloys* ·
Rolls-Royce — *The Jet Engine* · Kacker & Okapuu 1982, Dunham & Came 1970
(turbine loss updates, ASME).

Legitimate route: Cranfield's library, or buying them.

## Not available, and what stands in

| Wanted | Status | Stand-in |
|---|---|---|
| E³ fan blade section coordinates | not published | designed by the SP-36 / AGARD LS-167 method; labelled an assumption |
| GE coordinate tapes named in HPC Table X | not public | sections reconstructed from Table XXII parameters |
| SAE ARP755 station numbering | paywalled | the convention as used in the E³ reports and PF-08 |
| MMPDS | paywalled | MIL-HDBK-5J |
| Kacker–Okapuu, Dunham–Came | ASME | Ainley–Mathieson R&M 2974 + SP-290 |

---

## Verified 3 September — the architecture block is closed

| Claim | Settled as | Where |
|---|---|---|
| E³ fan blade count | **32**, solid Ti, 50 % span shrouds | CR-168219 §5.1.2 p.45; Fig. 13 |
| E³ booster | **single quarter-stage** under an untrapped island; rows 60 / 56 / 64 | §5.1 p.37, §5.1.1 p.43 |
| E³ HPC | 10 stages, **23.0** at the match point, 0.860 / 0.906 | §5.2 p.45, Table XIV p.51 |
| E³ LPT | **5** stages | §5.5 p.82 |
| E³ combustor | **double annular**, 60 cups, 30 nozzles | §5.3 pp.57–62 |

## Still to verify before quoting

| Claim | Status | Settle at |
|---|---|---|
| Booster rows 60 / 56 — vane vs blade | assigned by position in Fig. 13 | fan hardware report CR-165148 |
| HPC variable-stator row count | CR-168219 says IGV+1–4; HPC report says IGV+1–5 for the product | use the HPC report; note both |
| LPT blade counts per stage | not yet transcribed | LPT report §4.2.1, Fig. 52 |
| GE90-115B fan diameter and dry weight | sources disagree / unsourced | context only; not needed for the model |

Full inventory of transcribed / located / to-digitise:
[DATA-INDEX.md](DATA-INDEX.md).
