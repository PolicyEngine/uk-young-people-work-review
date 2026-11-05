# Runbook for the day the report is published

The publication date is not announced; trade press expects November 2026. The government response is due by the end of 2026, with a White Paper early in 2027, so official costings of the recommendations may not come on the day. The ONS NEET bulletin is due on 26 November 2026.

1. **G0 (as soon as the date is known).** Freeze the engine and data pair; record versions and the dataset SHA-256 in the PR. Decide the pin for the employer NICs measures (#1). Run one data-loading job at a time.
2. **G1 (within 30 minutes of publication).** Read the report. Write the coverage ledger: one line per recommendation with route, cause and where it applies. Replace the placeholder measures in `reforms.py` with the report's own, keeping `placeholder=True` until reconciled.
3. **G2.** Generate in model mode for the computable measures. Hand-check one household per measure against the presets in `household.py`.
4. **G3.** Reconcile against the report's own figures and any official figure in `data_inputs/official/`. Write a reason for each gap over 10%.
5. **G4.** Protected preview with banner and noindex, checked behind the login. Sign-off rows for every public file (`sign_off.REQUIRED` is on).
6. **G5.** Re-run after any correction or new official figure; update the ledger causes.

Nothing deploys from this repository until the team chooses a target (`.github/workflows/deploy.yml`).
