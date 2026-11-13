import warnings

import pytest

from young_people_work import data_limits, model_limits
from young_people_work.measure_templates import (
    REGISTERED_TEMPLATES,
    DataLimitedWarning,
    ModelLimitedWarning,
    merge,
    rate_change,
    threshold_change,
)

WA = "gov.dwp.universal_credit.means_test.work_allowance.with_housing"


def test_registered_templates():
    assert REGISTERED_TEMPLATES == ("rate_change", "threshold_change", "uc_health_element_change")


def test_uc_health_element_change_only_in_rebalanced_years():
    from young_people_work.measure_templates import UC_PROTECTED_HEALTH, uc_health_element_change

    assert uc_health_element_change(protected={2027: 400}) == {UC_PROTECTED_HEALTH: {"2027": 400.0}}
    with pytest.raises(ValueError, match="would score nothing"):
        uc_health_element_change(protected={2040: 400})
    with pytest.raises(ValueError):
        uc_health_element_change()


def test_health_element_amount_refused_in_rebalanced_years():
    with pytest.raises(ValueError, match="scores nothing"):
        rate_change("gov.dwp.universal_credit.elements.disabled.amount", {2027: 100})


def test_rate_change_keys_by_bare_year():
    built = rate_change(WA, {2027: 500, 2028: 510.5})
    assert built == {WA: {"2027": 500.0, "2028": 510.5}}


def test_paths_with_enum_keys_and_brackets():
    with pytest.warns(ModelLimitedWarning):
        rate_change("gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG", {2027: 300})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DataLimitedWarning)
        warnings.simplefilter("ignore", ModelLimitedWarning)
        rate_change("gov.hmrc.minimum_wage.non_apprentice[1].amount", {2027: 12})


@pytest.mark.parametrize("bad", [{"2027-04-01": 1.0}, {"27": 1.0}, {}])
def test_rate_change_refuses_other_keys(bad):
    with pytest.raises(ValueError):
        rate_change(WA, bad)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "1"])
def test_rate_change_refuses_bad_values(bad):
    with pytest.raises((ValueError, TypeError)):
        rate_change(WA, {2027: bad})


@pytest.mark.parametrize("bad", ["universal_credit.work_allowance", "gov..x", "gov.x[a]"])
def test_rate_change_refuses_bad_path(bad):
    with pytest.raises(ValueError):
        rate_change(bad, {2027: 1})


def test_minimum_wage_warns_as_data_limited():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rate_change("gov.hmrc.minimum_wage.non_apprentice[1].amount", {2027: 12.71})
    assert any(issubclass(w.category, DataLimitedWarning) for w in caught)


def test_age_threshold_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DataLimitedWarning)
        threshold_change("gov.dwp.LHA.shared_accommodation_age_threshold", {2027: 25})


def test_merge_refuses_duplicates():
    a = rate_change(WA, {2027: 500})
    with pytest.raises(ValueError):
        merge(a, a)


def test_data_limits_live():
    keys = {limit.key for limit in data_limits.LIMITS}
    assert "minimum_wage_does_not_reach_pay" in keys
    assert {
        "has_ever_worked",
        "neet_status",
        "wca_outcome",
        "is_care_leaver",
        "is_apprentice",
    } <= set(data_limits.MISSING_INPUTS_BY_KEY)
    assert data_limits.limits_for_paths(["gov.hmrc.minimum_wage.apprentice"])
    assert not data_limits.limits_for_paths([WA])
    assert not data_limits.is_only_data_limited([])


def test_model_limits_cover_the_known_gaps():
    def keys(path):
        return [limit.key for limit in model_limits.limits_for_paths([path])]

    assert keys("gov.dwp.universal_credit.elements.disabled.amount") == ["health_element_shadowed"]
    assert keys(WA) == ["no_age_dimension_in_uc_means_test"]
    # Fixed in policyengine-uk 2.174.1 and still on 2.177.7 (#1): no model limit on either.
    assert keys("gov.hmrc.minimum_wage.non_apprentice[1].amount") == []
    assert (
        keys("gov.hmrc.national_insurance.class_1.secondary_zero_rate_age_limits.under_21_group")
        == []
    )
    assert model_limits.limits_for_paths(
        [model_limits.variable_path("uc_limited_capability_for_WRA")]
    )
