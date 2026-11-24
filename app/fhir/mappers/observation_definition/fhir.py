"""ObservationDefinitionModel row -> FHIR R4 ObservationDefinition. The only
read-side mapper.

The resource is stored whole in ObservationDefinitionModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.observation_definition import ObservationDefinitionModel


def to_fhir_observation_definition(observation_definition: ObservationDefinitionModel) -> dict:
    return content_resource(
        "ObservationDefinition",
        observation_definition.observation_definition_id,
        observation_definition,
    )
