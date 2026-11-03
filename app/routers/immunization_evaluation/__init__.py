from fastapi import APIRouter

from app.routers.immunization_evaluation.core import router as core_router

router = APIRouter(
    prefix="/immunization-evaluations",
    tags=["ImmunizationEvaluations"],
)
router.include_router(core_router)

__all__ = ["router"]
