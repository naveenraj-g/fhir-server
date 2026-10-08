from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.di.container import Container
from app.services.fhir_profile_service import FhirProfileService


@inject
def get_fhir_profile_service(
    service: FhirProfileService = Depends(Provide[Container.fhir_profile.fhir_profile_service]),
) -> FhirProfileService:
    return service
