from fastapi import APIRouter

from app.routers.measure.core import router as core_router

router = APIRouter(prefix="/measures", tags=["Measures"])
router.include_router(core_router)

__all__ = ["router"]
