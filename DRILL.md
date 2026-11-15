# Drill: Sunday 15 November 2026, 21:30–00:00

A timed rehearsal for the day the final report of the independent review of young people and work is published (expected Tuesday 17 November 2026), on a mock statement. It uses the compressed 2.5-hour clock. All times are London time; times after midnight are Monday 16 November.

This file holds the plan only, and is the only copy of the clock and the packet hashes; the drill issue links here. It says nothing about the mock content. The statement, documents, inject and answer key are written and held outside this repository by the drill owner and are released at the times below.

Four drills run on this machine tonight, staggered so heavy runs never overlap. This drill is the first.

## Clock

| Time | T | Release | Gate |
|---|---|---|---|
| by 21:00 | – | none | **G0**: pair record and pair check posted on the drill PR |
| 21:30 | T+0 | statement | **G1** by 21:40: coverage ledger, every line routed; items already in the baseline flagged, with the time |
| 21:40–22:05 | – | none | **heavy slot 1** (G2 runs) |
| 22:00 | T+30 | none | **G2**: provisional numbers against the statement; one hand-checked household per coded measure |
| 22:10 | T+40 | documents: costings, example households, blank scoring sheet | **G3** by 22:40: re-base and reconcile; every gap over 10% has a written reason |
| 22:45 | T+75 | inject | **G5** by 23:05: act on the inject, re-run everything affected, new scoring SHA |
| 22:45–23:10 | – | none | **heavy slot 2** (G5 runs and the G4 build) |
| 23:10 | T+100 | none | **G4**: full page on a local production build, MOCK banner and noindex checked |
| 23:20 | T+110 | none | **stop**: log the stop commit |
| 23:25 | T+115 | none | **FREEZE.txt** posted on the drill PR |
| 23:30 | T+120 | answer key and scoring tool | scoring, to 23:50 |
| 00:00 | T+150 | none | retro filed on the drill issue |

A gate that runs late is logged with its actual time; the next gate still starts on the clock.

### Heavy slots tonight (one heavy job at a time)

Every heavy run (a national `model-run`, `make model`, a production build) takes the file lock `/tmp/pe-heavy.lock` (contents "<pid> <label>", noclobber, at least 22 GB free+inactive) and only inside its own drill's slot. A run that cannot finish inside the slot is not started; an overrun is logged, and the next slot owner logs the wait as lock wait.

| Slot | Owner | Status for this drill |
|---|---|---|
| 21:40–22:05 | this drill (G2) | ours |
| 22:15–22:35 | PIP review drill | busy |
| 22:45–23:10 | this drill (G5 and G4 build) | ours |
| 23:10–23:20 | energy price cap drill | busy |
| 23:20–23:45 | PIP review drill | busy |
| 23:50–00:10 | Scottish Budget drill | busy |
| 00:15–00:40 | energy price cap drill | busy |
| 00:55–01:20 | Scottish Budget drill | busy |

### Engine and data pair

The drill runs on: policyengine-uk 2.177.7, policyengine-core 3.34.10 (no policyengine.py), Microcosm build `uk-frs-calibration-attempt-20261112T133744Z-6f918b81` (SHA-256 `e268e3af7932784ad4471f008097a5acc6c3c5bc15c4c54fbb5a489b2a0ac9ae`), the build made on 2.177.7. No policyengine.py release covers this pair, so every figure carries the label "build uk-frs-calibration-attempt-20261112T133744Z-6f918b81, policyengine-uk 2.177.7, not in a policyengine.py release".

The rule is the repository's (`src/young_people_work/data_build.py`): a build runs only under the policyengine-uk version it was built on. A build under another engine version is a mixed pair; its figures are invalid and are not scored, whatever label they carry. Any change of build or engine during the drill is a new G0: a new record and a passing pair check, posted before any figure from the new pair is used. Figures from a pair not recorded at G0 are not scored.

## Gates

The run branch is local, cut from the head of `engine-2.177.7-microcosm-9e18f010` (on build 6f918b81 despite its name). Commands are in `docs/RUNBOOK.md`.

- **Before G0: merge the three retro PRs into the run branch**: #17 (`retro/household-rounding-tenure`: half-up penny rounding, the annual UC change, the tenure column), #18 (`retro/receipt-label-and-pair-check`: `young_people_work.pair_check` and the receipt label), #20 (`retro/zero-figure-check`: the publication check that refuses a coded measure shown at £0 in every year without a `zero_reason`). Run `uv run pytest` after each. If a merge conflicts, resolve it by hand and log the files; if it cannot be resolved before 21:00, the G0 pair check is done by hand (below) and the conflict is logged.
- **G0, pair record (by 21:00).** Post on the drill PR: start SHA and the engine-branch SHA it was cut from; policyengine-uk and policyengine-core from `importlib.metadata`; `runtime_identity.PINNED` (build id and SHA-256); `uv run python -m young_people_work.certified_data` output (the downloaded build's SHA-256); and the output of
  `uv run python -m young_people_work.pair_check <release folder>`
  where `<release folder>` holds the build's release JSON files (the `*.json` next to the `.h5` under `releases/microcosm-uk-2024-25-national/<build id>/` in the data repository). If the release files record no engine, add `--build-engine <version>` from the data owner's release note. The pair check must pass. **By hand** (if #18 did not merge): quote the engine version each release JSON records and the installed policyengine-uk, side by side, and state that they are equal.
- **G1, coverage ledger (21:30–21:40).** One line per statement item in `~/drill9-work/ledger.csv`, header `line,measure_id,route,cause,coverage,in_baseline,flagged_at,coded,zero_reason,notes`. Items already in the baseline are flagged here with the time (`flagged_at`), not coded. Mock measures get ids prefixed `mock_` and keep `placeholder=True` until reconciled.
- **G2, provisional numbers (by 22:00, heavy slot 1).** `uv run young-people-work model-run --measure <id>` per coded measure, then `--package`, then `uv run young-people-work generate --mode model --status mock`. A coded measure that the guard reports at £0 in every year is routed, not published as £0: route it not-computable with the reason, or give the reason zero is right in `zero_reason`. One hand-checked household per coded measure (`uv run young-people-work household <preset> --reform <id>`).
- **G3, re-base and reconcile (22:10–22:40).** Example households with `uv run young-people-work households <file.csv> --out ~/drill9-work/households-run<N>.csv` (columns in `docs/RUNBOOK.md`; set `tenure_type` and `new_claimant` from the household file). Fill the official CSV and run `uv run young-people-work reconcile ~/drill9-work/official.csv --out ~/drill9-work/national.csv` until it exits 0, then add `line` and `gap_class` columns. Update ledger causes after G3.
- **G5, inject (22:45–23:05, heavy slot 2).** Act on every part of the inject and log each action with its time. A correction is a full re-run (`docs/RUNBOOK.md`, "Corrections"); every hand-computed household is re-run into its own new file; record the new scoring SHA. Any instruction that would change the engine or the build goes through G0 again first.
- **G4, publication path (by 23:10, heavy slot 2).** `make build-mock`, then the checks under "MOCK and noindex".
- **Stop (23:20).** Log the stop commit. Nothing changes in a scored file after it.

## Freeze at stop

By 23:25 (before T+120), post `FREEZE.txt` on the drill PR: one line per scored file, `shasum -a 256` output for the household scoring file, the ledger and the national (reconciliation) file, as they stand at the stop commit, plus the stop commit SHA. Each scored file has a distinct file name. The scorer copies the frozen files, reads only that copy, and the scoring tool refuses any file whose SHA-256 differs from `FREEZE.txt`. Anything changed after the freeze is not scored; a defect found after the stop is logged, not fixed in the frozen files.

## Roles

| Role | Owns | Does not |
|---|---|---|
| Integrator | run branch, clock table, every commit, generation, re-basing, G0 | score households; open sealed files early |
| Reconciler | ledger, reconciliation CSV, defects posted as PR comments within 5 minutes, hash check of each release on arrival | push code |
| Scorer (the reconciler after the documents) | example households, one commit SHA per scoring run, the FREEZE.txt check, the hash check of the answer key at 23:30 | edit reform code |
| Drill owner (not the integrator) | the sealed packet, releases at the set times, the answer key and scoring tool | take part in coding |

Who holds each role is recorded on the drill issue. Only the integrator pushes; the run branch stays local unless G0 decides otherwise.

## Routes

| Route | Where the work lands | Meaning |
|---|---|---|
| `dashboard-param` | this repo | a parameter change in `reforms.py` |
| `dashboard-structural` | this repo | a hand-written modifier in `measures/`, one module, year-gated, checked by hand |
| `needs-pe-uk-first` | policyengine-uk | the engine has no route; noted with what upstream needs |
| `not-computable` | data (Microcosm) | acts only through an input the data lack; published with the reason, never as £0 |
| `ledger` | none | not modelled (spending, items already in the baseline); the official figure is recorded |

## Cause and gap classes

Cause class (ledger: what the measure needs before PolicyEngine can show it):

- `parameter`: an existing parameter carries it.
- `formula`: engine or modifier logic must change.
- `coverage`: the input the measure acts on is not in the data or the model (every not-computable line).
- `baseline_mismatch`: the baseline already holds the measure, or holds a different value from the official baseline (every item already in the baseline).
- `timing_fiscal_calendar`: start date, part year or fiscal year placement is the substance.
- `interaction`: the measure works through another benefit or measure.
- `data_calibration`: the data hold the input but its level is off.
- `basis`: a presentation choice only.

Gap class (national: why our figure differs from the official one by more than 10%):

- `basis`: static against behavioural, accrued against cash, geography, price base, gross against net.
- `data_calibration`: the data's count or level of the affected group differs from the official one for the same year.
- `baseline_mismatch`: the official baseline holds different policy or forecast assumptions.
- `timing_fiscal_calendar`, `coverage`, `interaction`: as above.

The cause class and the gap class are separate columns; where they are equal, write why. For a line with no figure, the gap column says `n/a` and the row records the official figure and the reason no figure is shown.

Declare the basis once, at G2, and repeat it next to every figure: static or behavioural, gross or net, fiscal year, coverage (UK, GB, England), and which baseline. Sign: positive is a cost to the Exchequer. Household rows: monthly Universal Credit rounded to the penny once, at the end, half up; the annual change from the rounded monthly amounts, as the documents define it.

## Rubric (100)

| Area | Points | How it is scored |
|---|---|---|
| Example households | 20 | each scored cell within ±1p of the key, on the values in force after the inject; 20 x matched / cells |
| National figures | 30 | per statement line, basis (half) and gap class (half); for not-computable and ledger lines the basis column carries the costing's basis, and the gap point is for recording the costing and the reason no figure is shown |
| Ledger | 25 | route and cause class per line, at the frozen stop state; items already in the baseline score only if flagged at G1 and left uncoded |
| Publication path | 10 | MOCK banner on every view; noindex meta and X-Robots-Tag on `next start`; not-computable lines shown with reasons, never as £0; disclosure floor; every coded measure on the page |
| Process | 15 | G0 pair record with a passing pair check, posted by 21:00; gates on time; one commit SHA per scoring run; the inject logged and acted on, with every hand row re-run into its own file; FREEZE.txt posted before T+120 and nothing scored that changed after it |

The answer key states the weight of each row inside these totals. Scoring uses the drill owner's scoring tool on the frozen copy only.

## What to time and log

The integrator keeps the clock table on the drill PR (no mock content in it):

| Step | Start | End | Machine time | People time | SHA | Note |
|---|---|---|---|---|---|---|
| G0 | | | | | | pair check result |
| G1 | | | | | | |
| G2 | | | | | | |
| Documents received | | | | | | hash check |
| G3 | | | | | | |
| Inject received | | | | | | hash check |
| G5 | | | | | | actions taken, with times |
| G4 | | | | | | |
| Stop | | | | | | stop commit |
| FREEZE posted | | | | | | FREEZE.txt SHA-256 |

Also log: every scoring run with its commit SHA; each release's arrival time and hash check; every inject action (what changed, which rows were re-run, into which file); every defect as a PR comment with the time found and fixed; every heavy run with start, end, peak memory and the lock; any lock wait.

## MOCK and noindex

- Every view built from the run branch shows a banner that starts with **MOCK**; results are generated with `--status mock` and the page is built with `NEXT_PUBLIC_MOCK=1`. The template's "Pre-release template" banner is not enough.
- The served HTML carries a robots meta with `noindex` and `nofollow`, and every response carries `X-Robots-Tag: noindex, nofollow`. Check both on `next start` (`curl -s <url> | grep -o '<meta name="robots"[^>]*>'`, `curl -sI <url> | grep -i x-robots-tag`), not only in the source.
- The public data guard (`uv run python scripts/check_public_data.py`) passes on the stop commit.
- Nothing from the drill is deployed, posted or shared outside the drill PR and the drill issue. The drill PR is a draft labelled `not for merge` and is never merged.

## Packet hygiene

- The packet is held outside this repository. Only its hashes are committed, below.
- Files are released at the set times, not before. The reconciler (the scorer at 23:30) checks each file's SHA-256 on arrival (`shasum -a 256 <file>`) against the table and logs the result.
- The integrator does not open any packet file before its release time.
- Defect text, the filled ledger, the reconciliation CSV and the scored households stay in `~/drill9-work/` until the answer key is released; the drill PR carries times, SHAs, hashes and pass or fail only.
- Code goes in waves: parameters, then modifiers, then new variables.

## Packet hashes (SHA-256)

| File | Release | SHA-256 |
|---|---|---|
| `00-owner-notes.md` | drill owner only | `f4e35d1750878ff031f7e679b932752b72700f894f04d32b51c4f158c5e455c4` |
| `01-statement.md` | 21:30 (T+0) | `ba74b6768cfb269b87c8d59df173f347731572daee2d1b6ac98f031d837c7b6b` |
| `02-documents.md` | 22:10 (T+40) | `69375199f67cc264a996a84da7e66c87242871e7f46e9e06d71a84210213c095` |
| `02-costings.csv` | 22:10 (T+40) | `6ee53f4318758c9a590dee25a1aca5933e0cb881bdbe8d0d9c338ea1d5dc53e0` |
| `02-households.csv` | 22:10 (T+40) | `48b7f589df376e200697820be5eb5a618ac301e6613e94f40e372886557ad472` |
| `02-scoring-sheet.csv` | 22:10 (T+40) | `0d69669448c47a196028dc946b347449519811b9613cdb4126e47ed6e329aab5` |
| `03-inject.md` | 22:45 (T+75) | `034583d6d92cbedffecdc0ff046ab147aba0da0e975ae6eaa3d3237a6da67a5e` |
| `04-answer-key.md` | 23:30 (T+120) | `fed6cc4fd8a35f6ff0b683d34207a687f543015a77d9dcd3efd19b5547c5e323` |
| `04-answer-key-households.csv` | 23:30 (T+120) | `706f730ba5775f536e9857a2fb2f49ab5eda8b261806c4a9b56bec52d48e6aa6` |
| `04-answer-key-ledger.csv` | 23:30 (T+120) | `08ad4ab906537ec5220f49222d801c0d81422081823c8a0db770dd273bdba98f` |
| `generate_household_key.py` | 23:30 (T+120) | `bbcd39f98598b994ef791c80aee13f2ff3f1b561efec9b65f5e43b66f88ff034` |
| `04-score.py` | 23:30 (T+120) | `3d2c2066a4f3a912104cb0f1d9f9d0f186b26678fe8be71e396fce79532947ef` |
