"""Publication gate, scaled down from the AB2026 dashboard's ``publication`` package.

Kept: a manifest of what may be published, a receipt binding each measure's
definition, the disclosure floor and validation of the public results file.
Dropped: release index, area-code routing, attestations and responsiveness
(no constituency map in this template).
"""

import hashlib
import inspect
import json
import sys
from collections.abc import Iterable
from typing import Any

from young_people_work import sign_off
from young_people_work.models import Reform

# Fewest unweighted survey households behind any published cell.
DISCLOSURE_FLOOR = 10

# Figure fields a measure carries only when it is computable.
FIGURE_FIELDS = (
    "budgetary_impact",
    "decile",
    "winners_losers",
    "age_band",
    "people_affected_k",
)

# Results file statuses. "placeholder": the template's illustrative figures.
# "mock": a drill build from an invented packet; every view shows the MOCK
# banner and every mock measure id starts with MOCK_PREFIX. "provisional"
# and "final": model output on the day.
STATUSES = ("placeholder", "mock", "provisional", "final")
BANNER_STATUSES = ("placeholder", "mock")
MOCK_PREFIX = "mock_"

# Keys that must never appear in a public file: record identifiers and weights.
FORBIDDEN_KEYS = frozenset(
    {
        "household_id",
        "person_id",
        "benunit_id",
        "household_weight",
        "person_weight",
        "benunit_weight",
        "weight",
        "weights",
    }
)


def _callable_identity(function) -> dict[str, str] | None:
    """A modifier's name and the SHA-256 of its module's source."""
    if function is None:
        return None
    module = sys.modules.get(function.__module__)
    try:
        source = inspect.getsource(module) if module else ""
    except (OSError, TypeError):
        source = ""
    return {
        "name": f"{function.__module__}.{function.__qualname__}",
        "module_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }


def receipt(reform: Reform, identity: dict[str, Any] | None = None) -> str:
    """SHA-256 of a measure's definition and, in model mode, of what ran it.

    ``identity`` is the execution identity (installed versions, dataset
    SHA-256, git SHA, limits digest); placeholder files bind the definition
    only.
    """
    payload = {
        "summary": reform.summary(),
        "parameter_changes": reform.parameter_changes,
        "baseline_parameter_changes": reform.baseline_parameter_changes,
        "modifier": _callable_identity(reform.simulation_modifier),
        "upper_bound_modifier": _callable_identity(reform.upper_bound_modifier),
        "applied_before_data_load": reform.applied_before_data_load,
        "identity": identity,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode()).hexdigest()


def status_of(reform: Reform) -> str:
    """What the page may show for a measure."""
    if not reform.computable:
        return reform.route.value
    if reform.placeholder:
        return "held-placeholder"
    if sign_off.REQUIRED:
        return "held-sign-off"
    return "published"


def manifest(reforms: Iterable[Reform]) -> list[dict[str, Any]]:
    return [
        {
            "id": reform.id,
            "status": status_of(reform),
            "receipt": receipt(reform),
        }
        for reform in reforms
    ]


def apply_floor(
    rows: list[dict[str, Any]],
    value_keys: Iterable[str],
    count_key: str = "n_households",
) -> list[dict[str, Any]]:
    """Blank the values of any row with fewer survey households than the floor.

    The count itself is dropped from the output, so the public file does not
    carry record counts.
    """
    value_keys = list(value_keys)
    out = []
    for row in rows:
        row = dict(row)
        count = row.pop(count_key, None)
        if count is None or count < DISCLOSURE_FLOOR:
            for key in value_keys:
                row[key] = None
            row["suppressed"] = True
        out.append(row)
    return out


def _walk_keys(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key, f"{path}.{key}"
            yield from _walk_keys(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _walk_keys(inner, f"{path}[{index}]")


def validate_public(results: dict[str, Any], allow_zero: bool = False) -> list[str]:
    """Problems that block publishing the results file. Empty means it passes.

    ``allow_zero`` lets a model run write its file when a coded measure scores
    £0 everywhere (``zero_figure_problems`` then warns), so the run is not
    lost; the public-data guard and the page build still refuse it.
    """
    errors: list[str] = []
    for key, where in _walk_keys(results):
        if key.lower() in FORBIDDEN_KEYS:
            errors.append(f"{where}: record identifier or weight in a public file")
        if key == "n_households":
            errors.append(f"{where}: record counts are not published")
    measures = results.get("measures", [])
    status = results.get("status")
    if status not in STATUSES:
        errors.append(f"$.status: {status!r} is not one of {', '.join(STATUSES)}")
    any_placeholder = any(m.get("placeholder") for m in measures)
    if any_placeholder and status not in BANNER_STATUSES:
        errors.append("$.status: a placeholder measure needs status 'placeholder' or 'mock'")
    if status in BANNER_STATUSES and not results.get("banner"):
        errors.append(f"$.banner: {status} figures need the banner text")
    any_mock = any(str(m.get("id", "")).startswith(MOCK_PREFIX) for m in measures)
    if any_mock and status != "mock":
        errors.append("$.status: a mock_ measure needs status 'mock'")
    if status == "mock" and "MOCK" not in str(results.get("banner", "")):
        errors.append("$.banner: a mock file's banner must say MOCK")
    if status in ("provisional", "final") and not results.get("engine", {}).get("validated_pair"):
        errors.append(
            "$.engine.validated_pair: a public build needs the certified engine "
            "and data pair; an unvalidated run is never published"
        )
    for measure in measures:
        mid = measure.get("id", "?")
        if not measure.get("computable"):
            for field in FIGURE_FIELDS:
                if measure.get(field) is not None:
                    errors.append(
                        f"{mid}.{field}: a measure that is not computable carries "
                        "no figure (never £0)"
                    )
            if not measure.get("route_reason"):
                errors.append(f"{mid}: give the reason it is not computable")
    if not allow_zero:
        errors.extend(zero_figure_problems(results))
    return errors


def zero_figure_problems(results: dict[str, Any]) -> list[str]:
    """Coded measures whose national figure is £0m in every year, unexplained."""
    return [
        f"{measure.get('id', '?')}.budgetary_impact: a coded measure scores £0 in every "
        "year. If it acts only through inputs the data lack, route it not-computable "
        "with the reason; if zero is right, say why in zero_reason"
        for measure in results.get("measures", [])
        if measure.get("computable") and _scores_zero(measure) and not measure.get("zero_reason")
    ]


def _scores_zero(measure: dict[str, Any]) -> bool:
    """True when a coded measure's national figure rounds to £0m in every year.

    A parameter that acts only through an input the data lack (a flag that
    defaults to False, a benefit unit the survey never builds) scores exactly
    zero. Shown as a costing, that zero is wrong, not small.
    """
    rows = measure.get("budgetary_impact") or []
    values = [row.get("value_m") for row in rows if isinstance(row, dict)]
    values = [v for v in values if v is not None]
    return bool(values) and all(abs(v) < 0.5 for v in values)
