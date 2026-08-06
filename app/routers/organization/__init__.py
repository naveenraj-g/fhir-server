from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/organizations", tags=["Organizations"])
router.include_router(core.router)
