# Candidate reforms

Probable recommendations of the independent review of young people and work, drawn from its terms of reference (November 2025), the interim report and analytical annex (28 May 2026), the Pathways to Work consultation response and reports in October and November 2026. Likelihood is a judgement of what the final report recommends; the government response, due by the end of 2026, could add others. The report is expected to set out principles more than rates, so the computable rows are illustrative scenarios with ranges, not point estimates.

The table is generated from `src/young_people_work/reforms.py`; edit the registry, not this file.

| Id | Measure | Likelihood | Route today | Applies in | Data needs | Issues |
|---|---|---|---|---|---|---|
| `youth_standard_allowance` | Lower youth standard allowance (illustrative) | High | dashboard-param (placeholder) | UK | none | #4 |
| `youth_route_never_worked` | Youth route for those who have never worked | High | not-computable | UK | `has_ever_worked`, `neet_status` | #4, #7 |
| `health_element_under_22` | No UC health element under 22 | High | needs-pe-uk-first | UK | `wca_outcome` | #2, #3 |
| `health_element_under_25` | No UC health element under 25 | Medium | needs-pe-uk-first | UK | `wca_outcome` | #2, #3 |
| `limited_capability_for_work_payment` | Payment for limited capability for work | Medium | needs-pe-uk-first | UK | `wca_outcome` | #3 |
| `work_allowance_all_ages` | Higher work allowances (illustrative) | Medium | dashboard-param (placeholder) | UK | none |  |
| `youth_guarantee` | Guarantee of work, training or an apprenticeship | High | ledger | UK | `neet_status` | #7 |
| `local_participation_funding` | Local participation system | High | ledger | England | none |  |
| `employer_nics_under_25` | Employer NICs zero rate to age 25 | Medium | needs-pe-uk-first | UK | none | #1, #6 |
| `youth_minimum_wage` | 18-20 minimum wage at the National Living Wage (illustrative) | Low | not-computable | UK | `hiring_flows` | #1 |
| `apprenticeship_incentives` | Apprenticeship incentives for employers | Medium | ledger | England | `is_apprentice` | #6 |
| `family_benefits_in_training` | Family support for young people in training to 21 (illustrative) | Low | dashboard-param (placeholder) | UK | none |  |
| `learning_allowance` | Learning allowance for young people in training | Low | needs-pe-uk-first | UK | none |  |
| `pip_young_people` | PIP for young people aged 16 to 24 | Medium | needs-pe-uk-first | England and Wales | none |  |
| `mental_health_access` | Mental health support for young people | Medium | ledger | England | none |  |
| `tracking_and_participation_age` | Track every young person; raise the participation age | Low | ledger | England | none |  |
| `shared_accommodation_age_25` | Shared accommodation rate to age 25 (illustrative) | Low | dashboard-param (placeholder) | UK | none |  |
| `shared_accommodation_care_leavers` | Shared accommodation rate exemptions for care leavers | Low | not-computable | UK | `is_care_leaver` | #5 |

## Ranges to have ready

| Lever | Parameter (policyengine-uk) | Current 2027-28 value (2.151.0) | Range to prepare |
|---|---|---|---|
| Youth standard allowance | `gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG` (and `COUPLE_YOUNG`) | £353.17 a month | 70% to 100% |
| Age band for a youth route | needs a new age parameter (#2) | 25 (`claimant_type.age_threshold`) | 18-21, 18-24 |
| Health element for young claimants | needs an age parameter (#2) | £217.26 a month for new claimants | £0 to £217.26; age 22 or 25; protected claimants in or out |
| Work allowances | `gov.dwp.universal_credit.means_test.work_allowance.*` | £441.94 / £734.85 a month | up to about £1,000 |
| Taper | `gov.dwp.universal_credit.means_test.reduction_rate` | 55% | 45% to 55% (youth-only needs an age dimension) |
| Employer NICs zero rate | `gov.hmrc.national_insurance.class_1.secondary_zero_rate_age_limits.under_21_group` (2.175.x only, #1) | 21 | 21 to 25 |
| Qualifying young person age limit | `...qualifying_young_person_age_limit` (UC, Child Benefit, CTC, Pension Credit) | 20 | 20 to 21 |
| Shared accommodation rate age | `gov.dwp.LHA.shared_accommodation_age_threshold` | 35 | 25 to 35 |
| Learning allowance | new variable | none | £30 to £60 a week, income test £20,000 to £35,000 |

## Spending lines

The guarantee, local participation funding, apprenticeship incentives, mental health access and the tracking duty are spending programmes. Record each as a ledger line with the official figure, or a unit cost with the source. A 6-month, 25-hour subsidised job at the 2027 18-20 rate of £11.27 costs about £7,300 in wages before support costs.

## Comparators to load on the day

- The final report and its analytical annex (caseload projections, case-study incomes). Interim annex Table 28 is in `data_inputs/official/`.
- ONS NEET bulletin (next release 26 November 2026).
- OBR Economic and fiscal outlook, October 2026: incapacity caseload and the welfare cap.
- DWP benefit expenditure and caseload tables; Stat-Xplore UC by age and conditionality regime; PIP by age.
- HMRC tax relief statistics, Table 2 (employer NICs reliefs for under-21s and apprentices).
