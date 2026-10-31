from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.consent import ConsentService


@inject
def get_consent_service(
    service: ConsentService = Depends(
        Provide[Container.consent.consent_service]
    ),
) -> ConsentService:
    return service
