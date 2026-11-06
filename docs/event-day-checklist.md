# Event-day checklist

One page. Details and commands: `docs/RUNBOOK.md`.

## Roles

| Role | Owns | Does not |
|---|---|---|
| Integrator | the branch, every commit, generation, re-basing, the clock | score households |
| Reconciler | the ledger, `reconciliation.csv`, defects within 5 minutes | push code |
| Scorer | households from the published sheets, one commit SHA per scoring run | edit reform code |

## Clock (from publication, T)

| T | Gate | Done when |
|---|---|---|
| before | G0 | freeze record posted: start SHA, versions, dataset id and SHA-256, certified or "unvalidated" |
| +30 min | G1 | every recommendation routed, with cause class and coverage |
| +60 min | G2 | `make model` finished; one hand-checked household per measure |
| +90 min | G3 | `reconcile` exits 0: every gap over 10% has a reason |
| +2 h | G4 | build checked: banner, noindex meta and header, every view screenshotted |
| any time | G5 | correction rerun with new receipts; household and reconciliation rows re-run |

## G4 checks on a local build

```
make build                      # inside /tmp/pe-heavy.lock
grep -q 'name="robots" content="noindex' dashboard/.next/server/app/index.html
grep -q 'placeholder-banner\|mock-banner' dashboard/.next/server/app/index.html
cd dashboard && bun run start -p 3917 &
curl -sI localhost:3917 | grep -i x-robots-tag      # noindex, nofollow
# screenshot every tab at 1280 and 390 wide; then kill the server
uv run python scripts/check_public_data.py
```

## Never

- Never merge, push to main or deploy from this checklist; publication is a reviewed PR.
- Never hand-edit `results.json`; rerun.
- Never show a measure that is not computable as £0, or add a spending line to the modelled total.
- Never publish a figure from an unvalidated engine and data pair (the build fails).
- Never run two heavy jobs at once; take `/tmp/pe-heavy.lock`.
- Never post figures, households or charts before sign-off, in a public PR, issue or channel.

## If something fails

| Failure | Do |
|---|---|
| `model-run` waits for the lock | check who holds it (`ls -ld /tmp/pe-heavy.lock`); clear it only once its owner has exited |
| a computable measure has no run | `generate --mode model` fails; run it, never publish without it |
| a gap over 10% has no reason | `reconcile` exits 1; write the reason or re-route the line |
| a build has no banner | stop; the results status or `NEXT_PUBLIC_MOCK` is wrong |
| a correction lands after G4 | G5: full rerun, new receipts, rebuild, re-check G4 |
