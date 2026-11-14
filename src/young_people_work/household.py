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

``uc_monthly`` and ``net_income_curve`` are arithmetic sketches used only for
the template's placeholder cards and chart. They cover the standard
allowance, the health element (the new-claimant rate, as every LCWRA preset
is a new claimant), housing costs as given (no Local Housing Allowance cap),
work allowances, the taper, income tax and employee National Insurance. Model
mode replaces them with the full model (``calculate`` and
``precompute_presets``), and a model-mode results file never carries them.

Scoring basis (the drill's): monthly Universal Credit rounded to the penny
once, at the end, half up in exact decimal; the annual change in net income
from the rounded monthly amounts. The annual change in Universal Credit, from
the rounded monthly Universal Credit, is written alongside it, because the two
differ by pence when earnings carry unrounded tax and National Insurance:
the drill sheet must say which one it scores.
"""

import csv
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from young_people_work.reforms import CURRENT_VALUES, SA, UC, WA
from young_people_work.years import POLICY_YEARS

# Published April 2027 hourly rate for ages 18 to 20, as the pinned engine
# (policyengine-uk 2.174.1) holds it.
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
        "new_claimant": True,
        "monthly_rent": 0,
        "full_model_only": False,
    },
    {
        "id": "age_22_health_element_pip_renting",
        "label": "22-year-old renting alone, new claimant in the health element group, with standard daily living PIP",
        "region": "WEST_MIDLANDS",
        "age": 22,
        "weekly_hours": 0,
        "hourly_wage": 13.21,
        "lcwra": True,
        "new_claimant": True,
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


def to_situation(preset: dict[str, Any], year: int = POLICY_YEARS[0]) -> dict[str, Any]:
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
        household["tenure_type"] = {period: preset.get("tenure_type") or "RENT_PRIVATELY"}
    # A hand-built household claims UC unless the row says it is not received:
    # would_claim_uc defaults to true in policyengine-uk.
    benunit: dict[str, Any] = {
        "members": names,
        "would_claim_uc": {period: bool(preset.get("claims_uc", True))},
    }
    if preset.get("lcwra"):
        # A household situation without this flag gets the protected rate
        # (the engine's default); say which the preset is.
        benunit["uc_receives_new_claimant_health_element"] = {
            period: bool(preset.get("new_claimant", False))
        }
    return {
        "people": people,
        "benunits": {"benunit": benunit},
        "households": {"household": household},
    }


def _value(values: dict[str, float], path: str) -> float:
    return values.get(path, CURRENT_VALUES[path])


def uc_monthly(
    preset: dict[str, Any],
    values: dict[str, float] | None = None,
    weekly_hours: float | None = None,
    health_min_age: int | None = None,
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
    gated = health_min_age is not None and preset["age"] < health_min_age
    if preset["lcwra"] and not gated:
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
    preset: dict[str, Any],
    values: dict[str, float] | None = None,
    health_min_age: int | None = None,
) -> list[dict[str, float]]:
    """Monthly net income (earnings after tax and NI, plus UC) by weekly hours."""
    rows = []
    for hours in CURVE_HOURS:
        earnings = annual_earnings(preset, hours)
        uc = uc_monthly(preset, values, hours, health_min_age) or 0.0
        net = (earnings - _tax_and_ni(earnings)) / 12 + uc
        rows.append({"hours": hours, "net_monthly": round(net, 2)})
    return rows


PENNY = Decimal("0.01")


def _penny(value: float | Decimal) -> float:
    """Round to the penny, half up, in exact decimal.

    ``f"{value:.2f}"`` rounds the binary float, so a half-penny tie such as
    100.005 (held as 100.00499...) went down. Floats are read through their
    shortest repr first, so 100.005 is the decimal 100.005.
    """
    exact = value if isinstance(value, Decimal) else Decimal(repr(float(value)))
    return float(exact.quantize(PENNY, rounding=ROUND_HALF_UP))


def _monthly(annual: float) -> float:
    """An engine annual amount as a monthly amount on the scoring basis.

    The engine holds amounts as float32, which cannot carry pennies exactly
    (2,400.18 is held as 2,400.1799...). Only that float32 noise is removed,
    by reading the shortest decimal that round-trips the float32 (2,400.18;
    an annual amount off the penny, such as 2,400.175 from the taper, stays
    2,400.175). That is divided by 12 and rounded half up once, to the penny.
    """
    import numpy as np

    exact = Decimal(np.format_float_positional(np.float32(annual), unique=True))
    return _penny(exact / 12)


def _annual_change(after: float, before: float) -> float:
    """12 times the change in two rounded monthly amounts, in exact decimal."""
    return _penny(12 * (Decimal(repr(after)) - Decimal(repr(before))))


def simulate(
    situation: dict[str, Any], reform=None, year: int = POLICY_YEARS[0]
) -> dict[str, float]:
    """Monthly UC and monthly net income for one situation, from the full model.

    Needs the ``model`` extra. Builds one household, never a survey
    simulation. A reform's modifier runs with its own timing, as in model
    mode. Each amount is rounded to the penny once, here, at the end.
    """
    from policyengine_uk import Simulation

    scenario = None if reform is None else reform.to_scenario()
    kwargs = {} if scenario is None else {"scenario": scenario}
    simulation = Simulation(situation=situation, **kwargs)
    uc_annual = float(simulation.calculate("universal_credit", year).sum())
    net_annual = float(simulation.calculate("household_net_income", year).sum())
    return {"uc_monthly": _monthly(uc_annual), "net_income_monthly": _monthly(net_annual)}


def calculate(preset_id: str, reform=None, year: int = POLICY_YEARS[0]) -> dict[str, float]:
    """Monthly UC and net income for one preset under current law or a reform."""
    return simulate(to_situation(PRESETS_BY_ID[preset_id], year), reform, year)


def compare(situation: dict[str, Any], reform, year: int) -> dict[str, float]:
    """Baseline and reform for one situation, on the scoring basis."""
    base = simulate(situation, None, year)
    after = simulate(situation, reform, year)
    return {
        "baseline_uc_monthly": base["uc_monthly"],
        "reform_uc_monthly": after["uc_monthly"],
        "uc_monthly_change": _penny(
            Decimal(repr(after["uc_monthly"])) - Decimal(repr(base["uc_monthly"]))
        ),
        "baseline_net_income_monthly": base["net_income_monthly"],
        "reform_net_income_monthly": after["net_income_monthly"],
        # From the rounded monthly amounts, as the scoring sheet asks. Both
        # annual changes are written; the drill sheet names the one it scores.
        "annual_uc_change": _annual_change(after["uc_monthly"], base["uc_monthly"]),
        "annual_net_income_change": _annual_change(
            after["net_income_monthly"], base["net_income_monthly"]
        ),
    }


# Columns of a household input file (CSV or a JSON list of objects). Only id
# and age are required; the rest default as in the presets.
HOUSEHOLD_COLUMNS = (
    "id",
    "year",
    "age",
    "weekly_hours",
    "hourly_wage",
    "lcwra",
    "new_claimant",
    "pip_dl_category",
    "monthly_rent",
    "tenure_type",
    "region",
    "in_approved_training",
    "parent_age",
    "parent_employment_income",
    "uc_received",
)


# policyengine-uk TenureType values. Social rents (council or housing
# association) are not capped at the Local Housing Allowance; private rents are.
TENURE_TYPES = (
    "RENT_PRIVATELY",
    "RENT_FROM_COUNCIL",
    "RENT_FROM_HA",
    "OWNED_OUTRIGHT",
    "OWNED_WITH_MORTGAGE",
)


def _tenure(value: Any) -> str | None:
    """A tenure from an input row; blank means private renting, as the presets."""
    text = str(value or "").strip().upper()
    if not text:
        return None
    if text not in TENURE_TYPES:
        raise ValueError(f"Unknown tenure_type {text!r}: use one of {', '.join(TENURE_TYPES)}")
    return text


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "y")


# uc_received values. Blank means the household claims, as the presets do.
UC_RECEIVED = ("1", "true", "yes", "y", "received")
UC_NOT_RECEIVED = ("0", "false", "no", "n", "not received")


def _claims_uc(value: Any) -> bool:
    """Whether a row's household claims UC; blank means it does, as the presets."""
    text = str(value or "").strip().lower()
    if not text or text in UC_RECEIVED:
        return True
    if text in UC_NOT_RECEIVED:
        return False
    raise ValueError(
        f"Unknown uc_received {value!r}: leave blank or use one of "
        f"{', '.join(UC_RECEIVED + UC_NOT_RECEIVED)}"
    )


def row_to_preset(row: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """A household input row as a preset, and its year."""
    unknown = set(row) - set(HOUSEHOLD_COLUMNS)
    if unknown:
        raise ValueError(f"Unknown household columns: {', '.join(sorted(unknown))}")

    def number(key, default=0.0):
        text = str(row.get(key, "") or "").strip()
        return float(text) if text else default

    preset = {
        "id": str(row["id"]),
        "label": str(row["id"]),
        "region": str(row.get("region") or "NORTH_EAST"),
        "age": int(number("age")),
        "weekly_hours": number("weekly_hours"),
        "hourly_wage": number("hourly_wage"),
        "lcwra": _truthy(row.get("lcwra", "")),
        "new_claimant": _truthy(row.get("new_claimant", "")),
        "pip_dl_category": str(row.get("pip_dl_category") or "NONE"),
        "monthly_rent": number("monthly_rent"),
        "tenure_type": _tenure(row.get("tenure_type")),
        "in_approved_training": _truthy(row.get("in_approved_training", "")),
        "claims_uc": _claims_uc(row.get("uc_received")),
        "full_model_only": True,
    }
    if str(row.get("parent_age", "") or "").strip():
        preset["parent"] = {
            "age": int(number("parent_age")),
            "employment_income": number("parent_employment_income"),
        }
    year = int(number("year", POLICY_YEARS[0]))
    return preset, year


def read_households(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".json":
        return list(json.loads(path.read_text()))
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def score_households(path: Path, reforms: list, commit: str | None) -> list[dict[str, Any]]:
    """One output row per household and reform, on the scoring basis."""
    out = []
    for row in read_households(path):
        preset, year = row_to_preset(row)
        situation = to_situation(preset, year)
        for reform in reforms:
            out.append(
                {
                    "id": preset["id"],
                    "year": year,
                    "measure": reform.id,
                    **compare(situation, reform, year),
                    "commit": commit,
                }
            )
    return out


def precompute_presets(reforms: list, year: int = POLICY_YEARS[0]) -> list[dict[str, Any]]:
    """Every preset under current law and each reform, from the full model.

    A measure that does not change a preset is recorded as no change, so the
    page can say so rather than draw an identical line.
    """
    rows = []
    for preset in PRESETS:
        situation = to_situation(preset, year)
        base = simulate(situation, None, year)
        by_measure = {}
        for reform in reforms:
            after = simulate(situation, reform, year)
            by_measure[reform.id] = {
                "uc_monthly": after["uc_monthly"],
                "net_income_monthly": after["net_income_monthly"],
                "changed": after != base,
            }
        rows.append(
            {
                "id": preset["id"],
                "label": preset["label"],
                "full_model_only": False,
                "source": "model",
                "year": year,
                "baseline_uc_monthly": base["uc_monthly"],
                "baseline_net_income_monthly": base["net_income_monthly"],
                "reform_uc_monthly": {mid: r["uc_monthly"] for mid, r in by_measure.items()},
                "reform_net_income_monthly": {
                    mid: r["net_income_monthly"] for mid, r in by_measure.items()
                },
                "changed_by": sorted(mid for mid, r in by_measure.items() if r["changed"]),
            }
        )
    return rows
