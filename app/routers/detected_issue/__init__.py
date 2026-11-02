from fastapi import APIRouter

from .core import router as _core_router

router = APIRouter(prefix="/detected-issues", tags=["DetectedIssues"])
router.include_router(_core_router)

__all__ = ["router"]
