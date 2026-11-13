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


def test_penny_rounds_half_up_in_exact_decimal():
    from young_people_work.household import _penny

    # f"{100.005:.2f}" gives 100.00: the binary float sits just below the tie.
    assert f"{100.005:.2f}" == "100.00"
    assert _penny(100.005) == 100.01
    assert _penny(200.015) == 200.02
    assert _penny(-0.005) == -0.01


def test_monthly_amount_survives_float32_annual():
    import struct

    from young_people_work.household import _monthly

    # The engine holds £2,400.18 a year as float32 (2,400.1799...): one
    # twelfth is a half-penny tie (200.015) that must round up, not down.
    as_float32 = struct.unpack("f", struct.pack("f", 2400.18))[0]
    assert f"{as_float32 / 12:.2f}" == "200.01"
    assert _monthly(as_float32) == 200.02


def test_annual_changes_from_rounded_monthly_amounts():
    from young_people_work.household import _annual_change

    # 12 x (310.27 - 200.13) is 1321.6799... in binary floats.
    assert _annual_change(310.27, 200.13) == 1321.68
    assert _annual_change(0.0, 100.01) == -1200.12


def test_household_row_takes_a_tenure():
    from young_people_work.household import row_to_preset

    preset, _ = row_to_preset(
        {"id": "h1", "age": "23", "monthly_rent": "400", "tenure_type": "rent_from_council"}
    )
    situation = to_situation(preset, 2028)
    assert situation["households"]["household"]["tenure_type"] == {"2028": "RENT_FROM_COUNCIL"}
    default, _ = row_to_preset({"id": "h2", "age": "23", "monthly_rent": "400"})
    assert to_situation(default, 2028)["households"]["household"]["tenure_type"] == {
        "2028": "RENT_PRIVATELY"
    }
    with pytest.raises(ValueError, match="tenure_type"):
        row_to_preset({"id": "h3", "age": "23", "tenure_type": "council"})
