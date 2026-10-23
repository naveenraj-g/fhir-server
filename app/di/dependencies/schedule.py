from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.schedule import ScheduleService


@inject
def get_schedule_service(
    service: ScheduleService = Depends(Provide[Container.schedule.schedule_service]),
) -> ScheduleService:
    return service
