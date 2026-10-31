from dependency_injector import containers, providers

from app.repository.specimen import SpecimenRepository
from app.services.specimen import SpecimenService


class SpecimenContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    specimen_repository = providers.Factory(
        SpecimenRepository,
        session_factory=core.database.provided.session,
    )

    specimen_service = providers.Factory(
        SpecimenService,
        repository=specimen_repository,
    )
