"""PIP points-threshold cuts on build 6f918b81 (REVIEW2 Y1).

Points are held only for PIP recipients, so a standard-threshold cut is not
computable, alone or bundled with another change; a raise is, under the
drawn-points assumption. Same rule as uk-pip-review-2026.
"""

import pytest

from young_people_work import data_limits, publication
from young_people_work.data_build import DATA_BUILD
from young_people_work.models import Reform
from young_people_work.reforms import get_reform

DL_STANDARD = "gov.dwp.pip.daily_living.points_thresholds.standard"
MOB_STANDARD = "gov.dwp.pip.mobility.points_thresholds.standard"
DL_ENHANCED = "gov.dwp.pip.daily_living.points_thresholds.enhanced"


def _fields():
    rate = get_reform("employer_nics_under_25")
    return rate, rate.model_dump(exclude={"parameter_changes", "id"})


def test_cut_limit_is_live_on_6f918b81():
    assert DATA_BUILD.short_id == "6f918b81"
    assert "pip_threshold_cut" in data_limits.LIMITS_BY_BUILD["6f918b81"]
    keys = {limit.key for limit in data_limits.LIMITS}
    assert "pip_threshold_cut" in keys


@pytest.mark.parametrize("path", [DL_STANDARD, MOB_STANDARD])
def test_standard_cut_is_not_computable(path):
    cut = {path: {"2027": 6.0}}
    assert not data_limits.is_computable_on_data(cut)
    assert data_limits.is_only_data_limited(cut)


def test_cut_bundled_with_another_change_is_refused():
    rate, fields = _fields()
    changes = {**rate.parameter_changes, DL_STANDARD: {"2027": 6.0}}
    assert not data_limits.is_only_data_limited(changes)
    assert [x.key for x in data_limits.refusing_limits(changes)] == ["pip_threshold_cut"]
    with pytest.raises(ValueError, match="pip_threshold_cut"):
        Reform(id="bundled_cut", parameter_changes=changes, **fields)
    sneaked = Reform.model_construct(id="bundled_cut", parameter_changes=changes, **fields)
    with pytest.raises(ValueError, match="Publication check failed"):
        publication.manifest([sneaked])


def test_raise_and_enhanced_cut_kept_at_8_stay_computable():
    rate, fields = _fields()
    for extra in ({DL_STANDARD: {"2027": 10.0}}, {DL_ENHANCED: {"2027": 10.0}}):
        changes = {**rate.parameter_changes, **extra}
        assert data_limits.is_computable_on_data(changes)
        assert Reform(id="ok", parameter_changes=changes, **fields).computable
    assert not data_limits.is_computable_on_data({DL_ENHANCED: {"2027": 7.0}})


def test_bare_threshold_path_is_treated_as_a_cut():
    assert data_limits.limits_for_paths([DL_STANDARD])
