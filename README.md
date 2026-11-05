# Young people and work review dashboard

PolicyEngine UK dashboard for the independent review of young people and work, which looks at the rise in the number of young people who are not in education, employment or training (NEET). The review's final recommendations are expected in November 2026; no publication date has been announced. This repository holds the analysis pipeline and the dashboard we will use to estimate what its proposals would cost and who would benefit.

**Status: pre-release template.** Nothing here is a PolicyEngine estimate yet. The template runs on placeholder figures until the final report is published and its recommendations are coded and checked.

## What the dashboard will show

- **Cost.** Static cost of each modelled recommendation and of the package, £m a year for 2027-28 to 2030-31, UK, with the parts we cannot model listed as spending lines.
- **Who benefits.** Average change in household net income by income decile, the share of households that gain or lose, and changes by the young person's age band (16-17, 18-20, 21-24), family type, region and Universal Credit status.
- **People affected.** Number of young people whose Universal Credit, health element or employer National Insurance changes.
- **Poverty.** Change in relative and absolute poverty, before and after housing costs.
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
| Dataset | Microcosm UK 2024-25 national build `20261025T091414Z-a6299504` |

The pinned engine does not yet model the employer National Insurance zero rate for under-21s, so the pin will be reviewed before the event. Versions will be frozen and recorded before the event. Microdata are licensed and are not stored in this repository; only aggregate outputs that pass a disclosure check are published.

## Licence

AGPL-3.0, as for other PolicyEngine repositories. See [LICENSE](LICENSE).

## How to run (template)

```sh
uv sync --extra dev                       # analysis package and tests, no engine
uv run pytest -q                          # registry, templates, limits, publication, households
uv run young-people-work generate         # writes data/results.json and the dashboard copy (placeholder mode)
uv run python scripts/check_public_data.py

cd dashboard && bun install && bun run dev   # local page on http://localhost:3000
```

`uv sync --extra model` adds `policyengine[uk]==6.11.1` for real runs and the household calculator (`uv run young-people-work household <preset>`).

## Layout

| Path | What it holds |
|---|---|
| `src/young_people_work/reforms.py` | Measure registry: every candidate recommendation with its route and where it applies; all placeholders |
| `src/young_people_work/measures/` | Hand-written modifiers, one per module (none yet) |
| `src/young_people_work/measure_templates.py` | Parameter builders (`rate_change`, `threshold_change`) |
| `src/young_people_work/data_limits.py`, `model_limits.py` | What the data and the model cannot cost, with the reason |
| `src/young_people_work/publication.py`, `sign_off.py` | Manifest, receipts, disclosure floor, validation; sign-off switch (on) |
| `src/young_people_work/pipeline.py`, `cli.py`, `household.py` | Generation and the household calculator |
| `data_inputs/` | Official figures, expected effects, drill packet hashes |
| `docs/` | Method, schema, data contract, colours, runbook, drill, candidate reforms, risk register |
| `scripts/` | Public data guard; weighted check of the young people base (team only) |
| `dashboard/` | Next 16, React 19, `@policyengine/ui-kit`, Recharts, bun |
