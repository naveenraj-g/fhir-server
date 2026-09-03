from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/schedules", tags=["Schedules"])
router.include_router(core.router)
