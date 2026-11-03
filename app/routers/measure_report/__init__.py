from fastapi import APIRouter

from app.routers.measure_report.core import router as core_router

router = APIRouter(prefix="/measure-reports", tags=["MeasureReports"])
router.include_router(core_router)

__all__ = ["router"]
