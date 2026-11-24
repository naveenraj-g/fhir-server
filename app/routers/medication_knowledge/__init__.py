from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/medication-knowledge", tags=["MedicationKnowledge"])
router.include_router(core.router)
