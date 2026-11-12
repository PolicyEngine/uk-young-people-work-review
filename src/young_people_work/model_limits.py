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
        return any(path == p or path.startswith((p + ".", p + "[")) for p in self.paths)


LIMITS: tuple[ModelLimit, ...] = (
    ModelLimit(
        key="health_element_shadowed",
        paths=(
            "gov.dwp.universal_credit.elements.disabled",
            "variable:uc_LCWRA_element",
        ),
        reason=(
            "From 2026-27 the model sets each claimant's UC health element "
            "directly, at the protected rate for claims made before April 2026 "
            "and the lower rate for later claims. A change to the element's own "
            "amount therefore has no effect; changes are written against the two "
            "rates, or as an age test applied before that step."
        ),
        issue=2,
    ),
    ModelLimit(
        key="new_claimant_share_has_no_age",
        paths=(
            "gov.dwp.universal_credit.rebalancing.new_claimant_share",
            "variable:uc_receives_new_claimant_health_element",
        ),
        reason=(
            "Which claimants get the lower health element rate for claims made "
            "from April 2026 is assigned at random, at the same share for every "
            "age (13% in 2027-28). Young claimants are more likely to be recent "
            "claimants, so a measure for new young claimants is shown as a range: "
            "from that share up to every young claimant."
        ),
        issue=2,
    ),
    ModelLimit(
        key="protected_rate_follows_every_standard_allowance",
        paths=(
            "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG",
            "gov.dwp.universal_credit.standard_allowance.amount.COUPLE_YOUNG",
        ),
        reason=(
            "Under the Universal Credit Act 2025 the protected health element "
            "rate is set so that, with each standard allowance, it keeps its "
            "value. Lowering the under-25 standard allowance would therefore "
            "raise the protected rate for claimants of every age. The measures "
            "here hold the protected rate at its current-law path, so the change "
            "reaches only the standard allowance."
        ),
    ),
    ModelLimit(
        key="lcwra_from_disability_benefits",
        paths=("variable:uc_limited_capability_for_WRA",),
        reason=(
            "Whether a claimant has limited capability for work-related activity "
            "follows receipt of disability benefits in the data, not an "
            "assessment outcome. The total for 16-24-year-olds is close to the "
            "official count, but who is in the group may differ; this is "
            "checked against the official figures on the day."
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
            "UC work allowances and the taper do not vary by age in the model, so "
            "an all-ages change stands in for a change for young people only and "
            "reaches claimants of every age."
        ),
    ),
    ModelLimit(
        key="youth_rate_single_claimants_only",
        paths=("gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG",),
        reason=(
            "The under-25 standard allowance for single claimants does not cover "
            "couples where both partners are under 25, who have their own rate."
        ),
    ),
    ModelLimit(
        key="pip_no_country_test",
        paths=("gov.dwp.pip", "variable:pip"),
        reason=(
            "PIP has no country test in the model, and Scotland's Adult "
            "Disability Payment is recorded as PIP in the data. PIP measures are "
            "shown for England and Wales only."
        ),
    ),
)


def variable_path(name: str) -> str:
    return f"variable:{name}"


def limits_for_paths(paths: Iterable[str]) -> list[ModelLimit]:
    paths = list(paths)
    return [limit for limit in LIMITS if any(limit.covers(p) for p in paths)]
