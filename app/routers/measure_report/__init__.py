from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/measure-reports", tags=["MeasureReports"])
router.include_router(core.router)
