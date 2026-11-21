from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/immunization-evaluations", tags=["ImmunizationEvaluations"])
router.include_router(core.router)
