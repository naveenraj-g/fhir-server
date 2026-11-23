"""EpisodeOfCareModel row -> FHIR R4 EpisodeOfCare. The only
read-side mapper.

The resource is stored whole in EpisodeOfCareModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.episode_of_care import EpisodeOfCareModel


def to_fhir_episode_of_care(episode_of_care: EpisodeOfCareModel) -> dict:
    return content_resource("EpisodeOfCare", episode_of_care.episode_of_care_id, episode_of_care)
