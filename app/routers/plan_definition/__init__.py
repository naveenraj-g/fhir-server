from fastapi import APIRouter

from .core import router as core_router

router = APIRouter(prefix="/plan-definitions", tags=["PlanDefinitions"])
router.include_router(core_router)

__all__ = ["router"]
