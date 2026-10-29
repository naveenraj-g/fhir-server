from dependency_injector import containers, providers

from app.repository.encounter import EncounterRepository
from app.services.encounter import EncounterService


class EncounterContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    encounter_repository = providers.Factory(
        EncounterRepository,
        session_factory=core.database.provided.session,
    )

    encounter_service = providers.Factory(
        EncounterService,
        repository=encounter_repository,
    )
