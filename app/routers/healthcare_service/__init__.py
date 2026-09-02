from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/healthcare-services", tags=["HealthcareServices"])
router.include_router(core.router)
