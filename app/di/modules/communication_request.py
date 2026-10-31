from dependency_injector import containers, providers

from app.repository.communication_request import CommunicationRequestRepository
from app.services.communication_request import CommunicationRequestService


class CommunicationRequestContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    communication_request_repository = providers.Factory(
        CommunicationRequestRepository,
        session_factory=core.database.provided.session,
    )

    communication_request_service = providers.Factory(
        CommunicationRequestService,
        repository=communication_request_repository,
    )
