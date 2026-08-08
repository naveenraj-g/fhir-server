from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/locations", tags=["Locations"])
router.include_router(core.router)
