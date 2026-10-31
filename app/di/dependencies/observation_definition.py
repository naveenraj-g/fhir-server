from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.observation_definition import ObservationDefinitionService


@inject
def get_observation_definition_service(
    service: ObservationDefinitionService = Depends(
        Provide[Container.observation_definition.observation_definition_service]
    ),
) -> ObservationDefinitionService:
    return service
