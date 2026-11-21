from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/specimens", tags=["Specimens"])
router.include_router(core.router)
