from dependency_injector import containers, providers

from app.repository.medication_dispense import (
    MedicationDispenseRepository,
)
from app.services.medication_dispense import (
    MedicationDispenseService,
)


class MedicationDispenseContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    medication_dispense_repository = providers.Factory(
        MedicationDispenseRepository,
        session_factory=core.database.provided.session,
    )
    medication_dispense_service = providers.Factory(
        MedicationDispenseService,
        repository=medication_dispense_repository,
    )
