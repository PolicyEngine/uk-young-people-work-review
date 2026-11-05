"""Model limits: places where the installed policyengine-uk mis-costs a measure.

Pruned from the AB2026 dashboard's ``model_limits``. A measure that touches a
model limit is held at provisional and never approved until the limit is
fixed upstream or handled in this repository.
"""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelLimit:
    key: str
    paths: tuple[str, ...]
    reason: str
    issue: int | None = None

    def covers(self, path: str) -> bool:
        return any(
            path == p or path.startswith((p + ".", p + "["))
            for p in self.paths
        )


LIMITS: tuple[ModelLimit, ...] = (
    ModelLimit(
        key="employer_nics_zero_rate_missing",
        paths=(
            "gov.hmrc.national_insurance.class_1.secondary_zero_rate_age_limits",
            "gov.hmrc.national_insurance.class_1.thresholds.upper_secondary_threshold",
        ),
        reason=(
            "policyengine-uk 2.151.0, the pinned version, does not model the "
            "employer zero rate for under-21s or apprentices under 25. Widening "
            "it changes nothing until the pin moves to 2.175.x or later."
        ),
        issue=1,
    ),
    ModelLimit(
        key="minimum_wage_2027_out_of_date",
        paths=("gov.hmrc.minimum_wage",),
        reason=(
            "The pinned version holds April 2027 minimum wage rates of £12.71, "
            "£10.85 and £8.00, against the published £13.21, £11.27 and £8.31."
        ),
        issue=1,
    ),
    ModelLimit(
        key="health_element_shadowed",
        paths=(
            "gov.dwp.universal_credit.elements.disabled",
            "gov.dwp.universal_credit.rebalancing",
            "variable:uc_LCWRA_element",
        ),
        reason=(
            "The UC health element has no age test, and in 2026-2032 the "
            "rebalancing step stores it with set_model_value, so a change to "
            "the amount parameter is overridden."
        ),
        issue=2,
    ),
    ModelLimit(
        key="lcwra_from_disability_benefits",
        paths=("variable:uc_limited_capability_for_WRA",),
        reason=(
            "LCWRA follows the stored flag is_disabled_for_benefits, not a Work "
            "Capability Assessment outcome, so the young LCWRA group is "
            "undercounted."
        ),
        issue=3,
    ),
    ModelLimit(
        key="no_age_dimension_in_uc_means_test",
        paths=(
            "gov.dwp.universal_credit.means_test.work_allowance",
            "gov.dwp.universal_credit.means_test.reduction_rate",
        ),
        reason=(
            "Work allowances and the taper do not vary by age. An all-ages change "
            "stands in for a youth-only one and reaches every UC claimant."
        ),
    ),
    ModelLimit(
        key="youth_rate_single_claimants_only",
        paths=("gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG",),
        reason=(
            "SINGLE_YOUNG covers single claimants under 25 only. Couples where "
            "both are under 25 use COUPLE_YOUNG; a youth route needs both, or a "
            "new age parameter."
        ),
    ),
    ModelLimit(
        key="pip_no_country_test",
        paths=("gov.dwp.pip", "variable:pip"),
        reason=(
            "PIP has no country test, and Scottish Adult Disability Payment is "
            "stored as PIP. Mask PIP measures to England and Wales."
        ),
    ),
)


def variable_path(name: str) -> str:
    return f"variable:{name}"


def limits_for_paths(paths: Iterable[str]) -> list[ModelLimit]:
    paths = list(paths)
    return [limit for limit in LIMITS if any(limit.covers(p) for p in paths)]
