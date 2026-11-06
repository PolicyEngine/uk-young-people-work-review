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
        return any(path == p or path.startswith((p + ".", p + "[")) for p in self.parameters)


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
    DataLimit(
        key="pip_assessment_points_missing",
        parameters=(
            "gov.dwp.pip.daily_living.points_thresholds",
            "gov.dwp.pip.mobility.points_thresholds",
        ),
        missing_input="pip_dl_points",
        reason=(
            "The data hold the PIP award level, not the assessment points behind "
            "it, so a change to the points needed for an award cannot be costed. "
            "Changes to the weekly rates can."
        ),
        variables=("pip_dl_points", "pip_m_points"),
    ),
)

# Data limits keyed by the Microcosm national build they hold for. A new
# build is adopted only after each entry is re-checked (docs/RUNBOOK.md,
# "Adopting a release"). a6299504 is the build policyengine 6.11.1 pins.
LIMITS_BY_BUILD: dict[str, tuple[str, ...]] = {
    "a6299504": (
        "minimum_wage_does_not_reach_pay",
        "pip_assessment_points_missing",
    ),
}


@dataclass(frozen=True)
class MissingInput:
    """An input a measure may need that no parameter path names."""

    key: str
    reason: str
    issue: int | None = None


MISSING_INPUTS: tuple[MissingInput, ...] = (
    MissingInput(
        "has_ever_worked",
        "No work history. The closest proxy, no earnings in the survey year, "
        "includes young people who have worked before.",
        4,
    ),
    MissingInput(
        "neet_status",
        "No flag for being out of education, employment or training, or for how "
        "long. A proxy is built from employment status, education and approved "
        "training, and is not calibrated to the ONS count.",
        7,
    ),
    MissingInput(
        "wca_outcome",
        "No Work Capability Assessment outcome. The health element group is "
        "inferred from disability-benefit receipt.",
        3,
    ),
    MissingInput(
        "is_care_leaver",
        "No survey source records who has left care, so the data have no "
        "care-leaver flag and the shared accommodation rate exceptions for care "
        "leavers are not observed. Care leavers appear in example households "
        "only.",
        5,
    ),
    MissingInput(
        "is_apprentice",
        "No apprentice flag in the pinned national build. Later builds impute "
        "apprentices among employees aged 21 to 24 to size the employer National "
        "Insurance relief, from a small number of survey records, so effects on "
        "apprentices alone are shown in example households, not as national "
        "totals.",
        6,
    ),
    MissingInput(
        "employees_under_21",
        "Employees under 21 are not a separate calibration target. The employer "
        "National Insurance relief for them is checked against HMRC's estimate "
        "on the data used for publication.",
        6,
    ),
    MissingInput(
        "uc_claimants_16_17",
        "Few survey records cover 16- and 17-year-olds on Universal Credit, so "
        "figures for them are national only and are not split by region.",
        7,
    ),
    MissingInput(
        "hiring_flows",
        "No employer records, hiring or job-to-job flows, so employment effects "
        "of wages and incentives are not modelled.",
    ),
)
MISSING_INPUTS_BY_KEY = {item.key: item for item in MISSING_INPUTS}


def limits_for_paths(paths: Iterable[str]) -> list[DataLimit]:
    """The data limits that cover any of the given parameter paths."""
    paths = list(paths)
    return [limit for limit in LIMITS if any(limit.covers(p) for p in paths)]


def is_only_data_limited(paths: Iterable[str]) -> bool:
    """True when every path is covered by a limit: the measure cannot move anyone."""
    paths = list(paths)
    return bool(paths) and all(limits_for_paths([p]) for p in paths)
