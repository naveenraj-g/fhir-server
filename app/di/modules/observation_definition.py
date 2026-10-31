from dependency_injector import containers, providers

from app.repository.observation_definition import ObservationDefinitionRepository
from app.services.observation_definition import ObservationDefinitionService


class ObservationDefinitionContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    observation_definition_repository = providers.Factory(
        ObservationDefinitionRepository,
        session_factory=core.database.provided.session,
    )

    observation_definition_service = providers.Factory(
        ObservationDefinitionService,
        repository=observation_definition_repository,
    )
