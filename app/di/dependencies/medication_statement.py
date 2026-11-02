from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.medication_statement import MedicationStatementService


@inject
def get_medication_statement_service(
    service: MedicationStatementService = Depends(
        Provide[Container.medication_statement.medication_statement_service]
    ),
) -> MedicationStatementService:
    return service
