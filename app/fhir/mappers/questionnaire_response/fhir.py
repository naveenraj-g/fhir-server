"""QuestionnaireResponseModel row -> FHIR R4 QuestionnaireResponse. The only
read-side mapper.

The resource is stored whole in QuestionnaireResponseModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.questionnaire_response import QuestionnaireResponseModel


def to_fhir_questionnaire_response(
    questionnaire_response: QuestionnaireResponseModel,
) -> dict:
    return content_resource(
        "QuestionnaireResponse",
        questionnaire_response.questionnaire_response_id,
        questionnaire_response,
    )
