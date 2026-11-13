import re
import tomllib
from pathlib import Path

from young_people_work import runtime_identity
from young_people_work.data_build import DATA_BUILD, LABEL
from young_people_work.pipeline import ENGINE

ROOT = Path(__file__).resolve().parents[1]


def _locked(name):
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    return next(p["version"] for p in lock["package"] if p["name"] == name)


def test_pinned_strings_match_uv_lock():
    pinned = runtime_identity.PINNED
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    assert pinned["policyengine"] is None
    assert "policyengine" not in {p["name"] for p in lock["package"]}
    assert pinned["policyengine_uk"] == _locked("policyengine-uk") == DATA_BUILD.engine
    assert pinned["policyengine_core"] == _locked("policyengine-core") == DATA_BUILD.core
    assert pinned["dataset"] == DATA_BUILD.id
    assert pinned["dataset_sha256"] == DATA_BUILD.sha256
    assert ENGINE["policyengine_uk"] == pinned["policyengine_uk"]
    assert ENGINE["label"] == LABEL


def test_pyproject_pin_matches_uv_lock():
    text = (ROOT / "pyproject.toml").read_text()
    assert f"policyengine-uk=={_locked('policyengine-uk')}" in text
    assert f"policyengine-core=={_locked('policyengine-core')}" in text
    assert "policyengine[uk]" not in text


def test_readme_names_the_pinned_pair():
    readme = (ROOT / "README.md").read_text()
    for text in (_locked("policyengine-uk"), DATA_BUILD.id, LABEL):
        assert re.search(re.escape(text), readme), text


def test_label():
    assert LABEL == (
        f"build {DATA_BUILD.id}, policyengine-uk {DATA_BUILD.engine}, "
        "not in a policyengine.py release"
    )


def test_engine_block_validates_only_the_pinned_file_and_engine(monkeypatch):
    class Sim:
        young_people_provenance = {"runtime_dataset_sha256": DATA_BUILD.sha256}

    pinned_versions = {
        "policyengine": None,
        "policyengine_uk": DATA_BUILD.engine,
        "policyengine_core": DATA_BUILD.core,
    }
    monkeypatch.setattr(runtime_identity, "installed_versions", lambda: pinned_versions)
    block = runtime_identity.engine_block(Sim())
    assert block["validated_pair"] is True
    assert block["dataset"] == DATA_BUILD.id
    assert block["label"] == LABEL
    monkeypatch.setattr(
        runtime_identity,
        "installed_versions",
        lambda: {**pinned_versions, "policyengine_uk": "2.174.1"},
    )
    assert runtime_identity.engine_block(Sim())["validated_pair"] is False


def test_data_limits_hold_for_the_pinned_build():
    from young_people_work import data_limits

    keys = {limit.key for limit in data_limits.LIMITS}
    assert keys == set(data_limits.LIMITS_BY_BUILD[DATA_BUILD.short_id])


def test_limits_digest_is_stable():
    assert runtime_identity.limits_digest() == runtime_identity.limits_digest()
    assert len(runtime_identity.limits_digest()) == 64
