"""Generate ``data/results.json``, the one file the page reads.

Two modes:
- ``placeholder`` (the only mode in this template): writes the full schema
  with illustrative figures for the computable measures, ``null`` for every
  measure that is not computable, ``status: "placeholder"`` and the banner
  text. No data are loaded and no simulation is built. The sign of each
  placeholder follows ``data_inputs/expected_effects.csv``; the sizes are
  seeded random numbers of the right shape, not estimates.
- ``model``: wired on the day. It will run each publishable measure through
  ``policyengine.tax_benefit_models.uk.managed_microsimulation`` on the
  frozen dataset. It is not implemented in the template and raises.

Basis, declared once (``BASIS``): static, cash, fiscal year, UK unless a
measure says otherwise, £m, positive is a cost to the Exchequer.
"""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from young_people_work import data_limits, model_limits, publication
from young_people_work.household import PRESETS, net_income_curve, uc_monthly
from young_people_work.reforms import REFORMS
from young_people_work.years import BASE_YEAR, POLICY_YEARS, fiscal_label

SCHEMA_VERSION = 1
BANNER = "Pre-release template: placeholder figures, not PolicyEngine estimates"

BASIS = {
    "cost": "Static, cash, fiscal year, UK unless a measure says otherwise, £ million; positive is a cost to the Exchequer",
    "distribution": "Average change in household net income by equivalised household income decile, UK",
    "age_band": "Average change in net income of the young person's benefit unit, by the age of its oldest adult",
    "behaviour": "No behavioural response: no change in hours, hiring, education or claims",
}

ENGINE = {
    "policyengine": "6.11.1",
    "policyengine_uk": "2.151.0",
    "dataset": "microcosm-uk-2024-25-national-20261025T091414Z-a6299504",
    "validated_pair": False,
}

AGE_BANDS = ["16-17", "18-20", "21-24", "25 and over"]
CURVE_PRESETS = ["single_20_looking_for_work", "single_20_new_health_element"]

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL = REPO_ROOT / "data_inputs" / "official"
EXPECTED_EFFECTS = REPO_ROOT / "data_inputs" / "expected_effects.csv"


def _rng(measure_id: str) -> np.random.Generator:
    seed = int(hashlib.sha256(measure_id.encode()).hexdigest()[:8], 16)
    return np.random.default_rng(seed)


def _expected_signs() -> dict[str, int]:
    with EXPECTED_EFFECTS.open() as handle:
        return {
            row["measure_id"]: -1 if row["expected_direction"] == "saving" else 1
            for row in csv.DictReader(handle)
        }


def _placeholder_figures(measure_id: str, sign: int) -> dict[str, Any]:
    """Illustrative numbers of the right shape and sign. Not estimates."""
    rng = _rng(measure_id)
    scale = float(rng.uniform(100, 900))
    budgetary = [
        {
            "year": year,
            "fiscal_year": fiscal_label(year),
            "value_m": round(sign * scale * (1 + 0.04 * i), 0),
        }
        for i, year in enumerate(POLICY_YEARS)
    ]
    shape = np.array([1.0, 1.1, 0.9, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
    decile = [
        {
            "decile": d + 1,
            "avg_change_gbp": round(float(sign * shape[d] * rng.uniform(20, 60)), 0),
            "pct_change": round(float(sign * shape[d] * rng.uniform(0.05, 0.3)), 2),
        }
        for d in range(10)
    ]
    gain_key, small_gain_key = ("gain_more_5", "gain_less_5") if sign > 0 else ("lose_more_5", "lose_less_5")
    winners_losers = []
    for d in range(10):
        row = {"decile": d + 1, "gain_more_5": 0.0, "gain_less_5": 0.0, "no_change": 0.0, "lose_less_5": 0.0, "lose_more_5": 0.0}
        row[gain_key] = round(float(shape[d] * rng.uniform(0, 5)), 1)
        row[small_gain_key] = round(float(shape[d] * rng.uniform(2, 10)), 1)
        row["no_change"] = round(100 - row[gain_key] - row[small_gain_key], 1)
        winners_losers.append(row)
    band_shape = {"16-17": 0.2, "18-20": 1.0, "21-24": 0.8, "25 and over": 0.05}
    age_band = [
        {"age_band": band, "avg_change_gbp": round(float(sign * band_shape[band] * rng.uniform(100, 400)), 0)}
        for band in AGE_BANDS
    ]
    return {
        "budgetary_impact": budgetary,
        "decile": decile,
        "winners_losers": winners_losers,
        "age_band": age_band,
        "people_affected_k": round(scale * 0.6, 0),
    }


def _read_csv(name: str) -> list[dict[str, str]]:
    with (OFFICIAL / name).open() as handle:
        return list(csv.DictReader(handle))


def _number(text: str) -> float | None:
    return float(text) if text.strip() else None


def _context() -> dict[str, Any]:
    """Official figures shown once, on the Baseline tab."""
    return {
        "young_claimants": [
            {
                "year": int(row["year"]),
                "fiscal_year": row["fiscal_year"],
                "uc_health_caseload_k": _number(row["uc_health_caseload_k"]),
                "uc_health_spend_m": _number(row["uc_health_spend_m"]),
                "pip_caseload_k": _number(row["pip_caseload_k"]),
                "pip_spend_m": _number(row["pip_spend_m"]),
            }
            for row in _read_csv("interim_annex_table28.csv")
        ],
        "young_claimants_source": "Interim report, analytical annex Table 28; England and Wales, ages 16-24",
        "neet": [
            {"period": row["period"], "neet_k": _number(row["neet_k"]), "neet_rate_pct": _number(row["neet_rate_pct"])}
            for row in _read_csv("ons_neet_16_24.csv")
        ],
        "neet_source": "ONS, young people not in education, employment or training, August 2026; UK, ages 16-24",
    }


def _measure_values(reform) -> dict[str, float]:
    return {
        path: values[str(POLICY_YEARS[0])]
        for path, values in (reform.parameter_changes or {}).items()
    }


def build_placeholder_results() -> dict[str, Any]:
    signs = _expected_signs()
    measures = []
    for reform in REFORMS:
        entry = reform.summary()
        entry["status"] = publication.status_of(reform)
        entry["receipt"] = publication.receipt(reform)
        if reform.computable:
            entry.update(_placeholder_figures(reform.id, signs.get(reform.id, 1)))
        else:
            entry.update({field: None for field in publication.FIGURE_FIELDS})
        measures.append(entry)

    computable = [r for r in REFORMS if r.computable]
    values_by_measure = {r.id: _measure_values(r) for r in computable}
    households = [
        {
            "id": preset["id"],
            "label": preset["label"],
            "full_model_only": preset["full_model_only"],
            "baseline_uc_monthly": uc_monthly(preset),
            "reform_uc_monthly": {mid: uc_monthly(preset, values) for mid, values in values_by_measure.items()},
        }
        for preset in PRESETS
    ]
    curves = []
    for preset_id in CURVE_PRESETS:
        preset = next(p for p in PRESETS if p["id"] == preset_id)
        rows = [{"hours": r["hours"], "baseline": r["net_monthly"]} for r in net_income_curve(preset)]
        for mid, values in values_by_measure.items():
            for row, reformed in zip(rows, net_income_curve(preset, values)):
                row[mid] = reformed["net_monthly"]
        curves.append({"preset": preset_id, "label": preset["label"], "hourly_wage": preset["hourly_wage"], "rows": rows})

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "placeholder",
        "banner": BANNER,
        "engine": ENGINE,
        "basis": BASIS,
        "base_year": BASE_YEAR,
        "years": POLICY_YEARS,
        "age_bands": AGE_BANDS,
        "measures": measures,
        "context": _context(),
        "households": households,
        "net_income_curves": curves,
        "data_limits": [
            {"key": limit.key, "missing_input": limit.missing_input, "reason": limit.reason, "issue": limit.issue}
            for limit in data_limits.LIMITS
        ]
        + [
            {"key": key, "missing_input": key, "reason": reason, "issue": None}
            for key, reason in data_limits.MISSING_INPUTS.items()
        ],
        "model_limits": [
            {"key": limit.key, "reason": limit.reason, "issue": limit.issue}
            for limit in model_limits.LIMITS
        ],
    }


def build_model_results() -> dict[str, Any]:
    raise NotImplementedError(
        "Model mode is wired on the day: freeze the engine and data pair (G0), "
        "take the heavy-run lock, and run each publishable measure through "
        "managed_microsimulation."
    )


def write_results(results: dict[str, Any], *paths: Path) -> None:
    errors = publication.validate_public(results)
    if errors:
        raise ValueError("Results fail the publication check:\n" + "\n".join(errors))
    text = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
