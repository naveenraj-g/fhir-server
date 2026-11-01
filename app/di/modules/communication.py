from dependency_injector import containers, providers

from app.repository.communication import CommunicationRepository
from app.services.communication import CommunicationService


class CommunicationContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    communication_repository = providers.Factory(
        CommunicationRepository,
        session_factory=core.database.provided.session,
    )

    communication_service = providers.Factory(
        CommunicationService,
        repository=communication_repository,
    )
