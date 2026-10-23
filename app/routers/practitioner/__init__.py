from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/practitioners", tags=["Practitioners"])
router.include_router(core.router)
