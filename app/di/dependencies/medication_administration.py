from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.medication_administration import MedicationAdministrationService


@inject
def get_medication_administration_service(
    service: MedicationAdministrationService = Depends(
        Provide[Container.medication_administration.medication_administration_service]
    ),
) -> MedicationAdministrationService:
    return service
