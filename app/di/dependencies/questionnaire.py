from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.questionnaire import QuestionnaireService


@inject
def get_questionnaire_service(
    service: QuestionnaireService = Depends(Provide[Container.questionnaire.questionnaire_service]),
) -> QuestionnaireService:
    return service
