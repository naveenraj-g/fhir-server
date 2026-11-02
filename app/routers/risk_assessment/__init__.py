from fastapi import APIRouter

from .core import router as core_router

router = APIRouter(
    prefix="/risk-assessments",
    tags=["RiskAssessments"],
)
router.include_router(core_router)

__all__ = ["router"]
