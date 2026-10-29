from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/encounters", tags=["Encounters"])
router.include_router(core.router)
