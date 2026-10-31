from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.condition import ConditionService


@inject
def get_condition_service(
    service: ConditionService = Depends(
        Provide[Container.condition.condition_service]
    ),
) -> ConditionService:
    return service
