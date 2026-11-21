"""ObservationModel row -> FHIR R4 Observation. The only
read-side mapper.

The resource is stored whole in ObservationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.observation import ObservationModel


def to_fhir_observation(observation: ObservationModel) -> dict:
    return content_resource("Observation", observation.observation_id, observation)
