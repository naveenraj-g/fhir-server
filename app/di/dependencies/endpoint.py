from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.endpoint import EndpointService


@inject
def get_endpoint_service(
    service: EndpointService = Depends(
        Provide[Container.endpoint.endpoint_service]
    ),
) -> EndpointService:
    return service
