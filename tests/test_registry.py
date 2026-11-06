import pytest

from young_people_work import data_limits
from young_people_work.measure_templates import UC_PROTECTED_HEALTH
from young_people_work.models import Likelihood, Reform, Route
from young_people_work.reforms import CURRENT_VALUES, REFORMS, REFORMS_BY_ID, get_reform
from young_people_work.years import POLICY_YEARS

COMPUTABLE = {
    "youth_standard_allowance",
    "health_element_under_22",
    "health_element_under_25",
    "work_allowance_all_ages",
    "family_benefits_in_training",
    "shared_accommodation_age_25",
}


def test_ids_unique_and_complete():
    assert len(REFORMS) == 18
    assert len(REFORMS_BY_ID) == len(REFORMS)


def test_every_measure_is_a_placeholder():
    # Template rule: nothing is published before the report.
    assert all(reform.placeholder for reform in REFORMS)
    assert not any(reform.publishable for reform in REFORMS)


@pytest.mark.parametrize("reform", REFORMS, ids=lambda r: r.id)
def test_every_measure_has_a_route_and_reason(reform):
    assert isinstance(reform.route, Route)
    assert reform.route_reason.strip()
    assert reform.recommendation.strip()


@pytest.mark.parametrize("reform", REFORMS, ids=lambda r: r.id)
def test_parameter_years_cover_policy_years(reform):
    for path, values in (reform.parameter_changes or {}).items():
        assert sorted(values) == [str(y) for y in POLICY_YEARS], path


@pytest.mark.parametrize("reform", REFORMS, ids=lambda r: r.id)
def test_data_needs_are_documented(reform):
    known = set(data_limits.MISSING_INPUTS_BY_KEY) | {
        limit.missing_input for limit in data_limits.LIMITS
    }
    assert set(reform.data_needs) <= known


def test_computable_measures():
    assert {r.id for r in REFORMS if r.computable} == COMPUTABLE
    for reform in REFORMS:
        if reform.computable and reform.parameter_changes:
            sketch_paths = set(reform.parameter_changes) - {UC_PROTECTED_HEALTH}
            assert sketch_paths <= set(CURRENT_VALUES)


def test_minimum_wage_measure_is_not_computable():
    # Earnings are inputs: a wage rate change is never costed.
    reform = get_reform("youth_minimum_wage")
    assert data_limits.is_only_data_limited(reform.parameter_changes)
    assert reform.route is Route.NOT_COMPUTABLE


def test_employer_nics_needs_the_model_first():
    reform = get_reform("employer_nics_under_25")
    assert reform.route is Route.NEEDS_PE_UK_FIRST
    assert reform.parameter_changes is None


def test_health_element_age_test_is_a_before_load_modifier():
    for reform_id in ("health_element_under_22", "health_element_under_25"):
        reform = get_reform(reform_id)
        assert reform.route is Route.DASHBOARD_STRUCTURAL
        assert reform.applied_before_data_load is True
        assert reform.upper_bound_modifier is not None


def test_headline_excludes_all_ages_and_older_stand_ins():
    headline = {r.id for r in REFORMS if r.computable and r.in_headline}
    assert "work_allowance_all_ages" not in headline
    assert "shared_accommodation_age_25" not in headline
    assert "youth_standard_allowance" in headline
    assert 2 in get_reform("health_element_under_22").issues
    assert 1 in get_reform("employer_nics_under_25").issues


def test_spending_lines_are_ledger_only():
    ledger = {r.id for r in REFORMS if r.route is Route.LEDGER}
    assert ledger == {
        "youth_guarantee",
        "local_participation_funding",
        "apprenticeship_incentives",
        "mental_health_access",
        "tracking_and_participation_age",
    }


def test_youth_rate_placeholder_is_ninety_percent():
    change = get_reform("youth_standard_allowance").parameter_changes
    path = "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG"
    assert change[path]["2027"] == pytest.approx(0.9 * CURRENT_VALUES[path], abs=0.01)


def test_coverage_values():
    assert get_reform("pip_young_people").coverage == "England and Wales"
    assert get_reform("local_participation_funding").coverage == "England"
    assert get_reform("youth_standard_allowance").coverage == "UK"


def test_route_validation_rejects_param_route_without_change():
    with pytest.raises(ValueError):
        Reform(
            id="bad",
            name="Bad",
            recommendation="x",
            likelihood=Likelihood.LOW,
            route=Route.DASHBOARD_PARAM,
            route_reason="x",
        )


def test_ledger_route_carries_no_change():
    with pytest.raises(ValueError):
        Reform(
            id="bad",
            name="Bad",
            recommendation="x",
            likelihood=Likelihood.LOW,
            route=Route.LEDGER,
            route_reason="x",
            parameter_changes={"gov.dwp.LHA.shared_accommodation_age_threshold": {"2027": 30.0}},
        )


def test_get_reform_unknown():
    with pytest.raises(KeyError):
        get_reform("nope")


def test_summary_has_no_callables():
    for reform in REFORMS:
        summary = reform.summary()
        assert all(not callable(v) for v in summary.values())
