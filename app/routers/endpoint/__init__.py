from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/endpoints", tags=["Endpoints"])
router.include_router(core.router)
