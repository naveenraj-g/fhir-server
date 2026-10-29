from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.appointment_response import AppointmentResponseService


@inject
def get_appointment_response_service(
    service: AppointmentResponseService = Depends(
        Provide[Container.appointment_response.appointment_response_service]
    ),
) -> AppointmentResponseService:
    return service
