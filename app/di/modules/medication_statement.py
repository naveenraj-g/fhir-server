from dependency_injector import containers, providers

from app.repository.medication_statement import MedicationStatementRepository
from app.services.medication_statement import MedicationStatementService


class MedicationStatementContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    medication_statement_repository = providers.Factory(
        MedicationStatementRepository,
        session_factory=core.database.provided.session,
    )

    medication_statement_service = providers.Factory(
        MedicationStatementService,
        repository=medication_statement_repository,
    )
