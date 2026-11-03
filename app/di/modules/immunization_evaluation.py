from dependency_injector import containers, providers

from app.repository.immunization_evaluation import ImmunizationEvaluationRepository
from app.services.immunization_evaluation import ImmunizationEvaluationService


class ImmunizationEvaluationContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    immunization_evaluation_repository = providers.Factory(
        ImmunizationEvaluationRepository,
        session_factory=core.database.provided.session,
    )

    immunization_evaluation_service = providers.Factory(
        ImmunizationEvaluationService,
        repository=immunization_evaluation_repository,
    )
