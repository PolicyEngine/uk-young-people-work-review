import re
import tomllib
from pathlib import Path

from young_people_work import runtime_identity
from young_people_work.pipeline import ENGINE

ROOT = Path(__file__).resolve().parents[1]


def _locked(name):
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    return next(p["version"] for p in lock["package"] if p["name"] == name)


def test_pinned_strings_match_uv_lock():
    pinned = runtime_identity.PINNED
    assert pinned["policyengine"] == _locked("policyengine")
    assert pinned["policyengine_uk"] == _locked("policyengine-uk")
    assert pinned["policyengine_core"] == _locked("policyengine-core")
    assert ENGINE["policyengine_uk"] == pinned["policyengine_uk"]


def test_pyproject_pin_matches_uv_lock():
    text = (ROOT / "pyproject.toml").read_text()
    assert f"policyengine[uk]=={_locked('policyengine')}" in text


def test_readme_names_the_pinned_versions():
    readme = (ROOT / "README.md").read_text()
    for version in (_locked("policyengine"), _locked("policyengine-uk")):
        assert re.search(re.escape(version), readme), version


def test_limits_digest_is_stable():
    assert runtime_identity.limits_digest() == runtime_identity.limits_digest()
    assert len(runtime_identity.limits_digest()) == 64
