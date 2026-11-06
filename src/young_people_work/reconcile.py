"""G3 reconciliation: model figures against the report's or official costings.

Input: a CSV with ``measure_id``, ``year`` (the fiscal year's first calendar
year, as in results.json), ``value_m`` (£ million, positive is a cost to the
Exchequer), ``basis`` (what the official figure covers) and an optional
``reason``. Output: one row per official figure with the model value, the gap
and the gap as a share of the official figure. A gap over the tolerance (10%)
needs a reason; ``young-people-work reconcile`` exits non-zero until every
such gap has one. A measure that is not computable is listed with no model
value and needs no reason: it is published as the official figure only.

Scaled down from the AB2026 dashboard's ``publication/reconcile.py``.
"""

from typing import Any


def _model_value(results: dict[str, Any], measure_id: str, year: int) -> float | None:
    if measure_id == "package":
        source = results.get("package") or {}
    else:
        source = next((m for m in results.get("measures", []) if m.get("id") == measure_id), None)
        if source is None:
            raise KeyError(f"No measure {measure_id!r} in the results file")
    for cell in source.get("budgetary_impact") or []:
        if int(cell["year"]) == int(year):
            return cell["value_m"]
    return None


def reconcile(
    results: dict[str, Any], official: list[dict[str, str]], tolerance: float = 0.10
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for line in official:
        measure_id = line["measure_id"].strip()
        year = int(line["year"])
        value = float(line["value_m"])
        reason = (line.get("reason") or "").strip()
        model = _model_value(results, measure_id, year)
        gap = None if model is None else model - value
        gap_pct = None if gap is None or value == 0 else 100 * gap / abs(value)
        over = gap is not None and (
            (value == 0 and gap != 0) or (gap_pct is not None and abs(gap_pct) > 100 * tolerance)
        )
        if over and not reason:
            failures.append(
                f"{measure_id} {year}: gap {gap_pct if gap_pct is not None else 'n/a'}% needs a reason"
            )
        rows.append(
            {
                "measure_id": measure_id,
                "year": year,
                "basis": line.get("basis", ""),
                "official_value_m": value,
                "model_value_m": model,
                "gap_m": None if gap is None else round(gap, 1),
                "gap_pct": None if gap_pct is None else round(gap_pct, 1),
                "over_tolerance": over,
                "reason": reason,
            }
        )
    return rows, failures
