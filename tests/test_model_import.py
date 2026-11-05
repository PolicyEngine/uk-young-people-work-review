"""The engine pin imports, when the ``model`` extra is installed (skipped otherwise)."""

import pytest

from young_people_work.reforms import get_reform


def test_scenario_builds_with_engine():
    pytest.importorskip("policyengine_uk")
    scenario = get_reform("youth_standard_allowance").to_scenario()
    assert scenario is not None
