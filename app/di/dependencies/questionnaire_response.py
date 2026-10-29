from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.questionnaire_response import QuestionnaireResponseService


@inject
def get_questionnaire_response_service(
    service: QuestionnaireResponseService = Depends(
        Provide[Container.questionnaire_response.questionnaire_response_service]
    ),
) -> QuestionnaireResponseService:
    return service
