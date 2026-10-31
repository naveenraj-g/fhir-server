from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.activity_definition import ActivityDefinitionService


@inject
def get_activity_definition_service(
    service: ActivityDefinitionService = Depends(
        Provide[Container.activity_definition.activity_definition_service]
    ),
) -> ActivityDefinitionService:
    return service
