from fastapi import Depends, Path

from app.di.dependencies.questionnaire_response import get_questionnaire_response_service
from app.models.questionnaire_response import QuestionnaireResponseModel
from app.services.questionnaire_response import QuestionnaireResponseService


async def resolve_questionnaire_response(
    questionnaire_response_id: int = Path(..., ge=1, description="Public questionnaire_response identifier."),
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
) -> QuestionnaireResponseModel:
    """Loads a QuestionnaireResponse by its public ID, 404 if missing — no
    ownership check (default/gateway-trusted pattern, see
    QuestionnaireResponseService's own docstring). Used as
    `Depends(resolve_questionnaire_response)` in route signatures."""
    return await service.get_by_questionnaire_response_id(questionnaire_response_id)
