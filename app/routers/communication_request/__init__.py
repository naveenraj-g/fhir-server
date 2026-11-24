from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/communication-requests", tags=["CommunicationRequestRequests"])
router.include_router(core.router)
