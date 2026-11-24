"""PlanDefinitionModel row -> FHIR R4 PlanDefinition. The only
read-side mapper.

The resource is stored whole in PlanDefinitionModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.plan_definition import PlanDefinitionModel


def to_fhir_plan_definition(plan_definition: PlanDefinitionModel) -> dict:
    return content_resource(
        "PlanDefinition",
        plan_definition.plan_definition_id,
        plan_definition,
    )
