from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/risk-assessments", tags=["RiskAssessments"])
router.include_router(core.router)
