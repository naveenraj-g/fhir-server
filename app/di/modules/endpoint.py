from dependency_injector import containers, providers

from app.repository.endpoint import EndpointRepository
from app.services.endpoint import EndpointService


class EndpointContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()

    endpoint_repository = providers.Factory(
        EndpointRepository,
        session_factory=core.database.provided.session,
    )

    endpoint_service = providers.Factory(
        EndpointService,
        repository=endpoint_repository,
    )
