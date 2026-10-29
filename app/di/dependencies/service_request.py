from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.service_request import ServiceRequestService


@inject
def get_service_request_service(
    service: ServiceRequestService = Depends(Provide[Container.service_request.service_request_service]),
) -> ServiceRequestService:
    return service
