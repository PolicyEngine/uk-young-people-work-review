"""Candidate measures for the independent review of young people and work.

PLACEHOLDERS. These are the probable recommendations, written before the final
report from the terms of reference, the May 2026 interim report and its
analytical annex, the Pathways to Work consultation and the Budget of
28 October 2026. None is announced policy, and every value below is
illustrative. Every measure has ``placeholder=True``, so the publication step
holds it back (``young_people_work.publication``): nothing here is published as
a figure until it is replaced by the report's own proposal and reconciled.

Every measure is compared against current law in the installed
policyengine-uk. Year Y is fiscal year Y-(Y+1). Values are 2027-28 values in
policyengine-uk 2.174.1, held flat over the policy years in the placeholders;
on the day each measure follows the uprated path. Measures change parameters
(``parameter_changes``, built from ``measure_templates``) or apply a modifier
from ``young_people_work.measures``, one module each; no modifier may live
here.

Routes (see ``docs/METHOD.md``): five placeholder parameter changes and two
structural modifiers (an age test on the UC health element) are computable
today. The rest are routed to the ledger (spending lines), not
computable (a data limit) or needs-pe-uk-first, with the reason shown on the
page.
"""

import warnings

from young_people_work.measure_templates import (
    DataLimitedWarning,
    ModelLimitedWarning,
    merge,
    rate_change,
    threshold_change,
    uc_health_element_change,
)
from young_people_work.measures import health_element_min_age
from young_people_work.models import Likelihood, Reform, Route
from young_people_work.years import POLICY_YEARS

UC = "gov.dwp.universal_credit"
SA = f"{UC}.standard_allowance.amount"
WA = f"{UC}.means_test.work_allowance"
LHA_SAR_AGE = "gov.dwp.LHA.shared_accommodation_age_threshold"
UC_QYP = f"{UC}.elements.child.eligibility.qualifying_young_person_age_limit"
CB_QYP = "gov.hmrc.child_benefit.eligibility.qualifying_young_person_age_limit"
MW_18_20 = "gov.hmrc.minimum_wage.non_apprentice[1].amount"
NI_UNDER_21_AGE = (
    "gov.hmrc.national_insurance.class_1.secondary_zero_rate_age_limits.under_21_group"
)

# 2027-28 values in policyengine-uk 2.174.1 (monthly for UC, hourly for the
# minimum wage, years of age for age limits).
CURRENT_VALUES = {
    f"{SA}.SINGLE_YOUNG": 353.17,
    f"{SA}.SINGLE_OLD": 443.21,
    f"{UC}.elements.disabled.amount": 217.26,
    f"{WA}.with_housing": 441.94,
    f"{WA}.without_housing": 734.85,
    f"{UC}.means_test.reduction_rate": 0.55,
    LHA_SAR_AGE: 35,
    UC_QYP: 20,
    CB_QYP: 20,
    "gov.hmrc.minimum_wage.non_apprentice[1].amount": 11.27,
    "gov.hmrc.minimum_wage.non_apprentice[2].amount": 13.21,
    NI_UNDER_21_AGE: 21,
}

# Current-law paths by fiscal year in policyengine-uk 2.174.1. Checked against
# the installed engine by tests/test_model_engine.py, so a pin move that
# changes them fails there and they are re-read at G0.
# - The protected UC health element (pre-2026 claimants), monthly: the
#   Universal Credit Act 2025 s. 4 floor the engine computes each year.
PROTECTED_HEALTH_ELEMENT = {
    2027: 442.10315091966623,
    2028: 448.01657825650784,
    2029: 454.36556455699156,
    2030: 463.4519296255613,
}
# - The minimum wage for 21 and over, hourly: the April 2027 rate Budget 2026
#   announced, then the engine's projection on the OBR's October 2026 EFO.
NATIONAL_LIVING_WAGE = {2027: 13.21, 2028: 13.51, 2029: 13.85, 2030: 14.23}


def _every_year(value: float) -> dict[int, float]:
    return {year: value for year in POLICY_YEARS}


YOUNG_BANDS = ("16-17", "18-20", "21-24")

with warnings.catch_warnings():
    # The model and data limits these placeholders touch are expected; each
    # measure's route and the Methodology tab record them.
    warnings.simplefilter("ignore", DataLimitedWarning)
    warnings.simplefilter("ignore", ModelLimitedWarning)
    # The 18-20 rate set to the 21-and-over rate in each year, read from the
    # current-law path rather than one literal.
    _MINIMUM_WAGE = rate_change(MW_18_20, dict(NATIONAL_LIVING_WAGE))
    # Lowering the under-25 standard allowance would raise the protected
    # health element for claimants of every age through the UC Act 2025
    # s. 4 floor; holding it at its current-law path keeps the measure to
    # the standard allowance (model limit
    # protected_rate_follows_every_standard_allowance).
    _YOUTH_STANDARD_ALLOWANCE = merge(
        rate_change(f"{SA}.SINGLE_YOUNG", _every_year(317.85)),
        uc_health_element_change(protected=dict(PROTECTED_HEALTH_ELEMENT)),
    )
    _WORK_ALLOWANCES = merge(
        rate_change(f"{WA}.with_housing", _every_year(530.33)),
        rate_change(f"{WA}.without_housing", _every_year(881.82)),
    )


REFORMS: list[Reform] = [
    Reform(
        id="youth_standard_allowance",
        name="Lower youth standard allowance (illustrative)",
        description=(
            "Illustrative age-only stand-in for a separate youth route: the UC "
            "standard allowance for single claimants under 25 at 90% of the "
            "2027-28 rate (£317.85 a month)."
        ),
        recommendation=(
            "A separate route for young people who have never worked, with less "
            "cash and more support"
        ),
        likelihood=Likelihood.HIGH,
        route=Route.DASHBOARD_PARAM,
        route_reason=(
            "The cash part for everyone under 25 is a parameter change. The "
            "never-worked test and the support offer are not modelled."
        ),
        parameter_changes=_YOUTH_STANDARD_ALLOWANCE,
        age_bands_reached=YOUNG_BANDS,
        issues=[4],
    ),
    Reform(
        id="youth_route_never_worked",
        name="Youth route for those who have never worked",
        description=(
            "Young people under 25 who have never worked move to a separate "
            "benefit route with a participation offer."
        ),
        recommendation=(
            "A separate route for young people who have never worked, with less "
            "cash and more support"
        ),
        likelihood=Likelihood.HIGH,
        route=Route.NOT_COMPUTABLE,
        route_reason=(
            "The data hold no work history. The closest proxy, no earnings in "
            "the survey year, includes people who have worked before."
        ),
        data_needs=["has_ever_worked", "neet_status"],
        issues=[4, 7],
    ),
    Reform(
        id="health_element_under_22",
        name="No UC health element for new claimants under 22",
        description=(
            "New claimants under 22 get no UC health element and are offered "
            "support instead. Shown as a range: from the claimants the model "
            "treats as new, up to every claimant under 22."
        ),
        recommendation="Health element for young people replaced by a support offer",
        likelihood=Likelihood.HIGH,
        route=Route.DASHBOARD_STRUCTURAL,
        route_reason=(
            "An age test applied to the health element before the model sets "
            "each claimant's rate. The support offer is not modelled."
        ),
        simulation_modifier=health_element_min_age.new_claimants_under_22,
        upper_bound_modifier=health_element_min_age.all_claimants_under_22,
        applied_before_data_load=True,
        data_needs=["wca_outcome"],
        age_bands_reached=YOUNG_BANDS,
        issues=[2, 3],
    ),
    Reform(
        id="health_element_under_25",
        name="No UC health element for new claimants under 25",
        description="As above, for new claimants under 25.",
        recommendation="Health element for young people replaced by a support offer",
        likelihood=Likelihood.MEDIUM,
        route=Route.DASHBOARD_STRUCTURAL,
        route_reason=(
            "An age test applied to the health element before the model sets "
            "each claimant's rate. The support offer is not modelled."
        ),
        simulation_modifier=health_element_min_age.new_claimants_under_25,
        upper_bound_modifier=health_element_min_age.all_claimants_under_25,
        applied_before_data_load=True,
        data_needs=["wca_outcome"],
        age_bands_reached=YOUNG_BANDS,
        in_headline=False,
        issues=[2, 3],
    ),
    Reform(
        id="limited_capability_for_work_payment",
        name="Payment for limited capability for work",
        description=(
            "A smaller payment for young claimants with limited capability for "
            "work, in place of the all-or-nothing health element."
        ),
        recommendation="Graded health support instead of a single health element",
        likelihood=Likelihood.MEDIUM,
        route=Route.NEEDS_PE_UK_FIRST,
        route_reason=(
            "The model has a limited capability for work flag but no element "
            "amount for it; needs a new variable."
        ),
        data_needs=["wca_outcome"],
        issues=[3],
    ),
    Reform(
        id="work_allowance_all_ages",
        name="Higher work allowances (illustrative)",
        description=(
            "Illustrative: UC work allowances 20% higher (£530.33 and £881.82 a "
            "month) for all ages, as a stand-in for a youth work allowance."
        ),
        recommendation="Make it pay for young people to try work",
        likelihood=Likelihood.MEDIUM,
        route=Route.DASHBOARD_PARAM,
        route_reason=(
            "The all-ages version is a parameter change. A youth-only work "
            "allowance or taper needs an age dimension upstream."
        ),
        parameter_changes=_WORK_ALLOWANCES,
        in_headline=False,
    ),
    Reform(
        id="youth_guarantee",
        name="Guarantee of work, training or an apprenticeship",
        description=(
            "A job, training place or apprenticeship for every young person who "
            "engages, with support and a duty to take up the offer."
        ),
        recommendation="A guarantee for every young person aged 16 to 24",
        likelihood=Likelihood.HIGH,
        route=Route.LEDGER,
        route_reason=(
            "A spending programme. Recorded as a spending line from official "
            "figures or a unit cost; a subsidised job's pay can be shown in "
            "household examples."
        ),
        data_needs=["neet_status"],
        issues=[7],
    ),
    Reform(
        id="local_participation_funding",
        name="Local participation system",
        description=(
            "Upfront funding for combined and local authorities in England to "
            "run support for young people."
        ),
        recommendation="A locally run participation system",
        likelihood=Likelihood.HIGH,
        route=Route.LEDGER,
        route_reason="A grant to local government; recorded as a spending line.",
        coverage="England",
    ),
    Reform(
        id="employer_nics_under_25",
        name="Employer NICs zero rate to age 25",
        description=(
            "Extend the employer National Insurance zero rate from employees "
            "under 21 to employees under 25, up to the upper secondary "
            "threshold."
        ),
        recommendation="Lower the cost of hiring young people",
        likelihood=Likelihood.MEDIUM,
        route=Route.DASHBOARD_PARAM,
        route_reason=(
            "The age limit for the employer zero rate is a parameter. The "
            "modelled relief for employees under 21 is below HMRC's estimate, "
            "so the extension is checked against HMRC's figures before it is "
            "published. Employment effects are not modelled."
        ),
        parameter_changes=threshold_change(NI_UNDER_21_AGE, _every_year(25)),
        data_needs=["employees_under_21", "hiring_flows"],
        # The model passes the employer saving on to pay, profits and prices,
        # so households of every age can gain: no age band is ruled out.
        issues=[1, 6],
    ),
    Reform(
        id="youth_minimum_wage",
        name="18-20 minimum wage at the National Living Wage (illustrative)",
        description=("Illustrative: the 18-20 rate raised to the rate for 21 and over."),
        recommendation="Minimum wage rates for young workers",
        likelihood=Likelihood.LOW,
        route=Route.NOT_COMPUTABLE,
        route_reason=(
            "Earnings are survey inputs, so a wage rate change does not reach "
            "pay; only the UC minimum income floor and similar tests read the "
            "rate. Employment effects are not modelled."
        ),
        parameter_changes=_MINIMUM_WAGE,
        data_needs=["hiring_flows"],
        issues=[1],
    ),
    Reform(
        id="apprenticeship_incentives",
        name="Apprenticeship incentives for employers",
        description=("Larger payments to employers who take on apprentices aged 16 to 24."),
        recommendation="More apprenticeships for young people",
        likelihood=Likelihood.MEDIUM,
        route=Route.LEDGER,
        route_reason=(
            "A payment to employers per apprentice; recorded as a spending line. "
            "The pinned data have no apprentice flag."
        ),
        data_needs=["is_apprentice"],
        issues=[6],
        coverage="England",
    ),
    Reform(
        id="family_benefits_in_training",
        name="Family support for young people in training to 21 (illustrative)",
        description=(
            "Illustrative: the UC child element and Child Benefit continue for "
            "young people in approved education or training until 21 rather "
            "than 20."
        ),
        recommendation="Keep family support while a young person trains",
        likelihood=Likelihood.LOW,
        route=Route.DASHBOARD_PARAM,
        route_reason=(
            "The qualifying young person age limits are parameters. A new "
            "learning allowance would need a new variable."
        ),
        parameter_changes=merge(
            threshold_change(UC_QYP, _every_year(21)),
            threshold_change(CB_QYP, _every_year(21)),
        ),
        age_bands_reached=("18-20", "21-24", "25 and over"),
    ),
    Reform(
        id="learning_allowance",
        name="Learning allowance for young people in training",
        description=(
            "A weekly allowance for young people aged 16 to 24 in approved "
            "training, tested on household income."
        ),
        recommendation="Financial support to stay in learning",
        likelihood=Likelihood.LOW,
        route=Route.NEEDS_PE_UK_FIRST,
        route_reason=(
            "No such allowance in the model; needs a new variable reading "
            "approved training and household income."
        ),
    ),
    Reform(
        id="pip_young_people",
        name="PIP for young people aged 16 to 24",
        description=(
            "Changes to PIP for young people, such as a participation plan "
            "alongside or in place of a daily living award."
        ),
        recommendation="Health and disability support for young people",
        likelihood=Likelihood.MEDIUM,
        route=Route.NEEDS_PE_UK_FIRST,
        route_reason=(
            "PIP rates are parameters but have no age dimension; any age rule "
            "needs a new formula. PIP applies in England and Wales."
        ),
        coverage="England and Wales",
    ),
    Reform(
        id="mental_health_access",
        name="Mental health support for young people",
        description="Faster access to mental health support for under-25s.",
        recommendation="Faster mental health support",
        likelihood=Likelihood.MEDIUM,
        route=Route.LEDGER,
        route_reason="A health service measure; recorded as a spending line.",
        coverage="England",
    ),
    Reform(
        id="tracking_and_participation_age",
        name="Track every young person; raise the participation age",
        description=(
            "A duty to track young people to 24 and a higher participation age in England."
        ),
        recommendation="Know where every young person is",
        likelihood=Likelihood.LOW,
        route=Route.LEDGER,
        route_reason="An administrative duty; recorded as a spending line if costed.",
        coverage="England",
    ),
    Reform(
        id="shared_accommodation_age_25",
        name="Shared accommodation rate to age 25 (illustrative)",
        description=(
            "Illustrative: single renters aged 25 to 34 move from the shared "
            "accommodation rate to the one-bedroom rate."
        ),
        recommendation="Housing support for young people",
        likelihood=Likelihood.LOW,
        route=Route.DASHBOARD_PARAM,
        route_reason="The age threshold is a parameter; modelled directly.",
        parameter_changes=threshold_change(LHA_SAR_AGE, _every_year(25)),
        age_bands_reached=("25 and over",),
        in_headline=False,
    ),
    Reform(
        id="shared_accommodation_care_leavers",
        name="Shared accommodation rate exemptions for care leavers",
        description=(
            "Wider exemptions from the shared accommodation rate for care "
            "leavers and other young people at risk."
        ),
        recommendation="Housing support for young people",
        likelihood=Likelihood.LOW,
        route=Route.NOT_COMPUTABLE,
        route_reason=(
            "The data have no care-leaver flag, and the model does not observe "
            "the existing care-leaver and hostel exceptions."
        ),
        data_needs=["is_care_leaver"],
        issues=[5],
    ),
]

REFORMS_BY_ID: dict[str, Reform] = {reform.id: reform for reform in REFORMS}


def get_reform(reform_id: str) -> Reform:
    try:
        return REFORMS_BY_ID[reform_id]
    except KeyError as error:
        raise KeyError(f"No measure {reform_id!r}") from error
