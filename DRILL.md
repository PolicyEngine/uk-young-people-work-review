# Drill 5: Thursday 12 November 2026, 10:00–12:30

A rehearsal for the day the final report of the independent review of young people and work is published. It is the morning drill; the PIP review drill runs in the afternoon of the same day. Both use the compressed clock.

The packet is **mock**: an invented summary of recommendations, an invented analytical annex with costings, a correction notice and an answer key, written by the drill owner. It is held outside this repository. This file holds only the plan and the SHA-256 of each packet file. The integrator does not see the packet before each release.

This is the only drill plan: `docs/DRILL.md` in the template PR (#8) is a pointer here. Drill log: #10. Tracker: #9.

## Clock (London time)

| Time | T | Release | Gate |
|---|---|---|---|
| by 09:00 | | none | **G0** freeze record for both of the day's drills (template below) |
| 10:00 | T+0 | statement (summary of recommendations); hash checked by the reconciler | **G1** by 10:10: coverage ledger, every line routed |
| 10:30 | T+30 | none | **G2**: provisional numbers against the statement, plus one hand-checked household per coded measure |
| 10:40 | T+40 | documents (annex tables, specimen households, blank scoring and ledger sheets) | **G3** to 11:10: re-base and reconcile; every gap over 10% has a written reason |
| 11:15 | T+75 | inject (a correction notice) | **G5**: rerun, new scoring SHA, re-run every hand-computed row, update ledger causes |
| 11:40 | T+100 | none | **G4**: full page on a local production build with the MOCK banner and noindex (meta and header), every view screenshotted |
| 11:50 | T+110 | none | stop; log the stop commit |
| 12:00 | T+120 | answer key | scoring, to 12:30 |

A gate that runs late is logged with its actual time, and the next gate still starts on the clock. G2's machine time is budgeted from the timed dry run in the preflight (issue #10).

## G0 freeze record

Post as a comment on the drill issue by 09:00:

```
start SHA:            <commit the run branch is cut from>
policyengine:         6.11.1 (or the version G0 moves to, with the reason; 6.14.0 pins the same policyengine-uk and dataset)
policyengine-uk:      2.151.0 (or as above)
policyengine-core:    3.33.3
dataset:              microcosm-uk-2024-25-national-20261025T091414Z-a6299504  sha256 b96a8cd625b645a409c063b1de5158532708a2f0d3c3897a794a8fb0bbd5064e (or the build G0 moves to)
pair:                 certified (the policyengine.py bundle's own build) | "unvalidated under this engine"
run branch:           drill5-run (local unless G0 decides otherwise)
roles:                drill owner / integrator / reconciler / scorer
lock and memory:      /tmp/pe-heavy.lock taken by this drill; vm_stat free+inactive >= 14 GB inside it
```

Every national figure carries "unvalidated under this engine" unless G0 names a certified pair. Model mode records the installed versions and the SHA-256 of the file it loaded in every receipt and in `data/manifest.json`; the G0 record is checked against them at G2.

## Roles (one person each; only the integrator pushes)

| Role | Owns | Does not |
|---|---|---|
| Drill owner | the packet, release times, the answer key | take part in the run |
| Integrator | the run branch, the clock table, every commit, generation, re-basing | score households or open the packet early |
| Reconciler | the T+0 and T+40 hash checks, the ledger, the reconciliation CSV, defects logged within 5 minutes | push code |
| Scorer (the reconciler after T+40) | specimen households, one commit SHA per scoring run, the T+75 and T+120 hash checks | edit reform code |

## Packet release

- The drill owner copies each file into `~/drill5-released/` at its time. Packet files are never committed to this repository or posted on GitHub.
- Each released file is checked against the hash table below before it is used (owners in the roles table), and the result logged.
- Mock measures carry ids prefixed `mock_` and the word MOCK in each name. Results are generated with `--status mock`, and the page is built with `NEXT_PUBLIC_MOCK=1`, so every view shows the MOCK banner whatever the measure flags say; the publication check refuses a `mock_` id in any other file. The run branch stays local unless G0 decides otherwise; the template PR is not merged for the drill.
- In-drill defects, the filled ledger, the reconciliation CSV and the scored households live in `~/drill5-work/` on the drill machine: never committed to this public repository and never posted. Issue #10 holds only times, SHAs, hashes and pass/fail until the answer key is released.

## Commands

Run from the template code (`template-dashboard`, PR #8). Heavy steps take `/tmp/pe-heavy.lock` themselves and wait for 14 GB free+inactive.

| Step | Command |
|---|---|
| Install (preflight) | `uv sync --locked --extra model --extra dev`; `cd dashboard && bun install --frozen-lockfile` |
| Data login check (preflight) | the saved read-only Hugging Face login is present; never print it |
| One measure | `uv run young-people-work model-run --measure <id>` |
| Package | `uv run young-people-work model-run --package` |
| All measures, then assembly | `make model STATUS=mock` |
| Hand check | `uv run young-people-work household <preset> --reform <id> [--year 2027]` |
| Specimen households | `uv run young-people-work households ~/drill5-work/households.csv --out ~/drill5-work/scored.csv` (columns in `docs/RUNBOOK.md`; map the specimen sheet onto them) |
| Reconcile | `uv run young-people-work reconcile ~/drill5-work/official.csv --out ~/drill5-work/reconciliation.csv` (exits 1 while a gap over 10% has no reason) |
| Guard | `uv run python scripts/check_public_data.py` |
| G4 build | `make build-mock`, then the checks under "MOCK banner and noindex" |

## Ledger: routes by where the work is

Every line in the statement gets one route, one cause class and a coverage (UK, GB, England, nation).

| Where the work is | Route | Meaning |
|---|---|---|
| This repository | `dashboard-param` | a parameter change in the registry |
| This repository | `dashboard-structural` | a modifier in `measures/`, one module, literal defaults, checked by hand on the day |
| policyengine-uk | `needs-pe-uk-first` | needs a new parameter, formula or the age dimension upstream; filed the same day as a draft |
| Data | `not-computable` | acts only through an input the data lack; published with the reason, never as £0 |
| None | `ledger` | spending line or no change; the official figure is recorded, not modelled |

Cause classes: `parameter`, `formula`, `data_calibration`, `basis`, `timing_fiscal_calendar`, `coverage`, `interaction`, `baseline_mismatch`.

Before G1, check every line against the known limits in issues #1 to #7, and mark any statement item already in the baseline or already announced as such rather than coding it.

## Basis (declare once, at G2)

- Sign: positive is a cost to the Exchequer (`docs/METHOD.md` in #8).
- Gross or net of tax offsets; nominal fiscal year or constant prices; static or behavioural; UK, GB or England.
- Household rows: monthly Universal Credit rounded to the penny once, at the end; the annual change in net income from the rounded monthly amounts (what `households` writes).

## What to time and log

Keep a clock table on the drill issue, one row per step (no mock content in it):

| Column | What |
|---|---|
| step | gate or task (for example "G3: re-base") |
| start, end | London time to the minute |
| machine minutes | generation and test runs only |
| people minutes | reading, coding, review |
| SHA | the commit the step produced or scored |
| route | for coding steps, the ledger route |
| note | pass/fail and decisions only; the defect text stays in `~/drill5-work/` |

Also log: the hash check of each released file, every inject action (what changed, which rows were re-run), and the stop commit.

## MOCK banner and noindex

- Every page built from the run branch shows the MOCK banner on every view, and carries `noindex, nofollow` in the page head.
- Check both on a local production build, as the AB2026 dashboard did: drills 2 and 4 could not observe the banner behind the team login, so a protected preview is kept for the real day only, once a Vercel project exists. Inside `/tmp/pe-heavy.lock`:
  - `make build-mock`
  - `grep -q 'name="robots" content="noindex' dashboard/.next/server/app/index.html` and `grep -q 'mock-banner' dashboard/.next/server/app/index.html`
  - `cd dashboard && bun run start -p 3917`, then `curl -sI localhost:3917 | grep -i x-robots-tag` (expects `noindex, nofollow`)
  - screenshot every tab at 1280 and 390 wide, keep them in `~/drill5-work/`, and kill the server.
- No mock figure, chart or household appears on any public page, post or file. The public data guard (`scripts/check_public_data.py`) must pass on the stop commit.

## Rubric (100)

| Item | Points |
|---|---|
| Households to ±1p, at the corrected values | 20 |
| National figures: declared basis and gap class with reason | 30 |
| Ledger: route, cause class and coverage | 25 |
| Publication path: MOCK banner on every view, noindex meta and header on the local build, guard passes | 10 |
| Process: gates on time, one SHA per scoring run, inject logged | 15 |

Trap lines (items already in the baseline or already announced) score only when marked as such and left uncoded.

## Hygiene

- One integrator. Reviews go in `~/drill5-work/` and are read at once.
- Code in waves: parameters, then modifiers, then new variables.
- Draft PR only, labelled `not for merge`, never stacked on another unmerged PR. Nothing is merged or deployed.
- Upstream needs are filed as drafts the same day; the drill does not wait for them.

## Packet hashes (SHA-256)

| File | Released at | SHA-256 |
|---|---|---|
| `statement.md` | T+0 | `4198424fe90a96e4afdcb34d73d414e9257e1334efa775c4ce5f0e14d0d8d1ab` |
| `documents/annex_tables.md` | T+40 | `c6e356f2d3dbd98cd5407de9ad55e2b308533dedc89e6bb01cde3ac0e70ae7c1` |
| `documents/specimen_households.csv` | T+40 | `32a49fbb8fc3f408b44e3990a65594ea5a4fbac2fb7da86201d0e10d43de1040` |
| `documents/scoring_sheet_households.csv` | T+40 | `64532709d2852f54912a7ccefc2ed589672ddd816cabfb5505f8c08c5442e344` |
| `documents/scoring_sheet_national.csv` | T+40 | `c34b079cd1f93ff39d564f3b9c884d7e25f693ae9e89922387c8c546dd237ca7` |
| `documents/ledger_sheet.csv` | T+40 | `fb35f78ded3f7c1ebdb319a046cf43dd91f4c89b5cc295ce9ab8abe20496b6e8` |
| `inject.md` | T+75 | `17d3201f353fbccf2274a799c1fba259d6359a6f86ce30163b53bf55a51fda2a` |
| `answer_key_households.csv` | T+120 | `21a62062dba65a94fc9b8c614fdd8318e8ec17fa146862dbcc3b16e5b7108b43` |
| `answer_key_national.csv` | T+120 | `e608f8b0c6a87bea0619c11dd7d705141ac5730bd29f791ea836b17853382798` |
| `answer_key_ledger.csv` | T+120 | `11cd933c59815e5c713c0155586c66cef45704e559c54fd5207cbdc889b52700` |
| `generator.py` | T+120, on request | `3bf0c56591fb9a37439e52e932e0d94b7945969c6d9ae78ca198dc5ee2ca7551` |
| `README_OWNER.md` | owner only | `0361ddfc939bdb743a534b4e998d65856892c01f54212bb50d9a8b2101c35139` |

The household key may be re-checked against the pinned engine before 09:00 on the day. If any file changes, the drill owner updates this table before T+0 and says so on the drill issue.

## Retro

File the retro on the drill issue by the end of the day using the template there: score by rubric line, gate times against the clock, machine time against people time, defects found and when they were read, and the follow-ups for the real day.
