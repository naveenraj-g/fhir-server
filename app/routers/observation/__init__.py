from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/observations", tags=["Observations"])
router.include_router(core.router)
