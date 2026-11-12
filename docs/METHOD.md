# Method

## Basis (declared once)

- Static microsimulation: no behavioural response. No change in hours, hiring, education or claims, and no move from NEET into work.
- Cash, fiscal year (year Y is Y-(Y+1)), £ million, nominal.
- UK unless a measure says otherwise. UC and National Insurance are UK-wide; PIP applies in England and Wales; employment support, the participation system and apprenticeship funding are devolved, so those measures apply in England. Each measure carries `coverage`.
- Positive is a cost to the Exchequer.
- Distribution: change in household net income by equivalised household income decile. By age: each person is given their household's change in net income and grouped by their own age (16-17, 18-20, 21-24, 25 and over), person-weighted, as in the AB2026 dashboard's `AgeImpactCalculator`. A 17-year-old living with a parent is in the 16-17 band.
- Package: the headline measures (`in_headline`) are also run once together (`model-run --package`), so interactions between UC measures are counted once. The page shows the package's figures when the selection is the package, and labels any other selection as a sum of single-measure figures.
- Households: monthly UC rounded to the penny once, at the end; the annual change in net income from the rounded monthly amounts.

The review's own estimates, such as the annual cost of young people being NEET, include long-run effects on output and earnings. Our static figures cover the first-round cost to the Exchequer and household incomes only; the reconciliation records that difference as cause class `basis`.

## Routes

Each recommendation gets one route before anything is coded:

| Route | Meaning |
|---|---|
| `dashboard-param` | Modelled by a parameter change |
| `dashboard-structural` | Modelled by a modifier in `src/young_people_work/measures/` |
| `ledger` | Not modelled; any official figure recorded as a spending line |
| `not-computable` | A data limit; shown with the reason, never as £0 |
| `needs-pe-uk-first` | Needs a model change upstream before it can be costed |

## The UC health element

From 2026-27 the engine's UC rebalancing sets each claimant's health element itself: the protected rate (£442.10 a month in 2027-28) for claims made before April 2026 and the new-claimant rate (£217.26) for later claims. So:

- a change to `elements.disabled.amount` in 2026-2032 scores nothing; `measure_templates` refuses it and points to `uc_health_element_change`;
- an age test (`measures/health_element_min_age.py`) wraps the element's formula before the data load (`applied_before_data_load=True`), which the rebalancing then respects; applied after, it does nothing;
- which claimants are new is a seeded draw at `rebalancing.new_claimant_share` (13% in 2027-28) with no age dimension, so an age-limited measure for new claimants is published as a range: new claimants only, up to every claimant under the age (`upper_bound_modifier`, `budgetary_impact_upper`). An age-specific share from Stat-Xplore would narrow it (issue #2);
- the protected rate follows every standard allowance under the UC Act 2025 s. 4 floor, so a lower under-25 standard allowance would raise it for claimants of every age. `youth_standard_allowance` holds it at the current-law path (`reforms.PROTECTED_HEALTH_ELEMENT`, checked against the engine).

## What the data hold

Age, employment status, education and approved training, earnings, hours, reported UC, disability-benefit receipt and PIP award categories. Not held: work history (#4), NEET status (proxy only, #7), Work Capability Assessment outcome (LCWRA follows disability-benefit receipt, #3), care-leaver status (#5), employer records and hiring flows. The apprentice flag in the pinned build is imputed from a small number of survey records (#6).

## NEET proxy

Aged 16-24, not employed or self-employed, `current_education` is `NOT_IN_EDUCATION`, not a student and not in approved training. It comes from the FRS, not the LFS, and is not calibrated to the ONS count (#7).

## Not modelled

The guarantee, local funding, apprenticeship incentives, mental health services and the tracking duty (spending lines); employment effects of minimum wages and employer incentives; flows on and off benefits over time.
