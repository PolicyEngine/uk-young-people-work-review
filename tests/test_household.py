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
