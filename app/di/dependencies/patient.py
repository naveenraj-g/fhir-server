from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from app.services.patient import PatientService
from app.di.container import Container


@inject
def get_patient_service(
    service: PatientService = Depends(Provide[Container.patient.patient_service]),
) -> PatientService:
    """FastAPI dependency that resolves a PatientService from the DI
    container — this is what every route in app/routers/patient.py depends on."""
    return service
