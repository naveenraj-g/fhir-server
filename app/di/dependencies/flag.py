from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.flag import FlagService


@inject
def get_flag_service(
    service: FlagService = Depends(
        Provide[Container.flag.flag_service]
    ),
) -> FlagService:
    return service
