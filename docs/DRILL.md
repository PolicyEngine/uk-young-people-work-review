# Drill: Thursday 12 November 2026, 10:00-12:30

A mock release of the final report of the independent review of young people and work, run on the compressed clock. This is the morning drill; the PIP review drill runs in the afternoon of the same day. The packet is mock: invented recommendations and costings, written by the drill owner and held outside this repository. Only their hashes are committed (`data_inputs/packet/HASHES.md`).

## Clock

| Time | T | Release | Gate |
|---|---|---|---|
| by 09:30 | | none | **G0** freeze record: start SHA, policyengine and policyengine-uk versions, dataset name and SHA-256, validated pair or "unvalidated" label (G0 for both of the day's drills is due by 09:00) |
| 10:00 | T+0 | statement (mock report summary and recommendations) | **G1** by 10:10: coverage ledger, every recommendation routed |
| 10:30 | T+30 | none | **G2**: provisional numbers against the statement, plus one hand-checked household per coded measure |
| 10:40 | T+40 | documents (mock analytical annex: caseload table, case-study incomes, specimen households, blank scoring sheet) | **G3** to 11:10: re-base and reconcile; each gap over 10% has a written reason |
| 11:15 | T+75 | inject (a correction notice) | **G5**: rerun, new scoring SHA, re-run hand-computed rows |
| 11:40 | T+100 | none | **G4**: full page on a protected preview with the banner and noindex, checked behind the login |
| 11:50 | T+110 | none | stop; log the stop commit |
| 12:00 | T+120 | answer key | scoring, to 12:30 |

## Roles (one person each; only the integrator pushes)

| Role | Owns | Does not |
|---|---|---|
| Integrator | the branch, the clock table, every commit, generation, re-basing | score households |
| Reconciler | the ledger, the reconciliation CSV, defects as PR comments within 5 minutes | push code |
| Scorer (the reconciler after T+40) | specimen households, one commit SHA per scoring run | edit reform code |

## Ledger

Every line gets a route (`dashboard-param`, `dashboard-structural`, `ledger`, `not-computable`, `needs-pe-uk-first`) and a cause class (`parameter`, `formula`, `data_calibration`, `basis`, `timing_fiscal_calendar`, `coverage`, `interaction`, `baseline_mismatch`).

Lines that must be in the ledger before G1, whatever the packet says:
- An age limit on the UC health element cannot be a parameter change: `needs-pe-uk-first`, or a modifier in this repository written and checked on the day (#2).
- Employer NICs measures cannot be scored on the pinned bundle (#1); `needs-pe-uk-first` unless G0 moved the pin.
- "Never worked" has no data; any route for that group uses the no-earnings proxy, with both bounds shown, or is `not-computable` (#4).
- Minimum wage changes do not reach pay: `not-computable` for the cost, household examples only.
- Employment support, the participation system and apprenticeship funding are devolved: England-only ledger lines.

## Rubric (100)

| Item | Points |
|---|---|
| Households to ±1p | 20 |
| National figures: basis and gap class | 30 |
| Ledger class, route and cause | 25 |
| Publication path (banner, noindex, guard passes) | 10 |
| Process: gates on time, one SHA per run, inject logged | 15 |

The packet includes trap rows: statement items already in the baseline or already announced, for example the lower health element for new claims from April 2026, the April 2027 minimum wage rates (in the baseline of policyengine-uk 2.175.x but not of the pinned 2.151.0, so a `baseline_mismatch` on the pin), the December 2025 Youth Guarantee expansion and the existing £2,000 apprenticeship incentives.

## Hygiene

- Draft PR from `main`, labelled `not for merge`, never stacked on another unmerged PR.
- Code in waves: parameters, then modifiers, then new variables.
- Time each step on the documents clock; record machine time and people time separately.
- Statutory rounding: UC amounts to the penny each month; minimum wage rates to the penny an hour.
