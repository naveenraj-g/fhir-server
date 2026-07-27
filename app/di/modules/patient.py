from dependency_injector import containers, providers
from app.repository.patient_repository import PatientRepository
from app.services.patient_service import PatientService


class PatientContainer(containers.DeclarativeContainer):
    """DI wiring for Patient: PatientRepository (session_factory from the core
    container's Database) -> PatientService (wraps the repository). Mounted
    as Container.patient in app/di/container.py."""

    core = providers.DependenciesContainer()

    patient_repository = providers.Factory(
        PatientRepository,
        session_factory=core.database.provided.session,
    )

    patient_service = providers.Factory(
        PatientService,
        repository=patient_repository,
    )
