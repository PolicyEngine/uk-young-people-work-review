# Data contract

- **Engine and data pair.** `policyengine[uk]==6.11.1`, which pins policyengine-uk 2.151.0 and the Microcosm UK 2024-25 national build `20261025T091414Z-a6299504`. Not yet a validated pair for these measures: every figure carries "unvalidated under this engine" until G0 names a certified pair. The pinned engine does not model the employer NICs zero rate (#1).
- **Microdata stay private.** No `.h5` file, record-level extract or weight is committed (`.gitignore`, `scripts/check_public_data.py`). `scripts/youth_base_check.py` prints weighted totals for the team only.
- **Columns the measures read:** `age`, `employment_status`, `current_education`, `is_in_approved_training`, `is_in_non_advanced_education`, `employment_income`, `self_employment_income`, `hours_worked`, `universal_credit_reported`, `is_disabled_for_benefits`, `pip_dl_category`, `pip_m_category`, `region`, `rent`, `tenure_type`.
- **Columns the measures need but the data lack:** work history, NEET status and duration, Work Capability Assessment outcome or UC conditionality group, care-leaver status, an apprentice flag (pinned build), employer records and hiring flows.
- **Heavy runs.** Run one data-loading job at a time and check available memory first. Prefer reading the needed columns to full simulations.
