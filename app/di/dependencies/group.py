from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.group import GroupService


@inject
def get_group_service(
    service: GroupService = Depends(
        Provide[Container.group.group_service]
    ),
) -> GroupService:
    return service
