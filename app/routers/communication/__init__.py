from fastapi import APIRouter

from .core import router as core_router

router = APIRouter(prefix="/communications", tags=["Communications"])
router.include_router(core_router)

__all__ = ["router"]
