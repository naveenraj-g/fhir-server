from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/medication-requests", tags=["MedicationRequests"])
router.include_router(core.router)
