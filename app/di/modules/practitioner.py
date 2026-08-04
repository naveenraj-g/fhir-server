from dependency_injector import containers, providers
from app.repository.practitioner import PractitionerRepository
from app.services.practitioner import PractitionerService


class PractitionerContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    practitioner_repository = providers.Factory(
        PractitionerRepository,
        session_factory=core.database.provided.session,
    )

    practitioner_service = providers.Factory(
        PractitionerService,
        repository=practitioner_repository,
    )
