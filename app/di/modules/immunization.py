from dependency_injector import containers, providers

from app.repository.immunization import ImmunizationRepository
from app.services.immunization import ImmunizationService


class ImmunizationContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    immunization_repository = providers.Factory(
        ImmunizationRepository,
        session_factory=core.database.provided.session,
    )

    immunization_service = providers.Factory(
        ImmunizationService,
        repository=immunization_repository,
    )
