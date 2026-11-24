"""ActivityDefinitionModel row -> FHIR R4 ActivityDefinition. The only
read-side mapper.

The resource is stored whole in ActivityDefinitionModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.activity_definition import ActivityDefinitionModel


def to_fhir_activity_definition(activity_definition: ActivityDefinitionModel) -> dict:
    return content_resource(
        "ActivityDefinition",
        activity_definition.activity_definition_id,
        activity_definition,
    )
