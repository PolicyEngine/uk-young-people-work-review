"""Checks against the installed engine (the ``model`` extra; skipped without it).

CI runs these in the model job. Single households only: no survey data.
"""

import pytest

pytest.importorskip("policyengine_uk")

from policyengine_core.parameters import Parameter  # noqa: E402
from policyengine_uk import Simulation  # noqa: E402
from policyengine_uk.scenarios import uc_reform  # noqa: E402
from policyengine_uk.system import system  # noqa: E402

from young_people_work import measure_templates, runtime_identity  # noqa: E402
from young_people_work.household import calculate, compare  # noqa: E402
from young_people_work.measure_templates import (  # noqa: E402
    UC_LCWRA_AMOUNT,
    UC_REBALANCING_ACTIVE,
    rate_change,
)
from young_people_work.reforms import (  # noqa: E402
    CURRENT_VALUES,
    NATIONAL_LIVING_WAGE,
    PROTECTED_HEALTH_ELEMENT,
    REFORMS,
    get_reform,
)
from young_people_work.years import POLICY_YEARS  # noqa: E402

Y = POLICY_YEARS[0]


def test_installed_engine_is_the_pin():
    versions = runtime_identity.installed_versions()
    pinned = runtime_identity.PINNED
    for key in ("policyengine", "policyengine_uk", "policyengine_core"):
        assert versions[key] == pinned[key]


def test_rebalanced_years_match_the_engine():
    assert list(measure_templates.UC_REBALANCED_YEARS) == list(uc_reform.REBALANCING_YEARS)
    assert measure_templates.UC_REBALANCED_YEARS_PINNED == uc_reform.REBALANCING_YEARS


@pytest.mark.parametrize("path", sorted(CURRENT_VALUES))
def test_current_values_match_the_engine(path):
    value = system.parameters.get_child(path)(f"{Y}-04-30")
    assert value == pytest.approx(CURRENT_VALUES[path], abs=0.005)


def test_national_living_wage_path_matches_the_engine():
    p = system.parameters.gov.hmrc.minimum_wage.non_apprentice.brackets[2].amount
    for year, value in NATIONAL_LIVING_WAGE.items():
        assert p(f"{year}-04-30") == pytest.approx(value)


def test_protected_health_element_path_matches_the_engine():
    sim = Simulation(
        situation={
            "people": {"a": {"age": {Y: 40}}},
            "benunits": {"b": {"members": ["a"]}},
            "households": {"h": {"members": ["a"]}},
        }
    )
    # One comparison over every year, so a failure prints the whole path.
    engine = {
        year: float(uc_reform._protected_existing_health_element_monthly(sim, year))
        for year in PROTECTED_HEALTH_ELEMENT
    }
    assert engine == pytest.approx(PROTECTED_HEALTH_ELEMENT, abs=1e-6)


@pytest.mark.parametrize("reform", [r for r in REFORMS if r.parameter_changes], ids=lambda r: r.id)
def test_every_parameter_path_resolves(reform):
    for path in reform.parameter_changes:
        assert isinstance(system.parameters.get_child(path), Parameter), path


def test_health_element_amount_and_switch_are_refused():
    with pytest.raises(ValueError, match="scores nothing"):
        rate_change(UC_LCWRA_AMOUNT, {Y: 100})
    with pytest.raises(ValueError, match="not the law"):
        rate_change(UC_REBALANCING_ACTIVE, {Y: 0})


def _claimant(age, new_claimant, year=Y):
    return {
        "people": {
            "a": {
                "age": {year: age},
                "employment_income": {year: 0},
                "uc_limited_capability_for_WRA": {year: True},
            }
        },
        "benunits": {
            "b": {
                "members": ["a"],
                "would_claim_uc": {year: True},
                "uc_receives_new_claimant_health_element": {year: new_claimant},
            }
        },
        "households": {"h": {"members": ["a"], "rent": {year: 6000}, "region": {year: "LONDON"}}},
    }


@pytest.mark.parametrize(
    ("age", "new", "changes"),
    [(21, True, True), (21, False, False), (22, True, False)],
)
def test_health_element_age_test_reaches_the_stored_award(age, new, changes):
    out = compare(_claimant(age, new), get_reform("health_element_under_22"), Y)
    assert (out["uc_monthly_change"] != 0) is changes
    if changes:
        assert out["uc_monthly_change"] == pytest.approx(-217.26)


def test_upper_bound_gates_protected_claimants_too():
    reform = get_reform("health_element_under_22")
    upper = reform.model_copy(update={"simulation_modifier": reform.upper_bound_modifier})
    out = compare(_claimant(21, False), upper, Y)
    assert out["uc_monthly_change"] == pytest.approx(-442.10, abs=0.01)


def test_youth_standard_allowance_leaves_older_protected_claimants_alone():
    for year in (2027, 2030):
        out = compare(_claimant(40, False, year), get_reform("youth_standard_allowance"), year)
        assert out["uc_monthly_change"] == 0


def test_one_preset_household_from_the_full_model():
    out = calculate("single_20_looking_for_work")
    assert out["uc_monthly"] == pytest.approx(
        CURRENT_VALUES["gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG"]
    )


def test_stored_pip_points_carry_forward_and_follow_the_thresholds():
    # Build 9e18f010 stores 2024 PIP points and no category: the category in
    # a scored year is derived from those points against that year's
    # thresholds, so a threshold change moves the award.
    from young_people_work import data_limits

    situation = {
        "people": {"p": {"age": {2024: 30}, "pip_dl_points": {2024: 9}}},
        "benunits": {"b": {"members": ["p"]}},
        "households": {"h": {"members": ["p"]}},
    }
    base = Simulation(situation=situation)
    assert str(base.calculate("pip_dl_category", Y)[0]) == "STANDARD"
    higher = Simulation(
        situation=situation,
        reform={"gov.dwp.pip.daily_living.points_thresholds.standard": {f"{Y}-01-01": 10}},
    )
    assert str(higher.calculate("pip_dl_category", Y)[0]) == "NONE"
    assert not data_limits.limits_for_paths(["gov.dwp.pip.daily_living.points_thresholds"])
