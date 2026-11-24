from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/measures", tags=["Measures"])
router.include_router(core.router)
