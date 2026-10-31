from fastapi import APIRouter

from .core import router as core_router

router = APIRouter(prefix="/flags", tags=["Flag"])
router.include_router(core_router)

__all__ = ["router"]
