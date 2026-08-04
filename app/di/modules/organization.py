from dependency_injector import containers, providers

from app.repository.organization import OrganizationRepository
from app.services.organization import OrganizationService


class OrganizationContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    organization_repository = providers.Factory(
        OrganizationRepository,
        session_factory=core.database.provided.session,
    )

    organization_service = providers.Factory(
        OrganizationService,
        repository=organization_repository,
    )
