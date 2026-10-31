from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/conditions", tags=["Conditions"])
router.include_router(core.router)

__all__ = ["router"]
