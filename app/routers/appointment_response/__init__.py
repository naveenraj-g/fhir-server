from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/appointment-responses", tags=["AppointmentResponses"])
router.include_router(core.router)
