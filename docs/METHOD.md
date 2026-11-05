# Method

## Basis (declared once)

- Static microsimulation: no behavioural response. No change in hours, hiring, education or claims, and no move from NEET into work.
- Cash, fiscal year (year Y is Y-(Y+1)), £ million, nominal.
- UK unless a measure says otherwise. UC and National Insurance are UK-wide; PIP applies in England and Wales; employment support, the participation system and apprenticeship funding are devolved, so those measures apply in England. Each measure carries `coverage`.
- Positive is a cost to the Exchequer.
- Distribution: change in household net income by equivalised household income decile, and the change for young people's benefit units by age band (16-17, 18-20, 21-24).

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

## What the data hold

Age, employment status, education and approved training, earnings, hours, reported UC, disability-benefit receipt and PIP award categories. Not held: work history (#4), NEET status (proxy only, #7), Work Capability Assessment outcome (LCWRA follows disability-benefit receipt, #3), care-leaver status (#5), an apprentice flag in the pinned build (#6), employer records and hiring flows.

## NEET proxy

Aged 16-24, not employed or self-employed, `current_education` is `NOT_IN_EDUCATION`, not a student and not in approved training. It comes from the FRS, not the LFS, and is not calibrated to the ONS count (#7).

## Not modelled

The guarantee, local funding, apprenticeship incentives, mental health services and the tracking duty (spending lines); employment effects of minimum wages and employer incentives; flows on and off benefits over time.
