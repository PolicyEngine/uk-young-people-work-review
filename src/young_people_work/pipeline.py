"""Generate ``data/results.json``, the one file the page reads.

Two modes:
- ``placeholder``: writes the full schema with illustrative figures for the
  computable measures, ``null`` for every measure that is not computable,
  ``status: "placeholder"`` and the banner text. No data are loaded and no
  simulation is built. The sign of each placeholder follows
  ``data_inputs/expected_effects.csv``; the sizes are seeded random numbers
  of the right shape, not estimates.
- ``model``: assembles the run files ``young-people-work model-run`` wrote
  (``young_people_work.model``: one measure per process, under the heavy-run
  lock, on the bundle's certified dataset), adds the package run, the
  household presets from the full model, receipts bound to the execution
  identity, and writes ``manifest.json`` next to ``results.json``. Status is
  ``provisional`` or, for a drill, ``mock`` (with the MOCK banner).

Basis, declared once (``BASIS``): static, cash, fiscal year, UK unless a
measure says otherwise, £m, positive is a cost to the Exchequer.
"""

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from young_people_work import data_limits, model_limits, publication, runtime_identity
from young_people_work.household import PRESETS, net_income_curve, uc_monthly
from young_people_work.reforms import REFORMS
from young_people_work.years import BASE_YEAR, POLICY_YEARS, fiscal_label

SCHEMA_VERSION = 1
BANNER = "Pre-release template: placeholder figures, not PolicyEngine estimates"
MOCK_BANNER = "MOCK: drill figures from an invented report, not PolicyEngine estimates"

BASIS = {
    "cost": "Static, cash, fiscal year, UK unless a measure says otherwise, £ million; positive is a cost to the Exchequer",
    "distribution": "Average change in household net income by equivalised household income decile, UK",
    "age_band": "Average change in household net income of people in each age band, by their own age",
    "behaviour": "No behavioural response: no change in hours, hiring, education or claims",
}

# The pinned strings (runtime_identity.PINNED, checked against uv.lock).
ENGINE = runtime_identity.engine_block()

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


def _placeholder_figures(measure_id: str, sign: int, bands_reached=None) -> dict[str, Any]:
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
    gain_key, small_gain_key = (
        ("gain_more_5", "gain_less_5") if sign > 0 else ("lose_more_5", "lose_less_5")
    )
    winners_losers = []
    for d in range(10):
        row = {
            "decile": d + 1,
            "gain_more_5": 0.0,
            "gain_less_5": 0.0,
            "no_change": 0.0,
            "lose_less_5": 0.0,
            "lose_more_5": 0.0,
        }
        row[gain_key] = round(float(shape[d] * rng.uniform(0, 5)), 1)
        row[small_gain_key] = round(float(shape[d] * rng.uniform(2, 10)), 1)
        row["no_change"] = round(100 - row[gain_key] - row[small_gain_key], 1)
        winners_losers.append(row)
    band_shape = {"16-17": 0.2, "18-20": 1.0, "21-24": 0.8, "25 and over": 0.05}
    if bands_reached is not None:
        band_shape = {band: (0.6 if band in bands_reached else 0.0) for band in AGE_BANDS}
    age_band = [
        {
            "age_band": band,
            "avg_change_gbp": round(float(sign * band_shape[band] * rng.uniform(100, 400)), 0),
        }
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
            {
                "period": row["period"],
                "neet_k": _number(row["neet_k"]),
                "neet_rate_pct": _number(row["neet_rate_pct"]),
            }
            for row in _read_csv("ons_neet_16_24.csv")
        ],
        "neet_source": "ONS, young people not in education, employment or training, May and August 2026 bulletins; UK, ages 16-24",
    }


# The household sketch's stand-in for the age-test modifiers.
SKETCH_HEALTH_MIN_AGE = {"health_element_under_22": 22, "health_element_under_25": 25}


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
            entry.update(
                _placeholder_figures(reform.id, signs.get(reform.id, 1), reform.age_bands_reached)
            )
        else:
            entry.update({field: None for field in publication.FIGURE_FIELDS})
        measures.append(entry)

    computable = [r for r in REFORMS if r.computable]
    values_by_measure = {r.id: _measure_values(r) for r in computable}
    min_ages = {r.id: SKETCH_HEALTH_MIN_AGE.get(r.id) for r in computable}
    households = []
    for preset in PRESETS:
        baseline = uc_monthly(preset)
        reformed = {
            mid: uc_monthly(preset, values, health_min_age=min_ages[mid])
            for mid, values in values_by_measure.items()
        }
        households.append(
            {
                "id": preset["id"],
                "label": preset["label"],
                "full_model_only": preset["full_model_only"],
                "source": "sketch",
                "year": POLICY_YEARS[0],
                "baseline_uc_monthly": baseline,
                "reform_uc_monthly": reformed,
                "changed_by": sorted(
                    mid
                    for mid, value in reformed.items()
                    if baseline is not None and value != baseline
                ),
            }
        )
    curves = []
    for preset_id in CURVE_PRESETS:
        preset = next(p for p in PRESETS if p["id"] == preset_id)
        rows = [
            {"hours": r["hours"], "baseline": r["net_monthly"]} for r in net_income_curve(preset)
        ]
        for mid, values in values_by_measure.items():
            for row, reformed in zip(rows, net_income_curve(preset, values, min_ages[mid])):
                row[mid] = reformed["net_monthly"]
        curves.append(
            {
                "preset": preset_id,
                "label": preset["label"],
                "hourly_wage": preset["hourly_wage"],
                "rows": rows,
            }
        )

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
        "package": None,
        "context": _context(),
        "households": households,
        "net_income_curves": curves,
        **_limits(),
    }


def _limits() -> dict[str, list[dict[str, Any]]]:
    return {
        "data_limits": [
            {
                "key": limit.key,
                "missing_input": limit.missing_input,
                "reason": limit.reason,
                "issue": limit.issue,
            }
            for limit in data_limits.LIMITS
        ]
        + [
            {"key": item.key, "missing_input": item.key, "reason": item.reason, "issue": item.issue}
            for item in data_limits.MISSING_INPUTS
        ],
        "model_limits": [
            {"key": limit.key, "reason": limit.reason, "issue": limit.issue}
            for limit in model_limits.LIMITS
        ],
    }


def build_model_results(
    runs_dir: Path,
    status: str = "provisional",
    households: list[dict[str, Any]] | None = None,
    curves: list[dict[str, Any]] | None = None,
    commit: str | None = None,
    reforms=None,
) -> dict[str, Any]:
    """Assemble model runs into results.json.

    Every computable measure needs a run file; a missing one fails rather
    than showing as £0. Receipts bind each definition to the execution
    identity: installed versions, dataset SHA-256, commit and limits digest.
    """
    from young_people_work import model

    if status not in ("provisional", "mock"):
        raise ValueError("Model mode writes status 'provisional' or 'mock'")
    reforms = list(REFORMS if reforms is None else reforms)
    runs = model.read_runs(runs_dir)
    missing = [r.id for r in reforms if r.computable and r.id not in runs]
    if missing:
        raise ValueError("No model run for: " + ", ".join(missing))
    engines = {json.dumps(run["identity"]["engine"], sort_keys=True) for run in runs.values()}
    if len(engines) != 1:
        raise ValueError("Runs come from different engines or datasets; rerun them on one G0 pair")
    engine = json.loads(engines.pop())
    identity = {
        "engine": engine,
        "commit": commit,
        "limits_sha256": runtime_identity.limits_digest(),
    }
    measures = []
    for reform in reforms:
        entry = reform.summary()
        entry["status"] = publication.status_of(reform)
        entry["receipt"] = publication.receipt(reform, identity)
        if reform.computable:
            entry.update(model.measure_figures(runs[reform.id]))
        else:
            entry.update({field: None for field in publication.FIGURE_FIELDS})
        measures.append(entry)
    package = None
    if "package" in runs:
        members = [r for r in reforms if r.computable and r.in_headline]
        package_def = model.package_reform(members)
        package = {
            "members": [r.id for r in members],
            "receipt": publication.receipt(package_def, identity),
            **model.measure_figures(runs["package"]),
        }
    results = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "banner": MOCK_BANNER if status == "mock" else "",
        "engine": engine,
        "basis": BASIS,
        "base_year": BASE_YEAR,
        "years": POLICY_YEARS,
        "age_bands": AGE_BANDS,
        "measures": measures,
        "package": package,
        "context": _context(),
        "households": households or [],
        "net_income_curves": curves or [],
        **_limits(),
    }
    return results


def write_manifest(results: dict[str, Any], path: Path, commit: str | None) -> None:
    """What may be published, and what produced it, next to results.json."""
    manifest = {
        "status": results["status"],
        "commit": commit,
        "engine": results["engine"],
        "limits_sha256": runtime_identity.limits_digest(),
        "measures": [
            {"id": m["id"], "status": m["status"], "receipt": m["receipt"]}
            for m in results["measures"]
        ],
        "package": None
        if not results.get("package")
        else {
            "members": results["package"]["members"],
            "receipt": results["package"]["receipt"],
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")


def write_results(results: dict[str, Any], *paths: Path) -> None:
    errors = publication.validate_public(results, allow_zero=True)
    if errors:
        raise ValueError("Results fail the publication check:\n" + "\n".join(errors))
    for warning in publication.zero_figure_problems(results):
        # Written so the run is kept; the guard and the page build refuse it.
        print(f"WARNING {warning}", file=sys.stderr)
    text = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
