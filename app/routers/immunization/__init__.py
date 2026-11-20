from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/immunizations", tags=["Immunizations"])
router.include_router(core.router)
