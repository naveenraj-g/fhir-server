from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.patient import PatientService


@inject
def get_patient_service(
    service: PatientService = Depends(Provide[Container.patient.patient_service]),
) -> PatientService:
    return service
