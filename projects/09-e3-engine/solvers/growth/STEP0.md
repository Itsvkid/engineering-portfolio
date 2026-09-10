# Step 0 — growth engine (K): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Why there is a Stage K at all

The work plan ends at Stage J, and the reconstruction it scoped is done.
But two lines in the transcribed data say the machine this project spent
nine stages validating was **not designed for the case it was validated
against**:

> `optimum_max_takeoff_C: 1365` / `design_max_takeoff_C: 1343` — *"Set on
> the low side of the sfc optimum (Fig 10, flat between 1343 and 1365 C)
> **to leave thrust-growth potential**. Final-design fan pressure ratio
> 1.65 against 1.7 preliminary."* (CR-167955 sec 3.1.2 p.21)

> `designed_for: growth engine, 15-20 percent higher thrust — higher T3,
> T41, pressure and speed; **the growth case was limiting throughout**`
> (CR-167955 sec 3.2.7 pp.59-65)

GE gave up sfc at the design point to buy growth headroom, and sized the
hot-section rotor structure to a case this project has only transcribed.
Stage K asks what that headroom cost and whether the hardware has it.

## Unit K2 — does the FPS hardware have the margin the growth case needs?

Unit F1 tabulated **seventeen** stresses against a printed allowable and
found every one with margin — but **four sitting at or within 2 % of the
limit**: the three LPT blade retainers (1.022, 1.011, **1.000**) and the
HPT stage-1 disk dovetail (**1.000**, which the report itself calls *"on
the limit exactly"*).

The fan report separately claims the hardware was sized with growth in
mind: `hub_radii_oversized_for_growth: true`.

**Both claims are testable, and they can disagree.**

### Method, and the one assumption in it

Centrifugal stress scales with the square of rotational speed. The growth
requirements print a **corrected fan tip speed** for each of three
ratings against the FPS's own, so the LP spool's speed ratio is published,
not inferred:

| rating | FPS m/s | growth m/s | ratio | stress ×|
|---|---|---|---|---|
| 1 | 411.5 | 457.2 | 1.1111 | **1.2346** |
| 2 | 399.6 | 446.8 | 1.1181 | 1.2502 |
| 3 | 365.2 | 420.9 | 1.1525 | 1.3283 |

`booster_speed_increase_pct: 11` agrees with rating 1 to a tenth of a
percent, which is the cross-check that the ratio means what it looks like.

**The assumption, stated:** every stress in scope is taken as
centrifugally dominated, so it scales as N². Where a part also carries
gas bending or thermal stress this over-states the scaling, and unit E8
showed gas bending is roughly half the resultant at an LPT blade root —
so this is a *bound*, not a prediction, and it is called one.

### What is in scope, and what is not

**In scope: the six LP-spool parts.** The fan and the LPT run on the low
spool, whose growth speed is published.

**Out of scope: the eleven HP-spool parts** — ten HPC roots and the HPT
dovetail. **No growth HP speed is published** in anything transcribed.
The HPT dovetail sitting at exactly 1.000 is the single most interesting
row in F1's table and this unit cannot touch it, which is worth saying
plainly rather than scaling it by the LP ratio and hoping.

| Check | Band | Basis |
|---|---|---|
| The speed ratio is read, not assumed | fan tip speed, FPS vs growth, same column | both printed in `requirements` |
| The two published speed statements agree | **±0.5 %** | tip-speed ratio 1.1111 against `booster_speed_increase_pct: 11` |
| Every LP part is re-margined at N² | six parts, all three ratings | |
| The claim `hub_radii_oversized_for_growth` | the **fan** parts keep margin > 1 at growth | that is what the claim is about |
| The parts the claim does *not* cover | reported separately, not folded in | the LPT retainers are not hub radii |
| Life is not confused with stress | an LCF allowable is a limit at a **stated cycle count**; margin > 1 on stress does not mean the life is met | CR-165148 Fig 48 is 72,000 cycles |

**Closes when** all six LP parts are re-margined at all three ratings from
a published speed ratio, the fan and non-fan results are reported
separately, and the eleven HP parts are declared out of scope with the
reason.

---

## Result — K2

| | |
|---|---|
| LP speed ratio, rating 1 | **1.1111** → stress **×1.2344** |
| Cross-check | tip speeds give +11.11 %, the note prints +11 % — **0.11 points apart** |
| In scope | **6** LP-spool parts |
| Out of scope | **11** HP-spool parts, no growth HP speed published |
| Fan parts (claim covers) | **1.037, 1.191, 1.397 — all survive** |
| LPT retainers (claim does not) | **0.828, 0.819, 0.810 — all fail** |
| At rating 3 (×1.3283) | the fan dovetail corner goes under too, at 0.964 |

**Closure: met.** The claim holds exactly where it applies.

### Findings

198. **`hub_radii_oversized_for_growth` is true, and true only of what it
     says.** Scaling unit F1's seventeen margins by the published LP-spool
     speed ratio squared splits them cleanly along the claim's own
     boundary. The three fan parts the claim covers keep margin at growth
     speed — **1.037, 1.191, 1.397** — the tightest of them by less than
     four percent. The three LPT blade retainers, which are not hub radii
     and which nothing published says were sized for growth, go to
     **0.828, 0.819 and 0.810**. GE's sentence is exactly as broad as it
     is, and the parts outside it were sized for the engine that was
     built rather than the one it was designed to become.

199. **The fan's growth margin is four percent, not a comfort.** The fan
     blade dovetail corner comes out at **1.037** at the first rating —
     it survives, and the claim stands — but at the third rating, where
     the published speed ratio is **1.1525** rather than 1.1111, it goes
     to **0.964** and joins the retainers. The headroom GE bought is real
     and it is thin, and which rating you ask about decides the answer.
     A single-rating check would have reported this claim as comfortably
     true.

200. **The most interesting row in the table cannot be tested.** F1 found
     the HPT stage-1 disk dovetail at margin **1.000**, which the HPT
     report itself calls *"on the limit exactly"* — and the same report
     says the rotor structure was designed for growth with *the growth
     case limiting throughout*. That is the sharpest available test of
     the growth claim and this unit cannot run it: the HPT is on the HIGH
     spool and **no growth HP-spool speed is published in anything
     transcribed**. Eleven of the seventeen rows are out of scope for that
     one reason. Scaling them by the LP ratio would have produced six
     confident numbers and one of them would have been about the row that
     matters most.

201. **This is a bound, and two things make it pessimistic.** N² assumes
     centrifugal dominance, and unit E8 measured gas bending at about half
     the resultant at an LPT blade root — so for any part carrying bending
     the growth stress is over-stated here. Against that, the LPT
     retainer allowable is 0.2 % yield **at 649 °C**, and the growth
     engine runs hotter, so its allowable would fall and the retainer
     result is optimistic in the other direction. Neither correction is
     applied, because neither has a published number behind it. What the
     unit reports is the scaling, not the answer.

