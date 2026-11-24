from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/communications", tags=["Communications"])
router.include_router(core.router)
