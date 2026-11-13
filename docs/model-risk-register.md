# Model risk register

| Risk | Effect on the day | Mitigation | Issue |
|---|---|---|---|
| Health element has no age test and is stored directly in 2026-2032 | The most likely cash measure cannot be costed | Age parameter upstream; until then household examples only | #2 |
| LCWRA follows disability-benefit receipt on eeb6093e; from the FRS UC admin record on builds with Microcosm #1550, fitted to DWP's paid count on 6f918b81 | Young LCWRA group and the saving from an age limit understated on eeb6093e | Re-run the young UC health count on the build used on the day; compare with Table 28 | #3 |
| No work history | "Never worked" route costed for everyone under the age limit, or on a proxy | Show both bounds; label the proxy | #4 |
| No care-leaver flag | Shared accommodation exemptions cost nothing | Household examples only; not computable | #5 |
| Apprentice flag drawn only at ages 21-24 (about 214-237 records); apprentice relief about 28% short of HMRC (£0.27bn against £0.37bn in 2024-25); under-21 relief close in 2024-25 (about £1.06bn against £1.10bn) but about 18% short in 2025-26 (about £1.55bn against HMRC's £1.9bn projection) | Employer NICs extension mis-sized, more so in later years | Check the under-21 relief against HMRC on the pinned build; close microcosm #1374 | #6 |
| No NEET target (a held-out check only); single ages 16-24 bound to ONS (Microcosm #1535, in eeb6093e); UC claimants 16-21 and 22-24 bound to DWP only on builds with Microcosm #1550; no age-band outputs | NEET base unchecked; custom code needed on the day | Run `scripts/youth_base_check.py`; add filters | #7 |
| Small cells for young people by region or constituency | Charts not publishable | Disclosure floor of 10 households; national and regional figures first | |
| Static basis against costings with behaviour | Gaps that read as errors | Declare the basis once; cause class `basis` | |
| Devolved employment support | UK figures for England-only measures | `coverage` on every measure; ledger lines by nation | |
