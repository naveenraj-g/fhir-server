"""ImmunizationRecommendationModel row -> FHIR R4 ImmunizationRecommendation. The only
read-side mapper.

The resource is stored whole in ImmunizationRecommendationModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.immunization_recommendation import ImmunizationRecommendationModel


def to_fhir_immunization_recommendation(immunization_recommendation: ImmunizationRecommendationModel) -> dict:
    return content_resource("ImmunizationRecommendation", immunization_recommendation.immunization_recommendation_id, immunization_recommendation)
