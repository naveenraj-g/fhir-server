from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/tasks", tags=["Tasks"])
router.include_router(core.router)
