from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/service-requests", tags=["ServiceRequests"])
router.include_router(core.router)
