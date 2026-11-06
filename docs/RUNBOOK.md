# Runbook for the day the report is published

The final report has no publication date; the latest government statement (5 November 2026) says "in the coming weeks". Recheck GOV.UK before each session. The government response is due by the end of 2026, with a White Paper early in 2027, so official costings of the recommendations may not come on the day. The ONS NEET bulletin is due on 26 November 2026: refresh `data_inputs/official/ons_neet_16_24.csv` that day.

The one-page version is `docs/event-day-checklist.md`.

## Commands

| Step | Command | Heavy |
|---|---|---|
| Install | `uv sync --locked --extra model --extra dev`, then `cd dashboard && bun install --frozen-lockfile` | no |
| Data login | the saved read-only Hugging Face login (never print it). policyengine.py reads only `HUGGING_FACE_TOKEN`; `model-run` and `certified_data` fall back to the saved login. `uv run python -m young_people_work.certified_data` downloads the certified file once and checks its SHA-256 | no |
| One measure | `uv run young-people-work model-run --measure <id>` | yes: takes `/tmp/pe-heavy.lock`, waits for 14 GB free+inactive |
| Package | `uv run young-people-work model-run --package` | yes |
| All of it | `make model` (each measure in its own process, then the package, then assembly) | yes |
| Assemble | `uv run young-people-work generate --mode model [--status mock]` | no (single households only) |
| One household | `uv run young-people-work household <preset> --reform <id>` (year defaults to 2027) | no |
| Household file | `uv run young-people-work households <file.csv> --out scored.csv` | no |
| Reconcile | `uv run young-people-work reconcile official.csv --out reconciliation.csv` | no |
| Guard | `uv run python scripts/check_public_data.py` | no |
| Local build | `make build` (or `make build-mock` for a drill) | yes |

Model mode scores a commit: `model-run` and `generate --mode model` refuse a dirty tree. Run files go to `data/runs/` and are git-ignored; they are aggregates, but nothing leaves the repository before the reconciler's sign-off.

Household files take the columns in `household.HOUSEHOLD_COLUMNS` (`id`, `year`, `age`, `weekly_hours`, `hourly_wage`, `lcwra`, `new_claimant`, `pip_dl_category`, `monthly_rent`, `region`, `in_approved_training`, `parent_age`, `parent_employment_income`); only `id` and `age` are required. Map a specimen sheet onto them before scoring. Each output row has monthly UC rounded to the penny once and the annual net income change from the rounded monthly amounts, with the commit SHA.

Do not read `is_uc_claimant` as a count of claimants: it flags benefit units that could claim. Use reported or modelled UC above zero.

## Gates

1. **G0 (as soon as the date is known).** Freeze the engine and data pair and post the record: start SHA; policyengine, policyengine-uk and policyengine-core from `importlib.metadata`; the dataset build id and SHA-256 (`runtime_identity.PINNED`: a6299504, `b96a8cd6...`); certified or "unvalidated under this engine". Decide the pin for the employer NICs measures and the 2027 minimum wage rates (#1). One heavy job at a time.
2. **G1.** Read the report. Write the coverage ledger: one line per recommendation with route, cause class and coverage. Replace the placeholder measures in `reforms.py` with the report's own, keeping `placeholder=True` until reconciled. Mark statement items already in the baseline or already announced as such, uncoded.
3. **G2.** `make model`. Hand-check one household per measure with `household`.
4. **G3.** Fill an official-costings CSV from the report and `data_inputs/official/`, run `reconcile`, and write a reason for each gap over 10%. Spending-line figures go in each measure's `official_cost` (value, year, source URL, paragraph); they are never added to the modelled total.
5. **G4.** Local build, then the checks in `docs/event-day-checklist.md`. On the real day, the Vercel preview behind the team login once the project exists.
6. **G5.** Re-run after any correction or new official figure (see Corrections).

## Corrections

A correction is a full rerun, never a hand edit of `results.json`:

1. Commit the change to the measure (or the official figure).
2. `make model`, which writes new receipts: each binds the definition, the commit, the installed versions, the dataset SHA-256 and the limits digest, so a figure from before the correction cannot pass for one after.
3. Re-run every hand-computed household and the reconciliation.
4. Update the ledger causes and say on the PR what changed and which rows were re-run.

## Rollback

- **Dashboard.** Vercel Instant Rollback to the previous production deployment, then `git revert -m 1 <merge>` on main in a reviewed PR so the next deploy does not bring it back. `vercel promote <deployment>` restores a known-good deployment.
- **Engine pin.** Revert the `uv.lock` and `pyproject.toml` bump in a reviewed PR, regenerate with `make model`, and check `runtime_identity.PINNED` and the README match the lock (the tests fail otherwise).

## Publication flip (one reviewed PR, not before sign-off)

The page is noindex and bannered until the figures are reconciled and signed off. The flip changes, together:

- `dashboard/app/layout.jsx`: `robots` to indexable, and the description without "Pre-release template";
- `dashboard/next.config.mjs`: remove the `X-Robots-Tag` header;
- `dashboard/src/noindex.test.js` and the two noindex greps in `.github/workflows/ci.yml`: invert them, so CI checks the page is indexable;
- results status `provisional` to `final` with the banner empty; the placeholder-banner grep in CI is replaced by a check that no banner is present;
- `sign_off.REQUIRED` and the review rows (issue for the sign-off decision).

## Adopting a release (when policyengine.py #731 or a later bump lands)

1. Bump `policyengine[uk]` in `pyproject.toml`, run `uv lock`, and `uv sync --locked --extra model --extra dev`.
2. Update `runtime_identity.PINNED` (versions, dataset build id and its SHA-256 from `uk_latest.release_bundle`) and the README pins; `tests/test_runtime_identity.py` checks them against the lock.
3. Re-run `pytest`; `tests/test_model_engine.py` re-reads `CURRENT_VALUES`, `PROTECTED_HEALTH_ELEMENT`, `NATIONAL_LIVING_WAGE` and the rebalanced years from the new engine and fails where they moved. Update them.
4. Re-check each entry of `data_limits.LIMITS_BY_BUILD` against the new build (for example `is_apprentice` from 0639b9c7) and the model limits (the employer zero rate exists from policyengine-uk 2.165.1; the 2027 minimum wage rates from 2.168.0).
5. `make model`, then hand-check the household presets against the previous run and explain each change.
6. The certified-data CI job (`python -m young_people_work.certified_data`) checks the bundle's dataset hash once the repository has the read secret `PE_UK_PRIVATE_HF_READ_TOKEN`; until then it reports that it was skipped.

Nothing deploys from this repository until the team chooses a target (`.github/workflows/deploy.yml`).
