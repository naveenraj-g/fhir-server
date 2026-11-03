from dependency_injector import containers, providers

from app.repository.medication_administration import (
    MedicationAdministrationRepository,
)
from app.services.medication_administration import (
    MedicationAdministrationService,
)


class MedicationAdministrationContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    medication_administration_repository = providers.Factory(
        MedicationAdministrationRepository,
        session_factory=core.database.provided.session,
    )
    medication_administration_service = providers.Factory(
        MedicationAdministrationService,
        repository=medication_administration_repository,
    )
