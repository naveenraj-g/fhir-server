from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.medication_request import MedicationRequestService


@inject
def get_medication_request_service(
    service: MedicationRequestService = Depends(Provide[Container.medication_request.medication_request_service]),
) -> MedicationRequestService:
    return service
