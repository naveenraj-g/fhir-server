from dependency_injector import containers, providers

from app.repository.specimen_definition import SpecimenDefinitionRepository
from app.services.specimen_definition import SpecimenDefinitionService


class SpecimenDefinitionContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    specimen_definition_repository = providers.Factory(
        SpecimenDefinitionRepository,
        session_factory=core.database.provided.session,
    )

    specimen_definition_service = providers.Factory(
        SpecimenDefinitionService,
        repository=specimen_definition_repository,
    )
