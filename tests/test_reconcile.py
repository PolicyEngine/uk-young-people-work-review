from young_people_work.pipeline import build_placeholder_results
from young_people_work.reconcile import reconcile


def test_gap_over_ten_percent_needs_a_reason():
    results = build_placeholder_results()
    measure = next(m for m in results["measures"] if m["computable"])
    model_value = measure["budgetary_impact"][0]["value_m"]
    official = [
        {
            "measure_id": measure["id"],
            "year": "2027",
            "value_m": str(model_value * 1.05),
            "basis": "test",
        },
        {
            "measure_id": measure["id"],
            "year": "2028",
            "value_m": str(model_value * 2),
            "basis": "test",
        },
        {
            "measure_id": measure["id"],
            "year": "2029",
            "value_m": str(model_value * 2),
            "basis": "test",
            "reason": "basis",
        },
        {
            "measure_id": "youth_guarantee",
            "year": "2027",
            "value_m": "500",
            "basis": "spending line",
        },
    ]
    rows, failures = reconcile(results, official)
    assert [r["over_tolerance"] for r in rows] == [False, True, True, False]
    assert len(failures) == 1 and "2028" in failures[0]
    assert rows[3]["model_value_m"] is None
