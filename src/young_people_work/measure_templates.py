"""Parameter builders, pruned from the AB2026 dashboard's ``measure_templates``.

Kept: ``rate_change``, ``threshold_change`` and ``uc_health_element_change``,
with the AB2026 refusals of the UC health traps. Every value is keyed by its
bare fiscal year in ASCII digits. The other registered AB2026 templates
(``allowance_uprating``, ``pension_uprating``, ``apply_vat_base_change``,
``apply_benefit_receipt_payment``, ``apply_age_conditioned_allowance``,
``apply_property_band_surcharge``) are copied from that repository when a
measure needs one.

Paths are checked against the installed engine's parameter tree when the
``model`` extra is installed, and by shape only when it is not (the template's
own tests). The model CI job runs with the engine, so a path that does not
resolve fails there.

A parameter covered by a data limit still builds, with a
``DataLimitedWarning``: the measure is published as not computable, never as
a figure. A parameter covered by a model limit builds with a
``ModelLimitedWarning``: the measure is held at provisional.
"""

import math
import re
import warnings
from collections.abc import Mapping

REGISTERED_TEMPLATES = ("rate_change", "threshold_change", "uc_health_element_change")
_YEAR_KEY = re.compile(r"^[0-9]{4}$")
# Lower-case path segments; a bracket index selects a scale bracket, as in
# ``gov.hmrc.minimum_wage.non_apprentice[1].amount``. Upper-case segments are
# enum keys, as in ``standard_allowance.amount.SINGLE_YOUNG``.
_PATH = re.compile(r"^gov(\.[A-Za-z0-9_]+(\[[0-9]+\])?)+$")

# Universal Credit's health (LCWRA) element. In the years the engine's UC
# rebalancing runs, it overwrites each claimant's element after the formula:
# pre-2026 claimants get the protected amount, new claimants the new-claimant
# amount. A change to the element's own amount in those years scores nothing.
UC_LCWRA_AMOUNT = "gov.dwp.universal_credit.elements.disabled.amount"
UC_PROTECTED_HEALTH = "gov.dwp.universal_credit.rebalancing.protected_health_element"
UC_NEW_CLAIMANT_HEALTH = "gov.dwp.universal_credit.rebalancing.new_claimant_health_element"
UC_REBALANCING_ACTIVE = "gov.dwp.universal_credit.rebalancing.active"
# policyengine-uk 2.151.0 exports REBALANCING_YEARS = range(2026, 2033). Used
# when the engine is not installed; tests/test_model_engine.py checks it
# against the installed engine.
UC_REBALANCED_YEARS_PINNED = range(2026, 2033)


class DataLimitedWarning(UserWarning):
    """The parameter acts only through an input the data do not hold."""


class ModelLimitedWarning(UserWarning):
    """The installed model mis-costs a change to this parameter."""


def _engine_parameters():
    """The installed engine's parameter tree, or None without the model extra."""
    try:
        from policyengine_uk.system import system
    except ImportError:
        return None
    return system.parameters


def _uc_rebalanced_years() -> range:
    try:
        from policyengine_uk.scenarios import uc_reform
    except ImportError:
        return UC_REBALANCED_YEARS_PINNED
    exported = getattr(uc_reform, "REBALANCING_YEARS", None)
    if exported is None:
        return range(2026, 2030)
    years = sorted(int(year) for year in exported)
    if not years or years != list(range(years[0], years[-1] + 1)):
        raise ValueError(
            "policyengine_uk.scenarios.uc_reform.REBALANCING_YEARS must be "
            f"consecutive years; got {exported!r}"
        )
    return range(years[0], years[-1] + 1)


UC_REBALANCED_YEARS = _uc_rebalanced_years()
UC_HEALTH_ADVICE = (
    "build a UC health measure with uc_health_element_change(), which sets "
    f"{UC_PROTECTED_HEALTH} (pre-2026 claimants) and {UC_NEW_CLAIMANT_HEALTH} "
    "(new claimants), or with a modifier in young_people_work.measures"
)


def _validate_path(path: str) -> None:
    if not isinstance(path, str) or not _PATH.match(path):
        raise ValueError(f"Not a parameter path: {path!r}")
    parameters = _engine_parameters()
    if parameters is None:
        return
    from policyengine_core.parameters import Parameter

    try:
        node = parameters.get_child(path)
    except (KeyError, AttributeError, IndexError, ValueError) as error:
        raise ValueError(f"Unknown parameter path in the installed engine: {path}") from error
    if not isinstance(node, Parameter):
        raise ValueError(f"Parameter path must identify a leaf: {path}")


def _annual_values(values: Mapping) -> dict[str, float]:
    if not values:
        raise ValueError("Give at least one year")
    out: dict[str, float] = {}
    for key, value in values.items():
        key_text = str(key)
        if not _YEAR_KEY.match(key_text) or not key_text.isascii():
            raise ValueError(f"Key each value by a bare fiscal year, not {key!r}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{key}: value must be a number")
        if not math.isfinite(value):
            raise ValueError(f"{key}: value must be finite")
        out[key_text] = float(value)
    return dict(sorted(out.items()))


def _warn_if_data_limited(path: str) -> None:
    from young_people_work.data_limits import limits_for_paths

    for limit in limits_for_paths([path]):
        warnings.warn(f"{path}: {limit.reason}", DataLimitedWarning, stacklevel=4)


def _warn_if_model_limited(path: str) -> None:
    from young_people_work.model_limits import limits_for_paths

    for limit in limits_for_paths([path]):
        warnings.warn(
            f"{path}: {limit.reason} A measure built on it is held at provisional.",
            ModelLimitedWarning,
            stacklevel=4,
        )


def _refuse_uc_health_traps(path: str, years) -> None:
    """Refuse the UC health changes that score nothing or the wrong thing."""
    rebalanced = [str(y) for y in years if int(y) in UC_REBALANCED_YEARS]
    if path == UC_LCWRA_AMOUNT and rebalanced:
        raise ValueError(
            f"{UC_LCWRA_AMOUNT} in {', '.join(rebalanced)} is not what UC health "
            f"awards pay: in {UC_REBALANCED_YEARS.start}-{UC_REBALANCED_YEARS.stop - 1} "
            "the engine's UC rebalancing overwrites each claimant's element, so a "
            "change to it scores nothing; " + UC_HEALTH_ADVICE
        )
    if path == UC_REBALANCING_ACTIVE:
        raise ValueError(
            f"{UC_REBALANCING_ACTIVE} switched off is not the law before the "
            "Universal Credit Act 2025: the 2026 element amount is already the "
            "new claimants' rate, so every claimant would get it; " + UC_HEALTH_ADVICE
        )


def rate_change(path: str, values: Mapping) -> dict[str, dict[str, float]]:
    """A rate or amount set for each fiscal year, for example a UC work allowance."""
    _validate_path(path)
    annual = _annual_values(values)
    _refuse_uc_health_traps(path, annual)
    _warn_if_data_limited(path)
    _warn_if_model_limited(path)
    return {path: annual}


def threshold_change(path: str, values: Mapping) -> dict[str, dict[str, float]]:
    """A threshold set for each fiscal year, for example an age limit."""
    _validate_path(path)
    annual = _annual_values(values)
    _refuse_uc_health_traps(path, annual)
    _warn_if_data_limited(path)
    _warn_if_model_limited(path)
    return {path: annual}


def uc_health_element_change(
    *, protected: Mapping | None = None, new_claimant: Mapping | None = None
) -> dict[str, dict[str, float]]:
    """Change the UC health (LCWRA) element as the model pays it.

    ``protected`` sets the amount for pre-2026 claimants and ``new_claimant``
    the amount for those who claim from April 2026, monthly, by fiscal year.
    Only the rebalanced years: outside them the rebalancing does not run and
    the values would score nothing. No model-limit warning: this is the
    route around the shadowing limit, not a change it covers.
    """
    changes = {}
    for path, values in ((UC_PROTECTED_HEALTH, protected), (UC_NEW_CLAIMANT_HEALTH, new_claimant)):
        if values is None:
            continue
        _validate_path(path)
        annual = _annual_values(values)
        outside = [y for y in annual if int(y) not in UC_REBALANCED_YEARS]
        if outside:
            raise ValueError(
                f"{path} is used only in {UC_REBALANCED_YEARS.start}-"
                f"{UC_REBALANCED_YEARS.stop - 1}, while the UC rebalancing runs; a "
                f"value for {', '.join(outside)} would score nothing"
            )
        changes[path] = annual
    if not changes:
        raise ValueError("Supply protected or new_claimant amounts")
    return changes


def merge(*changes: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]:
    """Merge builder outputs, refusing two values for one parameter."""
    merged: dict[str, dict[str, float]] = {}
    for change in changes:
        for path, years in change.items():
            if path in merged:
                raise ValueError(f"{path} is set twice")
            merged[path] = dict(years)
    return merged
