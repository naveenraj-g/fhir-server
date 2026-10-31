from dependency_injector import containers, providers

from app.repository.condition import ConditionRepository
from app.services.condition import ConditionService


class ConditionContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    condition_repository = providers.Factory(
        ConditionRepository,
        session_factory=core.database.provided.session,
    )

    condition_service = providers.Factory(
        ConditionService,
        repository=condition_repository,
    )
