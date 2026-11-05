"""Data limits: what the data do not hold, so a measure cannot move anyone.

Pruned from the AB2026 dashboard's ``data_limits`` to the entries the review
of young people and work touches. The source detects limits by inspecting
formulas; this template keeps the declarative entries and the lookup, which is
all the registry needs.

A measure that moves only a limited parameter is published as not computable,
with the reason, and never as £0 (``young_people_work.publication``).
"""

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DataLimit:
    key: str
    parameters: tuple[str, ...]
    missing_input: str
    reason: str
    issue: int | None = None
    variables: tuple[str, ...] = field(default_factory=tuple)

    def covers(self, path: str) -> bool:
        return any(
            path == p or path.startswith((p + ".", p + "["))
            for p in self.parameters
        )


LIMITS: tuple[DataLimit, ...] = (
    DataLimit(
        key="minimum_wage_does_not_reach_pay",
        parameters=("gov.hmrc.minimum_wage",),
        missing_input="hourly_wage_response",
        reason=(
            "Earnings are survey inputs. A change to a minimum wage rate does not "
            "change anyone's pay; only the UC minimum income floor, the benefit "
            "cap exception and similar tests read the rate. Hiring and hours "
            "effects are not modelled."
        ),
        issue=1,
        variables=("employment_income", "hours_worked"),
    ),
)

# Inputs a measure may need that no parameter path names. The registry lists
# them under ``data_needs``; the page shows the reason.
MISSING_INPUTS: dict[str, str] = {
    "has_ever_worked": (
        "No work history. The proxy, no earnings in the survey year, includes "
        "young people who have worked before (issue #4)."
    ),
    "neet_status": (
        "No NEET flag or NEET duration. A proxy is built from employment status, "
        "education and approved training, and is not calibrated to the ONS "
        "count (issue #7)."
    ),
    "wca_outcome": (
        "No Work Capability Assessment outcome. LCWRA follows disability-benefit "
        "receipt, so young claimants in the LCWRA group without PIP or DLA are "
        "missed (issue #3)."
    ),
    "is_care_leaver": (
        "No care-leaver flag; the shared accommodation rate exceptions for care "
        "leavers are not observed (issue #5)."
    ),
    "is_apprentice": (
        "No apprentice flag in the pinned national build; it is imputed from the "
        "20261103 build onwards (issue #6)."
    ),
    "hiring_flows": (
        "No employer records, hiring or job-to-job flows; employment effects of "
        "wages and incentives are not modelled."
    ),
}


def limits_for_paths(paths: Iterable[str]) -> list[DataLimit]:
    """The data limits that cover any of the given parameter paths."""
    paths = list(paths)
    return [limit for limit in LIMITS if any(limit.covers(p) for p in paths)]


def is_only_data_limited(paths: Iterable[str]) -> bool:
    """True when every path is covered by a limit: the measure cannot move anyone."""
    paths = list(paths)
    return bool(paths) and all(limits_for_paths([p]) for p in paths)
