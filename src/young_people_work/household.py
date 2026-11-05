"""Household calculator: presets and the situation each one builds.

The calculator runs locally (``young-people-work household``) or in the page
from precomputed presets. Nothing here deploys. ``calculate`` needs the
``model`` extra and builds a single-household simulation; it never loads
survey data.

The presets cover the cases coverage of the review is likely to turn on: a
young claimant expected to look for work, a new claimant in the health element
group, a young disabled renter, a young part-time worker, a young person in
training living with a parent, and a single renter on the shared
accommodation rate.

``uc_monthly`` and ``net_income_curve`` are arithmetic sketches used for the
template's placeholder cards and chart. They cover the standard allowance, the
health element, housing costs as given (no Local Housing Allowance cap), work
allowances, the taper, income tax and employee National Insurance. The real
calculator runs the full model (``calculate``).
"""

from typing import Any

from young_people_work.reforms import CURRENT_VALUES, SA, UC, WA
from young_people_work.years import BASE_YEAR

# Published April 2027 hourly rate for ages 18 to 20. The pinned engine holds
# £10.85 (issue #1); the arithmetic uses the published rate.
WAGE_18_20_2027 = 11.27
PERSONAL_ALLOWANCE = 12_570
BASIC_RATE = 0.20
EMPLOYEE_NI_RATE = 0.08
NI_PRIMARY_THRESHOLD = 12_570
CURVE_HOURS = [0, 5, 10, 15, 20, 25, 30, 35, 40]

PRESETS: list[dict[str, Any]] = [
    {
        "id": "single_20_looking_for_work",
        "label": "Single 20-year-old on UC, looking for work, living with a parent who pays the rent",
        "region": "NORTH_EAST",
        "age": 20,
        "weekly_hours": 0,
        "hourly_wage": WAGE_18_20_2027,
        "lcwra": False,
        "monthly_rent": 0,
        "full_model_only": False,
    },
    {
        "id": "single_20_new_health_element",
        "label": "Single 20-year-old on UC, new claimant in the health element group",
        "region": "NORTH_EAST",
        "age": 20,
        "weekly_hours": 0,
        "hourly_wage": WAGE_18_20_2027,
        "lcwra": True,
        "monthly_rent": 0,
        "full_model_only": False,
    },
    {
        "id": "age_22_health_element_pip_renting",
        "label": "22-year-old renting alone, in the health element group, with standard daily living PIP",
        "region": "WEST_MIDLANDS",
        "age": 22,
        "weekly_hours": 0,
        "hourly_wage": 13.21,
        "lcwra": True,
        "pip_dl_category": "STANDARD",
        "monthly_rent": 500,
        "full_model_only": False,
    },
    {
        "id": "age_19_part_time",
        "label": "19-year-old working 10 hours a week at the 18-20 minimum wage",
        "region": "YORKSHIRE",
        "age": 19,
        "weekly_hours": 10,
        "hourly_wage": WAGE_18_20_2027,
        "lcwra": False,
        "monthly_rent": 0,
        "full_model_only": False,
    },
    {
        "id": "age_20_training_with_lone_parent",
        "label": "20-year-old in approved training, living with a lone parent on UC",
        "region": "NORTH_WEST",
        "age": 20,
        "weekly_hours": 0,
        "hourly_wage": WAGE_18_20_2027,
        "lcwra": False,
        "monthly_rent": 650,
        "in_approved_training": True,
        "parent": {"age": 46, "employment_income": 15_000},
        "full_model_only": True,
    },
    {
        "id": "age_28_renting_shared_rate",
        "label": "28-year-old renting a room, on the shared accommodation rate",
        "region": "EAST_MIDLANDS",
        "age": 28,
        "weekly_hours": 0,
        "hourly_wage": 13.21,
        "lcwra": False,
        "monthly_rent": 600,
        "full_model_only": True,
    },
]

PRESETS_BY_ID = {preset["id"]: preset for preset in PRESETS}


def annual_earnings(preset: dict[str, Any], weekly_hours: float | None = None) -> float:
    hours = preset["weekly_hours"] if weekly_hours is None else weekly_hours
    return round(hours * preset["hourly_wage"] * 52, 2)


def to_situation(preset: dict[str, Any], year: int = BASE_YEAR) -> dict[str, Any]:
    """A policyengine-uk situation for one preset household."""
    period = str(year)
    young: dict[str, Any] = {
        "age": {period: preset["age"]},
        "employment_income": {period: annual_earnings(preset)},
        "hours_worked": {period: preset["weekly_hours"] * 52},
        "uc_limited_capability_for_WRA": {period: preset["lcwra"]},
        "pip_dl_category": {period: preset.get("pip_dl_category", "NONE")},
    }
    if preset.get("in_approved_training"):
        young["is_in_approved_training"] = {period: True}
    people = {"young_person": young}
    if "parent" in preset:
        people["parent"] = {
            "age": {period: preset["parent"]["age"]},
            "employment_income": {period: preset["parent"]["employment_income"]},
        }
    names = list(people)
    household: dict[str, Any] = {"members": names, "region": {period: preset["region"]}}
    if preset["monthly_rent"]:
        household["rent"] = {period: preset["monthly_rent"] * 12}
        household["tenure_type"] = {period: "RENT_PRIVATELY"}
    return {
        "people": people,
        "benunits": {
            "benunit": {"members": names, "would_claim_uc": {period: True}}
        },
        "households": {"household": household},
    }


def _value(values: dict[str, float], path: str) -> float:
    return values.get(path, CURRENT_VALUES[path])


def uc_monthly(
    preset: dict[str, Any],
    values: dict[str, float] | None = None,
    weekly_hours: float | None = None,
) -> float | None:
    """Monthly UC for a single young claimant (arithmetic sketch).

    ``None`` for presets that need the full model (a parent's benefit unit or
    the Local Housing Allowance), so the page never shows a made-up figure.
    """
    if preset["full_model_only"]:
        return None
    values = values or {}
    young = preset["age"] < 25
    award = _value(values, f"{SA}.SINGLE_YOUNG" if young else f"{SA}.SINGLE_OLD")
    if preset["lcwra"]:
        award += _value(values, f"{UC}.elements.disabled.amount")
    award += preset["monthly_rent"]
    work_allowance = 0.0
    if preset["lcwra"]:
        work_allowance = _value(
            values, f"{WA}.with_housing" if preset["monthly_rent"] else f"{WA}.without_housing"
        )
    earned = annual_earnings(preset, weekly_hours) / 12
    taper = _value(values, f"{UC}.means_test.reduction_rate")
    award -= taper * max(0.0, earned - work_allowance)
    return round(max(0.0, award), 2)


def _tax_and_ni(earnings: float) -> float:
    tax = BASIC_RATE * max(0.0, earnings - PERSONAL_ALLOWANCE)
    ni = EMPLOYEE_NI_RATE * max(0.0, earnings - NI_PRIMARY_THRESHOLD)
    return tax + ni


def net_income_curve(
    preset: dict[str, Any], values: dict[str, float] | None = None
) -> list[dict[str, float]]:
    """Monthly net income (earnings after tax and NI, plus UC) by weekly hours."""
    rows = []
    for hours in CURVE_HOURS:
        earnings = annual_earnings(preset, hours)
        uc = uc_monthly(preset, values, hours) or 0.0
        net = (earnings - _tax_and_ni(earnings)) / 12 + uc
        rows.append({"hours": hours, "net_monthly": round(net, 2)})
    return rows


def calculate(preset_id: str, reform=None, year: int = BASE_YEAR) -> dict[str, float]:
    """Net income and UC for one preset under current law or a reform.

    Needs the ``model`` extra. Builds one household, not a survey simulation.
    """
    from policyengine_uk import Simulation

    situation = to_situation(PRESETS_BY_ID[preset_id], year)
    scenario = None if reform is None else reform.to_scenario()
    simulation = Simulation(situation=situation, scenario=scenario)
    return {
        "household_net_income": float(
            simulation.calculate("household_net_income", year).sum()
        ),
        "universal_credit": float(simulation.calculate("universal_credit", year).sum()),
    }
