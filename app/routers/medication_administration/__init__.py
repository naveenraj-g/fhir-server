from fastapi import APIRouter

from . import core

router = APIRouter(
    prefix="/medication-administrations", tags=["MedicationAdministrations"]
)
router.include_router(core.router)
