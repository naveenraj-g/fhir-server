from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/medication-dispenses", tags=["MedicationDispenses"])
router.include_router(core.router)
