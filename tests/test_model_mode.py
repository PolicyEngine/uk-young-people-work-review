"""Model mode without data: a fake simulation exercises every code path."""

import json

import numpy as np
import pytest

from young_people_work import model, pipeline, publication
from young_people_work.reforms import REFORMS, get_reform

N_HOUSEHOLDS = 200
YEARS = [2027, 2028]


class FakeSimulation:
    """Two people per household; the reform adds £100 to the first half."""

    def __init__(self, scenario=None):
        self.reformed = scenario is not None
        rng = np.random.default_rng(1)
        self.income = rng.uniform(5_000, 60_000, N_HOUSEHOLDS)
        self.young_people_provenance = {
            "runtime_dataset_uri": "hf://fake/build.h5",
            "runtime_dataset_revision": "fake-build",
            "runtime_dataset_source": "/nonexistent/path.h5",
        }

    def calculate(self, name, year, map_to=None):
        h = N_HOUSEHOLDS
        change = np.where(np.arange(h) < h // 2, 100.0, 0.0) if self.reformed else np.zeros(h)
        household = {
            "gov_balance": -change,
            "household_net_income": self.income + change,
            "household_weight": np.full(h, 1_000.0),
            "household_income_decile": (np.arange(h) % 10) + 1,
            "household_count_people": np.full(h, 2),
            "region": np.array(["NORTH_EAST", "LONDON"] * (h // 2)),
            "household_id": np.arange(h),
            "in_poverty_bhc": self.income < 15_000,
            "in_poverty_ahc": self.income < 18_000,
        }
        if map_to == "household":
            return household[name]
        person_house = np.repeat(np.arange(h), 2)
        person = {
            "age": np.tile([20, 45], h),
            "person_weight": np.full(2 * h, 1_000.0),
            "person_household_id": person_house,
            "uc_work_related_group_apart_from_earnings": np.tile(
                ["ALL_REQUIREMENTS", "NOT_A_CLAIMANT"], h
            ),
            "is_adult": np.ones(2 * h, dtype=bool),
        }
        if name in person:
            return person[name]
        return household[name][person_house]


def fake_build(scenario=None):
    return FakeSimulation(scenario)


@pytest.fixture(autouse=True)
def no_engine_scenarios(monkeypatch):
    """Scenarios are opaque to the fake simulation, so CI needs no engine."""
    from young_people_work.models import Reform

    monkeypatch.setattr(Reform, "to_scenario", lambda self: ("reform", self.id))
    monkeypatch.setattr(
        Reform,
        "to_upper_bound_scenario",
        lambda self: None if self.upper_bound_modifier is None else ("upper", self.id),
    )


def test_run_scores_cost_deciles_and_age():
    out = model.run_measure(get_reform("youth_standard_allowance"), YEARS, build=fake_build)
    first = out["years"][0]
    # 100 households x £100 x weight 1,000 = £10m cost.
    assert first["budgetary_impact_m"] == pytest.approx(10.0)
    assert len(first["decile"]) == 10
    young = next(r for r in first["age_band"] if r["age_band"] == "18-20")
    assert young["avg_change_gbp"] == pytest.approx(50.0)
    assert {row["group"] for row in first["poverty"]} == {"all", "children", "aged_16_24"}
    assert (
        out["identity"]["engine"]["validated_pair"] is False
    )  # no file hash: never the pinned pair
    assert out["identity"]["engine"]["label"] is None


def test_upper_bound_runs_for_a_range_measure():
    out = model.run_measure(get_reform("health_element_under_22"), YEARS, build=fake_build)
    assert [row["year"] for row in out["upper"]] == YEARS


def test_figures_are_floored_and_counts_dropped():
    out = model.run_measure(get_reform("youth_standard_allowance"), YEARS, build=fake_build)
    out["years"][-1]["decile"][0]["n_households"] = 3
    figures = model.measure_figures(out)
    assert figures["decile"][0]["avg_change_gbp"] is None
    assert figures["decile"][0]["suppressed"] is True
    text = json.dumps(figures)
    assert "n_households" not in text


def test_package_merges_members_and_refuses_conflicts():
    members = [r for r in REFORMS if r.computable and r.in_headline]
    package = model.package_reform(members)
    assert package.applied_before_data_load is True
    assert set(package.parameter_changes) >= set(
        get_reform("youth_standard_allowance").parameter_changes
    )
    clash = get_reform("youth_standard_allowance").model_copy(
        update={
            "id": "clash",
            "parameter_changes": {
                "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG": {"2027": 1.0}
            },
        }
    )
    with pytest.raises(ValueError, match="set differently"):
        model.package_reform([get_reform("youth_standard_allowance"), clash])


def _write_runs(tmp_path):
    for reform in [r for r in REFORMS if r.computable]:
        model.write_run(
            model.run_measure(reform, YEARS, build=fake_build), tmp_path / f"{reform.id}.json"
        )
    members = [r for r in REFORMS if r.computable and r.in_headline]
    out = model.run_measure(model.package_reform(members), YEARS, build=fake_build)
    model.write_run(out, tmp_path / "package.json")


def test_model_results_assemble_and_pass_the_gate(tmp_path):
    _write_runs(tmp_path)
    results = pipeline.build_model_results(tmp_path, status="mock", commit="0" * 40)
    assert results["status"] == "mock"
    assert "MOCK" in results["banner"]
    assert results["package"]["members"]
    assert publication.validate_public(results) == []
    # Not certified, so it could never go out as provisional.
    results["status"] = "provisional"
    results["banner"] = ""
    assert any("validated_pair" in e for e in publication.validate_public(results))
    pipeline.write_manifest(results, tmp_path / "manifest.json", "0" * 40)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["commit"] == "0" * 40
    assert len(manifest["measures"]) == len(REFORMS)


def test_missing_run_fails_rather_than_showing_zero(tmp_path):
    with pytest.raises(ValueError, match="No model run"):
        pipeline.build_model_results(tmp_path, status="mock")


def test_receipt_binds_execution_identity():
    reform = get_reform("youth_standard_allowance")
    a = publication.receipt(reform, {"engine": {"dataset_sha256": "a"}})
    b = publication.receipt(reform, {"engine": {"dataset_sha256": "b"}})
    assert a != b != publication.receipt(reform)


OLD_ENGINE = {
    # A 6.17.2-era run: policyengine-uk 2.174.1 on build eeb6093e.
    "policyengine": "6.17.2",
    "policyengine_uk": "2.174.1",
    "policyengine_core": "3.34.10",
    "dataset": "microcosm-eeb6093e",
    "dataset_revision": "microcosm-eeb6093e",
    "dataset_sha256": "0a9b77db" + "0" * 56,
}


def _rewrite_engines(runs_dir, engine):
    for path in runs_dir.glob("*.json"):
        run = json.loads(path.read_text())
        run["identity"]["engine"] = engine
        path.write_text(json.dumps(run))


def test_stale_runs_claiming_a_validated_pair_are_refused(tmp_path):
    _write_runs(tmp_path)
    _rewrite_engines(tmp_path, {**OLD_ENGINE, "validated_pair": True, "label": "x"})
    with pytest.raises(ValueError, match="claim validated_pair"):
        pipeline.build_model_results(tmp_path, status="provisional", commit="0" * 40)


def test_stale_runs_are_marked_not_validated(tmp_path):
    _write_runs(tmp_path)
    _rewrite_engines(tmp_path, {**OLD_ENGINE, "validated_pair": False, "label": None})
    results = pipeline.build_model_results(tmp_path, status="provisional", commit="0" * 40)
    assert results["engine"]["validated_pair"] is False
    assert results["engine"]["label"] is None
    assert any("validated_pair" in e for e in publication.validate_public(results))


def test_runs_on_the_pinned_pair_are_validated(tmp_path):
    from young_people_work.data_build import DATA_BUILD, LABEL

    _write_runs(tmp_path)
    pinned = {
        "policyengine": None,
        "policyengine_uk": DATA_BUILD.engine,
        "policyengine_core": DATA_BUILD.core,
        "dataset": DATA_BUILD.id,
        "dataset_revision": None,
        "dataset_sha256": DATA_BUILD.sha256,
        "validated_pair": True,
        "label": LABEL,
    }
    _rewrite_engines(tmp_path, pinned)
    results = pipeline.build_model_results(tmp_path, status="mock", commit="0" * 40)
    assert results["engine"]["validated_pair"] is True
    assert results["engine"]["label"] == LABEL
