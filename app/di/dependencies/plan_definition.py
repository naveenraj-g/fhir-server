from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.plan_definition import PlanDefinitionService


@inject
def get_plan_definition_service(
    service: PlanDefinitionService = Depends(
        Provide[Container.plan_definition.plan_definition_service]
    ),
) -> PlanDefinitionService:
    return service
