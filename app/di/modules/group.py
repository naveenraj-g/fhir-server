from dependency_injector import containers, providers

from app.repository.group import GroupRepository
from app.services.group import GroupService


class GroupContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    group_repository = providers.Factory(
        GroupRepository,
        session_factory=core.database.provided.session,
    )

    group_service = providers.Factory(
        GroupService,
        repository=group_repository,
    )
