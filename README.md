# Young people and work review dashboard

PolicyEngine UK dashboard for the independent review of young people and work, which looks at the rise in the number of young people who are not in education, employment or training (NEET). The review's final report is expected late in 2026; no publication date has been announced. This repository holds the analysis pipeline and the dashboard we will use to estimate what its proposals would cost and who would benefit.

**Status: pre-release template.** Nothing here is a PolicyEngine estimate yet. The template runs on placeholder figures until the final report is published and its recommendations are coded and checked.

## What the dashboard will show

- **Cost.** Static cost of each modelled recommendation and of the package, £m a year for 2027-28 to 2030-31, UK, with the parts we cannot model listed as spending lines.
- **Who benefits.** Average change in household net income by income decile, the share of households that gain or lose, and changes by age (16-17, 18-20, 21-24, 25 and over), region and nation, and Universal Credit work-related group.
- **People affected.** Number of people in households whose net income changes.
- **Poverty.** Relative poverty before and after housing costs, for everyone, children and 16-24-year-olds.
- **Spending lines.** The report's own or official figures for programmes we do not model, kept apart from the modelled total.
- **Households.** Example young people and households under current law and under each scenario, including net income against hours worked.
- **Method and limits.** What we can and cannot model, measure by measure, with the reason.

The review is expected to set out principles and recommendations rather than costed parameters. The dashboard will therefore show illustrative parameter scenarios mapped to each recommendation, labelled as such.

## Method in brief

- PolicyEngine UK static microsimulation on the Microcosm UK dataset. No behavioural response is modelled: no change in hours, hiring or claims.
- Each recommendation is routed before anything is published: modelled by a parameter change, modelled by a structural change, recorded as a spending line, or not computable with the current data (with the reason). A measure we cannot compute is never shown as £0.
- The data do not record NEET status, work history, Work Capability Assessment outcomes or care-leaver status. Measures that depend on them use a stated proxy or are not computable.

## Data and model

| Item | Version |
|---|---|
| policyengine | 6.11.1 (`policyengine[uk]`) |
| policyengine-uk | 2.151.0 |
| policyengine-core | 3.33.3 |
| Dataset | Microcosm UK 2024-25 national build `20261025T091414Z-a6299504` (SHA-256 `b96a8cd6...064e`, certified with this bundle) |

policyengine 6.14.0 pins the same policyengine-uk and dataset, so 6.11.1 (the version the AB2026 dashboard uses) gives the same results. The pinned engine does not yet model the employer National Insurance zero rate for under-21s (policyengine-uk 2.165.1 does) or the April 2027 minimum wage rates (2.168.0), so the pin is reviewed before the event (#1). Versions will be frozen and recorded before the event. Microdata are licensed and are not stored in this repository; only aggregate outputs that pass a disclosure check are published.

## Licence

AGPL-3.0, as for other PolicyEngine repositories. See [LICENSE](LICENSE).

## How to run

```sh
make install                              # analysis package, tests and dashboard, no engine
make test lint                            # pytest, vitest, ruff, eslint
uv run young-people-work generate         # data/results.json and the dashboard copy (placeholder mode)
make guard                                # public data guard

make install-model                        # adds policyengine[uk]==6.11.1
uv run young-people-work household single_20_new_health_element --reform health_element_under_22
make model                                # full model, one measure per process, under /tmp/pe-heavy.lock
make build                                # local production build (heavy)

cd dashboard && bun run dev               # local page on http://localhost:3000
```

Commands for the day, corrections, rollback and adopting a release: `docs/RUNBOOK.md` and `docs/event-day-checklist.md`.

## Layout

| Path | What it holds |
|---|---|
| `src/young_people_work/reforms.py` | Measure registry: every candidate recommendation with its route and where it applies; all placeholders |
| `src/young_people_work/measures/` | Hand-written modifiers, one measure family per module (the health element age test) |
| `src/young_people_work/measure_templates.py` | Parameter builders (`rate_change`, `threshold_change`, `uc_health_element_change`) |
| `src/young_people_work/data_limits.py`, `model_limits.py` | What the data and the model cannot cost, with the reason |
| `src/young_people_work/publication.py`, `sign_off.py` | Manifest, receipts, disclosure floor, validation; sign-off switch (on) |
| `src/young_people_work/pipeline.py`, `model.py`, `cli.py`, `household.py` | Generation (placeholder and model mode), the household calculator |
| `src/young_people_work/runtime_identity.py`, `reconcile.py` | Execution identity for receipts and the manifest; G3 reconciliation |
| `data_inputs/` | Official figures and expected effects |
| `docs/` | Method, schema, data contract, colours, runbook, drill, candidate reforms, risk register |
| `scripts/` | Public data guard; weighted check of the young people base (team only) |
| `dashboard/` | Next 16, React 19, `@policyengine/ui-kit`, Recharts, bun |
