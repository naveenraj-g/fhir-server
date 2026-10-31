from fastapi import APIRouter

from .core import router as core_router

router = APIRouter(prefix="/activity-definitions", tags=["ActivityDefinitions"])
router.include_router(core_router)

__all__ = ["router"]
