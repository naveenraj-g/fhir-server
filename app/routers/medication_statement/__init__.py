from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/medication-statements", tags=["MedicationStatements"])
router.include_router(core.router)
