from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.measure import MeasureService


@inject
def get_measure_service(
    service: MeasureService = Depends(
        Provide[Container.measure.measure_service]
    ),
) -> MeasureService:
    return service
