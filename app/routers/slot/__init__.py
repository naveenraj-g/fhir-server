from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/slots", tags=["Slots"])
router.include_router(core.router)
