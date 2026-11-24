from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/flags", tags=["Flags"])
router.include_router(core.router)
