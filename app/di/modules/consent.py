from dependency_injector import containers, providers

from app.repository.consent import ConsentRepository
from app.services.consent import ConsentService


class ConsentContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    consent_repository = providers.Factory(
        ConsentRepository,
        session_factory=core.database.provided.session,
    )

    consent_service = providers.Factory(
        ConsentService,
        repository=consent_repository,
    )
