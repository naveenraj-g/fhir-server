from dependency_injector import containers, providers

from app.repository.questionnaire_response import QuestionnaireResponseRepository
from app.services.questionnaire_response import QuestionnaireResponseService


class QuestionnaireResponseContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    questionnaire_response_repository = providers.Factory(
        QuestionnaireResponseRepository,
        session_factory=core.database.provided.session,
    )

    questionnaire_response_service = providers.Factory(
        QuestionnaireResponseService,
        repository=questionnaire_response_repository,
    )
