from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.observation import ObservationService


@inject
def get_observation_service(
    service: ObservationService = Depends(Provide[Container.observation.observation_service]),
) -> ObservationService:
    return service
