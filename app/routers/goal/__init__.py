from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/goals", tags=["Goals"])
router.include_router(core.router)
