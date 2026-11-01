from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.communication import CommunicationService


@inject
def get_communication_service(
    service: CommunicationService = Depends(
        Provide[Container.communication.communication_service]
    ),
) -> CommunicationService:
    return service
