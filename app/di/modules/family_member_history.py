from dependency_injector import containers, providers

from app.repository.family_member_history import FamilyMemberHistoryRepository
from app.services.family_member_history import FamilyMemberHistoryService


class FamilyMemberHistoryContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    family_member_history_repository = providers.Factory(
        FamilyMemberHistoryRepository,
        session_factory=core.database.provided.session,
    )

    family_member_history_service = providers.Factory(
        FamilyMemberHistoryService,
        repository=family_member_history_repository,
    )
