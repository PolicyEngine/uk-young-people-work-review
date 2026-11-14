import pytest

from young_people_work.household import (
    CURVE_HOURS,
    PRESETS,
    PRESETS_BY_ID,
    annual_earnings,
    net_income_curve,
    to_situation,
    uc_monthly,
)

SA = "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG"


def test_six_presets_with_unique_ids():
    assert len(PRESETS) == 6
    assert len(PRESETS_BY_ID) == 6


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p["id"])
def test_situation_shape(preset):
    situation = to_situation(preset, 2027)
    names = list(situation["people"])
    assert names[0] == "young_person"
    assert situation["benunits"]["benunit"]["members"] == names
    assert situation["households"]["household"]["members"] == names
    young = situation["people"]["young_person"]
    assert young["age"] == {"2027": preset["age"]}


def test_uc_fit_for_work_is_the_standard_allowance():
    assert uc_monthly(PRESETS_BY_ID["single_20_looking_for_work"]) == pytest.approx(353.17)


def test_uc_health_element_adds_217_26():
    assert uc_monthly(PRESETS_BY_ID["single_20_new_health_element"]) == pytest.approx(570.43)


def test_uc_part_time_tapered_without_work_allowance():
    # 10 h x £11.27 x 52 / 12 = £488.37 a month; no work allowance without
    # LCWRA or children: 353.17 - 0.55 x 488.37 = £84.57.
    preset = PRESETS_BY_ID["age_19_part_time"]
    assert annual_earnings(preset) == pytest.approx(5_860.40)
    assert uc_monthly(preset) == pytest.approx(84.57, abs=0.01)


def test_uc_follows_youth_rate():
    preset = PRESETS_BY_ID["single_20_looking_for_work"]
    assert uc_monthly(preset, {SA: 317.85}) == pytest.approx(317.85)


def test_full_model_presets_carry_no_arithmetic():
    for preset in PRESETS:
        if preset["full_model_only"]:
            assert uc_monthly(preset) is None


def test_net_income_curve_rises_with_hours():
    rows = net_income_curve(PRESETS_BY_ID["single_20_looking_for_work"])
    assert [r["hours"] for r in rows] == CURVE_HOURS
    nets = [r["net_monthly"] for r in rows]
    assert nets == sorted(nets)


def test_cli_household_defaults_to_the_first_policy_year():
    from young_people_work.household import calculate

    assert calculate.__defaults__[-1] == 2027


def test_household_row_becomes_a_preset():
    from young_people_work.household import row_to_preset

    preset, year = row_to_preset(
        {"id": "h1", "age": "21", "lcwra": "yes", "new_claimant": "true", "year": "2028"}
    )
    assert (preset["age"], preset["lcwra"], preset["new_claimant"], year) == (21, True, True, 2028)
    with pytest.raises(ValueError, match="Unknown"):
        row_to_preset({"id": "h2", "age": "20", "colour": "red"})


def test_lcwra_presets_say_which_rate_they_get():
    situation = to_situation(PRESETS_BY_ID["single_20_new_health_element"], 2027)
    assert situation["benunits"]["benunit"]["uc_receives_new_claimant_health_element"] == {
        "2027": True
    }


def test_sketch_applies_the_health_element_age_test():
    preset = PRESETS_BY_ID["single_20_new_health_element"]
    assert uc_monthly(preset, health_min_age=22) == pytest.approx(353.17)


def _installed(monkeypatch, version):
    from young_people_work import runtime_identity

    monkeypatch.setattr(
        runtime_identity,
        "installed_versions",
        lambda: {"policyengine_uk": version, "policyengine_core": None},
    )


def test_household_path_refuses_another_engine(monkeypatch, tmp_path):
    # REVIEW2 Y2: the household path checks the engine as model mode does,
    # before any simulation or input row.
    from young_people_work import household
    from young_people_work.data_build import DATA_BUILD

    _installed(monkeypatch, "2.174.1")
    with pytest.raises(RuntimeError, match=DATA_BUILD.engine):
        household.simulate({"people": {}})
    with pytest.raises(RuntimeError, match="Never mix"):
        household.score_households(tmp_path / "absent.csv", [], None)


def test_household_engine_check_accepts_the_build_engine(monkeypatch):
    from young_people_work import runtime_identity
    from young_people_work.data_build import DATA_BUILD

    _installed(monkeypatch, DATA_BUILD.engine)
    assert runtime_identity.require_build_engine() == DATA_BUILD.engine
