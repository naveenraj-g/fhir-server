from dependency_injector import containers, providers

from app.repository.activity_definition import ActivityDefinitionRepository
from app.services.activity_definition import ActivityDefinitionService


class ActivityDefinitionContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    activity_definition_repository = providers.Factory(
        ActivityDefinitionRepository,
        session_factory=core.database.provided.session,
    )

    activity_definition_service = providers.Factory(
        ActivityDefinitionService,
        repository=activity_definition_repository,
    )
