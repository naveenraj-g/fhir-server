from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/diagnostic-reports", tags=["DiagnosticReports"])
router.include_router(core.router)
