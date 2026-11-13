# results.json schema (version 1)

One file, written by `young-people-work generate` to `data/results.json` and copied to `dashboard/public/data/results.json`. Every field is required; there are no defaults.

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | 1 |
| `status` | `"placeholder"` or `"final"` | `"placeholder"` while any measure is a placeholder |
| `banner` | string | Shown on every view while `status` is `"placeholder"` |
| `engine` | object | `policyengine`, `policyengine_uk`, `dataset`, `validated_pair` |
| `basis` | object | `cost`, `distribution`, `age_band`, `behaviour` text |
| `base_year`, `years` | int, int[] | Fiscal start years |
| `age_bands` | string[] | Age bands for the age view: `16-17`, `18-20`, `21-24`, `25 and over` |
| `measures[]` | object | Registry summary plus `status`, `receipt`, `budgetary_impact`, `decile`, `winners_losers`, `age_band`, `people_affected_k`, `coverage` |
| `context` | object | `neet[]` (ONS) and `young_claimants[]` (interim annex Table 28), each with its source text |
| `households[]` | object | `id`, `label`, `full_model_only`, `baseline_uc_monthly`, `reform_uc_monthly` by measure id (all values `null` when `full_model_only`) |
| `net_income_curves[]` | object | `preset`, `label`, `hourly_wage`, `rows[]` of `hours`, `baseline` and one value per computable measure |
| `data_limits[]`, `model_limits[]` | object | `key`, `reason`, `issue` |

Rules (checked by `publication.validate_public`, `scripts/check_public_data.py` and `dashboard/scripts/validate-results.mjs`):

- A measure that is not computable has `null` figures, never zeros, and a `route_reason`.
- A computable measure whose `budgetary_impact` rounds to £0m in every year needs a `zero_reason` saying why zero is right. Without one, the public-data guard and the page build refuse the file; `generate --mode model` still writes it, with a warning, so the run is kept. A measure that acts only through inputs the data lack is not computable: route it so, with the reason.
- No record identifiers, weights or record counts.
- Cells below 10 survey households are blanked (`suppressed: true`) before writing.
