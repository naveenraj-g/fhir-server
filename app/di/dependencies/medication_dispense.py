from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.medication_dispense import MedicationDispenseService


@inject
def get_medication_dispense_service(
    service: MedicationDispenseService = Depends(
        Provide[Container.medication_dispense.medication_dispense_service]
    ),
) -> MedicationDispenseService:
    return service
