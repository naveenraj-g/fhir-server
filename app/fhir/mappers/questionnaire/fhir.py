"""QuestionnaireModel row -> FHIR R4 Questionnaire. The only
read-side mapper.

The resource is stored whole in QuestionnaireModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.questionnaire import QuestionnaireModel


def to_fhir_questionnaire(questionnaire: QuestionnaireModel) -> dict:
    return content_resource(
        "Questionnaire", questionnaire.questionnaire_id, questionnaire
    )
