from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.appointment import AppointmentService


@inject
def get_appointment_service(
    service: AppointmentService = Depends(Provide[Container.appointment.appointment_service]),
) -> AppointmentService:
    return service
