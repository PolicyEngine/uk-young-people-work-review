"""Weighted check of the young people base in a Microcosm UK national file.

Reads only the columns it needs with h5py (about 0.5 GB); no simulation is
built. Prints weighted totals to stdout for issue #7: the 16-24 population, a
NEET proxy, UC and PIP receipt under 25 and the LCWRA proxy, with the
benchmark beside each. The output is for the team only: it is not a public
file and must not be committed under ``data/`` or ``dashboard/public/``.

Run one heavy job at a time on a shared machine:

    until mkdir /tmp/pe-heavy.lock 2>/dev/null; do sleep 30; done
    trap 'rmdir /tmp/pe-heavy.lock' EXIT
    uv run --with h5py python scripts/youth_base_check.py path/to/microcosm_uk_2024_25.h5
"""

import sys

import numpy as np

EMPLOYED = ["FT_EMPLOYED", "PT_EMPLOYED", "FT_SELF_EMPLOYED", "PT_SELF_EMPLOYED"]
COLUMNS = [
    "age",
    "person_household_id",
    "employment_status",
    "current_education",
    "is_in_approved_training",
    "employment_income",
    "self_employment_income",
    "universal_credit_reported",
    "pip_dl_category",
    "pip_m_category",
    "is_disabled_for_benefits",
    "is_apprentice",
]


def _text(values: np.ndarray) -> np.ndarray:
    return values.astype(str) if values.dtype.kind == "S" else values


def main(path: str) -> int:
    import h5py

    with h5py.File(path, "r") as handle:
        people = handle["person/table"]
        households = handle["household/table"]
        cols = {}
        for name in COLUMNS:
            if name in people.dtype.names:
                cols[name] = people.fields(name)[:]
            else:
                print(f"missing column: {name}")
        household_id = households.fields("household_id")[:]
        household_weight = households.fields("household_weight")[:]

    order = np.argsort(household_id)
    index = order[np.searchsorted(household_id[order], cols["person_household_id"])]
    weight = household_weight[index]
    age = cols["age"]

    def total(mask: np.ndarray) -> float:
        return float(weight[mask].sum())

    young = (age >= 16) & (age <= 24)
    status = _text(cols["employment_status"])
    education = _text(cols["current_education"])
    employed = np.isin(status, EMPLOYED)
    in_education = (education != "NOT_IN_EDUCATION") | (status == "STUDENT")
    training = cols["is_in_approved_training"].astype(bool)
    neet = young & ~employed & ~in_education & ~training
    earns = (cols["employment_income"] > 0) | (cols["self_employment_income"] > 0)
    uc = cols["universal_credit_reported"] > 0
    pip = (_text(cols["pip_dl_category"]) != "NONE") | (_text(cols["pip_m_category"]) != "NONE")
    disabled = cols["is_disabled_for_benefits"].astype(bool)

    rows = [
        ("Population 16-24", total(young), "ONS mid-2024, about 7.1-7.3m"),
        ("NEET proxy 16-24", total(neet), "ONS 981k (Apr-Jun 2026)"),
        ("UC reported, 16-24", total(young & uc), "DWP, about 900k young claimants"),
        ("PIP, 16-24", total(young & pip), "Interim annex Table 28: 416k (E&W, 2024-25)"),
        ("LCWRA proxy (UC and disabled for benefits), 16-24", total(young & uc & disabled), "Table 28: 161k (E&W, 2024-25)"),
        ("Never-worked proxy (no earnings), 18-24", total((age >= 18) & (age <= 24) & ~earns), "none"),
    ]
    if "is_apprentice" in cols:
        rows.append(("Apprentices, 16-24", total(young & cols["is_apprentice"].astype(bool)), "HMRC relief claimed by 72k employers"))
    for label, value, benchmark in rows:
        print(f"{label}: {value / 1e3:,.0f}k  (benchmark: {benchmark})")
    print(f"Survey records behind the NEET proxy: {int(neet.sum())}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(sys.argv[1]))
