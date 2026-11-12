# Model risk register

| Risk | Effect on the day | Mitigation | Issue |
|---|---|---|---|
| Health element has no age test and is stored directly in 2026-2032 | The most likely cash measure cannot be costed | Age parameter upstream; until then household examples only | #2 |
| LCWRA follows disability-benefit receipt | Young LCWRA group and the saving from an age limit understated | Impute LCWRA by age; calibration target against Table 28 | #3 |
| No work history | "Never worked" route costed for everyone under the age limit, or on a proxy | Show both bounds; label the proxy | #4 |
| No care-leaver flag | Shared accommodation exemptions cost nothing | Household examples only; not computable | #5 |
| Apprentice flag drawn only at ages 21-24 (about 214-237 records); apprentice relief about 28% short of HMRC; under-21 NICs base short of HMRC | Employer NICs extension mis-sized | Check the under-21 relief against HMRC on the pinned build; close microcosm #1374 | #6 |
| No youth calibration target; no age-band outputs | Base for young people unchecked; custom code needed on the day | Run `scripts/youth_base_check.py`; add filters | #7 |
| Small cells for young people by region or constituency | Charts not publishable | Disclosure floor of 10 households; national and regional figures first | |
| Static basis against costings with behaviour | Gaps that read as errors | Declare the basis once; cause class `basis` | |
| Devolved employment support | UK figures for England-only measures | `coverage` on every measure; ledger lines by nation | |
