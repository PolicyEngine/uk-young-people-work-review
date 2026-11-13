"""Reform definition, copied in shape from the AB2026 dashboard (``uk_budget_data.models``).

Changes from the source:
- the ``Scenario`` import is lazy, so the registry and its tests load without
  policyengine-uk;
- each reform carries its route, cause class, publication status and
  placeholder flag, so the ledger and the page read them from one place.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Route(str, Enum):
    """How a measure is handled on the day (the drill ledger's route classes)."""

    DASHBOARD_PARAM = "dashboard-param"
    DASHBOARD_STRUCTURAL = "dashboard-structural"
    LEDGER = "ledger"
    NOT_COMPUTABLE = "not-computable"
    NEEDS_PE_UK_FIRST = "needs-pe-uk-first"


class Likelihood(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Reform(BaseModel):
    """Definition of a policy reform.

    A reform is defined by parameter changes (simple reforms) or by a
    simulation modifier from ``young_people_work.measures`` (structural reforms).
    """

    id: str = Field(..., pattern=r"^[a-z0-9_]+$")
    name: str
    description: str = ""
    recommendation: str = Field(
        ..., description="The review recommendation this measure stands for"
    )
    likelihood: Likelihood = Field(
        ..., description="Our own pre-report guess; internal, never published"
    )
    route: Route
    route_reason: str = Field(..., description="Why the measure has this route; shown on the page")
    placeholder: bool = Field(
        True,
        description=(
            "Placeholder values, set before the report. A placeholder is never "
            "published as a figure."
        ),
    )
    zero_reason: str | None = Field(
        None,
        description=(
            "Why a coded measure's £0 national figure is right. Without it, a "
            "measure that scores £0 in every year fails the publication check."
        ),
    )
    data_needs: list[str] = Field(default_factory=list)
    issues: list[int] = Field(
        default_factory=list, description="Issues in this repository that block it"
    )
    parameter_changes: dict[str, dict[str, Any]] | None = None
    baseline_parameter_changes: dict[str, dict[str, Any]] | None = None
    simulation_modifier: Callable | None = None
    upper_bound_modifier: Callable | None = Field(
        None,
        description=(
            "A second modifier for the upper bound of a range (for example every "
            "claimant under an age limit, not only new claimants). Model mode "
            "runs it too and publishes the cost as budgetary_impact_upper."
        ),
    )
    applied_before_data_load: bool = Field(
        False,
        description=(
            "Run the modifier before the data load. A modifier that wraps a "
            "formula the UC rebalancing stores (uc_LCWRA_element) must run "
            "before it, or the stored value wins and the change does nothing."
        ),
    )
    in_headline: bool = Field(
        True,
        description=(
            "Part of the default package and the headline tile. Stand-ins that "
            "reach people outside the review's age group are shown as separate "
            "scenarios, never in the headline."
        ),
    )
    age_bands_reached: tuple[str, ...] | None = Field(
        None,
        description=(
            "The age bands a measure can change. A published age-band figure "
            "outside these is an error. None means every band."
        ),
    )
    official_cost: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "The report's or an official costing, kept apart from the modelled "
            "total: each row has year, value_m, source_url and paragraph."
        ),
    )
    coverage: str = Field(
        "UK",
        pattern=r"^(UK|Great Britain|England and Wales|England)$",
        description=(
            "Where the measure applies. UC and National Insurance are UK-wide; "
            "PIP applies in England and Wales; employment support and the "
            "participation system are devolved, so those apply in England."
        ),
    )

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def _route_matches_content(self) -> "Reform":
        computable = self.route in (Route.DASHBOARD_PARAM, Route.DASHBOARD_STRUCTURAL)
        has_change = self.parameter_changes is not None or self.simulation_modifier is not None
        if self.route is Route.DASHBOARD_PARAM and self.parameter_changes is None:
            raise ValueError(f"{self.id}: dashboard-param needs parameter_changes")
        if self.route is Route.DASHBOARD_STRUCTURAL and self.simulation_modifier is None:
            raise ValueError(f"{self.id}: dashboard-structural needs a modifier")
        if not computable and self.simulation_modifier is not None:
            raise ValueError(f"{self.id}: only a computable route takes a modifier")
        if not computable and has_change and self.route is not Route.NOT_COMPUTABLE:
            raise ValueError(f"{self.id}: a {self.route.value} measure carries no model change")
        return self

    @property
    def computable(self) -> bool:
        return self.route in (Route.DASHBOARD_PARAM, Route.DASHBOARD_STRUCTURAL)

    @property
    def publishable(self) -> bool:
        """A figure may be published: computable and no longer a placeholder."""
        return self.computable and not self.placeholder

    def to_scenario(self):
        """Convert to a policyengine-uk ``Scenario`` (needs the ``model`` extra)."""
        from policyengine_uk.utils.scenario import Scenario

        kwargs: dict[str, Any] = {}
        if self.parameter_changes is not None:
            kwargs["parameter_changes"] = self.parameter_changes
        if self.simulation_modifier is not None:
            kwargs["simulation_modifier"] = self.simulation_modifier
            kwargs["applied_before_data_load"] = self.applied_before_data_load
        return Scenario(**kwargs)

    def to_upper_bound_scenario(self):
        if self.upper_bound_modifier is None:
            return None
        from policyengine_uk.utils.scenario import Scenario

        return Scenario(
            parameter_changes=self.parameter_changes,
            simulation_modifier=self.upper_bound_modifier,
            applied_before_data_load=self.applied_before_data_load,
        )

    def to_baseline_scenario(self):
        if self.baseline_parameter_changes is None:
            return None
        from policyengine_uk.utils.scenario import Scenario

        return Scenario(parameter_changes=self.baseline_parameter_changes)

    def summary(self) -> dict[str, Any]:
        """The fields the page and the ledger read (no callables)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "recommendation": self.recommendation,
            "route": self.route.value,
            "route_reason": self.route_reason,
            "placeholder": self.placeholder,
            "computable": self.computable,
            "publishable": self.publishable,
            "zero_reason": self.zero_reason,
            "data_needs": list(self.data_needs),
            "issues": list(self.issues),
            "coverage": self.coverage,
            "in_headline": self.in_headline,
            "age_bands_reached": (
                None if self.age_bands_reached is None else list(self.age_bands_reached)
            ),
            "official_cost": [dict(row) for row in self.official_cost],
            "parameters": sorted(self.parameter_changes or {}),
        }
