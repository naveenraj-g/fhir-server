from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.communication_request import CommunicationRequestService


@inject
def get_communication_request_service(
    service: CommunicationRequestService = Depends(
        Provide[Container.communication_request.communication_request_service]
    ),
) -> CommunicationRequestService:
    return service
