"""An age test on the UC health (LCWRA) element.

From 2026-27 the engine's UC rebalancing (policyengine_uk/scenarios/
uc_reform.py, ``add_universal_credit_reform``) computes ``uc_LCWRA_element``
through its formula, gives each benefit unit with an element above zero the
protected or the new-claimant rate, and stores the result. A benefit unit the
formula gives no element keeps none. So an age test that wraps the formula
reaches the stored awards, but only when it is applied before the data load
(``Reform.applied_before_data_load=True``); applied after, the stored value
wins and the test does nothing (checked on 2.151.0 and 2.175.7).

Which claimants are new is the engine's seeded draw per benefit unit at
``rebalancing.new_claimant_share`` (13% in 2027-28), with no age dimension.
Young claimants are more likely to be recent claimants, so a measure for new
claimants under an age limit is published as a range: the lower bound gates
only the benefit units the engine treats as new, the upper bound every
claimant under the limit (``all_claimants_under_*``).

Literal defaults, one module, checked by hand against household tests
(tests/test_model_engine.py) on the day.
"""

import numpy as np

NEW_CLAIMANT_STATUS = "uc_receives_new_claimant_health_element"


def _apply(sim, min_age: int, include_protected: bool) -> None:
    from policyengine_uk.model_api import Variable

    system = sim.tax_benefit_system
    original = system.get_variable("uc_LCWRA_element")

    class uc_LCWRA_element(Variable):
        def formula(benunit, period, parameters):
            current = original.get_formula(period)(benunit, period, parameters)
            members = benunit.members
            young = benunit.any(
                members("is_claimant_or_partner", period) & (members("age", period) < min_age)
            )
            if include_protected:
                return np.where(young, 0, current)
            new = benunit(NEW_CLAIMANT_STATUS, period)
            return np.where(young & new, 0, current)

    system.update_variable(uc_LCWRA_element)


def new_claimants_under_22(sim) -> None:
    _apply(sim, min_age=22, include_protected=False)


def all_claimants_under_22(sim) -> None:
    _apply(sim, min_age=22, include_protected=True)


def new_claimants_under_25(sim) -> None:
    _apply(sim, min_age=25, include_protected=False)


def all_claimants_under_25(sim) -> None:
    _apply(sim, min_age=25, include_protected=True)
