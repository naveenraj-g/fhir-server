from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.practitioner import PractitionerService


@inject
def get_practitioner_service(
    service: PractitionerService = Depends(
        Provide[Container.practitioner.practitioner_service]
    ),
) -> PractitionerService:
    return service
